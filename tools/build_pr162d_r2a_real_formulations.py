#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.report_builder import (  # noqa: E402
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    summary = artifacts.summary
    print("PR162D_R2A_REAL_FORMULATIONS_BUILT")
    for field in (
        "real_formula_function_count",
        "real_algorithm_callable_count",
        "real_quantum_shape_builder_count",
        "real_classical_comparator_count",
        "test_vector_count",
        "candidate_packet_v1_count",
        "formulation_backed_qku_count",
        "formulation_unmapped_qku_count",
        "exact_field_fill_actions_created_count",
        "replay_paper_route_ready_count",
    ):
        print(f"{field}={summary[field]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
