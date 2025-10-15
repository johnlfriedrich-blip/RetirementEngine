# cli.py
"""This module provides a command-line interface (CLI) for the Retirement Engine.

It uses the Typer library to create a user-friendly interface for running single
retirement simulations and comprehensive Monte Carlo analyses.
"""

import pathlib
import pandas as pd
import math
import typer
from typing_extensions import Annotated
from enum import Enum
from dataclasses import dataclass, asdict
from retirement_engine.simulator import RetirementSimulator
from retirement_engine.withdrawal_strategies import strategy_factory
from retirement_engine import data_loader, config
from retirement_engine.monte_carlo import MonteCarloSimulator

# --- Path setup for robust data file access ---
# Get the directory of the current CLI file to build reliable paths.
_CLI_DIR = pathlib.Path(__file__).parent.resolve()
# Navigate up to the project's root directory.
_PROJECT_ROOT = _CLI_DIR.parent
# Define the default path for market data relative to the project root.
_DEFAULT_DATA_PATH = "data/market.csv"

# Initialize the Typer application.
app = typer.Typer(
    help="A command-line interface for the Retirement Engine.",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False, # Disable shell completion for simplicity.
)


class Strategy(str, Enum):
    """An enumeration for the available withdrawal strategies.
    
    This makes the CLI more robust by ensuring only valid strategies can be chosen.
    """

    FIXED = "fixed"
    DYNAMIC = "dynamic"
    GUARDRAILS = "guardrails"
    PAUSE_AFTER_LOSS = "pause_after_loss"
    VPW = "vpw"




# --- Main App Callback ---
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """A CLI for running retirement simulations.

    If no subcommand is provided, this function is called and prints a
    helpful message guiding the user.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(
            "No command specified. Use 'run' to start a simulation. See --help for details."
        )


# --- Result Printing Helpers ---
def _print_formatted_results(results_df, withdrawals):
    """Helper function to format and print single simulation results to the console.

    Args:
        results_df (pd.DataFrame): A DataFrame containing the yearly results of the simulation.
        withdrawals (list): A list of withdrawal amounts for each year.
    """
    # Handle the case where the simulation produces no data.
    if results_df.empty:
        typer.echo(
            typer.style(
                "\n[ERROR] Simulation failed to produce results.", fg=typer.colors.RED
            )
        )
        typer.echo(
            "This could be due to an empty or invalid market data file, or an issue with synthetic data generation."
        )
        raise typer.Exit(code=1)

    # Print the main results table.
    typer.echo("\n" + "=" * 50)
    typer.echo(" " * 18 + "YEARLY RESULTS")
    typer.echo("=" * 50)
    with pd.option_context(
        "display.max_rows", None, "display.float_format", "${:,.2f}".format
    ):
        typer.echo(results_df.to_string(index=False))
    typer.echo("=" * 50)

    # Print a summary of the outcome.
    final_balance = results_df["End Balance"].iloc[-1]
    summary_style = typer.style("[SUMMARY]", bold=True)
    if not math.isfinite(final_balance):
        typer.echo(
            f"\n{summary_style} Final Balance: Simulation resulted in a non-finite number ({final_balance})."
        )
        typer.echo("This is likely due to extreme values in the market data.")
    elif final_balance > 0:
        # Success case: Portfolio survived.
        typer.echo(
            typer.style(
                f"\n{summary_style} Portfolio Survived! Final Balance: ${final_balance:,.2f}",
                fg=typer.colors.GREEN,
            )
        )
    else:
        # Failure case: Portfolio was depleted.
        typer.echo(
            typer.style(
                f"\n{summary_style} Portfolio Depleted in Year {len(withdrawals)}.",
                fg=typer.colors.RED,
            )
        )
    typer.echo(f"{summary_style} Total Withdrawn: ${sum(withdrawals):,.2f}")
    typer.echo("-" * 30)


def _print_mc_results(mc_sim: MonteCarloSimulator):
    """Helper function to format and print Monte Carlo simulation results.

    Args:
        mc_sim (MonteCarloSimulator): The completed Monte Carlo simulator instance.
    """
    typer.echo("\n" + "=" * 50)
    typer.echo(" " * 15 + "MONTE CARLO RESULTS")
    typer.echo("=" * 50)

    success_rate = mc_sim.success_rate()
    # Dynamically color the success rate based on its value for quick visual feedback.
    color = (
        typer.colors.GREEN
        if success_rate >= 0.95
        else typer.colors.YELLOW
        if success_rate >= 0.85
        else typer.colors.RED
    )

    summary_style = typer.style("[SUMMARY]", bold=True)
    typer.echo(
        typer.style(
            f"\n{summary_style} Strategy Success Rate: {success_rate:.1%}",
            fg=color,
            bold=True,
        )
    )
    typer.echo(
        f"{summary_style} Ran {mc_sim.num_simulations} simulations over {mc_sim.duration_years} years."
    )

    # Print percentile information if results are available.
    if mc_sim.results is not None:
        # Get the final balance from the last year of each simulation run.
        final_balances = mc_sim.results.loc[
            mc_sim.results.groupby("Run")["Year"].idxmax()
        ]["End Balance"]
        p10, p50, p90 = final_balances.quantile([0.10, 0.50, 0.90])

        typer.echo("\n" + "-" * 30)
        typer.echo("  Portfolio Balance Percentiles:")
        typer.echo(f"  - 10th (Worst Case): ${p10:,.2f}")
        typer.echo(f"  - 50th (Median):     ${p50:,.2f}")
        typer.echo(f"  - 90th (Best Case):  ${p90:,.2f}")
        typer.echo("-" * 30)

def _print_comparison_results(results: list):
    """Helper function to format and print strategy comparison results.

    Args:
        results (list): A list of dictionaries, where each dictionary summarizes
                        the results for a single strategy.
    """
    typer.echo("\n" + "=" * 70)
    typer.echo(" " * 20 + "STRATEGY COMPARISON RESULTS")
    typer.echo("=" * 70)

    # Convert the list of results into a pandas DataFrame for easy formatting.
    df = pd.DataFrame(results)
    # Format columns for better readability.
    df["Success Rate"] = df["Success Rate"].apply(lambda x: f"{x:.1%}")
    df["Median Balance"] = df["Median Balance"].apply(lambda x: f"${x:,.2f}")
    df["10th Percentile"] = df["10th Percentile"].apply(lambda x: f"${x:,.2f}")
    df["90th Percentile"] = df["90th Percentile"].apply(lambda x: f"${x:,.2f}")

    # Print the DataFrame to the console without an index.
    with pd.option_context("display.max_rows", None, "display.width", None):
        typer.echo(df.to_string(index=False))
    typer.echo("=" * 70)




# --- CLI Commands ---
class DataSource(str, Enum):
    """Enumeration for the different sources of market data."""
    CSV = "csv"
    AV = "av"  # Alpha Vantage
    YF = "yf"  # Yahoo Finance

@app.command()
def run(
    # --- Core Simulation Options ---
    strategy: Strategy = typer.Option(..., help="Withdrawal strategy to use.", case_sensitive=False),
    initial_balance: float = typer.Option(config.START_BALANCE, help="Initial portfolio balance."),
    stock_allocation: float = typer.Option(config.STOCK_ALLOCATION, help="Stock allocation (e.g., 0.6 for 60%)."),
    
    # --- Strategy-Specific Options ---
    rate: float = typer.Option(config.WITHDRAWAL_RATE, help="Withdrawal rate for 'fixed', 'dynamic', and 'pause_after_loss' strategies."),
    min_pct: float = typer.Option(config.GUARDRAILS_MIN_PCT, help="Minimum withdrawal percent for 'guardrails' strategy."),
    max_pct: float = typer.Option(config.GUARDRAILS_MAX_PCT, help="Maximum withdrawal percent for 'guardrails' strategy."),
    start_age: int = typer.Option(config.START_AGE, help="Starting age for 'vpw' strategy."),

    # --- Data Source Options ---
    data_source: DataSource = typer.Option(DataSource.CSV, "--data-source", help="Data source to use.", case_sensitive=False),
    source: str = typer.Option(str(_DEFAULT_DATA_PATH), help="Path to market data CSV."),
    stock_ticker: str = typer.Option("VTI", help="Stock ticker for Alpha Vantage or Yahoo Finance."),
    bond_ticker: str = typer.Option("BND", help="Bond ticker for Alpha Vantage or Yahoo Finance."),

    # --- Synthetic Data Generation Options ---
    synthetic: bool = typer.Option(False, "--synthetic", help="Use synthetically generated market data."),
    num_years: int = typer.Option(config.DURATION_YEARS, help="Number of years to simulate (synthetic only)."),
    sp500_mean: float = typer.Option(config.STOCK_MEAN_RETURN, help="Mean annual return for stocks (synthetic only)."),
    sp500_std_dev: float = typer.Option(config.STOCK_STD_DEV, help="Std dev of annual stock returns (synthetic only)."),
    bonds_mean: float = typer.Option(config.BOND_MEAN_RETURN, help="Mean annual return for bonds (synthetic only)."),
    bonds_std_dev: float = typer.Option(config.BOND_STD_DEV, help="Std dev of annual bond returns (synthetic only)."),
    inflation_mean: float = typer.Option(config.INFLATION_MEAN, help="Mean annual inflation rate (for all data sources)."),
    inflation_std_dev: float = typer.Option(config.INFLATION_STD_DEV, help="Std dev of annual inflation (for all data sources)."),
):
    """Run a single retirement simulation using historical or synthetic data."""
    # Consolidate all strategy-related arguments into a single dictionary.
    strategy_args = {
        "initial_balance": initial_balance,
        "stock_allocation": stock_allocation,
        "rate": rate,
        "min_pct": min_pct,
        "max_pct": max_pct,
        "start_age": start_age,
    }

    # Determine the data source and load the market returns.
    if synthetic:
        # Generate synthetic market data based on the provided statistical parameters.
        data_args = {
            "num_years": num_years,
            "inflation_mean": inflation_mean,
            "inflation_std_dev": inflation_std_dev,
            "sp500_mean": sp500_mean,
            "sp500_std_dev": sp500_std_dev,
            "bonds_mean": bonds_mean,
            "bonds_std_dev": bonds_std_dev,
        }
        returns = data_loader.from_synthetic_data(**data_args)
    elif data_source == DataSource.CSV:
        # Load market data from a local CSV file.
        data_args = {"etf_source": source, "inflation_mean": inflation_mean, "inflation_std_dev": inflation_std_dev}
        source_path = pathlib.Path(data_args["etf_source"])
        if not source_path.is_file():
            typer.echo(
                typer.style(
                    f"Error: Data source not found at '{source_path}'.",
                    fg=typer.colors.RED,
                ),
                err=True,
            )
            raise typer.Exit(code=1)
        returns = data_loader.from_csv(**data_args)
    elif data_source == DataSource.AV:
        # Load market data from the Alpha Vantage API.
        data_args = {"stock_ticker": stock_ticker, "bond_ticker": bond_ticker, "inflation_mean": inflation_mean, "inflation_std_dev": inflation_std_dev}
        returns = data_loader.from_av(**data_args)
    elif data_source == DataSource.YF:
        # Load market data from the Yahoo Finance API.
        data_args = {"stock_ticker": stock_ticker, "bond_ticker": bond_ticker, "inflation_mean": inflation_mean, "inflation_std_dev": inflation_std_dev}
        returns = data_loader.from_yf(**data_args)


    try:
        # Create and run the simulation.
        typer.echo(f"Running simulation with '{strategy.value}' strategy...")
        # Use the factory to create the appropriate strategy object.
        strategy_obj = strategy_factory(strategy.value, **strategy_args)

        # Initialize the simulator with the loaded data and strategy.
        sim = RetirementSimulator(
            returns=returns,
            initial_balance=strategy_args["initial_balance"],
            stock_allocation=strategy_args["stock_allocation"],
            strategy=strategy_obj,
        )
        results_df, withdrawals = sim.run()
        _print_formatted_results(results_df, withdrawals)
    except (ValueError, TypeError) as e:
        # Catch errors during strategy creation or simulation (e.g., bad parameters).
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)


@app.command()
def run_mc(
    # --- Strategy Selection ---
    strategy: Strategy = typer.Option(Strategy.FIXED, help="Withdrawal strategy to use (ignored if --compare-all).", case_sensitive=False),
    compare_all: bool = typer.Option(False, "--compare-all", help="Compare all withdrawal strategies instead of running a single one."),

    # --- Core Simulation Parameters ---
    initial_balance: float = typer.Option(config.START_BALANCE, help="Initial portfolio balance."),
    stock_allocation: float = typer.Option(config.STOCK_ALLOCATION, help="Stock allocation (e.g., 0.6 for 60%)."),
    num_simulations: int = typer.Option(config.NUM_SIMULATIONS, help="Number of Monte Carlo simulations."),
    duration_years: int = typer.Option(config.DURATION_YEARS, help="Duration of each simulation in years."),

    # --- Strategy-Specific Parameters ---
    rate: float = typer.Option(config.WITHDRAWAL_RATE, help="Withdrawal rate for applicable strategies."),
    min_pct: float = typer.Option(config.GUARDRAILS_MIN_PCT, help="Minimum withdrawal percent for 'guardrails' strategy."),
    max_pct: float = typer.Option(config.GUARDRAILS_MAX_PCT, help="Maximum withdrawal percent for 'guardrails' strategy."),
    start_age: int = typer.Option(config.START_AGE, help="Starting age for 'vpw' strategy."),

    # --- Market Data Generation Parameters ---
    inflation_mean: float = typer.Option(config.INFLATION_MEAN, help="Mean annual inflation rate."),
    inflation_std_dev: float = typer.Option(config.INFLATION_STD_DEV, help="Standard deviation of annual inflation."),
    stock_mean_return: float = typer.Option(config.STOCK_MEAN_RETURN, help="Mean annual return for stocks."),
    stock_std_dev: float = typer.Option(config.STOCK_STD_DEV, help="Standard deviation of annual stock returns."),
    bond_mean_return: float = typer.Option(config.BOND_MEAN_RETURN, help="Mean annual return for bonds."),
    bond_std_dev: float = typer.Option(config.BOND_STD_DEV, help="Standard deviation of annual bond returns."),

    # --- Performance Options ---
    parallel: bool = typer.Option(config.PARALLEL_PROCESSING, help="Enable or disable parallel processing.", show_default=True),
):
    """Run a Monte Carlo simulation for one or all withdrawal strategies."""

    # Consolidate arguments for easy passing to other functions.
    strategy_args = {
        "initial_balance": initial_balance,
        "stock_allocation": stock_allocation,
        "rate": rate,
        "min_pct": min_pct,
        "max_pct": max_pct,
        "start_age": start_age,
    }
    market_data_args = {
        "inflation_mean": inflation_mean,
        "inflation_std_dev": inflation_std_dev,
        "stock_mean_return": stock_mean_return,
        "stock_std_dev": stock_std_dev,
        "bond_mean_return": bond_mean_return,
        "bond_std_dev": bond_std_dev,
    }

    if not compare_all:
        # --- Run a single Monte Carlo simulation for a specific strategy ---
        typer.echo(f"Running Monte Carlo simulation with '{strategy.value}' strategy...")
        try:
            mc_sim = MonteCarloSimulator(
                num_simulations=num_simulations,
                duration_years=duration_years,
                market_data_generator_args=market_data_args,
                parallel=parallel,
            )
            mc_sim.run(strategy_name=strategy.value, full_results=False, **strategy_args)
            _print_mc_results(mc_sim)
        except (ValueError, TypeError) as e:
            typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
            raise typer.Exit(code=1)
    else:
        # --- Run a comparison of all available strategies ---
        typer.echo("Comparing all withdrawal strategies...")
        results = []
        strategies_to_run = list(Strategy)

        for strat in strategies_to_run:
            typer.echo(f"\nRunning simulation for '{strat.value}'...")
            try:
                mc_sim = MonteCarloSimulator(
                    num_simulations=num_simulations,
                    duration_years=duration_years,
                    market_data_generator_args=market_data_args,
                    parallel=parallel,
                )
                mc_sim.run(strategy_name=strat.value, full_results=False, **strategy_args)

                # Collect results if the simulation was successful.
                if mc_sim.results is not None and not mc_sim.results.empty:
                    final_balances = mc_sim.results.loc[
                        mc_sim.results.groupby("Run")["Year"].idxmax()
                    ]["End Balance"]
                    p10, p50, p90 = final_balances.quantile([0.10, 0.50, 0.90])
                    results.append({
                        "Strategy": strat.value,
                        "Success Rate": mc_sim.success_rate(),
                        "Median Balance": p50,
                        "10th Percentile": p10,
                        "90th Percentile": p90,
                    })
                else:
                    # Append a failure record if the simulation produced no results.
                    results.append({
                        "Strategy": strat.value,
                        "Success Rate": 0.0,
                        "Median Balance": 0.0,
                        "10th Percentile": 0.0,
                        "90th Percentile": 0.0,
                    })

            except (ValueError, TypeError) as e:
                # Report errors for a specific strategy but continue with the comparison.
                typer.echo(typer.style(f"Error running strategy {strat.value}: {e}", fg=typer.colors.RED), err=True)

        if results:
            _print_comparison_results(results)


if __name__ == "__main__":
    # This allows the script to be run directly for development and debugging.
    app()
