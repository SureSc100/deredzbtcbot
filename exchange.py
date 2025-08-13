import os, pandas as pd
from binance.spot import Spot as SpotClient

def get_client():
    key = os.getenv("BINANCE_API_KEY", "").strip()
    secret = os.getenv("BINANCE_API_SECRET", "").strip()
    use_testnet = os.getenv("BINANCE_USE_TESTNET", "true").lower() == "true"
    base_url = "https://testnet.binance.vision" if use_testnet else None
    if key and secret:
        return SpotClient(key=key, secret=secret, base_url=base_url)
    else:
        return SpotClient(base_url=base_url)

def fetch_klines(symbol: str, interval: str="15m", limit: int=500):
    client = get_client()
    data = client.klines(symbol, interval, limit=limit)
    cols = ["open_time","open","high","low","close","volume","close_time",
            "qav","trades","taker_base","taker_quote","ignore"]
    df = pd.DataFrame(data, columns=cols)
    for c in ["open","high","low","close","volume"]:
        df[c] = df[c].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    return df
