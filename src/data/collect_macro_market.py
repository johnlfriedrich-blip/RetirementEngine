import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv
import os

def fetch_macro_market_data():
    load_dotenv()
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise ValueError("FRED_API_KEY not found in .env")

    fred = Fred(api_key=api_key)
    series_map = {
        "SP500": "SP500",
        "VIX": "VIXCLS",
        "10Y": "GS10",
    }

    data = {}
    for label, fred_id in series_map.items():
        try:
            s = fred.get_series(fred_id)
            df = s.to_frame(name=label)
            df.index.name = "date"
            df = df.resample("ME").last().dropna()
            data[label] = df
        except Exception as e:
            print(f"[ERROR] Failed to fetch {label} ({fred_id}): {e}")

    if not data:
        print("[ERROR] No macro market data collected.")
        return pd.DataFrame()

    merged = pd.concat(data.values(), axis=1)
    return merged.dropna()

if __name__ == "__main__":
    df = fetch_macro_market_data()
    if not df.empty:
        df.to_csv("data/macro_market.csv")
        print("Saved macro market data to data/macro_market.csv")
        print(df.tail())
    else:
        print("No data saved. Macro market CSV would be empty.")