# retirement_engine/withdrawal_strategies.py
import abc


class BaseWithdrawalStrategy(abc.ABC):
    """Abstract base class for all withdrawal strategies."""

    @abc.abstractmethod
    def calculate_annual_withdrawal(self, context: dict) -> float:
        """
        Calculate the withdrawal amount for the current year.

        Args:
            context: A dictionary containing simulation state, e.g.,
                     'current_balance', 'year_index', etc.

        Returns:
            The calculated withdrawal amount for the year.
        """
        pass


class FixedWithdrawal(BaseWithdrawalStrategy):
    """Implements a fixed withdrawal strategy, adjusted for inflation."""

    def __init__(self, initial_balance: float, rate: float, **kwargs):
        self.initial_withdrawal = initial_balance * rate
        self.withdrawals = []

    def calculate_annual_withdrawal(self, context: dict) -> float:
        if context["year_index"] == 0:
            withdrawal = self.initial_withdrawal
        else:
            # For subsequent years, use previous withdrawal and adjust for inflation
            # by compounding the daily inflation rates from the previous year.
            compounded_inflation = 1.0
            if context["trailing_returns"]:
                for _, _, inflation_r in context["trailing_returns"]:
                    compounded_inflation *= 1 + inflation_r

            withdrawal = self.withdrawals[-1] * compounded_inflation

        self.withdrawals.append(withdrawal)
        return withdrawal


class DynamicWithdrawal(BaseWithdrawalStrategy):
    """Implements a dynamic withdrawal strategy based on a percentage of the current balance."""

    def __init__(self, rate: float, **kwargs):
        self.rate = rate

    def calculate_annual_withdrawal(self, context: dict) -> float:
        return context["current_balance"] * self.rate


class PauseAfterLossWithdrawal(BaseWithdrawalStrategy):
    """
    Implements a withdrawal strategy that pauses withdrawals for a year
    following a year of negative portfolio returns.
    """

    def __init__(self, rate: float, sp500_weight: float, **kwargs):
        self.rate = rate
        self.stock_allocation = sp500_weight
        self.paused = False

    def _calculate_portfolio_return(self, trailing_returns: list) -> float:
        """Calculates the blended portfolio return over the trailing period."""
        if not trailing_returns:
            return 0.0

        # Simulate the growth of $1 over the period
        balance = 1.0
        for sp500_r, bonds_r, _ in trailing_returns:
            blended_r = (
                self.stock_allocation * sp500_r + (1 - self.stock_allocation) * bonds_r
            )
            balance *= 1 + blended_r
        return balance - 1.0

    def calculate_annual_withdrawal(self, context: dict) -> float:
        if context["year_index"] > 0:
            # Check last year's performance to decide if we should pause/unpause
            last_year_return = self._calculate_portfolio_return(
                context["trailing_returns"]
            )
            self.paused = last_year_return < 0

        if self.paused:
            return 0.0
        else:
            # If not paused, withdraw a percentage of the current balance
            return context["current_balance"] * self.rate


class GuardrailsWithdrawal(BaseWithdrawalStrategy):
    """
    Implements a guardrails withdrawal strategy.

    This strategy adjusts the withdrawal amount based on inflation, but keeps the
    withdrawal rate (as a percentage of the current balance) within a predefined
    min/max band (the "guardrails").
    """

    def __init__(
        self,
        initial_balance: float,
        rate: float,
        min_pct: float,
        max_pct: float,
        **kwargs,
    ):
        if not 0 < min_pct <= max_pct:
            raise ValueError("Guardrails must satisfy 0 < min_pct <= max_pct.")
        self.initial_withdrawal = initial_balance * rate
        self.min_pct = min_pct
        self.max_pct = max_pct
        self.withdrawals = []

    def calculate_annual_withdrawal(self, context: dict) -> float:
        current_balance = context["current_balance"]

        if context["year_index"] == 0:
            withdrawal = self.initial_withdrawal
        else:
            # Calculate inflation-adjusted withdrawal based on the previous year
            compounded_inflation = 1.0
            if context["trailing_returns"]:
                for _, _, inflation_r in context["trailing_returns"]:
                    compounded_inflation *= 1 + inflation_r

            base_withdrawal = self.withdrawals[-1] * compounded_inflation

            # Apply guardrails
            min_withdrawal = current_balance * self.min_pct
            max_withdrawal = current_balance * self.max_pct
            withdrawal = max(min_withdrawal, min(base_withdrawal, max_withdrawal))

        self.withdrawals.append(withdrawal)
        return withdrawal


def strategy_factory(strategy_name: str, **kwargs) -> BaseWithdrawalStrategy:
    strategies = {
        "fixed": FixedWithdrawal,
        "dynamic": DynamicWithdrawal,
        "pause_after_loss": PauseAfterLossWithdrawal,
        "guardrails": GuardrailsWithdrawal,
    }
    strategy_class = strategies.get(strategy_name.lower())
    if not strategy_class:
        raise ValueError(f"Unknown strategy: '{strategy_name}'")
    return strategy_class(**kwargs)
