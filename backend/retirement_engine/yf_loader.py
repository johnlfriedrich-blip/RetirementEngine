import yfinance as yf
import pandas as pd
import numpy as np
import time
from typing import List, Union, Optional


def fetch_returns(
    tickers: Union[str, List[str]],
    start: str = "2000-01-01",
    end: Optional[str] = None,
    interval: str = "1d",
    log: bool = False,
    retries: int = 3,
) -> pd.DataFrame:
    """
    Fetch historical adjusted close prices and compute returns using Ticker().history().

    Parameters:
        tickers (str or List[str]): Single ticker or list of tickers.
        start (str): Start date (YYYY-MM-DD).
        end (Optional[str]): End date (YYYY-MM-DD). Defaults to today.
        interval (str): Data interval ('1d', '1wk', '1mo').
        log (bool): If True, return log returns. Else, percent change.
        retries (int): Number of retry attempts on failure.

    Returns:
        pd.DataFrame: Returns indexed by date.
    """
    if isinstance(tickers, str):
        tickers = [tickers]

    all_returns = []

    for ticker in tickers:
        for attempt in range(retries):
            try:
                t = yf.Ticker(ticker)
                df = t.history(
                    start=start, end=end, interval=interval, auto_adjust=True
                )
                if df.empty or "Close" not in df.columns:
                    raise ValueError(f"No data for {ticker}")
                prices = df["Close"]
                returns = (
                    np.log(prices / prices.shift(1)) if log else prices.pct_change()
                )
                all_returns.append(returns.rename(ticker))
                break
            except Exception as e:
                print(f"[Attempt {attempt+1}] Failed to fetch {ticker}: {e}")
                time.sleep(2)
        else:
            raise RuntimeError(f"All attempts failed for {ticker}")

    return pd.concat(all_returns, axis=1).dropna()


def fetch_price_snapshot(tickers: Union[str, List[str]], date: str) -> pd.Series:
    """
    Fetch adjusted close prices for a specific date using Ticker().history().

    Parameters:
        tickers (str or List[str]): Ticker(s) to fetch.
        date (str): Date in YYYY-MM-DD format.

    Returns:
        pd.Series: Prices for each ticker on the given date.
    """
    if isinstance(tickers, str):
        tickers = [tickers]

    snapshot = {}

    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            df = t.history(start=date, end=date, auto_adjust=True)
            if df.empty or "Close" not in df.columns:
                raise ValueError(f"No data for {ticker} on {date}")
            snapshot[ticker] = df["Close"].iloc[0]
        except Exception as e:
            print(f"Failed to fetch snapshot for {ticker}: {e}")
            snapshot[ticker] = None

    return pd.Series(snapshot)
