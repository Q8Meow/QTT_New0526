from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

from tools import (
    validate_atomicrows_owner_submitted_research_source_intake_registry as gate,
)


REPO_ROOT = Path(".")
REGISTRY = Path(
    "docs/master_plan/atomicrows/"
    "AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.yaml"
)
SCHEMA = Path(
    "schemas/atomicrows/"
    "atomicrows_owner_submitted_research_source_intake_registry.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_owner_submitted_research_source_intake_registry.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/"
    "AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.report.json"
)


def _schema() -> dict:
    return gate.load_json(SCHEMA)


def _registry() -> dict:
    return gate.load_registry(REGISTRY)


def _fixture() -> dict:
    return gate.load_fixture(FIXTURE)


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _assert_failure_contains(failures: tuple[str, ...] | list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _mutated_registry() -> dict:
    return copy.deepcopy(_registry())


def _mutated_fixture() -> dict:
    return copy.deepcopy(_fixture())


def _synthetic_fixture_entry(fixture: dict) -> dict:
    return fixture["fixture_cases"][1]["registry"]["intake_entries"][0]


def _validate_registry_payload(payload: dict) -> list[str]:
    return gate.validate_registry_payload(
        payload,
        label="mutated_registry",
        pr70_source_types=gate.CANONICAL_SOURCE_TYPES,
        production=True,
        synthetic_only_entries=False,
    )


def _validate_fixture_payload(payload: dict) -> list[str]:
    return gate.validate_fixture_payload(
        payload,
        schema=_schema(),
        pr70_source_types=gate.CANONICAL_SOURCE_TYPES,
    )


def test_production_registry_validates_and_main_prints_marker(capsys):
    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )

    assert result.failures == ()
    assert gate.main([]) == 0
    assert capsys.readouterr().out.strip() == gate.SUCCESS_MARKER


def test_generated_report_is_deterministic_and_contains_success_marker():
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
    assert report["validation_marker"] == gate.SUCCESS_MARKER
    assert report["final_ready"] is False


def test_production_registry_has_zero_real_owner_intakes():
    registry = _registry()

    assert registry["real_owner_intake_entry_count"] == 0
    assert registry["intake_entries"] == []
    assert registry["real_owner_intakes_invented"] is False
    assert registry["synthetic_fixture_only"] is True
    assert registry["final_ready"] is False


def test_schema_requires_roadmap_and_quantum_forward_entry_fields():
    schema = _schema()
    intake_entry = schema["$defs"]["intake_entry"]

    assert intake_entry["required"] == list(gate.ENTRY_REQUIRED_FIELDS)
    assert set(gate.ROADMAP_REQUIRED_ENTRY_FIELDS).issubset(
        set(intake_entry["required"])
    )
    assert set(gate.QUANTUM_FORWARD_ENTRY_FIELDS).issubset(
        set(intake_entry["required"])
    )
    assert len(gate.ROADMAP_REQUIRED_ENTRY_FIELDS) == 11
    assert len(gate.QUANTUM_FORWARD_ENTRY_FIELDS) == 5


def test_source_types_align_with_pr70_classifier_dependency():
    pr70_source_types, failures = gate.validate_pr70_dependency(
        repo_root=REPO_ROOT,
        pr70_schema_path=gate.DEFAULT_PR70_SCHEMA,
        pr70_registry_path=gate.DEFAULT_PR70_REGISTRY,
        pr70_report_path=gate.DEFAULT_PR70_REPORT,
    )

    assert failures == []
    assert pr70_source_types == list(gate.CANONICAL_SOURCE_TYPES)
    assert _registry()["supported_source_types"] == pr70_source_types
    assert _schema()["$defs"]["source_type_id"]["enum"] == pr70_source_types


def test_unsupported_source_type_fails_fixture_validation():
    fixture = _mutated_fixture()
    _synthetic_fixture_entry(fixture)["source_type"] = "SYNTHETIC_UNSUPPORTED_SOURCE"

    failures = _validate_fixture_payload(fixture)

    _assert_failure_contains(failures, "source_type")


def test_missing_pr70_classifier_dependency_fails_closed():
    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=None,
        pr70_report_path=Path(
            "tests/fixtures/atomicrows/PR70_MISSING_SENTINEL_DOES_NOT_EXIST.json"
        ),
    )

    assert result.ok is False
    _assert_failure_contains(result.failures, "DEPENDENCY_MISSING")


def test_real_locator_in_fixture_or_registry_fails():
    fixture = _mutated_fixture()
    _synthetic_fixture_entry(fixture)["source_locator"] = "http" + "://synthetic.invalid"
    registry = _mutated_registry()
    registry["depends_on_provenance_classifier"]["report_path"] = (
        "http" + "://synthetic.invalid/report.json"
    )

    fixture_failures = _validate_fixture_payload(fixture)
    registry_failures = _validate_registry_payload(registry)

    _assert_failure_contains(fixture_failures, "REAL_HTTP_LOCATOR")
    _assert_failure_contains(registry_failures, "REAL_HTTP_LOCATOR")


def test_secret_like_value_in_fixture_fails():
    fixture = _mutated_fixture()
    _synthetic_fixture_entry(fixture)["owner_note"] = "bearer" + " token placeholder"

    failures = _validate_fixture_payload(fixture)

    _assert_failure_contains(failures, "SECRET_LIKE_BEARER_TOKEN")


def test_source_acceptance_claim_fails():
    fixture = _mutated_fixture()
    _synthetic_fixture_entry(fixture)["owner_note"] = (
        "accepted source packet" + " created"
    )

    failures = _validate_fixture_payload(fixture)

    _assert_failure_contains(failures, "SOURCE_ACCEPTANCE_CLAIM")


def test_connector_semantic_claim_fails():
    fixture = _mutated_fixture()
    _synthetic_fixture_entry(fixture)["owner_note"] = (
        "connector semantic binding" + " created"
    )

    failures = _validate_fixture_payload(fixture)

    _assert_failure_contains(failures, "CONNECTOR_SEMANTIC_CLAIM")


def test_runtime_artifact_claim_fails():
    registry = _mutated_registry()
    registry["creates_runtime_artifacts"] = True

    failures = _validate_registry_payload(registry)

    _assert_failure_contains(failures, "creates_runtime_artifacts")


def test_atomicrows_bundle_and_hash_creation_fails():
    scratch_root = Path(".pytest-pr71-forbidden-artifacts")
    shutil.rmtree(scratch_root, ignore_errors=True)
    try:
        bundle = scratch_root / gate.CANONICAL_BUNDLE_JSONL
        bundle.parent.mkdir(parents=True)
        bundle.write_text("", encoding="utf-8")
        bundle_hash = scratch_root / gate.CANONICAL_BUNDLE_SHA256
        bundle_hash.write_text("", encoding="utf-8")

        failures = gate.validate_no_forbidden_artifacts(scratch_root)
    finally:
        shutil.rmtree(scratch_root, ignore_errors=True)

    _assert_failure_contains(failures, "AtomicRows.bundle.jsonl")
    _assert_failure_contains(failures, "AtomicRows.bundle.sha256")


def test_pr72_conversion_artifact_claim_fails():
    registry = _mutated_registry()
    registry["implements_pr72_conversion"] = True
    registry["candidate_parameter_family_packet_created"] = True

    failures = _validate_registry_payload(registry)

    _assert_failure_contains(failures, "implements_pr72_conversion")
    _assert_failure_contains(failures, "candidate_parameter_family_packet_created")


def test_quantum_backend_execution_claim_fails():
    registry = _mutated_registry()
    registry["owner_override_fabricates_quantum_backend_execution"] = True

    failures = _validate_registry_payload(registry)

    _assert_failure_contains(
        failures,
        "owner_override_fabricates_quantum_backend_execution",
    )


def test_quantum_advantage_claim_fails():
    registry = _mutated_registry()
    registry["creates_quantum_advantage_claim"] = True

    failures = _validate_registry_payload(registry)

    _assert_failure_contains(failures, "creates_quantum_advantage_claim")


def test_profit_evidence_claim_fails():
    registry = _mutated_registry()
    registry["creates_profit_evidence"] = True

    failures = _validate_registry_payload(registry)

    _assert_failure_contains(failures, "creates_profit_evidence")


def test_replay_and_paper_proof_claims_fail():
    for prefix in ("replay passed", "paper passed"):
        fixture = _mutated_fixture()
        _synthetic_fixture_entry(fixture)["owner_note"] = prefix + " as proof"

        failures = _validate_fixture_payload(fixture)

        _assert_failure_contains(failures, "PROOF_CLAIM")


def test_owner_override_supported_but_cannot_fabricate_external_facts_or_evidence():
    registry = _registry()
    assert registry["owner_override_supported"] is True
    assert registry["owner_override_satisfies_internal_workflow_only"] is True
    assert registry["owner_override_fabricates_external_fact"] is False
    assert registry["owner_override_fabricates_accepted_source_packet"] is False
    assert registry["owner_override_fabricates_profit_evidence"] is False

    mutated = _mutated_registry()
    mutated["owner_override_fabricates_external_fact"] = True

    failures = _validate_registry_payload(mutated)

    _assert_failure_contains(failures, "owner_override_fabricates_external_fact")


def test_no_random_ranking_scoring_arbitration_trade_or_stack_selection_is_implemented():
    registry = _registry()
    for field in gate.NO_SELECTION_FALSE_FIELDS:
        assert registry[field] is False

    mutated = _mutated_registry()
    mutated["implements_ranking"] = True

    failures = _validate_registry_payload(mutated)

    _assert_failure_contains(failures, "implements_ranking")
