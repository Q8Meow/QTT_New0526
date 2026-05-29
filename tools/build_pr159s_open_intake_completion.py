#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake.report_builder import (
    write_artifacts,
)
from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake.validator import (
    validate_existing_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    write_artifacts(repo_root)
    result = validate_existing_artifacts(repo_root)
    for receipt in result.receipts:
        print(receipt)
    if result.failures:
        for failure in result.failures:
            print(failure)
        return 1
    print(c.SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

