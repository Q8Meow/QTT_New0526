#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.source_evidence.connector_semantic_consumer.ledger import (  # noqa: E402
    write_json_object,
)
from src.qtt.source_evidence.revalidation.validator import (  # noqa: E402
    FAILURE_MARKER,
    PR125_REPORT_PATH,
    SCHEDULER_REPORT_PATH,
    SOURCE_CHANGE_SNAPSHOT_REPORT_PATH,
    SUCCESS_MARKER,
    build_report_artifacts,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default=str(PR125_REPORT_PATH))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = Path(args.repo_root)
    pr125_report, scheduler_report, snapshot_report, failures = build_report_artifacts(repo_root)
    write_json_object(repo_root / Path(args.out), pr125_report)
    write_json_object(repo_root / SCHEDULER_REPORT_PATH, scheduler_report)
    write_json_object(repo_root / SOURCE_CHANGE_SNAPSHOT_REPORT_PATH, snapshot_report)
    if failures:
        print(FAILURE_MARKER)
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
