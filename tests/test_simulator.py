# tests/test_simulator.py
import pytest
import pandas as pd
from unittest.mock import Mock, call, patch

from retirement_engine.simulator import RetirementSimulator, run_simulation
from retirement_engine import config
from retirement_engine.withdrawal_strategies import (
    BaseWithdrawalStrategy,
    SimulationContext,
)


def test_simulator_with_mock_strategy():
    """
    Tests the RetirementSimulator's core loop using a mock strategy.
    This test verifies that the simulator correctly calls the strategy,
    updates the balance, and generates the expected yearly results.
    """
    # 1. Set up test data and mock object
    initial_balance = 1_000_000
    num_years = 3
    days_per_year = config.TRADINGDAYS

    # Create simple market data with zero returns to make calculations predictable
    mock_returns = [(0.0, 0.0, 0.0)] * (num_years * config.TRADINGDAYS)

    # Create a mock strategy object that conforms to the BaseWithdrawalStrategy interface
    mock_strategy = Mock(spec=BaseWithdrawalStrategy)

    # Configure the mock to return a fixed withdrawal amount every time it's called
    fixed_withdrawal_amount = 50_000
    mock_strategy.calculate_annual_withdrawal.return_value = fixed_withdrawal_amount

    # 2. Instantiate and run the simulator
    sim = RetirementSimulator(
        returns=mock_returns,
        initial_balance=initial_balance,
        stock_allocation=0.6,
        strategy=mock_strategy,
        days_per_year=days_per_year,
    )
    results_df, all_withdrawals = sim.run()

    # 3. Make assertions
    # Assert that the strategy's method was called once for each year
    assert mock_strategy.calculate_annual_withdrawal.call_count == num_years

    # Assert that the context object was passed correctly on each call
    all_calls = mock_strategy.calculate_annual_withdrawal.call_args_list
    assert len(all_calls) == num_years

    # Check the first call (year_index = 0)
    first_context = all_calls[0].args[0]
    assert isinstance(first_context, SimulationContext)
    assert first_context.year_index == 0
    assert first_context.current_balance == initial_balance
    assert first_context.previous_withdrawals == []

    # Check the second call (year_index = 1)
    second_context = all_calls[1].args[0]
    assert second_context.year_index == 1
    # Balance should be initial balance minus one withdrawal
    assert second_context.current_balance == pytest.approx(
        initial_balance - fixed_withdrawal_amount
    )
    assert second_context.previous_withdrawals == [fixed_withdrawal_amount]

    # Assert on the final results
    assert len(results_df) == num_years
    assert all_withdrawals == [50_000, 50_000, 50_000]

    # With zero market returns, the balance should decrease by exactly the withdrawal amount each year
    expected_final_balance = initial_balance - (num_years * fixed_withdrawal_amount)
    final_balance = results_df["End Balance"].iloc[-1]
    assert final_balance == pytest.approx(expected_final_balance)


def test_simulator_portfolio_depletion():
    """
    Tests that the simulator stops correctly when the portfolio is depleted.
    """
    # 1. Setup
    initial_balance = 100_000
    num_years = 5
    days_per_year = config.TRADINGDAYS
    mock_returns = [(0.0, 0.0, 0.0)] * (num_years * config.TRADINGDAYS)

    # This mock strategy will deplete the portfolio in the 3rd year
    mock_strategy = Mock(spec=BaseWithdrawalStrategy)
    mock_strategy.calculate_annual_withdrawal.return_value = 40_000

    # 2. Run simulation
    sim = RetirementSimulator(
        returns=mock_returns,
        initial_balance=initial_balance,
        stock_allocation=0.6,
        strategy=mock_strategy,
    )
    results_df, all_withdrawals = sim.run()

    # 3. Assertions
    # The simulation should stop after 3 years, not run for all 5
    assert len(results_df) == 3
    assert mock_strategy.calculate_annual_withdrawal.call_count == 3
    assert results_df["End Balance"].iloc[-1] == 0  # Final balance must be zero
    assert all_withdrawals == [40_000, 40_000, 40_000]


def test_simulator_mid_year_depletion():
    """Tests that the simulation stops correctly if the balance is depleted mid-year."""
    initial_balance = 50_000
    # A large negative return that will wipe out the balance
    mock_returns = [(-0.9, -0.9, 0.0)] * config.TRADINGDAYS
    mock_strategy = Mock(spec=BaseWithdrawalStrategy)
    mock_strategy.calculate_annual_withdrawal.return_value = 10_000 # Withdraw 10k

    sim = RetirementSimulator(
        returns=mock_returns,
        initial_balance=initial_balance,
        stock_allocation=1.0, # 100% stocks
        strategy=mock_strategy,
    )
    results_df, _ = sim.run()

    # Simulation should only run for one year and then stop
    assert len(results_df) == 1
    assert results_df["End Balance"].iloc[-1] == pytest.approx(0)


@patch('retirement_engine.simulator.data_loader')
@patch('retirement_engine.simulator.strategy_factory')
@patch('retirement_engine.simulator.RetirementSimulator')
def test_run_simulation_helper(MockRetirementSimulator, mock_strategy_factory, mock_data_loader):
    """Tests the run_simulation helper function."""
    # Setup mocks
    mock_strategy_obj = Mock()
    mock_strategy_factory.return_value = mock_strategy_obj
    mock_data_loader.from_csv.return_value = [(0.01, 0.005, 0.001)] * 2520
    mock_sim_instance = MockRetirementSimulator.return_value
    mock_sim_instance.run.return_value = (pd.DataFrame(), [])

    # Call the function
    run_simulation(
        etf_source='some_path.csv',
        strategy_name='fixed',
        initial_balance=1_500_000,
        sp500_weight=0.7,
        rate=0.05
    )

    # Assertions
    mock_strategy_factory.assert_called_once_with(
        'fixed', initial_balance=1_500_000, sp500_weight=0.7, rate=0.05
    )
    mock_data_loader.from_csv.assert_called_once()
    MockRetirementSimulator.assert_called_once_with(
        returns=mock_data_loader.from_csv.return_value,
        initial_balance=1_500_000,
        stock_allocation=0.7,
        strategy=mock_strategy_obj,
    )
    mock_sim_instance.run.assert_called_once()
