import os
from dotenv import load_dotenv
from alpha_vantage.timeseries import TimeSeries
import pandas as pd

load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


def fetch_daily_prices(ticker: str, outputsize: str = "compact") -> pd.DataFrame:
    ts = TimeSeries(key=API_KEY, output_format="pandas")
    data, meta = ts.get_daily(symbol=ticker, outputsize=outputsize)
    return data


if __name__ == "__main__":
    df = fetch_daily_prices("VTI")
    print(df.head())
