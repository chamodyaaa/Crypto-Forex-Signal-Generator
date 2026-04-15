import pandas as pd
import requests
from binance.client import Client
from dotenv import load_dotenv
import os

#Binance client
client=Client()

# load .env file
load_dotenv()

API_KEY = os.getenv("TWELVE_DATA_API_KEY")

#Fetch Crypto Data

def fetch_crypto_data(symbol="BTCUSDT", timeframe="1h",limit=500):
    klines=client.get_klines(
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
    url = (
        f"https://api.twelvedata.com/time_series?symbol={symbol}"
        f"&interval={timeframe}&outputsize={limit}&apikey={API_KEY}"
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