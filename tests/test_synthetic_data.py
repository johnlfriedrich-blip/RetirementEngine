import pandas as pd
from src.synthetic_data import from_synthetic_data, Distribution


def test_from_synthetic_data_normal_distribution():
    num_years = 1
    days_per_year = 252
    total_days = num_years * days_per_year
    df = from_synthetic_data(num_years=num_years, distribution=Distribution.NORMAL)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == total_days
    assert list(df.columns) == ["us_equities", "bonds", "inflation_returns"]


def test_from_synthetic_data_student_t_distribution():
    num_years = 1
    days_per_year = 252
    total_days = num_years * days_per_year
    df = from_synthetic_data(
        num_years=num_years, distribution=Distribution.STUDENT_T, df=5
    )
    assert isinstance(df, pd.DataFrame)
    assert len(df) == total_days
    assert list(df.columns) == ["us_equities", "bonds", "inflation_returns"]


def test_from_synthetic_data_invalid_distribution():
    try:
        from_synthetic_data(distribution="invalid")
        assert False, "ValueError was not raised for invalid distribution"
    except ValueError as e:
        assert "Unknown distribution: invalid" in str(e)
