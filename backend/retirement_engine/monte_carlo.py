# monte_carlo.py
import pandas as pd
import multiprocessing
from typing import Type
from functools import partial
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from .simulator import RetirementSimulator
from .withdrawal_strategies import BaseWithdrawalStrategy
from . import data_loader

def _run_single_simulation(
    run_id: int,
    data_source: str,
    simulator_class: Type[RetirementSimulator],
    withdrawal_strategy: BaseWithdrawalStrategy,
    start_balance: float,
    simulation_years: int,
    portfolio_weights: dict,
    historical_data_params: dict,
    synthetic_data_params: dict,
) -> pd.DataFrame:
    """
    A top-level function to run a single simulation instance.
    This is required for multiprocessing to be able to pickle the function.
    """
    try:
        if data_source == 'historical':
            returns = data_loader.from_historical_data(
                num_years=simulation_years, **historical_data_params
            )
        elif data_source == 'synthetic':
            returns = data_loader.from_synthetic_data(
                num_years=simulation_years, **synthetic_data_params
            )
        else:
            raise ValueError(f"Invalid data source: {data_source}")

        # Convert returns to a DataFrame
        returns_df = pd.DataFrame(returns, columns=['us_equities', 'bonds', 'inflation_returns'])

        sim = simulator_class(
            returns=returns_df,
            initial_balance=start_balance,
            portfolio_weights=portfolio_weights,
            strategy=withdrawal_strategy,
        )
        yearly_data_df, _ = sim.run()
        yearly_data_df["Run"] = run_id

        # Return only the last row for memory efficiency
        return yearly_data_df.tail(1)
    except Exception as e:
        logging.error(f"Error in simulation run {run_id}: {e}")
        return pd.DataFrame()


class MonteCarloResults:
    def __init__(self, results_df: pd.DataFrame, num_simulations: int):
        self.results_df = results_df
        self.num_simulations = num_simulations

    def success_rate(self) -> float:
        if self.results_df.empty:
            return 0.0
        successful_runs = self.results_df[self.results_df["End Balance"] > 0]
        return len(successful_runs) / self.num_simulations

    def median_final_balance(self) -> float:
        if self.results_df.empty:
            return 0.0
        return self.results_df["End Balance"].median()


class MonteCarloSimulator:
    def __init__(
        self,
        data_source: str,
        withdrawal_strategy: BaseWithdrawalStrategy,
        start_balance: float,
        simulation_years: int,
        portfolio_weights: dict,
        num_simulations: int = 1000,
        simulator_class=RetirementSimulator,
        parallel: bool = True,
        historical_data_params: dict = {},
        synthetic_data_params: dict = {},
    ):
        self.data_source = data_source
        self.withdrawal_strategy = withdrawal_strategy
        self.start_balance = start_balance
        self.simulation_years = simulation_years
        self.portfolio_weights = portfolio_weights
        self.num_simulations = num_simulations
        self.simulator_class = simulator_class
        self.parallel = parallel
        self.historical_data_params = historical_data_params
        self.synthetic_data_params = synthetic_data_params

    def run_simulations(self) -> MonteCarloResults:
        logging.info(f"Starting Monte Carlo simulation with {self.num_simulations} runs using {self.data_source} data.")
        worker_func = partial(
            _run_single_simulation,
            data_source=self.data_source,
            simulator_class=self.simulator_class,
            withdrawal_strategy=self.withdrawal_strategy,
            start_balance=self.start_balance,
            simulation_years=self.simulation_years,
            portfolio_weights=self.portfolio_weights,
            historical_data_params=self.historical_data_params,
            synthetic_data_params=self.synthetic_data_params,
        )

        if self.parallel:
            with multiprocessing.Pool() as pool:
                all_sim_results = pool.map(worker_func, range(self.num_simulations))
        else:
            all_sim_results = [worker_func(i) for i in range(self.num_simulations)]

        successful_results = [res for res in all_sim_results if not res.empty]

        if not successful_results:
            logging.warning("All simulations failed.")
            results_df = pd.DataFrame()
        else:
            results_df = pd.concat(successful_results, ignore_index=True)

        logging.info("Monte Carlo simulation complete.")
        return MonteCarloResults(results_df, self.num_simulations)

