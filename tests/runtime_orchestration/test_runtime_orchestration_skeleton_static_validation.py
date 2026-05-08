import json
from pathlib import Path

from tools.validate_runtime_orchestration_static import (
    RUNTIME_FORBIDDEN_ACTION_FLAGS,
    validate_runtime_orchestration_skeleton_fixture,
    validate_static_surface,
)


SCHEMA_PATH = Path(
    "schemas/runtime_orchestration/runtime_orchestration_skeleton.schema.json"
)
FIXTURE_PATH = Path(
    "tests/fixtures/runtime_orchestration/"
    "synthetic_runtime_orchestration_skeleton.v1.fixture.json"
)
EXPECTED_FIXTURE_NAME = "synthetic_runtime_orchestration_skeleton.v1.fixture.json"
SYNTHETIC_AUTHORITY_CLASS = (
    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_RUNTIME_ORCHESTRATION_NOT_SOURCE_FACT"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _skeleton(fixture: dict) -> dict:
    return fixture["runtime_orchestration_skeleton"]


def _receipt(fixture: dict) -> dict:
    return _skeleton(fixture)["receipt_envelopes"][0]


def test_runtime_orchestration_static_validator_accepts_schema_and_fixture():
    failures = validate_static_surface(schema_path=SCHEMA_PATH, fixture_path=FIXTURE_PATH)

    assert failures == []


def test_valid_synthetic_runtime_orchestration_skeleton_fixture_passes():
    fixture = _fixture()

    assert FIXTURE_PATH.name == EXPECTED_FIXTURE_NAME
    assert fixture["fixture_id"] == "SYNTHETIC_PR22_RUNTIME_ORCHESTRATION_SKELETON_FIXTURE"
    assert fixture["fixture_version"] == "PR22_RUNTIME_ORCHESTRATION_SKELETON_FIXTURE_V1"
    assert fixture["fixture_authority_class"] == SYNTHETIC_AUTHORITY_CLASS
    assert validate_runtime_orchestration_skeleton_fixture(fixture) == []


def test_runtime_orchestration_skeleton_rejects_missing_required_authority_scope_flags():
    fixture = _fixture()
    _skeleton(fixture)["runtime_authority_scope_flags"].pop(
        "accepted_source_evidence_required_before_runtime_use"
    )

    failures = validate_runtime_orchestration_skeleton_fixture(fixture)

    assert any(
        "accepted_source_evidence_required_before_runtime_use" in failure
        for failure in failures
    )


def test_runtime_live_order_profit_source_binding_and_private_state_flags_true_fail():
    forbidden_flags = {
        "runtime_enabled",
        "live_enabled",
        "order_execution_enabled",
        "profit_claim_enabled",
        "source_retrieval_enabled",
        "source_acceptance_execution_enabled",
        "external_fact_acceptance_enabled",
        "connector_binding_enabled",
        "private_state_fetch_enabled",
    }

    for flag in sorted(forbidden_flags):
        fixture = _fixture()
        _skeleton(fixture)["runtime_forbidden_action_flags"][flag] = True

        failures = validate_runtime_orchestration_skeleton_fixture(fixture)

        assert any(flag in failure for failure in failures)


def test_runtime_orchestration_rejects_every_forbidden_action_flag_when_true():
    for flag in sorted(RUNTIME_FORBIDDEN_ACTION_FLAGS):
        fixture = _fixture()
        _skeleton(fixture)["runtime_forbidden_action_flags"][flag] = True

        failures = validate_runtime_orchestration_skeleton_fixture(fixture)

        assert any(flag in failure for failure in failures)


def test_runtime_resolver_snapshot_creation_claims_fail():
    fixture = _fixture()
    _skeleton(fixture)["runtime_forbidden_action_flags"][
        "runtime_resolver_snapshot_creation_enabled"
    ] = True
    _receipt(fixture)["contains_runtime_resolver_snapshot"] = True
    fixture["fixture_no_claim_flags"]["creates_runtime_resolver_snapshot"] = True

    failures = validate_runtime_orchestration_skeleton_fixture(fixture)

    assert any("runtime_resolver_snapshot_creation_enabled" in failure for failure in failures)
    assert any("contains_runtime_resolver_snapshot" in failure for failure in failures)
    assert any("creates_runtime_resolver_snapshot" in failure for failure in failures)


def test_replay_and_paper_execution_claims_fail():
    fixture = _fixture()
    action_flags = _skeleton(fixture)["runtime_forbidden_action_flags"]
    action_flags["replay_execution_enabled"] = True
    action_flags["paper_execution_enabled"] = True
    fixture["fixture_no_claim_flags"]["executes_replay"] = True
    fixture["fixture_no_claim_flags"]["executes_paper"] = True

    failures = validate_runtime_orchestration_skeleton_fixture(fixture)

    assert any("replay_execution_enabled" in failure for failure in failures)
    assert any("paper_execution_enabled" in failure for failure in failures)
    assert any("executes_replay" in failure for failure in failures)
    assert any("executes_paper" in failure for failure in failures)


def test_runtime_cash_receipt_claims_fail():
    fixture = _fixture()
    _skeleton(fixture)["runtime_forbidden_action_flags"][
        "runtime_cash_receipt_creation_enabled"
    ] = True
    _receipt(fixture)["contains_runtime_cash_receipt"] = True
    fixture["fixture_no_claim_flags"]["creates_runtime_cash_receipts"] = True

    failures = validate_runtime_orchestration_skeleton_fixture(fixture)

    assert any("runtime_cash_receipt_creation_enabled" in failure for failure in failures)
    assert any("contains_runtime_cash_receipt" in failure for failure in failures)
    assert any("creates_runtime_cash_receipts" in failure for failure in failures)


def test_runtime_orchestration_fixture_has_no_live_private_or_real_source_material():
    raw_text = FIXTURE_PATH.read_text(encoding="utf-8").lower()

    for fragment in {
        "://",
        "www.",
        "http",
        "kalshi",
        "polymarket",
        "ibkr",
        "password",
        "account_id",
        "atomicrows.bundle",
    }:
        assert fragment not in raw_text

    fixture = _fixture()
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())
    assert _receipt(fixture)["receipt_state"] == "PLACEHOLDER_ONLY_NOT_CREATED"
    assert _receipt(fixture)["runtime_resolver_snapshot_reference"] == (
        "SYNTHETIC_NONE_NO_RUNTIME_RESOLVER_SNAPSHOT"
    )
    assert _receipt(fixture)["runtime_cash_receipt_reference"] == (
        "SYNTHETIC_NONE_NO_RUNTIME_CASH_RECEIPT"
    )
