from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.builder import (
    canonical_event_state_sort_key,
    canonical_orderbook_sort_key,
)
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.validator import (
    REPORT_PATHS,
    build_snapshot_artifacts,
    validate_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def artifacts() -> dict[str, Any]:
    return build_snapshot_artifacts(REPO_ROOT)


def cloned_artifacts() -> dict[str, Any]:
    return deepcopy(artifacts())


def validation_failures(value: Mapping[str, Any]) -> list[str]:
    return validate_artifacts(value, repo_root=REPO_ROOT)


def main_report() -> dict[str, Any]:
    return artifacts()["main_report"]


def snapshot_report() -> dict[str, Any]:
    return artifacts()["snapshot_report"]


def handoff() -> dict[str, Any]:
    return artifacts()["downstream_handoff"]


def input_locks() -> list[dict[str, Any]]:
    return artifacts()["snapshot_input_locks"]


def orderbook_snapshots() -> list[dict[str, Any]]:
    return artifacts()["orderbook_snapshots"]


def event_state_snapshots() -> list[dict[str, Any]]:
    return artifacts()["event_state_snapshots"]


def bindings() -> list[dict[str, Any]]:
    return artifacts()["snapshot_builder_bindings"]


def integrity_receipts() -> list[dict[str, Any]]:
    return artifacts()["snapshot_integrity_receipts"]


def atomicrows_records() -> list[dict[str, Any]]:
    return artifacts()["atomicrows_compatibility_records"]


def all_records() -> list[dict[str, Any]]:
    built = artifacts()
    return [
        *built["snapshot_input_locks"],
        *built["orderbook_snapshots"],
        *built["event_state_snapshots"],
        *built["snapshot_builder_bindings"],
        *built["snapshot_integrity_receipts"],
        *built["snapshot_rejections"],
        *built["atomicrows_compatibility_records"],
        built["downstream_handoff"],
    ]


def generated_report_payloads() -> dict[str, dict[str, Any]]:
    return {
        key: json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
        for key, path in REPORT_PATHS.items()
    }


def stage1_venues() -> set[str]:
    return set(policy.STAGE1_VENUE_IDS)


def shared_scopes() -> set[str]:
    return set(policy.SHARED_SCOPE_IDS)
