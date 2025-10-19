import pandas as pd
import math
from enum import Enum

from .normal_distribution import _generate_normal_by_box_muller
from .student_t_distribution import _generate_student_t_variates


class Distribution(str, Enum):
    NORMAL = "normal"
    STUDENT_T = "student-t"


def from_synthetic_data(
    num_years=30,
    portfolio_asset_params: dict = None,
    inflation_mean=0.03,
    inflation_std_dev=0.015,
    days_per_year=252,
    buffer_years=0,
    distribution: Distribution = Distribution.NORMAL,
    df: int = 3,
):
    """Generate synthetic market data and initialize the simulator."""
    if portfolio_asset_params is None:
        raise ValueError("portfolio_asset_params must be provided.")

    total_days = (num_years + buffer_years) * days_per_year
    all_returns = {}

    # Generate returns for each asset in the portfolio
    for asset_name, params in portfolio_asset_params.items():
        daily_mean = (1 + params["cagr"]) ** (1 / days_per_year) - 1
        daily_std_dev = params["std_dev"] / math.sqrt(days_per_year)

        if distribution == Distribution.NORMAL:
            returns = _generate_normal_by_box_muller(
                daily_mean, daily_std_dev, total_days
            )
        elif distribution == Distribution.STUDENT_T:
            returns = _generate_student_t_variates(
                df, daily_mean, daily_std_dev, total_days
            )
        else:
            raise ValueError(f"Unknown distribution: {distribution}")
        all_returns[asset_name] = returns

    # Generate inflation returns separately
    daily_inflation_mean = (1 + inflation_mean) ** (1 / days_per_year) - 1
    daily_inflation_std_dev = inflation_std_dev / math.sqrt(days_per_year)

    if distribution == Distribution.NORMAL:
        inflation_returns = _generate_normal_by_box_muller(
            daily_inflation_mean, daily_inflation_std_dev, total_days
        )
    elif distribution == Distribution.STUDENT_T:
        inflation_returns = _generate_student_t_variates(
            df, daily_inflation_mean, daily_inflation_std_dev, total_days
        )
    else:
        raise ValueError(f"Unknown distribution: {distribution}")
    all_returns["inflation_returns"] = inflation_returns

    # Combine all returns into a single DataFrame
    return pd.DataFrame(all_returns)
