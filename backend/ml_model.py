from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
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


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
	"""Add technical indicators required for feature engineering."""
	result = calculate_rsi(df, period=14, price_col="close")
	result = calculate_ema(result, span=20, price_col="close", output_col="ema_20")
	result = calculate_macd(result, price_col="close")
	return result


def generate_labels(df: pd.DataFrame) -> pd.DataFrame:
	"""Create rule-based labels: 1=buy, -1=sell, 0=hold."""
	result = df.copy()

	buy_rule = (
		(result["rsi"] < 35)
		& (result["close"] > result["ema_20"])
		& (result["macd"] > result["macd_signal"])
	)
	sell_rule = (
		(result["rsi"] > 65)
		& (result["close"] < result["ema_20"])
		& (result["macd"] < result["macd_signal"])
	)

	result["label"] = 0
	result.loc[buy_rule, "label"] = 1
	result.loc[sell_rule, "label"] = -1

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


def train_model(dataset: pd.DataFrame) -> tuple[RandomForestClassifier, dict[str, float], str]:
	"""Train and evaluate a Random Forest classifier."""
	X = dataset[FEATURE_COLUMNS]
	y = dataset["label"]

	X_train, X_test, y_train, y_test = train_test_split(
		X,
		y,
		test_size=0.2,
		random_state=42,
		stratify=y if y.nunique() > 1 else None,
	)

	model = RandomForestClassifier(
		n_estimators=300,
		max_depth=10,
		min_samples_split=5,
		random_state=42,
	)
	model.fit(X_train, y_train)

	y_pred = model.predict(X_test)
	accuracy = accuracy_score(y_test, y_pred)
	report = classification_report(y_test, y_pred, zero_division=0)

	metrics = {"accuracy": accuracy}
	return model, metrics, report


def save_model(model: RandomForestClassifier, file_path: str = "models/model.pkl") -> Path:
	"""Persist trained model to disk for later inference."""
	path = Path(file_path)
	path.parent.mkdir(parents=True, exist_ok=True)
	joblib.dump(model, path)
	return path


def run_training_pipeline(
	asset_type: str = "crypto",
	symbol: str = "BTCUSDT",
	timeframe: str = "1h",
	limit: int = 1000,
	model_path: str = "models/model.pkl",
) -> tuple[RandomForestClassifier, dict[str, float], str, Path]:
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

def load_model(file_path:str="models/model.pkl") -> RandomForestClassifier:
	"""Load saved model from disk"""
	path = Path(file_path)

	if not path.exists():
		raise FileNotFoundError(f"Model not found at {file_path}")

	model = joblib.load(path)
	return model

#Predict Signal
def predict_signal(model: RandomForestClassifier, df: pd.DataFrame) -> int:
	"""Predict trading signal using the trained model."""
	X = df[FEATURE_COLUMNS].tail(1)

	prediction = model.predict(X)[0]

	return int(prediction)

#Add Confidence

def predict_with_confidence(
	model: RandomForestClassifier,
	df: pd.DataFrame
) -> tuple[str, float]:
	"""Predict signal and return probability confidence."""

	X = df[FEATURE_COLUMNS].tail(1)

	prediction = model.predict(X)[0]

	probabilities = model.predict_proba(X)[0]

	confidence = float(max(probabilities))

	if prediction == 1:
		signal = "BUY"
	elif prediction == -1:
		signal = "SELL"
	else:
		signal = "HOLD"

	return signal, confidence