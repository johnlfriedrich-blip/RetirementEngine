import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class FinnhubIngestor:
    def __init__(self):
        self.api_key = os.getenv("FINNHUB_KEY")
        if not self.api_key:
            raise ValueError("Missing FINNHUB_KEY in environment")

    def fetch(self, symbol: str, label: str, days: int = 100) -> pd.DataFrame:
        end = datetime.now()
        start = end - timedelta(days=days)
        url = "https://finnhub.io/api/v1/stock/candle"
        params = {
            "symbol": symbol,
            "resolution": "D",
            "from": int(start.timestamp()),
            "to": int(end.timestamp()),
            "token": self.api_key,
        }

        try:
            r = requests.get(url, params=params)
            r.raise_for_status()
            j = r.json()
        except Exception as e:
            print(f"[ERROR] Request failed for {label} ({symbol}): {e}")
            return None

        if j.get("s") != "ok" or "c" not in j:
            print(f"[ERROR] No candle data returned for {label} ({symbol}): {j}")
            return None

        df = pd.DataFrame({"date": pd.to_datetime(j["t"], unit="s"), label: j["c"]})
        df = df.set_index("date").sort_index()
        df[label] = pd.to_numeric(df[label], errors="coerce")
        df = df[[label]].dropna()
        return df
