from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.credential_readiness import policy
from src.qtt.stage1_prediction_markets.credential_readiness.validator import (
    ALIAS_REPORT_PATH,
    HANDOFF_REPORT_PATH,
    MAIN_REPORT_PATH,
    NO_CAPTURE_REPORT_PATH,
    SCOPE_REPORT_PATH,
    build_credential_readiness_artifacts,
    validate_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def artifacts() -> dict[str, Any]:
    return build_credential_readiness_artifacts(REPO_ROOT)


def cloned_artifacts() -> dict[str, Any]:
    return deepcopy(artifacts())


def validation_failures(value: dict[str, Any]) -> list[str]:
    return validate_artifacts(value, repo_root=REPO_ROOT)


def main_report() -> dict[str, Any]:
    return artifacts()["main_report"]


def alias_report() -> dict[str, Any]:
    return artifacts()["alias_report"]


def no_capture_report() -> dict[str, Any]:
    return artifacts()["no_capture_report"]


def scope_report() -> dict[str, Any]:
    return artifacts()["scope_report"]


def handoff_report() -> dict[str, Any]:
    return artifacts()["handoff_report"]


def alias_records() -> list[dict[str, Any]]:
    return alias_report()["credential_alias_registry_records"]


def readiness_receipts() -> list[dict[str, Any]]:
    return alias_report()["credential_alias_readiness_receipts"]


def no_capture_attestations() -> list[dict[str, Any]]:
    return no_capture_report()["secret_no_capture_attestations"]


def rejection_receipts() -> list[dict[str, Any]]:
    return no_capture_report()["credential_readiness_rejection_receipts"]


def scope_bindings() -> list[dict[str, Any]]:
    return scope_report()["credential_scope_bindings"]


def downstream_handoff() -> dict[str, Any]:
    return handoff_report()["credential_readiness_downstream_handoff"]


def generated_report_payloads() -> dict[str, dict[str, Any]]:
    paths = {
        "main_report": MAIN_REPORT_PATH,
        "alias_report": ALIAS_REPORT_PATH,
        "no_capture_report": NO_CAPTURE_REPORT_PATH,
        "scope_report": SCOPE_REPORT_PATH,
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
