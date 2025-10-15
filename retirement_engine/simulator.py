"""This module contains the core `RetirementSimulator` class.

This class is responsible for running a single retirement simulation from start to
finish, given a set of market returns and a withdrawal strategy.
"""

import pandas as pd
from .withdrawal_strategies import strategy_factory, SimulationContext
from . import config
from . import data_loader


class RetirementSimulator:
    """Manages the execution of a single retirement simulation run."""
    def __init__(
        self,
        returns,
        initial_balance,
        stock_allocation,
        strategy,
        days_per_year=config.TRADINGDAYS,
    ):
        """Initializes the RetirementSimulator.

        Args:
            returns (list): A list of daily return tuples (stock_return, bond_return, inflation_rate).
            initial_balance (float): The starting portfolio balance.
            stock_allocation (float): The proportion of the portfolio allocated to stocks.
            strategy (BaseWithdrawalStrategy): An instantiated withdrawal strategy object.
            days_per_year (int): The number of trading days in a year.
        """
        self.returns = returns
        self.initial_balance = initial_balance
        self.stock_allocation = stock_allocation
        self.strategy = strategy
        self.days_per_year = days_per_year

    def run(self):
        """Executes the single simulation loop from start to finish.

        The simulation proceeds year by year. In each year, it:
        1. Calculates the annual withdrawal amount based on the provided strategy.
        2. Deducts the withdrawal from the current balance.
        3. Applies daily market returns to the remaining balance.
        4. Records the state of the portfolio at the end of the year.

        The simulation stops if the balance is depleted at any point.

        Returns:
            A tuple containing:
            - pd.DataFrame: A DataFrame with the yearly simulation results.
            - list: A list of all annual withdrawal amounts.
        """
        balance = self.initial_balance
        yearly_data = []
        all_withdrawals = []
        num_years = len(self.returns) // self.days_per_year

        # --- Main Simulation Loop ---
        for year_index in range(num_years):
            start_of_year_balance = balance
            day_of_withdrawal = year_index * self.days_per_year

            # Prepare the context object for the withdrawal strategy.
            # This object provides a snapshot of the simulation's current state.
            context = SimulationContext(
                current_balance=balance,
                year_index=year_index,
                trailing_returns=self.returns[
                    max(0, day_of_withdrawal - self.days_per_year) : day_of_withdrawal
                ],
                initial_balance=self.initial_balance,
                stock_allocation=self.stock_allocation,
                previous_withdrawals=list(all_withdrawals),  # Pass a copy
            )
            
            # 1. Calculate and apply the annual withdrawal.
            withdrawal_this_year = self.strategy.calculate_annual_withdrawal(context)
            balance -= withdrawal_this_year
            all_withdrawals.append(withdrawal_this_year)

            # 2. Check for portfolio depletion immediately after withdrawal.
            if balance <= 0:
                balance = 0  # Clamp to zero for clean output.
                yearly_data.append(
                    {
                        "Year": year_index + 1,
                        "Start Balance": start_of_year_balance,
                        "Withdrawal": withdrawal_this_year,
                        "End Balance": balance,
                    }
                )
                break  # Exit the simulation loop as the portfolio is empty.

            # 3. Apply daily returns for the current year.
            start_day = year_index * self.days_per_year
            end_day = start_day + self.days_per_year
            for day in range(start_day, end_day):
                sp500_r, bonds_r, _ = self.returns[day]
                # Calculate the blended return based on the stock/bond allocation.
                blended_r = (
                    self.stock_allocation * sp500_r
                    + (1 - self.stock_allocation) * bonds_r
                )
                balance *= 1 + blended_r
                
                # Check for depletion mid-year after applying daily returns.
                if balance <= 0:
                    balance = 0
                    break # Exit the daily loop.

            # 4. Record the results for the year.
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
    """A helper function to easily run a single simulation with data loading.

    This function is a convenience wrapper that handles creating the strategy,
    loading data from a CSV, and running the simulator.

    Args:
        etf_source (str): The path to the market data CSV file.
        strategy_name (str): The name of the withdrawal strategy to use.
        **kwargs: Additional arguments for the strategy and simulator.

    Returns:
        The result of the `RetirementSimulator.run()` method.
    """
    # Use the factory to create the appropriate strategy object.
    strategy_obj = strategy_factory(strategy_name, **kwargs)

    # Load historical market data from the specified CSV file.
    returns = data_loader.from_csv(
        etf_source=etf_source,
        inflation_mean=kwargs.get("inflation_mean", 0.03),
        inflation_std_dev=kwargs.get("inflation_std_dev", 0.015),
    )

    # Initialize and run the simulator.
    sim = RetirementSimulator(
        returns=returns,
        initial_balance=kwargs.get("initial_balance", 1_000_000),
        stock_allocation=kwargs.get("sp500_weight", 0.6),
        strategy=strategy_obj,
    )
    return sim.run()
