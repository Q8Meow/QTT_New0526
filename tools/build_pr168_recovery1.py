#!/usr/bin/env python3
"""Build PR168-RECOVERY1 RANK3-guided repair/retest artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_recovery1_config import REPORT_ALIASES
from tools.pr168_recovery1_dag_orchestrator import build_all


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--verify-online-docs",
        action="store_true",
        help="Materialize committed RANK3/RP3 public source-use rows into Recovery1 source-to-retest coverage.",
    )
    mode.add_argument(
        "--offline",
        action="store_true",
        help="Build from committed artifacts only. This is the CI-safe default.",
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
                "reports_written": len(REPORT_ALIASES),
                "work_item_count": summary["work_item_count"],
                "retest_before_after_count": summary["retest_before_after_count"],
                "online_verify_source_count": summary["online_verify_source_count"],
                "authority_counts_zero": summary["real_positive_count"] == summary["order_authority_created_count"] == summary["quantum_backend_execution_count"] == 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
