from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from data_fetcher import get_market_data
from indicators import calculate_ema, calculate_macd, calculate_rsi


FEATURE_COLUMNS = [
	"close",
	"rsi",
	"ema_20",
	"macd",
	"macd_signal",
	"macd_histogram",
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
	result = calculate_macd(result, price_col="close")
	return result


def generate_labels(df: pd.DataFrame) -> pd.DataFrame:
	"""Create rule-based labels: 1=buy, -1=sell, 0=hold."""
	result = df.copy()

	# More flexible BUY conditions - easier to trigger
	buy_rule = (
		((result["rsi"] < 40) & (result["macd"] > result["macd_signal"])) |  # RSI approaching oversold + bullish MACD
		((result["rsi"] < 30) & (result["close"] > result["ema_20"])) |  # Oversold + price above EMA
		((result["rsi"] > 50) & (result["rsi"] < 60) & (result["macd"] > result["macd_signal"]) & (result["close"] > result["ema_20"]))  # Neutral RSI but bullish technicals
	)
	
	# More flexible SELL conditions - easier to trigger
	sell_rule = (
		((result["rsi"] > 60) & (result["macd"] < result["macd_signal"])) |  # RSI approaching overbought + bearish MACD
		((result["rsi"] > 70) & (result["close"] < result["ema_20"])) |  # Overbought + price below EMA
		((result["rsi"] > 40) & (result["rsi"] < 50) & (result["macd"] < result["macd_signal"]) & (result["close"] < result["ema_20"]))  # Neutral RSI but bearish technicals
	)

	result["label"] = 0  # Default to HOLD
	result.loc[sell_rule, "label"] = -1  # Apply SELL first
	result.loc[buy_rule & ~sell_rule, "label"] = 1  # Apply BUY if not already SELL

	return result


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
	X = dataset[FEATURE_COLUMNS]
	y = dataset["label"]

	X_train, X_test, y_train, y_test = train_test_split(
		X,
		y,
		test_size=0.2,
		random_state=42,
		stratify=y if y.nunique() > 1 else None,
	)

	# Calculate class weights to handle imbalance
	from sklearn.utils.class_weight import compute_class_weight
	import numpy as np
	
	unique_classes = np.array(sorted(y_train.unique()))
	class_weights = compute_class_weight(
		'balanced',
		classes=unique_classes,
		y=y_train
	)
	class_weight_dict = dict(zip(unique_classes, class_weights))

	base_model = RandomForestClassifier(
		n_estimators=300,
		max_depth=10,
		min_samples_split=5,
		random_state=42,
		class_weight=class_weight_dict,  # Apply class weights
	)
	class_counts = y_train.value_counts()
	min_class_count = int(class_counts.min()) if not class_counts.empty else 0

	if min_class_count >= 2:
		cv_folds = min(5, min_class_count)
		model = CalibratedClassifierCV(
			estimator=base_model,
			method="sigmoid",
			cv=cv_folds,
		)
		model.fit(X_train, y_train)
	else:
		base_model.fit(X_train, y_train)
		model = base_model

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
	
	# Get the index of the predicted class
	class_index = list(model.classes_).index(prediction)
	# Get the probability for the predicted class
	confidence = float(probabilities[class_index])

	if prediction == 1:
		signal = "BUY"
	elif prediction == -1:
		signal = "SELL"
	else:
		signal = "HOLD"

	return signal, confidence