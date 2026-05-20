from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from src.qtt.stage1_prediction_markets.market_data_ingest.validator import (
    ADAPTER_REPORT_PATH,
    HANDOFF_REPORT_PATH,
    MAIN_REPORT_PATH,
    NO_LIVE_NETWORK_REPORT_PATH,
    SOURCE_DEPENDENCY_REPORT_PATH,
    build_market_data_ingest_artifacts,
    validate_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def artifacts() -> dict[str, Any]:
    return build_market_data_ingest_artifacts(REPO_ROOT)


def cloned_artifacts() -> dict[str, Any]:
    return deepcopy(artifacts())


def validation_failures(value: Mapping[str, Any]) -> list[str]:
    return validate_artifacts(value, repo_root=REPO_ROOT)


def main_report() -> dict[str, Any]:
    return artifacts()["main_report"]


def adapter_report() -> dict[str, Any]:
    return artifacts()["adapter_report"]


def source_dependency_report() -> dict[str, Any]:
    return artifacts()["source_dependency_report"]


def no_live_network_report() -> dict[str, Any]:
    return artifacts()["no_live_network_report"]


def handoff_report() -> dict[str, Any]:
    return artifacts()["handoff_report"]


def adapter_inputs() -> list[dict[str, Any]]:
    return adapter_report()["venue_market_data_adapter_inputs"]


def adapter_bindings() -> list[dict[str, Any]]:
    return adapter_report()["venue_market_data_adapter_bindings"]


def canonical_events() -> list[dict[str, Any]]:
    return adapter_report()["canonical_market_data_ingest_events"]


def source_dependencies() -> list[dict[str, Any]]:
    return source_dependency_report()["market_data_source_dependencies"]


def rejections() -> list[dict[str, Any]]:
    return source_dependency_report()["venue_market_data_adapter_rejections"]


def no_live_attestations() -> list[dict[str, Any]]:
    return no_live_network_report()["market_data_no_live_network_attestations"]


def downstream_handoff() -> dict[str, Any]:
    return handoff_report()["market_data_ingest_downstream_handoff"]


def generated_report_payloads() -> dict[str, dict[str, Any]]:
    paths = {
        "main_report": MAIN_REPORT_PATH,
        "adapter_report": ADAPTER_REPORT_PATH,
        "source_dependency_report": SOURCE_DEPENDENCY_REPORT_PATH,
        "no_live_network_report": NO_LIVE_NETWORK_REPORT_PATH,
        "handoff_report": HANDOFF_REPORT_PATH,
    }
    return {
        key: json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
        for key, path in paths.items()
    }


def stage1_venues() -> set[str]:
    return set(policy.STAGE1_VENUE_IDS)


def shared_scopes() -> set[str]:
    return set(policy.SHARED_SCOPE_IDS)


def all_contract_records() -> list[dict[str, Any]]:
    return [
        *adapter_inputs(),
        *adapter_bindings(),
        *canonical_events(),
        *source_dependencies(),
        *rejections(),
        *no_live_attestations(),
        downstream_handoff(),
    ]
