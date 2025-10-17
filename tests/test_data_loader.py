# tests/test_data_loader.py
import pytest
from backend.retirement_engine import data_loader

def test_from_synthetic_data():
    """Test the from_synthetic_data function."""
    returns = data_loader.from_synthetic_data(num_years=10)
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