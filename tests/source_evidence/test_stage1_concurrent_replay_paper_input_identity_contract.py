from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_concurrent_replay_paper_contract_check import (
    INPUT_IDENTITY_TYPE,
    REQUIRED_FIXTURE_CASES,
    validate_gate_case_record,
    validate_input_identity_record,
    validate_static_surface,
)


INPUT_IDENTITY_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/replay_paper/"
    "concurrent_replay_paper_input_identity.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/replay_paper/"
    "synthetic_concurrent_replay_paper_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _identity() -> dict:
    return copy.deepcopy(_fixture()["input_identity_records"][0])


def _case_by_fixture_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["execution_gate_case_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_concurrent_replay_paper_static_surface_validates_and_contains_all_required_cases():
    assert INPUT_IDENTITY_SCHEMA.exists()
    assert FIXTURE.exists()
    assert validate_static_surface(repo_root=Path(".")) == []

    fixture = _fixture()
    fixture_cases = {
        record["fixture_case"]
        for key in [
            "input_identity_records",
            "replay_lane_contract_records",
            "paper_lane_contract_records",
            "replay_result_packet_boundary_records",
            "paper_result_packet_boundary_records",
            "execution_gate_case_records",
        ]
        for record in fixture[key]
    }
    assert REQUIRED_FIXTURE_CASES.issubset(fixture_cases)


def test_input_identity_schema_requires_shared_snapshot_input_lock_identity_sets_and_receipts():
    schema = _load(INPUT_IDENTITY_SCHEMA)
    required = set(schema["required"])
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["input_identity_record_type"]["const"] == INPUT_IDENTITY_TYPE
    assert {
        "runtime_resolver_snapshot_id",
        "runtime_resolver_snapshot_digest",
        "runtime_resolver_input_lock_id",
        "runtime_resolver_input_lock_digest",
        "runtime_resolver_to_replay_paper_handoff_id",
        "runtime_resolver_handoff_gate_report_id",
        "replay_paper_input_identity_digest",
        "candidate_contract_identity_set",
        "candidate_contract_identity_set_digest",
        "venue_normalization_identity_set",
        "venue_normalization_identity_set_digest",
        "source_connector_semantic_gate_receipt_refs",
        "replay_lane_input_identity_ref",
        "paper_lane_input_identity_ref",
        "combined_result_packet_allowed_flag",
        "lane_result_merge_allowed_flag",
        "mutation_allowed_flag",
    }.issubset(required)
    assert props["combined_result_packet_allowed_flag"]["const"] is False
    assert props["lane_result_merge_allowed_flag"]["const"] is False
    assert props["mutation_allowed_flag"]["const"] is False
    assert props["live_reachability_allowed_flag"]["const"] is False
    assert props["order_execution_allowed_flag"]["const"] is False


def test_replay_and_paper_share_same_runtime_snapshot_input_lock_identity_sets_and_receipts():
    record = _identity()
    replay = record["replay_lane_input_identity_ref"]
    paper = record["paper_lane_input_identity_ref"]

    assert record["input_identity_state"] == "STATIC_INPUT_IDENTITY_VALID_FOR_GATE_ONLY"
    assert replay["runtime_resolver_snapshot_id"] == paper["runtime_resolver_snapshot_id"]
    assert replay["runtime_resolver_snapshot_digest"] == paper["runtime_resolver_snapshot_digest"]
    assert replay["runtime_resolver_input_lock_id"] == paper["runtime_resolver_input_lock_id"]
    assert (
        replay["replay_paper_input_identity_digest"]
        == paper["replay_paper_input_identity_digest"]
        == record["replay_paper_input_identity_digest"]
    )
    assert replay["candidate_contract_identity_set"] == paper["candidate_contract_identity_set"]
    assert replay["venue_normalization_identity_set"] == paper["venue_normalization_identity_set"]
    assert replay["source_evidence_gate_receipt_ids"] == paper["source_evidence_gate_receipt_ids"]
    assert replay["connector_semantic_gate_receipt_ids"] == paper["connector_semantic_gate_receipt_ids"]
    assert validate_input_identity_record(record) == []


def test_identity_contract_rejects_missing_mismatched_or_conflicting_shared_inputs():
    record = _identity()
    record["runtime_resolver_snapshot_id"] = ""
    record["paper_lane_input_identity_ref"]["runtime_resolver_snapshot_digest"] = (
        "9999999999999999999999999999999999999999999999999999999999999999"
    )
    record["paper_lane_input_identity_ref"]["runtime_resolver_input_lock_id"] = (
        "SYNTHETIC_DIFFERENT_INPUT_LOCK"
    )
    record["paper_lane_input_identity_ref"]["replay_paper_input_identity_digest"] = (
        "8888888888888888888888888888888888888888888888888888888888888888"
    )
    record["paper_lane_input_identity_ref"]["candidate_contract_identity_set"] = [
        "SYNTHETIC_DIFFERENT_CANDIDATE_CONTRACT_IDENTITY"
    ]
    record["paper_lane_input_identity_ref"]["venue_normalization_identity_set"] = [
        "SYNTHETIC_DIFFERENT_VENUE_NORMALIZATION_IDENTITY"
    ]
    record["paper_lane_input_identity_ref"]["source_evidence_gate_receipt_ids"] = [
        "SYNTHETIC_DIFFERENT_SOURCE_RECEIPT"
    ]

    failures = validate_input_identity_record(record)

    _assert_failure_contains(failures, "runtime_resolver_snapshot_id must be present")
    _assert_failure_contains(failures, "runtime_resolver_snapshot_digest must match")
    _assert_failure_contains(failures, "runtime_resolver_input_lock_id must match")
    _assert_failure_contains(failures, "replay and paper identity digests must match")
    _assert_failure_contains(failures, "candidate contract identity sets must match")
    _assert_failure_contains(failures, "venue normalization identity sets must match")
    _assert_failure_contains(failures, "source_evidence_gate_receipt_ids must match")


def test_gate_cases_block_missing_stale_conflict_schema_target_and_receipt_states():
    cases = _case_by_fixture_case()
    expected = {
        "BLOCKED_MISSING_RUNTIME_RESOLVER_SNAPSHOT_ID": "BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_ID_MISSING",
        "BLOCKED_MISSING_RUNTIME_RESOLVER_SNAPSHOT_DIGEST": "BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_DIGEST_MISSING",
        "BLOCKED_MISSING_RUNTIME_RESOLVER_INPUT_LOCK": "BLOCKED_RUNTIME_RESOLVER_INPUT_LOCK_MISSING",
        "BLOCKED_MISSING_HANDOFF_GATE_REPORT": "BLOCKED_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_REPORT_MISSING",
        "BLOCKED_STALE_RUNTIME_RESOLVER_SNAPSHOT": "BLOCKED_STALE_RUNTIME_RESOLVER_SNAPSHOT",
        "BLOCKED_SUPERSEDED_RUNTIME_RESOLVER_SNAPSHOT": "BLOCKED_SUPERSEDED_RUNTIME_RESOLVER_SNAPSHOT",
        "BLOCKED_CONFLICT_RUNTIME_RESOLVER_SNAPSHOT": "BLOCKED_CONFLICT_RUNTIME_RESOLVER_SNAPSHOT",
        "BLOCKED_SCHEMA_ERROR": "BLOCKED_SCHEMA_ERROR",
        "BLOCKED_TARGET_MISMATCH": "BLOCKED_TARGET_MISMATCH",
        "BLOCKED_MISSING_SOURCE_CONNECTOR_SEMANTIC_RECEIPTS": "BLOCKED_SOURCE_CONNECTOR_SEMANTIC_GATE_RECEIPTS_MISSING",
    }

    for fixture_case, expected_state in expected.items():
        record = cases[fixture_case]
        assert record["expected_gate_state"] == expected_state
        assert record["blocker_codes"]
        assert validate_gate_case_record(record) == []
