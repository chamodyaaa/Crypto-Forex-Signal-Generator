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
    ema_20 = latest["ema_20"]
    ema_50 = latest["ema_50"]
    macd = latest["macd"]
    macd_signal = latest["macd_signal"]

    signal = "HOLD"
    reason = "No clear signal"
    rule_confidence = 0.0  # Confidence for rule-based signal
    macd_gap = macd - macd_signal
    ema_gap_pct = ((price - ema_20) / ema_20) if ema_20 else 0.0
    ema50_gap_pct = ((price - ema_50) / ema_50) if ema_50 else 0.0
    ema_trend_gap_pct = ((ema_20 - ema_50) / ema_50) if ema_50 else 0.0

    # RULE BASED LOGIC with improved thresholds
    # BUY signals (multiple conditions)
    buy_conditions = [
        rsi <= 35 and macd_gap > -0.0003 and ema50_gap_pct > -0.01,  # Avoid deep long-term bearish regimes
        rsi < 48 and ema_gap_pct > -0.001 and macd_gap > 0 and ema_trend_gap_pct > -0.003,  # Slightly below EMA20 is allowed if EMA20~EMA50 and momentum improves
        48 <= rsi <= 65 and ema_gap_pct > 0.0005 and macd_gap > 0 and ema_trend_gap_pct > 0,  # Continuation when short trend is above long trend
    ]
    
    # SELL signals (multiple conditions)
    sell_conditions = [
        rsi >= 65 and macd_gap < 0.0003 and ema50_gap_pct < 0.01,  # Avoid deep long-term bullish regimes
        rsi > 52 and ema_gap_pct < 0.001 and macd_gap < 0 and ema_trend_gap_pct < 0.003,  # Slightly above EMA20 is allowed if EMA20~EMA50 and momentum weakens
        35 <= rsi <= 52 and ema_gap_pct < -0.0005 and macd_gap < 0 and ema_trend_gap_pct < 0,  # Continuation when short trend is below long trend
    ]

    if any(buy_conditions):
        signal = "BUY"
        reason = (
            f"RSI: {rsi:.2f} | MACD Bullish (gap {macd_gap:.4f}) | "
            f"EMA20/EMA50 Bullish ({ema_trend_gap_pct * 100:.2f}%)"
        )
        # Calculate confidence based on RSI extremeness and EMA alignment
        rsi_strength = abs(rsi - 50) / 50  # 0-1 scale, stronger at extremes
        price_ema_strength = abs(price - ema_20) / ema_20 if ema_20 != 0 else 0.1  # Strength of price separation from EMA20
        trend_strength = min(0.3, abs(ema_trend_gap_pct) * 10)
        momentum_strength = min(0.4, abs(macd_gap))
        rule_confidence = min(85, (rsi_strength + price_ema_strength + trend_strength + momentum_strength) * 45)
    elif any(sell_conditions):
        signal = "SELL"
        reason = (
            f"RSI: {rsi:.2f} | MACD Bearish (gap {macd_gap:.4f}) | "
            f"EMA20/EMA50 Bearish ({ema_trend_gap_pct * 100:.2f}%)"
        )
        # Calculate confidence based on RSI extremeness and EMA alignment
        rsi_strength = abs(rsi - 50) / 50  # 0-1 scale, stronger at extremes
        price_ema_strength = abs(price - ema_20) / ema_20 if ema_20 != 0 else 0.1  # Strength of price separation from EMA20
        trend_strength = min(0.3, abs(ema_trend_gap_pct) * 10)
        momentum_strength = min(0.4, abs(macd_gap))
        rule_confidence = min(85, (rsi_strength + price_ema_strength + trend_strength + momentum_strength) * 45)
    else:
        # Mild trend fallback: reduce excessive HOLD when momentum and trend are aligned.
        if macd_gap > 0 and ema_gap_pct > 0 and ema_trend_gap_pct >= 0 and rsi >= 52:
            signal = "BUY"
            reason = (
                f"Mild bullish trend fallback (RSI: {rsi:.2f}, MACD gap: {macd_gap:.4f}, "
                f"EMA20-EMA50: {ema_trend_gap_pct * 100:.2f}%)"
            )
            rule_confidence = 44
        elif macd_gap < 0 and ema_gap_pct < 0 and ema_trend_gap_pct <= 0 and rsi <= 48:
            signal = "SELL"
            reason = (
                f"Mild bearish trend fallback (RSI: {rsi:.2f}, MACD gap: {macd_gap:.4f}, "
                f"EMA20-EMA50: {ema_trend_gap_pct * 100:.2f}%)"
            )
            rule_confidence = 44
        else:
            reason = f"Neutral Signal (RSI: {rsi:.2f})"
            rule_confidence = 35  # Slightly higher neutral confidence to avoid over-penalizing hold context

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
        # If rule is neutral but ML is confidently directional, allow controlled ML override.
        if signal == "HOLD" and ml_signal in ["BUY", "SELL"] and ml_confidence >= 58:
            final_signal = ml_signal
            combined_reason = f"Rule neutral, ML directional ({ml_confidence:.0f}%)"
            combined_confidence = ml_confidence * 0.75 + rule_confidence * 0.25
        # Prevent HOLD bias: directional rule signals should not be easily overridden by ML HOLD.
        elif signal in ["BUY", "SELL"] and ml_signal == "HOLD":
            if rule_confidence >= 25 or ml_confidence < 65:
                final_signal = signal
                combined_reason = (
                    f"Directional rule preserved ({signal} {rule_confidence:.0f}%) "
                    f"despite ML HOLD ({ml_confidence:.0f}%)"
                )
                combined_confidence = rule_confidence * 0.7 + ml_confidence * 0.3
            else:
                final_signal = "HOLD"
                combined_reason = (
                    f"ML HOLD strongly dominant ({ml_confidence:.0f}%) over weak rule "
                    f"{signal} ({rule_confidence:.0f}%)"
                )
                combined_confidence = ml_confidence * 0.75 + rule_confidence * 0.25
        # Signals disagree in direction - use weighted approach.
        elif ml_confidence > 60:
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

    return {
        "rule_signal": signal,
        "rule_confidence": round(rule_confidence, 2),
        "ml_signal": ml_signal,
        "ml_confidence": round(ml_confidence, 2),
        "final_signal": final_signal,
        "combined_confidence": round(min(100, combined_confidence), 2),
        "price": float(round(price, 2)),
        "rsi": float(round(rsi, 2)),
        "ema": float(round(ema_20, 2)),
        "ema_20": float(round(ema_20, 2)),
        "ema_50": float(round(ema_50, 2)),
        "macd": float(round(macd, 4)),
        "macd_signal": float(round(macd_signal, 4)),
        "reason": reason,
        "combined_reason": combined_reason
    }