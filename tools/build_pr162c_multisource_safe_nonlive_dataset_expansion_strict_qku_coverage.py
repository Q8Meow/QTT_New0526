#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.report_builder import (
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    summary = artifacts.summary
    print("PR162C_MULTISOURCE_SAFE_NONLIVE_DATASET_EXECUTABLE_QKU_STRICT_COVERAGE")
    print(f"data_requirement_total={summary['data_requirement_total']}")
    print(f"unclassified_requirement_count={summary['unclassified_requirement_count']}")
    print(f"strict_run_capable_qku_count={summary['strict_run_capable_qku_count']}")
    print(f"strict_both_lane_qku_count={summary['strict_both_lane_qku_count']}")
    print(f"strict_quantum_feature_qku_count={summary['strict_quantum_feature_qku_count']}")
    print(f"owner_materialization_command_count={summary['owner_materialization_command_count']}")
    print(f"pr162r_readiness_status={summary['pr162r_readiness_status']}")
    print(f"pr163_blocker_status={summary['pr163_blocker_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
