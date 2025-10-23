import reflex as rx
import requests


class BacktestState(rx.State):
    initial_balance: int = 1_000_000
    withdrawal: int = 40_000
    result: str = ""

    def run_backtest(self):
        payload = {
            "initial_balance": self.initial_balance,
            "withdrawal": self.withdrawal,
        }
        try:
            res = requests.post("http://localhost:8000/backtest/", json=payload)
            self.result = res.text
        except Exception as e:
            self.result = f"Error: {str(e)}"
