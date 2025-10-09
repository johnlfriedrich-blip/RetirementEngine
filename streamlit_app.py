import streamlit as st
from retirement_engine.simulator import run_simulation
from retirement_engine.plotting import plot_balance  # if you’ve modularized plotting

st.title("Retirement Simulation")

withdrawal_rate = st.slider("Withdrawal Rate", 0.01, 0.10, 0.05, 0.005)
sp500_weight = st.slider("SP500 Weight", 0.0, 1.0, 0.6, 0.05)
etf_source = st.selectbox("ETF Source", ["market.csv", "etf_prices.csv"])

history, withdrawals = run_simulation(withdrawal_rate, sp500_weight, etf_source)
plot_balance(history)
