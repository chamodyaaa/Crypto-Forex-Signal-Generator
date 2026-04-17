def validate_indicators(df):

    print("\n===== Indicator Validation =====")

    print("\nColumns in DataFrame:")
    print(df.columns)

    print("\nLast 5 RSI values:")
    print(df["rsi"].tail())

    print("\nLast 5 EMA values:")
    print(df["ema_20"].tail())

    print("\nLast 5 MACD values:")
    print(df["macd"].tail())

    print("\nLast 5 MACD Signal values:")
    print(df["macd_signal"].tail())

    print("\nLast 5 MACD Histogram values:")
    print(df["macd_histogram"].tail())

    print("\nValidation Finished")
    