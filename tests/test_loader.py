import pandas as pd
from src.utils.build_daily_returns_labeled import build_daily_returns_labeled


def test_etf_loader():
    df = pd.read_csv("data/etf_prices.csv")
    assert "SP500" in df.columns
    assert df["SP500"].notna().sum() > 100


def test_treasury_loader():
    df = pd.read_csv("data/treasury_10y.csv")
    assert "10Y" in df.columns
    assert df["10Y"].notna().sum() > 100


def test_regime_loader():
    df = pd.read_csv("data/macro_regimes.csv")
    assert "Regime" in df.columns
    assert df["Regime"].nunique() >= 2
