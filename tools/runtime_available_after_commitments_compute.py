#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.capital_risk.field_map import (
    build_runtime_cash_artifacts,
)
from src.qtt.stage1_prediction_markets.capital_risk.validator import (
    AVAILABLE_REPORT_PATH,
)


SUCCESS_MARKER = "QTT_RUNTIME_AVAILABLE_AFTER_COMMITMENTS_FIXTURE_COMPUTE_OK"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--out", type=Path, default=AVAILABLE_REPORT_PATH)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    artifacts = build_runtime_cash_artifacts(args.repo_root)
    output = args.repo_root / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(artifacts["available_report"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
