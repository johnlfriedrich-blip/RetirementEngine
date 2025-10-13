# tests/test_yf_loader.py
import pytest
from retirement_engine.yf_loader import fetch_returns, fetch_price_snapshot
import numpy as np
import pandas as pd


def test_fetch_vti_returns():
    tickers = ["VTI"]
    start = "2020-01-01"
    end = "2020-12-31"
    try:
        df = fetch_returns(tickers, start=start, end=end)
        assert not df.empty
        assert "VTI" in df.columns
        assert df.index.is_monotonic_increasing
    except RuntimeError as e:
        pytest.skip(f"Data fetch failed: {e}")


def test_fetch_log_returns():
    tickers = ["SPY"]
    try:
        df = fetch_returns(tickers, start="2021-01-01", end="2021-06-30", log=True)
        assert not df.empty
        assert df["SPY"].dtype == "float64"
        assert df["SPY"].min() < 0  # log returns can be negative
    except RuntimeError as e:
        pytest.skip(f"Data fetch failed: {e}")


def test_invalid_ticker():
    with pytest.raises(RuntimeError):
        fetch_returns(["FAKE_TICKER_123"], start="2020-01-01", end="2020-12-31")


def test_price_snapshot():
    tickers = ["QQQ"]
    date = "2022-01-03"
    snapshot = fetch_price_snapshot(tickers, date)
    if snapshot["QQQ"] is None:
        pytest.skip(f"No snapshot data for {tickers} on {date}")
    assert isinstance(snapshot, pd.Series)
    assert "QQQ" in snapshot
    assert snapshot["QQQ"] > 0
