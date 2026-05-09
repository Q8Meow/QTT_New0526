import copy
import json
from pathlib import Path

import pytest

from tools.validate_source_evidence_gate_confirmation_static import (
    AUDIT_NO_CLAIM_FLAGS,
    CANONICAL_BUNDLE_RELATIVE_PATH,
    CANONICAL_BUNDLE_SHA_RELATIVE_PATH,
    FORBIDDEN_ACTION_FLAGS,
    validate_source_evidence_gate_confirmation_fixture,
    validate_static_surface,
)


SCHEMA_PATH = Path(
    "schemas/source_evidence/source_evidence_gate_confirmation.schema.json"
)
FIXTURE_PATH = Path(
    "tests/fixtures/source_evidence/"
    "synthetic_source_evidence_gate_confirmation_blocked.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _gate(fixture: dict) -> dict:
    return fixture["source_evidence_gate_confirmation"]


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _canonical_bundle_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_RELATIVE_PATH.parts)


def _canonical_bundle_sha_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_SHA_RELATIVE_PATH.parts)


def test_valid_blocked_static_fixture_passes():
    assert (
        validate_static_surface(
            schema_path=SCHEMA_PATH,
            fixture_path=FIXTURE_PATH,
            repo_root=Path("."),
        )
        == []
    )


def test_missing_static_audit_authority_fails():
    fixture = _fixture()
    fixture["gate_authority_class"] = "STATIC_SCHEMA_CONTRACT_ONLY"

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "gate_authority_class")


def test_source_retrieval_claim_fails():
    fixture = _fixture()
    _gate(fixture)["accepted_packet_schema_contract"][
        "source_retrieval_execution_claimed"
    ] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "source_retrieval_execution_claimed")


def test_source_acceptance_claim_fails():
    fixture = _fixture()
    _gate(fixture)["accepted_packet_schema_contract"][
        "source_acceptance_execution_claimed"
    ] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "source_acceptance_execution_claimed")


def test_source_fact_acceptance_claim_fails():
    fixture = _fixture()
    _gate(fixture)["accepted_packet_schema_contract"][
        "source_fact_acceptance_claimed"
    ] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "source_fact_acceptance_claimed")


def test_accepted_packet_creation_claim_fails():
    fixture = _fixture()
    _gate(fixture)["accepted_packet_schema_contract"][
        "accepted_packet_creation_by_this_audit"
    ] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "accepted_packet_creation_by_this_audit")


def test_connector_binding_claim_fails():
    fixture = _fixture()
    _gate(fixture)["accepted_packet_schema_contract"][
        "connector_semantic_binding_claimed"
    ] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "connector_semantic_binding_claimed")


def test_weakening_source_required_placeholder_preservation_fails():
    fixture = _fixture()
    _gate(fixture)["source_required_placeholder_contract"]["weakening_allowed"] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "weakening_allowed")


def test_non_source_required_placeholder_value_fails():
    fixture = _fixture()
    _gate(fixture)["source_required_placeholder_contract"][
        "source_required_value"
    ] = "SYNTHETIC_VALUE"

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "source_required_value")


def test_permitting_connector_binding_without_target_field_packet_fails():
    fixture = _fixture()
    _gate(fixture)["connector_semantic_block_contract"][
        "connector_binding_allowed_without_target_field_packet"
    ] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(
        failures,
        "connector_binding_allowed_without_target_field_packet",
    )


@pytest.mark.parametrize(
    "flag",
    [
        "source_dependent_value_acceptance_enabled",
        "venue_api_fact_population_enabled",
        "venue_semantics_acceptance_enabled",
        "fundamental_fact_population_enabled",
        "fee_semantics_acceptance_enabled",
        "tick_semantics_acceptance_enabled",
        "rate_limit_semantics_acceptance_enabled",
        "order_entry_semantics_acceptance_enabled",
        "settlement_semantics_acceptance_enabled",
        "private_state_semantics_acceptance_enabled",
        "replay_semantics_acceptance_enabled",
        "historical_data_semantics_acceptance_enabled",
    ],
)
def test_source_dependent_semantic_acceptance_without_exact_packet_fields_fails(flag):
    fixture = _fixture()
    _gate(fixture)["forbidden_action_flags"][flag] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, flag)


def test_blocked_semantic_family_status_must_not_be_accepted():
    fixture = _fixture()
    _gate(fixture)["blocked_semantic_families"]["fee_semantics"] = "ACCEPTED"

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "fee_semantics")


def test_live_reachability_claim_fails():
    fixture = _fixture()
    _gate(fixture)["runtime_block_contract"]["live_reachability_created"] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "live_reachability_created")


def test_runtime_resolver_snapshot_claim_fails():
    fixture = _fixture()
    _gate(fixture)["runtime_block_contract"][
        "runtime_resolver_snapshot_created"
    ] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "runtime_resolver_snapshot_created")


@pytest.mark.parametrize("field", ["replay_execution_claimed", "paper_execution_claimed"])
def test_replay_or_paper_execution_claim_fails(field):
    fixture = _fixture()
    _gate(fixture)["runtime_block_contract"][field] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, field)


def test_order_authority_claim_fails():
    fixture = _fixture()
    _gate(fixture)["runtime_block_contract"]["order_execution_authority_created"] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "order_execution_authority_created")


def test_blocker_reduction_claim_fails():
    fixture = _fixture()
    _gate(fixture)["runtime_block_contract"]["blocker_reduction_claimed"] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "blocker_reduction_claimed")


def test_profit_evidence_claim_fails():
    fixture = _fixture()
    _gate(fixture)["runtime_block_contract"]["profit_evidence_created"] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "profit_evidence_created")


@pytest.mark.parametrize(
    "flag",
    [
        "atomicrows_bundle_creation_enabled",
        "atomicrows_bundle_hash_creation_enabled",
        "atomicrows_sha_computation_enabled",
        "atomicrows_row_record_creation_enabled",
        "atomicrows_completion_claim_enabled",
        "sha_freeze_enabled",
    ],
)
def test_atomicrows_bundle_hash_sha_row_completion_action_claims_fail(flag):
    fixture = _fixture()
    _gate(fixture)["forbidden_action_flags"][flag] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, flag)


@pytest.mark.parametrize(
    "field",
    [
        "bundle_authority_present",
        "hash_authority_present",
        "sha_authority_present",
        "row_record_authority_present",
        "completion_authority_present",
        "claims_4183_row_completion",
    ],
)
def test_atomicrows_authority_state_claims_fail(field):
    fixture = _fixture()
    _gate(fixture)["atomicrows_authority_state"][field] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, field)


def test_atomicrows_row_count_completion_claim_fails():
    fixture = _fixture()
    _gate(fixture)["atomicrows_authority_state"][
        "claimed_atomicrows_row_count"
    ] = "4183"

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "claimed_atomicrows_row_count")


@pytest.mark.parametrize(
    "flag",
    [
        "creates_atomicrows_bundle",
        "creates_atomicrows_bundle_hash",
        "computes_atomicrows_sha",
        "creates_atomicrows_row_records",
        "claims_atomicrows_completion",
        "claims_4183_row_completion",
        "creates_freeze_authority",
    ],
)
def test_atomicrows_bundle_hash_sha_row_completion_no_claim_flags_fail(flag):
    assert flag in AUDIT_NO_CLAIM_FLAGS
    fixture = _fixture()
    _gate(fixture)["audit_no_claim_flags"][flag] = True

    failures = validate_source_evidence_gate_confirmation_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, flag)


def test_every_forbidden_action_flag_fails_when_true():
    for flag in sorted(FORBIDDEN_ACTION_FLAGS):
        fixture = _fixture()
        _gate(fixture)["forbidden_action_flags"][flag] = True

        failures = validate_source_evidence_gate_confirmation_fixture(
            fixture,
            repo_root=Path("."),
        )

        _assert_failure_contains(failures, flag)


def test_every_audit_no_claim_flag_fails_when_true():
    for flag in sorted(AUDIT_NO_CLAIM_FLAGS):
        fixture = _fixture()
        _gate(fixture)["audit_no_claim_flags"][flag] = True

        failures = validate_source_evidence_gate_confirmation_fixture(
            fixture,
            repo_root=Path("."),
        )

        _assert_failure_contains(failures, flag)


def test_actual_atomicrows_bundle_existing_at_canonical_path_fails(tmp_path):
    bundle_path = _canonical_bundle_path(tmp_path)
    bundle_path.parent.mkdir(parents=True)
    bundle_path.write_text("{}\n", encoding="utf-8")

    failures = validate_source_evidence_gate_confirmation_fixture(
        _fixture(),
        repo_root=tmp_path,
    )

    _assert_failure_contains(failures, "canonical AtomicRows bundle must remain absent")


def test_actual_atomicrows_bundle_hash_existing_at_canonical_path_fails(tmp_path):
    bundle_sha_path = _canonical_bundle_sha_path(tmp_path)
    bundle_sha_path.parent.mkdir(parents=True)
    bundle_sha_path.write_text("0" * 64 + "\n", encoding="utf-8")

    failures = validate_source_evidence_gate_confirmation_fixture(
        _fixture(),
        repo_root=tmp_path,
    )

    _assert_failure_contains(
        failures,
        "canonical AtomicRows bundle hash must remain absent",
    )


def test_validator_does_not_mutate_files_or_create_atomicrows_artifacts(tmp_path):
    schema_before = SCHEMA_PATH.read_bytes()
    fixture_before = FIXTURE_PATH.read_bytes()
    fixture_value = _fixture()
    fixture_copy = copy.deepcopy(fixture_value)

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
    assert fixture_value == fixture_copy
    assert not _canonical_bundle_path(tmp_path).exists()
    assert not _canonical_bundle_sha_path(tmp_path).exists()
