# monte_carlo.py
import pandas as pd
import multiprocessing
from typing import Type
from functools import partial
import logging
from .simulator import RetirementSimulator
from .withdrawal_strategies import BaseWithdrawalStrategy
from .synthetic_data import from_synthetic_data
from .config import NUM_SIMULATIONS


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def _run_single_simulation(
    run_id: int,
    market_data: pd.DataFrame,
    simulator_class: Type[RetirementSimulator],
    withdrawal_strategy: BaseWithdrawalStrategy,
    start_balance: float,
    simulation_years: int,
    portfolio_weights: dict,
    data_source: str,
    synthetic_params: dict,
) -> pd.DataFrame:
    """
    Run a single simulation and return a one‑row DataFrame with Run and End Balance.
    """
    try:
        required_length = simulation_years * 252

        if data_source == "historical":
            if len(market_data) < required_length:
                raise ValueError(
                    "Not enough historical market data for the simulation years"
                )

            max_start_index = len(market_data) - required_length
            start_index = pd.Series(range(max_start_index + 1)).sample(1).iloc[0]

            simulation_segment = market_data.iloc[
                start_index : start_index + required_length
            ]

            simulation_returns_df = pd.DataFrame(
                {
                    "us_equities": simulation_segment["sp500"].pct_change(),
                    "bonds": simulation_segment["bonds"].pct_change(),
                    "inflation_returns": simulation_segment["cpi"].pct_change(),
                }
            ).dropna()

            if len(simulation_returns_df) < required_length - 1:
                raise ValueError("Not enough market data after calculating returns")
        else:
            simulation_returns_df = from_synthetic_data(**synthetic_params)

        sim = simulator_class(
            returns=simulation_returns_df,
            initial_balance=start_balance,
            portfolio_weights=portfolio_weights,
            strategy=withdrawal_strategy,
        )
        yearly_data_df, _ = sim.run()

        if yearly_data_df.empty or "End Balance" not in yearly_data_df.columns:
            return pd.DataFrame()

        final_balance = float(yearly_data_df.iloc[-1]["End Balance"])
        return pd.DataFrame({"Run": [run_id], "End Balance": [final_balance]})

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
        num_simulations: int = NUM_SIMULATIONS,
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
        if not successful_results:
            logging.warning("All simulations failed.")
            results_df = pd.DataFrame()
        else:
            results_df = pd.concat(successful_results, ignore_index=True)
            logging.info(f"Results DataFrame columns: {results_df.columns.tolist()}")
            logging.info(f"First few rows:\n{results_df.head()}")

        logging.info("Monte Carlo simulation complete.")
        return MonteCarloResults(results_df, self.num_simulations)
