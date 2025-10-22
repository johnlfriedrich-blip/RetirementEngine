def build_portfolio_from_cli(portfolio_str: str) -> dict:
    """
    Parses a CLI-style portfolio string into a validated asset-weight dictionary.

    Example input: "us_equities:0.6,bonds:0.4"
    Returns: {"us_equities": 0.6, "bonds": 0.4}
    """
    try:
        parts = [p.strip() for p in portfolio_str.split(",")]
        portfolio = {}
        for part in parts:
            if ":" not in part:
                raise ValueError(f"Missing ':' in '{part}'")
            asset, weight = part.split(":")
            asset = asset.strip()
            weight = float(weight.strip())
            if asset in portfolio:
                raise ValueError(f"Duplicate asset '{asset}'")
            portfolio[asset] = weight

        total = sum(portfolio.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Portfolio weights must sum to 1.0 (got {total:.4f})")

        return portfolio
    except Exception as e:
        raise ValueError(f"Invalid portfolio format: {e}")
