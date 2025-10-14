# cli.py
import pathlib
import pandas as pd
import math
import typer
from typing_extensions import Annotated
from retirement_engine.simulator import RetirementSimulator
from retirement_engine.withdrawal_strategies import strategy_factory
<<<<<<< HEAD
from retirement_engine import data_loader, config, av_loader
=======
from retirement_engine import data_loader, config
from retirement_engine.monte_carlo import MonteCarloSimulator
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)

# --- Path setup for robust data file access ---
# Get the directory containing this cli.py file
_CLI_DIR = pathlib.Path(__file__).parent.resolve()
# Construct the path to the project's root directory (one level up)
_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
_DEFAULT_DATA_PATH = "data/market.csv"

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


def _print_mc_results(mc_sim: MonteCarloSimulator):
    """Helper function to format and print Monte Carlo simulation results."""
    typer.echo("\n" + "=" * 50)
    typer.echo(" " * 15 + "MONTE CARLO RESULTS")
    typer.echo("=" * 50)

    success_rate = mc_sim.success_rate()
    
    # Determine color based on success rate
    if success_rate >= 0.95:
        color = typer.colors.GREEN
    elif success_rate >= 0.85:
        color = typer.colors.YELLOW
    else:
        color = typer.colors.RED

    summary_style = typer.style("[SUMMARY]", bold=True)
    typer.echo(
        typer.style(
            f"\n{summary_style} Strategy Success Rate: {success_rate:.1%}",
            fg=color,
            bold=True,
        )
    )
    typer.echo(f"{summary_style} Ran {mc_sim.num_simulations} simulations over {mc_sim.duration_years} years.")

    # Optional: Add more details like percentile outcomes
    if mc_sim.results is not None:
        final_balances = mc_sim.results.loc[mc_sim.results.groupby("Run")["Year"].idxmax()]["End Balance"]
        p10 = final_balances.quantile(0.10)
        p50 = final_balances.quantile(0.50)
        p90 = final_balances.quantile(0.90)
        
        typer.echo("\n" + "-" * 30)
        typer.echo(f"  Portfolio Balance Percentiles:")
        typer.echo(f"  - 10th (Worst Case): ${p10:,.2f}")
        typer.echo(f"  - 50th (Median):     ${p50:,.2f}")
        typer.echo(f"  - 90th (Best Case):  ${p90:,.2f}")
        typer.echo("-" * 30)


def _run_and_print_simulation(
    strategy_name: str, strategy_args: dict, data_args: dict, use_synthetic: bool
):
    """
    A unified helper to create, run, and print a simulation.

    Args:
        strategy_name: The name of the withdrawal strategy.
        strategy_args: Arguments for creating the strategy object.
        data_args: Arguments for the data loader.
        use_synthetic: If True, use synthetic data; otherwise, use CSV data.
    """
    try:
        if use_synthetic:
            typer.echo(
                f"Running synthetic simulation with '{strategy_name}' strategy..."
            )
        else:
            typer.echo(f"Running simulation with '{strategy_name}' strategy...")

        strategy_obj = strategy_factory(strategy_name, **strategy_args)

        if use_synthetic:
            returns = data_loader.from_synthetic_data(**data_args)
        else:
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

        # For the simple simulators, derive portfolio_weights from stock_allocation
        stock_allocation = strategy_args.get("sp500_weight", 0.6)
        sim_args = {
            "initial_balance": strategy_args["initial_balance"],
<<<<<<< HEAD
            "portfolio_weights": [stock_allocation, 1 - stock_allocation],
=======
            "stock_allocation": strategy_args["stock_allocation"],
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)
            "strategy": strategy_obj,
        }

        sim = RetirementSimulator(returns=returns, **sim_args)
        results_df, withdrawals = sim.run()
        _print_formatted_results(results_df, withdrawals)
    except (ValueError, TypeError) as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)


@app.command()
def run(
    strategy: Annotated[
        str,
        typer.Option(
            ...,  # Ellipsis makes it a required option
            help="Withdrawal strategy to use. One of: fixed, dynamic, guardrails, pause_after_loss, vpw",
        ),
    ],
    initial_balance: Annotated[
        float, typer.Option(help="Initial portfolio balance.")
    ] = config.START_BALANCE,
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
    start_age: Annotated[
        int, typer.Option(help="Starting age for 'vpw' strategy.")
    ] = 65,
    inflation_mean: Annotated[
        float, typer.Option(help="Mean annual inflation rate.")
    ] = 0.03,
    inflation_std_dev: Annotated[
        float, typer.Option(help="Standard deviation of annual inflation.")
    ] = 0.015,
    # This option is specific to the 'run' command, so it remains here.
    source: Annotated[str, typer.Option(help="Path to market data CSV.")] = str(
        _DEFAULT_DATA_PATH
    ),
):
    """
    Run a retirement simulation with a chosen withdrawal strategy.
    """
    strategy_args = {
        "initial_balance": initial_balance,
        "stock_allocation": stock_allocation,
        "rate": rate,
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
        strategy_name=strategy,
        strategy_args=strategy_args,
        data_args=data_args,
        use_synthetic=False,
    )


@app.command()
def run_synthetic(  # noqa: PLR0913
    strategy: Annotated[
        str,
        typer.Option(
            ...,  # Ellipsis makes it a required option
            help="Withdrawal strategy to use. One of: fixed, dynamic, guardrails, pause_after_loss, vpw",
        ),
    ],
    initial_balance: Annotated[
        float, typer.Option(help="Initial portfolio balance.")
    ] = config.START_BALANCE,
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
    start_age: Annotated[
        int, typer.Option(help="Starting age for 'vpw' strategy.")
    ] = 65,
    inflation_mean: Annotated[
        float, typer.Option(help="Mean annual inflation rate.")
    ] = 0.03,
    inflation_std_dev: Annotated[
        float, typer.Option(help="Standard deviation of annual inflation.")
    ] = 0.015,
    # Options specific to the 'run-synthetic' command
    num_years: Annotated[int, typer.Option(help="Number of years to simulate.")] = 30,
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
):
    """
    Run a retirement simulation using synthetically generated market data.
    """
    strategy_args = {
        "initial_balance": initial_balance,
        "stock_allocation": stock_allocation,
        "rate": rate,
        "min_pct": min_pct,
        "max_pct": max_pct,
        "start_age": start_age,
    }
    data_args = {
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
        data_args=data_args,
        use_synthetic=True,
    )


@app.command()
<<<<<<< HEAD
def run_portfolio(  # noqa: PLR0913
    name: Annotated[
        str,
        typer.Option(
            help="Name of the portfolio to use, as defined in config.yaml."
        ),
    ],
    strategy: Annotated[
        str,
        typer.Option(
            help="Withdrawal strategy to use. One of: fixed, dynamic, guardrails, pause_after_loss, vpw"
=======
def run_mc(  # noqa: PLR0913
    strategy: Annotated[
        str,
        typer.Option(
            ...,
            help="Withdrawal strategy to use. One of: fixed, dynamic, guardrails, pause_after_loss, vpw",
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)
        ),
    ],
    initial_balance: Annotated[
        float, typer.Option(help="Initial portfolio balance.")
    ] = config.START_BALANCE,
<<<<<<< HEAD
=======
    stock_allocation: Annotated[
        float, typer.Option(help="Stock allocation (e.g., 0.6 for 60%).")
    ] = 0.6,
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)
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
    start_age: Annotated[
<<<<<<< HEAD
        int,
        typer.Option(help="Starting age for 'vpw' strategy."),
    ] = 65,
):
    """
    Run a retirement simulation using a pre-defined portfolio from config.yaml.
    """
    typer.echo(f"Running portfolio simulation for '{name}' with '{strategy}' strategy...")

    # Look up the portfolio in the config
    portfolio = config.config['portfolios'].get(name)
    if not portfolio:
        typer.echo(
            typer.style(
                f"Error: Portfolio '{name}' not found in config.yaml.",
                fg=typer.colors.RED,
            ),
            err=True,
        )
        raise typer.Exit(code=1)

    # Fetch the data using the av_loader
    returns_df = av_loader.fetch_daily_prices(portfolio["tickers"])
    daily_returns = returns_df.pct_change().dropna()

    # Prepare arguments for the simulation
    strategy_args = {
        "initial_balance": initial_balance,
=======
        int, typer.Option(help="Starting age for 'vpw' strategy.")
    ] = 65,
    # Monte Carlo options
    num_simulations: Annotated[
        int, typer.Option(help="Number of Monte Carlo simulations.")
    ] = 1000,
    duration_years: Annotated[
        int, typer.Option(help="Duration of each simulation in years.")
    ] = 30,
    # Market data options
    stock_mean_return: Annotated[
        float, typer.Option(help="Mean annual return for stocks.")
    ] = 0.09,
    stock_std_dev: Annotated[
        float, typer.Option(help="Standard deviation of annual stock returns.")
    ] = 0.18,
    bond_mean_return: Annotated[
        float, typer.Option(help="Mean annual return for bonds.")
    ] = 0.04,
    bond_std_dev: Annotated[
        float, typer.Option(help="Standard deviation of annual bond returns.")
    ] = 0.05,
    inflation_mean: Annotated[
        float, typer.Option(help="Mean annual inflation rate.")
    ] = 0.03,
    inflation_std_dev: Annotated[
        float, typer.Option(help="Standard deviation of annual inflation.")
    ] = 0.015,
):
    """
    Run a Monte Carlo simulation for a chosen withdrawal strategy.
    """
    typer.echo(f"Running Monte Carlo simulation with '{strategy}' strategy...")

    strategy_args = {
        "initial_balance": initial_balance,
        "stock_allocation": stock_allocation,
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)
        "rate": rate,
        "min_pct": min_pct,
        "max_pct": max_pct,
        "start_age": start_age,
<<<<<<< HEAD
        "sp500_weight": portfolio["weights"][0],  # Pass for legacy strategies
    }
    sim_args = {
        "initial_balance": initial_balance,
        "portfolio_weights": portfolio["weights"],
        "strategy": strategy_factory(strategy, **strategy_args),
    }

    # Run the simulation
    sim = RetirementSimulator(returns=daily_returns, **sim_args)
    results_df, withdrawals = sim.run()
    _print_formatted_results(results_df, withdrawals)
=======
    }

    market_data_args = {
        "stock_mean_return": stock_mean_return,
        "stock_std_dev": stock_std_dev,
        "bond_mean_return": bond_mean_return,
        "bond_std_dev": bond_std_dev,
        "inflation_mean": inflation_mean,
        "inflation_std_dev": inflation_std_dev,
    }

    try:
        mc_sim = MonteCarloSimulator(
            num_simulations=num_simulations,
            duration_years=duration_years,
            market_data_generator_args=market_data_args,
        )
        mc_sim.run(strategy_name=strategy, **strategy_args)
        _print_mc_results(mc_sim)
    except (ValueError, TypeError) as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)
>>>>>>> 4aeb09e (Refactored and added Monte Carlo)


if __name__ == "__main__":
    app()