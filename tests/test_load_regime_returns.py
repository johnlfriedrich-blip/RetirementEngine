from src.utils.load_regime_returns import load_returns_by_regime


def test_load_returns_by_regime_structure():
    regime_returns = load_returns_by_regime()

    assert isinstance(regime_returns, dict)
    assert len(regime_returns) >= 2  # at least 2 regimes

    for regime, returns in regime_returns.items():
        assert isinstance(returns, list)
        assert all(isinstance(pair, list) and len(pair) == 2 for pair in returns)
        assert all(isinstance(val, float) for pair in returns for val in pair)
