#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import validate_source_evidence_retrieval_executor as validator


SUCCESS_MARKER = "QTT_SOURCE_EVIDENCE_RETRIEVAL_EXECUTOR_MANIFEST_ONLY_OK"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--mode",
        choices=("manifest-only", "fixture-only"),
        default="manifest-only",
    )
    parser.add_argument(
        "--enable-external-fetch",
        action="store_true",
        help="Always disabled in PR122; retained as a future controller gate placeholder.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.enable_external_fetch:
        raise SystemExit(
            "SOURCE_RETRIEVAL_EXTERNAL_FETCH_BLOCKED_BY_PR122_CONTROLLER_GATE"
        )

    repo_root = Path(args.repo_root).resolve()
    failures = validator.validate_static_surface(repo_root)
    if failures:
        raise SystemExit(
            "SOURCE_EVIDENCE_RETRIEVAL_EXECUTOR_MANIFEST_ONLY_FAILED\n- "
            + "\n- ".join(failures)
        )
    validator.write_reports(repo_root)
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
