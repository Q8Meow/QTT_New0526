#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.replay_paper_executor_input_run_artifact_generation.report_builder import (
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
    print("PR161F_REPLAY_PAPER_EXECUTOR_INPUT_RUN_ARTIFACT_GENERATION")
    print(f"executor_input_records_count={summary['executor_input_records_count']}")
    print(f"replay_run_request_count={summary['replay_run_request_count']}")
    print(f"paper_run_request_count={summary['paper_run_request_count']}")
    print(f"run_artifact_envelope_count={summary['run_artifact_envelope_count']}")
    print(f"agent_run_task_logical_count={summary['agent_run_task_logical_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

