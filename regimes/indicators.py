# indicators.py

import pandas as pd
import yfinance as yf
from fredapi import Fred

fred = Fred(api_key="your_fred_key")


def fetch_gdp():
    gdp = fred.get_series("GDP")
    gdp = gdp.pct_change().dropna()
    gdp.name = "GDP"
    return gdp


def fetch_cpi():
    cpi = fred.get_series("CPIAUCSL")
    cpi = cpi.pct_change().dropna()
    cpi.name = "CPI"
    return cpi


def fetch_vix():
    vix = yf.download("^VIX", start="1990-01-01", interval="1mo")["Adj Close"]
    vix.name = "VIX"
    return vix


def fetch_sp500():
    spx = yf.download("^GSPC", start="1990-01-01", interval="1mo")["Adj Close"]
    returns = spx.pct_change().dropna()
    returns.name = "SP500"
    return returns


def fetch_credit_spread():
    spread = fred.get_series("BAMLH0A0HYM2") - fred.get_series("BAMLCC0A1AAATRIV")
    spread.name = "CreditSpread"
    return spread.dropna()


def fetch_oil():
    oil = fred.get_series("DCOILWTICO")
    oil = oil.pct_change().dropna()
    oil.name = "Oil"
    return oil


def build_indicator_df():
    gdp = fetch_gdp()
    cpi = fetch_cpi()
    vix = fetch_vix()
    sp500 = fetch_sp500()
    spread = fetch_credit_spread()
    oil = fetch_oil()

    df = pd.concat([gdp, cpi, vix, sp500, spread, oil], axis=1)
    df = df.dropna()
    return df
