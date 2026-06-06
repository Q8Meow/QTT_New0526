#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr163_b_paired_replay_paper_concurrent_executor.report_builder import (  # noqa: E402
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    summary = artifacts.summary
    print("PR163_B_PAIRED_REPLAY_PAPER_CONCURRENT_EXECUTOR_BUILT")
    for field in (
        "candidate_packet_universe_count",
        "paired_run_input_rows",
        "paired_clock_rows",
        "input_lock_rows",
        "leakage_guard_rows",
        "replay_trace_rows",
        "paper_trace_rows",
        "paired_comparison_complete_rows",
        "rejection_remediation_rows",
        "transaction_cost_analysis_rows",
        "scenario_stress_rows",
        "quantum_carry_forward_rows",
        "llm_future_review_handoff_rows",
        "recommendation_next_step",
    ):
        print(f"{field}={summary[field]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
