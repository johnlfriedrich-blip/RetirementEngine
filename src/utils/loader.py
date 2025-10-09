import pandas as pd
import logging


def load_macro_data(path):
    try:
        logging.info(f"Loading macro data from {path}")
        df = pd.read_csv(path, encoding="utf-8")

        # Validate expected columns
        expected_cols = ["GDP", "Inflation", "Unemployment"]
        missing = [col for col in expected_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        # Drop NaNs and reset index
        df = df.dropna().reset_index(drop=True)

        logging.info(f"Loaded {len(df)} rows with columns: {df.columns.tolist()}")
        return df

    except UnicodeDecodeError:
        logging.error("Encoding error: try UTF-16 or ISO-8859-1")
        raise

    except Exception as e:
        logging.error(f"Failed to load macro data: {e}")
        raise
