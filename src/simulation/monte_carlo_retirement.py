import numpy as np
import pandas as pd
import random


def scale_volatility(std, regime):
    if regime in ["Recession", "Stagflation"]:
        return std * 0.8  # dampen volatility in riskier regimes
    return std


def simulate_portfolio_path(
    initial_balance,
    regime_sequence,
    return_matrix,
    allocation_strategy,
    withdrawal_rate,
    tax_rate,
    sim_index,
    use_bootstrap=False,
    returns_by_regime=None,
):

    balance = initial_balance
    daily_gains = []
    history = []
    withdrawals = []
    DEBUG_LIMIT = 10  # Limit debug output to first 10 days

    for day_index, regime in enumerate(regime_sequence):
        # print(f"Day {day_index}: Regime = {regime}")

        if day_index % 365 == 0 and withdrawal_rate > 0:
            withdrawal = withdrawal_rate * balance
            tax = tax_rate * withdrawal
            balance -= withdrawal + tax
        else:
            withdrawal = 0

        rebalancing_event = day_index % 252 == 0 and day_index > 0
        weights = allocation_strategy.get(regime, {"SP500": 0.6, "10Y": 0.4})
        if use_bootstrap and returns_by_regime:
            sampled_returns = random.choice(returns_by_regime[regime])
            returns = {
                "SP500": sampled_returns[0],
                "10Y": sampled_returns[1],
            }
        else:
            returns = {
                etf: np.random.normal(
                    return_matrix[regime][etf]["mean"],
                    scale_volatility(return_matrix[regime][etf]["std"], regime),
                )
                for etf in weights
            }

        # 🔍 Debug output for first few days
        """
        if sim_index == 0 and day_index < DEBUG_LIMIT:
            print(f"\n📊 Day {day_index + 1} | Regime: {regime}")
            for etf in weights:
                mean = return_matrix[regime][etf]["mean"]
                std = return_matrix[regime][etf]["std"]
                scaled_std = scale_volatility(std, regime)
                sampled_return = returns[etf]
                weight = weights[etf]
                print(
                    f"  {etf}: mean={mean:.5f}, std={std:.5f}, scaled_std={scaled_std:.5f}, sampled_return={sampled_return:.5f}, weight={weight:.2f}"
                )
        """

        portfolio_return = sum(weights[etf] * returns[etf] for etf in weights)
        daily_gains.append(portfolio_return)
        gain = balance * portfolio_return
        tax = 0
        if rebalancing_event:
            realized_gain = max(balance * portfolio_return, 0)
            tax = realized_gain * tax_rate
        withdrawal = withdrawal_rate * balance
        balance += gain - tax - withdrawal

        """ 💰 Debug balance evolution
        if sim_index == 0 and day_index < DEBUG_LIMIT:
            print(f"💼 Portfolio return: {portfolio_return:.5f}")
            print(
                f"💰 Balance: ${balance:,.2f} | Gain: ${gain:,.2f} | Tax: ${tax:,.2f} | Withdrawal: ${withdrawal:,.2f}"
            )
        """
        history.append(balance)
        withdrawals.append(withdrawal)

        if balance <= 0:
            break

    return history, withdrawals, daily_gains


def adjust_withdrawal(balance, regime, base_rate):
    if balance < 800_000 and regime in ["Recession", "Stagflation"]:
        return base_rate * 0.75
    return base_rate


def survival_rate(results, years):
    survivors = 0
    for path in results:
        # Check if portfolio stayed alive for full duration
        if len(path) >= years and all(balance > 0 for balance in path[:years]):
            survivors += 1
    return survivors / len(results) if results else 0


def generate_regime_sequence(regime_sequence, years):
    sequence = []
    i = 0
    while len(sequence) < years:
        regime = regime_sequence.iloc[i % len(regime_sequence)]
        duration = random.randint(2, 5)  # Simulate regime persistence
        sequence.extend([regime] * duration)
        i += 1
        # print(sequence[:years])
    return sequence[:years]


def run_monte_carlo(
    num_simulations,
    initial_balance,
    regime_sequence,
    return_matrix,
    allocation_strategy,
    withdrawal_rate,
    tax_rate,
    simulation_years,
    use_bootstrap=False,
    returns_by_regime=None,
):
    results = []
    withdrawal_paths = []
    daily_gain_paths = []

    if use_bootstrap:
        print("🔁 Bootstrapping enabled: using historical regime returns")
    else:
        print("🎲 Parametric sampling: using regime-conditioned normal draws")

    for sim_index in range(num_simulations):
        sampled_sequence = generate_regime_sequence(regime_sequence, simulation_years)
        if sim_index == 0:
            print("\n🧠 Regime distribution in first simulation:")
            from collections import Counter

            print(Counter(sampled_sequence))

        path, withdrawals, gains = simulate_portfolio_path(
            initial_balance,
            sampled_sequence,
            return_matrix,
            allocation_strategy,
            withdrawal_rate,
            tax_rate,
            sim_index,
            use_bootstrap=use_bootstrap,
            returns_by_regime=returns_by_regime,
        )
        results.append(path)
        withdrawal_paths.append(withdrawals)
        daily_gain_paths.append(gains)

    return results, withdrawal_paths, daily_gain_paths
