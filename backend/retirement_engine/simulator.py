import pandas as pd
from .withdrawal_strategies import SimulationContext

class RetirementSimulator:
    def __init__(
        self,
        returns,
        initial_balance,
        portfolio_weights,
        strategy,
        days_per_year=252,
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
            trailing_returns_df = self.returns.iloc[trailing_returns_start:day_of_withdrawal]

            blended_trailing_returns = []
            if not trailing_returns_df.empty:
                blended_trailing_returns = [
                    (
                        sum(
                            row[asset] * weight
                            for asset, weight in self.portfolio_weights.items()
                        ),
                        0.0,  # Bond return - not used by strategies that need trailing_returns
                        0.0,  # Inflation - not currently modeled in the synthetic data
                    )
                    for _, row in trailing_returns_df.iterrows()
                ]

            # Calculate a weighted stock allocation
            stock_allocation = self.portfolio_weights.get('us_equities', 0.0) + self.portfolio_weights.get('intl_equities', 0.0)

            context = SimulationContext(
                current_balance=balance,
                year_index=year_index,
                trailing_returns=blended_trailing_returns,
                initial_balance=self.initial_balance,
                stock_allocation=stock_allocation,
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
