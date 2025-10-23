import logging


def get_logger(name: str = "retirement_engine") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler("logs/backtest.log")
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
