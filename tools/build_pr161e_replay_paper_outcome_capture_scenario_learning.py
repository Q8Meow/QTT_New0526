#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.replay_paper_outcome_capture_scenario_learning.report_builder import (
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--online-search-unavailable",
        action="store_true",
        help="Emit the non-blocking unavailable online-search lane for tests.",
    )
    args = parser.parse_args()
    artifacts = write_artifacts(
        Path(args.repo_root).resolve(),
        online_search_available=not args.online_search_unavailable,
    )
    summary = artifacts.summary
    print("PR161E_REPLAY_PAPER_OUTCOME_CAPTURE_SCENARIO_LEARNING")
    print(f"outcome_capture_registry_count={summary['outcome_capture_registry_count']}")
    print(f"bundle_result_ledger_count={summary['bundle_result_ledger_count']}")
    print(f"agent_outcome_task_queue_count={summary['agent_outcome_task_queue_count']}")
    print(f"online_metric_candidate_intake_count={summary['online_metric_candidate_intake_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
