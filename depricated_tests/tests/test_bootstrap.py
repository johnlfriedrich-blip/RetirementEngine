from src.utils.load_regime_returns import load_returns_by_regime
import random


def test_bootstrap_sampling():
    returns = load_returns_by_regime()
    for regime in ["Stable", "Overheating"]:
        sample = random.choice(returns[regime])
        assert len(sample) == 2  # SP500 and 10Y
        assert all(isinstance(x, float) for x in sample)
