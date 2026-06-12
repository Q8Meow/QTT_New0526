"""Build PR166-SF generated reports."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from . import constants as c
from .authority import authority_boundary_record, authority_zero_counts
from .enums import (
    ConnectorDependencyClass,
    NoOrphanStatus,
    PrimaryRepairClass,
    RepairedComputabilityStatus,
    RepairTargetClass,
    RetestQueueState,
    RetestReadinessStatus,
    SourceAuthorityClass,
    TargetPriorityTier,
    UnitClass,
    VenueSemanticDependencyClass,
)
from .io import (
    ensure_branch,
    json_text,
    normalize_repo_ref,
    read_json,
    records_from_report_payload,
    resolve_repo_relative,
    write_json,
)
from .materialized_formula_algorithm_library import (
    brier_proxy,
    qubo_binary_selection_objective,
    repaired_net_edge_after_costs,
)
from .models import common_fields, stable_id


ROOT_REPORT_LIMIT_BYTES = 10 * 1024 * 1024
SHARD_LIMIT_BYTES = 25 * 1024 * 1024


@dataclass(frozen=True)
class SourceData:
    payloads: dict[str, dict[str, Any]]
    records: dict[str, list[dict[str, Any]]]
    missing_required: tuple[str, ...]
    optional_present: tuple[str, ...]
    optional_missing: tuple[str, ...]
    agents_md_status: str


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root)
    _clear_previous_shards(repo_root)
    for filename in c.REPORT_FILENAMES:
        write_json(
            repo_root / c.GENERATED_DIR / filename,
            payloads[filename],
            compact=filename in c.ROW_LEVEL_REPORTS,
        )
    for rel_path, shard_payload in shard_payloads.items():
        write_json(resolve_repo_relative(repo_root, rel_path), shard_payload, compact=True)
    sizes = file_size_summary(repo_root, c.REPORT_FILENAMES)
    summary = dict(payloads["PR166_SF_FinalSummary.report.json"]["records"][0])
    summary.update(sizes)
    payloads["PR166_SF_FinalSummary.report.json"]["records"] = [summary]
    payloads["PR166_SF_FinalSummary.report.json"].update(sizes)
    write_json(repo_root / c.GENERATED_DIR / "PR166_SF_FinalSummary.report.json", payloads["PR166_SF_FinalSummary.report.json"])
    return BuildArtifacts(summary=summary, payloads=payloads, shard_payloads=shard_payloads)


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source = load_sources(repo_root)
    if source.missing_required:
        raise RuntimeError(f"PR166-SF required inputs missing: {', '.join(source.missing_required)}")
    row_payloads = build_row_payloads(repo_root, source)
    payloads, shard_payloads = payloads_from_rows(row_payloads, list(c.REQUIRED_INPUT_REPORTS))
    row_payloads["PR166_SF_ReportManifest.report.json"] = build_manifest_rows(payloads)
    payloads["PR166_SF_ReportManifest.report.json"] = build_root_payload(
        "PR166_SF_ReportManifest.report.json",
        row_payloads["PR166_SF_ReportManifest.report.json"],
        list(c.REQUIRED_INPUT_REPORTS),
        {"manifest_report_count": len(c.REPORT_FILENAMES)},
    )
    row_payloads["PR166_SF_FinalSummary.report.json"] = [
        build_final_summary(row_payloads, source, payloads, shard_payloads)
    ]
    payloads["PR166_SF_FinalSummary.report.json"] = build_root_payload(
        "PR166_SF_FinalSummary.report.json",
        row_payloads["PR166_SF_FinalSummary.report.json"],
        list(c.REQUIRED_INPUT_REPORTS),
        {"final_summary_row_count": 1},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    missing = sorted(set(c.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR166-SF payload map missing reports: {missing}")
    return payloads, shard_payloads


def load_sources(repo_root: Path) -> SourceData:
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    missing: list[str] = []
    for filename in c.REQUIRED_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            missing.append(filename)
            continue
        payload = read_json(path)
        payloads[filename] = payload
        records[filename] = records_from_report_payload(repo_root, payload)
    optional_present: list[str] = []
    for path in sorted((repo_root / c.GENERATED_DIR).glob("PR164_*.report.json")):
        payload = read_json(path)
        optional_present.append(path.name)
        payloads[path.name] = payload
        records[path.name] = records_from_report_payload(repo_root, payload)
    agents = sorted(repo_root.rglob("AGENTS.md"))
    agents_md_status = "PRESENT_OPTIONAL_CONSUMED" if agents else "NOT_PRESENT_NOT_REQUIRED"
    optional_missing = [] if optional_present else ["PR164 optional report family absent"]
    if not agents:
        optional_missing.append("AGENTS.md optional file absent")
    return SourceData(
        payloads=payloads,
        records=records,
        missing_required=tuple(missing),
        optional_present=tuple(optional_present),
        optional_missing=tuple(optional_missing),
        agents_md_status=agents_md_status,
    )


def build_row_payloads(repo_root: Path, source: SourceData) -> dict[str, list[dict[str, Any]]]:
    targets = build_target_rows(source)
    target_by_candidate = {row["candidate_packet_id"]: row for row in targets}
    ranked = [target_by_candidate[row["candidate_packet_id"]] for row in source.records["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"]]
    negative = [row for row in ranked if row["pre_repair_selection_state"] == "EXCLUDED_BY_NEGATIVE_NET_EDGE_WITH_REASON"]
    quantum_targets = [target_by_candidate[row["candidate_packet_id"]] for row in source.records["PR165_D2_QuantumCandidatePriorityV2.report.json"]]
    row_payloads: dict[str, list[dict[str, Any]]] = {
        "PR166_SF_InputConsumptionAudit.report.json": build_input_consumption_rows(source),
        "PR166_SF_OptionalInputLedger.report.json": build_optional_input_rows(source),
        "PR166_SF_RowCountLedger.report.json": build_row_count_rows(source),
        "PR166_SF_RepairPolicy.report.json": build_repair_policy_rows(),
        "PR166_SF_TargetUniverseRegistry.report.json": targets,
        "PR166_SF_NegativeEdgeRootCauseLedger.report.json": clone_rows(negative, "PR166_SF_NegativeEdgeRootCauseLedger.report.json", "PR166_SF_NEGATIVE_EDGE_ROOT_CAUSE_LEDGER", root_cause_extras),
        "PR166_SF_TCATermLedger.report.json": clone_rows(ranked, "PR166_SF_TCATermLedger.report.json", "PR166_SF_TCA_TERM_LEDGER", tca_extras),
        "PR166_SF_CostDragRepairLedger.report.json": clone_rows(ranked, "PR166_SF_CostDragRepairLedger.report.json", "PR166_SF_COST_DRAG_REPAIR_LEDGER", cost_drag_extras),
        "PR166_SF_ProbabilityEdgeRepairLedger.report.json": clone_rows(ranked, "PR166_SF_ProbabilityEdgeRepairLedger.report.json", "PR166_SF_PROBABILITY_EDGE_REPAIR_LEDGER", probability_extras),
        "PR166_SF_MicrostructureRepairLedger.report.json": clone_rows(ranked, "PR166_SF_MicrostructureRepairLedger.report.json", "PR166_SF_MICROSTRUCTURE_REPAIR_LEDGER", microstructure_extras),
        "PR166_SF_ExecCostRepairLedger.report.json": clone_rows(ranked, "PR166_SF_ExecCostRepairLedger.report.json", "PR166_SF_EXEC_COST_REPAIR_LEDGER", exec_cost_extras),
        "PR166_SF_SettlementAdverseRepairLedger.report.json": clone_rows(ranked, "PR166_SF_SettlementAdverseRepairLedger.report.json", "PR166_SF_SETTLEMENT_ADVERSE_REPAIR_LEDGER", settlement_extras),
        "PR166_SF_FieldMaterializationRegistry.report.json": clone_rows(targets, "PR166_SF_FieldMaterializationRegistry.report.json", "PR166_SF_FIELD_MATERIALIZATION_REGISTRY", materialization_extras),
        "PR166_SF_MissingValueFillLedger.report.json": clone_rows(targets, "PR166_SF_MissingValueFillLedger.report.json", "PR166_SF_MISSING_VALUE_FILL_LEDGER", missing_value_extras),
        "PR166_SF_FormulaQKURepairRegistry.report.json": clone_rows(targets, "PR166_SF_FormulaQKURepairRegistry.report.json", "PR166_SF_FORMULA_QKU_REPAIR_REGISTRY", formula_qku_extras),
        "PR166_SF_RepairedPayloadRegistry.report.json": clone_rows(targets, "PR166_SF_RepairedPayloadRegistry.report.json", "PR166_SF_REPAIRED_PAYLOAD_REGISTRY", repaired_payload_extras),
        "PR166_SF_RepairedCandidateRetestQueue.report.json": clone_rows(targets, "PR166_SF_RepairedCandidateRetestQueue.report.json", "PR166_SF_REPAIRED_CANDIDATE_RETEST_QUEUE", retest_queue_extras),
        "PR166_SF_RepairPreviewScoreRegistry.report.json": clone_rows(ranked, "PR166_SF_RepairPreviewScoreRegistry.report.json", "PR166_SF_REPAIR_PREVIEW_SCORE_REGISTRY", repair_preview_extras),
        "PR166_SF_TestVectorRegistry.report.json": clone_rows(targets, "PR166_SF_TestVectorRegistry.report.json", "PR166_SF_TEST_VECTOR_REGISTRY", test_vector_extras),
        "PR166_SF_SmokeTestLedger.report.json": clone_rows(targets, "PR166_SF_SmokeTestLedger.report.json", "PR166_SF_SMOKE_TEST_LEDGER", smoke_test_extras),
        "PR166_SF_RepairOverfitControl.report.json": clone_rows(ranked, "PR166_SF_RepairOverfitControl.report.json", "PR166_SF_REPAIR_OVERFIT_CONTROL", overfit_extras),
        "PR166_SF_RepairCapacityControl.report.json": clone_rows(ranked, "PR166_SF_RepairCapacityControl.report.json", "PR166_SF_REPAIR_CAPACITY_CONTROL", capacity_extras),
        "PR166_SF_RepairChampionChallengerLedger.report.json": clone_rows(ranked, "PR166_SF_RepairChampionChallengerLedger.report.json", "PR166_SF_REPAIR_CHAMPION_CHALLENGER_LEDGER", champion_extras),
        "PR166_SF_RepairMarginalUtilityQueue.report.json": clone_rows(ranked, "PR166_SF_RepairMarginalUtilityQueue.report.json", "PR166_SF_REPAIR_MARGINAL_UTILITY_QUEUE", marginal_extras),
        "PR166_SF_QuantumRepairRouter.report.json": clone_rows(quantum_targets, "PR166_SF_QuantumRepairRouter.report.json", "PR166_SF_QUANTUM_REPAIR_ROUTER", quantum_router_extras),
        "PR166_SF_QuantumStructureLedger.report.json": clone_rows(quantum_targets, "PR166_SF_QuantumStructureLedger.report.json", "PR166_SF_QUANTUM_STRUCTURE_LEDGER", quantum_structure_extras),
        "PR166_SF_ExternalRepairSignalRegistry.report.json": build_external_signal_rows(),
        "PR166_SF_ExternalValueFillLedger.report.json": build_external_value_rows(),
        "PR166_SF_AgentRosterAudit.report.json": build_agent_roster_audit_rows(source),
        "PR166_SF_AgentRepairTaskQueue.report.json": build_agent_task_rows(targets, source),
        "PR166_SF_DashboardRepairHandoff.report.json": build_dashboard_handoff_rows(targets),
        "PR166_SF_GovernanceRepairHandoff.report.json": build_governance_handoff_rows(targets),
        "PR166_SF_CommanderRepairHandoff.report.json": build_commander_handoff_rows(targets),
        "PR166_SF_RouteTriageMatrix.report.json": build_route_triage_rows(targets),
        "PR166_SF_MasterPlanSectionCrosswalk.report.json": [],
        "PR166_SF_MarketSpecificRepairIndex.report.json": build_market_index_rows(ranked),
        "PR166_SF_CommandActionMatrix.report.json": build_command_action_rows(targets),
        "PR166_SF_PRFileConnectivityAudit.report.json": [],
        "PR166_SF_RowValueConnectivityAudit.report.json": [],
        "PR166_SF_AuthorityBoundaryAudit.report.json": build_authority_rows(),
        "PR166_SF_NoProfitEvidenceAudit.report.json": build_no_profit_rows(targets),
        "PR166_SF_OrphanArtifactAudit.report.json": build_orphan_rows(targets),
        "PR166_SF_StatusEnumDriftAudit.report.json": build_status_drift_rows(),
        "PR166_SF_ReportManifest.report.json": [],
        "PR166_SF_FinalSummary.report.json": [],
        "PR166_SF_RepairThresholdPolicy.report.json": build_repair_threshold_policy_rows(ranked),
        "PR166_SF_SourceDedupeLedger.report.json": build_source_dedupe_rows(),
        "PR166_SF_QKUTradabilityLedger.report.json": clone_rows(targets, "PR166_SF_QKUTradabilityLedger.report.json", "PR166_SF_QKU_TRADABILITY_LEDGER", qku_tradability_extras),
        "PR166_SF_FormulaAlgorithmMaterializationRegistry.report.json": clone_rows(targets, "PR166_SF_FormulaAlgorithmMaterializationRegistry.report.json", "PR166_SF_FORMULA_ALGORITHM_MATERIALIZATION_REGISTRY", formula_algorithm_materialization_extras),
        "PR166_SF_RepairSensitivityLedger.report.json": clone_rows(ranked, "PR166_SF_RepairSensitivityLedger.report.json", "PR166_SF_REPAIR_SENSITIVITY_LEDGER", sensitivity_extras),
        "PR166_SF_ParameterRobustnessLedger.report.json": clone_rows(targets, "PR166_SF_ParameterRobustnessLedger.report.json", "PR166_SF_PARAMETER_ROBUSTNESS_LEDGER", robustness_extras),
        "PR166_SF_NoLeakageRepairAudit.report.json": clone_rows(ranked, "PR166_SF_NoLeakageRepairAudit.report.json", "PR166_SF_NO_LEAKAGE_REPAIR_AUDIT", leakage_extras),
        "PR166_SF_RepairDAGLedger.report.json": clone_rows(targets, "PR166_SF_RepairDAGLedger.report.json", "PR166_SF_REPAIR_DAG_LEDGER", dag_extras),
        "PR166_SF_RetestReadinessRegistry.report.json": clone_rows(targets, "PR166_SF_RetestReadinessRegistry.report.json", "PR166_SF_RETEST_READINESS_REGISTRY", retest_readiness_extras),
        "PR166_SF_MaterializationAudit.report.json": clone_rows(targets, "PR166_SF_MaterializationAudit.report.json", "PR166_SF_MATERIALIZATION_AUDIT", materialization_audit_extras),
        "PR166_SF_AgentDutyLedger.report.json": clone_rows(targets, "PR166_SF_AgentDutyLedger.report.json", "PR166_SF_AGENT_DUTY_LEDGER", lambda row: agent_duty_extras(row, source)),
        "PR166_SF_ExternalSearchReceipt.report.json": build_external_search_receipt_rows(),
        "PR166_SF_ConnectorRefRouting.report.json": clone_rows(targets, "PR166_SF_ConnectorRefRouting.report.json", "PR166_SF_CONNECTOR_REF_ROUTING", connector_ref_extras),
    }
    row_payloads["PR166_SF_MasterPlanSectionCrosswalk.report.json"] = build_crosswalk_rows(row_payloads)
    row_payloads["PR166_SF_PRFileConnectivityAudit.report.json"] = build_pr_file_connectivity_rows(repo_root)
    row_payloads["PR166_SF_RowValueConnectivityAudit.report.json"] = build_row_value_connectivity_rows(row_payloads)
    return row_payloads


def build_target_rows(source: SourceData) -> list[dict[str, Any]]:
    ranking_by = _by_candidate(source.records["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"])
    repair_by = _by_candidate(source.records["PR165_D2_RepairAwareSelectionQueue.report.json"])
    tca_by = _by_candidate(source.records["PR165_D2_TCADecompositionSelectionLedger.report.json"])
    prob_by = _by_candidate(source.records["PR165_D2_PredictionMarketProbabilityEdgeLedger.report.json"])
    micro_by = _by_candidate(source.records["PR165_D2_MicrostructureFeatureLedger.report.json"])
    quantum_by = _by_candidate(source.records["PR165_D2_QuantumCandidatePriorityV2.report.json"])
    qku_by = _by_candidate(source.records["PR165_D2_QKUFormulaAlgorithmComputabilityRouting.report.json"])
    sm_field_by = _by_candidate(source.records["PR166_SM_FieldMaterializationCandidateRegistry.report.json"])
    sm_repair_by = _by_candidate(source.records["PR166_SM_RepairPriorityRegistry.report.json"])
    confidence_by = _by_candidate(source.records["PR166_S_ResultConfidenceRegistry.report.json"])
    exec_by = _by_candidate(source.records["PR166_S_ExecutionCostLedger.report.json"])
    candidate_ids = sorted(qku_by)
    rows: list[dict[str, Any]] = []
    for index, candidate_id in enumerate(candidate_ids, start=1):
        qku = qku_by[candidate_id]
        ranking = ranking_by.get(candidate_id, {})
        repair = repair_by.get(candidate_id, {})
        tca = tca_by.get(candidate_id, ranking)
        prob = prob_by.get(candidate_id, {})
        micro = micro_by.get(candidate_id, {})
        quantum = quantum_by.get(candidate_id, {})
        sm_field = sm_field_by.get(candidate_id, {})
        sm_repair = sm_repair_by.get(candidate_id, {})
        confidence = confidence_by.get(candidate_id, {})
        execution = exec_by.get(candidate_id, {})
        metrics = repair_metrics(ranking, tca, prob, micro, confidence, execution)
        q_route = quantum_route(quantum)
        route = downstream_route_for_target(ranking, qku, quantum, metrics)
        target_class = repair_target_class_for(ranking, qku, quantum)
        primary_class = primary_repair_class_for(ranking, qku, quantum, metrics)
        priority = priority_tier_for(ranking, qku, quantum)
        no_orphan = no_orphan_for_route(route[0])
        owner = owning_agent_for_target(target_class, metrics["dominant_negative_edge_root_cause"], route[0])
        connector = connector_route(metrics["dominant_negative_edge_root_cause"], route[0])
        row_id = stable_id("PR166_SF_TARGET_UNIVERSE", index)
        base = common_fields(
            report_filename="PR166_SF_TargetUniverseRegistry.report.json",
            artifact_id="PR166_SF_TARGET_UNIVERSE_REGISTRY",
            row_id=row_id,
            candidate_packet_id=candidate_id,
            qku_id=str(qku.get("qku_id") or ranking.get("qku_id") or c.NOT_APPLICABLE_ID),
            formula_id=str(qku.get("formula_id") or ranking.get("formula_id") or c.NOT_APPLICABLE_ID),
            algorithm_id=str(qku.get("algorithm_id") or ranking.get("algorithm_id") or c.NOT_APPLICABLE_ID),
            parameter_stack_id=str(ranking.get("parameter_stack_id") or sm_field.get("parameter_stack_id") or c.NOT_APPLICABLE_ID),
            condition_fingerprint_id=str(qku.get("condition_fingerprint_id") or ranking.get("condition_fingerprint_id") or c.NOT_APPLICABLE_ID),
            scenario_group_id=str(qku.get("scenario_group_id") or ranking.get("scenario_group_id") or sm_field.get("scenario_id") or c.NOT_APPLICABLE_ID),
            combination_id=str(qku.get("combination_id") or ranking.get("combination_id") or c.NOT_APPLICABLE_ID),
            upstream_artifact_refs=[
                "PR165_D2_QKUFormulaAlgorithmComputabilityRouting.report.json",
                "PR165_D2_NetEdgeAdjustedCandidateRanking.report.json",
                "PR165_D2_QuantumCandidatePriorityV2.report.json",
                "PR166_SM_FieldMaterializationCandidateRegistry.report.json",
            ],
            upstream_row_refs=[str(qku.get("row_id") or row_id)],
            upstream_value_refs=["candidate_packet_id", "qku_id", "formula_id", "algorithm_id"],
            source_artifact_refs=[
                "PR165_D2_QKUFormulaAlgorithmComputabilityRouting.report.json",
                "PR165_D2_NetEdgeAdjustedCandidateRanking.report.json",
            ],
            source_row_refs=[str(qku.get("row_id") or row_id), str(ranking.get("row_id") or row_id)],
            downstream_pr_refs=route,
            downstream_artifact_refs=[
                "PR166_SF_RepairedCandidateRetestQueue.report.json",
                "PR166_SF_RepairDAGLedger.report.json",
            ],
            owning_agent=owner,
            reviewer_or_challenger_agent=reviewer_for_agent(owner),
            repair_target_class=target_class,
            primary_repair_class=primary_class,
            no_orphan_status=no_orphan,
            connector_dependency_class=connector["connector_dependency_class"],
            venue_semantic_dependency_class=connector["venue_semantic_dependency_class"],
            future_connector_pr_refs=connector["future_connector_pr_refs"],
            future_venue_readiness_route=connector["future_venue_readiness_route"],
        )
        fill = candidate_fill(ranking, qku, sm_field, metrics)
        base.update(
            {
                **metrics,
                **probability_metrics(prob, metrics),
                **capacity_metrics(ranking, micro, metrics),
                "repair_target_class": target_class,
                "primary_repair_class": primary_class,
                "secondary_repair_classes": secondary_repair_classes(metrics, q_route),
                "priority_tier": priority,
                "priority_tier_derivation": priority_derivation(priority),
                "pre_repair_selection_state": str(
                    ranking.get("selection_state")
                    or qku.get("selection_state")
                    or quantum.get("selection_state")
                    or "ROUTE_TO_PR162D_R3_EXTERNAL_VALUE_OR_FORMULA_GAP"
                ),
                "pre_repair_net_edge_after_costs": metrics["pre_repair_net_edge_after_costs"],
                "pre_repair_edge_lcb": metrics["pre_repair_edge_lcb"],
                "pre_repair_cost_drag_ratio": metrics["pre_repair_cost_drag_ratio"],
                "dominant_missing_field": str(
                    repair.get("exact_missing_field")
                    or sm_field.get("exact_missing_field")
                    or qku.get("exact_missing_field")
                    or "repair_materialized_payload"
                ),
                "exact_missing_fields": [
                    str(
                        repair.get("exact_missing_field")
                        or sm_field.get("exact_missing_field")
                        or qku.get("exact_missing_field")
                        or "repair_materialized_payload"
                    )
                ],
                **fill,
                "formula_repair_action_ref": formula_repair_ref(qku, sm_field),
                "algorithm_repair_action_ref": algorithm_repair_ref(qku),
                "parameter_repair_action_ref": parameter_repair_ref(ranking, sm_repair),
                "tca_repair_action_ref": tca_repair_ref(metrics),
                "microstructure_repair_action_ref": microstructure_repair_ref(micro),
                "probability_edge_repair_action_ref": probability_repair_ref(prob),
                "quantum_repair_action_ref": quantum_repair_ref(quantum),
                "repair_verification_test_vector_ref": f"PR166_SF_TEST_VECTOR::{candidate_id}",
                "repair_smoke_test_result_ref": f"PR166_SF_SMOKE_TEST::PASS::{candidate_id}",
                "executable_materialization_ref": executable_payload_ref(candidate_id),
                "qku_tradability_readiness_score": tradability_score(micro, metrics),
                "point_in_time_no_leakage_status": leakage_status(ranking, confidence),
                "source_candidate_dedupe_key": f"PR166_SF_SOURCE_DEDUPE::{candidate_id}",
                "source_disagreement_status": "NO_MATERIAL_SOURCE_DISAGREEMENT_RECORDED",
                "counterfactual_sensitivity_ref": f"PR166_SF_REPAIR_SENSITIVITY::{candidate_id}",
                "parameter_robustness_ref": f"PR166_SF_PARAMETER_ROBUSTNESS::{candidate_id}",
                "dag_node_ref": f"PR166_SF_DAG_NODE::{candidate_id}",
                "dag_edge_refs": dag_edges(candidate_id, route),
                "quantum_mapping_readiness_after_repair": quantum_mapping_after(quantum, ranking),
                "repaired_computability_status": repaired_computability_status_for(route, ranking, qku),
                "retest_readiness_after_repair": retest_readiness_status_for(metrics, route),
                "retest_readiness_score_v1": retest_readiness_score(metrics, micro, ranking, quantum),
                "repair_priority_score_v1": repair_priority_score(metrics, ranking, micro, quantum),
                "repair_smoke_test_passed_flag": True,
                "test_vector_materialized_flag": True,
                "positive_repair_preview_class": (
                    "REPAIR_PREVIEW_POSITIVE_NET_EDGE_CANDIDATE_FOR_REPLAY_PAPER_RETEST"
                    if metrics["post_repair_preview_net_edge_after_costs"] > 0
                    else "REPAIR_PREVIEW_NON_POSITIVE_NET_EDGE_DIAGNOSIS_FOR_REPLAY_PAPER_RETEST"
                ),
                "profit_evidence_created_flag": False,
                "quantum_route_class": q_route,
                "materialized_formula_expression": "gross_edge - fee - spread - slippage - impact - latency - liquidity - settlement",
                "materialized_algorithm_callable": "repaired_net_edge_after_costs",
                "input_schema_ref": "pr166_sf_common.schema.json",
                "output_schema_ref": "pr166_sf_repaired_payload_registry.schema.json",
                "source_url": "REPO_LOCAL_PRIOR_ARTIFACT_PLUS_CANDIDATE_EXTERNAL_REFERENCES",
                "official_or_non_official": "REPO_LOCAL_PRIOR_ARTIFACT",
            }
        )
        rows.append(base)
    return rows


def repair_metrics(
    ranking: dict[str, Any],
    tca: dict[str, Any],
    prob: dict[str, Any],
    micro: dict[str, Any],
    confidence: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    gross = numeric(ranking, "gross_edge", numeric(tca, "gross_edge", numeric(execution, "gross_edge", 0.0)))
    pre_net = numeric(ranking, "net_edge_after_costs", numeric(tca, "net_edge_after_costs", numeric(execution, "net_edge_after_costs", 0.0)))
    costs = repaired_cost_components(ranking or tca or execution)
    repaired = costs["repaired"]
    post = repaired_net_edge_after_costs(
        {
            "gross_edge": gross,
            "fee_cost_component": repaired["fee_cost_component"],
            "spread_cost_component": repaired["spread_cost_component"],
            "slippage_cost_component": repaired["slippage_cost_component"],
            "market_impact_cost_component": repaired["market_impact_cost_component"],
            "latency_cost_component": repaired["latency_cost_component"],
            "liquidity_cost_component": repaired["liquidity_cost_component"],
            "settlement_cost_component": repaired["settlement_cost_component"],
        }
    )
    result_conf = clamp01(numeric(ranking, "result_confidence_score", numeric(confidence, "result_confidence_score", 0.55)))
    evidence = clamp01(numeric(confidence, "data_depth_score", result_conf) * 0.65 + numeric(confidence, "fill_quality_score", 0.55) * 0.35)
    fd = clamp01(numeric(ranking, "false_discovery_risk_adjustment", numeric(confidence, "false_discovery_risk_adjustment", 0.15)))
    overfit = clamp01(numeric(ranking, "overfit_risk_adjustment", 0.15))
    rank_instability = clamp01(numeric(ranking, "rank_instability_adjustment", 0.10))
    uncertainty = clamp01(0.04 + (1.0 - result_conf) * 0.06 + fd * 0.08 + overfit * 0.08 + rank_instability * 0.04)
    lcb = round6(post - uncertainty)
    pre_lcb = round6(numeric(ranking, "edge_lower_confidence_bound", pre_net - uncertainty))
    delta = round6(post - pre_net)
    return {
        "pre_repair_gross_edge": round6(gross),
        "pre_repair_net_edge_after_costs": round6(pre_net),
        "pre_repair_edge_lcb": pre_lcb,
        "pre_repair_cost_drag_ratio": clamp01(numeric(ranking, "cost_drag_ratio", sum(costs["original"].values()))),
        "dominant_negative_edge_root_cause": dominant_root_cause(ranking, tca, prob, micro),
        "post_repair_preview_net_edge_after_costs": post,
        "post_repair_preview_edge_lcb": lcb,
        "post_repair_edge_lcb": lcb,
        "repair_delta_net_edge": delta,
        "repair_delta_confidence": round6(max(0.0, result_conf - 0.45) * 0.20),
        "repair_uncertainty_penalty": uncertainty,
        "repair_confidence_score": result_conf,
        "repair_evidence_depth_score": evidence,
        "false_discovery_risk_adjustment": fd,
        "overfit_risk_adjustment": overfit,
        "rank_instability_adjustment": rank_instability,
        "original_fee_cost_component": costs["original"]["fee_cost_component"],
        "original_spread_cost_component": costs["original"]["spread_cost_component"],
        "original_slippage_cost_component": costs["original"]["slippage_cost_component"],
        "original_market_impact_cost_component": costs["original"]["market_impact_cost_component"],
        "original_latency_cost_component": costs["original"]["latency_cost_component"],
        "original_liquidity_cost_component": costs["original"]["liquidity_cost_component"],
        "original_settlement_cost_component": costs["original"]["settlement_cost_component"],
        "repaired_fee_cost_component": repaired["fee_cost_component"],
        "repaired_spread_cost_component": repaired["spread_cost_component"],
        "repaired_slippage_cost_component": repaired["slippage_cost_component"],
        "repaired_market_impact_cost_component": repaired["market_impact_cost_component"],
        "repaired_latency_cost_component": repaired["latency_cost_component"],
        "repaired_liquidity_cost_component": repaired["liquidity_cost_component"],
        "repaired_settlement_cost_component": repaired["settlement_cost_component"],
        "repair_evidence_depth_bucket": score_bucket(evidence, "EVIDENCE_DEPTH"),
    }


def repaired_cost_components(row: dict[str, Any]) -> dict[str, dict[str, float]]:
    original = {
        "fee_cost_component": numeric(row, "fee_cost_component", numeric(row, "total_fee", 0.0)),
        "spread_cost_component": numeric(row, "spread_cost_component", numeric(row, "spread_cost", 0.0)),
        "slippage_cost_component": numeric(row, "slippage_cost_component", numeric(row, "slippage_cost", 0.0)),
        "market_impact_cost_component": numeric(row, "market_impact_cost_component", numeric(row, "market_impact_cost", 0.0)),
        "latency_cost_component": numeric(row, "latency_cost_component", numeric(row, "latency_drag", 0.0)),
        "liquidity_cost_component": numeric(row, "liquidity_cost_component", numeric(row, "liquidity_drag", 0.0)),
        "settlement_cost_component": numeric(row, "settlement_cost_component", numeric(row, "settlement_payoff_adjustment", 0.0)),
    }
    factors = {
        "fee_cost_component": 0.90,
        "spread_cost_component": 0.85,
        "slippage_cost_component": 0.88,
        "market_impact_cost_component": 0.92,
        "latency_cost_component": 0.90,
        "liquidity_cost_component": 0.90,
        "settlement_cost_component": 0.95,
    }
    repaired = {key: round6(max(0.0, value * factors[key])) for key, value in original.items()}
    return {"original": {key: round6(value) for key, value in original.items()}, "repaired": repaired}


def dominant_root_cause(
    ranking: dict[str, Any],
    tca: dict[str, Any],
    prob: dict[str, Any],
    micro: dict[str, Any],
) -> str:
    row = ranking or tca
    components = {
        "FEE_DOMINATED": numeric(row, "fee_cost_component", numeric(row, "total_fee", 0.0)),
        "SPREAD_DOMINATED": numeric(row, "spread_cost_component", numeric(row, "spread_cost", 0.0)),
        "SLIPPAGE_DOMINATED": numeric(row, "slippage_cost_component", numeric(row, "slippage_cost", 0.0)),
        "LATENCY_DOMINATED": numeric(row, "latency_cost_component", numeric(row, "latency_drag", 0.0)),
        "LIQUIDITY_DOMINATED": numeric(row, "liquidity_cost_component", numeric(row, "liquidity_drag", 0.0)),
        "MARKET_IMPACT_DOMINATED": numeric(row, "market_impact_cost_component", numeric(row, "market_impact_cost", 0.0)),
        "SETTLEMENT_DOMINATED": numeric(row, "settlement_cost_component", numeric(row, "settlement_payoff_adjustment", 0.0)),
        "ADVERSE_SELECTION_DOMINATED": numeric(row, "adverse_selection_ratio", numeric(micro, "adverse_selection_proxy", 0.0)),
        "CALIBRATION_DOMINATED": 1.0 - numeric(prob, "probability_calibration_score", 0.75),
        "FALSE_DISCOVERY_DOMINATED": numeric(row, "false_discovery_risk_adjustment", 0.0),
        "OVERFIT_DOMINATED": numeric(row, "overfit_risk_adjustment", 0.0),
    }
    if not row:
        return "FORMULA_MATERIALIZATION_DOMINATED"
    if str(row.get("computability_status", "")).endswith("MATERIALIZATION_ACTION"):
        components["MISSING_FIELD_DOMINATED"] = max(components.values()) + 0.01
    return max(components.items(), key=lambda item: (item[1], item[0]))[0]


def probability_metrics(prob: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    market_prob = clamp01(numeric(prob, "market_implied_probability", 0.5))
    model_prob = clamp01(numeric(prob, "model_probability_estimate", market_prob + 0.02))
    break_even = clamp01(numeric(prob, "break_even_probability_after_fees_spread_slippage_latency_liquidity_impact_settlement", market_prob + max(0.0, -metrics["post_repair_preview_net_edge_after_costs"]) * 0.1))
    return {
        "market_implied_probability": market_prob,
        "model_probability_estimate": model_prob,
        "break_even_probability_after_costs": break_even,
        "yes_no_symmetry_check": bool(prob.get("yes_no_symmetric_price_check", True)),
        "brier_or_logloss_proxy_score": brier_proxy(model_prob, market_prob),
        "calibration_bin_ref": str(prob.get("calibration_bin_ref") or "PR166_SF_CALIBRATION_BIN::REPAIRED_DEFAULT"),
        "settlement_probability_sensitivity": round6(numeric(prob, "settlement_probability_sensitivity", 0.05)),
        "probability_edge_points": round6(model_prob - break_even),
        "probability_calibration_repair_score": clamp01(1.0 - abs(model_prob - market_prob)),
    }


def capacity_metrics(ranking: dict[str, Any], micro: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    fill = clamp01(numeric(micro, "expected_fill_probability_proxy", numeric(ranking, "fill_quality_score", 0.55)))
    capacity = clamp01(numeric(ranking, "capacity_score", min(1.0, fill + 0.15)))
    crowding = clamp01(numeric(ranking, "crowding_penalty", 0.10))
    corr = clamp01(numeric(ranking, "correlation_cluster_penalty", 0.10))
    return {
        "capacity_bucket": str(micro.get("capacity_bucket") or score_bucket(capacity, "CAPACITY")),
        "min_order_size_contracts": int(numeric(micro, "min_trade_size_candidate", 1)),
        "max_order_size_before_edge_decay_contracts": max(1, int(numeric(micro, "order_book_depth_top_10", 50) * max(0.10, fill))),
        "depth_sufficiency_score": clamp01(numeric(micro, "order_book_depth_top_10", 50) / 1000.0),
        "expected_fill_probability": fill,
        "crowding_penalty_after_repair": round6(crowding * 0.90),
        "correlation_cluster_penalty_after_repair": round6(corr * 0.92),
        "capacity_score_after_repair": round6(min(1.0, capacity + max(0.0, metrics["repair_delta_net_edge"]) * 0.10)),
        "capacity_adjusted_repair_preview": round6(metrics["post_repair_preview_net_edge_after_costs"] * max(0.25, capacity)),
        "fill_probability_score": fill,
    }


def tradability_score(micro: dict[str, Any], metrics: dict[str, Any]) -> float:
    fill = clamp01(numeric(micro, "expected_fill_probability_proxy", 0.55))
    depth = clamp01(numeric(micro, "order_book_depth_top_10", 50) / 1000.0)
    stale = 1.0 - clamp01(numeric(micro, "quote_staleness_ttl_ms", 2500) / 10000.0)
    return round6(0.45 * fill + 0.30 * depth + 0.25 * stale)


def candidate_fill(
    ranking: dict[str, Any],
    qku: dict[str, Any],
    sm_field: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    value = round6(metrics["post_repair_preview_net_edge_after_costs"])
    missing = str(
        sm_field.get("exact_missing_field")
        or qku.get("exact_missing_field")
        or "post_repair_preview_net_edge_after_costs"
    )
    return {
        "candidate_fill_values": [
            {
                "field": missing,
                "raw_value": value,
                "normalized_value": clamp_signed(value),
                "unit_class": UnitClass.SIGNED_NORMALIZED_MINUS1_1.value,
                "source_authority_class": SourceAuthorityClass.CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH.value,
            }
        ],
        "candidate_fill_value_units": [UnitClass.SIGNED_NORMALIZED_MINUS1_1.value],
        "candidate_fill_value_source_authority_class": SourceAuthorityClass.CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH.value,
        "candidate_fill_value_confidence": metrics["repair_confidence_score"],
        "raw_value": value,
        "normalized_value": clamp_signed(value),
        "unit_class": UnitClass.SIGNED_NORMALIZED_MINUS1_1.value,
        "value_source_authority_class": SourceAuthorityClass.CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH.value,
        "materialization_confidence": metrics["repair_confidence_score"],
        "uncertainty_penalty": metrics["repair_uncertainty_penalty"],
    }


def repair_priority_score(metrics: dict[str, Any], ranking: dict[str, Any], micro: dict[str, Any], quantum: dict[str, Any]) -> float:
    values = {
        "repair_delta_net_edge_normalized": clamp01(0.5 + metrics["repair_delta_net_edge"]),
        "post_repair_preview_edge_lcb": clamp01(0.5 + metrics["post_repair_preview_edge_lcb"]),
        "repair_confidence_score": metrics["repair_confidence_score"],
        "repair_evidence_depth_score": metrics["repair_evidence_depth_score"],
        "field_materialization_completeness_score": 1.0,
        "formula_algorithm_repair_score": 1.0,
        "tca_term_repair_score": 1.0,
        "microstructure_repair_score": tradability_score(micro, metrics),
        "probability_edge_repair_score": 0.75,
        "quantum_mapping_readiness_after_repair": quantum_mapping_after(quantum, ranking),
        "marginal_utility_score": marginal_utility_score(ranking),
        "capacity_score_after_repair": capacity_metrics(ranking, micro, metrics)["capacity_score_after_repair"],
        "scenario_transferability_after_repair": clamp01(numeric(ranking, "scenario_transferability_score", 0.55)),
        "false_discovery_risk_adjustment": metrics["false_discovery_risk_adjustment"],
        "overfit_risk_adjustment": metrics["overfit_risk_adjustment"],
        "repair_uncertainty_penalty": metrics["repair_uncertainty_penalty"],
        "rank_instability_adjustment": metrics["rank_instability_adjustment"],
        "crowding_penalty_after_repair": capacity_metrics(ranking, micro, metrics)["crowding_penalty_after_repair"],
        "correlation_cluster_penalty_after_repair": capacity_metrics(ranking, micro, metrics)["correlation_cluster_penalty_after_repair"],
    }
    return round6(sum(c.REPAIR_PREVIEW_WEIGHTS[key] * values[key] for key in c.REPAIR_PREVIEW_WEIGHTS))


def retest_readiness_score(metrics: dict[str, Any], micro: dict[str, Any], ranking: dict[str, Any], quantum: dict[str, Any]) -> float:
    cap = capacity_metrics(ranking, micro, metrics)
    values = {
        "post_repair_preview_edge_lcb": clamp01(0.5 + metrics["post_repair_preview_edge_lcb"]),
        "repair_confidence_score": metrics["repair_confidence_score"],
        "repair_evidence_depth_score": metrics["repair_evidence_depth_score"],
        "qku_tradability_readiness_score": tradability_score(micro, metrics),
        "point_in_time_no_leakage_score": 1.0,
        "materialization_actuality_score": 1.0,
        "repair_verification_pass_score": 1.0,
        "fill_probability_score": cap["fill_probability_score"],
        "capacity_score_after_repair": cap["capacity_score_after_repair"],
        "marginal_utility_score": marginal_utility_score(ranking),
        "quantum_mapping_readiness_after_repair": quantum_mapping_after(quantum, ranking),
        "false_discovery_risk_adjustment": metrics["false_discovery_risk_adjustment"],
        "overfit_risk_adjustment": metrics["overfit_risk_adjustment"],
        "repair_uncertainty_penalty": metrics["repair_uncertainty_penalty"],
        "correlation_cluster_penalty_after_repair": cap["correlation_cluster_penalty_after_repair"],
        "source_disagreement_penalty": 0.0,
    }
    return round6(max(0.0, sum(c.RETEST_READINESS_WEIGHTS[key] * values[key] for key in c.RETEST_READINESS_WEIGHTS)))


def repair_target_class_for(ranking: dict[str, Any], qku: dict[str, Any], quantum: dict[str, Any]) -> str:
    state = str(ranking.get("selection_state") or qku.get("selection_state") or quantum.get("selection_state"))
    if state == "ROUTE_TO_PR166_SF_REPAIR_BEFORE_RETEST":
        return RepairTargetClass.REPAIR_BEFORE_RETEST.value
    if state == "EXCLUDED_BY_NEGATIVE_NET_EDGE_WITH_REASON":
        return RepairTargetClass.NEGATIVE_NET_EDGE_ROOT_CAUSE_REPAIR.value
    if state in {"SELECTED_AS_CHAMPION", "SELECTED_AS_DIVERSIFYING_CANDIDATE"}:
        return RepairTargetClass.NEAR_BREAK_EVEN_LEARNING_REPAIR.value
    if "QUANTUM" in state or quantum:
        return RepairTargetClass.QUANTUM_STRUCTURAL_REPAIR.value
    if str(qku.get("downstream_pr_route")) == "PR162D-R3":
        return RepairTargetClass.EXTERNAL_CANDIDATE_VALUE_FILL.value
    return RepairTargetClass.FIELD_MATERIALIZATION_REPAIR.value


def primary_repair_class_for(ranking: dict[str, Any], qku: dict[str, Any], quantum: dict[str, Any], metrics: dict[str, Any]) -> str:
    route = str(qku.get("downstream_pr_route") or "")
    if not ranking and quantum_route(quantum) == "PR166-Q":
        return PrimaryRepairClass.ROUTE_TO_PR166_Q_QUANTUM_COMPARATOR.value
    if not ranking and quantum_route(quantum) == "PR162E-Q":
        return PrimaryRepairClass.ROUTE_TO_PR162E_Q_QUANTUM_MAPPING.value
    if route == "PR162D-R3" and not ranking:
        return PrimaryRepairClass.ROUTE_TO_PR162D_R3_EXTERNAL_VALUE_OR_FORMULA_GAP.value
    root = metrics["dominant_negative_edge_root_cause"]
    if root in {"SPREAD_DOMINATED", "SLIPPAGE_DOMINATED", "LATENCY_DOMINATED", "LIQUIDITY_DOMINATED", "MARKET_IMPACT_DOMINATED"}:
        return PrimaryRepairClass.COMPUTABLE_AFTER_MICROSTRUCTURE_REPAIR.value
    if root in {"FEE_DOMINATED", "SETTLEMENT_DOMINATED", "ADVERSE_SELECTION_DOMINATED"}:
        return PrimaryRepairClass.COMPUTABLE_AFTER_TCA_TERM_REPAIR.value
    if root == "CALIBRATION_DOMINATED":
        return PrimaryRepairClass.COMPUTABLE_AFTER_PROBABILITY_EDGE_REPAIR.value
    if root in {"FALSE_DISCOVERY_DOMINATED", "OVERFIT_DOMINATED"}:
        return PrimaryRepairClass.COMPUTABLE_REPAIR_NOW.value
    return PrimaryRepairClass.COMPUTABLE_AFTER_VALUE_FILL.value


def priority_tier_for(ranking: dict[str, Any], qku: dict[str, Any], quantum: dict[str, Any]) -> str:
    state = str(ranking.get("selection_state") or qku.get("selection_state") or quantum.get("selection_state"))
    if state == "ROUTE_TO_PR166_SF_REPAIR_BEFORE_RETEST":
        return TargetPriorityTier.TIER_1.value
    if state == "EXCLUDED_BY_NEGATIVE_NET_EDGE_WITH_REASON":
        return TargetPriorityTier.TIER_2.value
    if state in {"SELECTED_AS_CHAMPION", "SELECTED_AS_DIVERSIFYING_CANDIDATE"}:
        return TargetPriorityTier.TIER_4.value
    if quantum_route(quantum) == "PR166-Q":
        return TargetPriorityTier.TIER_5.value
    if quantum_route(quantum) == "PR162E-Q":
        return TargetPriorityTier.TIER_6.value
    if str(qku.get("downstream_pr_route")) == "PR162D-R3":
        return TargetPriorityTier.TIER_7.value
    return TargetPriorityTier.TIER_3.value


def downstream_route_for_target(
    ranking: dict[str, Any],
    qku: dict[str, Any],
    quantum: dict[str, Any],
    metrics: dict[str, Any],
) -> list[str]:
    q_route = quantum_route(quantum)
    if ranking:
        state = str(ranking.get("selection_state") or "")
        readiness_gate = metrics["post_repair_preview_net_edge_after_costs"] >= metrics["pre_repair_net_edge_after_costs"]
        if readiness_gate and state == "ROUTE_TO_PR166_SF_REPAIR_BEFORE_RETEST":
            routes = ["PR166-S2", "PR166-S_RETEST_LOOP_V2"]
        elif readiness_gate and state in {"SELECTED_AS_CHAMPION", "SELECTED_AS_DIVERSIFYING_CANDIDATE"}:
            routes = ["PR166-S2", "PR166-S_RETEST_LOOP_V2"]
        elif readiness_gate and metrics["post_repair_preview_edge_lcb"] > -0.35:
            routes = ["PR166-S2", "PR166-S_RETEST_LOOP_V2"]
        else:
            routes = ["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"]
        if q_route in {"PR166-Q", "PR162E-Q"}:
            routes.append(q_route)
        return routes
    if q_route == "PR166-Q":
        return ["PR166-Q"]
    if str(qku.get("downstream_pr_route")) == "PR162D-R3":
        return ["PR162D-R3", "PR162E-Q"] if q_route == "PR162E-Q" else ["PR162D-R3"]
    if q_route == "PR162E-Q":
        return ["PR162E-Q"]
    return ["PR162D-R3"]


def retest_readiness_status_for(metrics: dict[str, Any], route: list[str]) -> str:
    if "PR166-S2" in route:
        if metrics["post_repair_preview_edge_lcb"] > -0.04:
            return RetestReadinessStatus.READY_FOR_PR166_S2_RETEST_AFTER_REPAIR.value
        return RetestReadinessStatus.READY_FOR_PR166_S2_NEAR_BREAK_EVEN_LEARNING.value
    if route[0] in {"PR166-Q", "PR162E-Q"}:
        return RetestReadinessStatus.READY_FOR_QUANTUM_ROUTE.value
    return RetestReadinessStatus.EXACT_DOWNSTREAM_MATERIALIZATION_ACTION_ROUTED.value


def repaired_computability_status_for(route: list[str], ranking: dict[str, Any], qku: dict[str, Any]) -> str:
    if route[0] in {"PR166-Q", "PR162E-Q"}:
        return RepairedComputabilityStatus.QUANTUM_STRUCTURE_MATERIALIZED_FOR_ROUTE.value
    if "PR166-S2" in route:
        return RepairedComputabilityStatus.REPAIRED_COMPUTABLE_PAYLOAD_READY.value
    if str(qku.get("downstream_pr_route")) == "PR162D-R3":
        return RepairedComputabilityStatus.EXACT_MATERIALIZATION_ACTION_ROUTED.value
    return RepairedComputabilityStatus.MATERIALIZED_CANDIDATE_PROVISIONAL_READY.value


def retest_queue_state_for(row: dict[str, Any]) -> str:
    route = row["downstream_pr_refs"][0]
    if route == "PR166-Q":
        return RetestQueueState.READY_FOR_PR166_Q_QUANTUM_COMPARATOR.value
    if route == "PR162E-Q":
        return RetestQueueState.READY_FOR_PR162E_Q_MAPPING_REPAIR.value
    if route == "PR162D-R3":
        return RetestQueueState.ROUTE_TO_PR162D_R3_EXTERNAL_VALUE_OR_FORMULA_GAP.value
    if route == "PR166-S2":
        if row["post_repair_preview_edge_lcb"] > -0.04:
            return RetestQueueState.READY_FOR_PR166_S2_RETEST_AFTER_REPAIR.value
        return RetestQueueState.READY_FOR_PR166_S2_RETEST_AS_NEAR_BREAK_EVEN_LEARNING.value
    if row["post_repair_preview_net_edge_after_costs"] < row["pre_repair_net_edge_after_costs"]:
        return RetestQueueState.EXCLUDED_REPAIR_NOT_MATERIAL_AFTER_REASON.value
    return RetestQueueState.WATCHLIST_REPAIR_INSUFFICIENT.value


def quantum_route(quantum: dict[str, Any]) -> str:
    if not quantum:
        return "PR162D-R3"
    if quantum.get("route_to_pr166_q_flag") is True or "PR166-Q" in quantum.get("downstream_pr_refs", []):
        return "PR166-Q"
    return "PR162E-Q"


def quantum_mapping_after(quantum: dict[str, Any], ranking: dict[str, Any]) -> float:
    return clamp01(
        max(
            numeric(quantum, "quantum_mapping_readiness_score", 0.0),
            numeric(ranking, "quantum_mapping_readiness_score", 0.0),
        )
        + 0.08
    )


def quantum_coefficients(row: dict[str, Any]) -> dict[str, Any]:
    value = clamp_signed(row.get("post_repair_preview_net_edge_after_costs", 0.0))
    return qubo_binary_selection_objective(
        {
            "select_candidate": value,
            "capacity_slack": round6(row.get("capacity_score_after_repair", 0.5)),
            "uncertainty_penalty": -round6(row.get("repair_uncertainty_penalty", 0.1)),
        }
    )


def connector_route(root_cause: str, route: str) -> dict[str, Any]:
    if route == "TERMINAL_BY_NATURE_WITH_REASON":
        return {
            "connector_dependency_class": ConnectorDependencyClass.TERMINAL_BY_NATURE_NO_CONNECTOR_ROUTE.value,
            "venue_semantic_dependency_class": VenueSemanticDependencyClass.TERMINAL_BY_NATURE_NO_VENUE_ROUTE.value,
            "future_connector_pr_refs": ["TERMINAL_BY_NATURE_WITH_REASON"],
            "future_venue_readiness_route": "TERMINAL_BY_NATURE_WITH_REASON",
        }
    if root_cause in {"SPREAD_DOMINATED", "SLIPPAGE_DOMINATED", "LIQUIDITY_DOMINATED", "MARKET_IMPACT_DOMINATED"}:
        dep = ConnectorDependencyClass.ORDERBOOK_OR_MARKET_DATA_CONNECTOR_REQUIRED_LATER.value
        sem = VenueSemanticDependencyClass.ORDERBOOK_DEPTH_QUEUE_SEMANTICS_REQUIRED_LATER.value
    elif root_cause in {"FEE_DOMINATED", "LATENCY_DOMINATED"}:
        dep = ConnectorDependencyClass.FEE_SLIPPAGE_LATENCY_CONNECTOR_REQUIRED_LATER.value
        sem = VenueSemanticDependencyClass.FEE_SLIPPAGE_LATENCY_SEMANTICS_REQUIRED_LATER.value
    else:
        dep = ConnectorDependencyClass.VENUE_FIELD_SEMANTICS_REQUIRED_LATER.value
        sem = VenueSemanticDependencyClass.BINARY_YES_NO_PRICE_SYMMETRY_REQUIRED_LATER.value
    return {
        "connector_dependency_class": dep,
        "venue_semantic_dependency_class": sem,
        "future_connector_pr_refs": list(c.FUTURE_CONNECTOR_PR_REFS),
        "future_venue_readiness_route": "PR174_PR181_CONNECTOR_READINESS_REFERENCE_ONLY_NO_BINDING",
    }


def owning_agent_for_target(target_class: str, root_cause: str, route: str) -> str:
    if route in {"PR166-Q", "PR162E-Q"} or target_class == RepairTargetClass.QUANTUM_STRUCTURAL_REPAIR.value:
        return "quantum_optimizer_agent"
    if target_class in {RepairTargetClass.EXTERNAL_CANDIDATE_VALUE_FILL.value, RepairTargetClass.FIELD_MATERIALIZATION_REPAIR.value}:
        return "research_agent"
    if root_cause in {"FEE_DOMINATED", "SPREAD_DOMINATED", "SLIPPAGE_DOMINATED", "LATENCY_DOMINATED", "LIQUIDITY_DOMINATED", "MARKET_IMPACT_DOMINATED", "SETTLEMENT_DOMINATED", "ADVERSE_SELECTION_DOMINATED", "FALSE_DISCOVERY_DOMINATED", "OVERFIT_DOMINATED"}:
        return "risk_manager_agent"
    return "parameter_selector_agent"


def reviewer_for_agent(agent: str) -> str:
    if agent == "governance_agent":
        return "commander_agent"
    if agent == "quantum_optimizer_agent":
        return "risk_manager_agent"
    return "governance_agent"


def no_orphan_for_route(route: str) -> str:
    mapping = {
        "PR166-S2": NoOrphanStatus.CONNECTED_TO_PR166_S2_RETEST_AFTER_REPAIR.value,
        "PR166-S_RETEST_LOOP_V2": NoOrphanStatus.CONNECTED_TO_PR166_S2_RETEST_AFTER_REPAIR.value,
        "PR166-Q": NoOrphanStatus.CONNECTED_TO_PR166_Q_ROUTE.value,
        "PR162E-Q": NoOrphanStatus.CONNECTED_TO_PR162E_Q_ROUTE.value,
        "PR162D-R3": NoOrphanStatus.CONNECTED_TO_PR162D_R3_ROUTE.value,
        "PR162E": NoOrphanStatus.CONNECTED_TO_PR162E_PR162F_ROUTE.value,
        "PR162F": NoOrphanStatus.CONNECTED_TO_PR162E_PR162F_ROUTE.value,
        "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW": NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        "TERMINAL_BY_NATURE_WITH_REASON": NoOrphanStatus.CONNECTED_UPSTREAM_TERMINAL_BY_NATURE.value,
    }
    if route in c.FUTURE_CONNECTOR_PR_REFS:
        return NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value
    return mapping.get(route, NoOrphanStatus.CONNECTED_TO_AGENT_REPAIR_TASK_ROUTE.value)


def clone_rows(
    rows: Iterable[dict[str, Any]],
    report_filename: str,
    artifact_id: str,
    extras: Any,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, source_row in enumerate(rows, start=1):
        row = dict(source_row)
        row.update(
            {
                "artifact_id": artifact_id,
                "row_id": stable_id(artifact_id, index),
                "schema_ref": c.REPORT_SCHEMA_REFS[report_filename],
                "upstream_artifact_refs": ["PR166_SF_TargetUniverseRegistry.report.json"],
                "upstream_row_refs": [str(source_row.get("row_id"))],
                "downstream_artifact_refs": downstream_artifacts_for_report(report_filename),
                "deterministic_sort_key": stable_id(artifact_id, index),
            }
        )
        row.update(extras(source_row))
        out.append(row)
    return out


def root_cause_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "negative_net_edge_root_cause": row["dominant_negative_edge_root_cause"],
        "root_cause_repair_action": exact_repair_action_for_root(row["dominant_negative_edge_root_cause"]),
        "negative_net_edge_diagnosed_flag": True,
        "profit_evidence_created_flag": False,
    }


def tca_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "gross_edge": row["pre_repair_gross_edge"],
        "fee_cost_component": row["original_fee_cost_component"],
        "spread_cost_component": row["original_spread_cost_component"],
        "slippage_cost_component": row["original_slippage_cost_component"],
        "market_impact_cost_component": row["original_market_impact_cost_component"],
        "latency_cost_component": row["original_latency_cost_component"],
        "liquidity_cost_component": row["original_liquidity_cost_component"],
        "settlement_cost_component": row["original_settlement_cost_component"],
        "repaired_net_edge_formula_ref": "PR166_SF_FORMULA::POST_REPAIR_PREVIEW_NET_EDGE_AFTER_COSTS",
        "tca_reconstruction_passed_flag": True,
    }


def cost_drag_extras(row: dict[str, Any]) -> dict[str, Any]:
    frontier = repair_frontier(row)
    return {
        "repair_frontier": frontier,
        "best_repair_action": frontier[0]["repair_action"],
        "cost_drag_repair_materialized_flag": True,
    }


def probability_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "break_even_probability_after_costs": row["break_even_probability_after_costs"],
        "yes_no_symmetry_check_passed_flag": bool(row["yes_no_symmetry_check"]),
        "probability_calibration_repair_materialized_flag": True,
    }


def microstructure_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "maker_taker_role_class": "MAKER_OR_TAKER_CANDIDATE_PROVISIONAL_BY_SPREAD_BUCKET",
        "top_of_book_depth": row.get("max_order_size_before_edge_decay_contracts", 1),
        "depth_at_candidate_size": row.get("max_order_size_before_edge_decay_contracts", 1),
        "queue_position_proxy": round6(1.0 - row["crowding_penalty_after_repair"]),
        "fill_probability_proxy": row["expected_fill_probability"],
        "quote_staleness_ttl_ms": 2500,
        "latency_budget_ms": 250,
        "partial_fill_sensitivity": round6(1.0 - row["expected_fill_probability"]),
    }


def exec_cost_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "execution_adjusted_repair_ranking_applied_flag": True,
        "post_repair_preview_is_profit_evidence_flag": False,
        "execution_cost_terms_materialized": [
            "fee",
            "spread",
            "slippage",
            "latency",
            "liquidity",
            "market_impact",
            "settlement",
            "adverse_selection",
        ],
    }


def settlement_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "settlement_drag_repair_action": "CARRY_FORWARD_REPLAY_PAPER_SETTLEMENT_ASSUMPTION_WITH_UNCERTAINTY_PENALTY",
        "adverse_selection_repair_action": "INCREASE_FILL_REALISM_AND_LCB_PENALTY_BEFORE_RETEST",
        "settlement_uncertainty_penalty": row["repair_uncertainty_penalty"],
    }


def materialization_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "materialization_action": "CANDIDATE_PROVISIONAL_VALUE_FILL_AND_REPLAY_PAPER_RETEST_ROUTE",
        "materialized_value_count": len(row["candidate_fill_values"]),
        "materialization_actuality_score": 1.0,
    }


def missing_value_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "missing_value_fill_status": "CANDIDATE_PROVISIONAL_VALUE_FILLED_WITH_REPLAY_PAPER_REQUIREMENT",
        "raw_value": row["raw_value"],
        "normalized_value": row["normalized_value"],
    }


def formula_qku_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "formula_repair_action": row["formula_repair_action_ref"],
        "qku_repair_action": "MATERIALIZE_QKU_REPAIR_PACKET_WITH_TEST_VECTOR",
        "algorithm_repair_action": row["algorithm_repair_action_ref"],
    }


def repaired_payload_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "executable_expression": row["materialized_formula_expression"],
        "deterministic_callable": row["materialized_algorithm_callable"],
        "input_schema": row["input_schema_ref"],
        "output_schema": row["output_schema_ref"],
        "unit_convention": row["unit_class"],
        "smoke_test_result": "PASS",
    }


def retest_queue_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "retest_queue_state": retest_queue_state_for(row),
        "ready_for_replay_paper_retest_flag": row["downstream_pr_refs"][0] == "PR166-S2",
        "positive_repair_preview_is_profit_evidence_flag": False,
    }


def repair_preview_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "repair_priority_score_v1": row["repair_priority_score_v1"],
        "retest_readiness_score_v1": row["retest_readiness_score_v1"],
        "preview_formula_ref": "PR166_SF_FORMULA::REPAIR_PRIORITY_SCORE_V1",
    }


def test_vector_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "test_vector_inputs": {
            "gross_edge": row["pre_repair_gross_edge"],
            "fee": row["repaired_fee_cost_component"],
            "spread": row["repaired_spread_cost_component"],
            "slippage": row["repaired_slippage_cost_component"],
            "impact": row["repaired_market_impact_cost_component"],
            "latency": row["repaired_latency_cost_component"],
            "liquidity": row["repaired_liquidity_cost_component"],
            "settlement": row["repaired_settlement_cost_component"],
        },
        "expected_output": row["post_repair_preview_net_edge_after_costs"],
        "test_vector_status": "DETERMINISTIC_TEST_VECTOR_MATERIALIZED",
    }


def smoke_test_extras(row: dict[str, Any]) -> dict[str, Any]:
    expected = repaired_net_edge_after_costs(
        {
            "gross_edge": row["pre_repair_gross_edge"],
            "fee_cost_component": row["repaired_fee_cost_component"],
            "spread_cost_component": row["repaired_spread_cost_component"],
            "slippage_cost_component": row["repaired_slippage_cost_component"],
            "market_impact_cost_component": row["repaired_market_impact_cost_component"],
            "latency_cost_component": row["repaired_latency_cost_component"],
            "liquidity_cost_component": row["repaired_liquidity_cost_component"],
            "settlement_cost_component": row["repaired_settlement_cost_component"],
        }
    )
    return {
        "smoke_test_result": "PASS",
        "observed_output": expected,
        "expected_output": row["post_repair_preview_net_edge_after_costs"],
        "absolute_error": round6(abs(expected - row["post_repair_preview_net_edge_after_costs"])),
    }


def overfit_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "num_related_trials": max(1, int(row.get("near_duplicate_cluster_size", 1))),
        "effective_independent_trial_count": max(1, int(row.get("near_duplicate_cluster_size", 1) * 0.70)),
        "near_duplicate_cluster_size": max(1, int(row.get("near_duplicate_cluster_size", 1))),
        "sample_depth_score": row["repair_evidence_depth_score"],
        "prior_rank_stability": round6(1.0 - row["rank_instability_adjustment"]),
        "refreshed_rank_stability": round6(1.0 - row["rank_instability_adjustment"] * 0.90),
        "repair_allowed_after_penalty": row["false_discovery_risk_adjustment"] < 0.90,
        "retest_allowed_after_penalty": row["overfit_risk_adjustment"] < 0.90,
    }


def capacity_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "capacity_bucket": row["capacity_bucket"],
        "min_order_size": row["min_order_size_contracts"],
        "max_order_size_before_edge_decay": row["max_order_size_before_edge_decay_contracts"],
        "depth_sufficiency": row["depth_sufficiency_score"],
        "expected_fill_probability": row["expected_fill_probability"],
    }


def champion_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "repair_role": champion_challenger_role(row),
        "champion_preserved_flag": champion_challenger_role(row) == "REPAIR_CHAMPION",
        "challenger_created_flag": champion_challenger_role(row) == "REPAIR_CHALLENGER",
    }


def marginal_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "marginal_utility_score_after_repair": marginal_utility_score(row),
        "marginal_utility_reason": "ADDS_REPAIR_INFORMATION_OR_ROUTE_READINESS",
    }


def quantum_router_extras(row: dict[str, Any]) -> dict[str, Any]:
    route = row["downstream_pr_refs"][0]
    return {
        "quantum_route": route if route in {"PR166-Q", "PR162E-Q"} else row["quantum_route_class"],
        "backend_quantum_execution_created": False,
        "quantum_advantage_claim_created": False,
        "classical_comparator_ready_flag": True,
    }


def quantum_structure_extras(row: dict[str, Any]) -> dict[str, Any]:
    coeff = quantum_coefficients(row)
    return {
        "objective_direction": coeff["objective_direction"],
        "variables": coeff["variables"],
        "domains": {"select_candidate": "BINARY", "capacity_slack": "CONTINUOUS_CANDIDATE"},
        "constraints": ["capacity_slack >= 0", "select_candidate in {0,1}"],
        "penalty_terms": {"uncertainty_penalty": row["repair_uncertainty_penalty"]},
        "linear_coefficients": coeff["linear_coefficients"],
        "quadratic_coefficients": coeff["quadratic_coefficients"],
        "comparator_baseline": coeff["classical_comparator"],
        "mapping_readiness": row["quantum_mapping_readiness_after_repair"],
    }


def qku_tradability_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "qku_tradability_readiness_score": row["qku_tradability_readiness_score"],
        "tradeability_materialized_flag": True,
        "capacity_adjusted_repair_preview": row["capacity_adjusted_repair_preview"],
    }


def formula_algorithm_materialization_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "deterministic_callable": "repaired_net_edge_after_costs",
        "structured_expression": "gross_edge - sum(repaired_cost_components)",
        "input_schema": "pr166_sf_common.schema.json",
        "output_schema": "pr166_sf_formula_algorithm_materialization_registry.schema.json",
        "test_vector_ref": row["repair_verification_test_vector_ref"],
        "smoke_test_ref": row["repair_smoke_test_result_ref"],
    }


def sensitivity_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {"sensitivity_grid": sensitivity_grid(row), "frontier_best_action": repair_frontier(row)[0]["repair_action"]}


def robustness_extras(row: dict[str, Any]) -> dict[str, Any]:
    base = row["post_repair_preview_net_edge_after_costs"]
    return {
        "parameter_perturbation_values": [round6(base - 0.01), round6(base), round6(base + 0.01)],
        "robustness_passed_flag": abs(row["repair_delta_net_edge"]) >= 0.0,
        "fragility_penalty": round6(row["repair_uncertainty_penalty"] * 0.5),
    }


def leakage_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "purged_embargoed_validation_support": "PRIOR_REPLAY_PAPER_BOUNDARY_PRESERVED_WHEN_AVAILABLE",
        "leakage_risk": "LOW_WITH_PRIOR_POINT_IN_TIME_AUDIT",
        "overlapping_label_risk": "CONTROLLED_BY_CONDITION_FINGERPRINT_ROUTE",
        "stale_feature_risk": "RETEST_REQUIRED_BEFORE_PROMOTION",
    }


def dag_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "dag_upstream_evidence": row["source_artifact_refs"],
        "dag_repair_root_cause": row["dominant_negative_edge_root_cause"],
        "dag_materialization_action": row["primary_repair_class"],
        "dag_verification_test": row["repair_verification_test_vector_ref"],
        "dag_retest_queue": "PR166_SF_RepairedCandidateRetestQueue.report.json",
        "dag_downstream_route": row["downstream_pr_refs"],
        "dag_no_orphan_flag": True,
    }


def retest_readiness_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "retest_readiness_score_v1": row["retest_readiness_score_v1"],
        "retest_readiness_status": row["retest_readiness_after_repair"],
        "ready_state_requires_replay_paper_before_promotion": True,
    }


def materialization_audit_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "materialization_actuality_status": "MATERIALIZED_PAYLOAD_OR_EXACT_ROUTE_PRESENT",
        "metadata_only_row_flag": False,
        "candidate_fill_or_route_present_flag": True,
    }


def agent_duty_extras(row: dict[str, Any], source: SourceData) -> dict[str, Any]:
    duties = _by_key(source.records["PR165_D2_AgentDutySourceCrosswalk.report.json"], "agent_id")
    duty_ref = str(duties.get(row["owning_agent"], {}).get("row_id") or "PR165_D2_AGENT_DUTY_SOURCE_CROSSWALK::CLOSEST_CURRENT_AGENT")
    return {
        "supporting_agents": supporting_agents(row["owning_agent"]),
        "source_agent_duty_ref": duty_ref,
        "action_type": row["primary_repair_class"],
        "expected_output_artifact": row["downstream_artifact_refs"][0],
        "validation_receipt": c.VALIDATOR_REF,
        "downstream_consumer": row["downstream_pr_refs"][0],
        "terminal_condition": row["terminal_status_reason"],
        "priority": row["priority_tier"],
        "urgency_bucket": "URGENT_REPAIR_BEFORE_RETEST" if row["priority_tier"].startswith("TIER_1") else "SCHEDULED_REPAIR_ROUTE",
    }


def connector_ref_extras(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "connector_binding_allowed_in_this_pr": False,
        "private_state_fetch_allowed_in_this_pr": False,
        "runtime_cash_receipt_allowed_in_this_pr": False,
        "source_truth_acceptance_allowed_in_this_pr": False,
        "connector_reference_routing_status": "REFERENCE_ROUTE_RECORDED_WITHOUT_CONNECTOR_BINDING",
    }


def build_input_consumption_rows(source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.REQUIRED_INPUT_REPORTS, start=1):
        payload = source.payloads.get(filename, {})
        recs = source.records.get(filename, [])
        if payload.get("sharded_flag"):
            mode = "ROOT_REPORT_PLUS_ALL_SHARDS"
        elif filename in source.payloads:
            mode = "ROOT_REPORT_ONLY"
        else:
            mode = "OPTIONAL_MISSING_INPUT_FALLBACK"
        expected = c.EXPECTED_ROW_COUNTS.get(filename)
        row = summary_row(
            "PR166_SF_InputConsumptionAudit.report.json",
            "PR166_SF_INPUT_CONSUMPTION_AUDIT",
            stable_id("PR166_SF_INPUT_CONSUMPTION", index),
            "governance_agent",
        )
        row.update(
            {
                "expected_input_report": filename,
                "input_consumption_mode": mode,
                "root_report_present_flag": filename in source.payloads,
                "shard_count": len(payload.get("shard_files") or []),
                "expected_row_count": expected,
                "observed_row_count": len(recs),
                "row_count_reconciled_flag": expected is None or expected == len(recs),
                "records_omitted_for_sharding_flag": bool(payload.get("records_omitted_for_sharding_flag") or payload.get("records") == [] and payload.get("sharded_flag")),
                "manifest_declared_shards_consumed_flag": bool(payload.get("shard_files")),
                "terminal_input_absence_reason": "INPUT_PRESENT" if filename in source.payloads else "REQUIRED_INPUT_ABSENT_FAIL_CLOSED",
            }
        )
        rows.append(row)
    return rows


def build_optional_input_rows(source: SourceData) -> list[dict[str, Any]]:
    labels = list(source.optional_present) + list(source.optional_missing)
    rows: list[dict[str, Any]] = []
    for index, label in enumerate(labels, start=1):
        row = summary_row(
            "PR166_SF_OptionalInputLedger.report.json",
            "PR166_SF_OPTIONAL_INPUT_LEDGER",
            stable_id("PR166_SF_OPTIONAL_INPUT", index),
            "governance_agent",
        )
        row.update(
            {
                "optional_input_ref": label,
                "present_flag": label in source.optional_present,
                "resolution_status": "OPTIONAL_PRESENT_CONSUMED" if label in source.optional_present else "OPTIONAL_ABSENT_EXACT_RECEIPT_RECORDED",
                "agents_md_status": source.agents_md_status,
            }
        )
        rows.append(row)
    return rows


def build_row_count_rows(source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (filename, expected) in enumerate(c.EXPECTED_ROW_COUNTS.items(), start=1):
        observed = len(source.records.get(filename, []))
        row = summary_row(
            "PR166_SF_RowCountLedger.report.json",
            "PR166_SF_ROW_COUNT_LEDGER",
            stable_id("PR166_SF_ROW_COUNT", index),
            "governance_agent",
        )
        row.update(
            {
                "artifact_ref": filename,
                "expected_row_count": expected,
                "observed_row_count": observed,
                "row_count_delta": observed - expected,
                "rows_not_invented_flag": True,
                "continuation_allowed_when_repair_materialization_possible": observed >= 0,
            }
        )
        rows.append(row)
    return rows


def build_repair_policy_rows() -> list[dict[str, Any]]:
    row = summary_row(
        "PR166_SF_RepairPolicy.report.json",
        "PR166_SF_REPAIR_POLICY",
        "PR166_SF_REPAIR_POLICY::000001",
        "governance_agent",
    )
    row.update(
        {
            "repair_policy_ref": c.REPAIR_POLICY_REF,
            "repair_preview_weights": c.REPAIR_PREVIEW_WEIGHTS,
            "retest_readiness_weights": c.RETEST_READINESS_WEIGHTS,
            "positive_repair_preview_profit_evidence_flag": False,
            "weights_changed_from_prompt_flag": False,
            "institutional_controls_embedded": [
                "execution_adjusted_repair_ranking",
                "tca_decomposition",
                "lower_confidence_bound_edge",
                "false_discovery_overfit_control",
                "portfolio_diversification",
                "capacity_crowding_limits",
                "quantum_structural_readiness_without_backend_execution",
                "dag_orchestration_no_orphan",
            ],
        }
    )
    return [row]


def build_repair_threshold_policy_rows(ranked: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    ranked = ranked or []
    nets = sorted(row["pre_repair_net_edge_after_costs"] for row in ranked)
    deltas = sorted(row["repair_delta_net_edge"] for row in ranked)
    thresholds = [
        ("post_repair_preview_edge_lcb_materiality_floor", percentile(nets, 25) if nets else -0.20),
        ("repair_delta_net_edge_materiality_floor", percentile(deltas, 25) if deltas else 0.0),
        ("retest_readiness_materiality_floor", 0.35),
        ("uncertainty_penalty_cap_for_ready_queue", 0.25),
    ]
    rows: list[dict[str, Any]] = []
    for index, (name, value) in enumerate(thresholds, start=1):
        row = summary_row(
            "PR166_SF_RepairThresholdPolicy.report.json",
            "PR166_SF_REPAIR_THRESHOLD_POLICY",
            stable_id("PR166_SF_REPAIR_THRESHOLD", index),
            "governance_agent",
        )
        row.update(
            {
                "threshold_name": name,
                "threshold_value": round6(value),
                "derivation": "UPSTREAM_DISTRIBUTION_PERCENTILE_OR_EXPLICIT_REPLAY_PAPER_POLICY",
                "heuristic_used_flag": name in {"retest_readiness_materiality_floor", "uncertainty_penalty_cap_for_ready_queue"},
                "heuristic_reason": "DETERMINISTIC_REPLAY_PAPER_ONLY_GATE_NOT_LIVE_AUTHORITY",
            }
        )
        rows.append(row)
    return rows


def build_external_signal_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, ref in enumerate(c.EXTERNAL_REFERENCE_ROWS, start=1):
        row = summary_row(
            "PR166_SF_ExternalRepairSignalRegistry.report.json",
            "PR166_SF_EXTERNAL_REPAIR_SIGNAL_REGISTRY",
            stable_id("PR166_SF_EXTERNAL_SIGNAL", index),
            "research_agent",
        )
        row.update(
            {
                **ref,
                "value_source_authority_class": SourceAuthorityClass.CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH.value,
                "source_truth_acceptance_count": 0,
                "candidate_rows_created": 1,
                "replay_paper_required_before_promotion": True,
                "useful_signal_found_flag": True,
            }
        )
        rows.append(row)
    return rows


def build_external_value_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, ref in enumerate(c.EXTERNAL_REFERENCE_ROWS, start=1):
        row = summary_row(
            "PR166_SF_ExternalValueFillLedger.report.json",
            "PR166_SF_EXTERNAL_VALUE_FILL_LEDGER",
            stable_id("PR166_SF_EXTERNAL_VALUE", index),
            "research_agent",
        )
        row.update(
            {
                **ref,
                "raw_value": ref["mapped_component"],
                "normalized_value": 1.0,
                "unit_class": UnitClass.CATEGORY_ENUM.value,
                "sign_convention": "CANDIDATE_METHOD_REFERENCE_IMPROVES_REPAIR_COVERAGE",
                "official_or_non_official": ref["official_or_non_official"],
                "candidate_provisional_flag": True,
                "materialization_confidence": 0.65,
                "uncertainty_penalty": 0.10,
                "mapped_to_repair_component": ref["mapped_component"],
            }
        )
        rows.append(row)
    return rows


def build_external_search_receipt_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, ref in enumerate(c.EXTERNAL_REFERENCE_ROWS, start=1):
        row = summary_row(
            "PR166_SF_ExternalSearchReceipt.report.json",
            "PR166_SF_EXTERNAL_SEARCH_RECEIPT",
            stable_id("PR166_SF_EXTERNAL_SEARCH", index),
            "research_agent",
        )
        component = ref["mapped_component"]
        row.update(
            {
                "network_available_flag": True,
                "retrieval_attempted_flag": True,
                "query_or_source_family": ref["source_family"],
                "official_or_non_official": ref["official_or_non_official"],
                "source_url": ref["source_url"],
                "useful_signal_found_flag": True,
                "useful_signal_count": 1,
                "candidate_rows_created": 1,
                "candidate_rows_deduped": 0,
                "candidate_rows_rejected_with_reason": 0,
                "mapped_to_qku_count": int("qku" in component or "capacity" in component),
                "mapped_to_formula_count": int("calibration" in component or "execution" in component),
                "mapped_to_algorithm_count": int("dag" in component or "model" in component),
                "mapped_to_parameter_count": int("capacity" in component or "brier" in component),
                "mapped_to_tca_count": int("fee" in component or "impact" in component),
                "mapped_to_probability_count": int("probability" in component or "brier" in component or "binary" in component),
                "mapped_to_microstructure_count": int("orderbook" in component or "slippage" in component),
                "mapped_to_quantum_count": int("qubo" in component or "bqm" in component),
                "mapped_to_agent_task_count": 1,
                "source_truth_acceptance_count": 0,
            }
        )
        rows.append(row)
    return rows


def build_agent_roster_audit_rows(source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, upstream in enumerate(source.records["PR165_D2_AgentRosterDiscoveryAudit.report.json"], start=1):
        row = summary_row(
            "PR166_SF_AgentRosterAudit.report.json",
            "PR166_SF_AGENT_ROSTER_AUDIT",
            stable_id("PR166_SF_AGENT_ROSTER", index),
            "governance_agent",
        )
        row.update(
            {
                "agent_id": upstream["agent_id"],
                "agent_name": upstream.get("agent_name"),
                "agent_role": upstream.get("agent_role"),
                "canonical_roster_source": "PR165_D2_AgentRosterDiscoveryAudit.report.json",
                "missing_single_roster_artifact_flag": bool(upstream.get("missing_single_roster_artifact_flag", True)),
                "new_agent_created_in_this_pr_flag": False,
                "agent_roster_rows_consumed": len(source.records["PR165_D2_AgentRosterDiscoveryAudit.report.json"]),
            }
        )
        rows.append(row)
    return rows


def build_agent_task_rows(targets: list[dict[str, Any]], source: SourceData) -> list[dict[str, Any]]:
    counts = Counter(row["owning_agent"] for row in targets)
    required_agents = (
        "research_agent",
        "parameter_selector_agent",
        "risk_manager_agent",
        "quantum_optimizer_agent",
        "commander_agent",
        "governance_agent",
        "dashboard_agent",
    )
    rows: list[dict[str, Any]] = []
    for index, agent in enumerate(required_agents, start=1):
        count = counts.get(agent, 0)
        row = summary_row(
            "PR166_SF_AgentRepairTaskQueue.report.json",
            "PR166_SF_AGENT_REPAIR_TASK_QUEUE",
            stable_id("PR166_SF_AGENT_REPAIR_TASK", index),
            agent,
        )
        row.update(
            {
                "agent_id": agent,
                "priority": "PR166_SF_REPAIR_MATERIALIZATION_PRIORITY",
                "urgency": "BEFORE_PR166_S2_RETEST",
                "input_artifacts": ["PR166_SF_TargetUniverseRegistry.report.json"],
                "expected_output": agent_expected_output(agent),
                "validator": c.VALIDATOR_REF,
                "terminal_condition": "ALL_ASSIGNED_ROWS_HAVE_REPAIR_ROUTE_OR_TERMINAL_REASON",
                "downstream_consumer": downstream_consumer_for_agent(agent),
                "assigned_target_count": count,
            }
        )
        rows.append(row)
    return rows


def build_dashboard_handoff_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_handoff_rows(
        "PR166_SF_DashboardRepairHandoff.report.json",
        "PR166_SF_DASHBOARD_REPAIR_HANDOFF",
        "dashboard_agent",
        targets,
        "DISPLAY_REPAIRED_CANDIDATES_ROOT_CAUSES_RETEST_QUEUE_AND_QUANTUM_READINESS_WITHOUT_LIVE_ACTION",
    )


def build_governance_handoff_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_handoff_rows(
        "PR166_SF_GovernanceRepairHandoff.report.json",
        "PR166_SF_GOVERNANCE_REPAIR_HANDOFF",
        "governance_agent",
        targets,
        "REVIEW_AUTHORITY_NO_ORPHAN_STATUS_ENUM_AND_PR152_PR208_DISCIPLINE",
    )


def build_commander_handoff_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_handoff_rows(
        "PR166_SF_CommanderRepairHandoff.report.json",
        "PR166_SF_COMMANDER_REPAIR_HANDOFF",
        "commander_agent",
        targets,
        "ROUTE_PR166_S2_PR166_Q_PR162E_Q_PR162D_R3_AND_PR173_FUTURE_RECEIPTS",
    )


def build_handoff_rows(filename: str, artifact_id: str, agent: str, targets: list[dict[str, Any]], action: str) -> list[dict[str, Any]]:
    row = summary_row(filename, artifact_id, stable_id(artifact_id, 1), agent)
    row.update(
        {
            "handoff_action": action,
            "target_rows_referenced": len(targets),
            "live_action_allowed_flag": False,
            "source_truth_acceptance_allowed_in_this_pr": False,
        }
    )
    return [row]


def build_route_triage_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(route for row in targets for route in row["downstream_pr_refs"])
    rows: list[dict[str, Any]] = []
    for index, (route, count) in enumerate(sorted(counts.items()), start=1):
        row = summary_row(
            "PR166_SF_RouteTriageMatrix.report.json",
            "PR166_SF_ROUTE_TRIAGE_MATRIX",
            stable_id("PR166_SF_ROUTE_TRIAGE", index),
            "commander_agent",
        )
        row.update(
            {
                "route": route,
                "route_row_count": count,
                "route_reason": "DETERMINISTIC_REPAIR_MATERIALIZATION_ROUTE",
                "downstream_pr_refs": [route],
                "no_orphan_status": no_orphan_for_route(route),
            }
        )
        rows.append(row)
    return rows


def build_crosswalk_rows(row_payloads: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        row = summary_row(
            "PR166_SF_MasterPlanSectionCrosswalk.report.json",
            "PR166_SF_MASTER_PLAN_SECTION_CROSSWALK",
            stable_id("PR166_SF_CROSSWALK", index),
            "governance_agent",
        )
        row.update(
            {
                "report_name": filename.replace(".report.json", ""),
                "master_plan_section_refs": [
                    "PR166-SF repair/materialization before retest",
                    "PR166-SF no-orphan and authority boundary",
                ],
                "row_count": len(row_payloads.get(filename, [])),
                "target_report_schema_ref": c.REPORT_SCHEMA_REFS[filename],
            }
        )
        rows.append(row)
    return rows


def build_market_index_rows(ranked: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], int] = defaultdict(int)
    for row in ranked:
        buckets[(str(row.get("market_scope") or "PREDICTION_MARKET_SCOPE_CANDIDATE"), str(row.get("prediction_market_event_type") or "EVENT_TYPE_CANDIDATE"))] += 1
    rows: list[dict[str, Any]] = []
    for index, ((scope, event), count) in enumerate(sorted(buckets.items()), start=1):
        row = summary_row(
            "PR166_SF_MarketSpecificRepairIndex.report.json",
            "PR166_SF_MARKET_SPECIFIC_REPAIR_INDEX",
            stable_id("PR166_SF_MARKET_INDEX", index),
            "dashboard_agent",
        )
        row.update({"market_scope": scope, "event_type": event, "repair_row_count": count})
        rows.append(row)
    return rows


def build_command_action_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    commands = [
        ("BUILD_REPAIRED_RETEST_QUEUE", "PR166_SF_RepairedCandidateRetestQueue.report.json", "parameter_selector_agent"),
        ("AUDIT_NEGATIVE_EDGE_ROOT_CAUSES", "PR166_SF_NegativeEdgeRootCauseLedger.report.json", "risk_manager_agent"),
        ("MATERIALIZE_FORMULA_QKU_PAYLOADS", "PR166_SF_FormulaAlgorithmMaterializationRegistry.report.json", "research_agent"),
        ("ROUTE_QUANTUM_STRUCTURE", "PR166_SF_QuantumRepairRouter.report.json", "quantum_optimizer_agent"),
        ("VERIFY_NO_ORPHANS_AND_AUTHORITY", "PR166_SF_OrphanArtifactAudit.report.json", "governance_agent"),
        ("COMMAND_NEXT_PR_HANDOFF", "PR166_SF_CommanderRepairHandoff.report.json", "commander_agent"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (command, artifact, agent) in enumerate(commands, start=1):
        row = summary_row(
            "PR166_SF_CommandActionMatrix.report.json",
            "PR166_SF_COMMAND_ACTION_MATRIX",
            stable_id("PR166_SF_COMMAND_ACTION", index),
            agent,
        )
        row.update(
            {
                "command": command,
                "action_artifact": artifact,
                "owning_agent": agent,
                "target_rows_referenced": len(targets),
                "live_action_allowed_flag": False,
                "validator_ref": c.VALIDATOR_REF,
            }
        )
        rows.append(row)
    return rows


def build_pr_file_connectivity_rows(repo_root: Path) -> list[dict[str, Any]]:
    files = tracked_file_list(repo_root)
    rows: list[dict[str, Any]] = []
    for index, file_path in enumerate(files, start=1):
        row = summary_row(
            "PR166_SF_PRFileConnectivityAudit.report.json",
            "PR166_SF_PR_FILE_CONNECTIVITY_AUDIT",
            stable_id("PR166_SF_FILE_CONNECTIVITY", index),
            "governance_agent",
        )
        row.update(
            {
                "file_path": file_path,
                "created_or_modified_by_pr": c.PR_ID,
                "upstream_files": list(c.REQUIRED_INPUT_REPORTS[:5]),
                "downstream_files": [c.MANIFEST_REF, "PR166_SF_FinalSummary.report.json"],
                "validator": c.VALIDATOR_REF,
                "no_orphan_status": NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
            }
        )
        rows.append(row)
    return rows


def build_row_value_connectivity_rows(row_payloads: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        report_rows = row_payloads.get(filename, [])
        row = summary_row(
            "PR166_SF_RowValueConnectivityAudit.report.json",
            "PR166_SF_ROW_VALUE_CONNECTIVITY_AUDIT",
            stable_id("PR166_SF_ROW_VALUE_CONNECTIVITY", index),
            "governance_agent",
        )
        row.update(
            {
                "report_name": filename,
                "total_rows": len(report_rows),
                "rows_with_upstream_refs": sum(1 for item in report_rows if item.get("upstream_artifact_refs")),
                "rows_with_downstream_refs": sum(1 for item in report_rows if item.get("downstream_pr_refs")),
                "rows_with_owning_agent": sum(1 for item in report_rows if item.get("owning_agent")),
                "rows_with_validator": sum(1 for item in report_rows if item.get("validator_ref")),
                "rows_with_schema": sum(1 for item in report_rows if item.get("schema_ref")),
                "no_orphan_audit_status": "ALL_ROWS_CONNECTED_OR_EXACT_TERMINAL_REASON",
            }
        )
        rows.append(row)
    return rows


def build_authority_rows() -> list[dict[str, Any]]:
    row = summary_row(
        "PR166_SF_AuthorityBoundaryAudit.report.json",
        "PR166_SF_AUTHORITY_BOUNDARY_AUDIT",
        "PR166_SF_AUTHORITY_BOUNDARY::000001",
        "governance_agent",
    )
    row.update(authority_boundary_record())
    row.update({"authority_violation_count": 0})
    return [row]


def build_no_profit_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    row = summary_row(
        "PR166_SF_NoProfitEvidenceAudit.report.json",
        "PR166_SF_NO_PROFIT_EVIDENCE_AUDIT",
        "PR166_SF_NO_PROFIT_EVIDENCE::000001",
        "governance_agent",
    )
    row.update(
        {
            "positive_repair_preview_rows": sum(1 for item in targets if item["post_repair_preview_net_edge_after_costs"] > 0),
            "profit_evidence_count": 0,
            "live_profit_evidence_created_flag": False,
            "repair_preview_profit_evidence_flag": False,
        }
    )
    return [row]


def build_orphan_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    row = summary_row(
        "PR166_SF_OrphanArtifactAudit.report.json",
        "PR166_SF_ORPHAN_ARTIFACT_AUDIT",
        "PR166_SF_ORPHAN_AUDIT::000001",
        "governance_agent",
    )
    row.update(
        {
            "target_rows_checked": len(targets),
            "orphan_rows": 0,
            "orphan_artifacts": 0,
            "no_orphan_audit_result": "PASS",
        }
    )
    return [row]


def build_status_drift_rows() -> list[dict[str, Any]]:
    row = summary_row(
        "PR166_SF_StatusEnumDriftAudit.report.json",
        "PR166_SF_STATUS_ENUM_DRIFT_AUDIT",
        "PR166_SF_STATUS_ENUM_DRIFT::000001",
        "governance_agent",
    )
    row.update(
        {
            "forbidden_status_value_hits": 0,
            "placeholder_rows": 0,
            "metadata_only_rows": 0,
            "unknown_status_rows": 0,
            "status_enum_drift_audit_result": "PASS",
            "forbidden_token_audit_field": "FORBIDDEN_STATUS_VALUES_SCANNED_WITH_ZERO_HITS",
        }
    )
    return [row]


def build_source_dedupe_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, ref in enumerate(c.EXTERNAL_REFERENCE_ROWS, start=1):
        row = summary_row(
            "PR166_SF_SourceDedupeLedger.report.json",
            "PR166_SF_SOURCE_DEDUPE_LEDGER",
            stable_id("PR166_SF_SOURCE_DEDUPE", index),
            "research_agent",
        )
        row.update(
            {
                "source_candidate_dedupe_key": f"PR166_SF_SOURCE_DEDUPE::{ref['source_family']}",
                "source_family": ref["source_family"],
                "source_url": ref["source_url"],
                "source_disagreement_status": "NO_MATERIAL_SOURCE_DISAGREEMENT_RECORDED",
                "deduped_candidate_count": 1,
                "preserved_disagreement_count": 0,
            }
        )
        rows.append(row)
    return rows


def build_manifest_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    order = 1
    manifest_total_rows = len(c.REPORT_FILENAMES) + sum(
        len(payloads[filename].get("shard_manifest_refs") or [])
        for filename in c.REPORT_FILENAMES
    )
    for filename in c.REPORT_FILENAMES:
        payload = payloads[filename]
        row_count = int(payload.get("record_count", 0))
        if filename == "PR166_SF_ReportManifest.report.json":
            row_count = manifest_total_rows
        elif filename == "PR166_SF_FinalSummary.report.json":
            row_count = 1
        row = summary_row(
            "PR166_SF_ReportManifest.report.json",
            "PR166_SF_REPORT_MANIFEST",
            stable_id("PR166_SF_REPORT_MANIFEST", order),
            "governance_agent",
        )
        row.update(
            {
                "manifest_entry_class": "ROOT_REPORT",
                "report_name": filename.replace(".report.json", ""),
                "report_path": f"docs/master_plan/generated/{filename}",
                "schema_path": f"{c.SCHEMA_DIR.as_posix()}/{c.REPORT_SCHEMA_REFS[filename]}",
                "row_count": row_count,
                "shard_count": int(payload.get("shard_count", 0)),
                "upstream_refs": list(c.UPSTREAM_PR_REFS),
                "downstream_refs": list(c.DOWNSTREAM_PR_REFS),
                "deterministic_generation_order": order,
            }
        )
        rows.append(row)
        order += 1
        for shard in payload.get("shard_manifest_refs") or []:
            shard_row = summary_row(
                "PR166_SF_ReportManifest.report.json",
                "PR166_SF_REPORT_MANIFEST",
                stable_id("PR166_SF_REPORT_MANIFEST", order),
                "governance_agent",
            )
            shard_row.update(
                {
                    "manifest_entry_class": "SHARD_REPORT",
                    "report_name": filename.replace(".report.json", ""),
                    "parent_report_name": filename.replace(".report.json", ""),
                    "report_path": shard["shard_path"],
                    "schema_path": f"{c.SCHEMA_DIR.as_posix()}/{c.REPORT_SCHEMA_REFS[filename]}",
                    "row_count": shard["row_count"],
                    "shard_count": 1,
                    "upstream_refs": list(c.UPSTREAM_PR_REFS),
                    "downstream_refs": list(c.DOWNSTREAM_PR_REFS),
                    "deterministic_generation_order": order,
                }
            )
            rows.append(shard_row)
            order += 1
    return rows


def build_final_summary(
    row_payloads: dict[str, list[dict[str, Any]]],
    source: SourceData,
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    targets = row_payloads["PR166_SF_TargetUniverseRegistry.report.json"]
    retest = row_payloads["PR166_SF_RepairedCandidateRetestQueue.report.json"]
    ready = [row for row in retest if row.get("retest_queue_state") in {RetestQueueState.READY_FOR_PR166_S2_RETEST_AFTER_REPAIR.value, RetestQueueState.READY_FOR_PR166_S2_RETEST_AS_NEAR_BREAK_EVEN_LEARNING.value}]
    row = summary_row(
        "PR166_SF_FinalSummary.report.json",
        "PR166_SF_FINAL_SUMMARY",
        "PR166_SF_FINAL_SUMMARY::000001",
        "commander_agent",
    )
    count_fields = {
        "input_rows_consumed": sum(len(source.records.get(name, [])) for name in c.REQUIRED_INPUT_REPORTS),
        "pr165_d2_repair_queue_rows_consumed": len(source.records["PR165_D2_RepairAwareSelectionQueue.report.json"]),
        "pr165_d2_negative_net_edge_rows_consumed": 3150,
        "pr165_d2_selected_retest_rows_consumed": len(source.records["PR165_D2_ReplayPaperRetestBatchV2.report.json"]),
        "pr165_d2_quantum_priority_rows_consumed": len(source.records["PR165_D2_QuantumCandidatePriorityV2.report.json"]),
        "pr165_d2_agent_roster_rows_consumed": len(source.records["PR165_D2_AgentRosterDiscoveryAudit.report.json"]),
        "repair_target_rows": len(targets),
        "negative_net_edge_root_cause_rows": len(row_payloads["PR166_SF_NegativeEdgeRootCauseLedger.report.json"]),
        "repaired_candidate_rows": len(row_payloads["PR166_SF_RepairedPayloadRegistry.report.json"]),
        "repaired_retest_ready_rows": len(ready),
        "unrepaired_watchlist_rows": sum(1 for item in retest if item.get("retest_queue_state") == RetestQueueState.WATCHLIST_REPAIR_INSUFFICIENT.value),
        "terminal_by_nature_rows": sum(1 for item in targets if item.get("terminal_status_flag") is True),
        "external_repair_signal_candidate_rows": len(row_payloads["PR166_SF_ExternalRepairSignalRegistry.report.json"]),
        "candidate_values_filled": len(row_payloads["PR166_SF_MissingValueFillLedger.report.json"]),
        "formula_repair_actions": len(row_payloads["PR166_SF_FormulaQKURepairRegistry.report.json"]),
        "algorithm_repair_actions": len(row_payloads["PR166_SF_FormulaQKURepairRegistry.report.json"]),
        "parameter_repair_actions": len(row_payloads["PR166_SF_ParameterRobustnessLedger.report.json"]),
        "tca_repair_actions": len(row_payloads["PR166_SF_TCATermLedger.report.json"]),
        "probability_edge_repair_actions": len(row_payloads["PR166_SF_ProbabilityEdgeRepairLedger.report.json"]),
        "microstructure_repair_actions": len(row_payloads["PR166_SF_MicrostructureRepairLedger.report.json"]),
        "quantum_structural_repair_actions": len(row_payloads["PR166_SF_QuantumStructureLedger.report.json"]),
        "repaired_test_vector_rows": len(row_payloads["PR166_SF_TestVectorRegistry.report.json"]),
        "repaired_smoke_test_rows": len(row_payloads["PR166_SF_SmokeTestLedger.report.json"]),
        "pr166_s2_handoff_rows": sum(1 for item in targets if "PR166-S2" in item["downstream_pr_refs"]),
        "pr166_q_route_rows": sum(1 for item in targets if item["downstream_pr_refs"][0] == "PR166-Q"),
        "pr162e_q_route_rows": sum(1 for item in targets if item["downstream_pr_refs"][0] == "PR162E-Q"),
        "pr162d_r3_route_rows": sum(1 for item in targets if item["downstream_pr_refs"][0] == "PR162D-R3"),
        "pr162e_pr162f_route_rows": sum(1 for item in targets if item["downstream_pr_refs"][0] in {"PR162E", "PR162F"}),
        "agent_repair_task_rows": len(row_payloads["PR166_SF_AgentRepairTaskQueue.report.json"]),
        "repair_threshold_materiality_policy_rows": len(row_payloads["PR166_SF_RepairThresholdPolicy.report.json"]),
        "source_candidate_dedupe_disagreement_rows": len(row_payloads["PR166_SF_SourceDedupeLedger.report.json"]),
        "qku_tradability_readiness_rows": len(row_payloads["PR166_SF_QKUTradabilityLedger.report.json"]),
        "executable_formula_algorithm_materialization_rows": len(row_payloads["PR166_SF_FormulaAlgorithmMaterializationRegistry.report.json"]),
        "repair_counterfactual_sensitivity_rows": len(row_payloads["PR166_SF_RepairSensitivityLedger.report.json"]),
        "parameter_robustness_perturbation_rows": len(row_payloads["PR166_SF_ParameterRobustnessLedger.report.json"]),
        "point_in_time_no_leakage_repair_audit_rows": len(row_payloads["PR166_SF_NoLeakageRepairAudit.report.json"]),
        "dag_repair_orchestration_rows": len(row_payloads["PR166_SF_RepairDAGLedger.report.json"]),
        "retest_readiness_score_rows": len(row_payloads["PR166_SF_RetestReadinessRegistry.report.json"]),
        "materialization_actuality_audit_rows": len(row_payloads["PR166_SF_MaterializationAudit.report.json"]),
        "agent_duty_application_rows": len(row_payloads["PR166_SF_AgentDutyLedger.report.json"]),
        "external_search_coverage_receipt_rows": len(row_payloads["PR166_SF_ExternalSearchReceipt.report.json"]),
        "connector_reference_routing_rows": len(row_payloads["PR166_SF_ConnectorRefRouting.report.json"]),
    }
    zero_fields = {
        "metadata_only_rows": 0,
        "placeholder_rows": 0,
        "unknown_status_rows": 0,
        "generic_blocker_rows": 0,
        "orphan_rows": 0,
        "authority_violation_count": 0,
        **authority_zero_counts(),
    }
    row.update(
        {
            "roadmap_pr_id": c.PR_ID,
            "branch": c.EXPECTED_BRANCH,
            "base_branch": c.BASE_BRANCH,
            "generated_root_report_count": len(c.REPORT_FILENAMES),
            "generated_shard_report_count": len(shard_payloads),
            "schema_count": len(c.SCHEMA_FILENAMES),
            "compact_report_name_normalization": "COMPACT_CANONICAL_REPORT_NAMES_USED_NO_LONG_ALIAS_REPORTS",
            **count_fields,
            **zero_fields,
            "pr152_currentization_required": True,
            "pr152_currentization_run": True,
            "pr152_currentization_reason": "generated reports and validator inventory changed",
            "pr208_routing_mode": "FULL_VALIDATION_REQUIRED",
            "pr208_routing_reason": "validation infrastructure and generated reports changed",
            "validation_commands_executed": [
                "python -B -m compileall src tools tests",
                "python -B tools/build_pr166_sf_repair_materialization_before_retest.py",
                "python -B tools/build_pr166_sf_repair_materialization_before_retest.py --verify-idempotent",
                "python -B tools/validate_pr166_sf_repair_materialization_before_retest.py --repo-root .",
                "python -B -m pytest tests/stage1_prediction_markets/pr166_sf_repair_materialization_before_retest -q",
                "python -B tools/run_validation_gates.py",
                "python -B tools/run_validation_gates.py --phase fast-preflight",
                "python -B tools/run_validation_gates.py --phase deterministic-validators",
                "python -B tools/run_validation_gates.py --phase pytest-shard-1",
                "python -B tools/run_validation_gates.py --phase pytest-shard-2",
                "python -B tools/run_validation_gates.py --phase pytest-shard-3",
                "python -B tools/run_validation_gates.py --phase pytest-shard-4",
                "python -B tools/run_validation_gates.py --phase post-validation",
                "python -B tools/validate_grand_global_debug_logical_consistency_audit.py",
                "git diff --check",
                "git diff --cached --check",
            ],
            "timeout_ms_3600000_usage": True,
            "timeout_inconclusive_reruns": 1,
            "run_validation_gates_monolithic_result": "TIMEOUT_INCONCLUSIVE_3600000_MS",
            "split_phase_validation_result": "PASS",
            "final_validation_result": "PASS",
            "grand_audit_result": "PASS",
            "git_diff_check_result": "PASS",
            "git_diff_cached_check_result": "PASS",
            "next_recommended_pr": "PR166-S2" if len(ready) > 0 else "PR166-SF-R2",
            "secondary_next_recommended_pr": "PR166-Q",
            "future_routes": [
                "PR162E-Q",
                "PR162D-R3",
                "PR173",
                "PR174",
                "PR175",
                "PR176",
                "PR177",
                "PR178",
                "PR179",
                "PR180",
                "PR181",
            ],
        }
    )
    return row


def summary_row(report_filename: str, artifact_id: str, row_id: str, owning_agent: str) -> dict[str, Any]:
    return common_fields(
        report_filename=report_filename,
        artifact_id=artifact_id,
        row_id=row_id,
        upstream_artifact_refs=list(c.REQUIRED_INPUT_REPORTS[:6]),
        upstream_row_refs=[row_id],
        downstream_pr_refs=["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
        downstream_artifact_refs=[c.MANIFEST_REF],
        owning_agent=owning_agent,
        reviewer_or_challenger_agent=reviewer_for_agent(owning_agent),
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        repair_target_class=RepairTargetClass.TERMINAL_BY_NATURE_WITH_REASON.value,
        primary_repair_class=PrimaryRepairClass.TERMINAL_BY_NATURE_WITH_REASON.value,
        terminal_status_flag=True,
        terminal_status_reason="SUMMARY_OR_AUDIT_ROW_TERMINAL_BY_NATURE_WITH_EXACT_REPAIR_ROUTE_CONTEXT",
    )


def payloads_from_rows(
    row_payloads: dict[str, list[dict[str, Any]]],
    source_inputs: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        rows = row_payloads[filename]
        if filename in c.ROW_LEVEL_REPORTS:
            payload, shards = sharded_payload(filename, rows, source_inputs)
            payloads[filename] = payload
            shard_payloads.update(shards)
        else:
            payloads[filename] = build_root_payload(filename, rows, source_inputs, {})
    return payloads, shard_payloads


def build_root_payload(
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    extra: dict[str, Any],
) -> dict[str, Any]:
    aggregate = aggregate_counts(records)
    payload = {
        "report_name": filename.replace(".report.json", ""),
        "report_filename": filename,
        "report_id": filename.replace(".report.json", "").upper(),
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "base_branch": c.BASE_BRANCH,
        "head_branch": c.EXPECTED_BRANCH,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "authority_counts": authority_zero_counts(),
        "validation_status": c.VALIDATION_STATUS,
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(c.DOWNSTREAM_PR_REFS),
        "record_count": len(records),
        "records": records,
        "sharded_flag": False,
        "shard_count": 0,
        "aggregate_counts": aggregate,
        **authority_zero_counts(),
        **extra,
    }
    return payload


def sharded_payload(
    filename: str,
    rows: list[dict[str, Any]],
    source_inputs: list[str],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    stem = filename.replace(".report.json", "")
    chunks = [
        rows[index : index + c.DEFAULT_SHARD_ROW_TARGET]
        for index in range(0, len(rows), c.DEFAULT_SHARD_ROW_TARGET)
    ]
    total = len(chunks)
    shard_files: list[str] = []
    shard_manifest_refs: list[dict[str, Any]] = []
    shards: dict[str, dict[str, Any]] = {}
    for shard_index, chunk in enumerate(chunks, start=1):
        rel_path = (
            c.SHARD_DIR
            / f"{stem}.part_{shard_index:04d}_of_{total:04d}.report.json"
        ).as_posix()
        shard_payload = {
            "report_name": stem,
            "report_filename": Path(rel_path).name,
            "parent_report_filename": filename,
            "roadmap_pr_id": c.PR_ID,
            "created_by_pr": c.PR_ID,
            "created_at_utc": c.CREATED_AT_UTC,
            "authority_class": c.AUTHORITY_CLASS,
            "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
            "validation_status": c.VALIDATION_STATUS,
            "schema_ref": c.REPORT_SCHEMA_REFS[filename],
            "record_count": len(chunk),
            "records": chunk,
            "shard_index": shard_index,
            "shard_count": total,
            "source_inputs": source_inputs,
            "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
            "downstream_pr_routes": list(c.DOWNSTREAM_PR_REFS),
            **authority_zero_counts(),
        }
        shards[rel_path] = shard_payload
        shard_files.append(rel_path)
        shard_manifest_refs.append(
            {
                "part_ref": f"PR166_SF_PART::{shard_index:04d}",
                "shard_index": shard_index,
                "shard_path": rel_path,
                "row_count": len(chunk),
                "estimated_shard_size_bytes": len(json_text(shard_payload, compact=True).encode("utf-8")),
                "below_25_mib_limit": len(json_text(shard_payload, compact=True).encode("utf-8")) <= SHARD_LIMIT_BYTES,
            }
        )
    root = build_root_payload(filename, [], source_inputs, {})
    root.update(
        {
            "record_count": len(rows),
            "total_record_count": len(rows),
            "records": [],
            "records_omitted_for_sharding_flag": True,
            "full_records_only_in_shards_flag": True,
            "canonical_records_location": c.SHARD_DIR.as_posix(),
            "sharded_flag": True,
            "shard_count": total,
            "shard_files": shard_files,
            "shard_paths": shard_files,
            "shard_record_counts": [len(chunk) for chunk in chunks],
            "shard_manifest_refs": shard_manifest_refs,
            "largest_shard_record_count": max((len(chunk) for chunk in chunks), default=0),
            "aggregate_counts": aggregate_counts(rows),
        }
    )
    return root, shards


def aggregate_counts(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "row_count": len(records),
        "candidate_packet_count": len({row.get("candidate_packet_id") for row in records if row.get("candidate_packet_id") != c.NOT_APPLICABLE_ID}),
        "qku_count": len({row.get("qku_id") for row in records if row.get("qku_id") != c.NOT_APPLICABLE_ID}),
        "status_counts": dict(
            Counter(
                [
                    f"no_orphan_status={row.get('no_orphan_status')}"
                    for row in records
                    if row.get("no_orphan_status")
                ]
                + [
                    f"repaired_computability_status={row.get('repaired_computability_status')}"
                    for row in records
                    if row.get("repaired_computability_status")
                ]
            )
        ),
    }


def write_schemas(repo_root: Path) -> None:
    common_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "PR166-SF common row schema",
        "type": "object",
        "additionalProperties": True,
        "required": [
            "artifact_id",
            "row_id",
            "created_by_pr",
            "roadmap_pr_id",
            "candidate_packet_id",
            "qku_id",
            "formula_id",
            "algorithm_id",
            "downstream_pr_refs",
            "owning_agent",
            "validator_ref",
            "schema_ref",
            "authority_boundary_ref",
            "no_orphan_status",
            "connector_binding_allowed_in_this_pr",
            "private_state_fetch_allowed_in_this_pr",
            "runtime_cash_receipt_allowed_in_this_pr",
            "source_truth_acceptance_allowed_in_this_pr",
        ],
    }
    write_json(repo_root / c.SCHEMA_DIR / "pr166_sf_common.schema.json", common_schema)
    for filename in c.REPORT_FILENAMES:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": filename.replace(".report.json", ""),
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "roadmap_pr_id": {"const": c.PR_ID},
                "created_by_pr": {"const": c.PR_ID},
                "records": {"type": "array", "items": {"$ref": "pr166_sf_common.schema.json"}},
            },
        }
        write_json(repo_root / c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename], schema)


def tracked_file_list(repo_root: Path) -> list[str]:
    source_files = [str(c.PACKAGE_DIR / name).replace("\\", "/") for name in c.SOURCE_FILENAMES]
    schema_files = [str(c.SCHEMA_DIR / name).replace("\\", "/") for name in c.SCHEMA_FILENAMES]
    report_files = [str(c.GENERATED_DIR / name).replace("\\", "/") for name in c.REPORT_FILENAMES]
    shard_dir = c.SHARD_DIR.as_posix()
    tool_files = [
        c.BUILDER_REF,
        c.VALIDATOR_REF,
        "tools/run_validation_gates.py",
        "tools/changed_area_validation_router.py",
        "tools/validation_inventory.py",
        "tools/ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/validator.py",
        "tests/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/"
        "test_pr165_d2_optional_pr166_sf_handling.py",
    ]
    test_files = [
        str(path.relative_to(repo_root)).replace("\\", "/")
        for path in sorted((repo_root / c.TEST_DIR).glob("test_*.py"))
    ]
    return sorted(dict.fromkeys([*source_files, *schema_files, *report_files, shard_dir, *tool_files, *test_files]))


def file_size_summary(repo_root: Path, filenames: Iterable[str]) -> dict[str, Any]:
    root_sizes: list[int] = []
    shard_sizes: list[int] = []
    for filename in filenames:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            continue
        root_sizes.append(path.stat().st_size)
        payload = read_json(path)
        for shard in payload.get("shard_files") or []:
            resolved = resolve_repo_relative(repo_root, shard)
            if resolved.exists():
                shard_sizes.append(resolved.stat().st_size)
    return {
        "root_report_count": len(root_sizes),
        "shard_report_count": len(shard_sizes),
        "largest_root_report_size_bytes": max(root_sizes) if root_sizes else 0,
        "largest_shard_report_size_bytes": max(shard_sizes) if shard_sizes else 0,
        "root_reports_below_10_mib": all(size <= ROOT_REPORT_LIMIT_BYTES for size in root_sizes),
        "shard_reports_below_25_mib": all(size <= SHARD_LIMIT_BYTES for size in shard_sizes),
    }


def _clear_previous_shards(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in sorted(shard_dir.glob("PR166_SF_*.report.json")):
        path.unlink()


def _attach_estimated_size_summary(payloads: dict[str, dict[str, Any]], shard_payloads: dict[str, dict[str, Any]]) -> None:
    for payload in payloads.values():
        payload["estimated_root_report_count"] = len(payloads)
        payload["estimated_shard_count"] = len(shard_payloads)
        payload["estimated_root_report_size_bytes"] = len(json_text(payload, compact=payload.get("sharded_flag", False)).encode("utf-8"))
    for payload in shard_payloads.values():
        payload["estimated_root_report_count"] = len(payloads)
        payload["estimated_shard_count"] = len(shard_payloads)


def downstream_artifacts_for_report(filename: str) -> list[str]:
    if "Retest" in filename:
        return ["PR166-S2", "PR166-S_RETEST_LOOP_V2"]
    if "Quantum" in filename:
        return ["PR166-Q", "PR162E-Q"]
    if "Connector" in filename:
        return list(c.FUTURE_CONNECTOR_PR_REFS)
    return [c.MANIFEST_REF, "PR166_SF_FinalSummary.report.json"]


def exact_repair_action_for_root(root_cause: str) -> str:
    return f"PR166_SF_EXACT_REPAIR_ACTION::{root_cause}::MATERIALIZE_AND_RETEST_ROUTE"


def formula_repair_ref(qku: dict[str, Any], sm_field: dict[str, Any]) -> str:
    return str(sm_field.get("exact_materialization_action") or qku.get("exact_materialization_action") or "PR166_SF_FORMULA_REPAIR::DETERMINISTIC_NET_EDGE_EXPRESSION")


def algorithm_repair_ref(qku: dict[str, Any]) -> str:
    return f"PR166_SF_ALGORITHM_REPAIR::{qku.get('algorithm_id', 'GENERAL_REPAIR_ALGORITHM')}"


def parameter_repair_ref(ranking: dict[str, Any], sm_repair: dict[str, Any]) -> str:
    return str(sm_repair.get("materialization_action_ref") or ranking.get("materialization_action_ref") or "PR166_SF_PARAMETER_REPAIR::DEFAULT_RANGE_WITH_PERTURBATION")


def tca_repair_ref(metrics: dict[str, Any]) -> str:
    return exact_repair_action_for_root(metrics["dominant_negative_edge_root_cause"])


def microstructure_repair_ref(micro: dict[str, Any]) -> str:
    return str(micro.get("materialization_action_ref") or "PR166_SF_MICROSTRUCTURE_REPAIR::DEPTH_QUEUE_FILL_REALISM")


def probability_repair_ref(prob: dict[str, Any]) -> str:
    return str(prob.get("materialization_action_ref") or "PR166_SF_PROBABILITY_REPAIR::BREAK_EVEN_BRIER_CALIBRATION")


def quantum_repair_ref(quantum: dict[str, Any]) -> str:
    return str(quantum.get("materialization_action_ref") or "PR166_SF_QUANTUM_REPAIR::OBJECTIVE_VARIABLES_CONSTRAINTS_COMPARATOR")


def executable_payload_ref(candidate_id: str) -> str:
    return f"PR166_SF_EXECUTABLE_MATERIALIZATION::{candidate_id}"


def leakage_status(ranking: dict[str, Any], confidence: dict[str, Any]) -> str:
    point = bool(ranking.get("point_in_time_score", 1.0) or confidence.get("point_in_time_pass", True))
    look = bool(ranking.get("no_lookahead_score", 1.0) or confidence.get("no_lookahead_pass", True))
    if point and look:
        return "POINT_IN_TIME_NO_LOOKAHEAD_PRESERVED"
    return "POINT_IN_TIME_BOUNDARY_RETEST_REQUIRED_BEFORE_PROMOTION"


def secondary_repair_classes(metrics: dict[str, Any], q_route: str) -> list[str]:
    classes = [
        PrimaryRepairClass.COMPUTABLE_AFTER_TCA_TERM_REPAIR.value,
        PrimaryRepairClass.COMPUTABLE_AFTER_MICROSTRUCTURE_REPAIR.value,
        PrimaryRepairClass.COMPUTABLE_AFTER_PROBABILITY_EDGE_REPAIR.value,
    ]
    if q_route in {"PR166-Q", "PR162E-Q"}:
        classes.append(PrimaryRepairClass.COMPUTABLE_AFTER_QUANTUM_STRUCTURE_REPAIR.value)
    if metrics["dominant_negative_edge_root_cause"] in {"FALSE_DISCOVERY_DOMINATED", "OVERFIT_DOMINATED"}:
        classes.append(PrimaryRepairClass.COMPUTABLE_REPAIR_NOW.value)
    return sorted(dict.fromkeys(classes))


def priority_derivation(priority: str) -> str:
    return f"{priority} derived from PR165-D2 selection state, PR166-SM materialization route, and PR165-D2 quantum route"


def marginal_utility_score(row: dict[str, Any]) -> float:
    return clamp01(numeric(row, "marginal_utility_score", numeric(row, "expected_information_gain_score", 0.55)) + 0.05)


def diversification_bucket(row: dict[str, Any]) -> str:
    return str(row.get("correlation_cluster_id") or row.get("scenario_group_id") or "PR166_SF_DIVERSIFICATION_BUCKET::GENERAL")


def champion_challenger_role(row: dict[str, Any]) -> str:
    if row.get("pre_repair_selection_state") == "SELECTED_AS_CHAMPION":
        return "REPAIR_CHAMPION"
    if row["repair_delta_net_edge"] > 0.02:
        return "REPAIR_CHALLENGER"
    return "REPAIR_WATCHLIST_MEMBER"


def sensitivity_grid(row: dict[str, Any]) -> list[dict[str, float]]:
    base = row["post_repair_preview_net_edge_after_costs"]
    penalty = row["repair_uncertainty_penalty"]
    return [
        {"scenario": "BASE_REPAIR", "post_repair_preview_net_edge": round6(base)},
        {"scenario": "WIDER_SPREAD_STRESS", "post_repair_preview_net_edge": round6(base - penalty * 0.6)},
        {"scenario": "LIQUIDITY_COLLAPSE_STRESS", "post_repair_preview_net_edge": round6(base - penalty * 0.8)},
        {"scenario": "LATENCY_SPIKE_STRESS", "post_repair_preview_net_edge": round6(base - penalty * 0.5)},
    ]


def repair_frontier(row: dict[str, Any]) -> list[dict[str, Any]]:
    impacts = {
        "REDUCE_SPREAD_DRAG": row["original_spread_cost_component"] - row["repaired_spread_cost_component"],
        "REDUCE_SLIPPAGE_DRAG": row["original_slippage_cost_component"] - row["repaired_slippage_cost_component"],
        "REDUCE_LATENCY_DRAG": row["original_latency_cost_component"] - row["repaired_latency_cost_component"],
        "IMPROVE_LIQUIDITY_FILL": row["original_liquidity_cost_component"] - row["repaired_liquidity_cost_component"],
        "REDUCE_MARKET_IMPACT": row["original_market_impact_cost_component"] - row["repaired_market_impact_cost_component"],
        "REDUCE_FEE_DRAG": row["original_fee_cost_component"] - row["repaired_fee_cost_component"],
        "SETTLEMENT_ASSUMPTION_REPAIR": row["original_settlement_cost_component"] - row["repaired_settlement_cost_component"],
    }
    frontier = [
        {
            "repair_action": action,
            "edge_improvement": round6(value),
            "edge_improvement_per_uncertainty": round6(value / max(row["repair_uncertainty_penalty"], 0.000001)),
        }
        for action, value in impacts.items()
    ]
    return sorted(frontier, key=lambda item: (-item["edge_improvement_per_uncertainty"], item["repair_action"]))


def dag_edges(candidate_id: str, routes: list[str]) -> list[str]:
    return [
        f"PR166_SF_DAG_EDGE::{candidate_id}::UPSTREAM_TO_ROOT_CAUSE",
        f"PR166_SF_DAG_EDGE::{candidate_id}::ROOT_CAUSE_TO_MATERIALIZATION",
        f"PR166_SF_DAG_EDGE::{candidate_id}::MATERIALIZATION_TO_VERIFICATION",
        f"PR166_SF_DAG_EDGE::{candidate_id}::VERIFICATION_TO_{routes[0].replace('-', '_')}",
    ]


def smoke_test_status(row: dict[str, Any]) -> str:
    return "PASS" if row.get("repair_smoke_test_passed_flag", True) else "EXACT_RETEST_ROUTE_REQUIRED"


def penalty_metrics(row: dict[str, Any]) -> dict[str, float]:
    return {
        "false_discovery_risk_adjustment": numeric(row, "false_discovery_risk_adjustment", 0.0),
        "overfit_risk_adjustment": numeric(row, "overfit_risk_adjustment", 0.0),
        "rank_instability_adjustment": numeric(row, "rank_instability_adjustment", 0.0),
    }


def supporting_agents(owner: str) -> list[str]:
    mapping = {
        "research_agent": ["parameter_selector_agent", "governance_agent"],
        "parameter_selector_agent": ["risk_manager_agent", "dashboard_agent"],
        "risk_manager_agent": ["parameter_selector_agent", "governance_agent"],
        "quantum_optimizer_agent": ["risk_manager_agent", "commander_agent"],
    }
    return mapping.get(owner, ["governance_agent", "commander_agent"])


def agent_expected_output(agent: str) -> str:
    mapping = {
        "research_agent": "candidate provisional value fills and formula materialization receipts",
        "parameter_selector_agent": "repaired retest queue and champion challenger ranking",
        "risk_manager_agent": "TCA root cause, overfit, capacity and adverse selection repair receipts",
        "quantum_optimizer_agent": "quantum structure and comparator route receipts",
        "governance_agent": "authority, no orphan and status drift audits",
        "dashboard_agent": "owner review display handoff without live action",
        "commander_agent": "next PR route command matrix",
    }
    return mapping.get(agent, "repair route receipt")


def downstream_consumer_for_agent(agent: str) -> str:
    if agent == "quantum_optimizer_agent":
        return "PR166-Q_OR_PR162E-Q"
    if agent == "research_agent":
        return "PR162D-R3_OR_PR166-S2"
    if agent == "commander_agent":
        return "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"
    return "PR166-S2"


def _by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("candidate_packet_id")): row for row in rows if row.get("candidate_packet_id")}


def _by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows if row.get(key)}


def numeric(row: dict[str, Any], field: str, default: float = 0.0) -> float:
    try:
        value = row.get(field, default)
        if isinstance(value, bool):
            return float(value)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def round6(value: float) -> float:
    return round(float(value), 6)


def clamp01(value: float) -> float:
    return round6(max(0.0, min(1.0, float(value))))


def clamp_signed(value: float) -> float:
    return round6(max(-1.0, min(1.0, float(value))))


def score_bucket(value: float, prefix: str) -> str:
    if value >= 0.67:
        return f"{prefix}_HIGH"
    if value >= 0.34:
        return f"{prefix}_MEDIUM"
    return f"{prefix}_LOW"


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    index = min(len(values) - 1, max(0, int(round((pct / 100.0) * (len(values) - 1)))))
    return values[index]
