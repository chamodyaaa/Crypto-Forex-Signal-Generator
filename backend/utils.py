import numpy as np


def validate_indicators(df, min_rows=50):
    """Validate presence and quality of indicator columns before signal generation."""
    required_cols = ["close", "rsi", "ema_20", "macd", "macd_signal", "macd_histogram"]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing indicator columns: {missing_cols}")

    if len(df) < min_rows:
        raise ValueError(f"Insufficient rows for robust indicators: {len(df)} available, need at least {min_rows}")

    numeric_view = df[required_cols].tail(10)
    if numeric_view.isna().any().any():
        raise ValueError("Recent indicator rows contain missing values")

    if not np.isfinite(numeric_view.to_numpy()).all():
        raise ValueError("Recent indicator rows contain non-finite values")

    return True
    