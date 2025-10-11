# simulator.py
import pandas as pd

FALLBACK_DATA_DIR = (
    "/mnt/c/Users/JohnFriedrich/OneDrive/Scripts/Python/RetirementEngine/data"
)

from retirement_engine.withdrawal_strategies import (
    fixed_withdrawal,
    inflation_adjusted_withdrawal,
    dynamic_percent_withdrawal,
    guardrails_withdrawal,
    pause_after_loss_withdrawal,
)


def run_simulation(
    withdrawal_rate, etf_source, strategy, initial_balance=1_000_000, sp500_weight=None
):
    returns = load_market_data(etf_source)  # flat list of daily returns
    days_per_year = 365
    balance = initial_balance
    balances = []
    withdrawals = []

    for day in range(len(returns)):
        # Trigger withdrawal once per year
        if day % days_per_year == 0:
            withdrawal = get_annual_withdrawal(
                strategy=strategy,
                balance=balance,
                withdrawals=withdrawals,
                past_returns=returns[:day],
                withdrawal_rate=withdrawal_rate,
                initial_balance=initial_balance,
                sp500_weight=sp500_weight,
            )
            balance -= withdrawal
            withdrawals.append(withdrawal)

        # Apply daily return
        daily_return = returns[day]
        if isinstance(daily_return, list):  # flatten if needed
            daily_return = daily_return[0]
        balance *= 1 + daily_return
        balances.append(balance)

    return balances, withdrawals


def get_annual_withdrawal(
    strategy,
    balance,
    withdrawals,
    past_returns,
    withdrawal_rate,
    initial_balance,
    sp500_weight,
):
    if strategy == "Fixed":
        return initial_balance * withdrawal_rate

    elif strategy == "Dynamic":
        return balance * withdrawal_rate

    elif strategy == "Guardrails":
        pct = guardrails_withdrawal(balance, withdrawals, min_pct=0.03, max_pct=0.06)
        return balance * pct

    elif strategy == "Pause After Loss":
        return pause_after_loss_withdrawal(
            balance, past_returns, withdrawal_rate, sp500_weight
        )

    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def load_market_data(etf_source):
    """
    Loads daily return data from a CSV file and returns a flat list of floats.
    Assumes the CSV has a 'daily_return' column with percentage or decimal returns.
    """
    df = pd.read_csv(etf_source)

    # Ensure 'daily_return' column exists
    if "daily_return" not in df.columns:
        raise ValueError("CSV must contain a 'daily_return' column.")

    # Convert to float if needed and return as flat list
    returns = df["daily_return"].astype(float).tolist()

    return returns
