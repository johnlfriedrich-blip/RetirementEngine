import reflex as rx
from frontend.state import BacktestState


def app():
    return rx.vstack(
        rx.heading("Retirement Backtest"),
        rx.input(
            value=BacktestState.initial_balance,
            on_change=BacktestState.set_initial_balance,
            placeholder="Initial Balance",
            type="number",
        ),
        rx.input(
            value=BacktestState.withdrawal,
            on_change=BacktestState.set_withdrawal,
            placeholder="Monthly Withdrawal",
            type="number",
        ),
        rx.button("Run Backtest", on_click=BacktestState.run_backtest),
        rx.text_area(value=BacktestState.result, width="100%", height="300px"),
    )


app = rx.App({app})
