# retirement_engine/plotting.py
import matplotlib.pyplot as plt


def plot_balance(history):
    plt.figure(figsize=(12, 6))
    plt.plot(history, label="Portfolio Balance")
    plt.title("Retirement Portfolio Over Time")
    plt.xlabel("Days")
    plt.ylabel("Balance ($)")
    plt.grid(True)
    plt.legend()
    plt.show()
