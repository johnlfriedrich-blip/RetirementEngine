# tests/test_data_loader.py
import pytest
import pandas as pd
from retirement_engine import data_loader

def test_from_synthetic_data():
    """Test the from_synthetic_data function."""
    returns = data_loader.from_synthetic_data(num_years=10)
    assert len(returns) == 10 * 252
    assert isinstance(returns, pd.DataFrame)
    assert set(returns.columns) == {'asset1', 'asset2', 'inflation'}

def test_from_csv(tmpdir):
    """Test the from_csv function."""
    csv_file = tmpdir.join("market.csv")
    csv_file.write("sp500,bonds\n100,100\n101,101\n")
    returns = data_loader.from_csv(etf_source=str(csv_file))
    assert len(returns) == 1
    assert isinstance(returns, pd.DataFrame)

    # Access by row index and column name
    first_row = returns.iloc[0]
    assert first_row['asset1'] == pytest.approx(0.01)
    assert first_row['asset2'] == pytest.approx(0.01)
