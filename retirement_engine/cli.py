# cli.py
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
_CLI_DIR = pathlib.Path(__file__).parent.resolve()
_PROJECT_ROOT = _CLI_DIR.parent
_DEFAULT_DATA_PATH = "data/market.csv"

app = typer.Typer(
    help="A command-line interface for the Retirement Engine.",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)


class Strategy(str, Enum):
    """An enumeration for the available withdrawal strategies."""

    FIXED = "fixed"
    DYNAMIC = "dynamic"
    GUARDRAILS = "guardrails"
    PAUSE_AFTER_LOSS = "pause_after_loss"
    VPW = "vpw"




# --- Main App Callback ---
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """A CLI for running retirement simulations."""
    if ctx.invoked_subcommand is None:
        typer.echo(
            "No command specified. Use 'run' to start a simulation. See --help for details."
        )


# --- Result Printing Helpers ---
def _print_formatted_results(results_df, withdrawals):
    """Helper function to format and print simulation results."""
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

    typer.echo("\n" + "=" * 50)
    typer.echo(" " * 18 + "YEARLY RESULTS")
    typer.echo("=" * 50)
    with pd.option_context(
        "display.max_rows", None, "display.float_format", "${:,.2f}".format
    ):
        typer.echo(results_df.to_string(index=False))
    typer.echo("=" * 50)

    final_balance = results_df["End Balance"].iloc[-1]
    summary_style = typer.style("[SUMMARY]", bold=True)
    if not math.isfinite(final_balance):
        typer.echo(
            f"\n{summary_style} Final Balance: Simulation resulted in a non-finite number ({final_balance})."
        )
        typer.echo("This is likely due to extreme values in the market data.")
    elif final_balance > 0:
        typer.echo(
            typer.style(
                f"\n{summary_style} Portfolio Survived! Final Balance: ${final_balance:,.2f}",
                fg=typer.colors.GREEN,
            )
        )
    else:
        typer.echo(
            typer.style(
                f"\n{summary_style} Portfolio Depleted in Year {len(withdrawals)}.",
                fg=typer.colors.RED,
            )
        )
    typer.echo(f"{summary_style} Total Withdrawn: ${sum(withdrawals):,.2f}")
    typer.echo("-" * 30)


def _print_mc_results(mc_sim: MonteCarloSimulator):
    """Helper function to format and print Monte Carlo simulation results."""
    typer.echo("\n" + "=" * 50)
    typer.echo(" " * 15 + "MONTE CARLO RESULTS")
    typer.echo("=" * 50)

    success_rate = mc_sim.success_rate()
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

    if mc_sim.results is not None:
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
    """Helper function to format and print strategy comparison results."""
    typer.echo("\n" + "=" * 70)
    typer.echo(" " * 20 + "STRATEGY COMPARISON RESULTS")
    typer.echo("=" * 70)

    df = pd.DataFrame(results)
    df["Success Rate"] = df["Success Rate"].apply(lambda x: f"{x:.1%}")
    df["Median Balance"] = df["Median Balance"].apply(lambda x: f"${x:,.2f}")
    df["10th Percentile"] = df["10th Percentile"].apply(lambda x: f"${x:,.2f}")
    df["90th Percentile"] = df["90th Percentile"].apply(lambda x: f"${x:,.2f}")

    with pd.option_context("display.max_rows", None, "display.width", None):
        typer.echo(df.to_string(index=False))
    typer.echo("=" * 70)




# --- CLI Commands ---
class DataSource(str, Enum):
    CSV = "csv"
    AV = "av"
    YF = "yf"

@app.command()
def run(
    strategy: Strategy = typer.Option(..., help="Withdrawal strategy to use.", case_sensitive=False),
    initial_balance: float = typer.Option(config.START_BALANCE, help="Initial portfolio balance."),
    stock_allocation: float = typer.Option(config.STOCK_ALLOCATION, help="Stock allocation (e.g., 0.6 for 60%)."),
    rate: float = typer.Option(config.WITHDRAWAL_RATE, help="Withdrawal rate for 'fixed', 'dynamic', and 'pause_after_loss' strategies."),
    min_pct: float = typer.Option(config.GUARDRAILS_MIN_PCT, help="Minimum withdrawal percent for 'guardrails' strategy."),
    max_pct: float = typer.Option(config.GUARDRAILS_MAX_PCT, help="Maximum withdrawal percent for 'guardrails' strategy."),
    start_age: int = typer.Option(config.START_AGE, help="Starting age for 'vpw' strategy."),
    inflation_mean: float = typer.Option(config.INFLATION_MEAN, help="Mean annual inflation rate."),
    inflation_std_dev: float = typer.Option(config.INFLATION_STD_DEV, help="Standard deviation of annual inflation."),
    # Data source options
    data_source: DataSource = typer.Option(DataSource.CSV, "--data-source", help="Data source to use.", case_sensitive=False),
    # CSV-specific options
    source: str = typer.Option(str(_DEFAULT_DATA_PATH), help="Path to market data CSV."),
    # AV/YF-specific options
    stock_ticker: str = typer.Option("VTI", help="Stock ticker to use for Alpha Vantage or Yahoo Finance."),
    bond_ticker: str = typer.Option("BND", help="Bond ticker to use for Alpha Vantage or Yahoo Finance."),
    # Synthetic-specific options
    synthetic: bool = typer.Option(False, "--synthetic", help="Use synthetically generated market data instead of a CSV source."),
    sp500_mean: float = typer.Option(config.STOCK_MEAN_RETURN, help="Mean annual return for stocks (synthetic)."),
    sp500_std_dev: float = typer.Option(config.STOCK_STD_DEV, help="Standard deviation of annual stock returns (synthetic)."),
    bonds_mean: float = typer.Option(config.BOND_MEAN_RETURN, help="Mean annual return for bonds (synthetic)."),
    bonds_std_dev: float = typer.Option(config.BOND_STD_DEV, help="Standard deviation of annual bond returns (synthetic)."),
    num_years: int = typer.Option(config.DURATION_YEARS, help="Number of years to simulate (synthetic)."),
):
    """Run a single retirement simulation using historical (CSV) or synthetic data."""
    strategy_args = {
        "initial_balance": initial_balance,
        "stock_allocation": stock_allocation,
        "rate": rate,
        "min_pct": min_pct,
        "max_pct": max_pct,
        "start_age": start_age,
    }

    if synthetic:
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
        data_args = {"stock_ticker": stock_ticker, "bond_ticker": bond_ticker, "inflation_mean": inflation_mean, "inflation_std_dev": inflation_std_dev}
        returns = data_loader.from_av(**data_args)
    elif data_source == DataSource.YF:
        data_args = {"stock_ticker": stock_ticker, "bond_ticker": bond_ticker, "inflation_mean": inflation_mean, "inflation_std_dev": inflation_std_dev}
        returns = data_loader.from_yf(**data_args)


    try:
        typer.echo(f"Running simulation with '{strategy.value}' strategy...")
        strategy_obj = strategy_factory(strategy.value, **strategy_args)

        sim = RetirementSimulator(
            returns=returns,
            initial_balance=strategy_args["initial_balance"],
            stock_allocation=strategy_args["stock_allocation"],
            strategy=strategy_obj,
        )
        results_df, withdrawals = sim.run()
        _print_formatted_results(results_df, withdrawals)
    except (ValueError, TypeError) as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)


@app.command()
def run_mc(
    strategy: Strategy = typer.Option(Strategy.FIXED, help="Withdrawal strategy to use (ignored if --compare-all).", case_sensitive=False),
    compare_all: bool = typer.Option(False, "--compare-all", help="Compare all withdrawal strategies instead of running a single one."),
    initial_balance: float = typer.Option(config.START_BALANCE, help="Initial portfolio balance."),
    stock_allocation: float = typer.Option(config.STOCK_ALLOCATION, help="Stock allocation (e.g., 0.6 for 60%)."),
    rate: float = typer.Option(config.WITHDRAWAL_RATE, help="Withdrawal rate for applicable strategies."),
    min_pct: float = typer.Option(config.GUARDRAILS_MIN_PCT, help="Minimum withdrawal percent for 'guardrails' strategy."),
    max_pct: float = typer.Option(config.GUARDRAILS_MAX_PCT, help="Maximum withdrawal percent for 'guardrails' strategy."),
    start_age: int = typer.Option(config.START_AGE, help="Starting age for 'vpw' strategy."),
    inflation_mean: float = typer.Option(config.INFLATION_MEAN, help="Mean annual inflation rate."),
    inflation_std_dev: float = typer.Option(config.INFLATION_STD_DEV, help="Standard deviation of annual inflation."),
    stock_mean_return: float = typer.Option(config.STOCK_MEAN_RETURN, help="Mean annual return for stocks."),
    stock_std_dev: float = typer.Option(config.STOCK_STD_DEV, help="Standard deviation of annual stock returns."),
    bond_mean_return: float = typer.Option(config.BOND_MEAN_RETURN, help="Mean annual return for bonds."),
    bond_std_dev: float = typer.Option(config.BOND_STD_DEV, help="Standard deviation of annual bond returns."),
    num_simulations: int = typer.Option(config.NUM_SIMULATIONS, help="Number of Monte Carlo simulations."),
    duration_years: int = typer.Option(config.DURATION_YEARS, help="Duration of each simulation in years."),
    parallel: bool = typer.Option(config.PARALLEL_PROCESSING, help="Enable or disable parallel processing.", show_default=True),
):
    """Run a Monte Carlo simulation for one or all withdrawal strategies."""

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
                    results.append({
                        "Strategy": strat.value,
                        "Success Rate": 0.0,
                        "Median Balance": 0.0,
                        "10th Percentile": 0.0,
                        "90th Percentile": 0.0,
                    })

            except (ValueError, TypeError) as e:
                typer.echo(typer.style(f"Error running strategy {strat.value}: {e}", fg=typer.colors.RED), err=True)

        if results:
            _print_comparison_results(results)


if __name__ == "__main__":
    app()
