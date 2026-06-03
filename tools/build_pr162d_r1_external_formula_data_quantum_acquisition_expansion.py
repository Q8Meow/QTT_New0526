#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr162d_r1_external_formula_data_quantum_acquisition_expansion.report_builder import (  # noqa: E402
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    summary = artifacts.summary
    print("PR162D_R1_EXTERNAL_FORMULA_DATA_QUANTUM_ACQUISITION_EXPANSION")
    for field in (
        "acquisition_first_effort_ratio",
        "master_plan_formula_mentions_scanned_count",
        "master_plan_algorithm_mentions_scanned_count",
        "master_plan_extracted_formula_candidate_count",
        "external_sources_scouted_count",
        "external_formula_candidates_created",
        "external_algorithm_candidates_created",
        "external_parameter_candidates_created",
        "external_dataset_candidates_created",
        "quantum_formula_candidates_created",
        "qku_mapped_external_candidate_count",
    ):
        print(f"{field}={summary[field]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
