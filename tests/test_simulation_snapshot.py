from src.simulation.run_retirement_simulation import run_simulation


def test_simulation_snapshot_monte_carlo():
    result = run_simulation(n_days=360, withdrawal_rate=0.04, use_regimes=False)

    assert isinstance(result["ending_balance"], float)
    assert 100_000 < result["ending_balance"] < 2_000_000  # sanity bounds
    assert len(result["history"]) == 360
    assert all(isinstance(x, float) for x in result["history"])


def test_simulation_snapshot_regime_aware():
    result = run_simulation(n_days=360, withdrawal_rate=0.04, use_regimes=True)
    assert isinstance(result["ending_balance"], float)
    assert 100_000 < result["ending_balance"] < 2_000_000
    assert len(result["history"]) == 360
