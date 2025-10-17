import csv
import math
import numpy as np
import pandas as pd
from .process_historical_data import merge_historical_data

def _generate_normal_by_box_muller(mean, std_dev, num_samples):
    """
    Generate normally distributed random numbers using the Box-Muller transform.
    """
    # Ensure we generate pairs of numbers. If num_samples is odd, we'll generate one extra and discard it.
    num_pairs = math.ceil(num_samples / 2)

    # Generate uniform random numbers in (0, 1]
    u1 = np.random.uniform(low=np.finfo(float).eps, high=1.0, size=num_pairs)
    u2 = np.random.uniform(low=np.finfo(float).eps, high=1.0, size=num_pairs)

    # Apply the Box-Muller transform to get standard normal variables
    log_u1 = np.log(u1)
    z0 = np.sqrt(-2.0 * log_u1) * np.cos(2.0 * np.pi * u2)
    z1 = np.sqrt(-2.0 * log_u1) * np.sin(2.0 * np.pi * u2)

    # Combine the pairs and truncate to the desired number of samples
    standard_normal = np.stack((z0, z1), axis=-1).flatten()[:num_samples]

    # Scale by mean and standard deviation
    return mean + standard_normal * std_dev


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
                        raise ValueError(
                            "Non-finite number detected in market data"
                        )

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

    return returns


def from_historical_data(
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
    df = merge_historical_data()
    if df is None:
        raise ValueError("Could not load historical data.")

    # Calculate daily returns
    df['sp500_returns'] = df['sp500'].pct_change(fill_method=None)
    df['bonds_returns'] = df['bonds'].pct_change(fill_method=None)
    df['inflation_returns'] = df['cpi'].pct_change(fill_method=None)

    # Drop rows with missing values (the first row)
    df = df.dropna()

    # Prepare the returns in the format expected by the simulation
    returns = list(zip(df['sp500_returns'], df['bonds_returns'], df['inflation_returns']))

    # Block bootstrapping
    total_days = num_years * days_per_year
    n_samples = len(returns)
    num_blocks = total_days // bootstrap_block_size
    bootstrapped_returns = []
    for _ in range(num_blocks):
        start_index = np.random.randint(0, n_samples - bootstrap_block_size)
        bootstrapped_returns.extend(
            returns[start_index : start_index + bootstrap_block_size]
        )

    return bootstrapped_returns

def from_synthetic_data(
    num_years=30,
    sp500_mean=0.10,
    sp500_std_dev=0.18,
    bonds_mean=0.03,
    bonds_std_dev=0.06,
    inflation_mean=0.03,
    inflation_std_dev=0.015,
    days_per_year=252,
):
    """Generate synthetic market data and initialize the simulator."""
    total_days = num_years * days_per_year

    # Convert annual stats to daily stats for the simulation
    daily_sp500_mean = (1 + sp500_mean) ** (1 / days_per_year) - 1
    daily_sp500_std_dev = sp500_std_dev / math.sqrt(days_per_year)

    daily_bonds_mean = (1 + bonds_mean) ** (1 / days_per_year) - 1
    daily_bonds_std_dev = bonds_std_dev / math.sqrt(days_per_year)

    daily_inflation_mean = (1 + inflation_mean) ** (1 / days_per_year) - 1
    daily_inflation_std_dev = inflation_std_dev / math.sqrt(days_per_year)

    # Generate the returns using the Box-Muller transform
    sp500_returns = _generate_normal_by_box_muller(
        daily_sp500_mean, daily_sp500_std_dev, total_days
    )
    bond_returns = _generate_normal_by_box_muller(
        daily_bonds_mean, daily_bonds_std_dev, total_days
    )
    inflation_returns = _generate_normal_by_box_muller(
        daily_inflation_mean, daily_inflation_std_dev, total_days
    )

    # Zip the returns into the list of tuples format the simulator expects
    returns = list(zip(sp500_returns, bond_returns, inflation_returns))

    return returns
