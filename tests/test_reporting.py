import pandas as pd
from src.reporting import (
    _print_mc_results,
    _print_comparison_results,
    _print_formatted_results,
)


class DummyResults:
    def __init__(self):
        self.results_df = pd.DataFrame({"End Balance": [100, 200, 300]})
        self.num_simulations = 3

    def success_rate(self):
        return 0.9


def test_print_mc_results(capsys):
    dummy = DummyResults()
    _print_mc_results(dummy, 30)
    out, _ = capsys.readouterr()
    assert "MONTE CARLO RESULTS" in out
    assert "Strategy Success Rate" in out


def test_print_comparison_results(capsys):
    results = [
        {
            "Strategy": "fixed",
            "Success Rate": 0.9,
            "Median Balance": 200,
            "10th Percentile": 100,
            "90th Percentile": 300,
        }
    ]
    _print_comparison_results(results)
    out, _ = capsys.readouterr()
    assert "STRATEGY COMPARISON RESULTS" in out
    assert "fixed" in out


def test_print_formatted_results(capsys):
    df = pd.DataFrame({"Balance": [100000, 105000, 110000]})
    withdrawals = {"Withdrawal": [4000, 4100, 4200]}
    _print_formatted_results(df, withdrawals)
    out, _ = capsys.readouterr()
    assert "SIMULATION RESULTS" in out
    assert "Final Portfolio Balance" in out
    assert "Year 1" in out
