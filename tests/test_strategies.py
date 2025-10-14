# tests/test_strategies.py
import pytest
import pandas as pd
from retirement_engine.withdrawal_strategies import (
    strategy_factory,
    FixedWithdrawal,
    DynamicWithdrawal,
    GuardrailsWithdrawal,
    PauseAfterLossWithdrawal,
    VariablePercentageWithdrawal,
)


@pytest.mark.parametrize(
    "strategy_name, expected_class",
    [
        ("fixed", FixedWithdrawal),
        ("dynamic", DynamicWithdrawal),
        ("guardrails", GuardrailsWithdrawal),
        ("pause_after_loss", PauseAfterLossWithdrawal),
        ("vpw", VariablePercentageWithdrawal),
    ],
)
def test_strategy_factory(strategy_name, expected_class):
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
    assert isinstance(strategy, expected_class)


def test_strategy_factory_invalid():
    """Test that the strategy factory raises an error for an invalid strategy."""
    with pytest.raises(ValueError, match="Unknown strategy: 'invalid_strategy'"):
        # We need to provide some kwargs that the factory might expect
        strategy_factory("invalid_strategy", initial_balance=1, rate=0.04)


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


def test_guardrails_withdrawal():
    """Test the GuardrailsWithdrawal strategy."""
    strategy = strategy_factory(
        "guardrails", initial_balance=1_000_000, rate=0.04, min_pct=0.03, max_pct=0.05
    )

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
