from retirement_engine.simulator import RetirementSimulator
import numpy as np


def test_cola_adjusted_strategy():
    np.random.seed(42)
    daily_returns = [
        (
            np.random.normal(0.0003, 0.01),
            np.random.normal(0.0001, 0.005),
            np.random.normal(0.00007, 0.0002),
        )
        for _ in range(252 * 30)
    ]

    sim = RetirementSimulator(
        returns=daily_returns,
        strategy="COLA Adjusted",
        withdrawal_rate=0.04,
        initial_balance=1_000_000,
        sp500_weight=0.6,
    )

    balances, withdrawals = sim.run()
    print(f"Final Balance: ${balances[-1]:,.2f}")
    print(f"Total Withdrawn: ${sum(withdrawals):,.2f}")

    assert len(balances) > 0
    assert len(withdrawals) == len(sim.inflation_windows)
    assert balances[-1] > 0
    assert all(w >= 0 for w in withdrawals)
    assert all(b > 0 for b in balances)
