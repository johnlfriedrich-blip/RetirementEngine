# tests/test_data_loader.py
import pytest
from src.synthetic_data import from_synthetic_data
from src import data_loader

default_portfolio_asset_params = {
    "us_equities": {"cagr": 0.10, "std_dev": 0.18},
    "bonds": {"cagr": 0.03, "std_dev": 0.06},
}


def test_from_synthetic_data():
    """Test the from_synthetic_data function."""
    returns = from_synthetic_data(
        num_years=10, portfolio_asset_params=default_portfolio_asset_params
    )
    assert len(returns) == 10 * 252


def test_from_csv(tmpdir):
    """Test the from_csv function."""
    csv_file = tmpdir.join("market.csv")
    csv_file.write("sp500,bonds\n100,100\n101,101\n")
    returns = data_loader.from_csv(etf_source=str(csv_file))
    assert len(returns) == 1
    sp500_r, bonds_r, _ = returns[0]
    assert sp500_r == pytest.approx(0.01)
    assert bonds_r == pytest.approx(0.01)


def test_from_historical_data(tmpdir):
    """Test the from_historical_data function."""
    print(f"tmpdir: {str(tmpdir)}")
    with pytest.raises(ValueError, match="Could not load historical data."):
        data_loader.from_historical_data(data_dir=str(tmpdir))
