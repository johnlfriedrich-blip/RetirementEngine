import os
import pytest
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()


def test_run_command_fixed():
    result = runner.invoke(
        app, ["run", "--strategy", "fixed", "--source", "src/data/market.csv"]
    )
    assert result.exit_code == 0
    assert "Running simulation with 'fixed' strategy..." in result.stdout


def test_run_command_dynamic():
    result = runner.invoke(
        app, ["run", "--strategy", "dynamic", "--source", "src/data/market.csv"]
    )
    assert result.exit_code == 0
    assert "Running simulation with 'dynamic' strategy..." in result.stdout


def test_run_mc_command_synthetic_normal():
    result = runner.invoke(
        app,
        [
            "run-mc",
            "--strategy",
            "fixed",
            "--data-source",
            "synthetic",
            "--distribution",
            "normal",
            "--num-simulations",
            "50",
        ],
    )
    assert result.exit_code == 0
    assert "Running Monte Carlo simulation with 'fixed' strategy..." in result.stdout
    assert "Strategy Success Rate:" in result.stdout


def test_run_mc_command_synthetic_student_t():
    result = runner.invoke(
        app,
        [
            "run-mc",
            "--strategy",
            "fixed",
            "--data-source",
            "synthetic",
            "--distribution",
            "student-t",
            "--df",
            "5",
            "--num-simulations",
            "50",
        ],
    )
    assert result.exit_code == 0
    assert "Running Monte Carlo simulation with 'fixed' strategy..." in result.stdout
    assert "Strategy Success Rate:" in result.stdout


@pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Historical data loading is problematic in CI.",
)
def test_run_mc_command_historical():
    result = runner.invoke(
        app,
        [
            "run-mc",
            "--strategy",
            "fixed",
            "--data-source",
            "historical",
            "--num-simulations",
            "50",
        ],
    )
    assert result.exit_code == 0
    assert "Running Monte Carlo simulation with 'fixed' strategy..." in result.stdout
    assert "Strategy Success Rate:" in result.stdout


def test_compare_strategies_command_synthetic_normal():
    result = runner.invoke(
        app,
        [
            "compare-strategies",
            "--data-source",
            "synthetic",
            "--distribution",
            "normal",
            "--num-simulations",
            "50",
        ],
    )
    assert result.exit_code == 0
    assert "Comparing all withdrawal strategies..." in result.stdout
    assert "Strategy Success Rate" in result.stdout


def test_compare_strategies_command_synthetic_student_t():
    result = runner.invoke(
        app,
        [
            "compare-strategies",
            "--data-source",
            "synthetic",
            "--distribution",
            "student-t",
            "--df",
            "5",
            "--num-simulations",
            "50",
        ],
    )
    assert result.exit_code == 0
    assert "Comparing all withdrawal strategies..." in result.stdout
    assert "Strategy Success Rate" in result.stdout


@pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Historical data loading is problematic in CI.",
)
def test_compare_strategies_command_historical():
    result = runner.invoke(
        app,
        [
            "compare-strategies",
            "--data-source",
            "historical",
            "--num-simulations",
            "50",
        ],
    )
    assert result.exit_code == 0
    assert "Comparing all withdrawal strategies..." in result.stdout
    assert "Strategy Success Rate" in result.stdout
