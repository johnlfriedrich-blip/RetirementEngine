import pandas as pd
from .withdrawal_strategies import SimulationContext
from .config import TRADING_DAYS


class RetirementSimulator:
    def __init__(
        self,
        returns,
        initial_balance,
        portfolio_weights,
        strategy,
        days_per_year=TRADING_DAYS,
    ):
        self.returns = returns
        self.initial_balance = initial_balance
        self.portfolio_weights = portfolio_weights
        self.strategy = strategy
        self.days_per_year = days_per_year

    def run(self):
        balance = self.initial_balance
        yearly_data = []
        all_withdrawals = []
        num_years = len(self.returns) // self.days_per_year

        for year_index in range(num_years):
            start_of_year_balance = balance
            day_of_withdrawal = year_index * self.days_per_year

            # Calculate the blended trailing returns for the context
            trailing_returns_start = max(0, day_of_withdrawal - self.days_per_year)
            trailing_returns_df = self.returns.iloc[
                trailing_returns_start:day_of_withdrawal
            ]

            trailing_returns_for_context = []
            if not trailing_returns_df.empty:
                for _, row in trailing_returns_df.iterrows():
                    sp500_r = row.get(
                        "us_equities", 0.0
                    )  # Assuming 'us_equities' is SP500
                    bonds_r = row.get("bonds", 0.0)  # Assuming 'bonds' is bonds
                    inflation_r = row.get(
                        "inflation_returns", 0.0
                    )  # Assuming 'inflation_returns' is available
                    trailing_returns_for_context.append((sp500_r, bonds_r, inflation_r))

            # Calculate a weighted stock allocation
            stock_allocation = self.portfolio_weights.get(
                "us_equities", 0.0
            ) + self.portfolio_weights.get("intl_equities", 0.0)

            context = SimulationContext(
                current_balance=balance,
                year_index=year_index,
                trailing_returns=trailing_returns_for_context,
                initial_balance=self.initial_balance,
                stock_allocation=stock_allocation,
                portfolio_weights=self.portfolio_weights,
                previous_withdrawals=list(all_withdrawals),
            )
            withdrawal_this_year = self.strategy.calculate_annual_withdrawal(context)
            balance -= withdrawal_this_year
            all_withdrawals.append(withdrawal_this_year)

            if balance <= 0:
                balance = 0
                yearly_data.append(
                    {
                        "Year": year_index + 1,
                        "Start Balance": start_of_year_balance,
                        "Withdrawal": withdrawal_this_year,
                        "End Balance": balance,
                    }
                )
                break

            start_day = year_index * self.days_per_year
            end_day = start_day + self.days_per_year
            for day in range(start_day, end_day):
                daily_returns = self.returns.iloc[day]
                blended_r = sum(
                    daily_returns[asset] * weight
                    for asset, weight in self.portfolio_weights.items()
                )
                balance *= 1 + blended_r
                if balance <= 0:
                    balance = 0
                    break

            yearly_data.append(
                {
                    "Year": year_index + 1,
                    "Start Balance": start_of_year_balance,
                    "Withdrawal": withdrawal_this_year,
                    "End Balance": balance,
                }
            )
            if balance <= 0:
                break

        return pd.DataFrame(yearly_data), all_withdrawals
