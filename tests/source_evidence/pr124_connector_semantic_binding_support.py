from __future__ import annotations

import json
from pathlib import Path

from src.qtt.source_evidence.connector_semantic_consumer.validator import (
    FUTURE_OFFICIAL_SOURCE_INGESTION_PATH,
    STAGE1_SURFACES,
    consume_pr124_fixture_inputs,
    load_pr124_fixture_inputs,
    validate_pr124_connector_semantic_binding,
)


REPO_ROOT = Path(".")
FIXTURE_ROOT = Path("tests/fixtures/source_evidence/pr124_connector_semantic_binding")
EXPECTED_PATH = FIXTURE_ROOT / "connector_semantic_binding_expected.v1.fixture.json"
REPORT_PATH = Path(
    "docs/master_plan/source_evidence/generated/"
    "CODEX_PR124_ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE_REPORT.json"
)


def inputs() -> dict:
    return load_pr124_fixture_inputs(REPO_ROOT)


def consumed() -> dict:
    return consume_pr124_fixture_inputs(inputs())


def expected() -> dict:
    return json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))


def report_and_failures() -> tuple[dict, list[str]]:
    return validate_pr124_connector_semantic_binding(REPO_ROOT)


def rejection_by_case(case_id: str) -> dict:
    return next(
        record
        for record in consumed()["rejection_reports"]
        if record["fixture_case"] == case_id
    )
