import os
import io
import pandas as pd
import pytest

from retirement_engine.simulator import load_market_data

# Helpers -------------------------------------------------------------------


def make_price_df(sp500_values, bonds_values=None):
    df = pd.DataFrame(
        {
            "date": pd.date_range("2002-07-26", periods=len(sp500_values)),
            "SP500": sp500_values,
        }
    )
    if bonds_values is not None:
        df["BONDS"] = bonds_values
    return df


# Tests ---------------------------------------------------------------------


def test_load_from_file_like_object_returns_daily_returns():
    # Create a CSV in-memory with SP500 prices
    df = make_price_df([100, 101, 102, 101])
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    returns = load_market_data(csv_buffer)
    # pct_change for [100,101,102,101] -> [0.01, ~0.00990099, -0.00980392] (length 3)
    assert isinstance(returns, list)
    assert len(returns) == 3
    assert pytest.approx(returns[0], rel=1e-6) == 0.01


def test_load_from_direct_path(tmp_path):
    # Write CSV to a temporary file and pass full path
    df = make_price_df([100, 105, 110])
    p = tmp_path / "market.csv"
    df.to_csv(p, index=False)

    returns = load_market_data(str(p))
    assert len(returns) == 2
    assert pytest.approx(returns[0], rel=1e-6) == 0.05


def test_load_from_fallback_path(tmp_path):
    # Create a fake fallback directory
    fake_data_dir = tmp_path / "data"
    fake_data_dir.mkdir()

    # Write a small test CSV to that directory
    p = fake_data_dir / "market.csv"
    df = pd.DataFrame(
        {
            "date": ["2022-01-01", "2022-01-02", "2022-01-03"],
            "SP500": [100, 105, 110],
            "BONDS": [80, 82, 84],
        }
    )
    df.to_csv(p, index=False)

    # Import and call loader with fallback_dir override
    from retirement_engine.simulator import load_market_data

    returns = load_market_data("market.csv", fallback_dir=str(fake_data_dir))

    print("[TEST] Returns length:", len(returns))
    assert isinstance(returns, list)
    assert len(returns) == 2
    assert pytest.approx(returns[0], abs=1e-6) == 0.05
    assert pytest.approx(returns[1], abs=1e-6) == 0.047619


def test_raises_file_not_found_for_missing_file(tmp_path):
    # Ensure a non-existent filename raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        load_market_data("this_file_does_not_exist.csv")


def test_raises_on_missing_sp500_column(tmp_path):
    # Create CSV without SP500 column
    df = pd.DataFrame({"date": ["2002-07-26", "2002-07-29"], "BONDS": [82.51, 81.42]})
    p = tmp_path / "nok.csv"
    df.to_csv(p, index=False)

    with pytest.raises(ValueError) as exc:
        load_market_data(str(p))
    assert "SP500" in str(exc.value)


def test_load_market_data_returns_are_normalized():
    returns = load_market_data("market.csv")

    # Basic sanity checks
    assert isinstance(returns, list), "Returns should be a list"
    assert len(returns) > 100, "Returns list should have sufficient data"

    # Check value range
    for r in returns[:10]:  # sample first 10
        assert isinstance(r, float), f"Return {r} is not a float"
        assert -1.0 < r < 1.0, f"Return {r} is outside expected range"

    # Check volatility (not all zeros)
    assert any(
        abs(r) > 0.0001 for r in returns
    ), "Returns appear flat — check loader logic"
