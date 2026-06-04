#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr162r_a_replay_paper_executability_classification_audit.report_builder import (  # noqa: E402
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    summary = artifacts.summary
    print("PR162R_A_REPLAY_PAPER_EXECUTABILITY_CLASSIFICATION_AUDIT")
    for field in (
        "candidate_source_count",
        "candidates_classified_count",
        "executable_replay_and_paper_ready_count",
        "partial_executable_replay_and_paper_ready_count",
        "targeted_micro_materialization_count",
        "targeted_pr162d_r2_critical_gap_backlog_count",
        "recommendation_next_step",
    ):
        print(f"{field}={summary[field]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
