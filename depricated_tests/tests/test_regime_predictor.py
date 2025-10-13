from src.ai.regime_predictor import predict_regimes
import pandas as pd
import numpy as np
from sklearn.dummy import DummyClassifier


def test_predict_regimes_with_dummy_model():
    df = pd.read_csv("data/macro.csv", parse_dates=["date"]).set_index("date")
    dummy = DummyClassifier(strategy="uniform")
    dummy.fit([[0]] * len(df), [0] * len(df))  # fake fit

    regimes = predict_regimes(df, dummy)

    # Patch: convert to DataFrame if needed
    if isinstance(regimes, pd.DataFrame):
        assert "Regime" in regimes.columns
        assert len(regimes) == len(df)
    elif isinstance(regimes, (list, tuple, np.ndarray)):
        assert len(regimes) == len(df)
    else:
        raise TypeError(f"Unexpected output type: {type(regimes)}")
