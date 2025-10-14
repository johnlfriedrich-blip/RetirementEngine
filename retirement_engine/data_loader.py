import csv
import math
import numpy as np


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


def from_av(
    stock_ticker,
    bond_ticker,
    inflation_mean=0.03,
    inflation_std_dev=0.015,
    days_per_year=252,
):
    """Load market data from Alpha Vantage and initialize the simulator."""
    daily_inflation_mean = (1 + inflation_mean) ** (1 / days_per_year) - 1
    daily_inflation_std_dev = inflation_std_dev / math.sqrt(days_per_year)

    from alpha_vantage.timeseries import TimeSeries
    import os
    from dotenv import load_dotenv

    load_dotenv()
    API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

    ts = TimeSeries(key=API_KEY, output_format="pandas")

    stock_prices, _ = ts.get_daily(symbol=stock_ticker, outputsize="full")
    bond_prices, _ = ts.get_daily(symbol=bond_ticker, outputsize="full")

    # Select and rename the '4. close' column from each dataframe
    stock_close = stock_prices[['4. close']].rename(columns={'4. close': 'stock'})
    bond_close = bond_prices[['4. close']].rename(columns={'4. close': 'bond'})

    # align the dataframes by joining on their index (dates)
    prices = stock_close.join(bond_close, how="inner")

    # calculate returns
    returns_df = prices.pct_change().dropna()

    returns = []
    for index, row in returns_df.iterrows():
        inflation_r = np.random.normal(
            daily_inflation_mean, daily_inflation_std_dev
        )
        returns.append((row['stock'], row['bond'], inflation_r))

    return returns


def from_yf(
    stock_ticker,
    bond_ticker,
    inflation_mean=0.03,
    inflation_std_dev=0.015,
    days_per_year=252,
):
    """Load market data from Yahoo Finance and initialize the simulator."""
    import yfinance as yf
    daily_inflation_mean = (1 + inflation_mean) ** (1 / days_per_year) - 1
    daily_inflation_std_dev = inflation_std_dev / math.sqrt(days_per_year)

    data = yf.download([stock_ticker, bond_ticker], start="2000-01-01", end="2023-01-01")

    prices = data.loc[:, "Adj Close"]
    prices = prices.rename(columns={stock_ticker: 'stock', bond_ticker: 'bond'})

    stock_returns = prices["stock"].pct_change().dropna()
    bond_returns = prices["bond"].pct_change().dropna()

    returns = []
    for i in range(len(stock_returns)):
        inflation_r = np.random.normal(
            daily_inflation_mean, daily_inflation_std_dev
        )
        returns.append((stock_returns[i], bond_returns[i], inflation_r))

    return returns
