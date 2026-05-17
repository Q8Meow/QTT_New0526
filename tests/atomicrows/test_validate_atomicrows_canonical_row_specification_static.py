import copy
import json
from pathlib import Path

import pytest

from tools.validate_atomicrows_canonical_row_specification_static import (
    BLOCKED_STATUS,
    CANONICAL_BUNDLE_RELATIVE_PATH,
    CANONICAL_BUNDLE_SHA_RELATIVE_PATH,
    CANONICAL_ROW_SPECIFICATION_SCOPE_FLAG_EXPECTATIONS,
    EXPECTED_REQUIREMENTS,
    FORBIDDEN_ACTION_FLAGS,
    NO_CLAIM_FLAGS,
    REQUIREMENT_ONLY_STATUS,
    UNBOUND_ROW_COUNT,
    validate_atomicrows_canonical_row_specification_fixture,
    validate_static_surface,
)

SCHEMA_PATH = Path(
    "schemas/atomicrows/atomicrows_canonical_row_specification_audit.schema.json"
)
FIXTURE_PATH = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_canonical_row_specification_required.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _canonical_bundle_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_RELATIVE_PATH.parts)


def _canonical_bundle_sha_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_SHA_RELATIVE_PATH.parts)


def test_valid_synthetic_blocked_fixture_passes():
    assert (
        validate_static_surface(
            schema_path=SCHEMA_PATH,
            fixture_path=FIXTURE_PATH,
            repo_root=Path("."),
        )
        == []
    )

    fixture = _fixture()
    requirements = fixture["canonical_row_specification_requirements"]

    assert fixture["audit_status"] == BLOCKED_STATUS
    assert set(requirements) == set(EXPECTED_REQUIREMENTS)
    assert all(
        entry["current_status"] == REQUIREMENT_ONLY_STATUS
        for entry in requirements.values()
    )
    assert fixture["atomicrows_authority_state"]["claimed_atomicrows_row_count"] == (
        UNBOUND_ROW_COUNT
    )
    assert fixture["canonical_row_specification_scope_flags"]["current_state_blocked"] is True


@pytest.mark.parametrize(
    "requirement_id",
    [
        "CANONICAL_ROW_ID_FIELD_FORMAT_REQUIREMENT",
        "REQUIRED_ROW_FIELDS_DECLARATION",
    ],
)
def test_missing_core_row_specification_requirement_fails(requirement_id):
    fixture = _fixture()
    fixture["canonical_row_specification_requirements"].pop(requirement_id)

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, requirement_id)


@pytest.mark.parametrize(
    "requirement_id",
    [
        "ROW_ORDERING_RULE_DECLARATION",
        "CANONICAL_JSON_KEY_ORDERING_RULE_DECLARATION",
    ],
)
def test_missing_ordering_rule_declaration_fails(requirement_id):
    fixture = _fixture()
    fixture["canonical_row_specification_requirements"].pop(requirement_id)

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, requirement_id)


@pytest.mark.parametrize(
    "requirement_id",
    [
        "UTF8_ENCODING_RULE_DECLARATION",
        "NEWLINE_POLICY_DECLARATION",
        "JSONL_ONE_OBJECT_PER_LINE_RULE_DECLARATION",
    ],
)
def test_missing_utf8_newline_or_jsonl_rule_fails(requirement_id):
    fixture = _fixture()
    fixture["canonical_row_specification_requirements"].pop(requirement_id)

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, requirement_id)


def test_permitting_timestamps_or_os_metadata_without_authority_fails():
    fixture = _fixture()
    fixture["canonical_row_specification_scope_flags"][
        "permits_timestamp_or_os_metadata_without_authority"
    ] = True
    fixture["forbidden_action_flags"]["timestamp_metadata_permission_enabled"] = True
    fixture["forbidden_action_flags"]["os_metadata_permission_enabled"] = True
    fixture["no_claim_flags"]["permits_timestamps_without_authority"] = True
    fixture["no_claim_flags"]["permits_os_metadata_without_authority"] = True

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "permits_timestamp_or_os_metadata_without_authority")
    _assert_failure_contains(failures, "timestamp_metadata_permission_enabled")
    _assert_failure_contains(failures, "os_metadata_permission_enabled")
    _assert_failure_contains(failures, "permits_timestamps_without_authority")
    _assert_failure_contains(failures, "permits_os_metadata_without_authority")


def test_row_creation_claim_and_actual_row_records_fail():
    fixture = _fixture()
    fixture["forbidden_action_flags"]["atomicrows_row_creation_enabled"] = True
    fixture["forbidden_action_flags"]["actual_row_record_creation_enabled"] = True
    fixture["no_claim_flags"]["creates_atomicrows_rows"] = True
    fixture["no_claim_flags"]["creates_actual_row_records"] = True
    fixture["row_records"] = [{"canonical_row_id": "AR-000001"}]

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "atomicrows_row_creation_enabled")
    _assert_failure_contains(failures, "actual_row_record_creation_enabled")
    _assert_failure_contains(failures, "creates_atomicrows_rows")
    _assert_failure_contains(failures, "creates_actual_row_records")
    _assert_failure_contains(failures, "row_records")


@pytest.mark.parametrize(
    "flag_group, flag",
    [
        ("forbidden_action_flags", "atomicrows_bundle_creation_enabled"),
        ("forbidden_action_flags", "atomicrows_bundle_hash_creation_enabled"),
        ("no_claim_flags", "creates_atomicrows_bundle"),
        ("no_claim_flags", "creates_atomicrows_bundle_hash"),
    ],
)
def test_bundle_or_hash_creation_claim_fails(flag_group, flag):
    fixture = _fixture()
    fixture[flag_group][flag] = True

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, flag)


def test_sha_computation_claim_fails():
    fixture = _fixture()
    fixture["forbidden_action_flags"]["atomicrows_sha_computation_enabled"] = True
    fixture["no_claim_flags"]["computes_atomicrows_sha"] = True

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "atomicrows_sha_computation_enabled")
    _assert_failure_contains(failures, "computes_atomicrows_sha")


def test_4183_row_completion_claim_fails():
    fixture = _fixture()
    fixture["forbidden_action_flags"]["row_count_completion_claim_enabled"] = True
    fixture["no_claim_flags"]["claims_4183_row_completion"] = True
    fixture["no_claim_flags"]["claims_atomicrows_row_count_completion"] = True
    fixture["atomicrows_authority_state"]["claimed_atomicrows_row_count"] = "4183"

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "row_count_completion_claim_enabled")
    _assert_failure_contains(failures, "claims_4183_row_completion")
    _assert_failure_contains(failures, "claims_atomicrows_row_count_completion")
    _assert_failure_contains(failures, "claimed_atomicrows_row_count")


@pytest.mark.parametrize(
    "flag_group, flag",
    [
        ("forbidden_action_flags", "blocker_reduction_enabled"),
        ("no_claim_flags", "claims_blocker_reduction"),
        ("atomicrows_authority_state", "blocker_reduction_present"),
    ],
)
def test_blocker_reduction_claim_fails(flag_group, flag):
    fixture = _fixture()
    fixture[flag_group][flag] = True

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, flag)


@pytest.mark.parametrize(
    "flag_group, flag",
    [
        ("forbidden_action_flags", "runtime_enabled"),
        ("forbidden_action_flags", "runtime_execution_enabled"),
        ("forbidden_action_flags", "live_enabled"),
        ("forbidden_action_flags", "source_authority_creation_enabled"),
        ("forbidden_action_flags", "source_acceptance_execution_enabled"),
        ("forbidden_action_flags", "external_fact_acceptance_enabled"),
        ("forbidden_action_flags", "connector_binding_enabled"),
        ("forbidden_action_flags", "connector_semantic_binding_enabled"),
        ("forbidden_action_flags", "private_state_fetch_enabled"),
        ("forbidden_action_flags", "order_execution_enabled"),
        ("forbidden_action_flags", "order_submit_enabled"),
        ("forbidden_action_flags", "profit_claim_enabled"),
        ("no_claim_flags", "creates_runtime_authority"),
        ("no_claim_flags", "creates_runtime_trading_authority"),
        ("no_claim_flags", "creates_live_authority"),
        ("no_claim_flags", "creates_source_authority"),
        ("no_claim_flags", "accepts_source_facts"),
        ("no_claim_flags", "accepts_external_facts"),
        ("no_claim_flags", "binds_connector"),
        ("no_claim_flags", "binds_connector_semantics"),
        ("no_claim_flags", "fetches_private_state"),
        ("no_claim_flags", "submits_orders"),
        ("no_claim_flags", "creates_profit_evidence"),
        ("no_claim_flags", "creates_profit_claim"),
        ("atomicrows_authority_state", "runtime_authority_present"),
        ("atomicrows_authority_state", "source_authority_present"),
        ("atomicrows_authority_state", "connector_authority_present"),
        ("atomicrows_authority_state", "private_state_authority_present"),
        ("atomicrows_authority_state", "order_authority_present"),
        ("atomicrows_authority_state", "profit_authority_present"),
    ],
)
def test_runtime_order_profit_source_connector_private_state_authority_claims_fail(
    flag_group,
    flag,
):
    fixture = _fixture()
    fixture[flag_group][flag] = True

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, flag)


@pytest.mark.parametrize(
    "flag_group, flag",
    [
        ("forbidden_action_flags", "audit_as_bundle_authority_enabled"),
        ("forbidden_action_flags", "audit_as_hash_authority_enabled"),
        ("forbidden_action_flags", "audit_as_unblock_authority_enabled"),
        ("no_claim_flags", "treats_audit_as_actual_bundle_authority"),
        ("no_claim_flags", "treats_audit_as_actual_hash_authority"),
        ("no_claim_flags", "treats_audit_as_unblock_authority"),
        ("atomicrows_authority_state", "bundle_authority_present"),
        ("atomicrows_authority_state", "hash_authority_present"),
        ("atomicrows_authority_state", "row_specification_authority_present"),
        ("atomicrows_authority_state", "row_creation_authority_present"),
        ("atomicrows_authority_state", "completion_authority_present"),
        ("atomicrows_authority_state", "sha_freeze_authority_present"),
    ],
)
def test_audit_as_bundle_hash_row_sha_or_unblock_authority_claim_fails(
    flag_group,
    flag,
):
    fixture = _fixture()
    fixture[flag_group][flag] = True

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, flag)


def test_completion_claim_without_bundle_hash_fails():
    fixture = _fixture()
    fixture["forbidden_action_flags"]["completion_claim_enabled"] = True
    fixture["no_claim_flags"]["claims_atomicrows_completion"] = True
    fixture["canonical_row_specification_scope_flags"][
        "permits_completion_claim_without_bundle_hash"
    ] = True

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "completion_claim_enabled")
    _assert_failure_contains(failures, "claims_atomicrows_completion")
    _assert_failure_contains(failures, "permits_completion_claim_without_bundle_hash")


def test_weakening_no_row_invention_requirement_fails():
    fixture = _fixture()
    fixture["canonical_row_specification_requirements"][
        "NO_ROW_INVENTION_RULE_DECLARATION"
    ]["required_precondition"] = "Rows may be inferred when convenient."
    fixture["canonical_row_specification_scope_flags"]["permits_row_invention"] = True
    fixture["no_claim_flags"]["weakens_no_row_invention"] = True

    failures = validate_atomicrows_canonical_row_specification_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "NO_ROW_INVENTION_RULE_DECLARATION")
    _assert_failure_contains(failures, "permits_row_invention")
    _assert_failure_contains(failures, "weakens_no_row_invention")


def test_every_forbidden_action_flag_fails_when_true():
    for flag in sorted(FORBIDDEN_ACTION_FLAGS):
        fixture = _fixture()
        fixture["forbidden_action_flags"][flag] = True

        failures = validate_atomicrows_canonical_row_specification_fixture(
            fixture,
            repo_root=Path("."),
        )

        _assert_failure_contains(failures, flag)


def test_every_no_claim_flag_fails_when_true():
    for flag in sorted(NO_CLAIM_FLAGS):
        fixture = _fixture()
        fixture["no_claim_flags"][flag] = True

        failures = validate_atomicrows_canonical_row_specification_fixture(
            fixture,
            repo_root=Path("."),
        )

        _assert_failure_contains(failures, flag)


def test_canonical_row_specification_scope_flags_are_fail_closed():
    for flag, expected in sorted(CANONICAL_ROW_SPECIFICATION_SCOPE_FLAG_EXPECTATIONS.items()):
        fixture = _fixture()
        fixture["canonical_row_specification_scope_flags"][flag] = not expected

        failures = validate_atomicrows_canonical_row_specification_fixture(
            fixture,
            repo_root=Path("."),
        )

        _assert_failure_contains(failures, flag)


def test_validator_rejects_actual_bundle_and_hash_paths_in_temp_repo(tmp_path):
    bundle_path = _canonical_bundle_path(tmp_path)
    bundle_sha_path = _canonical_bundle_sha_path(tmp_path)
    bundle_path.parent.mkdir(parents=True)
    bundle_path.write_text("", encoding="utf-8")
    bundle_sha_path.write_text("UNAUTHORIZED_TEST_HASH_PLACEHOLDER", encoding="utf-8")

    failures = validate_static_surface(
        schema_path=SCHEMA_PATH,
        fixture_path=FIXTURE_PATH,
        repo_root=tmp_path,
    )

    _assert_failure_contains(failures, "canonical AtomicRows bundle must remain absent")
    _assert_failure_contains(failures, "canonical AtomicRows bundle hash must remain absent")


def test_validator_does_not_create_atomicrows_bundle_or_hash_files(tmp_path):
    bundle_path = _canonical_bundle_path(tmp_path)
    bundle_sha_path = _canonical_bundle_sha_path(tmp_path)

    assert not bundle_path.exists()
    assert not bundle_sha_path.exists()
    assert (
        validate_static_surface(
            schema_path=SCHEMA_PATH,
            fixture_path=FIXTURE_PATH,
            repo_root=tmp_path,
        )
        == []
    )
    assert not bundle_path.exists()
    assert not bundle_sha_path.exists()


def test_fixture_has_no_mutating_authority_and_no_actual_rows():
    fixture = _fixture()
    frozen = copy.deepcopy(fixture)

    assert all(value is False for value in fixture["forbidden_action_flags"].values())
    assert all(value is False for value in fixture["no_claim_flags"].values())
    assert not any(
        entry["current_status"] != REQUIREMENT_ONLY_STATUS
        for entry in fixture["canonical_row_specification_requirements"].values()
    )
    assert fixture["atomicrows_authority_state"]["canonical_bundle_present"] is False
    assert fixture["atomicrows_authority_state"]["canonical_bundle_sha_present"] is False
    assert fixture["atomicrows_authority_state"]["row_creation_authority_present"] is False
    assert "row_records" not in fixture
    assert frozen == fixture


def test_canonical_atomicrows_bundle_and_hash_are_absent_in_bootstrap_repo():
    assert _canonical_bundle_path(Path(".")).exists()
    assert not _canonical_bundle_sha_path(Path(".")).exists()
