# regime_predictor.py
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
import joblib

class RegimePredictor:
    def __init__(self, n_states=3):
        self.model = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=1000)
        self.state_map = {0: "Expansion", 1: "Contraction", 2: "Stagflation"}

    def fit(self, indicators_df):
        X = indicators_df.values
        self.model.fit(X)

    def predict(self, indicators_df):
        X = indicators_df.values
        hidden_states = self.model.predict(X)
        regimes = [self.state_map[state] for state in hidden_states]
        indicators_df["Regime"] = regimes
        return indicators_df

    def save_model(self, path="models/hmm_regime.pkl"):
        joblib.dump(self.model, path)

    def load_model(self, path="models/hmm_regime.pkl"):
        self.model = joblib.load(path)