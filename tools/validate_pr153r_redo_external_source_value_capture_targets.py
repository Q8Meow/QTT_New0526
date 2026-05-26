#!/usr/bin/env python3
"""Validate PR153R redo external source-value capture targets."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr153r_redo_external_source_value_capture_targets import (
    constants as c,
)
from src.qtt.stage1_prediction_markets.pr153r_redo_external_source_value_capture_targets.validator import (
    validate_repository_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    failures = validate_repository_artifacts(repo_root)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(c.SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
