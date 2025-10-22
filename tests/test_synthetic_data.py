import math
import pandas as pd
from ..src.normal_distribution import _generate_normal_by_box_muller
from ..src.student_t_distribution import _generate_student_t_variates
from ..src.synthetic_data import (
    Distribution,
)  # or adjust import if Distribution is defined here


def from_synthetic_data(
    distribution,
    portfolio_asset_params: dict,
    num_years: int = 30,
    inflation_mean: float = 0.03,
    inflation_std_dev: float = 0.015,
    days_per_year: int = 252,
    buffer_years: int = 0,
    df: int = 3,
) -> pd.DataFrame:
    """Generate synthetic daily returns for each asset and inflation."""

    # --- Normalize distribution ---
    if isinstance(distribution, str):
        try:
            distribution = Distribution(distribution)
        except ValueError:
            raise ValueError(f"Unknown distribution: {distribution}")

    total_days = (num_years + buffer_years) * days_per_year
    all_returns = {}

    # Generate returns for each asset
    for asset_name, params in portfolio_asset_params.items():
        daily_mean = (1 + params["cagr"]) ** (1 / days_per_year) - 1
        daily_std_dev = params["std_dev"] / math.sqrt(days_per_year)

        if distribution == Distribution.BOX_MULLER:
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

    # Inflation series
    daily_inflation_mean = (1 + inflation_mean) ** (1 / days_per_year) - 1
    daily_inflation_std_dev = inflation_std_dev / math.sqrt(days_per_year)

    if distribution == Distribution.BOX_MULLER:
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

    return pd.DataFrame(all_returns)
