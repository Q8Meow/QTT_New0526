#!/usr/bin/env python3
"""Run the PR168-VS1 trading-intelligence vertical slice."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr168_vs1_trading_intelligence.models import RunConfig
from src.qtt.stage1_prediction_markets.pr168_vs1_trading_intelligence.runner import run_slice


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        default="all",
        choices=(
            "all",
            "positive_edge_fixture",
            "negative_edge_fixture",
            "thin_book_fixture",
            "crowded_capacity_fixture",
            "portfolio_conflict_fixture",
        ),
    )
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--max-identities", type=int, default=50)
    parser.add_argument("--max-stacks-per-fixture", type=int, default=20)
    parser.add_argument("--dump-temp", action="store_true")
    args = parser.parse_args(argv)

    result = run_slice(
        RunConfig(
            fixture=args.fixture,
            top_k=args.top_k,
            max_identities=args.max_identities,
            max_stacks_per_fixture=args.max_stacks_per_fixture,
            dump_temp=args.dump_temp,
        )
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
