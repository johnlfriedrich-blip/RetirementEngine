from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import pandas as pd
from .data.data_access import ASSET_CLASSES

# import os
# import pandas as pd

# Regime analysis imports
# from src.utils.loader import load_macro_data
# from src.ai.regime_predictor import fit_hmm, predict_regimes, score_confidence
# from src.regimes.confidence_plot import plot_regimes

# Simulation imports
# from .data.data_access import ASSET_CLASSES
from .monte_carlo import MonteCarloSimulator
from .withdrawal_strategies import FixedWithdrawal

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",  # React development server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "Backend is live"}


@app.get("/assets", response_model=List[str])
def list_assets():
    return list(ASSET_CLASSES.keys())


class Portfolio(BaseModel):
    assets: Dict[str, float]


@app.post("/simulate")
def run_simulation(portfolio: Portfolio):
    # Actual simulation logic
    start_balance = 1_000_000  # Example starting balance
    withdrawal_rate = 0.04  # Example 4% withdrawal rate
    years = 30  # Example simulation years
    num_simulations = 1000  # Example number of simulations

    synthetic_params_dict = {
        "portfolio_asset_params": ASSET_CLASSES,
        "num_years": years,  # Pass num_years to synthetic data generation
    }

    simulator = MonteCarloSimulator(
        market_data=pd.DataFrame(),  # Placeholder for synthetic data
        start_balance=start_balance,
        portfolio_weights=portfolio.assets,
        withdrawal_strategy=FixedWithdrawal(
            initial_balance=start_balance, rate=withdrawal_rate
        ),
        simulation_years=years,
        num_simulations=num_simulations,
        data_source="synthetic",
        synthetic_params=synthetic_params_dict,
    )

    results = simulator.run_simulations()

    success_rate = results.success_rate()
    median_final_balance = results.median_final_balance()

    return {"success_rate": success_rate, "median_final_balance": median_final_balance}


@app.get("/regime")
def run_regime_analysis():
    # [regime logic here]
    ...
