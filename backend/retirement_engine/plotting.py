import matplotlib.pyplot as plt
import streamlit as st


def plot_balance(history, withdrawals=None):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(history, label="Portfolio Balance", color="blue")

    if withdrawals:
        ax.plot(withdrawals, label="Annual Withdrawals", color="red", linestyle="--")

    ax.set_title("Retirement Portfolio Over Time")
    ax.set_xlabel("Days")
    ax.set_ylabel("Amount ($)")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)
