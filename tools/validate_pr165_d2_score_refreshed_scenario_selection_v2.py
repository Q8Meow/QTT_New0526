#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2.validator import validate_artifacts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    result = validate_artifacts(Path(args.repo_root).resolve())
    if not result.ok:
        for failure in result.failures:
            print(failure)
        return 1
    print("PR165_D2_SCORE_REFRESHED_SELECTION_VALIDATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
