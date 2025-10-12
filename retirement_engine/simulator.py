# simulator.py
import pandas as pd
import os
from retirement_engine.resolve_path import resolve_path


FALLBACK_DATA_DIR = os.environ.get(
    "RETIREMENT_ENGINE_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data")
)

from retirement_engine.withdrawal_strategies import (
    fixed_withdrawal,
    inflation_adjusted_withdrawal,
    dynamic_percent_withdrawal,
    guardrails_withdrawal,
    pause_after_loss_withdrawal,
)


def run_simulation(
    withdrawal_rate, etf_source, strategy, initial_balance=1_000_000, sp500_weight=0.6
):
    returns = load_market_data(etf_source, sp500_weight=sp500_weight)
    days_per_year = 252
    balance = initial_balance
    balances = []
    withdrawals = []

    for day in range(len(returns)):
        if day % days_per_year == 0:
            withdrawal = get_annual_withdrawal(
                strategy=strategy,
                balance=balance,
                withdrawals=withdrawals,
                past_returns=returns[max(0, day - days_per_year) : day],
                withdrawal_rate=withdrawal_rate,
                initial_balance=initial_balance,
                sp500_weight=sp500_weight,
                full_returns=returns,
                days_per_year=days_per_year,
            )

            # Defensive check
            if withdrawal is None or not isinstance(withdrawal, (int, float)):
                print(f"[ERROR] Invalid withdrawal at year {day // days_per_year}")
                withdrawal = 0.0

            print(
                f"Year {day // days_per_year}: Withdrawal = {withdrawal:.2f}, Balance = {balance:.2f}"
            )
            balance -= withdrawal
            withdrawals.append(withdrawal)

        # Apply daily return
        daily_return = returns[day]
        if isinstance(daily_return, list):
            daily_return = daily_return[0]

        # Guard against invalid return
        if (
            not isinstance(daily_return, (int, float))
            or daily_return == float("inf")
            or daily_return != daily_return
        ):
            print(f"[ERROR] Invalid daily return at day {day}: {daily_return}")
            daily_return = 0.0

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
    full_returns,
    days_per_year,
):

    if strategy == "Fixed":
        return initial_balance * withdrawal_rate

    elif strategy == "Dynamic":
        return balance * withdrawal_rate

    elif strategy == "Guardrails":
        pct_list = guardrails_withdrawal([balance], min_pct=0.03, max_pct=0.06)
        withdrawal = pct_list[0]
        if not isinstance(withdrawal, (int, float)) or not (0 <= withdrawal <= balance):
            print(f"[ERROR] Guardrails returned invalid withdrawal: {withdrawal}")
            withdrawal = 0.0
        return withdrawal

    elif strategy == "Pause After Loss":
        balance_series = []
        return_windows = []

        balance = initial_balance
        for day in range(len(full_returns)):
            sp500_r, bonds_r = full_returns[day]

            try:
                blended_r = sp500_weight * float(sp500_r) + (1 - sp500_weight) * float(
                    bonds_r
                )
            except Exception as e:
                print(
                    f"[ERROR] Failed to compute blended return at day {day}: {full_returns[day]} → {e}"
                )
                blended_r = 0.0

            if (
                not isinstance(blended_r, (int, float))
                or blended_r == float("inf")
                or blended_r != blended_r  # NaN check
            ):
                print(f"[ERROR] Invalid blended return at day {day}: {blended_r}")
                blended_r = 0.0

            balance *= 1 + blended_r

            withdrawals = pause_after_loss_withdrawal(
                balance_series, return_windows, withdrawal_rate, sp500_weight
            )

        # Reconstruct full balance timeline
        balances = []
        balance = initial_balance
        year_index = 0
        for day in range(len(full_returns)):
            if day % days_per_year == 0 and year_index < len(withdrawals):
                balance -= withdrawals[year_index]
                year_index += 1

            sp500_r, bonds_r = full_returns[day]
            blended_r = sp500_weight * sp500_r + (1 - sp500_weight) * bonds_r
            balance *= 1 + blended_r
            balances.append(balance)

        return balances, withdrawals


"""
def load_market_data(etf_source, sp500_weight=0.6):
    
    Loads daily return data from a CSV file and returns a flat list of floats.
    If both 'SP500' and 'BONDS' columns exist, computes a weighted average.
    
    # df = pd.read_csv(etf_source)

    from retirement_engine.resolve_path import resolve_path

    path = resolve_path(etf_source)
    print(path)
    df = pd.read_csv(path)

    if "SP500" in df.columns and "BONDS" in df.columns:
        returns = (
            df["SP500"].astype(float) * sp500_weight
            + df["BONDS"].astype(float) * (1 - sp500_weight)
        ).tolist()
    elif "SP500" in df.columns:
        returns = df["SP500"].astype(float).tolist()
    elif "BONDS" in df.columns:
        returns = df["BONDS"].astype(float).tolist()
    else:
        raise ValueError("CSV must contain 'SP500' and/or 'BONDS' columns.")

    return returns
"""
import pandas as pd


def load_market_data(path, sp500_weight=0.6):
    df = pd.read_csv(path)
    df["SP500_return"] = df["SP500"].pct_change()
    df["BONDS_return"] = df["BONDS"].pct_change()

    # Drop first row with NaN return
    df = df.dropna()

    # Blend returns
    blended = (
        sp500_weight * df["SP500_return"] + (1 - sp500_weight) * df["BONDS_return"]
    )
    return list(zip(df["SP500_return"], df["BONDS_return"]))
