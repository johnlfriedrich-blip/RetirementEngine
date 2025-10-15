# tests/test_monte_carlo.py
import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock, patch

from retirement_engine.monte_carlo import MonteCarloSimulator, _run_single_simulation
from retirement_engine.simulator import RetirementSimulator


@patch('retirement_engine.monte_carlo.MarketDataGenerator')
def test_monte_carlo_runs_correct_number_of_simulations(MockMarketDataGenerator):
    """
    Tests that the MonteCarloSimulator runs the specified number of simulations.
    """
    # 1. Setup
    num_simulations = 5
    duration_years = 10

    # Mock the MarketDataGenerator
    mock_market_data_generator = MockMarketDataGenerator.return_value
    mock_market_data_generator.generate_returns.return_value = [(0.0, 0.0, 0.0)] * (duration_years * 252)

    # Mock the RetirementSimulator class
    mock_simulator_instance = MagicMock(spec=RetirementSimulator)
    mock_simulator_instance.run.return_value = (pd.DataFrame({'Year': [1], 'End Balance': [1000]}), [50000])

    # This mock will be used as the class itself
    MockSimulatorClass = MagicMock(return_value=mock_simulator_instance)

    # 2. Instantiate and run MonteCarloSimulator
    mc_sim = MonteCarloSimulator(
        num_simulations=num_simulations,
        duration_years=duration_years,
        simulator_class=MockSimulatorClass,
        market_data_generator_args={},
        parallel=False,
    )
    mc_sim.run(strategy_name='fixed', initial_balance=1000000, rate=0.04)

    # 3. Assertions
    # Check that the simulator class was instantiated 5 times
    assert MockSimulatorClass.call_count == num_simulations
    # Check that the run method on the instance was called 5 times
    assert mock_simulator_instance.run.call_count == num_simulations


@patch('retirement_engine.monte_carlo.MarketDataGenerator')
def test_monte_carlo_success_rate_calculation(MockMarketDataGenerator):
    """
    Tests the success rate calculation of the MonteCarloSimulator.
    """
    # 1. Setup
    num_simulations = 10
    duration_years = 5

    mock_market_data_generator = MockMarketDataGenerator.return_value
    mock_market_data_generator.generate_returns.return_value = [(0.0, 0.0, 0.0)] * (duration_years * 252)

    # Mock the run results of the RetirementSimulator
    # 7 successful runs (end balance > 0) and 3 failed runs (end balance = 0)
    successful_run_result = (pd.DataFrame({'Year': [1, 2], 'End Balance': [50000, 1000]}), [50000, 50000])
    failed_run_result = (pd.DataFrame({'Year': [1, 2], 'End Balance': [50000, 0]}), [50000, 50000])

    mock_simulator_instance = MagicMock(spec=RetirementSimulator)
    # The side_effect cycles through the desired return values
    side_effects = []
    for _ in range(7):
        side_effects.append((pd.DataFrame({'Year': [1, 2], 'End Balance': [50000, 1000]}), [50000, 50000]))
    for _ in range(3):
        side_effects.append((pd.DataFrame({'Year': [1, 2], 'End Balance': [50000, 0]}), [50000, 50000]))
    mock_simulator_instance.run.side_effect = side_effects
    MockSimulatorClass = MagicMock(return_value=mock_simulator_instance)

    # 2. Instantiate and run MonteCarloSimulator
    mc_sim = MonteCarloSimulator(
        num_simulations=num_simulations,
        duration_years=duration_years,
        simulator_class=MockSimulatorClass,
        market_data_generator_args={},
        parallel=False,
    )
    mc_sim.run(strategy_name='fixed', initial_balance=1000000, rate=0.04)

    # 3. Assertion
    assert mc_sim.success_rate() == 0.7


@patch('retirement_engine.monte_carlo.strategy_factory')
@patch('retirement_engine.monte_carlo.MarketDataGenerator')
def test_run_single_simulation_error_handling(MockMarketDataGenerator, mock_strategy_factory):
    """Tests that _run_single_simulation returns an empty DataFrame on error."""
    MockMarketDataGenerator.side_effect = Exception("Test Error")
    result = _run_single_simulation(0, 10, {}, None, 'fixed', {}, False)
    assert isinstance(result, pd.DataFrame) and result.empty


def test_monte_carlo_success_rate_not_run_error():
    """Tests that success_rate raises an error if the simulation hasn't been run."""
    mc_sim = MonteCarloSimulator(parallel=False)
    with pytest.raises(RuntimeError, match="Simulation has not been run yet."):
        mc_sim.success_rate()


@patch('retirement_engine.monte_carlo._run_single_simulation')
def test_monte_carlo_all_simulations_fail(mock_run_single):
    """Tests the case where all individual simulations fail."""
    mock_run_single.return_value = pd.DataFrame()  # Simulate failure
    mc_sim = MonteCarloSimulator(num_simulations=5, parallel=False)
    results = mc_sim.run(strategy_name='fixed')
    assert results.empty
    assert mc_sim.success_rate() == 0.0


@patch('retirement_engine.monte_carlo.multiprocessing.Pool')
def test_monte_carlo_parallel_execution(MockPool):
    """Tests that the Monte Carlo simulation can be run in parallel."""
    mock_pool_instance = MockPool.return_value.__enter__.return_value
    mock_pool_instance.map.return_value = [pd.DataFrame({'Year': [1], 'End Balance': [1000]})]

    mc_sim = MonteCarloSimulator(num_simulations=1, parallel=True)
    mc_sim.run(strategy_name='fixed')

    MockPool.assert_called_once()
    mock_pool_instance.map.assert_called_once()


@patch('retirement_engine.monte_carlo._run_single_simulation')
def test_monte_carlo_full_results_false(mock_run_single):
    """Tests the simulation with full_results=False."""
    # Simulate that each run returns only the last row, with unique Run IDs
    mock_run_single.side_effect = [
        pd.DataFrame([{'Run': 0, 'Year': 30, 'End Balance': 12000}]),
        pd.DataFrame([{'Run': 1, 'Year': 30, 'End Balance': 15000}]),
        pd.DataFrame([{'Run': 2, 'Year': 30, 'End Balance': 0}]),
    ]

    mc_sim = MonteCarloSimulator(num_simulations=3, parallel=False)
    results = mc_sim.run(strategy_name='fixed', full_results=False)

    # The final result should contain one row per simulation
    assert len(results) == 3
    # We have 2 successful runs out of 3
    assert mc_sim.success_rate() == 2 / 3
