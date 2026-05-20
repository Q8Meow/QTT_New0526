#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.private_state_receipts.validator import (
    write_fixture_files,
    write_generated_reports,
)


SUCCESS_MARKER = "QTT_PRIVATE_STATE_READ_RECEIPT_FIXTURE_BUILD_OK"
FAILURE_MARKER = "QTT_PRIVATE_STATE_READ_RECEIPT_FIXTURE_BUILD_FAILED"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        write_fixture_files(args.repo_root)
        write_generated_reports(args.repo_root)
    except Exception as exc:
        print(f"{FAILURE_MARKER}: {exc}", file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
