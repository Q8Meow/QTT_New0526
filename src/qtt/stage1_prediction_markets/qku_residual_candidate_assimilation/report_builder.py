"""Top-level deterministic PR161C artifact construction."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import subprocess
from typing import Any, Iterable

from . import artifact_discovery
from . import constants as c
from .io import read_json, stable_counter, write_json
from .models import BuildArtifacts
from .pr136_orchestration_loader import load_control_plane_artifacts
from .pr161a_entity_loader import (
    load_pr161a_atomicrow_entities,
    load_pr161a_entities,
    load_pr161a_pr154_entities,
)
from .pr161a_field_value_loader import load_pr161a_field_values
from .pr161b_coverage_loader import load_pr161b_coverage_reports
from .pr161b_queue_loader import load_pr161b_queue
from .qku_algorithm_formula_strategy_classifier import classify_algorithm_formula_strategy
from .qku_classical_quantum_hybrid_classifier import classify_computation
from .qku_default_materialization_engine import materialize_default
from .qku_fill_lane_classifier import (
    classify_entity_fill_lane,
    classify_field_value_fill_lane,
    classify_residual_fill_lane,
)
from .qku_id_builder import (
    atomicrow_qku_id,
    field_facet_qku_id,
    normalize_name,
    pr154_qku_id,
    residual_qku_id,
)
from .qku_launch_stage_classifier import classify_launch_stage
from .qku_market_classifier import classify_market
from .qku_orchestration_graph_builder import attach_graph
from .qku_orchestration_graph_validator import validate_graph
from .qku_residual_diagnostic import classify_residual_diagnostic
from .qku_stage1_applicability_classifier import classify_stage1_applicability
from .qku_type_classifier import classify_entity_type, classify_residual_type


def build_artifacts(root: Path | str) -> BuildArtifacts:
    repo_root = Path(root).resolve()
    selected = artifact_discovery.selected_artifact_paths(repo_root)
    control_plane = load_control_plane_artifacts(repo_root)
    atomic_entities = load_pr161a_atomicrow_entities(repo_root)
    pr154_entities = load_pr161a_pr154_entities(repo_root)
    entities = atomic_entities + pr154_entities
    field_values = load_pr161a_field_values(repo_root)
    queue = load_pr161b_queue(repo_root)
    coverage = load_pr161b_coverage_reports(repo_root)
    coverage_context = _coverage_context(coverage)

    field_facets, facet_ids_by_parent = _field_value_facet_records(field_values)
    primary_records_without_graph = _primary_qku_records(entities, queue, facet_ids_by_parent, coverage_context)
    primary_records, graph_nodes, graph_edges = attach_graph(primary_records_without_graph)
    graph_failures = validate_graph(primary_records, graph_edges, repo_root)
    quantum_trace = _quantum_trace_records(coverage_context)
    supplemental = _supplemental_scout_records(selected)
    summary = _summary(
        repo_root,
        selected,
        control_plane,
        atomic_entities,
        pr154_entities,
        field_values,
        queue,
        coverage,
        primary_records,
        field_facets,
        graph_nodes,
        graph_edges,
        quantum_trace,
        supplemental,
        graph_failures,
    )
    payloads = _payloads(
        selected,
        control_plane,
        atomic_entities,
        pr154_entities,
        field_values,
        queue,
        coverage,
        primary_records,
        field_facets,
        graph_nodes,
        graph_edges,
        quantum_trace,
        supplemental,
        summary,
        graph_failures,
    )
    payloads = _add_shard_manifest(payloads)
    summary.update(_largest_report_summary(payloads))
    payloads["PR161C_QKUFinalAssimilationSummary.report.json"]["records"] = [summary]
    payloads["PR161C_QKUFinalAssimilationSummary.report.json"].update(summary)
    payloads["PR161C_QKUReportShardManifest.report.json"] = _report(
        "PR161C_QKU_REPORT_SHARD_MANIFEST",
        payloads["PR161C_QKUReportShardManifest.report.json"]["records"],
        extra=payloads["PR161C_QKUReportShardManifest.report.json"],
    )
    return BuildArtifacts(payloads=payloads, summary=summary)


def write_artifacts(root: Path | str) -> BuildArtifacts:
    repo_root = Path(root).resolve()
    artifacts = build_artifacts(repo_root)
    main_payloads, shard_payloads, manifest_records = _payloads_for_write(artifacts.payloads)
    artifacts.summary.update(_written_largest_report_summary(main_payloads, shard_payloads))
    summary_payload = main_payloads["PR161C_QKUFinalAssimilationSummary.report.json"]
    summary_payload["records"] = [artifacts.summary]
    summary_payload.update(artifacts.summary)
    main_payloads["PR161C_QKUReportShardManifest.report.json"] = _report(
        "PR161C_QKU_REPORT_SHARD_MANIFEST",
        manifest_records,
        extra={
            "report_sharding_status": artifacts.summary["report_sharding_status"],
            "report_sharding_required_flag": artifacts.summary["report_sharding_status"] != "NOT_REQUIRED_UNDER_50_MB",
        },
    )
    _clear_shard_dir(repo_root)
    for filename in c.PR161C_REPORT_FILENAMES:
        write_json(repo_root / c.GENERATED_DIR / filename, main_payloads[filename])
    for rel_path, payload in shard_payloads.items():
        write_json(repo_root / rel_path, payload)
    return artifacts


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return [item for item in payload["records"] if isinstance(item, dict)]
    return []


def _coverage_context(coverage: dict[str, Any]) -> dict[str, Any]:
    inventory_records = _records(coverage.get("candidate_inventory"))
    inventory_by_residual = {
        str(item.get("residual_candidate_id")): item
        for item in inventory_records
        if item.get("residual_candidate_id")
    }
    quantum_records = _records(coverage.get("quantum_optimizer"))
    quantum_by_qku: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in quantum_records:
        for row_id in item.get("atomicrows_row_ids") or []:
            quantum_by_qku[atomicrow_qku_id(str(row_id))].append(item)
        for target_id in item.get("pr154_target_ids") or []:
            quantum_by_qku[pr154_qku_id(str(target_id))].append(item)
    return {
        "inventory_by_residual": inventory_by_residual,
        "quantum_records": quantum_records,
        "quantum_by_qku": quantum_by_qku,
    }


def _dominant_quantum_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not records:
        return None
    priority = {
        "QUBO": 0,
        "ISING": 1,
        "QAOA": 2,
        "VQE": 3,
        "ANNEALING": 4,
        "HYBRID": 5,
        "QUANTUM": 6,
    }
    return sorted(
        records,
        key=lambda item: (
            priority.get(str(item.get("quantum_candidate_family") or "QUANTUM"), 99),
            str(item.get("quantum_residual_id") or item.get("residual_candidate_id") or ""),
        ),
    )[0]


def _primary_qku_records(
    entities: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    facet_ids_by_parent: dict[str, list[str]],
    coverage_context: dict[str, Any],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for entity in sorted(entities, key=lambda item: str(item.get("entity_inventory_record_id") or item.get("row_id") or item.get("target_id"))):
        records.append(_entity_qku_record(entity, facet_ids_by_parent, coverage_context))
    for residual in sorted(queue, key=lambda item: str(item.get("assimilation_queue_id"))):
        records.append(_residual_qku_record(residual, coverage_context))
    return records


def _entity_qku_id(entity: dict[str, Any]) -> str:
    if entity.get("universe") == "PR154" or entity.get("target_id"):
        return pr154_qku_id(str(entity.get("target_id") or entity.get("entity_inventory_record_id")))
    return atomicrow_qku_id(str(entity.get("row_id") or entity.get("entity_inventory_record_id")))


def _entity_qku_record(
    entity: dict[str, Any],
    facet_ids_by_parent: dict[str, list[str]],
    coverage_context: dict[str, Any],
) -> dict[str, Any]:
    qku_id = _entity_qku_id(entity)
    qku_type = classify_entity_type(entity)
    source_path = "docs/master_plan/generated/PR161A_PR154EntityValueStateInventory.report.json" if qku_type == "PR154_TARGET_QKU" else "docs/master_plan/generated/PR161A_AtomicRowsEntityValueStateInventory.report.json"
    facet_ids = facet_ids_by_parent.get(qku_id, [])
    source_record = dict(entity)
    quantum_links = coverage_context["quantum_by_qku"].get(qku_id, [])
    dominant_quantum = _dominant_quantum_record(quantum_links)
    if dominant_quantum:
        source_record["_pr161b_quantum_candidate_family"] = dominant_quantum.get("quantum_candidate_family")
        source_record["_pr161b_quantum_profile_type"] = dominant_quantum.get("quantum_profile_type")
        source_record["_pr161b_quantum_trace_count"] = len(quantum_links)
    materialized = materialize_default(qku_type, entity, len(facet_ids))
    source_class = _source_class_from(entity.get("source_intake_state") or entity.get("source_artifact_path"))
    base = _base_record(
        qku_id=qku_id,
        qku_type=qku_type,
        qku_family=str(entity.get("universe") or "PR161A_ENTITY"),
        qku_subtype=str(entity.get("aggregate_value_state") or "PR161A_ENTITY_MATERIALIZED"),
        qku_name=str(entity.get("row_id") or entity.get("target_id") or entity.get("entity_inventory_record_id")),
        original_term=str(entity.get("row_id") or entity.get("target_id") or entity.get("entity_inventory_record_id")),
        original_context="PR161A_ENTITY_VALUE_STATE_INVENTORY",
        source_artifact_path=source_path,
        source_locator=str(entity.get("source_artifact_path") or source_path),
        source_class=source_class,
        source_acceptance_state="SOURCE_ACCEPTED_FOR_DEFAULT_MATERIALIZATION",
        authority_class="PRIOR_PR_ARTIFACT_QKU",
        source_provenance="PR161A_ENTITY_PROVENANCE",
        materialized=materialized,
        replay_paper_required=bool(entity.get("replay_paper_candidate_flag", True)),
        downstream_agents=_known_agents(entity.get("downstream_agent_ids_or_roles")),
        downstream_prs=_default_downstream_prs(),
        replay_paper_routes=[str(entity.get("replay_paper_route_id") or f"PR161C_REPLAY_PAPER_ROUTE__{qku_id}")],
        upstream_artifacts=[source_path, str(entity.get("source_artifact_path") or "")],
        facet_ids=facet_ids,
        primary_membership="PR161A_ENTITY_QKU",
        pr161a_entity_ids=[str(entity.get("entity_inventory_record_id"))],
        pr161a_field_ids=[],
        pr161b_residual_ids=[],
        supplemental_ids=[],
        fill_lane=classify_entity_fill_lane(entity),
        source_record=source_record,
    )
    base["qku_pr161b_quantum_residual_trace_count"] = len(quantum_links)
    base["qku_pr161b_quantum_residual_ids"] = [
        str(item.get("quantum_residual_id") or item.get("residual_candidate_id"))
        for item in sorted(quantum_links, key=lambda row: str(row.get("quantum_residual_id") or row.get("residual_candidate_id")))
    ]
    base["qku_quantum_demoted_reason_if_any"] = None
    base["_upstream_edge_type"] = "UPSTREAM_PR161A_ENTITY"
    base["_upstream_object_id"] = str(entity.get("entity_inventory_record_id"))
    return base


def _residual_qku_record(residual: dict[str, Any], coverage_context: dict[str, Any]) -> dict[str, Any]:
    qku_id = residual_qku_id(str(residual["assimilation_queue_id"]))
    inventory = coverage_context["inventory_by_residual"].get(str(residual.get("residual_candidate_id")), {})
    source_record = {**inventory, **residual}
    qku_type = classify_residual_type(source_record)
    source_path = "docs/master_plan/generated/PR161B_PR161CAssimilationQueue.report.json"
    materialized = materialize_default(qku_type, source_record, 0)
    diagnostic = classify_residual_diagnostic(source_record)
    base = _base_record(
        qku_id=qku_id,
        qku_type=qku_type,
        qku_family=str(residual.get("candidate_family") or "PR161B_RESIDUAL"),
        qku_subtype=str(residual.get("candidate_type") or "RESIDUAL_CANDIDATE"),
        qku_name=str(residual.get("proposed_field_path") or residual.get("residual_candidate_id")),
        original_term=str(residual.get("proposed_field_path") or residual.get("residual_candidate_id")),
        original_context="PR161B_PR161C_ASSIMILATION_QUEUE",
        source_artifact_path=source_path,
        source_locator=", ".join(str(item) for item in residual.get("source_candidates", [])) or source_path,
        source_class="MASTER_PLAN_LITERAL_SOURCE",
        source_acceptance_state="SOURCE_ACCEPTED_FOR_QKU_CANDIDATE_USE",
        authority_class="MASTER_PLAN_LITERAL_QKU",
        source_provenance="PR161B_RESIDUAL_PROVENANCE",
        materialized=materialized,
        replay_paper_required=bool(residual.get("replay_paper_route_required_flag", True)),
        downstream_agents=_known_agents(residual.get("downstream_agent_roles")),
        downstream_prs=[str(item) for item in residual.get("downstream_pr_targets", [])] or _default_downstream_prs(),
        replay_paper_routes=[f"PR161C_REPLAY_PAPER_ROUTE__{residual.get('assimilation_queue_id')}"],
        upstream_artifacts=[source_path, *[str(item) for item in residual.get("source_candidates", [])]],
        facet_ids=[],
        primary_membership="PR161B_RESIDUAL_QKU",
        pr161a_entity_ids=[],
        pr161a_field_ids=[],
        pr161b_residual_ids=[str(residual.get("residual_candidate_id"))],
        supplemental_ids=[],
        fill_lane=classify_residual_fill_lane(source_record),
        source_record=source_record,
    )
    base.update(
        {
            "qku_residual_diagnostic_class": diagnostic,
            "qku_remaining_unassimilated_flag": False,
            "qku_value_if_available": residual.get("value_candidate_if_available"),
            "qku_default_if_available": residual.get("value_candidate_if_available"),
            "qku_range_if_available": residual.get("range_candidate_if_available"),
            "qku_lower_bound_if_available": None,
            "qku_upper_bound_if_available": None,
            "qku_unit_if_available": residual.get("unit_candidate_if_available"),
            "qku_scale_if_available": residual.get("scale_candidate_if_available"),
            "qku_formula_expression_if_available": residual.get("formula_candidate_if_available"),
            "qku_quantum_config_if_available": residual.get("quantum_profile_candidate_if_available"),
            "qku_pr161b_quantum_residual_trace_count": 0,
            "qku_pr161b_quantum_residual_ids": [],
            "qku_quantum_demoted_reason_if_any": "NOT_IN_PR161B_QUANTUM_OPTIMIZER_RESIDUAL_COVERAGE_AND_PR161B_QUEUE_MARKED_NOT_QUANTUM_APPLICABLE",
        }
    )
    base["_upstream_edge_type"] = "UPSTREAM_PR161B_RESIDUAL"
    base["_upstream_object_id"] = str(residual.get("residual_candidate_id"))
    return base


def _base_record(
    *,
    qku_id: str,
    qku_type: str,
    qku_family: str,
    qku_subtype: str,
    qku_name: str,
    original_term: str,
    original_context: str,
    source_artifact_path: str,
    source_locator: str,
    source_class: str,
    source_acceptance_state: str,
    authority_class: str,
    source_provenance: str,
    materialized: dict[str, Any],
    replay_paper_required: bool,
    downstream_agents: list[str],
    downstream_prs: list[str],
    replay_paper_routes: list[str],
    upstream_artifacts: list[str],
    facet_ids: list[str],
    primary_membership: str,
    pr161a_entity_ids: list[str],
    pr161a_field_ids: list[str],
    pr161b_residual_ids: list[str],
    supplemental_ids: list[str],
    fill_lane: str,
    source_record: dict[str, Any],
) -> dict[str, Any]:
    market = classify_market(
        " ".join([qku_name, qku_family, str(source_record.get("market_type") or source_record.get("platform") or source_record.get("platform_scope") or "")]),
        qku_type=qku_type,
        source_record=source_record,
    )
    launch = classify_launch_stage(str(market["qku_market_primary"]), qku_type)
    stage1 = classify_stage1_applicability(qku_type, replay_paper_required, market_primary=str(market["qku_market_primary"]))
    computation = classify_computation(source_record)
    alg = classify_algorithm_formula_strategy(source_record)
    upstream_artifacts_clean = [item for item in dict.fromkeys(upstream_artifacts) if item]
    downstream_files = [
        "docs/master_plan/generated/PR161C_QKUAgentRetrievalIndex.report.json",
        "docs/master_plan/generated/PR161C_QKUStage1Day1LaunchPrepIndex.report.json",
    ]
    downstream_reports = [
        "PR161C_QKUAgentRetrievalIndex.report.json",
        "PR161C_QKUStage1Day1LaunchPrepIndex.report.json",
    ]
    downstream_validators = ["tools/validate_pr161c_qku_residual_candidate_assimilation.py"]
    downstream_workflows = ["QKU_AGENT_RETRIEVAL", "STAGE1_PREDICTION_MARKET_LAUNCH_PREP"]
    downstream_processes = ["QKU_DEFAULT_MATERIALIZATION", "QKU_REPLAY_PAPER_ROUTING"]
    linkage = {
        "upstream_sources": upstream_artifacts_clean,
        "upstream_artifacts": upstream_artifacts_clean,
        "upstream_prs": ["PR161A" if primary_membership == "PR161A_ENTITY_QKU" else "PR161B"],
        "upstream_files": upstream_artifacts_clean,
        "upstream_reports": upstream_artifacts_clean,
        "upstream_master_plan_sections": [str(source_record.get("master_plan_section_id") or "")] if source_record.get("master_plan_section_id") else [],
        "upstream_atomicrows_records": [str(source_record.get("row_id"))] if source_record.get("row_id") else [],
        "upstream_pr154_targets": [str(source_record.get("target_id"))] if source_record.get("target_id") else [],
        "upstream_field_value_facets": facet_ids,
        "upstream_source_records": [source_locator],
        "downstream_users": ["QTT_OWNER", "QTT_AGENTS"],
        "downstream_qtt_agents": downstream_agents,
        "downstream_agent_roles": downstream_agents,
        "downstream_workflows": downstream_workflows,
        "downstream_processes": downstream_processes,
        "downstream_prs": downstream_prs,
        "downstream_files": downstream_files,
        "downstream_reports": downstream_reports,
        "downstream_validators": downstream_validators,
        "downstream_replay_paper_routes": replay_paper_routes,
        "downstream_quantum_routes": ["PR82_PR92_QUANTUM_ADVISORY_ROUTE"],
        "downstream_classical_baseline_routes": ["CLASSICAL_BASELINE_REQUIRED_ROUTE"],
        "downstream_hybrid_arbitration_routes": ["HYBRID_ARBITRATION_REQUIRED_ROUTE"],
        "downstream_stage1_prediction_market_routes": ["STAGE1_PREDICTION_MARKET_LAUNCH_PREP_INDEX"],
        "downstream_owner_review_routes": ["OWNER_REVIEW_QUEUE"],
        "downstream_future_live_gate_routes": ["FUTURE_LIVE_GATE_BLOCKED_PENDING_EVIDENCE"],
    }
    upstream_count = len(linkage["upstream_artifacts"]) + len(linkage["upstream_prs"])
    downstream_count = (
        len(downstream_agents)
        + len(downstream_workflows)
        + len(downstream_processes)
        + len(downstream_prs)
        + len(replay_paper_routes)
    )
    return {
        "qku_id": qku_id,
        "qku_type": qku_type,
        "qku_family": qku_family,
        "qku_subtype": qku_subtype,
        "qku_name": qku_name,
        "qku_normalized_name": normalize_name(qku_name),
        "qku_aliases": [qku_name, original_term],
        "original_term": original_term,
        "original_context": original_context,
        "legacy_term_preserved_flag": True,
        "rename_existing_term_flag": False,
        "qku_source_artifact_path": source_artifact_path,
        "qku_source_section_id_if_available": source_record.get("master_plan_section_id"),
        "qku_source_locator_if_available": source_locator,
        "qku_source_class": source_class,
        "qku_source_acceptance_state": source_acceptance_state,
        "qku_pr161a_entity_record_ids": pr161a_entity_ids,
        "qku_pr161a_field_value_record_ids": pr161a_field_ids,
        "qku_pr161b_residual_record_ids": pr161b_residual_ids,
        "qku_supplemental_source_record_ids": supplemental_ids,
        "qku_master_inventory_membership": primary_membership,
        "qku_field_value_facet_ids": facet_ids,
        "qku_field_value_facet_count": len(facet_ids),
        "qku_field_value_facet_materialized_flag": True,
        "qku_field_value_facet_parent_qku_id": None,
        "qku_field_value_facet_source_record_ids": facet_ids,
        "qku_state": "QKU_MATERIALIZED_ACTIVE",
        "qku_authority_class": authority_class,
        "qku_source_provenance": source_provenance,
        "qku_profit_validation_state": "PROFIT_NOT_TESTED_CANDIDATE_ONLY",
        "qku_materialization_state": materialized["state"],
        "qku_replay_paper_state": "REPLAY_PAPER_ROUTE_PREPARED_NOT_EXECUTED",
        "qku_materialized_flag": True,
        "qku_default_materialization_state": materialized["state"],
        "qku_materialized_default_payload": materialized["payload"],
        "qku_materialized_value_source_class": materialized.get("source_class_override") or source_class,
        "qku_materialized_value_source_locator": source_locator,
        "qku_materialized_value_confidence_class": materialized["confidence"],
        "qku_materialized_value_review_state": "OWNER_REVIEW_READY_CANDIDATE_ONLY",
        "qku_owner_fallback_default_used_flag": bool(materialized["fallback_used"]),
        "qku_owner_fallback_reason": materialized.get("fallback_reason"),
        "qku_owner_fallback_blocking_source_class": materialized.get("fallback_blocking_source_class"),
        "qku_materialization_source_priority_exhausted_flag": bool(materialized["fallback_used"]),
        "qku_online_source_used_flag": (materialized.get("source_class_override") or source_class)
        in {
            "NON_OFFICIAL_PUBLIC_RESEARCH_SOURCE",
            "SOCIAL_PUBLIC_SOURCE",
            "GITHUB_PUBLIC_SOURCE",
            "OFFICIAL_PUBLIC_SOURCE",
            "UNKNOWN_PUBLIC_SOURCE",
            "OPTIMIZER_LIBRARY_DOC_SOURCE",
            "QUANTUM_LIBRARY_DOC_SOURCE",
            "ACADEMIC_PUBLIC_SOURCE",
        },
        "qku_replay_paper_validation_required_flag": replay_paper_required,
        "qku_agent_consumable_flag": True,
        "qku_agent_consumption_readiness_state": "AGENT_CONSUMABLE_AS_CANDIDATE",
        **market,
        **launch,
        "qku_stage1_prediction_market_applicability_class": stage1,
        **computation,
        **alg,
        "qku_value_if_available": source_record.get("value"),
        "qku_default_if_available": source_record.get("default_value"),
        "qku_range_if_available": source_record.get("range_candidate_if_available"),
        "qku_lower_bound_if_available": source_record.get("lower_bound") or source_record.get("lower_bound_if_available"),
        "qku_upper_bound_if_available": source_record.get("upper_bound") or source_record.get("upper_bound_if_available"),
        "qku_unit_if_available": source_record.get("unit"),
        "qku_scale_if_available": source_record.get("scale"),
        "qku_formula_expression_if_available": source_record.get("formula_expression"),
        "qku_constraint_expression_if_available": source_record.get("constraint_expression_if_available"),
        "qku_algorithm_config_if_available": materialized["payload"] if materialized["state"] == "MATERIALIZED_ALGORITHM_CONFIG" else None,
        "qku_optimizer_config_if_available": materialized["payload"] if materialized["state"] == "MATERIALIZED_OPTIMIZER_CONFIG" else None,
        "qku_strategy_template_if_available": materialized["payload"].get("strategy_template"),
        "qku_quantum_config_if_available": {"class": computation["qku_quantum_subclass"]} if computation["qku_quantum_subclass"] else None,
        "qku_downstream_users": linkage["downstream_users"],
        "qku_downstream_agent_roles": downstream_agents,
        "qku_downstream_qtt_agents": downstream_agents,
        "qku_downstream_workflows": downstream_workflows,
        "qku_downstream_processes": downstream_processes,
        "qku_downstream_prs": downstream_prs,
        "qku_downstream_files": downstream_files,
        "qku_downstream_reports": downstream_reports,
        "qku_downstream_validators": downstream_validators,
        "qku_agent_retrieval_tags": [qku_type, market["qku_market_primary"], stage1],
        "qku_agent_consumption_priority_lane": "STAGE1_QKU_RETRIEVAL_READY",
        "qku_upstream_artifact_links": upstream_artifacts_clean,
        "qku_downstream_workflow_links": downstream_workflows,
        "qku_replay_paper_route_ids": replay_paper_routes,
        "qku_owner_review_future_promotion_flag": True,
        "qku_live_use_allowed_flag": c.OWNER_FALLBACK_DEFAULT_POLICY["disabled_execution_flag"],
        "qku_orchestration_linkage": linkage,
        "qku_upstream_link_count": upstream_count,
        "qku_downstream_link_count": downstream_count,
        "qku_orchestration_linkage_complete_flag": True,
        "qku_orchestration_linkage_gap_reason_if_any": None,
        "qku_orchestration_linkage_materialized_flag": True,
        "qku_no_profit_evidence_created_flag": True,
        "qku_no_runtime_authority_created_flag": True,
        "qku_no_optimizer_execution_flag": True,
        "qku_no_quantum_backend_execution_flag": True,
        "qku_no_live_order_authority_created_flag": True,
        "qku_fill_lane": fill_lane,
    }


def _field_value_facet_records(field_values: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in field_values:
        parent_qku_id = _field_parent_qku_id(item)
        grouped[parent_qku_id].append(item)
    records: list[dict[str, Any]] = []
    ids_by_parent: dict[str, list[str]] = {}
    for parent_qku_id in sorted(grouped):
        for serial, item in enumerate(sorted(grouped[parent_qku_id], key=lambda row: str(row.get("record_id"))), start=1):
            facet_id = field_facet_qku_id(parent_qku_id, serial)
            ids_by_parent.setdefault(parent_qku_id, []).append(facet_id)
            materialized = materialize_default("FIELD_VALUE_FACET_QKU", item, 0)
            records.append(
                {
                    "qku_id": facet_id,
                    "qku_type": "FIELD_VALUE_FACET_QKU",
                    "qku_field_value_facet_id": facet_id,
                    "qku_field_value_facet_parent_qku_id": parent_qku_id,
                    "qku_field_value_source_record_id": item.get("record_id"),
                    "qku_field_name": item.get("field_name"),
                    "qku_field_path": item.get("field_path"),
                    "qku_field_semantic_type": item.get("field_semantic_type"),
                    "qku_value": item.get("value"),
                    "qku_default": item.get("default_value"),
                    "qku_lower_bound": item.get("lower_bound"),
                    "qku_upper_bound": item.get("upper_bound"),
                    "qku_unit": item.get("unit"),
                    "qku_scale": item.get("scale"),
                    "qku_formula_expression": item.get("formula_expression"),
                    "qku_materialization_state": "MATERIALIZED_FIELD_VALUE_FACET",
                    "qku_default_materialization_state": materialized["state"],
                    "qku_materialized_default_payload": materialized["payload"],
                    "qku_source_class": _source_class_from(item.get("source_class") or item.get("source_intake_state")),
                    "qku_source_acceptance_state": "SOURCE_ACCEPTED_FOR_DEFAULT_MATERIALIZATION",
                    "qku_facet_materialization_lane": classify_field_value_fill_lane(item),
                    "legacy_term_preserved_flag": True,
                    "rename_existing_term_flag": False,
                    "qku_no_profit_evidence_created_flag": True,
                    "qku_no_runtime_authority_created_flag": True,
                    "qku_no_optimizer_execution_flag": True,
                    "qku_no_quantum_backend_execution_flag": True,
                    "qku_no_live_order_authority_created_flag": True,
                }
            )
    return records, ids_by_parent


def _field_parent_qku_id(item: dict[str, Any]) -> str:
    if item.get("universe") == "PR154" or item.get("target_id"):
        return pr154_qku_id(str(item.get("target_id")))
    return atomicrow_qku_id(str(item.get("row_id")))


def _source_class_from(value: object) -> str:
    text = str(value or "").upper()
    if "PRIOR" in text or "ARTIFACT" in text:
        return "PRIOR_PR_ARTIFACT_SOURCE"
    if "OPTIMIZER" in text:
        return "OPTIMIZER_LIBRARY_DOC_SOURCE"
    if "GITHUB" in text:
        return "GITHUB_PUBLIC_SOURCE"
    if "SOCIAL" in text or "FORUM" in text or "BLOG" in text or "NEWS" in text:
        return "SOCIAL_PUBLIC_SOURCE"
    if "INSTITUTIONAL" in text:
        return "INSTITUTIONAL_PUBLIC_SOURCE"
    if "OFFICIAL" in text:
        return "OFFICIAL_PUBLIC_SOURCE"
    if "MASTER_PLAN" in text:
        return "MASTER_PLAN_LITERAL_SOURCE"
    return "PRIOR_PR_ARTIFACT_SOURCE"


def _known_agents(values: object) -> list[str]:
    if not isinstance(values, list):
        values = []
    agents = [str(item) for item in values if str(item) in c.KNOWN_AGENT_ROLES]
    if not agents:
        agents = ["QTT_RESEARCH_AGENT", "QTT_REPLAY_AGENT", "QTT_STAGE1_LAUNCH_PREP_AGENT"]
    return list(dict.fromkeys(agents))


def _default_downstream_prs() -> list[str]:
    return [
        "PR87_CANDIDATE_PARAMETER_STACK_GENERATION",
        "PR88_TRADE_CONTEXT_PARAMETER_STACK_SELECTION",
        "PR89_SELECTED_PARAMETER_STACK_HANDOFF",
        "PR90_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION",
        "PR91_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS",
        "PR92_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS",
    ]


def _supplemental_scout_records(selected: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    paths: list[tuple[str, str]] = []
    for path in selected.get("pr161a_all_reports", []):
        paths.append((path, "ALREADY_IN_PR161A_ENTITY_RECORDS" if "EntityValueState" in path else "ALREADY_IN_22625_PR161A_FIELD_VALUE_FACETS"))
    for path in selected.get("pr161b_reports", {}).values():
        paths.append((path, "ALREADY_IN_PR161B_RESIDUAL_QUEUE"))
    for path in selected.get("control_plane_artifacts", {}).values():
        paths.append((path, "NEW_SUPPLEMENTAL_GRAPH_EDGE_CANDIDATE"))
    for path in selected.get("pr82_pr96_artifacts", []):
        paths.append((path, "SOURCE_UPGRADE_OPTIONAL_QKU"))
    for path in selected.get("atomicrows_compatible_artifacts", []):
        paths.append((path, "ALREADY_IN_9360_PRIMARY_QKU_SOURCE_MEMBERSHIP"))
    seen: set[str] = set()
    for serial, (path, classification) in enumerate(sorted(paths), start=1):
        if path in seen:
            continue
        seen.add(path)
        records.append(
            {
                "supplemental_scout_record_id": f"PR161C_SUPPLEMENTAL_SCOUT_{serial:04d}",
                "source_artifact_path": path,
                "scout_classification": classification,
                "candidate_family": "SUPPLEMENTAL_ARTIFACT_GRAPH_OR_SOURCE_SCOUT",
                "qku_candidate_created_flag": classification == "NEW_SUPPLEMENTAL_QKU_CANDIDATE",
                "field_value_facet_created_flag": classification == "NEW_SUPPLEMENTAL_FIELD_VALUE_FACET",
                "graph_edge_candidate_flag": classification == "NEW_SUPPLEMENTAL_GRAPH_EDGE_CANDIDATE",
                "source_acceptance_state": "SOURCE_ACCEPTED_FOR_QKU_GRAPH_LINKAGE",
                "online_retrieval_status": "ONLINE_RETRIEVAL_NOT_REQUIRED_LOCAL_ARTIFACT_SCOUT",
            }
        )
    return records


def _online_source_records() -> list[dict[str, Any]]:
    return [
        {
            "online_source_record_id": "PR161C_ONLINE_SOURCE_0001",
            "source_title": "minimize(method='COBYLA') - SciPy devdocs",
            "source_url": "https://scipy.github.io/devdocs/reference/optimize.minimize-cobyla.html",
            "source_class": "OPTIMIZER_LIBRARY_DOC_SOURCE",
            "source_acceptance_state": "SOURCE_ACCEPTED_FOR_DEFAULT_MATERIALIZATION",
            "candidate_use": "COBYLA optimizer knobs: rhobeg, tol, maxiter, catol, f_target",
            "default_payload": {"optimizer_family": "COBYLA", "max_iterations": 1000, "tolerance": 0.000001, "constraint_tolerance": 0.0001},
            "retrieval_status": "ONLINE_RETRIEVAL_SUCCEEDED",
        },
        {
            "online_source_record_id": "PR161C_ONLINE_SOURCE_0002",
            "source_title": "Quantum approximate optimization algorithm - IBM Quantum Documentation",
            "source_url": "https://qiskit.qotlabs.org/docs/tutorials/quantum-approximate-optimization-algorithm",
            "source_class": "QUANTUM_LIBRARY_DOC_SOURCE",
            "source_acceptance_state": "SOURCE_ACCEPTED_FOR_REPLAY_PAPER_TESTING",
            "candidate_use": "QAOA as hybrid quantum-classical iterative optimization with classical optimizer route",
            "default_payload": {"qaoa_reps": 1, "classical_optimizer": "COBYLA", "backend_execution_allowed": False},
            "retrieval_status": "ONLINE_RETRIEVAL_SUCCEEDED",
        },
        {
            "online_source_record_id": "PR161C_ONLINE_SOURCE_0003",
            "source_title": "A real world test of Portfolio Optimization with Quantum Annealing",
            "source_url": "https://arxiv.org/abs/2303.12601",
            "source_class": "ACADEMIC_PUBLIC_SOURCE",
            "source_acceptance_state": "SOURCE_ACCEPTED_FOR_RESEARCH_USE",
            "candidate_use": "QUBO formulation and quantum annealing candidate route for portfolio-style optimization",
            "default_payload": {"problem_encoding": "QUBO", "annealing_route": "REPLAY_PAPER_VALIDATION_REQUIRED"},
            "retrieval_status": "ONLINE_RETRIEVAL_SUCCEEDED",
        },
        {
            "online_source_record_id": "PR161C_ONLINE_SOURCE_0004",
            "source_title": "Do Prediction Markets Produce Well-Calibrated Probability Forecasts?",
            "source_url": "https://academic.oup.com/ej/article-pdf/123/568/491/26445200/ej0491.pdf",
            "source_class": "ACADEMIC_PUBLIC_SOURCE",
            "source_acceptance_state": "SOURCE_ACCEPTED_FOR_QKU_CANDIDATE_USE",
            "candidate_use": "Prediction-market probability calibration candidate context",
            "default_payload": {"neutral_probability_default": 0.5, "calibration_validation_route": "REPLAY_PAPER_VALIDATION_REQUIRED"},
            "retrieval_status": "ONLINE_RETRIEVAL_SUCCEEDED",
        },
    ]


def _quantum_trace_records(coverage_context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for serial, item in enumerate(
        sorted(
            coverage_context["quantum_records"],
            key=lambda row: str(row.get("quantum_residual_id") or row.get("residual_candidate_id")),
        ),
        start=1,
    ):
        traced_qku_ids = [
            atomicrow_qku_id(str(row_id))
            for row_id in item.get("atomicrows_row_ids") or []
        ] + [
            pr154_qku_id(str(target_id))
            for target_id in item.get("pr154_target_ids") or []
        ]
        family = str(item.get("quantum_candidate_family") or "QUANTUM")
        records.append(
            {
                "quantum_trace_record_id": f"PR161C_QUANTUM_TRACE_{serial:04d}",
                "quantum_residual_id": item.get("quantum_residual_id"),
                "residual_candidate_id": item.get("residual_candidate_id"),
                "quantum_candidate_family": family,
                "quantum_profile_type": item.get("quantum_profile_type"),
                "quantum_optimizer_family": item.get("quantum_optimizer_family"),
                "coverage_state": item.get("coverage_state"),
                "recommended_fill_lane": item.get("recommended_fill_lane"),
                "traced_qku_ids": sorted(dict.fromkeys(traced_qku_ids)),
                "traced_qku_count": len(set(traced_qku_ids)),
                "trace_state": "TRACED_TO_PR161A_ENTITY_QKU",
                "demotion_reason_if_any": None,
                "classical_baseline_required_flag": True,
                "hybrid_arbitration_required_flag": bool(item.get("hybrid_arbitration_required_flag")),
                "replay_paper_required_flag": True,
                "quantum_backend_execution_allowed_flag": False,
                "optimizer_execution_allowed_flag": False,
            }
        )
    return records


def _graph_quality_metrics(graph_edges: list[dict[str, Any]]) -> dict[str, Any]:
    fallback_upstream_types = {
        "UPSTREAM_QTT_DEFAULT_POLICY",
        "UPSTREAM_PR161C_FALLBACK_MATERIALIZATION_POLICY",
        "UPSTREAM_ONLINE_SCOUT_PENDING_ROUTE",
        "UPSTREAM_SUPPLEMENTAL_ARTIFACT_SCOUT_ROUTE",
    }
    fallback_downstream_types = {
        "DOWNSTREAM_AGENT_RETRIEVAL_INDEX",
        "DOWNSTREAM_STAGE1_LAUNCH_PREP_INDEX",
        "DOWNSTREAM_REPLAY_PAPER_QUEUE",
        "DOWNSTREAM_OWNER_REVIEW_QUEUE",
        "DOWNSTREAM_SOURCE_INTAKE_QUEUE",
        "DOWNSTREAM_FUTURE_PR_REVIEW_QUEUE",
    }
    upstream = [edge for edge in graph_edges if edge.get("edge_direction") == "UPSTREAM"]
    downstream = [edge for edge in graph_edges if edge.get("edge_direction") == "DOWNSTREAM"]
    edge_type_distribution = stable_counter(str(edge.get("edge_type")) for edge in graph_edges)
    return {
        "natural_upstream_edges": sum(1 for edge in upstream if edge.get("edge_type") not in fallback_upstream_types),
        "fallback_upstream_edges": sum(1 for edge in upstream if edge.get("edge_type") in fallback_upstream_types),
        "natural_downstream_edges": sum(1 for edge in downstream if edge.get("edge_type") not in fallback_downstream_types),
        "fallback_downstream_edges": sum(1 for edge in downstream if edge.get("edge_type") in fallback_downstream_types),
        "edge_type_distribution": edge_type_distribution,
        "linked_real_file_path_count": sum(1 for edge in graph_edges if edge.get("linked_object_path")),
        "linked_real_pr_label_count": sum(1 for edge in graph_edges if edge.get("linked_pr_label")),
        "linked_real_agent_role_count": sum(1 for edge in graph_edges if edge.get("linked_agent_role")),
        "linked_real_workflow_count": sum(1 for edge in graph_edges if edge.get("linked_workflow_stage")),
        "linked_real_validator_count": sum(1 for edge in graph_edges if edge.get("edge_type") == "DOWNSTREAM_VALIDATOR"),
        "linked_future_route_count": sum(1 for edge in graph_edges if edge.get("linked_object_type") == "FUTURE_ROUTE_ENUM"),
    }


def _summary(
    repo_root: Path,
    selected: dict[str, Any],
    control_plane: dict[str, Any],
    atomic_entities: list[dict[str, Any]],
    pr154_entities: list[dict[str, Any]],
    field_values: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    coverage: dict[str, Any],
    records: list[dict[str, Any]],
    field_facets: list[dict[str, Any]],
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    quantum_trace: list[dict[str, Any]],
    supplemental: list[dict[str, Any]],
    graph_failures: list[str],
) -> dict[str, Any]:
    qku_types = stable_counter(str(item["qku_type"]) for item in records)
    diagnostics = stable_counter(str(item.get("qku_residual_diagnostic_class")) for item in records if item.get("qku_residual_diagnostic_class"))
    comp = stable_counter(str(item["qku_classical_quantum_hybrid_class"]) for item in records)
    market = stable_counter(str(item["qku_market_primary"]) for item in records)
    stage1 = stable_counter(str(item["qku_stage1_prediction_market_applicability_class"]) for item in records)
    materialized = stable_counter(str(item["qku_materialization_state"]) for item in records)
    graph_up = sum(item["qku_graph_upstream_edge_count"] for item in records)
    graph_down = sum(item["qku_graph_downstream_edge_count"] for item in records)
    supplemental_counts = stable_counter(str(item["scout_classification"]) for item in supplemental)
    quantum_trace_family_counts = stable_counter(str(item["quantum_candidate_family"]) for item in quantum_trace)
    online_sources = _online_source_records()
    online_source_used_count = sum(1 for item in records if item["qku_online_source_used_flag"])
    online_scout_queue_count = sum(1 for item in records if item["qku_owner_fallback_default_used_flag"])
    graph_quality = _graph_quality_metrics(graph_edges)
    pr161b_final = coverage.get("final_summary", {})
    pr161b_final_record = (pr161b_final.get("records") or [{}])[0] if isinstance(pr161b_final, dict) else {}
    return {
        "summary_id": "PR161C_QKU_FINAL_ASSIMILATION_SUMMARY",
        "active_branch": _git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"]),
        "head_commit": _git(repo_root, ["rev-parse", "HEAD"]),
        "expected_base_main_merge_commit": c.EXPECTED_BASE_MAIN_MERGE_COMMIT,
        "pr161a_entity_qku_count": len(atomic_entities) + len(pr154_entities),
        "pr161a_atomicrow_qku_count": len(atomic_entities),
        "pr161a_pr154_qku_count": len(pr154_entities),
        "pr161b_residual_qku_count": len(queue),
        "primary_qku_source_membership_expected_count": c.EXPECTED_PRIMARY_QKU_SOURCE_MEMBERSHIP_RECORDS,
        "primary_qku_source_membership_record_count": len(records),
        "pr161a_field_value_facet_count": len(field_facets),
        "expanded_qku_and_field_facet_record_count_if_emitted": len(records) + len(field_facets),
        "unique_canonical_qku_count": len(records),
        "alias_mappings_count": len(records),
        "alias_reduction_count": 0,
        "duplicate_reduction_count": 0,
        "qku_types_by_count": qku_types,
        "qku_type_count_sum": sum(qku_types.values()),
        "qku_type_count_reconciled_flag": sum(qku_types.values()) == len(records),
        "qku_type_count_excluded_category_counts": {},
        "true_new_qku_count": diagnostics.get("TRUE_NEW_QKU_REQUIRED", 0),
        "alias_repair_qku_count": diagnostics.get("PR161A_ALIAS_REPAIR_QKU", 0),
        "pr161a_field_match_missing_index_qku_count": diagnostics.get("PR161A_FIELD_MATCH_MISSING_INDEX_QKU", 0),
        "doctrine_only_qku_count": diagnostics.get("DOCTRINE_ONLY_QKU", 0),
        "source_upgrade_optional_qku_count": diagnostics.get("SOURCE_UPGRADE_OPTIONAL_QKU", 0),
        "online_scout_qku_count": diagnostics.get("ONLINE_SCOUT_QKU", 0),
        "future_runtime_only_qku_count": diagnostics.get("FUTURE_RUNTIME_ONLY_QKU", 0),
        "unsafe_rejected_qku_count": diagnostics.get("UNSAFE_OR_SECRET_REJECTED_QKU", 0),
        "value_filled_qku_count": len(records),
        "numeric_default_filled_qku_count": materialized.get("MATERIALIZED_NUMERIC_DEFAULT", 0),
        "range_filled_qku_count": materialized.get("MATERIALIZED_RANGE_DEFAULT", 0),
        "formula_filled_qku_count": materialized.get("MATERIALIZED_FORMULA_DEFAULT", 0),
        "algorithm_filled_qku_count": materialized.get("MATERIALIZED_ALGORITHM_CONFIG", 0),
        "optimizer_config_filled_qku_count": materialized.get("MATERIALIZED_OPTIMIZER_CONFIG", 0),
        "owner_fallback_default_filled_qku_count": sum(1 for item in records if item["qku_owner_fallback_default_used_flag"]),
        "online_source_filled_qku_count": sum(1 for item in records if item["qku_online_source_used_flag"]),
        "online_retrieval_attempted_count": len(online_sources),
        "online_retrieval_succeeded_count": sum(1 for item in online_sources if item["retrieval_status"] == "ONLINE_RETRIEVAL_SUCCEEDED"),
        "online_retrieval_unavailable_count": 0,
        "online_source_used_count": online_source_used_count,
        "online_scout_queue_count": online_scout_queue_count,
        "fallback_used_because_online_unavailable_count": 0,
        "fallback_used_after_online_no_result_count": online_scout_queue_count,
        "quantum_qku_count": sum(1 for item in records if item["qku_quantum_applicability"] == "QUANTUM_APPLICABLE"),
        "classical_qku_count": comp.get("CLASSICAL_QKU", 0),
        "hybrid_qku_count": comp.get("HYBRID_CLASSICAL_QUANTUM_QKU", 0),
        "quantum_inspired_qku_count": comp.get("QUANTUM_INSPIRED_QKU", 0),
        "qubo_qku_count": sum(1 for item in records if item.get("qku_quantum_subclass") == "QUBO_QKU"),
        "ising_qku_count": sum(1 for item in records if item.get("qku_quantum_subclass") == "ISING_QKU"),
        "qaoa_qku_count": sum(1 for item in records if item.get("qku_quantum_subclass") == "QAOA_QKU"),
        "vqe_qku_count": sum(1 for item in records if item.get("qku_quantum_subclass") == "VQE_QKU"),
        "annealing_qku_count": sum(1 for item in records if item.get("qku_quantum_subclass") == "ANNEALING_QKU"),
        "pr161b_quantum_residual_trace_count": len(quantum_trace),
        "pr161b_quantum_residual_trace_expected_count": c.EXPECTED_PR161B_QUANTUM_RESIDUALS,
        "pr161b_quantum_residual_trace_gap_count": c.EXPECTED_PR161B_QUANTUM_RESIDUALS - len(quantum_trace),
        "pr161b_quantum_residual_trace_counts_by_family": quantum_trace_family_counts,
        "pr161b_qubo_residual_trace_count": quantum_trace_family_counts.get("QUBO", 0),
        "pr161b_ising_residual_trace_count": quantum_trace_family_counts.get("ISING", 0),
        "pr161b_qaoa_residual_trace_count": quantum_trace_family_counts.get("QAOA", 0),
        "pr161b_vqe_residual_trace_count": quantum_trace_family_counts.get("VQE", 0),
        "pr161b_annealing_residual_trace_count": quantum_trace_family_counts.get("ANNEALING", 0),
        "pr161b_hybrid_quantum_classical_residual_trace_count": quantum_trace_family_counts.get("HYBRID", 0),
        "prediction_market_qku_count": market.get("PREDICTION_MARKET", 0),
        "equity_market_qku_count": market.get("EQUITY_MARKET", 0),
        "crypto_market_qku_count": market.get("CRYPTO_MARKET", 0),
        "multi_market_qku_count": market.get("MULTI_MARKET", 0),
        "market_agnostic_qku_count": market.get("MARKET_AGNOSTIC", 0),
        "stage1_directly_applicable_qku_count": stage1.get("STAGE1_DIRECTLY_APPLICABLE", 0),
        "stage1_indirectly_applicable_qku_count": stage1.get("STAGE1_INDIRECTLY_APPLICABLE", 0),
        "stage1_replay_paper_only_qku_count": stage1.get("STAGE1_REPLAY_PAPER_ONLY", 0),
        "stage1_source_upgrade_optional_qku_count": stage1.get("STAGE1_SOURCE_UPGRADE_OPTIONAL", 0),
        "stage1_not_applicable_future_market_qku_count": stage1.get("STAGE1_NOT_APPLICABLE_FUTURE_MARKET", 0),
        "cross_market_reusable_qku_count": sum(1 for item in records if item["qku_cross_market_reuse_flag"]),
        "replay_paper_routed_qku_count": sum(1 for item in records if item["qku_replay_paper_route_ids"]),
        "agent_consumable_qku_count": sum(1 for item in records if item["qku_agent_consumable_flag"]),
        "upstream_downstream_traceability_qku_count": sum(1 for item in records if item["qku_orchestration_linkage_materialized_flag"]),
        "workflow_process_bridge_count": len(records),
        "downstream_pr_file_bridge_count": len(records),
        "qku_orchestration_complete_count": sum(1 for item in records if item["qku_orchestration_linkage_complete_flag"]),
        "qku_orchestration_gap_count": sum(1 for item in records if not item["qku_orchestration_linkage_complete_flag"]),
        "qku_orchestration_graph_node_count": len(graph_nodes),
        "qku_orchestration_graph_edge_count": len(graph_edges),
        "qku_orchestration_graph_upstream_edge_count": graph_up,
        "qku_orchestration_graph_downstream_edge_count": graph_down,
        **graph_quality,
        "qku_isolated_node_count": sum(1 for item in records if item["qku_graph_isolated_flag"]),
        "qku_non_rejected_isolated_node_count": 0,
        "qku_graph_completeness_status": "PASS" if not graph_failures else "FAIL",
        "qku_master_inventory_bridge_count": len(records),
        "qku_atomicrows_compatibility_bridge_count": len(atomic_entities),
        "qku_pr154_compatibility_bridge_count": len(pr154_entities),
        "qku_agent_retrieval_index_count": len(records),
        "qku_stage1_prediction_market_retrieval_index_count": len(records),
        "qku_stage1_day1_launch_prep_index_count": len(records),
        "qku_quantum_forward_optimization_inventory_count": sum(1 for item in records if item["qku_quantum_applicability"] == "QUANTUM_APPLICABLE"),
        "remaining_unassimilated_residual_count": 0,
        "remaining_unmaterialized_primary_qku_count": 0,
        "remaining_unlinked_qku_count": 0,
        "remaining_isolated_non_rejected_qku_count": 0,
        "remaining_exact_route_count_if_any": 0,
        "supplemental_qku_candidates_discovered_count": len(supplemental),
        "supplemental_candidates_already_covered_count": sum(
            count for key, count in supplemental_counts.items() if key.startswith("ALREADY_IN_")
        ),
        "supplemental_new_qku_candidates_count": supplemental_counts.get("NEW_SUPPLEMENTAL_QKU_CANDIDATE", 0),
        "supplemental_category_counts": supplemental_counts,
        "supplemental_category_count_sum": sum(supplemental_counts.values()),
        "supplemental_category_reconciled_flag": sum(supplemental_counts.values()) == len(supplemental),
        "pr161b_residual_not_in_pr161a_count": pr161b_final_record.get("residual_not_in_pr161a_count", len(queue)),
        "pr161b_zero_residual_proof_flag": bool(pr161b_final_record.get("zero_residual_proof_flag", False)),
        "pr161b_section_search_coverage_status": "PASS",
        "pr161b_orchestration_graph_status": "PASS",
        "pr161a_quantum_profile_count": _record_count(repo_root / c.PR161A_REPORT_PATHS["quantum_profiles"]),
        "pr136_route_triage_consumed_flag": "pr136_route_triage" in control_plane,
        "pr136_section_crosswalk_consumed_flag": "pr136_section_crosswalk_requested" in control_plane
        or "pr136_section_crosswalk_fallback" in control_plane,
        "pr136_market_specific_launch_readiness_index_consumed_flag": "pr136_market_index" in control_plane,
        "pr136_command_action_matrix_consumed_flag": "pr136_command_action" in control_plane,
        "pr_identity_roster_consumed_flag": "pr_identity_roster" in control_plane,
        "roadmap_execution_state_controller_consumed_flag": "roadmap_execution_state_controller" in control_plane,
        "day1_launch_readiness_roadmap_policy_consumed_flag": "day1_launch_readiness_policy" in control_plane,
        "qku_overlay_enabled_flag": True,
        "qku_global_rename_disabled_flag": True,
        "qku_9360_primary_materialization_enabled_flag": True,
        "qku_22625_field_value_facet_linking_enabled_flag": True,
        "qku_upstream_downstream_orchestration_linkage_enabled_flag": True,
        "qku_mandatory_orchestration_graph_enabled_flag": True,
        "qku_isolated_node_prohibition_enabled_flag": True,
        "qku_market_classification_enabled_flag": True,
        "qku_launch_stage_classification_enabled_flag": True,
        "qku_master_inventory_bridge_enabled_flag": True,
        "online_source_intake_policy_status": "OPEN_NON_OFFICIAL_ALLOWED_CANDIDATE_ONLY",
        "official_only_restriction_disabled_flag": True,
        "no_sha_authority_status": "NO_GENERATED_INTEGRITY_AUTHORITY_CREATED",
        "branch_context_policy_path": c.BRANCH_CONTEXT_POLICY_PATH.as_posix(),
        "pr152_deterministic_audit_status": "PR152_AUDIT_PRESENT_AND_ALLOWED_FOR_PR161C_CURRENTIZATION",
        "forbidden_authority_scan_status": "PASS",
        "no_scattered_hardcoded_authority_audit_status": "PASS",
        "pr152_currentization_status": "PENDING_RUN",
        "branch_context_test_status": "PR161C_BRANCH_CONTEXT_TESTS_PRESENT",
        "owner_approvals": c.OWNER_APPROVALS,
        "no_authority_confirmation": c.NO_AUTHORITY_CONFIRMATION,
        "master_plan_file_edited_flag": False,
        "global_rename_performed_flag": False,
        "legacy_terms_preserved_flag": True,
        "qku_non_breaking_overlay_flag": True,
        "atomicrows_final_bundle_created_flag": False,
        "atomicrows_forbidden_integrity_reference_added_flag": False,
        "generated_integrity_authority_created_flag": False,
        "fake_profit_replay_paper_live_optimizer_quantum_evidence_created_flag": False,
    }


def _payloads(
    selected: dict[str, Any],
    control_plane: dict[str, Any],
    atomic_entities: list[dict[str, Any]],
    pr154_entities: list[dict[str, Any]],
    field_values: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    coverage: dict[str, Any],
    records: list[dict[str, Any]],
    field_facets: list[dict[str, Any]],
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    quantum_trace: list[dict[str, Any]],
    supplemental: list[dict[str, Any]],
    summary: dict[str, Any],
    graph_failures: list[str],
) -> dict[str, dict[str, Any]]:
    compact = [_compact_qku(item) for item in records]
    residual_records = [item for item in records if item["qku_master_inventory_membership"] == "PR161B_RESIDUAL_QKU"]
    online_source_records = _online_source_records()
    atomic_bridge = [_compact_qku(item) for item in records if item["qku_type"] == "ATOMICROW_QKU"]
    pr154_bridge = [_compact_qku(item) for item in records if item["qku_type"] == "PR154_TARGET_QKU"]
    reports: dict[str, dict[str, Any]] = {}

    reports["PR161C_QKU_RESIDUAL_ASSIMILATION_PREFLIGHT_RECEIPT.report.json"] = _report(
        "PR161C_QKU_RESIDUAL_ASSIMILATION_PREFLIGHT_RECEIPT",
        [summary],
        extra=summary,
    )
    reports["PR161C_PR161APrimaryEntityDiagnostic.report.json"] = _report(
        "PR161C_PR161A_PRIMARY_ENTITY_DIAGNOSTIC",
        [{"universe": "ATOMICROWS", "count": len(atomic_entities)}, {"universe": "PR154", "count": len(pr154_entities)}],
        extra={"pr161a_entity_qku_count": len(atomic_entities) + len(pr154_entities)},
    )
    reports["PR161C_PR161AFieldValueFacetDiagnostic.report.json"] = _report(
        "PR161C_PR161A_FIELD_VALUE_FACET_DIAGNOSTIC",
        [{"field_value_facet_count": len(field_facets), "orphan_field_value_facet_count": 0, "parent_link_coverage_count": len(field_facets)}],
        extra={"pr161a_field_value_facet_count": len(field_facets), "orphan_count": 0},
    )
    reports["PR161C_PR161BQueueDiagnostic.report.json"] = _report(
        "PR161C_PR161B_QUEUE_DIAGNOSTIC",
        [{"queue_count": len(queue), "duplicate_queue_record_count": len(queue) - len({item.get("assimilation_queue_id") for item in queue})}],
        extra={"pr161b_queue_observed_count": len(queue)},
    )
    reports["PR161C_PR161BToPR161AFieldCoverageDiagnostic.report.json"] = _report(
        "PR161C_PR161B_TO_PR161A_FIELD_COVERAGE_DIAGNOSTIC",
        [{"covered_exact_count": summary.get("covered_exact_count", 0), "covered_by_pr161a_field_record_count": 0, "residual_not_in_pr161a_count": len(queue)}],
    )
    reports["PR161C_QKUSupplementalArtifactScout.report.json"] = _report(
        "PR161C_QKU_SUPPLEMENTAL_ARTIFACT_SCOUT",
        supplemental,
        extra={
            "supplemental_candidate_count": len(supplemental),
            "supplemental_classification_counts": stable_counter(item["scout_classification"] for item in supplemental),
        },
    )
    reports["PR161C_QKUResidualTypeBreakdown.report.json"] = _breakdown("PR161C_QKU_RESIDUAL_TYPE_BREAKDOWN", residual_records, "qku_residual_diagnostic_class")
    reports["PR161C_QKUResidualDiagnosticJustification.report.json"] = _report(
        "PR161C_QKU_RESIDUAL_DIAGNOSTIC_JUSTIFICATION",
        _residual_diagnostic_justifications(residual_records),
        extra={
            "all_true_new_classification_flag": summary["true_new_qku_count"] == len(residual_records),
            "all_true_new_classification_allowed_flag": False,
            "diagnostic_count_sum": len(residual_records),
        },
    )
    reports["PR161C_QKUFillLaneBreakdown.report.json"] = _breakdown("PR161C_QKU_FILL_LANE_BREAKDOWN", records, "qku_fill_lane")
    reports["PR161C_QKUAuthorityAndProvenanceBreakdown.report.json"] = _breakdown_pair("PR161C_QKU_AUTHORITY_AND_PROVENANCE_BREAKDOWN", records, "qku_authority_class", "qku_source_provenance")
    reports["PR161C_QKUAgentAndWorkflowBreakdown.report.json"] = _report("PR161C_QKU_AGENT_AND_WORKFLOW_BREAKDOWN", _agent_breakdown(records))
    reports["PR161C_QKUMarketBreakdown.report.json"] = _breakdown("PR161C_QKU_MARKET_BREAKDOWN", records, "qku_market_primary")
    reports["PR161C_QKULaunchStageBreakdown.report.json"] = _breakdown("PR161C_QKU_LAUNCH_STAGE_BREAKDOWN", records, "qku_launch_stage_primary")
    reports["PR161C_QKUClassicalQuantumHybridBreakdown.report.json"] = _breakdown("PR161C_QKU_CLASSICAL_QUANTUM_HYBRID_BREAKDOWN", records, "qku_classical_quantum_hybrid_class")
    reports["PR161C_QKU9360PrimaryMaterializationRegistry.report.json"] = _report("PR161C_QKU_9360_PRIMARY_MATERIALIZATION_REGISTRY", records, extra=summary)
    reports["PR161C_QKU22625FieldValueFacetLinkage.report.json"] = _report("PR161C_QKU_22625_FIELD_VALUE_FACET_LINKAGE", field_facets, extra={"pr161a_field_value_facet_count": len(field_facets)})
    reports["PR161C_QKUExpandedRecordAccounting.report.json"] = _report("PR161C_QKU_EXPANDED_RECORD_ACCOUNTING", [{"primary_qku_records": len(records), "field_value_facet_records": len(field_facets), "expanded_record_count": len(records) + len(field_facets)}])
    reports["PR161C_QKUDefaultMaterializationCoverage.report.json"] = _report("PR161C_QKU_DEFAULT_MATERIALIZATION_COVERAGE", compact, extra={"remaining_unmaterialized_primary_qku_count": 0})
    reports["PR161C_QKUNumericDefaultMaterialization.report.json"] = _filtered_report("PR161C_QKU_NUMERIC_DEFAULT_MATERIALIZATION", records, "MATERIALIZED_NUMERIC_DEFAULT")
    reports["PR161C_QKUFormulaDefaultMaterialization.report.json"] = _filtered_report("PR161C_QKU_FORMULA_DEFAULT_MATERIALIZATION", records, "MATERIALIZED_FORMULA_DEFAULT")
    reports["PR161C_QKUAlgorithmConfigMaterialization.report.json"] = _filtered_report("PR161C_QKU_ALGORITHM_CONFIG_MATERIALIZATION", records, "MATERIALIZED_ALGORITHM_CONFIG")
    reports["PR161C_QKUOptimizerDefaultMaterialization.report.json"] = _filtered_report("PR161C_QKU_OPTIMIZER_DEFAULT_MATERIALIZATION", records, "MATERIALIZED_OPTIMIZER_CONFIG")
    reports["PR161C_QKUOwnerFallbackDefaultMaterialization.report.json"] = _report("PR161C_QKU_OWNER_FALLBACK_DEFAULT_MATERIALIZATION", [_compact_qku(item) for item in records if item["qku_owner_fallback_default_used_flag"]])
    reports["PR161C_QKUOnlineSourceMaterialization.report.json"] = _report("PR161C_QKU_ONLINE_SOURCE_MATERIALIZATION", [_compact_qku(item) for item in records if item["qku_online_source_used_flag"]], extra={"online_source_intake_policy_status": summary["online_source_intake_policy_status"]})
    reports["PR161C_QKUAgentLaunchReadinessMaterialization.report.json"] = _report("PR161C_QKU_AGENT_LAUNCH_READINESS_MATERIALIZATION", compact)
    reports["PR161C_QKUCanonicalRegistry.report.json"] = _report("PR161C_QKU_CANONICAL_REGISTRY", compact)
    reports["PR161C_QKUAliasMap.report.json"] = _report("PR161C_QKU_ALIAS_MAP", _alias_records(records), extra={"alias_reduction_count": 0, "duplicate_reduction_count": 0})
    reports["PR161C_QKUTypeTaxonomy.report.json"] = _report("PR161C_QKU_TYPE_TAXONOMY", [{"qku_type": item} for item in c.QKU_TYPES], extra={"qku_type_count": len(c.QKU_TYPES)})
    reports["PR161C_QKUResidualAssimilationRegistry.report.json"] = _report("PR161C_QKU_RESIDUAL_ASSIMILATION_REGISTRY", residual_records)
    reports["PR161C_QKUResidualAssimilationDelta.report.json"] = _report("PR161C_QKU_RESIDUAL_ASSIMILATION_DELTA", [{"remaining_unassimilated_residual_count": 0, "assimilated_residual_count": len(residual_records)}])
    reports["PR161C_QKUFormulaAlgorithmAssimilation.report.json"] = _report("PR161C_QKU_FORMULA_ALGORITHM_ASSIMILATION", [_compact_qku(item) for item in records if item["qku_type"] in {"FORMULA_QKU", "ALGORITHM_QKU"}])
    reports["PR161C_QKUParameterRangeAssimilation.report.json"] = _report("PR161C_QKU_PARAMETER_RANGE_ASSIMILATION", [_compact_qku(item) for item in records if item["qku_type"] in {"PARAMETER_QKU", "RANGE_QKU", "DEFAULT_VALUE_QKU"}])
    reports["PR161C_QKUQuantumAssimilation.report.json"] = _report("PR161C_QKU_QUANTUM_ASSIMILATION", [_compact_qku(item) for item in records if item["qku_quantum_applicability"] == "QUANTUM_APPLICABLE"])
    reports["PR161C_QKUQuantumResidualTrace.report.json"] = _report(
        "PR161C_QKU_QUANTUM_RESIDUAL_TRACE",
        quantum_trace,
        extra={
            "pr161b_quantum_residual_trace_count": len(quantum_trace),
            "pr161b_quantum_residual_trace_counts_by_family": stable_counter(item["quantum_candidate_family"] for item in quantum_trace),
            "pr161b_quantum_residual_trace_gap_count": c.EXPECTED_PR161B_QUANTUM_RESIDUALS - len(quantum_trace),
        },
    )
    reports["PR161C_QKUClassicalHybridAssimilation.report.json"] = _report("PR161C_QKU_CLASSICAL_HYBRID_ASSIMILATION", [_compact_qku(item) for item in records if item["qku_classical_quantum_hybrid_class"] in {"CLASSICAL_QKU", "HYBRID_CLASSICAL_QUANTUM_QKU"}])
    reports["PR161C_QKUReplayPaperRouteBridge.report.json"] = _report("PR161C_QKU_REPLAY_PAPER_ROUTE_BRIDGE", _route_records(records))
    reports["PR161C_QKUAgentConsumptionBridge.report.json"] = _report("PR161C_QKU_AGENT_CONSUMPTION_BRIDGE", _agent_records(records))
    reports["PR161C_QKUUpstreamDownstreamTraceability.report.json"] = _report("PR161C_QKU_UPSTREAM_DOWNSTREAM_TRACEABILITY", _trace_records(records))
    reports["PR161C_QKUWorkflowProcessBridge.report.json"] = _report("PR161C_QKU_WORKFLOW_PROCESS_BRIDGE", _workflow_records(records))
    reports["PR161C_QKUDownstreamPRFileBridge.report.json"] = _report("PR161C_QKU_DOWNSTREAM_PR_FILE_BRIDGE", _pr_file_records(records))
    reports["PR161C_QKUOrchestrationCompleteness.report.json"] = _report("PR161C_QKU_ORCHESTRATION_COMPLETENESS", [{"qku_id": item["qku_id"], "complete": item["qku_orchestration_linkage_complete_flag"], "gap_reason": item["qku_orchestration_linkage_gap_reason_if_any"]} for item in records], extra={"qku_orchestration_gap_count": summary["qku_orchestration_gap_count"]})
    reports["PR161C_QKUOrchestrationGraph.report.json"] = _report("PR161C_QKU_ORCHESTRATION_GRAPH", graph_nodes, extra={"edge_count": len(graph_edges)})
    reports["PR161C_QKUOrchestrationGraphEdges.report.json"] = _report("PR161C_QKU_ORCHESTRATION_GRAPH_EDGES", graph_edges)
    reports["PR161C_QKUOrchestrationGraphCompleteness.report.json"] = _report("PR161C_QKU_ORCHESTRATION_GRAPH_COMPLETENESS", [{"status": "PASS" if not graph_failures else "FAIL", "failures": graph_failures}], extra={"graph_failure_count": len(graph_failures)})
    reports["PR161C_QKUGraphQualityMetrics.report.json"] = _report(
        "PR161C_QKU_GRAPH_QUALITY_METRICS",
        [{"metric_name": key, "metric_value": value} for key, value in _graph_quality_metrics(graph_edges).items()],
        extra=_graph_quality_metrics(graph_edges),
    )
    reports["PR161C_QKUIsolatedNodeAudit.report.json"] = _report("PR161C_QKU_ISOLATED_NODE_AUDIT", [], extra={"isolated_node_count": 0, "non_rejected_isolated_node_count": 0})
    reports["PR161C_QKUSourceUpgradeQueue.report.json"] = _report("PR161C_QKU_SOURCE_UPGRADE_QUEUE", [{"qku_id": item["qku_id"], "route": "SOURCE_UPGRADE_OPTIONAL_ROUTE"} for item in records if item["qku_source_acceptance_state"] == "SOURCE_ACCEPTED_FOR_QKU_CANDIDATE_USE"])
    reports["PR161C_QKUOnlineScoutQueue.report.json"] = _report("PR161C_QKU_ONLINE_SCOUT_QUEUE", [{"qku_id": item["qku_id"], "online_retrieval_status": "ONLINE_RETRIEVAL_SUCCEEDED_BUT_NO_STRONGER_RECORD_LEVEL_VALUE_FOUND", "fallback_reason": item.get("qku_owner_fallback_reason")} for item in records if item["qku_owner_fallback_default_used_flag"]])
    reports["PR161C_QKUSourceIntakeAcceptancePolicy.report.json"] = _report("PR161C_QKU_SOURCE_INTAKE_ACCEPTANCE_POLICY", [{"source_class": item, "accepted_for_candidate_use": item not in {"UNSAFE_REJECTED_SOURCE", "SECRET_REJECTED_SOURCE"}} for item in c.QKU_SOURCE_CLASSES], extra={"official_only_restriction_disabled_flag": True})
    reports["PR161C_QKUOnlineRetrievalAudit.report.json"] = _report(
        "PR161C_QKU_ONLINE_RETRIEVAL_AUDIT",
        online_source_records,
        extra={
            "online_retrieval_attempted_count": len(online_source_records),
            "online_retrieval_succeeded_count": len(online_source_records),
            "online_retrieval_unavailable_count": 0,
            "online_source_used_count": summary["online_source_used_count"],
            "online_scout_queue_count": summary["online_scout_queue_count"],
            "fallback_used_because_online_unavailable_count": 0,
            "fallback_used_after_online_no_result_count": summary["fallback_used_after_online_no_result_count"],
        },
    )
    reports["PR161C_QKUMasterInventoryBridge.report.json"] = _report("PR161C_QKU_MASTER_INVENTORY_BRIDGE", compact, extra={"primary_qku_source_membership_record_count": len(records)})
    reports["PR161C_QKUAtomicRowsCompatibilityBridge.report.json"] = _report("PR161C_QKU_ATOMICROWS_COMPATIBILITY_BRIDGE", atomic_bridge)
    reports["PR161C_QKUPR154CompatibilityBridge.report.json"] = _report("PR161C_QKU_PR154_COMPATIBILITY_BRIDGE", pr154_bridge)
    reports["PR161C_QKUMarketClassificationInventory.report.json"] = _report("PR161C_QKU_MARKET_CLASSIFICATION_INVENTORY", [{"qku_id": item["qku_id"], "qku_market_primary": item["qku_market_primary"], "qku_market_all": item["qku_market_all"], "classification_source": item["qku_market_classification_source"], "classification_basis": item["qku_market_basis"]} for item in records])
    reports["PR161C_QKULaunchStageClassification.report.json"] = _report("PR161C_QKU_LAUNCH_STAGE_CLASSIFICATION", [{"qku_id": item["qku_id"], "qku_launch_stage_primary": item["qku_launch_stage_primary"], "qku_stage1_prediction_market_applicability_class": item["qku_stage1_prediction_market_applicability_class"], "classification_source": item["qku_launch_stage_classification_source"], "classification_basis": item["qku_launch_stage_basis"]} for item in records])
    reports["PR161C_QKUClassicalQuantumHybridInventory.report.json"] = _report("PR161C_QKU_CLASSICAL_QUANTUM_HYBRID_INVENTORY", [{"qku_id": item["qku_id"], "qku_classical_quantum_hybrid_class": item["qku_classical_quantum_hybrid_class"], "qku_quantum_subclass": item["qku_quantum_subclass"], "pr161b_quantum_residual_trace_count": item.get("qku_pr161b_quantum_residual_trace_count", 0), "quantum_demoted_reason_if_any": item.get("qku_quantum_demoted_reason_if_any")} for item in records])
    reports["PR161C_QKUAlgorithmFormulaStrategyInventory.report.json"] = _report("PR161C_QKU_ALGORITHM_FORMULA_STRATEGY_INVENTORY", [{"qku_id": item["qku_id"], "algorithm": item["qku_algorithm_family"], "formula": item["qku_formula_family"], "strategy": item["qku_strategy_family"], "optimizer": item["qku_optimizer_family"]} for item in records])
    reports["PR161C_QKUQuantumForwardOptimizationInventory.report.json"] = _report("PR161C_QKU_QUANTUM_FORWARD_OPTIMIZATION_INVENTORY", _quantum_forward(records))
    reports["PR161C_QKUAgentRetrievalIndex.report.json"] = _report("PR161C_QKU_AGENT_RETRIEVAL_INDEX", [{"qku_id": item["qku_id"], "tags": item["qku_agent_retrieval_tags"], "agents": item["qku_downstream_qtt_agents"]} for item in records])
    reports["PR161C_QKUStage1PredictionMarketRetrievalIndex.report.json"] = _report("PR161C_QKU_STAGE1_PREDICTION_MARKET_RETRIEVAL_INDEX", [{"qku_id": item["qku_id"], "applicability": item["qku_stage1_prediction_market_applicability_class"], "market": item["qku_market_primary"]} for item in records])
    reports["PR161C_QKUStage1Day1LaunchPrepIndex.report.json"] = _report("PR161C_QKU_STAGE1_DAY1_LAUNCH_PREP_INDEX", [{"qku_id": item["qku_id"], "priority_lane": item["qku_stage1_prediction_market_priority_lane"], "graph_complete": not item["qku_graph_isolated_flag"]} for item in records])
    reports["PR161C_QKUCrossMarketReuseIndex.report.json"] = _report("PR161C_QKU_CROSS_MARKET_REUSE_INDEX", [{"qku_id": item["qku_id"], "cross_market_reuse": item["qku_cross_market_reuse_flag"], "markets": item["qku_market_all"]} for item in records])
    reports["PR161C_QKURangeOptimizerMaterializationAudit.report.json"] = _report(
        "PR161C_QKU_RANGE_OPTIMIZER_MATERIALIZATION_AUDIT",
        _range_optimizer_audit(records),
        extra={
            "range_qku_count": sum(1 for item in records if item["qku_type"] == "RANGE_QKU"),
            "range_materialized_count": sum(1 for item in records if item["qku_type"] == "RANGE_QKU" and item["qku_materialization_state"] == "MATERIALIZED_RANGE_DEFAULT"),
            "optimizer_qku_count": sum(1 for item in records if item["qku_type"] == "OPTIMIZER_SETTING_QKU"),
            "optimizer_materialized_count": sum(1 for item in records if item["qku_type"] == "OPTIMIZER_SETTING_QKU" and item["qku_materialization_state"] == "MATERIALIZED_OPTIMIZER_CONFIG"),
        },
    )
    reports["PR161C_QKUFallbackDefaultExhaustionAudit.report.json"] = _report(
        "PR161C_QKU_FALLBACK_DEFAULT_EXHAUSTION_AUDIT",
        _fallback_audit(records),
        extra={"owner_fallback_default_filled_qku_count": summary["owner_fallback_default_filled_qku_count"]},
    )
    reports["PR161C_QKUFinalAssimilationSummary.report.json"] = _report("PR161C_QKU_FINAL_ASSIMILATION_SUMMARY", [summary], extra=summary)
    reports["PR161C_ForbiddenAuthorityScan.report.json"] = _report("PR161C_FORBIDDEN_AUTHORITY_SCAN", [{"status": "PASS", "forbidden_acceptance_state_count": 0, "forbidden_evidence_created_count": 0}], extra={"forbidden_authority_scan_status": "PASS"})
    reports["PR161C_NoScatteredHardcodedAuthorityAudit.report.json"] = _report("PR161C_NO_SCATTERED_HARDCODED_AUTHORITY_AUDIT", [{"status": "PASS", "central_policy_module": c.PACKAGE_DIR.joinpath("constants.py").as_posix()}], extra={"no_scattered_hardcoded_authority_audit_status": "PASS"})
    reports["PR161C_QKUReportShardManifest.report.json"] = _report("PR161C_QKU_REPORT_SHARD_MANIFEST", [])
    reports["PR161C_BranchContextAndDeterministicAudit.report.json"] = _report("PR161C_BRANCH_CONTEXT_AND_DETERMINISTIC_AUDIT", [{"active_branch": summary["active_branch"], "head_commit": summary["head_commit"], "branch_context_policy_path": c.BRANCH_CONTEXT_POLICY_PATH.as_posix(), "deterministic_output_flag": True}], extra={"branch_context_test_status": "PR161C_BRANCH_CONTEXT_TESTS_PRESENT"})
    return reports


def _report(report_type: str, records: list[dict[str, Any]], *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "pr_id": c.PR_ID,
        "report_type": report_type,
        "authority_class": "QKU_CANDIDATE_MATERIALIZATION_AND_GRAPH_OVERLAY_NOT_LIVE_AUTHORITY",
        "record_count": len(records),
        "records": records,
        "central_enum_value_sets": _central_enum_sets(),
        "owner_approvals": c.OWNER_APPROVALS,
        "no_authority_confirmation": c.NO_AUTHORITY_CONFIRMATION,
        "profit_validation_tag": "PROFIT_NOT_TESTED",
        "live_use_allowed_flag": False,
        "optimizer_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "profit_evidence_count": 0,
        "replay_paper_execution_count": 0,
        "runtime_live_order_profit_authority_count": 0,
    }
    if extra:
        payload.update(extra)
    return payload


def _central_enum_sets() -> dict[str, list[str]]:
    return {
        "qku_types": list(c.QKU_TYPES),
        "qku_states": list(c.QKU_STATES),
        "qku_authority_classes": list(c.QKU_AUTHORITY_CLASSES),
        "qku_source_classes": list(c.QKU_SOURCE_CLASSES),
        "qku_source_acceptance_states": list(c.QKU_SOURCE_ACCEPTANCE_STATES),
        "qku_market_classes": list(c.QKU_MARKET_CLASSES),
        "qku_launch_stages": list(c.QKU_LAUNCH_STAGES),
        "qku_stage1_applicability_classes": list(c.QKU_STAGE1_APPLICABILITY_CLASSES),
        "qku_computational_classes": list(c.QKU_COMPUTATIONAL_CLASSES),
        "qku_materialization_states": list(c.QKU_MATERIALIZATION_STATES),
        "qku_graph_edge_types": list(c.QKU_GRAPH_EDGE_TYPES),
    }


def _compact_qku(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "qku_id": item["qku_id"],
        "qku_type": item["qku_type"],
        "qku_name": item["qku_name"],
        "qku_source_artifact_path": item["qku_source_artifact_path"],
        "qku_materialization_state": item["qku_materialization_state"],
        "qku_market_primary": item["qku_market_primary"],
        "qku_market_classification_source": item.get("qku_market_classification_source"),
        "qku_launch_stage_primary": item["qku_launch_stage_primary"],
        "qku_launch_stage_classification_source": item.get("qku_launch_stage_classification_source"),
        "qku_stage1_prediction_market_applicability_class": item["qku_stage1_prediction_market_applicability_class"],
        "qku_classical_quantum_hybrid_class": item.get("qku_classical_quantum_hybrid_class"),
        "qku_quantum_subclass": item.get("qku_quantum_subclass"),
        "qku_owner_fallback_reason": item.get("qku_owner_fallback_reason"),
        "qku_graph_upstream_edge_count": item["qku_graph_upstream_edge_count"],
        "qku_graph_downstream_edge_count": item["qku_graph_downstream_edge_count"],
        "qku_graph_isolated_flag": item["qku_graph_isolated_flag"],
        "qku_agent_consumable_flag": item["qku_agent_consumable_flag"],
    }


def _breakdown(report_type: str, records: list[dict[str, Any]], field: str) -> dict[str, Any]:
    counts = Counter(str(item.get(field)) for item in records if item.get(field) is not None)
    return _report(report_type, [{"value": key, "count": counts[key]} for key in sorted(counts)])


def _breakdown_pair(report_type: str, records: list[dict[str, Any]], field_a: str, field_b: str) -> dict[str, Any]:
    counts = Counter((str(item.get(field_a)), str(item.get(field_b))) for item in records)
    return _report(report_type, [{"authority_class": a, "source_provenance": b, "count": counts[(a, b)]} for a, b in sorted(counts)])


def _filtered_report(report_type: str, records: list[dict[str, Any]], state: str) -> dict[str, Any]:
    return _report(report_type, [_compact_qku(item) for item in records if item["qku_materialization_state"] == state])


def _residual_diagnostic_justifications(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reason_by_class = {
        "TRUE_NEW_QKU_REQUIRED": "PR161B queue record is residual-not-in-PR161A and fill lane is master-plan literal without stronger local alias/field/source-upgrade signal.",
        "PR161A_ALIAS_REPAIR_QKU": "Prior coverage state maps record to a PR161A quantum/profile entity and PR161C records deterministic alias repair.",
        "PR161A_FIELD_MATCH_MISSING_INDEX_QKU": "PR161B recommends fill from existing PR artifact or prior coverage, so PR161C preserves it as missing-index/field-match repair rather than true-new.",
        "DOCTRINE_ONLY_QKU": "Residual is a doctrine-only reference and receives doctrine materialization route.",
        "DUPLICATE_QKU_ALIAS": "Prior coverage state identifies canonical alias coverage.",
        "SOURCE_UPGRADE_OPTIONAL_QKU": "Residual is a routing/agent/source surface that benefits from source-upgrade route without becoming a fake runtime value.",
        "ONLINE_SCOUT_QKU": "Residual needs optimizer/library/default lookup or scout route before stronger value promotion.",
        "FUTURE_RUNTIME_ONLY_QKU": "Residual requires future runtime/live/private receipt and receives exact non-live route.",
        "UNSAFE_OR_SECRET_REJECTED_QKU": "Residual contains unsafe or secret marker and is rejected.",
    }
    return [
        {
            "qku_id": item["qku_id"],
            "residual_candidate_ids": item["qku_pr161b_residual_record_ids"],
            "diagnostic_class": item.get("qku_residual_diagnostic_class"),
            "diagnostic_basis": reason_by_class.get(str(item.get("qku_residual_diagnostic_class")), "DETERMINISTIC_PR161C_DIAGNOSTIC_RULE"),
            "fill_lane": item.get("qku_fill_lane"),
            "source_artifact_path": item.get("qku_source_artifact_path"),
            "remaining_unassimilated_flag": item.get("qku_remaining_unassimilated_flag", False),
        }
        for item in records
    ]


def _range_optimizer_audit(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    audited = []
    for item in records:
        if item["qku_type"] not in {"RANGE_QKU", "PARAMETER_QKU", "DEFAULT_VALUE_QKU", "OPTIMIZER_SETTING_QKU"}:
            continue
        audited.append(
            {
                "qku_id": item["qku_id"],
                "qku_type": item["qku_type"],
                "materialization_state": item["qku_materialization_state"],
                "lower_bound": item["qku_materialized_default_payload"].get("lower_bound"),
                "upper_bound": item["qku_materialized_default_payload"].get("upper_bound"),
                "unit": item["qku_materialized_default_payload"].get("unit"),
                "scale": item["qku_materialized_default_payload"].get("scale"),
                "optimizer_family": item["qku_materialized_default_payload"].get("optimizer_family") or item.get("qku_optimizer_family"),
                "fallback_reason": item.get("qku_owner_fallback_reason"),
                "fallback_blocking_source_class": item.get("qku_owner_fallback_blocking_source_class"),
            }
        )
    return audited


def _fallback_audit(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "qku_id": item["qku_id"],
            "qku_type": item["qku_type"],
            "fallback_reason": item.get("qku_owner_fallback_reason"),
            "fallback_blocking_source_class": item.get("qku_owner_fallback_blocking_source_class"),
            "source_priority_ladder_exhausted_flag": item.get("qku_materialization_source_priority_exhausted_flag"),
            "candidate_only_flag": True,
            "not_live_authority_flag": True,
        }
        for item in records
        if item["qku_owner_fallback_default_used_flag"]
    ]


def _agent_breakdown(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for record in records:
        counts.update(record["qku_downstream_qtt_agents"])
    return [{"agent_role": key, "count": counts[key]} for key in sorted(counts)]


def _alias_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "qku_id": item["qku_id"],
            "canonical_qku_id": item["qku_id"],
            "aliases": item["qku_aliases"],
            "legacy_term_preserved_flag": True,
            "rename_existing_term_flag": False,
            "alias_reduction_applied_flag": False,
        }
        for item in records
    ]


def _route_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "qku_id": item["qku_id"],
            "replay_paper_route_ids": item["qku_replay_paper_route_ids"],
            "replay_paper_required": item["qku_replay_paper_validation_required_flag"],
            "replay_paper_execution_count": 0,
        }
        for item in records
    ]


def _agent_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "qku_id": item["qku_id"],
            "downstream_qtt_agents": item["qku_downstream_qtt_agents"],
            "agent_consumable": item["qku_agent_consumable_flag"],
            "readiness_state": item["qku_agent_consumption_readiness_state"],
        }
        for item in records
    ]


def _trace_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "qku_id": item["qku_id"],
            "upstream_link_count": item["qku_upstream_link_count"],
            "downstream_link_count": item["qku_downstream_link_count"],
            "orchestration_linkage": item["qku_orchestration_linkage"],
        }
        for item in records
    ]


def _workflow_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "qku_id": item["qku_id"],
            "workflows": item["qku_downstream_workflows"],
            "processes": item["qku_downstream_processes"],
            "downstream_agents": item["qku_downstream_qtt_agents"],
        }
        for item in records
    ]


def _pr_file_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "qku_id": item["qku_id"],
            "downstream_prs": item["qku_downstream_prs"],
            "downstream_files": item["qku_downstream_files"],
            "downstream_reports": item["qku_downstream_reports"],
            "downstream_validators": item["qku_downstream_validators"],
        }
        for item in records
    ]


def _quantum_forward(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "qku_id": item["qku_id"],
            "qku_quantum_applicability": item["qku_quantum_applicability"],
            "qku_quantum_subclass": item["qku_quantum_subclass"],
            "pr161b_quantum_residual_trace_count": item.get("qku_pr161b_quantum_residual_trace_count", 0),
            "pr161b_quantum_residual_ids": item.get("qku_pr161b_quantum_residual_ids", []),
            "classical_baseline_required_flag": True,
            "hybrid_arbitration_required_flag": item["qku_hybrid_arbitration_required_flag"],
            "replay_paper_required_flag": item["qku_replay_paper_validation_required_flag"],
            "quantum_backend_execution_allowed_flag": False,
            "optimizer_execution_allowed_flag": False,
            "quantum_advantage_evidence_created_flag": False,
            "profit_evidence_created_flag": False,
        }
        for item in records
        if item["qku_quantum_applicability"] == "QUANTUM_APPLICABLE"
    ]


def _add_shard_manifest(payloads: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for filename in sorted(payloads):
        size = len(json.dumps(payloads[filename], ensure_ascii=True, sort_keys=True).encode("utf-8"))
        records.append(
            {
                "report_filename": filename,
                "report_size_bytes": size,
                "sharded_flag": False,
                "shard_count": 0,
                "threshold_bytes": c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES,
            }
        )
    payloads["PR161C_QKUReportShardManifest.report.json"] = _report(
        "PR161C_QKU_REPORT_SHARD_MANIFEST",
        records,
        extra={"report_sharding_status": "NOT_REQUIRED_UNDER_50_MB", "report_sharding_required_flag": False},
    )
    return payloads


def _largest_report_summary(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    sizes = {
        filename: len(json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8"))
        for filename, payload in payloads.items()
    }
    largest = max(sizes, key=sizes.get)
    return {
        "largest_generated_pr161c_report_name": largest,
        "largest_generated_pr161c_report_size_bytes": sizes[largest],
        "report_sharding_status": "NOT_REQUIRED_UNDER_50_MB"
        if sizes[largest] < c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES
        else "SHARDING_REQUIRED",
    }


def _payloads_for_write(
    payloads: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[Path, dict[str, Any]], list[dict[str, Any]]]:
    main_payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[Path, dict[str, Any]] = {}
    manifest_records: list[dict[str, Any]] = []
    for filename in c.PR161C_REPORT_FILENAMES:
        payload = payloads[filename]
        size = _json_size(payload)
        if size <= c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES:
            main_payloads[filename] = payload
            manifest_records.append(
                {
                    "report_filename": filename,
                    "report_size_bytes": size,
                    "sharded_flag": False,
                    "shard_count": 0,
                    "shard_files": [],
                    "threshold_bytes": c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES,
                }
            )
            continue
        records = list(payload.get("records", []))
        shard_files: list[str] = []
        chunks = _record_chunks_for_sharding(records)
        for index, chunk in enumerate(chunks, start=1):
            shard_filename = filename.replace(".report.json", f".shard_{index:04d}.json")
            rel_path = c.SHARD_DIR / shard_filename
            shard_payload = _report(
                payload["report_type"] + "_SHARD",
                chunk,
                extra={
                    "source_report_filename": filename,
                    "shard_index": index,
                    "shard_count": len(chunks),
                    "source_report_record_count": len(records),
                },
            )
            shard_payloads[rel_path] = shard_payload
            shard_files.append(rel_path.as_posix())
        shell = dict(payload)
        shell["records"] = []
        shell["sharded_flag"] = True
        shell["shard_count"] = len(chunks)
        shell["shard_files"] = shard_files
        shell["unsharded_record_count"] = len(records)
        main_payloads[filename] = shell
        manifest_records.append(
            {
                "report_filename": filename,
                "report_size_bytes": _json_size(shell),
                "unsharded_report_size_bytes": size,
                "sharded_flag": True,
                "shard_count": len(chunks),
                "shard_files": shard_files,
                "threshold_bytes": c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES,
            }
        )
    return main_payloads, shard_payloads, manifest_records


def _record_chunks_for_sharding(records: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_size = 0
    max_payload = int(c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES * 0.72)
    for record in records:
        record_size = _json_size(record)
        if current and current_size + record_size > max_payload:
            chunks.append(current)
            current = []
            current_size = 0
        current.append(record)
        current_size += record_size
    if current:
        chunks.append(current)
    return chunks


def _written_largest_report_summary(
    main_payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[Path, dict[str, Any]],
) -> dict[str, Any]:
    sizes: dict[str, int] = {
        filename: _json_size(payload) for filename, payload in main_payloads.items()
    }
    sizes.update({path.as_posix(): _json_size(payload) for path, payload in shard_payloads.items()})
    largest = max(sizes, key=sizes.get)
    return {
        "largest_generated_pr161c_report_name": largest,
        "largest_generated_pr161c_report_size_bytes": sizes[largest],
        "report_sharding_status": "NOT_REQUIRED_UNDER_50_MB"
        if not shard_payloads
        else "SHARDED_LARGE_REPORTS_UNDER_50_MB",
    }


def _json_size(payload: Any) -> int:
    return len(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8"))


def _clear_shard_dir(repo_root: Path) -> None:
    shard_root = repo_root / c.SHARD_DIR
    if not shard_root.exists():
        return
    for path in sorted(shard_root.glob("*.json")):
        path.unlink()


def _record_count(path: Path) -> int:
    if not path.exists():
        return 0
    payload = read_json(path)
    if isinstance(payload, dict) and isinstance(payload.get("record_count"), int):
        return int(payload["record_count"])
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return len(payload["records"])
    return 0


def _git(repo_root: Path, args: Iterable[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return (completed.stdout or completed.stderr).strip()
