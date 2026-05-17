from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_atomicrows_parameter_selection_universe_consumer_gate as validator


ROOT = Path(".")


def _schema() -> dict:
    return validator.load_json(validator.DEFAULT_SCHEMA)


def _production() -> dict:
    return validator.load_yaml(validator.DEFAULT_PRODUCTION_GATE)


def _fixture() -> dict:
    return validator.load_json(validator.DEFAULT_FIXTURE)


def _fixture_gate() -> dict:
    return validator._gate_from_fixture(_fixture())


def _report() -> dict:
    if not validator.DEFAULT_REPORT.exists():
        result = validator.validate(
            repo_root=ROOT,
            schema_path=validator.DEFAULT_SCHEMA,
            production_gate_path=validator.DEFAULT_PRODUCTION_GATE,
            fixture_path=validator.DEFAULT_FIXTURE,
            output_path=validator.DEFAULT_REPORT,
        )
        assert result.failures == ()
    return json.loads(validator.DEFAULT_REPORT.read_text(encoding="utf-8"))


def _case(case_id: str) -> dict:
    return {case["case_id"]: case for case in _fixture()["fixture_cases"]}[case_id]


def _case_access(case_id: str) -> dict:
    gate, request = validator._case_gate_from_fixture(_fixture(), _case(case_id))
    return validator.evaluate_consumer_access(gate, request)


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_production_consumer_gate_validates_and_report_is_deterministic(capsys):
    first = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        production_gate_path=validator.DEFAULT_PRODUCTION_GATE,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )
    second = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        production_gate_path=validator.DEFAULT_PRODUCTION_GATE,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )
    report_text = validator.DEFAULT_REPORT.read_text(encoding="utf-8")

    assert first.failures == second.failures == ()
    assert first.report == second.report == json.loads(report_text)
    assert report_text == json.dumps(json.loads(report_text), indent=2, sort_keys=True) + "\n"
    assert json.loads(report_text)["validation_marker"] == validator.SUCCESS_MARKER
    assert validator.SUCCESS_MARKER in report_text
    assert validator.main([]) == 0
    assert capsys.readouterr().out.strip() == validator.SUCCESS_MARKER


def test_pr79_pr78_pr77_pr73_pr74_pr75_and_pr76_dependencies_are_valid():
    _pr79_schema, pr79_registry, pr79_report, pr79_failures = validator.validate_pr79_dependency(ROOT)
    _trade_schema, _trade_packet, pr78_failures = validator.validate_pr78_dependency(ROOT)
    _edge_schema, _edge_packet, pr77_failures = validator.validate_pr77_dependency(ROOT)

    assert not validator.validate_pr73_dependency(ROOT)
    assert not validator.validate_pr74_dependency(ROOT)
    assert not validator.validate_pr75_dependency(ROOT)
    assert not pr77_failures
    assert not pr78_failures
    assert not pr79_failures
    assert not validator.validate_repair_pr76_dependency(ROOT)
    assert pr79_registry["required_selection_universe_ids"] == list(
        validator.REQUIRED_SELECTION_UNIVERSE_IDS
    )
    assert pr79_report["validation_marker"] == validator.PR79_SUCCESS_MARKER


def test_foundation_dependencies_are_present_and_static_reports_are_loaded():
    report = _report()

    assert validator.validate_agent_algorithm_foundation_dependencies(ROOT) == []
    assert validator.validate_atomicrows_lifecycle_binding_dependencies(ROOT) == []
    assert report["agent_algorithm_foundation_dependencies_present"] is True
    assert report["atomicrows_lifecycle_binding_dependencies_present"] is True
    for rel_path in validator.AGENT_ALGORITHM_FOUNDATION_REPORTS:
        assert (ROOT / rel_path).exists()
    for rel_path in validator.ATOMICROWS_LIFECYCLE_BINDING_REPORTS:
        assert (ROOT / rel_path).exists()


def test_required_universe_ids_authorized_classes_and_matrix_exist():
    production = _production()
    _schema_payload, pr79_registry, _report_payload, failures = validator.validate_pr79_dependency(ROOT)
    assert not failures

    assert production["required_selection_universe_ids"] == list(
        validator.REQUIRED_SELECTION_UNIVERSE_IDS
    )
    assert not validator.validate_required_universes(production, pr79_registry)
    assert not validator.validate_authorized_consumer_classes(production)
    assert not validator.validate_allowed_consumption_matrix(production)
    assert set(validator._matrix_by_universe(production)) == set(
        validator.REQUIRED_SELECTION_UNIVERSE_IDS
    )
    assert set(production["authorized_consumer_classes"]) == set(
        validator.AUTHORIZED_CONSUMER_CLASSES
    )


def test_matrix_references_pr79_universes_agent_roles_and_consumer_classes():
    production = _production()
    _schema_payload, pr79_registry, _report_payload, failures = validator.validate_pr79_dependency(ROOT)
    pr79_ids = {
        universe["universe_id"]
        for universe in pr79_registry["universe_definitions"]
    }

    assert not failures
    assert not validator.validate_agent_roles_exist(production, ROOT)
    assert not validator.validate_consumer_classes_exist(production)
    for row in production["allowed_universe_consumption_matrix"]:
        assert row["universe_id"] in pr79_ids
        assert set(row["allowed_agent_roles"]).issubset(
            validator._agent_roles_from_charter_schema(ROOT)
        )
        assert set(row["allowed_consumer_classes"]).issubset(
            set(production["authorized_consumer_classes"])
        )
        assert row["creates_routing"] is False
        assert row["creates_selection"] is False
        assert row["creates_scoring"] is False
        assert row["creates_optimizer_arbitration"] is False
        assert row["creates_runtime"] is False
        assert row["creates_order_authority"] is False


def test_unknown_and_disallowed_consumer_access_cases_block_normal_access():
    assert "UNKNOWN_UNIVERSE_ID_BLOCKED" in _case_access(
        "SELECTION_UNIVERSE_CONSUMER_BLOCKED_UNKNOWN_UNIVERSE_ID"
    )["block_reason_codes"]
    assert "UNKNOWN_AGENT_ROLE_BLOCKED" in _case_access(
        "SELECTION_UNIVERSE_CONSUMER_BLOCKED_UNKNOWN_AGENT_ROLE"
    )["block_reason_codes"]
    assert "UNKNOWN_CONSUMER_CLASS_BLOCKED" in _case_access(
        "SELECTION_UNIVERSE_CONSUMER_BLOCKED_UNKNOWN_CONSUMER_CLASS"
    )["block_reason_codes"]
    assert "MISSING_UNIVERSE_BINDING_BLOCKED" in _case_access(
        "SELECTION_UNIVERSE_CONSUMER_BLOCKED_MISSING_UNIVERSE_BINDING"
    )["block_reason_codes"]
    assert "DISALLOWED_AGENT_UNIVERSE_PAIR_BLOCKED" in _case_access(
        "SELECTION_UNIVERSE_CONSUMER_BLOCKED_DISALLOWED_AGENT_UNIVERSE_PAIR"
    )["block_reason_codes"]
    assert "DISALLOWED_CONSUMER_CLASS_BLOCKED" in _case_access(
        "SELECTION_UNIVERSE_CONSUMER_BLOCKED_DISALLOWED_CONSUMER_CLASS"
    )["block_reason_codes"]


def test_owner_override_satisfies_internal_access_only_and_fabricates_no_evidence():
    production = _production()
    owner = production["owner_override_policy"]
    access = _case_access("OWNER_OVERRIDE_SATISFIED_INTERNAL_SELECTION_UNIVERSE_CONSUMER_ACCESS_ONLY")

    assert access["normal_access_allowed"] is False
    assert access["owner_override_access_allowed"] is True
    assert access["final_internal_access_allowed"] is True
    assert owner["owner_override_satisfies_internal_selection_universe_consumer_access_only"] is True
    assert owner["owner_override_fabricates_external_fact"] is False
    assert owner["owner_override_fabricates_accepted_source_packet"] is False
    assert owner["owner_override_fabricates_connector_semantic"] is False
    assert owner["owner_override_fabricates_runtime_cash_receipt"] is False
    assert owner["owner_override_fabricates_order_receipt"] is False
    assert owner["owner_override_fabricates_replay_paper_result"] is False
    assert owner["owner_override_fabricates_quantum_backend_execution"] is False
    assert owner["owner_override_fabricates_profit_evidence"] is False


def test_consumer_gate_is_static_deterministic_and_does_not_route_select_score_or_arbitrate():
    production = _production()
    static = production["gate_static_policy"]
    future = production["future_consumer_contract"]
    readiness = production["production_readiness"]

    assert static["selection_universe_consumer_gate_is_static_only"] is True
    assert static["agent_universe_consumer_access_is_deterministic"] is True
    assert static["random_consumer_access_allowed"] is False
    assert static["dynamic_runtime_access_evaluation_created"] is False
    assert static["trade_context_to_selection_universe_routing_created"] is False
    assert static["routed_universe_ids_created"] is False
    assert static["route_result_created"] is False
    assert static["selected_stack_created"] is False
    assert static["stack_selection_created"] is False
    assert static["scoring_created"] is False
    assert static["ranking_created"] is False
    assert static["optimizer_arbitration_created"] is False
    assert static["candidate_stack_generation_created"] is False
    assert static["replay_paper_execution_created"] is False
    assert static["runtime_live_order_authority_created"] is False
    assert future["this_pr_performs_routing"] is False
    assert future["this_pr_performs_scoring"] is False
    assert future["this_pr_performs_ranking"] is False
    assert future["this_pr_performs_selection"] is False
    assert future["this_pr_performs_arbitration"] is False
    assert future["this_pr_generates_candidate_stacks"] is False
    assert future["this_pr_executes_replay_or_paper"] is False
    assert future["this_pr_executes_runtime_or_live"] is False
    assert readiness == validator.PRODUCTION_READINESS_EXPECTED


def test_source_connector_runtime_live_order_and_profit_boundaries_not_created():
    production = _production()
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    flags = production["explicit_no_claim_flags"]

    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert source["market_data_fact_requires_accepted_source_packet"] is True
    assert source["liquidity_fact_requires_accepted_source_packet"] is True
    assert flags["market_data_fact_created"] is False
    assert flags["liquidity_fact_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert connector["connector_semantic_value_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["runtime_resolver_execution_created"] is False
    assert runtime["live_readiness_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["private_state_fetch_created"] is False
    assert runtime["order_intent_authority_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["cash_receipts_created"] is False
    assert runtime["order_receipts_created"] is False
    assert runtime["fill_receipts_created"] is False
    assert runtime["profit_evidence_created"] is False


def test_quantum_universe_consumer_access_is_static_metadata_only():
    production = _production()
    quantum = production["quantum_consumer_policy"]
    quantum_row = validator._matrix_by_universe(production)[
        "QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION"
    ]

    assert quantum_row["quantum_static_access_only"] is True
    assert "QUANTUM_BACKEND_AGENT" in quantum_row["allowed_agent_roles"]
    assert "QUANTUM_UNIVERSE_METADATA_CONSUMER_STATIC_ONLY" in quantum_row[
        "allowed_consumer_classes"
    ]
    assert quantum["quantum_optimized_portfolio_selection_consumption_supported_static_only"] is True
    assert quantum["quantum_consumer_access_static_metadata_only"] is True
    assert quantum["future_quantum_applicability_registry_required_before_quantum_selection"] is True
    assert quantum["future_owner_quantum_priority_policy_required_before_quantum_priority_selection"] is True
    assert quantum["future_optimizer_arbitration_gate_required_before_optimizer_choice"] is True
    assert quantum["strongest_classical_comparator_required_before_quantum_advantage_claim"] is True
    assert quantum["fallback_bundle_required_before_quantum_runtime_use"] is True
    assert quantum["replay_paper_evidence_required_before_advantage_claim"] is True
    assert quantum["live_evidence_required_before_profit_claim"] is True
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False


def test_fixture_negative_cases_fail_closed_with_required_blockers():
    fixture = _fixture()
    _schema_payload, pr79_registry, _report_payload, failures = validator.validate_pr79_dependency(ROOT)

    assert not failures
    assert not validator.validate_fixture_cases(fixture, _schema(), pr79_registry, ROOT)
    for case_id in validator.REQUIRED_FIXTURE_CASE_IDS:
        assert _case(case_id)["synthetic_case_only"] is True


def test_in_memory_negative_fixtures_block_forbidden_outputs_and_boundaries():
    production = _production()

    mutated = copy.deepcopy(production)
    mutated["gate_static_policy"]["route_result_created"] = True
    _assert_failure_contains(validator.validate_gate_static_policy(mutated), "route_result_created")

    mutated = copy.deepcopy(production)
    mutated["routed_universe_ids"] = ["SYNTHETIC_FORBIDDEN"]
    _assert_failure_contains(validator.validate_forbidden_output_fields(mutated), "routed_universe_ids")

    mutated = copy.deepcopy(production)
    mutated["selected_stack_id"] = "SYNTHETIC_FORBIDDEN"
    _assert_failure_contains(validator.validate_forbidden_output_fields(mutated), "selected_stack_id")

    mutated = copy.deepcopy(production)
    mutated["score_breakdown"] = {"SYNTHETIC_SCORE": "FORBIDDEN"}
    _assert_failure_contains(validator.validate_forbidden_output_fields(mutated), "score_breakdown")

    mutated = copy.deepcopy(production)
    mutated["optimizer_arbitration_result"] = "SYNTHETIC_FORBIDDEN"
    _assert_failure_contains(
        validator.validate_forbidden_output_fields(mutated),
        "optimizer_arbitration_result",
    )

    mutated = copy.deepcopy(production)
    mutated["source_evidence_boundary_policy"]["source_acceptance_created"] = True
    _assert_failure_contains(
        validator.validate_source_evidence_boundary(mutated),
        "source_acceptance_created",
    )

    mutated = copy.deepcopy(production)
    mutated["connector_semantic_boundary_policy"]["connector_semantic_binding_created"] = True
    _assert_failure_contains(
        validator.validate_connector_semantic_boundary(mutated),
        "connector_semantic_binding_created",
    )

    mutated = copy.deepcopy(production)
    mutated["runtime_live_order_boundary_policy"]["order_authority_created"] = True
    _assert_failure_contains(
        validator.validate_runtime_live_order_boundary(mutated),
        "order_authority_created",
    )

    mutated = copy.deepcopy(production)
    mutated["quantum_consumer_policy"]["quantum_backend_execution_created"] = True
    _assert_failure_contains(
        validator.validate_quantum_consumer_boundary(mutated),
        "quantum_backend_execution_created",
    )

    mutated = copy.deepcopy(production)
    mutated["quantum_consumer_policy"]["quantum_advantage_claim_created"] = True
    _assert_failure_contains(
        validator.validate_quantum_consumer_boundary(mutated),
        "quantum_advantage_claim_created",
    )


def test_forbidden_output_fields_no_claim_flags_artifacts_and_master_plan_state():
    production = _production()
    fixture_gate = _fixture_gate()
    completed = validator.subprocess.run(
        ["git", "diff", "--quiet", "--", str(validator.MASTER_PLAN_CURRENT)],
        stdout=validator.subprocess.PIPE,
        stderr=validator.subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 0
    assert validator.validate_master_plan_not_modified(ROOT) == []
    assert not validator.validate_forbidden_output_fields(production, "production")
    assert not validator.validate_forbidden_output_fields(fixture_gate, "fixture")
    assert all(
        production["explicit_no_claim_flags"][field] is False
        for field in validator.EXPLICIT_NO_CLAIM_FALSE_FIELDS
    )
    for field in validator.FORBIDDEN_OUTPUT_FIELDS:
        assert field not in production
        assert field not in fixture_gate
        assert field not in _schema()["properties"]
    assert (ROOT / validator.CANONICAL_BUNDLE_JSONL).exists()
    assert not (ROOT / validator.CANONICAL_BUNDLE_SHA256).exists()
    assert (ROOT / validator.PR76_SHORT_TEST).exists()
    assert not (ROOT / validator.PR76_OLD_LONG_TEST).exists()
    report = _report()
    assert report["atomicrows_bundle_jsonl_exists"] is True
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert report["repair_pr76_long_path_fix_present"] is True
