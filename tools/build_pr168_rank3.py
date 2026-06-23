#!/usr/bin/env python3
"""Build PR168-RANK3 RP3 evidence-backed stack ranking artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rank3_config import REPORT_ALIASES
from tools.pr168_rank3_dag_orchestrator import build_all


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--verify-online-docs",
        action="store_true",
        help="Consume committed RP3 public source-use rows into RANK3 source coverage rows.",
    )
    mode.add_argument(
        "--offline",
        action="store_true",
        help="Build from committed RP3/MAP3/upstream artifacts only.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    summary = build_all(verify_online_docs=bool(args.verify_online_docs))
    print(
        json.dumps(
            {
                "built": True,
                "mode": "verify-online-docs" if args.verify_online_docs else "offline",
                "rankable_stack_count": summary["rankable_stack_count"],
                "no_trade_competitor_count": summary["no_trade_competitor_count"],
                "expression_repair_attempt_count": summary["expression_repair_attempt_count"],
                "source_provenance_attempt_count": summary["source_provenance_attempt_count"],
                "reports_written": len(REPORT_ALIASES),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
