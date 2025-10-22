from src.portfolio_builder import build_portfolio_from_cli
import pytest


def test_valid_portfolio():
    result = build_portfolio_from_cli("us_equities:0.6,bonds:0.4")
    assert result == {"us_equities": 0.6, "bonds": 0.4}


def test_whitespace_handling():
    result = build_portfolio_from_cli(" tech_etf : 0.5 , real_estate : 0.5 ")
    assert result == {"tech_etf": 0.5, "real_estate": 0.5}


def test_sum_not_one():
    with pytest.raises(ValueError, match="must sum to 1.0"):
        build_portfolio_from_cli("us_equities:0.7,bonds:0.4")


def test_missing_colon():
    with pytest.raises(ValueError, match="Missing ':'"):
        build_portfolio_from_cli("us_equities=0.6,bonds:0.4")


def test_duplicate_assets():
    with pytest.raises(ValueError, match="Duplicate asset"):
        build_portfolio_from_cli("us_equities:0.5,us_equities:0.5")


def test_non_numeric_weight():
    with pytest.raises(ValueError, match="could not convert string to float"):
        build_portfolio_from_cli("us_equities:abc,bonds:0.4")
