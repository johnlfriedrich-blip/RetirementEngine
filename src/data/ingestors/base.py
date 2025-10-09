# src/data/ingestors/base.py

from abc import ABC, abstractmethod
import pandas as pd


class MarketIngestor(ABC):
    @abstractmethod
    def fetch(self, symbol: str, label: str) -> pd.DataFrame:
        """
        Fetch market data for a given symbol and return a DataFrame
        with a 'date' index and a single column named `label`.
        """
        pass
