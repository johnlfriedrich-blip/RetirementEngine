import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/processed")


def load_spx_ohlcv(filename: str = "SPX.csv") -> pd.DataFrame:
    path = DATA_DIR / filename
    df = pd.read_csv(path, parse_dates=["Date"])
    df.set_index("Date", inplace=True)
    df = df.sort_index()
    df = df[["Adj Close"]].rename(columns={"Adj Close": "sp500"})
    return df


def load_market_data(filename: str = "market.csv") -> pd.DataFrame:
    path = DATA_DIR / filename
    df = pd.read_csv(path, parse_dates=["Date"])
    df.set_index("Date", inplace=True)
    df = df.sort_index()
    df.columns = ["sp500", "bonds", "cpi"]
    return df


def compute_monthly_returns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    monthly = df[columns].resample("M").last()
    returns = monthly.pct_change().dropna()
    return returns


def adjust_for_inflation(df: pd.DataFrame) -> pd.DataFrame:
    df["real_sp500"] = df["sp500"] / df["cpi"]
    df["real_bonds"] = df["bonds"] / df["cpi"]
    return df


def load_real_returns() -> pd.DataFrame:
    df = load_market_data()
    df = adjust_for_inflation(df)
    real = df[["real_sp500", "real_bonds"]].resample("ME").last().pct_change().dropna()
    return real
