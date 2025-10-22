import pandas as pd
import pytest
import numpy as np

import src.historical_data_processor as hdp


def test_merge_historical_data_and_slice(monkeypatch):
    # Fake merged data
    dates = pd.date_range("1980-01-01", periods=252 * 5, freq="D")
    df = pd.DataFrame(
        {
            "sp500": np.linspace(100, 200, len(dates)),
            "bonds": np.linspace(50, 60, len(dates)),
            "cpi": np.linspace(200, 210, len(dates)),
        },
        index=dates,
    )

    monkeypatch.setattr(hdp, "pd", pd)  # ensure using real pandas
    monkeypatch.setattr(hdp, "merge_historical_data", lambda **kwargs: df)

    merged = hdp.merge_historical_data()
    assert isinstance(merged, pd.DataFrame)
    assert {"sp500", "bonds", "cpi"} <= set(merged.columns)

    sliced = hdp.slice_historical_window(merged, start_year=1980, max_years=2)
    assert not sliced.empty
    assert sliced.index.min().year == 1980
    assert sliced.index.max().year <= 1981


def test_from_csv_reads_returns(tmp_path):
    csv_path = tmp_path / "market.csv"
    with open(csv_path, "w") as f:
        f.write("sp500,bonds\n100,100\n101,100.5\n102,101\n")

    df = hdp.from_csv(str(csv_path))
    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == {"us_equities", "bonds", "inflation_returns"}
    assert len(df) > 0


def test_from_historical_data_with_start_year(monkeypatch):
    dates = pd.date_range("1990-01-01", periods=252 * 10, freq="D")
    df = pd.DataFrame(
        {
            "sp500": np.linspace(100, 200, len(dates)),
            "bonds": np.linspace(50, 60, len(dates)),
            "cpi": np.linspace(200, 210, len(dates)),
        },
        index=dates,
    )

    monkeypatch.setattr(hdp, "merge_historical_data", lambda **kwargs: df)

    result = hdp.from_historical_data(start_year=1990, num_years=2)
    assert isinstance(result, pd.DataFrame)
    assert {"us_equities", "bonds", "inflation_returns"} <= set(result.columns)


def test_from_historical_data_with_bootstrap(monkeypatch):
    dates = pd.date_range("2000-01-01", periods=252 * 5, freq="D")
    df = pd.DataFrame(
        {
            "sp500": np.linspace(100, 200, len(dates)),
            "bonds": np.linspace(50, 60, len(dates)),
            "cpi": np.linspace(200, 210, len(dates)),
        },
        index=dates,
    )

    monkeypatch.setattr(hdp, "merge_historical_data", lambda **kwargs: df)

    result = hdp.from_historical_data(num_years=2, bootstrap_block_size=50)
    assert len(result) == 2 * 252
    assert {"us_equities", "bonds", "inflation_returns"} <= set(result.columns)


def test_from_historical_data_invalid(monkeypatch):
    monkeypatch.setattr(hdp, "merge_historical_data", lambda **kwargs: None)
    with pytest.raises(ValueError):
        hdp.from_historical_data()
