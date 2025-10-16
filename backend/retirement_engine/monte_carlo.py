# monte_carlo.py
import pandas as pd
import multiprocessing
from typing import Type
from functools import partial
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from .simulator import RetirementSimulator
from .withdrawal_strategies import BaseWithdrawalStrategy


def _run_single_simulation(
    run_id: int,
    market_data: pd.DataFrame,
    simulator_class: Type[RetirementSimulator],
    withdrawal_strategy: BaseWithdrawalStrategy,
    start_balance: float,
    simulation_years: int,
    portfolio_weights: dict,
) -> pd.DataFrame:
    """
    A top-level function to run a single simulation instance.
    This is required for multiprocessing to be able to pickle the function.
    """
    try:
        # Create a new returns series for each simulation run by sampling from the market data
        # This simulates the randomness of starting retirement in different years
        start_day = (len(market_data) - simulation_years * 252)
        if start_day <= 0:
            raise ValueError("Not enough market data for the simulation years")

        start_index = pd.Series(range(start_day)).sample(1).iloc[0]
        end_index = start_index + (simulation_years * 252)
        simulation_returns = market_data.iloc[start_index:end_index].pct_change().dropna()

        sim = simulator_class(
            returns=simulation_returns,
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
        market_data: pd.DataFrame,
        withdrawal_strategy: BaseWithdrawalStrategy,
        start_balance: float,
        simulation_years: int,
        portfolio_weights: dict,
        num_simulations: int = 1000,
        simulator_class=RetirementSimulator,
        parallel: bool = True,
    ):
        self.market_data = market_data
        self.withdrawal_strategy = withdrawal_strategy
        self.start_balance = start_balance
        self.simulation_years = simulation_years
        self.portfolio_weights = portfolio_weights
        self.num_simulations = num_simulations
        self.simulator_class = simulator_class
        self.parallel = parallel

    def run_simulations(self) -> MonteCarloResults:
        logging.info(f"Starting Monte Carlo simulation with {self.num_simulations} runs.")
        worker_func = partial(
            _run_single_simulation,
            market_data=self.market_data,
            simulator_class=self.simulator_class,
            withdrawal_strategy=self.withdrawal_strategy,
            start_balance=self.start_balance,
            simulation_years=self.simulation_years,
            portfolio_weights=self.portfolio_weights,
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
