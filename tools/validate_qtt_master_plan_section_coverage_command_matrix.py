#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import validate_master_plan_section_coverage as section_coverage


REPO_ROOT = _REPO_ROOT
SUCCESS_MARKER = "QTT_MASTER_PLAN_SECTION_COVERAGE_COMMAND_MATRIX_OK"
FAILURE_MARKER = "QTT_MASTER_PLAN_SECTION_COVERAGE_COMMAND_MATRIX_FAILED"


def validate(
    *,
    repo_root: pathlib.Path = REPO_ROOT,
    master_plan: pathlib.Path = section_coverage.builder.DEFAULT_MASTER_PLAN,
    registry_path: pathlib.Path = section_coverage.builder.DEFAULT_REGISTRY,
    report_path: pathlib.Path = section_coverage.builder.DEFAULT_OUTPUT,
    schema_path: pathlib.Path = section_coverage.DEFAULT_SCHEMA,
) -> section_coverage.ValidationResult:
    return section_coverage.validate(
        mode="dev",
        repo_root=repo_root,
        master_plan=master_plan,
        registry_path=registry_path,
        report_path=report_path,
        schema_path=schema_path,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=REPO_ROOT)
    parser.add_argument(
        "--master-plan",
        type=pathlib.Path,
        default=section_coverage.builder.DEFAULT_MASTER_PLAN,
    )
    parser.add_argument(
        "--registry",
        type=pathlib.Path,
        default=section_coverage.builder.DEFAULT_REGISTRY,
    )
    parser.add_argument(
        "--report",
        type=pathlib.Path,
        default=section_coverage.builder.DEFAULT_OUTPUT,
    )
    parser.add_argument("--schema", type=pathlib.Path, default=section_coverage.DEFAULT_SCHEMA)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate(
        repo_root=args.repo_root,
        master_plan=args.master_plan,
        registry_path=args.registry,
        report_path=args.report,
        schema_path=args.schema,
    )
    if not result.ok:
        for failure in result.failures:
            print(f"{FAILURE_MARKER}: {failure}", file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
