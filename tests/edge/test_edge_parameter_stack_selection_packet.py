import json
from pathlib import Path

from tools import validate_edge_parameter_stack_selection_packet as validator


ROOT = Path(".")


def _schema() -> dict:
    return validator.load_json(validator.DEFAULT_SCHEMA)


def _production() -> dict:
    return validator.load_yaml(validator.DEFAULT_PRODUCTION_PACKET)


def _fixture() -> dict:
    return validator.load_json(validator.DEFAULT_FIXTURE)


def _case(case_id: str) -> dict:
    cases = {case["case_id"]: case for case in _fixture()["fixture_cases"]}
    return cases[case_id]


def _case_packet(case_id: str) -> dict:
    return validator.case_packet_from_fixture(_fixture(), _case(case_id))


def _schema_failures(packet: dict) -> list[str]:
    return validator.schema_subset_failures(packet, _schema(), "packet")


def test_production_packet_validates_and_report_is_deterministic():
    result = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        production_packet_path=validator.DEFAULT_PRODUCTION_PACKET,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )

    assert result.ok, result.failures
    assert result.report is not None
    assert result.report["validation_marker"] == validator.SUCCESS_MARKER
    report_text = validator.DEFAULT_REPORT.read_text(encoding="utf-8")
    assert report_text == json.dumps(json.loads(report_text), indent=2, sort_keys=True) + "\n"
    assert "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_OK" in report_text


def test_required_roles_and_dependencies_match_pr73_pr74_pr75():
    production = _production()
    pr73_roles, pr73_failures = validator.validate_pr73_dependency(ROOT)
    pr74_roles, pr74_failures = validator.validate_pr74_dependency(ROOT, pr73_roles)
    pr75_roles, pr75_failures = validator.validate_pr75_dependency(ROOT, pr74_roles)

    assert not pr73_failures
    assert not pr74_failures
    assert not pr75_failures
    assert pr73_roles == list(validator.REQUIRED_STACK_ROLES)
    assert pr74_roles == list(validator.REQUIRED_STACK_ROLES)
    assert pr75_roles == list(validator.REQUIRED_STACK_ROLES)
    assert production["required_stack_role_family_fields"] == validator.ROLE_FAMILY_FIELD_BY_ROLE
    assert production["depends_on_parameter_stack_role_taxonomy"]["validation_marker"] == (
        "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK"
    )
    assert production["depends_on_parameter_stack_completeness_gate"]["validation_marker"] == (
        "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK"
    )
    assert production["depends_on_parameter_stack_compatibility_gate"]["validation_marker"] == (
        "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_OK"
    )


def test_all_minimum_packet_fields_and_role_family_fields_exist():
    production = _production()
    schema_required = set(_schema()["required"])

    for field in validator.MINIMUM_REQUIRED_PACKET_FIELDS:
        assert field in production
        assert field in schema_required
    for field in validator.SELECTED_FAMILY_FIELDS:
        assert field in production
        assert field in schema_required
        assert isinstance(production[field], list)
        assert all(isinstance(item, str) for item in production[field])
    assert "atomicrows_bundle_digest_ref" in schema_required
    assert "source_dependency_state" in schema_required
    assert "selected_quantum_advisory_family_ids" in schema_required


def test_static_bundle_source_selected_stack_candidate_and_review_boundaries():
    production = _production()
    flags = production["explicit_no_claim_flags"]
    bundle = production["atomicrows_bundle_boundary_policy"]
    source = production["source_evidence_boundary_policy"]
    static_policy = production["static_packet_policy"]
    readiness = production["production_readiness"]

    assert production["atomicrows_bundle_digest_ref"] in validator.ALLOWED_BUNDLE_DIGEST_REFS
    assert bundle["atomicrows_bundle_digest_ref_static_placeholder_allowed"] is True
    assert bundle["atomicrows_bundle_file_created_by_this_pr"] is False
    assert bundle["atomicrows_bundle_sha_created_by_this_pr"] is False
    assert bundle["atomicrows_bundle_hash_authority_created_by_this_pr"] is False
    assert bundle["atomicrows_bundle_rows_created_by_this_pr"] is False
    assert source["source_dependency_state_is_static_metadata_only"] is True
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert production["selected_stack_id"] == "SYNTHETIC_SELECTED_STACK_ID_SCHEMA_FIELD_ONLY"
    assert static_policy["selected_stack_id_is_static_schema_field_only"] is True
    assert production["candidate_stack_generation_count"] == 0
    assert production["replay_paper_competition_required_flag"] is True
    assert production["owner_review_required_flag"] is True
    assert flags["owner_approval_receipt_created"] is False
    assert flags["owner_review_dashboard_runtime_created"] is False
    assert readiness == validator.PRODUCTION_READINESS_EXPECTED


def test_fixture_missing_required_role_family_fields_block_validation():
    missing_signal = _case_packet("EDGE_PACKET_BLOCKED_MISSING_SIGNAL_ROLE_FIELD")
    missing_quantum = _case_packet("EDGE_PACKET_BLOCKED_MISSING_QUANTUM_ADVISORY_ROLE_FIELD")

    assert any("selected_signal_family_ids" in failure for failure in _schema_failures(missing_signal))
    assert any(
        "selected_quantum_advisory_family_ids" in failure
        for failure in _schema_failures(missing_quantum)
    )


def test_incomplete_role_and_incompatible_compatibility_block_normal_readiness():
    role_case = _case_packet("EDGE_PACKET_BLOCKED_UPSTREAM_ROLE_INCOMPLETE")
    compatibility_case = _case_packet("EDGE_PACKET_BLOCKED_UPSTREAM_COMPATIBILITY_INCOMPLETE")

    assert role_case["role_completion_state"] in validator.ROLE_COMPLETION_STATES
    assert compatibility_case["compatibility_state"] in validator.COMPATIBILITY_STATES
    assert not _schema_failures(role_case)
    assert not _schema_failures(compatibility_case)
    assert validator._normal_packet_ready(role_case) is False
    assert validator._normal_packet_ready(compatibility_case) is False


def test_source_dependency_and_bundle_authority_attempts_fail_closed():
    source_case = _case_packet("EDGE_PACKET_BLOCKED_SOURCE_DEPENDENCY_NOT_ACCEPTED")
    bundle_case = _case_packet("EDGE_PACKET_BLOCKED_BUNDLE_AUTHORITY_ATTEMPT")

    assert not _schema_failures(source_case)
    assert source_case["source_dependency_state"] == (
        "SOURCE_DEPENDENCY_ACCEPTED_PACKET_REQUIRED_BEFORE_CONNECTOR_OR_LIVE_USE"
    )
    assert source_case["source_evidence_boundary_policy"]["accepted_source_packets_created"] is False
    assert validator._normal_packet_ready(source_case) is False
    assert any("atomicrows_bundle_digest_ref" in failure for failure in _schema_failures(bundle_case))


def test_selection_candidate_replay_paper_quantum_attempts_fail_schema():
    blocked_case_ids = [
        "EDGE_PACKET_BLOCKED_SELECTION_AUTHORITY_ATTEMPT",
        "EDGE_PACKET_BLOCKED_CANDIDATE_GENERATION_ATTEMPT",
        "EDGE_PACKET_BLOCKED_REPLAY_PAPER_EXECUTION_ATTEMPT",
        "EDGE_PACKET_BLOCKED_QUANTUM_BACKEND_ATTEMPT",
        "EDGE_PACKET_BLOCKED_QUANTUM_ADVANTAGE_CLAIM",
    ]

    for case_id in blocked_case_ids:
        assert _schema_failures(_case_packet(case_id)), case_id


def test_owner_override_is_internal_only_and_cannot_fabricate_evidence():
    production = _production()
    owner_case = _case_packet("OWNER_OVERRIDE_SATISFIED_INTERNAL_EDGE_PACKET_READINESS_ONLY")
    no_fabrication_case = _case_packet(
        "OWNER_GLOBAL_OVERRIDE_DOES_NOT_FABRICATE_EXTERNAL_FACTS_OR_EVIDENCE"
    )

    assert owner_case["role_completion_state"] == (
        "OWNER_OVERRIDE_SATISFIED_INTERNAL_STACK_READINESS_ONLY"
    )
    assert owner_case["compatibility_state"] == (
        "OWNER_OVERRIDE_SATISFIED_INTERNAL_COMPATIBILITY_ONLY"
    )
    assert production["owner_override_policy"][
        "owner_override_satisfies_internal_edge_packet_readiness_only"
    ] is True
    for field in validator.OWNER_OVERRIDE_FALSE_FIELDS:
        assert production["owner_override_policy"][field] is False
        assert no_fabrication_case["owner_override_policy"][field] is False
    assert not _schema_failures(owner_case)
    assert not _schema_failures(no_fabrication_case)


def test_no_scoring_selection_runtime_source_connector_profit_or_quantum_claims_created():
    production = _production()
    flags = production["explicit_no_claim_flags"]
    future = production["future_consumer_contract"]
    quantum = production["quantum_advisory_policy"]

    assert all(flags[field] is False for field in validator.EXPLICIT_NO_CLAIM_FALSE_FIELDS)
    assert all(future[field] is False for field in validator.FUTURE_CONSUMER_FALSE_FIELDS)
    assert quantum["selected_quantum_advisory_family_ids_required"] is True
    assert quantum["quantum_advisory_static_metadata_only"] is True
    assert all(quantum[field] is False for field in validator.QUANTUM_FALSE_FIELDS)
    assert flags["scoring_created"] is False
    assert flags["ranking_created"] is False
    assert flags["stack_selection_created"] is False
    assert flags["candidate_stack_generation_created"] is False
    assert flags["optimizer_arbitration_created"] is False
    assert flags["trade_context_routing_created"] is False
    assert flags["replay_execution_created"] is False
    assert flags["paper_execution_created"] is False
    assert flags["runtime_live_use_created"] is False
    assert flags["order_authority_created"] is False
    assert flags["profit_evidence_created"] is False
    assert flags["source_retrieval_created"] is False
    assert flags["source_acceptance_created"] is False
    assert flags["connector_semantic_binding_created"] is False
    assert flags["quantum_backend_evidence_created"] is False
    assert flags["quantum_advantage_claim_created"] is False


def test_forbidden_artifacts_master_plan_and_repair_pr76_state():
    completed = validator.subprocess.run(
        ["git", "diff", "--quiet", "--", str(validator.MASTER_PLAN_CURRENT)],
        stdout=validator.subprocess.PIPE,
        stderr=validator.subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 0
    assert not (ROOT / validator.CANONICAL_BUNDLE_JSONL).exists()
    assert not (ROOT / validator.CANONICAL_BUNDLE_SHA256).exists()
    assert (ROOT / validator.PR76_SHORT_TEST).exists()
    assert not (ROOT / validator.PR76_OLD_LONG_TEST).exists()
