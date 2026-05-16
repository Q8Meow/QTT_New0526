from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

from tools import (
    validate_atomicrows_research_source_to_candidate_family_gate as gate,
)


REPO_ROOT = Path(".")
GATE = Path(
    "docs/master_plan/atomicrows/AtomicRowsResearchSourceToCandidateFamilyGate.yaml"
)
SCHEMA = Path(
    "schemas/atomicrows/atomicrows_research_source_to_candidate_family_gate.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_research_source_to_candidate_family_gate.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/AtomicRowsResearchSourceToCandidateFamilyGate.report.json"
)


def _schema() -> dict:
    return gate.load_json(SCHEMA)


def _gate() -> dict:
    return gate.load_yaml(GATE)


def _fixture() -> dict:
    return gate.load_fixture(FIXTURE)


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _assert_failure_contains(failures: tuple[str, ...] | list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _mutated_gate() -> dict:
    return copy.deepcopy(_gate())


def _mutated_fixture() -> dict:
    return copy.deepcopy(_fixture())


def _conversion_case(fixture: dict) -> dict:
    return fixture["fixture_cases"][1]


def _synthetic_entry(fixture: dict, index: int = 0) -> dict:
    return _conversion_case(fixture)["synthetic_source_intake_entries"][index]


def _owner_override_reference(fixture: dict) -> dict:
    return _conversion_case(fixture)["synthetic_outputs"][
        "owner_override_receipt_references"
    ][0]


def _validate_gate_payload(payload: dict) -> list[str]:
    return gate.validate_gate_payload(
        payload,
        schema=_schema(),
        pr70_source_types=gate.CANONICAL_SOURCE_TYPES,
        pr71_registry=gate.pr71_gate.load_registry(gate.DEFAULT_PR71_REGISTRY),
        production=True,
    )


def _validate_fixture_payload(payload: dict) -> list[str]:
    return gate.validate_synthetic_fixture_conversion(
        payload,
        schema=_schema(),
        pr70_source_types=gate.CANONICAL_SOURCE_TYPES,
    )


def test_production_gate_validates_and_main_prints_marker(capsys):
    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        gate_path=GATE,
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
        gate_path=GATE,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )
    second = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        gate_path=GATE,
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


def test_pr70_and_pr71_dependencies_are_required():
    missing = Path("tests/fixtures/atomicrows/MISSING_PR72_DEPENDENCY_SENTINEL.json")
    pr70_result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        gate_path=GATE,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=None,
        pr70_report_path=missing,
    )
    pr71_result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        gate_path=GATE,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=None,
        pr71_report_path=missing,
    )

    assert pr70_result.ok is False
    assert pr71_result.ok is False
    _assert_failure_contains(pr70_result.failures, "PR70_CLASSIFIER_DEPENDENCY_MISSING")
    _assert_failure_contains(pr71_result.failures, "PR71_INTAKE_REGISTRY_DEPENDENCY_MISSING")


def test_supported_source_types_align_and_pr71_production_input_is_empty():
    pr70_source_types, pr70_failures = gate.validate_pr70_dependency(
        repo_root=REPO_ROOT,
        pr70_schema_path=gate.DEFAULT_PR70_SCHEMA,
        pr70_registry_path=gate.DEFAULT_PR70_REGISTRY,
        pr70_report_path=gate.DEFAULT_PR70_REPORT,
    )
    pr71_registry, _, pr71_failures = gate.validate_pr71_dependency(
        repo_root=REPO_ROOT,
        pr71_schema_path=gate.DEFAULT_PR71_SCHEMA,
        pr71_registry_path=gate.DEFAULT_PR71_REGISTRY,
        pr71_report_path=gate.DEFAULT_PR71_REPORT,
        pr70_source_types=pr70_source_types,
    )

    assert pr70_failures == []
    assert pr71_failures == []
    assert pr70_source_types == list(gate.CANONICAL_SOURCE_TYPES)
    assert _gate()["supported_source_types"] == pr70_source_types
    assert _schema()["$defs"]["source_type_id"]["enum"] == pr70_source_types
    assert pr71_registry["real_owner_intake_entry_count"] == 0
    assert pr71_registry["intake_entries"] == []


def test_production_outputs_are_empty_and_static_invariants_are_false():
    production_gate = _gate()
    outputs = production_gate["production_outputs"]

    assert outputs["candidate_parameter_family_packets"] == []
    assert outputs["candidate_algorithm_family_packets"] == []
    assert outputs["candidate_agent_binding_requests"] == []
    assert outputs["owner_override_receipt_references"] == []
    assert production_gate["candidate_parameter_family_packet_count"] == 0
    assert production_gate["candidate_algorithm_family_packet_count"] == 0
    assert production_gate["candidate_agent_binding_request_count"] == 0
    assert production_gate["owner_override_receipt_reference_count"] == 0
    assert production_gate["real_candidate_outputs_invented"] is False
    assert production_gate["synthetic_fixture_only"] is True
    assert production_gate["conversion_gate_contract_ready"] is True
    assert production_gate["production_conversion_ready"] is False
    assert production_gate["final_ready"] is False


def test_schema_defines_output_packet_types_and_required_packet_fields():
    schema = _schema()

    assert schema["$defs"]["output_packet_type"]["enum"] == list(gate.OUTPUT_PACKET_TYPES)
    assert schema["$defs"]["candidate_parameter_family_packet"]["required"] == list(
        gate.CANDIDATE_PARAMETER_PACKET_FIELDS
    )
    assert schema["$defs"]["candidate_algorithm_family_packet"]["required"] == list(
        gate.CANDIDATE_ALGORITHM_PACKET_FIELDS
    )
    assert schema["$defs"]["candidate_agent_binding_request"]["required"] == list(
        gate.CANDIDATE_AGENT_BINDING_REQUEST_FIELDS
    )
    assert schema["$defs"]["owner_override_receipt_reference"]["required"] == list(
        gate.OWNER_OVERRIDE_RECEIPT_REFERENCE_FIELDS
    )


def test_synthetic_fixture_conversion_ids_and_traceability_are_deterministic():
    fixture = _fixture()
    case = _conversion_case(fixture)
    outputs = case["synthetic_outputs"]

    assert (
        outputs["candidate_parameter_family_packets"][0][
            "candidate_parameter_family_packet_id"
        ]
        == "SYNTHETIC-CANDIDATE-PARAMETER-FAMILY-PACKET-001"
    )
    assert (
        outputs["candidate_algorithm_family_packets"][0][
            "candidate_algorithm_family_packet_id"
        ]
        == "SYNTHETIC-CANDIDATE-ALGORITHM-FAMILY-PACKET-001"
    )
    assert (
        outputs["candidate_agent_binding_requests"][0][
            "candidate_agent_binding_request_id"
        ]
        == "SYNTHETIC-CANDIDATE-AGENT-BINDING-REQUEST-001"
    )
    assert (
        outputs["owner_override_receipt_references"][0][
            "owner_override_receipt_reference_id"
        ]
        == "SYNTHETIC-OWNER-OVERRIDE-RECEIPT-REFERENCE-001"
    )
    assert gate.validate_traceability_to_synthetic_intake(case) == []
    assert gate.fixture_contains_only_synthetic_entries(fixture) is True


def test_unsupported_source_type_and_candidate_route_fail():
    source_fixture = _mutated_fixture()
    _synthetic_entry(source_fixture)["source_type"] = "SYNTHETIC_UNSUPPORTED_SOURCE"
    route_fixture = _mutated_fixture()
    _synthetic_entry(route_fixture)["candidate_route"] = "SYNTHETIC_UNSUPPORTED_ROUTE"

    source_failures = _validate_fixture_payload(source_fixture)
    route_failures = _validate_fixture_payload(route_fixture)

    _assert_failure_contains(source_failures, "source_type")
    _assert_failure_contains(route_failures, "candidate_route")


def test_real_locator_in_gate_or_fixture_fails():
    fixture = _mutated_fixture()
    _synthetic_entry(fixture)["source_locator"] = "http" + "://synthetic.invalid"
    production_gate = _mutated_gate()
    production_gate["depends_on_research_provenance_classifier"]["report_path"] = (
        "https" + "://synthetic.invalid/report.json"
    )

    fixture_text_failures = gate.validate_no_forbidden_claims(
        (("fixture", json.dumps(fixture, sort_keys=True)),)
    )
    gate_text_failures = gate.validate_no_forbidden_claims(
        (("gate", json.dumps(production_gate, sort_keys=True)),)
    )

    _assert_failure_contains(fixture_text_failures, "REAL_HTTP_LOCATOR")
    _assert_failure_contains(gate_text_failures, "REAL_HTTPS_LOCATOR")


def test_secret_like_and_account_private_state_values_fail():
    secret_failures = gate.validate_no_forbidden_claims(
        (("fixture", "bearer" + " token placeholder"),)
    )
    account_failures = gate.validate_no_forbidden_claims(
        (("fixture", "private account" + " state placeholder"),)
    )

    _assert_failure_contains(secret_failures, "SECRET_LIKE_BEARER_TOKEN")
    _assert_failure_contains(account_failures, "PRIVATE_ACCOUNT_STATE")


def test_source_acceptance_and_connector_semantic_claims_fail():
    source_failures = gate.validate_no_forbidden_claims(
        (("fixture", "accepted source packet" + " created"),)
    )
    connector_failures = gate.validate_no_forbidden_claims(
        (("fixture", "connector semantic binding" + " created"),)
    )

    _assert_failure_contains(source_failures, "SOURCE_ACCEPTANCE_CLAIM")
    _assert_failure_contains(connector_failures, "CONNECTOR_SEMANTIC_CLAIM")


def test_runtime_live_order_and_bundle_authority_claims_fail():
    runtime_gate = _mutated_gate()
    runtime_gate["creates_runtime_artifacts"] = True
    live_order_gate = _mutated_gate()
    live_order_gate["creates_order_authority"] = True
    bundle_gate = _mutated_gate()
    bundle_gate["creates_atomicrows_bundle_rows"] = True
    bundle_gate["creates_atomicrows_bundle_jsonl"] = True
    bundle_gate["creates_atomicrows_bundle_sha256"] = True

    runtime_failures = _validate_gate_payload(runtime_gate)
    live_order_failures = _validate_gate_payload(live_order_gate)
    bundle_failures = _validate_gate_payload(bundle_gate)

    _assert_failure_contains(runtime_failures, "creates_runtime_artifacts")
    _assert_failure_contains(live_order_failures, "creates_order_authority")
    _assert_failure_contains(bundle_failures, "creates_atomicrows_bundle_rows")
    _assert_failure_contains(bundle_failures, "creates_atomicrows_bundle_jsonl")
    _assert_failure_contains(bundle_failures, "creates_atomicrows_bundle_sha256")


def test_replay_paper_profit_quantum_and_advantage_claims_fail():
    replay_failures = gate.validate_no_forbidden_claims(
        (("fixture", "replay passed" + " as proof"),)
    )
    paper_failures = gate.validate_no_forbidden_claims(
        (("fixture", "paper passed" + " as proof"),)
    )
    profit_gate = _mutated_gate()
    profit_gate["creates_profit_evidence"] = True
    quantum_policy_gate = _mutated_gate()
    quantum_policy_gate["owner_override_policy"][
        "owner_override_fabricates_quantum_backend_execution"
    ] = True
    quantum_advantage_gate = _mutated_gate()
    quantum_advantage_gate["creates_quantum_advantage_claim"] = True

    _assert_failure_contains(replay_failures, "REPLAY_PROOF_CLAIM")
    _assert_failure_contains(paper_failures, "PAPER_PROOF_CLAIM")
    _assert_failure_contains(_validate_gate_payload(profit_gate), "creates_profit_evidence")
    _assert_failure_contains(
        _validate_gate_payload(quantum_policy_gate),
        "owner_override_fabricates_quantum_backend_execution",
    )
    _assert_failure_contains(
        _validate_gate_payload(quantum_advantage_gate),
        "creates_quantum_advantage_claim",
    )


def test_ranking_scoring_arbitration_and_trade_context_routing_claims_fail():
    ranking_gate = _mutated_gate()
    ranking_gate["creates_ranking"] = True
    scoring_gate = _mutated_gate()
    scoring_gate["creates_scoring"] = True
    arbitration_gate = _mutated_gate()
    arbitration_gate["creates_optimizer_arbitration"] = True
    routing_gate = _mutated_gate()
    routing_gate["creates_trade_context_routing"] = True

    _assert_failure_contains(_validate_gate_payload(ranking_gate), "creates_ranking")
    _assert_failure_contains(_validate_gate_payload(scoring_gate), "creates_scoring")
    _assert_failure_contains(
        _validate_gate_payload(arbitration_gate), "creates_optimizer_arbitration"
    )
    _assert_failure_contains(
        _validate_gate_payload(routing_gate), "creates_trade_context_routing"
    )


def test_owner_override_reference_is_internal_only_and_cannot_fabricate_evidence():
    fixture = _fixture()
    reference = _owner_override_reference(fixture)

    assert reference["owner_override_internal_workflow_only"] is True
    assert reference["external_fact_fabrication_allowed"] is False
    assert reference["accepted_source_packet_fabrication_allowed"] is False
    assert reference["runtime_cash_receipt_fabrication_allowed"] is False
    assert reference["order_receipt_fabrication_allowed"] is False
    assert reference["replay_paper_result_fabrication_allowed"] is False
    assert reference["quantum_backend_execution_fabrication_allowed"] is False
    assert reference["profit_evidence_fabrication_allowed"] is False

    mutated_reference = copy.deepcopy(reference)
    mutated_reference["external_fact_fabrication_allowed"] = True
    mutated_reference["profit_evidence_fabrication_allowed"] = True

    failures = gate.validate_no_output_claims(mutated_reference, "owner_override")

    _assert_failure_contains(failures, "external_fact_fabrication_allowed")
    _assert_failure_contains(failures, "profit_evidence_fabrication_allowed")


def test_no_random_selection_or_stack_selection_is_implemented():
    production_gate = _gate()
    assert production_gate["implements_random_selection"] is False
    assert production_gate["implements_stack_selection"] is False
    assert production_gate["creates_ranking"] is False
    assert production_gate["creates_scoring"] is False
    assert production_gate["creates_optimizer_arbitration"] is False
    assert production_gate["creates_trade_context_routing"] is False

    mutated_gate = _mutated_gate()
    mutated_gate["implements_random_selection"] = True
    mutated_gate["implements_stack_selection"] = True

    failures = _validate_gate_payload(mutated_gate)

    _assert_failure_contains(failures, "implements_random_selection")
    _assert_failure_contains(failures, "implements_stack_selection")


def test_forbidden_bundle_files_and_master_plan_edit_guard():
    assert (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()
    assert gate.validate_master_plan_not_modified(REPO_ROOT) == []

    scratch_root = Path(".pytest-pr72-forbidden-artifacts")
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

    _assert_failure_contains(failures, "AtomicRows.bundle.sha256")
