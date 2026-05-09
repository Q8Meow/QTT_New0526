from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_runtime_resolver_to_replay_paper_handoff_check import (
    validate_handoff_case_record,
    validate_handoff_record,
)


FIXTURE = Path(
    "tests/fixtures/source_evidence/runtime_resolver_snapshot/"
    "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _valid_handoff() -> dict:
    return copy.deepcopy(_fixture()["valid_handoff_record"])


def _case_by_fixture_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["handoff_case_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_handoff_fixture_blocks_execution_result_live_order_cash_profit_atomicrows_and_blocker_reduction_claims():
    cases = _case_by_fixture_case()
    expected = {
        "BLOCKED_REPLAY_PAPER_EXECUTION_CLAIM": "REPLAY_PAPER_EXECUTION_AUTHORITY",
        "BLOCKED_REPLAY_PAPER_RESULT_PACKET_CLAIM": "REPLAY_PAPER_RESULT_PACKET_CREATION",
        "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM": "LIVE_ORDER_RUNTIME_CASH_PROFIT",
        "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM": "ATOMICROWS_BUNDLE_HASH_MUTATION",
        "BLOCKED_BLOCKER_REDUCTION_CLAIM": "BLOCKER_REDUCTION",
    }

    for fixture_case, claim_type in expected.items():
        record = cases[fixture_case]
        assert record["claim_attempt_type"] == claim_type
        assert record["expected_handoff_state"].startswith("BLOCKED_")
        assert record["blocker_codes"]
        assert validate_handoff_case_record(record) == []


def test_handoff_fixture_blocks_missing_stale_conflict_target_mismatch_digest_and_schema_states():
    cases = _case_by_fixture_case()
    expected_states = {
        "BLOCKED_STALE_SNAPSHOT": "BLOCKED_STALE_SNAPSHOT",
        "BLOCKED_STALE_INPUT_LOCK": "BLOCKED_STALE_INPUT_LOCK",
        "BLOCKED_SUPERSEDED_SNAPSHOT": "BLOCKED_SUPERSEDED_SNAPSHOT",
        "BLOCKED_CONFLICT_STATE": "BLOCKED_CONFLICT_STATE",
        "BLOCKED_TARGET_MISMATCH": "BLOCKED_TARGET_MISMATCH",
        "BLOCKED_DIGEST_MISMATCH": "BLOCKED_DIGEST_MISMATCH",
        "BLOCKED_MISSING_SNAPSHOT_PACKET": "BLOCKED_SNAPSHOT_PACKET_MISSING",
        "BLOCKED_MISSING_SNAPSHOT_GATE_REPORT": "BLOCKED_SNAPSHOT_GATE_REPORT_MISSING",
        "BLOCKED_MISSING_INPUT_LOCK": "BLOCKED_INPUT_LOCK_MISSING",
        "BLOCKED_MISSING_CONSUMER_ALLOWLIST": "BLOCKED_CONSUMER_ALLOWLIST_MISSING",
        "BLOCKED_SCHEMA_ERROR": "BLOCKED_SCHEMA_ERROR",
    }

    for fixture_case, expected_state in expected_states.items():
        record = cases[fixture_case]
        assert record["expected_handoff_state"] == expected_state
        assert record["blocker_codes"]
        assert validate_handoff_case_record(record) == []


def test_handoff_rejects_replay_paper_execution_result_dual_review_and_live_authority_flags():
    record = _valid_handoff()
    flags = record["handoff_boundary_flags"]
    flags["replay_paper_execution_authority_allowed_flag"] = True
    flags["replay_paper_result_packet_creation_allowed_flag"] = True
    flags["dual_result_review_creation_allowed_flag"] = True
    flags["live_reachability_allowed_flag"] = True
    flags["order_execution_allowed_flag"] = True
    flags["runtime_cash_claim_allowed_flag"] = True
    flags["profit_claim_allowed_flag"] = True
    record["no_claim_flags"]["executes_replay_or_paper"] = True
    record["no_claim_flags"]["creates_dual_result_review"] = True

    failures = validate_handoff_record(record)

    for fragment in [
        "replay_paper_execution_authority_allowed_flag",
        "replay_paper_result_packet_creation_allowed_flag",
        "dual_result_review_creation_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "executes_replay_or_paper",
        "creates_dual_result_review",
    ]:
        _assert_failure_contains(failures, fragment)


def test_handoff_rejects_snapshot_mutation_new_market_selection_atomicrows_and_blocker_reduction():
    record = _valid_handoff()
    flags = record["handoff_boundary_flags"]
    flags["runtime_resolver_snapshot_mutation_allowed_flag"] = True
    flags["new_contract_event_market_selection_allowed_flag"] = True
    flags["atomicrows_bundle_mutation_allowed_flag"] = True
    flags["blocker_reduction_claim_allowed_flag"] = True
    flags["source_fact_acceptance_allowed_flag"] = True
    flags["connector_semantic_population_allowed_flag"] = True
    flags["network_io_allowed_flag"] = True
    flags["live_client_import_allowed_flag"] = True
    record["no_claim_flags"]["creates_atomicrows_bundle_or_hash"] = True
    record["no_claim_flags"]["reduces_blockers"] = True

    failures = validate_handoff_record(record)

    for fragment in [
        "runtime_resolver_snapshot_mutation_allowed_flag",
        "new_contract_event_market_selection_allowed_flag",
        "atomicrows_bundle_mutation_allowed_flag",
        "blocker_reduction_claim_allowed_flag",
        "source_fact_acceptance_allowed_flag",
        "connector_semantic_population_allowed_flag",
        "network_io_allowed_flag",
        "live_client_import_allowed_flag",
        "creates_atomicrows_bundle_or_hash",
        "reduces_blockers",
    ]:
        _assert_failure_contains(failures, fragment)


def test_handoff_rejects_missing_references_and_non_green_states_for_ready_handoff():
    record = _valid_handoff()
    record["runtime_resolver_snapshot_packet_reference"]["freshness_state"] = "STALE"
    record["runtime_resolver_snapshot_input_lock_reference"]["input_lock_id"] = ""
    record["runtime_resolver_snapshot_gate_report_reference"]["gate_state"] = "MISSING"
    record["runtime_resolver_snapshot_consumer_allowlist_reference"]["allowlist_state"] = "MISSING"

    failures = validate_handoff_record(record)

    _assert_failure_contains(failures, "snapshot.freshness_state")
    _assert_failure_contains(failures, "input_lock_id")
    _assert_failure_contains(failures, "gate.gate_state")
    _assert_failure_contains(failures, "allowlist.allowlist_state")
