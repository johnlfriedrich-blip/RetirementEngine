import matplotlib
import matplotlib.pyplot as plt
import logging

matplotlib.use("Agg")  # Use non-GUI backend for headless environments


def plot_regimes(df, regimes, confidence, output_path):
    try:
        logging.info(f"Plotting regimes to {output_path}")

        fig, ax1 = plt.subplots(figsize=(12, 6))

        ax1.plot(df.index, regimes, label="Regime", color="tab:blue", linewidth=1.5)
        ax1.set_ylabel("Regime State")
        ax1.set_xlabel("Time")
        ax1.grid(True)

        ax2 = ax1.twinx()
        ax2.plot(
            df.index, confidence, label="Confidence", color="tab:orange", alpha=0.6
        )
        ax2.set_ylabel("Confidence Score")

        fig.suptitle("Regime Transitions with Confidence Overlay", fontsize=14)
        fig.legend(loc="upper right")

        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()

        logging.info("Plot saved successfully.")

    except Exception as e:
        logging.error(f"Failed to plot regimes: {e}")
        raise
