# retirement_engine/av_loader.py
import os
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
CACHE_DIR = "data/cache"


def fetch_daily_prices(tickers):
    """
    Fetch daily adjusted close prices for a list of tickers from Alpha Vantage.
    Uses a file-based cache to avoid redundant API calls.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    all_data = {}
    ts = TimeSeries(key=API_KEY, output_format='pandas')

    for ticker in tickers:
        cache_file = os.path.join(CACHE_DIR, f"{ticker}.csv")
        if os.path.exists(cache_file):
            print(f"Loading {ticker} data from cache...")
            all_data[ticker] = pd.read_csv(cache_file, index_col='date', parse_dates=True)
        else:
            print(f"Fetching {ticker} data from Alpha Vantage...")
            data, _ = ts.get_daily_adjusted(symbol=ticker, outputsize='full')
            data = data.rename(columns={'5. adjusted close': 'adjusted_close'})
            data.to_csv(cache_file)
            all_data[ticker] = data

    # Combine all data into a single DataFrame
    combined_df = pd.DataFrame({ticker: df['adjusted_close'] for ticker, df in all_data.items()})
    combined_df = combined_df.dropna()
    return combined_df
