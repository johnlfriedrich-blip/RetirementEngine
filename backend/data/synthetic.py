import numpy as np
import pandas as pd

def generate_synthetic_data(
    years: int,
    cagr: float,
    std_dev: float,
    start_price: float = 100.0,
) -> pd.DataFrame:
    """
    Generates a pandas DataFrame of synthetic daily returns for a single asset class.

    Args:
        years: The number of years of data to generate.
        cagr: The compound annual growth rate of the asset class.
        std_dev: The standard deviation of the asset class.
        start_price: The starting price of the asset.

    Returns:
        A pandas DataFrame with a "price" column.
    """
    num_days = years * 252  # Assuming 252 trading days per year
    daily_return_mean = (1 + cagr) ** (1 / 252) - 1
    daily_std_dev = std_dev / np.sqrt(252)

    # Generate daily returns from a log-normal distribution
    daily_returns = np.random.lognormal(
        mean=daily_return_mean,
        sigma=daily_std_dev,
        size=num_days,
    ) - 1

    # Create a DataFrame and calculate the price series
    df = pd.DataFrame({"daily_return": daily_returns})
    df["price"] = start_price * (1 + df["daily_return"]).cumprod()

    return df[["price"]]
