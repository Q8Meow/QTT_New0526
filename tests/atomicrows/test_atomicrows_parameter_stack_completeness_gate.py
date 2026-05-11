from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_atomicrows_parameter_stack_completeness_gate as gate


REPO_ROOT = Path(".")
SCHEMA = Path(
    "schemas/atomicrows/atomicrows_parameter_stack_completeness_gate.schema.json"
)
PRODUCTION_GATE = Path(
    "docs/master_plan/atomicrows/AtomicRowsParameterStackCompletenessGate.yaml"
)
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_parameter_stack_completeness_gate.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/AtomicRowsParameterStackCompletenessGate.report.json"
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
        for case in fixture["completeness_cases"]
    }[case_id]


def _assert_failure_contains(failures: tuple[str, ...] | list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_production_pr74_gate_validates_and_main_prints_marker(capsys):
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


def test_required_role_list_exactly_matches_pr73():
    pr73_roles, failures = gate.validate_pr73_dependency(REPO_ROOT)
    production = _production_gate()
    fixture = _fixture()

    assert failures == []
    assert pr73_roles == list(gate.REQUIRED_STACK_ROLES)
    assert production["required_stack_roles"] == pr73_roles
    assert fixture["required_stack_roles"] == pr73_roles


def test_full_role_case_is_complete():
    case = _case(_fixture(), "SYNTHETIC_ALL_NINE_REQUIRED_ROLES_PRESENT")

    assert case["supplied_role_ids"] == list(gate.REQUIRED_STACK_ROLES)
    assert case["missing_role_ids"] == []
    assert case["duplicate_role_ids"] == []
    assert case["role_completion_state"] == "ROLE_COMPLETE"
    assert case["normal_stack_readiness"] == "NORMAL_STACK_READY"
    assert case["final_stack_readiness"] is False


def test_missing_signal_blocks_normal_readiness():
    case = _case(_fixture(), "SYNTHETIC_MISSING_SIGNAL_BLOCKS_NORMAL_READINESS")

    assert case["missing_role_ids"] == ["SIGNAL"]
    assert case["role_completion_state"] == "ROLE_INCOMPLETE_MISSING_REQUIRED_ROLE"
    assert case["normal_stack_readiness"] == "NORMAL_STACK_BLOCKED"

    mutated = copy.deepcopy(_fixture())
    _case(mutated, case["stack_case_id"])["normal_stack_readiness"] = "NORMAL_STACK_READY"
    failures = gate.validate_fixture_cases(mutated, _schema(), list(gate.REQUIRED_STACK_ROLES))
    _assert_failure_contains(failures, "missing SIGNAL case must block normal readiness")


def test_missing_quantum_advisory_blocks_normal_completeness():
    case = _case(
        _fixture(),
        "SYNTHETIC_MISSING_QUANTUM_ADVISORY_BLOCKS_NORMAL_COMPLETENESS",
    )

    assert case["missing_role_ids"] == ["QUANTUM_ADVISORY"]
    assert case["role_completion_state"] == "ROLE_INCOMPLETE_MISSING_REQUIRED_ROLE"
    assert case["normal_stack_readiness"] == "NORMAL_STACK_BLOCKED"
    assert _production_gate()["quantum_advisory_policy"][
        "missing_quantum_advisory_blocks_normal_completeness"
    ] is True


def test_duplicate_role_blocks_normal_readiness():
    case = _case(_fixture(), "SYNTHETIC_DUPLICATE_SIGNAL_BLOCKS_NORMAL_READINESS")

    assert case["duplicate_role_ids"] == ["SIGNAL"]
    assert case["role_completion_state"] == "ROLE_INCOMPLETE_DUPLICATE_ROLE"
    assert case["normal_stack_readiness"] == "NORMAL_STACK_BLOCKED"

    mutated = copy.deepcopy(_fixture())
    _case(mutated, case["stack_case_id"])["role_completion_state"] = "ROLE_COMPLETE"
    failures = gate.validate_fixture_cases(mutated, _schema(), list(gate.REQUIRED_STACK_ROLES))
    _assert_failure_contains(failures, "duplicate role case must be duplicate-role incomplete")


def test_single_parameter_set_is_incomplete_without_owner_override():
    production = _production_gate()
    case = _case(_fixture(), "SYNTHETIC_SINGLE_PARAMETER_SET_WITHOUT_OWNER_OVERRIDE")

    assert production["completeness_policy"][
        "single_parameter_set_complete_without_owner_override"
    ] is False
    assert case["single_parameter_set"] is True
    assert case["owner_override_present"] is False
    assert case["role_completion_state"] == "ROLE_INCOMPLETE_SINGLE_PARAMETER_ONLY"
    assert case["normal_stack_readiness"] == "NORMAL_STACK_BLOCKED"


def test_single_algorithm_set_is_incomplete_without_owner_override():
    production = _production_gate()
    case = _case(_fixture(), "SYNTHETIC_SINGLE_ALGORITHM_SET_WITHOUT_OWNER_OVERRIDE")

    assert production["completeness_policy"][
        "single_algorithm_set_complete_without_owner_override"
    ] is False
    assert case["single_algorithm_set"] is True
    assert case["owner_override_present"] is False
    assert case["role_completion_state"] == "ROLE_INCOMPLETE_SINGLE_ALGORITHM_ONLY"
    assert case["normal_stack_readiness"] == "NORMAL_STACK_BLOCKED"


def test_owner_global_override_satisfies_internal_stack_readiness_only():
    fixture = _fixture()
    case_ids = [
        "SYNTHETIC_MISSING_RISK_WITH_OWNER_GLOBAL_OVERRIDE",
        "SYNTHETIC_SINGLE_PARAMETER_SET_WITH_OWNER_GLOBAL_OVERRIDE",
        "SYNTHETIC_SINGLE_ALGORITHM_SET_WITH_OWNER_GLOBAL_OVERRIDE",
    ]

    for case_id in case_ids:
        case = _case(fixture, case_id)
        assert case["owner_override_present"] is True
        assert case["owner_override_satisfaction_basis"] == gate.OWNER_GLOBAL_OVERRIDE
        assert case["role_completion_state"] == gate.OWNER_OVERRIDE_INTERNAL_ONLY
        assert (
            case["owner_override_stack_readiness"]
            == "OWNER_OVERRIDE_INTERNAL_STACK_READINESS_SATISFIED"
        )
        assert case["normal_stack_readiness"] == "NORMAL_STACK_BLOCKED"
        assert case["final_stack_readiness"] is False


def test_owner_override_cannot_fabricate_external_facts_or_evidence():
    production = _production_gate()
    policy = production["owner_override_policy"]

    for field in gate.OWNER_OVERRIDE_FALSE_FIELDS:
        assert policy[field] is False

    mutated = copy.deepcopy(production)
    mutated["owner_override_policy"]["owner_override_fabricates_external_fact"] = True
    mutated["owner_override_policy"][
        "owner_override_fabricates_accepted_source_packet"
    ] = True
    mutated["owner_override_policy"]["owner_override_fabricates_connector_semantic"] = True
    mutated["owner_override_policy"][
        "owner_override_fabricates_runtime_cash_receipt"
    ] = True
    mutated["owner_override_policy"]["owner_override_fabricates_order_receipt"] = True
    mutated["owner_override_policy"][
        "owner_override_fabricates_replay_paper_result"
    ] = True
    mutated["owner_override_policy"][
        "owner_override_fabricates_quantum_backend_execution"
    ] = True
    mutated["owner_override_policy"]["owner_override_fabricates_profit_evidence"] = True

    failures = gate.validate_production_gate(
        mutated, _schema(), list(gate.REQUIRED_STACK_ROLES)
    )

    for field in gate.OWNER_OVERRIDE_FALSE_FIELDS:
        _assert_failure_contains(failures, field)


def test_no_stack_compatibility_selection_scoring_ranking_arbitration_or_routing():
    production = _production_gate()
    contract = production["future_consumer_contract"]
    flags = production["explicit_no_claim_flags"]
    report = _report()

    assert contract["this_gate_performs_compatibility"] is False
    assert contract["this_gate_performs_scoring"] is False
    assert contract["this_gate_performs_selection"] is False
    assert contract["this_gate_performs_arbitration"] is False
    assert contract["this_gate_routes_trade_context"] is False
    assert flags["creates_stack_compatibility_gate"] is False
    assert flags["creates_stack_selection"] is False
    assert flags["creates_scoring"] is False
    assert flags["creates_ranking"] is False
    assert flags["creates_optimizer_arbitration"] is False
    assert flags["creates_trade_context_routing"] is False
    assert report["stack_compatibility_gate_created"] is False
    assert report["stack_selection_created"] is False
    assert report["scoring_created"] is False
    assert report["ranking_created"] is False
    assert report["optimizer_arbitration_created"] is False
    assert report["trade_context_routing_created"] is False


def test_no_runtime_live_order_profit_replay_paper_or_quantum_evidence_created():
    production = _production_gate()
    flags = production["explicit_no_claim_flags"]
    report = _report()

    assert flags["creates_runtime_artifacts"] is False
    assert flags["creates_live_readiness"] is False
    assert flags["creates_order_authority"] is False
    assert flags["creates_cash_receipts"] is False
    assert flags["creates_replay_results"] is False
    assert flags["creates_paper_results"] is False
    assert flags["creates_profit_evidence"] is False
    assert flags["creates_quantum_backend_evidence"] is False
    assert flags["creates_quantum_advantage_claim"] is False
    assert report["runtime_artifacts_created"] is False
    assert report["live_readiness_created"] is False
    assert report["order_authority_created"] is False
    assert report["cash_receipts_created"] is False
    assert report["replay_results_created"] is False
    assert report["paper_results_created"] is False
    assert report["profit_evidence_created"] is False
    assert report["quantum_backend_evidence_created"] is False
    assert report["quantum_advantage_claim_created"] is False


def test_forbidden_atomicrows_bundle_files_absent_and_master_plan_unmodified():
    report = _report()

    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()
    assert report["atomicrows_bundle_jsonl_exists"] is False
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert gate.validate_master_plan_not_modified(REPO_ROOT) == []


def test_completeness_gate_contract_ready_but_not_production_or_final_ready():
    production = _production_gate()
    readiness = production["production_readiness"]
    report = _report()

    assert readiness["completeness_gate_contract_ready"] is True
    assert readiness["production_stack_completeness_evaluated"] is False
    assert readiness["production_stack_ready"] is False
    assert readiness["final_ready"] is False
    assert production["final_ready"] is False
    assert report["completeness_gate_contract_ready"] is True
    assert report["production_stack_completeness_evaluated"] is False
    assert report["production_stack_ready"] is False
    assert report["final_ready"] is False


def test_source_retrieval_acceptance_and_connector_semantics_are_not_created():
    production = _production_gate()
    flags = production["explicit_no_claim_flags"]
    report = _report()

    assert flags["retrieves_source_facts"] is False
    assert flags["accepts_source_facts"] is False
    assert flags["creates_accepted_source_packets"] is False
    assert flags["creates_connector_semantics"] is False
    assert report["source_retrieval_created"] is False
    assert report["source_acceptance_created"] is False
    assert report["accepted_source_packets_created"] is False
    assert report["connector_semantics_created"] is False

