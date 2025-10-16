# tests/test_simulator.py
import pytest
import pandas as pd
from unittest.mock import Mock, call

from backend.retirement_engine.simulator import RetirementSimulator
from backend.retirement_engine.withdrawal_strategies import (
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
    days_per_year = 252

    # Create simple market data with zero returns to make calculations predictable
    mock_returns = pd.DataFrame({'asset1': [0.0] * (num_years * days_per_year)})

    # Create a mock strategy object that conforms to the BaseWithdrawalStrategy interface
    mock_strategy = Mock(spec=BaseWithdrawalStrategy)

    # Configure the mock to return a fixed withdrawal amount every time it's called
    fixed_withdrawal_amount = 50_000
    mock_strategy.calculate_annual_withdrawal.return_value = fixed_withdrawal_amount

    # 2. Instantiate and run the simulator
    sim = RetirementSimulator(
        returns=mock_returns,
        initial_balance=initial_balance,
        portfolio_weights={'asset1': 1.0},
        strategy=mock_strategy,
        days_per_year=days_per_year,
    )
    results_df, all_withdrawals = sim.run()

    # 3. Make assertions
    assert mock_strategy.calculate_annual_withdrawal.call_count == num_years
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
    assert second_context.current_balance == pytest.approx(initial_balance - fixed_withdrawal_amount)
    assert second_context.previous_withdrawals == [fixed_withdrawal_amount]

    assert len(results_df) == num_years
    assert all_withdrawals == [50_000, 50_000, 50_000]

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
    days_per_year = 252
    mock_returns = pd.DataFrame({'asset1': [0.0] * (num_years * days_per_year)})

    mock_strategy = Mock(spec=BaseWithdrawalStrategy)
    mock_strategy.calculate_annual_withdrawal.return_value = 40_000

    # 2. Run simulation
    sim = RetirementSimulator(
        returns=mock_returns,
        initial_balance=initial_balance,
        portfolio_weights={'asset1': 1.0},
        strategy=mock_strategy,
    )
    results_df, all_withdrawals = sim.run()

    # 3. Assertions
    assert len(results_df) == 3
    assert mock_strategy.calculate_annual_withdrawal.call_count == 3
    assert results_df["End Balance"].iloc[-1] == 0
    assert all_withdrawals == [40_000, 40_000, 40_000]
