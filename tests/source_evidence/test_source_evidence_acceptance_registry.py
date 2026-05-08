import copy
import json
from pathlib import Path

from tools.validate_source_evidence_static import (
    REGISTRY_FORBIDDEN_ACTION_FLAGS,
    validate_acceptance_registry_fixture,
)


FIXTURE_PATH = Path(
    "tests/fixtures/source_evidence/synthetic_acceptance_registry.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _registry(fixture: dict) -> dict:
    return fixture["source_evidence_acceptance_registry"]


def test_valid_synthetic_acceptance_registry_fixture_passes_static_validation():
    assert validate_acceptance_registry_fixture(_fixture()) == []


def test_acceptance_registry_rejects_missing_required_authority_scope_flags():
    fixture = _fixture()
    _registry(fixture)["registry_authority_scope_flags"].pop(
        "accepted_fact_claims_require_accepted_source_packet_authority_flag"
    )

    failures = validate_acceptance_registry_fixture(fixture)

    assert any(
        "accepted_fact_claims_require_accepted_source_packet_authority_flag" in failure
        for failure in failures
    )


def test_acceptance_registry_rejects_runtime_live_order_profit_source_and_connector_flags():
    for flag in sorted(
        {
            "runtime_enabled",
            "live_enabled",
            "order_execution_enabled",
            "profit_claim_enabled",
            "source_retrieval_enabled",
            "connector_binding_enabled",
        }
    ):
        fixture = _fixture()
        _registry(fixture)["registry_forbidden_action_flags"][flag] = True

        failures = validate_acceptance_registry_fixture(fixture)

        assert any(flag in failure for failure in failures)


def test_acceptance_registry_rejects_every_forbidden_action_flag_when_true():
    for flag in sorted(REGISTRY_FORBIDDEN_ACTION_FLAGS):
        fixture = _fixture()
        _registry(fixture)["registry_forbidden_action_flags"][flag] = True

        failures = validate_acceptance_registry_fixture(fixture)

        assert any(flag in failure for failure in failures)


def test_acceptance_registry_rejects_accepted_fact_claim_without_packet_authority():
    fixture = _fixture()
    accepted_record = _registry(fixture)["accepted_records"][0]
    accepted_record["accepted_fact_claim_present"] = True
    accepted_record["accepted_source_packet_authority_present"] = False

    failures = validate_acceptance_registry_fixture(fixture)

    assert any(
        "accepted fact claim requires accepted-source packet authority" in failure
        for failure in failures
    )


def test_acceptance_registry_rejects_record_level_runtime_or_profit_flags():
    fixture = _fixture()
    candidate_record = _registry(fixture)["candidate_records"][0]
    accepted_record = copy.deepcopy(_registry(fixture)["accepted_records"][0])
    candidate_record["registry_forbidden_action_flags"]["runtime_enabled"] = True
    accepted_record["registry_forbidden_action_flags"]["profit_claim_enabled"] = True
    _registry(fixture)["accepted_records"][0] = accepted_record

    failures = validate_acceptance_registry_fixture(fixture)

    assert any("runtime_enabled" in failure for failure in failures)
    assert any("profit_claim_enabled" in failure for failure in failures)
