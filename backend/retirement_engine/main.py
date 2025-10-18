from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
from retirement_engine.data.data_access import ASSET_CLASSES

# import os
# import pandas as pd

# Regime analysis imports
# from src.utils.loader import load_macro_data
# from src.ai.regime_predictor import fit_hmm, predict_regimes, score_confidence
# from src.regimes.confidence_plot import plot_regimes

# Simulation imports
# from src.data.data_access import ASSET_CLASSES, get_asset_data
# from src.retirement_engine.monte_carlo import MonteCarloSimulator
# from src.retirement_engine.withdrawal_strategies import FixedWithdrawal

# from retirement_engine.monte_carlo import MonteCarloSimulator
# from retirement_engine.withdrawal_strategies import FixedWithdrawal

app = FastAPI()


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
    # [simulation logic here]
    ...


@app.get("/regime")
def run_regime_analysis():
    # [regime logic here]
    ...
