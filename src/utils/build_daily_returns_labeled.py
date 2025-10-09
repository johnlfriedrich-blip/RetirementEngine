import pandas as pd

df = pd.read_csv("data/etf_prices.csv")
print("📁 Columns in etf_prices.csv:", df.columns.tolist())


def build_daily_returns_labeled():
    # Load ETF prices
    etf = pd.read_csv("data/etf_prices.csv", parse_dates=["date"])
    etf.rename(columns={"date": "Date"}, inplace=True)
    etf.sort_values("Date", inplace=True)
    etf["SP500_return"] = etf["SP500"].pct_change()

    # Load Treasury prices
    treasury = pd.read_csv("data/treasury_10y.csv", parse_dates=["date"])
    treasury.rename(columns={"date": "Date"}, inplace=True)
    treasury.sort_values("Date", inplace=True)
    treasury["10Y_return"] = treasury["10Y"].pct_change()

    returns = pd.merge(
        etf[["Date", "SP500_return"]], treasury[["Date", "10Y_return"]], on="Date"
    )
    print("✅ Merged ETF + Treasury:", len(returns))
    print(returns.head())

    # Load regime labels
    regimes = pd.read_csv("data/macro_regimes.csv", parse_dates=["date"])
    regimes.rename(columns={"date": "Date"}, inplace=True)
    regimes.sort_values("Date", inplace=True)
    print(regimes["Date"].min(), regimes["Date"].max())
    print(regimes.head())

    # Merge with regime labels using nearest match
    returns.sort_values("Date", inplace=True)
    regimes.sort_values("Date", inplace=True)

    labeled = pd.merge_asof(
        returns,
        regimes[["Date", "Regime"]],
        on="Date",
        direction="backward",
        tolerance=pd.Timedelta("90D"),  # allow up to 3 months back
    )
    labeled = labeled.dropna(subset=["Regime"])
    labeled = labeled.rename(columns={"SP500_return": "SP500", "10Y_return": "10Y"})
    labeled = labeled[["Date", "Regime", "SP500", "10Y"]]

    labeled.to_csv("data/daily_returns_labeled.csv", index=False)
    print("✅ Saved daily_returns_labeled.csv")

    return labeled


if __name__ == "__main__":
    build_daily_returns_labeled()
