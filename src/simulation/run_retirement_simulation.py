from src.simulation.monte_carlo_retirement import run_monte_carlo, survival_rate
from src.utils.load_regime_returns import load_returns_by_regime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

global_stats = {
    "SP500_mean": 0.0005,
    "SP500_std": 0.013,
    "10Y_mean": 0.0000,
    "10Y_std": 0.010,
}


def run_simulation(n_days=360, withdrawal_rate=0.04, use_regimes=True):
    from src.utils.load_regime_returns import load_returns_by_regime
    import random

    returns_by_regime = load_returns_by_regime()
    balance = 1_000_000
    history = []

    for day in range(n_days):
        regime = "Stable"  # placeholder until regime sequencing is added
        if use_regimes:
            sp500_return, ten_year_return = random.choice(returns_by_regime[regime])
        else:
            # Monte Carlo sampling from global stats
            sp500_return = random.gauss(
                global_stats["SP500_mean"], global_stats["SP500_std"]
            )
            ten_year_return = random.gauss(
                global_stats["10Y_mean"], global_stats["10Y_std"]
            )

        portfolio_return = sp500_return * 0.85 + ten_year_return * 0.15
        gain = balance * portfolio_return
        withdrawal = 0 if withdrawal_rate == 0 else balance * (withdrawal_rate / 365)
        balance += gain - withdrawal
        history.append(balance)

    return {
        "ending_balance": balance,
        "history": history,
        "survival_rate": 1.0 if balance > 0 else 0.0,
    }


# Load raw CSV without headers
raw = pd.read_csv("data/etf_regime_summary.csv", header=None, skiprows=3)

# Define expected column names
columns = ["Regime"] + [
    f"{etf}_{metric}"
    for etf in ["SP500", "VIX", "10Y"]
    for metric in ["mean", "std", "count"]
]

# Validate shape
if raw.shape[1] != len(columns):
    raise ValueError(f"Expected {len(columns)} columns, but got {raw.shape[1]}")

# Assign column names
raw.columns = columns

# Convert all numeric columns to float
for col in columns[1:]:  # Skip 'Regime'
    raw[col] = pd.to_numeric(raw[col], errors="coerce")

# Set regime as index
raw.set_index("Regime", inplace=True)

# Copy to working variable
data = raw.copy()

# Optional: print for validation
print("Final columns:", data.columns.tolist())
print("Final index:", data.index.tolist())
print(data.head())

# Build etf_matrix
etf_matrix = {
    regime: {
        etf: {
            "mean": data.loc[regime][f"{etf}_mean"],
            "std": data.loc[regime][f"{etf}_std"],
        }
        for etf in ["SP500", "VIX", "10Y"]
    }
    for regime in data.index
}

# Regime sequence example
macro = pd.read_csv("data/macro_regimes.csv", parse_dates=["date"])
macro_daily = macro.set_index("date").resample("D").ffill()
regime_sequence = macro_daily["Regime"].copy()
regime_returns = load_returns_by_regime()

# Define allocation strategy
allocation_strategy = {
    "Stable": {"SP500": 0.85, "10Y": 0.15},
    "Stagflation": {"SP500": 0.4, "10Y": 0.6},
    "Recession": {"SP500": 0.25, "10Y": 0.75},
    "Overheating": {"SP500": 0.65, "10Y": 0.35},
}

# Run simulation
results, withdrawal_paths, daily_gain_paths = run_monte_carlo(
    num_simulations=10000,
    initial_balance=1_000_000,
    regime_sequence=regime_sequence,
    return_matrix=etf_matrix,
    allocation_strategy=allocation_strategy,
    withdrawal_rate=0.04,
    tax_rate=0.15,
    simulation_years=30,
    use_bootstrap=True,
    returns_by_regime=regime_returns,
)

# Analyze survival
rate = survival_rate(results, 30)
print(f"Portfolio survival rate over 30 years: {rate:.2%}")

# Plot results

paths = np.array([w + [np.nan] * (30 - len(w)) for w in withdrawal_paths])
percentiles = np.nanpercentile(paths, [10, 50, 90], axis=0)

for p, label in zip(percentiles, ["10%", "50%", "90%"]):
    plt.plot(p, label=label)

plt.title("Annual Withdrawals Over Time")
plt.xlabel("Year")
plt.ylabel("Withdrawal Amount")
plt.legend()
plt.tight_layout()
# plt.show()


os.makedirs("output", exist_ok=True)
plt.savefig("output/withdrawal_paths.png")

ending_balances = [path[-1] if path else 0 for path in results]
print(f"Max ending balance: ${max(ending_balances):,.2f}")
print(f"Median ending balance: ${np.median(ending_balances):,.2f}")
print(f"Min ending balance: ${min(ending_balances):,.2f}")
ending_withdrawals = [
    withdrawals[-1] if withdrawals else 0 for withdrawals in withdrawal_paths
]

plt.scatter(ending_balances, ending_withdrawals, alpha=0.3)
plt.xlabel("Ending Balance")
plt.ylabel("Final Year Withdrawal")
plt.title("Final Withdrawal vs Ending Balance")
plt.tight_layout()

os.makedirs("output", exist_ok=True)
plt.savefig("output/final_withdrawal_vs_ending_balance.png")

# Convert results to matrix
paths_matrix = np.array([path + [np.nan] * (30 - len(path)) for path in results])

# Plot all paths
plt.figure(figsize=(12, 6))
for path in paths_matrix:
    plt.plot(path, color="gray", alpha=0.05)

# Add baseline
plt.axhline(y=1_000_000, color="red", linestyle="--", label="Starting Balance")

plt.title("Monte Carlo Portfolio Paths Over 30 Years")
plt.xlabel("Year")
plt.ylabel("Portfolio Balance")
plt.legend()
plt.tight_layout()
plt.savefig("output/monte_carlo_paths.png")


plt.figure(figsize=(12, 6))
for gains in daily_gain_paths[:100]:
    cumulative = np.cumprod([1 + g for g in gains])
    plt.plot(cumulative, alpha=0.3)

plt.title("Cumulative Gains per Simulations")
plt.xlabel("Days")
plt.ylabel("Cumulative Return")
plt.axhline(1, color="gray", linestyle="--", linewidth=1)
plt.grid(True)
plt.tight_layout()
plt.savefig("output/cumulative_gain_paths.png")
