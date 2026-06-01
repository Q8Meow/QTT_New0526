#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.safe_repo_local_nonlive_dataset_materialization_authority_gate.report_builder import (
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--materialize-public-candidates",
        action="store_true",
        help="Record the explicit materialization intent; CI/default remains offline.",
    )
    args = parser.parse_args()
    artifacts = write_artifacts(
        Path(args.repo_root).resolve(),
        materialize_public_candidates=args.materialize_public_candidates,
    )
    summary = artifacts.summary
    print("PR162A_SAFE_REPO_LOCAL_NONLIVE_DATASET_MATERIALIZATION_AUTHORITY_GATE")
    print(f"run_capable_dataset_count={summary['run_capable_dataset_count']}")
    print(f"qkus_mapped_to_run_capable_datasets={summary['qkus_mapped_to_run_capable_datasets']}")
    print(f"pr162_adapter_rerun_ready_count={summary['pr162_adapter_rerun_ready_count']}")
    print(f"pr163_readiness_state={summary['pr163_readiness_state']}")
    print(f"ci_default_mode_requires_network={summary['ci_default_mode_requires_network']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
