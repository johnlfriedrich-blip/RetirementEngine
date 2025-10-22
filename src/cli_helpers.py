def build_strategy_args(
    strategy_name: str,
    initial_balance: float,
    portfolio_dict: dict,
    rate: float = 0.04,
    min_pct: float = 0.03,
    max_pct: float = 0.06,
    start_age: int = 65,
) -> dict:
    """
    Build strategy_args conditionally based on the strategy type.
    """
    args = {
        "initial_balance": initial_balance,
        "portfolio_weights": portfolio_dict,
    }

    if strategy_name in ("fixed", "percent"):
        args["rate"] = rate
    if strategy_name == "guardrails":
        args["min_pct"] = min_pct
        args["max_pct"] = max_pct
    if strategy_name == "vpw":
        args["start_age"] = start_age

    return args


def build_data_args(
    portfolio_dict: dict,
    sp500_mean: float,
    sp500_std_dev: float,
    bonds_mean: float,
    bonds_std_dev: float,
    inflation_mean: float,
    inflation_std_dev: float,
    distribution,
    df: int,
    start_year: int | None = None,
    bootstrap_block_size: int | None = None,
) -> dict:
    """
    Build data_args for SimulatorFactory, covering both synthetic and historical cases.
    """
    args = {
        "portfolio_asset_params": {
            asset: {
                "cagr": sp500_mean if "equities" in asset else bonds_mean,
                "std_dev": sp500_std_dev if "equities" in asset else bonds_std_dev,
            }
            for asset in portfolio_dict.keys()
        },
        "inflation_mean": inflation_mean,
        "inflation_std_dev": inflation_std_dev,
        "distribution": distribution,
        "df": df,
    }

    if start_year is not None:
        args["start_year"] = start_year
    if bootstrap_block_size is not None:
        args["bootstrap_block_size"] = bootstrap_block_size

    return args
