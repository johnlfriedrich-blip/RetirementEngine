from src.synthetic_data import from_synthetic_data
from src.data_loader import from_historical_data
from src.withdrawal_strategies import strategy_factory
from src.monte_carlo import MonteCarloSimulator


class SimulatorFactory:
    def __init__(
        self,
        strategy_name: str,
        strategy_args: dict,
        data_source: str,
        data_args: dict,
    ):
        self.strategy_name = strategy_name
        self.strategy_args = strategy_args
        self.data_source = data_source
        self.data_args = data_args

    def create_strategy(self):
        return strategy_factory(self.strategy_name, **self.strategy_args)

    def create_market_data(self, simulation_years: int):
        if self.data_source == "synthetic":
            self.data_args["num_years"] = simulation_years
            # print(f"[FACTORY] Generating synthetic data for {simulation_years} years")
            return from_synthetic_data(**self.data_args)
        else:
            self.data_args["num_years"] = simulation_years
            # print(f"[FACTORY] Loading historical data for {simulation_years} years")
            return from_historical_data(**self.data_args)

    def create_monte_carlo(
        self, simulation_years: int, num_simulations: int, parallel: bool
    ):
        strategy = self.create_strategy()
        market_data = self.create_market_data(simulation_years)
        weights = self.strategy_args["portfolio_weights"]

        # print(
        #     f"[FACTORY] Creating Monte Carlo simulator with strategy '{self.strategy_name}'"
        # )
        # print(f"[FACTORY] Portfolio weights: {weights}")
        # print(f"[FACTORY] Data source: {self.data_source}")
        # print(f"[FACTORY] Simulations: {num_simulations}, Years: {simulation_years}")

        return MonteCarloSimulator(
            market_data=market_data,
            withdrawal_strategy=strategy,
            start_balance=self.strategy_args["initial_balance"],
            simulation_years=simulation_years,
            portfolio_weights=weights,
            data_source=self.data_source,
            synthetic_params=self.data_args if self.data_source == "synthetic" else {},
            num_simulations=num_simulations,
            parallel=parallel,
        )
