from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.qtt.pretrade import pr169_pretrade1_resolvers as resolvers
from tools import validate_pr169_pretrade1 as validator
from tools import validation_inventory


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "docs/master_plan/generated/pr169_pretrade1"
REGISTRY_REF = "docs/master_plan/generated/pr169_pretrade1/pretrade_decision_registry.jsonl"
PROJECTION_VERSION = "PR169-PRETRADE1-v2.8S2"


def _jsonl(name: str) -> list[dict]:
    with (ARTIFACT_DIR / name).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _json(name: str) -> dict:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def _candidate_ids() -> set[str]:
    return {row["candidate_id"] for row in _jsonl("pretrade_decision_registry.jsonl")}


def _assert_false_authority(rows: list[dict], *fields: str) -> None:
    for row in rows:
        for field in fields:
            if field in row:
                assert row[field] is False, f"{field} widened in {row.get('candidate_id')}"


def test_pr169_pretrade1_registry_contracts_parametrized():
    registry = _jsonl("pretrade_decision_registry.jsonl")
    manifest = _json("pretrade_manifest.json")
    assert registry
    assert {row["generated_from"] for row in registry} == {REGISTRY_REF}
    assert {row["authoritative_source"] for row in registry} == {REGISTRY_REF}
    assert {row["projection_version"] for row in registry} == {PROJECTION_VERSION}
    assert all(row["manual_edit_allowed"] is False for row in registry)
    assert all(row["orphan_status"] == "NOT_ORPHANED_ROUTE_PROOF_PRESENT" for row in registry)
    assert manifest["canonical_registry_ref"] == REGISTRY_REF
    assert manifest["generated_prefix"] == "docs/master_plan/generated/pr169_pretrade1"
    assert all("_hint" not in artifact["artifact_ref"] for artifact in manifest["generated_artifacts"])
    assert all("future" not in artifact["artifact_ref"].lower() for artifact in manifest["generated_artifacts"])

    view = resolvers.load_registry(repo_root=REPO_ROOT)
    assert set(view.candidate_ids()) == _candidate_ids()
    assert view.provider_pending_packets()
    assert "PR169-PAPER-LOOP::provider_pending" in view.downstream_consumers()


def test_pr169_pretrade1_readiness1_input_consumption_parametrized():
    rows = _jsonl("readiness1_input_map.generated.jsonl")
    registry = _jsonl("pretrade_decision_registry.jsonl")
    assert {row["candidate_id"] for row in rows} == _candidate_ids()
    assert all("pr169_readiness1" in row["readiness1_registry_row_ref"] for row in rows)
    assert all(row["readiness1_recomputed"] is False for row in rows)
    assert all(row["readiness1_modified"] is False for row in rows)
    assert all("pr168_mem1" in row["mem1_memory_ref_or_gap"] for row in registry)
    _assert_false_authority(registry, "mem1_redone", "parallel_memory_registry_created", "memory_update_receipt_created")


def test_pr169_pretrade1_decision_packet_contracts_parametrized():
    required = _candidate_ids()
    candidate_rows = _jsonl("pretrade_decision_candidates.generated.jsonl")
    assert {row["candidate_id"] for row in candidate_rows} == required
    for row in candidate_rows:
        assert row["pretrade_decision_state"] in validator.ALLOWED_DECISION_STATES
        for field in (
            "trade_plan_candidate_ref",
            "readiness1_registry_row_ref",
            "qku_refs",
            "formula_refs",
            "no_trade_candidate_ref",
            "order_policy_candidate_set_ref",
            "scenario_ladder_decision_ref",
            "venue_reality_model_ref",
            "fee_model_ref",
            "fill_model_ref",
            "slippage_model_ref",
            "pretrade_objective_kernel_ref_or_gap",
            "contract_payoff_model_ref_or_gap",
            "market_state_quality_gate_ref_or_gap",
            "probability_calibration_gate_ref_or_gap",
            "pretrade_model_validity_horizon_ref_or_gap",
            "tca_decomposition_ref",
        ):
            assert row.get(field), field

    for name in (
        "trade_plan_bindings.generated.jsonl",
        "no_trade_candidates.generated.jsonl",
        "order_policy_candidate_sets.generated.jsonl",
        "scenario_ladder_decisions.generated.jsonl",
        "latency_budget_decisions.generated.jsonl",
        "mode_authority_matrix.generated.jsonl",
    ):
        assert {row["candidate_id"] for row in _jsonl(name)} >= required

    mode = _jsonl("mode_authority_matrix.generated.jsonl")
    _assert_false_authority(mode, "connector_read_allowed", "venue_submit_allowed", "runtime_execution_allowed", "execution_router_release_allowed")


@pytest.mark.parametrize(
    ("filename", "id_field"),
    sorted(validator.EXACT_MODEL_ID_FIELDS.items()),
)
def test_pr169_pretrade1_reality_models_parametrized(filename: str, id_field: str):
    rows = _jsonl(filename)
    assert {row["candidate_id"] for row in rows} == _candidate_ids()
    assert all(row[id_field] for row in rows)
    assert all(row["source_authority_state"] == "CANDIDATE_RESEARCH_PROVISIONAL_NOT_SOURCE_TRUTH" for row in rows)
    _assert_false_authority(rows, "source_truth_created", "connector_read_created", "live_order_authority_created")

    contracts = _jsonl("reality_model_component_contracts.generated.jsonl")
    by_candidate = {candidate_id: set() for candidate_id in _candidate_ids()}
    for row in contracts:
        by_candidate[row["candidate_id"]].add(row["component_family"])
        assert row["missing_value_policy"] == "NO_OPTIMISTIC_DEFAULT_SCOPED_GAP"
    assert all(validator.COMPONENT_FAMILIES <= families for families in by_candidate.values())


def test_pr169_pretrade1_tca_no_trade_champion_challenger_parametrized():
    tca = _jsonl("tca_decomposition.generated.jsonl")
    no_trade = _jsonl("no_trade_candidates.generated.jsonl")
    scorecard = _jsonl("pretrade_scorecard.generated.jsonl")
    edge = _jsonl("pretrade_edge_alpha_capture_map.generated.jsonl")
    objective = _jsonl("pretrade_objective_kernels.generated.jsonl")
    assert tca and no_trade and scorecard and edge and objective
    for row in tca:
        assert row["tca_state"] == "DECOMPOSED_COMPONENT_ROUTES_PRESENT"
        assert row["explicit_fee_component_ref_or_gap"]
        assert row["adverse_selection_component_ref_or_gap"]
        assert row["settlement_cashflow_component_ref_or_gap"]
    assert all(row["no_trade_is_terminal"] is False for row in no_trade)
    assert all(0 <= row["pretrade_readiness_score_0_1"] <= 1 for row in scorecard)
    _assert_false_authority(tca + no_trade + edge + objective, "profit_claim_created", "order_authority_created")


def test_pr169_pretrade1_agent_llm_owner_routes_parametrized():
    agent = _jsonl("pretrade_agent_packet_map.generated.jsonl")
    llm = _jsonl("pretrade_llm_grounding_view.generated.jsonl")
    owner = _jsonl("pretrade_owner_view_handoff.generated.jsonl")
    intent = _jsonl("pretrade_owner_intent_bindings.generated.jsonl")
    next_steps = _jsonl("pretrade_owner_next_step_handoff.generated.jsonl")
    guidance = _jsonl("pretrade_owner_guidance_handoff.generated.jsonl")
    trace = _jsonl("pretrade_decision_traces.generated.jsonl")
    workflow = _jsonl("agent_workflow_obs_handoff.generated.jsonl")
    assert all(rows for rows in (agent, llm, owner, intent, next_steps, guidance, trace, workflow))
    assert all(row["agent_roster_discovery_audit_ref_or_gap"] for row in agent)
    assert all("direct_trade_submission" in row["forbidden_llm_roles"] for row in llm)
    assert all(row["dashboard_surface_registry_ref_or_gap"] for row in owner)
    assert all(row["central_owner_ux_semantic_bundle_ref_or_gap"] for row in owner)
    assert all(row["owner_intent_examples"] for row in intent)
    assert all(row["expected_receipt_classes"] for row in workflow)
    _assert_false_authority(agent + llm + owner + intent + workflow, "runtime_llm_call_created", "runtime_dashboard_service_created", "agent_execution_created", "fake_agent_status_created", "fake_queue_item_created", "fake_timestamp_created")


def test_pr169_pretrade1_microstructure_risk_threshold_trace_parametrized():
    micro = _jsonl("microstructure_state_models.generated.jsonl")
    risk = _jsonl("pretrade_risk_envelopes.generated.jsonl")
    threshold = _jsonl("pretrade_threshold_policy.generated.jsonl")
    trace = _jsonl("pretrade_decision_traces.generated.jsonl")
    assert all(rows for rows in (micro, risk, threshold, trace))
    assert all(row["quote_freshness_state"] for row in micro)
    assert all(row["risk_envelope_state"].startswith(("MATERIALIZED", "SCOPED_GAP")) for row in risk)
    assert all(row["threshold_policy_state"].startswith("MATERIALIZED") for row in threshold)
    assert all(row["decision_state"] in validator.ALLOWED_DECISION_STATES for row in trace)


def test_pr169_pretrade1_memory_recovery_venue_attribution_parametrized():
    memory = _jsonl("pretrade_memory_prior_reval.generated.jsonl")
    recovery = _jsonl("pretrade_recovery_frontiers.generated.jsonl")
    venues = _jsonl("pretrade_venue_policy_matrix.generated.jsonl")
    attribution = _jsonl("pretrade_edge_attribution.generated.jsonl")
    assert all(row["current_snapshot_revalidation_required"] is True for row in memory)
    _assert_false_authority(memory, "memory_prior_used_as_proof", "mem1_redone", "parallel_memory_registry_created", "memory_update_receipt_created")
    assert all(row["terminal_dead_end_created"] is False for row in recovery)
    assert {"KALSHI", "POLYMARKET", "FORECASTEX_IBKR"} <= {row["venue_scope"] for row in venues}
    assert all(row["cross_venue_generalization_allowed"] is False for row in venues)
    _assert_false_authority(attribution, "realized_pnl_created", "profit_claim_created", "paper_receipt_created", "live_receipt_created")


def test_pr169_pretrade1_connector_execution_hotpath_quantum_routes_parametrized():
    connector = _jsonl("pretrade_connector_handoff.generated.jsonl")
    execution = _jsonl("pretrade_execution_router_handoff.generated.jsonl")
    hotpath = _jsonl("pretrade_hotpath_handoff.generated.jsonl")
    quantum = _jsonl("pretrade_quantum_readiness_handoff.generated.jsonl")
    gate = _jsonl("pretrade_gate_snapshot_handoff.generated.jsonl")
    dag = _jsonl("pretrade_agent_dag_handoff.generated.jsonl")
    ladder = _jsonl("pretrade_exec_ladder_handoff.generated.jsonl")
    assert all(rows for rows in (connector, execution, hotpath, quantum, gate, dag, ladder))
    assert all(row["connector_route_state"] == "PROVIDER_PENDING_NO_CONNECTOR_READ" for row in connector)
    assert all(row["execution_router_release_state"] == "PROVIDER_PENDING_DOWNSTREAM" for row in execution)
    assert all(row["precompute_requirement_state"] == "PRECOMPUTED_SNAPSHOT_REQUIRED" for row in hotpath)
    assert all(row["q_classical_comparator_ref_or_gap"] for row in quantum)
    _assert_false_authority(connector + execution + hotpath + quantum + gate + ladder, "connector_read_created", "connector_write_created", "order_authority_created", "venue_submit_created", "execution_router_release_created", "quantum_backend_execution_created", "live_execution_created")


def test_pr169_pretrade1_source_coverage_external_lanes_calibration_parametrized():
    source = _jsonl("source_coverage_handoff.generated.jsonl")
    external = _jsonl("candidate_external_info_lanes.generated.jsonl")
    diff = _jsonl("paper_vs_replay_reality_diff.generated.jsonl")
    calibration = _jsonl("reality_model_calibration_receipts.generated.jsonl")
    assert all(rows for rows in (source, external, diff, calibration))
    assert all(row["source_authority_state"] == "CANDIDATE_RESEARCH_PROVISIONAL_NOT_ACCEPTED_SOURCE_TRUTH" for row in source)
    assert all(row["candidate_external_info_lane_ref_or_gap"] for row in source)
    assert all(row["lane_state"] == "CANDIDATE_RESEARCH_PROVISIONAL" for row in external)
    assert all(row["calibration_state"] == "EXISTING_EVIDENCE_ONLY_NO_MODEL_TRAINING" for row in calibration)
    _assert_false_authority(source + external + diff + calibration, "accepted_source_truth_created", "source_truth_created", "paper_execution_created", "replay_execution_created")


def test_pr169_pretrade1_currentization_and_validation_workflow():
    validator.validate(REPO_ROOT, ARTIFACT_DIR)
    matched = validation_inventory.entries_matching_path("docs/master_plan/generated/pr169_pretrade1/pretrade_manifest.json")
    assert matched
    assert any(entry.owner_pr_or_feature == "PR169_PRETRADE1" for entry in matched)
    matched_resolver = validation_inventory.entries_matching_path("src/qtt/pretrade/pr169_pretrade1_resolvers.py")
    assert matched_resolver


def test_pr169_pretrade1_quality_gates_report():
    quality = _json("pretrade_quality_gates.report.json")
    no_submit = _json("no_submit_authority.report.json")
    market = _json("market_installation_acceptance.report.json")
    assert quality["acceptance_state"] == "PASS"
    assert quality["readiness1_consumption_state"].startswith("PASS")
    assert quality["authority_boundary_state"].startswith("PASS")
    assert quality["memory_prior_used_as_proof"] is False
    assert quality["parallel_memory_registry_created"] is False
    assert quality["cross_venue_generalization_allowed"] is False
    assert quality["realized_pnl_created"] is False
    assert no_submit["acceptance_state"] == "PASS"
    assert no_submit["submit_authority_created_count"] == 0
    assert no_submit["runtime_receipt_created_count"] == 0
    assert no_submit["profit_claim_created_count"] == 0
    assert market["acceptance_state"] == "PASS"
    assert market["runtime_connector_created"] is False
    assert market["orphan_market_route_count"] == 0
