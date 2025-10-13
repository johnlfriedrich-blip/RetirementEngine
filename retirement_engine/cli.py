# cli.py
import pathlib
import pandas as pd
import math
import typer
from typing_extensions import Annotated
from retirement_engine.simulator import RetirementSimulator, run_simulation
from retirement_engine.withdrawal_strategies import strategy_factory

# --- Path setup for robust data file access ---
# Get the directory containing this cli.py file
_CLI_DIR = pathlib.Path(__file__).parent.resolve()
# Construct the path to the project's root directory (one level up)
_PROJECT_ROOT = _CLI_DIR.parent
_DEFAULT_DATA_PATH = _PROJECT_ROOT / "data" / "market.csv"

app = typer.Typer(
    help="A command-line interface for the Retirement Engine.",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """A CLI for running retirement simulations."""
    if ctx.invoked_subcommand is None:
        typer.echo(
            "No command specified. Use 'run' to start a simulation. See --help for details."
        )


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

    # --- Print Yearly Data ---
    typer.echo("\n" + "=" * 50)
    typer.echo(" " * 18 + "YEARLY RESULTS")
    typer.echo("=" * 50)
    with pd.option_context(
        "display.max_rows", None, "display.float_format", "${:,.2f}".format
    ):
        typer.echo(results_df.to_string(index=False))
    typer.echo("=" * 50)

    # --- Print Summary ---
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


def _run_and_print_simulation(
    strategy_name: str, strategy_args: dict, sim_args: dict, use_synthetic: bool
):
    """
    A unified helper to create, run, and print a simulation.

    Args:
        strategy_name: The name of the withdrawal strategy.
        strategy_args: Arguments for creating the strategy object.
        sim_args: Arguments for creating the RetirementSimulator.
        use_synthetic: If True, use synthetic data; otherwise, use CSV data.
    """
    try:
        strategy_obj = strategy_factory(strategy_name, **strategy_args)
        sim_args["strategy"] = strategy_obj

        if use_synthetic:
            sim = RetirementSimulator.from_synthetic_data(**sim_args)
        else:
            source_path = pathlib.Path(sim_args["etf_source"])
            if not source_path.is_file():
                typer.echo(
                    typer.style(
                        f"Error: Data source not found at '{source_path}'.",
                        fg=typer.colors.RED,
                    ),
                    err=True,
                )
                raise typer.Exit(code=1)
            sim = RetirementSimulator.from_csv(**sim_args)

        results_df, withdrawals = sim.run()
        _print_formatted_results(results_df, withdrawals)
    except (ValueError, TypeError) as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)


@app.command()
def run(  # noqa: PLR0913
    strategy: Annotated[
        str,
        typer.Option(
            help="Withdrawal strategy to use. One of: fixed, dynamic, guardrails, pause_after_loss"
        ),
    ],
    initial_balance: Annotated[
        float, typer.Option(help="Initial portfolio balance.")
    ] = 1_000_000,
    stock_allocation: Annotated[
        float, typer.Option(help="Stock allocation (e.g., 0.6 for 60%).")
    ] = 0.6,
    rate: Annotated[
        float,
        typer.Option(
            help="Withdrawal rate for 'fixed', 'dynamic', and 'pause_after_loss' strategies."
        ),
    ] = 0.04,
    min_pct: Annotated[
        float,
        typer.Option(help="Minimum withdrawal percent for 'guardrails' strategy."),
    ] = 0.03,
    max_pct: Annotated[
        float,
        typer.Option(help="Maximum withdrawal percent for 'guardrails' strategy."),
    ] = 0.06,
    inflation_mean: Annotated[
        float, typer.Option(help="Mean annual inflation rate.")
    ] = 0.03,
    inflation_std_dev: Annotated[
        float, typer.Option(help="Standard deviation of annual inflation.")
    ] = 0.015,
    source: Annotated[str, typer.Option(help="Path to market data CSV.")] = str(
        _DEFAULT_DATA_PATH
    ),
):  # ruff: noqa: PLR0913
    """
    Run a retirement simulation with a chosen withdrawal strategy.
    """
    typer.echo(f"Running simulation with '{strategy}' strategy...")

    strategy_args = {
        "initial_balance": initial_balance,
        "sp500_weight": stock_allocation,
        "rate": rate,
        "min_pct": min_pct,
        "max_pct": max_pct,
    }
    sim_args = {
        "etf_source": source,
        "initial_balance": initial_balance,
        "stock_allocation": stock_allocation,
        "inflation_mean": inflation_mean,
        "inflation_std_dev": inflation_std_dev,
    }

    _run_and_print_simulation(
        strategy_name=strategy,
        strategy_args=strategy_args,
        sim_args=sim_args,
        use_synthetic=False,
    )


@app.command()
def run_synthetic(  # noqa: PLR0913
    strategy: Annotated[
        str,
        typer.Option(
            help="Withdrawal strategy to use. One of: fixed, dynamic, guardrails, pause_after_loss"
        ),
    ],
    num_years: Annotated[int, typer.Option(help="Number of years to simulate.")] = 30,
    initial_balance: Annotated[
        float, typer.Option(help="Initial portfolio balance.")
    ] = 1_000_000,
    stock_allocation: Annotated[
        float, typer.Option(help="Stock allocation (e.g., 0.6 for 60%).")
    ] = 0.6,
    rate: Annotated[
        float,
        typer.Option(
            help="Withdrawal rate for 'fixed', 'dynamic', and 'pause_after_loss' strategies."
        ),
    ] = 0.04,
    min_pct: Annotated[
        float,
        typer.Option(help="Minimum withdrawal percent for 'guardrails' strategy."),
    ] = 0.03,
    max_pct: Annotated[
        float,
        typer.Option(help="Maximum withdrawal percent for 'guardrails' strategy."),
    ] = 0.06,
    sp500_mean: Annotated[
        float, typer.Option(help="Mean annual return for stocks.")
    ] = 0.10,
    sp500_std_dev: Annotated[
        float, typer.Option(help="Standard deviation of annual stock returns.")
    ] = 0.18,
    bonds_mean: Annotated[
        float, typer.Option(help="Mean annual return for bonds.")
    ] = 0.03,
    bonds_std_dev: Annotated[
        float, typer.Option(help="Standard deviation of annual bond returns.")
    ] = 0.06,
    inflation_mean: Annotated[
        float, typer.Option(help="Mean annual inflation rate.")
    ] = 0.03,
    inflation_std_dev: Annotated[
        float, typer.Option(help="Standard deviation of annual inflation.")
    ] = 0.015,
):
    """
    Run a retirement simulation using synthetically generated market data.
    """
    typer.echo(f"Running synthetic simulation with '{strategy}' strategy...")

    strategy_args = {
        "initial_balance": initial_balance,
        "sp500_weight": stock_allocation,
        "rate": rate,
        "min_pct": min_pct,
        "max_pct": max_pct,
    }
    sim_args = {
        "initial_balance": initial_balance,
        "stock_allocation": stock_allocation,
        "num_years": num_years,
        "sp500_mean": sp500_mean,
        "sp500_std_dev": sp500_std_dev,
        "bonds_mean": bonds_mean,
        "bonds_std_dev": bonds_std_dev,
        "inflation_mean": inflation_mean,
        "inflation_std_dev": inflation_std_dev,
    }

    _run_and_print_simulation(
        strategy_name=strategy,
        strategy_args=strategy_args,
        sim_args=sim_args,
        use_synthetic=True,
    )


if __name__ == "__main__":
    app()
