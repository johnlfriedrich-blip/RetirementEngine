from typing import Dict
import pandas as pd
from .synthetic import generate_synthetic_data

ASSET_CLASSES: Dict[str, Dict[str, float]] = {
    "us_equities": {"cagr": 0.083, "std_dev": 0.199},
    "intl_equities": {"cagr": 0.065, "std_dev": 0.174},
    "fixed_income": {"cagr": 0.024, "std_dev": 0.103},
}


def get_asset_data(asset_class: str, years: int = 50) -> pd.DataFrame:
    """
    Retrieves the synthetic data for a given asset class.

    Args:
        asset_class: The name of the asset class to retrieve data for.
        years: The number of years of data to generate.

    Returns:
        A pandas DataFrame with the synthetic price data.
    """
    if asset_class not in ASSET_CLASSES:
        raise ValueError(f"Invalid asset class: {asset_class}")

    return generate_synthetic_data(
        years=years,
        cagr=ASSET_CLASSES[asset_class]["cagr"],
        std_dev=ASSET_CLASSES[asset_class]["std_dev"],
    )
