import pandas as pd
from hmmlearn.hmm import GaussianHMM


def fit_hmm(df, n_states=3):
    model = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=1000)
    X = df.values  # assumes df is numeric and clean
    model.fit(X)
    return model


def predict_regimes(df, model):
    X = df.values
    hidden_states = model.predict(X)
    return hidden_states


def score_confidence(X, model):
    _, posteriors = model.score_samples(X)
    return posteriors.max(axis=1)  # 1D array of max confidence per row


def score_posteriors(X, model):
    _, posteriors = model.score_samples(X)
    return pd.DataFrame(
        posteriors, index=X.index, columns=["Regime_0", "Regime_1", "Regime_2"]
    )
