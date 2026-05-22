#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.atomicrows_bundle_reconciliation.report import (  # noqa: E402
    write_report_files,
)
from src.qtt.stage1_prediction_markets.atomicrows_bundle_reconciliation.validator import (  # noqa: E402
    validate_report_payload,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    report = write_report_files(repo_root)
    outcome = validate_report_payload(
        report,
        repo_root=repo_root,
        enforce_environment=True,
    )
    if not outcome.ok:
        for failure in outcome.failures:
            print(failure)
        return 1
    for receipt in outcome.receipts:
        print(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
