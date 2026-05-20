from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.capital_risk.field_map import (
    ACTIVE_STAGE1_VENUES,
    COMPONENTS,
    SHARED_SCOPE_METADATA,
    build_runtime_cash_artifacts,
)
from src.qtt.stage1_prediction_markets.capital_risk.validator import (
    AVAILABLE_REPORT_PATH,
    FIELD_MAP_REPORT_PATH,
    GATE_REPORT_PATH,
    HANDOFF_REPORT_PATH,
    MAIN_REPORT_PATH,
    RECONCILIATION_REPORT_PATH,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def artifacts() -> dict[str, Any]:
    return build_runtime_cash_artifacts(REPO_ROOT)


def main_report() -> dict[str, Any]:
    return artifacts()["main_report"]


def field_map_report() -> dict[str, Any]:
    return artifacts()["field_map_report"]


def reconciliation_report() -> dict[str, Any]:
    return artifacts()["reconciliation_report"]


def available_report() -> dict[str, Any]:
    return artifacts()["available_report"]


def gate_report() -> dict[str, Any]:
    return artifacts()["gate_report"]


def handoff_report() -> dict[str, Any]:
    return artifacts()["handoff_report"]


def field_maps() -> list[dict[str, Any]]:
    return field_map_report()["runtime_cash_component_field_maps"]


def venue_bindings() -> list[dict[str, Any]]:
    return field_map_report()["venue_balance_semantic_bindings"]


def source_rejections() -> list[dict[str, Any]]:
    return field_map_report()["source_packet_required_rejection_receipts"]


def unknown_rejections() -> list[dict[str, Any]]:
    return field_map_report()["unknown_cash_component_rejection_receipts"]


def available_receipts() -> list[dict[str, Any]]:
    return available_report()["runtime_available_after_commitments_receipts"]


def gate_receipts() -> list[dict[str, Any]]:
    return gate_report()["new_exposure_cash_gate_receipts"]


def stage1_venues() -> set[str]:
    return set(ACTIVE_STAGE1_VENUES)


def component_classes() -> set[str]:
    return {component.class_name for component in COMPONENTS}


def shared_scope_metadata() -> set[str]:
    return set(SHARED_SCOPE_METADATA)


def generated_report_payloads() -> dict[str, dict[str, Any]]:
    return {
        "main_report": json.loads((REPO_ROOT / MAIN_REPORT_PATH).read_text(encoding="utf-8")),
        "field_map_report": json.loads(
            (REPO_ROOT / FIELD_MAP_REPORT_PATH).read_text(encoding="utf-8")
        ),
        "reconciliation_report": json.loads(
            (REPO_ROOT / RECONCILIATION_REPORT_PATH).read_text(encoding="utf-8")
        ),
        "available_report": json.loads(
            (REPO_ROOT / AVAILABLE_REPORT_PATH).read_text(encoding="utf-8")
        ),
        "handoff_report": json.loads(
            (REPO_ROOT / HANDOFF_REPORT_PATH).read_text(encoding="utf-8")
        ),
        "gate_report": json.loads((REPO_ROOT / GATE_REPORT_PATH).read_text(encoding="utf-8")),
    }
