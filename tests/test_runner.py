import pandas as pd
from src.runner import _run_and_print_simulation


class DummySimulator:
    def __init__(self, *args, **kwargs):
        pass

    def run(self):
        df = pd.DataFrame({"Balance": [100000, 105000, 110000]})
        withdrawals = {"Withdrawal": [4000, 4100, 4200]}
        return df, withdrawals


def test_run_and_print_simulation(monkeypatch, capsys):
    monkeypatch.setattr(
        "src.runner.strategy_factory", lambda name, **kwargs: "dummy_strategy"
    )
    monkeypatch.setattr(
        "src.synthetic_data.from_synthetic_data",
        lambda **kwargs: [(0.01, 0.005, 0.002)] * 10,
    )
    monkeypatch.setattr("src.runner.RetirementSimulator", DummySimulator)

    _run_and_print_simulation(
        strategy_name="fixed",
        strategy_args={
            "initial_balance": 100000,
            "portfolio_weights": {"us_equities": 0.6, "bonds": 0.4},
        },
        data_source="synthetic",
        data_args={"portfolio_asset_params": {}},
    )
    out, _ = capsys.readouterr()
    assert "SIMULATION RESULTS" in out
    assert "Final Portfolio Balance" in out
