import pandas as pd


def calculate_rsi(df: pd.DataFrame, period: int = 14, price_col: str = "close") -> pd.DataFrame:
	"""Return a copy of the DataFrame with an RSI column added."""
	if price_col not in df.columns:
		raise ValueError(f"Missing required column: {price_col}")
	if period <= 0:
		raise ValueError("period must be a positive integer")

	result = df.copy()
	prices = result[price_col].astype(float)

	delta = prices.diff()
	gain = delta.clip(lower=0)
	loss = -delta.clip(upper=0)

	avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
	avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

	rs = avg_gain / avg_loss
	result["rsi"] = 100 - (100 / (1 + rs))
	result["rsi"] = result["rsi"].fillna(0)

	return result


def calculate_ema(
	df: pd.DataFrame,
	span: int = 20,
	price_col: str = "close",
	output_col: str | None = None,
) -> pd.DataFrame:
	"""Return a copy of the DataFrame with an EMA column added."""
	if price_col not in df.columns:
		raise ValueError(f"Missing required column: {price_col}")
	if span <= 0:
		raise ValueError("span must be a positive integer")

	result = df.copy()
	col_name = output_col or f"ema_{span}"
	prices = result[price_col].astype(float)
	result[col_name] = prices.ewm(span=span, adjust=False).mean()

	return result


def calculate_macd(
	df: pd.DataFrame,
	price_col: str = "close",
	fast_span: int = 12,
	slow_span: int = 26,
	signal_span: int = 9,
	macd_col: str = "macd",
	signal_col: str = "macd_signal",
	histogram_col: str = "macd_histogram",
) -> pd.DataFrame:
	"""Return a copy of the DataFrame with MACD, signal, and histogram columns added."""
	if price_col not in df.columns:
		raise ValueError(f"Missing required column: {price_col}")
	if fast_span <= 0 or slow_span <= 0 or signal_span <= 0:
		raise ValueError("fast_span, slow_span, and signal_span must be positive integers")
	if fast_span >= slow_span:
		raise ValueError("fast_span must be smaller than slow_span")

	result = df.copy()
	prices = result[price_col].astype(float)

	fast_ema = prices.ewm(span=fast_span, adjust=False).mean()
	slow_ema = prices.ewm(span=slow_span, adjust=False).mean()

	result[macd_col] = fast_ema - slow_ema
	result[signal_col] = result[macd_col].ewm(span=signal_span, adjust=False).mean()
	result[histogram_col] = result[macd_col] - result[signal_col]

	return result