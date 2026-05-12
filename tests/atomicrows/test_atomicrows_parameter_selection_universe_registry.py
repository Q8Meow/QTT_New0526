from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_atomicrows_parameter_selection_universe_registry as validator


ROOT = Path(".")


def _schema() -> dict:
    return validator.load_json(validator.DEFAULT_SCHEMA)


def _production() -> dict:
    return validator.load_yaml(validator.DEFAULT_PRODUCTION_REGISTRY)


def _fixture() -> dict:
    return validator.load_json(validator.DEFAULT_FIXTURE)


def _fixture_registry() -> dict:
    return validator._fixture_to_registry(_fixture())


def _report() -> dict:
    if not validator.DEFAULT_REPORT.exists():
        result = validator.validate(
            repo_root=ROOT,
            schema_path=validator.DEFAULT_SCHEMA,
            production_registry_path=validator.DEFAULT_PRODUCTION_REGISTRY,
            fixture_path=validator.DEFAULT_FIXTURE,
            output_path=validator.DEFAULT_REPORT,
        )
        assert result.failures == ()
    return json.loads(validator.DEFAULT_REPORT.read_text(encoding="utf-8"))


def _case(case_id: str) -> dict:
    return {
        case["case_id"]: case
        for case in _fixture()["fixture_cases"]
    }[case_id]


def _case_registry(case_id: str) -> dict:
    return validator._case_registry_from_fixture(_fixture(), _case(case_id))


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_production_registry_validates_and_report_is_deterministic(capsys):
    first = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        production_registry_path=validator.DEFAULT_PRODUCTION_REGISTRY,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )
    second = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        production_registry_path=validator.DEFAULT_PRODUCTION_REGISTRY,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )
    report_text = validator.DEFAULT_REPORT.read_text(encoding="utf-8")

    assert first.failures == second.failures == ()
    assert first.report == second.report == json.loads(report_text)
    assert report_text == json.dumps(json.loads(report_text), indent=2, sort_keys=True) + "\n"
    assert json.loads(report_text)["validation_marker"] == validator.SUCCESS_MARKER
    assert "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY_OK" in report_text
    assert validator.main([]) == 0
    assert capsys.readouterr().out.strip() == validator.SUCCESS_MARKER


def test_pr78_pr77_pr73_pr74_pr75_and_pr76_dependencies_are_valid():
    trade_schema, trade_packet, pr78_failures = validator.validate_pr78_dependency(ROOT)
    edge_schema, edge_packet, pr77_failures = validator.validate_pr77_dependency(ROOT)

    assert not validator.validate_pr73_dependency(ROOT)
    assert not validator.validate_pr74_dependency(ROOT)
    assert not validator.validate_pr75_dependency(ROOT)
    assert not pr77_failures
    assert not pr78_failures
    assert not validator.validate_repair_pr76_dependency(ROOT)
    assert trade_schema["properties"]["registry_id" if "registry_id" in trade_schema["properties"] else "packet_id"]
    assert trade_packet["depends_on_edge_parameter_stack_selection_packet"]["validation_marker"] == (
        "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_OK"
    )
    assert edge_schema["properties"]["packet_id"]["const"] == "EDGE_PARAMETER_STACK_SELECTION_PACKET"
    assert edge_packet["required_stack_role_family_fields"] == validator.ROLE_FAMILY_FIELD_BY_ROLE


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


def test_required_universe_ids_exist_are_unique_and_named_universes_present():
    production = _production()
    report = _report()
    universes = validator._universe_by_id(production)

    assert production["required_selection_universe_ids"] == list(
        validator.REQUIRED_SELECTION_UNIVERSE_IDS
    )
    assert not validator.validate_required_universes(production)
    assert not validator.validate_universe_uniqueness(production)
    assert set(universes) == set(validator.REQUIRED_SELECTION_UNIVERSE_IDS)
    assert "KALSHI_BINARY_SHORT_HORIZON" in universes
    assert "POLYMARKET_EVENT_MARKET_MOMENTUM" in universes
    assert "FORECASTEX_IBKR_EVENT_RISK_HEDGE" in universes
    assert "QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION" in universes
    assert report["required_universe_ids_present"] is True
    assert report["universe_ids_unique"] is True


def test_static_registry_policies_do_not_route_select_score_rank_or_execute():
    production = _production()
    static = production["registry_static_policy"]
    membership = production["universe_membership_policy"]
    readiness = production["production_readiness"]
    report = _report()

    assert static["selection_universe_registry_is_static_only"] is True
    assert static["universe_definitions_are_static"] is True
    assert static["universe_membership_filters_are_deterministic"] is True
    assert static["random_universe_selection_allowed"] is False
    assert static["dynamic_membership_evaluation_created"] is False
    assert static["member_row_ids_created"] is False
    assert membership["membership_defined_by_static_filters_only"] is True
    assert membership["membership_evaluated_against_live_data"] is False
    assert membership["membership_evaluated_against_atomicrows_bundle"] is False
    assert membership["membership_uses_random_sampling"] is False
    assert static["trade_context_to_selection_universe_routing_created"] is False
    assert static["route_result_created"] is False
    assert static["selection_universe_consumer_gate_created"] is False
    assert static["selected_stack_created"] is False
    assert static["stack_selection_created"] is False
    assert static["scoring_created"] is False
    assert static["ranking_created"] is False
    assert static["optimizer_arbitration_created"] is False
    assert static["candidate_stack_generation_created"] is False
    assert static["replay_paper_execution_created"] is False
    assert static["runtime_live_order_authority_created"] is False
    assert readiness == validator.PRODUCTION_READINESS_EXPECTED
    assert report["atomicrows_parameter_selection_universe_registry_ready"] is True
    assert report["production_selection_universe_registry_evaluated"] is False


def test_trade_context_edge_packet_and_stack_role_alignment():
    production = _production()
    trade_schema, trade_packet, pr78_failures = validator.validate_pr78_dependency(ROOT)
    _edge_schema, edge_packet, pr77_failures = validator.validate_pr77_dependency(ROOT)

    assert not pr78_failures
    assert not pr77_failures
    assert not validator.validate_trade_context_alignment(
        production,
        trade_schema,
        trade_packet,
    )
    assert not validator.validate_edge_packet_alignment(production, edge_packet)
    assert not validator.validate_stack_role_alignment(production)
    for universe in production["universe_definitions"]:
        assert universe["required_stack_roles"] == list(validator.REQUIRED_STACK_ROLES)
        assert universe["required_role_family_fields"] == validator.ROLE_FAMILY_FIELD_BY_ROLE
        assert universe["deterministic_filter_keys"] == list(
            validator.TRADE_CONTEXT_FILTER_FIELDS
        )
        assert universe["trade_context_field_filters"] == universe["static_membership_filters"]


def test_required_universe_characteristics_and_quantum_forward_static_metadata():
    production = _production()
    universes = validator._universe_by_id(production)
    quantum = production["quantum_universe_policy"]
    quantum_universe = universes["QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION"]

    assert not validator.validate_required_universe_characteristics(production)
    assert "KALSHI" in universes["KALSHI_BINARY_SHORT_HORIZON"]["platform_scope"]
    assert "POLYMARKET" in universes["POLYMARKET_EVENT_MARKET_MOMENTUM"]["platform_scope"]
    assert "FORECASTEX_IBKR" in universes["FORECASTEX_IBKR_EVENT_RISK_HEDGE"]["platform_scope"]
    assert "QUANTUM_ADVISORY" in quantum_universe["required_stack_roles"]
    assert quantum_universe["quantum_applicability_mode"] in validator.QUANTUM_PORTFOLIO_ALLOWED_MODES
    assert "OWNER_QUANTUM_PRIORITY_POLICY_PENDING_PR83" in quantum_universe[
        "quantum_priority_mode_compatibility"
    ]
    assert quantum["quantum_optimized_portfolio_selection_universe_required"] is True
    assert quantum["quantum_universe_static_metadata_only"] is True
    assert quantum["quantum_applicability_mode_static_metadata_only"] is True
    assert quantum["quantum_priority_mode_compatibility_static_metadata_only"] is True
    assert quantum["future_quantum_applicability_registry_required_before_quantum_selection"] is True
    assert quantum["future_owner_quantum_priority_policy_required_before_quantum_priority_selection"] is True
    assert quantum["future_optimizer_arbitration_gate_required_before_optimizer_choice"] is True
    assert quantum["strongest_classical_comparator_required_before_quantum_advantage_claim"] is True
    assert quantum["fallback_bundle_required_before_quantum_runtime_use"] is True
    assert quantum["replay_paper_evidence_required_before_advantage_claim"] is True
    assert quantum["live_evidence_required_before_profit_claim"] is True
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False


def test_source_connector_runtime_live_order_profit_and_owner_override_boundaries():
    production = _production()
    owner = production["owner_override_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    flags = production["explicit_no_claim_flags"]

    assert owner["owner_override_satisfies_internal_selection_universe_registry_readiness_only"] is True
    assert owner["owner_override_fabricates_external_fact"] is False
    assert owner["owner_override_fabricates_accepted_source_packet"] is False
    assert owner["owner_override_fabricates_connector_semantic"] is False
    assert owner["owner_override_fabricates_runtime_cash_receipt"] is False
    assert owner["owner_override_fabricates_order_receipt"] is False
    assert owner["owner_override_fabricates_replay_paper_result"] is False
    assert owner["owner_override_fabricates_quantum_backend_execution"] is False
    assert owner["owner_override_fabricates_profit_evidence"] is False
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


def test_forbidden_output_fields_and_no_claim_flags_absent_from_valid_registry():
    production = _production()
    fixture_registry = _fixture_registry()

    assert not validator.validate_forbidden_output_fields(production, "production")
    assert not validator.validate_forbidden_output_fields(fixture_registry, "fixture")
    assert all(
        production["explicit_no_claim_flags"][field] is False
        for field in validator.EXPLICIT_NO_CLAIM_FALSE_FIELDS
    )
    for field in validator.FORBIDDEN_OUTPUT_FIELDS:
        assert field not in production
        assert field not in fixture_registry
        assert field not in _schema()["properties"]


def test_fixture_negative_cases_fail_closed_with_required_blockers():
    fixture = _fixture()

    assert not validator.validate_fixture_cases(fixture, _schema())
    _assert_failure_contains(
        validator.validate_required_universes(
            _case_registry("SELECTION_UNIVERSE_BLOCKED_MISSING_KALSHI_BINARY_SHORT_HORIZON")
        ),
        "KALSHI_BINARY_SHORT_HORIZON",
    )
    _assert_failure_contains(
        validator.validate_required_universes(
            _case_registry("SELECTION_UNIVERSE_BLOCKED_MISSING_POLYMARKET_EVENT_MARKET_MOMENTUM")
        ),
        "POLYMARKET_EVENT_MARKET_MOMENTUM",
    )
    _assert_failure_contains(
        validator.validate_required_universes(
            _case_registry("SELECTION_UNIVERSE_BLOCKED_MISSING_FORECASTEX_IBKR_EVENT_RISK_HEDGE")
        ),
        "FORECASTEX_IBKR_EVENT_RISK_HEDGE",
    )
    _assert_failure_contains(
        validator.validate_required_universes(
            _case_registry("SELECTION_UNIVERSE_BLOCKED_MISSING_QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION")
        ),
        "QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION",
    )
    _assert_failure_contains(
        validator.validate_universe_uniqueness(
            _case_registry("SELECTION_UNIVERSE_BLOCKED_DUPLICATE_UNIVERSE_ID")
        ),
        "duplicate universe_id",
    )


def test_in_memory_negative_fixtures_block_random_dynamic_member_route_stack_score_and_boundaries():
    production = _production()

    mutated = copy.deepcopy(production)
    mutated["registry_static_policy"]["random_universe_selection_allowed"] = True
    _assert_failure_contains(
        validator.validate_universe_static_policies(mutated),
        "random_universe_selection_allowed",
    )

    mutated = copy.deepcopy(production)
    mutated["registry_static_policy"]["dynamic_membership_evaluation_created"] = True
    _assert_failure_contains(
        validator.validate_universe_static_policies(mutated),
        "dynamic_membership_evaluation_created",
    )

    mutated = copy.deepcopy(production)
    mutated["registry_static_policy"]["member_row_ids_created"] = True
    _assert_failure_contains(
        validator.validate_universe_static_policies(mutated),
        "member_row_ids_created",
    )

    mutated = copy.deepcopy(production)
    mutated["routed_universe_ids"] = ["SYNTHETIC_FORBIDDEN"]
    _assert_failure_contains(
        validator.validate_forbidden_output_fields(mutated),
        "routed_universe_ids",
    )

    mutated = copy.deepcopy(production)
    mutated["selected_stack_id"] = "SYNTHETIC_FORBIDDEN"
    _assert_failure_contains(
        validator.validate_forbidden_output_fields(mutated),
        "selected_stack_id",
    )

    mutated = copy.deepcopy(production)
    mutated["score_breakdown"] = {"SYNTHETIC": "FORBIDDEN"}
    _assert_failure_contains(
        validator.validate_forbidden_output_fields(mutated),
        "score_breakdown",
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
    mutated["quantum_universe_policy"]["quantum_backend_execution_created"] = True
    _assert_failure_contains(
        validator.validate_quantum_universe_boundary(mutated),
        "quantum_backend_execution_created",
    )

    mutated = copy.deepcopy(production)
    mutated["quantum_universe_policy"]["quantum_advantage_claim_created"] = True
    _assert_failure_contains(
        validator.validate_quantum_universe_boundary(mutated),
        "quantum_advantage_claim_created",
    )


def test_forbidden_artifacts_master_plan_and_repair_pr76_state():
    completed = validator.subprocess.run(
        ["git", "diff", "--quiet", "--", str(validator.MASTER_PLAN_CURRENT)],
        stdout=validator.subprocess.PIPE,
        stderr=validator.subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 0
    assert validator.validate_master_plan_not_modified(ROOT) == []
    assert not (ROOT / validator.CANONICAL_BUNDLE_JSONL).exists()
    assert not (ROOT / validator.CANONICAL_BUNDLE_SHA256).exists()
    assert (ROOT / validator.PR76_SHORT_TEST).exists()
    assert not (ROOT / validator.PR76_OLD_LONG_TEST).exists()
    report = _report()
    assert report["atomicrows_bundle_jsonl_exists"] is False
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert report["repair_pr76_long_path_fix_present"] is True
