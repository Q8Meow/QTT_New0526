from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_concurrent_replay_paper_contract_check import (
    PAPER_LANE_TYPE,
    REPLAY_LANE_TYPE,
    validate_gate_case_record,
    validate_lane_contract_record,
)


REPLAY_LANE_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/replay_paper/"
    "concurrent_replay_lane_contract.schema.json"
)
PAPER_LANE_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/replay_paper/"
    "concurrent_paper_lane_contract.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/replay_paper/"
    "synthetic_concurrent_replay_paper_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _replay_lane() -> dict:
    return copy.deepcopy(_fixture()["replay_lane_contract_records"][0])


def _paper_lane() -> dict:
    return copy.deepcopy(_fixture()["paper_lane_contract_records"][0])


def _case_by_fixture_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["execution_gate_case_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_lane_schemas_are_closed_and_define_replay_paper_as_separate_non_sequential_lanes():
    replay_schema = _load(REPLAY_LANE_SCHEMA)
    paper_schema = _load(PAPER_LANE_SCHEMA)

    assert replay_schema["additionalProperties"] is False
    assert paper_schema["additionalProperties"] is False
    assert replay_schema["properties"]["replay_lane_contract_type"]["const"] == REPLAY_LANE_TYPE
    assert paper_schema["properties"]["paper_lane_contract_type"]["const"] == PAPER_LANE_TYPE
    assert replay_schema["properties"]["lane_type"]["const"] == "REPLAY"
    assert paper_schema["properties"]["lane_type"]["const"] == "PAPER"
    assert replay_schema["properties"]["replay_pass_starts_paper_flag"]["const"] is False
    assert paper_schema["properties"]["replay_pass_required_before_paper_flag"]["const"] is False
    assert replay_schema["properties"]["result_packet_merge_allowed_flag"]["const"] is False
    assert paper_schema["properties"]["result_packet_merge_allowed_flag"]["const"] is False
    assert replay_schema["properties"]["dual_result_review_allowed_flag"]["const"] is False
    assert paper_schema["properties"]["dual_result_review_allowed_flag"]["const"] is False


def test_replay_and_paper_lane_records_share_input_identity_but_do_not_merge_or_promote():
    replay = _replay_lane()
    paper = _paper_lane()

    assert replay["lane_type"] == "REPLAY"
    assert paper["lane_type"] == "PAPER"
    assert replay["shared_input_identity_id"] == paper["shared_input_identity_id"]
    assert replay["runtime_resolver_snapshot_id"] == paper["runtime_resolver_snapshot_id"]
    assert replay["replay_paper_input_identity_digest"] == paper["replay_paper_input_identity_digest"]
    assert replay["lane_start_policy"] == "SEPARATE_NON_SEQUENTIAL_LANE_AFTER_SHARED_INPUT_LOCK_ONLY"
    assert paper["lane_start_policy"] == "SEPARATE_NON_SEQUENTIAL_LANE_AFTER_SHARED_INPUT_LOCK_ONLY"
    assert replay["lane_execution_allowed_flag"] is False
    assert paper["lane_execution_allowed_flag"] is False
    assert replay["result_packet_merge_allowed_flag"] is False
    assert paper["result_packet_merge_allowed_flag"] is False
    assert replay["paper_pass_implies_live_eligibility_flag"] is False
    assert paper["paper_pass_implies_live_eligibility_flag"] is False
    assert validate_lane_contract_record(replay, lane_type="REPLAY") == []
    assert validate_lane_contract_record(paper, lane_type="PAPER") == []


def test_lane_contracts_reject_execution_sequential_merge_review_live_and_profit_claims():
    replay = _replay_lane()
    replay["replay_pass_starts_paper_flag"] = True
    replay["lane_execution_allowed_flag"] = True
    replay["result_packet_creation_allowed_flag"] = True
    replay["result_packet_merge_allowed_flag"] = True
    replay["dual_result_review_allowed_flag"] = True
    replay["owner_live_promotion_review_allowed_flag"] = True
    replay["live_reachability_allowed_flag"] = True
    replay["order_execution_allowed_flag"] = True
    replay["runtime_cash_claim_allowed_flag"] = True
    replay["profit_claim_allowed_flag"] = True
    replay["atomicrows_bundle_mutation_allowed_flag"] = True
    replay["blocker_reduction_claim_allowed_flag"] = True

    failures = validate_lane_contract_record(replay, lane_type="REPLAY")

    for fragment in [
        "replay_pass_starts_paper_flag",
        "lane_execution_allowed_flag",
        "result_packet_creation_allowed_flag",
        "result_packet_merge_allowed_flag",
        "dual_result_review_allowed_flag",
        "owner_live_promotion_review_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "atomicrows_bundle_mutation_allowed_flag",
        "blocker_reduction_claim_allowed_flag",
    ]:
        _assert_failure_contains(failures, fragment)


def test_gate_cases_block_replay_and_paper_execution_claims_independently():
    cases = _case_by_fixture_case()
    expected = {
        "BLOCKED_REPLAY_EXECUTION_CLAIM": "REPLAY_EXECUTION_AUTHORITY",
        "BLOCKED_PAPER_EXECUTION_CLAIM": "PAPER_EXECUTION_AUTHORITY",
    }

    for fixture_case, claim_type in expected.items():
        record = cases[fixture_case]
        assert record["claim_attempt_type"] == claim_type
        assert record["expected_gate_state"].startswith("BLOCKED_")
        assert record["blocker_codes"]
        assert validate_gate_case_record(record) == []
