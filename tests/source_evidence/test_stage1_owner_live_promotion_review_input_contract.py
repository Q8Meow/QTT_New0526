from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_owner_live_promotion_review_contract_check import (
    INPUT_CONTRACT_TYPE,
    REQUIRED_FIXTURE_CASES,
    validate_gate_case_record,
    validate_input_contract_record,
    validate_static_surface,
)


INPUT_CONTRACT_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/owner_live_promotion_review/"
    "stage1_owner_live_promotion_review_input_contract.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/owner_live_promotion_review/"
    "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _input_contract() -> dict:
    return copy.deepcopy(_fixture()["owner_live_promotion_review_input_contract_records"][0])


def _case_by_fixture_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["owner_live_promotion_review_gate_case_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_owner_live_promotion_review_static_surface_validates_and_contains_required_cases():
    assert INPUT_CONTRACT_SCHEMA.exists()
    assert FIXTURE.exists()
    assert validate_static_surface(repo_root=Path(".")) == []

    fixture = _fixture()
    fixture_cases = {
        record["fixture_case"]
        for key in [
            "owner_live_promotion_review_input_contract_records",
            "owner_approval_receipt_boundary_records",
            "three_venue_canary_eligibility_handoff_block_records",
            "owner_live_promotion_review_gate_case_records",
        ]
        for record in fixture[key]
    }
    assert REQUIRED_FIXTURE_CASES.issubset(fixture_cases)


def test_input_contract_schema_requires_pr44_gate_separate_results_digest_and_unchanged_snapshot():
    schema = _load(INPUT_CONTRACT_SCHEMA)
    props = schema["properties"]
    required = set(schema["required"])

    assert schema["additionalProperties"] is False
    assert props["owner_live_promotion_review_input_contract_type"]["const"] == INPUT_CONTRACT_TYPE
    assert {
        "dual_result_review_gate_report_ref",
        "dual_result_review_gate_report_digest",
        "dual_result_review_input_identity_digest",
        "replay_result_packet_boundary_ref",
        "paper_result_packet_boundary_ref",
        "runtime_resolver_snapshot_id",
        "dual_result_runtime_resolver_snapshot_id",
        "runtime_resolver_snapshot_identity_unchanged_flag",
        "upstream_report_references_immutable_flag",
        "upstream_receipt_references_immutable_flag",
        "result_merge_claimed_flag",
        "owner_live_promotion_review_decision_created_flag",
        "owner_approval_receipt_created_flag",
    }.issubset(required)
    assert props["runtime_resolver_snapshot_identity_unchanged_flag"]["const"] is True
    assert props["upstream_report_references_immutable_flag"]["const"] is True
    assert props["upstream_receipt_references_immutable_flag"]["const"] is True
    assert props["result_merge_claimed_flag"]["const"] is False
    assert props["owner_live_promotion_review_decision_created_flag"]["const"] is False
    assert props["owner_approval_receipt_created_flag"]["const"] is False


def test_input_contract_references_pr44_gate_separate_boundaries_and_unchanged_snapshot_identity():
    record = _input_contract()

    assert record["dual_result_review_gate_report_ref"]
    assert record["dual_result_review_gate_report_state"] == (
        "PRESENT_IMMUTABLE_PASS_OWNER_REVIEW_REQUIRED"
    )
    assert record["dual_result_review_state"] == "PASS_OWNER_REVIEW_REQUIRED"
    assert record["replay_result_packet_boundary_ref"] != record["paper_result_packet_boundary_ref"]
    assert record["replay_result_packet_boundary_digest"] != record["paper_result_packet_boundary_digest"]
    assert record["dual_result_review_input_identity_digest"]
    assert (
        record["runtime_resolver_snapshot_id"]
        == record["dual_result_runtime_resolver_snapshot_id"]
        == record["replay_runtime_resolver_snapshot_id"]
        == record["paper_runtime_resolver_snapshot_id"]
    )
    assert (
        record["runtime_resolver_snapshot_digest"]
        == record["dual_result_runtime_resolver_snapshot_digest"]
        == record["replay_runtime_resolver_snapshot_digest"]
        == record["paper_runtime_resolver_snapshot_digest"]
    )
    assert record["upstream_report_references_immutable_flag"] is True
    assert record["upstream_receipt_references_immutable_flag"] is True
    assert validate_input_contract_record(record) == []


def test_input_contract_rejects_missing_gate_boundaries_digest_stale_conflict_schema_lane_target_and_merge():
    record = _input_contract()
    record["dual_result_review_gate_report_ref"] = ""
    record["replay_result_packet_boundary_ref"] = ""
    record["paper_result_packet_boundary_ref"] = ""
    record["dual_result_review_input_identity_digest"] = ""
    record["dual_result_review_gate_report_state"] = "STALE"
    record["input_identity_digest_state"] = "MISSING"
    record["conflict_state"] = "CONFLICT_PRESENT"
    record["schema_state"] = "SCHEMA_ERROR"
    record["lane_match_state"] = "MISMATCH"
    record["target_match_state"] = "MISMATCH"
    record["result_merge_claimed_flag"] = True
    record["dual_result_runtime_resolver_snapshot_id"] = "SYNTHETIC_DIFFERENT_RUNTIME_SNAPSHOT"
    record["dual_result_runtime_resolver_snapshot_digest"] = (
        "9999999999999999999999999999999999999999999999999999999999999999"
    )

    failures = validate_input_contract_record(record)

    for fragment in [
        "dual_result_review_gate_report_ref must be present",
        "replay_result_packet_boundary_ref must be present",
        "paper_result_packet_boundary_ref must be present",
        "dual_result_review_input_identity_digest must be present",
        "dual_result_review_gate_report_state must be",
        "input_identity_digest_state must be PRESENT",
        "conflict_state must be NO_CONFLICT",
        "schema_state must be SCHEMA_VALID",
        "lane_match_state must be MATCH",
        "target_match_state must be MATCH",
        "result_merge_claimed_flag",
        "dual_result_runtime_resolver_snapshot_id must match",
        "dual_result_runtime_resolver_snapshot_digest must match",
    ]:
        _assert_failure_contains(failures, fragment)


def test_gate_cases_block_missing_dual_result_gate_boundaries_digest_and_invalid_states():
    cases = _case_by_fixture_case()
    expected = {
        "BLOCKED_MISSING_DUAL_RESULT_REVIEW_GATE_REPORT": (
            "BLOCKED_OWNER_REVIEW_DUAL_RESULT_REVIEW_GATE_REPORT_MISSING"
        ),
        "BLOCKED_MISSING_REPLAY_RESULT_BOUNDARY": (
            "BLOCKED_OWNER_REVIEW_REPLAY_RESULT_BOUNDARY_MISSING"
        ),
        "BLOCKED_MISSING_PAPER_RESULT_BOUNDARY": (
            "BLOCKED_OWNER_REVIEW_PAPER_RESULT_BOUNDARY_MISSING"
        ),
        "BLOCKED_MISSING_DUAL_RESULT_REVIEW_INPUT_IDENTITY_DIGEST": (
            "BLOCKED_OWNER_REVIEW_INPUT_IDENTITY_DIGEST_MISSING"
        ),
        "BLOCKED_STALE_DUAL_RESULT_REVIEW_REPORT": (
            "BLOCKED_OWNER_REVIEW_DUAL_RESULT_REVIEW_REPORT_STALE"
        ),
        "BLOCKED_SUPERSEDED_DUAL_RESULT_REVIEW_REPORT": (
            "BLOCKED_OWNER_REVIEW_DUAL_RESULT_REVIEW_REPORT_SUPERSEDED"
        ),
        "BLOCKED_CONFLICT_STATE": "BLOCKED_OWNER_REVIEW_CONFLICT_STATE",
        "BLOCKED_SCHEMA_ERROR_STATE": "BLOCKED_OWNER_REVIEW_SCHEMA_ERROR",
        "BLOCKED_LANE_MISMATCH": "BLOCKED_OWNER_REVIEW_LANE_MISMATCH",
        "BLOCKED_TARGET_MISMATCH": "BLOCKED_OWNER_REVIEW_TARGET_MISMATCH",
    }

    for fixture_case, expected_state in expected.items():
        record = cases[fixture_case]
        assert record["expected_gate_state"] == expected_state
        assert record["blocker_codes"]
        assert validate_gate_case_record(record) == []
