import pandas as pd
import requests
import logging


def fetch_fred_series(series_id, api_key, start_date="2000-01-01"):
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
    }

    try:
        logging.info(f"Fetching FRED series: {series_id}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()["observations"]

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df[series_id] = pd.to_numeric(df["value"], errors="coerce")
        print(df.shape[1])  # Number of columns
        print(df.columns)  # Actual column names
        return df[[series_id]]

    except Exception as e:
        logging.error(f"Failed to fetch {series_id}: {e}")
        raise
