from src.simulation.monte_carlo_retirement import survival_rate


def test_survival_rate_detects_depletion():
    # Simulated paths: one survives, one depletes early
    paths = [
        [1_000_000] * 30,  # survived all years
        [1_000_000, 500_000, 0.0] + [0.0] * 27,  # depleted in year 3
    ]

    rate = survival_rate(paths, years=30)
    assert rate == 0.5, f"Expected 50% survival, got {rate:.2%}"
