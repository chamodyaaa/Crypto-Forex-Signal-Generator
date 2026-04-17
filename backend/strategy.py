import pandas as pd
from ml_model import adjust_confidence, load_model, predict_with_confidence, add_indicators

def generate_signal(df: pd.DataFrame) -> dict:

    if df.empty:
        raise ValueError("DataFrame is empty")

    # add indicators if not already present
    df = add_indicators(df)

    latest = df.iloc[-1]

    price = latest["close"]
    rsi = latest["rsi"]
    ema = latest["ema_20"]
    macd = latest["macd"]
    macd_signal = latest["macd_signal"]

    signal = "HOLD"
    reason = "No clear signal"

    # RULE BASED LOGIC with improved thresholds
    # BUY signals (multiple conditions)
    buy_conditions = [
        rsi < 35 and macd > macd_signal,  # Oversold + Bullish MACD
        rsi < 40 and price > ema and macd > macd_signal,  # Approaching oversold with bullish setup
        rsi > 50 and rsi < 60 and macd > macd_signal and price > ema,  # Neutral RSI with bullish technicals
    ]
    
    # SELL signals (multiple conditions)
    sell_conditions = [
        rsi > 65 and macd < macd_signal,  # Overbought + Bearish MACD
        rsi > 60 and price < ema and macd < macd_signal,  # Approaching overbought with bearish setup
        rsi > 40 and rsi < 50 and macd < macd_signal and price < ema,  # Neutral RSI with bearish technicals
    ]

    if any(buy_conditions):
        signal = "BUY"
        reason = f"RSI: {rsi:.2f} | MACD Bullish | EMA Setup"
    elif any(sell_conditions):
        signal = "SELL"
        reason = f"RSI: {rsi:.2f} | MACD Bearish | EMA Setup"
    else:
        reason = f"Neutral Signal (RSI: {rsi:.2f})"

    # ML MODEL PREDICTION
    try:
        model = load_model()
        ml_signal, raw_confidence = predict_with_confidence(model, df)
        confidence = adjust_confidence(raw_confidence)
    except FileNotFoundError:
        print("WARNING: Model not found. Train the model first using: python ml_model.py")
        ml_signal = signal  # Use rule-based signal as fallback
        raw_confidence = 0.0
        confidence = 0.0

    return {
        "rule_signal": signal,
        "ml_signal": ml_signal,
        "confidence": round(confidence * 100, 2),
        "model_confidence": round(raw_confidence * 100, 2),
        "price": float(round(price, 2)),
        "rsi": float(round(rsi, 2)),
        "ema": float(round(ema, 2)),
        "macd": float(round(macd, 4)),
        "macd_signal": float(round(macd_signal, 4)),
        "reason": reason
    }