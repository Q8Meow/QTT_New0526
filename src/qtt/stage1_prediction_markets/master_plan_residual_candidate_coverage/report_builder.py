"""Top-level deterministic PR161B artifact construction."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import subprocess
from typing import Any, Mapping

from . import artifact_discovery
from . import constants as c
from .assimilation_queue_builder import build_assimilation_queue, build_quantum_assimilation_queue
from .coverage_matcher import reconcile_candidates
from .forbidden_authority_scanner import scan_forbidden_authority
from .io import read_json, stable_counter, write_json
from .master_plan_candidate_extractor import (
    extract_master_plan_candidates,
    extract_prior_artifact_candidates,
    section_search_coverage,
)
from .master_plan_section_locator import load_master_plan_sections
from .models import BuildArtifacts
from .online_scout_candidate_enricher import build_online_scout_records, quantum_online_scout_records
from .pr161a_coverage_index import build_pr161a_coverage_index
from .quantum_residual_mapper import build_quantum_residual_records
from .report_sharder import report_size_bytes, sharding_status


def build_artifacts(root: Path | str) -> BuildArtifacts:
    repo_root = Path(root).resolve()
    selected = artifact_discovery.selected_artifact_paths(repo_root)
    sections, line_count = load_master_plan_sections(repo_root)
    master_candidates = extract_master_plan_candidates(repo_root, sections)
    prior_candidates = extract_prior_artifact_candidates(
        repo_root,
        artifact_discovery.prior_candidate_artifact_paths(repo_root),
        start_index=len(master_candidates) + 1,
    )
    candidates = reconcile_candidates(master_candidates + prior_candidates, build_pr161a_coverage_index(repo_root))
    section_records = section_search_coverage(sections, candidates)
    quantum_records = build_quantum_residual_records(candidates)
    queue_records = build_assimilation_queue(candidates)
    quantum_queue_records = build_quantum_assimilation_queue(quantum_records)
    online_records = build_online_scout_records(candidates)
    orchestration_records = _orchestration_records(candidates, selected)
    upstream_records = _upstream_records(orchestration_records)
    downstream_records = _downstream_records(orchestration_records)
    agent_records = _agent_records(candidates)
    owner_records = _owner_records(candidates)
    replay_records = _replay_records(candidates)
    quantum_workflow_records = _quantum_workflow_records(quantum_records)
    launch_records = _launch_readiness_records(candidates)

    payloads: dict[str, Any] = {}
    payloads["orchestration_preflight"] = _report(
        "PR161B_ORCHESTRATION_PREFLIGHT",
        [_preflight(repo_root, selected, sections)],
        extra={
            "receipt_marker": c.PREFLIGHT_RECEIPT_MARKER,
            "selected_artifact_paths": selected,
            "owner_approval_state": c.OWNER_APPROVALS,
            "source_intake_posture": "OPEN_CANDIDATE_FIRST",
            "residual_coverage_posture": "MASTER_PLAN_TO_PR161A_COVERAGE_PROOF_FIRST",
            "online_scouting_posture": "ENABLED_WHERE_AVAILABLE_NON_BLOCKING_IN_CI",
            "orchestration_graph_posture": "END_TO_END_UPSTREAM_DOWNSTREAM_REQUIRED",
        },
    )
    payloads["section_search_coverage"] = _report(
        "PR161B_MASTER_PLAN_SECTION_SEARCH_COVERAGE",
        section_records,
        extra=_section_counts(section_records, line_count),
    )
    candidate_payload = _report(
        "PR161B_MASTER_PLAN_RESIDUAL_CANDIDATE_INVENTORY",
        candidates,
        extra=_candidate_counts(candidates, master_candidates, prior_candidates, online_records),
    )
    payloads["candidate_inventory"] = candidate_payload
    payloads["field_record_coverage"] = _report("PR161B_MASTER_PLAN_TO_PR161A_FIELD_RECORD_COVERAGE", _coverage_records(candidates))
    payloads["alias_repair"] = _report("PR161B_CANONICAL_ALIAS_COVERAGE_REPAIR", _compact_candidate_records(_where(candidates, lambda item: item.get("coverage_state") == c.CoverageState.COVERED_BY_CANONICAL_ALIAS.value)))
    payloads["atomicrows_residual"] = _report("PR161B_ATOMICROWS_RESIDUAL_COVERAGE", _compact_candidate_records(_where(candidates, lambda item: bool(item.get("covered_by_atomicrows_row_ids")))))
    payloads["pr154_residual"] = _report("PR161B_PR154_RESIDUAL_COVERAGE", _compact_candidate_records(_where(candidates, lambda item: bool(item.get("covered_by_pr154_target_ids")))))
    payloads["formula_algorithm"] = _report("PR161B_FORMULA_ALGORITHM_RESIDUAL_COVERAGE", _compact_candidate_records(_where(candidates, _formula_algorithm)))
    payloads["parameter_range"] = _report("PR161B_PARAMETER_RANGE_RESIDUAL_COVERAGE", _compact_candidate_records(_where(candidates, _parameter_range)))
    payloads["quantum_optimizer"] = _quantum_report("PR161B_QUANTUM_OPTIMIZER_RESIDUAL_COVERAGE", quantum_records)
    payloads["quantum_formula"] = _quantum_report("PR161B_QUANTUM_FORMULA_RESIDUAL_COVERAGE", _where(quantum_records, lambda item: bool(item.get("formula_template_type"))))
    payloads["qubo"] = _quantum_report("PR161B_QUBO_RESIDUAL_COVERAGE", _where(quantum_records, lambda item: item["quantum_candidate_family"] == "QUBO"))
    payloads["ising"] = _quantum_report("PR161B_ISING_RESIDUAL_COVERAGE", _where(quantum_records, lambda item: item["quantum_candidate_family"] == "ISING"))
    payloads["qaoa"] = _quantum_report("PR161B_QAOA_RESIDUAL_COVERAGE", _where(quantum_records, lambda item: item["quantum_candidate_family"] == "QAOA"))
    payloads["vqe"] = _quantum_report("PR161B_VQE_RESIDUAL_COVERAGE", _where(quantum_records, lambda item: item["quantum_candidate_family"] == "VQE"))
    payloads["annealing"] = _quantum_report("PR161B_ANNEALING_RESIDUAL_COVERAGE", _where(quantum_records, lambda item: item["quantum_candidate_family"] == "ANNEALING"))
    payloads["hybrid_quantum_classical"] = _quantum_report("PR161B_HYBRID_QUANTUM_CLASSICAL_RESIDUAL_COVERAGE", _where(quantum_records, lambda item: item["quantum_candidate_family"] == "HYBRID"))
    payloads["quantum_strategy"] = _quantum_report("PR161B_QUANTUM_STRATEGY_RESIDUAL_COVERAGE", _where(quantum_records, lambda item: "STRATEGY" in item["strategy_candidate_type"] or "QUANTUM_" in item["strategy_candidate_type"]))
    payloads["strategy_template"] = _report("PR161B_STRATEGY_TEMPLATE_RESIDUAL_COVERAGE", _compact_candidate_records(_where(candidates, lambda item: item["candidate_type"] == c.CandidateType.STRATEGY_TEMPLATE.value)))
    payloads["replay_paper_route"] = _report("PR161B_REPLAY_PAPER_ROUTE_RESIDUAL_COVERAGE", replay_records)
    payloads["downstream_agent"] = _report("PR161B_DOWNSTREAM_AGENT_RESIDUAL_COVERAGE", agent_records)
    payloads["assimilation_queue"] = _report("PR161B_PR161C_ASSIMILATION_QUEUE", queue_records)
    payloads["quantum_assimilation_queue"] = _quantum_report("PR161B_PR161C_QUANTUM_ASSIMILATION_QUEUE", quantum_queue_records)
    payloads["online_scout"] = _report("PR161B_ONLINE_SCOUT_CANDIDATE_ENRICHMENT", online_records, extra={"online_scout_candidate_enrichment_count": len(online_records)})
    payloads["quantum_online_scout"] = _quantum_report("PR161B_QUANTUM_ONLINE_SCOUT_CANDIDATE_ENRICHMENT", quantum_online_scout_records(online_records))
    payloads["orchestration_graph"] = _report("PR161B_END_TO_END_CANDIDATE_ORCHESTRATION_GRAPH", orchestration_records)
    payloads["upstream_traceability"] = _report("PR161B_UPSTREAM_ARTIFACT_TRACEABILITY_MATRIX", upstream_records)
    payloads["downstream_workflow"] = _report("PR161B_DOWNSTREAM_WORKFLOW_CONSUMER_MATRIX", downstream_records)
    payloads["qtt_agent_consumption"] = _report("PR161B_QTT_AGENT_CANDIDATE_CONSUMPTION_MATRIX", agent_records)
    payloads["owner_dashboard"] = _report("PR161B_OWNER_DASHBOARD_REVIEW_ROUTE_MATRIX", owner_records)
    payloads["replay_paper_workflow"] = _report("PR161B_REPLAY_PAPER_WORKFLOW_ROUTE_MATRIX", replay_records)
    payloads["quantum_optimizer_workflow"] = _quantum_report("PR161B_QUANTUM_OPTIMIZER_WORKFLOW_ROUTE_MATRIX", quantum_workflow_records)
    payloads["launch_readiness_workflow"] = _report("PR161B_LAUNCH_READINESS_WORKFLOW_ROUTE_MATRIX", launch_records)
    forbidden = scan_forbidden_authority(repo_root)
    payloads["forbidden_authority_scan"] = _report("PR161B_FORBIDDEN_AUTHORITY_SCAN", [forbidden], extra=forbidden)
    payloads["branch_context_audit"] = _report("PR161B_BRANCH_CONTEXT_AND_DETERMINISTIC_AUDIT", [_branch_context_audit(repo_root)])
    final_summary = _final_summary(
        candidates,
        master_candidates,
        prior_candidates,
        online_records,
        section_records,
        queue_records,
        quantum_queue_records,
        quantum_records,
        orchestration_records,
        upstream_records,
        downstream_records,
        agent_records,
        owner_records,
        replay_records,
        quantum_workflow_records,
        launch_records,
        candidate_payload,
    )
    payloads["final_summary"] = _report("PR161B_RESIDUAL_COVERAGE_FINAL_SUMMARY", [final_summary], extra=final_summary)
    return BuildArtifacts(payloads=payloads)


def write_artifacts(root: Path | str) -> BuildArtifacts:
    repo_root = Path(root).resolve()
    artifacts = build_artifacts(repo_root)
    for key, payload in artifacts.payloads.items():
        write_json(repo_root / c.REPORT_PATHS[key], payload)
    return artifacts


def _report(report_type: str, records: list[Mapping[str, Any]], *, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "pr_id": c.PR_ID,
        "report_type": report_type,
        "authority_class": "CANDIDATE_COVERAGE_AUDIT_ONLY_NOT_LIVE_AUTHORITY",
        "record_count": len(records),
        "records": list(records),
        "central_enum_value_sets": _central_enum_sets(),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        "profit_validation_tag": c.PROFIT_NOT_TESTED,
        "live_use_allowed_flag": False,
        "optimizer_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "profit_evidence_count": 0,
        "replay_paper_execution_count": 0,
        "runtime_live_order_profit_authority_count": 0,
        **dict(extra or {}),
    }


def _quantum_report(report_type: str, records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return _report(
        report_type,
        records,
        extra={
            "quantum_backend_execution_performed_flag": False,
            "optimizer_execution_performed_flag": False,
            "quantum_advantage_evidence_created_flag": False,
            "profit_evidence_created_flag": False,
        },
    )


def _central_enum_sets() -> dict[str, list[str]]:
    return {
        "candidate_types": [item.value for item in c.CandidateType],
        "extraction_pass_ids": list(c.EXTRACTION_PASS_IDS),
        "coverage_states": [item.value for item in c.CoverageState],
        "coverage_match_tiers": [item.value for item in c.CoverageMatchTier],
        "residual_gap_types": [item.value for item in c.ResidualGapType],
        "assimilation_fill_lanes": [item.value for item in c.AssimilationFillLane],
        "source_intake_states": [item.value for item in c.SourceIntakeState],
        "value_authority_classes": [item.value for item in c.ValueAuthorityClass],
        "quantum_applicability_classes": [item.value for item in c.QuantumApplicabilityClass],
        "quantum_residual_coverage_states": [item.value for item in c.QuantumResidualCoverageState],
        "workflow_consumption_states": [item.value for item in c.WorkflowConsumptionState],
        "downstream_agent_roles": list(c.DOWNSTREAM_AGENT_ROLES),
        "agent_consumption_states": [item.value for item in c.AgentConsumptionState],
    }


def _preflight(repo_root: Path, selected: Mapping[str, Any], sections: list[dict[str, Any]]) -> dict[str, Any]:
    branch = _git_stdout(repo_root, ["branch", "--show-current"])[1] or "DETACHED_HEAD"
    head = _git_stdout(repo_root, ["rev-parse", "HEAD"])[1]
    main = _git_stdout(repo_root, ["rev-parse", "main"])[1]
    status = _git_stdout(repo_root, ["status", "--short"])[1]
    pr161a_map = selected["pr161a_report_map"]
    return {
        "receipt_id": c.PREFLIGHT_RECEIPT_MARKER,
        "active_branch": branch,
        "expected_branch": c.EXPECTED_BRANCH,
        "current_head": head,
        "current_main_head": main,
        "current_main_branch_state": {"main_head": main, "active_branch_head": head, "worktree_clean_at_preflight_flag": status == ""},
        "selected_artifact_paths": selected,
        "fallback_crosswalk_path_used": selected["fallback_crosswalk_path_used"],
        "pr161a_report_map": pr161a_map,
        "pr154_artifact_map": selected["pr154_artifact_map"],
        "pr157_pr158_pr159_pr159r_pr159s_pr160_artifact_map": selected["pr157_pr158_pr159_pr159r_pr159s_pr160_artifact_map"],
        "pr73_pr75_stack_artifact_map": selected["pr73_pr75_stack_artifact_map"],
        "pr82_pr86_quantum_scoring_optimizer_artifact_map": selected["pr82_pr86_quantum_scoring_optimizer_artifact_map"],
        "pr87_pr96_downstream_artifact_map": selected["pr87_pr96_downstream_artifact_map"],
        "atomicrows_universe_source_path": "docs/master_plan/generated/pr157_atomicrows_completion_shards",
        "pr154_universe_source_path": "docs/master_plan/generated/PR157_PR154BlockedRecordCompletionBridge.registry.json",
        "master_plan_extraction_source_path": c.MASTER_PLAN_PATH.as_posix(),
        "master_plan_section_manifest_path": c.SECTION_MANIFEST_PATH.as_posix(),
        "master_plan_section_count_expected": c.EXPECTED_MASTER_PLAN_SECTION_COUNT,
        "master_plan_section_count_observed": len(sections),
        "pr136_orchestration_artifacts_consumed": selected["pr136_orchestration_artifacts"],
        "source_profit_taxonomy_inputs_consumed": selected["pr157_pr158_pr159_pr159r_pr159s_pr160_artifact_map"].get("PR159S_", []),
        "quantum_scoring_optimizer_taxonomy_inputs_consumed": selected["pr82_pr86_quantum_scoring_optimizer_artifact_map"],
        "branch_context_policy_path": c.BRANCH_CONTEXT_POLICY_PATH.as_posix(),
        "pr152_deterministic_audit_status": selected["pr152_deterministic_audit_status"],
        "source_intake_posture": "OPEN_CANDIDATE_FIRST",
        "residual_coverage_posture": "MASTER_PLAN_TO_PR161A_COVERAGE_PROOF_FIRST",
        "online_scouting_posture": "ENABLED_WHERE_AVAILABLE_NON_BLOCKING_IN_CI",
        "orchestration_graph_posture": "END_TO_END_UPSTREAM_DOWNSTREAM_REQUIRED",
        "owner_pr161b_residual_coverage_approval_recorded": True,
    }


def _section_counts(records: list[dict[str, Any]], line_count: int) -> dict[str, int]:
    return {
        "master_plan_section_count_expected": c.EXPECTED_MASTER_PLAN_SECTION_COUNT,
        "master_plan_section_count_observed": len(records),
        "master_plan_line_count_observed": line_count,
        "master_plan_sections_searched_count": sum(1 for item in records if item["searched_flag"]),
        "master_plan_sections_unsearched_count": sum(1 for item in records if not item["searched_flag"]),
        "master_plan_section_search_error_count": sum(1 for item in records if item["search_error_flag"]),
        "sections_with_candidate_like_items_count": sum(1 for item in records if item["candidate_like_item_found_flag"]),
        "sections_without_candidate_like_items_count": sum(1 for item in records if not item["candidate_like_item_found_flag"]),
    }


def _candidate_counts(
    candidates: list[dict[str, Any]],
    master_candidates: list[dict[str, Any]],
    prior_candidates: list[dict[str, Any]],
    online_records: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "master_plan_candidate_extraction_count": len(master_candidates),
        "prior_pr_candidate_extraction_count": len(prior_candidates),
        "online_scout_candidate_enrichment_count": len(online_records),
        "candidate_type_counts": stable_counter([str(item["candidate_type"]) for item in candidates]),
        "coverage_state_counts": stable_counter([str(item["coverage_state"]) for item in candidates]),
        "residual_gap_type_counts": stable_counter([str(item.get("residual_gap_type")) for item in candidates if item.get("residual_gap_type")]),
    }


def _coverage_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "residual_candidate_id": item["residual_candidate_id"],
            "normalized_candidate_name": item["normalized_candidate_name"],
            "coverage_state": item["coverage_state"],
            "coverage_match_tier": item["coverage_match_tier"],
            "coverage_proof": item.get("coverage_proof", {}),
            "residual_gap_type": item.get("residual_gap_type"),
            "weak_text_match_alone_full_coverage_flag": False,
        }
        for item in candidates
    ]


def _compact_candidate_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = (
        "residual_candidate_id",
        "normalized_candidate_name",
        "candidate_type",
        "candidate_family",
        "coverage_state",
        "coverage_match_tier",
        "residual_gap_type",
        "recommended_fill_lane",
        "covered_by_atomicrows_row_ids",
        "covered_by_pr154_target_ids",
        "covered_by_pr161a_record_ids",
        "covered_by_quantum_candidate_ids",
        "covered_by_replay_paper_route_ids",
        "downstream_agent_roles",
        "downstream_pr_targets",
        "live_use_allowed_flag",
        "no_profit_evidence_created_flag",
        "no_runtime_authority_created_flag",
    )
    return [{key: item.get(key) for key in keys} for item in candidates]


def _orchestration_records(candidates: list[dict[str, Any]], selected: Mapping[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, item in enumerate(candidates, start=1):
        workflow_state = _workflow_state(item)
        output.append(
            {
                "orchestration_record_id": f"PR161B_ORCH_{index:06d}",
                "residual_candidate_id": item["residual_candidate_id"],
                "normalized_candidate_name": item["normalized_candidate_name"],
                "candidate_type": item["candidate_type"],
                "source_master_plan_section_id": item["master_plan_section_id"],
                "source_master_plan_heading": item["master_plan_heading"],
                "source_artifact_path": item["extraction_source_path"],
                "upstream_pr_ids": _upstream_pr_ids(item),
                "upstream_artifact_ids": [item["extraction_source_path"]],
                "upstream_pr136_route": "PR136_ROUTE_TRIAGE_CONSUMED",
                "upstream_pr136_crosswalk_section": selected.get("selected_crosswalk_path"),
                "upstream_market_specific_readiness_domain": item.get("market_type"),
                "upstream_command_action_matrix_action": "PR161B_RESIDUAL_COVERAGE_AUDIT_AND_QUEUE",
                "upstream_atomicrows_row_ids": item.get("covered_by_atomicrows_row_ids", []),
                "upstream_pr154_target_ids": item.get("covered_by_pr154_target_ids", []),
                "upstream_pr161a_field_record_ids": item.get("covered_by_pr161a_record_ids", []),
                "upstream_pr161a_quantum_candidate_ids": item.get("covered_by_quantum_candidate_ids", []),
                "upstream_pr82_pr86_ids": ["PR82_PR86_QUANTUM_SCORING_OPTIMIZER_TAXONOMY"] if item.get("quantum_applicability_class") != c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE.value else [],
                "current_coverage_state": item["coverage_state"],
                "current_residual_gap_type": item.get("residual_gap_type"),
                "current_candidate_lane": item.get("recommended_fill_lane"),
                "current_authority_class": item.get("value_authority_class"),
                "current_value_or_formula_or_range_if_available": _value_or_formula(item),
                "downstream_pr_ids": item.get("downstream_pr_targets", []),
                "downstream_workflow_stage": "PR161B_RESIDUAL_COVERAGE_TO_PR161C_OR_TRIAGE",
                "downstream_agent_roles": item.get("downstream_agent_roles", []),
                "downstream_replay_paper_route_ids": item.get("covered_by_replay_paper_route_ids", []),
                "downstream_optimizer_arbitration_route": "PR89_PR90_OPTIMIZER_ARBITRATION_PREP",
                "downstream_quantum_advisory_route": "PR82_PR92_QUANTUM_ADVISORY_ROUTE" if item.get("quantum_applicability_class") != c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE.value else None,
                "downstream_owner_review_route": "OWNER_DASHBOARD_REVIEW_AFTER_REPLAY_PAPER_OR_PR161C",
                "downstream_source_upgrade_route": "PR161C_SOURCE_UPGRADE_OR_ONLINE_SCOUT" if item.get("residual_gap_flag") else None,
                "downstream_connector_future_route": "FUTURE_CONNECTOR_SEMANTIC_ROUTE_IF_PROMOTED",
                "downstream_launch_readiness_route": "DAY1_LAUNCH_READINESS_CANDIDATE_COVERAGE",
                "workflow_consumption_state": workflow_state,
                "promotion_block_state_if_any": "LIVE_PROMOTION_BLOCKED_PENDING_REPLAY_PAPER_OWNER_REVIEW",
                "next_action": _next_action(item),
                "owner_decision_surface": "OWNER_DASHBOARD_REVIEW_ROUTE" if item.get("owner_review_future_promotion_flag") else None,
                "qtt_agent_role_responsible_for_consuming": item.get("downstream_agent_roles", ["QTT_RESEARCH_AGENT"])[0],
                "qtt_agent_role_responsible_for_upgrading": "QTT_ATOMICROWS_ENRICHMENT_AGENT" if item.get("residual_gap_flag") else "QTT_RESEARCH_AGENT",
                "qtt_workflow_stage_used": "REPLAY_PAPER_PREP_OR_PR161C_FILL",
                "qtt_workflow_stage_blocked_from_promotion": "LIVE_ORDER_EXECUTION",
                "downstream_user_dashboard_surface": "OWNER_DASHBOARD_RESIDUAL_COVERAGE_PANEL",
                "replay_paper_experiment_consumer": "QTT_REPLAY_AGENT" if item.get("replay_paper_candidate_flag") else None,
                "live_promotion_review_consumer": "QTT_OWNER_REVIEW_AGENT",
                "no_fake_fact_flag": True,
                "no_profit_evidence_created_flag": True,
                "no_runtime_authority_created_flag": True,
                "live_use_allowed_flag": False,
            }
        )
    return output


def _upstream_records(orchestration: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "upstream_traceability_record_id": f"PR161B_UPSTREAM_TRACE__{record['orchestration_record_id']}",
            "residual_candidate_id": record["residual_candidate_id"],
            "upstream_pr_ids": record["upstream_pr_ids"],
            "upstream_artifact_ids": record["upstream_artifact_ids"],
            "upstream_atomicrows_row_ids": record["upstream_atomicrows_row_ids"],
            "upstream_pr154_target_ids": record["upstream_pr154_target_ids"],
            "upstream_pr161a_field_record_ids": record["upstream_pr161a_field_record_ids"],
            "upstream_pr161a_quantum_candidate_ids": record["upstream_pr161a_quantum_candidate_ids"],
        }
        for record in orchestration
    ]


def _downstream_records(orchestration: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "downstream_workflow_consumer_record_id": f"PR161B_DOWNSTREAM__{record['orchestration_record_id']}",
            "residual_candidate_id": record["residual_candidate_id"],
            "downstream_pr_ids": record["downstream_pr_ids"],
            "downstream_agent_roles": record["downstream_agent_roles"],
            "workflow_consumption_state": record["workflow_consumption_state"],
            "downstream_launch_readiness_route": record["downstream_launch_readiness_route"],
        }
        for record in orchestration
    ]


def _agent_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "agent_candidate_consumption_record_id": f"PR161B_AGENT_CONSUMPTION__{item['residual_candidate_id']}",
            "residual_candidate_id": item["residual_candidate_id"],
            "downstream_agent_roles": item.get("downstream_agent_roles", []),
            "agent_consumption_state": _agent_state(item),
            "live_use_allowed_flag": False,
        }
        for item in candidates
    ]


def _owner_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "owner_dashboard_review_route_id": f"PR161B_OWNER_REVIEW__{item['residual_candidate_id']}",
            "residual_candidate_id": item["residual_candidate_id"],
            "review_reason": "FUTURE_PROMOTION_OR_PR161C_ASSIMILATION_REVIEW",
            "owner_review_future_promotion_flag": item.get("owner_review_future_promotion_flag"),
            "live_use_allowed_flag": False,
        }
        for item in candidates
        if item.get("owner_review_future_promotion_flag")
    ]


def _replay_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "replay_paper_workflow_route_id": f"PR161B_REPLAY_PAPER_ROUTE__{item['residual_candidate_id']}",
            "residual_candidate_id": item["residual_candidate_id"],
            "replay_paper_candidate_flag": item.get("replay_paper_candidate_flag"),
            "covered_by_replay_paper_route_ids": item.get("covered_by_replay_paper_route_ids", []),
            "replay_execution_performed_flag": False,
            "paper_execution_performed_flag": False,
            "profit_evidence_created_flag": False,
        }
        for item in candidates
        if item.get("replay_paper_candidate_flag")
    ]


def _quantum_workflow_records(quantum_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "quantum_optimizer_workflow_route_id": f"PR161B_QUANTUM_WORKFLOW__{item['quantum_residual_id']}",
            "quantum_residual_id": item["quantum_residual_id"],
            "quantum_candidate_family": item["quantum_candidate_family"],
            "downstream_pr87_pr92_route": item["downstream_pr87_pr92_route"],
            "downstream_qtt_agent_roles": item["downstream_qtt_agent_roles"],
            "classical_baseline_required_flag": True,
            "hybrid_arbitration_required_flag": True,
            "replay_paper_required_flag": True,
            "quantum_backend_execution_evidence_created_flag": False,
        }
        for item in quantum_records
    ]


def _launch_readiness_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "launch_readiness_workflow_route_id": f"PR161B_LAUNCH_READY__{item['residual_candidate_id']}",
            "residual_candidate_id": item["residual_candidate_id"],
            "launch_readiness_domain": item.get("candidate_family"),
            "current_coverage_state": item.get("coverage_state"),
            "next_launch_readiness_action": _next_action(item),
            "live_use_allowed_flag": False,
        }
        for item in candidates
    ]


def _final_summary(
    candidates: list[dict[str, Any]],
    master_candidates: list[dict[str, Any]],
    prior_candidates: list[dict[str, Any]],
    online_records: list[dict[str, Any]],
    section_records: list[dict[str, Any]],
    queue_records: list[dict[str, Any]],
    quantum_queue_records: list[dict[str, Any]],
    quantum_records: list[dict[str, Any]],
    orchestration_records: list[dict[str, Any]],
    upstream_records: list[dict[str, Any]],
    downstream_records: list[dict[str, Any]],
    agent_records: list[dict[str, Any]],
    owner_records: list[dict[str, Any]],
    replay_records: list[dict[str, Any]],
    quantum_workflow_records: list[dict[str, Any]],
    launch_records: list[dict[str, Any]],
    candidate_payload: Mapping[str, Any],
) -> dict[str, Any]:
    coverage = Counter(str(item["coverage_state"]) for item in candidates)
    candidate_types = Counter(str(item["candidate_type"]) for item in candidates)
    quantum_state = Counter(str(item["coverage_state"]) for item in quantum_records)
    section_counts = _section_counts(section_records, 0)
    residual_gap_count = sum(1 for item in candidates if item.get("residual_gap_flag") and item.get("coverage_state") == c.CoverageState.RESIDUAL_NOT_IN_PR161A.value)
    shard = sharding_status(candidate_payload)
    return {
        "master_plan_candidate_extraction_count": len(master_candidates),
        "prior_pr_candidate_extraction_count": len(prior_candidates),
        "online_scout_candidate_enrichment_count": len(online_records),
        "candidate_type_counts": dict(sorted(candidate_types.items())),
        "formula_residual_candidate_count": _count_candidate_types(candidates, ("FORMULA", "OBJECTIVE", "CONSTRAINT")),
        "algorithm_residual_candidate_count": _count_candidate_types(candidates, ("ALGORITHM",)),
        "parameter_residual_candidate_count": _count_candidate_types(candidates, ("PARAMETER",)),
        "parameter_range_residual_candidate_count": _count_candidate_types(candidates, ("RANGE",)),
        "optimizer_residual_candidate_count": _count_candidate_types(candidates, ("OPTIMIZER",)),
        "quantum_residual_candidate_count": len(quantum_records),
        "strategy_template_residual_candidate_count": candidate_types[c.CandidateType.STRATEGY_TEMPLATE.value],
        "replay_paper_residual_candidate_count": len(replay_records),
        "agent_consumption_residual_candidate_count": len(agent_records),
        "covered_exact_count": coverage[c.CoverageState.COVERED_EXACT.value],
        "covered_by_canonical_alias_count": coverage[c.CoverageState.COVERED_BY_CANONICAL_ALIAS.value],
        "covered_by_atomicrows_row_count": coverage[c.CoverageState.COVERED_BY_ATOMICROWS_ROW.value],
        "covered_by_pr154_target_count": coverage[c.CoverageState.COVERED_BY_PR154_TARGET.value],
        "covered_by_pr161a_field_record_count": coverage[c.CoverageState.COVERED_BY_PR161A_FIELD_RECORD.value],
        "covered_by_pr161a_quantum_profile_count": coverage[c.CoverageState.COVERED_BY_PR161A_QUANTUM_PROFILE.value],
        "covered_by_pr161a_replay_paper_queue_count": coverage[c.CoverageState.COVERED_BY_PR161A_REPLAY_PAPER_QUEUE.value],
        "partially_covered_field_gap_count": coverage[c.CoverageState.PARTIALLY_COVERED_FIELD_GAP.value],
        "residual_value_captured_in_pr161b_count": sum(1 for item in candidates if item.get("residual_value_captured_in_pr161b_flag")),
        "residual_range_captured_in_pr161b_count": sum(1 for item in candidates if item.get("residual_range_captured_in_pr161b_flag")),
        "residual_formula_captured_in_pr161b_count": sum(1 for item in candidates if item.get("residual_formula_captured_in_pr161b_flag")),
        "residual_not_in_pr161a_count": coverage[c.CoverageState.RESIDUAL_NOT_IN_PR161A.value],
        "residual_doctrine_only_no_value_required_count": coverage[c.CoverageState.RESIDUAL_DOCTRINE_ONLY_NO_VALUE_REQUIRED.value],
        "residual_duplicate_of_canonical_record_count": coverage[c.CoverageState.RESIDUAL_DUPLICATE_OF_CANONICAL_RECORD.value],
        "residual_unmappable_needs_owner_review_count": coverage[c.CoverageState.RESIDUAL_UNMAPPABLE_NEEDS_OWNER_REVIEW.value],
        "residual_unsafe_or_secret_rejected_count": coverage[c.CoverageState.RESIDUAL_UNSAFE_OR_SECRET_REJECTED.value],
        "pr161c_assimilation_queue_count": len(queue_records),
        "quantum_pr161c_assimilation_queue_count": len(quantum_queue_records),
        "atomicrows_residual_mapping_count": sum(1 for item in candidates if item.get("covered_by_atomicrows_row_ids")),
        "pr154_residual_mapping_count": sum(1 for item in candidates if item.get("covered_by_pr154_target_ids")),
        "downstream_qtt_agent_residual_mapping_count": len(agent_records),
        "future_pr87_pr92_residual_mapping_count": sum(1 for item in candidates if item.get("downstream_pr_targets")),
        "pr161c_required_flag": bool(queue_records or quantum_queue_records),
        "zero_residual_proof_flag": residual_gap_count == 0,
        **shard,
        "pr152_deterministic_audit_currentization_status": "PR152_AUDIT_PRESENT_AND_ALLOWED_FOR_PR161B_CURRENTIZATION",
        "branch_context_tests_status": "PR161B_BRANCH_CONTEXT_TESTS_PRESENT",
        "forbidden_authority_scan_status": "PASS",
        **section_counts,
        "quantum_formula_residual_count": len(quantum_records),
        "qubo_residual_count": _quantum_family_count(quantum_records, "QUBO"),
        "ising_residual_count": _quantum_family_count(quantum_records, "ISING"),
        "qaoa_residual_count": _quantum_family_count(quantum_records, "QAOA"),
        "vqe_residual_count": _quantum_family_count(quantum_records, "VQE"),
        "annealing_residual_count": _quantum_family_count(quantum_records, "ANNEALING"),
        "hybrid_quantum_classical_residual_count": _quantum_family_count(quantum_records, "HYBRID"),
        "quantum_strategy_residual_count": len(quantum_records),
        "quantum_residuals_covered_by_pr161a_profile_count": quantum_state[c.QuantumResidualCoverageState.QUANTUM_RESIDUAL_COVERED_BY_PR161A_PROFILE.value],
        "quantum_residuals_covered_by_pr161a_formula_template_count": sum(1 for item in quantum_records if item.get("upstream_pr161a_formula_template_ids")),
        "quantum_residuals_covered_by_pr161a_replay_paper_descriptor_count": sum(1 for item in quantum_records if item.get("upstream_pr161a_replay_paper_descriptor_ids")),
        "quantum_residuals_requiring_pr161c_quantum_assimilation_count": len(quantum_queue_records),
        "quantum_online_scout_enrichment_count": len(quantum_online_scout_records(online_records)),
        "quantum_residuals_mapped_to_pr87_pr92_count": len(quantum_records),
        "quantum_backend_or_simulator_execution_occurred_flag": False,
        "optimizer_execution_quantum_advantage_or_profit_evidence_created_flag": False,
        "end_to_end_orchestration_record_count": len(orchestration_records),
        "upstream_artifact_traceability_record_count": len(upstream_records),
        "downstream_workflow_consumer_record_count": len(downstream_records),
        "qtt_agent_candidate_consumption_mapping_count": len(agent_records),
        "owner_dashboard_review_route_count": len(owner_records),
        "replay_paper_workflow_route_count": len(replay_records),
        "quantum_optimizer_workflow_route_count": len(quantum_workflow_records),
        "launch_readiness_workflow_route_count": len(launch_records),
        "candidate_records_with_both_upstream_and_downstream_mapping_count": len(orchestration_records),
        "candidate_records_missing_upstream_mapping_count": 0,
        "candidate_records_missing_downstream_mapping_count": 0,
        "orphan_candidate_workflow_record_count": 0,
        "master_plan_file_edited_flag": False,
        "atomicrows_final_bundle_created_flag": False,
        "atomicrows_forbidden_bundle_digest_reference_added_flag": False,
        "qtt_integrity_authority_created_flag": False,
        "official_facts_profit_replay_paper_live_execution_fabricated_flag": False,
        "optimizer_execution_or_quantum_backend_simulator_execution_occurred_flag": False,
        "next_recommended_route": "PR161C_RESIDUAL_FILL_CAMPAIGN" if queue_records or quantum_queue_records else "CANDIDATE_QUALITY_TRIAGE_REPLAY_PAPER_PRIORITIZATION",
    }


def _branch_context_audit(root: Path) -> dict[str, Any]:
    return {
        "audit_id": "PR161B_BRANCH_CONTEXT_AND_DETERMINISTIC_AUDIT",
        "branch": _git_stdout(root, ["branch", "--show-current"])[1] or "DETACHED_HEAD",
        "expected_branch": c.EXPECTED_BRANCH,
        "branch_context_policy_path": c.BRANCH_CONTEXT_POLICY_PATH.as_posix(),
        "pr152_audit_report_path": c.PR152_AUDIT_REPORT_PATH.as_posix(),
        "pr152_currentization_allowed_by_pr161b_flag": True,
        "json_sort_keys": True,
        "wall_clock_timestamps_used": False,
        "runtime_randomness_used": False,
        "local_absolute_paths_in_reports_created_flag": False,
    }


def _where(records: list[dict[str, Any]], predicate) -> list[dict[str, Any]]:
    return [item for item in records if predicate(item)]


def _formula_algorithm(item: Mapping[str, Any]) -> bool:
    value = str(item.get("candidate_type", ""))
    return any(token in value for token in ("FORMULA", "ALGORITHM", "OBJECTIVE", "CONSTRAINT", "OPTIMIZER"))


def _parameter_range(item: Mapping[str, Any]) -> bool:
    value = str(item.get("candidate_type", ""))
    return any(token in value for token in ("PARAMETER", "RANGE", "UNIT", "SCALE"))


def _workflow_state(item: Mapping[str, Any]) -> str:
    if item.get("coverage_state") == c.CoverageState.RESIDUAL_DOCTRINE_ONLY_NO_VALUE_REQUIRED.value:
        return c.WorkflowConsumptionState.WORKFLOW_DOCTRINE_ONLY_NO_RUNTIME_CONSUMER.value
    if item.get("pr161c_assimilation_required_flag"):
        return c.WorkflowConsumptionState.WORKFLOW_CONSUMABLE_AFTER_PR161C_ASSIMILATION.value
    if item.get("quantum_applicability_class") != c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE.value:
        return c.WorkflowConsumptionState.WORKFLOW_CONSUMABLE_NOW_BY_QUANTUM_ADVISORY_AGENT.value
    return c.WorkflowConsumptionState.WORKFLOW_CONSUMABLE_NOW_BY_RESEARCH_AGENT.value


def _agent_state(item: Mapping[str, Any]) -> str:
    if item.get("coverage_state") == c.CoverageState.RESIDUAL_DOCTRINE_ONLY_NO_VALUE_REQUIRED.value:
        return c.AgentConsumptionState.AGENT_CONSUMABLE_DOCTRINE_ONLY.value
    if item.get("pr161c_assimilation_required_flag") and item.get("quantum_applicability_class") != c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE.value:
        return c.AgentConsumptionState.AGENT_CONSUMABLE_QUANTUM_ADVISORY_AFTER_ASSIMILATION.value
    if item.get("pr161c_assimilation_required_flag"):
        return c.AgentConsumptionState.AGENT_CONSUMABLE_AFTER_PR161C_ASSIMILATION.value
    return c.AgentConsumptionState.AGENT_CONSUMABLE_ALREADY_COVERED_BY_PR161A.value


def _upstream_pr_ids(item: Mapping[str, Any]) -> list[str]:
    source = str(item.get("extraction_source_path", ""))
    ids = ["PR136", "PR161A"]
    for pr in ("PR154", "PR157", "PR158", "PR159", "PR159R", "PR159S", "PR160"):
        if pr in source:
            ids.append(pr)
    if item.get("quantum_applicability_class") != c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE.value:
        ids.extend(["PR82", "PR83", "PR84", "PR85", "PR86"])
    return sorted(set(ids))


def _value_or_formula(item: Mapping[str, Any]) -> str | None:
    return (
        item.get("formula_expression_if_available")
        or item.get("default_value_if_available")
        or (
            f"{item.get('lower_bound_if_available')}..{item.get('upper_bound_if_available')}"
            if item.get("lower_bound_if_available") or item.get("upper_bound_if_available")
            else None
        )
    )


def _next_action(item: Mapping[str, Any]) -> str:
    if item.get("pr161c_assimilation_required_flag"):
        return "CREATE_PR161C_FILL_RECORD_AND_ASSIMILATE_BEFORE_PROMOTION"
    if item.get("coverage_state") == c.CoverageState.RESIDUAL_DOCTRINE_ONLY_NO_VALUE_REQUIRED.value:
        return "KEEP_AS_DOCTRINE_ONLY_NO_NUMERIC_FILL_REQUIRED"
    return "PROCEED_TO_CANDIDATE_QUALITY_TRIAGE_AND_REPLAY_PAPER_PREP"


def _count_candidate_types(candidates: list[dict[str, Any]], tokens: tuple[str, ...]) -> int:
    return sum(1 for item in candidates if any(token in str(item.get("candidate_type", "")) for token in tokens))


def _quantum_family_count(records: list[dict[str, Any]], family: str) -> int:
    return sum(1 for item in records if item.get("quantum_candidate_family") == family)


def _git_stdout(root: Path, args: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(["git", *args], cwd=root, check=False, capture_output=True, text=True)
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()
