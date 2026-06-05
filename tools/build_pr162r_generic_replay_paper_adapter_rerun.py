#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr162r_generic_replay_paper_adapter_rerun.report_builder import (  # noqa: E402
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    summary = artifacts.summary
    print("PR162R_GENERIC_REPLAY_PAPER_ADAPTER_RERUN_BUILT")
    for field in (
        "candidate_packet_v1_ingested_count",
        "pr162d_r2a_candidate_packet_ingested_count",
        "qku_computability_classification_rows_count",
        "formula_callable_smoke_checked_count",
        "algorithm_callable_smoke_checked_count",
        "quantum_shape_builder_smoke_checked_count",
        "classical_comparator_smoke_checked_count",
        "replay_adapter_input_packet_count",
        "paper_adapter_input_packet_count",
        "paired_replay_paper_run_request_candidate_count",
        "missing_data_binding_action_count",
        "quantum_batch_precompute_rows_count",
        "recommendation_next_step",
    ):
        print(f"{field}={summary[field]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
