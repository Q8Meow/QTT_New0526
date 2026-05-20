from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.qtt.source_evidence.cross_venue_execution_normalization.taxonomy import (
    ACTIVE_STAGE1_VENUES,
)
from src.qtt.source_evidence.cross_venue_execution_normalization.validator import (
    BINDING_REPORT_PATH,
    DOWNSTREAM_HANDOFF_REPORT_PATH,
    MAIN_REPORT_PATH,
    TAXONOMY_REPORT_PATH,
    build_validation_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def artifacts() -> dict[str, Any]:
    return build_validation_artifacts(REPO_ROOT)


def main_report() -> dict[str, Any]:
    return artifacts()["main_report"]


def binding_report() -> dict[str, Any]:
    return artifacts()["binding_report"]


def taxonomy_record() -> dict[str, Any]:
    return binding_report()["taxonomy_records"][0]


def phase_bindings() -> list[dict[str, Any]]:
    return binding_report()["phase_binding_records"]


def transition_bindings() -> list[dict[str, Any]]:
    return binding_report()["transition_binding_records"]


def placeholder_records() -> list[dict[str, Any]]:
    return binding_report()["placeholder_normalization_records"]


def arbitrage_preconditions() -> list[dict[str, Any]]:
    return binding_report()["arbitrage_comparability_precondition_records"]


def downstream_handoff() -> dict[str, Any]:
    return binding_report()["downstream_handoff"]


def rejection_records() -> list[dict[str, Any]]:
    return binding_report()["rejection_records"]


def rejections_by_state() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in rejection_records():
        grouped.setdefault(record["normalization_state"], []).append(record)
    return grouped


def generated_report_payloads() -> dict[str, dict[str, Any]]:
    return {
        "main_report": json.loads((REPO_ROOT / MAIN_REPORT_PATH).read_text(encoding="utf-8")),
        "binding_report": json.loads(
            (REPO_ROOT / BINDING_REPORT_PATH).read_text(encoding="utf-8")
        ),
        "taxonomy_report": json.loads(
            (REPO_ROOT / TAXONOMY_REPORT_PATH).read_text(encoding="utf-8")
        ),
        "downstream_handoff_report": json.loads(
            (REPO_ROOT / DOWNSTREAM_HANDOFF_REPORT_PATH).read_text(encoding="utf-8")
        ),
    }


def stage1_venues() -> set[str]:
    return set(ACTIVE_STAGE1_VENUES)
