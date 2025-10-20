# cli.py
import os
import pandas as pd
import math
import typer
from enum import Enum
from .simulator import RetirementSimulator
from .withdrawal_strategies import strategy_factory
from . import data_loader, config
from .monte_carlo import MonteCarloSimulator, MonteCarloResults
from .synthetic_data import Distribution, from_synthetic_data
from .resolve_path import resolve_path

# --- Path setup for robust data file access ---
_DEFAULT_DATA_PATH = resolve_path("src/data/market.csv")

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


class DataSource(str, Enum):
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


def _print_mc_results(mc_results: MonteCarloResults, simulation_years: int):
    """Helper function to format and print Monte Carlo simulation results."""
    typer.echo("\n" + "=" * 50)
    typer.echo(" " * 15 + "MONTE CARLO RESULTS")
    typer.echo("=" * 50)

    success_rate = mc_results.success_rate()
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
        f"{summary_style} Ran {mc_results.num_simulations} simulations over {simulation_years} years."
    )

    if not mc_results.results_df.empty:
        final_balances = mc_results.results_df["End Balance"]
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


# --- Simulation Runner Helper ---
def _run_and_print_simulation(
    strategy_name: str,
    strategy_args: dict,
    data_source: str,
    data_args: dict,
):
    """A unified helper to create, run, and print a simulation."""
    try:
        typer.echo(f"Running simulation with '{strategy_name}' strategy...")
        strategy_obj = strategy_factory(strategy_name, **strategy_args)

        if data_source == "synthetic":
            returns = data_loader.from_synthetic_data(**data_args)
        else:
            source_path = resolve_path(data_args["etf_source"])
            if not os.path.exists(source_path):
                typer.echo(
                    typer.style(
                        f"Error: Data source not found at '{source_path}'.",
                        fg=typer.colors.RED,
                    ),
                    err=True,
                )
                raise typer.Exit(code=1)
            data_args["etf_source"] = source_path
            returns = data_loader.from_csv(**data_args)

        returns_df = pd.DataFrame(
            returns, columns=["us_equities", "bonds", "inflation_returns"]
        )

        sim = RetirementSimulator(
            returns=returns_df,
            initial_balance=strategy_args["initial_balance"],
            portfolio_weights=strategy_args["portfolio_weights"],
            strategy=strategy_obj,
        )
        results_df, withdrawals = sim.run()
        _print_formatted_results(results_df, withdrawals)
    except (ValueError, TypeError) as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)


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
        "0.6,0.4", help="Portfolio weights for stocks and bonds (e.g., '0.6,0.4')."
    ),
    rate: float = typer.Option(
        0.04,
        help="Withdrawal rate for 'fixed', 'dynamic', and 'pause_after_loss' strategies.",
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
    sp500_mean: float = typer.Option(0.10, help="Mean annual return for stocks."),
    sp500_std_dev: float = typer.Option(
        0.18, help="Standard deviation of annual stock returns."
    ),
    bonds_mean: float = typer.Option(0.03, help="Mean annual return for bonds."),
    bonds_std_dev: float = typer.Option(
        0.06, help="Standard deviation of annual bond returns."
    ),
    bootstrap_block_size: int = typer.Option(
        252, help="Block size for historical bootstrapping (in days)."
    ),
    num_simulations: int = typer.Option(
        1000, help="Number of Monte Carlo simulations."
    ),
    simulation_years: int = typer.Option(
        30, help="Duration of each simulation in years."
    ),
    distribution: Distribution = typer.Option(
        Distribution.NORMAL, help="Distribution to use for synthetic data generation."
    ),
    df: int = typer.Option(
        3, help="Degrees of freedom for Student-t distribution (if selected)."
    ),
    parallel: bool = typer.Option(
        True, help="Enable or disable parallel processing.", show_default=True
    ),
):
    """Run a Monte Carlo simulation for a chosen withdrawal strategy."""
    typer.echo(f"Running Monte Carlo simulation with '{strategy.value}' strategy...")

    weights = [float(w.strip()) for w in portfolio_weights.split(",")]
    strategy_obj = strategy_factory(
        strategy.value,
        initial_balance=initial_balance,
        portfolio_weights={"us_equities": weights[0], "bonds": weights[1]},
        rate=rate,
        min_pct=min_pct,
        max_pct=max_pct,
        start_age=start_age,
    )

    historical_params = {
        "inflation_mean": inflation_mean,
        "inflation_std_dev": inflation_std_dev,
        "bootstrap_block_size": bootstrap_block_size,
    }
    synthetic_params = {
        "portfolio_asset_params": {
            "us_equities": {"cagr": sp500_mean, "std_dev": sp500_std_dev},
            "bonds": {"cagr": bonds_mean, "std_dev": bonds_std_dev},
        },
        "inflation_mean": inflation_mean,
        "inflation_std_dev": inflation_std_dev,
        "distribution": distribution,
        "df": df,
    }

    if data_source == DataSource.SYNTHETIC:
        synthetic_params["num_years"] = simulation_years
        market_data = from_synthetic_data(**synthetic_params)
    else:
        historical_params["num_years"] = simulation_years
        historical_params["data_dir"] = "src/data/raw"
        market_data = data_loader.from_historical_data(**historical_params)

    try:
        mc_sim = MonteCarloSimulator(
            market_data=market_data,
            withdrawal_strategy=strategy_obj,
            start_balance=initial_balance,
            simulation_years=simulation_years,
            portfolio_weights={
                "us_equities": weights[0],
                "bonds": weights[1],
            },
            data_source=data_source.value,
            synthetic_params=synthetic_params,
            num_simulations=num_simulations,
            parallel=parallel,
        )
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
    stock_allocation: float = typer.Option(
        0.6, help="Stock allocation (e.g., 0.6 for 60%)."
    ),
    rate: float = typer.Option(0.04, help="Withdrawal rate for applicable strategies."),
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
    sp500_mean: float = typer.Option(0.10, help="Mean annual return for stocks."),
    sp500_std_dev: float = typer.Option(
        0.18, help="Standard deviation of annual stock returns."
    ),
    bond_mean_return: float = typer.Option(0.03, help="Mean annual return for bonds."),
    bond_std_dev: float = typer.Option(
        0.06, help="Standard deviation of annual bond returns."
    ),
    bootstrap_block_size: int = typer.Option(
        252, help="Block size for historical bootstrapping (in days)."
    ),
    num_simulations: int = typer.Option(
        1000, help="Number of Monte Carlo simulations."
    ),
    simulation_years: int = typer.Option(
        30, help="Duration of each simulation in years."
    ),
    distribution: Distribution = typer.Option(
        Distribution.NORMAL, help="Distribution to use for synthetic data generation."
    ),
    df: int = typer.Option(
        3, help="Degrees of freedom for Student-t distribution (if selected)."
    ),
    parallel: bool = typer.Option(
        True, help="Enable or disable parallel processing.", show_default=True
    ),
    data_source: DataSource = typer.Option(
        DataSource.SYNTHETIC,
        help="Data source for the simulation.",
        case_sensitive=False,
    ),
):
    """Compare all withdrawal strategies using the same Monte Carlo simulation inputs."""
    typer.echo("Comparing all withdrawal strategies...")

    results = []
    for strategy_enum in Strategy:
        typer.echo(f"\nRunning simulation for '{strategy_enum.value}'...")
        weights = [stock_allocation, 1.0 - stock_allocation]
        strategy_obj = strategy_factory(
            strategy_enum.value,
            initial_balance=initial_balance,
            portfolio_weights={
                "us_equities": weights[0],
                "bonds": weights[1],
            },
            stock_allocation=stock_allocation,
            rate=rate,
            min_pct=min_pct,
            max_pct=max_pct,
            start_age=start_age,
        )

        historical_params = {
            "inflation_mean": inflation_mean,
            "inflation_std_dev": inflation_std_dev,
        }
        synthetic_params = {
            "portfolio_asset_params": {
                "us_equities": {"cagr": sp500_mean, "std_dev": sp500_std_dev},
                "bonds": {"cagr": bond_mean_return, "std_dev": bond_std_dev},
            },
            "inflation_mean": inflation_mean,
            "inflation_std_dev": inflation_std_dev,
            "distribution": distribution,
            "df": df,
        }

        if data_source == DataSource.SYNTHETIC:
            market_data = from_synthetic_data(**synthetic_params)
        else:
            historical_params["data_dir"] = "src/data/raw"
            market_data = data_loader.from_historical_data(**historical_params)

        try:
            mc_sim = MonteCarloSimulator(
                market_data=market_data,
                withdrawal_strategy=strategy_obj,
                start_balance=initial_balance,
                simulation_years=simulation_years,
                portfolio_weights={
                    "us_equities": weights[0],
                    "bonds": weights[1],
                },
                num_simulations=num_simulations,
                parallel=parallel,
                data_source=data_source.value,
                synthetic_params=synthetic_params,
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
