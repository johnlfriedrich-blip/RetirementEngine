# retirement_engine/withdrawal_strategies.py
"""This module defines the various withdrawal strategies available in the simulation.

It includes a base class for all strategies and several concrete implementations,
_such as fixed withdrawal, dynamic percentage-based withdrawal, and more complex
_strategies like guardrails and variable percentage withdrawal (VPW).
"""

import abc
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class SimulationContext:
    """A data object holding the state of the simulation for a given year.

    This object is passed to a withdrawal strategy's `calculate_annual_withdrawal`
    method to provide all the necessary information to make a withdrawal decision.
    The `frozen=True` argument makes instances of this class immutable.

    Attributes:
        current_balance (float): The portfolio balance at the start of the current year.
        year_index (int): The zero-based index of the current simulation year.
        initial_balance (float): The starting balance of the portfolio at year 0.
        stock_allocation (float): The proportion of the portfolio allocated to stocks (e.g., 0.6 for 60%).
        trailing_returns (List[Tuple[float, float, float]]): A list of the previous year's
            daily returns for (stocks, bonds, inflation).
        previous_withdrawals (List[float]): A list of all withdrawal amounts from previous years.
    """

    current_balance: float
    year_index: int
    initial_balance: float
    stock_allocation: float
    trailing_returns: List[Tuple[float, float, float]]
    previous_withdrawals: List[float]


class BaseWithdrawalStrategy(abc.ABC):
    """Abstract base class for all withdrawal strategies.

    All concrete withdrawal strategies must inherit from this class and implement
    the `calculate_annual_withdrawal` method.
    """

    @abc.abstractmethod
    def calculate_annual_withdrawal(self, context: SimulationContext) -> float:
        """
        Calculate the withdrawal amount for the current year.

        This is the core method for any strategy. It takes the simulation context
        and returns the dollar amount to be withdrawn for the current year.

        Args:
            context: An object containing the current simulation state.

        Returns:
            The calculated withdrawal amount for the year.
        """
        pass


class FixedWithdrawal(BaseWithdrawalStrategy):
    """Implements a fixed withdrawal strategy, adjusted for inflation.

    In this strategy, the initial withdrawal is a fixed percentage of the initial
    balance. In subsequent years, the withdrawal amount is adjusted based on the
    compounded inflation from the previous year.
    """

    def __init__(self, initial_balance: float, rate: float, **kwargs):
        """Initializes the FixedWithdrawal strategy.

        Args:
            initial_balance (float): The starting portfolio balance.
            rate (float): The initial withdrawal rate (e.g., 0.04 for 4%).
            **kwargs: Catches unused arguments from the strategy factory.
        """
        self.initial_withdrawal = initial_balance * rate

    def calculate_annual_withdrawal(self, context: SimulationContext) -> float:
        """Calculates the withdrawal, adjusting for inflation after the first year."""
        if context.year_index == 0:
            # For the first year, use the pre-calculated initial withdrawal.
            return self.initial_withdrawal
        else:
            # For subsequent years, adjust the *previous* year's withdrawal for inflation.
            compounded_inflation = 1.0
            if context.trailing_returns:
                # Compound the daily inflation rates from the previous year.
                for _, _, inflation_r in context.trailing_returns:
                    compounded_inflation *= 1 + inflation_r

            # Apply the compounded inflation to the last withdrawal amount.
            return context.previous_withdrawals[-1] * compounded_inflation


class DynamicWithdrawal(BaseWithdrawalStrategy):
    """Implements a dynamic withdrawal strategy based on a percentage of the current balance.

    This is the simplest strategy, where the withdrawal is always a fixed percentage
    of the current portfolio balance at the time of withdrawal.
    """

    def __init__(self, rate: float, **kwargs):
        """Initializes the DynamicWithdrawal strategy.

        Args:
            rate (float): The withdrawal rate (e.g., 0.04 for 4%).
            **kwargs: Catches unused arguments from the strategy factory.
        """
        self.rate = rate

    def calculate_annual_withdrawal(self, context: SimulationContext) -> float:
        """Calculates the withdrawal as a simple percentage of the current balance."""
        return context.current_balance * self.rate


class PauseAfterLossWithdrawal(BaseWithdrawalStrategy):
    """
    Implements a withdrawal strategy that pauses withdrawals for a year
    following a year of negative portfolio returns.
    """

    def __init__(self, rate: float, stock_allocation: float, **kwargs):
        """Initializes the PauseAfterLossWithdrawal strategy.

        Args:
            rate (float): The withdrawal rate to use in non-paused years.
            stock_allocation (float): The stock allocation, needed to calculate portfolio returns.
            **kwargs: Catches unused arguments from the strategy factory.
        """
        self.rate = rate
        self.paused = False # State to track if the withdrawal is currently paused.

    def _calculate_portfolio_return(
        self, trailing_returns: list, stock_allocation: float
    ) -> float:
        """Calculates the blended portfolio return over the trailing period."""
        if not trailing_returns:
            return 0.0

        # Simulate the growth of $1 over the period to find the total return.
        balance = 1.0
        for sp500_r, bonds_r, _ in trailing_returns:
            blended_r = stock_allocation * sp500_r + (1 - stock_allocation) * bonds_r
            balance *= 1 + blended_r
        return balance - 1.0

    def calculate_annual_withdrawal(self, context: SimulationContext) -> float:
        """Pauses withdrawal if last year had a negative return."""
        if context.year_index > 0:
            # Check last year's performance to decide if we should pause or unpause.
            last_year_return = self._calculate_portfolio_return(
                context.trailing_returns, context.stock_allocation
            )
            self.paused = last_year_return < 0

        if self.paused:
            return 0.0
        else:
            # If not paused, withdraw a percentage of the current balance.
            return context.current_balance * self.rate


class GuardrailsWithdrawal(BaseWithdrawalStrategy):
    """
    Implements a guardrails withdrawal strategy.

    This strategy adjusts the withdrawal amount based on inflation, but keeps the
    withdrawal rate (as a percentage of the current balance) within a predefined
    min/max band (the "guardrails"). This prevents withdrawals from becoming too
    large in a down market or too small in a bull market.
    """

    def __init__(
        self,
        initial_balance: float,
        rate: float,
        min_pct: float,
        max_pct: float,
        **kwargs,
    ):
        """Initializes the GuardrailsWithdrawal strategy.

        Args:
            initial_balance (float): The starting portfolio balance.
            rate (float): The initial withdrawal rate.
            min_pct (float): The minimum withdrawal as a percentage of the current balance.
            max_pct (float): The maximum withdrawal as a percentage of the current balance.
            **kwargs: Catches unused arguments.
        """
        if not 0 < min_pct <= max_pct:
            raise ValueError("Guardrails must satisfy 0 < min_pct <= max_pct.")
        self.initial_withdrawal = initial_balance * rate
        self.min_pct = min_pct
        self.max_pct = max_pct

    def calculate_annual_withdrawal(self, context: SimulationContext) -> float:
        """Calculates withdrawal, applying guardrails to the inflation-adjusted amount."""
        if context.year_index == 0:
            return self.initial_withdrawal
        else:
            current_balance = context.current_balance
            # Calculate the base withdrawal by adjusting the previous year's for inflation.
            compounded_inflation = 1.0
            if context.trailing_returns:
                for _, _, inflation_r in context.trailing_returns:
                    compounded_inflation *= 1 + inflation_r

            base_withdrawal = context.previous_withdrawals[-1] * compounded_inflation

            # Define the guardrails: a floor and a ceiling for the withdrawal amount.
            min_withdrawal = current_balance * self.min_pct
            max_withdrawal = current_balance * self.max_pct
            
            # Clamp the base withdrawal between the min and max guardrails.
            return max(min_withdrawal, min(base_withdrawal, max_withdrawal))


# VPW rates based on a simplified model, assuming increasing withdrawal rates with age.
# This table is a core part of the Variable Percentage Withdrawal strategy.
VPW_RATES = {
    65: 0.0400, 66: 0.0408, 67: 0.0417, 68: 0.0426, 69: 0.0435,
    70: 0.0444, 71: 0.0455, 72: 0.0465, 73: 0.0476, 74: 0.0488,
    75: 0.0500, 76: 0.0513, 77: 0.0526, 78: 0.0541, 79: 0.0556,
    80: 0.0571, 81: 0.0588, 82: 0.0606, 83: 0.0625, 84: 0.0645,
    85: 0.0667, 86: 0.0689, 87: 0.0714, 88: 0.0741, 89: 0.0769,
    90: 0.0800, 91: 0.0833, 92: 0.0870, 93: 0.0909, 94: 0.0952,
    95: 1.0,  # Withdraw all remaining at age 95 to ensure portfolio is used.
}


class VariablePercentageWithdrawal(BaseWithdrawalStrategy):
    """
    Implements the Variable Percentage Withdrawal (VPW) strategy.
    
    Withdrawal amount is a percentage of the current balance, where the percentage
    increases with age based on a predefined schedule (VPW_RATES).
    """

    def __init__(self, start_age: int, **kwargs):
        """Initializes the VPW strategy.

        Args:
            start_age (int): The age at which the simulation begins.
            **kwargs: Catches unused arguments.
        """
        if start_age not in VPW_RATES:
            # Ensure the provided start age is within the bounds of the VPW table.
            min_age, max_age = min(VPW_RATES.keys()), max(VPW_RATES.keys())
            raise ValueError(f"Start age must be between {min_age} and {max_age-1}")
        self.start_age = start_age

    def calculate_annual_withdrawal(self, context: SimulationContext) -> float:
        """Calculates withdrawal based on the current age and the VPW table."""
        current_age = self.start_age + context.year_index

        # Get the withdrawal rate for the current age.
        # If age exceeds the table, use the last available rate (which is 1.0 at age 95).
        rate = VPW_RATES.get(current_age, VPW_RATES[max(VPW_RATES.keys())])

        return context.current_balance * rate


def strategy_factory(strategy_name: str, **kwargs) -> BaseWithdrawalStrategy:
    """A factory function to create withdrawal strategy objects from their names.

    This decouples the simulation logic from the concrete strategy classes.

    Args:
        strategy_name (str): The name of the strategy to create (e.g., 'fixed').
        **kwargs: Arguments to be passed to the strategy's constructor.

    Raises:
        ValueError: If the strategy_name is unknown.

    Returns:
        An instance of a BaseWithdrawalStrategy subclass.
    """
    strategies = {
        "fixed": FixedWithdrawal,
        "dynamic": DynamicWithdrawal,
        "pause_after_loss": PauseAfterLossWithdrawal,
        "guardrails": GuardrailsWithdrawal,
        "vpw": VariablePercentageWithdrawal,
    }
    strategy_class = strategies.get(strategy_name.lower())
    if not strategy_class:
        raise ValueError(f"Unknown strategy: '{strategy_name}'")
    # Instantiate the chosen strategy class with the provided arguments.
    return strategy_class(**kwargs)
