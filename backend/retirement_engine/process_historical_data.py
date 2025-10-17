
import os
import sys
import pandas as pd

def merge_historical_data():
    """
    Merges historical S&P 500, 10-year US Treasury, and CPI data into a single CSV file.
    """
    # Define file paths
    sp500_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "sp500.csv")
    us10y_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "us10y.csv")
    cpi_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "cpi_fred.csv")

    # Check if the raw data files exist
    if not os.path.exists(sp500_path):
        print(f"Raw data file not found: {sp500_path}", file=sys.stderr)
        return None
    if not os.path.exists(us10y_path):
        print(f"Raw data file not found: {us10y_path}", file=sys.stderr)
        return None
    if not os.path.exists(cpi_path):
        print(f"Raw data file not found: {cpi_path}", file=sys.stderr)
        return None

    # Load the datasets
    sp500_df = pd.read_csv(sp500_path)
    us10y_df = pd.read_csv(us10y_path)
    cpi_df = pd.read_csv(cpi_path)

    # Rename columns for clarity
    sp500_df.rename(columns={"Close": "sp500"}, inplace=True)
    us10y_df.rename(columns={"DATE": "Date", "DGS10": "bonds"}, inplace=True)
    cpi_df.rename(columns={"DATE": "Date", "CPIAUCSL": "cpi"}, inplace=True)

    # Convert 'Date' columns to datetime objects
    sp500_df["Date"] = pd.to_datetime(sp500_df["Date"])
    us10y_df["Date"] = pd.to_datetime(us10y_df["Date"])
    cpi_df["Date"] = pd.to_datetime(cpi_df["Date"])

    # Set Date as index for resampling and merging
    sp500_df.set_index("Date", inplace=True)
    us10y_df.set_index("Date", inplace=True)
    cpi_df.set_index("Date", inplace=True)

    # Resample CPI to daily frequency and forward-fill missing values
    cpi_df = cpi_df.resample('D').ffill()

    # Merge the dataframes on the 'Date' index
    merged_df = pd.merge(sp500_df, us10y_df, on="Date", how="inner")
    merged_df = pd.merge(merged_df, cpi_df, on="Date", how="inner")

    # Filter data from 1962 onwards
    merged_df = merged_df[merged_df.index.year >= 1962]

    # Select and rename columns to match the expected format
    merged_df = merged_df[["sp500", "bonds", "cpi"]]

    return merged_df

if __name__ == "__main__":
    df = merge_historical_data()
    if df is not None:
        df.to_csv(sys.stdout, index=False)
