import os
import pandas as pd
import typer

from src.withdrawal_strategies import strategy_factory
from src import data_loader
from src.synthetic_data import from_synthetic_data
from src.reporting import _print_formatted_results

from src.simulator import RetirementSimulator


def _run_and_print_simulation(
    strategy_name: str,
    strategy_args: dict,
    data_source: str,
    data_args: dict,
):
    """A unified helper to create, run, and print a deterministic simulation."""
    try:
        typer.echo(f"Running simulation with '{strategy_name}' strategy...")
        strategy_obj = strategy_factory(strategy_name, **strategy_args)

        if data_source == "synthetic":
            returns = from_synthetic_data(**data_args)
        else:
            source_path = data_args.get("etf_source")
            if not source_path or not os.path.exists(source_path):
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

        # Import here to avoid circular dependency

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
