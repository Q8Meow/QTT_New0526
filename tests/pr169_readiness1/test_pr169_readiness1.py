from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.qtt.readiness import pr169_readiness1_resolvers as resolvers
from tools import validate_pr169_readiness1 as validator


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "docs/master_plan/generated/pr169_readiness1"
REGISTRY_REF = "docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl"


def _jsonl(name: str) -> list[dict]:
    with (ARTIFACT_DIR / name).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _json(name: str) -> dict:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def test_pr169_readiness1_registry_contracts_parametrized():
    registry = _jsonl("agent_readiness_registry.jsonl")
    assert registry
    assert {row["generated_from"] for row in registry} == {REGISTRY_REF}
    assert {row["authoritative_source"] for row in registry} == {REGISTRY_REF}
    assert all(row["manual_edit_allowed"] is False for row in registry)
    assert all(row["stage_access_mode"] == "CENTRAL_RESOLVER_PROJECTION_ONLY" for row in registry)
    assert all("\\" not in row["trade_plan_candidate_ref"] for row in registry)
    assert all(row["effective_live_write_state"] == "NOT_ARMED_IN_READINESS1" for row in registry)

    manifest = _json("readiness_manifest.json")
    assert manifest["canonical_registry_ref"] == REGISTRY_REF
    assert manifest["generated_prefix"] == "docs/master_plan/generated/pr169_readiness1"
    assert all("_hint" not in artifact["artifact_ref"] for artifact in manifest["generated_artifacts"])


def test_pr169_readiness1_no_scatter_no_orphan_no_raw_jsonl_parametrized():
    no_orphan = _json("no_orphan.report.json")
    no_raw = _json("no_raw_jsonl_scan.report.json")
    routes = _jsonl("consumer_routes.generated.jsonl")

    assert no_orphan["acceptance_state"] == "PASS"
    assert no_orphan["orphan_count"] == 0
    assert no_raw["result"] == "PASS"
    assert no_raw["blocked_paths"] == []
    assert routes
    assert all(route["live_use_allowed"] is False for route in routes)
    assert all(route["runtime_use_allowed"] is False for route in routes)

    resolver = resolvers.load_registry(repo_root=REPO_ROOT)
    assert resolver.executable_now_candidates()


def test_pr169_readiness1_computability_authority_executable_now_parametrized():
    registry = {row["candidate_id"]: row for row in _jsonl("agent_readiness_registry.jsonl")}
    contracts = {row["candidate_id"]: row for row in _jsonl("computable_contracts.generated.jsonl")}
    executable = _jsonl("executable_now.generated.jsonl")
    fake = _json("no_fake_readiness.report.json")
    materialization = _json("no_placeholder_materialization.report.json")

    assert contracts.keys() == registry.keys()
    assert executable
    for row in executable:
        reg = registry[row["candidate_id"]]
        assert reg["computability_state"] == "COMPUTABLE_EXECUTABLE_NOW"
        assert reg["executable_now_state"] == "EXECUTABLE_NOW_NONLIVE_SAFE"
        assert row["runtime_side_effect_allowed"] is False
        assert row["source_truth_created"] is False
        assert row["order_authority_created"] is False
        assert row["profit_claim_created"] is False

    assert fake["fake_executable_now_count"] == 0
    assert materialization["metadata_only_row_count"] == 0


def test_pr169_readiness1_agent_llm_owner_surface_routes_parametrized():
    compute_map = _jsonl("qku_formula_agent_compute_map.generated.jsonl")
    llm = _jsonl("llm_grounding_view.generated.jsonl")
    plain = _jsonl("owner_plain_english_intent_routes.generated.jsonl")
    chat = _jsonl("owner_chat_action_catalog_routes.generated.jsonl")
    surface = _jsonl("surface_parity_handoff.generated.jsonl")
    ux = _jsonl("owner_ux_semantic_bundle_handoff.generated.jsonl")

    assert compute_map and llm and plain and chat and surface and ux
    assert all(row["agent_execution_created"] is False for row in compute_map)
    assert all(row["runtime_llm_call_created"] is False for row in llm)
    assert all(row["route_state"] == "STRUCTURED_PROVIDER_PENDING_NO_RUNTIME" for row in plain)
    assert all("DIRECT_VENUE_SUBMIT" in row["forbidden_chat_actions"] for row in chat)
    assert all(row["runtime_service_created"] is False for row in surface)
    assert all(row["runtime_ui_service_created"] is False for row in ux)
    assert all(row["robinhood_like_benchmark_state"] == "UX_QUALITY_BENCHMARK_ONLY_NOT_SOURCE_TRUTH" for row in ux)


def test_pr169_readiness1_institutional_quantum_order_shadow_routes_parametrized():
    institutional = _jsonl("institutional_controls.generated.jsonl")
    quantum = _jsonl("quantum_readiness.generated.jsonl")
    trade_vars = _jsonl("trade_variable_search_handoff.generated.jsonl")
    edge = _jsonl("edge_alpha_decision_readiness.generated.jsonl")
    tournament = _jsonl("order_scenario_tournament_handoff.generated.jsonl")
    shadow = _jsonl("shadow_comparison_handoff.generated.jsonl")
    execution = _jsonl("execution_router_action_handoff.generated.jsonl")

    assert institutional and quantum and trade_vars and edge and tournament and shadow and execution
    assert all(row["winner_state"] == "NO_LIVE_WINNER_DECLARED" for row in institutional)
    assert all(row["q_backend_execution_allowed"] is False for row in quantum)
    assert all(row["immutable_formula_state"] == "IMMUTABLE" for row in trade_vars)
    assert all(row["formula_mutation_created"] is False for row in trade_vars)
    assert all(row["promotion_claim_created"] is False for row in edge)
    assert all(row["simulation_executed_in_this_pr"] is False for row in tournament)
    assert all(row["shadow_required_before_canary"] is False for row in shadow)
    assert all(row["execution_router_release_created"] is False for row in execution)
    assert {"BUY", "SELL", "OPEN", "CLOSE", "CANCEL", "REPLACE", "REDUCE", "EXIT"} <= set(execution[0]["allowed_downstream_action_verbs"])


def test_pr169_readiness1_connector_metrics_plugin_learning_source_routes_parametrized():
    connector = _jsonl("connector_route_handoff.generated.jsonl")
    metrics = _jsonl("metrics_route_alias.generated.jsonl")
    plugin = _jsonl("plugin_intake_handoff.generated.jsonl")
    accountability = _jsonl("agent_kpi_trust_quarantine_handoff.generated.jsonl")
    learning = _jsonl("agent_learning_handoff.generated.jsonl")
    source = _jsonl("source_coverage_handoff.generated.jsonl")
    external = _jsonl("candidate_external_info_lanes.generated.jsonl")

    assert connector and metrics and plugin and accountability and learning and source and external
    assert all(row["connector_read_created"] is False for row in connector)
    assert all(row["runtime_metrics_ledger_created"] is False for row in metrics)
    assert all(row["runtime_plugin_created"] is False for row in plugin)
    assert all(row["agent_accountability_materialization_state"] == "MATERIALIZED_CONTRACT" for row in accountability)
    assert all(row["model_training_created"] is False for row in learning)
    assert all(row["accepted_source_truth_created"] is False for row in source)
    assert all(row["candidate_lane_state"] == "CANDIDATE_RESEARCH_PROVISIONAL" for row in external)


def test_pr169_readiness1_currentization_and_validation_workflow():
    validator.validate(REPO_ROOT, ARTIFACT_DIR)


def test_pr169_readiness1_owner_three_question_report():
    report = _json("owner_three_question_coverage.report.json")
    assert report["report_type"] == "OWNER_THREE_QUESTION_COVERAGE_REPORT"
    assert report["acceptance_state"] == "PASS"
    assert report["q1_edge_alpha_capture_coverage_state"].startswith("PASS")
    assert report["q2_no_orphan_coverage_state"].startswith("PASS")
    assert report["q3_agent_llm_computation_route_state"].startswith("PASS")
    assert report["q3_actual_buy_sell_open_close_created"] is False
    assert report["q3_runtime_agent_execution_created"] is False
    assert report["q3_runtime_llm_call_created"] is False
    assert report["q3_live_execution_created"] is False
    assert report["q3_execution_router_release_created"] is False
