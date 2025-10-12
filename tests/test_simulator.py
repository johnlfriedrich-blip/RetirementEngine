import pytest
from retirement_engine.simulator import run_simulation, load_market_data


def test_run_simulation_fixed_withdrawal():
    # Create dummy returns: 1% daily for 365 days
    returns = [0.01] * 365
    withdrawal_rate = 0.04
    strategy = "Fixed"
    initial_balance = 1_000_000

    # Patch load_market_data to return dummy returns
    def dummy_loader(*args, **kwargs):
        return returns

    # Inject dummy loader
    from retirement_engine import simulator

    simulator.load_market_data = dummy_loader

    balances, withdrawals = run_simulation(
        withdrawal_rate=withdrawal_rate,
        etf_source="dummy.csv",
        strategy=strategy,
        initial_balance=initial_balance,
    )

    assert len(balances) == 365
    assert len(withdrawals) == 1
    assert withdrawals[0] == initial_balance * withdrawal_rate
    assert balances[0] < initial_balance  # withdrawal applied
    assert balances[-1] > balances[0]  # growth applied


def test_load_market_data_raises_if_file_missing():
    with pytest.raises(FileNotFoundError):
        load_market_data("data/does_not_exist.csv")
