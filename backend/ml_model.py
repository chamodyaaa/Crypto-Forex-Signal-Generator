from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit, train_test_split

from data_fetcher import get_market_data
from indicators import calculate_ema, calculate_macd, calculate_rsi


FEATURE_COLUMNS = [
	"close",
	"rsi",
	"ema_20",
	"ema_50",
	"macd",
	"macd_signal",
	"macd_histogram",
	"return_1",
	"volatility_10",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_model_path(file_path: str) -> Path:
	"""Resolve model paths relative to the project root by default."""
	path = Path(file_path)
	if path.is_absolute():
		return path

	cwd_path = Path.cwd() / path
	if cwd_path.exists():
		return cwd_path

	return PROJECT_ROOT / path


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
	"""Add technical indicators required for feature engineering."""
	result = calculate_rsi(df, period=14, price_col="close")
	result = calculate_ema(result, span=20, price_col="close", output_col="ema_20")
	result = calculate_ema(result, span=50, price_col="close", output_col="ema_50")
	result = calculate_macd(result, price_col="close")
	result["return_1"] = result["close"].pct_change()
	result["volatility_10"] = result["return_1"].rolling(10).std()
	return result


def generate_labels(df: pd.DataFrame) -> pd.DataFrame:
	"""Create rule-based labels: 1=buy, -1=sell, 0=hold."""
	result = df.copy()

	trend_up = result["ema_20"] >= result["ema_50"]
	trend_down = result["ema_20"] <= result["ema_50"]

	# More flexible BUY conditions - easier to trigger
	buy_rule = (
		((result["rsi"] < 40) & (result["macd"] > result["macd_signal"])) |  # RSI approaching oversold + bullish MACD
		((result["rsi"] < 30) & (result["close"] > result["ema_20"])) |  # Oversold + price above EMA
		((result["rsi"] > 50) & (result["rsi"] < 60) & (result["macd"] > result["macd_signal"]) & (result["close"] > result["ema_20"])) |  # Neutral RSI but bullish technicals
		((result["rsi"] >= 50) & trend_up & (result["close"] > result["ema_20"]) & (result["macd"] >= result["macd_signal"]))  # Trend continuation buy
	)
	
	# More flexible SELL conditions - easier to trigger
	sell_rule = (
		((result["rsi"] > 60) & (result["macd"] < result["macd_signal"])) |  # RSI approaching overbought + bearish MACD
		((result["rsi"] > 70) & (result["close"] < result["ema_20"])) |  # Overbought + price below EMA
		((result["rsi"] > 40) & (result["rsi"] < 50) & (result["macd"] < result["macd_signal"]) & (result["close"] < result["ema_20"])) |  # Neutral RSI but bearish technicals
		((result["rsi"] <= 50) & trend_down & (result["close"] < result["ema_20"]) & (result["macd"] <= result["macd_signal"]))  # Trend continuation sell
	)

	result["label"] = 0  # Default to HOLD
	result.loc[sell_rule, "label"] = -1  # Apply SELL first
	result.loc[buy_rule & ~sell_rule, "label"] = 1  # Apply BUY if not already SELL

	return result


def rebalance_training_labels(
	dataset: pd.DataFrame,
	hold_label: int = 0,
	max_hold_ratio: float = 0.45,
	random_state: int = 42,
) -> pd.DataFrame:
	"""Downsample HOLD rows so training is less biased toward neutral predictions."""
	if dataset.empty:
		return dataset

	hold_rows = dataset[dataset["label"] == hold_label]
	directional_rows = dataset[dataset["label"] != hold_label]

	if directional_rows.empty:
		return dataset

	max_hold_count = int((max_hold_ratio / max(1e-6, 1 - max_hold_ratio)) * len(directional_rows))
	if len(hold_rows) <= max_hold_count:
		return dataset

	hold_sampled = hold_rows.sample(n=max_hold_count, random_state=random_state)
	rebalanced = pd.concat([directional_rows, hold_sampled], axis=0)
	rebalanced = rebalanced.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

	return rebalanced


def prepare_dataset(
	asset_type: str = "crypto",
	symbol: str = "BTCUSDT",
	timeframe: str = "1h",
	limit: int = 1000,
) -> pd.DataFrame:
	"""Fetch market data and return a labeled dataset ready for ML."""
	df = get_market_data(asset_type=asset_type, symbol=symbol, timeframe=timeframe)

	# Align to requested dataset size when source API provides more rows.
	if limit > 0 and len(df) > limit:
		df = df.tail(limit).copy()

	df = add_indicators(df)
	df = generate_labels(df)

	# Remove warm-up rows where indicators are not fully initialized.
	df = df.dropna(subset=FEATURE_COLUMNS + ["label"]).copy()

	return df


def train_model(dataset: pd.DataFrame) -> tuple[CalibratedClassifierCV, dict[str, float], str]:
	"""Train and evaluate a calibrated Random Forest classifier."""
	dataset = rebalance_training_labels(dataset)

	X = dataset[FEATURE_COLUMNS]
	y = dataset["label"]

	X_train, X_test, y_train, y_test = train_test_split(
		X,
		y,
		test_size=0.2,
		random_state=42,
		stratify=y if y.nunique() > 1 else None,
	)

	base_model = RandomForestClassifier(
		random_state=42,
		class_weight="balanced_subsample",
		n_jobs=-1,
	)

	# Time-series aware tuning on training split only.
	search_space = {
		"n_estimators": [200, 300, 400, 500],
		"max_depth": [6, 8, 10, 12, None],
		"min_samples_split": [2, 5, 10],
		"min_samples_leaf": [1, 2, 4],
		"max_features": ["sqrt", "log2", None],
	}

	tscv = TimeSeriesSplit(n_splits=4)
	search = RandomizedSearchCV(
		estimator=base_model,
		param_distributions=search_space,
		n_iter=12,
		scoring="f1_weighted",
		cv=tscv,
		random_state=42,
		n_jobs=-1,
	)
	search.fit(X_train, y_train)
	tuned_model = search.best_estimator_
	class_counts = y_train.value_counts()
	min_class_count = int(class_counts.min()) if not class_counts.empty else 0

	if min_class_count >= 2:
		cv_folds = min(5, min_class_count)
		model = CalibratedClassifierCV(
			estimator=tuned_model,
			method="sigmoid",
			cv=cv_folds,
		)
		model.fit(X_train, y_train)
	else:
		tuned_model.fit(X_train, y_train)
		model = tuned_model

	y_pred = model.predict(X_test)
	accuracy = accuracy_score(y_test, y_pred)
	report = classification_report(y_test, y_pred, zero_division=0)

	metrics = {"accuracy": accuracy}
	return model, metrics, report


def save_model(model: CalibratedClassifierCV, file_path: str = "models/model.pkl") -> Path:
	"""Persist trained model to disk for later inference."""
	path = _resolve_model_path(file_path)
	path.parent.mkdir(parents=True, exist_ok=True)
	joblib.dump(model, path)
	return path


def run_training_pipeline(
	asset_type: str = "crypto",
	symbol: str = "BTCUSDT",
	timeframe: str = "1h",
	limit: int = 1000,
	model_path: str = "models/model.pkl",
) -> tuple[CalibratedClassifierCV, dict[str, float], str, Path]:
	"""End-to-end pipeline: dataset -> labels -> train -> evaluate -> save."""
	dataset = prepare_dataset(
		asset_type=asset_type,
		symbol=symbol,
		timeframe=timeframe,
		limit=limit,
	)

	model, metrics, report = train_model(dataset)
	saved_path = save_model(model, model_path)

	return model, metrics, report, saved_path


if __name__ == "__main__":
	_, metrics, report, saved_path = run_training_pipeline(
		asset_type="crypto",
		symbol="BTCUSDT",
		timeframe="1h",
		limit=1000,
		model_path="models/model.pkl",
	)

	print(f"Model accuracy: {metrics['accuracy']:.4f}")
	print("Classification report:")
	print(report)
	print(f"Model saved to: {saved_path}")

#Load Model

def load_model(file_path:str="models/model.pkl"):
	"""Load saved model from disk"""
	path = _resolve_model_path(file_path)

	if not path.exists():
		raise FileNotFoundError(f"Model not found at {file_path}")

	model = joblib.load(path)
	return model

#Predict Signal
def predict_signal(model, df: pd.DataFrame) -> int:
	"""Predict trading signal using the trained model."""
	X = df[FEATURE_COLUMNS].tail(1)

	prediction = model.predict(X)[0]

	return int(prediction)


def adjust_confidence(confidence: float, shrink_factor: float = 0.7) -> float:
	"""Shrink overconfident probabilities toward a neutral 50% baseline."""
	return 0.5 + (confidence - 0.5) * shrink_factor

#Add Confidence

def predict_with_confidence(
	model,
	df: pd.DataFrame
) -> tuple[str, float]:
	"""Predict signal and return probability confidence."""

	X = df[FEATURE_COLUMNS].tail(1)

	prediction = model.predict(X)[0]
	probabilities = model.predict_proba(X)[0]
	classes = list(model.classes_)
	prob_map = {int(cls): float(probabilities[idx]) for idx, cls in enumerate(classes)}

	confidence = prob_map.get(int(prediction), 0.0)

	# Reduce HOLD bias: if HOLD is only slightly stronger than directional classes,
	# emit the strongest directional class instead of staying neutral.
	hold_prob = prob_map.get(0, 0.0)
	buy_prob = prob_map.get(1, 0.0)
	sell_prob = prob_map.get(-1, 0.0)
	best_directional_class = 1 if buy_prob >= sell_prob else -1
	best_directional_prob = max(buy_prob, sell_prob)
	hold_advantage = hold_prob - best_directional_prob

	if int(prediction) == 0:
		adjusted_hold_prob = hold_prob * 0.92
		if best_directional_prob >= adjusted_hold_prob or hold_advantage <= 0.06:
			prediction = best_directional_class
			confidence = best_directional_prob

	if prediction == 1:
		signal = "BUY"
	elif prediction == -1:
		signal = "SELL"
	else:
		signal = "HOLD"

	return signal, confidence