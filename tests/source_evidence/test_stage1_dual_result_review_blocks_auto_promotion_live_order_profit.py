from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_dual_result_review_contract_check import (
    OWNER_REVIEW_ONLY_CONSUMER,
    build_report,
    validate_gate_case_record,
    validate_handoff_block_record,
    validate_input_contract_record,
)


HANDOFF_BLOCK_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/dual_result_review/"
    "stage1_owner_live_promotion_handoff_block.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/dual_result_review/"
    "synthetic_stage1_dual_result_review_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _input_contract() -> dict:
    return copy.deepcopy(_fixture()["dual_result_review_input_contract_records"][0])


def _handoff_block() -> dict:
    return copy.deepcopy(_fixture()["owner_live_promotion_handoff_block_records"][0])


def _case_by_fixture_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["dual_result_review_gate_case_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_owner_live_promotion_handoff_block_schema_allows_only_later_owner_review_input():
    schema = _load(HANDOFF_BLOCK_SCHEMA)
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["dual_result_review_pass_next_allowed_consumer"]["const"] == (
        OWNER_REVIEW_ONLY_CONSUMER
    )
    assert props["dual_result_review_direct_live_consumer_allowed"]["const"] is False
    assert props["dual_result_review_direct_order_router_allowed"]["const"] is False
    assert props["dual_result_review_direct_canary_allowed"]["const"] is False
    assert props["dual_result_review_auto_promotion_allowed"]["const"] is False
    assert props["owner_review_required_before_live_eligibility"]["const"] is True
    assert props["owner_live_promotion_review_created_flag"]["const"] is False
    assert props["owner_approval_receipt_created_flag"]["const"] is False


def test_handoff_block_routes_to_owner_review_only_without_creating_owner_review_or_live_authority():
    record = _handoff_block()

    assert record["dual_result_review_pass_next_allowed_consumer"] == (
        OWNER_REVIEW_ONLY_CONSUMER
    )
    assert record["dual_result_review_direct_live_consumer_allowed"] is False
    assert record["dual_result_review_direct_order_router_allowed"] is False
    assert record["dual_result_review_direct_canary_allowed"] is False
    assert record["dual_result_review_auto_promotion_allowed"] is False
    assert record["owner_review_required_before_live_eligibility"] is True
    assert record["owner_live_promotion_review_created_flag"] is False
    assert record["owner_approval_receipt_created_flag"] is False
    assert record["live_eligibility_created_flag"] is False
    assert record["order_authority_created_flag"] is False
    assert validate_handoff_block_record(record) == []


def test_handoff_block_rejects_auto_promotion_owner_approval_live_order_cash_and_profit_claims():
    record = _handoff_block()
    record["dual_result_review_direct_live_consumer_allowed"] = True
    record["dual_result_review_direct_order_router_allowed"] = True
    record["dual_result_review_direct_canary_allowed"] = True
    record["dual_result_review_auto_promotion_allowed"] = True
    record["owner_live_promotion_review_created_flag"] = True
    record["owner_approval_receipt_created_flag"] = True
    record["live_eligibility_created_flag"] = True
    record["live_reachability_created_flag"] = True
    record["order_authority_created_flag"] = True
    record["runtime_cash_claim_created_flag"] = True
    record["profit_claim_created_flag"] = True

    failures = validate_handoff_block_record(record)

    for fragment in [
        "dual_result_review_direct_live_consumer_allowed",
        "dual_result_review_direct_order_router_allowed",
        "dual_result_review_direct_canary_allowed",
        "dual_result_review_auto_promotion_allowed",
        "owner_live_promotion_review_created_flag",
        "owner_approval_receipt_created_flag",
        "live_eligibility_created_flag",
        "live_reachability_created_flag",
        "order_authority_created_flag",
        "runtime_cash_claim_created_flag",
        "profit_claim_created_flag",
    ]:
        _assert_failure_contains(failures, fragment)


def test_input_contract_rejects_review_decision_owner_live_order_runtime_cash_atomicrows_and_profit_claims():
    record = _input_contract()
    record["review_decision_created_flag"] = True
    record["result_merge_created_flag"] = True
    record["auto_promotion_allowed_flag"] = True
    record["owner_live_promotion_review_created_flag"] = True
    record["owner_approval_receipt_created_flag"] = True
    record["live_reachability_created_flag"] = True
    record["order_authority_created_flag"] = True
    record["runtime_cash_claim_created_flag"] = True
    record["atomicrows_bundle_hash_created_or_mutated_flag"] = True
    record["blocker_reduction_claim_created_flag"] = True
    record["profit_evidence_created_flag"] = True

    failures = validate_input_contract_record(record)

    for fragment in [
        "review_decision_created_flag",
        "result_merge_created_flag",
        "auto_promotion_allowed_flag",
        "owner_live_promotion_review_created_flag",
        "owner_approval_receipt_created_flag",
        "live_reachability_created_flag",
        "order_authority_created_flag",
        "runtime_cash_claim_created_flag",
        "atomicrows_bundle_hash_created_or_mutated_flag",
        "blocker_reduction_claim_created_flag",
        "profit_evidence_created_flag",
    ]:
        _assert_failure_contains(failures, fragment)


def test_gate_cases_block_auto_promotion_owner_review_owner_approval_live_atomicrows_and_blocker_reduction():
    cases = _case_by_fixture_case()
    expected = {
        "BLOCKED_AUTO_PROMOTION_CLAIM": "AUTO_PROMOTION",
        "BLOCKED_OWNER_LIVE_PROMOTION_REVIEW_CREATION": "OWNER_LIVE_PROMOTION_REVIEW_CREATION",
        "BLOCKED_OWNER_APPROVAL_RECEIPT_CREATION": "OWNER_APPROVAL_RECEIPT",
        "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM": "LIVE_ORDER_RUNTIME_CASH_PROFIT",
        "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM": "ATOMICROWS_BUNDLE_HASH_MUTATION",
        "BLOCKED_BLOCKER_REDUCTION_CLAIM": "BLOCKER_REDUCTION",
    }

    for fixture_case, claim_type in expected.items():
        record = cases[fixture_case]
        assert record["claim_attempt_type"] == claim_type
        assert record["expected_gate_state"].startswith("BLOCKED_DUAL_REVIEW")
        assert validate_gate_case_record(record) == []


def test_gate_report_cannot_auto_promote_to_live_order_or_profit_authority():
    report = build_report(fixture=_fixture(), repo_root=Path("."), validation_failures=[])

    assert report["dual_result_review_pass_next_allowed_consumer"] == (
        OWNER_REVIEW_ONLY_CONSUMER
    )
    assert report["dual_result_review_direct_live_consumer_allowed"] is False
    assert report["dual_result_review_direct_order_router_allowed"] is False
    assert report["dual_result_review_direct_canary_allowed"] is False
    assert report["dual_result_review_auto_promotion_allowed"] is False
    assert report["owner_review_required_before_live_eligibility"] is True
    assert report["owner_live_promotion_review_created_flag"] is False
    assert report["owner_approval_receipt_created_flag"] is False
    assert report["live_eligibility_created_flag"] is False
    assert report["live_reachability_created_flag"] is False
    assert report["order_authority_created_flag"] is False
    assert report["runtime_cash_claim_created_flag"] is False
    assert report["atomicrows_bundle_hash_created_or_mutated_flag"] is False
    assert report["blocker_reduction_claim_created_flag"] is False
    assert report["profit_evidence_created_flag"] is False
