def classify_regime(row):
    """
    Classify macro regime based on z-scores:
    - Overheating: High GDP, high Inflation, low Unemployment
    - Recession: Low GDP, low Inflation, high Unemployment
    - Stagflation: Low GDP, high Inflation, high Unemployment
    - Stable: No strong signals
    """
    gdp_z = row["GDP_z"]
    infl_z = row["Inflation_z"]
    unemp_z = row["Unemployment_z"]

    if gdp_z > 1.0 and infl_z > 1.0 and unemp_z < -0.5:
        return "Overheating"
    elif gdp_z < -1.0 and infl_z < -0.5 and unemp_z > 1.0:
        return "Recession"
    elif gdp_z < -0.5 and infl_z > 1.0 and unemp_z > 1.0:
        return "Stagflation"
    else:
        return "Stable"


def apply_regime_classification(df):
    df = df.copy()
    df["Regime"] = df.apply(classify_regime, axis=1)
    return df


def add_regime_transitions(df):
    df = df.copy()
    df["Regime_Change"] = df["Regime"] != df["Regime"].shift()
    return df


def add_regime_duration(df):
    df = df.copy()
    regime_group = (df["Regime"] != df["Regime"].shift()).cumsum()
    df["Regime_Duration"] = df.groupby(regime_group).cumcount() + 1
    return df


def add_anomaly_flags(df, threshold=2.0):
    df = df.copy()
    for col in ["GDP_z", "Inflation_z", "Unemployment_z"]:
        df[f"{col}_Anomaly"] = df[col].abs() > threshold
    return df
