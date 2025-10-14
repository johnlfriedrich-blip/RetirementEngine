import pandas as pd
from typing import Any

from .market_data import MarketDataGenerator
from .simulator import RetirementSimulator
from .withdrawal_strategies import strategy_factory


class MonteCarloSimulator:
    """
    Runs multiple retirement simulations to analyze strategy success.
    """

    def __init__(
        self,
        num_simulations: int = 1000,
        duration_years: int = 30,
        simulator_class=RetirementSimulator,
        market_data_generator_args: dict = None,
    ):
        self.num_simulations = num_simulations
        self.duration_years = duration_years
        if market_data_generator_args is None:
            market_data_generator_args = {}
        self.market_data_generator = MarketDataGenerator(**market_data_generator_args)
        self.results = None
        self.simulator_class = simulator_class

    def run(self, strategy_name: str, **strategy_args: Any) -> pd.DataFrame:
        """
        Executes the Monte Carlo simulation for a given strategy.

        Args:
            strategy_name: The name of the withdrawal strategy (e.g., 'fixed', 'guardrails').
            **strategy_args: Arguments for the strategy's constructor (e.g., initial_balance, rate).

        Returns:
            A pandas DataFrame containing the results of all simulations.
        """
        all_sim_results = []

        for i in range(self.num_simulations):
            # 1. Generate a new random market history for this single run
            returns = self.market_data_generator.generate_returns(self.duration_years)

            # 2. Create the strategy object for this run
            strategy_obj = strategy_factory(strategy_name, **strategy_args)

            # 3. Use the existing RetirementSimulator for the single run
            sim = self.simulator_class(
                returns=returns,
                initial_balance=strategy_args.get("initial_balance", 1_000_000),
                stock_allocation=strategy_args.get("stock_allocation", 0.6),
                strategy=strategy_obj,
            )
            yearly_data_df, _ = sim.run()
            yearly_data_df["Run"] = i
            all_sim_results.append(yearly_data_df)

        self.results = pd.concat(all_sim_results, ignore_index=True)
        return self.results

    def success_rate(self) -> float:
        """Calculates the percentage of simulations that did not run out of money."""
        if self.results is None:
            raise RuntimeError("Simulation has not been run yet. Call .run() first.")

        final_year_balances = self.results.loc[
            self.results.groupby("Run")["Year"].idxmax()
        ]
        successful_runs = final_year_balances[final_year_balances["End Balance"] > 0]
        return len(successful_runs) / self.num_simulations
