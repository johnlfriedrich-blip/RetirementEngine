# tests/test_monte_carlo.py
import pandas as pd
from unittest.mock import patch

from src.monte_carlo import MonteCarloSimulator
from src.withdrawal_strategies import FixedWithdrawal


@patch("src.monte_carlo._run_single_simulation")
def test_monte_carlo_runs_correct_number_of_simulations(mock_run_single_simulation):
    """
    Tests that the MonteCarloSimulator runs the specified number of simulations.
    """
    # 1. Setup
    num_simulations = 5
    market_data = pd.DataFrame({"price": [100, 101, 102]})
    withdrawal_strategy = FixedWithdrawal(initial_balance=1000000, rate=0.04)

    mc_sim = MonteCarloSimulator(
        market_data=market_data,
        withdrawal_strategy=withdrawal_strategy,
        start_balance=1000000,
        simulation_years=1,
        portfolio_weights={"us_equities": 1.0},
        data_source="test",
        synthetic_params={},
        num_simulations=num_simulations,
        parallel=False,
    )
    mc_sim.run_simulations()

    # 3. Assertions
    assert mock_run_single_simulation.call_count == num_simulations


@patch("src.monte_carlo._run_single_simulation")
def test_monte_carlo_success_rate_calculation(mock_run_single_simulation):
    """
    Tests the success rate calculation of the MonteCarloSimulator.
    """
    # 1. Setup
    num_simulations = 10
    market_data = pd.DataFrame({"price": [100, 101, 102]})
    withdrawal_strategy = FixedWithdrawal(initial_balance=1000000, rate=0.04)

    # 7 successful runs (end balance > 0) and 3 failed runs (end balance = 0)
    side_effects = []
    for i in range(7):
        side_effects.append(pd.DataFrame({"Run": [i], "End Balance": [1000]}))
    for i in range(7, 10):
        side_effects.append(pd.DataFrame({"Run": [i], "End Balance": [0]}))
    mock_run_single_simulation.side_effect = side_effects

    # 2. Instantiate and run MonteCarloSimulator
    mc_sim = MonteCarloSimulator(
        market_data=market_data,
        withdrawal_strategy=withdrawal_strategy,
        start_balance=1000000,
        simulation_years=1,
        portfolio_weights={"us_equities": 1.0},
        data_source="test",
        synthetic_params={},
        num_simulations=num_simulations,
        parallel=False,
    )
    results = mc_sim.run_simulations()

    # 3. Assertion
    assert results.success_rate() == 0.7
