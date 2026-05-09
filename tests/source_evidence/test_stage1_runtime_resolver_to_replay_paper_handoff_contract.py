from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_runtime_resolver_to_replay_paper_handoff_check import (
    ALLOWED_IMMEDIATE_CONSUMER,
    HANDOFF_TYPE,
    READY_STATE,
    REQUIRED_FIXTURE_CASES,
    build_report,
    validate_handoff_record,
    validate_static_surface,
)


CONSUMER_ALLOWLIST_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
    "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json"
)
HANDOFF_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
    "stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json"
)
REPORT_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
    "stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/runtime_resolver_snapshot/"
    "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _valid_handoff() -> dict:
    return copy.deepcopy(_fixture()["valid_handoff_record"])


def _allowlists() -> list[dict]:
    return _fixture()["consumer_allowlist_records"]


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_handoff_static_surface_validates_and_contains_all_required_cases():
    assert CONSUMER_ALLOWLIST_SCHEMA.exists()
    assert HANDOFF_SCHEMA.exists()
    assert REPORT_SCHEMA.exists()
    assert FIXTURE.exists()
    assert validate_static_surface(repo_root=Path(".")) == []

    fixture_cases = {record["fixture_case"] for record in _fixture()["handoff_case_records"]}
    assert REQUIRED_FIXTURE_CASES.issubset(fixture_cases)


def test_handoff_schema_requires_snapshot_input_lock_gate_allowlist_and_no_authority_flags():
    schema = _load(HANDOFF_SCHEMA)
    required = set(schema["required"])
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["handoff_record_type"]["const"] == HANDOFF_TYPE
    assert {
        "runtime_resolver_snapshot_packet_reference",
        "runtime_resolver_snapshot_input_lock_reference",
        "runtime_resolver_snapshot_gate_report_reference",
        "runtime_resolver_snapshot_consumer_allowlist_reference",
        "upstream_digest_contract",
        "matching_identity_contract",
        "handoff_boundary_flags",
        "no_claim_flags",
        "validation_hook_ids",
    }.issubset(required)

    boundary_props = schema["$defs"]["handoff_boundary_flags"]["properties"]
    assert boundary_props["no_replay_or_paper_execution_created_flag"]["const"] is True
    assert boundary_props["no_replay_or_paper_result_created_flag"]["const"] is True
    assert boundary_props["no_dual_result_review_created_flag"]["const"] is True
    assert boundary_props["runtime_resolver_snapshot_mutation_allowed_flag"]["const"] is False
    assert boundary_props["new_contract_event_market_selection_allowed_flag"]["const"] is False
    assert boundary_props["replay_paper_execution_authority_allowed_flag"]["const"] is False
    assert boundary_props["order_execution_allowed_flag"]["const"] is False
    assert boundary_props["runtime_cash_claim_allowed_flag"]["const"] is False
    assert boundary_props["profit_claim_allowed_flag"]["const"] is False


def test_valid_handoff_requires_allowlisted_input_lock_gate_and_matching_references():
    record = _valid_handoff()
    assert record["handoff_state"] == READY_STATE
    assert record["requested_immediate_consumer_id"] == ALLOWED_IMMEDIATE_CONSUMER
    assert record["allowed_next_consumer_task_packet_id"] == ALLOWED_IMMEDIATE_CONSUMER
    assert record["allowed_next_consumer_section_id"] == "0X.4T_INPUT_LOCK_GATE_ONLY"
    assert validate_handoff_record(record, allowlist_records=_allowlists()) == []

    snapshot = record["runtime_resolver_snapshot_packet_reference"]
    input_lock = record["runtime_resolver_snapshot_input_lock_reference"]
    gate = record["runtime_resolver_snapshot_gate_report_reference"]
    allowlist = record["runtime_resolver_snapshot_consumer_allowlist_reference"]

    assert input_lock["snapshot_packet_id"] == snapshot["snapshot_packet_id"]
    assert gate["snapshot_packet_id"] == snapshot["snapshot_packet_id"]
    assert allowlist["snapshot_packet_id"] == snapshot["snapshot_packet_id"]
    assert input_lock["snapshot_packet_digest"] == snapshot["snapshot_packet_digest"]
    assert gate["snapshot_packet_digest"] == snapshot["snapshot_packet_digest"]
    assert allowlist["snapshot_packet_digest"] == snapshot["snapshot_packet_digest"]
    assert (
        record["upstream_digest_contract"]["runtime_resolver_snapshot_input_lock_digest"]
        == input_lock["input_lock_digest"]
    )


def test_handoff_report_remains_static_and_creates_no_runtime_authority():
    fixture = _fixture()
    report = build_report(fixture=fixture, repo_root=Path("."), validation_failures=[])

    assert report["gate_state"] == "STATIC_HANDOFF_CONTRACT_VALIDATED_NO_RUNTIME_AUTHORITY"
    assert report["allowed_immediate_consumer_count"] == 1
    assert report["runtime_execution_authority_created_flag"] is False
    assert report["replay_paper_execution_created_flag"] is False
    assert report["replay_paper_result_packet_created_flag"] is False
    assert report["dual_result_review_created_flag"] is False
    assert report["live_reachability_created_flag"] is False
    assert report["order_authority_created_flag"] is False
    assert report["runtime_cash_claim_created_flag"] is False
    assert report["atomicrows_bundle_hash_created_or_mutated_flag"] is False
    assert report["blocker_reduction_claim_created_flag"] is False
    assert report["profit_evidence_created_flag"] is False


def test_handoff_rejects_consumer_not_allowlisted_even_with_matching_digests():
    record = _valid_handoff()
    record["requested_immediate_consumer_id"] = "DIRECT_LIVE_CONSUMER"
    record["requested_immediate_consumer_class"] = "DIRECT_LIVE_CONSUMER"

    failures = validate_handoff_record(record, allowlist_records=_allowlists())

    _assert_failure_contains(failures, "requested_immediate_consumer_id is not allowlisted")


def test_handoff_rejects_digest_and_identity_mismatches_fail_closed():
    record = _valid_handoff()
    record["runtime_resolver_snapshot_gate_report_reference"]["snapshot_packet_digest"] = (
        "9999999999999999999999999999999999999999999999999999999999999999"
    )
    record["matching_identity_contract"]["handoff_identity_digest_from_input_lock"] = (
        "8888888888888888888888888888888888888888888888888888888888888888"
    )

    failures = validate_handoff_record(record, allowlist_records=_allowlists())

    _assert_failure_contains(failures, "snapshot_packet_digest must match snapshot packet digest")
    _assert_failure_contains(failures, "matching_identity_contract digests must all match")
