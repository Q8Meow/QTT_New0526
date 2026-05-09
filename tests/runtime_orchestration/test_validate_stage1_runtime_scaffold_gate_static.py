import copy
import json
from pathlib import Path

import pytest

from tools.validate_stage1_runtime_scaffold_gate_static import (
    CANONICAL_BUNDLE_RELATIVE_PATH,
    CANONICAL_BUNDLE_SHA_RELATIVE_PATH,
    FORBIDDEN_ACTION_FLAGS,
    NO_CLAIM_FLAGS,
    validate_stage1_runtime_scaffold_gate_fixture,
    validate_static_surface,
)


SCHEMA_PATH = Path(
    "schemas/runtime_orchestration/stage1_runtime_scaffold_gate.schema.json"
)
FIXTURE_PATH = Path(
    "tests/fixtures/runtime_orchestration/"
    "synthetic_stage1_runtime_scaffold_gate_blocked.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _validate_fixture(fixture: dict, repo_root: Path = Path(".")) -> list[str]:
    return validate_stage1_runtime_scaffold_gate_fixture(
        fixture,
        repo_root=repo_root,
    )


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _canonical_bundle_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_RELATIVE_PATH.parts)


def _canonical_bundle_sha_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_SHA_RELATIVE_PATH.parts)


def test_valid_static_blocked_fixture_passes():
    assert (
        validate_static_surface(
            schema_path=SCHEMA_PATH,
            fixture_path=FIXTURE_PATH,
            repo_root=Path("."),
        )
        == []
    )


def test_missing_static_scaffold_authority_fails():
    fixture = _fixture()
    fixture["gate_authority"]["scaffold_only"] = False

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "scaffold_only")


def test_missing_connector_scaffold_source_required_gate_receipt_requirement_fails():
    fixture = _fixture()
    fixture["prerequisite_receipts"][
        "connector_scaffold_source_required_gate_receipt_required"
    ] = False

    failures = _validate_fixture(fixture)

    _assert_failure_contains(
        failures,
        "connector_scaffold_source_required_gate_receipt_required",
    )


def test_missing_venue_neutral_prediction_adapter_gate_receipt_requirement_fails():
    fixture = _fixture()
    fixture["prerequisite_receipts"][
        "venue_neutral_prediction_adapter_gate_receipt_required"
    ] = False

    failures = _validate_fixture(fixture)

    _assert_failure_contains(
        failures,
        "venue_neutral_prediction_adapter_gate_receipt_required",
    )


def test_missing_stage1_packet_schema_gate_receipt_requirement_fails():
    fixture = _fixture()
    fixture["prerequisite_receipts"]["stage1_packet_schema_gate_receipt_required"] = (
        False
    )

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "stage1_packet_schema_gate_receipt_required")


def test_missing_source_evidence_gate_confirmation_receipt_requirement_fails():
    fixture = _fixture()
    fixture["prerequisite_receipts"][
        "source_evidence_gate_confirmation_receipt_required"
    ] = False

    failures = _validate_fixture(fixture)

    _assert_failure_contains(
        failures,
        "source_evidence_gate_confirmation_receipt_required",
    )


@pytest.mark.parametrize(
    "policy_flag,forbidden_flag,no_claim_flag",
    [
        (
            "exact_market_selection_claimed",
            "exact_market_selection_enabled",
            "selects_exact_markets",
        ),
        (
            "exact_contract_selection_claimed",
            "exact_contract_selection_enabled",
            "selects_exact_contracts",
        ),
        (
            "exact_event_selection_claimed",
            "exact_event_selection_enabled",
            "selects_exact_events",
        ),
        (
            "exact_live_venue_selection_claimed",
            "exact_live_venue_selection_enabled",
            "selects_live_venues",
        ),
    ],
)
def test_exact_market_contract_event_or_venue_selection_claim_fails(
    policy_flag,
    forbidden_flag,
    no_claim_flag,
):
    fixture = _fixture()
    fixture["resolver_policy"][policy_flag] = True
    fixture["forbidden_action_flags"][forbidden_flag] = True
    fixture["no_claim_flags"][no_claim_flag] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, policy_flag)
    _assert_failure_contains(failures, forbidden_flag)
    _assert_failure_contains(failures, no_claim_flag)


def test_runtime_resolver_snapshot_emission_claim_fails():
    fixture = _fixture()
    fixture["resolver_policy"]["runtime_resolver_snapshot_emission_allowed"] = True
    fixture["resolver_policy"]["runtime_resolver_snapshot_created"] = True
    fixture["resolver_policy"]["runtime_resolver_snapshot_creation_claimed"] = True
    fixture["forbidden_action_flags"][
        "runtime_resolver_snapshot_emission_enabled"
    ] = True
    fixture["forbidden_action_flags"][
        "runtime_resolver_snapshot_creation_enabled"
    ] = True
    fixture["no_claim_flags"]["emits_runtime_resolver_snapshots"] = True
    fixture["no_claim_flags"]["creates_runtime_resolver_snapshots"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "runtime_resolver_snapshot_emission_allowed")
    _assert_failure_contains(failures, "runtime_resolver_snapshot_created")


def test_replay_execution_claim_fails():
    fixture = _fixture()
    fixture["replay_paper_policy"]["replay_execution_claimed"] = True
    fixture["forbidden_action_flags"]["replay_execution_enabled"] = True
    fixture["no_claim_flags"]["executes_replay"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "replay_execution_claimed")
    _assert_failure_contains(failures, "replay_execution_enabled")


def test_paper_execution_claim_fails():
    fixture = _fixture()
    fixture["replay_paper_policy"]["paper_execution_claimed"] = True
    fixture["forbidden_action_flags"]["paper_execution_enabled"] = True
    fixture["no_claim_flags"]["executes_paper"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "paper_execution_claimed")
    _assert_failure_contains(failures, "paper_execution_enabled")


def test_replay_paper_result_creation_claim_fails():
    fixture = _fixture()
    fixture["replay_paper_policy"]["runtime_replay_result_packet_created"] = True
    fixture["replay_paper_policy"]["runtime_paper_result_packet_created"] = True
    fixture["replay_paper_policy"]["replay_paper_result_creation_allowed"] = True
    fixture["forbidden_action_flags"][
        "runtime_replay_result_packet_creation_enabled"
    ] = True
    fixture["forbidden_action_flags"][
        "runtime_paper_result_packet_creation_enabled"
    ] = True
    fixture["forbidden_action_flags"]["replay_paper_result_creation_enabled"] = True
    fixture["no_claim_flags"]["creates_runtime_replay_result_packets"] = True
    fixture["no_claim_flags"]["creates_runtime_paper_result_packets"] = True
    fixture["no_claim_flags"]["creates_replay_paper_results"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "runtime_replay_result_packet_created")
    _assert_failure_contains(failures, "runtime_paper_result_packet_created")
    _assert_failure_contains(failures, "replay_paper_result_creation_allowed")


def test_replay_paper_merge_permission_fails():
    fixture = _fixture()
    fixture["replay_paper_policy"]["replay_paper_merge_allowed"] = True
    fixture["replay_paper_policy"]["replay_paper_merge_claimed"] = True
    fixture["forbidden_action_flags"]["replay_paper_merge_enabled"] = True
    fixture["no_claim_flags"]["merges_replay_and_paper_results"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "replay_paper_merge_allowed")
    _assert_failure_contains(failures, "replay_paper_merge_claimed")


def test_dual_result_decision_permission_fails():
    fixture = _fixture()
    fixture["replay_paper_policy"]["dual_result_review_decision_allowed"] = True
    fixture["replay_paper_policy"]["dual_result_review_decision_created"] = True
    fixture["forbidden_action_flags"]["dual_result_review_decision_enabled"] = True
    fixture["no_claim_flags"]["creates_dual_result_review_decisions"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "dual_result_review_decision_allowed")
    _assert_failure_contains(failures, "dual_result_review_decision_created")


def test_live_arbitrage_enablement_claim_fails():
    fixture = _fixture()
    fixture["arbitrage_policy"]["live_arbitrage_enabled"] = True
    fixture["arbitrage_policy"]["live_arbitrage_enablement_claimed"] = True
    fixture["forbidden_action_flags"]["live_arbitrage_enabled"] = True
    fixture["no_claim_flags"]["enables_live_arbitrage"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "live_arbitrage_enabled")
    _assert_failure_contains(failures, "live_arbitrage_enablement_claimed")


def test_cross_venue_order_write_permission_fails():
    fixture = _fixture()
    fixture["arbitrage_policy"]["cross_venue_order_routing_allowed"] = True
    fixture["arbitrage_policy"]["cross_venue_order_write_allowed"] = True
    fixture["arbitrage_policy"]["cross_venue_order_write_permission_claimed"] = True
    fixture["order_authority_policy"]["cross_venue_order_write_allowed"] = True
    fixture["forbidden_action_flags"]["cross_venue_order_routing_enabled"] = True
    fixture["forbidden_action_flags"]["cross_venue_order_write_enabled"] = True
    fixture["no_claim_flags"]["permits_cross_venue_order_routing"] = True
    fixture["no_claim_flags"]["permits_cross_venue_order_writes"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "cross_venue_order_routing_allowed")
    _assert_failure_contains(failures, "cross_venue_order_write_allowed")


def test_dashboard_active_run_mutation_claim_fails():
    fixture = _fixture()
    fixture["dashboard_policy"]["active_run_mutation_allowed"] = True
    fixture["dashboard_policy"]["active_run_mutation_claimed"] = True
    fixture["forbidden_action_flags"]["dashboard_active_run_mutation_enabled"] = True
    fixture["no_claim_flags"]["mutates_dashboard_active_runs"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "active_run_mutation_allowed")
    _assert_failure_contains(failures, "active_run_mutation_claimed")


def test_live_effective_value_mutation_claim_fails():
    fixture = _fixture()
    fixture["dashboard_policy"]["live_effective_value_mutation_allowed"] = True
    fixture["dashboard_policy"]["live_effective_value_mutation_claimed"] = True
    fixture["forbidden_action_flags"]["live_effective_value_mutation_enabled"] = True
    fixture["no_claim_flags"]["mutates_live_effective_values"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "live_effective_value_mutation_allowed")
    _assert_failure_contains(failures, "live_effective_value_mutation_claimed")


@pytest.mark.parametrize(
    "policy_allowed,policy_claimed,forbidden_flag,no_claim_flag",
    [
        (
            "observed_fact_rewrite_allowed",
            "observed_fact_rewrite_claimed",
            "observed_fact_rewrite_enabled",
            "rewrites_observed_facts",
        ),
        (
            "source_fact_rewrite_allowed",
            "source_fact_rewrite_claimed",
            "source_fact_rewrite_enabled",
            "rewrites_source_facts",
        ),
        (
            "market_data_rewrite_allowed",
            "market_data_rewrite_claimed",
            "market_data_rewrite_enabled",
            "rewrites_market_data",
        ),
        (
            "replay_result_fact_rewrite_allowed",
            "replay_result_fact_rewrite_claimed",
            "replay_result_fact_rewrite_enabled",
            "rewrites_replay_result_facts",
        ),
        (
            "paper_result_fact_rewrite_allowed",
            "paper_result_fact_rewrite_claimed",
            "paper_result_fact_rewrite_enabled",
            "rewrites_paper_result_facts",
        ),
        (
            "runtime_balance_rewrite_allowed",
            "runtime_balance_rewrite_claimed",
            "runtime_balance_rewrite_enabled",
            "rewrites_runtime_balances",
        ),
    ],
)
def test_observed_source_market_result_or_balance_fact_rewrite_claim_fails(
    policy_allowed,
    policy_claimed,
    forbidden_flag,
    no_claim_flag,
):
    fixture = _fixture()
    fixture["dashboard_policy"][policy_allowed] = True
    fixture["dashboard_policy"][policy_claimed] = True
    fixture["forbidden_action_flags"][forbidden_flag] = True
    fixture["no_claim_flags"][no_claim_flag] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, policy_allowed)
    _assert_failure_contains(failures, policy_claimed)


def test_runtime_cash_and_usable_cash_claim_fails():
    fixture = _fixture()
    fixture["capital_risk_policy"]["runtime_cash_claimed"] = True
    fixture["capital_risk_policy"]["usable_cash_claimed"] = True
    fixture["forbidden_action_flags"]["runtime_cash_claim_enabled"] = True
    fixture["forbidden_action_flags"]["usable_cash_claim_enabled"] = True
    fixture["no_claim_flags"]["claims_runtime_cash"] = True
    fixture["no_claim_flags"]["claims_usable_cash"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "runtime_cash_claimed")
    _assert_failure_contains(failures, "usable_cash_claimed")


def test_increased_exposure_claim_fails():
    fixture = _fixture()
    fixture["capital_risk_policy"]["increased_exposure_allowed"] = True
    fixture["capital_risk_policy"]["increased_exposure_claimed"] = True
    fixture["forbidden_action_flags"]["increased_exposure_enabled"] = True
    fixture["no_claim_flags"]["claims_increased_exposure"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "increased_exposure_allowed")
    _assert_failure_contains(failures, "increased_exposure_claimed")


@pytest.mark.parametrize(
    "allowed,claimed,forbidden_flag,no_claim_flag",
    [
        (
            "limited_live_canary_promotion_allowed",
            "limited_live_canary_promotion_claimed",
            "limited_live_canary_promotion_enabled",
            "promotes_limited_live_canary",
        ),
        (
            "triggered_live_comparison_promotion_allowed",
            "triggered_live_comparison_promotion_claimed",
            "triggered_live_comparison_promotion_enabled",
            "promotes_triggered_live_comparison",
        ),
        (
            "full_live_promotion_allowed",
            "full_live_promotion_claimed",
            "full_live_promotion_enabled",
            "promotes_full_live",
        ),
        (
            "scaled_live_promotion_allowed",
            "scaled_live_promotion_claimed",
            "scaled_live_promotion_enabled",
            "promotes_scaled_live",
        ),
        (
            "limited_live_arbitrage_promotion_allowed",
            "limited_live_arbitrage_promotion_claimed",
            "limited_live_arbitrage_promotion_enabled",
            "promotes_limited_live_arbitrage",
        ),
    ],
)
def test_limited_live_full_live_or_arbitrage_promotion_claim_fails(
    allowed,
    claimed,
    forbidden_flag,
    no_claim_flag,
):
    fixture = _fixture()
    fixture["transition_runtime_policy"][allowed] = True
    fixture["transition_runtime_policy"][claimed] = True
    fixture["forbidden_action_flags"][forbidden_flag] = True
    fixture["no_claim_flags"][no_claim_flag] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, allowed)
    _assert_failure_contains(failures, claimed)


def test_live_reachability_claim_fails():
    fixture = _fixture()
    fixture["live_reachability_policy"]["live_reachability_created"] = True
    fixture["live_reachability_policy"]["live_reachability_claimed"] = True
    fixture["forbidden_action_flags"]["live_reachability_enabled"] = True
    fixture["no_claim_flags"]["creates_live_reachability"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "live_reachability_created")
    _assert_failure_contains(failures, "live_reachability_claimed")


def test_order_authority_claim_fails():
    fixture = _fixture()
    fixture["order_authority_policy"]["order_authority_created"] = True
    fixture["order_authority_policy"]["order_execution_authority_created"] = True
    fixture["order_authority_policy"]["order_authority_claimed"] = True
    fixture["forbidden_action_flags"]["order_authority_enabled"] = True
    fixture["forbidden_action_flags"]["order_execution_authority_enabled"] = True
    fixture["no_claim_flags"]["creates_order_authority"] = True
    fixture["no_claim_flags"]["creates_order_execution_authority"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "order_authority_created")
    _assert_failure_contains(failures, "order_execution_authority_created")


def test_source_retrieval_source_acceptance_and_connector_binding_claims_fail():
    fixture = _fixture()
    fixture["source_authority_policy"]["source_retrieval_claimed"] = True
    fixture["source_authority_policy"]["source_acceptance_claimed"] = True
    fixture["source_authority_policy"]["source_facts_accepted"] = True
    fixture["source_authority_policy"]["accepted_source_packet_created"] = True
    fixture["source_authority_policy"]["accepted_source_evidence_packet_created"] = True
    fixture["connector_semantic_policy"]["connector_semantic_binding_allowed"] = True
    fixture["connector_semantic_policy"]["connector_semantic_binding_claimed"] = True
    fixture["connector_semantic_policy"]["connector_semantics_bound"] = True
    fixture["forbidden_action_flags"]["source_retrieval_enabled"] = True
    fixture["forbidden_action_flags"]["source_acceptance_execution_enabled"] = True
    fixture["forbidden_action_flags"]["source_fact_acceptance_enabled"] = True
    fixture["forbidden_action_flags"]["accepted_source_packet_creation_enabled"] = True
    fixture["forbidden_action_flags"][
        "accepted_source_evidence_packet_creation_enabled"
    ] = True
    fixture["forbidden_action_flags"]["connector_semantic_binding_enabled"] = True
    fixture["no_claim_flags"]["claims_source_retrieval"] = True
    fixture["no_claim_flags"]["claims_source_acceptance"] = True
    fixture["no_claim_flags"]["claims_source_fact_acceptance"] = True
    fixture["no_claim_flags"]["creates_accepted_source_packets"] = True
    fixture["no_claim_flags"]["creates_accepted_source_evidence_packets"] = True
    fixture["no_claim_flags"]["binds_connector_semantics"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "source_retrieval_claimed")
    _assert_failure_contains(failures, "source_acceptance_claimed")
    _assert_failure_contains(failures, "accepted_source_packet_created")
    _assert_failure_contains(failures, "connector_semantic_binding_allowed")


def test_blocker_reduction_claim_fails():
    fixture = _fixture()
    fixture["claim_policy"]["blocker_reduction_claimed"] = True
    fixture["forbidden_action_flags"]["blocker_reduction_enabled"] = True
    fixture["no_claim_flags"]["claims_blocker_reduction"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "blocker_reduction_claimed")
    _assert_failure_contains(failures, "blocker_reduction_enabled")


def test_profit_evidence_claim_fails():
    fixture = _fixture()
    fixture["claim_policy"]["profit_claim_created"] = True
    fixture["claim_policy"]["profit_evidence_created"] = True
    fixture["forbidden_action_flags"]["profit_claim_enabled"] = True
    fixture["forbidden_action_flags"]["profit_evidence_creation_enabled"] = True
    fixture["no_claim_flags"]["creates_profit_claim"] = True
    fixture["no_claim_flags"]["creates_profit_evidence"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "profit_claim_created")
    _assert_failure_contains(failures, "profit_evidence_created")


def test_atomicrows_bundle_hash_sha_row_or_completion_authority_claim_fails():
    fixture = _fixture()
    fixture["atomicrows_authority_state"]["atomicrows_bundle_creation_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_hash_creation_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_sha_computation_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_sha_authority_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_row_creation_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_completion_claimed"] = True
    fixture["atomicrows_authority_state"]["claims_4183_row_completion"] = True
    fixture["forbidden_action_flags"]["atomicrows_bundle_creation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_bundle_hash_creation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_sha_computation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_sha_authority_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_row_creation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_completion_claim_enabled"] = True
    fixture["no_claim_flags"]["contains_atomicrows_bundle"] = True
    fixture["no_claim_flags"]["contains_atomicrows_bundle_hash"] = True
    fixture["no_claim_flags"]["computes_atomicrows_sha"] = True
    fixture["no_claim_flags"]["claims_atomicrows_sha_authority"] = True
    fixture["no_claim_flags"]["creates_atomicrows_rows"] = True
    fixture["no_claim_flags"]["creates_atomicrows_row_records"] = True
    fixture["no_claim_flags"]["claims_atomicrows_completion"] = True
    fixture["no_claim_flags"]["claims_4183_row_completion"] = True

    failures = _validate_fixture(fixture)

    for fragment in [
        "atomicrows_bundle_creation_claimed",
        "atomicrows_hash_creation_claimed",
        "atomicrows_sha_computation_claimed",
        "atomicrows_sha_authority_claimed",
        "atomicrows_row_creation_claimed",
        "atomicrows_completion_claimed",
        "claims_4183_row_completion",
    ]:
        _assert_failure_contains(failures, fragment)


def test_actual_atomicrows_bundle_existing_at_canonical_path_fails(tmp_path):
    bundle_path = _canonical_bundle_path(tmp_path)
    bundle_path.parent.mkdir(parents=True)
    bundle_path.write_text("", encoding="utf-8")

    failures = _validate_fixture(_fixture(), repo_root=tmp_path)

    _assert_failure_contains(failures, "canonical AtomicRows bundle must remain absent")


def test_actual_atomicrows_bundle_hash_existing_at_canonical_path_fails(tmp_path):
    sha_path = _canonical_bundle_sha_path(tmp_path)
    sha_path.parent.mkdir(parents=True)
    sha_path.write_text("UNAUTHORIZED_TEST_HASH_PLACEHOLDER", encoding="utf-8")

    failures = _validate_fixture(_fixture(), repo_root=tmp_path)

    _assert_failure_contains(
        failures,
        "canonical AtomicRows bundle hash must remain absent",
    )


def test_every_forbidden_action_flag_fails_when_true():
    for flag in sorted(FORBIDDEN_ACTION_FLAGS):
        fixture = _fixture()
        fixture["forbidden_action_flags"][flag] = True

        failures = _validate_fixture(fixture)

        _assert_failure_contains(failures, flag)


def test_every_no_claim_flag_fails_when_true():
    for flag in sorted(NO_CLAIM_FLAGS):
        fixture = _fixture()
        fixture["no_claim_flags"][flag] = True

        failures = _validate_fixture(fixture)

        _assert_failure_contains(failures, flag)


def test_validator_does_not_mutate_files_fixture_or_create_atomicrows_files(tmp_path):
    schema_before = SCHEMA_PATH.read_bytes()
    fixture_before = FIXTURE_PATH.read_bytes()
    fixture = _fixture()
    frozen = copy.deepcopy(fixture)

    assert (
        validate_static_surface(
            schema_path=SCHEMA_PATH,
            fixture_path=FIXTURE_PATH,
            repo_root=tmp_path,
        )
        == []
    )

    assert SCHEMA_PATH.read_bytes() == schema_before
    assert FIXTURE_PATH.read_bytes() == fixture_before
    assert fixture == frozen
    assert not _canonical_bundle_path(tmp_path).exists()
    assert not _canonical_bundle_sha_path(tmp_path).exists()


def test_canonical_atomicrows_bundle_and_hash_are_absent_in_repo():
    assert not _canonical_bundle_path(Path(".")).exists()
    assert not _canonical_bundle_sha_path(Path(".")).exists()
