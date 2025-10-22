from src.factory import SimulatorFactory
from src.synthetic_data import Distribution


def test_factory_creates_strategy():
    strategy_args = {
        "initial_balance": 100000,
        "portfolio_weights": {"us_equities": 0.6, "bonds": 0.4},
        "rate": 0.04,
        "min_pct": 0.03,
        "max_pct": 0.06,
        "start_age": 65,
    }
    factory = SimulatorFactory(
        strategy_name="fixed",
        strategy_args=strategy_args,
        data_source="synthetic",
        data_args={
            "portfolio_asset_params": {
                "us_equities": {"cagr": 0.10, "std_dev": 0.18},
                "bonds": {"cagr": 0.03, "std_dev": 0.06},
            },
            "inflation_mean": 0.03,
            "inflation_std_dev": 0.015,
            "distribution": Distribution.BOX_MULLER,
            "df": 3,
        },
    )
    strategy = factory.create_strategy()
    assert strategy is not None


def test_factory_creates_market_data():
    factory = SimulatorFactory(
        strategy_name="fixed",
        strategy_args={
            "initial_balance": 100000,
            "portfolio_weights": {"us_equities": 0.6, "bonds": 0.4},
        },
        data_source="synthetic",
        data_args={
            "portfolio_asset_params": {
                "us_equities": {"cagr": 0.10, "std_dev": 0.18},
                "bonds": {"cagr": 0.03, "std_dev": 0.06},
            },
            "inflation_mean": 0.03,
            "inflation_std_dev": 0.015,
            "distribution": Distribution.BOX_MULLER,
            "df": 3,
        },
    )
    df = factory.create_market_data(simulation_years=30)
    assert df.shape[0] == 30 * 252
    assert "us_equities" in df.columns
    assert "bonds" in df.columns
    assert "inflation_returns" in df.columns


def test_factory_creates_monte_carlo():
    strategy_args = {
        "initial_balance": 100000,
        "portfolio_weights": {"us_equities": 0.6, "bonds": 0.4},
        "rate": 0.04,
        "min_pct": 0.03,
        "max_pct": 0.06,
        "start_age": 65,
    }
    factory = SimulatorFactory(
        strategy_name="fixed",
        strategy_args=strategy_args,
        data_source="synthetic",
        data_args={
            "portfolio_asset_params": {
                "us_equities": {"cagr": 0.10, "std_dev": 0.18},
                "bonds": {"cagr": 0.03, "std_dev": 0.06},
            },
            "inflation_mean": 0.03,
            "inflation_std_dev": 0.015,
            "distribution": Distribution.BOX_MULLER,
            "df": 3,
        },
    )
    mc_sim = factory.create_monte_carlo(
        simulation_years=30, num_simulations=10, parallel=False
    )
    assert mc_sim is not None
    assert mc_sim.num_simulations == 10
