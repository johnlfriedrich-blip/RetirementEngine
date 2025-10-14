# tests/test_new_features.py
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from retirement_engine.cli import app
from retirement_engine.data_loader import from_av, from_yf
import pandas as pd


runner = CliRunner()


def test_cli_run_av_source():
    """
    Tests that the `run` command correctly calls the `from_av` data loader.
    """
    with patch('retirement_engine.data_loader.from_av') as mock_from_av:
        mock_from_av.return_value = [(0.1, 0.05, 0.03)] * 252 * 2
        result = runner.invoke(
            app,
            [
                "run",
                "--strategy",
                "fixed",
                "--data-source",
                "av",
            ],
        )
        assert result.exit_code == 0
        mock_from_av.assert_called_once()

def test_cli_run_yf_source():
    """
    Tests that the `run` command correctly calls the `from_yf` data loader.
    """
    with patch('retirement_engine.data_loader.from_yf') as mock_from_yf:
        mock_from_yf.return_value = [(0.1, 0.05, 0.03)] * 252 * 2
        result = runner.invoke(
            app,
            [
                "run",
                "--strategy",
                "fixed",
                "--data-source",
                "yf",
            ],
        )
        assert result.exit_code == 0
        mock_from_yf.assert_called_once()


def test_cli_run_mc_compare_all_flag():
    """
    Tests that the `run-mc` command correctly runs a comparison when the
    --compare-all flag is used.
    """
    with patch('retirement_engine.cli.MonteCarloSimulator') as mock_mc_simulator:
        # To prevent the simulation from actually running, we can mock the `run` method
        mock_instance = mock_mc_simulator.return_value
        mock_instance.run.return_value = None
        mock_instance.results = pd.DataFrame({
            'Run': [0, 1], 'Year': [30, 30], 'End Balance': [1000, 0]
        })
        mock_instance.success_rate.return_value = 0.5

        result = runner.invoke(
            app,
            [
                "run-mc",
                "--compare-all",
                "--num-simulations",
                "10", # Use a small number for testing
            ],
        )
        assert result.exit_code == 0

        # Assert that MonteCarloSimulator was instantiated for each strategy
        from retirement_engine.cli import Strategy
        assert mock_mc_simulator.call_count == len(list(Strategy))


@patch('alpha_vantage.timeseries.TimeSeries.get_daily')
def test_from_av_data_loader(mock_get_daily, monkeypatch):
    """
    Tests the `from_av` data loader function to ensure it processes data correctly.
    """
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "DUMMY_KEY")
    # Create mock pandas DataFrames to be returned by the mocked fetch function
    mock_stock_data = pd.DataFrame({
        '4. close': [100.0, 101.0, 102.0]
    }, index=pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']))

    mock_bond_data = pd.DataFrame({
        '4. close': [50.0, 50.1, 50.2]
    }, index=pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']))

    # Configure the mock to return different values based on the ticker
    def get_daily_side_effect(symbol, **kwargs):
        if symbol == 'VTI':
            return mock_stock_data, {}
        if symbol == 'BND':
            return mock_bond_data, {}
        return pd.DataFrame(), {}

    mock_get_daily.side_effect = get_daily_side_effect

    # Call the function
    returns = from_av(stock_ticker='VTI', bond_ticker='BND')

    # Assertions
    # We expect n-1 returns from n prices
    assert len(returns) == 2

    # Check the first return calculation
    # Stock: (101/100) - 1 = 0.01
    # Bond: (50.1/50) - 1 = 0.002
    assert pytest.approx(returns[0][0]) == 0.01
    assert pytest.approx(returns[0][1]) == 0.002
    assert -0.1 < returns[0][2] < 0.1 # Inflation should be a small random number


@patch('yfinance.download')
def test_from_yf_data_loader(mock_yf_download):
    """
    Tests the `from_yf` data loader function to ensure it processes data correctly.
    """
    # Create a mock pandas DataFrame to be returned by the mocked fetch function
    mock_data = pd.DataFrame({
        ('Adj Close', 'VTI'): [100.0, 101.0, 102.0],
        ('Adj Close', 'BND'): [50.0, 50.1, 50.2]
    }, index=pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']))
    mock_yf_download.return_value = mock_data

    # Call the function
    returns = from_yf(stock_ticker='VTI', bond_ticker='BND')

    # Assertions
    # We expect n-1 returns from n prices
    assert len(returns) == 2

    # Check the first return calculation
    # Stock: (101/100) - 1 = 0.01
    # Bond: (50.1/50) - 1 = 0.002
    assert pytest.approx(returns[0][0]) == 0.01
    assert pytest.approx(returns[0][1]) == 0.002
    assert -0.1 < returns[0][2] < 0.1 # Inflation should be a small random number
