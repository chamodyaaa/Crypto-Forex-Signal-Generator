import pandas as pd

def generate_signal(df:pd.DataFrame) -> dict:
    if df.empty:
        raise ValueError("DataFrame is empty")
    
    latest=df.iloc[-1]

    price=latest["close"]
    rsi=latest["rsi"]
    ema=latest["ema_20"]
    macd=latest["macd"]
    macd_signal=latest["macd_signal"]

    signal="HOLD"
    reason="No clear signal"

    #BUY CONDITIONS

    if rsi<30 and macd>macd_signal and price > ema:
        signal = "BUY"
        reason="Oversold RSI + Bullish MACD + Price above EMA"

    #SELL CONDITION

    elif rsi >70 and macd<macd_signal and price<ema:
        signal="SELL"
        reason="Overbought RSI + Bearish MACD + Price below EMA"

    return{
         "signal": signal,
        "price": round(price, 2),
        "rsi": round(rsi, 2),
        "ema": round(ema, 2),
        "macd": round(macd, 4),
        "macd_signal": round(macd_signal, 4),
        "reason": reason
    }