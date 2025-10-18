import pandas as pd


def extract_macro_signals(df):
    df = df.copy()

    # Rolling averages (12-month window)
    df["GDP_roll"] = df["GDP"].rolling(12).mean()
    df["Inflation_roll"] = df["Inflation"].rolling(12).mean()
    df["Unemployment_roll"] = df["Unemployment"].rolling(12).mean()

    # Percent change (month-over-month)
    df["GDP_pct"] = df["GDP"].pct_change()
    df["Inflation_pct"] = df["Inflation"].pct_change()
    df["Unemployment_pct"] = df["Unemployment"].pct_change()

    # Z-scores (standardized anomalies)
    for col in ["GDP", "Inflation", "Unemployment"]:
        df[f"{col}_z"] = (df[col] - df[col].mean()) / df[col].std()

    # Yield Curve features
    df["YieldCurve_roll"] = df["YieldCurve"].rolling(12).mean()
    df["YieldCurve_pct"] = df["YieldCurve"].pct_change()
    df["YieldCurve_z"] = (df["YieldCurve"] - df["YieldCurve"].mean()) / df[
        "YieldCurve"
    ].std()

    for col in ["FedFunds", "10Y_Treasury", "2Y_Treasury"]:
        df[f"{col}_z"] = (df[col] - df[col].mean()) / df[col].std()

    return df.dropna()


if __name__ == "__main__":
    df = pd.read_csv("data/macro.csv", parse_dates=["date"], index_col="date")
    signals = extract_macro_signals(df)
    signals.to_csv("data/macro_signals.csv")
    print("✅ Extracted macro signals saved to data/macro_signals.csv")
