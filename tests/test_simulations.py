import pytest
import numpy as np
import pandas as pd
from scipy.stats import kurtosis

from retirement_engine import config
from retirement_engine.market_data import MarketDataGenerator
from retirement_engine.monte_carlo import MonteCarloSimulator
from retirement_engine.simulator import RetirementSimulator

# --- Tests for MarketDataGenerator ---

def test_market_data_generator_shape():
    """Tests that the generator produces returns for the correct number of days."""
    gen = MarketDataGenerator()
    duration = 5
    returns = gen.generate_returns(duration_years=duration)
    assert len(returns) == duration * config.TRADINGDAYS
    assert isinstance(returns[0], tuple)


def test_market_data_generator_distributions():
    """
    Performs a statistical test on the generated distributions.
    Checks if the mean and standard deviation of a large sample are close to the target.
    Also checks that the Student's t-distribution has fatter tails (higher kurtosis).
    """
    num_samples = 500_000  # Use a large sample for statistical significance
    mean, std_dev = 0.05, 0.15

    # Test Normal Distribution
    gen_normal = MarketDataGenerator(distribution_type="normal")
    samples_normal = gen_normal._generate_random_variates(mean, std_dev, num_samples)

    assert np.mean(samples_normal) == pytest.approx(mean, abs=1e-3)
    assert np.std(samples_normal) == pytest.approx(std_dev, abs=1e-3)
    kurtosis_normal = kurtosis(samples_normal)

    # Test Student's t-Distribution
    gen_student_t = MarketDataGenerator(distribution_type="student-t", student_t_df=5)
    samples_student_t = gen_student_t._generate_random_variates(
        mean, std_dev, num_samples
    )

    assert np.mean(samples_student_t) == pytest.approx(mean, abs=1e-3)
    assert np.std(samples_student_t) == pytest.approx(
        std_dev, abs=1e-2
    )  # Higher tolerance
    kurtosis_student_t = kurtosis(samples_student_t)

    # Kurtosis for a normal distribution is ~0. For a t-distribution, it's > 0.
    assert kurtosis_student_t > kurtosis_normal
    assert kurtosis_student_t > 1  # Expect significantly fatter tails


def test_market_data_generator_errors():
    """Tests error conditions for the generator."""
    # Error for invalid degrees of freedom
    with pytest.raises(ValueError, match="must be > 2"):
        MarketDataGenerator(distribution_type="student-t", student_t_df=2)

    # Error for unknown distribution type
    gen = MarketDataGenerator(distribution_type="unknown")
    with pytest.raises(ValueError, match="Unknown distribution type"):
        gen.generate_returns(1)


# --- Tests for MonteCarloSimulator ---


def _mock_simulator_factory(mock_simulator):
    """A top-level function to create a mock simulator for pickling."""
    return mock_simulator


def test_monte_carlo_simulator_run_structure(mocker):
    """
    Tests the overall structure of the output from a Monte Carlo run.
    Mocks the underlying simulation to return predictable data.
    """
    num_sims = 5
    duration = 10

    # Mock the RetirementSimulator class
    mock_yearly_df = pd.DataFrame({"Year": range(1, duration + 1)})
    mock_simulator = mocker.Mock(spec=RetirementSimulator)
    mock_simulator.run.side_effect = [(mock_yearly_df.copy(), []) for _ in range(num_sims)]

    mc_sim = MonteCarloSimulator(
        num_simulations=num_sims,
        duration_years=duration,
        simulator_class=lambda **kwargs: _mock_simulator_factory(mock_simulator),
        parallel=False,  # Disable parallel for testing
    )
    results = mc_sim.run(strategy_name="fixed", initial_balance=1e6, rate=0.04)

    assert isinstance(results, pd.DataFrame)
    assert "Run" in results.columns
    assert len(results) == num_sims * duration
    assert set(results["Run"].unique()) == set(range(num_sims))


def test_monte_carlo_success_rate(mocker):
    """
    Tests the success_rate calculation by mocking simulation outcomes.
    """
    # --- Scenario 1: 100% success ---
    mock_success_df = pd.DataFrame({"Year": [1, 2], "End Balance": [500, 100]})
    mock_simulator_success = mocker.Mock(spec=RetirementSimulator)
    mock_simulator_success.run.side_effect = [(mock_success_df.copy(), []) for _ in range(10)]

    mc_sim_success = MonteCarloSimulator(
        num_simulations=10,
        duration_years=2,
        simulator_class=lambda **kwargs: _mock_simulator_factory(mock_simulator_success),
        parallel=False,  # Disable parallel for testing
    )
    mc_sim_success.run(strategy_name="fixed", initial_balance=1e6, rate=0.04)
    assert mc_sim_success.success_rate() == 1.0

    # --- Scenario 2: 0% success ---
    mock_fail_df = pd.DataFrame({"Year": [1, 2], "End Balance": [500, 0]})
    mock_simulator_fail = mocker.Mock(spec=RetirementSimulator)
    mock_simulator_fail.run.side_effect = [(mock_fail_df.copy(), []) for _ in range(10)]

    mc_sim_fail = MonteCarloSimulator(
        num_simulations=10,
        duration_years=2,
        simulator_class=lambda **kwargs: _mock_simulator_factory(mock_simulator_fail),
        parallel=False,  # Disable parallel for testing
    )
    mc_sim_fail.run(strategy_name="fixed", initial_balance=1e6, rate=0.04)
    assert mc_sim_fail.success_rate() == 0.0

    # --- Scenario 3: 50% success ---
    mock_simulator_mixed = mocker.Mock(spec=RetirementSimulator)
    mock_simulator_mixed.run.side_effect = [
        (mock_success_df.copy(), []) if i % 2 == 0 else (mock_fail_df.copy(), [])
        for i in range(10)
    ]
    mc_sim_mixed = MonteCarloSimulator(
        num_simulations=10,
        duration_years=2,
        simulator_class=lambda **kwargs: _mock_simulator_factory(mock_simulator_mixed),
        parallel=False,  # Disable parallel for testing
    )
    mc_sim_mixed.run(strategy_name="fixed", initial_balance=1e6, rate=0.04)
    assert mc_sim_mixed.success_rate() == 0.5


def test_monte_carlo_success_rate_before_run():
    """Tests that calling success_rate before run raises an error."""
    mc_sim = MonteCarloSimulator()
    with pytest.raises(RuntimeError, match="Simulation has not been run yet"):
        mc_sim.success_rate()