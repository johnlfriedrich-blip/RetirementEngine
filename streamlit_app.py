import streamlit as st
import pandas as pd
from retirement_engine.simulator import run_simulation

STRATEGY_MAP = {
    "Fixed": "Fixed",
    "Guardrails": "Guardrails",
    "Pause After Loss": "Pause After Loss",
    "Dynamic Percent": "Dynamic",
}


def simulate_balances(withdrawal_rate, sp500_weight, etf_source):
    strategies = ["Fixed", "Guardrails", "Pause After Loss", "Dynamic Percent"]
    balances_by_strategy = {}

    for label, internal_name in STRATEGY_MAP.items():
        balances, _ = run_simulation(
            withdrawal_rate=withdrawal_rate,
            sp500_weight=sp500_weight,
            etf_source=etf_source,
            strategy=internal_name,
        )
        balances_by_strategy[label] = balances

    return balances_by_strategy


def simulate_withdrawals(withdrawal_rate, sp500_weight, etf_source):
    strategies = ["Fixed", "Guardrails", "Pause After Loss", "Dynamic Percent"]
    withdrawals_by_strategy = {}

    for label, internal_name in STRATEGY_MAP.items():
        _, withdrawals = run_simulation(
            withdrawal_rate=withdrawal_rate,
            sp500_weight=sp500_weight,
            etf_source=etf_source,
            strategy=internal_name,
        )
        withdrawals_by_strategy[label] = withdrawals

    return withdrawals_by_strategy


st.title("Retirement Simulation")

# Sidebar controls
withdrawal_rate = st.sidebar.slider(
    "Withdrawal Rate", min_value=0.01, max_value=0.10, value=0.05, step=0.01
)
sp500_weight = st.sidebar.slider(
    "SP500 Weight", min_value=0.0, max_value=1.0, value=0.6, step=0.05
)
etf_source = st.sidebar.selectbox("ETF Source", ["market.csv", "custom.csv"])
spending_strategy = st.sidebar.selectbox(
    "Spending Strategy",
    [
        "Fixed",
        "Guardrails",
        "Pause After Loss",
        "Inflation-Adjusted",
        "Dynamic Percent",
    ],
)

# Run simulation
if st.button("Run Simulation"):

    # Replace these with actual simulation calls
    portfolio_balances = simulate_balances(
        withdrawal_rate=withdrawal_rate,
        sp500_weight=sp500_weight,
        etf_source=etf_source,
    )

    withdrawals = simulate_withdrawals(
        withdrawal_rate=withdrawal_rate,
        sp500_weight=sp500_weight,
        etf_source=etf_source,
    )

    # Determine number of years
    first_strategy = next(iter(portfolio_balances))
    num_years = len(simulate_balances[first_strategy])
    years = list(range(1, len(next(iter(portfolio_balances.values()))) + 1))

    # 📈 Chart: Portfolio Balances
    st.subheader("Portfolio Balance Over Time")
    balance_df = pd.DataFrame(portfolio_balances, index=years)
    balance_df.index.name = "Year"
    st.line_chart(balance_df)

    # 📊 Table: Combined Balances + Withdrawals
    st.subheader("Yearly Portfolio Snapshot")
    combined_df = pd.DataFrame(index=years)
    for strategy in portfolio_balances:
        combined_df[f"{strategy} Balance"] = portfolio_balances[strategy]
        combined_df[f"{strategy} Withdrawal"] = withdrawals[strategy]
    combined_df.index.name = "Year"
    st.dataframe(combined_df.style.format("${:,.2f}"))

else:
    st.info("Adjust parameters and click 'Run Simulation' to view results.")
