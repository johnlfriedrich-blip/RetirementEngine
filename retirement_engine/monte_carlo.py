# monte_carlo.py
import pandas as pd
import multiprocessing
from typing import Any, Dict, Type
from functools import partial
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from .market_data import MarketDataGenerator
from .simulator import RetirementSimulator
from .withdrawal_strategies import strategy_factory


def _run_single_simulation(
    run_id: int,
    duration_years: int,
    market_data_gen_args: Dict,
    simulator_class: Type[RetirementSimulator],
    strategy_name: str,
    strategy_args: Dict,
    full_results: bool,
) -> pd.DataFrame:
    """
    A top-level function to run a single simulation instance.
    This is required for multiprocessing to be able to pickle the function.
    """
    try:
        logging.info(f"Starting simulation run {run_id}")
        # 1. Generate a new random market history for this single run
        market_data_generator = MarketDataGenerator(**market_data_gen_args)
        returns = market_data_generator.generate_returns(duration_years)

        # 2. Create the strategy object for this run
        strategy_obj = strategy_factory(strategy_name, **strategy_args)

        # 3. Use the existing RetirementSimulator for the single run
        sim = simulator_class(
            returns=returns,
            initial_balance=strategy_args.get("initial_balance", 1_000_000),
            stock_allocation=strategy_args.get("stock_allocation", 0.6),
            strategy=strategy_obj,
        )
        yearly_data_df, _ = sim.run()
        yearly_data_df["Run"] = run_id
        logging.info(f"Finished simulation run {run_id}")

        if full_results:
            return yearly_data_df
        else:
            # Return only the last row for memory efficiency
            return yearly_data_df.tail(1)
    except Exception as e:
        logging.error(f"Error in simulation run {run_id}: {e}")
        # Return an empty DataFrame or some indicator of failure
        return pd.DataFrame()


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
        parallel: bool = True,  # New: Control parallel execution
    ):
        self.num_simulations = num_simulations
        self.duration_years = duration_years
        self.market_data_generator_args = market_data_generator_args or {}
        self.results = None
        self.simulator_class = simulator_class
        self.parallel = parallel

    def run(
        self, strategy_name: str, full_results: bool = True, **strategy_args: Any
    ) -> pd.DataFrame:
        """
        Executes the Monte Carlo simulation for a given strategy.

        Args:
            strategy_name: The name of the withdrawal strategy.
            full_results: If True, returns the full history of all simulations.
                          If False, returns only the final year of each simulation
                          to conserve memory.
            **strategy_args: Arguments for the strategy's constructor.

        Returns:
            A pandas DataFrame containing the results of all simulations.
        """
        logging.info(f"Starting Monte Carlo simulation with {self.num_simulations} runs.")
        worker_func = partial(
            _run_single_simulation,
            duration_years=self.duration_years,
            market_data_gen_args=self.market_data_generator_args,
            simulator_class=self.simulator_class,
            strategy_name=strategy_name,
            strategy_args=strategy_args,
            full_results=full_results,
        )

        if self.parallel:
            # Use a Pool to run simulations in parallel
            with multiprocessing.Pool() as pool:
                all_sim_results = pool.map(worker_func, range(self.num_simulations))
        else:
            # Run sequentially (useful for debugging)
            all_sim_results = [worker_func(i) for i in range(self.num_simulations)]

        # Filter out failed runs (which return empty DataFrames)
        successful_results = [res for res in all_sim_results if not res.empty]

        if not successful_results:
            logging.warning("All simulations failed.")
            self.results = pd.DataFrame()
            return self.results

        logging.info(f"{len(successful_results)} simulations finished. Concatenating results.")
        self.results = pd.concat(successful_results, ignore_index=True)
        logging.info("Monte Carlo simulation complete.")
        return self.results

    def success_rate(self) -> float:
        """Calculates the percentage of simulations that did not run out of money."""
        if self.results is None:
            raise RuntimeError("Simulation has not been run yet. Call .run() first.")

        # If full_results was False, self.results already contains only final year data
        if "Year" in self.results.columns:
            final_year_balances = self.results.loc[
                self.results.groupby("Run")["Year"].idxmax()
            ]
        else:
            final_year_balances = self.results

        successful_runs = final_year_balances[final_year_balances["End Balance"] > 0]
        return len(successful_runs) / self.num_simulations
