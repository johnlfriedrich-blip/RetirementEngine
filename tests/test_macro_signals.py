import pandas as pd
import pytest
from src.features.macro_signals import extract_macro_signals
from src.features.regime_classifier import (
    apply_regime_classification,
    add_regime_transitions,
    add_regime_duration,
    add_anomaly_flags,
)
from src.simulation.run_retirement_simulation import run_simulation


@pytest.fixture
def macro_df():
    df = pd.read_csv("data/macro.csv", parse_dates=["date"]).set_index("date")
    return df


def test_monte_carlo_mode():
    result = run_simulation(n_days=12, use_regimes=False)
    assert result["ending_balance"] > 0


def test_macro_signal_pipeline(macro_df):
    signals = extract_macro_signals(macro_df)
    assert not signals.empty
    assert "GDP_z" in signals.columns

    classified = apply_regime_classification(signals)
    assert "Regime" in classified.columns
    assert classified["Regime"].nunique() >= 2

    classified = add_regime_transitions(classified)
    assert "Regime_Change" in classified.columns
    assert classified["Regime_Change"].dtype == bool

    classified = add_regime_duration(classified)
    assert "Regime_Duration" in classified.columns
    assert classified["Regime_Duration"].min() >= 1

    classified = add_anomaly_flags(classified)
    assert "GDP_z_Anomaly" in classified.columns
    assert classified["GDP_z_Anomaly"].dtype == bool
