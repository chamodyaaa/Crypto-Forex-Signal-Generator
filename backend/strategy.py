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
    rule_confidence = 0.0  # Confidence for rule-based signal

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
        # Calculate confidence based on RSI extremeness and price vs EMA
        rsi_strength = abs(rsi - 50) / 50  # 0-1 scale, stronger at extremes
        price_ema_strength = abs(price - ema) / ema if ema != 0 else 0.1  # Strength of price separation
        rule_confidence = min(80, (rsi_strength + price_ema_strength) * 50)  # Cap at 80%
    elif any(sell_conditions):
        signal = "SELL"
        reason = f"RSI: {rsi:.2f} | MACD Bearish | EMA Setup"
        # Calculate confidence based on RSI extremeness and price vs EMA
        rsi_strength = abs(rsi - 50) / 50  # 0-1 scale, stronger at extremes
        price_ema_strength = abs(price - ema) / ema if ema != 0 else 0.1  # Strength of price separation
        rule_confidence = min(80, (rsi_strength + price_ema_strength) * 50)  # Cap at 80%
    else:
        reason = f"Neutral Signal (RSI: {rsi:.2f})"
        rule_confidence = 30  # Low confidence for HOLD signals

    # ML MODEL PREDICTION
    try:
        model = load_model()
        ml_signal, raw_confidence = predict_with_confidence(model, df)
        confidence = adjust_confidence(raw_confidence)
        # Convert to 0-100 scale for consistency with rule_confidence
        ml_confidence = confidence * 100
        print(f"ML Model loaded successfully. Raw confidence: {raw_confidence:.4f}, Adjusted: {confidence:.4f}, ML Confidence %: {ml_confidence:.2f}")
    except FileNotFoundError:
        print("WARNING: Model not found. Using rule-based confidence only.")
        ml_signal = signal  # Use rule-based signal as fallback
        ml_confidence = 0  # No ML confidence if model not available
        confidence = 0
    except Exception as e:
        print(f"ERROR loading ML model: {e}. Using rule-based confidence only.")
        ml_signal = signal  # Use rule-based signal as fallback
        ml_confidence = 0  # No ML confidence if model fails
        confidence = 0

    # COMBINE SIGNALS - Merge rule-based and ML outputs into final decision
    final_signal = "HOLD"
    combined_reason = ""
    
    if signal == ml_signal:
        # Both signals agree - high confidence
        final_signal = signal
        combined_reason = f"Both systems agree on {signal}"
        # Average both confidences with boost for agreement
        combined_confidence = min(100, (rule_confidence + ml_confidence) / 2 + 15)
    else:
        # Signals disagree - use weighted approach
        if ml_confidence > 60:
            # ML model is confident - prioritize ML signal
            final_signal = ml_signal
            combined_reason = f"ML system ({ml_confidence:.0f}% confidence) overrides rule-based ({signal} {rule_confidence:.0f}%)"
            combined_confidence = ml_confidence * 0.7 + rule_confidence * 0.3
        elif ml_confidence > 40:
            # Mixed confidence - stick with rule-based but note ML disagreement
            final_signal = signal
            combined_reason = f"Rule-based {signal} ({rule_confidence:.0f}%) vs ML {ml_signal} ({ml_confidence:.0f}%)"
            combined_confidence = rule_confidence * 0.6 + ml_confidence * 0.4
        else:
            # ML not confident - prioritize rule-based (if it's confident enough)
            if rule_confidence > 30:
                final_signal = signal
                combined_reason = f"Rule-based {signal} ({rule_confidence:.0f}% confidence) - ML weak ({ml_confidence:.0f}%)"
                combined_confidence = rule_confidence * 0.8 + ml_confidence * 0.2
            else:
                # Both weak - default to HOLD or safer signal
                final_signal = "HOLD"
                combined_reason = f"Both systems weak - Rule: {signal} ({rule_confidence:.0f}%), ML: {ml_signal} ({ml_confidence:.0f}%) - HOLD recommended"
                combined_confidence = (rule_confidence + ml_confidence) / 2
            combined_confidence = rule_confidence * 0.8 + confidence * 0.2

    return {
        "rule_signal": signal,
        "rule_confidence": round(rule_confidence, 2),
        "ml_signal": ml_signal,
        "ml_confidence": round(ml_confidence, 2),
        "final_signal": final_signal,
        "combined_confidence": round(min(100, combined_confidence), 2),
        "price": float(round(price, 2)),
        "rsi": float(round(rsi, 2)),
        "ema": float(round(ema, 2)),
        "macd": float(round(macd, 4)),
        "macd_signal": float(round(macd_signal, 4)),
        "reason": reason,
        "combined_reason": combined_reason
    }