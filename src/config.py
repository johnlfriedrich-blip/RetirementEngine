# retirement_engine/config.py
import yaml
from pathlib import Path

# Build the path to the config file relative to this file's location
# config_path = Path(__file__).resolve().parent / "config.yaml"
# with open(config_path, "r") as f:
#    config = yaml.safe_load(f)

# Resolve config.yaml relative to the original source tree
this_file = Path(__file__).resolve()

# If running from build/lib/src/config.py, walk up to find the real src/
while this_file.name != "src" and this_file != this_file.parent:
    this_file = this_file.parent

config_path = this_file / "config.yaml"

if not config_path.exists():
    raise FileNotFoundError(f"Missing config.yaml at {config_path}")

with open(config_path, "r") as f:
    config = yaml.safe_load(f)


DEFAULT_ETF = config["default_etf"]
TAX_RATE = config["tax_rate"]
START_BALANCE = config["start_balance"]
TRADING_DAYS = config["trading_days"]
NUM_SIMULATIONS = config["num_simulations"]
