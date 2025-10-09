# file: src/ai/run_regime_prediction.py

import pandas as pd
from src.ai.regime_predictor import fit_hmm, predict_regimes, score_confidence
from src.features.regime_classifier import (
    apply_regime_classification,
    add_regime_transitions,
    add_regime_duration,
    add_anomaly_flags,
)
from src.regimes.confidence_plot import plot_regimes


def run_pipeline():
    print("Loading macro signals...")
    df = pd.read_csv("data/macro_signals.csv", parse_dates=["date"], index_col="date")

    # Filter to feature columns only
    feature_cols = [
        col
        for col in df.columns
        if col.endswith("_z") or col.endswith("_pct") or col.endswith("_roll")
    ]
    X = df[feature_cols].dropna()

    print("Fitting HMM model...")
    model = fit_hmm(X)

    # Align df to X's index
    df = df.loc[X.index]
    df["regime"] = predict_regimes(X, model)
    df["confidence"] = score_confidence(X, model)

    print("Applying regime classification...")
    df = apply_regime_classification(df)
    df = add_regime_transitions(df)
    df = add_regime_duration(df)
    df = add_anomaly_flags(df)

    print("Saving enriched regime data...")
    df.to_csv("data/macro_regimes.csv")

    print("Plotting regime transitions...")
    plot_regimes(df, df["regime"], df["confidence"], "outputs/regime_plot.png")

    print(
        "✅ Regime prediction complete. Output saved to data/macro_regimes.csv and outputs/regime_plot.png"
    )


if __name__ == "__main__":
    run_pipeline()
