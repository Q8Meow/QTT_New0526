from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_dual_result_review_contract_check import (
    COMPARISON_MATRIX_TYPE,
    build_report,
    validate_comparison_matrix_record,
    validate_gate_case_record,
)


COMPARISON_MATRIX_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/dual_result_review/"
    "stage1_replay_paper_comparison_matrix.schema.json"
)
GATE_REPORT_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/dual_result_review/"
    "stage1_dual_result_review_gate_report.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/dual_result_review/"
    "synthetic_stage1_dual_result_review_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _matrix() -> dict:
    return copy.deepcopy(_fixture()["replay_paper_comparison_matrix_records"][0])


def _case_by_fixture_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["dual_result_review_gate_case_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_comparison_matrix_schema_is_static_only_and_blocks_merge_live_order_profit():
    schema = _load(COMPARISON_MATRIX_SCHEMA)
    report_schema = _load(GATE_REPORT_SCHEMA)
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["comparison_matrix_type"]["const"] == COMPARISON_MATRIX_TYPE
    assert props["static_fields_only_flag"]["const"] is True
    assert props["compares_synthetic_boundary_refs_only_flag"]["const"] is True
    assert props["replay_paper_results_merged_flag"]["const"] is False
    assert props["combined_result_packet_created_flag"]["const"] is False
    assert props["live_eligibility_created_flag"]["const"] is False
    assert props["owner_promotion_readiness_created_flag"]["const"] is False
    assert props["order_authority_created_flag"]["const"] is False
    assert props["profit_claim_created_flag"]["const"] is False
    assert report_schema["properties"]["replay_paper_results_merged_flag"]["const"] is False
    assert report_schema["properties"]["dual_result_review_auto_promotion_allowed"]["const"] is False


def test_comparison_matrix_references_results_without_merging_or_mutating_lane_packets():
    record = _matrix()

    assert record["replay_result_packet_boundary_ref"] != record["paper_result_packet_boundary_ref"]
    assert record["static_fields_only_flag"] is True
    assert record["compares_synthetic_boundary_refs_only_flag"] is True
    assert record["negative_lane_metrics_preserved_flag"] is True
    assert record["replay_result_packet_mutated_flag"] is False
    assert record["paper_result_packet_mutated_flag"] is False
    assert record["replay_paper_results_merged_flag"] is False
    assert record["combined_result_packet_created_flag"] is False
    assert record["next_required_state"] == "OWNER_LIVE_PROMOTION_REVIEW_REQUIRED"
    assert validate_comparison_matrix_record(record) == []


def test_comparison_matrix_rejects_result_merge_direct_live_promotion_and_dropped_negative_metrics():
    record = _matrix()
    record["replay_result_packet_mutated_flag"] = True
    record["paper_result_packet_mutated_flag"] = True
    record["replay_paper_results_merged_flag"] = True
    record["combined_result_packet_created_flag"] = True
    record["direct_live_promotion_claimed_flag"] = True
    record["live_eligibility_created_flag"] = True
    record["owner_promotion_readiness_created_flag"] = True
    record["order_authority_created_flag"] = True
    record["runtime_cash_claim_created_flag"] = True
    record["profit_claim_created_flag"] = True
    record["metric_pair_records"][0]["metric_merge_allowed_flag"] = True
    record["metric_pair_records"][0]["metric_average_for_promotion_allowed_flag"] = True
    record["metric_pair_records"][0]["negative_lane_metric_drop_allowed_flag"] = True

    failures = validate_comparison_matrix_record(record)

    for fragment in [
        "replay_result_packet_mutated_flag",
        "paper_result_packet_mutated_flag",
        "replay_paper_results_merged_flag",
        "combined_result_packet_created_flag",
        "direct_live_promotion_claimed_flag",
        "live_eligibility_created_flag",
        "owner_promotion_readiness_created_flag",
        "order_authority_created_flag",
        "runtime_cash_claim_created_flag",
        "profit_claim_created_flag",
        "metric_merge_allowed_flag",
        "metric_average_for_promotion_allowed_flag",
        "negative_lane_metric_drop_allowed_flag",
    ]:
        _assert_failure_contains(failures, fragment)


def test_gate_cases_block_result_merge_and_dual_result_review_decision_claims():
    cases = _case_by_fixture_case()
    expected = {
        "BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM": "REPLAY_PAPER_RESULT_MERGE",
        "BLOCKED_DUAL_RESULT_REVIEW_DECISION_CLAIM": "DUAL_RESULT_REVIEW_DECISION",
    }

    for fixture_case, claim_type in expected.items():
        record = cases[fixture_case]
        assert record["claim_attempt_type"] == claim_type
        assert record["expected_gate_state"].startswith("BLOCKED_DUAL_REVIEW")
        assert validate_gate_case_record(record) == []


def test_gate_report_preserves_separate_results_and_no_merge_authority():
    report = build_report(fixture=_fixture(), repo_root=Path("."), validation_failures=[])

    assert report["gate_state"] == (
        "STATIC_DUAL_RESULT_REVIEW_CONTRACT_VALIDATED_NO_RUNTIME_AUTHORITY"
    )
    assert report["replay_result_packet_created_flag"] is False
    assert report["paper_result_packet_created_flag"] is False
    assert report["replay_paper_results_merged_flag"] is False
    assert report["dual_result_review_decision_created_flag"] is False
    assert report["owner_live_promotion_review_created_flag"] is False
