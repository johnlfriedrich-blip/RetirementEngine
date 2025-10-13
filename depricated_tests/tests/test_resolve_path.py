from retirement_engine.resolve_path import resolve_path
import os
import pytest


def test_resolve_path_returns_absolute_path():
    path = resolve_path("data/market.csv")
    assert os.path.isabs(path)
    assert os.path.exists(path)
    assert os.path.isfile(path)
    assert os.path.basename(path) == "market.csv"

    expected_dir = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "..", "data")
    )
    actual_dir = os.path.dirname(os.path.realpath(path))
    assert actual_dir == expected_dir


def test_missing_file_raises_error():
    path = resolve_path("data/does_not_exist.csv")
    print(path)
    assert os.path.isabs(path)
    assert path.endswith("data/does_not_exist.csv")
    assert not os.path.exists(path)
    assert not os.path.isfile(path)
