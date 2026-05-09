import copy
import json
from pathlib import Path

import pytest

from tools.validate_connector_scaffold_source_required_gate_static import (
    CANONICAL_BUNDLE_RELATIVE_PATH,
    CANONICAL_BUNDLE_SHA_RELATIVE_PATH,
    FORBIDDEN_ACTION_FLAGS,
    NO_CLAIM_FLAGS,
    TARGET_FIELDS,
    validate_connector_scaffold_source_required_gate_fixture,
    validate_static_surface,
)


SCHEMA_PATH = Path(
    "schemas/connectors/connector_scaffold_source_required_gate.schema.json"
)
FIXTURE_PATH = Path(
    "tests/fixtures/connectors/"
    "synthetic_connector_scaffold_source_required_blocked.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _validate_fixture(fixture: dict, repo_root: Path = Path(".")) -> list[str]:
    return validate_connector_scaffold_source_required_gate_fixture(
        fixture,
        repo_root=repo_root,
    )


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _canonical_bundle_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_RELATIVE_PATH.parts)


def _canonical_bundle_sha_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_SHA_RELATIVE_PATH.parts)


def _card(fixture: dict) -> dict:
    return fixture["connector_capability_cards"][0]


def _matrix(fixture: dict) -> dict:
    return fixture["active_connector_capability_matrix"]


def _first_placeholder(fixture: dict) -> dict:
    return _card(fixture)["source_required_placeholders"][0]


def test_valid_static_blocked_fixture_passes():
    assert (
        validate_static_surface(
            schema_path=SCHEMA_PATH,
            fixture_path=FIXTURE_PATH,
            repo_root=Path("."),
        )
        == []
    )

    fixture = _fixture()
    assert [item["target_field_path"] for item in fixture["connector_target_fields"]] == (
        TARGET_FIELDS
    )
    assert _card(fixture)["accepted_target_field_packet_count"] == (
        "NO_ACCEPTED_TARGET_FIELD_PACKETS"
    )


def test_missing_static_audit_authority_fails():
    fixture = _fixture()
    fixture["gate_authority"]["static_audit_only"] = False

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "static_audit_only")


def test_missing_venue_neutral_adapter_gate_receipt_requirement_fails():
    fixture = _fixture()
    fixture["prerequisite_receipts"][
        "venue_neutral_prediction_adapter_gate_receipt_required"
    ] = False

    failures = _validate_fixture(fixture)

    _assert_failure_contains(
        failures,
        "venue_neutral_prediction_adapter_gate_receipt_required",
    )


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


def test_missing_stage1_packet_schema_gate_receipt_requirement_fails():
    fixture = _fixture()
    fixture["prerequisite_receipts"][
        "stage1_packet_schema_gate_receipt_required"
    ] = False

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "stage1_packet_schema_gate_receipt_required")


def test_live_connector_creation_claim_fails():
    fixture = _fixture()
    fixture["live_connector_policy"]["live_connector_client_created"] = True
    fixture["live_connector_policy"]["live_connector_client_creation_allowed"] = True
    fixture["forbidden_action_flags"]["live_connector_client_creation_enabled"] = True
    fixture["no_claim_flags"]["creates_live_connector_client"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "live_connector_client_created")
    _assert_failure_contains(failures, "live_connector_client_creation_allowed")


def test_network_io_claim_fails():
    fixture = _fixture()
    fixture["network_policy"]["network_io_created"] = True
    fixture["network_policy"]["network_io_allowed"] = True
    fixture["forbidden_action_flags"]["network_io_enabled"] = True
    fixture["no_claim_flags"]["creates_network_io"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "network_io_created")
    _assert_failure_contains(failures, "network_io_allowed")
    _assert_failure_contains(failures, "network_io_enabled")


def test_venue_sdk_or_api_module_reference_claim_fails():
    fixture = _fixture()
    fixture["implementation_import_policy"]["venue_sdk_import_reference"] = (
        "from venue_sdk import RuntimeClient"
    )
    fixture["implementation_import_policy"]["venue_sdk_import_allowed"] = True
    fixture["forbidden_action_flags"]["venue_sdk_import_enabled"] = True
    fixture["no_claim_flags"]["imports_venue_sdk"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "venue_sdk_import_reference")
    _assert_failure_contains(failures, "venue_sdk_import_enabled")


def test_source_retrieval_claim_fails():
    fixture = _fixture()
    fixture["source_authority_policy"]["source_retrieval_claimed"] = True
    fixture["accepted_target_field_packet_policy"]["source_retrieval_claimed"] = True
    fixture["forbidden_action_flags"]["source_retrieval_enabled"] = True
    fixture["no_claim_flags"]["claims_source_retrieval"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "source_retrieval_claimed")
    _assert_failure_contains(failures, "source_retrieval_enabled")


def test_source_acceptance_claim_fails():
    fixture = _fixture()
    fixture["source_authority_policy"]["source_acceptance_claimed"] = True
    fixture["source_authority_policy"]["source_facts_accepted"] = True
    fixture["accepted_target_field_packet_policy"]["source_acceptance_claimed"] = True
    fixture["accepted_target_field_packet_policy"]["source_facts_accepted"] = True
    fixture["forbidden_action_flags"]["source_acceptance_execution_enabled"] = True
    fixture["forbidden_action_flags"]["source_fact_acceptance_enabled"] = True
    fixture["no_claim_flags"]["claims_source_acceptance"] = True
    fixture["no_claim_flags"]["claims_source_fact_acceptance"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "source_acceptance_claimed")
    _assert_failure_contains(failures, "source_facts_accepted")


def test_accepted_source_packet_creation_claim_fails():
    fixture = _fixture()
    fixture["source_authority_policy"]["accepted_source_packet_created"] = True
    fixture["source_authority_policy"][
        "accepted_source_evidence_packet_created"
    ] = True
    fixture["accepted_target_field_packet_policy"][
        "accepted_target_field_packets_created"
    ] = True
    fixture["accepted_target_field_packet_policy"][
        "accepted_source_packet_creation_allowed"
    ] = True
    fixture["forbidden_action_flags"]["accepted_source_packet_creation_enabled"] = True
    fixture["forbidden_action_flags"][
        "accepted_source_evidence_packet_creation_enabled"
    ] = True
    fixture["no_claim_flags"]["creates_accepted_source_packets"] = True
    fixture["no_claim_flags"]["creates_accepted_source_evidence_packets"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "accepted_source_packet_created")
    _assert_failure_contains(failures, "accepted_target_field_packets_created")


def test_connector_semantic_binding_claim_fails():
    fixture = _fixture()
    fixture["connector_semantic_binding_policy"][
        "connector_semantic_binding_allowed"
    ] = True
    fixture["forbidden_action_flags"]["connector_semantic_binding_enabled"] = True
    fixture["no_claim_flags"]["binds_connector_semantics"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "connector_semantic_binding_allowed")
    _assert_failure_contains(failures, "connector_semantic_binding_enabled")


def test_connector_semantic_value_population_claim_fails():
    fixture = _fixture()
    fixture["connector_semantic_binding_policy"][
        "connector_semantic_values_populated"
    ] = True
    fixture["semantic_population_policy"]["connector_semantic_values_populated"] = True
    fixture["forbidden_action_flags"][
        "connector_semantic_value_population_enabled"
    ] = True
    fixture["no_claim_flags"]["populates_connector_semantic_values"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "connector_semantic_values_populated")
    _assert_failure_contains(failures, "connector_semantic_value_population_enabled")


def test_venue_api_fact_population_claim_fails():
    fixture = _fixture()
    fixture["connector_semantic_binding_policy"]["venue_api_facts_populated"] = True
    fixture["semantic_population_policy"]["venue_api_facts_populated"] = True
    fixture["forbidden_action_flags"]["venue_api_fact_population_enabled"] = True
    fixture["no_claim_flags"]["populates_venue_api_facts"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "venue_api_facts_populated")
    _assert_failure_contains(failures, "venue_api_fact_population_enabled")


@pytest.mark.parametrize(
    "policy_flag,forbidden_flag,no_claim_flag",
    [
        (
            "exact_fee_semantics_populated",
            "exact_fee_semantics_enabled",
            "encodes_exact_fee_semantics",
        ),
        (
            "exact_tick_semantics_populated",
            "exact_tick_semantics_enabled",
            "encodes_exact_tick_semantics",
        ),
        (
            "exact_rate_limit_semantics_populated",
            "exact_rate_limit_semantics_enabled",
            "encodes_exact_rate_limit_semantics",
        ),
        (
            "exact_settlement_semantics_populated",
            "exact_settlement_semantics_enabled",
            "encodes_exact_settlement_semantics",
        ),
        (
            "exact_order_entry_fields_populated",
            "exact_order_entry_fields_enabled",
            "encodes_exact_order_entry_fields",
        ),
        (
            "exact_order_status_lifecycle_populated",
            "exact_order_status_lifecycle_enabled",
            "encodes_exact_order_status_lifecycle",
        ),
        (
            "exact_private_state_semantics_populated",
            "exact_private_state_semantics_enabled",
            "encodes_exact_private_state_semantics",
        ),
        (
            "exact_account_semantics_populated",
            "exact_account_semantics_enabled",
            "encodes_exact_account_semantics",
        ),
        (
            "exact_balance_semantics_populated",
            "exact_balance_semantics_enabled",
            "encodes_exact_balance_semantics",
        ),
    ],
)
def test_exact_connector_semantic_claims_fail(
    policy_flag,
    forbidden_flag,
    no_claim_flag,
):
    fixture = _fixture()
    fixture["semantic_population_policy"][policy_flag] = True
    fixture["forbidden_action_flags"][forbidden_flag] = True
    fixture["no_claim_flags"][no_claim_flag] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, policy_flag)
    _assert_failure_contains(failures, forbidden_flag)
    _assert_failure_contains(failures, no_claim_flag)


def test_source_required_placeholder_weakening_fails():
    fixture = _fixture()
    _first_placeholder(fixture)["placeholder_value"] = "SYNTHETIC_BOUND_VALUE"

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "placeholder_value")


def test_source_required_placeholder_without_target_field_metadata_fails():
    fixture = _fixture()
    _first_placeholder(fixture).pop("target_field_metadata")

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "target_field_metadata")


def test_connector_binding_without_accepted_target_field_packets_fails():
    fixture = _fixture()
    _matrix(fixture)["connector_semantic_binding_allowed"] = True
    fixture["accepted_target_field_packet_policy"][
        "connector_binding_allowed_without_accepted_target_field_packet"
    ] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "connector_semantic_binding_allowed")
    _assert_failure_contains(
        failures,
        "connector_binding_allowed_without_accepted_target_field_packet",
    )


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
def test_exact_market_contract_event_symbol_or_live_venue_selection_claim_fails(
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
    fixture["forbidden_action_flags"]["order_authority_enabled"] = True
    fixture["forbidden_action_flags"]["order_execution_enabled"] = True
    fixture["no_claim_flags"]["creates_order_authority"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "order_authority_created")
    _assert_failure_contains(failures, "order_execution_authority_created")


def test_runtime_cash_authority_claim_fails():
    fixture = _fixture()
    fixture["runtime_cash_policy"]["runtime_cash_value_authority_created"] = True
    fixture["runtime_cash_policy"]["runtime_cash_value_claimed"] = True
    fixture["forbidden_action_flags"]["runtime_cash_value_authority_enabled"] = True
    fixture["no_claim_flags"]["creates_runtime_cash_value_authority"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "runtime_cash_value_authority_created")
    _assert_failure_contains(failures, "runtime_cash_value_claimed")


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
    fixture["atomicrows_authority_state"]["atomicrows_sha_authority_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_row_creation_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_completion_claimed"] = True
    fixture["atomicrows_authority_state"]["claims_4183_row_completion"] = True
    fixture["forbidden_action_flags"]["atomicrows_bundle_creation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_bundle_hash_creation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_sha_computation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_row_creation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_completion_claim_enabled"] = True
    fixture["no_claim_flags"]["contains_atomicrows_bundle"] = True
    fixture["no_claim_flags"]["contains_atomicrows_bundle_hash"] = True
    fixture["no_claim_flags"]["computes_atomicrows_sha"] = True
    fixture["no_claim_flags"]["creates_atomicrows_rows"] = True
    fixture["no_claim_flags"]["creates_atomicrows_row_records"] = True
    fixture["no_claim_flags"]["claims_atomicrows_completion"] = True

    failures = _validate_fixture(fixture)

    for fragment in [
        "atomicrows_bundle_creation_claimed",
        "atomicrows_hash_creation_claimed",
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
