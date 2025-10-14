# tests/test_simulator.py
import pytest
import pandas as pd
<<<<<<< HEAD
from unittest.mock import MagicMock
=======
from unittest.mock import Mock, call
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)

from retirement_engine.simulator import RetirementSimulator
from retirement_engine import config
from retirement_engine.withdrawal_strategies import (
    BaseWithdrawalStrategy,
    SimulationContext,
)


def test_simulator_with_mock_strategy():
    """
<<<<<<< HEAD
    Pytest fixture for mock market data.
    Returns a DataFrame with daily returns for two assets and inflation.
    """
    total_days = 252 * 30
    data = {
        'asset1': [0.000378] * total_days,
        'asset2': [0.000117] * total_days,
        'inflation': [0.0001] * total_days,
    }
    return pd.DataFrame(data)
=======
    Tests the RetirementSimulator's core loop using a mock strategy.
    This test verifies that the simulator correctly calls the strategy,
    updates the balance, and generates the expected yearly results.
    """
    # 1. Set up test data and mock object
    initial_balance = 1_000_000
    num_years = 3
    days_per_year = config.TRADINGDAYS
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)

    # Create simple market data with zero returns to make calculations predictable
    mock_returns = [(0.0, 0.0, 0.0)] * (num_years * config.TRADINGDAYS)

<<<<<<< HEAD
def test_simulator_initialization(mock_market_data):
    """Test the Simulator class initialization."""
    strategy = strategy_factory(
        "fixed", initial_balance=1_000_000, rate=0.04
    )
    sim = RetirementSimulator(
        initial_balance=1_000_000,
        portfolio_weights=[0.6, 0.4],
        returns=mock_market_data,
        strategy=strategy,
    )
    assert len(sim.returns) == 252 * 30
    assert sim.initial_balance == 1_000_000
    assert sim.portfolio_weights == [0.6, 0.4]
    assert isinstance(sim.strategy, FixedWithdrawal)


def test_run_simulation(mock_market_data):
    """Test a single run of the simulation."""
    strategy = strategy_factory(
        "fixed", initial_balance=1_000_000, rate=0.04
    )
    sim = RetirementSimulator(
        initial_balance=1_000_000,
        portfolio_weights=[0.6, 0.4],
        returns=mock_market_data,
        strategy=strategy,
    )

    final_balances, final_withdrawals = sim.run()

    # We expect 30 years of withdrawals, one per year.
    assert len(final_withdrawals) == 30
    assert len(final_balances) == 30
    assert final_balances["End Balance"].iloc[-1] > 0
    assert final_withdrawals[0] == 40_000


def test_run_simulation_dynamic_strategy():
    """Test a simulation run with the dynamic withdrawal strategy."""
    returns_yr1 = pd.DataFrame({'asset1': [0.0004] * 252, 'asset2': [0.0001] * 252, 'inflation': [0.0] * 252})
    returns_yr2 = pd.DataFrame({'asset1': [-0.0004] * 252, 'asset2': [-0.0001] * 252, 'inflation': [0.0] * 252})
    mock_returns = pd.concat([returns_yr1, returns_yr2], ignore_index=True)

    strategy = strategy_factory("dynamic", rate=0.04)
    sim = RetirementSimulator(
        initial_balance=1_000_000,
        portfolio_weights=[0.6, 0.4],
=======
    # Create a mock strategy object that conforms to the BaseWithdrawalStrategy interface
    mock_strategy = Mock(spec=BaseWithdrawalStrategy)

    # Configure the mock to return a fixed withdrawal amount every time it's called
    fixed_withdrawal_amount = 50_000
    mock_strategy.calculate_annual_withdrawal.return_value = fixed_withdrawal_amount

    # 2. Instantiate and run the simulator
    sim = RetirementSimulator(
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)
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

<<<<<<< HEAD
    assert withdrawals[0] == 40_000
    start_of_year_2_balance = results_df["End Balance"].iloc[0]
    assert withdrawals[1] == pytest.approx(start_of_year_2_balance * 0.04)
    assert withdrawals[1] > withdrawals[0]


def test_run_simulation_guardrails_strategy():
    """Test the guardrails strategy under different market conditions."""
    returns_yr1 = pd.DataFrame({'asset1': [0.00139] * 252, 'inflation': [0.02 / 252] * 252})
    returns_yr2 = pd.DataFrame({'asset1': [-0.002] * 252, 'inflation': [0.02 / 252] * 252})
    returns_yr3 = pd.DataFrame({'asset1': [0.0011] * 252, 'inflation': [0.02 / 252] * 252})
    returns_yr4 = pd.DataFrame({'asset1': [0.0] * 252, 'inflation': [0.02 / 252] * 252})
    mock_returns = pd.concat([returns_yr1, returns_yr2, returns_yr3, returns_yr4], ignore_index=True)

    strategy = strategy_factory(
        "guardrails",
        initial_balance=1_000_000,
        rate=0.04,
        min_pct=0.03,
        max_pct=0.05,
=======
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
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)
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
<<<<<<< HEAD
        initial_balance=1_000_000,
        portfolio_weights=[1.0],
=======
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)
        returns=mock_returns,
        initial_balance=initial_balance,
        stock_allocation=0.6,
        strategy=mock_strategy,
    )
    results_df, all_withdrawals = sim.run()

<<<<<<< HEAD
    results_df, withdrawals = sim.run()

    assert withdrawals[0] == 40_000
    balance_y1_end = results_df["End Balance"].iloc[0]

    compounded_inflation_y1 = (1 + 0.02 / 252)**252
    base_withdrawal_y2 = withdrawals[0] * compounded_inflation_y1
    min_withdrawal_y2 = balance_y1_end * 0.03
    assert base_withdrawal_y2 < min_withdrawal_y2, "Lower guardrail should be triggered"
    assert withdrawals[1] == pytest.approx(min_withdrawal_y2)
    balance_y2_end = results_df["End Balance"].iloc[1]

    compounded_inflation_y2 = (1 + 0.02 / 252)**252
    base_withdrawal_y3 = withdrawals[1] * compounded_inflation_y2
    max_withdrawal_y3 = balance_y2_end * 0.05
    assert base_withdrawal_y3 > max_withdrawal_y3, "Upper guardrail should be triggered"
    assert withdrawals[2] == pytest.approx(max_withdrawal_y3)
    balance_y3_end = results_df["End Balance"].iloc[2]

    compounded_inflation_y3 = (1 + 0.02 / 252)**252
    expected_withdrawal_y4 = withdrawals[2] * compounded_inflation_y3
    min_withdrawal_y4 = balance_y3_end * 0.03
    max_withdrawal_y4 = balance_y3_end * 0.05
    assert min_withdrawal_y4 <= expected_withdrawal_y4 <= max_withdrawal_y4, "Withdrawal should be within guardrails"
    assert withdrawals[3] == pytest.approx(expected_withdrawal_y4)
=======
    # 3. Assertions
    # The simulation should stop after 3 years, not run for all 5
    assert len(results_df) == 3
    assert mock_strategy.calculate_annual_withdrawal.call_count == 3
    assert results_df["End Balance"].iloc[-1] == 0  # Final balance must be zero
    assert all_withdrawals == [40_000, 40_000, 40_000]
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)
