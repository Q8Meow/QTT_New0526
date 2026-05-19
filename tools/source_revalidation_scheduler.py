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
from src.qtt.source_evidence.revalidation.scheduler import (  # noqa: E402
    DETERMINISTIC_FIXTURE_TIME,
    load_pr125_fixture_inputs,
    run_revalidation_scheduler,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--out",
        default=(
            "docs/master_plan/source_evidence/generated/"
            "SourceRevalidationScheduler.report.json"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = Path(args.repo_root)
    inputs = load_pr125_fixture_inputs(repo_root)
    result = run_revalidation_scheduler(
        inputs["accepted_source_evidence_records"]["accepted_source_evidence_records"],
        inputs["connector_semantic_binding_records"]["connector_semantic_binding_records"],
        inputs["revalidation_events"]["revalidation_events"],
        deterministic_fixture_time=DETERMINISTIC_FIXTURE_TIME,
    )
    write_json_object(repo_root / Path(args.out), result)
    print("QTT_SOURCE_REVALIDATION_SCHEDULER_FIXTURE_OUTPUT_WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
