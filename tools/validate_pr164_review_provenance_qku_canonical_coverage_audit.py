#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.validators import validate_artifacts  # noqa: E402


SUCCESS_MARKER = "PR164_REVIEW_PROVENANCE_QKU_CANONICAL_COVERAGE_AUDIT_VALIDATED"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    result = validate_artifacts(Path(args.repo_root).resolve())
    if not result.ok:
        for failure in result.failures:
            print(failure, file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
