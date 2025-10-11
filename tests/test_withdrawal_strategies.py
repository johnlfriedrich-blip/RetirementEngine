# test_withdrawal_strategies.py

import pytest
from retirement_engine.withdrawal_strategies import (
    fixed_withdrawal,
    inflation_adjusted_withdrawal,
    dynamic_percent_withdrawal,
    guardrails_withdrawal,
    pause_after_loss_withdrawal,
)


def test_fixed_withdrawal():
    result = fixed_withdrawal(1_000_000, 0.04, 5)
    assert result == [40_000] * 5


def test_inflation_adjusted_withdrawal():
    inflation = [0.02, 0.03, 0.01, 0.025, 0.00]
    result = inflation_adjusted_withdrawal(1_000_000, 0.04, inflation)
    expected = [40_800.0, 41_200.0, 40_400.0, 41_000.0, 40_000.0]
    assert all(abs(a - b) < 1 for a, b in zip(result, expected))


def test_dynamic_percent_withdrawal():
    balances = [1_000_000, 950_000, 980_000, 1_020_000]
    result = dynamic_percent_withdrawal(balances, 0.05)
    expected = [50_000, 47_500, 49_000, 51_000]
    assert result == expected


def test_guardrails_withdrawal():
    balances = [400_000, 600_000, 800_000, 1_200_000]
    result = guardrails_withdrawal(balances, min_pct=0.03, max_pct=0.06)
    expected = [400_000 * 0.03, 600_000 * 0.036, 800_000 * 0.048, 1_200_000 * 0.06]
    assert all(abs(a - b) < 1 for a, b in zip(result, expected))


def test_strategies_produce_different_ending_balances():
    # Simulated portfolio trajectory and return stream
    balances = [1_000_000, 980_000, 990_000, 1_010_000, 1_030_000]
    returns = [0.01, -0.02, 0.015, -0.01, 0.02]

    rate = 0.05

    # Run each strategy
    fixed = fixed_withdrawal(balances[0], rate, len(balances))
    inflation = inflation_adjusted_withdrawal(balances[0], rate, returns)
    dynamic = dynamic_percent_withdrawal(balances, rate)
    guardrails = guardrails_withdrawal(balances, min_pct=0.03, max_pct=0.06)
    pause = pause_after_loss_withdrawal(
        balances, [[r, 0] for r in returns], rate, sp500_weight=1.0
    )

    # Compute ending balances after withdrawals
    def apply_withdrawals(bal, rets, wd):
        for i in range(len(wd)):
            bal *= 1 + rets[i]
            bal -= wd[i]
        return bal

    results = {
        "Fixed": apply_withdrawals(balances[0], returns, fixed),
        "Inflation": apply_withdrawals(balances[0], returns, inflation),
        "Dynamic": apply_withdrawals(balances[0], returns, dynamic),
        "Guardrails": apply_withdrawals(balances[0], returns, guardrails),
        "PauseAfterLoss": apply_withdrawals(balances[0], returns, pause),
    }

    # Print for debug
    for name, end_balance in results.items():
        print(f"[TEST] Strategy: {name}, Ending Balance: ${end_balance:,.2f}")

    # Ensure all ending balances are distinct
    balances_set = set(round(b, 2) for b in results.values())
    assert len(balances_set) == len(
        results
    ), "Strategies produced identical ending balances"


def test_pause_after_loss_withdrawal():
    from retirement_engine.withdrawal_strategies import pause_after_loss_withdrawal

    balances = [1_000_000, 1_020_000, 1_030_000, 1_040_000, 1_050_000]
    returns = [
        [0.02, 0.01],  # blended = +0.017
        [-0.03, -0.01],  # blended = -0.023
        [-0.01, 0.0],  # blended = -0.006
        [0.01, 0.01],  # blended = +0.01
    ]
    rate = 0.04
    sp500_weight = 0.6

    result = pause_after_loss_withdrawal(balances, returns, rate, sp500_weight)
    expected = [40_000.0, 40_800.0, 0, 0, 42_000.0]

    assert all(
        abs(a - b) < 1 for a, b in zip(result, expected)
    ), f"Expected {expected}, got {result}"
