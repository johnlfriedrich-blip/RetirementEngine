# retirement_engine/config.py
import yaml
from pathlib import Path

# Build the path to the config file relative to this file's location
config_path = Path(__file__).parent / "config.yaml"

with open(config_path, "r") as f:
    config = yaml.safe_load(f)

DEFAULT_ETF = config["default_etf"]
TAX_RATE = config["tax_rate"]
START_BALANCE = config["start_balance"]
