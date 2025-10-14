import pandas as pd
import numpy as np
from .withdrawal_strategies import strategy_factory
from . import data_loader


class RetirementSimulator:
    def __init__(
        self,
        returns,
        initial_balance,
        portfolio_weights,
        strategy,
        days_per_year=config.TRADINGDAYS,
    ):
        self.returns = returns
        self.initial_balance = initial_balance
        self.portfolio_weights = portfolio_weights
        self.strategy = strategy
        self.days_per_year = days_per_year

    def run(self):
        # Single simulation loop
        balance = self.initial_balance
        yearly_data = []
        all_withdrawals = []
        num_years = len(self.returns) // self.days_per_year

        for year_index in range(num_years):
            start_of_year_balance = balance
            day_of_withdrawal = year_index * self.days_per_year

            # Prepare context for the strategy
            context = SimulationContext(
                current_balance=balance,
                year_index=year_index,
                trailing_returns=self.returns[
                    max(0, day_of_withdrawal - self.days_per_year) : day_of_withdrawal
                ],
                "initial_balance": self.initial_balance,
                "portfolio_weights": self.portfolio_weights,
            }
            withdrawal_this_year = self.strategy.calculate_annual_withdrawal(context)
            balance -= withdrawal_this_year
            all_withdrawals.append(withdrawal_this_year)

            # If balance is depleted after withdrawal, record the final state and stop.
            if balance <= 0:
                balance = 0  # Clamp to zero for clean output
                yearly_data.append(
                    {
                        "Year": year_index + 1,
                        "Start Balance": start_of_year_balance,
                        "Withdrawal": withdrawal_this_year,
                        "End Balance": balance,
                    }
                )
                break  # Exit the simulation loop

            # Apply daily returns for the year
            start_day = year_index * self.days_per_year
            end_day = start_day + self.days_per_year
            for day in range(start_day, end_day):
                daily_returns = self.returns.iloc[day].drop('inflation', errors='ignore')
                blended_r = np.dot(daily_returns, self.portfolio_weights)
                balance *= 1 + blended_r
                # If balance is depleted mid-year, stop daily calculations.
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
            # If balance was depleted mid-year, exit the main simulation loop.
            if balance <= 0:
                break

        return pd.DataFrame(yearly_data), all_withdrawals


def run_simulation(etf_source, strategy_name, **kwargs):
    # Use the factory to create the appropriate strategy object
    strategy_obj = strategy_factory(strategy_name, **kwargs)

    returns = data_loader.from_csv(
        etf_source=etf_source,
        inflation_mean=kwargs.get("inflation_mean", 0.03),
        inflation_std_dev=kwargs.get("inflation_std_dev", 0.015),
    )

    sim = RetirementSimulator(
        returns=returns,
        initial_balance=kwargs.get("initial_balance", 1_000_000),
        portfolio_weights=kwargs.get("portfolio_weights", [0.6, 0.4]),
        strategy=strategy_obj,
    )
    return sim.run()
