from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_atomicrows_parameter_stack_compatibility_gate as gate


REPO_ROOT = Path(".")
SCHEMA = Path(
    "schemas/atomicrows/atomicrows_parameter_stack_compatibility_gate.schema.json"
)
PRODUCTION_GATE = Path(
    "docs/master_plan/atomicrows/AtomicRowsParameterStackCompatibilityGate.yaml"
)
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_parameter_stack_compatibility_gate.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/AtomicRowsParameterStackCompatibilityGate.report.json"
)


def _schema() -> dict:
    return gate.load_json(SCHEMA)


def _production_gate() -> dict:
    return gate.load_yaml(PRODUCTION_GATE)


def _fixture() -> dict:
    return gate.load_json(FIXTURE)


def _report() -> dict:
    if not REPORT.exists():
        result = gate.validate(
            repo_root=REPO_ROOT,
            schema_path=SCHEMA,
            production_gate_path=PRODUCTION_GATE,
            fixture_path=FIXTURE,
            output_path=REPORT,
        )
        assert result.failures == ()
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _case(fixture: dict, case_id: str) -> dict:
    return {
        case["stack_case_id"]: case
        for case in fixture["compatibility_cases"]
    }[case_id]


def _assert_failure_contains(failures: tuple[str, ...] | list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_production_pr75_gate_validates_and_main_prints_marker(capsys):
    result = gate.validate(
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        production_gate_path=PRODUCTION_GATE,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )

    assert result.failures == ()
    assert gate.main([]) == 0
    assert capsys.readouterr().out.strip() == gate.SUCCESS_MARKER


def test_generated_report_is_deterministic_and_contains_success_marker():
    first = gate.validate(
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        production_gate_path=PRODUCTION_GATE,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )
    second = gate.validate(
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        production_gate_path=PRODUCTION_GATE,
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


def test_required_roles_match_pr73_and_pr74_dependencies():
    pr73_roles, pr73_failures = gate.validate_pr73_dependency(REPO_ROOT)
    pr74_roles, pr74_failures = gate.validate_pr74_dependency(REPO_ROOT, pr73_roles)
    production = _production_gate()
    fixture = _fixture()

    assert pr73_failures == []
    assert pr74_failures == []
    assert pr73_roles == pr74_roles == list(gate.REQUIRED_STACK_ROLES)
    assert production["required_stack_roles"] == pr73_roles
    assert fixture["required_stack_roles"] == pr73_roles


def test_all_nine_role_interface_contracts_exist_and_match_expected_contracts():
    production = _production_gate()
    fixture = _fixture()

    assert gate.validate_role_interface_contracts(production, "production") == []
    assert gate.validate_role_interface_contracts(fixture, "fixture") == []
    assert [c["role_id"] for c in production["role_interface_contracts"]] == list(
        gate.REQUIRED_STACK_ROLES
    )
    assert len(production["role_interface_contracts"]) == 9


def test_compatible_role_complete_case_is_complete():
    case = _case(_fixture(), "SYNTHETIC_ROLE_COMPLETE_ALL_INTERFACES_COMPATIBLE")

    assert case["supplied_role_ids"] == list(gate.REQUIRED_STACK_ROLES)
    assert case["role_complete"] is True
    assert case["compatibility_state"] == "COMPATIBILITY_COMPLETE"
    assert case["normal_stack_compatibility"] == "NORMAL_STACK_COMPATIBLE"
    assert case["role_interface_bindings"] == list(gate.EXPECTED_COMPATIBLE_BINDINGS)


def test_upstream_role_incomplete_blocks_normal_compatibility():
    case = _case(_fixture(), "SYNTHETIC_UPSTREAM_ROLE_INCOMPLETE_BLOCKS_COMPATIBILITY")

    assert case["upstream_completeness_state"] == "ROLE_INCOMPLETE_MISSING_REQUIRED_ROLE"
    assert case["role_complete"] is False
    assert case["compatibility_state"] == "COMPATIBILITY_BLOCKED_UPSTREAM_ROLE_INCOMPLETE"
    assert case["normal_stack_compatibility"] == "NORMAL_STACK_BLOCKED"


def test_missing_interface_blocks_normal_compatibility_with_negative_fixture():
    fixture = _fixture()
    case = _case(fixture, "SYNTHETIC_MISSING_SIGNAL_OUTPUT_INTERFACE_BLOCKS_SCORING")

    assert case["missing_interface_ids"] == ["signal_candidate_interface"]
    assert case["compatibility_state"] == "COMPATIBILITY_INCOMPLETE_MISSING_INTERFACE"
    assert case["normal_stack_compatibility"] == "NORMAL_STACK_BLOCKED"

    mutated = copy.deepcopy(fixture)
    _case(mutated, case["stack_case_id"])["compatibility_state"] = "COMPATIBILITY_COMPLETE"
    failures = gate.validate_fixture_cases(mutated, _schema(), list(gate.REQUIRED_STACK_ROLES))
    _assert_failure_contains(failures, "COMPATIBILITY_INCOMPLETE_MISSING_INTERFACE")


def test_interface_mismatch_and_duplicate_interface_block_normal_compatibility():
    fixture = _fixture()
    mismatch = _case(fixture, "SYNTHETIC_SCORING_CONSUMES_WRONG_SIGNAL_INTERFACE")
    duplicate = _case(
        fixture,
        "SYNTHETIC_DUPLICATE_NORMALIZED_CANDIDATE_INTERFACE_BINDING",
    )

    assert mismatch["mismatched_interface_ids"] == ["signal_candidate_interface_v2_wrong"]
    assert mismatch["compatibility_state"] == "COMPATIBILITY_INCOMPLETE_INTERFACE_MISMATCH"
    assert mismatch["normal_stack_compatibility"] == "NORMAL_STACK_BLOCKED"
    assert duplicate["duplicate_interface_ids"] == ["normalized_candidate_interface"]
    assert duplicate["compatibility_state"] == "COMPATIBILITY_INCOMPLETE_DUPLICATE_INTERFACE"
    assert duplicate["normal_stack_compatibility"] == "NORMAL_STACK_BLOCKED"


def test_authority_source_connector_runtime_and_quantum_boundaries_block():
    fixture = _fixture()
    expectations = {
        "SYNTHETIC_SIGNAL_PRODUCES_ORDER_AUTHORITY": "COMPATIBILITY_INCOMPATIBLE_AUTHORITY_TRANSITION",
        "SYNTHETIC_NORMALIZATION_SOURCE_FACT_WITHOUT_ACCEPTED_PACKET": "COMPATIBILITY_INCOMPATIBLE_SOURCE_FACT_BOUNDARY",
        "SYNTHETIC_EXECUTION_CONNECTOR_SEMANTIC_WITHOUT_ACCEPTED_PACKET": "COMPATIBILITY_INCOMPATIBLE_CONNECTOR_SEMANTIC_BOUNDARY",
        "SYNTHETIC_EXECUTION_ATTEMPTS_LIVE_ORDER_AUTHORITY": "COMPATIBILITY_INCOMPATIBLE_RUNTIME_LIVE_ORDER_BOUNDARY",
        "SYNTHETIC_CAPITAL_ATTEMPTS_RUNTIME_CASH_RECEIPT": "COMPATIBILITY_INCOMPATIBLE_RUNTIME_LIVE_ORDER_BOUNDARY",
        "SYNTHETIC_LATENCY_ATTEMPTS_LATENCY_SUPERIORITY_CLAIM": "COMPATIBILITY_INCOMPATIBLE_RUNTIME_LIVE_ORDER_BOUNDARY",
        "SYNTHETIC_QUANTUM_ADVISORY_ATTEMPTS_BACKEND_EXECUTION": "COMPATIBILITY_INCOMPATIBLE_QUANTUM_BOUNDARY",
        "SYNTHETIC_QUANTUM_ADVISORY_ATTEMPTS_ADVANTAGE_CLAIM": "COMPATIBILITY_INCOMPATIBLE_QUANTUM_BOUNDARY",
        "SYNTHETIC_QUANTUM_ADVISORY_MISSING_FUTURE_APPLICABILITY_METADATA": "COMPATIBILITY_INCOMPATIBLE_QUANTUM_BOUNDARY",
    }

    for case_id, expected_state in expectations.items():
        case = _case(fixture, case_id)
        assert case["compatibility_state"] == expected_state
        assert case["normal_stack_compatibility"] == "NORMAL_STACK_BLOCKED"


def test_owner_global_override_satisfies_internal_compatibility_only():
    fixture = _fixture()
    case_ids = [
        "SYNTHETIC_MISSING_INTERFACE_WITH_OWNER_GLOBAL_OVERRIDE",
        "SYNTHETIC_QUANTUM_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE",
        "SYNTHETIC_SOURCE_FACT_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE",
        "SYNTHETIC_CONNECTOR_SEMANTIC_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE",
        "SYNTHETIC_RUNTIME_ORDER_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE",
    ]

    for case_id in case_ids:
        case = _case(fixture, case_id)
        assert case["owner_override_present"] is True
        assert case["owner_override_satisfaction_basis"] == gate.OWNER_GLOBAL_OVERRIDE
        assert case["compatibility_state"] == gate.OWNER_OVERRIDE_INTERNAL_ONLY
        assert (
            case["owner_override_stack_compatibility"]
            == "OWNER_OVERRIDE_INTERNAL_STACK_COMPATIBILITY_SATISFIED"
        )
        assert case["normal_stack_compatibility"] == "NORMAL_STACK_BLOCKED"
        assert case["final_stack_compatibility"] is False


def test_owner_override_cannot_fabricate_facts_or_evidence_with_negative_fixture():
    production = _production_gate()
    policy = production["owner_override_policy"]

    for field in gate.OWNER_OVERRIDE_FALSE_FIELDS:
        assert policy[field] is False

    mutated = copy.deepcopy(production)
    for field in gate.OWNER_OVERRIDE_FALSE_FIELDS:
        mutated["owner_override_policy"][field] = True
    failures = gate.validate_production_gate(
        mutated, _schema(), list(gate.REQUIRED_STACK_ROLES)
    )

    for field in gate.OWNER_OVERRIDE_FALSE_FIELDS:
        _assert_failure_contains(failures, field)


def test_no_scoring_ranking_selection_generation_arbitration_or_routing_created():
    production = _production_gate()
    flags = production["explicit_no_claim_flags"]
    contract = production["future_consumer_contract"]
    report = _report()

    assert flags["creates_scoring"] is False
    assert flags["creates_ranking"] is False
    assert flags["creates_stack_selection"] is False
    assert flags["creates_candidate_stack_generation"] is False
    assert flags["creates_optimizer_arbitration"] is False
    assert flags["creates_trade_context_routing"] is False
    assert contract["this_gate_performs_scoring"] is False
    assert contract["this_gate_performs_ranking"] is False
    assert contract["this_gate_performs_selection"] is False
    assert contract["this_gate_performs_arbitration"] is False
    assert contract["this_gate_routes_trade_context"] is False
    assert report["scoring_created"] is False
    assert report["ranking_created"] is False
    assert report["stack_selection_created"] is False
    assert report["candidate_stack_generation_created"] is False
    assert report["optimizer_arbitration_created"] is False
    assert report["trade_context_routing_created"] is False


def test_no_replay_paper_runtime_live_order_profit_or_quantum_evidence_created():
    production = _production_gate()
    flags = production["explicit_no_claim_flags"]
    runtime = production["runtime_live_order_boundary_policy"]
    quantum = production["quantum_compatibility_policy"]
    report = _report()

    assert flags["creates_replay_results"] is False
    assert flags["creates_paper_results"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["live_readiness_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["private_state_fetch_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["cash_receipts_created"] is False
    assert runtime["order_receipts_created"] is False
    assert runtime["fill_receipts_created"] is False
    assert runtime["profit_evidence_created"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert flags["creates_quantum_backend_evidence"] is False
    assert flags["creates_quantum_advantage_claim"] is False
    assert report["replay_results_created"] is False
    assert report["paper_results_created"] is False
    assert report["runtime_artifacts_created"] is False
    assert report["live_readiness_created"] is False
    assert report["runtime_live_use_created"] is False
    assert report["private_state_fetch_created"] is False
    assert report["order_authority_created"] is False
    assert report["profit_evidence_created"] is False
    assert report["quantum_backend_evidence_created"] is False
    assert report["quantum_advantage_claim_created"] is False


def test_no_source_retrieval_acceptance_or_connector_binding_created():
    production = _production_gate()
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    report = _report()

    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert report["source_retrieval_created"] is False
    assert report["source_acceptance_created"] is False
    assert report["accepted_source_packets_created"] is False
    assert report["connector_semantics_created"] is False
    assert report["connector_semantic_binding_created"] is False


def test_contract_ready_but_not_production_or_final_ready():
    production = _production_gate()
    readiness = production["production_readiness"]
    report = _report()

    assert readiness["compatibility_gate_contract_ready"] is True
    assert readiness["production_stack_compatibility_evaluated"] is False
    assert readiness["production_stack_compatible"] is False
    assert readiness["production_stack_ready"] is False
    assert readiness["final_ready"] is False
    assert production["final_ready"] is False
    assert report["compatibility_gate_contract_ready"] is True
    assert report["production_stack_compatibility_evaluated"] is False
    assert report["production_stack_compatible"] is False
    assert report["production_stack_ready"] is False
    assert report["final_ready"] is False


def test_forbidden_atomicrows_bundle_files_absent_and_master_plan_unmodified():
    report = _report()

    assert (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()
    assert report["atomicrows_bundle_jsonl_exists"] is True
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert gate.validate_master_plan_not_modified(REPO_ROOT) == []
