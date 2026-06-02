#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.report_builder import (
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    summary = artifacts.summary
    print("PR162B_QKU_FORMULA_ALGORITHM_SOLVER_MARKET_SCOPE_MATERIALIZATION")
    print(f"total_qku_count={summary['total_qku_count']}")
    print(f"classified_qku_count={summary['classified_qku_count']}")
    print(f"unclassified_qku_count={summary['unclassified_qku_count']}")
    print(f"formula_records_materialized={summary['formula_records_materialized']}")
    print(f"algorithm_records_materialized={summary['algorithm_records_materialized']}")
    print(f"solver_mapping_records_materialized={summary['solver_mapping_records_materialized']}")
    print(f"pr162r_readiness_state={summary['pr162r_readiness_state']}")
    print(f"pr163_readiness_state={summary['pr163_readiness_state']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
