# /home/abqjuan/RetirementEngine/tests/test_strategies.py

import pytest
from src import config
from src.withdrawal_strategies import (
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
    assert isinstance(strategy, expected_class)


def test_strategy_factory_unknown():
    """Tests if the factory raises an error for an unknown strategy."""
    with pytest.raises(ValueError, match="Unknown strategy: 'unknown_strategy'"):
        strategy_factory("unknown_strategy")


# --- Test Individual Strategies ---


def test_fixed_withdrawal_inflation_adjustment():
    """Tests the inflation adjustment in the second year for FixedWithdrawal."""
    strategy = FixedWithdrawal(initial_balance=1_000_000, rate=0.04)

    # Year 1
    context1 = SimulationContext(
        year_index=0,
        current_balance=1_000_000,
        trailing_returns=[],
        initial_balance=1_000_000,
        stock_allocation=0.6,
        portfolio_weights={"us_equities": 0.6, "bonds": 0.4},
        previous_withdrawals=[],
    )
    withdrawal1 = strategy.calculate_annual_withdrawal(context1)
    assert withdrawal1 == 40_000.0

    # Year 2 - with 3% compounded inflation
    mock_trailing_returns = [(0, 0, 0.03 / config.TRADING_DAYS)] * config.TRADING_DAYS
    context2 = SimulationContext(
        year_index=1,
        current_balance=980_000,
        trailing_returns=mock_trailing_returns,
        initial_balance=1_000_000,
        stock_allocation=0.6,
        portfolio_weights={"us_equities": 0.6, "bonds": 0.4},
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
        portfolio_weights={"us_equities": 0.6, "bonds": 0.4},
        previous_withdrawals=[],
    )
    assert strategy.calculate_annual_withdrawal(context_year1) == 50_000.0
    assert not strategy.paused

    # Context for Year 2, following a year of losses
    # Simulate a -10% portfolio return
    mock_loss_returns = [
        (-0.1 / config.TRADING_DAYS, -0.1 / config.TRADING_DAYS, 0)
    ] * config.TRADING_DAYS
    context_year2_after_loss = SimulationContext(
        year_index=1,
        current_balance=900_000,
        trailing_returns=mock_loss_returns,
        initial_balance=1_000_000,
        stock_allocation=0.6,
        portfolio_weights={"us_equities": 0.6, "bonds": 0.4},
        previous_withdrawals=[50_000],
    )
    # Withdrawal should be paused (returns 0)
    assert strategy.calculate_annual_withdrawal(context_year2_after_loss) == 0.0
    assert strategy.paused

    # Context for Year 3, following a year of gains
    # Simulate a +10% portfolio return
    mock_gain_returns = [
        (0.1 / config.TRADING_DAYS, 0.1 / config.TRADING_DAYS, 0)
    ] * config.TRADING_DAYS
    context_year3_after_gain = SimulationContext(
        year_index=2,
        current_balance=990_000,
        trailing_returns=mock_gain_returns,
        initial_balance=1_000_000,
        stock_allocation=0.6,
        portfolio_weights={"us_equities": 0.6, "bonds": 0.4},
        previous_withdrawals=[50_000, 0],
    )
    # Withdrawal should resume
    withdrawal3 = strategy.calculate_annual_withdrawal(context_year3_after_gain)
    assert withdrawal3 > 0
    assert not strategy.paused
