# retirement_engine/config.py
import yaml
from pathlib import Path

# Build the path to the config file relative to this file's location
config_path = Path(__file__).parent / "config.yaml"

with open(config_path, "r") as f:
    _config = yaml.safe_load(f)

# General Simulation Settings
DEFAULT_ETF = _config["default_etf"]
TAX_RATE = _config["tax_rate"]
START_BALANCE = _config["start_balance"]
TRADINGDAYS = _config["trading_days"]
STOCK_ALLOCATION = _config["stock_allocation"]
START_AGE = _config["start_age"]

# Withdrawal Strategy Defaults
WITHDRAWAL_RATE = _config["withdrawal_rate"]
GUARDRAILS_MIN_PCT = _config["guardrails_min_pct"]
GUARDRAILS_MAX_PCT = _config["guardrails_max_pct"]

# Market Data & Inflation Defaults
INFLATION_MEAN = _config["inflation_mean"]
INFLATION_STD_DEV = _config["inflation_std_dev"]
STOCK_MEAN_RETURN = _config["stock_mean_return"]
STOCK_STD_DEV = _config["stock_std_dev"]
BOND_MEAN_RETURN = _config["bond_mean_return"]
BOND_STD_DEV = _config["bond_std_dev"]

# Monte Carlo Simulation Defaults
NUM_SIMULATIONS = _config["num_simulations"]
DURATION_YEARS = _config["duration_years"]
PARALLEL_PROCESSING = _config["parallel_processing"]
