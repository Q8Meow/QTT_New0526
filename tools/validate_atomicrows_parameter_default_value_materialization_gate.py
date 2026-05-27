#!/usr/bin/env python3
"""Validate PR154 AtomicRows parameter-default value materialization gate."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence


_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.atomicrows_parameter_default_value_materialization_gate import (  # noqa: E402
    report as report_builder,
    taxonomy as tx,
    validator,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional validation output path for an untracked PR154 report copy.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Opt-in tracked PR154 report regeneration.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if args.write_report:
        report_builder.write_report_file(repo_root)
    if args.output is not None:
        output = args.output if args.output.is_absolute() else repo_root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            report_builder.json_dump(report_builder.build_report(repo_root)),
            encoding="utf-8",
            newline="\n",
        )

    failures = validator.validate_repository_artifacts(repo_root)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(tx.VALIDATOR_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
