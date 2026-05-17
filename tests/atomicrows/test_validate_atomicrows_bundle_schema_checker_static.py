import copy
import json
from pathlib import Path

import pytest

from tools.validate_atomicrows_bundle_schema_checker_static import (
    BOOTSTRAP_MODE,
    CANONICAL_BUNDLE_RELATIVE_PATH,
    CANONICAL_BUNDLE_SHA_RELATIVE_PATH,
    CHECK_STATUS,
    CHECKER_CAPABILITY_EXPECTATIONS,
    COMPLETION_REQUIREMENT_EXPECTATIONS,
    FORBIDDEN_ACTION_FLAGS,
    NO_CLAIM_FLAGS,
    UNBOUND_ROW_COUNT,
    validate_atomicrows_bundle_schema_checker_fixture,
    validate_static_surface,
)

ROW_SCHEMA_PATH = Path("schemas/atomicrows/atomic_parameter_row.schema.json")
BUNDLE_SCHEMA_PATH = Path("schemas/atomicrows/atomic_row_bundle.schema.json")
FIXTURE_PATH = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_bundle_bootstrap_absent.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _canonical_bundle_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_RELATIVE_PATH.parts)


def _canonical_bundle_sha_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_SHA_RELATIVE_PATH.parts)


def test_valid_bootstrap_absent_fixture_passes():
    assert (
        validate_static_surface(
            row_schema_path=ROW_SCHEMA_PATH,
            bundle_schema_path=BUNDLE_SCHEMA_PATH,
            fixture_path=FIXTURE_PATH,
            repo_root=Path("."),
        )
        == []
    )

    fixture = _fixture()
    assert fixture["checker_mode"] == BOOTSTRAP_MODE
    assert fixture["check_status"] == CHECK_STATUS
    assert fixture["bootstrap_absent_receipt"]["canonical_bundle_state"] == "NOT_CREATED"
    assert fixture["bootstrap_absent_receipt"]["canonical_bundle_sha_state"] == (
        "NOT_CREATED"
    )
    assert fixture["completion_mode_requirements"][
        "required_launch_row_count"
    ] == 4183
    assert fixture["completion_mode_requirements"]["completion_mode_satisfied"] is False
    assert fixture["atomicrows_authority_state"]["claimed_atomicrows_row_count"] == (
        UNBOUND_ROW_COUNT
    )


def test_missing_canonical_bundle_path_fails():
    fixture = _fixture()
    fixture["expected_canonical_paths"].pop("canonical_bundle_path")

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "canonical_bundle_path")


def test_wrong_canonical_bundle_path_fails():
    fixture = _fixture()
    fixture["expected_canonical_paths"]["canonical_bundle_path"] = (
        "docs/master_plan/atomic_rows/Wrong.bundle.jsonl"
    )

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(
        failures,
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
    )


def test_missing_canonical_sha_path_fails():
    fixture = _fixture()
    fixture["expected_canonical_paths"].pop("canonical_bundle_sha_path")

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "canonical_bundle_sha_path")


def test_wrong_canonical_sha_path_fails():
    fixture = _fixture()
    fixture["expected_canonical_paths"]["canonical_bundle_sha_path"] = (
        "docs/master_plan/atomic_rows/Wrong.bundle.sha256"
    )

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(
        failures,
        "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256",
    )


def test_missing_bootstrap_absent_mode_fails():
    fixture = _fixture()
    fixture["bootstrap_absent_receipt"].pop("bootstrap_absent_mode_explicit")

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "bootstrap_absent_mode_explicit")


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "atomicrows_bundle_creation_enabled"),
        ("no_claim_flags", "creates_atomicrows_bundle"),
        ("bootstrap_absent_receipt", "created_bundle"),
        ("checker_capabilities", "creates_atomicrows_bundle"),
    ],
)
def test_bundle_creation_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "atomicrows_bundle_hash_creation_enabled"),
        ("no_claim_flags", "creates_atomicrows_bundle_hash"),
        ("bootstrap_absent_receipt", "created_hash"),
        ("checker_capabilities", "creates_atomicrows_bundle_hash"),
    ],
)
def test_hash_creation_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "atomicrows_sha_authority_enabled"),
        ("no_claim_flags", "claims_sha_authority"),
        ("bootstrap_absent_receipt", "created_sha_authority"),
        ("checker_capabilities", "creates_sha_authority"),
        ("atomicrows_authority_state", "sha_authority_present"),
    ],
)
def test_sha_authority_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "atomicrows_row_creation_enabled"),
        ("forbidden_action_flags", "actual_row_record_creation_enabled"),
        ("no_claim_flags", "creates_atomicrows_rows"),
        ("no_claim_flags", "creates_canonical_row_records"),
        ("bootstrap_absent_receipt", "created_rows"),
        ("checker_capabilities", "creates_atomicrows_rows"),
        ("atomicrows_authority_state", "row_creation_authority_present"),
    ],
)
def test_row_creation_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, field_path[1])


def test_actual_row_record_payload_fails():
    fixture = _fixture()
    fixture["row_records"] = [{"atomic_parameter_row_id": "atomic_parameter_row_0001"}]

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "row_records")


def test_4183_row_completion_claim_fails():
    fixture = _fixture()
    fixture["forbidden_action_flags"]["row_count_completion_claim_enabled"] = True
    fixture["no_claim_flags"]["claims_4183_row_completion"] = True
    fixture["no_claim_flags"]["claims_atomicrows_row_count_completion"] = True
    fixture["completion_mode_requirements"]["completion_mode_satisfied"] = True
    fixture["completion_mode_requirements"]["current_pr_creates_completion_authority"] = True
    fixture["atomicrows_authority_state"]["claimed_atomicrows_row_count"] = "4183"

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, "claims_4183_row_completion")
    _assert_failure_contains(failures, "claims_atomicrows_row_count_completion")
    _assert_failure_contains(failures, "completion_mode_satisfied")
    _assert_failure_contains(failures, "current_pr_creates_completion_authority")
    _assert_failure_contains(failures, "claimed_atomicrows_row_count")


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "blocker_reduction_enabled"),
        ("no_claim_flags", "claims_blocker_reduction"),
        ("bootstrap_absent_receipt", "reduced_blockers"),
        ("checker_capabilities", "reduces_blockers"),
        ("atomicrows_authority_state", "blocker_reduction_present"),
    ],
)
def test_blocker_reduction_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "runtime_trading_enabled"),
        ("forbidden_action_flags", "runtime_execution_enabled"),
        ("forbidden_action_flags", "live_reachability_enabled"),
        ("forbidden_action_flags", "order_execution_enabled"),
        ("forbidden_action_flags", "order_submit_enabled"),
        ("forbidden_action_flags", "profit_claim_enabled"),
        ("no_claim_flags", "creates_runtime_trading_authority"),
        ("no_claim_flags", "creates_live_reachability"),
        ("no_claim_flags", "submits_orders"),
        ("no_claim_flags", "creates_order_execution_authority"),
        ("no_claim_flags", "creates_profit_evidence"),
        ("checker_capabilities", "allows_runtime_trading_authority"),
        ("checker_capabilities", "allows_live_reachability"),
        ("checker_capabilities", "allows_order_execution"),
        ("checker_capabilities", "allows_profit_evidence"),
        ("atomicrows_authority_state", "runtime_authority_present"),
        ("atomicrows_authority_state", "live_reachability_authority_present"),
        ("atomicrows_authority_state", "order_execution_authority_present"),
        ("atomicrows_authority_state", "profit_authority_present"),
    ],
)
def test_runtime_order_profit_authority_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "source_fact_acceptance_enabled"),
        ("forbidden_action_flags", "connector_binding_enabled"),
        ("forbidden_action_flags", "private_state_fetch_enabled"),
        ("forbidden_action_flags", "replay_execution_enabled"),
        ("forbidden_action_flags", "paper_execution_enabled"),
        ("no_claim_flags", "accepts_source_facts"),
        ("no_claim_flags", "binds_connector"),
        ("no_claim_flags", "fetches_private_state"),
        ("no_claim_flags", "executes_replay"),
        ("no_claim_flags", "executes_paper"),
        ("checker_capabilities", "allows_source_fact_acceptance"),
        ("checker_capabilities", "allows_connector_binding"),
        ("checker_capabilities", "allows_private_state_fetch"),
        ("checker_capabilities", "allows_replay_or_paper_success"),
        ("atomicrows_authority_state", "source_fact_acceptance_authority_present"),
        ("atomicrows_authority_state", "connector_authority_present"),
        ("atomicrows_authority_state", "private_state_authority_present"),
    ],
)
def test_source_connector_private_state_replay_paper_claim_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, field_path[1])


@pytest.mark.parametrize(
    "field_path",
    [
        ("forbidden_action_flags", "mutate_canonical_bundle_enabled"),
        ("forbidden_action_flags", "normalize_canonical_bundle_in_place_enabled"),
        ("forbidden_action_flags", "repair_canonical_bundle_in_place_enabled"),
        ("checker_capabilities", "creates_or_mutates_files"),
        ("checker_capabilities", "mutates_canonical_bundle_in_place"),
        ("checker_capabilities", "normalizes_canonical_bundle_in_place"),
        ("checker_capabilities", "repairs_canonical_bundle_in_place"),
    ],
)
def test_mutate_normalize_repair_in_place_permission_fails(field_path):
    fixture = _fixture()
    fixture[field_path[0]][field_path[1]] = True

    failures = validate_atomicrows_bundle_schema_checker_fixture(
        fixture,
        repo_root=Path("."),
    )

    _assert_failure_contains(failures, field_path[1])


def test_actual_atomicrows_bundle_existing_at_canonical_path_fails_bootstrap_validation(
    tmp_path,
):
    bundle_path = _canonical_bundle_path(tmp_path)
    bundle_path.parent.mkdir(parents=True)
    bundle_path.write_text("", encoding="utf-8")

    failures = validate_static_surface(
        row_schema_path=ROW_SCHEMA_PATH,
        bundle_schema_path=BUNDLE_SCHEMA_PATH,
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
        row_schema_path=ROW_SCHEMA_PATH,
        bundle_schema_path=BUNDLE_SCHEMA_PATH,
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

        failures = validate_atomicrows_bundle_schema_checker_fixture(
            fixture,
            repo_root=Path("."),
        )

        _assert_failure_contains(failures, flag)


def test_every_no_claim_flag_fails_when_true():
    for flag in sorted(NO_CLAIM_FLAGS):
        fixture = _fixture()
        fixture["no_claim_flags"][flag] = True

        failures = validate_atomicrows_bundle_schema_checker_fixture(
            fixture,
            repo_root=Path("."),
        )

        _assert_failure_contains(failures, flag)


def test_checker_capabilities_are_fail_closed():
    for flag, expected in sorted(CHECKER_CAPABILITY_EXPECTATIONS.items()):
        fixture = _fixture()
        fixture["checker_capabilities"][flag] = not expected

        failures = validate_atomicrows_bundle_schema_checker_fixture(
            fixture,
            repo_root=Path("."),
        )

        _assert_failure_contains(failures, flag)


def test_completion_mode_requirements_are_declared_but_not_satisfied():
    for field, expected in sorted(COMPLETION_REQUIREMENT_EXPECTATIONS.items()):
        fixture = _fixture()
        fixture["completion_mode_requirements"][field] = (
            False if expected is True else True
        )

        failures = validate_atomicrows_bundle_schema_checker_fixture(
            fixture,
            repo_root=Path("."),
        )

        _assert_failure_contains(failures, field)


def test_validator_does_not_create_atomicrows_bundle_or_hash_files(tmp_path):
    bundle_path = _canonical_bundle_path(tmp_path)
    sha_path = _canonical_bundle_sha_path(tmp_path)

    assert not bundle_path.exists()
    assert not sha_path.exists()
    assert (
        validate_static_surface(
            row_schema_path=ROW_SCHEMA_PATH,
            bundle_schema_path=BUNDLE_SCHEMA_PATH,
            fixture_path=FIXTURE_PATH,
            repo_root=tmp_path,
        )
        == []
    )
    assert not bundle_path.exists()
    assert not sha_path.exists()


def test_fixture_has_no_mutating_authority_and_no_actual_rows():
    fixture = _fixture()
    frozen = copy.deepcopy(fixture)

    assert all(value is False for value in fixture["forbidden_action_flags"].values())
    assert all(value is False for value in fixture["no_claim_flags"].values())
    assert fixture["bootstrap_absent_receipt"]["completion_mode_satisfied"] is False
    assert fixture["atomicrows_authority_state"]["canonical_bundle_present"] is False
    assert fixture["atomicrows_authority_state"]["canonical_bundle_sha_present"] is False
    assert fixture["atomicrows_authority_state"]["completion_authority_present"] is False
    assert "row_records" not in fixture
    assert frozen == fixture


def test_canonical_atomicrows_bundle_and_hash_are_absent_in_bootstrap_repo():
    assert _canonical_bundle_path(Path(".")).exists()
    assert not _canonical_bundle_sha_path(Path(".")).exists()
