from data_fetcher import get_market_data
from indicators import calculate_rsi, calculate_ema, calculate_macd
from utils import validate_indicators
from strategy import generate_signal
import sys

def process_asset(asset_type, symbol, timeframe):
    print(f"\nFetching data for {symbol} ({asset_type})...")

    df = get_market_data(
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
    signal = generate_signal(df)

    print("Signal Result:")
    print(signal)

    return signal

def get_user_assets():
    """Get trading pairs from user input or command-line arguments."""
    print("\n" + "="*60)
    print("CRYPTO-FOREX SIGNAL GENERATOR")
    print("="*60)
    print("\nCommon symbols:")
    print("Crypto: BTCUSDT, ETHUSDT, BNBUSDT, ADAUSDT, XRPUSDT")
    print("Forex: EUR/USD, GBP/USD, USD/JPY, USD/CHF")
    
    assets = []
    
    # If command-line args provided, use them
    if len(sys.argv) > 1:
        print(f"\nUsing command-line arguments: {' '.join(sys.argv[1:])}")
        for arg in sys.argv[1:]:
            if "/" in arg.upper():  # Forex pair
                assets.append(("forex", arg.upper()))
            else:  # Crypto pair
                assets.append(("crypto", arg.upper()))
    else:
        # Interactive mode
        try:
            # Get crypto pairs
            crypto_input = input("\nEnter crypto pair(s) (comma-separated, or press Enter to skip): ").strip()
            if crypto_input:
                for symbol in crypto_input.split(","):
                    assets.append(("crypto", symbol.strip().upper()))
            
            # Get forex pairs
            forex_input = input("Enter forex pair(s) (comma-separated, or press Enter to skip): ").strip()
            if forex_input:
                for symbol in forex_input.split(","):
                    assets.append(("forex", symbol.strip().upper()))
        except EOFError:
            pass  # If EOF, use defaults
    
    # Default to BTC if no input
    if not assets:
        print("\nNo input provided. Using default pairs: BTC and EUR/USD")
        assets = [("crypto", "BTCUSDT"), ("forex", "EUR/USD")]
    
    return assets

if __name__ == "__main__":
    timeframe = "1h"
    
    # Get trading pairs from user
    trading_pairs = get_user_assets()
    
    all_signals = {}
    
    # Process each trading pair
    for asset_type, symbol in trading_pairs:
        try:
            signal = process_asset(
                asset_type=asset_type,
                symbol=symbol,
                timeframe=timeframe
            )
            all_signals[f"{symbol} ({asset_type})"] = signal
        except Exception as e:
            print(f"ERROR processing {symbol}: {str(e)}")
            all_signals[f"{symbol} ({asset_type})"] = {"error": str(e)}

    # Display final results
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    for pair, signal_data in all_signals.items():
        print(f"\n{pair}:")
        if "error" in signal_data:
            print(f"  ERROR: {signal_data['error']}")
        else:
            print(f"  Signal: {signal_data['rule_signal']}")
            print(f"  ML Signal: {signal_data['ml_signal']}")
            print(f"  Confidence: {signal_data['confidence']}%")
            print(f"  Price: {signal_data['price']}")
            print(f"  RSI: {signal_data['rsi']}")
            print(f"  EMA (20): {signal_data['ema']}")
            print(f"  MACD: {signal_data['macd']}")
            print(f"  Reason: {signal_data['reason']}")
   



