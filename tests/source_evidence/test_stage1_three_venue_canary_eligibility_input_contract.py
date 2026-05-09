from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_three_venue_canary_eligibility_contract_check import (
    CANONICAL_PLATFORMS,
    INPUT_CONTRACT_TYPE,
    OWNER_REVIEW_TO_CANARY_CONSUMER,
    REQUIRED_FIXTURE_CASES,
    validate_gate_case_record,
    validate_input_contract_record,
    validate_static_surface,
)


INPUT_CONTRACT_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
    "stage1_three_venue_canary_eligibility_input_contract.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/three_venue_canary_eligibility/"
    "synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _input_contract() -> dict:
    return copy.deepcopy(
        _fixture()["three_venue_canary_eligibility_input_contract_records"][0]
    )


def _case_by_fixture_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["three_venue_canary_eligibility_gate_case_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_three_venue_canary_eligibility_static_surface_validates_and_contains_required_cases():
    assert INPUT_CONTRACT_SCHEMA.exists()
    assert FIXTURE.exists()
    assert validate_static_surface(repo_root=Path(".")) == []

    fixture = _fixture()
    fixture_cases = {
        record["fixture_case"]
        for key in [
            "three_venue_canary_eligibility_input_contract_records",
            "three_venue_platform_readiness_matrix_records",
            "owner_review_to_canary_eligibility_handoff_records",
            "limited_live_canary_execution_block_records",
            "three_venue_canary_eligibility_gate_case_records",
        ]
        for record in fixture[key]
    }
    assert REQUIRED_FIXTURE_CASES.issubset(fixture_cases)


def test_input_contract_schema_requires_owner_review_owner_approval_and_three_platform_scope():
    schema = _load(INPUT_CONTRACT_SCHEMA)
    props = schema["properties"]
    required = set(schema["required"])

    assert schema["additionalProperties"] is False
    assert props["three_venue_canary_eligibility_input_contract_type"]["const"] == (
        INPUT_CONTRACT_TYPE
    )
    assert {
        "owner_live_promotion_review_gate_report_ref",
        "owner_approval_receipt_boundary_ref",
        "owner_live_promotion_review_pass_next_allowed_consumer",
        "owner_approval_receipt_required_before_canary_eligibility_flag",
        "owner_review_required_before_canary_eligibility_flag",
        "required_platform_scope_identities",
        "owner_live_promotion_review_auto_approval_allowed",
        "owner_live_promotion_review_auto_promotion_allowed",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
    }.issubset(required)
    assert props["owner_live_promotion_review_pass_next_allowed_consumer"]["const"] == (
        OWNER_REVIEW_TO_CANARY_CONSUMER
    )
    assert props["owner_approval_receipt_required_before_canary_eligibility_flag"]["const"] is True
    assert props["owner_review_required_before_canary_eligibility_flag"]["const"] is True
    assert props["owner_live_promotion_review_auto_approval_allowed"]["const"] is False
    assert props["owner_live_promotion_review_auto_promotion_allowed"]["const"] is False


def test_input_contract_requires_pr45_owner_review_and_approval_before_canary_gate():
    record = _input_contract()

    assert record["owner_live_promotion_review_gate_report_ref"]
    assert record["owner_live_promotion_review_gate_report_state"] == (
        "PRESENT_IMMUTABLE_PASS_THREE_VENUE_CANARY_ELIGIBILITY_REQUIRED"
    )
    assert record["owner_approval_receipt_boundary_ref"]
    assert record["owner_approval_receipt_boundary_state"] == "PRESENT_IMMUTABLE_REQUIRED"
    assert record["owner_live_promotion_review_pass_next_allowed_consumer"] == (
        OWNER_REVIEW_TO_CANARY_CONSUMER
    )
    assert record["required_platform_scope_identities"] == CANONICAL_PLATFORMS
    assert record["platform_specific_readiness_placeholder_only_flag"] is True
    assert record["real_platform_readiness_created_flag"] is False
    assert record["three_venue_canary_eligibility_created_flag"] is False
    assert validate_input_contract_record(record) == []


def test_input_contract_rejects_missing_owner_review_missing_owner_approval_stale_conflict_schema_target():
    record = _input_contract()
    record["owner_live_promotion_review_gate_report_ref"] = ""
    record["owner_approval_receipt_boundary_ref"] = ""
    record["owner_live_promotion_review_gate_report_state"] = "STALE"
    record["owner_review_freshness_state"] = "STALE"
    record["owner_approval_receipt_boundary_state"] = "MISSING"
    record["conflict_state"] = "CONFLICT_PRESENT"
    record["schema_state"] = "SCHEMA_ERROR"
    record["target_match_state"] = "MISMATCH"

    failures = validate_input_contract_record(record)

    for fragment in [
        "owner_live_promotion_review_gate_report_ref must be present",
        "owner_approval_receipt_boundary_ref must be present",
        "owner_live_promotion_review_gate_report_state must be",
        "owner_approval_receipt_boundary_state must be PRESENT_IMMUTABLE_REQUIRED",
        "owner_review_freshness_state must be FRESH",
        "conflict_state must be NO_CONFLICT",
        "schema_state must be SCHEMA_VALID",
        "target_match_state must be MATCH",
    ]:
        _assert_failure_contains(failures, fragment)


def test_gate_cases_block_missing_owner_review_approval_stale_superseded_conflict_schema_and_target():
    cases = _case_by_fixture_case()
    expected = {
        "BLOCKED_MISSING_OWNER_LIVE_PROMOTION_REVIEW_GATE_REPORT": (
            "BLOCKED_CANARY_ELIGIBILITY_OWNER_REVIEW_GATE_REPORT_MISSING"
        ),
        "BLOCKED_MISSING_OWNER_APPROVAL_RECEIPT_BOUNDARY": (
            "BLOCKED_CANARY_ELIGIBILITY_OWNER_APPROVAL_RECEIPT_BOUNDARY_MISSING"
        ),
        "BLOCKED_STALE_OWNER_REVIEW_REPORT": (
            "BLOCKED_CANARY_ELIGIBILITY_OWNER_REVIEW_REPORT_STALE"
        ),
        "BLOCKED_SUPERSEDED_OWNER_REVIEW_REPORT": (
            "BLOCKED_CANARY_ELIGIBILITY_OWNER_REVIEW_REPORT_SUPERSEDED"
        ),
        "BLOCKED_CONFLICT_STATE": "BLOCKED_CANARY_ELIGIBILITY_CONFLICT_STATE",
        "BLOCKED_SCHEMA_ERROR_STATE": "BLOCKED_CANARY_ELIGIBILITY_SCHEMA_ERROR",
        "BLOCKED_TARGET_MISMATCH": "BLOCKED_CANARY_ELIGIBILITY_TARGET_MISMATCH",
    }

    for fixture_case, expected_state in expected.items():
        record = cases[fixture_case]
        assert record["expected_gate_state"] == expected_state
        assert record["blocker_codes"]
        assert validate_gate_case_record(record) == []
