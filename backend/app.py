from data_fetcher import get_market_data
from indicators import calculate_rsi, calculate_ema, calculate_macd
from utils import validate_indicators
from strategy import generate_signal

def process_asset(asset_type,symbol,timeframe):
    print(f"\nFetching data for {symbol} ({asset_type})...")

    df=get_market_data(
        asset_type=asset_type,
        symbol=symbol,
        timeframe=timeframe
    
    )

    print("Latest Market Data:")
    print(df.tail())

    print("\nCalculating indicators...")

    df = calculate_rsi(df)
    df = calculate_ema(df)
    df = calculate_macd(df)

    validate_indicators(df)

    print("\nGenerating Trading Signal...")
    signal=generate_signal(df)

    print("Signal Result:")
    print(signal)

    return signal

if __name__=="__main__":

    timeframe="1h"
   
    # Test Crypto
    crypto_signal = process_asset(
        asset_type="crypto",
        symbol="BTCUSDT",
        timeframe=timeframe
    )

    # Test Forex
    forex_signal = process_asset(
        asset_type="forex",
        symbol="EUR/USD",
        timeframe=timeframe
    )

    print("\nFinal Results")
    print("Crypto Signal:", crypto_signal)
    print("Forex Signal:", forex_signal)
   



