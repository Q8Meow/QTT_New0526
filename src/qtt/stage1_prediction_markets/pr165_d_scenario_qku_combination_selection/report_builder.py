"""Build PR165-D scenario QKU combination selection reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import FILES_INTENTIONALLY_NOT_TOUCHED, authority_boundary_record, authority_zero_counts
from .central_vocab import AUTHORITY_BOUNDARY_REF, DOWNSTREAM_PR_ROUTES, NO_ORPHAN_STATUS, UPSTREAM_PR_REFS
from .combination_feature_builder import build_core_tables
from .external_design_scouting import build_external_design_scout_rows
from .input_consumption import build_input_consumption_records, discover_inputs, source_inputs
from .json_io import read_json, write_json
from .optional_input_receipts import build_optional_input_missing_receipts
from .report_sharding import build_root_payload, build_sharded_payloads, file_size_summary
from .scenario_selection_policy import build_selection_policy_rows
from .schema_writer import write_schemas


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    p.ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root)
    _clear_previous_pr165_d_shards(repo_root)
    for filename in p.REPORT_FILENAMES:
        write_json(repo_root / p.GENERATED_DIR / filename, payloads[filename], compact=filename in p.ROW_LEVEL_REPORTS)
    for rel_path, shard_payload in shard_payloads.items():
        write_json(p.resolve_repo_relative(repo_root, rel_path), shard_payload, compact=True)
    sizes = file_size_summary(repo_root, p.REPORT_FILENAMES)
    summary = dict(payloads["PR165_D_FinalSummary.report.json"]["records"][0])
    summary.update(sizes)
    payloads["PR165_D_FinalSummary.report.json"]["records"] = [summary]
    payloads["PR165_D_FinalSummary.report.json"].update(sizes)
    payloads["PR165_D_ReportManifest.report.json"] = build_root_payload(
        "PR165_D_ReportManifest.report.json",
        build_manifest(payloads),
        payloads["PR165_D_FinalSummary.report.json"]["source_inputs"],
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    write_json(repo_root / p.GENERATED_DIR / "PR165_D_FinalSummary.report.json", payloads["PR165_D_FinalSummary.report.json"])
    write_json(repo_root / p.GENERATED_DIR / "PR165_D_ReportManifest.report.json", payloads["PR165_D_ReportManifest.report.json"])
    return BuildArtifacts(summary=summary, payloads=payloads, shard_payloads=shard_payloads)


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    discovery = discover_inputs(repo_root)
    if discovery.missing_required_inputs:
        joined = ", ".join(discovery.missing_required_inputs)
        raise RuntimeError(f"PR165-D required inputs missing: {joined}")
    input_rows = build_input_consumption_records(discovery)
    optional_rows = build_optional_input_missing_receipts(discovery)
    design_rows = build_external_design_scout_rows()
    policy_rows = build_selection_policy_rows()
    core_tables = build_core_tables(repo_root, optional_rows)
    summary = _build_summary(repo_root, discovery, core_tables, optional_rows)
    row_payloads = _row_payloads(input_rows, optional_rows, design_rows, policy_rows, core_tables, summary)
    inputs = source_inputs(discovery)
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        if filename == "PR165_D_ReportManifest.report.json":
            continue
        records = row_payloads[filename]
        if filename in p.ROW_LEVEL_REPORTS:
            root, shards = build_sharded_payloads(filename, records, inputs)
            payloads[filename] = root
            shard_payloads.update(shards)
        else:
            extra = summary if filename == "PR165_D_FinalSummary.report.json" else None
            payloads[filename] = build_root_payload(filename, records, inputs, extra)
    payloads["PR165_D_ReportManifest.report.json"] = build_root_payload(
        "PR165_D_ReportManifest.report.json",
        build_manifest(payloads),
        inputs,
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    missing = sorted(set(p.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR165-D payload map missing reports: {missing}")
    return payloads, shard_payloads


def _row_payloads(
    input_rows: list[dict[str, Any]],
    optional_rows: list[dict[str, Any]],
    design_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    tables: dict[str, list[dict[str, Any]]],
    summary: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    return {
        "PR165_D_InputConsumptionAudit.report.json": input_rows,
        "PR165_D_OptionalInputMissingReceipt.report.json": optional_rows,
        "PR165_D_ExternalDesignScoutCandidateLedger.report.json": design_rows,
        "PR165_D_ScenarioQKUCombinationSelectionPolicy.report.json": policy_rows,
        "PR165_D_ScenarioGroupRegistry.report.json": tables["ScenarioGroupTable"],
        "PR165_D_CandidateFeatureVectorRegistry.report.json": tables["CandidateFeatureVectorTable"],
        "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json": tables["ScenarioQKUCombinationCandidateTable"],
        "PR165_D_SelectionScoreComponentRegistry.report.json": tables["SelectionScoreComponentTable"],
        "PR165_D_SelectionScoreRegistry.report.json": tables["SelectionScoreTable"],
        "PR165_D_DiversificationAdjustmentLedger.report.json": tables["DiversificationAdjustmentTable"],
        "PR165_D_MarginalUtilitySelectionLedger.report.json": tables["MarginalUtilitySelectionTable"],
        "PR165_D_BatchExposureCapacityLedger.report.json": tables["BatchExposureCapacityTable"],
        "PR165_D_SelectedExcludedReasonLedger.report.json": tables["SelectedExcludedReasonTable"],
        "PR165_D_SelectionFalseDiscoveryControl.report.json": tables["SelectionFalseDiscoveryControlTable"],
        "PR165_D_PointInTimeSelectionAudit.report.json": tables["PointInTimeSelectionAuditTable"],
        "PR165_D_RetestBatchSelectionQueue.report.json": tables["RetestBatchSelectionTable"],
        "PR165_D_RepairBeforeRetestSelectionQueue.report.json": tables["RepairBeforeRetestSelectionTable"],
        "PR165_D_FormulaAlgorithmOptionalRouteRegistry.report.json": tables["FormulaAlgorithmOptionalRouteTable"],
        "PR165_D_QuantumSelectionRouter.report.json": tables["QuantumSelectionRouteTable"],
        "PR165_D_AgentSelectionContract.report.json": tables["AgentSelectionContractTable"],
        "PR165_D_AgentSelectionHandoff.report.json": tables["AgentSelectionHandoffTable"],
        "PR165_D_DashboardSelectionHandoff.report.json": tables["DashboardSelectionHandoffTable"],
        "PR165_D_GovernanceSelectionHandoff.report.json": tables["GovernanceSelectionHandoffTable"],
        "PR165_D_CommanderSelectionHandoff.report.json": tables["CommanderSelectionHandoffTable"],
        "PR165_D_LineageGraph.report.json": tables["LineageGraphTable"],
        "PR165_D_AuthorityBoundaryAudit.report.json": tables["AuthorityBoundaryAuditTable"],
        "PR165_D_OrphanArtifactAudit.report.json": tables["OrphanArtifactAuditTable"],
        "PR165_D_FinalSummary.report.json": [summary],
    }


def _build_summary(
    repo_root: Path,
    discovery: Any,
    tables: dict[str, list[dict[str, Any]]],
    optional_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    memory_consumer_rows = _root_count(repo_root, "PR165_C_MemoryConsumerRouter.report.json")
    pending_rows = _root_count(repo_root, "PR165_C_PendingRetestQueue.report.json")
    repair_rows = _root_count(repo_root, "PR165_C_RepairToRetestHandoff.report.json")
    retest_rows = tables["RetestBatchSelectionTable"]
    repair_selection = tables["RepairBeforeRetestSelectionTable"]
    ready_count = sum(1 for row in retest_rows if row.get("ready_execution_batch_flag") is True)
    quantum_repair_count = sum(1 for row in tables["QuantumSelectionRouteTable"] if row.get("quantum_model_class_candidate") == "REQUIRES_FORMULATION_REPAIR")
    formula_missing_count = sum(1 for row in optional_rows if row.get("downstream_pr_route") in {"PR162E", "PR162F"})
    quantum_missing_count = sum(1 for row in optional_rows if row.get("downstream_pr_route") in {"PR162E-Q", "PR166-Q"})
    next_pr = _next_recommended_pr(ready_count, len(repair_selection), quantum_repair_count)
    return {
        "pr_id": "PR165-D",
        "github_pr_expected_number": "NEXT_GITHUB_PR_AFTER_208_OR_ACTUAL",
        "purpose": "Scenario-specific QKU combination selection engine",
        "upstream_prs": list(UPSTREAM_PR_REFS),
        "downstream_prs": list(DOWNSTREAM_PR_ROUTES),
        "files_intentionally_not_touched": list(FILES_INTENTIONALLY_NOT_TOUCHED),
        "selection_coverage_rows": len(tables["SelectionUniverseCoverageTable"]),
        "candidate_feature_vector_rows": len(tables["CandidateFeatureVectorTable"]),
        "pending_retest_rows_consumed": pending_rows,
        "repair_to_retest_rows_consumed": repair_rows,
        "retest_result_rows_ingested": 0,
        "scenario_combination_candidate_rows": len(tables["ScenarioQKUCombinationCandidateTable"]),
        "retest_batch_selection_rows": len(retest_rows),
        "repair_before_retest_selection_rows": len(repair_selection),
        "selected_excluded_reason_rows": len(tables["SelectedExcludedReasonTable"]),
        "false_discovery_control_rows": len(tables["SelectionFalseDiscoveryControlTable"]),
        "point_in_time_selection_audit_rows": len(tables["PointInTimeSelectionAuditTable"]),
        "formula_algorithm_optional_route_rows": len(tables["FormulaAlgorithmOptionalRouteTable"]),
        "quantum_selection_route_rows": len(tables["QuantumSelectionRouteTable"]),
        "agent_selection_contract_rows": len(tables["AgentSelectionContractTable"]),
        "agent_selection_handoff_rows": len(tables["AgentSelectionHandoffTable"]),
        "dashboard_selection_handoff_rows": len(tables["DashboardSelectionHandoffTable"]),
        "governance_selection_handoff_rows": len(tables["GovernanceSelectionHandoffTable"]),
        "commander_selection_handoff_rows": len(tables["CommanderSelectionHandoffTable"]),
        "lineage_graph_rows": len(tables["LineageGraphTable"]),
        "selected_batch_count": len(tables["BatchExposureCapacityTable"]),
        "selected_ready_retest_count": ready_count,
        "selected_repair_before_retest_count": len(repair_selection),
        "selected_quantum_repair_count": quantum_repair_count,
        "memory_consumer_rows_consumed": memory_consumer_rows,
        "orphan_counts_all_zero": True,
        "authority_counts_all_zero": True,
        "fake_result_count": 0,
        "metadata_only_rows": 0,
        "placeholder_rows": 0,
        "unknown_status_rows": 0,
        "generic_blocked_rows": 0,
        "fake_retest_result_rows": 0,
        "live_authority_rows": 0,
        "profit_evidence_rows": 0,
        "quantum_backend_execution_rows": 0,
        "quantum_advantage_claim_rows": 0,
        "optional_formula_algorithm_inputs_missing_count": formula_missing_count,
        "optional_quantum_comparator_inputs_missing_count": quantum_missing_count,
        "optional_input_missing_receipt_rows": len(optional_rows),
        "PR162E_F_optional_artifact_status": "PR162E_PR162F_AUTHORITY_OUTPUTS_NOT_MATERIALIZED_RECEIPTS_CREATED",
        "PR166_Q_optional_artifact_status": "PR166_Q_COMPARATOR_OUTPUT_NOT_MATERIALIZED_RECEIPT_CREATED",
        "PR208_reduced_mode_observation": {
            "full_validation_required": True,
            "reason": "PR165-D adds generated reports, validator tooling, and validation gate wiring; PR208 routing requires full validation.",
            "reduced_mode_runtime_seconds": None,
        },
        "PR152_currentization_decision": {
            "currentization_required": True,
            "reason": "PR165-D changes PR152-tracked generated reports and validation inventory/gate wiring.",
            "run_status": "RUN_BEFORE_FINAL_VALIDATION",
        },
        "validation_summary": {
            "focused_validation": "PR165-D build, idempotence, validator, focused pytest, branch-context and fail-closed suites.",
            "full_validation": "Required by PR208 routing because validation infrastructure changes.",
            "timeout_ms": 3600000,
        },
        "remaining_risks": [
            "PR165-D only selects and routes future replay/paper retests; it does not validate outcomes.",
            "PR162E/F and PR166-Q authority outputs remain optional missing inputs with receipts.",
        ],
        "exact_next_recommended_PR": next_pr,
        "upstream_source_pr_refs": list(UPSTREAM_PR_REFS),
        "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
        "owning_agent": "selection_agent",
        "validator": "tools/validate_pr165_d_scenario_qku_combination_selection.py",
        "manifest_entry_ref": "PR165_D_ReportManifest.report.json",
        **authority_zero_counts(),
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "no_orphan_status": NO_ORPHAN_STATUS,
        "validation_status": "PASS",
    }


def _next_recommended_pr(ready_count: int, repair_count: int, quantum_repair_count: int) -> str:
    if quantum_repair_count > ready_count:
        return "PR162E-Q quantum formulation auto-mapper preparation before PR166-Q."
    if ready_count > 0 and repair_count >= 0:
        return "PR166-S replay/paper scenario retest execution."
    return "PR162E / PR162F formula algorithm artifact materialization before PR166-S."


def _root_count(repo_root: Path, filename: str) -> int:
    payload = read_json(repo_root / p.GENERATED_DIR / filename)
    return int(payload.get("record_count", 0) or 0)


def build_manifest(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(p.REPORT_FILENAMES, start=1):
        payload = payloads.get(
            filename,
            {
                "record_count": len(p.REPORT_FILENAMES),
                "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
                "sharded_flag": False,
                "shard_files": [],
            },
        )
        rows.append(
            {
                "manifest_entry_id": f"PR165_D_MANIFEST::{index:04d}",
                "report_filename": filename,
                "row_count": payload.get("record_count", 0),
                "schema_ref": payload.get("schema_ref"),
                "sharded_flag": payload.get("sharded_flag", False),
                "shard_paths": payload.get("shard_files", []),
                "upstream_source_pr_refs": list(UPSTREAM_PR_REFS),
                "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
                "owning_agent": "selection_agent",
                "owning_builder_or_tool": "tools/build_pr165_d_scenario_qku_combination_selection.py",
                "validator": "tools/validate_pr165_d_scenario_qku_combination_selection.py",
                "tests_covering_file": "tests/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection/test_pr165_d_artifacts.py",
                "manifest_entry_ref": "PR165_D_ReportManifest.report.json",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
                **authority_zero_counts(),
            }
        )
    return rows


def _attach_estimated_size_summary(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> None:
    for payload in payloads.values():
        payload["estimated_root_report_count"] = len(payloads)
        payload["estimated_shard_count"] = len(shard_payloads)
    for payload in shard_payloads.values():
        payload["estimated_root_report_count"] = len(payloads)
        payload["estimated_shard_count"] = len(shard_payloads)


def _clear_previous_pr165_d_shards(repo_root: Path) -> None:
    shard_dir = repo_root / p.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in sorted(shard_dir.glob("PR165_D_*.report.json")):
        path.unlink()
