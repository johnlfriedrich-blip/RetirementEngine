from src.simulation.run_retirement_simulation import run_simulation


def test_simulation_runs():
    result = run_simulation(n_days=12, withdrawal_rate=0)
    assert "ending_balance" in result
    assert result["ending_balance"] > 0


def test_simulation_snapshot():
    result = run_simulation(n_days=12, withdrawal_rate=0.0, use_regimes=False)
    assert isinstance(result["ending_balance"], float)
    assert 800_000 < result["ending_balance"] < 1_200_000  # sanity bounds
    assert len(result["history"]) == 12
