#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr162r_b_replay_paper_data_binding_completion.report_builder import (  # noqa: E402
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    summary = artifacts.summary
    print("PR162R_B_REPLAY_PAPER_DATA_BINDING_COMPLETION_BUILT")
    for field in (
        "raw_missing_actions_consumed",
        "candidate_packet_universe_count",
        "collapsed_binding_family_count",
        "unique_binding_tasks_count",
        "deduplication_ratio",
        "dataset_binding_packets_created",
        "replay_dataset_binding_packets_created",
        "paper_dataset_binding_packets_created",
        "row_binding_resolution_matrix_rows",
        "rows_with_any_binding_improvement",
        "missing_action_reduction_count",
        "paper_binding_fixture_rows",
        "quantum_binding_improvement_rows",
        "recommendation_next_step",
    ):
        print(f"{field}={summary[field]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
