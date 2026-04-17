import pandas as pd
import requests
from binance.client import Client
from dotenv import load_dotenv
import os

# load .env file
load_dotenv()

# Lazy-loaded Binance client
_client = None

def get_binance_client():
    global _client
    if _client is None:
        try:
            _client = Client()
        except Exception as e:
            print(f"Warning: Failed to initialize Binance client: {e}")
            print("Running in offline mode")
            _client = None
    return _client

client = None  # Will be initialized on first use

API_KEY = os.getenv("TWELVE_DATA_API_KEY")

#Fetch Crypto Data

def fetch_crypto_data(symbol="BTCUSDT", timeframe="1h",limit=500):
    binance_client = get_binance_client()
    if binance_client is None:
        raise Exception("Binance client not available - network connection failed")
    
    klines=binance_client.get_klines(
        symbol=symbol,
        interval=timeframe,
        limit=limit
    )

    df=pd.DataFrame(klines,columns=[
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "trades",
        "taker_buy_base",
        "taker_buy_quote",
        "ignore"
    ])

    df=df[["timestamp","open","high","low","close","volume"]]

    df["timestamp"]=pd.to_datetime(df["timestamp"],unit="ms")

    df[["open","high","low","close","volume"]]=df[["open","high","low","close","volume"]].astype(float)

    return df

#Fetch Forex Data
def fetch_forex_data(symbol, timeframe="1h", limit=500):
    # Convert timeframe to Twelve Data API format
    forex_timeframe = convert_timeframe_for_forex(timeframe)
    
    url = (
        f"https://api.twelvedata.com/time_series?symbol={symbol}"
        f"&interval={forex_timeframe}&outputsize={limit}&apikey={API_KEY}"
    )
    response = requests.get(url)
    data = response.json()

    if "values" not in data:
        raise Exception(f"Error fetching forex data: {data}")
     
    df=pd.DataFrame(data["values"])

    # Rename column
    df.rename(columns={"datetime":"timestamp"}, inplace=True)

    # Convert timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Ensure correct column order (forex doesn't have volume)
    df = df[["timestamp","open","high","low","close"]]

    # Convert numeric columns
    df[["open","high","low","close"]] = df[
        ["open","high","low","close"]
    ].astype(float)

    # Sort ascending
    df = df.sort_values("timestamp")

    return df



# Timeframe conversion for Forex API
def convert_timeframe_for_forex(timeframe):
    """Convert timeframe from crypto format to Twelve Data forex format."""
    timeframe_map = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "4h": "4h",
        "1d": "1day",
        "1w": "1week",
    }
    return timeframe_map.get(timeframe, timeframe)


# Main Function 


def get_market_data(asset_type, symbol, timeframe):

    """
    asset_type : 'crypto' or 'forex'
    symbol     : BTCUSDT / XRPUSDT / EUR/USD
    timeframe  : 1m / 5m / 1h / 4h / 1d
    """

    if asset_type.lower() == "crypto":
        return fetch_crypto_data(symbol, timeframe)

    elif asset_type.lower() == "forex":
        return fetch_forex_data(symbol, timeframe)

    else:
        raise ValueError("asset_type must be 'crypto' or 'forex'")