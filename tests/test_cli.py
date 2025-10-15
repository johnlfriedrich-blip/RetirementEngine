# tests/test_cli.py
import pytest
import pandas as pd
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from retirement_engine.cli import app

# Create a runner instance that can invoke the CLI commands
runner = CliRunner()


def test_main_no_command():
    """Tests that the main callback shows a message when no command is given."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "No command specified" in result.stdout


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
    assert result.exit_code == 2
    assert "Invalid value for '--strategy'" in result.stderr


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


@patch('retirement_engine.cli.data_loader')
def test_run_command_data_sources(mock_data_loader):
    """Tests the 'run' command with different data sources."""
    mock_data_loader.from_av.return_value = [(0.01, 0.005, 0.001)] * 2520
    mock_data_loader.from_yf.return_value = [(0.01, 0.005, 0.001)] * 2520

    # Test Alpha Vantage
    result_av = runner.invoke(app, ["run", "--strategy=fixed", "--data-source=av"])
    assert result_av.exit_code == 0
    mock_data_loader.from_av.assert_called_once()

    # Test Yahoo Finance
    result_yf = runner.invoke(app, ["run", "--strategy=fixed", "--data-source=yf"])
    assert result_yf.exit_code == 0
    mock_data_loader.from_yf.assert_called_once()


@patch('retirement_engine.cli.strategy_factory')
def test_run_command_strategy_error(mock_strategy_factory):
    """Tests that the CLI handles errors during strategy creation."""
    mock_strategy_factory.side_effect = ValueError("Invalid strategy params")
    result = runner.invoke(app, ["run", "--strategy=fixed", "--synthetic"])
    assert result.exit_code == 1
    assert "Error: Invalid strategy params" in result.stderr


def test_run_mc_command_success():
    """Tests a successful run of the 'run-mc' command with the fixed strategy."""
    result = runner.invoke(
        app,
        [
            "run-mc",
            "--strategy=fixed",
            "--initial-balance=500000",
            "--stock-allocation=0.5",
            "--rate=0.05",
            "--num-simulations=10",
            "--duration-years=5",
            "--no-parallel",
        ],
    )
    assert result.exit_code == 0
    assert "Running Monte Carlo simulation with 'fixed' strategy..." in result.stdout
    assert "[SUMMARY] Strategy Success Rate" in result.stdout


@patch('retirement_engine.cli.MonteCarloSimulator')
def test_run_mc_compare_all(MockMonteCarloSimulator):
    """Tests the 'run-mc --compare-all' command."""
    # Mock the MonteCarloSimulator to return some results
    mock_mc_instance = MockMonteCarloSimulator.return_value
    mock_mc_instance.success_rate.return_value = 0.95
    mock_mc_instance.results = pd.DataFrame({
        'Run': [0, 1],
        'Year': [30, 30],
        'End Balance': [100000, 200000]
    })

    result = runner.invoke(app, ["run-mc", "--compare-all", "--num-simulations=2", "--no-parallel"])

    assert result.exit_code == 0
    assert "Comparing all withdrawal strategies..." in result.stdout
    # Check that it ran for all strategies
    assert "Running simulation for 'fixed'..." in result.stdout
    assert "Running simulation for 'vpw'..." in result.stdout
    assert "STRATEGY COMPARISON RESULTS" in result.stdout


@patch('retirement_engine.cli.MonteCarloSimulator.run')
def test_run_mc_compare_all_strategy_error(mock_mc_run):
    """Tests that '--compare-all' handles an error in one of the strategies."""
    # Make the 'vpw' strategy raise an error
    def side_effect(strategy_name, **kwargs):
        if strategy_name == 'vpw':
            raise ValueError("VPW Age Error")
        return
    mock_mc_run.side_effect = side_effect

    result = runner.invoke(app, ["run-mc", "--compare-all", "--num-simulations=2", "--no-parallel"])
    assert result.exit_code == 0
    assert "Error running strategy vpw: VPW Age Error" in result.stderr
    assert "STRATEGY COMPARISON RESULTS" in result.stdout # Should still print results for others


def test_run_synthetic_command_success():
    """Tests a successful run of the 'run --synthetic' command."""
    result = runner.invoke(
        app,
        [
            "run",
            "--strategy=dynamic",
            "--num-years=5",
            "--initial-balance=10000",
            "--synthetic",
        ],
    )
    assert result.exit_code == 0
    assert "Running simulation with 'dynamic' strategy..." in result.stdout
    assert "YEARLY RESULTS" in result.stdout


@patch('retirement_engine.cli._print_formatted_results')
def test_run_command_empty_results(mock_print):
    """Tests that the CLI handles empty simulation results."""
    with patch('retirement_engine.cli.RetirementSimulator.run') as mock_sim_run:
        mock_sim_run.return_value = (pd.DataFrame(), [])
        runner.invoke(app, ["run", "--strategy=fixed", "--synthetic"])
        # Check that the print function was called with an empty DataFrame
        mock_print.assert_called_once()
        assert mock_print.call_args[0][0].empty


@patch('typer.echo')
def test_print_mc_results_all_fail(mock_echo):
    """Tests printing Monte Carlo results when all simulations fail."""
    from retirement_engine.cli import _print_mc_results
    mock_mc_sim = MagicMock()
    mock_mc_sim.success_rate.return_value = 0.0
    mock_mc_sim.results = None # No results df

    _print_mc_results(mock_mc_sim)
    # Check for the red-colored 0.0% success rate
    assert any("0.0%" in str(call_args) for call_args in mock_echo.call_args_list)
