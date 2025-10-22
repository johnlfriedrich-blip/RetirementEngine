from src.cli_helpers import build_strategy_args, build_data_args


def test_build_strategy_args_fixed():
    args = build_strategy_args("fixed", 100000, {"us_equities": 0.6}, rate=0.05)
    assert args["rate"] == 0.05
    assert "initial_balance" in args


def test_build_strategy_args_guardrails():
    args = build_strategy_args(
        "guardrails", 100000, {"bonds": 0.4}, min_pct=0.02, max_pct=0.07
    )
    assert args["min_pct"] == 0.02
    assert args["max_pct"] == 0.07


def test_build_strategy_args_vpw():
    args = build_strategy_args("vpw", 100000, {"us_equities": 0.6}, start_age=70)
    assert args["start_age"] == 70


def test_build_data_args_structure():
    portfolio = {"us_equities": 0.6, "bonds": 0.4}
    args = build_data_args(
        portfolio_dict=portfolio,
        sp500_mean=0.1,
        sp500_std_dev=0.18,
        bonds_mean=0.03,
        bonds_std_dev=0.06,
        inflation_mean=0.03,
        inflation_std_dev=0.015,
        distribution="box_muller",
        df=3,
        start_year=1980,
        bootstrap_block_size=50,
    )
    assert "portfolio_asset_params" in args
    assert "inflation_mean" in args
    assert args["start_year"] == 1980
    assert args["bootstrap_block_size"] == 50
