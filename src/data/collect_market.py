# src/data/collect_market.py
import pandas as pd

from src.data.ingestors.alpha_vantage import AlphaVantageIngestor

# from src.data.ingestors.finnhub import FinnhubIngestor


def collect_market(ingestor):
    tickers = {"SP500": "SPY", "BONDS": "TLT"}

    dfs = []
    for label, symbol in tickers.items():
        df = ingestor.fetch(symbol, label)
        if df is not None:
            dfs.append(df)

    if not dfs:
        print("[ERROR] No market data collected.")
        return

    merged = pd.concat(dfs, axis=1).dropna()
    merged.to_csv("data/market.csv")
    print("Saved market data to data/market.csv")
    print(merged.tail())


if __name__ == "__main__":
    ingestor = AlphaVantageIngestor()
    # ingestor = FinnhubIngestor()
    collect_market(ingestor)
