import numpy as np
from . import config
from typing import Literal


class MarketDataGenerator:
    """
    Generates random market data for stocks and bonds based on a normal distribution.
    """

    def __init__(
        self,
        stock_mean_return: float = 0.09,
        stock_std_dev: float = 0.18,
        bond_mean_return: float = 0.04,
        bond_std_dev: float = 0.05,
        inflation_mean: float = 0.03,
        inflation_std_dev: float = 0.015,
        distribution_type: Literal["normal", "student-t"] = "normal",
        student_t_df: int = 6,
    ):
        # Convert annual stats to daily stats for simulation
        self.stock_daily_mean = stock_mean_return / config.TRADINGDAYS
        self.stock_daily_std = stock_std_dev / np.sqrt(config.TRADINGDAYS)
        self.bond_daily_mean = bond_mean_return / config.TRADINGDAYS
        self.bond_daily_std = bond_std_dev / np.sqrt(config.TRADINGDAYS)
        self.inflation_daily_mean = inflation_mean / config.TRADINGDAYS
        self.inflation_daily_std = inflation_std_dev / np.sqrt(config.TRADINGDAYS)

        self.distribution_type = distribution_type
        self.student_t_df = student_t_df

        if self.distribution_type == "student-t" and self.student_t_df <= 2:
            raise ValueError(
                "Degrees of freedom for Student's t-distribution must be > 2."
            )

    def generate_returns(self, duration_years: int) -> list[tuple[float, float, float]]:
        """
        Generates a list of daily returns for the entire simulation duration.

        Returns:
            A list of tuples, where each tuple is (stock_return, bond_return, inflation_rate)
            for a single trading day.
        """
        num_days = duration_years * config.TRADINGDAYS

        stock_returns = self._generate_random_variates(
            self.stock_daily_mean, self.stock_daily_std, num_days
        )
        bond_returns = self._generate_random_variates(
            self.bond_daily_mean, self.bond_daily_std, num_days
        )
        inflation_rates = self._generate_random_variates(
            self.inflation_daily_mean, self.inflation_daily_std, num_days
        )

        return list(zip(stock_returns, bond_returns, inflation_rates))

    def _generate_random_variates(
        self, mean: float, std_dev: float, num_samples: int
    ) -> np.ndarray:
        """Generates random numbers from the specified distribution."""
        if self.distribution_type == "normal":
            return np.random.normal(mean, std_dev, num_samples)

        if self.distribution_type == "student-t":
            # Generate standard t-distributed random numbers (mean=0)
            standard_t_variates = np.random.standard_t(self.student_t_df, num_samples)

            # The variance of a standard t-distribution is df / (df - 2)
            # We need to scale our variates to match the desired std_dev
            std_of_standard_t = np.sqrt(self.student_t_df / (self.student_t_df - 2))
            scaled_variates = standard_t_variates * (std_dev / std_of_standard_t)

            # Shift the variates to match the desired mean
            return mean + scaled_variates

        raise ValueError(f"Unknown distribution type: {self.distribution_type}")
