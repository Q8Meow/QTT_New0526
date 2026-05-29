#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.master_plan_residual_candidate_coverage.validator import (
    validate_existing_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    result = validate_existing_artifacts(Path(args.repo_root).resolve())
    if not result.ok:
        for failure in result.failures:
            print(failure)
        return 1
    for receipt in result.receipts:
        print(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
