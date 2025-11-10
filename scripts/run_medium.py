"""
Run medium swing strategy using shared base runner.
"""

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.strategies.medium_swing import MediumSwingRunner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run medium swing strategy")
    parser.add_argument(
        "--budget",
        type=float,
        help="Override budget allocation (USD) instead of risk manager value",
    )
    return parser.parse_args()


async def main(args: argparse.Namespace) -> None:
    runner = MediumSwingRunner()
    result = await runner.run(budget_override=args.budget)

    print("\n=== Medium Swing Strategy Summary ===")
    print(f"Status:        {result.status or 'completed'}")
    print(f"Trades Created: {result.trades_created}")
    print(f"Budget Used:    ${result.budget_used:.2f}")
    print(f"Est. Profit:    ${result.estimated_profit:.2f}")
    if args.budget is not None:
        print(f"Budget Override: ${args.budget:.2f}")
    print("====================================\n")


if __name__ == "__main__":
    cli_args = parse_args()
    asyncio.run(main(cli_args))
