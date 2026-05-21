from __future__ import annotations

import copy
import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor import (
    policy,
    validator,
)
from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor.executor import (
    build_runtime_resolver_snapshot_artifacts,
)
from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor.integrity import (
    compute_integrity_summary,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "source_evidence"
    / "pr134_runtime_resolver_snapshot_executor"
)
PACKAGE_DIR = (
    REPO_ROOT
    / "src"
    / "qtt"
    / "stage1_prediction_markets"
    / "runtime_resolver_snapshot_executor"
)


def artifacts() -> dict:
    return build_runtime_resolver_snapshot_artifacts()


def mutable_artifacts() -> dict:
    return copy.deepcopy(artifacts())


def failure_codes(payload: dict) -> set[str]:
    return {failure.code for failure in validator.validate_artifacts(payload, repo_root=REPO_ROOT)}


def summary(payload: dict | None = None) -> dict:
    payload = payload or artifacts()
    return compute_integrity_summary(
        payload["runtime_resolver_input_locks"],
        payload["runtime_resolver_snapshots"],
        payload["runtime_resolver_bindings"],
        payload["orderbook_event_state_snapshot_downstream_handoff"],
        payload["atomicrows_pre_bridge_compatibility"],
    )


def malformed_payload(file_name: str) -> dict:
    path = FIXTURE_DIR / file_name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return validator.build_malformed_fixture_payloads()[file_name]


def assert_malformed(file_name: str, expected_code: str) -> None:
    payload = malformed_payload(file_name)
    failures = validator.validate_malformed_fixture_payload(payload)
    assert expected_code in {failure.code for failure in failures}


def schema(file_name: str) -> dict:
    path = PACKAGE_DIR / file_name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return validator.build_schema_documents()[file_name]


def all_runtime_records(payload: dict | None = None) -> list[dict]:
    payload = payload or artifacts()
    records: list[dict] = []
    for key in (
        "runtime_resolver_input_locks",
        "runtime_resolver_snapshots",
        "runtime_resolver_bindings",
        "runtime_resolver_integrity_receipts",
        "runtime_resolver_rejections",
        "atomicrows_pre_bridge_compatibility",
    ):
        records.extend(payload[key])
    records.append(payload["runtime_resolver_downstream_handoff"])
    return records


def scope_value(record: dict) -> str:
    return record.get("venue_id") or record.get("scope_id")


def venue_records(records: list[dict]) -> list[dict]:
    return [record for record in records if record.get("venue_id") in policy.STAGE1_VENUE_IDS]
