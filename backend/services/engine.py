from backend.services.historical import load_real_returns
import pandas as pd


def evaluate_strategy(
    returns: pd.DataFrame,
    initial_balance: float = 1_000_000,
    withdrawal: float = 40_000,
) -> dict:
    balance = initial_balance
    balances = []

    for _, row in returns.iterrows():
        # Apply returns
        balance *= 1 + row["real_sp500"]
        # Withdraw
        balance -= withdrawal
        balances.append(balance)

    success = bool(balance > 0)
    return {
        "final_balance": round(balance, 2),
        "success": success,
        "path": balances,
        "success_rate": 100.0 if success else 0.0,
    }


def run_backtest(
    initial_balance: float = 1_000_000, withdrawal: float = 40_000
) -> dict:
    returns = load_real_returns()
    return evaluate_strategy(returns, initial_balance, withdrawal)
