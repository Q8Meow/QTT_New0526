#!/usr/bin/env python3
"""Build PR168-RP3 MAP3 replay/paper evidence artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp3_dag_orchestrator import build_all
from tools.pr168_rp3_config import REPORT_ALIASES


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--verify-online-docs",
        action="store_true",
        help="Materialize RP3 online coverage rows from committed MAP3 source evidence rows.",
    )
    mode.add_argument(
        "--offline",
        action="store_true",
        help="Rebuild from committed upstream artifacts only.",
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
                "formula_count": summary["map3_formula_universe_count"],
                "computed_formula_count": summary["map3_replay_paper_computable_formula_count"],
                "rank2_rows": summary["rank2_evidence_handoff_count"],
                "reports_written": len(REPORT_ALIASES),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
