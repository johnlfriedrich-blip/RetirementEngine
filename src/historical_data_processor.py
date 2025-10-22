import os
import sys
import csv
import math
import numpy as np
import pandas as pd


def merge_historical_data(data_dir="src/data/raw") -> pd.DataFrame | None:
    """
    Merges historical S&P 500, 10-year US Treasury, and CPI data into a single DataFrame.
    """
    sp500_path = os.path.join(data_dir, "sp500.csv")
    us10y_path = os.path.join(data_dir, "us10y_daily_fred.csv")
    cpi_path = os.path.join(data_dir, "cpi_fred.csv")

    if not os.path.exists(sp500_path):
        print(f"Raw data file not found: {sp500_path}", file=sys.stderr)
        return None
    if not os.path.exists(us10y_path):
        print(f"Raw data file not found: {us10y_path}", file=sys.stderr)
        return None
    if not os.path.exists(cpi_path):
        print(f"Raw data file not found: {cpi_path}", file=sys.stderr)
        return None

    sp500_df = pd.read_csv(sp500_path)
    us10y_df = pd.read_csv(us10y_path)
    cpi_df = pd.read_csv(cpi_path)

    us10y_df["DGS10"] = pd.to_numeric(us10y_df["DGS10"], errors="coerce")
    us10y_df["DGS10"] = us10y_df["DGS10"].ffill().bfill()

    sp500_df.rename(columns={"Close": "sp500"}, inplace=True)
    us10y_df.rename(columns={"DATE": "Date", "DGS10": "bonds"}, inplace=True)
    cpi_df.rename(columns={"DATE": "Date", "CPIAUCSL": "cpi"}, inplace=True)

    sp500_df["Date"] = pd.to_datetime(sp500_df["Date"])
    us10y_df["Date"] = pd.to_datetime(us10y_df["Date"])
    cpi_df["Date"] = pd.to_datetime(cpi_df["Date"])

    sp500_df.set_index("Date", inplace=True)
    us10y_df.set_index("Date", inplace=True)
    cpi_df.set_index("Date", inplace=True)

    cpi_df = cpi_df.resample("D").ffill()

    merged_df = pd.merge(sp500_df, us10y_df, on="Date", how="inner")
    merged_df = pd.merge(merged_df, cpi_df, on="Date", how="inner")

    merged_df = merged_df[merged_df.index.year >= 1962]
    merged_df = merged_df[["sp500", "bonds", "cpi"]]

    print(f"[DEBUG] Merged DataFrame length: {len(merged_df)}")
    return merged_df


def slice_historical_window(
    df: pd.DataFrame, start_year: int, max_years: int = 30
) -> pd.DataFrame:
    """
    Slices the historical data from a given start year for up to max_years.
    """
    start_date = pd.Timestamp(f"{start_year}-01-01")
    end_year = start_year + max_years - 1
    end_date = pd.Timestamp(f"{end_year}-12-31")

    sliced = df.loc[(df.index >= start_date) & (df.index <= end_date)]
    if sliced.empty:
        raise ValueError(f"No historical data available for start year {start_year}")
    print(
        f"[DEBUG] Sliced historical window: {start_year} to {end_year} ({len(sliced)} rows)"
    )
    return sliced


def from_csv(
    etf_source,
    inflation_mean=0.03,
    inflation_std_dev=0.015,
    days_per_year=252,
):
    """Load market data from a pre-merged CSV and compute returns."""
    daily_inflation_mean = (1 + inflation_mean) ** (1 / days_per_year) - 1
    daily_inflation_std_dev = inflation_std_dev / math.sqrt(days_per_year)

    prev_sp500, prev_bonds = None, None
    returns = []
    with open(etf_source, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        reader.fieldnames = [field.strip().lower() for field in reader.fieldnames]

        for row in reader:
            try:
                current_sp500 = float(row["sp500"])
                current_bonds = float(row["bonds"])

                if prev_sp500 is not None:
                    if prev_sp500 == 0 or prev_bonds == 0:
                        print(f"[WARN] Skipping row due to zero previous value: {row}")
                        prev_sp500, prev_bonds = current_sp500, current_bonds
                        continue

                    sp500_r = (current_sp500 / prev_sp500) - 1
                    bonds_r = (current_bonds / prev_bonds) - 1

                    if abs(sp500_r) > 10 or abs(bonds_r) > 10:
                        raise ValueError(
                            "Absurdly large daily return detected in market data"
                        )

                    if not all(math.isfinite(r) for r in [sp500_r, bonds_r]):
                        raise ValueError("Non-finite number detected in market data")

                    inflation_r = np.random.normal(
                        daily_inflation_mean, daily_inflation_std_dev
                    )
                    returns.append((sp500_r, bonds_r, inflation_r))

                prev_sp500, prev_bonds = current_sp500, current_bonds

            except (ValueError, KeyError) as e:
                print(f"[WARN] Skipping invalid row in {etf_source}: {row} -> {e}")

    if not returns:
        raise ValueError(
            f"No valid data loaded from {etf_source}. The file may be empty or incorrectly formatted."
        )

    return pd.DataFrame(returns, columns=["us_equities", "bonds", "inflation_returns"])


def from_historical_data(
    data_dir="src/data/raw",
    num_years=30,
    start_year=None,
    inflation_mean=0.03,
    inflation_std_dev=0.015,
    days_per_year=252,
    bootstrap_block_size=None,
):
    """
    Load historical market data and either:
    - Slice a contiguous window starting at `start_year` (if provided).
    - Or perform block bootstrapping (if bootstrap_block_size is set).
    """
    df = merge_historical_data(data_dir=data_dir)
    if df is None:
        raise ValueError("Could not load historical data.")

    # Convert to daily returns
    df["us_equities"] = df["sp500"].pct_change().fillna(0)
    df["bonds"] = df["bonds"].pct_change().fillna(0)

    # Inflation as random noise around mean/std
    daily_inflation_mean = (1 + inflation_mean) ** (1 / days_per_year) - 1
    daily_inflation_std_dev = inflation_std_dev / math.sqrt(days_per_year)
    df["inflation_returns"] = np.random.normal(
        daily_inflation_mean, daily_inflation_std_dev, len(df)
    )

    df = df[["us_equities", "bonds", "inflation_returns"]]

    if start_year:
        df = slice_historical_window(df, start_year=start_year, max_years=num_years)

    if bootstrap_block_size:
        # Simple block bootstrap
        blocks = []
        total_days = num_years * days_per_year
        while sum(len(b) for b in blocks) < total_days:
            start_idx = np.random.randint(0, len(df) - bootstrap_block_size)
            block = df.iloc[start_idx : start_idx + bootstrap_block_size]
            blocks.append(block)
        df = pd.concat(blocks).iloc[:total_days]

    return df.reset_index(drop=True)


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "market.csv")

    df = merge_historical_data()
    if df is not None:
        df.to_csv(output_path, index=True)
        print(f"Merged historical data saved to {output_path}")
