# tests/test_cli.py

import os
import pytest
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()


# --- Shared dummy factory fixture ---
@pytest.fixture
def dummy_factory(monkeypatch):
    class DummyResults:
        def __init__(self):
            import pandas as pd

            self.results_df = pd.DataFrame({"End Balance": [100, 200, 300]})
            self.num_simulations = 3

        def success_rate(self):
            return 0.9

    class DummySim:
        def run_simulations(self):
            return DummyResults()

    class DummyFactory:
        def __init__(self, *args, **kwargs):
            pass

        def create_monte_carlo(self, *args, **kwargs):
            return DummySim()

    # Patch the symbol that cli.py imported
    monkeypatch.setattr("src.cli.SimulatorFactory", DummyFactory)
    return DummyFactory


# --- Basic run commands ---
def test_run_command_fixed():
    result = runner.invoke(
        app, ["run", "--strategy", "fixed", "--source", "src/data/market.csv"]
    )
    assert result.exit_code == 0
    assert "Running simulation with 'fixed' strategy" in result.stdout


def test_run_command_dynamic():
    result = runner.invoke(
        app, ["run", "--strategy", "dynamic", "--source", "src/data/market.csv"]
    )
    assert result.exit_code == 0
    assert "Running simulation with 'dynamic' strategy" in result.stdout


# --- Monte Carlo synthetic (box_muller) ---
def test_run_mc_command_synthetic_box_muller(dummy_factory):
    result = runner.invoke(
        app,
        [
            "run-mc",
            "--strategy",
            "fixed",
            "--data-source",
            "synthetic",
            "--distribution",
            "box_muller",
            "--num-simulations",
            "10",
        ],
    )
    assert result.exit_code == 0
    assert "MONTE CARLO RESULTS" in result.stdout
    assert "Strategy Success Rate" in result.stdout


# --- Monte Carlo synthetic (student_t) ---
def test_run_mc_command_synthetic_student_t(dummy_factory):
    result = runner.invoke(
        app,
        [
            "run-mc",
            "--strategy",
            "fixed",
            "--data-source",
            "synthetic",
            "--distribution",
            "student_t",
            "--df",
            "5",
            "--num-simulations",
            "10",
        ],
    )
    assert result.exit_code == 0
    assert "MONTE CARLO RESULTS" in result.stdout
    assert "Strategy Success Rate" in result.stdout


# --- Monte Carlo historical (skipped in CI) ---
@pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Historical data loading is problematic in CI.",
)
def test_run_mc_command_historical(dummy_factory):
    result = runner.invoke(
        app,
        [
            "run-mc",
            "--strategy",
            "fixed",
            "--data-source",
            "historical",
            "--num-simulations",
            "10",
        ],
    )
    assert result.exit_code == 0
    assert "MONTE CARLO RESULTS" in result.stdout


# --- Compare strategies synthetic ---
def test_compare_strategies_command_synthetic(dummy_factory):
    result = runner.invoke(
        app,
        [
            "compare-strategies",
            "--data-source",
            "synthetic",
            "--distribution",
            "box_muller",
            "--num-simulations",
            "10",
        ],
    )
    assert result.exit_code == 0
    assert "STRATEGY COMPARISON RESULTS" in result.stdout
    assert "Strategy Success Rate" in result.stdout
