from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.engine import run_backtest
from backend.utils.logger import get_logger

logger = get_logger()


router = APIRouter()


class BacktestRequest(BaseModel):
    initial_balance: float = 1_000_000
    withdrawal: float = 40_000


@router.post("/")
def backtest_endpoint(config: BacktestRequest):
    logger.info(f"Received backtest request: {config.model_dump()}")
    result = run_backtest(
        initial_balance=config.initial_balance, withdrawal=config.withdrawal
    )
    logger.info(f"Backtest result: {result}")
    return result
