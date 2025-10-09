import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()  # ✅ loads .env from project root


class AlphaVantageIngestor:
    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("Missing ALPHA_VANTAGE_API_KEY in environment")

    def fetch(self, symbol: str, label: str, timeout: int = 15) -> pd.DataFrame:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "full",
            "apikey": self.api_key,
            "datatype": "json",
        }

        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            j = r.json()
        except Exception as e:
            print(f"[ERROR] Request failed for {label} ({symbol}): {e}")
            return None

        ts = j.get("Time Series (Daily)")
        if not ts:
            print(f"[ERROR] No time series returned for {label} ({symbol}): {j}")
            return None

        df = pd.DataFrame.from_dict(ts, orient="index")
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df = df.rename(columns={"4. close": label})
        df[label] = pd.to_numeric(df[label], errors="coerce")
        df = df[[label]].dropna()
        df.index.name = "date"
        return df
