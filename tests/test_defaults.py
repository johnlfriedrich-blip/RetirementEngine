# tests/test_defaults.py
from src.main import load_defaults
from src.data.data_access import ASSET_CLASSES


def test_defaults_cover_all_assets_and_sum_to_one():
    defaults = load_defaults()

    # 1. Every asset in ASSET_CLASSES must have a default
    assert set(defaults.keys()) == set(ASSET_CLASSES.keys())

    # 2. Weights must sum to 1.0 (within tolerance)
    total = sum(defaults.values())
    assert abs(total - 1.0) < 1e-6

    # 3. Each weight must be between 0 and 1
    for v in defaults.values():
        assert 0.0 <= v <= 1.0
