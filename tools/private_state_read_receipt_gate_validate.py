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
    build_private_state_read_receipt_artifacts,
    validate_artifacts,
    write_fixture_files,
    write_generated_reports,
)


SUCCESS_MARKER = "QTT_ACCOUNT_WALLET_BALANCE_AND_PRIVATE_STATE_READ_RECEIPT_GATE_OK"
FAILURE_MARKER = "QTT_ACCOUNT_WALLET_BALANCE_AND_PRIVATE_STATE_READ_RECEIPT_GATE_FAILED"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.check_only:
            artifacts = build_private_state_read_receipt_artifacts(args.repo_root)
        else:
            artifacts = write_fixture_files(args.repo_root)
            write_generated_reports(args.repo_root)
        failures = validate_artifacts(artifacts)
    except Exception as exc:
        print(f"{FAILURE_MARKER}: {exc}", file=sys.stderr)
        return 1
    if failures:
        for failure in failures:
            print(f"{FAILURE_MARKER}: {failure}", file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
