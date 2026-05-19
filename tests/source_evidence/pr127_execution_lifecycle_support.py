from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.qtt.source_evidence.execution_lifecycle.builder import ACTIVE_STAGE1_VENUES
from src.qtt.source_evidence.execution_lifecycle.validator import (
    BUILDER_REPORT_PATH,
    HANDOFF_REPORT_PATH,
    MAIN_REPORT_PATH,
    MODELS_REPORT_PATH,
    build_validation_artifacts,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "source_evidence"
    / "pr127_execution_lifecycle"
)


def artifacts() -> dict[str, Any]:
    return build_validation_artifacts(REPO_ROOT)


def main_report() -> dict[str, Any]:
    return artifacts()["main_report"]


def model_records() -> list[dict[str, Any]]:
    return artifacts()["models_report"]["lifecycle_model_records"]


def models_by_venue() -> dict[str, dict[str, Any]]:
    return {record["venue_id"]: record for record in model_records()}


def placeholder_records() -> list[dict[str, Any]]:
    return artifacts()["models_report"]["placeholder_records"]


def rejection_records() -> list[dict[str, Any]]:
    return artifacts()["models_report"]["rejection_records"]


def rejections_by_state() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in rejection_records():
        grouped.setdefault(record["lifecycle_model_state"], []).append(record)
    return grouped


def validation_receipts() -> list[dict[str, Any]]:
    return artifacts()["models_report"]["validation_receipts"]


def handoff() -> dict[str, Any]:
    return artifacts()["handoff_report"]["handoff"]


def generated_report_payloads() -> dict[str, dict[str, Any]]:
    return {
        "main_report": json.loads((REPO_ROOT / MAIN_REPORT_PATH).read_text(encoding="utf-8")),
        "builder_report": json.loads(
            (REPO_ROOT / BUILDER_REPORT_PATH).read_text(encoding="utf-8")
        ),
        "models_report": json.loads((REPO_ROOT / MODELS_REPORT_PATH).read_text(encoding="utf-8")),
        "handoff_report": json.loads((REPO_ROOT / HANDOFF_REPORT_PATH).read_text(encoding="utf-8")),
    }


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def stage1_venues() -> set[str]:
    return set(ACTIVE_STAGE1_VENUES)
