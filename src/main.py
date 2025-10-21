import os
import pandas as pd
import math
from typing import Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .data.data_access import ASSET_CLASSES
from dotenv import load_dotenv
from .monte_carlo import MonteCarloSimulator
from .withdrawal_strategies import FixedWithdrawal

app = FastAPI()
load_dotenv()


def load_defaults():
    defaults = {
        "us_equities": float(os.getenv("US_EQUITIES_WEIGHT", 0.3333)),
        "intl_equities": float(os.getenv("INTL_EQUITIES_WEIGHT", 0.3333)),
        "fixed_income": float(os.getenv("FIXED_INCOME_WEIGHT", 0.3334)),
    }
    # normalize and round to 4 decimal places
    total = sum(defaults.values())
    defaults = {k: round(v / total, 4) for k, v in defaults.items()}
    return defaults


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


@app.get("/assets/defaults")
def get_defaults():
    return load_defaults()


class Portfolio(BaseModel):
    assets: Dict[str, float]


@app.post("/simulate")
def run_simulation(portfolio: Portfolio):
    # Validate portfolio is not empty
    if not portfolio.assets:
        raise HTTPException(status_code=400, detail="Portfolio must not be empty.")

    # Validate portfolio weights sum to 1.0
    total_weights = sum(portfolio.assets.values())
    if not math.isclose(total_weights, 1.0):
        raise HTTPException(
            status_code=400, detail="Portfolio weights must sum to 1.0."
        )

    # Validate asset classes
    for asset_name in portfolio.assets.keys():
        if asset_name not in ASSET_CLASSES:
            raise HTTPException(
                status_code=400, detail=f"Invalid asset class: {asset_name}"
            )

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
