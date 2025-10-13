import pytest
from retirement_engine.simulator import run_simulation
from retirement_engine.resolve_path import resolve_path
import os


@pytest.mark.parametrize("strategy", ["Guardrails", "Pause After Loss"])
def test_simulation_runs_with_guardrails_and_pause(strategy):
    path = resolve_path("data/market.csv")
    assert os.path.exists(path), "Expected market.csv to exist for integration test"

    balances, withdrawals = run_simulation(
        withdrawal_rate=0.04,
        etf_source="data/market.csv",
        strategy=strategy,
        initial_balance=1_000_000,
    )

    print(f"[DEBUG] Strategy: {strategy}, Final Balance: ${balances[-1]:,.2f}")
    assert len(balances) > 0
    assert len(withdrawals) > 0
    assert all(b > 0 for b in balances)
    assert all(w >= 0 for w in withdrawals)
