# retirement_engine/simulator.py
from retirement_engine.config import DEFAULT_ETF, TAX_RATE, START_BALANCE
import pandas as pd
import numpy as np


def run_simulation(withdrawal_rate, sp500_weight, etf_source="market.csv"):
    market = pd.read_csv(f"data/{etf_source}", parse_dates=["date"])
    market.set_index("date", inplace=True)
    market.sort_index(inplace=True)

    returns = market.pct_change().dropna()
    returns.rename(
        columns={"SP500": "SP500_return", "BONDS": "10Y_return"}, inplace=True
    )

    balance = 1_000_000
    tax_rate = 0.15
    withdrawals = []
    history = []

    for day_index, (date, row) in enumerate(returns.iterrows()):
        weights = {"SP500": sp500_weight, "10Y": 1 - sp500_weight}
        portfolio_return = (
            row["SP500_return"] * weights["SP500"] + row["10Y_return"] * weights["10Y"]
        )
        balance += balance * portfolio_return

        if day_index % 365 == 0:
            withdrawal = withdrawal_rate * balance
            tax = tax_rate * withdrawal
            balance -= withdrawal + tax
        else:
            withdrawal = 0

        withdrawals.append(withdrawal)
        history.append(balance)

        if balance <= 0:
            balance = 0
            break

    return history, withdrawals
