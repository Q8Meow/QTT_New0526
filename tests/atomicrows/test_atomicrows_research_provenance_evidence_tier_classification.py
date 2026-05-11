from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools import (
    validate_atomicrows_research_provenance_evidence_tier_classification as gate,
)


REPO_ROOT = Path(".")
REGISTRY = Path(
    "docs/master_plan/atomicrows/"
    "AtomicRowsResearchProvenanceEvidenceTierClassification.yaml"
)
SCHEMA = Path(
    "schemas/atomicrows/"
    "atomicrows_research_provenance_evidence_tier_classification.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_research_provenance_evidence_tier_classification.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/"
    "AtomicRowsResearchProvenanceEvidenceTierClassification.report.json"
)


def _registry() -> dict:
    return gate.load_registry(REGISTRY)


def _fixture() -> dict:
    return gate.load_fixture(FIXTURE)


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _source(payload: dict, source_type: str) -> dict:
    for entry in payload["source_types"]:
        if entry["source_type"] == source_type:
            return entry
    raise AssertionError(f"missing source type {source_type}")


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _mutated_registry() -> dict:
    return copy.deepcopy(_registry())


def test_schema_surface_and_required_fields_are_fail_closed():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert schema["required"] == list(gate.TOP_LEVEL_REQUIRED_FIELDS)
    assert schema["$defs"]["source_type_id"]["enum"] == list(
        gate.CANONICAL_SOURCE_TYPES
    )
    assert schema["$defs"]["evidence_tier"]["enum"] == list(
        gate.ALLOWED_EVIDENCE_TIERS
    )
    assert schema["$defs"]["candidate_route_kind"]["enum"] == list(
        gate.ALLOWED_CANDIDATE_ROUTE_KINDS
    )
    assert schema["$defs"]["source_type_entry"]["required"] == list(
        gate.SOURCE_TYPE_FIELDS
    )
    assert schema["properties"]["source_types"]["minItems"] == 14
    assert schema["properties"]["source_types"]["maxItems"] == 14
    assert len(schema["properties"]["source_types"]["prefixItems"]) == 14


def test_registry_fixture_and_validator_pass(capsys):
    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )

    assert result.failures == ()
    assert gate.validate_classification_payload(_registry(), label="registry") == []
    assert gate.validate_fixture_shape(_fixture()) == []
    assert gate.validate_classification_payload(_fixture(), label="fixture") == []
    assert gate.main([]) == 0
    assert capsys.readouterr().out.strip() == gate.SUCCESS_MARKER


def test_generated_report_is_deterministic_and_has_expected_counts():
    first = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )
    second = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )
    report = _report()

    assert first.failures == second.failures == ()
    assert first.report == second.report == report
    assert gate.serialize_report(first.report or {}) == gate.serialize_report(
        second.report or {}
    )
    assert report["generated_at_utc"] == gate.DETERMINISTIC_GENERATED_AT
    assert report["source_type_count"] == 14
    assert report["required_source_type_count"] == 14
    assert report["required_source_types_present_count"] == 14
    assert report["missing_source_type_count"] == 0
    assert report["invalid_source_type_order_count"] == 0
    assert report["invalid_ordinal_order_count"] == 0
    assert report["authority_class_mismatch_count"] == 0
    assert report["evidence_tier_mismatch_count"] == 0
    assert report["candidate_route_kind_mismatch_count"] == 0
    assert report["forbidden_source_type_boundary_true_count"] == 0
    assert report["source_type_ids"] == list(gate.CANONICAL_SOURCE_TYPES)
    assert report["candidate_seed_source_type_count"] == 12
    assert report["algorithm_candidate_seed_source_type_count"] == 12
    assert report["agent_binding_request_seed_source_type_count"] == 8
    assert report["retrieval_target_seed_source_type_count"] == 13
    assert report["owner_review_seed_source_type_count"] == 14
    assert report["accepted_source_review_seed_source_type_count"] == 1
    assert report["authority_boundary_all_false"] is True


def test_owner_official_github_uploaded_and_future_routing_semantics():
    registry = _registry()
    owner = _source(registry, "OWNER_SUBMITTED_RESEARCH_SOURCE")
    owner_override = _source(registry, "OWNER_GLOBAL_OVERRIDE")
    official = _source(registry, "OFFICIAL_SOURCE_EVIDENCE")
    github = _source(registry, "GITHUB_REPOSITORY")
    uploaded = _source(registry, "UPLOADED_DOCUMENT")

    assert owner["may_seed_parameter_candidate"] is True
    assert owner["may_seed_algorithm_candidate"] is True
    assert owner["may_seed_agent_binding_request"] is True
    assert owner["future_pr71_intake_supported"] is True
    assert owner["future_pr72_candidate_routing_supported"] is True
    assert owner["future_parameter_stack_routing_supported"] is True
    assert owner["future_trade_context_routing_supported"] is True
    assert owner["future_quantum_applicability_routing_supported"] is True
    assert owner["future_scoring_ranking_routing_supported"] is True
    assert owner["future_quantum_classical_arbitration_routing_supported"] is True

    assert (
        registry["owner_override_may_satisfy_internal_source_evidence_requirement"]
        is True
    )
    assert owner_override["may_seed_owner_review_request"] is True
    assert (
        owner_override[
            "may_satisfy_internal_source_evidence_requirement_with_owner_override"
        ]
        is True
    )
    assert owner_override["may_authorize_external_fact"] is False
    assert registry["owner_override_external_fact_authority"] is False

    assert official["may_seed_accepted_source_review"] is True
    assert official["may_create_accepted_source_packet"] is False
    assert official["may_unlock_connector_semantics"] is False
    assert github["no_clone_no_run_required"] is True
    assert github["no_install_required"] is True
    assert github["secret_materialization_blocked"] is True
    assert uploaded["private_access_rights_attestation_required"] is True


@pytest.mark.parametrize("source_type", gate.CANONICAL_SOURCE_TYPES)
def test_missing_any_required_source_type_fails(source_type: str):
    payload = _mutated_registry()
    payload["source_types"] = [
        entry
        for entry in payload["source_types"]
        if entry["source_type"] != source_type
    ]
    payload["source_type_ids_canonical_order"] = [
        entry["source_type"] for entry in payload["source_types"]
    ]
    payload["source_type_count"] = len(payload["source_types"])

    failures = gate.validate_classification_payload(payload, label="mutated")

    _assert_failure_contains(failures, "source_type_count")
    _assert_failure_contains(failures, "canonical order")


def test_extra_source_type_fails():
    payload = _mutated_registry()
    extra = copy.deepcopy(payload["source_types"][0])
    extra["ordinal"] = 15
    extra["source_type"] = "SYNTHETIC_EXTRA_SOURCE_TYPE"
    payload["source_types"].append(extra)
    payload["source_type_count"] = 15

    failures = gate.validate_classification_payload(payload, label="mutated")

    _assert_failure_contains(failures, "source_type_count")
    _assert_failure_contains(failures, "exactly 14 entries")


def test_swapped_source_type_order_fails():
    payload = _mutated_registry()
    payload["source_types"][0], payload["source_types"][1] = (
        payload["source_types"][1],
        payload["source_types"][0],
    )

    failures = gate.validate_classification_payload(payload, label="mutated")

    _assert_failure_contains(failures, "canonical order")


@pytest.mark.parametrize(
    ("source_type", "field", "bad_value", "fragment"),
    [
        ("OWNER_SUBMITTED_RESEARCH_SOURCE", "ordinal", 99, "ordinal"),
        (
            "PUBLIC_WEBSITE",
            "authority_class",
            "WRONG_AUTHORITY_CLASS",
            "authority_class",
        ),
        ("RESEARCH_ARTICLE", "evidence_tier", "OWNER_INTERNAL_OVERRIDE", "evidence_tier"),
        (
            "ACADEMIC_RESEARCH_PAPER",
            "candidate_route_kind",
            "OWNER_OVERRIDE_TO_INTERNAL_REQUIREMENT_SATISFACTION_ONLY",
            "candidate_route_kind",
        ),
        (
            "OFFICIAL_SOURCE_EVIDENCE",
            "may_create_accepted_source_packet",
            True,
            "may_create_accepted_source_packet",
        ),
        (
            "OFFICIAL_SOURCE_EVIDENCE",
            "may_unlock_connector_semantics",
            True,
            "may_unlock_connector_semantics",
        ),
        (
            "GITHUB_REPOSITORY",
            "no_clone_no_run_required",
            False,
            "no_clone_no_run_required",
        ),
        ("GITHUB_REPOSITORY", "no_install_required", False, "no_install_required"),
        (
            "GITHUB_REPOSITORY",
            "secret_materialization_blocked",
            False,
            "secret_materialization_blocked",
        ),
        (
            "UPLOADED_DOCUMENT",
            "private_access_rights_attestation_required",
            False,
            "private_access_rights_attestation_required",
        ),
    ],
)
def test_source_type_required_mapping_or_special_boundary_fails(
    source_type: str,
    field: str,
    bad_value: object,
    fragment: str,
):
    payload = _mutated_registry()
    _source(payload, source_type)[field] = bad_value

    failures = gate.validate_classification_payload(payload, label="mutated")

    _assert_failure_contains(failures, fragment)


@pytest.mark.parametrize("field", gate.FORBIDDEN_SOURCE_TYPE_FALSE_FIELDS)
def test_any_forbidden_source_type_boundary_true_fails(field: str):
    payload = _mutated_registry()
    payload["source_types"][0][field] = True

    failures = gate.validate_classification_payload(payload, label="mutated")

    _assert_failure_contains(failures, field)


@pytest.mark.parametrize("field", gate.TOP_LEVEL_FALSE_FIELDS)
def test_top_level_forbidden_boundary_true_fails(field: str):
    payload = _mutated_registry()
    payload[field] = True

    failures = gate.validate_classification_payload(payload, label="mutated")

    _assert_failure_contains(failures, field)


def test_authority_boundary_all_false_false_fails():
    payload = _mutated_registry()
    payload["authority_boundary_all_false"] = False

    failures = gate.validate_classification_payload(payload, label="mutated")

    _assert_failure_contains(failures, "authority_boundary_all_false")


def test_final_mode_remains_incomplete():
    result = gate.validate(
        mode="final",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=None,
    )

    assert result.ok is False
    _assert_failure_contains(result.failures, "final mode incomplete")
