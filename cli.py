# cli.py
import argparse
from retirement_engine.simulator import run_simulation


def main():
    parser = argparse.ArgumentParser(description="Run retirement simulation from CLI")
    parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        choices=["Fixed", "Dynamic", "Guardrails", "Pause After Loss"],
        help="Withdrawal strategy to use",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=0.04,
        help="Initial withdrawal rate (default: 0.04)",
    )
    parser.add_argument(
        "--source", type=str, default="data/market.csv", help="Path to market data CSV"
    )
    parser.add_argument(
        "--initial",
        type=float,
        default=1_000_000,
        help="Initial portfolio balance (default: $1M)",
    )
    parser.add_argument(
        "--weight",
        type=float,
        default=0.6,
        help="SP500 weight in blended returns (default: 0.6)",
    )

    args = parser.parse_args()

    balances, withdrawals = run_simulation(
        withdrawal_rate=args.rate,
        etf_source=args.source,
        strategy=args.strategy,
        initial_balance=args.initial,
        sp500_weight=args.weight,
    )

    print(f"\n[RESULT] Final Balance: ${balances[-1]:,.2f}")
    print(f"[RESULT] Total Withdrawn: ${sum(withdrawals):,.2f}")
    print(f"[RESULT] Years Simulated: {len(withdrawals)}")


if __name__ == "__main__":
    main()
