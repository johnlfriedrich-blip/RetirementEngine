from retirement_engine.simulator import run_simulation


def test_run_simulation_ending_balance_fixed_strategy():
    # Setup known inputs
    withdrawal_rate = 0.05
    sp500_weight = 0.6
    etf_source = "market.csv"
    strategy = "Fixed"
    initial_balance = 1_000_000

    # Run simulation
    history, withdrawals = run_simulation(
        withdrawal_rate=withdrawal_rate,
        sp500_weight=sp500_weight,
        etf_source=etf_source,
        strategy=strategy,
        initial_balance=initial_balance,
    )

    # Validate output structure
    assert isinstance(history, list), "History should be a list"
    assert isinstance(withdrawals, list), "Withdrawals should be a list"
    assert (
        len(history) == len(withdrawals) + 1
    ), "History should be one element longer than withdrawals"

    # Validate ending balance
    ending_balance = history[-1]
    assert isinstance(ending_balance, float), "Ending balance should be a float"
    assert (
        ending_balance > -1_000_000_000
    ), "Ending balance is unrealistically low — check compounding logic"
    assert (
        ending_balance < 10_000_000
    ), "Ending balance is unrealistically high — check return normalization"

    # Optional: print for manual inspection
    print(f"[TEST] Ending balance: ${ending_balance:,.2f}")
