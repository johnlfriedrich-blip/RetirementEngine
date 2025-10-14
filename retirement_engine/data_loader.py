import csv
import math
import numpy as np
import pandas as pd


def _generate_normal_by_box_muller(mean, std_dev, num_samples):
    """
    Generate normally distributed random numbers using the Box-Muller transform.
    """
    num_pairs = math.ceil(num_samples / 2)
    u1 = np.random.uniform(low=np.finfo(float).eps, high=1.0, size=num_pairs)
    u2 = np.random.uniform(low=np.finfo(float).eps, high=1.0, size=num_pairs)
    log_u1 = np.log(u1)
    z0 = np.sqrt(-2.0 * log_u1) * np.cos(2.0 * np.pi * u2)
    z1 = np.sqrt(-2.0 * log_u1) * np.sin(2.0 * np.pi * u2)
    standard_normal = np.stack((z0, z1), axis=-1).flatten()[:num_samples]
    return mean + standard_normal * std_dev


def from_csv(
    etf_source,
    inflation_mean=0.03,
    inflation_std_dev=0.015,
    days_per_year=252,
):
    """Load market data from a CSV and return a DataFrame."""
    daily_inflation_mean = (1 + inflation_mean) ** (1 / days_per_year) - 1
    daily_inflation_std_dev = inflation_std_dev / math.sqrt(days_per_year)

    data_rows = []
    with open(etf_source, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        reader.fieldnames = [field.strip().lower() for field in reader.fieldnames]

        prev_sp500, prev_bonds = None, None
        for row in reader:
            try:
                current_sp500 = float(row["sp500"])
                current_bonds = float(row["bonds"])

                if prev_sp500 is not None:
                    sp500_r = (current_sp500 / prev_sp500) - 1
                    bonds_r = (current_bonds / prev_bonds) - 1

                    if abs(sp500_r) > 10 or abs(bonds_r) > 10:
                        raise ValueError("Absurdly large daily return detected")
                    if not all(math.isfinite(r) for r in [sp500_r, bonds_r]):
                        raise ValueError("Non-finite number detected")

                    inflation_r = np.random.normal(daily_inflation_mean, daily_inflation_std_dev)
                    data_rows.append({'asset1': sp500_r, 'asset2': bonds_r, 'inflation': inflation_r})

                prev_sp500, prev_bonds = current_sp500, current_bonds

            except (ValueError, KeyError) as e:
                print(f"[WARN] Skipping invalid row in {etf_source}: {row} -> {e}")

    if not data_rows:
        raise ValueError(f"No valid data loaded from {etf_source}.")

    return pd.DataFrame(data_rows)


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
    """Generate synthetic market data and return a DataFrame."""
    total_days = num_years * days_per_year

    # Convert annual stats to daily stats
    daily_sp500_mean = (1 + sp500_mean) ** (1 / days_per_year) - 1
    daily_sp500_std_dev = sp500_std_dev / math.sqrt(days_per_year)
    daily_bonds_mean = (1 + bonds_mean) ** (1 / days_per_year) - 1
    daily_bonds_std_dev = bonds_std_dev / math.sqrt(days_per_year)
    daily_inflation_mean = (1 + inflation_mean) ** (1 / days_per_year) - 1
    daily_inflation_std_dev = inflation_std_dev / math.sqrt(days_per_year)

    # Generate returns
    sp500_returns = _generate_normal_by_box_muller(daily_sp500_mean, daily_sp500_std_dev, total_days)
    bond_returns = _generate_normal_by_box_muller(daily_bonds_mean, daily_bonds_std_dev, total_days)
    inflation_returns = _generate_normal_by_box_muller(daily_inflation_mean, daily_inflation_std_dev, total_days)

    # Create DataFrame
    returns_df = pd.DataFrame({
        'asset1': sp500_returns,
        'asset2': bond_returns,
        'inflation': inflation_returns,
    })

    return returns_df
