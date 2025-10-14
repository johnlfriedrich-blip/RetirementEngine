# tests/test_cli.py
import pytest
from typer.testing import CliRunner
from retirement_engine.cli import app

# Create a runner instance that can invoke the CLI commands
runner = CliRunner()


def test_run_command_success():
    """Tests a successful run of the 'run' command with the fixed strategy."""
    # This test requires a valid 'data/market.csv' file to exist.
    # For more robust tests, you could mock the file system or data loader.
    result = runner.invoke(
        app,
        [
            "run",
            "--strategy=fixed",
            "--initial-balance=500000",
            "--stock-allocation=0.5",
            "--rate=0.05",
        ],
    )
    assert result.exit_code == 0
    assert "Running simulation with 'fixed' strategy..." in result.stdout
    # The outcome can vary based on market data, so we check for either result
    assert (
        "Portfolio Survived!" in result.stdout or "Portfolio Depleted" in result.stdout
    )
    assert "[SUMMARY] Total Withdrawn" in result.stdout


def test_run_command_unknown_strategy():
    """Tests that the CLI exits gracefully with an unknown strategy."""
    result = runner.invoke(
        app,
        [
            "run",
            "--strategy=nonexistent_strategy",
            "--initial-balance=100000",
        ],
    )
    assert result.exit_code == 1
    assert "Error: Unknown strategy: 'nonexistent_strategy'" in result.stderr


def test_run_command_missing_data_file():
    """Tests that the CLI exits gracefully if the data source is not found."""
    result = runner.invoke(
        app,
        [
            "run",
            "--strategy=fixed",
            "--source=path/to/nonexistent/file.csv",
        ],
    )
    assert result.exit_code == 1
    assert "Error: Data source not found" in result.stderr


def test_run_synthetic_command_success():
    """Tests a successful run of the 'run-synthetic' command."""
    result = runner.invoke(
        app,
        [
            "run-synthetic",
            "--strategy=dynamic",
            "--num-years=5",
            "--initial-balance=10000",
        ],
    )
    assert result.exit_code == 0
    assert "Running synthetic simulation with 'dynamic' strategy..." in result.stdout
    assert "YEARLY RESULTS" in result.stdout
