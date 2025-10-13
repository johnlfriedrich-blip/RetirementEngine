# tests/test_simulator.py
import pytest
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
    The simulator's `run` method accesses returns via integer index: `returns[day]`.
    """
    total_days = 252 * 30
    daily_return_tuple = (0.000378, 0.000117, 0.0)
    mock_df = MagicMock()
    mock_df.__getitem__.return_value = daily_return_tuple
    mock_df.__len__.return_value = total_days  # For the initialization test
    return mock_df


def test_simulator_initialization(mock_market_data):
    """Test the Simulator class initialization."""
    strategy = strategy_factory(
        "fixed", initial_balance=1_000_000, rate=0.04, sp500_weight=0.6
    )
    sim = RetirementSimulator(
        initial_balance=1_000_000,
        stock_allocation=0.6,
        returns=mock_market_data,
        strategy=strategy,
    )
    assert len(sim.returns) == 252 * 30
    assert sim.initial_balance == 1_000_000
    assert sim.stock_allocation == 0.6
    assert isinstance(sim.strategy, FixedWithdrawal)


def test_run_simulation(mock_market_data):
    """Test a single run of the simulation."""
    strategy = strategy_factory(
        "fixed", initial_balance=1_000_000, rate=0.04, sp500_weight=0.6
    )
    sim = RetirementSimulator(
        initial_balance=1_000_000,
        stock_allocation=0.6,
        returns=mock_market_data,
        strategy=strategy,
    )

    final_balances, final_withdrawals = sim.run()

    # We expect 30 years of withdrawals, one per year.
    assert len(final_withdrawals) == 30
    # The balance is recorded once per year.
    assert len(final_balances) == 30

    # With a fixed withdrawal and positive returns, the portfolio should survive.
    assert final_balances["End Balance"].iloc[-1] > 0

    # The first withdrawal should be 4% of the initial balance.
    assert final_withdrawals[0] == 40_000  # 1,000,000 * 0.04


def test_run_simulation_dynamic_strategy():
    """Test a simulation run with the dynamic withdrawal strategy."""
    # Mock returns: positive in year 1, negative in year 2
    returns_yr1 = [(0.0004, 0.0001, 0.0)] * 252  # Approx 10% annual return
    returns_yr2 = [(-0.0004, -0.0001, 0.0)] * 252  # Approx -10% annual return
    mock_returns = returns_yr1 + returns_yr2

    strategy = strategy_factory("dynamic", rate=0.04)
    sim = RetirementSimulator(
        initial_balance=1_000_000,
        stock_allocation=0.6,
        returns=mock_returns,
        strategy=strategy,
    )
    assert isinstance(sim.strategy, DynamicWithdrawal)

    results_df, withdrawals = sim.run()

    # First withdrawal is 4% of the initial balance
    assert withdrawals[0] == 40_000

    # After a year of positive returns, the balance will be higher, so the next withdrawal should be larger.
    # Start of Year 2 balance is End of Year 1 balance from the dataframe.
    start_of_year_2_balance = results_df["End Balance"].iloc[0]
    assert withdrawals[1] == pytest.approx(start_of_year_2_balance * 0.04)
    assert withdrawals[1] > withdrawals[0]


def test_run_simulation_guardrails_strategy():
    """Test the guardrails strategy under different market conditions."""
    # Year 1: Baseline
    # Year 2: Strong market growth, triggers lower guardrail (min_pct)
    # Year 3: Market crash, triggers upper guardrail (max_pct)
    # Year 4: Stable market, withdrawal is inflation-adjusted within guardrails
    returns_yr1 = [(0.0, 0.0, 0.02 / 252)] * 252  # 2% inflation
    returns_yr2 = [(0.001, 0.0, 0.02 / 252)] * 252  # ~28% growth, 2% inflation
    returns_yr3 = [(-0.002, 0.0, 0.02 / 252)] * 252  # ~-40% crash, 2% inflation
    returns_yr4 = [(0.0, 0.0, 0.02 / 252)] * 252  # 0% growth, 2% inflation
    mock_returns = returns_yr1 + returns_yr2 + returns_yr3 + returns_yr4

    strategy = strategy_factory(
        "guardrails",
        initial_balance=1_000_000,
        rate=0.04,
        min_pct=0.03,
        max_pct=0.05,
    )
    sim = RetirementSimulator(
        initial_balance=1_000_000,
        stock_allocation=1.0,  # 100% stock for clear results
        returns=mock_returns,
        strategy=strategy,
    )
    assert isinstance(sim.strategy, GuardrailsWithdrawal)

    results_df, withdrawals = sim.run()

    # --- Year 1: Initial Withdrawal ---
    # Withdrawal is 4% of initial balance.
    assert withdrawals[0] == 40_000
    balance_y1_end = results_df["End Balance"].iloc[0]

    # --- Year 2: Lower Guardrail (min_pct) Triggered ---
    # Portfolio grew significantly. Inflation-adjusted withdrawal would be too low.
    # Inflation-adjusted: 40000 * 1.02 = 40800.
    # Rate: 40800 / balance_y1_end is < 3%, so we must withdraw 3% of current balance.
    expected_withdrawal_y2 = balance_y1_end * 0.03
    assert withdrawals[1] == pytest.approx(expected_withdrawal_y2)
    assert withdrawals[1] > 40800  # The guardrail forced a larger withdrawal
    balance_y2_end = results_df["End Balance"].iloc[1]

    # --- Year 3: Upper Guardrail (max_pct) Triggered ---
    # Portfolio crashed. Inflation-adjusted withdrawal would be too high.
    # Inflation-adjusted: withdrawals[1] * 1.02
    # Rate: (withdrawals[1] * 1.02) / balance_y2_end is > 5%, so we must withdraw 5% of current balance.
    expected_withdrawal_y3 = balance_y2_end * 0.05
    assert withdrawals[2] == pytest.approx(expected_withdrawal_y3)
    assert withdrawals[2] < (
        withdrawals[1] * 1.02
    )  # The guardrail forced a smaller withdrawal
    balance_y3_end = results_df["End Balance"].iloc[2]

    # --- Year 4: Within Guardrails ---
    # Market is stable. Withdrawal should just be inflation-adjusted.
    # Inflation-adjusted: withdrawals[2] * 1.02
    expected_withdrawal_y4 = withdrawals[2] * (1 + 0.02)
    # Check the rate: expected_withdrawal_y4 / balance_y3_end should be between 3% and 5%
    current_rate = expected_withdrawal_y4 / balance_y3_end
    assert 0.03 < current_rate < 0.05
    assert withdrawals[3] == pytest.approx(expected_withdrawal_y4)
