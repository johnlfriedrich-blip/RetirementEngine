import csv
import math

import numpy as np

from .process_historical_data import merge_historical_data


def from_csv(
    etf_source,
    inflation_mean=0.03,
    inflation_std_dev=0.015,
    days_per_year=252,
):
    """Load market data from a CSV and initialize the simulator."""
    daily_inflation_mean = (1 + inflation_mean) ** (1 / days_per_year) - 1
    daily_inflation_std_dev = inflation_std_dev / math.sqrt(days_per_year)

    prev_sp500, prev_bonds = None, None
    returns = []
    with open(etf_source, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        # Normalize header names: lowercase and strip whitespace
        reader.fieldnames = [field.strip().lower() for field in reader.fieldnames]

        for row in reader:
            try:
                current_sp500 = float(row["sp500"])
                current_bonds = float(row["bonds"])

                if prev_sp500 is not None:
                    sp500_r = (current_sp500 / prev_sp500) - 1
                    bonds_r = (current_bonds / prev_bonds) - 1

                    # Add a check for absurdly large returns (e.g., > 1000% daily)
                    if abs(sp500_r) > 10 or abs(bonds_r) > 10:
                        raise ValueError(
                            "Absurdly large daily return detected in market data"
                        )

                    # Add a check for finite numbers to prevent bad data
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
            f"No valid data loaded from {etf_source}. "
            "The file may be empty or incorrectly formatted."
        )

    return returns


def from_historical_data(
    data_dir="src/data/raw",
    num_years=30,
    inflation_mean=0.03,
    inflation_std_dev=0.015,
    days_per_year=252,
    bootstrap_block_size=5,
):
    """
    Load historical market data, calculate returns, and then use
    block bootstrapping to generate a new sequence of returns.
    """
    # Load the historical data
    df = merge_historical_data(data_dir=data_dir)
    print(
        f"[DEBUG] DataFrame length after merge_historical_data: {len(df) if df is not None else 'None'}"
    )
    if df is None:
        raise ValueError("Could not load historical data.")

    return df
