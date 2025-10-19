# monte_carlo.py
import pandas as pd
import multiprocessing
from typing import Type
from functools import partial
import logging
from .simulator import RetirementSimulator
from .withdrawal_strategies import BaseWithdrawalStrategy
from .synthetic_data import from_synthetic_data


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def _run_single_simulation(
    run_id: int,
    market_data: pd.DataFrame,  # This is now the full historical data
    simulator_class: Type[RetirementSimulator],
    withdrawal_strategy: BaseWithdrawalStrategy,
    start_balance: float,
    simulation_years: int,
    portfolio_weights: dict,
    data_source: str,
    synthetic_params: dict,
) -> pd.DataFrame:
    """
    A top-level function to run a single simulation instance.
    This is required for multiprocessing to be able to pickle the function.
    """
    try:
        # Calculate the required length for one simulation run
        required_length = simulation_years * 252

        if data_source == "historical":
            # Ensure there's enough historical data to sample from
            if len(market_data) < required_length:
                raise ValueError(
                    "Not enough historical market data for the simulation years"
                )

            # Randomly select a starting point for the simulation segment
            # The end index must not exceed the length of market_data
            max_start_index = len(market_data) - required_length
            start_index = (
                pd.Series(range(max_start_index + 1)).sample(1).iloc[0]
            )  # +1 because randint is exclusive of high

            # Extract the simulation segment
            simulation_segment = market_data.iloc[
                start_index : start_index + required_length
            ]

            # Calculate daily returns for the simulation segment
            # The original market_data already has 'sp500', 'bonds', 'cpi' columns
            # We need to calculate returns from these values
            simulation_returns_df = pd.DataFrame(
                {
                    "us_equities": simulation_segment["sp500"].pct_change(),
                    "bonds": simulation_segment["bonds"].pct_change(),
                    "inflation_returns": simulation_segment["cpi"].pct_change(),
                }
            ).dropna()  # Dropna to handle the first row after pct_change

            # Ensure the simulation_returns_df has enough data after pct_change and dropna
            if (
                len(simulation_returns_df) < required_length - 1
            ):  # -1 because pct_change reduces length by 1
                raise ValueError(
                    "Not enough market data after calculating returns for the simulation years"
                )
        else:  # Synthetic data
            simulation_returns_df = from_synthetic_data(**synthetic_params)

        sim = simulator_class(
            returns=simulation_returns_df,  # Pass the calculated returns DataFrame
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
        data_source: str,
        synthetic_params: dict = None,
        num_simulations: int = 1000,
        simulator_class=RetirementSimulator,
        parallel: bool = True,
    ):
        self.market_data = market_data
        self.withdrawal_strategy = withdrawal_strategy
        self.start_balance = start_balance
        self.simulation_years = simulation_years
        self.portfolio_weights = portfolio_weights
        self.data_source = data_source
        self.synthetic_params = synthetic_params
        self.num_simulations = num_simulations
        self.simulator_class = simulator_class
        self.parallel = parallel

    def run_simulations(self) -> MonteCarloResults:
        logging.info(
            f"Starting Monte Carlo simulation with {self.num_simulations} runs."
        )
        worker_func = partial(
            _run_single_simulation,
            market_data=self.market_data,
            simulator_class=self.simulator_class,
            withdrawal_strategy=self.withdrawal_strategy,
            start_balance=self.start_balance,
            simulation_years=self.simulation_years,
            portfolio_weights=self.portfolio_weights,
            data_source=self.data_source,
            synthetic_params=self.synthetic_params,
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
