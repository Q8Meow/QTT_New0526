from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.qtt.source_evidence.connector_semantic_implementation.validator import (
    GATE_REPORT_PATH,
    MAIN_REPORT_PATH,
    MANIFEST_REPORT_PATH,
    build_validation_artifacts,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "source_evidence"
    / "pr126_connector_semantic_implementation_gate"
)


def artifacts() -> dict[str, Any]:
    return build_validation_artifacts(REPO_ROOT)


def decisions_by_binding() -> dict[str, dict[str, Any]]:
    return {
        record["source_connector_binding_ledger_record_id"]: record
        for record in artifacts()["gate_report"]["decision_receipts"]
    }


def rejection_by_binding() -> dict[str, dict[str, Any]]:
    return {
        record["source_connector_binding_ledger_record_id"]: record
        for record in artifacts()["gate_report"]["rejection_records"]
    }


def manifest_records() -> list[dict[str, Any]]:
    return artifacts()["manifest_report"]["manifest_records"]


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def generated_report_payloads() -> dict[str, dict[str, Any]]:
    return {
        "main_report": json.loads((REPO_ROOT / MAIN_REPORT_PATH).read_text(encoding="utf-8")),
        "gate_report": json.loads((REPO_ROOT / GATE_REPORT_PATH).read_text(encoding="utf-8")),
        "manifest_report": json.loads(
            (REPO_ROOT / MANIFEST_REPORT_PATH).read_text(encoding="utf-8")
        ),
    }
