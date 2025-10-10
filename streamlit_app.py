import streamlit as st
from retirement_engine.simulator import run_simulation
from retirement_engine.plotting import plot_balance

st.title("Retirement Simulation")

withdrawal_rate = st.slider("Withdrawal Rate", 0.01, 0.10, 0.05, 0.005)
sp500_weight = st.slider("SP500 Weight", 0.0, 1.0, 0.6, 0.05)
etf_source = st.selectbox("ETF Source", ["market.csv", "etf_prices.csv"])


# Run simulation using CSV
history, withdrawals = run_simulation(withdrawal_rate, sp500_weight, etf_source)

st.write("Withdrawals sample:", withdrawals[:5])
st.write("Length of withdrawals:", len(withdrawals))

st.write("First 5 balances:", history[:5])
st.write("Total points:", len(history))
# Plot results
plot_balance(history)
