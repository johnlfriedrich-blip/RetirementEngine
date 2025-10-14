# tests/test_simulator.py
import pytest
import pandas as pd
from unittest.mock import MagicMock

from retirement_engine.simulator import RetirementSimulator
from retirement_engine.withdrawal_strategies import (
    FixedWithdrawal,
    DynamicWithdrawal,
    GuardrailsWithdrawal,
    strategy_factory,
)


@pytest.fixture
def mock_market_data():
    """
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
        returns=mock_returns,
        strategy=strategy,
    )
    assert isinstance(sim.strategy, DynamicWithdrawal)

    results_df, withdrawals = sim.run()

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
    )
    sim = RetirementSimulator(
        initial_balance=1_000_000,
        portfolio_weights=[1.0],
        returns=mock_returns,
        strategy=strategy,
    )
    assert isinstance(sim.strategy, GuardrailsWithdrawal)

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
