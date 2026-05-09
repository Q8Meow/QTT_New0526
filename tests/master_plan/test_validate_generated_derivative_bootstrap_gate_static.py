import copy
import json
from pathlib import Path

import pytest

from tools.validate_generated_derivative_bootstrap_gate_static import (
    AUTHORITY_SCOPE_FLAG_EXPECTATIONS,
    CANONICAL_BUNDLE_RELATIVE_PATH,
    CANONICAL_BUNDLE_SHA_RELATIVE_PATH,
    DERIVATIVE_ABSENT_STATUS,
    FORBIDDEN_ACTION_FLAGS,
    GATE_MODE,
    METADATA_FIELDS,
    NO_CLAIM_FLAGS,
    validate_generated_derivative_bootstrap_gate_fixture,
    validate_static_surface,
)


SCHEMA_PATH = Path("schemas/master_plan/generated_derivative_bootstrap_gate.schema.json")
FIXTURE_PATH = Path(
    "tests/fixtures/master_plan/"
    "synthetic_generated_derivative_bootstrap_gate.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _output(fixture: dict) -> dict:
    return fixture["generated_derivative_outputs"][0]


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _validate_fixture(fixture: dict, repo_root: Path = Path(".")) -> list[str]:
    return validate_generated_derivative_bootstrap_gate_fixture(
        fixture,
        repo_root=repo_root,
    )


def _canonical_bundle_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_RELATIVE_PATH.parts)


def _canonical_bundle_sha_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_SHA_RELATIVE_PATH.parts)


def test_valid_bootstrap_fixture_passes():
    assert (
        validate_static_surface(
            schema_path=SCHEMA_PATH,
            fixture_path=FIXTURE_PATH,
            repo_root=Path("."),
        )
        == []
    )

    fixture = _fixture()
    assert fixture["gate_mode"] == GATE_MODE
    assert _output(fixture)["derivative_status"] == DERIVATIVE_ABSENT_STATUS
    assert fixture["bootstrap_gate_receipt"]["completion_mode_claimed"] is False
    assert fixture["coverage_ledger_report"]["blockers_reduced"] is False


def test_missing_gate_mode_fails():
    fixture = _fixture()
    fixture.pop("gate_mode")

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "gate_mode")


def test_completion_mode_claim_fails():
    fixture = _fixture()
    fixture["gate_mode"] = "COMPLETION"
    fixture["bootstrap_gate_receipt"]["completion_mode_claimed"] = True
    fixture["completion_mode_requirements"]["current_pr_claims_completion"] = True
    fixture["no_claim_flags"]["claims_completion_mode"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "gate_mode")
    _assert_failure_contains(failures, "completion_mode_claimed")
    _assert_failure_contains(failures, "current_pr_claims_completion")
    _assert_failure_contains(failures, "claims_completion_mode")


def test_4183_row_coverage_claim_fails():
    fixture = _fixture()
    fixture["bootstrap_gate_receipt"]["claims_4183_row_derivative_coverage"] = True
    fixture["completion_mode_requirements"][
        "current_pr_claims_4183_row_derivative_coverage"
    ] = True
    fixture["coverage_ledger_report"]["claims_4183_row_derivative_coverage"] = True
    fixture["no_claim_flags"]["claims_4183_row_derivative_coverage"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "claims_4183_row_derivative_coverage")
    _assert_failure_contains(
        failures,
        "current_pr_claims_4183_row_derivative_coverage",
    )


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "atomicrows_bundle_creation_enabled"),
        ("authority_scope_flags", "atomicrows_bundle_creation_allowed"),
        ("bootstrap_gate_receipt", "atomicrows_bundle_created"),
        ("no_claim_flags", "creates_atomicrows_bundle"),
        ("no_claim_flags", "contains_atomicrows_bundle"),
    ],
)
def test_atomicrows_bundle_creation_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "atomicrows_bundle_hash_creation_enabled"),
        ("authority_scope_flags", "atomicrows_bundle_hash_creation_allowed"),
        ("bootstrap_gate_receipt", "atomicrows_hash_created"),
        ("no_claim_flags", "creates_atomicrows_bundle_hash"),
        ("no_claim_flags", "contains_atomicrows_bundle_hash"),
    ],
)
def test_atomicrows_hash_creation_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "atomicrows_sha_computation_enabled"),
        ("forbidden_action_flags", "atomicrows_sha_authority_enabled"),
        ("authority_scope_flags", "atomicrows_sha_authority_allowed"),
        ("bootstrap_gate_receipt", "atomicrows_sha_authority_created"),
        ("no_claim_flags", "computes_atomicrows_sha"),
        ("no_claim_flags", "claims_atomicrows_sha_authority"),
    ],
)
def test_sha_authority_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "atomicrows_row_creation_enabled"),
        ("forbidden_action_flags", "actual_row_record_creation_enabled"),
        ("authority_scope_flags", "atomicrows_row_creation_allowed"),
        ("bootstrap_gate_receipt", "atomicrows_rows_created"),
        ("no_claim_flags", "creates_atomicrows_rows"),
        ("no_claim_flags", "creates_atomicrows_row_records"),
        ("no_claim_flags", "contains_atomicrows_row_records"),
    ],
)
def test_row_creation_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, field_path[1])


def test_actual_row_records_fail():
    fixture = _fixture()
    fixture["row_records"] = [{"atomic_parameter_row_id": "atomic_parameter_row_0001"}]

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "row_records")


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "blocker_reduction_enabled"),
        ("authority_scope_flags", "coverage_ledger_blocker_reduction_allowed"),
        ("coverage_ledger_report", "blocker_reduction_allowed"),
        ("coverage_ledger_report", "blockers_reduced"),
        ("no_claim_flags", "claims_blocker_reduction"),
    ],
)
def test_blocker_reduction_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "stage1_packet_schema_unblock_enabled"),
        ("authority_scope_flags", "stage1_packet_schema_unblock_allowed"),
        ("bootstrap_gate_receipt", "stage1_packet_schema_unblocked"),
        ("coverage_ledger_report", "stage1_packet_schema_unblocking_claimed"),
        ("no_claim_flags", "claims_stage1_packet_schema_unblock"),
    ],
)
def test_stage1_packet_schema_unblock_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "source_fact_acceptance_enabled"),
        ("authority_scope_flags", "source_fact_acceptance_allowed"),
        ("no_claim_flags", "claims_source_fact_acceptance"),
        ("no_claim_flags", "accepts_source_facts"),
    ],
)
def test_source_fact_acceptance_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "connector_binding_enabled"),
        ("forbidden_action_flags", "connector_semantic_binding_enabled"),
        ("authority_scope_flags", "connector_binding_allowed"),
        ("authority_scope_flags", "connector_semantic_binding_allowed"),
        ("no_claim_flags", "binds_connector"),
        ("no_claim_flags", "claims_connector_semantic_binding"),
    ],
)
def test_connector_binding_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "runtime_trading_enabled"),
        ("forbidden_action_flags", "runtime_execution_enabled"),
        ("forbidden_action_flags", "live_reachability_enabled"),
        ("forbidden_action_flags", "order_execution_enabled"),
        ("forbidden_action_flags", "order_submit_enabled"),
        ("forbidden_action_flags", "private_state_fetch_enabled"),
        ("forbidden_action_flags", "profit_claim_enabled"),
        ("forbidden_action_flags", "profit_evidence_creation_enabled"),
        ("authority_scope_flags", "runtime_trading_allowed"),
        ("authority_scope_flags", "live_reachability_allowed"),
        ("authority_scope_flags", "order_execution_allowed"),
        ("authority_scope_flags", "private_state_fetch_allowed"),
        ("authority_scope_flags", "profit_claim_allowed"),
        ("no_claim_flags", "creates_runtime_trading_authority"),
        ("no_claim_flags", "creates_live_reachability"),
        ("no_claim_flags", "creates_order_execution_authority"),
        ("no_claim_flags", "submits_orders"),
        ("no_claim_flags", "fetches_private_state"),
        ("no_claim_flags", "creates_profit_evidence"),
        ("no_claim_flags", "creates_profit_claim"),
    ],
)
def test_runtime_live_order_private_state_profit_authority_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "replay_execution_enabled"),
        ("forbidden_action_flags", "paper_execution_enabled"),
        ("forbidden_action_flags", "neural_training_enabled"),
        ("forbidden_action_flags", "neural_inference_enabled"),
        ("authority_scope_flags", "replay_execution_allowed"),
        ("authority_scope_flags", "paper_execution_allowed"),
        ("authority_scope_flags", "neural_training_allowed"),
        ("authority_scope_flags", "neural_inference_allowed"),
        ("no_claim_flags", "executes_replay"),
        ("no_claim_flags", "executes_paper"),
        ("no_claim_flags", "trains_neural_models"),
        ("no_claim_flags", "runs_neural_models"),
    ],
)
def test_replay_paper_neural_claims_fail(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize("metadata_field", sorted(METADATA_FIELDS))
def test_missing_metadata_fields_fail(metadata_field):
    fixture = _fixture()
    _output(fixture)["metadata"].pop(metadata_field)

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, metadata_field)


def test_missing_declared_writer_identity_fails():
    fixture = _fixture()
    _output(fixture).pop("declared_writer_identity")

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "declared_writer_identity")


def test_manual_edit_permission_fails():
    fixture = _fixture()
    _output(fixture)["manual_edit_authority_allowed"] = True
    _output(fixture)["declared_writer_identity"]["manual_edit_authority_allowed"] = True
    fixture["forbidden_action_flags"]["manual_edit_enabled"] = True
    fixture["no_claim_flags"]["permits_manual_editing"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "manual_edit_authority_allowed")
    _assert_failure_contains(failures, "manual_edit_enabled")
    _assert_failure_contains(failures, "permits_manual_editing")


def test_atomicrows_absent_without_not_created_status_fails():
    fixture = _fixture()
    _output(fixture)["derivative_status"] = "CREATED_WITHOUT_ATOMICROWS_BUNDLE"

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, DERIVATIVE_ABSENT_STATUS)


def test_actual_atomicrows_bundle_existing_at_canonical_path_fails_bootstrap_validation(
    tmp_path,
):
    bundle_path = _canonical_bundle_path(tmp_path)
    bundle_path.parent.mkdir(parents=True)
    bundle_path.write_text("", encoding="utf-8")

    failures = validate_static_surface(
        schema_path=SCHEMA_PATH,
        fixture_path=FIXTURE_PATH,
        repo_root=tmp_path,
    )

    _assert_failure_contains(failures, "canonical AtomicRows bundle must remain absent")


def test_actual_atomicrows_sha_existing_at_canonical_path_fails_bootstrap_validation(
    tmp_path,
):
    sha_path = _canonical_bundle_sha_path(tmp_path)
    sha_path.parent.mkdir(parents=True)
    sha_path.write_text("UNAUTHORIZED_TEST_HASH_PLACEHOLDER", encoding="utf-8")

    failures = validate_static_surface(
        schema_path=SCHEMA_PATH,
        fixture_path=FIXTURE_PATH,
        repo_root=tmp_path,
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


def test_authority_scope_flags_are_fail_closed():
    for flag, expected in sorted(AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()):
        fixture = _fixture()
        fixture["authority_scope_flags"][flag] = not expected

        failures = _validate_fixture(fixture)

        _assert_failure_contains(failures, flag)


def test_validator_does_not_mutate_fixture_or_create_bundle_or_hash(tmp_path):
    fixture = _fixture()
    frozen = copy.deepcopy(fixture)
    bundle_path = _canonical_bundle_path(tmp_path)
    sha_path = _canonical_bundle_sha_path(tmp_path)

    assert _validate_fixture(fixture, repo_root=tmp_path) == []

    assert fixture == frozen
    assert not bundle_path.exists()
    assert not sha_path.exists()


def test_canonical_atomicrows_bundle_and_hash_are_absent_in_bootstrap_repo():
    assert not _canonical_bundle_path(Path(".")).exists()
    assert not _canonical_bundle_sha_path(Path(".")).exists()
