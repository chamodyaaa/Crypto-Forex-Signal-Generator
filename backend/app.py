from data_fetcher import get_market_data

# Test Crypto
df = get_market_data(
    asset_type="crypto",
    symbol="BTCUSDT",
    timeframe="1h"
)

print(df.tail())


#Test Forex
df = get_market_data(
    asset_type="forex",
    symbol="EUR/USD",
    timeframe="1h"
)

print(df.tail())