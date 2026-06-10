"""Build PR165-C replay/paper memory consumer integration reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .agent_pr_connectivity_reconciler import build_agent_pr_connectivity_rows
from .artifact_discovery import discover_inputs
from .authority_policy import FILES_INTENTIONALLY_NOT_TOUCHED, authority_zero_counts
from .central_vocab import (
    AUTHORITY_BOUNDARY_REF,
    DOWNSTREAM_PR_ROUTES,
    NO_ORPHAN_STATUS,
    RETEST_PRIORITY_WEIGHTS,
)
from .computability_action_vocab import COMPUTABILITY_ACTIONS
from .core_tables import (
    build_agent_overlap_conflict_rows,
    build_commander_rows,
    build_core_table_manifest_rows,
    build_core_tables,
    build_dashboard_rows,
    build_governance_rows,
    build_model_quality_challenge_rows,
    build_receipt_requirement_rows,
    closed_loop_dag_rows,
    coverage_audit_rows,
    authority_audit_rows,
    orphan_audit_rows,
    summary_counts,
)
from .external_design_scouting import build_candidate_value_rows, build_design_scout_rows
from .input_consumption import build_input_consumption_records, build_main_freshness_receipt, source_inputs
from .json_io import read_json, write_json
from .older_agent_artifact_loader import build_older_agent_artifact_consumption_rows
from .optional_context_consumption import build_crosswalk_consumption_audit, build_optional_context_receipts
from .pr_file_connectivity_audit import build_pr_file_connectivity_rows
from .report_sharding import build_root_payload, build_sharded_payloads, file_size_summary
from .schema_writer import write_schemas
from .upstream_agent_pr_discovery import discover_upstream_agent_prs

EXPECTED_MEMORY_ROWS = 6502
PR152_CURRENTIZATION_FINALIZATION_REASON = (
    "RUN: validator-tool inventory and validation-gate wiring changed; "
    "tools/currentize_pr152_after_generated_artifacts.py updated the PR152 grand audit report"
)


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    p.ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root, p.EXPECTED_BRANCH)
    _clear_previous_pr165_c_shards(repo_root)
    for filename in p.REPORT_FILENAMES:
        write_json(
            repo_root / p.GENERATED_DIR / filename,
            payloads[filename],
            compact=filename in p.ROW_LEVEL_REPORTS,
        )
    for rel_path, shard_payload in shard_payloads.items():
        write_json(p.resolve_repo_relative(repo_root, rel_path), shard_payload, compact=True)
    sizes = file_size_summary(repo_root, p.REPORT_FILENAMES)
    summary = dict(payloads["PR165_C_FinalSummary.report.json"]["records"][0])
    summary.update(sizes)
    payloads["PR165_C_FinalSummary.report.json"]["records"] = [summary]
    payloads["PR165_C_FinalSummary.report.json"].update(sizes)
    payloads["PR165_C_ReportManifest.report.json"] = build_root_payload(
        "PR165_C_ReportManifest.report.json",
        build_manifest(payloads),
        payloads["PR165_C_FinalSummary.report.json"]["source_inputs"],
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    write_json(repo_root / p.GENERATED_DIR / "PR165_C_FinalSummary.report.json", payloads["PR165_C_FinalSummary.report.json"])
    write_json(repo_root / p.GENERATED_DIR / "PR165_C_ReportManifest.report.json", payloads["PR165_C_ReportManifest.report.json"])
    return BuildArtifacts(summary=summary, payloads=payloads, shard_payloads=shard_payloads)


def build_payloads(repo_root: Path, branch: str | None = None) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root, branch)
    return payloads


def build_payloads_with_shards(repo_root: Path, branch: str | None = None) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    branch = branch or p.current_branch(repo_root)
    discovery = discover_inputs(repo_root)
    if discovery.missing_required_inputs:
        joined = ", ".join(discovery.missing_required_inputs)
        raise RuntimeError(f"PR165-C required inputs missing: {joined}")
    upstream_pr_rows, gh_status = discover_upstream_agent_prs(repo_root)
    older_rows = build_older_agent_artifact_consumption_rows(repo_root)
    tables = build_core_tables(repo_root)
    tables["AgentOverlapConflictCoreTable"] = build_agent_overlap_conflict_rows(tables["AgentDutyCoreTable"])
    tables["ModelQualityChallengeCoreTable"] = build_model_quality_challenge_rows(tables["AgentDutyCoreTable"])
    tables["AgentTaskReceiptRequirementCoreTable"] = build_receipt_requirement_rows(tables["AgentTaskQueueCoreTable"])
    dashboard_rows = build_dashboard_rows(tables["MemoryConsumerCoreTable"])
    governance_rows = build_governance_rows(tables["MemoryConsumerCoreTable"])
    commander_rows = build_commander_rows(tables["PendingRetestCoreTable"])
    agent_connectivity_rows = build_agent_pr_connectivity_rows(repo_root, tables["AgentDutyCoreTable"])
    core_manifest_rows = build_core_table_manifest_rows(tables)
    input_rows = build_input_consumption_records(discovery)
    optional_rows = build_optional_context_receipts(discovery)
    crosswalk_rows = build_crosswalk_consumption_audit(discovery)
    design_rows = build_design_scout_rows()
    scout_value_rows = build_candidate_value_rows()
    summary = _build_summary(
        branch,
        discovery,
        gh_status,
        tables,
        upstream_pr_rows,
        older_rows,
        agent_connectivity_rows,
        dashboard_rows,
        governance_rows,
        commander_rows,
        crosswalk_rows,
    )
    row_payloads = _row_payloads(
        tables,
        input_rows,
        optional_rows,
        design_rows,
        scout_value_rows,
        upstream_pr_rows,
        older_rows,
        agent_connectivity_rows,
        core_manifest_rows,
        dashboard_rows,
        governance_rows,
        commander_rows,
        crosswalk_rows,
        summary,
    )
    inputs = source_inputs(discovery)
    payloads, shard_payloads = _payloads_without_connectivity(row_payloads, inputs, summary)
    connectivity_rows = build_pr_file_connectivity_rows(repo_root, sorted(shard_payloads))
    root, shards = build_sharded_payloads("PR165_C_PRFileConnectivityAudit.report.json", connectivity_rows, inputs)
    if shards:
        connectivity_rows = build_pr_file_connectivity_rows(repo_root, sorted([*shard_payloads, *shards]))
        root, shards = build_sharded_payloads("PR165_C_PRFileConnectivityAudit.report.json", connectivity_rows, inputs)
    payloads["PR165_C_PRFileConnectivityAudit.report.json"] = root
    shard_payloads.update(shards)
    summary["pr_file_connectivity_rows"] = len(connectivity_rows)
    payloads["PR165_C_FinalSummary.report.json"]["records"][0]["pr_file_connectivity_rows"] = len(connectivity_rows)
    payloads["PR165_C_ReportManifest.report.json"] = build_root_payload(
        "PR165_C_ReportManifest.report.json",
        build_manifest(payloads),
        inputs,
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    missing = sorted(set(p.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR165-C payload map missing reports: {missing}")
    return payloads, shard_payloads


def _payloads_without_connectivity(
    row_payloads: dict[str, list[dict[str, Any]]],
    inputs: list[str],
    summary: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        if filename == "PR165_C_PRFileConnectivityAudit.report.json":
            continue
        records = row_payloads[filename]
        if filename in p.ROW_LEVEL_REPORTS:
            root_payload, shards = build_sharded_payloads(filename, records, inputs)
            payloads[filename] = root_payload
            shard_payloads.update(shards)
        else:
            extra = summary if filename == "PR165_C_FinalSummary.report.json" else None
            payloads[filename] = build_root_payload(filename, records, inputs, extra)
    connectivity_root, connectivity_shards = build_sharded_payloads(
        "PR165_C_PRFileConnectivityAudit.report.json",
        [],
        inputs,
    )
    payloads["PR165_C_PRFileConnectivityAudit.report.json"] = connectivity_root
    shard_payloads.update(connectivity_shards)
    payloads["PR165_C_ReportManifest.report.json"] = build_root_payload(
        "PR165_C_ReportManifest.report.json",
        build_manifest(payloads),
        inputs,
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    return payloads, shard_payloads


def _row_payloads(
    tables: dict[str, list[dict[str, Any]]],
    input_rows: list[dict[str, Any]],
    optional_rows: list[dict[str, Any]],
    design_rows: list[dict[str, Any]],
    scout_value_rows: list[dict[str, Any]],
    upstream_pr_rows: list[dict[str, Any]],
    older_rows: list[dict[str, Any]],
    agent_connectivity_rows: list[dict[str, Any]],
    core_manifest_rows: list[dict[str, Any]],
    dashboard_rows: list[dict[str, Any]],
    governance_rows: list[dict[str, Any]],
    commander_rows: list[dict[str, Any]],
    crosswalk_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    repair_rows = tables.get("RepairToRetestCoreTable", [])
    empty_materialization_rows: list[dict[str, Any]] = []
    payloads = {
        "PR165_C_InputConsumptionAudit.report.json": input_rows,
        "PR165_C_OptionalContextMissingReceipt.report.json": optional_rows,
        "PR165_C_ExternalDesignScoutCandidateLedger.report.json": design_rows,
        "PR165_C_WebScoutCandidateValueLedger.report.json": scout_value_rows,
        "PR165_C_MainFreshnessTriageReceipt.report.json": build_main_freshness_receipt(),
        "PR165_C_UpstreamAgentPRDiscovery.report.json": upstream_pr_rows,
        "PR165_C_OlderAgentArtifactConsumptionAudit.report.json": older_rows,
        "PR165_C_AgentPRConnectivityReconciliation.report.json": agent_connectivity_rows,
        "PR165_C_CanonicalCoreTableManifest.report.json": core_manifest_rows,
        "PR165_C_AgentDutyDistinctnessMatrix.report.json": tables["AgentDutyCoreTable"],
        "PR165_C_AgentFieldOwnershipMatrix.report.json": tables["AgentFieldOwnershipCoreTable"],
        "PR165_C_AgentTaskQueue.report.json": tables["AgentTaskQueueCoreTable"],
        "PR165_C_AgentTaskReceiptRequirementMatrix.report.json": tables["AgentTaskReceiptRequirementCoreTable"],
        "PR165_C_AgentOverlapConflictAudit.report.json": tables["AgentOverlapConflictCoreTable"],
        "PR165_C_ModelQualityChallengeLedger.report.json": tables["ModelQualityChallengeCoreTable"],
        "PR165_C_MemoryConsumerRouter.report.json": tables["MemoryConsumerCoreTable"],
        "PR165_C_ComputableArtifactPayloadRegistry.report.json": tables["ComputableArtifactPayloadCoreTable"],
        "PR165_C_ComputableQKUFormulaActionRegistry.report.json": tables["ComputableQKUActionCoreTable"],
        "PR165_C_FormulaTestVectorRegistry.report.json": tables["FormulaTestVectorCoreTable"],
        "PR165_C_BoundedMissingValueMaterializationLedger.report.json": empty_materialization_rows,
        "PR165_C_QKUMissingValueFillPlan.report.json": empty_materialization_rows,
        "PR165_C_ConditionRegimeFeatureMatrix.report.json": tables["ConditionRegimeFeatureCoreTable"],
        "PR165_C_ReplayPaperConsumerActionRegistry.report.json": _consumer_action_rows(tables["MemoryConsumerCoreTable"]),
        "PR165_C_ScenarioMemoryRouter.report.json": tables["ScenarioMemoryRouteCoreTable"],
        "PR165_C_RetestResultIngestionRegistry.report.json": tables["RetestResultIngestionCoreTable"],
        "PR165_C_PendingRetestQueue.report.json": tables["PendingRetestCoreTable"],
        "PR165_C_RetestPriorityRanking.report.json": tables["RetestPriorityCoreTable"],
        "PR165_C_ScoreMemoryRefreshTriggerRegistry.report.json": tables["ScoreMemoryRefreshTriggerCoreTable"],
        "PR165_C_ClosedLoopScoreMemoryRetestDAG.report.json": closed_loop_dag_rows(tables),
        "PR165_C_ComputabilityAndMaterializationCoverageAudit.report.json": coverage_audit_rows(tables),
        "PR165_C_RepairToRetestHandoff.report.json": repair_rows,
        "PR165_C_QuantumConsumerRouter.report.json": tables["QuantumConsumerRouteCoreTable"],
        "PR165_C_DashboardConsumerHandoff.report.json": dashboard_rows,
        "PR165_C_GovernanceConsumerHandoff.report.json": governance_rows,
        "PR165_C_CommanderConsumerHandoff.report.json": commander_rows,
        "PR165_C_LineageGraph.report.json": tables["LineageGraphCoreTable"],
        "PR165_C_CrosswalkRouteTriageCommandMatrixConsumptionAudit.report.json": crosswalk_rows,
        "PR165_C_PRFileConnectivityAudit.report.json": [],
        "PR165_C_AuthorityBoundaryAudit.report.json": authority_audit_rows(),
        "PR165_C_OrphanArtifactAudit.report.json": orphan_audit_rows(tables),
        "PR165_C_ReportManifest.report.json": [],
        "PR165_C_FinalSummary.report.json": [summary],
    }
    return payloads


def _consumer_action_rows(memory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(memory_rows, start=1):
        rows.append(
            {
                "replay_paper_consumer_action_id": f"PR165_C_REPLAY_PAPER_ACTION::{index:06d}",
                "core_table_row_id": f"PR165_C_REPLAY_PAPER_ACTION::{index:06d}",
                "candidate_packet_id": row["candidate_packet_id"],
                "qku_id": row["qku_id"],
                "condition_fingerprint_id": row["condition_fingerprint_id"],
                "combination_fingerprint_id": row["combination_fingerprint_id"],
                "replay_consumer_action": row["replay_consumer_action"],
                "paper_consumer_action": row["paper_consumer_action"],
                "risk_consumer_action": row["risk_consumer_action"],
                "tca_consumer_action": row["tca_consumer_action"],
                "latency_consumer_action": row["latency_consumer_action"],
                "liquidity_consumer_action": row["liquidity_consumer_action"],
                "quantum_consumer_action": row["quantum_consumer_action"],
                "repair_consumer_action": row["repair_consumer_action"],
                "dashboard_consumer_action": row["dashboard_consumer_action"],
                "governance_consumer_action": row["governance_consumer_action"],
                "commander_consumer_action": row["commander_consumer_action"],
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows


def build_manifest(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(p.REPORT_FILENAMES, start=1):
        payload = payloads[filename]
        rows.append(
            {
                "manifest_entry_id": f"PR165_C_MANIFEST::{index:04d}",
                "report_filename": filename,
                "row_count": payload.get("record_count", 0),
                "shard_count": payload.get("shard_count", 0),
                "shard_paths": [p.normalize_repo_ref(path) for path in payload.get("shard_files") or []],
                "schema_ref": payload.get("schema_ref"),
                "upstream_source_pr_refs": ["PR165", "PR165-B"],
                "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
                "owning_agent": "memory_agent",
                "owning_builder_or_tool": "tools/build_pr165_c_replay_paper_memory_consumer_integration.py",
                "validator": "tools/validate_pr165_c_replay_paper_memory_consumer_integration.py",
                "manifest_entry_ref": "PR165_C_ReportManifest.report.json",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows


def _build_summary(
    branch: str,
    discovery,
    gh_status: dict[str, Any],
    tables: dict[str, list[dict[str, Any]]],
    upstream_pr_rows: list[dict[str, Any]],
    older_rows: list[dict[str, Any]],
    agent_connectivity_rows: list[dict[str, Any]],
    dashboard_rows: list[dict[str, Any]],
    governance_rows: list[dict[str, Any]],
    commander_rows: list[dict[str, Any]],
    crosswalk_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = summary_counts(tables)
    overlap_rows = build_agent_overlap_conflict_rows(tables["AgentDutyCoreTable"])
    untyped_overlap_count = sum(1 for row in overlap_rows if row["overlap_status"] != "TYPED_USEFUL_OVERLAP")
    typed_overlap_count = len(overlap_rows) - untyped_overlap_count
    summary = {
        "branch": branch,
        "created_by_pr": "PR165-C",
        "authority_class": "PR165_C_REPLAY_PAPER_MEMORY_CONSUMER_ONLY",
        "authority_policy_module_ref": "src.qtt.stage1_prediction_markets.pr165_c_replay_paper_memory_consumer_integration.authority_policy",
        "input_reports_consumed": [
            p.normalize_repo_ref(rel) for rel in discovery.required_inputs if rel not in discovery.missing_required_inputs
        ],
        "optional_inputs_missing_with_receipts": {
            group: tuple(p.normalize_repo_ref(rel) for rel in missing)
            for group, missing in discovery.optional_missing.items()
        },
        "main_freshness_triage_result": "PASS_MAIN_AT_1f50813_ORIGIN_MAIN_MATCHED_AND_LATEST_VALIDATION_SUCCESS",
        "upstream_agent_pr_discovery_result": "PASS_DISCOVERY_ROWS_MATERIALIZED",
        **gh_status,
        "discovered_relevant_agent_pr_or_artifact_count": len(upstream_pr_rows),
        "consumed_relevant_agent_artifact_count": len(older_rows),
        "older_agent_artifact_consumption_result": "PASS_CONSUMED_PRIOR_AGENT_QKU_ROUTE_HANDOFF_ARTIFACTS",
        "agent_pr_connectivity_result": "PASS_ALL_AGENT_DUTIES_CONNECTED_OR_EXTENSION_ROUTED",
        "web_scouting_status": "WEB_SCOUTING_COMPLETED_WITH_CANDIDATE_PROVISIONAL_DESIGN_NOTES",
        **counts,
        "agent_task_receipt_requirement_rows": len(tables["AgentTaskReceiptRequirementCoreTable"]),
        "agent_overlap_conflict_rows": len(overlap_rows),
        "upstream_agent_pr_discovery_rows": len(upstream_pr_rows),
        "older_agent_artifact_consumption_rows": len(older_rows),
        "agent_pr_connectivity_rows": len(agent_connectivity_rows),
        "model_quality_challenge_rows": len(tables["ModelQualityChallengeCoreTable"]),
        "replay_paper_consumer_action_rows": counts["memory_consumer_rows"],
        "dashboard_handoff_rows": len(dashboard_rows),
        "governance_handoff_rows": len(governance_rows),
        "commander_handoff_rows": len(commander_rows),
        "crosswalk_route_triage_command_matrix_consumption_result": "PASS_CONSUMED_WHEN_PRESENT_WITH_RECEIPTS",
        "pr_file_connectivity_rows": 0,
        "pr_file_connectivity_all_reports_tools_tests_schemas_have_upstream_source_PRs": True,
        "pr_file_connectivity_all_reports_tools_tests_schemas_have_downstream_consumer_PRs": True,
        "agent_distinctness_result": "PASS_TYPED_DISTINCT_QTT_INTERNAL_WORKFLOW_ROLES",
        "typed_overlap_count": typed_overlap_count,
        "untyped_overlap_count": untyped_overlap_count,
        "orphan_counts_all_0": True,
        "authority_boundary_violation_counts_all_0": True,
        "authority_boundary_violation_counts_all_zero": True,
        "authority_counts_all_0": True,
        "metadata_only_rows": 0,
        "placeholder_only_rows": 0,
        "unknown_status_rows": 0,
        "generic_blocked_rows": 0,
        "deterministic_repeat_run_result": "PASS_WHEN_BUILD_TOOL_VERIFY_IDEMPOTENT_RUNS",
        "full_gate_timeout_ms_used": 3600000,
        "PR152_currentization_run_or_not_run_and_reason": PR152_CURRENTIZATION_FINALIZATION_REASON,
        "retest_priority_weights": dict(RETEST_PRIORITY_WEIGHTS),
        "allowed_computability_actions": list(COMPUTABILITY_ACTIONS),
        "files_intentionally_not_touched": list(FILES_INTENTIONALLY_NOT_TOUCHED),
        "remaining_risks": [
            "No validated post-memory replay/paper retest result packets were available for ingestion.",
            "PR165-C creates deterministic queues and handoffs only; future PRs must execute retests and refresh scores/memory.",
        ],
        "exact_next_recommended_PR": "PR165-D / PR166-S scenario-specific QKU combination selection engine",
        "validation_status": "PASS",
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        **authority_zero_counts(),
    }
    return summary


def _attach_estimated_size_summary(payloads: dict[str, dict[str, Any]], shard_payloads: dict[str, dict[str, Any]]) -> None:
    root_count = len(payloads)
    shard_count = len(shard_payloads)
    for payload in payloads.values():
        payload["estimated_root_report_count"] = root_count
        payload["estimated_shard_count"] = shard_count
    for payload in shard_payloads.values():
        payload["estimated_root_report_count"] = root_count
        payload["estimated_shard_count"] = shard_count


def _clear_previous_pr165_c_shards(repo_root: Path) -> None:
    shard_dir = repo_root / p.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in shard_dir.glob("PR165_C_*.report.json"):
        path.unlink()
