from src.utils.build_daily_returns_labeled import build_daily_returns_labeled
import pandas as pd


def test_build_daily_returns_labeled():
    df = build_daily_returns_labeled()
    assert not df.empty
    assert "SP500" in df.columns
    assert "10Y" in df.columns
    assert "Regime" in df.columns
    assert df["Regime"].nunique() >= 2
