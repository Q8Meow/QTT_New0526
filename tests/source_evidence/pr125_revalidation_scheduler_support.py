from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.qtt.source_evidence.revalidation.scheduler import (
    DETERMINISTIC_FIXTURE_TIME,
    load_pr125_fixture_inputs,
    run_revalidation_scheduler,
)
from src.qtt.source_evidence.revalidation.validator import (
    FUTURE_OFFICIAL_SOURCE_REVALIDATION_PATH,
    validate_source_revalidation_scheduler,
)


REPO_ROOT = Path(".")
FIXTURE_ROOT = Path("tests/fixtures/source_evidence/pr125_revalidation_scheduler")
REPORT_PATH = Path(
    "docs/master_plan/source_evidence/generated/"
    "CODEX_PR125_SOURCE_REVALIDATION_SUPERSESSION_MATERIALITY_SCHEDULER_REPORT.json"
)


def inputs() -> dict[str, Any]:
    return load_pr125_fixture_inputs(REPO_ROOT)


def result() -> dict[str, Any]:
    fixture_inputs = inputs()
    return run_revalidation_scheduler(
        fixture_inputs["accepted_source_evidence_records"]["accepted_source_evidence_records"],
        fixture_inputs["connector_semantic_binding_records"][
            "connector_semantic_binding_records"
        ],
        fixture_inputs["revalidation_events"]["revalidation_events"],
        deterministic_fixture_time=DETERMINISTIC_FIXTURE_TIME,
    )


def report_and_failures() -> tuple[dict[str, Any], list[str]]:
    return validate_source_revalidation_scheduler(REPO_ROOT)


def generated_report() -> dict[str, Any]:
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


def schedule_by_packet(packet_id: str) -> dict[str, Any]:
    return next(
        record
        for record in result()["source_revalidation_schedule_records"]
        if record["accepted_source_evidence_packet_id"] == packet_id
    )


def materiality_by_event(event_id: str) -> dict[str, Any]:
    return next(
        record
        for record in result()["source_change_materiality_events"]
        if record["source_change_event_id"] == event_id
    )


def snapshot() -> dict[str, Any]:
    return result()["source_change_impact_snapshots"][0]


def supersession_records() -> list[dict[str, Any]]:
    return result()["source_supersession_records"]
