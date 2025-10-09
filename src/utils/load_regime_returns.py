import pandas as pd


def load_returns_by_regime(filepath="data/daily_returns_labeled.csv"):
    df = pd.read_csv(filepath)
    return {
        regime: df[df["Regime"] == regime][["SP500", "10Y"]].values.tolist()
        for regime in df["Regime"].unique()
    }
