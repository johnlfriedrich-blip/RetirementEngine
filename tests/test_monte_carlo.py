# tests/test_monte_carlo.py
import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock, patch

from retirement_engine.monte_carlo import MonteCarloSimulator
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
