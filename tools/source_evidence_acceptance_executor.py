#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.source_evidence.acceptance.executor import execute_acceptance_input
from src.qtt.source_evidence.acceptance.validator import stable_report
from tools import validate_source_evidence_acceptance as validator


SUCCESS_MARKER = "QTT_SOURCE_EVIDENCE_ACCEPTANCE_EXECUTOR_OK"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--write-reports", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    if args.input:
        input_record = json.loads((repo_root / args.input).read_text(encoding="utf-8"))
        result = execute_acceptance_input(input_record)
        output = {
            "decision_receipt": result.decision_receipt,
            "accepted_packet": result.accepted_packet,
            "accepted_ledger_record": result.accepted_ledger_record,
            "conflict_report": result.conflict_report,
            "revalidation_status": result.revalidation_status,
            "reject_receipt": result.reject_receipt,
        }
        if args.output:
            output_path = repo_root / args.output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(stable_report(output), encoding="utf-8", newline="\n")
        else:
            print(stable_report(output), end="")
    if args.write_reports or not args.input:
        failures = validator.validate_static_surface(repo_root)
        if failures:
            raise SystemExit(
                "QTT_SOURCE_EVIDENCE_ACCEPTANCE_EXECUTOR_FAILED\n- "
                + "\n- ".join(failures)
            )
        validator.write_reports(repo_root)
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
