from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.source_evidence.execution_lifecycle.validator import write_generated_reports


SUCCESS_MARKER = "QTT_PER_VENUE_EXECUTION_LIFECYCLE_MODEL_BUILDER_OK"
FAILURE_MARKER = "QTT_PER_VENUE_EXECUTION_LIFECYCLE_MODEL_BUILDER_FAILED"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ok, failures, _artifacts = write_generated_reports(args.repo_root)
    if not ok:
        for failure in failures:
            print(f"{FAILURE_MARKER}: {failure}", file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
