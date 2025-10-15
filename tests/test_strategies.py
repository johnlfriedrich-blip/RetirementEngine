# /home/abqjuan/RetirementEngine/tests/test_strategies.py

import pytest
from retirement_engine import config
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
        previous_withdrawals=[],
    )
    withdrawal1 = strategy.calculate_annual_withdrawal(context1)
    assert withdrawal1 == 40_000.0

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


def test_dynamic_withdrawal():
    """Tests the DynamicWithdrawal strategy."""
    strategy = DynamicWithdrawal(rate=0.04)
    context = SimulationContext(
        year_index=0,
        current_balance=1_200_000,
        trailing_returns=[],
        initial_balance=1_000_000,
        stock_allocation=0.6,
        previous_withdrawals=[],
    )
    assert strategy.calculate_annual_withdrawal(context) == 1_200_000 * 0.04


def test_guardrails_withdrawal_initialization_error():
    """Tests that GuardrailsWithdrawal raises an error for invalid guardrails."""
    with pytest.raises(ValueError, match="Guardrails must satisfy 0 < min_pct <= max_pct."):
        GuardrailsWithdrawal(initial_balance=1_000_000, rate=0.04, min_pct=0.05, max_pct=0.03)


@pytest.mark.parametrize(
    "balance, prev_withdrawal, expected_outcome",
    [
        # Scenario 1: Base withdrawal is within guardrails
        (1_000_000, 40_000, 41_200),  # 40k * 1.03 = 41.2k, which is between 30k and 50k
        # Scenario 2: Base withdrawal is below the lower guardrail (min_pct)
        (1_500_000, 40_000, 45_000),  # 41.2k is less than 1.5M * 3% = 45k, so use 45k
        # Scenario 3: Base withdrawal is above the upper guardrail (max_pct)
        (700_000, 40_000, 35_000),  # 41.2k is more than 700k * 5% = 35k, so use 35k
    ],
)
def test_guardrails_withdrawal_scenarios(balance, prev_withdrawal, expected_outcome):
    """Tests the different scenarios for the GuardrailsWithdrawal strategy."""
    strategy = GuardrailsWithdrawal(
        initial_balance=1_000_000, rate=0.04, min_pct=0.03, max_pct=0.05
    )
    # 3% inflation
    mock_trailing_returns = [(0, 0, 0.03 / config.TRADINGDAYS)] * config.TRADINGDAYS
    context = SimulationContext(
        year_index=1,
        current_balance=balance,
        trailing_returns=mock_trailing_returns,
        initial_balance=1_000_000,
        stock_allocation=0.6,
        previous_withdrawals=[prev_withdrawal],
    )
    assert strategy.calculate_annual_withdrawal(context) == pytest.approx(expected_outcome, rel=1e-2)


def test_variable_percentage_withdrawal_initialization_error():
    """Tests that VariablePercentageWithdrawal raises an error for an invalid start age."""
    with pytest.raises(ValueError, match="Start age must be between 65 and 94"):
        VariablePercentageWithdrawal(start_age=64)


def test_variable_percentage_withdrawal():
    """Tests the VariablePercentageWithdrawal strategy for ages inside and outside the table."""
    # Age inside the table
    strategy_70 = VariablePercentageWithdrawal(start_age=70)
    context_70 = SimulationContext(
        year_index=0, current_balance=1_000_000, trailing_returns=[], initial_balance=1_000_000, stock_allocation=0.6, previous_withdrawals=[]
    )
    assert strategy_70.calculate_annual_withdrawal(context_70) == 1_000_000 * 0.0444

    # Age outside the table (should use the max rate)
    strategy_100 = VariablePercentageWithdrawal(start_age=90)
    context_100 = SimulationContext(
        year_index=10, current_balance=500_000, trailing_returns=[], initial_balance=1_000_000, stock_allocation=0.6, previous_withdrawals=[]
    ) # age = 90 + 10 = 100
    assert strategy_100.calculate_annual_withdrawal(context_100) == 500_000 * 1.0


def test_pause_after_loss_no_trailing_returns():
    """Tests PauseAfterLossWithdrawal's _calculate_portfolio_return with no trailing returns."""
    strategy = PauseAfterLossWithdrawal(rate=0.05, stock_allocation=0.6)
    assert strategy._calculate_portfolio_return([], 0.6) == 0.0
