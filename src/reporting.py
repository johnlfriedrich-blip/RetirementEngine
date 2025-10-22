import pandas as pd
import typer
from src.monte_carlo import MonteCarloResults


def _print_mc_results(mc_results: MonteCarloResults, simulation_years: int):
    """Format and print Monte Carlo simulation results."""
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
        if "End Balance" in mc_results.results_df.columns:
            final_balances = mc_results.results_df["End Balance"]
        elif "Balance" in mc_results.results_df.columns:
            final_balances = mc_results.results_df["Balance"]
        else:
            typer.echo(
                "No balance data available in results.",
            )
            return

    # Calculate percentiles
    p10, p50, p90 = final_balances.quantile([0.10, 0.50, 0.90])

    typer.echo("\n" + "-" * 30)
    typer.echo("  Portfolio Balance Percentiles:")
    typer.echo(f"  - 10th (Worst Case): ${p10:,.2f}")
    typer.echo(f"  - 50th (Median):     ${p50:,.2f}")
    typer.echo(f"  - 90th (Best Case):  ${p90:,.2f}")
    typer.echo("-" * 30)


def _print_comparison_results(results: list):
    """Format and print strategy comparison results."""
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


def _print_formatted_results(results_df, withdrawals):
    """Format and print results for deterministic (single-path) simulations."""
    typer.echo("\n" + "=" * 50)
    typer.echo(" " * 15 + "SIMULATION RESULTS")
    typer.echo("=" * 50)

    if results_df.empty:
        typer.echo("No results to display.")
        return

    # Handle both possible column names
    if "End Balance" in results_df.columns:
        final_balance = results_df["End Balance"].iloc[-1]
    elif "Balance" in results_df.columns:
        final_balance = results_df["Balance"].iloc[-1]
    else:
        raise KeyError("No balance column found in results_df")

    typer.echo(f"\nFinal Portfolio Balance: ${final_balance:,.2f}")

    if "Withdrawal" in withdrawals:
        typer.echo("\nWithdrawals:")
        for year, amount in enumerate(withdrawals["Withdrawal"], start=1):
            typer.echo(f" Year {year}: ${amount:,.2f}")

    typer.echo("=" * 50)
    typer.echo("End of Simulation Results")
