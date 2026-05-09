from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_three_venue_canary_eligibility_contract_check import (
    EXECUTION_BLOCK_TYPE,
    HANDOFF_TYPE,
    LIMITED_LIVE_BOUNDARY_CONSUMER,
    OWNER_REVIEW_TO_CANARY_CONSUMER,
    build_report,
    validate_execution_block_record,
    validate_gate_case_record,
    validate_handoff_record,
    validate_input_contract_record,
)


HANDOFF_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
    "stage1_owner_review_to_canary_eligibility_handoff.schema.json"
)
EXECUTION_BLOCK_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
    "stage1_limited_live_canary_execution_block.schema.json"
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


def _handoff() -> dict:
    return copy.deepcopy(_fixture()["owner_review_to_canary_eligibility_handoff_records"][0])


def _execution_block() -> dict:
    return copy.deepcopy(_fixture()["limited_live_canary_execution_block_records"][0])


def _case_by_fixture_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["three_venue_canary_eligibility_gate_case_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_handoff_schema_routes_owner_review_to_canary_gate_only_and_execution_boundary_later():
    schema = _load(HANDOFF_SCHEMA)
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["owner_review_to_canary_eligibility_handoff_type"]["const"] == HANDOFF_TYPE
    assert props["owner_live_promotion_review_pass_next_allowed_consumer"]["const"] == (
        OWNER_REVIEW_TO_CANARY_CONSUMER
    )
    assert props["three_venue_canary_eligibility_green_next_allowed_consumer"]["const"] == (
        LIMITED_LIVE_BOUNDARY_CONSUMER
    )
    assert props["direct_limited_live_canary_execution_allowed_flag"]["const"] is False
    assert props["direct_live_order_router_allowed_flag"]["const"] is False
    assert props["direct_live_arbitrage_allowed_flag"]["const"] is False
    assert props["direct_full_scaled_live_allowed_flag"]["const"] is False
    assert props["canary_execution_receipt_created_flag"]["const"] is False


def test_handoff_record_only_allows_static_blocked_readiness_report_scaffolding():
    record = _handoff()

    assert record["owner_live_promotion_review_pass_next_allowed_consumer"] == (
        OWNER_REVIEW_TO_CANARY_CONSUMER
    )
    assert record["three_venue_canary_eligibility_green_next_allowed_consumer"] == (
        LIMITED_LIVE_BOUNDARY_CONSUMER
    )
    assert record["canary_eligibility_gate_output_scope"] == (
        "STATIC_BLOCKED_READINESS_REPORTS_ONLY"
    )
    assert record["canary_eligibility_gate_may_only_produce_static_blocked_readiness_reports_flag"] is True
    assert record["three_venue_canary_eligibility_green_flag"] is False
    assert record["limited_live_canary_execution_created_flag"] is False
    assert record["canary_execution_receipt_created_flag"] is False
    assert validate_handoff_record(record) == []


def test_limited_live_canary_execution_block_schema_and_record_keep_all_execution_flags_false():
    schema = _load(EXECUTION_BLOCK_SCHEMA)
    props = schema["properties"]
    record = _execution_block()

    assert props["limited_live_canary_execution_block_type"]["const"] == EXECUTION_BLOCK_TYPE
    for field in [
        "limited_live_canary_execution_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "canary_execution_receipt_created_flag",
    ]:
        assert props[field]["const"] is False
        assert record[field] is False
    assert record["blocker_codes"]
    assert record["receipt_ids"]
    assert validate_execution_block_record(record) == []


def test_input_handoff_and_execution_block_reject_canary_live_order_cash_profit_atomicrows_and_blocker_claims():
    input_record = _input_contract()
    input_record["three_venue_canary_eligibility_allowed_flag"] = True
    input_record["three_venue_canary_eligibility_created_flag"] = True
    input_record["three_venue_canary_eligibility_green_flag"] = True
    input_record["limited_live_canary_execution_created_flag"] = True
    input_record["direct_limited_live_canary_execution_allowed_flag"] = True
    input_record["direct_live_order_router_allowed_flag"] = True
    input_record["direct_live_arbitrage_allowed_flag"] = True
    input_record["direct_full_scaled_live_allowed_flag"] = True
    input_record["direct_canary_execution_claimed_flag"] = True
    input_record["canary_execution_receipt_created_flag"] = True
    input_record["live_reachability_allowed_flag"] = True
    input_record["order_execution_allowed_flag"] = True
    input_record["runtime_cash_claim_allowed_flag"] = True
    input_record["atomicrows_bundle_hash_created_or_mutated_flag"] = True
    input_record["blocker_reduction_claim_created_flag"] = True
    input_record["profit_claim_allowed_flag"] = True

    failures = validate_input_contract_record(input_record)
    for fragment in [
        "three_venue_canary_eligibility_allowed_flag",
        "three_venue_canary_eligibility_created_flag",
        "three_venue_canary_eligibility_green_flag",
        "limited_live_canary_execution_created_flag",
        "direct_limited_live_canary_execution_allowed_flag",
        "direct_live_order_router_allowed_flag",
        "direct_live_arbitrage_allowed_flag",
        "direct_full_scaled_live_allowed_flag",
        "direct_canary_execution_claimed_flag",
        "canary_execution_receipt_created_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "atomicrows_bundle_hash_created_or_mutated_flag",
        "blocker_reduction_claim_created_flag",
        "profit_claim_allowed_flag",
    ]:
        _assert_failure_contains(failures, fragment)

    handoff = _handoff()
    handoff["direct_limited_live_canary_execution_allowed_flag"] = True
    handoff["direct_live_order_router_allowed_flag"] = True
    handoff["direct_live_arbitrage_allowed_flag"] = True
    handoff["direct_full_scaled_live_allowed_flag"] = True
    handoff["canary_execution_receipt_created_flag"] = True
    handoff["order_execution_allowed_flag"] = True
    handoff["runtime_cash_claim_allowed_flag"] = True
    handoff["profit_claim_allowed_flag"] = True
    failures = validate_handoff_record(handoff)
    for fragment in [
        "direct_limited_live_canary_execution_allowed_flag",
        "direct_live_order_router_allowed_flag",
        "direct_live_arbitrage_allowed_flag",
        "direct_full_scaled_live_allowed_flag",
        "canary_execution_receipt_created_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
    ]:
        _assert_failure_contains(failures, fragment)

    block = _execution_block()
    block["limited_live_canary_execution_allowed_flag"] = True
    block["live_reachability_allowed_flag"] = True
    block["order_execution_allowed_flag"] = True
    block["runtime_cash_claim_allowed_flag"] = True
    block["profit_claim_allowed_flag"] = True
    block["canary_execution_receipt_created_flag"] = True
    block["atomicrows_bundle_hash_created_or_mutated_flag"] = True
    block["blocker_reduction_claim_allowed_flag"] = True
    failures = validate_execution_block_record(block)
    for fragment in [
        "limited_live_canary_execution_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "canary_execution_receipt_created_flag",
        "atomicrows_bundle_hash_created_or_mutated_flag",
        "blocker_reduction_claim_allowed_flag",
    ]:
        _assert_failure_contains(failures, fragment)


def test_gate_cases_block_canary_execution_live_reachability_order_cash_profit_atomicrows_and_blocker_reduction():
    cases = _case_by_fixture_case()
    expected = {
        "BLOCKED_DIRECT_CANARY_EXECUTION_CLAIM": "DIRECT_CANARY_EXECUTION",
        "BLOCKED_LIVE_REACHABILITY_CLAIM": "LIVE_REACHABILITY",
        "BLOCKED_ORDER_EXECUTION_CLAIM": "ORDER_EXECUTION",
        "BLOCKED_RUNTIME_CASH_PROFIT_CLAIM": "RUNTIME_CASH_PROFIT",
        "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM": "ATOMICROWS_BUNDLE_HASH_MUTATION",
        "BLOCKED_BLOCKER_REDUCTION_CLAIM": "BLOCKER_REDUCTION",
    }

    for fixture_case, claim_type in expected.items():
        record = cases[fixture_case]
        assert record["claim_attempt_type"] == claim_type
        assert record["expected_gate_state"].startswith("BLOCKED_CANARY_ELIGIBILITY")
        assert validate_gate_case_record(record) == []


def test_gate_report_blocks_canary_execution_live_order_cash_atomicrows_blocker_and_profit():
    report = build_report(fixture=_fixture(), repo_root=Path("."), validation_failures=[])

    assert report["gate_state"] == (
        "STATIC_THREE_VENUE_CANARY_ELIGIBILITY_CONTRACT_VALIDATED_NO_RUNTIME_AUTHORITY"
    )
    assert report["owner_live_promotion_review_pass_next_allowed_consumer"] == (
        OWNER_REVIEW_TO_CANARY_CONSUMER
    )
    assert report["three_venue_canary_eligibility_green_next_allowed_consumer"] == (
        LIMITED_LIVE_BOUNDARY_CONSUMER
    )
    assert report["three_venue_canary_eligibility_created_flag"] is False
    assert report["three_venue_canary_eligibility_green_flag"] is False
    assert report["limited_live_canary_execution_allowed_flag"] is False
    assert report["limited_live_canary_execution_created_flag"] is False
    assert report["canary_execution_receipt_created_flag"] is False
    assert report["live_reachability_allowed_flag"] is False
    assert report["order_execution_allowed_flag"] is False
    assert report["runtime_cash_claim_allowed_flag"] is False
    assert report["atomicrows_bundle_hash_created_or_mutated_flag"] is False
    assert report["blocker_reduction_claim_created_flag"] is False
    assert report["profit_claim_allowed_flag"] is False
