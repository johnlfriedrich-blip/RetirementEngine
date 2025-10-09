# file: src/data/integrate_macro.py

import pandas as pd
import logging


def integrate_macro():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting macro integration")

    # Load raw series
    gdp = pd.read_csv("data/raw/GDP.csv", index_col="date", parse_dates=True)
    cpi = pd.read_csv("data/raw/Inflation.csv", index_col="date", parse_dates=True)
    unemp = pd.read_csv("data/raw/Unemployment.csv", index_col="date", parse_dates=True)
    sp500 = pd.read_csv("data/raw/SP500.csv", index_col="date", parse_dates=True)
    vix = pd.read_csv("data/raw/VIX.csv", index_col="date", parse_dates=True)
    treasury_10y = pd.read_csv(
        "data/raw/10Y_Treasury.csv", index_col="date", parse_dates=True
    )
    treasury_2y = pd.read_csv(
        "data/raw/2Y_Treasury.csv", index_col="date", parse_dates=True
    )
    fedfunds = pd.read_csv("data/raw/FedFunds.csv", index_col="date", parse_dates=True)

    treasury_10y = pd.read_csv(
        "data/raw/10Y_Treasury.csv", index_col="date", parse_dates=True
    )
    treasury_10y = treasury_10y.rename(columns={"GS10": "10Y_Treasury"})

    treasury_2y = pd.read_csv(
        "data/raw/2Y_Treasury.csv", index_col="date", parse_dates=True
    )
    treasury_2y = treasury_2y.rename(columns={"DGS2": "2Y_Treasury"})

    # Resample daily series to quarterly
    sp500_q = sp500.resample("QE").mean()
    vix_q = vix.resample("QE").mean()
    treasury_10y_q = treasury_10y.resample("QE").mean()
    treasury_2y_q = treasury_2y.resample("QE").mean()
    fedfunds_q = fedfunds.resample("QE").mean()

    # Align to GDP dates
    macro_index = gdp.index
    cpi = cpi.reindex(macro_index, method="ffill")
    unemp = unemp.reindex(macro_index, method="ffill")
    sp500_q = sp500_q.reindex(macro_index, method="ffill")
    vix_q = vix_q.reindex(macro_index, method="ffill")
    treasury_10y_q = treasury_10y_q.reindex(macro_index, method="ffill")
    treasury_2y_q = treasury_2y_q.reindex(macro_index, method="ffill")
    fedfunds_q = fedfunds_q.reindex(macro_index, method="ffill")

    # Compute yield curve
    yield_curve = treasury_10y_q["10Y_Treasury"] - treasury_2y_q["2Y_Treasury"]
    yield_curve_df = yield_curve.to_frame(name="YieldCurve")

    # Merge all series
    df = pd.concat(
        [
            gdp,
            cpi,
            unemp,
            sp500_q,
            vix_q,
            treasury_10y_q,
            treasury_2y_q,
            fedfunds_q,
            yield_curve_df,
        ],
        axis=1,
    ).dropna()

    df.columns = [
        "GDP",
        "Inflation",
        "Unemployment",
        "SP500",
        "VIX",
        "10Y_Treasury",
        "2Y_Treasury",
        "FedFunds",
        "YieldCurve",
    ]

    df.to_csv("data/macro.csv", index=True)
    logging.info("Macro snapshot saved to data/macro.csv")


if __name__ == "__main__":
    integrate_macro()
