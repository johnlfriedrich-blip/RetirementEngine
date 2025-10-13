import csv
import math
import numpy as np
import pandas as pd
from .withdrawal_strategies import strategy_factory


class RetirementSimulator:
    def __init__(
        self,
        returns,
        initial_balance,
        stock_allocation,
        strategy,
        days_per_year=252,
    ):
        self.returns = returns
        self.initial_balance = initial_balance
        self.stock_allocation = stock_allocation
        self.strategy = strategy
        self.days_per_year = days_per_year

    @classmethod
    def from_csv(
        cls,
        etf_source,
        inflation_mean=0.03,
        inflation_std_dev=0.015,
        days_per_year=252,
        **kwargs,
    ):
        """Load market data from a CSV and initialize the simulator."""
        daily_inflation_mean = (1 + inflation_mean) ** (1 / days_per_year) - 1
        daily_inflation_std_dev = inflation_std_dev / math.sqrt(days_per_year)

        prev_sp500, prev_bonds = None, None
        returns = []
        with open(etf_source, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            # Normalize header names: lowercase and strip whitespace
            reader.fieldnames = [field.strip().lower() for field in reader.fieldnames]

            for row in reader:
                try:
                    current_sp500 = float(row["sp500"])
                    current_bonds = float(row["bonds"])

                    if prev_sp500 is not None:
                        sp500_r = (current_sp500 / prev_sp500) - 1
                        bonds_r = (current_bonds / prev_bonds) - 1

                        # Add a check for absurdly large returns (e.g., > 1000% daily)
                        if abs(sp500_r) > 10 or abs(bonds_r) > 10:
                            raise ValueError(
                                "Absurdly large daily return detected in market data"
                            )

                        # Add a check for finite numbers to prevent bad data
                        if not all(math.isfinite(r) for r in [sp500_r, bonds_r]):
                            raise ValueError(
                                "Non-finite number detected in market data"
                            )

                        inflation_r = np.random.normal(
                            daily_inflation_mean, daily_inflation_std_dev
                        )
                        returns.append((sp500_r, bonds_r, inflation_r))

                    prev_sp500, prev_bonds = current_sp500, current_bonds

                except (ValueError, KeyError) as e:
                    print(f"[WARN] Skipping invalid row in {etf_source}: {row} -> {e}")
        if not returns:
            raise ValueError(
                f"No valid data loaded from {etf_source}. The file may be empty or incorrectly formatted."
            )

        return cls(returns=returns, days_per_year=days_per_year, **kwargs)

    @staticmethod
    def _generate_normal_by_box_muller(mean, std_dev, num_samples):
        """
        Generate normally distributed random numbers using the Box-Muller transform.
        """
        # Ensure we generate pairs of numbers. If num_samples is odd, we'll generate one extra and discard it.
        num_pairs = math.ceil(num_samples / 2)

        # Generate uniform random numbers in (0, 1]
        u1 = np.random.uniform(low=np.finfo(float).eps, high=1.0, size=num_pairs)
        u2 = np.random.uniform(low=np.finfo(float).eps, high=1.0, size=num_pairs)

        # Apply the Box-Muller transform to get standard normal variables
        log_u1 = np.log(u1)
        z0 = np.sqrt(-2.0 * log_u1) * np.cos(2.0 * np.pi * u2)
        z1 = np.sqrt(-2.0 * log_u1) * np.sin(2.0 * np.pi * u2)

        # Combine the pairs and truncate to the desired number of samples
        standard_normal = np.stack((z0, z1), axis=-1).flatten()[:num_samples]

        # Scale by mean and standard deviation
        return mean + standard_normal * std_dev

    @classmethod
    def from_synthetic_data(
        cls,
        num_years=30,
        sp500_mean=0.10,
        sp500_std_dev=0.18,
        bonds_mean=0.03,
        bonds_std_dev=0.06,
        inflation_mean=0.03,
        inflation_std_dev=0.015,
        days_per_year=252,
        **kwargs,
    ):
        """Generate synthetic market data and initialize the simulator."""
        total_days = num_years * days_per_year

        # Convert annual stats to daily stats for the simulation
        daily_sp500_mean = (1 + sp500_mean) ** (1 / days_per_year) - 1
        daily_sp500_std_dev = sp500_std_dev / math.sqrt(days_per_year)

        daily_bonds_mean = (1 + bonds_mean) ** (1 / days_per_year) - 1
        daily_bonds_std_dev = bonds_std_dev / math.sqrt(days_per_year)

        daily_inflation_mean = (1 + inflation_mean) ** (1 / days_per_year) - 1
        daily_inflation_std_dev = inflation_std_dev / math.sqrt(days_per_year)

        # Generate the returns using the Box-Muller transform
        sp500_returns = cls._generate_normal_by_box_muller(
            daily_sp500_mean, daily_sp500_std_dev, total_days
        )
        bond_returns = cls._generate_normal_by_box_muller(
            daily_bonds_mean, daily_bonds_std_dev, total_days
        )
        inflation_returns = cls._generate_normal_by_box_muller(
            daily_inflation_mean, daily_inflation_std_dev, total_days
        )

        # Zip the returns into the list of tuples format the simulator expects
        returns = list(zip(sp500_returns, bond_returns, inflation_returns))

        return cls(returns=returns, days_per_year=days_per_year, **kwargs)

    def run(self):
        # Single simulation loop
        balance = self.initial_balance
        yearly_data = []
        all_withdrawals = []
        num_years = len(self.returns) // self.days_per_year

        for year_index in range(num_years):
            start_of_year_balance = balance
            day_of_withdrawal = year_index * self.days_per_year

            # Prepare context for the strategy
            context = {
                "current_balance": balance,
                "year_index": year_index,
                "trailing_returns": self.returns[
                    max(0, day_of_withdrawal - self.days_per_year) : day_of_withdrawal
                ],
                "initial_balance": self.initial_balance,
                "stock_allocation": self.stock_allocation,
            }
            withdrawal_this_year = self.strategy.calculate_annual_withdrawal(context)
            balance -= withdrawal_this_year
            all_withdrawals.append(withdrawal_this_year)

            # If balance is depleted after withdrawal, record the final state and stop.
            if balance <= 0:
                balance = 0  # Clamp to zero for clean output
                yearly_data.append(
                    {
                        "Year": year_index + 1,
                        "Start Balance": start_of_year_balance,
                        "Withdrawal": withdrawal_this_year,
                        "End Balance": balance,
                    }
                )
                break  # Exit the simulation loop

            # Apply daily returns for the year
            start_day = year_index * self.days_per_year
            end_day = start_day + self.days_per_year
            for day in range(start_day, end_day):
                sp500_r, bonds_r, _ = self.returns[day]
                blended_r = (
                    self.stock_allocation * sp500_r
                    + (1 - self.stock_allocation) * bonds_r
                )
                balance *= 1 + blended_r
                # If balance is depleted mid-year, stop daily calculations.
                if balance <= 0:
                    balance = 0
                    break

            yearly_data.append(
                {
                    "Year": year_index + 1,
                    "Start Balance": start_of_year_balance,
                    "Withdrawal": withdrawal_this_year,
                    "End Balance": balance,
                }
            )
            # If balance was depleted mid-year, exit the main simulation loop.
            if balance <= 0:
                break

        return pd.DataFrame(yearly_data), all_withdrawals


def run_simulation(etf_source, strategy_name, **kwargs):
    # Use the factory to create the appropriate strategy object
    strategy_obj = strategy_factory(strategy_name, **kwargs)

    sim = RetirementSimulator.from_csv(
        etf_source=etf_source,
        initial_balance=kwargs.get("initial_balance", 1_000_000),
        stock_allocation=kwargs.get("sp500_weight", 0.6),
        inflation_mean=kwargs.get("inflation_mean", 0.03),
        inflation_std_dev=kwargs.get("inflation_std_dev", 0.015),
        strategy=strategy_obj,
    )
    return sim.run()
