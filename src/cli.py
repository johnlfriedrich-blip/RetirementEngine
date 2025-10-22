# cli.py

import typer
from enum import Enum
from src import config
from src.synthetic_data import Distribution
from .resolve_path import resolve_path

# from refactored code
from src.factory import SimulatorFactory
from src.portfolio_builder import build_portfolio_from_cli

# from src.data_loader import DataSource
from src.reporting import (
    _print_mc_results,
    _print_comparison_results,
)
from src.runner import _run_and_print_simulation
from src.cli_helpers import build_strategy_args, build_data_args
from src.enums import DataSource, Strategy


# --- Path setup for robust data file access ---
_DEFAULT_DATA_PATH = resolve_path("src/data/market.csv")

app = typer.Typer(
    help="A command-line interface for the Retirement Engine.",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)


class StrategyName(str, Enum):
    """An enumeration for the available withdrawal strategies."""

    FIXED = "fixed"
    DYNAMIC = "dynamic"
    GUARDRAILS = "guardrails"
    PAUSE_AFTER_LOSS = "pause_after_loss"
    VPW = "vpw"


class DataSourceName(str, Enum):
    """An enumeration for the available data sources."""

    SYNTHETIC = "synthetic"
    HISTORICAL = "historical"


# --- Main App Callback ---
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """A CLI for running retirement simulations."""
    if ctx.invoked_subcommand is None:
        typer.echo(
            "No command specified. Use 'run' to start a simulation. See --help for details."
        )


# --- CLI Commands ---
@app.command()
def run(
    strategy: Strategy = typer.Option(
        ..., help="Withdrawal strategy to use.", case_sensitive=False
    ),
    initial_balance: float = typer.Option(
        config.START_BALANCE, help="Initial portfolio balance."
    ),
    portfolio_weights: str = typer.Option(
        "0.6,0.4", help="Portfolio weights for stocks and bonds (e.g., '0.6,0.4')."
    ),
    rate: float = typer.Option(
        0.04,
        help="Withdrawal rate for 'fixed', 'dynamic', and 'pause_after_loss' strategies.",
    ),
    stock_allocation: float = typer.Option(
        0.6, help="Stock allocation for 'pause_after_loss' strategy."
    ),
    min_pct: float = typer.Option(
        0.03, help="Minimum withdrawal percent for 'guardrails' strategy."
    ),
    max_pct: float = typer.Option(
        0.06, help="Maximum withdrawal percent for 'guardrails' strategy."
    ),
    start_age: int = typer.Option(65, help="Starting age for 'vpw' strategy."),
    inflation_mean: float = typer.Option(0.03, help="Mean annual inflation rate."),
    inflation_std_dev: float = typer.Option(
        0.015, help="Standard deviation of annual inflation."
    ),
    source: str = typer.Option(
        str(_DEFAULT_DATA_PATH), help="Path to market data CSV."
    ),
    start_year: int = typer.Option(
        None,
        help="Starting year for contiguous historical simulation (historical only).",
    ),
    bootstrap_block_size: int = typer.Option(
        None, help="Block size (days) for historical bootstrapping (historical only)."
    ),
):
    """Run a retirement simulation with a chosen withdrawal strategy."""
    weights = [float(w.strip()) for w in portfolio_weights.split(",")]
    strategy_args = {
        "initial_balance": initial_balance,
        "portfolio_weights": {"us_equities": weights[0], "bonds": weights[1]},
        "rate": rate,
        "stock_allocation": stock_allocation,
        "min_pct": min_pct,
        "max_pct": max_pct,
        "start_age": start_age,
    }
    data_args = {
        "etf_source": source,
        "inflation_mean": inflation_mean,
        "inflation_std_dev": inflation_std_dev,
    }

    _run_and_print_simulation(
        strategy_name=strategy.value,
        strategy_args=strategy_args,
        data_source="csv",
        data_args=data_args,
    )


@app.command()
def run_mc(
    strategy: Strategy = typer.Option(
        ..., help="Withdrawal strategy to use.", case_sensitive=False
    ),
    data_source: DataSource = typer.Option(
        DataSource.SYNTHETIC,
        help="Data source for the simulation.",
        case_sensitive=False,
    ),
    initial_balance: float = typer.Option(
        config.START_BALANCE, help="Initial portfolio balance."
    ),
    portfolio_weights: str = typer.Option(
        "us_equities:0.6,bonds:0.4", help="Portfolio weights as asset:weight pairs."
    ),
    # universal options
    inflation_mean: float = typer.Option(0.03, help="Mean annual inflation rate."),
    inflation_std_dev: float = typer.Option(0.015, help="Std dev of annual inflation."),
    sp500_mean: float = typer.Option(0.10, help="Mean annual return for equities."),
    sp500_std_dev: float = typer.Option(0.18, help="Std dev of annual equities."),
    bonds_mean: float = typer.Option(0.03, help="Mean annual return for bonds."),
    bonds_std_dev: float = typer.Option(0.06, help="Std dev of annual bonds."),
    num_simulations: int = typer.Option(
        config.NUM_SIMULATIONS, help="Number of Monte Carlo simulations."
    ),
    simulation_years: int = typer.Option(
        config.SIMULATION_YEARS, help="Duration of each simulation in years."
    ),
    distribution: Distribution = typer.Option(
        Distribution.BOX_MULLER, help="Distribution for synthetic data."
    ),
    df: int = typer.Option(3, help="Degrees of freedom for Student-t distribution."),
    start_year: int = typer.Option(
        None,
        help="Starting year for contiguous historical simulation (historical only).",
    ),
    bootstrap_block_size: int = typer.Option(
        None, help="Block size (days) for historical bootstrapping (historical only)."
    ),
    parallel: bool = typer.Option(
        True, help="Enable or disable parallel processing.", show_default=True
    ),
    # strategy-specific knobs (optional, only used if relevant)
    rate: float = typer.Option(
        0.04, help="Withdrawal rate (fixed/percent strategies)."
    ),
    min_pct: float = typer.Option(
        0.03, help="Minimum withdrawal percent (guardrails)."
    ),
    max_pct: float = typer.Option(
        0.06, help="Maximum withdrawal percent (guardrails)."
    ),
    start_age: int = typer.Option(65, help="Starting age (vpw)."),
):
    """Run a Monte Carlo simulation for a chosen withdrawal strategy."""
    portfolio_dict = build_portfolio_from_cli(portfolio_weights)

    # --- Build strategy_args conditionally ---
    strategy_args = build_strategy_args(
        strategy_name=strategy.value,
        initial_balance=initial_balance,
        portfolio_dict=portfolio_dict,
        rate=rate,
        min_pct=min_pct,
        max_pct=max_pct,
        start_age=start_age,
    )

    # --- Build data_args ---
    data_args = build_data_args(
        portfolio_dict=portfolio_dict,
        sp500_mean=sp500_mean,
        sp500_std_dev=sp500_std_dev,
        bonds_mean=bonds_mean,
        bonds_std_dev=bonds_std_dev,
        inflation_mean=inflation_mean,
        inflation_std_dev=inflation_std_dev,
        distribution=distribution,
        df=df,
        start_year=start_year,
        bootstrap_block_size=bootstrap_block_size,
    )

    factory = SimulatorFactory(
        strategy_name=strategy.value,
        strategy_args=strategy_args,
        data_source=data_source.value,
        data_args=data_args,
    )

    try:
        mc_sim = factory.create_monte_carlo(simulation_years, num_simulations, parallel)
        mc_results = mc_sim.run_simulations()
        _print_mc_results(mc_results, simulation_years)
    except (ValueError, TypeError) as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)


@app.command()
def compare_strategies(
    initial_balance: float = typer.Option(
        config.START_BALANCE, help="Initial portfolio balance."
    ),
    portfolio_weights: str = typer.Option(
        "us_equities:0.6,bonds:0.4", help="Portfolio weights as asset:weight pairs."
    ),
    # universal options
    inflation_mean: float = typer.Option(0.03, help="Mean annual inflation rate."),
    inflation_std_dev: float = typer.Option(0.015, help="Std dev of annual inflation."),
    sp500_mean: float = typer.Option(0.10, help="Mean annual return for equities."),
    sp500_std_dev: float = typer.Option(0.18, help="Std dev of annual equities."),
    bonds_mean: float = typer.Option(0.03, help="Mean annual return for bonds."),
    bonds_std_dev: float = typer.Option(0.06, help="Std dev of annual bonds."),
    num_simulations: int = typer.Option(
        config.NUM_SIMULATIONS, help="Number of Monte Carlo simulations."
    ),
    simulation_years: int = typer.Option(
        config.SIMULATION_YEARS, help="Duration of each simulation in years."
    ),
    distribution: Distribution = typer.Option(
        Distribution.BOX_MULLER, help="Distribution for synthetic data."
    ),
    df: int = typer.Option(3, help="Degrees of freedom for Student-t distribution."),
    start_year: int = typer.Option(
        None,
        help="Starting year for contiguous historical simulation (historical only).",
    ),
    bootstrap_block_size: int = typer.Option(
        None, help="Block size (days) for historical bootstrapping (historical only)."
    ),
    parallel: bool = typer.Option(
        True, help="Enable or disable parallel processing.", show_default=True
    ),
    data_source: DataSource = typer.Option(
        DataSource.SYNTHETIC,
        help="Data source for the simulation.",
        case_sensitive=False,
    ),
    # strategy-specific knobs (optional, only used if relevant)
    rate: float = typer.Option(
        0.04, help="Withdrawal rate (fixed/percent strategies)."
    ),
    min_pct: float = typer.Option(
        0.03, help="Minimum withdrawal percent (guardrails)."
    ),
    max_pct: float = typer.Option(
        0.06, help="Maximum withdrawal percent (guardrails)."
    ),
    start_age: int = typer.Option(65, help="Starting age (vpw)."),
):
    """Compare all withdrawal strategies using the same Monte Carlo simulation inputs."""
    portfolio_dict = build_portfolio_from_cli(portfolio_weights)

    results = []
    for strategy_enum in Strategy:
        strategy_args = build_strategy_args(
            strategy_name=strategy_enum.value,
            initial_balance=initial_balance,
            portfolio_dict=portfolio_dict,
            rate=rate,
            min_pct=min_pct,
            max_pct=max_pct,
            start_age=start_age,
        )

        data_args = build_data_args(
            portfolio_dict=portfolio_dict,
            sp500_mean=sp500_mean,
            sp500_std_dev=sp500_std_dev,
            bonds_mean=bonds_mean,
            bonds_std_dev=bonds_std_dev,
            inflation_mean=inflation_mean,
            inflation_std_dev=inflation_std_dev,
            distribution=distribution,
            df=df,
            start_year=start_year,
            bootstrap_block_size=bootstrap_block_size,
        )

        try:
            factory = SimulatorFactory(
                strategy_name=strategy_enum.value,
                strategy_args=strategy_args,
                data_source=data_source.value,
                data_args=data_args,
            )

            mc_sim = factory.create_monte_carlo(
                simulation_years=simulation_years,
                num_simulations=num_simulations,
                parallel=parallel,
            )
            mc_results = mc_sim.run_simulations()

            if not mc_results.results_df.empty:
                final_balances = mc_results.results_df["End Balance"]
                p10, p50, p90 = final_balances.quantile([0.10, 0.50, 0.90])
                results.append(
                    {
                        "Strategy": strategy_enum.value,
                        "Success Rate": mc_results.success_rate(),
                        "Median Balance": p50,
                        "10th Percentile": p10,
                        "90th Percentile": p90,
                    }
                )
            else:
                results.append(
                    {
                        "Strategy": strategy_enum.value,
                        "Success Rate": 0.0,
                        "Median Balance": 0.0,
                        "10th Percentile": 0.0,
                        "90th Percentile": 0.0,
                    }
                )
        except (ValueError, TypeError) as e:
            typer.echo(
                typer.style(
                    f"Error running strategy {strategy_enum.value}: {e}",
                    fg=typer.colors.RED,
                ),
                err=True,
            )

    if results:
        _print_comparison_results(results)


if __name__ == "__main__":
    app()
