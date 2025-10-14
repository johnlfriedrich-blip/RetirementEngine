# /home/abqjuan/RetirementEngine/tests/test_strategies.py

import pytest
<<<<<<< HEAD
import pandas as pd
=======
from retirement_engine import config
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)
from retirement_engine.withdrawal_strategies import (
    FixedWithdrawal,
    DynamicWithdrawal,
    PauseAfterLossWithdrawal,
    GuardrailsWithdrawal,
    VariablePercentageWithdrawal,
    strategy_factory,
    SimulationContext,
)

# --- Test Strategy Factory ---


@pytest.mark.parametrize(
    "strategy_name, expected_class",
    [
        ("fixed", FixedWithdrawal),
        ("dynamic", DynamicWithdrawal),
        ("pause_after_loss", PauseAfterLossWithdrawal),
        ("guardrails", GuardrailsWithdrawal),
        ("vpw", VariablePercentageWithdrawal),
    ],
)
def test_strategy_factory(strategy_name, expected_class):
<<<<<<< HEAD
    """Test that the strategy factory returns the correct strategy class."""
    # Add start_age for the vpw strategy
    if strategy_name == "vpw":
        strategy = strategy_factory(
            strategy_name,
            initial_balance=1_000_000,
            rate=0.04,
            min_pct=0.03,
            max_pct=0.05,
            start_age=65,
        )
    else:
        strategy = strategy_factory(
            strategy_name,
            initial_balance=1_000_000,
            rate=0.04,
            min_pct=0.03,
            max_pct=0.05,
        )
=======
    """Tests that the factory returns the correct strategy class."""
    # Provide all possible arguments to satisfy all constructors.
    # The key change is adding 'stock_allocation'.
    args = {
        "initial_balance": 1_000_000,
        "rate": 0.04,
        "min_pct": 0.03,
        "max_pct": 0.05,
        "start_age": 65,
        "stock_allocation": 0.6,  # FIX: Added required argument
    }
    strategy = strategy_factory(strategy_name, **args)
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)
    assert isinstance(strategy, expected_class)


def test_strategy_factory_unknown():
    """Tests if the factory raises an error for an unknown strategy."""
    with pytest.raises(ValueError, match="Unknown strategy: 'unknown_strategy'"):
        strategy_factory("unknown_strategy")


<<<<<<< HEAD
def test_fixed_withdrawal():
    """Test the FixedWithdrawal strategy."""
    strategy = strategy_factory("fixed", initial_balance=1_000_000, rate=0.04)
    context = {
        "initial_balance": 1_000_000,
        "current_balance": 1_100_000,  # Should be ignored
        "year_index": 0,
        "trailing_returns": pd.DataFrame(),
    }
    withdrawal = strategy.calculate_annual_withdrawal(context)
    assert withdrawal == 40_000


def test_dynamic_withdrawal():
    """Test the DynamicWithdrawal strategy."""
    strategy = strategy_factory("dynamic", rate=0.04)
    context = {
        "initial_balance": 1_000_000,  # Should be ignored
        "current_balance": 1_100_000,
        "year_index": 0,
        "trailing_returns": pd.DataFrame(),
    }
    withdrawal = strategy.calculate_annual_withdrawal(context)
    assert withdrawal == 44_000
=======
# --- Test Individual Strategies ---


def test_fixed_withdrawal_inflation_adjustment():
    """Tests the inflation adjustment in the second year for FixedWithdrawal."""
    strategy = FixedWithdrawal(initial_balance=1_000_000, rate=0.04)
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)

    # Year 1
    context1 = SimulationContext(
        year_index=0,
        current_balance=1_000_000,
        trailing_returns=[],
        initial_balance=1_000_000,
        stock_allocation=0.6,
        previous_withdrawals=[],
    )
    withdrawal1 = strategy.calculate_annual_withdrawal(context1)
    assert withdrawal1 == 40_000.0

<<<<<<< HEAD
    # --- Year 0: Initial Withdrawal ---
    context_y0 = {"current_balance": 1_000_000, "year_index": 0}
    withdrawal_y0 = strategy.calculate_annual_withdrawal(context_y0)
    assert withdrawal_y0 == 40_000

    # --- Year 1: Within Guardrails ---
    daily_inflation_for_2_pct_annual = (1 + 0.02) ** (1 / 252) - 1
    trailing_returns_y1 = pd.DataFrame({'inflation': [daily_inflation_for_2_pct_annual] * 252})
    context_y1 = {
        "current_balance": 1_050_000,
        "year_index": 1,
        "trailing_returns": trailing_returns_y1,
    }
    assert strategy.calculate_annual_withdrawal(context_y1) == pytest.approx(40800)

    # --- Year 2: Upper Guardrail (max_pct) Triggered ---
    trailing_returns_y2 = pd.DataFrame({'inflation': [daily_inflation_for_2_pct_annual] * 252})
    context_y2 = {
        "current_balance": 800_000,
        "year_index": 2,
        "trailing_returns": trailing_returns_y2,
    }
    assert strategy.calculate_annual_withdrawal(context_y2) == pytest.approx(40000)

    # --- Year 3: Lower Guardrail (min_pct) Triggered ---
    trailing_returns_y3 = pd.DataFrame({'inflation': [daily_inflation_for_2_pct_annual] * 252})
    context_y3 = {
        "current_balance": 1_400_000,
        "year_index": 3,
        "trailing_returns": trailing_returns_y3,
    }
    assert strategy.calculate_annual_withdrawal(context_y3) == pytest.approx(42000)


def test_pause_after_loss_withdrawal():
    """Test the PauseAfterLossWithdrawal strategy."""
    strategy = strategy_factory("pause_after_loss", rate=0.04)

    # Year 0: Initial withdrawal (no trailing returns to check)
    context_y0 = {
        "current_balance": 1_000_000,
        "year_index": 0,
        "trailing_returns": pd.DataFrame(),
        "portfolio_weights": [0.6, 0.4],
    }
    assert strategy.calculate_annual_withdrawal(context_y0) == 40_000
    assert not strategy.paused

    # Year 1: Negative return in the previous year, should pause withdrawals
    loss_return = pd.DataFrame({'asset1': [-0.001] * 252, 'asset2': [0.0] * 252})
    context_y1 = {
        "current_balance": 900_000,
        "year_index": 1,
        "trailing_returns": loss_return,
        "portfolio_weights": [0.6, 0.4],
    }
    assert strategy.calculate_annual_withdrawal(context_y1) == 0.0
    assert strategy.paused

    # Year 2: Positive return in the previous year, should un-pause
    gain_return = pd.DataFrame({'asset1': [0.001] * 252, 'asset2': [0.0] * 252})
    context_y2 = {
        "current_balance": 950_000,
        "year_index": 2,
        "trailing_returns": gain_return,
        "portfolio_weights": [0.6, 0.4],
    }
    assert strategy.calculate_annual_withdrawal(context_y2) == 950_000 * 0.04
    assert not strategy.paused


def test_vpw_withdrawal():
    """Test the VariablePercentageWithdrawal strategy."""
    strategy = strategy_factory("vpw", start_age=65)

    # --- Year 0 (Age 65) ---
    context_y0 = {"current_balance": 1_000_000, "year_index": 0}
    assert strategy.calculate_annual_withdrawal(context_y0) == pytest.approx(40000)

    # --- Year 5 (Age 70) ---
    context_y5 = {"current_balance": 1_200_000, "year_index": 5}
    assert strategy.calculate_annual_withdrawal(context_y5) == pytest.approx(53280)


def test_vpw_age_cap():
    """Test that VPW uses the last available rate for ages beyond the table."""
    strategy = strategy_factory("vpw", start_age=90)

    # --- Year 10 (Age 100) ---
    context_y10 = {"current_balance": 50_000, "year_index": 10}
    assert strategy.calculate_annual_withdrawal(context_y10) == pytest.approx(50000)
=======
    # Year 2 - with 3% compounded inflation
    mock_trailing_returns = [(0, 0, 0.03 / config.TRADINGDAYS)] * config.TRADINGDAYS
    context2 = SimulationContext(
        year_index=1,
        current_balance=980_000,
        trailing_returns=mock_trailing_returns,
        initial_balance=1_000_000,
        stock_allocation=0.6,
        previous_withdrawals=[withdrawal1],  # Pass the history
    )
    withdrawal2 = strategy.calculate_annual_withdrawal(context2)

    # Expected: 40000 * (1 + 0.03/252)^252
    assert withdrawal2 == pytest.approx(40000 * 1.03045, rel=1e-4)


def test_pause_after_loss_withdrawal():
    """
    Tests the core logic of the PauseAfterLossWithdrawal strategy.
    """
    # FIX: Provide the required 'stock_allocation' argument.
    strategy = PauseAfterLossWithdrawal(rate=0.05, stock_allocation=0.6)

    # Context for Year 1 (no trailing returns, so should not be paused)
    context_year1 = SimulationContext(
        year_index=0,
        current_balance=1_000_000,
        trailing_returns=[],
        initial_balance=1_000_000,
        stock_allocation=0.6,
        previous_withdrawals=[],
    )
    assert strategy.calculate_annual_withdrawal(context_year1) == 50_000.0
    assert not strategy.paused

    # Context for Year 2, following a year of losses
    # Simulate a -10% portfolio return
    mock_loss_returns = [
        (-0.1 / config.TRADINGDAYS, -0.1 / config.TRADINGDAYS, 0)
    ] * config.TRADINGDAYS
    context_year2_after_loss = SimulationContext(
        year_index=1,
        current_balance=900_000,
        trailing_returns=mock_loss_returns,
        initial_balance=1_000_000,
        stock_allocation=0.6,
        previous_withdrawals=[50_000],
    )
    # Withdrawal should be paused (returns 0)
    assert strategy.calculate_annual_withdrawal(context_year2_after_loss) == 0.0
    assert strategy.paused

    # Context for Year 3, following a year of gains
    # Simulate a +10% portfolio return
    mock_gain_returns = [
        (0.1 / config.TRADINGDAYS, 0.1 / config.TRADINGDAYS, 0)
    ] * config.TRADINGDAYS
    context_year3_after_gain = SimulationContext(
        year_index=2,
        current_balance=990_000,
        trailing_returns=mock_gain_returns,
        initial_balance=1_000_000,
        stock_allocation=0.6,
        previous_withdrawals=[50_000, 0],
    )
    # Withdrawal should resume
    assert strategy.calculate_annual_withdrawal(context_year3_after_gain) > 0
    assert not strategy.paused
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)
