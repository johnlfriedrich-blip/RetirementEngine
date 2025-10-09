# file: src/data/collect_raw_macro.py

import os
import logging
from dotenv import load_dotenv
from src.data.ingestors.fetch_fred import fetch_fred_series

load_dotenv()
api_key = os.getenv("FRED_API_KEY")


def collect_raw_macro(api_key):
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting raw macro collection")

    series_map = {
        "GDP": "GDP",
        "Inflation": "CPIAUCSL",
        "Unemployment": "UNRATE",
        "SP500": "SP500",
        "VIX": "VIXCLS",
        "10Y_Treasury": "GS10",
        "2Y_Treasury": "DGS2",
        "FedFunds": "FEDFUNDS",
    }

    for label, fred_id in series_map.items():
        logging.info(f"Fetching {label} ({fred_id})")
        df = fetch_fred_series(fred_id, api_key)
        df.to_csv(f"data/raw/{label}.csv", index=True)
        logging.info(f"Saved {label} to data/raw/{label}.csv")


if __name__ == "__main__":
    collect_raw_macro(api_key)
