import pandas as pd
import pytest
from src.synthetic_data import from_synthetic_data, Distribution

default_portfolio_asset_params = {
    "us_equities": {"cagr": 0.10, "std_dev": 0.18},
    "bonds": {"cagr": 0.03, "std_dev": 0.06},
}


def test_from_synthetic_data_normal_distribution():
    num_years = 1
    days_per_year = 252
    total_days = num_years * days_per_year
    df = from_synthetic_data(
        num_years=num_years,
        distribution=Distribution.NORMAL,
        portfolio_asset_params=default_portfolio_asset_params,
    )
    assert isinstance(df, pd.DataFrame)
    assert len(df) == total_days
    assert list(df.columns) == ["us_equities", "bonds", "inflation_returns"]


def test_from_synthetic_data_student_t_distribution():
    num_years = 1
    days_per_year = 252
    total_days = num_years * days_per_year
    df = from_synthetic_data(
        num_years=num_years,
        distribution=Distribution.STUDENT_T,
        df=5,
        portfolio_asset_params=default_portfolio_asset_params,
    )
    assert isinstance(df, pd.DataFrame)
    assert len(df) == total_days
    assert list(df.columns) == ["us_equities", "bonds", "inflation_returns"]


def test_from_synthetic_data_invalid_distribution():
    with pytest.raises(ValueError, match="Unknown distribution: invalid"):
        from_synthetic_data(
            distribution="invalid",
            portfolio_asset_params=default_portfolio_asset_params,
        )
