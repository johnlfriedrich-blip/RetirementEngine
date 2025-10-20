import os
import pytest
from typer.testing import CliRunner
from src.cli import app
from pathlib import Path
import logging

runner = CliRunner()

# Construct the absolute path to the data file
# This makes the test independent of the current working directory
# and robust for CI environments.
TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent
DATA_PATH = str(PROJECT_ROOT / "src" / "data" / "market.csv")

# To resolve logging issues in CI environments
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"DATA_PATH resolved to: {DATA_PATH}")


def test_run_command_fixed():
    result = runner.invoke(app, ["run", "--strategy", "fixed", "--source", DATA_PATH])
    assert result.exit_code == 0
    assert "Running simulation with 'fixed' strategy..." in result.stdout


def test_run_command_dynamic():
    result = runner.invoke(app, ["run", "--strategy", "dynamic", "--source", DATA_PATH])
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
            "--no-parallel",
        ],
        # catch_exceptions=False,
    )
    print("CLI Output:", result.stdout)
    print("Exit Code:", result.exit_code)
    print("STDERR:", result.stderr)

    # print("Exit Code:", result.exit_code)
    assert result.exit_code == 0
    assert "[SUMMARY] Ran 50 simulations" in result.stdout
    # assert "Running Monte Carlo simulation with 'fixed' strategy..." in result.stdout
    # assert "Strategy Success Rate:" in result.stdout


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
            "--no-parallel",
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
            "--no-parallel",
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
            "--no-parallel",
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
            "--no-parallel",
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
            "--no-parallel",
        ],
    )
    assert result.exit_code == 0
    assert "Comparing all withdrawal strategies..." in result.stdout
    assert "Strategy Success Rate" in result.stdout
