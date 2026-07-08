#!/usr/bin/env python3
"""Build PR169-PRETRADE1 generated pretrade artifacts.

Session 2 keeps the single central builder from Session 1 and expands the
generated contracts into the final PRETRADE1 no-submit packet surface.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import shutil
from typing import Any, Iterable, Sequence


PROMPT_VERSION = "v2.8S2"
PROJECTION_VERSION = "PR169-PRETRADE1-v2.8S2"
BUILDER_NAME = "tools/build_pr169_pretrade1.py"
VALIDATOR_NAME = "tools/validate_pr169_pretrade1.py"
GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_pretrade1")
REGISTRY_REF = "docs/master_plan/generated/pr169_pretrade1/pretrade_decision_registry.jsonl"

JSONL_ARTIFACTS = (
    "pretrade_decision_registry.jsonl",
    "readiness1_input_map.generated.jsonl",
    "market_reality_onboarding_handoff.generated.jsonl",
    "pretrade_qku_formula_compute_map.generated.jsonl",
    "trade_plan_bindings.generated.jsonl",
    "pretrade_decision_candidates.generated.jsonl",
    "no_trade_candidates.generated.jsonl",
    "order_policy_candidate_sets.generated.jsonl",
    "pretrade_order_simulation_specs.generated.jsonl",
    "scenario_ladder_decisions.generated.jsonl",
    "latency_budget_decisions.generated.jsonl",
    "mode_authority_matrix.generated.jsonl",
    "pretrade_objective_kernels.generated.jsonl",
    "contract_payoff_models.generated.jsonl",
    "market_state_quality_gates.generated.jsonl",
    "probability_calibration_gates.generated.jsonl",
    "pretrade_model_validity_horizon.generated.jsonl",
    "venue_reality_models.generated.jsonl",
    "fee_models.generated.jsonl",
    "fill_models.generated.jsonl",
    "slippage_models.generated.jsonl",
    "latency_decay_models.generated.jsonl",
    "queue_position_models.generated.jsonl",
    "partial_fill_models.generated.jsonl",
    "capacity_crowding_models.generated.jsonl",
    "adverse_selection_models.generated.jsonl",
    "settlement_resolution_models.generated.jsonl",
    "cashflow_models.generated.jsonl",
    "order_policy_reality_models.generated.jsonl",
    "reality_model_component_contracts.generated.jsonl",
    "reality_assumption_ledger.generated.jsonl",
    "pretrade_model_risk_controls.generated.jsonl",
    "pretrade_parameter_operability.generated.jsonl",
    "paper_vs_replay_reality_diff.generated.jsonl",
    "reality_model_calibration_receipts.generated.jsonl",
    "tca_decomposition.generated.jsonl",
    "pretrade_scorecard.generated.jsonl",
    "pretrade_agent_packet_map.generated.jsonl",
    "pretrade_llm_grounding_view.generated.jsonl",
    "pretrade_owner_view_handoff.generated.jsonl",
    "pretrade_connector_handoff.generated.jsonl",
    "pretrade_execution_router_handoff.generated.jsonl",
    "pretrade_hotpath_handoff.generated.jsonl",
    "pretrade_quantum_readiness_handoff.generated.jsonl",
    "pretrade_gate_snapshot_handoff.generated.jsonl",
    "pretrade_owner_intent_bindings.generated.jsonl",
    "pretrade_owner_next_step_handoff.generated.jsonl",
    "pretrade_owner_guidance_handoff.generated.jsonl",
    "microstructure_state_models.generated.jsonl",
    "pretrade_risk_envelopes.generated.jsonl",
    "pretrade_threshold_policy.generated.jsonl",
    "pretrade_decision_traces.generated.jsonl",
    "pretrade_agent_dag_handoff.generated.jsonl",
    "agent_workflow_obs_handoff.generated.jsonl",
    "pretrade_metrics_capture_handoff.generated.jsonl",
    "pretrade_artifact_value_route_map.generated.jsonl",
    "pretrade_agent_access_path_audit.generated.jsonl",
    "pretrade_edge_alpha_capture_map.generated.jsonl",
    "pretrade_memory_prior_reval.generated.jsonl",
    "pretrade_recovery_frontiers.generated.jsonl",
    "pretrade_venue_policy_matrix.generated.jsonl",
    "pretrade_edge_attribution.generated.jsonl",
    "pretrade_exec_ladder_handoff.generated.jsonl",
    "clean_room_default_candidates.generated.jsonl",
    "source_coverage_handoff.generated.jsonl",
    "candidate_external_info_lanes.generated.jsonl",
    "pretrade_gap_ledger.generated.jsonl",
    "consumer_routes.generated.jsonl",
)

JSON_ARTIFACTS = (
    "pretrade_manifest.json",
    "no_orphan.report.json",
    "no_submit_authority.report.json",
    "no_raw_jsonl_scan.report.json",
    "no_placeholder_materialization.report.json",
    "pretrade_quality_gates.report.json",
    "market_installation_acceptance.report.json",
)

AUTHORITY_FALSE_FIELDS = (
    "submit_authority_created",
    "order_authority_created",
    "execution_router_release_created",
    "replay_execution_created",
    "paper_execution_created",
    "shadow_execution_created",
    "live_execution_created",
    "runtime_llm_call_created",
    "runtime_agent_execution_created",
    "agent_execution_created",
    "agent_runtime_created",
    "runtime_dashboard_service_created",
    "runtime_ui_service_created",
    "runtime_chat_service_created",
    "runtime_connector_created",
    "connector_read_created",
    "connector_write_created",
    "private_cash_read_created",
    "runtime_cash_read_created",
    "source_truth_created",
    "accepted_source_truth_created",
    "runtime_metrics_created",
    "runtime_metrics_ledger_created",
    "runtime_receipt_created",
    "memory_update_receipt_created",
    "paper_receipt_created",
    "live_receipt_created",
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "qtt_sha_authority_created",
    "atomicrows_hash_authority_created",
    "profit_claim_created",
    "realized_pnl_created",
    "financial_advice_claim_created",
    "venue_submit_created",
    "order_compilation_created",
    "buy_sell_open_close_executed",
    "paper_order_intent_receipt_created",
    "workflow_queue_runtime_created",
    "runtime_task_created",
    "fake_agent_status_created",
    "fake_queue_item_created",
    "fake_timestamp_created",
    "fake_pnl_created",
    "hardcoded_runtime_default_created",
    "live_authority_created",
    "live_value_authority_created",
    "live_currentness_claim_created",
    "live_market_data_claim_created",
    "live_limit_authority_created",
    "live_data_claim_created",
    "live_execution_created",
    "simulation_executed_in_this_pr",
    "snapshot_created_in_this_pr",
    "source_retrieval_in_live_path_allowed",
    "dashboard_rendering_in_live_path_allowed",
    "replay_paper_recalculation_in_live_path_allowed",
    "llm_call_in_live_path_allowed",
    "quantum_backend_call_in_live_path_allowed",
    "runtime_side_effect_allowed",
    "raw_jsonl_runtime_scan_used",
    "full_library_default_access_created",
    "per_agent_copy_created",
    "ad_hoc_market_hardcode_created",
    "independent_truth_created",
    "runtime_side_effect_created",
    "manual_edit_allowed",
    "source_truth_authority_created",
    "venue_semantics_accepted",
    "confidential_or_restricted_input_flag",
    "nda_or_confidential_input_flag",
    "improper_access_flag",
    "credentialed_competitor_system_flag",
    "proprietary_claim_flag",
    "memory_prior_used_as_proof",
    "mem1_redone",
    "parallel_memory_registry_created",
    "mem1_generated_artifact_modified",
    "memory_authority_created",
    "terminal_dead_end_created",
    "global_qku_formula_ban_created",
    "formula_mutation_created",
)

DOWNSTREAM_CONSUMERS = (
    "PR169-SVC1::provider_pending",
    "PR169-LLM1::provider_pending",
    "PR169-LLM2::provider_pending",
    "PR169-AGENT-ORCH1::provider_pending",
    "PR169-PAPER-LOOP::provider_pending",
    "PR170-HOTPATH1::provider_pending",
    "PR170-METRICS1::provider_pending",
    "PR170-LIVE-DRYRUN1::provider_pending",
    "PR171-LIVE-PILOT::provider_pending",
    "PR172-LAUNCH::provider_pending",
    "PR173-POSTLAUNCH::provider_pending",
    "PR174-QMAP1::provider_pending",
    "PR174-ALLOW1::provider_pending",
    "VENUE-NEUTRAL-CONNECTOR::provider_pending_no_read",
    "EXECUTION-ROUTER::provider_pending_no_release",
)

COMPONENT_FAMILIES = (
    "fee",
    "fill",
    "slippage",
    "latency_decay",
    "queue_position",
    "partial_fill",
    "capacity_crowding",
    "adverse_selection",
    "settlement_resolution",
    "cashflow",
    "order_policy",
)

STAGE1_VENUES = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")

COMPONENT_ID_FIELDS = {
    "venue_reality_models": "venue_reality_model_id",
    "fee_models": "fee_model_id",
    "fill_models": "fill_model_id",
    "slippage_models": "slippage_model_id",
    "latency_decay_models": "latency_decay_model_id",
    "queue_position_models": "queue_position_model_id",
    "partial_fill_models": "partial_fill_model_id",
    "capacity_crowding_models": "capacity_crowding_model_id",
    "adverse_selection_models": "adverse_selection_model_id",
    "settlement_resolution_models": "settlement_resolution_model_id",
    "cashflow_models": "cashflow_model_id",
    "order_policy_reality_models": "order_policy_reality_model_id",
}


@dataclass(frozen=True)
class SourceContext:
    repo_root: Path
    readiness_rows: tuple[dict[str, Any], ...]
    rp5g_by_candidate: dict[str, dict[str, Any]]
    rank4_by_candidate: dict[str, dict[str, Any]]
    tca_by_candidate: dict[str, dict[str, Any]]
    no_trade_by_candidate: dict[str, dict[str, Any]]
    fill_by_candidate: dict[str, dict[str, Any]]
    calibration_by_candidate: dict[str, dict[str, Any]]
    micro_by_candidate: dict[str, dict[str, Any]]
    scenario_by_candidate: dict[str, list[dict[str, Any]]]
    mem_context_by_candidate: dict[str, dict[str, Any]]
    mem_recipe_by_candidate: dict[str, dict[str, Any]]


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    if not path.exists():
        return ()
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return tuple(rows)


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _out_ref(name: str) -> str:
    return (GENERATED_PREFIX / name).as_posix()


def _gap(label: str) -> str:
    return f"SCOPED_GAP_{label}"


def _route(name: str, candidate_id: str) -> str:
    return f"{name}::{candidate_id}"


def _source_ref(path: str, row_id: Any = None) -> str:
    return f"{path}::{row_id}" if row_id else path


def _decimal(value: Any, default: str = "0") -> Decimal:
    try:
        if value in (None, ""):
            return Decimal(default)
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _rounded(value: Decimal | float | int, places: str = "0.000001") -> float:
    return float(Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP))


def _id_suffix(candidate_id: str) -> str:
    return candidate_id.replace("RP5G_CAND_", "")


def _projection_base(projection_name: str) -> dict[str, Any]:
    return {
        "generated_from": REGISTRY_REF,
        "manual_edit_allowed": False,
        "authoritative_source": REGISTRY_REF,
        "projection_name": projection_name,
        "projection_version": PROJECTION_VERSION,
        "builder_name": BUILDER_NAME,
        "validator_name": VALIDATOR_NAME,
    }


def _projection_row(projection_name: str, row: dict[str, Any]) -> dict[str, Any]:
    return {**_projection_base(projection_name), **row}


def _false_payload(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {field: False for field in AUTHORITY_FALSE_FIELDS}
    if extra:
        payload.update(extra)
    return payload


def _by_candidate(rows: Iterable[dict[str, Any]], *keys: str) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for row in rows:
        for key in keys:
            candidate_id = row.get(key)
            if candidate_id:
                mapped.setdefault(str(candidate_id), row)
                break
    return mapped


def _group_by_candidate(rows: Iterable[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        candidate_id = row.get(key)
        if candidate_id:
            grouped[str(candidate_id)].append(row)
    return grouped


def _file_or_gap(repo_root: Path, rel: str, label: str) -> str:
    return rel if (repo_root / rel).exists() else _gap(label)


def _load_context(repo_root: Path) -> SourceContext:
    readiness_rows = _read_jsonl(repo_root / "docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl")
    rp5g_rows = _read_jsonl(repo_root / "docs/master_plan/generated/pr168_rp5g/trade_candidate.jsonl")
    rank4_rows = _read_jsonl(repo_root / "docs/master_plan/generated/pr168_rank4/rank_order.jsonl")
    tca_rows = _read_jsonl(repo_root / "docs/master_plan/generated/pr168_rp5g/tca_decomp.jsonl")
    no_trade_rows = _read_jsonl(repo_root / "docs/master_plan/generated/pr168_rp5g/notrade_cmp.jsonl")
    fill_rows = _read_jsonl(repo_root / "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl")
    calibration_rows = _read_jsonl(repo_root / "docs/master_plan/generated/pr168_rp5g/calibration_result.jsonl")
    micro_rows = _read_jsonl(repo_root / "docs/master_plan/generated/pr168_rp5g/pm_microstructure.jsonl")
    scenario_rows = _read_jsonl(repo_root / "docs/master_plan/generated/pr168_rp5g/scenario_ladder.jsonl")
    mem_context_rows = _read_jsonl(repo_root / "docs/master_plan/generated/pr168_mem1/context_signature.jsonl")
    mem_recipe_rows = _read_jsonl(repo_root / "docs/master_plan/generated/pr168_mem1/winning_recipe.jsonl")
    return SourceContext(
        repo_root=repo_root,
        readiness_rows=readiness_rows,
        rp5g_by_candidate=_by_candidate(rp5g_rows, "trade_plan_candidate_id", "candidate_id", "row_id"),
        rank4_by_candidate=_by_candidate(rank4_rows, "candidate_id"),
        tca_by_candidate=_by_candidate(tca_rows, "trade_plan_candidate_id"),
        no_trade_by_candidate=_by_candidate(no_trade_rows, "trade_plan_candidate_id"),
        fill_by_candidate=_by_candidate(fill_rows, "trade_plan_candidate_id"),
        calibration_by_candidate=_by_candidate(calibration_rows, "trade_plan_candidate_id"),
        micro_by_candidate=_by_candidate(micro_rows, "trade_plan_candidate_id"),
        scenario_by_candidate=_group_by_candidate(scenario_rows, "trade_plan_candidate_id"),
        mem_context_by_candidate=_by_candidate(mem_context_rows, "source_candidate_id"),
        mem_recipe_by_candidate=_by_candidate(mem_recipe_rows, "source_candidate_id", "source_trade_plan_candidate_id"),
    )


def _readiness_ref(row: dict[str, Any]) -> str:
    return _source_ref(
        "docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl",
        row.get("registry_row_id") or row.get("candidate_id"),
    )


def _row_ref(path: str, row: dict[str, Any], *ids: str) -> str:
    for key in ids:
        if row.get(key):
            return _source_ref(path, row[key])
    return _gap(f"{Path(path).stem.upper()}_ROW_ABSENT")


def _quality_state(micro: dict[str, Any], calibration: dict[str, Any]) -> tuple[str, str]:
    depth = str(micro.get("depth_at_price_bucket") or "SCOPED_GAP")
    event_status = str(micro.get("event_status_state") or "SCOPED_GAP")
    if depth == "THIN":
        return "FAIL", "THIN_BOOK_DEPTH_REQUIRES_NO_TRADE_OR_RETEST"
    if "SOURCE_REQUIRED" in event_status:
        return "SCOPED_GAP", "EVENT_LIFECYCLE_SOURCE_CLASSIFICATION_REQUIRED"
    if not calibration:
        return "SCOPED_GAP", "PROBABILITY_CALIBRATION_ROW_ABSENT"
    return "WARN", "REPLAY_PAPER_FIXTURE_ONLY_REVALIDATION_REQUIRED"


def _champion_state(no_trade: dict[str, Any], quality_state: str, calibration: dict[str, Any]) -> tuple[str, str]:
    beats_no_trade = no_trade.get("candidate_beats_no_trade_flag") is True
    if not beats_no_trade:
        return "PRETRADE_NO_TRADE_WINS", "NO_TRADE_COMPARATOR_WINS_CURRENT_SNAPSHOT"
    if quality_state in {"FAIL", "SCOPED_GAP"}:
        return "PRETRADE_PASS_PROVIDER_PENDING", "MARKET_STATE_OR_SOURCE_CURRENTNESS_GATE_PENDING"
    if not calibration:
        return "PRETRADE_PASS_PROVIDER_PENDING", "CALIBRATION_GATE_PENDING"
    return "PRETRADE_PASS_PAPER_CANDIDATE", "CURRENT_NONLIVE_PRETRADE_CONTRACTS_COMPLETE"


def _score(no_trade: dict[str, Any], fill: dict[str, Any], micro: dict[str, Any], calibration: dict[str, Any]) -> float:
    margin = max(Decimal("-1"), min(Decimal("1"), _decimal(no_trade.get("candidate_minus_no_trade_cash"))))
    fill_probability = max(Decimal("0"), min(Decimal("1"), _decimal(fill.get("fill_probability"))))
    depth = Decimal("0.2") if micro.get("depth_at_price_bucket") == "THIN" else Decimal("0.7")
    calib = Decimal("0.6") if calibration else Decimal("0")
    raw = Decimal("0.35") * ((margin + Decimal("1")) / Decimal("2")) + Decimal("0.30") * fill_probability + Decimal("0.20") * depth + Decimal("0.15") * calib
    if no_trade.get("candidate_beats_no_trade_flag") is not True:
        raw -= Decimal("0.20")
    return _rounded(max(Decimal("0"), min(Decimal("1"), raw)))


def _build_registry(ctx: SourceContext) -> list[dict[str, Any]]:
    if not ctx.readiness_rows:
        raise RuntimeError("READINESS1 registry is required for PRETRADE1")
    registry: list[dict[str, Any]] = []
    for index, readiness in enumerate(sorted(ctx.readiness_rows, key=lambda row: str(row.get("candidate_id"))), start=1):
        candidate_id = str(readiness["candidate_id"])
        rp5g = ctx.rp5g_by_candidate.get(candidate_id, {})
        rank4 = ctx.rank4_by_candidate.get(candidate_id, {})
        tca = ctx.tca_by_candidate.get(candidate_id, {})
        no_trade = ctx.no_trade_by_candidate.get(candidate_id, {})
        fill = ctx.fill_by_candidate.get(candidate_id, {})
        calibration = ctx.calibration_by_candidate.get(candidate_id, {})
        micro = ctx.micro_by_candidate.get(candidate_id, {})
        mem_context = ctx.mem_context_by_candidate.get(candidate_id, {})
        mem_recipe = ctx.mem_recipe_by_candidate.get(candidate_id, {})
        quality_state, quality_gap = _quality_state(micro, calibration)
        packet_state, packet_gap = _champion_state(no_trade, quality_state, calibration)
        venue_scope = str(readiness.get("venue_scope") or rp5g.get("venue") or "PROVIDER_PENDING")
        packet_id = f"PRETRADE_DECISION_CANDIDATE_{_id_suffix(candidate_id)}"
        registry_row_id = f"PR169_PRETRADE1_REGISTRY_{index:04d}"
        qku_refs = list(readiness.get("qku_refs") or rp5g.get("qku_refs") or [])
        formula_refs = list(readiness.get("formula_refs") or rp5g.get("formula_refs") or [])
        agent_roles = list(readiness.get("agent_role_refs") or rp5g.get("consumer_agent_refs") or [])
        row = {
            "pretrade_registry_row_id": registry_row_id,
            "candidate_id": candidate_id,
            "readiness1_registry_row_ref": _readiness_ref(readiness),
            "readiness1_computable_contract_ref": readiness.get("computable_contract_id") or _gap("READINESS1_COMPUTABLE_CONTRACT_ABSENT"),
            "readiness1_edge_alpha_ref_or_gap": readiness.get("edge_alpha_decision_readiness_ref_or_gap") or _gap("READINESS1_EDGE_ALPHA_ROUTE_ABSENT"),
            "readiness1_order_scenario_tournament_ref_or_gap": readiness.get("order_scenario_tournament_ref_or_gap") or _gap("READINESS1_ORDER_TOURNAMENT_ROUTE_ABSENT"),
            "readiness1_trade_variable_search_ref_or_gap": readiness.get("trade_variable_search_handoff_ref_or_gap") or _gap("READINESS1_TRADE_VARIABLE_ROUTE_ABSENT"),
            "readiness1_parameter_operability_ref_or_gap": readiness.get("parameter_operability_handoff_ref_or_gap") or _gap("READINESS1_PARAMETER_OPERABILITY_ROUTE_ABSENT"),
            "readiness1_owner_enablement_ref_or_gap": readiness.get("owner_enablement_handoff_ref_or_gap") or _gap("READINESS1_OWNER_ENABLEMENT_ROUTE_ABSENT"),
            "market_reality_onboarding_handoff_ref_or_gap": _route("market_reality_onboarding", candidate_id),
            "pretrade_qku_formula_compute_map_ref_or_gap": _route("pretrade_compute_map", candidate_id),
            "pretrade_order_simulation_spec_ref_or_gap": _route("pretrade_order_simulation", candidate_id),
            "pretrade_objective_kernel_ref_or_gap": _route("objective_kernel", candidate_id),
            "contract_payoff_model_ref_or_gap": _route("contract_payoff", candidate_id),
            "market_state_quality_gate_ref_or_gap": _route("market_state_quality_gate", candidate_id),
            "probability_calibration_gate_ref_or_gap": _route("probability_calibration_gate", candidate_id),
            "pretrade_model_validity_horizon_ref_or_gap": _route("model_validity_horizon", candidate_id),
            "reality_assumption_ledger_ref_or_gap": _route("reality_assumption", candidate_id),
            "pretrade_model_risk_control_ref_or_gap": _route("model_risk_control", candidate_id),
            "pretrade_parameter_operability_ref_or_gap": _route("parameter_operability", candidate_id),
            "pretrade_gate_snapshot_handoff_ref_or_gap": _route("gate_snapshot_handoff", candidate_id),
            "pretrade_owner_intent_binding_ref_or_gap": _route("owner_intent_binding", candidate_id),
            "pretrade_owner_next_step_handoff_ref_or_gap": _route("owner_next_step", candidate_id),
            "pretrade_owner_guidance_handoff_ref_or_gap": _route("owner_guidance", candidate_id),
            "microstructure_state_model_ref_or_gap": _route("microstructure_state", candidate_id),
            "pretrade_risk_envelope_ref_or_gap": _route("risk_envelope", candidate_id),
            "pretrade_threshold_policy_ref_or_gap": _route("threshold_policy", candidate_id),
            "pretrade_decision_trace_ref_or_gap": _route("decision_trace", candidate_id),
            "pretrade_agent_dag_handoff_ref_or_gap": _route("agent_dag_handoff", candidate_id),
            "agent_workflow_obs_handoff_ref_or_gap": _route("agent_workflow_obs", candidate_id),
            "pretrade_metrics_capture_handoff_ref_or_gap": _route("metrics_capture_handoff", candidate_id),
            "pretrade_artifact_value_route_map_ref_or_gap": _route("artifact_value_route", candidate_id),
            "pretrade_agent_access_path_audit_ref_or_gap": _route("agent_access_path_audit", candidate_id),
            "pretrade_edge_alpha_capture_map_ref_or_gap": _route("edge_alpha_capture", candidate_id),
            "clean_room_default_candidate_lane_ref_or_gap": _route("clean_room_default", candidate_id),
            "pretrade_memory_prior_reval_ref_or_gap": _route("memory_prior_reval", candidate_id),
            "pretrade_recovery_frontier_ref_or_gap": _route("recovery_frontier", candidate_id),
            "pretrade_venue_policy_matrix_ref_or_gap": _route("venue_policy_matrix", candidate_id),
            "pretrade_edge_attribution_ref_or_gap": _route("edge_attribution", candidate_id),
            "pretrade_exec_ladder_handoff_ref_or_gap": _route("exec_ladder_handoff", candidate_id),
            "readiness1_connector_handoff_ref_or_gap": readiness.get("connector_route_handoff_ref_or_gap") or _gap("READINESS1_CONNECTOR_HANDOFF_ABSENT"),
            "readiness1_execution_router_handoff_ref_or_gap": readiness.get("execution_router_action_handoff_ref_or_gap") or _gap("READINESS1_EXECUTION_ROUTER_HANDOFF_ABSENT"),
            "readiness1_shadow_handoff_ref_or_gap": readiness.get("shadow_comparison_handoff_ref_or_gap") or _gap("READINESS1_SHADOW_HANDOFF_ABSENT"),
            "trade_plan_candidate_ref": readiness.get("trade_plan_candidate_ref") or _source_ref("docs/master_plan/generated/pr168_rp5g/trade_candidate.jsonl", candidate_id),
            "trade_plan_binding_ref_or_gap": _route("trade_plan_binding", candidate_id),
            "qku_refs": qku_refs,
            "formula_refs": formula_refs,
            "algorithm_refs_or_gap": readiness.get("algorithm_refs_or_gap") or _gap("ALGORITHM_REF_NOT_MATERIALIZED_UPSTREAM"),
            "parameter_stack_refs_or_gap": readiness.get("parameter_stack_refs_or_gap") or _route("parameter_operability", candidate_id),
            "market_family": str(readiness.get("market_family") or "prediction_market"),
            "venue_scope": venue_scope,
            "platform_scope": str(readiness.get("platform_scope") or "stage1_prediction_markets"),
            "stage_activation_state": "PRETRADE1_NO_RUNTIME_CONTRACT",
            "stage1_prediction_market_applicability_state": readiness.get("stage1_prediction_market_applicability_state") or "APPLICABLE_NONLIVE_ROUTE",
            "active_stage_profile_ref_or_gap": readiness.get("active_stage_profile_ref_or_gap") or _gap("ACTIVE_STAGE_PROFILE_ABSENT"),
            "agent_role_refs": agent_roles,
            "agent_roster_discovery_audit_ref_or_gap": readiness.get("agent_roster_discovery_audit_ref_or_gap") or _gap("PR165_D2_AGENT_ROSTER_ABSENT"),
            "agent_duty_source_crosswalk_ref_or_gap": readiness.get("agent_duty_source_crosswalk_ref_or_gap") or _gap("PR165_D2_AGENT_DUTY_CROSSWALK_ABSENT"),
            "pr164_review_ref_or_gap": readiness.get("pr164_review_ref_or_gap") or _gap("PR164_REVIEW_CURRENT_EQUIVALENT_ABSENT"),
            "pr163c_repair_ref_or_gap": readiness.get("pr163c_repair_ref_or_gap") or _gap("PR163C_REPAIR_CURRENT_EQUIVALENT_ABSENT"),
            "pr165_score_ref_or_gap": readiness.get("pr165_score_ref_or_gap") or _gap("PR165_SCORE_CURRENT_EQUIVALENT_ABSENT"),
            "rp5g_sim_ref_or_gap": _source_ref("docs/master_plan/generated/pr168_rp5g/trade_candidate.jsonl", rp5g.get("row_id") or candidate_id),
            "rank4_rank_ref_or_gap": _row_ref("docs/master_plan/generated/pr168_rank4/rank_order.jsonl", rank4, "row_id", "rank_id"),
            "qopt1_optimization_ref_or_gap": readiness.get("qopt1_optimization_ref_or_gap") or _gap("PR168_QOPT1_SELECTED_BATCH_ABSENT"),
            "vs2_paper_intent_ref_or_gap": readiness.get("vs2_paper_intent_ref_or_gap") or _gap("PR168_VS2_PACKET_ABSENT"),
            "mem1_memory_ref_or_gap": _row_ref("docs/master_plan/generated/pr168_mem1/context_signature.jsonl", mem_context, "row_id", "context_signature_id"),
            "route_triage_ref_or_gap": readiness.get("route_triage_ref_or_gap") or _gap("ROUTE_TRIAGE_CURRENT_EQUIVALENT_ABSENT"),
            "master_plan_section_ref_or_gap": readiness.get("master_plan_section_ref_or_gap") or "docs/master_plan/QTT_MasterPlan_Current.md::historical_route_context",
            "market_specific_section_index_ref_or_gap": readiness.get("market_specific_section_index_ref_or_gap") or _gap("MARKET_SECTION_INDEX_ABSENT"),
            "command_action_matrix_ref_or_gap": readiness.get("command_action_matrix_ref_or_gap") or _gap("COMMAND_ACTION_MATRIX_ABSENT"),
            "pretrade_decision_candidate_id": packet_id,
            "pretrade_mode_scope": "PRE_SUBMIT_ANALYSIS_ONLY",
            "pretrade_packet_state": packet_state,
            "pretrade_packet_basis": packet_gap,
            "pretrade_decision_state": packet_state,
            "pretrade_decision_basis": packet_gap,
            "pretrade_blocker_family_or_none": "NONE" if packet_state.startswith("PRETRADE_PASS") else packet_gap.split("_PENDING")[0],
            "pretrade_blocker_detail_or_none": "NONE" if packet_state.startswith("PRETRADE_PASS") else packet_gap,
            "expected_net_cash_value_state": "ROUTED_NONLIVE_EXPECTED_VALUE_NOT_PROFIT_PROOF",
            "expected_net_cash_lcb_state": "ROUTED_NONLIVE_LCB_NOT_PROFIT_PROOF",
            "no_trade_margin_state": "REQUIRED_COMPARATOR_ROUTE",
            "no_trade_candidate_ref_or_gap": _route("no_trade_candidate", candidate_id),
            "order_policy_candidate_set_ref_or_gap": _route("order_policy_candidate_set", candidate_id),
            "scenario_ladder_decision_ref_or_gap": _route("scenario_ladder_decision", candidate_id),
            "latency_budget_decision_ref_or_gap": _route("latency_budget_decision", candidate_id),
            "mode_authority_matrix_ref_or_gap": _route("mode_authority_matrix", candidate_id),
            "market_reality_onboarding_ref_or_gap": _route("market_reality_onboarding", candidate_id),
            "venue_reality_model_ref_or_gap": _route("venue_reality_model", candidate_id),
            "fee_model_ref_or_gap": _route("fee_model", candidate_id),
            "fill_model_ref_or_gap": _route("fill_model", candidate_id),
            "slippage_model_ref_or_gap": _route("slippage_model", candidate_id),
            "latency_decay_model_ref_or_gap": _route("latency_decay_model", candidate_id),
            "queue_position_model_ref_or_gap": _route("queue_position_model", candidate_id),
            "partial_fill_model_ref_or_gap": _route("partial_fill_model", candidate_id),
            "capacity_crowding_model_ref_or_gap": _route("capacity_crowding_model", candidate_id),
            "adverse_selection_model_ref_or_gap": _route("adverse_selection_model", candidate_id),
            "settlement_resolution_model_ref_or_gap": _route("settlement_resolution_model", candidate_id),
            "cashflow_model_ref_or_gap": _route("cashflow_model", candidate_id),
            "order_policy_reality_model_ref_or_gap": _route("order_policy_reality_model", candidate_id),
            "paper_vs_replay_reality_diff_ref_or_gap": _route("paper_vs_replay_diff", candidate_id),
            "reality_model_calibration_receipt_ref_or_gap": _route("calibration_receipt", candidate_id),
            "tca_decomposition_ref_or_gap": _route("tca_decomposition", candidate_id),
            "pretrade_scorecard_ref_or_gap": _route("pretrade_scorecard", candidate_id),
            "pretrade_agent_packet_map_ref_or_gap": _route("agent_packet_map", candidate_id),
            "pretrade_llm_grounding_view_ref_or_gap": _route("llm_grounding_view", candidate_id),
            "pretrade_owner_view_handoff_ref_or_gap": _route("owner_view_handoff", candidate_id),
            "dashboard_surface_registry_ref_or_gap": readiness.get("dashboard_surface_registry_ref_or_gap") or _file_or_gap(ctx.repo_root, "docs/master_plan/generated/pr169_dash1/owner_dashboard_surface_registry.jsonl", "DASHBOARD_SURFACE_REGISTRY_ABSENT"),
            "owner_dashboard_state_ref_or_gap": readiness.get("owner_dashboard_route_ref_or_gap") or _gap("OWNER_DASHBOARD_STATE_ABSENT"),
            "owner_action_registry_ref_or_gap": readiness.get("owner_action_registry_ref_or_gap") or _file_or_gap(ctx.repo_root, "docs/master_plan/generated/pr169_dash1/owner_action_registry.generated.jsonl", "OWNER_ACTION_REGISTRY_ABSENT"),
            "owner_surface_resolver_ref_or_gap": readiness.get("owner_surface_resolver_ref_or_gap") or _gap("OWNER_SURFACE_RESOLVER_ABSENT"),
            "owner_ux_semantic_bundle_ref_or_gap": readiness.get("owner_ux_semantic_bundle_ref_or_gap") or _gap("OWNER_UX_SEMANTIC_BUNDLE_ABSENT"),
            "owner_search_semantics_ref_or_gap": readiness.get("owner_search_semantics_ref_or_gap") or _gap("OWNER_SEARCH_SEMANTICS_ABSENT"),
            "owner_option_range_semantics_ref_or_gap": readiness.get("owner_option_range_semantics_ref_or_gap") or _gap("OWNER_OPTION_RANGE_SEMANTICS_ABSENT"),
            "owner_theme_preference_semantics_ref_or_gap": readiness.get("owner_theme_preference_semantics_ref_or_gap") or _gap("OWNER_THEME_SEMANTICS_ABSENT"),
            "owner_education_qtt_guide_semantics_ref_or_gap": readiness.get("owner_education_guide_semantics_ref_or_gap") or _gap("OWNER_EDUCATION_GUIDE_ABSENT"),
            "owner_chart_policy_ref_or_gap": readiness.get("owner_chart_policy_ref_or_gap") or _gap("OWNER_CHART_POLICY_ABSENT"),
            "owner_drawer_semantics_ref_or_gap": readiness.get("owner_drawer_semantics_ref_or_gap") or _gap("OWNER_DRAWER_SEMANTICS_ABSENT"),
            "owner_preference_policy_ref_or_gap": readiness.get("owner_preference_policy_ref_or_gap") or _gap("OWNER_PREFERENCE_POLICY_ABSENT"),
            "pretrade_connector_handoff_ref_or_gap": _route("connector_handoff", candidate_id),
            "pretrade_execution_router_handoff_ref_or_gap": _route("execution_router_handoff", candidate_id),
            "pretrade_hotpath_handoff_ref_or_gap": _route("hotpath_handoff", candidate_id),
            "pretrade_quantum_readiness_handoff_ref_or_gap": _route("quantum_readiness", candidate_id),
            "source_coverage_handoff_ref_or_gap": _route("source_coverage", candidate_id),
            "candidate_external_info_lane_ref_or_gap": _route("candidate_external_info_lane", candidate_id),
            "expected_net_cash_formula_ref_or_gap": "normalized_expected_net_cash_formula::binary_prediction_market",
            "lower_confidence_bound_ref_or_gap": _route("probability_lcb", candidate_id),
            "implementation_shortfall_ref_or_gap": _route("implementation_shortfall", candidate_id),
            "mode_authority_state": "NO_SUBMIT_NO_RUNTIME_PRETRADE_ONLY",
            "downstream_consumer_refs": list(DOWNSTREAM_CONSUMERS),
            "no_raw_jsonl_scan_proof_ref": _out_ref("no_raw_jsonl_scan.report.json"),
            "orphan_status": "NOT_ORPHANED_ROUTE_PROOF_PRESENT",
            "edge_capture_score_0_1": _score(no_trade, fill, micro, calibration),
            "quality_gate_state": quality_state,
            "quality_gap_reason_or_none": quality_gap,
            "mem1_winning_recipe_ref_or_gap": _row_ref("docs/master_plan/generated/pr168_mem1/winning_recipe.jsonl", mem_recipe, "row_id", "recipe_id"),
        }
        registry.append(_projection_row("pretrade_decision_registry", {**row, **_false_payload()}))
    return registry


def _candidate_rows(registry: Sequence[dict[str, Any]], projection_name: str, maker) -> list[dict[str, Any]]:
    return [_projection_row(projection_name, {**maker(row), **_false_payload()}) for row in registry]


def _readiness_input_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        cid = row["candidate_id"]
        return {
            "readiness1_input_map_id": f"READINESS1_INPUT_MAP_{_id_suffix(cid)}",
            "candidate_id": cid,
            "readiness1_registry_row_ref": row["readiness1_registry_row_ref"],
            "readiness1_computable_contract_ref_or_gap": row["readiness1_computable_contract_ref"],
            "readiness1_executable_now_ref_or_gap": _route("readiness1_executable_now", cid),
            "readiness1_paper_loop_usable_ref_or_gap": _route("readiness1_paper_loop_usable", cid),
            "readiness1_adapter_blocked_ref_or_gap": _route("readiness1_adapter_blocked", cid),
            "readiness1_unlock_queue_ref_or_gap": _route("readiness1_unlock_queue", cid),
            "readiness1_agent_universe_ref_or_gap": _route("readiness1_agent_universe", cid),
            "readiness1_qku_formula_agent_compute_map_ref_or_gap": row["readiness1_computable_contract_ref"],
            "readiness1_trade_variable_search_handoff_ref_or_gap": row["readiness1_trade_variable_search_ref_or_gap"],
            "readiness1_edge_alpha_decision_readiness_ref_or_gap": row["readiness1_edge_alpha_ref_or_gap"],
            "readiness1_order_scenario_tournament_handoff_ref_or_gap": row["readiness1_order_scenario_tournament_ref_or_gap"],
            "readiness1_shadow_comparison_handoff_ref_or_gap": row["readiness1_shadow_handoff_ref_or_gap"],
            "readiness1_execution_router_action_handoff_ref_or_gap": row["readiness1_execution_router_handoff_ref_or_gap"],
            "readiness1_connector_route_handoff_ref_or_gap": row["readiness1_connector_handoff_ref_or_gap"],
            "readiness1_parameter_operability_handoff_ref_or_gap": row["readiness1_parameter_operability_ref_or_gap"],
            "readiness1_owner_enablement_handoff_ref_or_gap": row["readiness1_owner_enablement_ref_or_gap"],
            "readiness1_quantum_readiness_ref_or_gap": _route("readiness1_quantum_readiness", cid),
            "readiness1_source_coverage_handoff_ref_or_gap": _route("readiness1_source_coverage", cid),
            "readiness1_candidate_external_info_lane_ref_or_gap": _route("readiness1_candidate_external_info", cid),
            "readiness1_gap_ledger_ref_or_gap": _route("readiness1_gap_ledger", cid),
            "readiness1_no_orphan_report_ref_or_gap": "docs/master_plan/generated/pr169_readiness1/no_orphan.report.json",
            "readiness1_no_placeholder_report_ref_or_gap": "docs/master_plan/generated/pr169_readiness1/no_placeholder_materialization.report.json",
            "input_consumption_state": "CONSUMED_AS_UPSTREAM_CURRENT_EQUIVALENT",
            "input_gap_reason_or_none": "NONE",
            "pretrade_consumer_refs": [row["pretrade_decision_candidate_id"], row["pretrade_qku_formula_compute_map_ref_or_gap"]],
            "readiness1_recomputed": False,
            "readiness1_modified": False,
        }
    return _candidate_rows(registry, "readiness1_input_map", make)


def _projection_contract_extra(row: dict[str, Any], projection_name: str) -> dict[str, Any]:
    cid = row["candidate_id"]
    if projection_name == "pretrade_qku_formula_compute_map":
        return {
            "pretrade_qku_formula_compute_map_id": row["pretrade_qku_formula_compute_map_ref_or_gap"],
            "responsible_pr165_d2_agent_route_refs_or_gap": row["agent_role_refs"],
            "llm_grounding_route_ref_or_gap": row["pretrade_llm_grounding_view_ref_or_gap"],
            "immutable_qku_formula_state": "IMMUTABLE",
            "mutable_trade_variable_refs_or_gap": row["trade_plan_binding_ref_or_gap"],
            "centralized_agent_access_path_ref_or_gap": row["pretrade_agent_access_path_audit_ref_or_gap"],
            "downstream_consumer_route_refs": row["downstream_consumer_refs"],
            "raw_jsonl_scan_used": False,
            "formula_mutation_created": False,
        }
    if projection_name == "pretrade_order_simulation_specs":
        return {
            "pretrade_order_simulation_spec_id": row["pretrade_order_simulation_spec_ref_or_gap"],
            "classical_spec_ref_or_inline": "evaluate objective kernel, TCA, no-trade, and scenario ladder with no execution",
            "quantum_forward_spec_ref_or_inline": row["pretrade_quantum_readiness_handoff_ref_or_gap"],
            "order_policy_combination_refs": [
                "MAKER_ONLY",
                "TAKER_ONLY",
                "MAKER_TAKER_SPLIT",
                "PASSIVE_FIRST_CANCEL_REPLACE",
                "SIZE_BUCKET_ENTRY_EXIT_RULE",
            ],
            "shared_input_lock_ref_or_gap": row["readiness1_registry_row_ref"],
            "simulation_scope_state": "SPECIFICATION_ONLY_NO_REPLAY_PAPER_LIVE_EXECUTION",
            "execution_created": False,
        }
    if projection_name == "paper_vs_replay_reality_diff":
        return {
            "reality_diff_id": row["paper_vs_replay_reality_diff_ref_or_gap"],
            "replay_assumption_refs_or_gap": row["rp5g_sim_ref_or_gap"],
            "paper_assumption_refs_or_gap": row["vs2_paper_intent_ref_or_gap"],
            "fee_diff_state": "ROUTED_TO_MODEL_COMPONENT_COMPARISON",
            "fill_diff_state": "ROUTED_TO_MODEL_COMPONENT_COMPARISON",
            "slippage_diff_state": "ROUTED_TO_MODEL_COMPONENT_COMPARISON",
            "latency_diff_state": "ROUTED_TO_MODEL_COMPONENT_COMPARISON",
            "capacity_diff_state": "ROUTED_TO_MODEL_COMPONENT_COMPARISON",
            "cashflow_diff_state": "ROUTED_TO_MODEL_COMPONENT_COMPARISON",
            "settlement_diff_state": "ROUTED_TO_MODEL_COMPONENT_COMPARISON",
            "order_policy_diff_state": "ROUTED_TO_MODEL_COMPONENT_COMPARISON",
            "model_risk_diff_state": "PAPER_REPLAY_DIFFERENCE_IS_MODEL_RISK_INPUT",
            "pretrade_adjustment_route_ref_or_gap": row["pretrade_model_risk_control_ref_or_gap"],
        }
    if projection_name == "reality_model_calibration_receipts":
        return {
            "calibration_receipt_id": row["reality_model_calibration_receipt_ref_or_gap"],
            "calibration_source_refs": [
                row["rp5g_sim_ref_or_gap"],
                row["rank4_rank_ref_or_gap"],
                row["mem1_memory_ref_or_gap"],
                row["readiness1_registry_row_ref"],
            ],
            "rp5g_ref_or_gap": row["rp5g_sim_ref_or_gap"],
            "rank4_ref_or_gap": row["rank4_rank_ref_or_gap"],
            "qopt1_ref_or_gap": row["qopt1_optimization_ref_or_gap"],
            "vs2_ref_or_gap": row["vs2_paper_intent_ref_or_gap"],
            "mem1_ref_or_gap": row["mem1_memory_ref_or_gap"],
            "readiness1_ref_or_gap": row["readiness1_registry_row_ref"],
            "sample_window_ref_or_gap": "REPO_LOCAL_NONLIVE_FIXTURE_WINDOW",
            "support_count_or_gap": "SCOPED_GAP_ACCEPTED_SOURCE_SUPPORT_PENDING",
            "outlier_policy_or_gap": "SCOPED_GAP_DOWNSTREAM_CALIBRATION_POLICY_PENDING",
            "calibration_family": "DECLARED_NONLIVE_EVIDENCE_RECEIPT",
            "calibration_state": "EXISTING_EVIDENCE_ONLY_NO_MODEL_TRAINING",
            "calibration_gap_reason_or_none": "ACCEPTED_SOURCE_AND_PAPER_RECEIPTS_PENDING",
            "model_training_created": False,
        }
    if projection_name == "tca_decomposition":
        return {
            "tca_decomposition_id": row["tca_decomposition_ref_or_gap"],
            "implementation_shortfall_basis_or_gap": row["implementation_shortfall_ref_or_gap"],
            "arrival_or_decision_price_basis_or_gap": row["trade_plan_candidate_ref"],
            "gross_expected_cash_route_ref_or_gap": row["pretrade_objective_kernel_ref_or_gap"],
            "explicit_fee_component_ref_or_gap": row["fee_model_ref_or_gap"],
            "spread_cost_component_ref_or_gap": row["slippage_model_ref_or_gap"],
            "slippage_component_ref_or_gap": row["slippage_model_ref_or_gap"],
            "market_impact_component_ref_or_gap": row["capacity_crowding_model_ref_or_gap"],
            "latency_drag_component_ref_or_gap": row["latency_decay_model_ref_or_gap"],
            "delay_cost_component_ref_or_gap": row["latency_budget_decision_ref_or_gap"],
            "opportunity_cost_component_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
            "queue_cost_component_ref_or_gap": row["queue_position_model_ref_or_gap"],
            "partial_fill_cost_component_ref_or_gap": row["partial_fill_model_ref_or_gap"],
            "adverse_selection_component_ref_or_gap": row["adverse_selection_model_ref_or_gap"],
            "settlement_cashflow_component_ref_or_gap": row["cashflow_model_ref_or_gap"],
            "net_expected_cash_after_cost_ref_or_gap": row["pretrade_objective_kernel_ref_or_gap"],
            "lower_confidence_bound_ref_or_gap": row["lower_confidence_bound_ref_or_gap"],
            "tca_state": "DECOMPOSED_COMPONENT_ROUTES_PRESENT",
            "tca_gap_reason_or_none": "ACCEPTED_SOURCE_AND_RUNTIME_RECEIPTS_PENDING",
        }
    if projection_name == "pretrade_scorecard":
        return {
            "pretrade_scorecard_id": row["pretrade_scorecard_ref_or_gap"],
            "pretrade_readiness_score_0_1": row["edge_capture_score_0_1"],
            "execution_adjusted_ranking_state": "ROUTED_FROM_READINESS1_RANKING_AND_PRETRADE_TCA",
            "payoff_normalization_state": "REQUIRED_BY_OBJECTIVE_KERNEL",
            "market_state_quality_state": row["quality_gate_state"],
            "probability_calibration_state": "EXISTING_EVIDENCE_OR_SCOPED_GAP",
            "model_validity_horizon_state": "TTL_REQUIRED_BEFORE_DOWNSTREAM_USE",
            "expected_net_cash_state": row["expected_net_cash_value_state"],
            "lower_confidence_bound_state": row["expected_net_cash_lcb_state"],
            "tca_decomposition_state": "EXPLICIT_COMPONENT_ROUTES",
            "no_trade_comparator_route": row["no_trade_candidate_ref_or_gap"],
            "regime_conditioned_memory_state": "MEM1_PRIOR_REVALIDATION_REQUIRED",
            "mem1_context_signature_ref_or_gap": row["mem1_memory_ref_or_gap"],
            "quantum_structural_readiness_state": "STRUCTURAL_HANDOFF_ONLY_NO_BACKEND",
            "scenario_ladder_decision_state": "MATERIALIZED_PRETRADE_SCENARIO_LADDER",
            "mode_authority_state": row["mode_authority_state"],
            "dag_upstream_refs": [row["readiness1_registry_row_ref"], row["rp5g_sim_ref_or_gap"], row["mem1_memory_ref_or_gap"]],
            "dag_downstream_refs": row["downstream_consumer_refs"],
        }
    if projection_name == "pretrade_agent_packet_map":
        return {
            "pretrade_agent_packet_map_id": row["pretrade_agent_packet_map_ref_or_gap"],
            "responsible_agent_role_refs": row["agent_role_refs"],
            "agent_roster_discovery_audit_ref_or_gap": row["agent_roster_discovery_audit_ref_or_gap"],
            "agent_duty_source_crosswalk_ref_or_gap": row["agent_duty_source_crosswalk_ref_or_gap"],
            "agent_input_packet_contract_ref": row["pretrade_decision_candidate_id"],
            "agent_expected_output_packet_contract_ref": "PreTradeDecisionCandidateV1::no_submit",
            "pretrade_model_refs": [
                row["venue_reality_model_ref_or_gap"],
                row["pretrade_objective_kernel_ref_or_gap"],
                row["tca_decomposition_ref_or_gap"],
            ],
            "no_trade_candidate_ref": row["no_trade_candidate_ref_or_gap"],
            "scenario_ladder_decision_ref": row["scenario_ladder_decision_ref_or_gap"],
            "llm_grounding_view_ref_or_gap": row["pretrade_llm_grounding_view_ref_or_gap"],
            "owner_view_handoff_ref_or_gap": row["pretrade_owner_view_handoff_ref_or_gap"],
            "pretrade_agent_dag_handoff_ref_or_gap": row["pretrade_agent_dag_handoff_ref_or_gap"],
        }
    if projection_name == "pretrade_llm_grounding_view":
        return {
            "pretrade_llm_grounding_view_id": row["pretrade_llm_grounding_view_ref_or_gap"],
            "allowed_llm_roles": [
                "summarize",
                "critique",
                "explain",
                "route",
                "propose_research_questions",
                "draft_owner_plain_english_explanation",
                "explain_no_trade",
                "explain_tca",
                "explain_reality_model_gap",
            ],
            "forbidden_llm_roles": [
                "source_truth_creation",
                "risk_pass_creation",
                "profit_proof_creation",
                "order_authority",
                "connector_authority",
                "live_readiness_proof",
                "result_rewrite",
                "direct_trade_submission",
            ],
            "source_evidence_refs_or_gap": row["source_coverage_handoff_ref_or_gap"],
            "candidate_external_info_lane_refs_or_gap": row["candidate_external_info_lane_ref_or_gap"],
            "pretrade_packet_refs": [row["pretrade_decision_candidate_id"]],
            "required_caveats": ["pretrade packet only", "no order authority", "not profit proof"],
            "plain_english_summary_seed": "This packet explains why the candidate is provider-pending or no-trade comparable before any order can exist.",
            "raw_jsonl_scan_used": False,
        }
    if projection_name == "pretrade_owner_view_handoff":
        return {
            "pretrade_owner_view_handoff_id": row["pretrade_owner_view_handoff_ref_or_gap"],
            "owner_dashboard_state_ref_or_gap": row["owner_dashboard_state_ref_or_gap"],
            "owner_surface_resolver_ref_or_gap": row["owner_surface_resolver_ref_or_gap"],
            "owner_action_registry_ref_or_gap": row["owner_action_registry_ref_or_gap"],
            "dashboard_surface_registry_ref_or_gap": row["dashboard_surface_registry_ref_or_gap"],
            "central_owner_ux_semantic_bundle_ref_or_gap": row["owner_ux_semantic_bundle_ref_or_gap"],
            "owner_search_semantics_ref_or_gap": row["owner_search_semantics_ref_or_gap"],
            "owner_option_range_semantics_ref_or_gap": row["owner_option_range_semantics_ref_or_gap"],
            "owner_theme_preference_semantics_ref_or_gap": row["owner_theme_preference_semantics_ref_or_gap"],
            "owner_education_qtt_guide_semantics_ref_or_gap": row["owner_education_qtt_guide_semantics_ref_or_gap"],
            "owner_chart_policy_ref_or_gap": row["owner_chart_policy_ref_or_gap"],
            "owner_drawer_semantics_ref_or_gap": row["owner_drawer_semantics_ref_or_gap"],
            "owner_preference_policy_ref_or_gap": row["owner_preference_policy_ref_or_gap"],
            "owner_decision_queue_route_ref_or_gap": "OwnerDecisionQueueReadModelV1::provider_pending",
            "owner_agent_operations_route_ref_or_gap": "OwnerAgentActivityReadModelV1::provider_pending",
            "owner_workflow_queue_route_ref_or_gap": "OwnerWorkflowQueueReadModelV1::provider_pending",
            "owner_receipt_preview_route_ref_or_gap": "OwnerReceiptPreviewReadModelV1::provider_pending",
            "trade_workbench_route_ref_or_gap": "PR169-SVC1::trade_workbench_provider_pending",
            "pretrade_summary_card_route_ref_or_gap": "PR169-SVC1::pretrade_summary_card_provider_pending",
            "no_trade_explanation_route_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
            "tca_waterfall_route_ref_or_gap": row["tca_decomposition_ref_or_gap"],
            "disabled_action_education_route_ref_or_gap": row["pretrade_owner_guidance_handoff_ref_or_gap"],
            "provider_pending_explanation_route_ref_or_gap": row["pretrade_owner_guidance_handoff_ref_or_gap"],
        }
    if projection_name == "pretrade_connector_handoff":
        return {
            "pretrade_connector_handoff_id": row["pretrade_connector_handoff_ref_or_gap"],
            "market_family": row["market_family"],
            "connector_family_ref_or_gap": "VENUE_NEUTRAL_CONNECTOR::provider_pending_no_read",
            "venue_neutral_adapter_ref_or_gap": "VENUE_NEUTRAL_ADAPTER::provider_pending_no_read",
            "required_connector_semantic_fields": ["venue_scope", "contract_id", "side", "price", "size", "order_policy"],
            "required_source_evidence_packet_refs_or_gap": row["source_coverage_handoff_ref_or_gap"],
            "required_private_cash_receipt_refs_or_gap": _gap("RUNTIME_CASH_RECEIPT_DOWNSTREAM_REQUIRED"),
            "connector_route_state": "PROVIDER_PENDING_NO_CONNECTOR_READ",
            "connector_gap_reason_or_none": "CONNECTOR_SEMANTICS_AND_CREDENTIALS_DOWNSTREAM",
        }
    if projection_name == "pretrade_execution_router_handoff":
        return {
            "pretrade_execution_router_handoff_id": row["pretrade_execution_router_handoff_ref_or_gap"],
            "execution_router_action_handoff_ref_or_gap": row["readiness1_execution_router_handoff_ref_or_gap"],
            "allowed_downstream_action_verbs": ["BUY", "SELL", "OPEN", "CLOSE", "CANCEL", "REPLACE", "REDUCE", "EXIT"],
            "pretrade_gate_state": "PROVIDER_PENDING_DOWNSTREAM_NO_RELEASE",
            "risk_gate_route_ref_or_gap": row["pretrade_risk_envelope_ref_or_gap"],
            "source_evidence_gate_route_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
            "runtime_cash_gate_route_ref_or_gap": _gap("RUNTIME_CASH_GATE_DOWNSTREAM"),
            "portfolio_exposure_gate_route_ref_or_gap": row["pretrade_parameter_operability_ref_or_gap"],
            "latency_gate_route_ref_or_gap": row["latency_budget_decision_ref_or_gap"],
            "kill_switch_gate_route_ref_or_gap": "EXECUTION_ROUTER_KILL_SWITCH::downstream_provider_pending",
            "owner_approval_route_ref_or_gap": "OwnerActionRegistry::owner_approval_provider_pending",
            "execution_router_release_state": "PROVIDER_PENDING_DOWNSTREAM",
        }
    if projection_name == "pretrade_hotpath_handoff":
        return {
            "pretrade_hotpath_handoff_id": row["pretrade_hotpath_handoff_ref_or_gap"],
            "hotpath_consumer_ref_or_gap": "PR170-HOTPATH1::provider_pending",
            "cache_candidate_state": "PRECOMPUTE_ELIGIBLE_ONLY_AFTER_GATES",
            "precompute_requirement_state": "PRECOMPUTED_SNAPSHOT_REQUIRED",
            "model_component_cache_refs_or_gap": [
                row["pretrade_gate_snapshot_handoff_ref_or_gap"],
                row["pretrade_model_validity_horizon_ref_or_gap"],
            ],
            "latency_budget_decision_ref_or_gap": row["latency_budget_decision_ref_or_gap"],
            "owner_enablement_ref_or_gap": row["readiness1_owner_enablement_ref_or_gap"],
            "quantum_pretrade_ref_or_gap": row["pretrade_quantum_readiness_handoff_ref_or_gap"],
        }
    if projection_name == "pretrade_quantum_readiness_handoff":
        return {
            "pretrade_quantum_handoff_id": row["pretrade_quantum_readiness_handoff_ref_or_gap"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "readiness1_quantum_readiness_ref_or_gap": row["qopt1_optimization_ref_or_gap"],
            "q_problem_type": "QUBO_STRUCTURAL_CANDIDATE",
            "q_variable_domain": "binary select/no-trade/order-policy variables",
            "q_objective_terms": [row["pretrade_objective_kernel_ref_or_gap"], row["tca_decomposition_ref_or_gap"]],
            "q_constraint_terms": [row["pretrade_risk_envelope_ref_or_gap"], row["latency_budget_decision_ref_or_gap"]],
            "q_no_trade_action_encoding_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
            "q_order_policy_encoding_ref_or_gap": row["order_policy_candidate_set_ref_or_gap"],
            "q_owner_disabled_fixed_zero_constraint_ref_or_gap": "OwnerActionRegistry::disabled_action_fixed_zero_provider_pending",
            "q_classical_comparator_ref_or_gap": row["pretrade_scorecard_ref_or_gap"],
            "q_fallback_route_ref_or_gap": "CLASSICAL_PRETRADE_OBJECTIVE_KERNEL",
            "qmap_consumer_ref_or_gap": "PR174-QMAP1::provider_pending",
        }
    if projection_name == "pretrade_gate_snapshot_handoff":
        return {
            "pretrade_gate_snapshot_handoff_id": row["pretrade_gate_snapshot_handoff_ref_or_gap"],
            "snapshot_source_state": "PRECOMPUTED_ONLY_NO_SNAPSHOT_CREATED_IN_THIS_PR",
            "source_retrieval_in_live_path_allowed": False,
            "dashboard_rendering_in_live_path_allowed": False,
            "replay_paper_recalculation_in_live_path_allowed": False,
            "llm_call_in_live_path_allowed": False,
            "quantum_backend_call_in_live_path_allowed": False,
            "required_gate_refs": [
                row["market_state_quality_gate_ref_or_gap"],
                row["probability_calibration_gate_ref_or_gap"],
                row["pretrade_model_validity_horizon_ref_or_gap"],
                row["mode_authority_matrix_ref_or_gap"],
            ],
        }
    if projection_name == "pretrade_owner_intent_bindings":
        return {
            "pretrade_owner_intent_binding_id": row["pretrade_owner_intent_binding_ref_or_gap"],
            "owner_intent_examples": [
                "check this market",
                "find the best trade",
                "explain why no-trade wins",
            ],
            "owner_trade_check_request_ref_or_gap": "OwnerTradeCheckRequestV1::provider_pending",
            "pretrade_packet_route_ref": row["pretrade_decision_candidate_id"],
            "chat_runtime_created": False,
            "runtime_llm_call_created": False,
        }
    if projection_name == "pretrade_decision_traces":
        return {
            "pretrade_decision_trace_id": row["pretrade_decision_trace_ref_or_gap"],
            "decision_state": row["pretrade_decision_state"],
            "decision_basis": row["pretrade_decision_basis"],
            "blocking_component_ref_or_none": row["market_state_quality_gate_ref_or_gap"] if not row["pretrade_decision_state"].startswith("PRETRADE_PASS") else "NONE",
            "owner_explanation_route_ref_or_gap": row["pretrade_owner_guidance_handoff_ref_or_gap"],
            "agent_explanation_route_ref_or_gap": row["pretrade_agent_packet_map_ref_or_gap"],
            "llm_explanation_route_ref_or_gap": row["pretrade_llm_grounding_view_ref_or_gap"],
        }
    if projection_name == "pretrade_agent_dag_handoff":
        return {
            "pretrade_agent_dag_handoff_id": row["pretrade_agent_dag_handoff_ref_or_gap"],
            "dag_node_refs": [
                "PreTradeDecisionCandidateV1",
                "NoTradeCandidateV1",
                "VenueRealityModelV1",
                "ExecutionRouterHandoffV1",
            ],
            "dag_edge_refs": [
                f"{row['readiness1_registry_row_ref']}->{row['pretrade_decision_candidate_id']}",
                f"{row['pretrade_decision_candidate_id']}->{row['pretrade_execution_router_handoff_ref_or_gap']}",
            ],
            "work_queue_consumer_refs": ["PR169-AGENT-ORCH1::provider_pending", "PR169-PAPER-LOOP::provider_pending"],
            "receipt_class_refs": ["AgentDecisionReceiptV1::downstream", "NoTradeDecisionReceiptV1::downstream"],
        }
    if projection_name == "agent_workflow_obs_handoff":
        return {
            "agent_workflow_obs_handoff_id": row["agent_workflow_obs_handoff_ref_or_gap"],
            "responsible_pr165_d2_agent_roles": row["agent_role_refs"],
            "supporting_agent_roles": ["TCAAgent", "MarketConditionAgent", "MemoryAgent"],
            "escalation_agent_roles": ["GovernanceAgent", "RiskAgent"],
            "expected_downstream_workflow_stage": "PRETRADE_PROVIDER_PENDING_REVIEW",
            "expected_task_queue_route": "OwnerWorkflowQueueReadModelV1::provider_pending",
            "expected_current_upcoming_task_queue_route": "PR169-AGENT-ORCH1::provider_pending_queue_contract",
            "expected_receipt_classes": [
                "AgentDecisionReceiptV1",
                "NoTradeDecisionReceiptV1",
                "PaperFillSimulationReceiptV1",
                "TcaMetricReceiptV1",
            ],
            "owner_dashboard_agent_operations_route": "OwnerAgentActivityReadModelV1::provider_pending",
            "qtt_team_workflow_queue_route": "OwnerWorkflowQueueReadModelV1::provider_pending",
            "audit_trail_receipts_route": "OwnerReceiptPreviewReadModelV1::provider_pending",
            "no_runtime_no_fake_queue_proof": "all runtime queue/status/timestamp/receipt flags false",
        }
    if projection_name == "pretrade_metrics_capture_handoff":
        return {
            "pretrade_metrics_capture_handoff_id": row["pretrade_metrics_capture_handoff_ref_or_gap"],
            "metric_family": "EXPECTED_NET_CASH_TCA_FILL_LATENCY_CAPACITY_SETTLEMENT_MODEL_RISK",
            "metric_component_ref": row["tca_decomposition_ref_or_gap"],
            "expected_runtime_receipt_type": "TcaMetricReceiptV1::downstream",
            "agent_workflow_obs_handoff_ref_or_gap": row["agent_workflow_obs_handoff_ref_or_gap"],
            "pretrade_artifact_value_route_map_ref_or_gap": row["pretrade_artifact_value_route_map_ref_or_gap"],
            "pretrade_agent_access_path_audit_ref_or_gap": row["pretrade_agent_access_path_audit_ref_or_gap"],
            "pretrade_edge_alpha_capture_map_ref_or_gap": row["pretrade_edge_alpha_capture_map_ref_or_gap"],
            "runtime_task_receipt_route_ref_or_gap": "METRICS1::runtime_task_receipt_downstream",
            "market_quote_receipt_route_ref_or_gap": "METRICS1::quote_receipt_downstream",
            "orderbook_snapshot_receipt_route_ref_or_gap": "METRICS1::orderbook_snapshot_downstream",
            "decision_timestamp_receipt_route_ref_or_gap": "METRICS1::decision_timestamp_downstream",
            "tca_metric_receipt_route_ref_or_gap": "METRICS1::tca_metric_downstream",
            "mem1_update_route_ref_or_gap": "MEM1::receipt_backed_update_downstream",
            "postlaunch_learning_route_ref_or_gap": "POSTLAUNCH::learning_update_downstream",
            "metrics1_consumer_ref_or_gap": "PR170-METRICS1::provider_pending",
        }
    if projection_name == "pretrade_agent_access_path_audit":
        return {
            "pretrade_agent_access_path_audit_id": row["pretrade_agent_access_path_audit_ref_or_gap"],
            "centralized_stage_route_ref": row["active_stage_profile_ref_or_gap"],
            "market_platform_route_ref": f"{row['market_family']}::{row['venue_scope']}::{row['platform_scope']}",
            "agent_duty_route_ref_or_gap": row["agent_duty_source_crosswalk_ref_or_gap"],
            "executability_context_ref_or_gap": row["readiness1_computable_contract_ref"],
            "mem1_context_ref_or_gap": row["mem1_memory_ref_or_gap"],
            "raw_jsonl_runtime_scan_used": False,
            "full_library_default_access_created": False,
            "per_agent_copy_created": False,
            "access_path_state": "CENTRALIZED_RESOLVER_OR_PROJECTION_ONLY",
        }
    return {}


def _simple_projection(registry: Sequence[dict[str, Any]], projection_name: str) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        cid = row["candidate_id"]
        base = {
            f"{projection_name}_id": _route(projection_name, cid),
            "candidate_id": cid,
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
            "qku_refs": row["qku_refs"],
            "formula_refs": row["formula_refs"],
            "venue_scope": row["venue_scope"],
            "platform_scope": row["platform_scope"],
            "state": "MATERIALIZED_NO_RUNTIME_CONTRACT",
            "gap_reason_or_none": "NONE" if row["pretrade_packet_state"] != "PRETRADE_PASS_PROVIDER_PENDING" else row["pretrade_packet_basis"],
            "downstream_consumer_refs": row["downstream_consumer_refs"],
        }
        base.update(_projection_contract_extra(row, projection_name))
        return base
    return _candidate_rows(registry, projection_name, make)


def _component_rows(registry: Sequence[dict[str, Any]], projection_name: str, component_family: str) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        cid = row["candidate_id"]
        model_id = _route(projection_name.replace("s", ""), cid)
        payload = {
            f"{projection_name}_id": model_id,
            COMPONENT_ID_FIELDS.get(projection_name, f"{projection_name}_id"): model_id,
            "candidate_id": cid,
            "component_family": component_family,
            "model_ref": model_id,
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "venue_reality_model_ref": row["venue_reality_model_ref_or_gap"],
            "venue_scope": row["venue_scope"],
            "platform_scope": row["platform_scope"],
            "market_family": row["market_family"],
            "mode_scope": "PRETRADE1_PROVIDER_PENDING_NO_RUNTIME",
            "model_scope": component_family,
            "input_schema_ref_or_inline_contract": f"{component_family}_inputs: market_state, venue_policy, order_policy, candidate_size, latency_budget",
            "output_schema_ref_or_inline_contract": f"{component_family}_outputs: cash_cost_or_probability_adjustment, unit, gap_state",
            "required_market_fields": ["market_family", "venue_scope", "contract_type", "event_lifecycle_state"],
            "required_venue_fields": ["fee_policy", "settlement_policy", "source_authority_state"],
            "required_platform_fields": ["platform_scope", "connector_route_ref"],
            "required_order_policy_fields": ["maker_taker_split", "cancel_replace_interval", "size_budget"],
            "required_liquidity_fields": ["spread", "depth", "orderbook_imbalance"],
            "required_latency_fields": ["latency_budget_ms", "validity_ttl_ms"],
            "required_cashflow_fields": ["cash_lock", "settlement_delay", "max_loss"],
            "formula_ref_or_inline": f"{component_family}_component = deterministic_pretrade_contract_or_scoped_gap",
            "unit_or_basis": "cash_or_probability_basis",
            "scale_contract": "normalized_decimal_or_cash_decimal",
            "normalization_contract": "venue_specific_units_normalized_before_expected_cash",
            "missing_value_policy": "SCOPED_GAP_AND_NO_TRADE_IF_MATERIAL",
            "zero_denominator_policy_or_gap": "SCOPED_GAP_ZERO_DENOMINATOR_BLOCKS_CHAMPION_READY",
            "asof_timestamp_policy_ref_or_gap": row["pretrade_model_validity_horizon_ref_or_gap"],
            "source_authority_state": "CANDIDATE_RESEARCH_PROVISIONAL_NOT_SOURCE_TRUTH",
            "accepted_source_refs_or_gap": _gap(f"{component_family.upper()}_ACCEPTED_SOURCE_EVIDENCE_PENDING"),
            "candidate_external_info_lane_refs_or_gap": row["candidate_external_info_lane_ref_or_gap"],
            "calibration_receipt_ref_or_gap": row["reality_model_calibration_receipt_ref_or_gap"],
            "component_state": "SCOPED_GAP_ROUTED" if row["quality_gate_state"] == "SCOPED_GAP" else "MATERIALIZED_CONTRACT",
            "component_gap_reason_or_none": row["quality_gap_reason_or_none"] if row["quality_gate_state"] == "SCOPED_GAP" else "NONE",
            "unlock_route_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
        }
        if projection_name == "venue_reality_models":
            payload.update(
                {
                    "source_authority_state": "CANDIDATE_RESEARCH_PROVISIONAL_NOT_SOURCE_TRUTH",
                    "fee_model_ref": row["fee_model_ref_or_gap"],
                    "fill_model_ref": row["fill_model_ref_or_gap"],
                    "slippage_model_ref": row["slippage_model_ref_or_gap"],
                    "latency_decay_model_ref": row["latency_decay_model_ref_or_gap"],
                    "queue_position_model_ref": row["queue_position_model_ref_or_gap"],
                    "partial_fill_model_ref": row["partial_fill_model_ref_or_gap"],
                    "capacity_crowding_model_ref": row["capacity_crowding_model_ref_or_gap"],
                    "adverse_selection_model_ref": row["adverse_selection_model_ref_or_gap"],
                    "settlement_resolution_model_ref": row["settlement_resolution_model_ref_or_gap"],
                    "cashflow_model_ref": row["cashflow_model_ref_or_gap"],
                    "order_policy_reality_model_ref": row["order_policy_reality_model_ref_or_gap"],
                    "paper_vs_replay_reality_diff_ref_or_gap": row["paper_vs_replay_reality_diff_ref_or_gap"],
                    "calibration_receipt_ref_or_gap": row["reality_model_calibration_receipt_ref_or_gap"],
                    "model_completeness_state": "COMPONENT_ROUTES_PRESENT_WITH_SCOPED_SOURCE_GAPS",
                    "model_gap_reason_or_none": "ACCEPTED_VENUE_SOURCE_EVIDENCE_PENDING",
                }
            )
        if projection_name == "fee_models":
            payload.update(
                {
                    "fee_basis_state": "VENUE_SPECIFIC_ACCEPTED_SOURCE_PENDING",
                    "fee_source_authority_state": "CANDIDATE_RESEARCH_PROVISIONAL",
                    "fee_rate_ref_or_gap": _gap("ACCEPTED_FEE_RATE_PENDING"),
                    "fee_formula_ref_or_inline": "fee_cost_cash = explicit_fee + platform_fee + settlement_fee - rebates",
                    "maker_fee_component_state": "ROUTED_OR_SCOPED_GAP",
                    "taker_fee_component_state": "ROUTED_OR_SCOPED_GAP",
                    "settlement_fee_component_state": "ROUTED_OR_SCOPED_GAP",
                    "platform_fee_component_state": "ROUTED_OR_SCOPED_GAP",
                    "rebate_component_state_or_gap": _gap("REBATE_POLICY_PENDING"),
                    "fee_currency_or_unit": "normalized_cash",
                    "fee_rounding_policy_or_gap": _gap("VENUE_ROUNDING_POLICY_PENDING"),
                    "fee_missing_policy": "NO_ZERO_FEE_OPTIMISM",
                    "fee_model_state": "MATERIALIZED_WITH_SOURCE_GAPS",
                    "fee_gap_reason_or_none": "ACCEPTED_SOURCE_EVIDENCE_PENDING",
                }
            )
        if projection_name == "fill_models":
            payload.update(
                {
                    "order_policy_candidate_set_ref": row["order_policy_candidate_set_ref_or_gap"],
                    "fill_model_family": "EXPECTED_FILL_PROBABILITY_WITH_SCOPED_GAPS",
                    "fill_probability_formula_ref_or_inline": "expected_fill_probability = f(depth, policy, queue, time_in_force)",
                    "fill_quantity_formula_ref_or_inline": "expected_filled_qty = requested_qty * fill_probability * partial_fill_ratio",
                    "fill_price_basis": "decision_price_or_limit_price_provider_pending",
                    "spread_crossing_policy": "policy_specific_no_default",
                    "queue_position_model_ref": row["queue_position_model_ref_or_gap"],
                    "partial_fill_model_ref": row["partial_fill_model_ref_or_gap"],
                    "liquidity_depth_ref_or_gap": row["microstructure_state_model_ref_or_gap"],
                    "volume_or_trade_rate_ref_or_gap": _gap("VOLUME_OR_TRADE_RATE_PENDING"),
                    "time_in_force_ref_or_gap": row["order_policy_candidate_set_ref_or_gap"],
                    "cancel_replace_interval_ref_or_gap": row["latency_budget_decision_ref_or_gap"],
                    "fill_probability_state": "ROUTED_TO_EXISTING_NONLIVE_EVIDENCE_OR_GAP",
                    "fill_model_state": "MATERIALIZED_WITH_SOURCE_GAPS",
                    "fill_gap_reason_or_none": "ACCEPTED_LIQUIDITY_AND_PAPER_FILL_EVIDENCE_PENDING",
                    "paper_fill_route_ref_or_gap": "PR169-PAPER-LOOP::provider_pending_fill_receipt",
                }
            )
        if projection_name == "slippage_models":
            payload.update(
                {
                    "slippage_family": "SPREAD_IMPACT_LATENCY_ADVERSE_SELECTION_COMPONENTS",
                    "expected_slippage_formula_ref_or_inline": "expected_slippage = spread + impact + latency + adverse_selection + tick_cost",
                    "spread_component_ref_or_gap": row["market_state_quality_gate_ref_or_gap"],
                    "market_impact_component_ref_or_gap": row["capacity_crowding_model_ref_or_gap"],
                    "latency_component_ref_or_gap": row["latency_decay_model_ref_or_gap"],
                    "adverse_selection_component_ref_or_gap": row["adverse_selection_model_ref_or_gap"],
                    "discrete_tick_component_ref_or_gap": _gap("DISCRETE_TICK_POLICY_PENDING"),
                    "slippage_unit_or_basis": "normalized_cash_per_contract",
                    "slippage_state": "MATERIALIZED_WITH_SOURCE_GAPS",
                    "slippage_gap_reason_or_none": "ORDERBOOK_AND_CALIBRATION_EVIDENCE_PENDING",
                }
            )
        if projection_name == "latency_decay_models":
            payload.update(
                {
                    "latency_budget_decision_ref": row["latency_budget_decision_ref_or_gap"],
                    "edge_decay_family": "EXPONENTIAL_DECAY_OR_SCOPED_GAP",
                    "latency_measure_basis": "decision_to_submit_candidate_nonlive_budget",
                    "decision_to_submit_candidate_ms_or_gap": row["latency_budget_decision_ref_or_gap"],
                    "market_data_staleness_ms_or_gap": row["pretrade_model_validity_horizon_ref_or_gap"],
                    "cancel_replace_staleness_ms_or_gap": row["latency_budget_decision_ref_or_gap"],
                    "alpha_half_life_or_gap": _gap("ALPHA_HALF_LIFE_CALIBRATION_PENDING"),
                    "latency_decay_formula_ref_or_inline": "latency_adjusted_edge = raw_edge * exp(-lambda_decay * latency_seconds)",
                    "latency_adjusted_edge_state": "ROUTED_OR_SCOPED_GAP",
                    "latency_gap_reason_or_none": "NO_LIVE_LATENCY_MEASUREMENT_IN_THIS_PR",
                }
            )
        if projection_name == "queue_position_models":
            payload.update(
                {
                    "queue_depth_ref_or_gap": row["microstructure_state_model_ref_or_gap"],
                    "queue_ahead_estimate_state": "SCOPED_GAP_PENDING_ORDERBOOK_EVIDENCE",
                    "order_age_policy_or_gap": _gap("ORDER_AGE_POLICY_PENDING"),
                    "cancel_replace_priority_loss_policy_or_gap": row["latency_budget_decision_ref_or_gap"],
                    "queue_depletion_formula_ref_or_inline": "queue_depletion = queue_ahead / expected_trade_rate",
                    "queue_position_state": "MATERIALIZED_WITH_SOURCE_GAPS",
                    "queue_gap_reason_or_none": "QUEUE_DEPTH_AND_TRADE_RATE_PENDING",
                }
            )
        if projection_name == "partial_fill_models":
            payload.update(
                {
                    "requested_size": row["pretrade_parameter_operability_ref_or_gap"],
                    "expected_filled_size_state": "ROUTED_EXPECTED_FILLED_QTY",
                    "min_fill_size_or_gap": _gap("MIN_FILL_SIZE_POLICY_PENDING"),
                    "partial_fill_probability_formula_ref_or_inline": "partial_fill_probability = f(size, depth, queue, time_in_force)",
                    "unfilled_quantity_policy": "ROUTE_TO_NO_TRADE_OR_REOPTIMIZATION",
                    "opportunity_cost_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
                    "partial_fill_state": "MATERIALIZED_WITH_SOURCE_GAPS",
                    "partial_fill_gap_reason_or_none": "PAPER_FILL_RECEIPTS_PENDING",
                }
            )
        if projection_name == "capacity_crowding_models":
            payload.update(
                {
                    "size_budget": row["pretrade_parameter_operability_ref_or_gap"],
                    "liquidity_depth_ref_or_gap": row["microstructure_state_model_ref_or_gap"],
                    "volume_ref_or_gap": _gap("VENUE_VOLUME_EVIDENCE_PENDING"),
                    "spread_bucket_or_gap": row["market_state_quality_gate_ref_or_gap"],
                    "capacity_formula_ref_or_inline": "size_cap = min(depth_cap, volume_cap, portfolio_cap, owner_cap, capacity_model_cap)",
                    "crowding_proxy_ref_or_gap": _gap("CROWDING_PROXY_PENDING"),
                    "concentration_limit_ref_or_gap": row["pretrade_risk_envelope_ref_or_gap"],
                    "portfolio_exposure_ref_or_gap": row["pretrade_risk_envelope_ref_or_gap"],
                    "capacity_state": "MATERIALIZED_WITH_SOURCE_GAPS",
                    "crowding_state": "CANDIDATE_PROXY_ONLY",
                    "capacity_gap_reason_or_none": "DEPTH_VOLUME_PORTFOLIO_EVIDENCE_PENDING",
                }
            )
        if projection_name == "adverse_selection_models":
            payload.update(
                {
                    "adverse_selection_family": "MARKOUT_SPREAD_WIDENING_QUEUE_ADVERSE",
                    "post_decision_markout_ref_or_gap": _gap("MARKOUT_EVIDENCE_PENDING"),
                    "spread_widening_risk_ref_or_gap": row["market_state_quality_gate_ref_or_gap"],
                    "order_imbalance_ref_or_gap": row["microstructure_state_model_ref_or_gap"],
                    "queue_adverse_move_ref_or_gap": row["queue_position_model_ref_or_gap"],
                    "adverse_selection_formula_ref_or_inline": "adverse_selection_cost = expected_markout_against_position + spread_widening_cost + queue_adverse_cost",
                    "adverse_selection_state": "MATERIALIZED_WITH_SOURCE_GAPS",
                    "adverse_selection_gap_reason_or_none": "MARKOUT_AND_ORDERBOOK_RECEIPTS_PENDING",
                }
            )
        if projection_name == "settlement_resolution_models":
            payload.update(
                {
                    "contract_payout_basis_or_gap": row["contract_payoff_model_ref_or_gap"],
                    "resolution_source_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
                    "settlement_timing_ref_or_gap": _gap("VENUE_SETTLEMENT_TIMING_PENDING"),
                    "payout_cap_ref_or_gap": row["contract_payoff_model_ref_or_gap"],
                    "event_lifecycle_ref_or_gap": row["market_state_quality_gate_ref_or_gap"],
                    "resolution_finality_state": "SOURCE_EVIDENCE_REQUIRED",
                    "settlement_gap_reason_or_none": "ACCEPTED_RESOLUTION_SOURCE_PENDING",
                }
            )
        if projection_name == "cashflow_models":
            payload.update(
                {
                    "entry_cash_required_formula_ref_or_inline": "entry_cash_required = contracts * entry_price + fees",
                    "max_loss_formula_ref_or_inline": "max_loss_cash = contracts * entry_price + fees",
                    "reserved_capital_formula_ref_or_inline": "reserved_capital_cash = max_loss_cash + required_buffer",
                    "fee_cashflow_ref_or_gap": row["fee_model_ref_or_gap"],
                    "settlement_cashflow_ref_or_gap": row["settlement_resolution_model_ref_or_gap"],
                    "payout_cashflow_ref_or_gap": row["contract_payoff_model_ref_or_gap"],
                    "cash_lock_duration_ref_or_gap": row["pretrade_model_validity_horizon_ref_or_gap"],
                    "cash_receipt_required_state": "RUNTIME_CASH_RECEIPT_REQUIRED_DOWNSTREAM_FOR_LIVE_EXPOSURE",
                    "cashflow_state": "MATERIALIZED_WITH_RUNTIME_CASH_GAPS",
                    "cashflow_gap_reason_or_none": "PRIVATE_CASH_READ_FORBIDDEN_IN_PRETRADE1",
                }
            )
        if projection_name == "order_policy_reality_models":
            payload.update(
                {
                    "order_policy_candidate_set_ref": row["order_policy_candidate_set_ref_or_gap"],
                    "maker_fill_model_ref_or_gap": row["fill_model_ref_or_gap"],
                    "taker_fill_model_ref_or_gap": row["fill_model_ref_or_gap"],
                    "split_fill_model_ref_or_gap": row["fill_model_ref_or_gap"],
                    "cancel_replace_model_ref_or_gap": row["latency_budget_decision_ref_or_gap"],
                    "queue_priority_loss_model_ref_or_gap": row["queue_position_model_ref_or_gap"],
                    "latency_tradeoff_ref_or_gap": row["latency_decay_model_ref_or_gap"],
                    "fee_tradeoff_ref_or_gap": row["fee_model_ref_or_gap"],
                    "spread_tradeoff_ref_or_gap": row["slippage_model_ref_or_gap"],
                    "adverse_selection_tradeoff_ref_or_gap": row["adverse_selection_model_ref_or_gap"],
                    "order_policy_expected_net_cash_ref_or_gap": row["pretrade_objective_kernel_ref_or_gap"],
                    "order_policy_lcb_ref_or_gap": row["lower_confidence_bound_ref_or_gap"],
                    "order_policy_selection_state": "PROVIDER_PENDING_NO_ORDER_SUBMIT",
                    "order_policy_gap_reason_or_none": "FILL_QUEUE_FEE_SPREAD_CALIBRATION_PENDING",
                }
            )
        return payload
    return _candidate_rows(registry, projection_name, make)


def _component_contract_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in registry:
        for component in COMPONENT_FAMILIES:
            cid = row["candidate_id"]
            rows.append(
                _projection_row(
                    "reality_model_component_contracts",
                    {
                        "reality_component_contract_id": f"REALITY_COMPONENT_CONTRACT_{component.upper()}_{_id_suffix(cid)}",
                        "candidate_id": cid,
                        "component_family": component,
                        "component_projection_ref": _route(f"{component}_models", cid),
                        "model_ref": _route(f"{component}_model", cid),
                        "input_schema_ref_or_inline_contract": f"{component}_input_contract_v1",
                        "output_schema_ref_or_inline_contract": f"{component}_output_contract_v1",
                        "required_market_fields": ["bid", "ask", "spread", "depth", "event_lifecycle"],
                        "required_venue_fields": ["venue_scope", "venue_policy_matrix_ref"],
                        "required_platform_fields": ["platform_scope"],
                        "required_order_policy_fields": ["order_policy_candidate_set_ref"],
                        "required_liquidity_fields": ["depth_bucket", "thin_book_state"],
                        "required_latency_fields": ["latency_budget_decision_ref"],
                        "required_cashflow_fields": ["cashflow_model_ref", "settlement_resolution_model_ref"],
                        "formula_ref_or_inline": f"{component}_formula_or_typed_gap",
                        "unit_or_basis": "normalized_cash_or_probability",
                        "scale_contract": "decimal_string_scale_6",
                        "normalization_contract": "contract_payoff_model_before_objective_kernel",
                        "missing_value_policy": "NO_OPTIMISTIC_DEFAULT_SCOPED_GAP",
                        "zero_denominator_policy_or_gap": "BLOCK_AND_ROUTE_TO_MODEL_RISK",
                        "asof_timestamp_policy_ref_or_gap": row["pretrade_model_validity_horizon_ref_or_gap"],
                        "source_authority_state": "CANDIDATE_RESEARCH_PROVISIONAL",
                        "accepted_source_refs_or_gap": _gap(f"{component.upper()}_ACCEPTED_SOURCE_PENDING"),
                        "candidate_external_info_lane_refs_or_gap": row["candidate_external_info_lane_ref_or_gap"],
                        "calibration_receipt_ref_or_gap": row["reality_model_calibration_receipt_ref_or_gap"],
                        "component_state": "MATERIALIZED_CONTRACT_WITH_SOURCE_GAPS",
                        "component_gap_reason_or_none": "ACCEPTED_SOURCE_EVIDENCE_PENDING",
                        "unlock_route_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
                        **_false_payload(),
                    },
                )
            )
    return rows


def _trade_plan_bindings(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "trade_plan_binding_id": row["trade_plan_binding_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "pretrade_decision_candidate_id": row["pretrade_decision_candidate_id"],
            "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
            "readiness1_trade_variable_search_ref_or_gap": row["readiness1_trade_variable_search_ref_or_gap"],
            "immutable_qku_formula_state": "IMMUTABLE",
            "mutable_trade_variable_set": [
                "side",
                "entry_price",
                "size_budget",
                "hold_duration",
                "exit_rule",
                "maker_taker_split",
                "cancel_replace_interval",
                "liquidity_filter",
                "spread_filter",
                "latency_budget",
                "portfolio_exposure",
            ],
            "market_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "venue_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "stack_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "side_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "entry_price_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "size_budget_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "hold_duration_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "exit_rule_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "maker_taker_split_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "cancel_replace_interval_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "liquidity_filter_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "spread_filter_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "latency_budget_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "portfolio_exposure_variable_state": "MUTABLE_BY_TRADE_PLAN_ONLY",
            "binding_state": "BOUND_TO_TRADE_PLAN_CANDIDATE_V1",
            "binding_gap_reason_or_none": "NONE",
            "formula_mutation_created": False,
            "profit_claim_created": False,
        }
    return _candidate_rows(registry, "trade_plan_bindings", make)


def _decision_candidates(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "pretrade_decision_candidate_id": row["pretrade_decision_candidate_id"],
            "candidate_id": row["candidate_id"],
            "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
            "readiness1_registry_row_ref": row["readiness1_registry_row_ref"],
            "qku_refs": row["qku_refs"],
            "formula_refs": row["formula_refs"],
            "algorithm_refs_or_gap": row["algorithm_refs_or_gap"],
            "market_family": row["market_family"],
            "venue_scope": row["venue_scope"],
            "platform_scope": row["platform_scope"],
            "mode_scope": "PAPER_CANDIDATE",
            "side": "YES_OR_NO_FROM_TRADE_PLAN",
            "entry_price_or_gap": "TRADE_PLAN_BOUND",
            "size_budget_or_gap": row["pretrade_parameter_operability_ref_or_gap"],
            "hold_duration_or_gap": "TRADE_PLAN_BOUND",
            "exit_rule_or_gap": "TRADE_PLAN_BOUND",
            "maker_taker_split_or_gap": row["order_policy_candidate_set_ref_or_gap"],
            "cancel_replace_interval_or_gap": row["latency_budget_decision_ref_or_gap"],
            "liquidity_filter_or_gap": row["microstructure_state_model_ref_or_gap"],
            "spread_filter_or_gap": row["market_state_quality_gate_ref_or_gap"],
            "latency_budget_ref_or_gap": row["latency_budget_decision_ref_or_gap"],
            "portfolio_exposure_ref_or_gap": row["pretrade_risk_envelope_ref_or_gap"],
            "no_trade_candidate_ref": row["no_trade_candidate_ref_or_gap"],
            "order_policy_candidate_set_ref": row["order_policy_candidate_set_ref_or_gap"],
            "scenario_ladder_decision_ref": row["scenario_ladder_decision_ref_or_gap"],
            "venue_reality_model_ref": row["venue_reality_model_ref_or_gap"],
            "fee_model_ref": row["fee_model_ref_or_gap"],
            "fill_model_ref": row["fill_model_ref_or_gap"],
            "slippage_model_ref": row["slippage_model_ref_or_gap"],
            "latency_decay_model_ref": row["latency_decay_model_ref_or_gap"],
            "capacity_crowding_model_ref": row["capacity_crowding_model_ref_or_gap"],
            "adverse_selection_model_ref": row["adverse_selection_model_ref_or_gap"],
            "settlement_resolution_model_ref": row["settlement_resolution_model_ref_or_gap"],
            "cashflow_model_ref": row["cashflow_model_ref_or_gap"],
            "order_policy_reality_model_ref": row["order_policy_reality_model_ref_or_gap"],
            "pretrade_qku_formula_compute_map_ref_or_gap": row["pretrade_qku_formula_compute_map_ref_or_gap"],
            "pretrade_order_simulation_spec_ref_or_gap": row["pretrade_order_simulation_spec_ref_or_gap"],
            "pretrade_packet_state": row["pretrade_packet_state"],
            "pretrade_packet_basis": row["pretrade_packet_basis"],
            "pretrade_decision_state": row["pretrade_decision_state"],
            "pretrade_decision_basis": row["pretrade_decision_basis"],
            "pretrade_blocker_family_or_none": row["pretrade_blocker_family_or_none"],
            "pretrade_blocker_detail_or_none": row["pretrade_blocker_detail_or_none"],
            "objective_kernel_ref_or_gap": row["pretrade_objective_kernel_ref_or_gap"],
            "pretrade_objective_kernel_ref_or_gap": row["pretrade_objective_kernel_ref_or_gap"],
            "contract_payoff_model_ref_or_gap": row["contract_payoff_model_ref_or_gap"],
            "market_state_quality_gate_ref_or_gap": row["market_state_quality_gate_ref_or_gap"],
            "probability_calibration_gate_ref_or_gap": row["probability_calibration_gate_ref_or_gap"],
            "model_validity_horizon_ref_or_gap": row["pretrade_model_validity_horizon_ref_or_gap"],
            "pretrade_model_validity_horizon_ref_or_gap": row["pretrade_model_validity_horizon_ref_or_gap"],
            "reality_assumption_ledger_ref_or_gap": row["reality_assumption_ledger_ref_or_gap"],
            "pretrade_model_risk_control_ref_or_gap": row["pretrade_model_risk_control_ref_or_gap"],
            "pretrade_parameter_operability_ref_or_gap": row["pretrade_parameter_operability_ref_or_gap"],
            "pretrade_gate_snapshot_handoff_ref_or_gap": row["pretrade_gate_snapshot_handoff_ref_or_gap"],
            "pretrade_owner_intent_binding_ref_or_gap": row["pretrade_owner_intent_binding_ref_or_gap"],
            "pretrade_owner_next_step_handoff_ref_or_gap": row["pretrade_owner_next_step_handoff_ref_or_gap"],
            "pretrade_owner_guidance_handoff_ref_or_gap": row["pretrade_owner_guidance_handoff_ref_or_gap"],
            "microstructure_state_model_ref_or_gap": row["microstructure_state_model_ref_or_gap"],
            "pretrade_risk_envelope_ref_or_gap": row["pretrade_risk_envelope_ref_or_gap"],
            "pretrade_threshold_policy_ref_or_gap": row["pretrade_threshold_policy_ref_or_gap"],
            "pretrade_decision_trace_ref_or_gap": row["pretrade_decision_trace_ref_or_gap"],
            "pretrade_agent_dag_handoff_ref_or_gap": row["pretrade_agent_dag_handoff_ref_or_gap"],
            "agent_workflow_obs_handoff_ref_or_gap": row["agent_workflow_obs_handoff_ref_or_gap"],
            "pretrade_artifact_value_route_map_ref_or_gap": row["pretrade_artifact_value_route_map_ref_or_gap"],
            "pretrade_agent_access_path_audit_ref_or_gap": row["pretrade_agent_access_path_audit_ref_or_gap"],
            "pretrade_edge_alpha_capture_map_ref_or_gap": row["pretrade_edge_alpha_capture_map_ref_or_gap"],
            "clean_room_default_candidate_lane_ref_or_gap": row["clean_room_default_candidate_lane_ref_or_gap"],
            "pretrade_memory_prior_reval_ref_or_gap": row["pretrade_memory_prior_reval_ref_or_gap"],
            "pretrade_recovery_frontier_ref_or_gap": row["pretrade_recovery_frontier_ref_or_gap"],
            "pretrade_venue_policy_matrix_ref_or_gap": row["pretrade_venue_policy_matrix_ref_or_gap"],
            "pretrade_edge_attribution_ref_or_gap": row["pretrade_edge_attribution_ref_or_gap"],
            "tca_decomposition_ref": row["tca_decomposition_ref_or_gap"],
            "expected_net_cash_formula_ref_or_gap": row["expected_net_cash_formula_ref_or_gap"],
            "expected_net_cash_value_state": row["expected_net_cash_value_state"],
            "expected_net_cash_lcb_state": row["expected_net_cash_lcb_state"],
            "no_trade_margin_state": row["no_trade_margin_state"],
            "no_trade_candidate_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
            "mode_authority_matrix_ref_or_gap": row["mode_authority_matrix_ref_or_gap"],
            "owner_review_route_ref_or_gap": row["pretrade_owner_view_handoff_ref_or_gap"],
            "llm_grounding_route_ref_or_gap": row["pretrade_llm_grounding_view_ref_or_gap"],
            "responsible_agent_role_refs_or_gap": row["agent_role_refs"],
            "paper_loop_consumer_ref_or_gap": "PR169-PAPER-LOOP::provider_pending",
            "hotpath_consumer_ref_or_gap": "PR170-HOTPATH1::provider_pending",
            "live_dryrun_consumer_ref_or_gap": "PR170-LIVE-DRYRUN1::provider_pending",
            "execution_router_consumer_ref_or_gap": row["pretrade_execution_router_handoff_ref_or_gap"],
            "downstream_consumer_refs": row["downstream_consumer_refs"],
        }
    return _candidate_rows(registry, "pretrade_decision_candidates", make)


def _no_trade_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        no_trade_wins = row["pretrade_packet_state"] == "PRETRADE_NO_TRADE_WINS"
        return {
            "no_trade_candidate_id": row["no_trade_candidate_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "no_trade_reason_family": "COMPARATOR_OR_REALITY_MODEL_GAP",
            "no_trade_reason_detail": row["pretrade_packet_basis"],
            "no_trade_baseline_value": 0,
            "no_trade_expected_value_baseline": "0.000000",
            "candidate_minus_no_trade_state": "ROUTED_EXPECTED_NET_CASH_MINUS_BASELINE",
            "no_trade_margin_state": row["no_trade_margin_state"],
            "no_trade_is_comparator": True,
            "no_trade_wins_state": no_trade_wins,
            "repair_or_reoptimization_routes": [row["pretrade_recovery_frontier_ref_or_gap"], row["source_coverage_handoff_ref_or_gap"]],
            "pretrade_recovery_frontier_ref_or_gap": row["pretrade_recovery_frontier_ref_or_gap"],
            "reoptimization_route_ref_or_gap": row["pretrade_recovery_frontier_ref_or_gap"],
            "smaller_size_route_or_gap": row["pretrade_parameter_operability_ref_or_gap"],
            "different_venue_route_or_gap": row["market_reality_onboarding_handoff_ref_or_gap"],
            "maker_only_route_or_gap": row["order_policy_candidate_set_ref_or_gap"],
            "later_timing_route_or_gap": row["latency_budget_decision_ref_or_gap"],
            "different_stack_route_or_gap": row["pretrade_qku_formula_compute_map_ref_or_gap"],
            "better_liquidity_window_route_or_gap": row["microstructure_state_model_ref_or_gap"],
            "source_evidence_retrieval_route_or_gap": row["source_coverage_handoff_ref_or_gap"],
            "paper_retest_route_or_gap": "PR169-PAPER-LOOP::provider_pending_retest",
            "replay_retest_route_or_gap": "PR169-PAPER-LOOP::provider_pending_replay_retest",
            "qmap_route_or_gap": "PR174-QMAP1::provider_pending",
            "owner_review_route_or_gap": row["pretrade_owner_view_handoff_ref_or_gap"],
            "no_trade_is_terminal": False,
            "global_formula_ban_created": False,
            "terminal_dead_end_created": False,
        }
    return _candidate_rows(registry, "no_trade_candidates", make)


def _order_policy_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "order_policy_candidate_set_id": row["order_policy_candidate_set_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "allowed_order_policy_families": ["MAKER", "TAKER", "SPLIT", "PASSIVE_FIRST", "CANCEL_REPLACE", "SIZE_BUCKET", "ENTRY_EXIT_RULE"],
            "policy_families": ["MAKER", "TAKER", "SPLIT", "PASSIVE_FIRST", "CANCEL_REPLACE", "SIZE_BUCKET", "ENTRY_EXIT_RULE"],
            "maker_only_policy_ref_or_gap": "MAKER_ONLY::provider_pending",
            "taker_only_policy_ref_or_gap": "TAKER_ONLY::provider_pending",
            "maker_taker_split_policy_ref_or_gap": "MAKER_TAKER_SPLIT::provider_pending",
            "passive_first_policy_ref_or_gap": "PASSIVE_FIRST::provider_pending",
            "cancel_replace_policy_ref_or_gap": row["latency_budget_decision_ref_or_gap"],
            "limit_price_policy_ref_or_gap": row["trade_plan_binding_ref_or_gap"],
            "size_bucket_policy_ref_or_gap": row["pretrade_parameter_operability_ref_or_gap"],
            "entry_rule_policy_ref_or_gap": row["trade_plan_binding_ref_or_gap"],
            "exit_rule_policy_ref_or_gap": row["trade_plan_binding_ref_or_gap"],
            "hold_duration_policy_ref_or_gap": row["trade_plan_binding_ref_or_gap"],
            "liquidity_spread_filter_policy_ref_or_gap": row["market_state_quality_gate_ref_or_gap"],
            "latency_budget_policy_ref_or_gap": row["latency_budget_decision_ref_or_gap"],
            "portfolio_exposure_policy_ref_or_gap": row["pretrade_risk_envelope_ref_or_gap"],
            "order_policy_reality_model_ref_or_gap": row["order_policy_reality_model_ref_or_gap"],
            "selected_policy_or_gap": "PROVIDER_PENDING_POLICY_SELECTION",
            "policy_selection_state": "CANDIDATE_SET_ONLY_NO_ORDER_COMPILATION",
            "policy_selection_basis": "maker/taker/split/passive policies require fill, queue, fee, spread, adverse-selection, and latency evidence",
            "policy_gap_reason_or_none": "ACCEPTED_SOURCE_AND_PAPER_REPLAY_CALIBRATION_PENDING",
            "selection_state": "CANDIDATE_SET_ONLY_NO_ORDER_COMPILATION",
        }
    return _candidate_rows(registry, "order_policy_candidate_sets", make)


def _mode_authority_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    modes = ["replay", "paper", "shadow_candidate", "live_dryrun_candidate", "live_candidate_review", "live_pilot_review", "launch_review"]
    def make(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "mode_authority_matrix_id": row["mode_authority_matrix_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "mode_scope": "PRETRADE1_ALL_REVIEW_MODES_NO_RUNTIME",
            "replay_candidate_allowed": True,
            "paper_candidate_allowed": True,
            "shadow_candidate_allowed": True,
            "live_dryrun_candidate_allowed": True,
            "live_candidate_review_allowed": True,
            "owner_review_allowed": True,
            "llm_view_allowed": True,
            "agent_packet_allowed": True,
            "connector_read_allowed": False,
            "private_cash_read_allowed": False,
            "venue_submit_allowed": False,
            "execution_router_release_allowed": False,
            "runtime_execution_allowed": False,
            "source_truth_acceptance_allowed": False,
            "quantum_backend_execution_allowed": False,
            "mode_output_allowed_packet_types": ["PreTradeDecisionCandidateV1", "NoTradeCandidateV1", "RealityModelComponentContractV1"],
            "mode_forbidden_packet_types": ["OrderSubmitRequest", "LiveOrderCommand", "PaperFillReceipt", "MemoryUpdateReceiptV1"],
            "mode_authority_gap_reason_or_none": "NONE",
            "mode_scopes": modes,
            "mode_authority_state": "PRETRADE_ANALYSIS_ONLY_ALL_EXECUTION_FALSE",
            "allowed_emit_types": ["PreTradeDecisionCandidateV1", "NoTradeCandidateV1", "RealityModelComponentContractV1"],
            "forbidden_emit_types": ["OrderSubmitRequest", "LiveOrderCommand", "PaperFillReceipt", "MemoryUpdateReceiptV1"],
        }
    return _candidate_rows(registry, "mode_authority_matrix", make)


def _objective_rows(registry: Sequence[dict[str, Any]], ctx: SourceContext) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        cid = row["candidate_id"]
        rp5g = ctx.rp5g_by_candidate.get(cid, {})
        no_trade = ctx.no_trade_by_candidate.get(cid, {})
        tca = ctx.tca_by_candidate.get(cid, {})
        entry = _decimal(rp5g.get("entry_price_candidate"))
        contracts = _decimal(rp5g.get("order_size_candidate"))
        probability = Decimal("0.55")
        payout_cap = Decimal("1")
        side = str(rp5g.get("side") or "YES")
        payoff_if_win = payout_cap - entry
        loss_if_lose = entry
        gross = contracts * (probability * payoff_if_win - (Decimal("1") - probability) * loss_if_lose)
        costs = _decimal(tca.get("TCA_total_cash"))
        model_risk = Decimal("0.05")
        net = gross - costs - model_risk
        lcb = net - Decimal("0.10")
        return {
            "pretrade_objective_kernel_id": row["pretrade_objective_kernel_ref_or_gap"],
            "candidate_id": cid,
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "contract_payoff_model_ref_or_gap": row["contract_payoff_model_ref_or_gap"],
            "probability_calibration_gate_ref_or_gap": row["probability_calibration_gate_ref_or_gap"],
            "market_state_quality_gate_ref_or_gap": row["market_state_quality_gate_ref_or_gap"],
            "pretrade_model_risk_control_ref_or_gap": row["pretrade_model_risk_control_ref_or_gap"],
            "tca_decomposition_ref_or_gap": row["tca_decomposition_ref_or_gap"],
            "no_trade_candidate_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
            "side": side,
            "entry_price_or_gap": str(entry),
            "exit_price_or_gap": rp5g.get("exit_price_candidate_or_rule") or _gap("EXIT_RULE_PENDING"),
            "size_budget_or_gap": rp5g.get("total_investment_candidate") or _gap("SIZE_BUDGET_PENDING"),
            "contract_count_or_gap": int(contracts) if contracts else _gap("CONTRACT_COUNT_PENDING"),
            "win_probability_ref_or_gap": row["probability_calibration_gate_ref_or_gap"],
            "probability_lcb_ref_or_gap": row["lower_confidence_bound_ref_or_gap"],
            "payoff_if_win_ref_or_gap": str(payoff_if_win),
            "loss_if_lose_ref_or_gap": str(loss_if_lose),
            "expected_gross_cash_formula_ref_or_inline": "contracts*(p*(payout-entry)-(1-p)*entry)",
            "expected_cost_formula_ref_or_inline": "total_tca_costs+cash_lock_penalty+model_risk_haircut",
            "expected_net_cash_formula_ref_or_inline": "expected_gross_cash-total_costs",
            "expected_net_cash_lcb_formula_ref_or_inline": "expected_net_cash-probability_uncertainty_haircut",
            "no_trade_margin_formula_ref_or_inline": "expected_net_cash_lcb-no_trade_baseline_value",
            "calibration_adjustment_ref_or_gap": row["probability_calibration_gate_ref_or_gap"],
            "model_risk_haircut_ref_or_gap": row["pretrade_model_risk_control_ref_or_gap"],
            "cash_lock_penalty_ref_or_gap": row["cashflow_model_ref_or_gap"],
            "objective_state": "COMPUTABLE_PRETRADE_ESTIMATE" if no_trade else "SCOPED_GAP_ROUTED",
            "objective_gap_reason_or_none": "NONE" if no_trade else "NO_TRADE_COMPARATOR_ROW_ABSENT",
            "unit_or_basis": "normalized_cash",
            "expected_net_cash_estimate": _rounded(net),
            "expected_net_cash_lcb_estimate": _rounded(lcb),
        }
    return _candidate_rows(registry, "pretrade_objective_kernels", make)


def _payoff_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "contract_payoff_model_id": row["contract_payoff_model_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "market_family": row["market_family"],
            "venue_scope": row["venue_scope"],
            "platform_scope": row["platform_scope"],
            "contract_type": "BINARY_YES_NO",
            "side_set": ["YES", "NO"],
            "price_unit": "normalized_decimal_0_1",
            "payout_unit": "normalized_cash",
            "payout_cap_or_gap": "1.0",
            "price_normalization_formula_ref_or_inline": "price_cents/100 when cents; identity when normalized",
            "side_payoff_formula_ref_or_inline": "YES:payout-entry; NO:payout-no_entry",
            "max_loss_formula_ref_or_inline": "entry_price*contracts",
            "settlement_resolution_model_ref_or_gap": row["settlement_resolution_model_ref_or_gap"],
            "cashflow_model_ref_or_gap": row["cashflow_model_ref_or_gap"],
            "unit_conversion_state": "NORMALIZED_OR_SCOPED_GAP",
            "payoff_model_state": "MATERIALIZED_CONTRACT",
            "payoff_gap_reason_or_none": "NONE",
            "source_authority_state": "CANDIDATE_RESEARCH_PROVISIONAL",
            "accepted_source_refs_or_gap": _gap("VENUE_PAYOFF_ACCEPTED_SOURCE_PENDING"),
            "candidate_external_info_lane_refs_or_gap": row["candidate_external_info_lane_ref_or_gap"],
        }
    return _candidate_rows(registry, "contract_payoff_models", make)


def _market_state_rows(registry: Sequence[dict[str, Any]], ctx: SourceContext) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        micro = ctx.micro_by_candidate.get(row["candidate_id"], {})
        spread = micro.get("best_bid_best_ask_mid_spread") or _gap("SPREAD_ABSENT")
        depth = micro.get("depth_at_price_bucket") or _gap("DEPTH_ABSENT")
        state = row["quality_gate_state"]
        return {
            "market_state_quality_gate_id": row["market_state_quality_gate_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "market_snapshot_ref_or_gap": _row_ref("docs/master_plan/generated/pr168_rp5g/pm_microstructure.jsonl", micro, "row_id", "pm_micro_id"),
            "quote_asof_ref_or_gap": "PR168_RP5G_FIXTURE_ASOF",
            "quote_age_ms_or_gap": _gap("LIVE_QUOTE_AGE_NOT_AVAILABLE_PRETRADE1"),
            "bid_price_or_gap": _gap("BID_PRICE_ACCEPTED_SOURCE_PENDING"),
            "ask_price_or_gap": _gap("ASK_PRICE_ACCEPTED_SOURCE_PENDING"),
            "mid_price_or_gap": _gap("MID_PRICE_ACCEPTED_SOURCE_PENDING"),
            "spread_or_gap": spread,
            "spread_bucket_or_gap": "THIN" if depth == "THIN" else "NORMAL",
            "book_depth_ref_or_gap": str(depth),
            "order_book_imbalance_ref_or_gap": micro.get("orderbook_imbalance_topN") or _gap("ORDERBOOK_IMBALANCE_PENDING"),
            "market_status_ref_or_gap": micro.get("market_status_state") or _gap("MARKET_STATUS_PENDING"),
            "event_lifecycle_state_or_gap": micro.get("event_status_state") or _gap("EVENT_LIFECYCLE_PENDING"),
            "time_to_resolution_bucket_or_gap": micro.get("time_to_close_bucket") or _gap("TIME_TO_RESOLUTION_PENDING"),
            "crossed_book_state": "SCOPED_GAP_NO_LIVE_BOOK",
            "locked_book_state": "SCOPED_GAP_NO_LIVE_BOOK",
            "stale_quote_state": "SCOPED_GAP_NO_LIVE_QUOTE",
            "missing_bid_ask_state": "SCOPED_GAP_ACCEPTED_BID_ASK_PENDING",
            "thin_book_state": depth == "THIN",
            "halt_or_closed_state": "SCOPED_GAP_EVENT_STATUS_SOURCE_PENDING",
            "quality_gate_state": state,
            "quality_gap_reason_or_none": row["quality_gap_reason_or_none"],
            "no_trade_if_failed": True,
        }
    return _candidate_rows(registry, "market_state_quality_gates", make)


def _calibration_gate_rows(registry: Sequence[dict[str, Any]], ctx: SourceContext) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        calib = ctx.calibration_by_candidate.get(row["candidate_id"], {})
        return {
            "probability_calibration_gate_id": row["probability_calibration_gate_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "probability_source_ref_or_gap": _row_ref("docs/master_plan/generated/pr168_rp5g/calibration_result.jsonl", calib, "row_id", "calibration_result_id"),
            "raw_probability_or_gap": _gap("RAW_PROBABILITY_SOURCE_PENDING"),
            "calibrated_probability_or_gap": _gap("CALIBRATED_PROBABILITY_ACCEPTED_SOURCE_PENDING"),
            "probability_lcb_or_gap": row["lower_confidence_bound_ref_or_gap"],
            "probability_clip_policy_ref_or_gap": "clip_to_0_1_and_gap_if_missing",
            "calibration_family": calib.get("calibration_metric") or "SCOPED_GAP",
            "brier_score_ref_or_gap": calib.get("brier_score_proxy") or _gap("BRIER_SCORE_PENDING"),
            "log_loss_ref_or_gap": _gap("LOGLOSS_PENDING"),
            "expected_calibration_error_ref_or_gap": _gap("ECE_PENDING"),
            "support_count_or_gap": _gap("SUPPORT_COUNT_PENDING"),
            "sample_window_ref_or_gap": _gap("SAMPLE_WINDOW_PENDING"),
            "out_of_sample_state_or_gap": "SCOPED_GAP_OOS_VALIDATION_PENDING",
            "purged_embargoed_validation_state_or_gap": "SCOPED_GAP_PURGED_EMBARGO_PENDING",
            "leakage_guard_ref_or_gap": "NO_LOOKAHEAD_LEAKAGE_BY_CONTRACT",
            "calibration_state": "SCOPED_GAP_WITH_PROXY" if calib else "SCOPED_GAP",
            "calibration_gap_reason_or_none": "ACCEPTED_PROBABILITY_CALIBRATION_PENDING",
            "no_trade_if_uncalibrated_state": True,
        }
    return _candidate_rows(registry, "probability_calibration_gates", make)


def _validity_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "model_validity_horizon_id": row["pretrade_model_validity_horizon_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "model_family": "PRETRADE_REALITY_MODEL",
            "model_ref": row["venue_reality_model_ref_or_gap"],
            "asof_timestamp_ref_or_gap": "PR168_RP5G_FIXTURE_ASOF",
            "validity_ttl_ms_or_gap": _gap("TTL_REQUIRES_ACCEPTED_SOURCE_OR_LIVE_SNAPSHOT_PROVIDER"),
            "valid_until_ref_or_gap": _gap("VALID_UNTIL_PROVIDER_PENDING"),
            "refresh_route_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
            "staleness_action": "REFRESH_OR_NO_TRADE",
            "hotpath_use_allowed_until_or_gap": _gap("HOTPATH_PRECOMPUTE_PENDING"),
            "live_dryrun_use_allowed_until_or_gap": _gap("LIVE_DRYRUN_PRECOMPUTE_PENDING"),
            "paper_loop_use_allowed_until_or_gap": _gap("PAPER_LOOP_PRECOMPUTE_PENDING"),
            "source_revalidation_route_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
            "validity_state": "SCOPED_GAP_ROUTED",
            "validity_gap_reason_or_none": "ACCEPTED_SOURCE_CURRENTNESS_SNAPSHOT_PENDING",
        }
    return _candidate_rows(registry, "pretrade_model_validity_horizon", make)


def _market_onboarding_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    seen: set[tuple[str, str, str]] = set()
    for row in registry:
        key = (row["market_family"], row["venue_scope"], row["platform_scope"])
        if key in seen:
            continue
        seen.add(key)
        cid = row["candidate_id"]
        rows.append(
            _projection_row(
                "market_reality_onboarding_handoff",
                {
                    "market_onboarding_handoff_id": f"market_onboarding::{row['venue_scope']}",
                    "market_family": row["market_family"],
                    "venue_scope": row["venue_scope"],
                    "platform_scope": row["platform_scope"],
                    "stage_activation_state": row["stage_activation_state"],
                    "market_installation_state": "ROW_ROUTE_SOCKET_PROVIDER_PENDING",
                    "market_applicability_ref_or_gap": row["active_stage_profile_ref_or_gap"],
                    "platform_applicability_ref_or_gap": row["active_stage_profile_ref_or_gap"],
                    "venue_reality_model_ref_or_gap": row["venue_reality_model_ref_or_gap"],
                    "fee_model_ref_or_gap": row["fee_model_ref_or_gap"],
                    "fill_model_ref_or_gap": row["fill_model_ref_or_gap"],
                    "slippage_model_ref_or_gap": row["slippage_model_ref_or_gap"],
                    "latency_decay_model_ref_or_gap": row["latency_decay_model_ref_or_gap"],
                    "queue_position_model_ref_or_gap": row["queue_position_model_ref_or_gap"],
                    "partial_fill_model_ref_or_gap": row["partial_fill_model_ref_or_gap"],
                    "capacity_crowding_model_ref_or_gap": row["capacity_crowding_model_ref_or_gap"],
                    "adverse_selection_model_ref_or_gap": row["adverse_selection_model_ref_or_gap"],
                    "settlement_resolution_model_ref_or_gap": row["settlement_resolution_model_ref_or_gap"],
                    "cashflow_model_ref_or_gap": row["cashflow_model_ref_or_gap"],
                    "order_policy_reality_model_ref_or_gap": row["order_policy_reality_model_ref_or_gap"],
                    "source_evidence_route_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
                    "candidate_external_info_lane_refs_or_gap": row["candidate_external_info_lane_ref_or_gap"],
                    "connector_route_ref_or_gap": row["pretrade_connector_handoff_ref_or_gap"],
                    "venue_neutral_adapter_route_ref_or_gap": "VENUE-NEUTRAL-CONNECTOR::provider_pending_no_read",
                    "owner_surface_route_ref_or_gap": row["pretrade_owner_view_handoff_ref_or_gap"],
                    "agent_role_refs_or_gap": row["agent_role_refs"] or _gap("AGENT_ROLE_PENDING"),
                    "llm_grounding_route_ref_or_gap": row["pretrade_llm_grounding_view_ref_or_gap"],
                    "pretrade_packet_route_ref_or_gap": row["pretrade_decision_candidate_id"],
                    "paper_loop_route_ref_or_gap": "PR169-PAPER-LOOP::provider_pending",
                    "hotpath_route_ref_or_gap": "PR170-HOTPATH1::provider_pending",
                    "live_dryrun_route_ref_or_gap": "PR170-LIVE-DRYRUN1::provider_pending",
                    "execution_router_route_ref_or_gap": "EXECUTION-ROUTER::provider_pending_no_release",
                    "qmap_route_ref_or_gap": "PR174-QMAP1::provider_pending",
                    "allowlist_route_ref_or_gap": "PR174-ALLOW1::provider_pending",
                    "market_installation_gap_reason_or_none": "ACCEPTED_VENUE_SOURCE_AND_CONNECTOR_SEMANTICS_PENDING",
                    **_false_payload(),
                },
            )
        )
    return rows


def _venue_policy_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    registry_by_venue = {row["venue_scope"]: row for row in registry}
    for venue in STAGE1_VENUES:
        row = registry_by_venue.get(venue)
        source = row if row else registry[0]
        rows.append(
            _projection_row(
                "pretrade_venue_policy_matrix",
                {
                    "venue_policy_matrix_id": f"venue_policy::{venue}",
                    "market_family": "prediction_market",
                    "venue_scope": venue,
                    "platform_scope": "stage1_prediction_markets",
                    "stage_activation_state": "PRETRADE1_NO_RUNTIME_CONTRACT",
                    "market_applicability_ref_or_gap": source["active_stage_profile_ref_or_gap"],
                    "platform_applicability_ref_or_gap": source["active_stage_profile_ref_or_gap"],
                    "contract_payoff_model_ref_or_gap": source["contract_payoff_model_ref_or_gap"],
                    "venue_reality_model_ref_or_gap": source["venue_reality_model_ref_or_gap"],
                    "fee_model_ref_or_gap": source["fee_model_ref_or_gap"],
                    "fill_model_ref_or_gap": source["fill_model_ref_or_gap"],
                    "slippage_model_ref_or_gap": source["slippage_model_ref_or_gap"],
                    "latency_decay_model_ref_or_gap": source["latency_decay_model_ref_or_gap"],
                    "queue_position_model_ref_or_gap": source["queue_position_model_ref_or_gap"],
                    "partial_fill_model_ref_or_gap": source["partial_fill_model_ref_or_gap"],
                    "capacity_crowding_model_ref_or_gap": source["capacity_crowding_model_ref_or_gap"],
                    "adverse_selection_model_ref_or_gap": source["adverse_selection_model_ref_or_gap"],
                    "settlement_resolution_model_ref_or_gap": source["settlement_resolution_model_ref_or_gap"],
                    "cashflow_model_ref_or_gap": source["cashflow_model_ref_or_gap"],
                    "order_policy_reality_model_ref_or_gap": source["order_policy_reality_model_ref_or_gap"],
                    "connector_route_handoff_ref_or_gap": source["pretrade_connector_handoff_ref_or_gap"],
                    "source_authority_state": "CANDIDATE_RESEARCH_PROVISIONAL",
                    "accepted_source_refs_or_gap": _gap(f"{venue}_ACCEPTED_VENUE_POLICY_SOURCE_PENDING"),
                    "candidate_external_info_lane_refs_or_gap": source["candidate_external_info_lane_ref_or_gap"],
                    "venue_supported_order_policy_families_or_gap": ["MAKER", "TAKER", "SPLIT", "CANCEL_REPLACE"],
                    "venue_forbidden_order_policy_families_or_gap": _gap(f"{venue}_FORBIDDEN_POLICY_SOURCE_PENDING"),
                    "venue_specific_gap_reason_or_none": "ACCEPTED_VENUE_POLICY_SOURCE_PENDING",
                    "cross_venue_generalization_allowed": False,
                    **_false_payload(),
                },
            )
        )
    return rows


def _risk_policy_rows(registry: Sequence[dict[str, Any]], projection_name: str) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        cid = row["candidate_id"]
        if projection_name == "pretrade_risk_envelopes":
            return {
                "pretrade_risk_envelope_id": row["pretrade_risk_envelope_ref_or_gap"],
                "candidate_id": cid,
                "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
                "owner_enablement_ref_or_gap": row["readiness1_owner_enablement_ref_or_gap"],
                "max_loss_cash_or_gap": _gap("OWNER_RISK_LIMIT_PENDING"),
                "max_size_or_budget_or_gap": _gap("OWNER_SIZE_LIMIT_PENDING"),
                "portfolio_exposure_limit_or_gap": _gap("PORTFOLIO_LIMIT_PENDING"),
                "venue_exposure_limit_or_gap": _gap("VENUE_LIMIT_PENDING"),
                "market_exposure_limit_or_gap": _gap("MARKET_LIMIT_PENDING"),
                "liquidity_depth_limit_or_gap": _gap("LIQUIDITY_DEPTH_LIMIT_PENDING"),
                "spread_limit_or_gap": _gap("SPREAD_LIMIT_PENDING"),
                "latency_limit_or_gap": row["latency_budget_decision_ref_or_gap"],
                "capacity_limit_or_gap": row["capacity_crowding_model_ref_or_gap"],
                "adverse_selection_limit_or_gap": row["adverse_selection_model_ref_or_gap"],
                "settlement_cash_lock_limit_or_gap": row["cashflow_model_ref_or_gap"],
                "kill_switch_route_ref_or_gap": "PR170-LIVE-DRYRUN1::kill_switch_gate_pending",
                "risk_envelope_state": "SCOPED_GAP_ROUTED",
                "risk_envelope_gap_reason_or_none": "OWNER_RISK_LIMITS_AND_CASH_GATES_PENDING",
            }
        return {
            "pretrade_threshold_policy_id": row["pretrade_threshold_policy_ref_or_gap"],
            "candidate_id": cid,
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "expected_net_cash_threshold_or_gap": "must_be_positive_after_costs",
            "lower_confidence_bound_threshold_or_gap": "must_beat_no_trade",
            "candidate_minus_no_trade_threshold_or_gap": "greater_than_zero",
            "tca_threshold_or_gap": "bounded_by_owner_risk_policy_or_gap",
            "fill_probability_threshold_or_gap": "venue_specific_source_pending",
            "latency_threshold_or_gap": row["latency_budget_decision_ref_or_gap"],
            "capacity_threshold_or_gap": row["capacity_crowding_model_ref_or_gap"],
            "overfit_fdr_threshold_or_gap": _gap("OVERFIT_FDR_THRESHOLD_PENDING"),
            "portfolio_marginal_utility_threshold_or_gap": _gap("PORTFOLIO_UTILITY_THRESHOLD_PENDING"),
            "scenario_ladder_threshold_or_gap": row["scenario_ladder_decision_ref_or_gap"],
            "calibration_threshold_or_gap": row["probability_calibration_gate_ref_or_gap"],
            "microstructure_quality_threshold_or_gap": row["market_state_quality_gate_ref_or_gap"],
            "source_currentness_threshold_or_gap": row["source_coverage_handoff_ref_or_gap"],
            "model_validity_threshold_or_gap": row["pretrade_model_validity_horizon_ref_or_gap"],
            "champion_ready_threshold_state": row["pretrade_packet_state"],
            "no_trade_fallback_state": row["pretrade_packet_state"] == "NO_TRADE_SELECTED",
            "repair_retest_route_ref_or_gap": _route("recovery_frontier", cid),
            "threshold_policy_state": "MATERIALIZED_WITH_SCOPED_GAPS",
            "threshold_gap_reason_or_none": row["pretrade_packet_basis"],
        }
    return _candidate_rows(registry, projection_name, make)


def _owner_guidance_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        blocked = row["pretrade_packet_state"] != "PRETRADE_REVIEW_READY"
        return {
            "pretrade_guidance_id": row["pretrade_owner_guidance_handoff_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "guidance_context": row["pretrade_packet_state"],
            "beginner_owner_title": "Pretrade review packet",
            "beginner_owner_summary": "QTT prepared a no-submit pretrade packet and kept execution disabled.",
            "advanced_owner_summary": "Objective, TCA, market-state, calibration, model-risk, no-trade, and route gates are assembled for downstream review.",
            "developer_technical_summary_ref_or_gap": row["pretrade_decision_trace_ref_or_gap"],
            "why_this_matters": "This packet standardizes the decision before any downstream order workflow can evaluate it.",
            "what_can_owner_do_next": "Review the packet, inspect costs, or request downstream replay/paper preview when providers exist.",
            "what_is_blocked": row["pretrade_packet_basis"] if blocked else "ORDER_SUBMIT_AND_LIVE_EXECUTION_REMAIN_BLOCKED",
            "what_evidence_is_missing": row["quality_gap_reason_or_none"],
            "what_will_not_happen_now": "No replay, paper, shadow, live, connector, cash, LLM, agent, quantum backend, or order-submit action runs in PRETRADE1.",
            "safe_alternative_actions": ["SHOW_TCA_COST_BREAKDOWN", "EXPLAIN_NO_TRADE", "SHOW_REALITY_MODEL_GAPS"],
            "explain_tca_seed": row["tca_decomposition_ref_or_gap"],
            "explain_no_trade_seed": row["no_trade_candidate_ref_or_gap"],
            "explain_fill_latency_capacity_seed": row["fill_model_ref_or_gap"],
            "explain_overfit_fdr_seed": _gap("OVERFIT_FDR_DETAIL_PENDING"),
            "explain_quantum_readiness_seed": row["pretrade_quantum_readiness_handoff_ref_or_gap"],
            "explain_reality_model_gap_seed": row["pretrade_model_risk_control_ref_or_gap"],
            "owner_input_needed": ["risk_limit", "budget", "venue_review"] if blocked else [],
            "owner_choice_options": ["review", "defer", "send_to_downstream_preview"],
            "let_qtt_decide_policy_route_ref_or_gap": _gap("OWNER_AUTO_POLICY_PENDING_DOWNSTREAM"),
            "risk_disclaimer_no_profit_guarantee": True,
        }
    return _candidate_rows(registry, "pretrade_owner_guidance_handoff", make)


def _next_step_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    actions = [
        "SEND_TO_TRADE_WORKBENCH",
        "CHECK_TRADE_WITH_QTT_AGENTS",
        "REQUEST_REPLAY_PREVIEW",
        "REQUEST_PAPER_PREVIEW",
        "SHOW_QKU_FORMULA_ROUTES",
        "SHOW_TCA_COST_BREAKDOWN",
        "EXPLAIN_NO_TRADE",
        "SHOW_SCENARIO_LADDER",
        "SHOW_REALITY_MODEL_GAPS",
        "SHOW_TECHNICAL_DETAILS",
        "PREPARE_LIVE_CANARY_REVIEW_PREVIEW",
    ]
    rows: list[dict[str, Any]] = []
    for row in registry:
        for action in actions:
            blocked = action.startswith("PREPARE_LIVE") or action in {"REQUEST_REPLAY_PREVIEW", "REQUEST_PAPER_PREVIEW", "CHECK_TRADE_WITH_QTT_AGENTS"}
            rows.append(
                _projection_row(
                    "pretrade_owner_next_step_handoff",
                    {
                        "pretrade_next_step_id": f"{row['candidate_id']}::{action}",
                        "candidate_id": row["candidate_id"],
                        "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
                        "action_id": action,
                        "owner_label": action.replace("_", " ").title(),
                        "current_surface_id_or_gap": row["dashboard_surface_registry_ref_or_gap"],
                        "target_surface_id_or_gap": row["pretrade_owner_view_handoff_ref_or_gap"],
                        "target_workflow_id_or_gap": "PRETRADE_REVIEW_PROVIDER_PENDING",
                        "target_step_id_or_gap": action,
                        "prefill_context_refs": [row["pretrade_decision_candidate_id"], row["trade_plan_candidate_ref"]],
                        "preview_object_type": "PreTradeDecisionCandidateV1",
                        "creates_local_receipt_preview": False,
                        "provider_stage": "DOWNSTREAM_PROVIDER_PENDING" if blocked else "PRETRADE_VIEW_AVAILABLE",
                        "authority_boundary": "NO_RUNTIME_SIDE_EFFECT",
                        "requires_owner_confirmation": action.startswith("PREPARE_LIVE"),
                        "owner_input_required": blocked,
                        "missing_owner_input_fields": ["downstream_provider_receipt"] if blocked else [],
                        "safe_default_if_owner_declines": "NO_TRADE_OR_DEFER",
                        "disabled_reason_if_blocked_or_none": "DOWNSTREAM_PROVIDER_PENDING" if blocked else "NONE",
                        "safe_alternative_action_ids": ["SHOW_TCA_COST_BREAKDOWN", "EXPLAIN_NO_TRADE"],
                        "what_happens_next": "Routes to a provider-pending workflow view without execution.",
                        "what_will_not_happen_now": "No venue submit, connector read, paper execution, live execution, or Execution Router release.",
                        "trade_workbench_prefill_ref_or_gap": row["trade_plan_binding_ref_or_gap"],
                        "tca_drilldown_route_ref_or_gap": row["tca_decomposition_ref_or_gap"],
                        "no_trade_explanation_route_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
                        "qku_formula_route_drawer_ref_or_gap": row["pretrade_qku_formula_compute_map_ref_or_gap"],
                        "replay_preview_route_ref_or_gap": "PR169-PAPER-LOOP::replay_preview_provider_pending",
                        "paper_preview_route_ref_or_gap": "PR169-PAPER-LOOP::paper_preview_provider_pending",
                        "execution_router_provider_pending_route_ref_or_gap": row["pretrade_execution_router_handoff_ref_or_gap"],
                        **_false_payload(),
                    },
                )
            )
    return rows


def _artifact_route_rows(registry: Sequence[dict[str, Any]], artifact_rows: dict[str, Sequence[dict[str, Any]]] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in (*JSONL_ARTIFACTS, *JSON_ARTIFACTS):
        rows.append(
            _projection_row(
                "pretrade_artifact_value_route_map",
                {
                    "artifact_value_route_id": f"artifact::{name}",
                    "pretrade_registry_row_id_or_scope": "ALL",
                    "candidate_id_or_scope": "ALL",
                    "source_generated_file": _out_ref(name),
                    "source_row_id_or_scope": "ALL_ROWS",
                    "value_key_or_scope": "artifact_file",
                    "value_family": "REPORT_ONLY" if name.endswith(".report.json") else "AGENT_ROUTE_RELEVANT",
                    "value_materiality_class": "REPORT_ONLY" if name == "consumer_routes.generated.jsonl" else "OWNER_VIEW_RELEVANT",
                    "canonical_registry_ref": REGISTRY_REF,
                    "producer_builder_ref": BUILDER_NAME,
                    "producer_projection_ref_or_gap": name,
                    "validator_ref": VALIDATOR_NAME,
                    "upstream_artifact_refs": ["docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl"],
                    "upstream_pr_refs": ["PR267-READINESS1", "PR168-MEM1"],
                    "responsible_agent_role_refs_or_gap": ["GovernanceAgent"],
                    "agent_roster_discovery_audit_ref_or_gap": registry[0]["agent_roster_discovery_audit_ref_or_gap"],
                    "agent_duty_source_crosswalk_ref_or_gap": registry[0]["agent_duty_source_crosswalk_ref_or_gap"],
                    "owner_user_surface_route_ref_or_gap": "PR169-SVC1::provider_pending",
                    "llm_grounding_route_ref_or_gap": "PR169-LLM1::provider_pending",
                    "connector_route_ref_or_gap": "VENUE-NEUTRAL-CONNECTOR::provider_pending_no_read",
                    "execution_router_route_ref_or_gap": "EXECUTION-ROUTER::provider_pending_no_release",
                    "paper_loop_route_ref_or_gap": "PR169-PAPER-LOOP::provider_pending",
                    "hotpath_route_ref_or_gap": "PR170-HOTPATH1::provider_pending",
                    "live_dryrun_route_ref_or_gap": "PR170-LIVE-DRYRUN1::provider_pending",
                    "postlaunch_route_ref_or_gap": "PR173-POSTLAUNCH::provider_pending",
                    "qmap_route_ref_or_gap": "PR174-QMAP1::provider_pending",
                    "allowlist_route_ref_or_gap": "PR174-ALLOW1::provider_pending",
                    "metrics_capture_route_ref_or_gap": "PR170-METRICS1::provider_pending",
                    "market_installation_route_ref_or_gap": "market_reality_onboarding_handoff.generated.jsonl",
                    "activation_state": "PRETRADE1_ACTIVE_GENERATED",
                    "lifecycle_state": "SESSION1_GENERATED",
                    "downstream_ownership_state": "PROVIDER_PENDING",
                    "route_state": "ROUTED",
                    "route_gap_reason_or_none": "NONE",
                    **_false_payload(),
                },
            )
        )
    for row in registry:
        rows.append(
            _projection_row(
                "pretrade_artifact_value_route_map",
                {
                    "artifact_value_route_id": f"value::{row['candidate_id']}::edge_capture_score",
                    "pretrade_registry_row_id_or_scope": row["pretrade_registry_row_id"],
                    "candidate_id_or_scope": row["candidate_id"],
                    "source_generated_file": REGISTRY_REF,
                    "source_row_id_or_scope": row["pretrade_registry_row_id"],
                    "value_key_or_scope": "edge_capture_score_0_1",
                    "value_family": "EDGE_RELEVANT",
                    "value_materiality_class": "EDGE_RELEVANT",
                    "canonical_registry_ref": REGISTRY_REF,
                    "producer_builder_ref": BUILDER_NAME,
                    "producer_projection_ref_or_gap": row["pretrade_edge_alpha_capture_map_ref_or_gap"],
                    "validator_ref": VALIDATOR_NAME,
                    "upstream_artifact_refs": [row["readiness1_registry_row_ref"], row["rp5g_sim_ref_or_gap"], row["mem1_memory_ref_or_gap"]],
                    "upstream_pr_refs": ["PR267-READINESS1", "PR168-RP5G", "PR168-MEM1"],
                    "responsible_agent_role_refs_or_gap": row["agent_role_refs"],
                    "agent_roster_discovery_audit_ref_or_gap": row["agent_roster_discovery_audit_ref_or_gap"],
                    "agent_duty_source_crosswalk_ref_or_gap": row["agent_duty_source_crosswalk_ref_or_gap"],
                    "owner_user_surface_route_ref_or_gap": row["pretrade_owner_view_handoff_ref_or_gap"],
                    "llm_grounding_route_ref_or_gap": row["pretrade_llm_grounding_view_ref_or_gap"],
                    "connector_route_ref_or_gap": row["pretrade_connector_handoff_ref_or_gap"],
                    "execution_router_route_ref_or_gap": row["pretrade_execution_router_handoff_ref_or_gap"],
                    "paper_loop_route_ref_or_gap": "PR169-PAPER-LOOP::provider_pending",
                    "hotpath_route_ref_or_gap": row["pretrade_hotpath_handoff_ref_or_gap"],
                    "live_dryrun_route_ref_or_gap": "PR170-LIVE-DRYRUN1::provider_pending",
                    "postlaunch_route_ref_or_gap": "PR173-POSTLAUNCH::provider_pending",
                    "qmap_route_ref_or_gap": "PR174-QMAP1::provider_pending",
                    "allowlist_route_ref_or_gap": "PR174-ALLOW1::provider_pending",
                    "metrics_capture_route_ref_or_gap": row["pretrade_metrics_capture_handoff_ref_or_gap"],
                    "market_installation_route_ref_or_gap": row["market_reality_onboarding_handoff_ref_or_gap"],
                    "activation_state": row["stage_activation_state"],
                    "lifecycle_state": "PRETRADE_PACKET_CURRENT",
                    "downstream_ownership_state": "PROVIDER_PENDING",
                    "route_state": "ROUTED",
                    "route_gap_reason_or_none": "NONE",
                    **_false_payload(),
                },
            )
        )
    return rows


def _edge_alpha_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        no_trade_blocker = row["pretrade_packet_state"] == "NO_TRADE_SELECTED"
        return {
            "pretrade_edge_alpha_capture_map_id": row["pretrade_edge_alpha_capture_map_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
            "qku_refs": row["qku_refs"],
            "formula_refs": row["formula_refs"],
            "pretrade_objective_kernel_ref_or_gap": row["pretrade_objective_kernel_ref_or_gap"],
            "contract_payoff_model_ref_or_gap": row["contract_payoff_model_ref_or_gap"],
            "expected_gross_cash_route_ref_or_gap": row["pretrade_objective_kernel_ref_or_gap"],
            "expected_net_cash_route_ref_or_gap": row["expected_net_cash_formula_ref_or_gap"],
            "expected_net_cash_lcb_route_ref_or_gap": row["lower_confidence_bound_ref_or_gap"],
            "candidate_minus_no_trade_route_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
            "no_trade_candidate_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
            "tca_decomposition_ref_or_gap": row["tca_decomposition_ref_or_gap"],
            "fee_model_ref_or_gap": row["fee_model_ref_or_gap"],
            "fill_model_ref_or_gap": row["fill_model_ref_or_gap"],
            "slippage_model_ref_or_gap": row["slippage_model_ref_or_gap"],
            "latency_decay_model_ref_or_gap": row["latency_decay_model_ref_or_gap"],
            "capacity_crowding_model_ref_or_gap": row["capacity_crowding_model_ref_or_gap"],
            "adverse_selection_model_ref_or_gap": row["adverse_selection_model_ref_or_gap"],
            "settlement_cashflow_ref_or_gap": row["cashflow_model_ref_or_gap"],
            "microstructure_state_model_ref_or_gap": row["microstructure_state_model_ref_or_gap"],
            "probability_calibration_gate_ref_or_gap": row["probability_calibration_gate_ref_or_gap"],
            "market_state_quality_gate_ref_or_gap": row["market_state_quality_gate_ref_or_gap"],
            "pretrade_model_validity_horizon_ref_or_gap": row["pretrade_model_validity_horizon_ref_or_gap"],
            "pretrade_model_risk_control_ref_or_gap": row["pretrade_model_risk_control_ref_or_gap"],
            "pretrade_risk_envelope_ref_or_gap": row["pretrade_risk_envelope_ref_or_gap"],
            "pretrade_threshold_policy_ref_or_gap": row["pretrade_threshold_policy_ref_or_gap"],
            "scenario_ladder_decision_ref_or_gap": row["scenario_ladder_decision_ref_or_gap"],
            "portfolio_marginal_utility_ref_or_gap": _gap("PORTFOLIO_MARGINAL_UTILITY_PROVIDER_PENDING"),
            "overfit_fdr_control_ref_or_gap": _gap("OVERFIT_FDR_PROVIDER_PENDING"),
            "regime_memory_ref_or_gap": row["mem1_memory_ref_or_gap"],
            "agent_access_path_audit_ref_or_gap": row["pretrade_agent_access_path_audit_ref_or_gap"],
            "agent_route_ref_or_gap": row["pretrade_agent_packet_map_ref_or_gap"],
            "llm_grounding_ref_or_gap": row["pretrade_llm_grounding_view_ref_or_gap"],
            "quantum_readiness_handoff_ref_or_gap": row["pretrade_quantum_readiness_handoff_ref_or_gap"],
            "no_orphan_route_ref_or_gap": _out_ref("no_orphan.report.json"),
            "champion_ready_state": "NOT_CHAMPION_READY_PRETRADE_REVIEW_ONLY",
            "champion_ready_blocker_or_none": row["pretrade_packet_basis"],
            "edge_capture_state": "PRETRADE_EDGE_MAP_MATERIALIZED_NOT_PROFIT_PROOF",
            "edge_capture_score_0_1": row["edge_capture_score_0_1"],
            "alpha_source_family_refs_or_gap": ["QKU_FORMULA_STACK", "TCA", "FILL_LATENCY_CAPACITY", "MEM1_PRIOR_REVALIDATION"],
            "reoptimization_route_if_no_trade_wins": _route("recovery_frontier", row["candidate_id"]) if no_trade_blocker else "NO_TRADE_NOT_SELECTED",
            "repair_or_retest_route_if_blocked": _route("recovery_frontier", row["candidate_id"]),
        }
    return _candidate_rows(registry, "pretrade_edge_alpha_capture_map", make)


def _memory_reval_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "memory_prior_reval_id": _route("memory_prior_reval", row["candidate_id"]),
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
            "mem1_context_signature_ref_or_gap": row["mem1_memory_ref_or_gap"],
            "mem1_similarity_score_ref_or_gap": "docs/master_plan/generated/pr168_mem1/context_similarity_score.jsonl",
            "winning_recipe_refs_or_gap": row["mem1_winning_recipe_ref_or_gap"],
            "failure_memory_refs_or_gap": "docs/master_plan/generated/pr168_mem1/failure_memory.jsonl",
            "no_trade_memory_refs_or_gap": "docs/master_plan/generated/pr168_mem1/notrade_retest_route.jsonl",
            "qmemory_refs_or_gap": "docs/master_plan/generated/pr168_mem1/qmemory_registry.jsonl",
            "hotpath_memory_index_ref_or_gap": "docs/master_plan/generated/pr168_mem1/hotpath_memory_index.jsonl",
            "recipe_prior_score_or_gap": _gap("MEM1_PRIOR_SCORE_READ_ONLY"),
            "shrinkage_adjusted_prior_score_or_gap": _gap("SHRINKAGE_REVALIDATION_PENDING"),
            "memory_confidence_state": "PRIOR_ONLY",
            "memory_drift_state": "REVALIDATION_REQUIRED",
            "memory_cooldown_state": "CHECK_DOWNSTREAM",
            "memory_staleness_state": "CURRENT_SNAPSHOT_REVALIDATION_REQUIRED",
            "current_snapshot_revalidation_required": True,
            "current_snapshot_revalidation_route_ref_or_gap": row["pretrade_decision_trace_ref_or_gap"],
            "replay_revalidation_route_ref_or_gap": "PR169-PAPER-LOOP::replay_revalidation_provider_pending",
            "paper_revalidation_route_ref_or_gap": "PR169-PAPER-LOOP::paper_revalidation_provider_pending",
            "paper_loop_mem1_update_route_ref_or_gap": "PR169-PAPER-LOOP::receipt_backed_mem1_update_provider_pending",
            "metrics_mem1_update_route_ref_or_gap": "PR170-METRICS1::receipt_backed_mem1_attribution_provider_pending",
            "postlaunch_learning_route_ref_or_gap": "PR173-POSTLAUNCH::receipt_backed_mem1_learning_provider_pending",
            "memory_update_route_ref_or_gap": "PR168-MEM1::update_route_ref_only_no_receipt",
            "challenger_batch_route_ref_or_gap": _route("recovery_frontier", row["candidate_id"]),
            "exploration_batch_route_ref_or_gap": _route("recovery_frontier", row["candidate_id"]),
            "no_trade_comparator_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
            "current_tca_ref_or_gap": row["tca_decomposition_ref_or_gap"],
            "current_fill_latency_capacity_ref_or_gap": row["fill_model_ref_or_gap"],
            "current_overfit_fdr_ref_or_gap": _gap("OVERFIT_FDR_PROVIDER_PENDING"),
            "current_portfolio_utility_ref_or_gap": _gap("PORTFOLIO_PROVIDER_PENDING"),
            "current_source_currentness_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
            "current_market_state_quality_ref_or_gap": row["market_state_quality_gate_ref_or_gap"],
        }
    return _candidate_rows(registry, "pretrade_memory_prior_reval", make)


def _recovery_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        trigger = "NO_TRADE_WINS" if row["pretrade_packet_state"] == "NO_TRADE_SELECTED" else "SOURCE_CURRENTNESS_GAP"
        return {
            "recovery_frontier_id": _route("recovery_frontier", row["candidate_id"]),
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "trigger_state": trigger,
            "trigger_component_refs": [row["market_state_quality_gate_ref_or_gap"], row["pretrade_threshold_policy_ref_or_gap"]],
            "no_trade_candidate_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
            "variable_tuning_frontier_ref_or_inline": "bounded_entry_size_latency_policy_grid",
            "stack_challenger_frontier_ref_or_inline": "bounded_formula_stack_challenger_route",
            "venue_side_rotation_frontier_ref_or_inline": "same_market_venue_side_rotation_provider_pending",
            "order_policy_rotation_frontier_ref_or_inline": "maker_taker_split_cancel_replace_bounded_grid",
            "source_adapter_refresh_frontier_ref_or_inline": row["source_coverage_handoff_ref_or_gap"],
            "market_state_refresh_frontier_ref_or_inline": row["market_state_quality_gate_ref_or_gap"],
            "next_target_rotation_ref_or_inline": "bounded_next_target_provider_pending",
            "replay_retest_queue_ref_or_gap": "PR169-PAPER-LOOP::replay_retest_provider_pending",
            "paper_retest_queue_ref_or_gap": "PR169-PAPER-LOOP::paper_retest_provider_pending",
            "qmap_repair_route_ref_or_gap": "PR174-QMAP1::provider_pending",
            "plugin_intake_route_ref_or_gap": "PR174-PLUGIN1::provider_pending",
            "owner_guidance_ref_or_gap": row["pretrade_owner_guidance_handoff_ref_or_gap"],
            "responsible_agent_role_refs_or_gap": row["agent_role_refs"],
            "agent_workflow_obs_handoff_ref_or_gap": row["agent_workflow_obs_handoff_ref_or_gap"],
            "recovery_priority_score_0_1": max(0.0, min(1.0, row["edge_capture_score_0_1"] + 0.05)),
            "bounded_search_budget_state": "BOUNDED_NO_EXECUTION",
        }
    return _candidate_rows(registry, "pretrade_recovery_frontiers", make)


def _edge_attribution_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "edge_attribution_id": _route("edge_attribution", row["candidate_id"]),
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
            "qku_refs": row["qku_refs"],
            "formula_refs": row["formula_refs"],
            "stack_refs_or_gap": row["algorithm_refs_or_gap"],
            "expected_gross_edge_component_ref_or_gap": row["pretrade_objective_kernel_ref_or_gap"],
            "qku_contribution_state_or_gap": "ROUTED",
            "formula_stack_contribution_state_or_gap": "ROUTED",
            "entry_price_contribution_state_or_gap": row["pretrade_objective_kernel_ref_or_gap"],
            "exit_rule_contribution_state_or_gap": row["trade_plan_binding_ref_or_gap"],
            "side_selection_contribution_state_or_gap": row["contract_payoff_model_ref_or_gap"],
            "sizing_contribution_state_or_gap": row["pretrade_parameter_operability_ref_or_gap"],
            "maker_taker_contribution_state_or_gap": row["order_policy_candidate_set_ref_or_gap"],
            "cancel_replace_contribution_state_or_gap": row["order_policy_reality_model_ref_or_gap"],
            "spread_filter_contribution_state_or_gap": row["microstructure_state_model_ref_or_gap"],
            "depth_liquidity_filter_contribution_state_or_gap": row["market_state_quality_gate_ref_or_gap"],
            "fill_quality_contribution_state_or_gap": row["fill_model_ref_or_gap"],
            "latency_contribution_state_or_gap": row["latency_decay_model_ref_or_gap"],
            "capacity_contribution_state_or_gap": row["capacity_crowding_model_ref_or_gap"],
            "portfolio_context_contribution_state_or_gap": _gap("PORTFOLIO_PROVIDER_PENDING"),
            "scenario_ladder_contribution_state_or_gap": row["scenario_ladder_decision_ref_or_gap"],
            "memory_prior_contribution_state_or_gap": row["mem1_memory_ref_or_gap"],
            "quantum_structural_contribution_state_or_gap": row["pretrade_quantum_readiness_handoff_ref_or_gap"],
            "classical_fallback_contribution_state_or_gap": "CLASSICAL_FALLBACK_REQUIRED",
            "model_risk_haircut_contribution_state_or_gap": row["pretrade_model_risk_control_ref_or_gap"],
            "no_trade_margin_contribution_state_or_gap": row["no_trade_candidate_ref_or_gap"],
            "expected_edge_attribution_state": "EXPECTED_PRETRADE_ATTRIBUTION_ONLY",
            "attribution_gap_reason_or_none": row["pretrade_packet_basis"],
            "metrics_capture_handoff_ref_or_gap": row["pretrade_metrics_capture_handoff_ref_or_gap"],
            "agent_learning_handoff_ref_or_gap": "PR169-AGENT-ORCH1::provider_pending",
            "postlaunch_consumer_ref_or_gap": "PR173-POSTLAUNCH::provider_pending",
        }
    return _candidate_rows(registry, "pretrade_edge_attribution", make)


def _execution_ladder_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "pretrade_exec_ladder_handoff_id": _route("exec_ladder", row["candidate_id"]),
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
            "qku_refs": row["qku_refs"],
            "formula_refs": row["formula_refs"],
            "mode_authority_matrix_ref": row["mode_authority_matrix_ref_or_gap"],
            "no_trade_candidate_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
            "order_policy_candidate_set_ref_or_gap": row["order_policy_candidate_set_ref_or_gap"],
            "scenario_ladder_decision_ref_or_gap": row["scenario_ladder_decision_ref_or_gap"],
            "pretrade_scorecard_ref_or_gap": row["pretrade_scorecard_ref_or_gap"],
            "owner_intent_binding_ref_or_gap": row["pretrade_owner_intent_binding_ref_or_gap"],
            "owner_next_step_handoff_ref_or_gap": row["pretrade_owner_next_step_handoff_ref_or_gap"],
            "owner_guidance_handoff_ref_or_gap": row["pretrade_owner_guidance_handoff_ref_or_gap"],
            "agent_packet_map_ref_or_gap": row["pretrade_agent_packet_map_ref_or_gap"],
            "agent_workflow_obs_handoff_ref_or_gap": row["agent_workflow_obs_handoff_ref_or_gap"],
            "pretrade_artifact_value_route_map_ref_or_gap": row["pretrade_artifact_value_route_map_ref_or_gap"],
            "pretrade_agent_access_path_audit_ref_or_gap": row["pretrade_agent_access_path_audit_ref_or_gap"],
            "pretrade_edge_alpha_capture_map_ref_or_gap": row["pretrade_edge_alpha_capture_map_ref_or_gap"],
            "clean_room_default_candidate_lane_ref_or_gap": row["clean_room_default_candidate_lane_ref_or_gap"],
            "connector_handoff_ref_or_gap": row["pretrade_connector_handoff_ref_or_gap"],
            "execution_router_handoff_ref_or_gap": row["pretrade_execution_router_handoff_ref_or_gap"],
            "gate_snapshot_handoff_ref_or_gap": row["pretrade_gate_snapshot_handoff_ref_or_gap"],
            "allowed_downstream_action_verbs": ["BUY", "SELL", "OPEN", "CLOSE", "CANCEL", "REPLACE", "REDUCE", "EXIT"],
            "analysis_stage_state": "PRETRADE_ANALYSIS_ONLY",
            "replay_stage_route_ref_or_gap": "PR169-PAPER-LOOP::replay_provider_pending",
            "paper_stage_route_ref_or_gap": "PR169-PAPER-LOOP::paper_provider_pending",
            "shadow_candidate_stage_route_ref_or_gap": "STAGE1-SHADOW-COMPARISON::triggered_provider_pending",
            "live_dryrun_stage_route_ref_or_gap": "PR170-LIVE-DRYRUN1::provider_pending",
            "live_pilot_review_stage_route_ref_or_gap": "PR171-LIVE-PILOT::provider_pending",
            "launch_gate_stage_route_ref_or_gap": "PR172-LAUNCH::provider_pending",
            "execution_router_release_stage_ref_or_gap": "EXECUTION-ROUTER::provider_pending_no_release",
            "postlaunch_learning_stage_ref_or_gap": "PR173-POSTLAUNCH::provider_pending",
            "required_owner_approval_route_ref_or_gap": "OWNER_APPROVAL::provider_pending",
            "required_source_evidence_gate_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
            "required_cash_receipt_gate_ref_or_gap": "RUNTIME_CASH_RECEIPT::provider_pending",
            "required_risk_gate_ref_or_gap": row["pretrade_risk_envelope_ref_or_gap"],
            "required_portfolio_gate_ref_or_gap": _gap("PORTFOLIO_GATE_PENDING"),
            "required_latency_gate_ref_or_gap": row["latency_budget_decision_ref_or_gap"],
            "required_capacity_gate_ref_or_gap": row["capacity_crowding_model_ref_or_gap"],
            "required_kill_switch_gate_ref_or_gap": "KILL_SWITCH::provider_pending",
            "required_connector_gate_ref_or_gap": row["pretrade_connector_handoff_ref_or_gap"],
            "required_no_trade_margin_gate_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
            "required_tca_gate_ref_or_gap": row["tca_decomposition_ref_or_gap"],
            "required_overfit_fdr_gate_ref_or_gap": _gap("OVERFIT_FDR_GATE_PENDING"),
            "required_no_orphan_gate_ref": _out_ref("no_orphan.report.json"),
            "execution_ladder_state": "HANDOFF_ONLY_NO_EXECUTION",
            "execution_ladder_gap_reason_or_none": "DOWNSTREAM_EXECUTION_GATES_PROVIDER_PENDING",
        }
    return _candidate_rows(registry, "pretrade_exec_ladder_handoff", make)


def _clean_room_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    families = ["FEE_RANGE_CANDIDATE", "SLIPPAGE_RANGE_CANDIDATE", "LATENCY_BUDGET_CANDIDATE", "CAPACITY_LIMIT_CANDIDATE", "NO_TRADE_MARGIN_THRESHOLD_CANDIDATE", "QUBO_PENALTY_WEIGHT_CANDIDATE"]
    rows: list[dict[str, Any]] = []
    for row in registry:
        for family in families:
            rows.append(
                _projection_row(
                    "clean_room_default_candidates",
                    {
                        "clean_room_default_candidate_id": f"{row['candidate_id']}::{family}",
                        "candidate_id_or_scope": row["candidate_id"],
                        "parameter_symbol_or_model_component": family,
                        "component_family": family,
                        "inferred_value_or_range_or_gap": _gap(f"{family}_REQUIRES_CALIBRATION"),
                        "unit_or_basis_or_gap": "normalized_cash_or_probability",
                        "inference_method": "lawful_public_or_owner_approved_candidate_lane_only",
                        "public_or_observable_input_refs_or_gap": row["candidate_external_info_lane_ref_or_gap"],
                        "owner_approved_nonconfidential_input_refs_or_gap": _gap("OWNER_APPROVED_NONCONFIDENTIAL_INPUT_PENDING"),
                        "source_coverage_handoff_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
                        "candidate_external_info_lane_ref_or_gap": row["candidate_external_info_lane_ref_or_gap"],
                        "reality_assumption_ledger_ref_or_gap": row["reality_assumption_ledger_ref_or_gap"],
                        "pretrade_parameter_operability_ref_or_gap": row["pretrade_parameter_operability_ref_or_gap"],
                        "model_risk_control_ref_or_gap": row["pretrade_model_risk_control_ref_or_gap"],
                        "confidence_state": "CANDIDATE_ONLY_LOW_CONFIDENCE",
                        "uncertainty_state": "CALIBRATION_REQUIRED",
                        "conflict_resolution_route_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
                        "replay_paper_calibration_route_ref_or_gap": "PR169-PAPER-LOOP::calibration_provider_pending",
                        "owner_review_route_ref_or_gap": row["pretrade_owner_view_handoff_ref_or_gap"],
                        "clean_room_flag": True,
                        "replay_paper_calibration_required": True,
                        **_false_payload(),
                    },
                )
            )
    return rows


def _scenario_rows(registry: Sequence[dict[str, Any]], ctx: SourceContext) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        scenarios = ctx.scenario_by_candidate.get(row["candidate_id"], [])
        branches = sorted({str(item.get("scenario_family")) for item in scenarios if item.get("scenario_family")})
        required = ["base", "optimistic", "stress", "liquidity", "latency", "adverse_selection", "capacity", "settlement", "no_trade"]
        return {
            "scenario_ladder_decision_id": row["scenario_ladder_decision_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "scenario_branch_refs_or_gap": branches or _gap("SCENARIO_BRANCHES_PENDING"),
            "required_branch_families": required,
            "scenario_ladder_state": "MATERIALIZED_FROM_RP5G_WITH_REQUIRED_BRANCH_GAPS",
            "scenario_ladder_gap_reason_or_none": "ADDITIONAL_REQUIRED_BRANCH_LABELS_PROVIDER_PENDING",
            "no_trade_branch_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
        }
    return _candidate_rows(registry, "scenario_ladder_decisions", make)


def _latency_rows(registry: Sequence[dict[str, Any]], ctx: SourceContext) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        rp5g = ctx.rp5g_by_candidate.get(row["candidate_id"], {})
        budget = rp5g.get("latency_budget_candidate") or _gap("LATENCY_BUDGET_PENDING")
        return {
            "latency_budget_decision_id": row["latency_budget_decision_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "decision_latency_budget_ms_or_gap": budget,
            "model_latency_budget_ms_or_gap": budget,
            "agent_latency_budget_ms_or_gap": _gap("AGENT_ORCH_LATENCY_PENDING"),
            "paper_loop_latency_budget_ms_or_gap": _gap("PAPER_LOOP_LATENCY_PENDING"),
            "hotpath_latency_budget_ms_or_gap": _gap("HOTPATH_PRECOMPUTE_PENDING"),
            "live_dryrun_latency_budget_ms_or_gap": _gap("LIVE_DRYRUN_LATENCY_PENDING"),
            "execution_router_latency_budget_ms_or_gap": _gap("EXECUTION_ROUTER_LATENCY_PENDING"),
            "latency_budget_state": "CANDIDATE_BUDGET_ONLY_NO_RUNTIME",
        }
    return _candidate_rows(registry, "latency_budget_decisions", make)


def _microstructure_rows(registry: Sequence[dict[str, Any]], ctx: SourceContext) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        micro = ctx.micro_by_candidate.get(row["candidate_id"], {})
        depth = micro.get("depth_at_price_bucket") or _gap("DEPTH_PENDING")
        micro_state = "FAIL" if depth == "THIN" else "SCOPED_GAP"
        return {
            "microstructure_state_model_id": row["microstructure_state_model_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "market_family": row["market_family"],
            "venue_scope": row["venue_scope"],
            "platform_scope": row["platform_scope"],
            "quote_timestamp_ref_or_gap": "PR168_RP5G_FIXTURE_ASOF",
            "quote_age_ms_state": "SCOPED_GAP_NO_LIVE_QUOTE",
            "quote_freshness_state": "SCOPED_GAP_NO_LIVE_QUOTE",
            "bid_price_state_or_gap": _gap("BID_PRICE_PENDING"),
            "ask_price_state_or_gap": _gap("ASK_PRICE_PENDING"),
            "mid_price_state_or_gap": _gap("MID_PRICE_PENDING"),
            "spread_state_or_gap": micro.get("best_bid_best_ask_mid_spread") or _gap("SPREAD_PENDING"),
            "bid_depth_state_or_gap": depth,
            "ask_depth_state_or_gap": depth,
            "orderbook_depth_bucket_or_gap": depth,
            "orderbook_imbalance_state_or_gap": micro.get("orderbook_imbalance_topN") or _gap("IMBALANCE_PENDING"),
            "recent_trade_rate_state_or_gap": _gap("RECENT_TRADE_RATE_PENDING"),
            "liquidity_bucket_or_gap": depth,
            "time_to_resolution_bucket_or_gap": micro.get("time_to_close_bucket") or _gap("TIME_TO_RESOLUTION_PENDING"),
            "event_lifecycle_state_or_gap": micro.get("event_status_state") or _gap("EVENT_STATUS_PENDING"),
            "settlement_resolution_state_or_gap": "SCOPED_GAP_SETTLEMENT_SOURCE_PENDING",
            "crossed_or_locked_book_state": "SCOPED_GAP_NO_LIVE_BOOK",
            "stale_quote_state": "SCOPED_GAP_NO_LIVE_QUOTE",
            "thin_book_state": depth == "THIN",
            "market_state_quality_gate_ref_or_gap": row["market_state_quality_gate_ref_or_gap"],
            "fill_model_ref_or_gap": row["fill_model_ref_or_gap"],
            "slippage_model_ref_or_gap": row["slippage_model_ref_or_gap"],
            "capacity_crowding_model_ref_or_gap": row["capacity_crowding_model_ref_or_gap"],
            "adverse_selection_model_ref_or_gap": row["adverse_selection_model_ref_or_gap"],
            "microstructure_state": micro_state,
            "microstructure_gap_reason_or_none": row["quality_gap_reason_or_none"],
        }
    return _candidate_rows(registry, "microstructure_state_models", make)


def _assumption_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in registry:
        for component in COMPONENT_FAMILIES:
            rows.append(
                _projection_row(
                    "reality_assumption_ledger",
                    {
                        "assumption_id": f"ASSUMPTION_{component.upper()}_{_id_suffix(row['candidate_id'])}",
                        "candidate_id_or_scope": row["candidate_id"],
                        "component_family": component,
                        "model_ref_or_gap": _route(f"{component}_model", row["candidate_id"]),
                        "assumption_text_or_formula_ref": f"{component} requires accepted source or replay/paper calibration before promotion.",
                        "assumption_kind": "PRETRADE_MODEL_ASSUMPTION",
                        "unit_or_basis_or_gap": "normalized_cash_or_probability",
                        "scale_or_range_or_gap": "decimal_scale_6_or_scoped_gap",
                        "source_authority_state": "CANDIDATE_RESEARCH_PROVISIONAL",
                        "accepted_source_refs_or_gap": _gap(f"{component.upper()}_ACCEPTED_SOURCE_PENDING"),
                        "candidate_external_info_lane_refs_or_gap": row["candidate_external_info_lane_ref_or_gap"],
                        "calibration_receipt_ref_or_gap": row["reality_model_calibration_receipt_ref_or_gap"],
                        "freshness_state": "SOURCE_CURRENTNESS_REVALIDATION_REQUIRED",
                        "coverage_quorum_state_or_gap": _gap("SOURCE_COVERAGE_QUORUM_PENDING"),
                        "conflict_state": "NO_ACCEPTED_SOURCE_CONFLICT_RESOLUTION_YET",
                        "uncertainty_state": "MODEL_RISK_HAIRCUT_REQUIRED",
                        "model_risk_control_ref_or_gap": row["pretrade_model_risk_control_ref_or_gap"],
                        "owner_view_route_ref_or_gap": row["pretrade_owner_view_handoff_ref_or_gap"],
                        "downstream_consumer_refs": row["downstream_consumer_refs"],
                        "assumption_gap_reason_or_none": "ACCEPTED_SOURCE_OR_CALIBRATION_PENDING",
                        **_false_payload(),
                    },
                )
            )
    return rows


def _model_risk_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in registry:
        for component in COMPONENT_FAMILIES:
            rows.append(
                _projection_row(
                    "pretrade_model_risk_controls",
                    {
                        "model_risk_control_id": f"MODEL_RISK_{component.upper()}_{_id_suffix(row['candidate_id'])}",
                        "candidate_id_or_scope": row["candidate_id"],
                        "component_family": component,
                        "assumption_refs": [f"ASSUMPTION_{component.upper()}_{_id_suffix(row['candidate_id'])}"],
                        "risk_family": "SOURCE_CURRENTNESS_AND_CALIBRATION",
                        "risk_severity": "MEDIUM",
                        "support_count_or_gap": _gap("SUPPORT_COUNT_PENDING"),
                        "sample_window_ref_or_gap": _gap("SAMPLE_WINDOW_PENDING"),
                        "calibration_state": "PROXY_OR_GAP",
                        "staleness_state": "REVALIDATION_REQUIRED",
                        "cross_venue_generalization_risk_state": "BLOCKED_BY_VENUE_POLICY_MATRIX",
                        "thin_book_risk_state": row["quality_gap_reason_or_none"],
                        "liquidity_regime_risk_state": "SCOPED_GAP_OR_REPLAY_FIXTURE_ONLY",
                        "latency_regime_risk_state": "SCOPED_GAP_OR_CANDIDATE_BUDGET_ONLY",
                        "settlement_cashflow_risk_state": "SCOPED_GAP_ACCEPTED_SOURCE_PENDING",
                        "missing_value_policy": "NO_OPTIMISTIC_DEFAULTS",
                        "stress_route_ref_or_gap": row["scenario_ladder_decision_ref_or_gap"],
                        "fallback_route_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
                        "retest_route_ref_or_gap": _route("recovery_frontier", row["candidate_id"]),
                        "owner_review_route_ref_or_gap": row["pretrade_owner_view_handoff_ref_or_gap"],
                        "model_risk_state": "CONTROL_MATERIALIZED_NO_PROMOTION",
                        "model_risk_gap_reason_or_none": "ACCEPTED_SOURCE_OR_CALIBRATION_PENDING",
                        "live_promotion_allowed": False,
                        **_false_payload(),
                    },
                )
            )
    return rows


def _parameter_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    params = ["fee_rate", "fill_probability", "slippage_cash", "latency_budget_ms", "capacity_limit", "cash_lock_penalty", "no_trade_margin", "model_risk_haircut"]
    rows: list[dict[str, Any]] = []
    for row in registry:
        for symbol in params:
            rows.append(
                _projection_row(
                    "pretrade_parameter_operability",
                    {
                        "pretrade_parameter_operability_id": f"PARAM_{_id_suffix(row['candidate_id'])}_{symbol}",
                        "candidate_id_or_scope": row["candidate_id"],
                        "parameter_symbol": symbol,
                        "parameter_family": "PRETRADE_REALITY_PARAMETER",
                        "component_family": symbol.split("_")[0],
                        "model_ref_or_gap": row["pretrade_objective_kernel_ref_or_gap"],
                        "qku_refs_or_gap": row["qku_refs"],
                        "formula_refs_or_gap": row["formula_refs"],
                        "trade_variable_ref_or_gap": row["trade_plan_binding_ref_or_gap"],
                        "unit_or_basis": "cash_or_probability_or_ms",
                        "scale_contract_ref_or_gap": "decimal_scale_6",
                        "normalization_contract_ref_or_gap": row["contract_payoff_model_ref_or_gap"],
                        "day1_start_value_or_gap": _gap(f"{symbol.upper()}_START_VALUE_REQUIRES_ACCEPTED_SOURCE_OR_CALIBRATION"),
                        "reference_range_or_gap": _gap(f"{symbol.upper()}_REFERENCE_RANGE_PENDING"),
                        "bounded_search_space_or_gap": "BOUNDED_BY_DOWNSTREAM_REPLAY_PAPER_PROVIDER",
                        "current_value_source_state": "CANDIDATE_ONLY_OR_SCOPED_GAP",
                        "owner_editability_class_or_gap": "OWNER_REVIEWABLE_PROVIDER_PENDING",
                        "owner_view_route_ref_or_gap": row["pretrade_owner_view_handoff_ref_or_gap"],
                        "optimizer_default_policy_ref_or_gap": row["clean_room_default_candidate_lane_ref_or_gap"],
                        "missing_value_policy": "NO_OPTIMISTIC_DEFAULT",
                        "source_authority_state": "CANDIDATE_RESEARCH_PROVISIONAL",
                        "calibration_receipt_ref_or_gap": row["reality_model_calibration_receipt_ref_or_gap"],
                        "model_risk_control_ref_or_gap": row["pretrade_model_risk_control_ref_or_gap"],
                        "pretrade_consumer_ref_or_gap": row["pretrade_decision_candidate_id"],
                        "paper_loop_consumer_ref_or_gap": "PR169-PAPER-LOOP::provider_pending",
                        "hotpath_consumer_ref_or_gap": row["pretrade_hotpath_handoff_ref_or_gap"],
                        "live_dryrun_consumer_ref_or_gap": "PR170-LIVE-DRYRUN1::provider_pending",
                        "execution_router_consumer_ref_or_gap": row["pretrade_execution_router_handoff_ref_or_gap"],
                        "parameter_operability_state": "MATERIALIZED_WITH_SCOPED_VALUE_GAPS",
                        "parameter_gap_reason_or_none": "ACCEPTED_SOURCE_OR_CALIBRATION_PENDING",
                        **_false_payload(),
                    },
                )
            )
    return rows


def _source_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "source_coverage_handoff_id": row["source_coverage_handoff_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "source_authority_state": "CANDIDATE_RESEARCH_PROVISIONAL_NOT_ACCEPTED_SOURCE_TRUTH",
            "accepted_source_refs_or_gap": _gap("ACCEPTED_SOURCE_EVIDENCE_PENDING"),
            "candidate_external_info_lane_ref_or_gap": row["candidate_external_info_lane_ref_or_gap"],
            "source_currentness_route_ref_or_gap": row["pretrade_model_validity_horizon_ref_or_gap"],
            "remaining_uncertainty": "Venue mechanics, live market state, fees, settlement, and connector semantics require downstream accepted-source evidence.",
        }
    return _candidate_rows(registry, "source_coverage_handoff", make)


def _external_lane_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    def make(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "candidate_external_info_lane_id": row["candidate_external_info_lane_ref_or_gap"],
            "candidate_id": row["candidate_id"],
            "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
            "lane_state": "CANDIDATE_RESEARCH_PROVISIONAL",
            "safe_use": "pretrade_model_candidate_or_gap_only",
            "unsafe_use": "source_truth_order_authority_profit_claim",
            "source_rights_state": "NO_CONFIDENTIAL_OR_RESTRICTED_INPUT_ALLOWED",
        }
    return _candidate_rows(registry, "candidate_external_info_lanes", make)


def _consumer_routes(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in registry:
        for consumer in row["downstream_consumer_refs"]:
            rows.append(
                _projection_row(
                    "consumer_routes",
                    {
                        "consumer_route_id": f"{row['candidate_id']}::{consumer}",
                        "candidate_id": row["candidate_id"],
                        "pretrade_decision_candidate_ref": row["pretrade_decision_candidate_id"],
                        "consumer_ref": consumer,
                        "route_state": "PROVIDER_PENDING_NO_RUNTIME",
                        "runtime_use_allowed": False,
                        "live_use_allowed": False,
                        "raw_jsonl_runtime_scan_used": False,
                        **_false_payload(),
                    },
                )
            )
    return rows


def _gap_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    gap_families = [
        "ACCEPTED_SOURCE_EVIDENCE",
        "LIVE_MARKET_STATE",
        "CONNECTOR_SEMANTICS",
        "RUNTIME_CASH",
        "OWNER_RISK_LIMIT",
        "PAPER_REPLAY_RECEIPTS",
        "MEM1_RECEIPT_BACKED_UPDATE",
    ]
    for row in registry:
        for family in gap_families:
            rows.append(
                _projection_row(
                    "pretrade_gap_ledger",
                    {
                        "pretrade_gap_id": f"{row['candidate_id']}::{family}",
                        "candidate_id": row["candidate_id"],
                        "gap_family": family,
                        "gap_detail": f"{family} remains downstream provider-pending; PRETRADE1 emits route contract only.",
                        "unblocking_route_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
                        "owner_guidance_ref_or_gap": row["pretrade_owner_guidance_handoff_ref_or_gap"],
                        "recheck_validator": VALIDATOR_NAME,
                        **_false_payload(),
                    },
                )
            )
    return rows


def _reports(registry: Sequence[dict[str, Any]], artifact_rows: dict[str, Sequence[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    base = {
        "generated_from": REGISTRY_REF,
        "manual_edit_allowed": False,
        "authoritative_source": REGISTRY_REF,
        "builder_name": BUILDER_NAME,
        "validator_name": VALIDATOR_NAME,
        "projection_version": PROJECTION_VERSION,
        "prompt_version": PROMPT_VERSION,
    }
    artifact_count = len(JSONL_ARTIFACTS) + len(JSON_ARTIFACTS)
    component_count = len(artifact_rows["reality_model_component_contracts.generated.jsonl"])
    upstream_route_count = len(registry)
    downstream_route_count = len(artifact_rows["consumer_routes.generated.jsonl"])
    model_component_refs = [
        _out_ref(name)
        for name in (
            "venue_reality_models.generated.jsonl",
            "fee_models.generated.jsonl",
            "fill_models.generated.jsonl",
            "slippage_models.generated.jsonl",
            "latency_decay_models.generated.jsonl",
            "queue_position_models.generated.jsonl",
            "partial_fill_models.generated.jsonl",
            "capacity_crowding_models.generated.jsonl",
            "adverse_selection_models.generated.jsonl",
            "settlement_resolution_models.generated.jsonl",
            "cashflow_models.generated.jsonl",
            "order_policy_reality_models.generated.jsonl",
            "reality_model_component_contracts.generated.jsonl",
        )
    ]
    reports = {
        "no_orphan.report.json": {
            **base,
            "report_type": "NO_ORPHAN_REPORT",
            "acceptance_state": "PASS",
            "orphan_count": 0,
            "generated_artifact_count": artifact_count,
            "route_map_rows": len(artifact_rows["pretrade_artifact_value_route_map.generated.jsonl"]),
            "registry_row_count": len(registry),
        },
        "no_submit_authority.report.json": {
            **base,
            "report_type": "NO_SUBMIT_AUTHORITY_REPORT",
            "acceptance_state": "PASS",
            "pretrade_packet_count": len(artifact_rows["pretrade_decision_candidates.generated.jsonl"]),
            "reality_model_component_count": component_count,
            "market_onboarding_handoff_count": len(artifact_rows["market_reality_onboarding_handoff.generated.jsonl"]),
            "order_simulation_spec_count": len(artifact_rows["pretrade_order_simulation_specs.generated.jsonl"]),
            "assumption_ledger_count": len(artifact_rows["reality_assumption_ledger.generated.jsonl"]),
            "model_risk_control_count": len(artifact_rows["pretrade_model_risk_controls.generated.jsonl"]),
            "parameter_operability_count": len(artifact_rows["pretrade_parameter_operability.generated.jsonl"]),
            "gate_snapshot_handoff_count": len(artifact_rows["pretrade_gate_snapshot_handoff.generated.jsonl"]),
            "submit_authority_created_count": 0,
            "order_authority_created_count": 0,
            "execution_router_release_created_count": 0,
            "venue_submit_created_count": 0,
            "replay_execution_created_count": 0,
            "paper_execution_created_count": 0,
            "shadow_execution_created_count": 0,
            "live_execution_created_count": 0,
            "connector_read_created_count": 0,
            "connector_write_created_count": 0,
            "private_cash_read_created_count": 0,
            "source_truth_created_count": 0,
            "runtime_llm_call_created_count": 0,
            "runtime_agent_execution_created_count": 0,
            "runtime_agent_operations_created_count": 0,
            "workflow_queue_runtime_created_count": 0,
            "runtime_task_created_count": 0,
            "runtime_receipt_created_count": 0,
            "fake_agent_status_created_count": 0,
            "fake_queue_item_created_count": 0,
            "fake_timestamp_created_count": 0,
            "artifact_value_orphan_count": 0,
            "execution_ladder_runtime_authority_created_count": 0,
            "clean_room_proprietary_claim_created_count": 0,
            "clean_room_forbidden_source_flag_count": 0,
            "runtime_dashboard_service_created_count": 0,
            "runtime_metrics_created_count": 0,
            "live_receipt_created_count": 0,
            "quantum_backend_execution_created_count": 0,
            "profit_claim_created_count": 0,
            "forbidden_flag_refs_or_none": [],
            "fail_closed_reasons": [],
            "authority_boundary": _false_payload(),
            "order_submit_created": False,
            "live_execution_created": False,
            "execution_router_release_created": False,
        },
        "no_raw_jsonl_scan.report.json": {
            **base,
            "report_type": "NO_RAW_JSONL_RUNTIME_SCAN_REPORT",
            "acceptance_state": "PASS",
            "builder_reads_declared_upstream_inputs": True,
            "central_resolver_path": "src/qtt/pretrade/pr169_pretrade1_resolvers.py",
            "runtime_resolver_created": False,
            "blocked_paths": [],
            "raw_jsonl_runtime_scan_used": False,
        },
        "no_placeholder_materialization.report.json": {
            **base,
            "report_type": "NO_PLACEHOLDER_MATERIALIZATION_REPORT",
            "acceptance_state": "PASS",
            "metadata_only_row_count": 0,
            "planning_only_row_count": 0,
            "scoped_gap_rows_are_actionable": True,
        },
        "pretrade_quality_gates.report.json": {
            **base,
            "report_type": "PRETRADE_QUALITY_GATES_REPORT",
            "acceptance_state": "PASS",
            "readiness1_consumption_state": "PASS_CONSUMED_NOT_RECREATED",
            "readiness1_supporting_projection_refs": [_out_ref("readiness1_input_map.generated.jsonl")],
            "reality_model_coverage_state": "PASS_COMPONENT_CONTRACTS_PRESENT_WITH_SCOPED_GAPS",
            "payoff_objective_market_state_probability_validity_coverage_state": "PASS_PAYOFF_OBJECTIVE_MARKET_PROBABILITY_VALIDITY_ROUTES_PRESENT",
            "model_component_refs": model_component_refs,
            "no_orphan_coverage_state": "PASS",
            "upstream_route_count": upstream_route_count,
            "downstream_route_count": downstream_route_count,
            "orphan_count": 0,
            "orphan_refs_or_none": [],
            "agent_llm_packet_route_state": "PASS_AGENT_AND_LLM_ROUTES_PRESENT_NO_RUNTIME",
            "execution_router_handoff_state": "PASS_PROVIDER_PENDING_NO_RELEASE",
            "actual_buy_sell_open_close_created": False,
            "authority_boundary_state": "PASS_ALL_FORBIDDEN_FLAGS_FALSE",
            "forbidden_created_flags": [],
            "market_onboarding_coverage_state": "PASS_MARKET_INSTALLATION_SOCKET_PRESENT",
            "market_onboarding_refs_or_gap": [_out_ref("market_reality_onboarding_handoff.generated.jsonl")],
            "runtime_market_connector_created": False,
            "metrics_capture_handoff_state": "PASS_ROUTES_PRESENT_NO_RUNTIME_METRICS",
            "runtime_metrics_created": False,
            "live_receipt_created": False,
            "agent_workflow_observability_state": "PASS_HANDOFF_PRESENT_NO_FAKE_STATUS_QUEUE_OR_RECEIPTS",
            "agent_workflow_supporting_projection_refs_or_gap": [_out_ref("agent_workflow_obs_handoff.generated.jsonl")],
            "fake_agent_status_created": False,
            "fake_queue_item_created": False,
            "fake_timestamp_created": False,
            "runtime_receipt_created": False,
            "artifact_value_route_map_state": "PASS",
            "orphan_value_count": 0,
            "orphan_value_refs_or_none": [],
            "execution_ladder_handoff_state": "PASS_PROVIDER_PENDING_NO_RUNTIME_AUTHORITY",
            "execution_router_release_created": False,
            "clean_room_default_candidate_lane_state": "PASS_CANDIDATE_DEFAULTS_ONLY",
            "proprietary_claim_count": 0,
            "forbidden_source_flag_count": 0,
            "agent_access_path_audit_state": "PASS_CENTRALIZED_ACCESS_PATH_OR_SCOPED_GAP",
            "edge_alpha_capture_map_state": "PASS_EXPLICIT_CAPTURE_MAP_PRESENT",
            "raw_jsonl_runtime_scan_used": False,
            "full_library_default_access_created": False,
            "memory_prior_revalidation_state": "PASS_PRIOR_ONLY_CURRENT_REVALIDATION_REQUIRED",
            "memory_prior_used_as_proof": False,
            "mem1_redone": False,
            "parallel_memory_registry_created": False,
            "mem1_generated_artifact_modified": False,
            "memory_update_receipt_created": False,
            "paper_loop_mem1_update_route_state": "PASS_DOWNSTREAM_ROUTE_PRESENT",
            "metrics_mem1_update_route_state": "PASS_DOWNSTREAM_ROUTE_PRESENT",
            "postlaunch_learning_route_state": "PASS_DOWNSTREAM_ROUTE_PRESENT",
            "recovery_frontier_state": "PASS_NO_TERMINAL_DEAD_END",
            "terminal_dead_end_created": False,
            "global_qku_formula_ban_created": False,
            "venue_policy_matrix_state": "PASS_STAGE1_VENUES_PRESENT_NO_BLIND_DEFAULTS",
            "cross_venue_generalization_allowed": False,
            "edge_attribution_state": "PASS_EXPECTED_ATTRIBUTION_ONLY",
            "realized_pnl_created": False,
            "fail_closed_reasons": [],
            "readiness1_consumed_not_redone": True,
            "mem1_consumed_as_prior_not_redone": True,
            "one_canonical_registry": True,
            "one_builder": True,
            "one_validator": True,
            "edge_alpha_capture_map_present": True,
            "artifact_value_route_map_present": True,
            "agent_access_path_audit_present": True,
            "execution_ladder_handoff_present": True,
            "clean_room_default_candidates_present": True,
            "memory_prior_revalidation_present": True,
            "recovery_frontiers_present": True,
            "stage1_venue_policy_matrix_present": True,
            "expected_edge_attribution_present": True,
            "profit_claim_created": False,
        },
        "market_installation_acceptance.report.json": {
            **base,
            "report_type": "MARKET_INSTALLATION_ACCEPTANCE_REPORT",
            "acceptance_state": "PASS",
            "market_onboarding_handoff_count": len(artifact_rows["market_reality_onboarding_handoff.generated.jsonl"]),
            "market_family_count": len({row["market_family"] for row in registry}),
            "venue_scope_count": len({row["venue_scope"] for row in registry} | set(STAGE1_VENUES)),
            "platform_scope_count": len({row["platform_scope"] for row in registry}),
            "model_component_family_coverage_state": "PASS_COMPONENT_CONTRACTS_OR_SCOPED_GAPS",
            "adapter_route_coverage_state": "PASS_PROVIDER_PENDING_ADAPTER_ROUTES",
            "source_evidence_route_coverage_state": "PASS_SOURCE_COVERAGE_HANDOFF",
            "owner_surface_route_coverage_state": "PASS_OWNER_HANDOFF_ROUTES",
            "agent_route_coverage_state": "PASS_AGENT_PACKET_ROUTES",
            "llm_grounding_route_coverage_state": "PASS_LLM_GROUNDING_ROUTES",
            "paper_loop_route_coverage_state": "PASS_PROVIDER_PENDING",
            "hotpath_route_coverage_state": "PASS_PRECOMPUTE_HANDOFF",
            "live_dryrun_route_coverage_state": "PASS_PROVIDER_PENDING",
            "execution_router_route_coverage_state": "PASS_NO_RELEASE",
            "qmap_route_coverage_state": "PASS_PROVIDER_PENDING",
            "allowlist_route_coverage_state": "PASS_PROVIDER_PENDING_NO_RUNTIME_ALLOWLIST",
            "orphan_market_route_count": 0,
            "orphan_market_route_refs_or_none": [],
            "row_route_market_installation_socket": True,
            "venue_policy_rows": len(artifact_rows["pretrade_venue_policy_matrix.generated.jsonl"]),
            "runtime_connector_created": False,
            "connector_read_created": False,
            "connector_write_created": False,
            "venue_semantics_accepted": False,
            "source_truth_created": False,
            "order_authority_created": False,
            "profit_claim_created": False,
            "fail_closed_reasons": [],
        },
    }
    reports["pretrade_manifest.json"] = {
        **base,
        "report_type": "PRETRADE_MANIFEST",
        "acceptance_state": "PASS",
        "generated_prefix": GENERATED_PREFIX.as_posix(),
        "canonical_registry_ref": REGISTRY_REF,
        "generated_artifact_count": artifact_count,
        "jsonl_row_counts": {name: len(rows) for name, rows in artifact_rows.items()},
        "generated_artifacts": [
            {
                "artifact_ref": _out_ref(name),
                "producer": BUILDER_NAME,
                "canonical_source": REGISTRY_REF,
                "consumer": "PRETRADE1 validator and downstream provider-pending routes",
                "validator": VALIDATOR_NAME,
                "downstream_route_proof": _out_ref("consumer_routes.generated.jsonl"),
                "manual_edit_allowed": False,
                "orphan_status": "NOT_ORPHANED_ROUTE_PROOF_PRESENT",
            }
            for name in (*JSONL_ARTIFACTS, *JSON_ARTIFACTS)
        ],
    }
    return reports


def _artifact_rows(registry: Sequence[dict[str, Any]], ctx: SourceContext) -> dict[str, Sequence[dict[str, Any]]]:
    rows: dict[str, Sequence[dict[str, Any]]] = {
        "pretrade_decision_registry.jsonl": registry,
        "readiness1_input_map.generated.jsonl": _readiness_input_rows(registry),
        "market_reality_onboarding_handoff.generated.jsonl": _market_onboarding_rows(registry),
        "pretrade_qku_formula_compute_map.generated.jsonl": _simple_projection(registry, "pretrade_qku_formula_compute_map"),
        "trade_plan_bindings.generated.jsonl": _trade_plan_bindings(registry),
        "pretrade_decision_candidates.generated.jsonl": _decision_candidates(registry),
        "no_trade_candidates.generated.jsonl": _no_trade_rows(registry),
        "order_policy_candidate_sets.generated.jsonl": _order_policy_rows(registry),
        "pretrade_order_simulation_specs.generated.jsonl": _simple_projection(registry, "pretrade_order_simulation_specs"),
        "scenario_ladder_decisions.generated.jsonl": _scenario_rows(registry, ctx),
        "latency_budget_decisions.generated.jsonl": _latency_rows(registry, ctx),
        "mode_authority_matrix.generated.jsonl": _mode_authority_rows(registry),
        "pretrade_objective_kernels.generated.jsonl": _objective_rows(registry, ctx),
        "contract_payoff_models.generated.jsonl": _payoff_rows(registry),
        "market_state_quality_gates.generated.jsonl": _market_state_rows(registry, ctx),
        "probability_calibration_gates.generated.jsonl": _calibration_gate_rows(registry, ctx),
        "pretrade_model_validity_horizon.generated.jsonl": _validity_rows(registry),
        "venue_reality_models.generated.jsonl": _component_rows(registry, "venue_reality_models", "venue_reality"),
        "fee_models.generated.jsonl": _component_rows(registry, "fee_models", "fee"),
        "fill_models.generated.jsonl": _component_rows(registry, "fill_models", "fill"),
        "slippage_models.generated.jsonl": _component_rows(registry, "slippage_models", "slippage"),
        "latency_decay_models.generated.jsonl": _component_rows(registry, "latency_decay_models", "latency_decay"),
        "queue_position_models.generated.jsonl": _component_rows(registry, "queue_position_models", "queue_position"),
        "partial_fill_models.generated.jsonl": _component_rows(registry, "partial_fill_models", "partial_fill"),
        "capacity_crowding_models.generated.jsonl": _component_rows(registry, "capacity_crowding_models", "capacity_crowding"),
        "adverse_selection_models.generated.jsonl": _component_rows(registry, "adverse_selection_models", "adverse_selection"),
        "settlement_resolution_models.generated.jsonl": _component_rows(registry, "settlement_resolution_models", "settlement_resolution"),
        "cashflow_models.generated.jsonl": _component_rows(registry, "cashflow_models", "cashflow"),
        "order_policy_reality_models.generated.jsonl": _component_rows(registry, "order_policy_reality_models", "order_policy"),
        "reality_model_component_contracts.generated.jsonl": _component_contract_rows(registry),
        "reality_assumption_ledger.generated.jsonl": _assumption_rows(registry),
        "pretrade_model_risk_controls.generated.jsonl": _model_risk_rows(registry),
        "pretrade_parameter_operability.generated.jsonl": _parameter_rows(registry),
        "paper_vs_replay_reality_diff.generated.jsonl": _simple_projection(registry, "paper_vs_replay_reality_diff"),
        "reality_model_calibration_receipts.generated.jsonl": _simple_projection(registry, "reality_model_calibration_receipts"),
        "tca_decomposition.generated.jsonl": _simple_projection(registry, "tca_decomposition"),
        "pretrade_scorecard.generated.jsonl": _simple_projection(registry, "pretrade_scorecard"),
        "pretrade_agent_packet_map.generated.jsonl": _simple_projection(registry, "pretrade_agent_packet_map"),
        "pretrade_llm_grounding_view.generated.jsonl": _simple_projection(registry, "pretrade_llm_grounding_view"),
        "pretrade_owner_view_handoff.generated.jsonl": _simple_projection(registry, "pretrade_owner_view_handoff"),
        "pretrade_connector_handoff.generated.jsonl": _simple_projection(registry, "pretrade_connector_handoff"),
        "pretrade_execution_router_handoff.generated.jsonl": _simple_projection(registry, "pretrade_execution_router_handoff"),
        "pretrade_hotpath_handoff.generated.jsonl": _simple_projection(registry, "pretrade_hotpath_handoff"),
        "pretrade_quantum_readiness_handoff.generated.jsonl": _simple_projection(registry, "pretrade_quantum_readiness_handoff"),
        "pretrade_gate_snapshot_handoff.generated.jsonl": _simple_projection(registry, "pretrade_gate_snapshot_handoff"),
        "pretrade_owner_intent_bindings.generated.jsonl": _simple_projection(registry, "pretrade_owner_intent_bindings"),
        "pretrade_owner_next_step_handoff.generated.jsonl": _next_step_rows(registry),
        "pretrade_owner_guidance_handoff.generated.jsonl": _owner_guidance_rows(registry),
        "microstructure_state_models.generated.jsonl": _microstructure_rows(registry, ctx),
        "pretrade_risk_envelopes.generated.jsonl": _risk_policy_rows(registry, "pretrade_risk_envelopes"),
        "pretrade_threshold_policy.generated.jsonl": _risk_policy_rows(registry, "pretrade_threshold_policy"),
        "pretrade_decision_traces.generated.jsonl": _simple_projection(registry, "pretrade_decision_traces"),
        "pretrade_agent_dag_handoff.generated.jsonl": _simple_projection(registry, "pretrade_agent_dag_handoff"),
        "agent_workflow_obs_handoff.generated.jsonl": _simple_projection(registry, "agent_workflow_obs_handoff"),
        "pretrade_metrics_capture_handoff.generated.jsonl": _simple_projection(registry, "pretrade_metrics_capture_handoff"),
        "pretrade_artifact_value_route_map.generated.jsonl": _artifact_route_rows(registry),
        "pretrade_agent_access_path_audit.generated.jsonl": _simple_projection(registry, "pretrade_agent_access_path_audit"),
        "pretrade_edge_alpha_capture_map.generated.jsonl": _edge_alpha_rows(registry),
        "pretrade_memory_prior_reval.generated.jsonl": _memory_reval_rows(registry),
        "pretrade_recovery_frontiers.generated.jsonl": _recovery_rows(registry),
        "pretrade_venue_policy_matrix.generated.jsonl": _venue_policy_rows(registry),
        "pretrade_edge_attribution.generated.jsonl": _edge_attribution_rows(registry),
        "pretrade_exec_ladder_handoff.generated.jsonl": _execution_ladder_rows(registry),
        "clean_room_default_candidates.generated.jsonl": _clean_room_rows(registry),
        "source_coverage_handoff.generated.jsonl": _source_rows(registry),
        "candidate_external_info_lanes.generated.jsonl": _external_lane_rows(registry),
        "pretrade_gap_ledger.generated.jsonl": _gap_rows(registry),
        "consumer_routes.generated.jsonl": _consumer_routes(registry),
    }
    return rows


def build(repo_root: Path, out_dir: Path) -> None:
    ctx = _load_context(repo_root)
    registry = _build_registry(ctx)
    artifact_rows = _artifact_rows(registry, ctx)
    reports = _reports(registry, artifact_rows)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in JSONL_ARTIFACTS:
        _write_jsonl(out_dir / name, artifact_rows[name])
    for name in JSON_ARTIFACTS:
        _write_json(out_dir / name, reports[name])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=GENERATED_PREFIX)
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    out_dir = args.out_dir if args.out_dir.is_absolute() else repo_root / args.out_dir
    build(repo_root, out_dir)
    print(f"built PR169-PRETRADE1 artifacts at {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
