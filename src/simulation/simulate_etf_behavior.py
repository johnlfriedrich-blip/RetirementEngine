# file: src/simulation/simulate_etf_behavior.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


def run_etf_simulation():
    print("Loading ETF prices...")
    prices = pd.read_csv("data/etf_prices.csv", parse_dates=["date"], index_col="date")
    prices = prices[["SP500", "VIX", "10Y"]]  # Adjust tickers as needed

    print("Calculating returns...")
    returns = prices.pct_change().dropna()

    print("Loading regime labels...")
    regimes = pd.read_csv(
        "data/macro_regimes.csv", parse_dates=["date"], index_col="date"
    )
    regimes = regimes[["Regime"]]

    print("Aligning returns to regimes...")
    regimes = regimes.resample("D").ffill()
    aligned = returns.join(regimes, how="inner")

    print("Aggregating performance by regime...")
    summary = aligned.groupby("Regime").agg(["mean", "std", "count"])

    print("Saving summary...")
    os.makedirs("output", exist_ok=True)
    # summary.to_csv("output/etf_regime_summary.csv")
    from pathlib import Path

    output_dir = Path(__file__).resolve().parent.parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    summary.to_csv(output_dir / "etf_regime_summary.csv", index=True, header=True)
    df = pd.read_csv("output/etf_regime_summary.csv", header=None, index_col=0)
    print(df.index.tolist())

    print("Plotting regime performance...")
    for etf in ["SP500", "VIX", "10Y"]:
        plt.figure(figsize=(8, 5))
        sns.barplot(x=summary.index, y=summary[etf]["mean"])
        plt.title(f"{etf} Mean Return by Regime")
        plt.ylabel("Mean Return")
        plt.xlabel("Regime")
        plt.tight_layout()
        plt.savefig(f"output/{etf}_regime_bar.png")
        plt.clf()

    print("✅ ETF regime comparison complete. Summary and plots saved to /output")


if __name__ == "__main__":
    run_etf_simulation()
