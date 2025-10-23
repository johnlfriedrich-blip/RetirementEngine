from fastapi import FastAPI
from backend.api import backtest

app = FastAPI(title="RetirementEngine API")

app.include_router(backtest.router, prefix="/backtest")
