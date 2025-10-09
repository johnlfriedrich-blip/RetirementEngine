import os
from src.utils.loader import load_macro_data
from src.ai.regime_predictor import fit_hmm, predict_regimes, score_confidence
from src.regimes.confidence_plot import plot_regimes


def main():
    # Paths
    data_path = "data/macro.csv"
    output_path = "outputs/regime_plot.png"

    # Load and validate data
    df = load_macro_data(data_path)

    # Fit HMM and predict regimes
    model = fit_hmm(df, n_states=3)
    regimes = predict_regimes(df, model)
    confidence = score_confidence(df, model)

    # Visualize regimes and confidence
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plot_regimes(df, regimes, confidence, output_path)

    print(f"Regime plot saved to {output_path}")


if __name__ == "__main__":
    main()
