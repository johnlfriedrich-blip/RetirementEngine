from src.simulation.run_retirement_simulation import run_simulation
import numpy as np


def test_monte_carlo_simulation_without_regimes():
    result = run_simulation(n_days=360, withdrawal_rate=0.04, use_regimes=False)

    # ✅ Structural checks
    assert isinstance(result, dict)
    assert "ending_balance" in result
    assert "history" in result

    # ✅ Behavioral checks
    assert isinstance(result["ending_balance"], float)
    assert len(result["history"]) == 360
    assert all(isinstance(x, float) for x in result["history"])

    # ✅ Sanity bounds (adjust as needed)
    assert 100_000 < result["ending_balance"] < 2_000_000


def test_monte_carlo_percentile_snapshot():
    balances = [
        run_simulation(n_days=360, withdrawal_rate=0.04, use_regimes=False)[
            "ending_balance"
        ]
        for _ in range(500)
    ]
    p10, p50, p90 = np.percentile(balances, [10, 50, 90])
    assert p10 > 100_000
    assert p90 < 2_000_000
