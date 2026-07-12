#!/usr/bin/env python3
"""Validate PR169-READINESS1 generated readiness artifacts."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any, Iterable, Sequence


GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_readiness1")
REGISTRY_REF = "docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl"
BUILDER_NAME = "tools/build_pr169_readiness1.py"
VALIDATOR_NAME = "tools/validate_pr169_readiness1.py"
PROJECTION_VERSION = "PR169-READINESS1-v4.3.1"

REQUIRED_JSONL = (
    "agent_readiness_registry.jsonl",
    "access_path_resolutions.generated.jsonl",
    "computable_contracts.generated.jsonl",
    "executable_now.generated.jsonl",
    "paper_loop_usable.generated.jsonl",
    "adapter_blocked.generated.jsonl",
    "unlock_queue.generated.jsonl",
    "agent_universe.generated.jsonl",
    "llm_view.generated.jsonl",
    "llm_grounding_view.generated.jsonl",
    "owner_command_routes.generated.jsonl",
    "owner_plain_english_intent_routes.generated.jsonl",
    "owner_chat_action_catalog_routes.generated.jsonl",
    "surface_parity_handoff.generated.jsonl",
    "owner_ux_semantic_bundle_handoff.generated.jsonl",
    "plugin_intake_handoff.generated.jsonl",
    "metrics_route_alias.generated.jsonl",
    "agent_kpi_trust_quarantine_handoff.generated.jsonl",
    "qku_formula_agent_compute_map.generated.jsonl",
    "trade_variable_search_handoff.generated.jsonl",
    "edge_alpha_decision_readiness.generated.jsonl",
    "order_scenario_tournament_handoff.generated.jsonl",
    "shadow_comparison_handoff.generated.jsonl",
    "execution_router_action_handoff.generated.jsonl",
    "connector_route_handoff.generated.jsonl",
    "agent_learning_handoff.generated.jsonl",
    "source_coverage_handoff.generated.jsonl",
    "parameter_operability_handoff.generated.jsonl",
    "owner_enablement_handoff.generated.jsonl",
    "consumer_routes.generated.jsonl",
    "readiness_scorecard.generated.jsonl",
    "institutional_controls.generated.jsonl",
    "quantum_readiness.generated.jsonl",
    "hotpath_handoff.generated.jsonl",
    "candidate_external_info_lanes.generated.jsonl",
    "readiness_gap_ledger.generated.jsonl",
)

REQUIRED_JSON = (
    "readiness_manifest.json",
    "no_orphan.report.json",
    "no_raw_jsonl_scan.report.json",
    "no_fake_readiness.report.json",
    "no_placeholder_materialization.report.json",
    "owner_three_question_coverage.report.json",
)

REGISTRY_REQUIRED_FIELDS = (
    "registry_row_id",
    "candidate_id",
    "trade_plan_candidate_ref",
    "qku_refs",
    "formula_refs",
    "algorithm_refs_or_gap",
    "parameter_stack_refs_or_gap",
    "market_family",
    "venue_scope",
    "platform_scope",
    "stage_activation_state",
    "stage1_prediction_market_applicability_state",
    "active_stage_profile_ref_or_gap",
    "market_applicability_ref_or_gap",
    "platform_applicability_ref_or_gap",
    "agent_access_policy_ref_or_gap",
    "stage_access_mode",
    "agent_role_refs",
    "agent_roster_discovery_audit_ref_or_gap",
    "agent_duty_source_crosswalk_ref_or_gap",
    "pr164_review_ref_or_gap",
    "pr163c_repair_ref_or_gap",
    "pr165_score_ref_or_gap",
    "rp5g_sim_ref_or_gap",
    "rank4_rank_ref_or_gap",
    "qopt1_optimization_ref_or_gap",
    "vs2_paper_intent_ref_or_gap",
    "mem1_memory_ref_or_gap",
    "route_triage_ref_or_gap",
    "master_plan_section_ref_or_gap",
    "market_specific_section_index_ref_or_gap",
    "command_action_matrix_ref_or_gap",
    "computable_contract_id",
    "computability_state",
    "computability_basis",
    "input_contract_state",
    "output_contract_state",
    "parameter_contract_state",
    "variable_contract_state",
    "test_vector_state",
    "units_or_scale_state",
    "executable_now_state",
    "executable_now_basis",
    "paper_loop_usable_state",
    "paper_loop_usable_basis",
    "adapter_blocker_family",
    "adapter_blocker_detail",
    "reality_model_blocker_detail_or_gap",
    "input_binding_blocker_detail_or_gap",
    "output_binding_blocker_detail_or_gap",
    "agent_route_blocker_detail_or_gap",
    "qstruct_blocker_detail_or_gap",
    "plugin_intake_blocker_detail_or_gap",
    "unlock_action_family",
    "unlock_priority_score",
    "readiness_score",
    "paper_loop_priority_score",
    "readiness_confidence",
    "source_evidence_state",
    "evidence_staleness_state",
    "candidate_external_info_lane_state",
    "deterministic_contract_coverage_state",
    "plain_english_owner_intent_route_ref_or_gap",
    "owner_command_route_ref_or_gap",
    "owner_chat_action_catalog_route_ref_or_gap",
    "surface_parity_route_ref_or_gap",
    "owner_ux_semantic_bundle_ref_or_gap",
    "dashboard_surface_registry_ref_or_gap",
    "owner_search_semantics_ref_or_gap",
    "owner_option_range_semantics_ref_or_gap",
    "owner_theme_preference_semantics_ref_or_gap",
    "owner_education_guide_semantics_ref_or_gap",
    "owner_chart_policy_ref_or_gap",
    "owner_drawer_semantics_ref_or_gap",
    "owner_preference_policy_ref_or_gap",
    "plugin_intake_handoff_ref_or_gap",
    "metrics_route_alias_ref_or_gap",
    "agent_kpi_trust_quarantine_route_ref_or_gap",
    "qku_formula_agent_compute_map_ref_or_gap",
    "trade_variable_search_handoff_ref_or_gap",
    "edge_alpha_decision_readiness_ref_or_gap",
    "order_scenario_tournament_ref_or_gap",
    "shadow_comparison_handoff_ref_or_gap",
    "execution_router_action_handoff_ref_or_gap",
    "universal_owner_enablement_matrix_ref_or_gap",
    "effective_live_write_state",
    "connector_route_handoff_ref_or_gap",
    "agent_learning_handoff_ref_or_gap",
    "source_coverage_handoff_ref_or_gap",
    "parameter_operability_handoff_ref_or_gap",
    "owner_enablement_handoff_ref_or_gap",
    "source_currentness_handoff_ref_or_gap",
    "owner_dashboard_route_ref_or_gap",
    "owner_conversation_state_ref_or_gap",
    "owner_widget_manifest_ref_or_gap",
    "owner_chart_manifest_ref_or_gap",
    "owner_surface_resolver_ref_or_gap",
    "llm_view_policy",
    "llm_grounding_view_ref_or_gap",
    "source_agnostic_intake_route_ref_or_gap",
    "pretrade_route_ref_or_gap",
    "paper_loop_route_ref_or_gap",
    "hotpath_route_ref_or_gap",
    "shadow_comparison_route_ref_or_gap",
    "live_dryrun_route_ref_or_gap",
    "live_pilot_route_ref_or_gap",
    "launch_route_ref_or_gap",
    "postlaunch_route_ref_or_gap",
    "plugin_route_ref_or_gap",
    "qmap_route_ref_or_gap",
    "allowlist_route_ref_or_gap",
    "runtime_side_effect_allowed",
    "source_truth_created",
    "order_authority_created",
    "runtime_llm_allowed",
    "connector_private_cash_read_allowed",
    "replay_execution_created",
    "paper_execution_created",
    "shadow_execution_created",
    "live_execution_created",
    "execution_router_release_created",
    "runtime_ui_service_created",
    "runtime_mobile_created",
    "runtime_telegram_created",
    "runtime_metrics_created",
    "runtime_plugin_created",
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "qtt_sha_authority_created",
    "atomicrows_hash_authority_created",
    "profit_claim_created",
    "downstream_consumer_refs",
    "no_raw_jsonl_scan_proof_ref",
    "orphan_status",
)

AUTHORITY_FALSE_FIELDS = (
    "runtime_side_effect_allowed",
    "source_truth_created",
    "order_authority_created",
    "runtime_llm_allowed",
    "connector_private_cash_read_allowed",
    "replay_execution_created",
    "paper_execution_created",
    "shadow_execution_created",
    "live_execution_created",
    "execution_router_release_created",
    "runtime_ui_service_created",
    "runtime_mobile_created",
    "runtime_telegram_created",
    "runtime_metrics_created",
    "runtime_plugin_created",
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "qtt_sha_authority_created",
    "atomicrows_hash_authority_created",
    "profit_claim_created",
    "runtime_llm_call_created",
    "agent_execution_created",
    "source_truth_created",
    "paper_execution_created",
    "shadow_execution_created",
    "live_execution_created",
    "order_authority_created",
    "execution_router_release_created",
    "connector_read_created",
    "connector_write_created",
    "private_cash_read_created",
    "venue_semantics_accepted",
    "live_order_authority_created",
    "runtime_plugin_created",
    "hot_reload_created",
    "live_formula_allowlist_created",
    "live_promotion_created",
    "runtime_metrics_ledger_created",
    "event_time_capture_created",
    "runtime_agent_kpi_created",
    "agent_self_healing_runtime_created",
    "agent_replacement_runtime_created",
    "agent_permission_expansion_allowed",
    "agent_live_authority_auto_grant_allowed",
    "agent_live_write_secret_access_auto_grant_allowed",
    "model_training_created",
    "model_inference_created",
    "live_learning_authority_created",
    "accepted_source_truth_created",
    "connector_semantics_created",
    "hardcoded_runtime_default_created",
    "live_authority_created",
    "connector_binding_created",
    "formula_mutation_created",
    "promotion_claim_created",
    "simulation_executed_in_this_pr",
    "buy_sell_open_close_executed",
    "order_compilation_created",
    "venue_submit_created",
    "live_enablement_created",
    "runtime_value_created",
    "live_value_authority_created",
    "q_backend_execution_allowed",
    "q_live_order_authority_allowed",
    "q_quantum_advantage_claim_created",
    "runtime_chat_service_created",
    "runtime_service_created",
    "mobile_runtime_created",
    "telegram_runtime_created",
    "pwa_service_worker_created",
    "direct_venue_submit_authority_created",
    "runtime_ui_service_created",
)

COMPUTABLE_CONTRACT_FIELDS = (
    "computable_contract_id",
    "candidate_id",
    "qku_refs",
    "formula_refs",
    "algorithm_refs_or_gap",
    "contract_kind",
    "symbolic_formula_ref_or_gap",
    "objective_ref_or_gap",
    "constraint_refs_or_gap",
    "input_schema_ref_or_inline_contract",
    "output_schema_ref_or_inline_contract",
    "parameter_stack_refs_or_gap",
    "required_market_fields",
    "required_venue_fields",
    "required_platform_fields",
    "required_time_fields",
    "required_price_fields",
    "required_liquidity_fields",
    "required_event_lifecycle_fields",
    "required_portfolio_fields",
    "required_latency_fields",
    "required_cost_fields",
    "variable_search_space_ref_or_gap",
    "unit_scale_contract",
    "normalization_contract",
    "missing_value_policy",
    "zero_denominator_policy_or_gap",
    "lookahead_leakage_guard_ref_or_gap",
    "asof_timestamp_policy_ref_or_gap",
    "source_evidence_refs_or_gap",
    "candidate_external_info_lane_ref_or_gap",
    "nonlive_test_vector_ref_or_gap",
    "expected_output_shape_or_gap",
    "execution_side_effect_allowed",
    "profit_claim_created",
    "contract_gap_reason_or_none",
    "unlock_route_ref_or_gap",
)


class ValidationError(RuntimeError):
    pass


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValidationError(f"{path}:{line_number} is not a JSON object")
            rows.append(payload)
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValidationError(f"{path} is not a JSON object")
    return payload


def _walk_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_values(nested)
    else:
        yield value


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _artifact_dir(repo_root: Path, artifact_dir: Path | None) -> Path:
    path = artifact_dir or GENERATED_PREFIX
    return path if path.is_absolute() else repo_root / path


def _load_all(repo_root: Path, artifact_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    reports: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_JSONL:
        path = artifact_dir / name
        _assert(path.exists(), f"missing READINESS1 JSONL artifact: {path}")
        rows[name] = _read_jsonl(path)
    for name in REQUIRED_JSON:
        path = artifact_dir / name
        _assert(path.exists(), f"missing READINESS1 JSON artifact: {path}")
        reports[name] = _read_json(path)
    _assert((artifact_dir / "pr_body.md").exists(), "missing READINESS1 PR body artifact")
    return rows, reports


def _validate_projection_metadata(rows_by_file: dict[str, list[dict[str, Any]]]) -> None:
    for name, rows in rows_by_file.items():
        projection_name = Path(name).name.replace(".generated.jsonl", "").replace(".jsonl", "")
        _assert(rows, f"{name} has no rows")
        for row in rows:
            if row.get("row_kind") == "PR169_FORMULA_OWNER_EXTENSION_V1":
                _assert(bool(row.get("readiness_projection_id")), f"{name} PR169 formula extension missing readiness id")
                _assert(bool(row.get("numeric_authority_chain_id")), f"{name} PR169 formula extension missing numeric authority")
                _assert(row.get("order_authority_created") is False, f"{name} PR169 formula extension widened authority")
                continue
            _assert(row.get("generated_from") == REGISTRY_REF, f"{name} row missing generated_from registry")
            _assert(row.get("manual_edit_allowed") is False, f"{name} row allows manual edits")
            _assert(row.get("authoritative_source") == REGISTRY_REF, f"{name} row missing authoritative source")
            _assert(row.get("projection_version") == PROJECTION_VERSION, f"{name} row has wrong projection version")
            _assert(row.get("builder_name") == BUILDER_NAME, f"{name} row has wrong builder")
            _assert(row.get("validator_name") == VALIDATOR_NAME, f"{name} row has wrong validator")
            _assert(row.get("projection_name") == projection_name, f"{name} row has wrong projection name")


def _validate_registry(registry: list[dict[str, Any]]) -> None:
    seen_ids: set[str] = set()
    for row in registry:
        missing = [field for field in REGISTRY_REQUIRED_FIELDS if field not in row]
        _assert(not missing, f"registry row missing fields: {missing}")
        candidate_id = str(row["candidate_id"])
        _assert(candidate_id not in seen_ids, f"duplicate registry candidate_id: {candidate_id}")
        seen_ids.add(candidate_id)
        _assert(row["qku_refs"], f"{candidate_id} missing qku refs")
        _assert(row["formula_refs"], f"{candidate_id} missing formula refs")
        _assert(row["computable_contract_id"], f"{candidate_id} missing computable contract")
        _assert(row["effective_live_write_state"] == "NOT_ARMED_IN_READINESS1", f"{candidate_id} has live write armed")
        _assert(row["orphan_status"] == "NOT_ORPHANED_ROUTE_PROOF_PRESENT", f"{candidate_id} orphan route proof missing")
        _assert(row["downstream_consumer_refs"], f"{candidate_id} has no downstream consumers")
        _assert(row["stage_access_mode"] == "CENTRAL_RESOLVER_PROJECTION_ONLY", f"{candidate_id} bypasses resolver projection")
        for field in AUTHORITY_FALSE_FIELDS:
            if field in row:
                _assert(row[field] is False, f"{candidate_id} authority field {field} is not false")
        if row["executable_now_state"] == "EXECUTABLE_NOW_NONLIVE_SAFE":
            _assert(row["computability_state"] == "COMPUTABLE_EXECUTABLE_NOW", f"{candidate_id} executable without computable state")
            _assert("DETERMINISTIC" in row["input_contract_state"], f"{candidate_id} executable without deterministic input")
            _assert("DETERMINISTIC" in row["output_contract_state"], f"{candidate_id} executable without deterministic output")
            _assert(row["test_vector_state"], f"{candidate_id} executable without test vector route")


def _validate_contracts(registry: list[dict[str, Any]], contracts: list[dict[str, Any]]) -> None:
    registry_contracts = {row["computable_contract_id"]: row["candidate_id"] for row in registry}
    contract_ids = {row.get("computable_contract_id") for row in contracts}
    _assert(set(registry_contracts) == contract_ids, "computable contracts do not match registry")
    for row in contracts:
        missing = [field for field in COMPUTABLE_CONTRACT_FIELDS if field not in row]
        _assert(not missing, f"computable contract missing fields: {missing}")
        _assert(row["qku_refs"], f"{row['candidate_id']} contract missing qku refs")
        _assert(row["formula_refs"], f"{row['candidate_id']} contract missing formula refs")
        _assert(row["execution_side_effect_allowed"] is False, "contract allows execution side effect")
        _assert(row["profit_claim_created"] is False, "contract creates profit claim")


def _validate_executable_now(registry: list[dict[str, Any]], executable: list[dict[str, Any]]) -> None:
    registry_by_candidate = {row["candidate_id"]: row for row in registry}
    for row in executable:
        candidate_id = row["candidate_id"]
        reg = registry_by_candidate[candidate_id]
        _assert(reg["executable_now_state"] == "EXECUTABLE_NOW_NONLIVE_SAFE", f"{candidate_id} executable projection not in registry")
        _assert(reg["computability_state"] == "COMPUTABLE_EXECUTABLE_NOW", f"{candidate_id} executable projection not computable")
        _assert(row["runtime_side_effect_allowed"] is False, f"{candidate_id} executable side effect allowed")
        _assert(row["source_truth_created"] is False, f"{candidate_id} executable creates source truth")
        _assert(row["order_authority_created"] is False, f"{candidate_id} executable creates order authority")
        _assert(row["profit_claim_created"] is False, f"{candidate_id} executable creates profit claim")


def _validate_route_artifacts(rows_by_file: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]]) -> None:
    registry = rows_by_file["agent_readiness_registry.jsonl"]
    candidate_ids = {row["candidate_id"] for row in registry}
    per_candidate_files = (
        "qku_formula_agent_compute_map.generated.jsonl",
        "trade_variable_search_handoff.generated.jsonl",
        "edge_alpha_decision_readiness.generated.jsonl",
        "order_scenario_tournament_handoff.generated.jsonl",
        "shadow_comparison_handoff.generated.jsonl",
        "execution_router_action_handoff.generated.jsonl",
        "connector_route_handoff.generated.jsonl",
        "agent_learning_handoff.generated.jsonl",
        "source_coverage_handoff.generated.jsonl",
        "owner_enablement_handoff.generated.jsonl",
        "owner_plain_english_intent_routes.generated.jsonl",
        "owner_chat_action_catalog_routes.generated.jsonl",
        "surface_parity_handoff.generated.jsonl",
        "owner_ux_semantic_bundle_handoff.generated.jsonl",
        "plugin_intake_handoff.generated.jsonl",
        "metrics_route_alias.generated.jsonl",
        "agent_kpi_trust_quarantine_handoff.generated.jsonl",
        "institutional_controls.generated.jsonl",
        "quantum_readiness.generated.jsonl",
        "candidate_external_info_lanes.generated.jsonl",
    )
    for name in per_candidate_files:
        projected_candidates = {row["candidate_id"] for row in rows_by_file[name]}
        _assert(candidate_ids <= projected_candidates, f"{name} does not cover every registry candidate")

    for row in rows_by_file["execution_router_action_handoff.generated.jsonl"]:
        _assert(row["effective_live_write_state"] == "NOT_ARMED_IN_READINESS1", "Execution Router handoff arms live write")
        _assert(row["execution_router_release_state"] == "PROVIDER_PENDING_DOWNSTREAM", "Execution Router release not provider-pending")
        for verb in ("BUY", "SELL", "OPEN", "CLOSE", "CANCEL", "REPLACE", "REDUCE", "EXIT"):
            _assert(verb in row["allowed_downstream_action_verbs"], f"missing action verb {verb}")
        for field in ("order_compilation_created", "venue_submit_created", "buy_sell_open_close_executed", "live_execution_created", "execution_router_release_created", "order_authority_created"):
            _assert(row[field] is False, f"Execution Router field {field} is not false")

    for row in rows_by_file["shadow_comparison_handoff.generated.jsonl"]:
        _assert(row["shadow_required_before_canary"] is False, "shadow made mandatory before canary")
        _assert(row["shadow_replaces_replay"] is False, "shadow replaces replay")
        _assert(row["shadow_replaces_paper"] is False, "shadow replaces paper")
        _assert(row["pre_live_gate_role_allowed"] is False, "shadow allowed as pre-live gate")
        _assert(row["shadow_execution_created"] is False, "shadow execution created")

    for row in rows_by_file["connector_route_handoff.generated.jsonl"]:
        for field in ("connector_read_created", "connector_write_created", "private_cash_read_created", "source_truth_created", "venue_semantics_accepted", "live_order_authority_created"):
            _assert(row[field] is False, f"connector field {field} is not false")

    for row in rows_by_file["source_coverage_handoff.generated.jsonl"]:
        _assert(row["assumption_family"], "source coverage missing assumption family")
        _assert(row["search_access_state"], "source coverage missing search access state")
        _assert(row["source_conflict_state"], "source coverage missing conflict state")
        _assert(row["remaining_uncertainty"], "source coverage missing uncertainty")
        _assert(row["candidate_external_info_lane_refs_or_gap"], "source coverage missing external lane")
        _assert(row["accepted_source_truth_created"] is False, "source coverage creates accepted source truth")

    owner = reports["owner_three_question_coverage.report.json"]
    _assert(owner["acceptance_state"] == "PASS", "owner three-question report did not pass")
    for field in (
        "q3_actual_buy_sell_open_close_created",
        "q3_runtime_agent_execution_created",
        "q3_runtime_llm_call_created",
        "q3_live_execution_created",
        "q3_execution_router_release_created",
    ):
        _assert(owner[field] is False, f"owner report field {field} is not false")


def _validate_manifest(rows_by_file: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]]) -> None:
    manifest = reports["readiness_manifest.json"]
    generated = manifest.get("generated_artifacts", [])
    artifact_refs = {item.get("artifact_ref") for item in generated}
    expected = {
        f"docs/master_plan/generated/pr169_readiness1/{name}"
        for name in (*REQUIRED_JSONL, *REQUIRED_JSON, "pr_body.md")
    }
    _assert(expected <= artifact_refs, "manifest missing generated artifact proof")
    for item in generated:
        for field in ("producer", "consumer", "validator", "downstream_route_proof", "orphan_status"):
            _assert(item.get(field), f"manifest artifact missing {field}: {item}")
        _assert(item["manual_edit_allowed"] is False, "manifest artifact allows manual edit")
    for report_name in (
        "no_orphan.report.json",
        "no_fake_readiness.report.json",
        "no_placeholder_materialization.report.json",
    ):
        _assert(reports[report_name]["acceptance_state"] == "PASS", f"{report_name} failed")
    _assert(reports["no_orphan.report.json"]["orphan_count"] == 0, "orphan report is not clean")
    _assert(reports["no_raw_jsonl_scan.report.json"]["blocked_paths"] == [], "raw JSONL scan report has blocked paths")


def _validate_no_placeholders(rows_by_file: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]]) -> None:
    banned_exact = {"TODO", "TBD", "needs work", "unknown"}
    for name, rows in rows_by_file.items():
        _assert("_hint" not in name, f"weak hint artifact filename found: {name}")
        _assert("future" not in name.lower(), f"future encoded in filename: {name}")
        for row in rows:
            for value in _walk_values(row):
                if isinstance(value, str):
                    _assert(value not in banned_exact, f"{name} contains vague placeholder: {value}")
    _assert(reports["no_placeholder_materialization.report.json"]["metadata_only_row_count"] == 0, "metadata-only rows passed")


def _source_reads(path: Path) -> set[str]:
    if not path.exists():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    reads: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "docs/master_plan/generated" in node.value and node.value.endswith(".jsonl"):
                reads.add(node.value.replace("\\", "/"))
    return reads


def _validate_no_raw_jsonl_runtime(repo_root: Path, reports: dict[str, dict[str, Any]]) -> None:
    resolver_reads = _source_reads(repo_root / "src/qtt/readiness/pr169_readiness1_resolvers.py")
    for ref in resolver_reads:
        _assert(ref.startswith("docs/master_plan/generated/pr169_readiness1/"), f"resolver reads upstream JSONL directly: {ref}")
    report = reports["no_raw_jsonl_scan.report.json"]
    _assert(report["result"] == "PASS", "no raw JSONL scan report failed")
    _assert(not report["blocked_paths"], "no raw JSONL scan report has blocked paths")


def _validate_all_authority_flags(rows_by_file: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]]) -> None:
    for name, rows in rows_by_file.items():
        for row in rows:
            for field in AUTHORITY_FALSE_FIELDS:
                if field in row:
                    _assert(row[field] is False, f"{name} field {field} is not false")
            for value in _walk_values(row):
                if isinstance(value, str):
                    _assert("PROFIT_PROOF_CREATION" not in value or row.get("projection_name") == "owner_chat_action_catalog_routes", "profit proof role leaked outside forbidden action list")
    for report in reports.values():
        for field in AUTHORITY_FALSE_FIELDS:
            if field in report:
                _assert(report[field] is False, f"report field {field} is not false")


def validate(repo_root: Path, artifact_dir: Path) -> None:
    rows_by_file, reports = _load_all(repo_root, artifact_dir)
    _validate_projection_metadata(rows_by_file)
    registry = rows_by_file["agent_readiness_registry.jsonl"]
    _validate_registry(registry)
    _validate_contracts(registry, rows_by_file["computable_contracts.generated.jsonl"])
    _validate_executable_now(registry, rows_by_file["executable_now.generated.jsonl"])
    _validate_route_artifacts(rows_by_file, reports)
    _validate_manifest(rows_by_file, reports)
    _validate_no_placeholders(rows_by_file, reports)
    _validate_no_raw_jsonl_runtime(repo_root, reports)
    _validate_all_authority_flags(rows_by_file, reports)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--artifact-dir", type=Path, default=GENERATED_PREFIX)
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    artifact_dir = _artifact_dir(repo_root, args.artifact_dir)
    validate(repo_root, artifact_dir)
    print(f"validated PR169-READINESS1 artifacts at {artifact_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
