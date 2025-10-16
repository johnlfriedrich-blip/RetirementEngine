from typing import Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.data.data_access import ASSET_CLASSES, get_asset_data
from backend.retirement_engine.monte_carlo import MonteCarloSimulator
from backend.retirement_engine.withdrawal_strategies import FixedWithdrawal
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:80", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Portfolio(BaseModel):
    """Represents a user-defined portfolio with asset allocations."""

    assets: Dict[str, float]


@app.get("/assets", response_model=List[str])
def list_assets():
    """Returns a list of available asset classes."""
    return list(ASSET_CLASSES.keys())


@app.post("/simulate")
def run_simulation(portfolio: Portfolio):
    """
    Runs a retirement simulation based on the provided portfolio.
    """
    if not portfolio.assets:
        return {"error": "Portfolio must not be empty."}

    if not abs(sum(portfolio.assets.values()) - 1.0) < 1e-9:
        return {"error": "Portfolio weights must sum to 1.0."}

    # Fetch data for all assets in the portfolio
    asset_data = {}
    for asset_class in portfolio.assets:
        try:
            # Generate 100 years of data to ensure enough for sampling
            asset_data[asset_class] = get_asset_data(asset_class, years=100)
        except ValueError as e:
            return {"error": str(e)}

    # Combine asset data into a single DataFrame
    market_data = pd.concat(
        [df.rename(columns={"price": asset}) for asset, df in asset_data.items()],
        axis=1,
    )

    # Configure and run the Monte Carlo simulation
    start_balance = 1000000
    simulator = MonteCarloSimulator(
        market_data=market_data,
        withdrawal_strategy=FixedWithdrawal(
            initial_balance=start_balance, rate=0.04
        ),
        start_balance=start_balance,
        simulation_years=30,
        portfolio_weights=portfolio.assets,
        num_simulations=100,
        parallel=False,
    )
    results = simulator.run_simulations()

    return {
        "success_rate": results.success_rate(),
        "median_final_balance": results.median_final_balance(),
    }
