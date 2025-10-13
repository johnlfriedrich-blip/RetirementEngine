# tests/test_strategies.py
import pytest
from retirement_engine.withdrawal_strategies import (
    strategy_factory,
    FixedWithdrawal,
    DynamicWithdrawal,
    GuardrailsWithdrawal,
    PauseAfterLossWithdrawal,
)


@pytest.mark.parametrize(
    "strategy_name, expected_class",
    [
        ("fixed", FixedWithdrawal),
        ("dynamic", DynamicWithdrawal),
        ("guardrails", GuardrailsWithdrawal),
        ("pause_after_loss", PauseAfterLossWithdrawal),
    ],
)
def test_strategy_factory(strategy_name, expected_class):
    """Test that the strategy factory returns the correct strategy class."""
    strategy = strategy_factory(
        strategy_name,
        initial_balance=1_000_000,
        rate=0.04,
        sp500_weight=0.6,
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
        "trailing_returns": [],
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
        "trailing_returns": [],
    }
    withdrawal = strategy.calculate_annual_withdrawal(context)
    assert withdrawal == 44_000


def test_guardrails_withdrawal():
    """Test the GuardrailsWithdrawal strategy."""
    strategy = strategy_factory(
        "guardrails", initial_balance=1_000_000, rate=0.04, min_pct=0.03, max_pct=0.05
    )

    # --- Year 0: Initial Withdrawal ---
    # Should be initial_balance * rate
    context_y0 = {"current_balance": 1_000_000, "year_index": 0}
    withdrawal_y0 = strategy.calculate_annual_withdrawal(context_y0)
    assert withdrawal_y0 == 40_000

    # --- Year 1: Within Guardrails ---
    # Inflation-adjusted withdrawal is within the 3%-5% band.
    # Use a daily rate that compounds to ~2% annually.
    daily_inflation_for_2_pct_annual = (1 + 0.02) ** (1 / 252) - 1
    # Inflation-adjusted: 40000 * 1.02 = 40800. Rate: 40800 / 1_050_000 = 3.88%
    context_y1 = {
        "current_balance": 1_050_000,
        "year_index": 1,
        "trailing_returns": [(0.0, 0.0, daily_inflation_for_2_pct_annual)] * 252,
    }
    assert strategy.calculate_annual_withdrawal(context_y1) == pytest.approx(40800)

    # --- Year 2: Upper Guardrail (max_pct) Triggered ---
    # Market drops. Inflation-adjusted withdrawal would be > 5% of balance.
    # Inflation-adjusted: 40800 * 1.02 = 41616. Rate: 41616 / 800_000 = 5.2%
    context_y2 = {
        "current_balance": 800_000,
        "year_index": 2,
        "trailing_returns": [(0.0, 0.0, daily_inflation_for_2_pct_annual)] * 252,
    }
    # Withdrawal is capped at 5% of current balance: 800_000 * 0.05 = 40_000
    assert strategy.calculate_annual_withdrawal(context_y2) == pytest.approx(40000)

    # --- Year 3: Lower Guardrail (min_pct) Triggered ---
    # Market booms. Inflation-adjusted withdrawal would be < 3% of balance.
    # Inflation-adjusted: 40000 * 1.02 = 40800. Rate: 40800 / 1_400_000 = 2.9%
    context_y3 = {
        "current_balance": 1_400_000,
        "year_index": 3,
        "trailing_returns": [(0.0, 0.0, daily_inflation_for_2_pct_annual)] * 252,
    }
    # Withdrawal is boosted to 3% of current balance: 1_400_000 * 0.03 = 42_000
    assert strategy.calculate_annual_withdrawal(context_y3) == pytest.approx(42000)


def test_pause_after_loss_withdrawal():
    """Test the PauseAfterLossWithdrawal strategy."""
    strategy = strategy_factory("pause_after_loss", rate=0.04, sp500_weight=0.6)

    # Year 0: Initial withdrawal (no trailing returns to check)
    context_y0 = {
        "current_balance": 1_000_000,
        "year_index": 0,
        "trailing_returns": [],
        "stock_allocation": 0.6,
    }
    assert strategy.calculate_annual_withdrawal(context_y0) == 40_000
    assert strategy.paused is False

    # Year 1: Negative return in the previous year, should pause withdrawals
    loss_return = [(-0.001, 0.0, 0.0)] * 252  # Approx -22% annual stock return
    context_y1 = {
        "current_balance": 900_000,
        "year_index": 1,
        "trailing_returns": loss_return,
        "stock_allocation": 0.6,
    }
    assert strategy.calculate_annual_withdrawal(context_y1) == 0.0
    assert strategy.paused is True

    # Year 2: Positive return in the previous year, should un-pause
    gain_return = [(0.001, 0.0, 0.0)] * 252  # Approx +28% annual stock return
    context_y2 = {
        "current_balance": 950_000,
        "year_index": 2,
        "trailing_returns": gain_return,
        "stock_allocation": 0.6,
    }
    # Withdrawal resumes based on current balance
    assert strategy.calculate_annual_withdrawal(context_y2) == 950_000 * 0.04
    assert strategy.paused is False
