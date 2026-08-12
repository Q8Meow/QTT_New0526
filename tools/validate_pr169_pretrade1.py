#!/usr/bin/env python3
"""Validate PR169-PRETRADE1 generated pretrade artifacts."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any, Iterable, Sequence


GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_pretrade1")
REGISTRY_REF = "docs/master_plan/generated/pr169_pretrade1/pretrade_decision_registry.jsonl"
BUILDER_NAME = "tools/build_pr169_pretrade1.py"
VALIDATOR_NAME = "tools/validate_pr169_pretrade1.py"
PROJECTION_VERSION = "PR169-PRETRADE1-v2.8S2"
ST12G_DESCRIPTOR_NAME = "st12g_evidence_projection_contract.generated.jsonl"
ST12G_CONTRACT_MANIFEST_REF = (
    "docs/master_plan/generated/qku_control_plane/"
    "existing_owner_projection/st12g_projection_contract_manifest.json"
)

REQUIRED_JSONL = (
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

REQUIRED_JSON = (
    "pretrade_manifest.json",
    "no_orphan.report.json",
    "no_submit_authority.report.json",
    "no_raw_jsonl_scan.report.json",
    "no_placeholder_materialization.report.json",
    "pretrade_quality_gates.report.json",
    "market_installation_acceptance.report.json",
)

REGISTRY_REQUIRED_FIELDS = (
    "pretrade_registry_row_id",
    "candidate_id",
    "readiness1_registry_row_ref",
    "readiness1_computable_contract_ref",
    "trade_plan_candidate_ref",
    "trade_plan_binding_ref_or_gap",
    "qku_refs",
    "formula_refs",
    "market_family",
    "venue_scope",
    "platform_scope",
    "agent_role_refs",
    "mem1_memory_ref_or_gap",
    "pretrade_decision_candidate_id",
    "pretrade_packet_state",
    "no_trade_candidate_ref_or_gap",
    "order_policy_candidate_set_ref_or_gap",
    "scenario_ladder_decision_ref_or_gap",
    "latency_budget_decision_ref_or_gap",
    "mode_authority_matrix_ref_or_gap",
    "pretrade_objective_kernel_ref_or_gap",
    "contract_payoff_model_ref_or_gap",
    "market_state_quality_gate_ref_or_gap",
    "probability_calibration_gate_ref_or_gap",
    "pretrade_model_validity_horizon_ref_or_gap",
    "pretrade_agent_access_path_audit_ref_or_gap",
    "pretrade_edge_alpha_capture_map_ref_or_gap",
    "source_coverage_handoff_ref_or_gap",
    "downstream_consumer_refs",
    "no_raw_jsonl_scan_proof_ref",
    "orphan_status",
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

COMPONENT_FAMILIES = {
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
}

ALLOWED_DECISION_STATES = {
    "PRETRADE_PASS_PROVIDER_PENDING",
    "PRETRADE_PASS_REPLAY_CANDIDATE",
    "PRETRADE_PASS_PAPER_CANDIDATE",
    "PRETRADE_REQUIRES_REPAIR_OR_RETEST",
    "PRETRADE_NO_TRADE_WINS",
    "PRETRADE_BLOCKED_BY_REALITY_MODEL_GAP",
    "PRETRADE_BLOCKED_BY_SOURCE_EVIDENCE_GAP",
    "PRETRADE_BLOCKED_BY_CASHFLOW_GAP",
    "PRETRADE_BLOCKED_BY_CONNECTOR_ROUTE_GAP",
    "PRETRADE_BLOCKED_BY_AGENT_ROUTE_GAP",
    "PRETRADE_REJECT_UNSAFE_DUPLICATE_IRRELEVANT_OR_UNMAPPABLE",
}

EXACT_MODEL_ID_FIELDS = {
    "venue_reality_models.generated.jsonl": "venue_reality_model_id",
    "fee_models.generated.jsonl": "fee_model_id",
    "fill_models.generated.jsonl": "fill_model_id",
    "slippage_models.generated.jsonl": "slippage_model_id",
    "latency_decay_models.generated.jsonl": "latency_decay_model_id",
    "queue_position_models.generated.jsonl": "queue_position_model_id",
    "partial_fill_models.generated.jsonl": "partial_fill_model_id",
    "capacity_crowding_models.generated.jsonl": "capacity_crowding_model_id",
    "adverse_selection_models.generated.jsonl": "adverse_selection_model_id",
    "settlement_resolution_models.generated.jsonl": "settlement_resolution_model_id",
    "cashflow_models.generated.jsonl": "cashflow_model_id",
    "order_policy_reality_models.generated.jsonl": "order_policy_reality_model_id",
}


class ValidationError(RuntimeError):
    pass


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            _assert(isinstance(payload, dict), f"{path}:{line_number} is not a JSON object")
            rows.append(payload)
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    _assert(isinstance(payload, dict), f"{path} is not a JSON object")
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


def _artifact_dir(repo_root: Path, artifact_dir: Path | None) -> Path:
    path = artifact_dir or GENERATED_PREFIX
    return path if path.is_absolute() else repo_root / path


def _projection_name(name: str) -> str:
    return Path(name).name.replace(".generated.jsonl", "").replace(".jsonl", "")


def _load_all(artifact_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    reports: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_JSONL:
        path = artifact_dir / name
        _assert(path.exists(), f"missing PRETRADE1 JSONL artifact: {path}")
        rows[name] = _read_jsonl(path)
    for name in REQUIRED_JSON:
        path = artifact_dir / name
        _assert(path.exists(), f"missing PRETRADE1 JSON artifact: {path}")
        reports[name] = _read_json(path)
    return rows, reports


def _validate_filenames(artifact_dir: Path) -> None:
    expected = set(REQUIRED_JSONL) | set(REQUIRED_JSON) | {ST12G_DESCRIPTOR_NAME}
    actual = {path.name for path in artifact_dir.iterdir() if path.is_file()}
    _assert(expected <= actual, "not all required artifacts are present")
    for name in actual:
        _assert("_hint" not in name, f"weak hint filename is forbidden: {name}")
        _assert("future" not in name.lower(), f"future-style filename is forbidden: {name}")
        _assert(name in expected, f"unexpected artifact in PRETRADE1 owned prefix: {name}")


def _validate_projection_metadata(rows_by_file: dict[str, list[dict[str, Any]]]) -> None:
    for name, rows in rows_by_file.items():
        _assert(rows, f"{name} has no rows")
        expected_projection = _projection_name(name)
        for row in rows:
            _assert(row.get("generated_from") == REGISTRY_REF, f"{name} row missing generated_from")
            _assert(row.get("manual_edit_allowed") is False, f"{name} row allows manual edits")
            _assert(row.get("authoritative_source") == REGISTRY_REF, f"{name} row missing authoritative_source")
            _assert(row.get("projection_name") == expected_projection, f"{name} row has wrong projection_name")
            _assert(row.get("projection_version") == PROJECTION_VERSION, f"{name} row has wrong version")
            _assert(row.get("builder_name") == BUILDER_NAME, f"{name} row has wrong builder")
            _assert(row.get("validator_name") == VALIDATOR_NAME, f"{name} row has wrong validator")


def _validate_authority(rows_by_file: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]]) -> None:
    for name, rows in rows_by_file.items():
        for row in rows:
            for field in AUTHORITY_FALSE_FIELDS:
                if field in row:
                    _assert(row[field] is False, f"{name} field {field} is not false")
            for value in _walk_values(row):
                if isinstance(value, str):
                    _assert("QTT_SHA_AUTHORITY_CREATED_TRUE" not in value, f"{name} leaks QTT SHA authority")
                    _assert("ATOMICROWS_HASH_AUTHORITY_CREATED_TRUE" not in value, f"{name} leaks AtomicRows hash authority")
    for report_name, report in reports.items():
        for field in AUTHORITY_FALSE_FIELDS:
            if field in report:
                _assert(report[field] is False, f"{report_name} field {field} is not false")


def _validate_registry(registry: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for row in registry:
        missing = [field for field in REGISTRY_REQUIRED_FIELDS if field not in row]
        _assert(not missing, f"registry row missing fields: {missing}")
        candidate_id = str(row["candidate_id"])
        _assert(candidate_id not in seen, f"duplicate candidate_id: {candidate_id}")
        seen.add(candidate_id)
        _assert(row["qku_refs"], f"{candidate_id} missing qku refs")
        _assert(row["formula_refs"], f"{candidate_id} missing formula refs")
        _assert(row["agent_role_refs"], f"{candidate_id} missing agent role refs")
        _assert("pr169_readiness1" in row["readiness1_registry_row_ref"], f"{candidate_id} does not consume READINESS1")
        _assert("pr168_mem1" in row["mem1_memory_ref_or_gap"], f"{candidate_id} does not consume MEM1 as upstream ref")
        _assert(row["orphan_status"] == "NOT_ORPHANED_ROUTE_PROOF_PRESENT", f"{candidate_id} orphan status failed")
        _assert(row["mode_authority_state"] == "NO_SUBMIT_NO_RUNTIME_PRETRADE_ONLY", f"{candidate_id} authority state widened")
        _assert(row["pretrade_packet_state"] in ALLOWED_DECISION_STATES, f"{candidate_id} invalid pretrade_packet_state")
        _assert(row.get("pretrade_decision_state") in ALLOWED_DECISION_STATES, f"{candidate_id} invalid pretrade_decision_state")
        for field in (
            "pretrade_memory_prior_reval_ref_or_gap",
            "pretrade_recovery_frontier_ref_or_gap",
            "pretrade_venue_policy_matrix_ref_or_gap",
            "pretrade_edge_attribution_ref_or_gap",
            "pretrade_exec_ladder_handoff_ref_or_gap",
            "expected_net_cash_value_state",
            "expected_net_cash_lcb_state",
            "no_trade_margin_state",
        ):
            _assert(row.get(field), f"{candidate_id} missing registry contract field {field}")
        _assert(row["downstream_consumer_refs"], f"{candidate_id} missing downstream consumers")
        for field in AUTHORITY_FALSE_FIELDS:
            if field in row:
                _assert(row[field] is False, f"{candidate_id} authority field {field} is not false")


def _validate_reality_contracts(rows_by_file: dict[str, list[dict[str, Any]]]) -> None:
    registry = rows_by_file["pretrade_decision_registry.jsonl"]
    candidate_ids = {row["candidate_id"] for row in registry}
    contracts = rows_by_file["reality_model_component_contracts.generated.jsonl"]
    by_candidate: dict[str, set[str]] = {candidate_id: set() for candidate_id in candidate_ids}
    for row in contracts:
        cid = row["candidate_id"]
        by_candidate.setdefault(cid, set()).add(row["component_family"])
        for field in (
            "input_schema_ref_or_inline_contract",
            "output_schema_ref_or_inline_contract",
            "unit_or_basis",
            "scale_contract",
            "normalization_contract",
            "missing_value_policy",
            "source_authority_state",
            "unlock_route_ref_or_gap",
        ):
            _assert(row.get(field), f"component contract missing {field}: {row.get('reality_component_contract_id')}")
    for candidate_id, families in by_candidate.items():
        _assert(COMPONENT_FAMILIES <= families, f"{candidate_id} missing component contracts: {COMPONENT_FAMILIES - families}")
    for filename, id_field in EXACT_MODEL_ID_FIELDS.items():
        for row in rows_by_file[filename]:
            _assert(row.get(id_field), f"{filename} missing exact model id field {id_field}")
            _assert(row.get("source_authority_state") == "CANDIDATE_RESEARCH_PROVISIONAL_NOT_SOURCE_TRUTH", f"{filename} source authority widened")


def _validate_pretrade_specific(rows_by_file: dict[str, list[dict[str, Any]]]) -> None:
    candidate_ids = {row["candidate_id"] for row in rows_by_file["pretrade_decision_registry.jsonl"]}
    for name in (
        "pretrade_decision_candidates.generated.jsonl",
        "pretrade_objective_kernels.generated.jsonl",
        "contract_payoff_models.generated.jsonl",
        "market_state_quality_gates.generated.jsonl",
        "probability_calibration_gates.generated.jsonl",
        "pretrade_model_validity_horizon.generated.jsonl",
        "pretrade_edge_alpha_capture_map.generated.jsonl",
        "pretrade_memory_prior_reval.generated.jsonl",
        "pretrade_recovery_frontiers.generated.jsonl",
        "pretrade_edge_attribution.generated.jsonl",
        "pretrade_exec_ladder_handoff.generated.jsonl",
    ):
        projected = {row["candidate_id"] for row in rows_by_file[name] if "candidate_id" in row}
        _assert(candidate_ids <= projected, f"{name} does not cover every registry candidate")

    for row in rows_by_file["pretrade_memory_prior_reval.generated.jsonl"]:
        _assert(row["current_snapshot_revalidation_required"] is True, "MEM1 prior does not require revalidation")
        for field in ("memory_prior_used_as_proof", "mem1_redone", "parallel_memory_registry_created", "mem1_generated_artifact_modified", "memory_authority_created", "memory_update_receipt_created"):
            _assert(row.get(field) is False, f"MEM1 boundary field {field} is not false")

    for row in rows_by_file["clean_room_default_candidates.generated.jsonl"]:
        _assert(row["clean_room_flag"] is True, "clean-room row missing clean_room_flag")
        _assert(row["replay_paper_calibration_required"] is True, "clean-room row does not require calibration")
        for field in ("confidential_or_restricted_input_flag", "nda_or_confidential_input_flag", "improper_access_flag", "credentialed_competitor_system_flag", "proprietary_claim_flag", "accepted_source_truth_created"):
            _assert(row.get(field) is False, f"clean-room field {field} is not false")

    venue_rows = rows_by_file["pretrade_venue_policy_matrix.generated.jsonl"]
    venues = {row["venue_scope"] for row in venue_rows}
    _assert({"KALSHI", "POLYMARKET", "FORECASTEX_IBKR"} <= venues, "Stage-1 venue matrix incomplete")
    for row in venue_rows:
        _assert(row["cross_venue_generalization_allowed"] is False, "cross-venue generalization allowed")

    for row in rows_by_file["pretrade_exec_ladder_handoff.generated.jsonl"]:
        verbs = set(row["allowed_downstream_action_verbs"])
        _assert({"BUY", "SELL", "OPEN", "CLOSE", "CANCEL", "REPLACE", "REDUCE", "EXIT"} <= verbs, "execution ladder missing action verbs")
        for field in ("buy_sell_open_close_executed", "order_compilation_created", "venue_submit_created", "execution_router_release_created", "paper_execution_created", "replay_execution_created", "shadow_execution_created", "live_execution_created"):
            _assert(row.get(field) is False, f"execution ladder field {field} is not false")

    for row in rows_by_file["pretrade_recovery_frontiers.generated.jsonl"]:
        for field in ("terminal_dead_end_created", "global_qku_formula_ban_created", "formula_mutation_created"):
            _assert(row.get(field) is False, f"recovery frontier field {field} is not false")

    for row in rows_by_file["pretrade_edge_attribution.generated.jsonl"]:
        for field in ("realized_pnl_created", "live_receipt_created", "paper_receipt_created", "profit_claim_created"):
            _assert(row.get(field) is False, f"edge attribution field {field} is not false")

    for row in rows_by_file["pretrade_decision_candidates.generated.jsonl"]:
        _assert(row["pretrade_decision_state"] in ALLOWED_DECISION_STATES, "decision candidate has invalid state")
        for field in (
            "trade_plan_candidate_ref",
            "readiness1_registry_row_ref",
            "qku_refs",
            "formula_refs",
            "no_trade_candidate_ref",
            "scenario_ladder_decision_ref",
            "venue_reality_model_ref",
            "tca_decomposition_ref",
            "pretrade_agent_access_path_audit_ref_or_gap",
            "pretrade_edge_alpha_capture_map_ref_or_gap",
            "pretrade_memory_prior_reval_ref_or_gap",
            "pretrade_recovery_frontier_ref_or_gap",
            "pretrade_venue_policy_matrix_ref_or_gap",
            "pretrade_edge_attribution_ref_or_gap",
        ):
            _assert(row.get(field), f"decision candidate missing {field}")

    for row in rows_by_file["tca_decomposition.generated.jsonl"]:
        for field in (
            "explicit_fee_component_ref_or_gap",
            "spread_cost_component_ref_or_gap",
            "slippage_component_ref_or_gap",
            "latency_drag_component_ref_or_gap",
            "queue_cost_component_ref_or_gap",
            "partial_fill_cost_component_ref_or_gap",
            "adverse_selection_component_ref_or_gap",
            "settlement_cashflow_component_ref_or_gap",
            "net_expected_cash_after_cost_ref_or_gap",
            "lower_confidence_bound_ref_or_gap",
        ):
            _assert(row.get(field), f"TCA row missing {field}")

    for row in rows_by_file["agent_workflow_obs_handoff.generated.jsonl"]:
        _assert(row.get("responsible_pr165_d2_agent_roles"), "workflow obs missing responsible agents")
        _assert(row.get("expected_downstream_workflow_stage"), "workflow obs missing stage")
        _assert(row.get("expected_receipt_classes"), "workflow obs missing receipt classes")

    for row in rows_by_file["pretrade_gate_snapshot_handoff.generated.jsonl"]:
        for field in (
            "source_retrieval_in_live_path_allowed",
            "dashboard_rendering_in_live_path_allowed",
            "replay_paper_recalculation_in_live_path_allowed",
            "llm_call_in_live_path_allowed",
            "quantum_backend_call_in_live_path_allowed",
        ):
            _assert(row.get(field) is False, f"gate snapshot live-path field {field} is not false")


def _validate_reports(rows_by_file: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]]) -> None:
    for name, report in reports.items():
        _assert(report.get("generated_from") == REGISTRY_REF, f"{name} missing generated_from")
        _assert(report.get("manual_edit_allowed") is False, f"{name} allows manual edits")
        _assert(report.get("authoritative_source") == REGISTRY_REF, f"{name} missing authoritative source")
        _assert(report.get("builder_name") == BUILDER_NAME, f"{name} wrong builder")
        _assert(report.get("validator_name") == VALIDATOR_NAME, f"{name} wrong validator")
        _assert(report.get("acceptance_state") == "PASS", f"{name} did not pass")
    _assert(reports["no_orphan.report.json"]["orphan_count"] == 0, "orphan report has orphan rows")
    _assert(reports["no_raw_jsonl_scan.report.json"]["blocked_paths"] == [], "raw JSONL scan report has blocked paths")
    _assert(reports["no_raw_jsonl_scan.report.json"]["runtime_resolver_created"] is False, "runtime resolver created")
    quality = reports["pretrade_quality_gates.report.json"]
    for field in (
        "readiness1_consumed_not_redone",
        "mem1_consumed_as_prior_not_redone",
        "one_canonical_registry",
        "one_builder",
        "one_validator",
        "edge_alpha_capture_map_present",
        "artifact_value_route_map_present",
        "agent_access_path_audit_present",
        "execution_ladder_handoff_present",
        "memory_prior_revalidation_present",
        "expected_edge_attribution_present",
    ):
        _assert(quality.get(field) is True, f"quality gate {field} is not true")
    for field in (
        "readiness1_consumption_state",
        "reality_model_coverage_state",
        "no_orphan_coverage_state",
        "agent_llm_packet_route_state",
        "execution_router_handoff_state",
        "authority_boundary_state",
        "metrics_capture_handoff_state",
        "agent_workflow_observability_state",
        "artifact_value_route_map_state",
        "execution_ladder_handoff_state",
        "clean_room_default_candidate_lane_state",
        "agent_access_path_audit_state",
        "edge_alpha_capture_map_state",
        "memory_prior_revalidation_state",
        "recovery_frontier_state",
        "venue_policy_matrix_state",
        "edge_attribution_state",
    ):
        _assert(str(quality.get(field, "")).startswith("PASS"), f"quality gate state {field} did not pass")
    for field in (
        "actual_buy_sell_open_close_created",
        "runtime_market_connector_created",
        "runtime_metrics_created",
        "live_receipt_created",
        "fake_agent_status_created",
        "fake_queue_item_created",
        "fake_timestamp_created",
        "runtime_receipt_created",
        "execution_router_release_created",
        "raw_jsonl_runtime_scan_used",
        "full_library_default_access_created",
        "memory_prior_used_as_proof",
        "mem1_redone",
        "parallel_memory_registry_created",
        "mem1_generated_artifact_modified",
        "memory_update_receipt_created",
        "terminal_dead_end_created",
        "global_qku_formula_ban_created",
        "cross_venue_generalization_allowed",
        "realized_pnl_created",
    ):
        _assert(quality.get(field) is False, f"quality gate forbidden field {field} is not false")
    no_submit = reports["no_submit_authority.report.json"]
    forbidden_count_fields = [key for key in no_submit if key.endswith("_count") and key not in {
        "pretrade_packet_count",
        "reality_model_component_count",
        "market_onboarding_handoff_count",
        "order_simulation_spec_count",
        "assumption_ledger_count",
        "model_risk_control_count",
        "parameter_operability_count",
        "gate_snapshot_handoff_count",
    }]
    for field in forbidden_count_fields:
        _assert(no_submit[field] == 0, f"no-submit forbidden count {field} is not zero")
    market = reports["market_installation_acceptance.report.json"]
    for field in (
        "model_component_family_coverage_state",
        "adapter_route_coverage_state",
        "source_evidence_route_coverage_state",
        "owner_surface_route_coverage_state",
        "agent_route_coverage_state",
        "llm_grounding_route_coverage_state",
        "paper_loop_route_coverage_state",
        "hotpath_route_coverage_state",
        "live_dryrun_route_coverage_state",
        "execution_router_route_coverage_state",
        "qmap_route_coverage_state",
        "allowlist_route_coverage_state",
    ):
        _assert(str(market.get(field, "")).startswith("PASS"), f"market report {field} did not pass")
    for field in (
        "runtime_connector_created",
        "connector_read_created",
        "connector_write_created",
        "venue_semantics_accepted",
        "order_authority_created",
        "profit_claim_created",
    ):
        _assert(market.get(field) is False, f"market report forbidden field {field} is not false")

    manifest = reports["pretrade_manifest.json"]
    artifact_refs = {item.get("artifact_ref") for item in manifest.get("generated_artifacts", [])}
    expected_refs = {_as_ref(name) for name in (*REQUIRED_JSONL, *REQUIRED_JSON)}
    _assert(expected_refs <= artifact_refs, "manifest missing generated artifacts")
    route_rows = rows_by_file["pretrade_artifact_value_route_map.generated.jsonl"]
    routed_files = {row["source_generated_file"] for row in route_rows}
    missing_routes = expected_refs - routed_files
    _assert(not missing_routes, f"artifact/value route map missing files: {sorted(missing_routes)}")


def _as_ref(name: str) -> str:
    return (GENERATED_PREFIX / name).as_posix()


def _source_reads(path: Path) -> set[str]:
    if not path.exists():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    reads: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value.replace("\\", "/")
            if "docs/master_plan/generated" in value and value.endswith(".jsonl"):
                reads.add(value)
    return reads


def _validate_central_resolver(repo_root: Path) -> None:
    resolver = repo_root / "src/qtt/pretrade/pr169_pretrade1_resolvers.py"
    _assert(resolver.exists(), "Session 2 requires the PRETRADE1 central resolver")
    reads = _source_reads(resolver)
    _assert(reads <= {REGISTRY_REF}, f"resolver reads unexpected generated JSONL paths: {sorted(reads)}")


def _validate_st12g_descriptor(artifact_dir: Path, reports: dict[str, dict[str, Any]]) -> None:
    rows = _read_jsonl(artifact_dir / ST12G_DESCRIPTOR_NAME)
    expected = {
        "descriptor_id": "ST12G-DESCRIPTOR::PRETRADE1",
        "contract_version": "2.0",
        "consumer_id": "PRETRADE1",
        "contract_type": "ST12GPretradeEvidenceProjectionV2",
        "source_contract_manifest_ref": ST12G_CONTRACT_MANIFEST_REF,
        "canonical_owner_ref": "PR169_PRETRADE1_CANONICAL_REGISTRY_AND_RESOLVER",
        "runtime_instance_state": "NOT_MATERIALIZED_BY_REPOSITORY_BUILD",
        "manual_edit_allowed": False,
        "runtime_effect_allowed": False,
        "write_authority": "NONE",
        "downstream_route_refs": ["PRETRADE1"],
    }
    _assert(rows == [expected], "PRETRADE1 ST12-G descriptor differs")
    artifact_refs = {
        item.get("artifact_ref")
        for item in reports["pretrade_manifest.json"].get("generated_artifacts", [])
    }
    _assert(
        _as_ref(ST12G_DESCRIPTOR_NAME) in artifact_refs,
        "PRETRADE1 manifest omits ST12-G descriptor",
    )
    _assert(
        reports["no_orphan.report.json"].get("st12g_contract_descriptor_count")
        == 1,
        "PRETRADE1 no-orphan report omits ST12-G descriptor",
    )


def validate(repo_root: Path, artifact_dir: Path) -> None:
    _assert(artifact_dir.name == "pr169_pretrade1", "validator must target PRETRADE1 owned prefix")
    _assert(artifact_dir.exists(), f"artifact directory missing: {artifact_dir}")
    _validate_filenames(artifact_dir)
    rows_by_file, reports = _load_all(artifact_dir)
    _validate_projection_metadata(rows_by_file)
    _validate_registry(rows_by_file["pretrade_decision_registry.jsonl"])
    _validate_authority(rows_by_file, reports)
    _validate_reality_contracts(rows_by_file)
    _validate_pretrade_specific(rows_by_file)
    _validate_reports(rows_by_file, reports)
    _validate_st12g_descriptor(artifact_dir, reports)
    _validate_central_resolver(repo_root)
    builder_reads = _source_reads(repo_root / BUILDER_NAME)
    _assert("docs/master_plan/generated/pr168_mem1/memory_query_receipt.jsonl" not in builder_reads, "builder must not consume MEM1 receipts as truth")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--artifact-dir", type=Path, default=GENERATED_PREFIX)
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    artifact_dir = _artifact_dir(repo_root, args.artifact_dir)
    validate(repo_root, artifact_dir)
    print(f"validated PR169-PRETRADE1 artifacts at {artifact_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
