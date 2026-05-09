import copy
import json
import shutil
from pathlib import Path

import pytest

from tools.validate_venue_neutral_prediction_adapter_gate_static import (
    ALLOWED_SOURCE_DEPENDENCY_STATES,
    CANONICAL_BUNDLE_RELATIVE_PATH,
    CANONICAL_BUNDLE_SHA_RELATIVE_PATH,
    EXPECTED_ADAPTER_SURFACES,
    FORBIDDEN_ACTION_FLAGS,
    NO_CLAIM_FLAGS,
    validate_static_surface,
    validate_venue_neutral_prediction_adapter_gate_fixture,
)


SCHEMA_DIR = Path("schemas/venue_neutral_prediction_adapter")
FIXTURE_PATH = Path(
    "tests/fixtures/venue_neutral_prediction_adapter/"
    "synthetic_venue_neutral_prediction_adapter_gate_blocked.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _validate_fixture(fixture: dict, repo_root: Path = Path(".")) -> list[str]:
    return validate_venue_neutral_prediction_adapter_gate_fixture(
        fixture,
        repo_root=repo_root,
        schema_dir=SCHEMA_DIR,
    )


def _canonical_bundle_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_RELATIVE_PATH.parts)


def _canonical_bundle_sha_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_SHA_RELATIVE_PATH.parts)


def test_valid_schema_only_blocked_fixture_passes():
    assert (
        validate_static_surface(
            repo_root=Path("."),
            schema_dir=SCHEMA_DIR,
            fixture_path=FIXTURE_PATH,
        )
        == []
    )

    fixture = _fixture()
    assert fixture["expected_adapter_surfaces"] == EXPECTED_ADAPTER_SURFACES
    assert fixture["adapter_gate_authority"]["schema_only_static_audit"] is True
    assert fixture["source_dependency_policy"]["allowed_source_dependency_states"] == (
        ALLOWED_SOURCE_DEPENDENCY_STATES
    )


def test_missing_schema_only_authority_fails():
    fixture = _fixture()
    fixture["adapter_gate_authority"].pop("schema_only_static_audit")

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "schema_only_static_audit")


def test_missing_stage1_packet_schema_gate_receipt_requirement_fails():
    fixture = _fixture()
    fixture["prerequisite_receipts"][
        "stage1_packet_schema_gate_receipt_required"
    ] = False

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


def test_missing_backbone_manifest_receipt_requirement_or_pending_representation_fails():
    fixture = _fixture()
    fixture["prerequisite_receipts"]["backbone_manifest_receipt_required"] = False
    fixture["prerequisite_receipts"]["backbone_manifest_receipt_status"] = "OMITTED"

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "backbone_manifest_receipt_required")
    _assert_failure_contains(failures, "backbone_manifest_receipt_status")


def test_missing_required_adapter_schema_surface_fails(tmp_path):
    schema_dir = tmp_path / "venue_neutral_prediction_adapter"
    shutil.copytree(SCHEMA_DIR, schema_dir)
    (schema_dir / "venue_neutral_market_snapshot.schema.json").unlink()

    failures = validate_static_surface(
        repo_root=Path("."),
        schema_dir=schema_dir,
        fixture_path=FIXTURE_PATH,
    )

    _assert_failure_contains(failures, "venue_neutral_market_snapshot.schema.json")


def test_source_dependency_state_outside_allowed_set_fails():
    fixture = _fixture()
    fixture["placeholder_records"][0]["source_dependency_state"] = "BOUND_RUNTIME_VALUE"

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "source_dependency_state")


def test_venue_specific_api_shape_claim_fails():
    fixture = _fixture()
    fixture["connector_semantic_policy"]["venue_specific_api_shape_populated"] = True
    fixture["forbidden_action_flags"]["venue_specific_api_shape_enabled"] = True
    fixture["no_claim_flags"]["encodes_venue_specific_api_shape"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "venue_specific_api_shape_populated")
    _assert_failure_contains(failures, "venue_specific_api_shape_enabled")
    _assert_failure_contains(failures, "encodes_venue_specific_api_shape")


def test_endpoint_and_authentication_flow_semantic_value_claims_fail():
    fixture = _fixture()
    fixture["connector_semantic_policy"]["endpoint_semantic_value_populated"] = True
    fixture["connector_semantic_policy"][
        "authentication_flow_semantic_value_populated"
    ] = True
    fixture["forbidden_action_flags"]["endpoint_semantic_value_enabled"] = True
    fixture["forbidden_action_flags"]["authentication_flow_semantic_value_enabled"] = True
    fixture["no_claim_flags"]["encodes_endpoint_semantic_value"] = True
    fixture["no_claim_flags"]["encodes_authentication_flow_semantic_value"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "endpoint_semantic_value_populated")
    _assert_failure_contains(
        failures,
        "authentication_flow_semantic_value_populated",
    )
    _assert_failure_contains(failures, "endpoint_semantic_value_enabled")
    _assert_failure_contains(
        failures,
        "authentication_flow_semantic_value_enabled",
    )


@pytest.mark.parametrize(
    "policy_flag,forbidden_flag,no_claim_flag",
    [
        (
            "fee_semantic_value_populated",
            "fee_semantic_value_enabled",
            "encodes_fee_semantic_value",
        ),
        (
            "tick_semantic_value_populated",
            "tick_semantic_value_enabled",
            "encodes_tick_semantic_value",
        ),
        (
            "rate_limit_semantic_value_populated",
            "rate_limit_semantic_value_enabled",
            "encodes_rate_limit_semantic_value",
        ),
        (
            "settlement_semantic_value_populated",
            "settlement_semantic_value_enabled",
            "encodes_settlement_semantic_value",
        ),
        (
            "order_status_semantic_value_populated",
            "order_status_semantic_value_enabled",
            "encodes_order_status_semantic_value",
        ),
        (
            "private_state_semantic_value_populated",
            "private_state_semantic_value_enabled",
            "encodes_private_state_semantic_value",
        ),
    ],
)
def test_fee_tick_rate_limit_settlement_order_status_and_private_state_claims_fail(
    policy_flag,
    forbidden_flag,
    no_claim_flag,
):
    fixture = _fixture()
    fixture["connector_semantic_policy"][policy_flag] = True
    fixture["forbidden_action_flags"][forbidden_flag] = True
    fixture["no_claim_flags"][no_claim_flag] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, policy_flag)
    _assert_failure_contains(failures, forbidden_flag)
    _assert_failure_contains(failures, no_claim_flag)


def test_connector_scaffold_creation_claim_fails():
    fixture = _fixture()
    fixture["connector_scaffold_policy"]["connector_scaffold_created"] = True
    fixture["connector_scaffold_policy"]["connector_scaffold_creation_allowed"] = True
    fixture["forbidden_action_flags"]["connector_scaffold_creation_enabled"] = True
    fixture["no_claim_flags"]["creates_connector_scaffold"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "connector_scaffold_created")
    _assert_failure_contains(failures, "connector_scaffold_creation_allowed")
    _assert_failure_contains(failures, "connector_scaffold_creation_enabled")
    _assert_failure_contains(failures, "creates_connector_scaffold")


def test_connector_semantic_implementation_claim_fails():
    fixture = _fixture()
    fixture["connector_semantic_policy"][
        "connector_semantic_implementation_created"
    ] = True
    fixture["connector_semantic_policy"]["connector_semantic_values_populated"] = True
    fixture["forbidden_action_flags"][
        "connector_semantic_implementation_enabled"
    ] = True
    fixture["forbidden_action_flags"][
        "connector_semantic_value_population_enabled"
    ] = True
    fixture["no_claim_flags"]["creates_connector_semantic_implementation"] = True
    fixture["no_claim_flags"]["populates_connector_semantic_values"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "connector_semantic_implementation_created")
    _assert_failure_contains(failures, "connector_semantic_values_populated")
    _assert_failure_contains(failures, "connector_semantic_implementation_enabled")
    _assert_failure_contains(failures, "populates_connector_semantic_values")


def test_venue_specific_connector_module_import_reference_fails():
    fixture = _fixture()
    fixture["connector_scaffold_policy"]["venue_specific_connector_module_reference"] = (
        "from qtt.connectors.venue_specific import RuntimeClient"
    )
    fixture["forbidden_action_flags"]["connector_import_enabled"] = True
    fixture["no_claim_flags"]["imports_venue_specific_connector_module"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "venue_specific_connector_module_reference")
    _assert_failure_contains(failures, "connector_import_enabled")
    _assert_failure_contains(failures, "imports_venue_specific_connector_module")


def test_source_required_placeholder_without_target_field_fails():
    fixture = _fixture()
    fixture["placeholder_records"][0].pop("target_field_path")

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "target_field_path")


@pytest.mark.parametrize(
    "selection_flag,forbidden_flag,no_claim_flag",
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
            "exact_symbol_selection_claimed",
            "exact_symbol_selection_enabled",
            "selects_exact_symbols",
        ),
        (
            "exact_live_venue_selection_claimed",
            "exact_live_venue_selection_enabled",
            "selects_live_venues",
        ),
    ],
)
def test_exact_market_contract_event_symbol_or_venue_selection_claim_fails(
    selection_flag,
    forbidden_flag,
    no_claim_flag,
):
    fixture = _fixture()
    fixture["selection_policy"][selection_flag] = True
    fixture["forbidden_action_flags"][forbidden_flag] = True
    fixture["no_claim_flags"][no_claim_flag] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, selection_flag)
    _assert_failure_contains(failures, forbidden_flag)
    _assert_failure_contains(failures, no_claim_flag)


def test_runtime_resolver_snapshot_creation_claim_fails():
    fixture = _fixture()
    fixture["runtime_policy"]["runtime_resolver_snapshot_created"] = True
    fixture["runtime_policy"]["runtime_resolver_snapshot_creation_claimed"] = True
    fixture["forbidden_action_flags"][
        "runtime_resolver_snapshot_creation_enabled"
    ] = True
    fixture["no_claim_flags"]["creates_runtime_resolver_snapshots"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "runtime_resolver_snapshot_created")
    _assert_failure_contains(failures, "runtime_resolver_snapshot_creation_claimed")
    _assert_failure_contains(failures, "runtime_resolver_snapshot_creation_enabled")
    _assert_failure_contains(failures, "creates_runtime_resolver_snapshots")


def test_replay_and_paper_execution_claims_fail():
    fixture = _fixture()
    fixture["execution_policy"]["replay_execution_claimed"] = True
    fixture["execution_policy"]["paper_execution_claimed"] = True
    fixture["forbidden_action_flags"]["replay_execution_enabled"] = True
    fixture["forbidden_action_flags"]["paper_execution_enabled"] = True
    fixture["no_claim_flags"]["executes_replay"] = True
    fixture["no_claim_flags"]["executes_paper"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "replay_execution_claimed")
    _assert_failure_contains(failures, "paper_execution_claimed")
    _assert_failure_contains(failures, "replay_execution_enabled")
    _assert_failure_contains(failures, "paper_execution_enabled")


def test_runtime_replay_or_paper_result_packet_creation_claim_fails():
    fixture = _fixture()
    fixture["execution_policy"]["runtime_replay_result_packet_created"] = True
    fixture["execution_policy"]["runtime_paper_result_packet_created"] = True
    fixture["forbidden_action_flags"][
        "runtime_replay_result_packet_creation_enabled"
    ] = True
    fixture["forbidden_action_flags"][
        "runtime_paper_result_packet_creation_enabled"
    ] = True
    fixture["no_claim_flags"]["creates_runtime_replay_result_packets"] = True
    fixture["no_claim_flags"]["creates_runtime_paper_result_packets"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "runtime_replay_result_packet_created")
    _assert_failure_contains(failures, "runtime_paper_result_packet_created")
    _assert_failure_contains(failures, "runtime_replay_result_packet_creation_enabled")
    _assert_failure_contains(failures, "runtime_paper_result_packet_creation_enabled")


def test_live_reachability_claim_fails():
    fixture = _fixture()
    fixture["live_reachability_policy"]["live_reachability_created"] = True
    fixture["live_reachability_policy"]["live_reachability_claimed"] = True
    fixture["forbidden_action_flags"]["live_reachability_enabled"] = True
    fixture["no_claim_flags"]["creates_live_reachability"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "live_reachability_created")
    _assert_failure_contains(failures, "live_reachability_claimed")
    _assert_failure_contains(failures, "live_reachability_enabled")
    _assert_failure_contains(failures, "creates_live_reachability")


def test_order_authority_claim_fails():
    fixture = _fixture()
    fixture["order_authority_policy"]["order_authority_created"] = True
    fixture["order_authority_policy"]["order_execution_authority_created"] = True
    fixture["forbidden_action_flags"]["order_authority_enabled"] = True
    fixture["forbidden_action_flags"]["order_execution_enabled"] = True
    fixture["no_claim_flags"]["creates_order_authority"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "order_authority_created")
    _assert_failure_contains(failures, "order_execution_authority_created")
    _assert_failure_contains(failures, "order_authority_enabled")
    _assert_failure_contains(failures, "order_execution_enabled")


def test_order_submit_cancel_reduce_and_close_claims_fail():
    fixture = _fixture()
    fixture["order_authority_policy"]["order_submission_enabled"] = True
    fixture["order_authority_policy"]["order_cancel_enabled"] = True
    fixture["order_authority_policy"]["order_reduce_enabled"] = True
    fixture["order_authority_policy"]["order_close_enabled"] = True
    fixture["forbidden_action_flags"]["order_submit_enabled"] = True
    fixture["forbidden_action_flags"]["order_cancel_enabled"] = True
    fixture["forbidden_action_flags"]["order_reduce_enabled"] = True
    fixture["forbidden_action_flags"]["order_close_enabled"] = True
    fixture["no_claim_flags"]["submits_orders"] = True
    fixture["no_claim_flags"]["cancels_orders"] = True
    fixture["no_claim_flags"]["reduces_orders"] = True
    fixture["no_claim_flags"]["closes_orders"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "order_submission_enabled")
    _assert_failure_contains(failures, "order_cancel_enabled")
    _assert_failure_contains(failures, "order_reduce_enabled")
    _assert_failure_contains(failures, "order_close_enabled")


def test_private_state_balance_or_account_fetch_claim_fails():
    fixture = _fixture()
    fixture["forbidden_action_flags"]["private_state_fetch_enabled"] = True
    fixture["forbidden_action_flags"]["balance_fetch_enabled"] = True
    fixture["forbidden_action_flags"]["account_state_fetch_enabled"] = True
    fixture["no_claim_flags"]["fetches_private_state"] = True
    fixture["no_claim_flags"]["fetches_balances"] = True
    fixture["no_claim_flags"]["fetches_account_state"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "private_state_fetch_enabled")
    _assert_failure_contains(failures, "balance_fetch_enabled")
    _assert_failure_contains(failures, "account_state_fetch_enabled")


def test_source_retrieval_and_acceptance_claims_fail():
    fixture = _fixture()
    fixture["source_authority_policy"]["source_retrieval_claimed"] = True
    fixture["source_authority_policy"]["source_acceptance_claimed"] = True
    fixture["source_authority_policy"]["source_facts_accepted"] = True
    fixture["source_dependency_policy"]["source_retrieval_claimed"] = True
    fixture["source_dependency_policy"]["source_fact_acceptance_claimed"] = True
    fixture["forbidden_action_flags"]["source_retrieval_enabled"] = True
    fixture["forbidden_action_flags"]["source_acceptance_execution_enabled"] = True
    fixture["forbidden_action_flags"]["source_fact_acceptance_enabled"] = True
    fixture["no_claim_flags"]["claims_source_retrieval"] = True
    fixture["no_claim_flags"]["claims_source_fact_acceptance"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "source_retrieval_claimed")
    _assert_failure_contains(failures, "source_acceptance_claimed")
    _assert_failure_contains(failures, "source_facts_accepted")
    _assert_failure_contains(failures, "source_retrieval_enabled")
    _assert_failure_contains(failures, "source_acceptance_execution_enabled")


def test_accepted_source_packet_creation_claim_fails():
    fixture = _fixture()
    fixture["source_authority_policy"]["accepted_source_packet_created"] = True
    fixture["source_authority_policy"]["accepted_source_evidence_packet_created"] = True
    fixture["source_dependency_policy"]["accepted_source_packet_created"] = True
    fixture["source_dependency_policy"]["accepted_source_evidence_packet_created"] = True
    fixture["forbidden_action_flags"]["accepted_source_packet_creation_enabled"] = True
    fixture["forbidden_action_flags"][
        "accepted_source_evidence_packet_creation_enabled"
    ] = True
    fixture["no_claim_flags"]["creates_accepted_source_packets"] = True
    fixture["no_claim_flags"]["creates_accepted_source_evidence_packets"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "accepted_source_packet_created")
    _assert_failure_contains(failures, "accepted_source_evidence_packet_created")
    _assert_failure_contains(failures, "accepted_source_packet_creation_enabled")
    _assert_failure_contains(
        failures,
        "accepted_source_evidence_packet_creation_enabled",
    )


def test_blocker_reduction_claim_fails():
    fixture = _fixture()
    fixture["claim_policy"]["blocker_reduction_claimed"] = True
    fixture["forbidden_action_flags"]["blocker_reduction_enabled"] = True
    fixture["no_claim_flags"]["claims_blocker_reduction"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "blocker_reduction_claimed")
    _assert_failure_contains(failures, "blocker_reduction_enabled")
    _assert_failure_contains(failures, "claims_blocker_reduction")


def test_profit_evidence_or_claim_fails():
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
    _assert_failure_contains(failures, "profit_claim_enabled")
    _assert_failure_contains(failures, "profit_evidence_creation_enabled")


def test_atomicrows_bundle_hash_sha_row_or_completion_authority_claim_fails():
    fixture = _fixture()
    fixture["atomicrows_authority_state"]["atomicrows_bundle_creation_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_hash_creation_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_sha_authority_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_row_creation_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_completion_claimed"] = True
    fixture["atomicrows_authority_state"]["claims_4183_row_completion"] = True
    fixture["atomicrows_authority_state"]["freeze_authority_claimed"] = True
    fixture["forbidden_action_flags"]["atomicrows_bundle_creation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_bundle_hash_creation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_sha_computation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_sha_authority_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_row_creation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_completion_claim_enabled"] = True
    fixture["forbidden_action_flags"]["freeze_authority_enabled"] = True
    fixture["no_claim_flags"]["contains_atomicrows_bundle"] = True
    fixture["no_claim_flags"]["contains_atomicrows_bundle_hash"] = True
    fixture["no_claim_flags"]["computes_atomicrows_sha"] = True
    fixture["no_claim_flags"]["claims_atomicrows_sha_authority"] = True
    fixture["no_claim_flags"]["creates_atomicrows_rows"] = True
    fixture["no_claim_flags"]["creates_atomicrows_row_records"] = True
    fixture["no_claim_flags"]["claims_atomicrows_completion"] = True
    fixture["no_claim_flags"]["claims_4183_row_completion"] = True
    fixture["no_claim_flags"]["creates_freeze_authority"] = True

    failures = _validate_fixture(fixture)

    for fragment in [
        "atomicrows_bundle_creation_claimed",
        "atomicrows_hash_creation_claimed",
        "atomicrows_sha_authority_claimed",
        "atomicrows_row_creation_claimed",
        "atomicrows_completion_claimed",
        "claims_4183_row_completion",
        "freeze_authority_claimed",
        "claims_atomicrows_sha_authority",
    ]:
        _assert_failure_contains(failures, fragment)


def test_actual_atomicrows_bundle_existing_at_canonical_path_fails(tmp_path):
    bundle_path = _canonical_bundle_path(tmp_path)
    bundle_path.parent.mkdir(parents=True)
    bundle_path.write_text("", encoding="utf-8")

    failures = validate_static_surface(
        repo_root=tmp_path,
        schema_dir=SCHEMA_DIR,
        fixture_path=FIXTURE_PATH,
    )

    _assert_failure_contains(failures, "canonical AtomicRows bundle must remain absent")


def test_actual_atomicrows_sha_existing_at_canonical_path_fails(tmp_path):
    sha_path = _canonical_bundle_sha_path(tmp_path)
    sha_path.parent.mkdir(parents=True)
    sha_path.write_text("UNAUTHORIZED_TEST_HASH_PLACEHOLDER", encoding="utf-8")

    failures = validate_static_surface(
        repo_root=tmp_path,
        schema_dir=SCHEMA_DIR,
        fixture_path=FIXTURE_PATH,
    )

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


def test_fixture_rejects_atomicrows_row_records():
    fixture = _fixture()
    fixture["row_records"] = [{"atomic_parameter_row_id": "atomic_parameter_row_0001"}]

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "row_records")


def test_validator_does_not_mutate_fixture_or_create_atomicrows_files(tmp_path):
    fixture = _fixture()
    frozen = copy.deepcopy(fixture)
    bundle_path = _canonical_bundle_path(tmp_path)
    sha_path = _canonical_bundle_sha_path(tmp_path)

    assert (
        validate_venue_neutral_prediction_adapter_gate_fixture(
            fixture,
            repo_root=tmp_path,
            schema_dir=SCHEMA_DIR,
        )
        == []
    )

    assert fixture == frozen
    assert not bundle_path.exists()
    assert not sha_path.exists()


def test_canonical_atomicrows_bundle_and_hash_are_absent_in_repo():
    assert not _canonical_bundle_path(Path(".")).exists()
    assert not _canonical_bundle_sha_path(Path(".")).exists()
