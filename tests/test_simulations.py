import numpy as np
import pandas as pd

from backend.retirement_engine.monte_carlo import MonteCarloSimulator, MonteCarloResults
from backend.retirement_engine.withdrawal_strategies import FixedWithdrawal


def test_monte_carlo_simulator_run_structure(mocker):
    """
    Tests the overall structure of the output from a Monte Carlo run.
    Mocks the underlying simulation to return predictable data.
    """
    num_sims = 5
    duration = 10
    market_data = pd.DataFrame({"price": np.random.rand(duration * 252)})
    withdrawal_strategy = FixedWithdrawal(initial_balance=1e6, rate=0.04)

    # Mock the _run_single_simulation function
    mock_run_single = mocker.patch(
        "backend.retirement_engine.monte_carlo._run_single_simulation"
    )
    mock_run_single.return_value = pd.DataFrame({"Year": [duration], "Run": [0]})

    mc_sim = MonteCarloSimulator(
        market_data=market_data,
        withdrawal_strategy=withdrawal_strategy,
        start_balance=1e6,
        simulation_years=duration,
        portfolio_weights={"asset1": 1.0},
        num_simulations=num_sims,
        parallel=False,
    )
    results = mc_sim.run_simulations()

    assert isinstance(results, MonteCarloResults)
    assert "Run" in results.results_df.columns
    assert len(results.results_df) == num_sims


def test_monte_carlo_success_rate(mocker):
    """
    Tests the success_rate calculation by mocking simulation outcomes.
    """
    num_sims = 10
    market_data = pd.DataFrame({"price": np.random.rand(2 * 252)})
    withdrawal_strategy = FixedWithdrawal(initial_balance=1e6, rate=0.04)

    # --- Scenario 1: 100% success ---
    mock_run_single = mocker.patch(
        "backend.retirement_engine.monte_carlo._run_single_simulation"
    )
    mock_run_single.return_value = pd.DataFrame({"End Balance": [100]})

    mc_sim_success = MonteCarloSimulator(
        market_data=market_data,
        withdrawal_strategy=withdrawal_strategy,
        start_balance=1e6,
        simulation_years=2,
        portfolio_weights={"asset1": 1.0},
        num_simulations=num_sims,
        parallel=False,
    )
    results_success = mc_sim_success.run_simulations()
    assert results_success.success_rate() == 1.0

    # --- Scenario 2: 0% success ---
    mock_run_single.return_value = pd.DataFrame({"End Balance": [0]})
    results_fail = mc_sim_success.run_simulations()
    assert results_fail.success_rate() == 0.0

    # --- Scenario 3: 50% success ---
    mock_run_single.side_effect = [
        (
            pd.DataFrame({"End Balance": [100]})
            if i % 2 == 0
            else pd.DataFrame({"End Balance": [0]})
        )
        for i in range(num_sims)
    ]
    results_mixed = mc_sim_success.run_simulations()
    assert results_mixed.success_rate() == 0.5


def test_monte_carlo_results_before_run():
    """Tests that calling success_rate on an empty result raises no error."""
    results = MonteCarloResults(pd.DataFrame(), 0)
    assert results.success_rate() == 0.0
    assert results.median_final_balance() == 0.0
