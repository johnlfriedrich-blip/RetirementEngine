# monte_carlo.py
"""This module provides the core functionality for running Monte Carlo simulations.

It orchestrates multiple individual retirement simulations, each with a unique,
randomly generated market history, to analyze the statistical success of a given
withdrawal strategy.
"""

import pandas as pd
import multiprocessing
from typing import Any, Dict, Type
from functools import partial
import logging

from .market_data import MarketDataGenerator
from .simulator import RetirementSimulator
from .withdrawal_strategies import strategy_factory

# Configure basic logging to show simulation progress and errors.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
    A top-level function to run a single, isolated retirement simulation instance.

    This function is designed to be picklable by the `multiprocessing` module,
    which requires it to be defined at the top level of the module.

    Args:
        run_id (int): A unique identifier for this simulation run.
        duration_years (int): The number of years the simulation should last.
        market_data_gen_args (Dict): Arguments for the MarketDataGenerator.
        simulator_class (Type[RetirementSimulator]): The class to use for the simulation.
        strategy_name (str): The name of the withdrawal strategy.
        strategy_args (Dict): Arguments for the withdrawal strategy's constructor.
        full_results (bool): If True, return the full yearly history; otherwise, return
                             only the final year's data.

    Returns:
        A pandas DataFrame containing the simulation results. Returns an empty
        DataFrame if an error occurs.
    """
    try:
        logging.info(f"Starting simulation run {run_id}")
        # 1. Generate a new random market history for this single run.
        market_data_generator = MarketDataGenerator(**market_data_gen_args)
        returns = market_data_generator.generate_returns(duration_years)

        # 2. Create the strategy object for this run using the factory.
        strategy_obj = strategy_factory(strategy_name, **strategy_args)

        # 3. Instantiate and run the simulator with the generated data and strategy.
        sim = simulator_class(
            returns=returns,
            initial_balance=strategy_args.get("initial_balance", 1_000_000),
            stock_allocation=strategy_args.get("stock_allocation", 0.6),
            strategy=strategy_obj,
        )
        yearly_data_df, _ = sim.run()
        yearly_data_df["Run"] = run_id  # Tag the results with the run ID.
        logging.info(f"Finished simulation run {run_id}")

        if full_results:
            return yearly_data_df
        else:
            # Return only the last row to conserve memory when full history is not needed.
            return yearly_data_df.tail(1)
    except Exception as e:
        logging.error(f"Error in simulation run {run_id}: {e}")
        # Return an empty DataFrame to indicate that this run failed.
        return pd.DataFrame()


class MonteCarloSimulator:
    """
    Runs multiple retirement simulations to analyze the statistical success of a strategy.

    This class manages the execution of thousands of individual simulations, either in
    parallel or sequentially, and aggregates their results for analysis.
    """

    def __init__(
        self,
        num_simulations: int = 1000,
        duration_years: int = 30,
        simulator_class=RetirementSimulator,
        market_data_generator_args: dict = None,
        parallel: bool = True,
    ):
        """Initializes the MonteCarloSimulator.

        Args:
            num_simulations (int): The number of individual simulations to run.
            duration_years (int): The length of each simulation in years.
            simulator_class: The simulator class to use (for dependency injection).
            market_data_generator_args (dict): Arguments for the MarketDataGenerator.
            parallel (bool): If True, run simulations in parallel using multiprocessing.
        """
        self.num_simulations = num_simulations
        self.duration_years = duration_years
        self.market_data_generator_args = market_data_generator_args or {}
        self.results = None  # Will hold the concatenated results DataFrame.
        self.simulator_class = simulator_class
        self.parallel = parallel

    def run(
        self, strategy_name: str, full_results: bool = True, **strategy_args: Any
    ) -> pd.DataFrame:
        """
        Executes the full Monte Carlo simulation for a given strategy.

        Args:
            strategy_name (str): The name of the withdrawal strategy to test.
            full_results (bool): If True, returns the full history of all simulations.
                                 If False, returns only the final year of each simulation
                                 to conserve memory.
            **strategy_args: Arguments for the strategy's constructor.

        Returns:
            A pandas DataFrame containing the aggregated results of all simulations.
        """
        logging.info(f"Starting Monte Carlo simulation with {self.num_simulations} runs.")
        
        # Use functools.partial to create a worker function with fixed arguments.
        # This is necessary for passing the function to the multiprocessing pool.
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
            # Use a multiprocessing Pool to run simulations in parallel, distributing
            # the workload across available CPU cores.
            with multiprocessing.Pool() as pool:
                all_sim_results = pool.map(worker_func, range(self.num_simulations))
        else:
            # Run sequentially in a single process (useful for debugging).
            all_sim_results = [worker_func(i) for i in range(self.num_simulations)]

        # Filter out any failed runs, which are returned as empty DataFrames.
        successful_results = [res for res in all_sim_results if not res.empty]

        if not successful_results:
            logging.warning("All simulations failed.")
            self.results = pd.DataFrame()
            return self.results

        logging.info(f"{len(successful_results)} simulations finished. Concatenating results.")
        # Combine the results from all successful runs into a single DataFrame.
        self.results = pd.concat(successful_results, ignore_index=True)
        logging.info("Monte Carlo simulation complete.")
        return self.results

    def success_rate(self) -> float:
        """Calculates the percentage of simulations that did not run out of money.

        A simulation is considered successful if the ending balance is greater than zero.

        Raises:
            RuntimeError: If the simulation has not been run yet.

        Returns:
            The success rate as a float between 0.0 and 1.0.
        """
        if self.results is None:
            raise RuntimeError("Simulation has not been run yet. Call .run() first.")

        if self.results.empty:
            # If all simulations failed, the success rate is 0.
            return 0.0

        # If full_results was True, we need to find the final year for each run.
        if "Year" in self.results.columns:
            final_year_balances = self.results.loc[
                self.results.groupby("Run")["Year"].idxmax()
            ]
        else:
            # If full_results was False, the results already contain only final year data.
            final_year_balances = self.results

        # A successful run is one where the final balance is positive.
        successful_runs = final_year_balances[final_year_balances["End Balance"] > 0]
        return len(successful_runs) / self.num_simulations
