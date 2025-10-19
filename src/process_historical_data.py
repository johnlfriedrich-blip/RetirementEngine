import os
import sys
import pandas as pd


def merge_historical_data(data_dir="src/data/raw"):
    """
    Merges historical S&P 500, 10-year US Treasury, and CPI data into a single CSV file.
    """
    # Define file paths
    sp500_path = os.path.join(data_dir, "sp500.csv")
    us10y_path = os.path.join(data_dir, "us10y_daily_fred.csv")
    cpi_path = os.path.join(data_dir, "cpi_fred.csv")

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

    # Convert DGS10 to numeric, coercing errors to NaN
    us10y_df["DGS10"] = pd.to_numeric(us10y_df["DGS10"], errors="coerce")
    # Fill missing values in DGS10 using forward fill, then backward fill
    us10y_df["DGS10"] = us10y_df["DGS10"].ffill().bfill()

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
    cpi_df = cpi_df.resample("D").ffill()

    # Merge the dataframes on the 'Date' index
    merged_df = pd.merge(sp500_df, us10y_df, on="Date", how="inner")
    merged_df = pd.merge(merged_df, cpi_df, on="Date", how="inner")

    # Filter data from 1962 onwards
    merged_df = merged_df[merged_df.index.year >= 1962]

    # Select and rename columns to match the expected format
    merged_df = merged_df[["sp500", "bonds", "cpi"]]
    print(f"[DEBUG] Merged DataFrame length: {len(merged_df)}")
    return merged_df


if __name__ == "__main__":
    # Ensure the output directory exists
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "market.csv")

    df = merge_historical_data()
    if df is not None:
        df.to_csv(output_path, index=True)  # Save with index (Date column)
        print(f"Merged historical data saved to {output_path}")
