#!/usr/bin/env python3
"""Validate PR169-SVC1 generated service/read-model artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import build_pr169_svc1 as builder


GENERATED_PREFIX = builder.GENERATED_PREFIX
REGISTRY_REF = builder.REGISTRY_REF
PROJECTION_VERSION = builder.PROJECTION_VERSION
BUILDER_NAME = builder.BUILDER_NAME
VALIDATOR_NAME = builder.VALIDATOR_NAME

REQUIRED_JSONL = builder.JSONL_ARTIFACTS
REQUIRED_JSON = builder.JSON_ARTIFACTS
AUTHORITY_FALSE_FIELDS = builder.AUTHORITY_FALSE_FIELDS
ACTION_REQUEST_CLASSES = builder.ACTION_REQUEST_CLASSES
EVENT_CLASSES = builder.EVENT_CLASSES
SNAPSHOT_CLASSES = builder.SNAPSHOT_CLASSES
RECEIPT_CLASSES = builder.RECEIPT_CLASSES
ST12G_DESCRIPTOR_NAME = builder.ST12G_DESCRIPTOR_NAME
ST12G_CONTRACT_MANIFEST_REF = builder.ST12G_CONTRACT_MANIFEST_REF

REGISTRY_REQUIRED_FIELDS = (
    "registry_row_id",
    "service_domain",
    "service_object_type",
    "service_object_id",
    "service_object_version",
    "generated_from",
    "builder_name",
    "validator_name",
    "manual_edit_allowed",
    "source_readiness_registry_ref_or_gap",
    "source_readiness_projection_ref_or_gap",
    "source_pretrade_registry_ref_or_gap",
    "source_pretrade_projection_ref_or_gap",
    "source_owner_dashboard_state_ref_or_gap",
    "source_owner_surface_resolver_ref_or_gap",
    "source_owner_action_registry_ref_or_gap",
    "source_owner_ux_semantic_bundle_ref_or_gap",
    "source_owner_conversation_state_ref_or_gap",
    "source_owner_search_index_ref_or_gap",
    "source_owner_layout_profile_ref_or_gap",
    "source_owner_notification_tier_ref_or_gap",
    "source_mobile_app_shell_contract_ref_or_gap",
    "source_pwa_contract_ref_or_gap",
    "trade_plan_candidate_ref_or_gap",
    "pretrade_decision_candidate_ref_or_gap",
    "no_trade_candidate_ref_or_gap",
    "qku_refs",
    "formula_refs",
    "algorithm_refs_or_gap",
    "computable_contract_refs_or_gap",
    "test_vector_refs_or_gap",
    "candidate_external_info_lane_ref_or_gap",
    "owner_read_model_snapshot_ref",
    "owner_read_model_section",
    "owner_surface_route_ref_or_gap",
    "owner_widget_ref_or_gap",
    "owner_chart_ref_or_gap",
    "owner_action_ref_or_gap",
    "owner_conversation_route_ref_or_gap",
    "owner_plain_english_intent_route_ref_or_gap",
    "owner_chat_route_preview_ref_or_gap",
    "owner_research_intake_route_ref_or_gap",
    "owner_trade_intent_route_ref_or_gap",
    "owner_search_index_route_ref_or_gap",
    "owner_layout_profile_route_ref_or_gap",
    "owner_notification_tier_policy_ref_or_gap",
    "owner_stale_data_banner_ref_or_gap",
    "mobile_app_shell_contract_ref_or_gap",
    "mobile_navigation_contract_ref_or_gap",
    "trade_workbench_route_ref_or_gap",
    "execution_ladder_stage_ref_or_gap",
    "owner_plain_english_title",
    "owner_plain_english_summary",
    "owner_status_copy",
    "why_this_matters_copy",
    "what_owner_can_do_next_copy",
    "trading_relevance_copy",
    "risk_plain_english_copy",
    "missing_information_copy",
    "technical_details_ref_or_gap",
    "developer_mode_ref_or_gap",
    "owner_trading_command_authority_allowed",
    "owner_trading_command_authority_scope",
    "direct_venue_submit_bypass_allowed",
    "execution_router_release_allowed",
    "owner_request_available",
    "owner_review_available",
    "owner_approval_preview_available",
    "owner_veto_available",
    "owner_pause_available",
    "owner_rollback_request_available",
    "owner_kill_switch_request_available",
    "provider_state",
    "provider_stage",
    "freshness_state",
    "stale_state_policy",
    "last_snapshot_time_or_static_build_time",
    "snapshot_delta_policy_ref_or_gap",
    "runtime_timestamp_created",
    "fake_runtime_status_created",
    "fake_receipt_created",
    "activation_state",
    "lifecycle_state",
    "timing_state",
    "downstream_owner",
    "authority_state",
    "source_authority_state",
    "external_candidate_lane_ref_or_gap",
    "projection_consumers",
    "orphan_status",
    "route_gap_reason_or_none",
    "validation_state",
    "fail_closed_reasons",
    "event_stream_contract_ref_or_gap",
    "event_cursor_ref_or_gap",
    "action_request_ref_or_gap",
    "action_receipt_ref_or_gap",
    "action_eligibility_ref_or_gap",
    "action_denied_reason_ref_or_gap",
    "action_confirmation_policy_ref_or_gap",
    "action_request_natural_key",
    "action_dedupe_policy_ref_or_gap",
    "action_risk_class_ref_or_gap",
    "owner_next_step_route_ref_or_gap",
    "target_surface_id_or_gap",
    "target_workflow_id_or_gap",
    "target_step_id_or_gap",
    "prefill_context_refs_or_gap",
    "creates_local_receipt_preview",
    "runtime_side_effect_allowed",
    "what_happens_next_copy_or_gap",
    "what_will_not_happen_now_copy_or_gap",
    "responsible_agent_role_refs",
    "supporting_agent_role_refs_or_gap",
    "escalation_agent_role_refs_or_gap",
    "agent_roster_discovery_audit_ref_or_gap",
    "agent_duty_source_crosswalk_ref_or_gap",
    "agent_workflow_stage",
    "agent_next_stage_route_ref_or_gap",
    "agent_operations_view_ref_or_gap",
    "team_workflow_queue_ref_or_gap",
    "owner_agent_state_ref_or_gap",
    "owner_workflow_queue_state_ref_or_gap",
    "agent_pod_ref_or_gap",
    "agent_status_preview_state",
    "agent_trust_score_ref_or_gap",
    "agent_kpi_route_ref_or_gap",
    "agent_quarantine_route_ref_or_gap",
    "agent_reroute_control_ref_or_gap",
    "expected_receipt_classes",
    "agent_llm_task_route_ref_or_gap",
    "llm_grounding_route_ref_or_gap",
    "llm_review_prompt_contract_ref_or_gap",
    "runtime_llm_call_created",
    "llm_source_truth_created",
    "llm_order_authority_created",
    "llm_profit_claim_created",
    "institutional_control_refs",
    "execution_adjusted_ranking_view_ref_or_gap",
    "tca_decomposition_view_ref_or_gap",
    "overfit_fdr_control_view_ref_or_gap",
    "portfolio_diversification_view_ref_or_gap",
    "capacity_crowding_view_ref_or_gap",
    "champion_challenger_view_ref_or_gap",
    "regime_memory_prior_view_ref_or_gap",
    "marginal_utility_view_ref_or_gap",
    "quantum_structural_readiness_view_ref_or_gap",
    "dag_route_view_ref_or_gap",
    "no_trade_margin_view_ref_or_gap",
    "calibration_view_ref_or_gap",
    "scenario_ladder_view_ref_or_gap",
    "mode_authority_ref_or_gap",
    "connector_route_ref_or_gap",
    "execution_router_route_ref_or_gap",
    "hotpath_handoff_route_ref_or_gap",
    "metrics_capture_route_ref_or_gap",
    "paper_loop_route_ref_or_gap",
    "shadow_route_ref_or_gap",
    "live_dryrun_route_ref_or_gap",
    "postlaunch_route_ref_or_gap",
    "telegram_route_ref_or_gap",
    "mobile_route_ref_or_gap",
    "plugin_route_ref_or_gap",
    "qmap_route_ref_or_gap",
    "allowlist_route_ref_or_gap",
    "control_plane_only",
    "live_critical_path_allowed",
    "precomputed_snapshot_route_ref_or_gap",
    "runtime_recompute_required",
    "dashboard_rendering_required_in_live_path",
    "source_retrieval_allowed_in_live_path",
    "llm_call_allowed_in_live_path",
    "quantum_backend_call_allowed_in_live_path",
    "master_plan_compilation_allowed_in_live_path",
    "read_model_runtime_side_effect_allowed",
    "network_server_started",
    "direct_venue_submit_authority_created",
    "execution_router_release_authority_created",
    "order_submission_created",
    "replay_execution_created",
    "paper_execution_created",
    "shadow_execution_created",
    "live_execution_created",
    "connector_read_created",
    "connector_write_created",
    "private_cash_account_read_created",
    "runtime_agent_execution_created",
    "runtime_metrics_created",
    "runtime_plugin_created",
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "quantum_order_authority_created",
    "profit_claim_created",
    "qtt_sha_authority_created",
    "atomicrows_hash_authority_created",
)


class ValidationError(RuntimeError):
    pass


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _artifact_dir(repo_root: Path, path: Path) -> Path:
    artifact_dir = path if path.is_absolute() else repo_root / path
    return artifact_dir.resolve()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    _assert(isinstance(payload, dict), f"{path} is not a JSON object")
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            _assert(isinstance(payload, dict), f"{path}:{line_number} is not a JSON object")
            rows.append(payload)
    return rows


def _validate_filenames(artifact_dir: Path) -> None:
    _assert(artifact_dir.name == "pr169_svc1", "validator must target SVC1 owned prefix")
    for path in artifact_dir.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(artifact_dir).as_posix()
        _assert("future" not in relative.lower(), f"forbidden future filename: {relative}")
        _assert("_hint" not in relative.lower(), f"forbidden weak hint filename: {relative}")
        _assert(
            relative != "pretrade_execution_ladder_handoff.generated.jsonl",
            "must not create duplicate stale pretrade_execution_ladder_handoff.generated.jsonl",
        )


def _load_all(artifact_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    rows_by_file: dict[str, list[dict[str, Any]]] = {}
    reports: dict[str, dict[str, Any]] = {}
    for file_name in REQUIRED_JSONL:
        path = artifact_dir / file_name
        _assert(path.exists(), f"missing required SVC1 JSONL artifact: {file_name}")
        rows = _load_jsonl(path)
        _assert(rows, f"required SVC1 JSONL artifact is empty: {file_name}")
        rows_by_file[file_name] = rows
    for file_name in REQUIRED_JSON:
        path = artifact_dir / file_name
        _assert(path.exists(), f"missing required SVC1 JSON artifact: {file_name}")
        reports[file_name] = _load_json(path)
    return rows_by_file, reports


def _validate_registry(rows: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for row in rows:
        missing = [field for field in REGISTRY_REQUIRED_FIELDS if field not in row]
        _assert(not missing, f"registry row {row.get('registry_row_id')} missing fields: {missing[:10]}")
        row_id = str(row["registry_row_id"])
        _assert(row_id not in seen, f"duplicate registry_row_id: {row_id}")
        seen.add(row_id)
        _assert(row["generated_from"] == REGISTRY_REF, f"{row_id} generated_from drift")
        _assert(row["builder_name"] == BUILDER_NAME, f"{row_id} builder drift")
        _assert(row["validator_name"] == VALIDATOR_NAME, f"{row_id} validator drift")
        _assert(row["manual_edit_allowed"] is False, f"{row_id} allows manual edit")
        _assert(row["service_object_version"] == PROJECTION_VERSION, f"{row_id} version drift")
        _assert(row["orphan_status"] in {"NOT_ORPHAN", "SCOPED_GAP_ROUTED"}, f"{row_id} orphan state invalid")
        _assert(row["control_plane_only"] is True, f"{row_id} not control-plane only")
        _assert(row["live_critical_path_allowed"] is False, f"{row_id} live critical path widened")
        _assert(row["owner_trading_command_authority_allowed"] is True, f"{row_id} owner command authority missing")
        _assert(row["direct_venue_submit_bypass_allowed"] is False, f"{row_id} direct submit bypass widened")
        _assert(row["execution_router_release_allowed"] is False, f"{row_id} execution router release widened")
        _assert(row["projection_consumers"], f"{row_id} has no projection consumers")
        _assert(row["responsible_agent_role_refs"], f"{row_id} has no responsible agent refs")
        _assert(row["agent_roster_discovery_audit_ref_or_gap"], f"{row_id} missing agent roster audit ref")
        _assert(row["agent_duty_source_crosswalk_ref_or_gap"], f"{row_id} missing agent duty crosswalk ref")
        _assert(row["qku_refs"], f"{row_id} missing QKU refs")
        _assert(row["formula_refs"], f"{row_id} missing formula refs")
        _assert(row["owner_plain_english_summary"], f"{row_id} missing owner summary")
        _assert(row["what_will_not_happen_now_copy_or_gap"], f"{row_id} missing no-runtime owner copy")
        for field in AUTHORITY_FALSE_FIELDS:
            if field in row:
                _assert(row[field] is False, f"{field} widened in {row_id}")


def _validate_projection_metadata(rows_by_file: dict[str, list[dict[str, Any]]]) -> None:
    registry_ids = {str(row["registry_row_id"]) for row in rows_by_file["service_registry.jsonl"]}
    for file_name, rows in rows_by_file.items():
        for row in rows:
            row_id = str(row.get("registry_row_id", ""))
            _assert(row.get("generated_from") == REGISTRY_REF, f"{file_name}:{row_id} generated_from drift")
            _assert(row.get("manual_edit_allowed") is False, f"{file_name}:{row_id} allows manual edit")
            _assert(row_id in registry_ids, f"{file_name}:{row_id} is not in canonical registry")
            _assert(row.get("source_registry_row_id") in registry_ids, f"{file_name}:{row_id} source registry missing")
            _assert(row.get("source_registry_ref", "").startswith(f"{REGISTRY_REF}::"), f"{file_name}:{row_id} source registry ref invalid")


def _validate_actions(rows_by_file: dict[str, list[dict[str, Any]]]) -> None:
    requests = rows_by_file["owner_action_requests.generated.jsonl"]
    action_codes = {str(row["action_code"]) for row in requests}
    _assert(set(ACTION_REQUEST_CLASSES) <= action_codes, "missing required owner action request classes")
    denied_seen = False
    for row in requests:
        row_id = row["registry_row_id"]
        if str(row["eligible_state"]).startswith("ELIGIBLE"):
            _assert(row["eligibility_proof_ref_or_gap"], f"{row_id} missing eligibility proof")
        else:
            denied_seen = True
            _assert(row["denied_reason_ref_or_gap"], f"{row_id} missing denied reason")
        _assert(row["audit_receipt_class"], f"{row_id} missing receipt class")
        _assert(row["action_request_natural_key"], f"{row_id} missing natural key")
        _assert(row["dedupe_policy_ref_or_gap"], f"{row_id} missing dedupe policy")
        _assert(row["required_confirmation_class"], f"{row_id} missing confirmation class")
        _assert(row["risk_class"], f"{row_id} missing risk class")
        _assert(row["owner_trading_command_authority_allowed"] is True, f"{row_id} missing owner command authority")
        _assert(row["direct_submit_created"] is False, f"{row_id} created direct submit")
        _assert(row["execution_router_release_created"] is False, f"{row_id} created execution release")
        _assert(row["order_submission_created"] is False, f"{row_id} created order submission")
        _assert(row["private_cash_read_created"] is False, f"{row_id} created private cash read")
        _assert(row["runtime_llm_call_created"] is False, f"{row_id} created runtime LLM call")
        _assert(row["runtime_agent_execution_created"] is False, f"{row_id} created runtime agent execution")
    _assert(denied_seen, "at least one disabled/direct-submit boundary action is required")

    next_steps = rows_by_file["owner_next_step_routes.generated.jsonl"]
    _assert({str(row["action_code"]) for row in next_steps} >= set(ACTION_REQUEST_CLASSES), "next-step routes missing action codes")
    _assert(
        any(row.get("next_step_route_id") == "LIVE_ORDER_SUBMIT_DISABLED" for row in next_steps),
        "OwnerNextStepRouter must include LIVE_ORDER_SUBMIT_DISABLED route",
    )
    for row in next_steps:
        _assert(row["target_surface_id"], f"{row['registry_row_id']} missing target surface")
        _assert(row["target_workflow_id"], f"{row['registry_row_id']} missing target workflow")
        _assert(row["target_step_id"], f"{row['registry_row_id']} missing target step")
        _assert(row["runtime_side_effect_allowed"] is False, f"{row['registry_row_id']} next step has side effect")


def _validate_events_and_receipts(rows_by_file: dict[str, list[dict[str, Any]]]) -> None:
    events = rows_by_file["event_stream_contracts.generated.jsonl"]
    _assert(set(EVENT_CLASSES) <= {str(row["event_class"]) for row in events}, "missing event classes")
    for row in events + rows_by_file["audit_receipt_stream.generated.jsonl"]:
        _assert(row["event_sample_state"] == "CONTRACT_SAMPLE_NOT_RUNTIME_EVENT", f"{row['registry_row_id']} fakes runtime event")
        _assert(row["fake_receipt_created"] is False, f"{row['registry_row_id']} fake receipt created")
        _assert(row["runtime_timestamp_created"] is False, f"{row['registry_row_id']} fake timestamp created")
    receipts = rows_by_file["owner_action_receipts.generated.jsonl"]
    _assert(receipts, "owner action receipts missing")
    for row in receipts:
        _assert(set(RECEIPT_CLASSES) & set(row["expected_receipt_classes"]), f"{row['registry_row_id']} missing expected receipt classes")
        _assert(row["receipt_contract_only"] is True, f"{row['registry_row_id']} receipt is not contract-only")


def _validate_snapshots(rows_by_file: dict[str, list[dict[str, Any]]]) -> None:
    snapshots = rows_by_file["read_model_snapshots.generated.jsonl"]
    classes = {str(row["snapshot_class"]) for row in snapshots}
    _assert(set(SNAPSHOT_CLASSES) <= classes, "missing read-model snapshot classes")
    for row in snapshots:
        row_id = row["registry_row_id"]
        for field in (
            "snapshot_id",
            "title",
            "plain_english_summary",
            "status",
            "why_this_matters",
            "what_owner_can_do_next",
            "visible_trading_relevance",
            "related_qtt_agents",
            "related_llm_route",
            "related_workflow_stage",
            "provider_state",
            "freshness_state",
            "stale_warning",
            "candidate_refs",
            "qku_formula_refs_collapsed",
        ):
            _assert(row.get(field), f"{row_id} missing snapshot field {field}")
        _assert(row["technical_details_collapsed_by_default"] is True, f"{row_id} raw refs not collapsed")
        _assert(row["developer_mode_required_for_raw_refs"] is True, f"{row_id} developer mode not required")
        _assert(row["fake_pnl_cash_fill_live_position_data_created"] is False, f"{row_id} fake runtime data created")


def _validate_institutional_quantum(rows_by_file: dict[str, list[dict[str, Any]]]) -> None:
    institutional_files = (
        "execution_adjusted_ranking_views.generated.jsonl",
        "tca_decomposition_views.generated.jsonl",
        "overfit_fdr_control_views.generated.jsonl",
        "portfolio_diversification_views.generated.jsonl",
        "capacity_crowding_views.generated.jsonl",
        "champion_challenger_views.generated.jsonl",
        "regime_memory_prior_views.generated.jsonl",
        "marginal_utility_views.generated.jsonl",
        "quantum_structural_readiness_views.generated.jsonl",
        "scenario_ladder_views.generated.jsonl",
        "calibration_views.generated.jsonl",
        "downstream_dag_route_views.generated.jsonl",
    )
    for file_name in institutional_files:
        _assert(rows_by_file[file_name], f"{file_name} is empty")

    for row in rows_by_file["execution_adjusted_ranking_views.generated.jsonl"]:
        for field in (
            "expected_net_cash_ref_or_gap",
            "candidate_minus_no_trade_ref_or_gap",
            "lower_confidence_bound_ref_or_gap",
            "fill_adjusted_ev_ref_or_gap",
            "capacity_adjusted_ev_ref_or_gap",
            "portfolio_marginal_utility_ref_or_gap",
            "fdr_overfit_status_ref_or_gap",
            "tca_decomposition_ref_or_gap",
            "latency_budget_ref_or_gap",
            "scenario_ladder_ref_or_gap",
            "calibration_ref_or_gap",
            "agent_route_ref_or_gap",
            "no_orphan_route_ref_or_gap",
        ):
            _assert(row.get(field), f"{row['registry_row_id']} missing ranking field {field}")
        _assert(row["ranking_is_view_only"] is True, f"{row['registry_row_id']} ranking mutated")
        _assert(row["ranking_recomputed_by_svc1"] is False, f"{row['registry_row_id']} ranking recomputed")

    for row in rows_by_file["tca_decomposition_views.generated.jsonl"]:
        _assert(row["tca_is_explicit_not_vague_score"] is True, f"{row['registry_row_id']} TCA is vague")
        for field in (
            "fees_ref_or_gap",
            "spread_cost_ref_or_gap",
            "slippage_ref_or_gap",
            "market_impact_ref_or_gap",
            "opportunity_cost_ref_or_gap",
            "cancel_replace_cost_ref_or_gap",
            "latency_drag_ref_or_gap",
            "adverse_selection_ref_or_gap",
            "settlement_cashflow_ref_or_gap",
            "capacity_crowding_ref_or_gap",
        ):
            _assert(row.get(field), f"{row['registry_row_id']} missing TCA field {field}")

    for row in rows_by_file["regime_memory_prior_views.generated.jsonl"]:
        _assert(row["memory_is_prior_not_proof"] is True, f"{row['registry_row_id']} memory used as proof")
        _assert(row["memory_update_receipt_created"] is False, f"{row['registry_row_id']} created memory receipt")

    for row in rows_by_file["quantum_structural_readiness_views.generated.jsonl"]:
        for field in (
            "objective_function_route_ref_or_gap",
            "variable_encoding_route_ref_or_gap",
            "constraint_route_ref_or_gap",
            "penalty_scaling_route_ref_or_gap",
            "coefficient_scaling_route_ref_or_gap",
            "classical_exact_or_heuristic_comparator_ref_or_gap",
            "fallback_route_ref_or_gap",
        ):
            _assert(row.get(field), f"{row['registry_row_id']} missing quantum field {field}")
        _assert(row["quantum_backend_execution_created"] is False, f"{row['registry_row_id']} created quantum backend")
        _assert(row["quantum_advantage_claim_created"] is False, f"{row['registry_row_id']} claimed quantum advantage")
        _assert(row["quantum_order_authority_created"] is False, f"{row['registry_row_id']} created quantum order authority")


def _validate_agent_llm_qku_routes(rows_by_file: dict[str, list[dict[str, Any]]]) -> None:
    for file_name in (
        "qku_formula_compute_route_views.generated.jsonl",
        "agent_llm_task_route_views.generated.jsonl",
        "llm_grounding_route_views.generated.jsonl",
        "agent_operations_views.generated.jsonl",
        "team_workflow_queue_views.generated.jsonl",
        "owner_agent_state_views.generated.jsonl",
        "owner_workflow_queue_state_views.generated.jsonl",
    ):
        rows = rows_by_file[file_name]
        _assert(rows, f"{file_name} is empty")
        for row in rows:
            _assert(row["responsible_agent_role_refs"], f"{row['registry_row_id']} missing agent roles")
            _assert(row["agent_roster_discovery_audit_ref_or_gap"], f"{row['registry_row_id']} missing PR165-D2 audit ref")
            _assert(row["agent_duty_source_crosswalk_ref_or_gap"], f"{row['registry_row_id']} missing PR165-D2 crosswalk ref")
            _assert(row["llm_grounding_route_ref_or_gap"], f"{row['registry_row_id']} missing LLM grounding route")
            _assert(row["runtime_llm_call_created"] is False, f"{row['registry_row_id']} created runtime LLM")
            _assert(row["runtime_agent_execution_created"] is False, f"{row['registry_row_id']} created runtime agent execution")
            _assert(row["order_authority_created"] is False, f"{row['registry_row_id']} created order authority")

    for row in rows_by_file["qku_formula_compute_route_views.generated.jsonl"]:
        _assert(row["qku_refs"], f"{row['registry_row_id']} missing qku refs")
        _assert(row["formula_refs"], f"{row['registry_row_id']} missing formula refs")
        _assert(row["computable_contract_refs_or_gap"], f"{row['registry_row_id']} missing computable contract")
        for field in (
            "paper_loop_route_ref_or_gap",
            "hotpath_handoff_route_ref_or_gap",
            "live_dryrun_route_ref_or_gap",
            "shadow_route_ref_or_gap",
            "plugin_route_ref_or_gap",
            "qmap_route_ref_or_gap",
            "allowlist_route_ref_or_gap",
        ):
            _assert(row.get(field), f"{row['registry_row_id']} missing downstream {field}")


def _validate_surface_chat_mobile_expansion(rows_by_file: dict[str, list[dict[str, Any]]]) -> None:
    for file_name in (
        "owner_ux_semantic_routes.generated.jsonl",
        "owner_copy_map.generated.jsonl",
        "owner_widget_manifest.generated.jsonl",
        "owner_chart_manifest.generated.jsonl",
        "owner_mode_technical_disclosure.generated.jsonl",
        "professional_provider_pending_frames.generated.jsonl",
        "surface_parity_routes.generated.jsonl",
        "cross_surface_state_contract.generated.jsonl",
        "owner_conversation_views.generated.jsonl",
        "owner_plain_english_intent_routes.generated.jsonl",
        "owner_chat_route_previews.generated.jsonl",
        "owner_research_intake_routes.generated.jsonl",
        "owner_trade_intent_routes.generated.jsonl",
        "owner_search_index_routes.generated.jsonl",
        "owner_mode_policy.generated.jsonl",
        "owner_layout_profile_routes.generated.jsonl",
        "owner_notification_tier_policy.generated.jsonl",
        "owner_stale_data_banner_views.generated.jsonl",
        "mobile_app_shell_contract_views.generated.jsonl",
        "mobile_navigation_contract_views.generated.jsonl",
        "trade_workbench_route_views.generated.jsonl",
        "execution_ladder_stage_views.generated.jsonl",
        "ui_visual_qa_handoff_views.generated.jsonl",
        "market_venue_expansion_socket_routes.generated.jsonl",
        "qku_formula_intake_route_views.generated.jsonl",
        "plugin_qmap_allowlist_route_views.generated.jsonl",
        "reality_model_installation_socket_views.generated.jsonl",
    ):
        _assert(rows_by_file[file_name], f"{file_name} is empty")

    for row in rows_by_file["professional_provider_pending_frames.generated.jsonl"]:
        _assert(row["fake_pnl_cash_fill_live_position_data_created"] is False, f"{row['registry_row_id']} fake chart data")

    for row in rows_by_file["cross_surface_state_contract.generated.jsonl"] + rows_by_file["mobile_app_shell_contract_views.generated.jsonl"]:
        for field in (
            "desktop_dashboard_route_state",
            "mobile_web_route_state",
            "pwa_route_state",
            "native_mobile_route_state",
            "telegram_mirror_route_state",
            "shared_state_id_state",
            "shared_action_id_state",
            "shared_widget_id_state",
            "shared_chart_id_state",
            "shared_chat_id_state",
            "shared_receipt_id_state",
            "no_mobile_only_fork_proof",
            "no_telegram_second_governance_plane_proof",
        ):
            _assert(row.get(field), f"{row['registry_row_id']} missing surface parity {field}")
        _assert(row["service_worker_runtime_created"] is False, f"{row['registry_row_id']} created service worker")
        _assert(row["push_notification_runtime_created"] is False, f"{row['registry_row_id']} created push runtime")
        _assert(row["native_mobile_runtime_created"] is False, f"{row['registry_row_id']} created native runtime")

    for row in rows_by_file["owner_plain_english_intent_routes.generated.jsonl"]:
        _assert(row["parser_contract_ref"].startswith("NaturalLanguageOwnerIntentParserContractV1"), f"{row['registry_row_id']} missing parser contract")
        _assert(row["runtime_llm_call_created"] is False, f"{row['registry_row_id']} created runtime LLM")
        _assert(row["source_truth_created"] is False, f"{row['registry_row_id']} created source truth")
        _assert(row["source_family"], f"{row['registry_row_id']} missing source families")

    for row in rows_by_file["market_venue_expansion_socket_routes.generated.jsonl"]:
        for field in (
            "required_market_adapter_route_or_gap",
            "required_connector_semantic_route_or_gap",
            "required_replay_data_route_or_gap",
            "required_paper_validation_route_or_gap",
            "required_live_dryrun_route_or_gap",
            "required_risk_cash_settlement_route_or_gap",
            "required_execution_router_route_or_gap",
            "no_scattered_market_logic_proof",
        ):
            _assert(row.get(field), f"{row['registry_row_id']} missing expansion socket {field}")
        _assert(row["connector_read_created"] is False, f"{row['registry_row_id']} created connector read")

    for row in rows_by_file["execution_ladder_stage_views.generated.jsonl"]:
        _assert(
            row["upstream_current_equivalent_ref"] == builder.PRETRADE_EXEC_LADDER_EQUIVALENT_REF,
            f"{row['registry_row_id']} does not use actual pretrade exec ladder current equivalent",
        )


def _validate_reports(reports: dict[str, dict[str, Any]]) -> None:
    for file_name, report in reports.items():
        _assert(report.get("acceptance_state") == "PASS", f"{file_name} not PASS")
        _assert(report.get("manual_edit_allowed") is False, f"{file_name} allows manual edits")
    quality = reports["service_quality_gates.report.json"]
    _assert(quality["acceptance_state"] == "PASS", "service quality gates not PASS")
    _assert(quality["readiness1_consumption_state"].startswith("PASS"), "READINESS1 not consumed")
    _assert(quality["pretrade1_consumption_state"].startswith("PASS"), "PRETRADE1 not consumed")
    _assert(quality["mem1_upstream_only_state"].startswith("PASS"), "MEM1 not prior-only")
    manifest = reports["service_manifest.json"]
    _assert(manifest["canonical_registry_ref"] == REGISTRY_REF, "manifest registry drift")
    _assert(manifest["phase0_mapping"], "manifest missing Phase-0 mapping")
    mapping = manifest["phase0_mapping"]
    _assert(
        any(row["current_equivalent_path_or_absent"] == builder.PRETRADE_EXEC_LADDER_EQUIVALENT_REF for row in mapping),
        "Phase-0 mapping missing pretrade exec ladder current equivalent",
    )


def _validate_st12g_descriptor(
    artifact_dir: Path, reports: dict[str, dict[str, Any]]
) -> None:
    path = artifact_dir / ST12G_DESCRIPTOR_NAME
    _assert(path.exists(), f"missing SVC1 ST12-G descriptor: {path}")
    rows = _load_jsonl(path)
    expected = {
        "descriptor_id": "ST12G-DESCRIPTOR::SVC1",
        "contract_version": "2.0",
        "consumer_id": "SVC1",
        "contract_type": "ST12GServiceEvidenceViewV2",
        "source_contract_manifest_ref": ST12G_CONTRACT_MANIFEST_REF,
        "canonical_owner_ref": "PR169_SVC1_SERVICE_REGISTRY_AND_READ_MODEL_FABRIC",
        "runtime_instance_state": "NOT_MATERIALIZED_BY_REPOSITORY_BUILD",
        "manual_edit_allowed": False,
        "runtime_effect_allowed": False,
        "write_authority": "NONE",
        "downstream_route_refs": ["SVC1", "DASH1_UI1"],
    }
    _assert(rows == [expected], "SVC1 ST12-G descriptor differs")
    artifact_refs = {
        item.get("artifact_ref")
        for item in reports["service_manifest.json"].get("generated_artifacts", [])
    }
    _assert(
        (GENERATED_PREFIX / ST12G_DESCRIPTOR_NAME).as_posix() in artifact_refs,
        "SVC1 manifest omits ST12-G descriptor",
    )
    _assert(
        reports["no_orphan.report.json"].get("st12g_contract_descriptor_count")
        == 1,
        "SVC1 no-orphan report omits ST12-G descriptor",
    )


def _validate_no_raw_runtime_scan(repo_root: Path) -> None:
    resolver = repo_root / "src/qtt/service/pr169_svc1_resolvers.py"
    _assert(resolver.exists(), "SVC1 resolver missing")
    text = resolver.read_text(encoding="utf-8")
    forbidden = (
        "pr169_pretrade1",
        "pr169_readiness1",
        "rglob(",
        ".glob(",
        "docs/master_plan/generated/**/*.jsonl",
        "openai",
        "import requests",
        "requests.get(",
        "requests.post(",
        "requests.put(",
        "requests.delete(",
        "socket.",
        "subprocess.",
    )
    for marker in forbidden:
        _assert(marker not in text, f"resolver contains forbidden runtime scan/network marker: {marker}")


def _validate_current_equivalent(repo_root: Path, artifact_dir: Path) -> None:
    actual = repo_root / builder.PRETRADE_EXEC_LADDER_EQUIVALENT_REF
    stale_upstream = repo_root / "docs/master_plan/generated/pr169_pretrade1/pretrade_execution_ladder_handoff.generated.jsonl"
    stale_svc1 = artifact_dir / "pretrade_execution_ladder_handoff.generated.jsonl"
    _assert(actual.exists(), "actual pretrade exec ladder current-equivalent file is missing")
    _assert(not stale_upstream.exists(), "stale upstream pretrade_execution_ladder_handoff.generated.jsonl exists")
    _assert(not stale_svc1.exists(), "SVC1 created stale duplicate pretrade_execution_ladder_handoff.generated.jsonl")


def validate(repo_root: Path, artifact_dir: Path) -> None:
    _assert(artifact_dir.exists(), f"artifact directory missing: {artifact_dir}")
    _validate_filenames(artifact_dir)
    rows_by_file, reports = _load_all(artifact_dir)
    _validate_registry(rows_by_file["service_registry.jsonl"])
    _validate_projection_metadata(rows_by_file)
    _validate_actions(rows_by_file)
    _validate_events_and_receipts(rows_by_file)
    _validate_snapshots(rows_by_file)
    _validate_institutional_quantum(rows_by_file)
    _validate_agent_llm_qku_routes(rows_by_file)
    _validate_surface_chat_mobile_expansion(rows_by_file)
    _validate_reports(reports)
    _validate_st12g_descriptor(artifact_dir, reports)
    _validate_no_raw_runtime_scan(repo_root)
    _validate_current_equivalent(repo_root, artifact_dir)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--artifact-dir", type=Path, default=GENERATED_PREFIX)
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    artifact_dir = _artifact_dir(repo_root, args.artifact_dir)
    validate(repo_root, artifact_dir)
    print(f"validated PR169-SVC1 artifacts at {artifact_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
