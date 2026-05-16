import copy
import json
from pathlib import Path

import pytest

from tools import validate_atomicrows_readiness_static as validator
from tools.validate_atomicrows_readiness_static import (
    BLOCKED_STATUS,
    CANONICAL_BUNDLE_RELATIVE_PATH,
    CANONICAL_BUNDLE_SHA_RELATIVE_PATH,
    FORBIDDEN_ACTION_FLAGS,
    NO_CLAIM_FLAGS,
    READINESS_SCOPE_FLAG_EXPECTATIONS,
    UNBOUND_ROW_COUNT,
    validate_atomicrows_readiness_fixture,
    validate_static_surface,
)

SCHEMA_PATH = Path("schemas/atomicrows/atomicrows_readiness_audit.schema.json")
FIXTURE_PATH = Path(
    "tests/fixtures/atomicrows/synthetic_atomicrows_readiness_blocked.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _canonical_bundle_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_RELATIVE_PATH.parts)


def _canonical_bundle_sha_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_SHA_RELATIVE_PATH.parts)


def test_valid_blocked_state_synthetic_fixture_passes():
    assert (
        validate_static_surface(
            schema_path=SCHEMA_PATH,
            fixture_path=FIXTURE_PATH,
            repo_root=Path("."),
        )
        == []
    )

    fixture = _fixture()
    assert fixture["audit_status"] == BLOCKED_STATUS
    assert fixture["atomicrows_authority_state"]["audit_status"] == BLOCKED_STATUS
    assert fixture["atomicrows_authority_state"]["claimed_atomicrows_row_count"] == (
        UNBOUND_ROW_COUNT
    )
    assert fixture["readiness_scope_flags"]["blocked_pending_bundle_authority"] is True


def test_missing_blocked_state_authority_flag_fails():
    fixture = _fixture()
    fixture["readiness_scope_flags"].pop("blocked_pending_bundle_authority")

    failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

    _assert_failure_contains(failures, "blocked_pending_bundle_authority")


@pytest.mark.parametrize(
    "field_path",
    [
        ("audit_status",),
        ("atomicrows_authority_state", "audit_status"),
    ],
)
def test_missing_blocked_state_status_fails(field_path):
    fixture = _fixture()
    target = fixture
    for part in field_path[:-1]:
        target = target[part]
    target[field_path[-1]] = "COMPLETE"

    failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

    _assert_failure_contains(failures, BLOCKED_STATUS)


def test_completion_claim_without_real_bundle_hash_authority_fails():
    fixture = _fixture()
    fixture["forbidden_action_flags"]["completion_claim_enabled"] = True
    fixture["no_claim_flags"]["claims_atomicrows_completion"] = True
    fixture["atomicrows_authority_state"]["completion_authority_present"] = True

    failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

    _assert_failure_contains(failures, "completion_claim_enabled")
    _assert_failure_contains(failures, "claims_atomicrows_completion")
    _assert_failure_contains(failures, "completion_authority_present")


def test_row_count_completion_claim_fails_when_bundle_hash_are_absent():
    fixture = _fixture()
    fixture["forbidden_action_flags"]["row_count_completion_claim_enabled"] = True
    fixture["no_claim_flags"]["claims_atomicrows_row_count_completion"] = True
    fixture["no_claim_flags"]["claims_4183_row_completion"] = True
    fixture["atomicrows_authority_state"]["claimed_atomicrows_row_count"] = "4183"

    failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

    _assert_failure_contains(failures, "row_count_completion_claim_enabled")
    _assert_failure_contains(failures, "claims_atomicrows_row_count_completion")
    _assert_failure_contains(failures, "claims_4183_row_completion")
    _assert_failure_contains(failures, "claimed_atomicrows_row_count")


@pytest.mark.parametrize(
    "flag_group, flag",
    [
        ("forbidden_action_flags", "atomicrows_bundle_creation_enabled"),
        ("forbidden_action_flags", "atomicrows_bundle_hash_creation_enabled"),
        ("no_claim_flags", "creates_atomicrows_bundle"),
        ("no_claim_flags", "creates_atomicrows_bundle_hash"),
    ],
)
def test_bundle_or_hash_creation_flag_true_fails(flag_group, flag):
    fixture = _fixture()
    fixture[flag_group][flag] = True

    failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

    _assert_failure_contains(failures, flag)


@pytest.mark.parametrize(
    "flag",
    [
        "row_invention_enabled",
        "synthetic_row_completion_enabled",
        "generated_authoritative_row_bundle_enabled",
        "atomicrows_sha_computation_enabled",
        "sha_freeze_enabled",
    ],
)
def test_row_invention_synthetic_completion_authoritative_bundle_or_sha_flags_fail(flag):
    fixture = _fixture()
    fixture["forbidden_action_flags"][flag] = True

    failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

    _assert_failure_contains(failures, flag)


@pytest.mark.parametrize(
    "flag",
    [
        "contains_atomicrows_rows",
        "contains_synthetic_completed_rows",
        "contains_generated_authoritative_row_bundle",
        "computes_atomicrows_sha",
        "creates_sha_freeze_authority",
    ],
)
def test_row_invention_synthetic_completion_authoritative_bundle_or_sha_claims_fail(flag):
    fixture = _fixture()
    fixture["no_claim_flags"][flag] = True

    failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

    _assert_failure_contains(failures, flag)


@pytest.mark.parametrize(
    "flag_group, flag",
    [
        ("forbidden_action_flags", "blocker_reduction_enabled"),
        ("no_claim_flags", "claims_blocker_reduction"),
    ],
)
def test_blocker_reduction_flag_true_fails(flag_group, flag):
    fixture = _fixture()
    fixture[flag_group][flag] = True

    failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

    _assert_failure_contains(failures, flag)


@pytest.mark.parametrize(
    "flag",
    [
        "runtime_enabled",
        "runtime_execution_enabled",
        "runtime_resolver_snapshot_creation_enabled",
        "replay_execution_enabled",
        "paper_execution_enabled",
        "live_enabled",
        "source_retrieval_enabled",
        "source_acceptance_execution_enabled",
        "connector_binding_enabled",
        "connector_semantic_binding_enabled",
        "private_state_fetch_enabled",
        "order_execution_enabled",
        "order_submit_enabled",
        "order_cancel_enabled",
        "order_reduce_enabled",
        "order_close_enabled",
        "profit_claim_enabled",
    ],
)
def test_runtime_live_order_profit_source_connector_private_state_flags_true_fail(flag):
    fixture = _fixture()
    fixture["forbidden_action_flags"][flag] = True

    failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

    _assert_failure_contains(failures, flag)


@pytest.mark.parametrize(
    "flag",
    [
        "creates_runtime_authority",
        "creates_runtime_trading_authority",
        "creates_live_authority",
        "creates_source_retrieval",
        "accepts_source_facts",
        "binds_connector",
        "binds_connector_semantics",
        "fetches_private_state",
        "creates_runtime_resolver_snapshot",
        "executes_replay",
        "executes_paper",
        "submits_orders",
        "cancels_orders",
        "reduces_orders",
        "closes_orders",
        "creates_profit_evidence",
    ],
)
def test_runtime_live_order_profit_source_connector_private_state_claims_fail(flag):
    fixture = _fixture()
    fixture["no_claim_flags"][flag] = True

    failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

    _assert_failure_contains(failures, flag)


def test_every_forbidden_action_flag_fails_when_true():
    for flag in sorted(FORBIDDEN_ACTION_FLAGS):
        fixture = _fixture()
        fixture["forbidden_action_flags"][flag] = True

        failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

        _assert_failure_contains(failures, flag)


def test_every_no_claim_flag_fails_when_true():
    for flag in sorted(NO_CLAIM_FLAGS):
        fixture = _fixture()
        fixture["no_claim_flags"][flag] = True

        failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

        _assert_failure_contains(failures, flag)


def test_readiness_scope_flags_are_fail_closed():
    for flag, expected in sorted(READINESS_SCOPE_FLAG_EXPECTATIONS.items()):
        fixture = _fixture()
        fixture["readiness_scope_flags"][flag] = not expected

        failures = validate_atomicrows_readiness_fixture(fixture, repo_root=Path("."))

        _assert_failure_contains(failures, flag)


def test_filesystem_presence_mismatch_fails(monkeypatch):
    monkeypatch.setattr(validator, "_actual_presence", lambda repo_root: (True, True))

    failures = validate_atomicrows_readiness_fixture(_fixture(), repo_root=Path("."))

    _assert_failure_contains(failures, "canonical_bundle_sha_present")


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


def test_fixture_has_no_mutating_authority_and_no_row_claims():
    fixture = _fixture()
    frozen = copy.deepcopy(fixture)

    assert all(value is False for value in fixture["forbidden_action_flags"].values())
    assert all(value is False for value in fixture["no_claim_flags"].values())
    assert fixture["atomicrows_authority_state"]["canonical_bundle_present"] is False
    assert fixture["atomicrows_authority_state"]["canonical_bundle_sha_present"] is False
    assert fixture["atomicrows_authority_state"]["bundle_authority_present"] is False
    assert fixture["atomicrows_authority_state"]["completion_authority_present"] is False
    assert frozen == fixture


def test_canonical_atomicrows_bundle_and_hash_are_absent_in_bootstrap_repo():
    assert _canonical_bundle_path(Path(".")).exists()
    assert not _canonical_bundle_sha_path(Path(".")).exists()
