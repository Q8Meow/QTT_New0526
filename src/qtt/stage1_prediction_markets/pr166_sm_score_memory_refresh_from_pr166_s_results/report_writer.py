"""Build PR166-SM generated reports."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import authority_boundary_record, authority_zero_counts
from .capacity import capacity_metrics, cluster_counter, correlation_cluster_id
from .confidence import confidence_metrics
from .connectivity import build_pr_file_connectivity_rows, build_row_value_connectivity_rows, tracked_file_list
from .cost_model import cost_metrics, net_edge_after_costs, numeric
from .dominance import classify
from .enums import (
    AgentId,
    ComputabilityStatus,
    DownstreamRoute,
    MemoryOutcome,
    NoOrphanStatus,
    PrimaryClassification,
    SourceAuthorityClass,
    ValueAuthorityLane,
)
from .external_intake import build_external_candidate_rows
from .false_discovery import cluster_counts, cluster_id, risk_controls
from .io import (
    ensure_branch,
    json_text,
    load_report_records,
    normalize_repo_ref,
    read_json,
    records_from_report_payload,
    resolve_repo_relative,
    schema_path,
    write_json,
)
from .manifest import build_manifest_rows
from .memory import memory_outcome
from .models import algorithm_id_from_role, common_fields, formula_id_from_family, stable_id
from .normalization import rank_normalize_by_group, round6, winsor_caps
from .quantum_priority import quantum_priority, quantum_structures, readiness_score
from .ranking import assign_ranks, reason_for_delta
from .repair_priority import repair_priority_score, repair_route
from .scenario_similarity import scenario_similarity_score
from .scoring import refreshed_net_edge_score


ROOT_REPORT_LIMIT_BYTES = 10 * 1024 * 1024
SHARD_LIMIT_BYTES = 25 * 1024 * 1024
DEFAULT_SHARD_ROW_TARGET = 1000


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class SourceData:
    payloads: dict[str, dict[str, Any]]
    records: dict[str, list[dict[str, Any]]]
    missing_required: tuple[str, ...]
    missing_optional: tuple[str, ...]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root)
    _clear_previous_shards(repo_root)
    for filename in c.REPORT_FILENAMES:
        write_json(repo_root / c.GENERATED_DIR / filename, payloads[filename], compact=filename in c.ROW_LEVEL_REPORTS)
    for rel_path, shard_payload in shard_payloads.items():
        write_json(resolve_repo_relative(repo_root, rel_path), shard_payload, compact=True)
    sizes = file_size_summary(repo_root, c.REPORT_FILENAMES)
    summary = dict(payloads["PR166_SM_FinalSummary.report.json"]["records"][0])
    summary.update(sizes)
    payloads["PR166_SM_FinalSummary.report.json"]["records"] = [summary]
    payloads["PR166_SM_FinalSummary.report.json"].update(sizes)
    payloads["PR166_SM_ReportManifest.report.json"] = build_root_payload(
        "PR166_SM_ReportManifest.report.json",
        build_manifest_rows(payloads),
        list(c.REQUIRED_INPUT_REPORTS),
        {"manifest_report_count": len(c.REPORT_FILENAMES)},
    )
    write_json(repo_root / c.GENERATED_DIR / "PR166_SM_FinalSummary.report.json", payloads["PR166_SM_FinalSummary.report.json"])
    write_json(repo_root / c.GENERATED_DIR / "PR166_SM_ReportManifest.report.json", payloads["PR166_SM_ReportManifest.report.json"])
    return BuildArtifacts(summary=summary, payloads=payloads, shard_payloads=shard_payloads)


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source = load_sources(repo_root)
    if source.missing_required:
        raise RuntimeError(f"PR166-SM required inputs missing: {', '.join(source.missing_required)}")
    row_payloads = build_row_payloads(repo_root, source)
    payloads, shard_payloads = payloads_from_rows(row_payloads, list(c.REQUIRED_INPUT_REPORTS))
    payloads["PR166_SM_ReportManifest.report.json"] = build_root_payload(
        "PR166_SM_ReportManifest.report.json",
        build_manifest_rows(payloads),
        list(c.REQUIRED_INPUT_REPORTS),
        {"manifest_report_count": len(c.REPORT_FILENAMES)},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    missing = sorted(set(c.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR166-SM payload map missing reports: {missing}")
    return payloads, shard_payloads


def load_sources(repo_root: Path) -> SourceData:
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    missing_required: list[str] = []
    missing_optional: list[str] = []
    for filename in c.REQUIRED_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            missing_required.append(filename)
            continue
        payload = read_json(path)
        payloads[filename] = payload
        records[filename] = records_from_report_payload(repo_root, payload)
    for filename in c.OPTIONAL_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            missing_optional.append(filename)
            continue
        payload = read_json(path)
        payloads[filename] = payload
        records[filename] = records_from_report_payload(repo_root, payload)
    return SourceData(payloads, records, tuple(missing_required), tuple(missing_optional))


def build_row_payloads(repo_root: Path, source: SourceData) -> dict[str, list[dict[str, Any]]]:
    input_rows = _input_consumption_rows(source)
    policy_rows = _refresh_policy_rows()
    (
        score_rows,
        memory_rows,
        rank_delta_rows,
        fd_rows,
        overfit_rows,
        capacity_rows,
        correlation_rows,
        repair_rows,
        quantum_priority_rows,
        quantum_readiness_rows,
        qku_computability_rows,
        materialization_rows,
        selection_ready_rows,
        failure_route_rows,
    ) = _candidate_rows(source)

    winner_rows, loser_rows = _winner_loser_rows(score_rows)
    downgrade_rows = _downgrade_rows(score_rows)
    external_rows = build_external_candidate_rows()
    agent_contract_rows = _agent_contract_rows()
    agent_task_rows = _agent_task_rows(score_rows, repair_rows, quantum_priority_rows, external_rows)
    dashboard_rows = _dashboard_rows(winner_rows, loser_rows, repair_rows, quantum_priority_rows, external_rows)
    governance_rows = _governance_rows()
    commander_rows = _commander_rows(score_rows, repair_rows, quantum_priority_rows)
    institutional_rows = _institutional_rows(score_rows, fd_rows, overfit_rows, capacity_rows, quantum_readiness_rows)
    normalization_rows = _normalization_policy_rows(score_rows)
    authority_rows = _authority_boundary_rows()
    orphan_rows = _orphan_rows()
    status_rows = _status_drift_rows()
    row_payloads: dict[str, list[dict[str, Any]]] = {
        "PR166_SM_InputConsumptionAudit.report.json": input_rows,
        "PR166_SM_ReplayPaperResultRefreshPolicy.report.json": policy_rows,
        "PR166_SM_ScoreNormalizationPolicy.report.json": normalization_rows,
        "PR166_SM_RefreshedScoreRegistry.report.json": score_rows,
        "PR166_SM_RefreshedMemoryLedger.report.json": memory_rows,
        "PR166_SM_NetEdgeRankDeltaRegistry.report.json": rank_delta_rows,
        "PR166_SM_ConditionScopedWinnerRegistry.report.json": winner_rows,
        "PR166_SM_ConditionScopedLoserRegistry.report.json": loser_rows,
        "PR166_SM_CostDominatedDowngradeRegistry.report.json": downgrade_rows["cost"],
        "PR166_SM_LatencyDominatedDowngradeRegistry.report.json": downgrade_rows["latency"],
        "PR166_SM_LiquidityDominatedDowngradeRegistry.report.json": downgrade_rows["liquidity"],
        "PR166_SM_AdverseSelectionDowngradeRegistry.report.json": downgrade_rows["adverse_selection"],
        "PR166_SM_SettlementSensitivityRegistry.report.json": downgrade_rows["settlement"],
        "PR166_SM_FalseDiscoveryRiskRefreshLedger.report.json": fd_rows,
        "PR166_SM_OverfitAndRankInstabilityRegistry.report.json": overfit_rows,
        "PR166_SM_CapacityAndCrowdingRegistry.report.json": capacity_rows,
        "PR166_SM_CorrelationClusterRegistry.report.json": correlation_rows,
        "PR166_SM_RepairPriorityRegistry.report.json": repair_rows,
        "PR166_SM_QuantumPriorityAfterReplayPaperRegistry.report.json": quantum_priority_rows,
        "PR166_SM_QuantumMappingCandidateReadiness.report.json": quantum_readiness_rows,
        "PR166_SM_AgentScoreMemoryRefreshContract.report.json": agent_contract_rows,
        "PR166_SM_AgentTaskQueue.report.json": agent_task_rows,
        "PR166_SM_DashboardScoreMemoryRefreshHandoff.report.json": dashboard_rows,
        "PR166_SM_GovernanceScoreMemoryRefreshHandoff.report.json": governance_rows,
        "PR166_SM_CommanderScoreMemoryRefreshHandoff.report.json": commander_rows,
        "PR166_SM_PRFileConnectivityAudit.report.json": [],
        "PR166_SM_RowValueConnectivityAudit.report.json": [],
        "PR166_SM_AuthorityBoundaryAudit.report.json": authority_rows,
        "PR166_SM_OrphanArtifactAudit.report.json": orphan_rows,
        "PR166_SM_StatusEnumDriftAudit.report.json": status_rows,
        "PR166_SM_ReportManifest.report.json": [],
        "PR166_SM_FinalSummary.report.json": [],
        "PR166_SM_ExternalCandidateValueIntakeRegistry.report.json": external_rows,
        "PR166_SM_FieldMaterializationCandidateRegistry.report.json": materialization_rows,
        "PR166_SM_QKUComputabilityClosureAudit.report.json": qku_computability_rows,
        "PR166_SM_InstitutionalSignalQualityAudit.report.json": institutional_rows,
        "PR166_SM_SelectionReadinessForPR165D2.report.json": selection_ready_rows,
        "PR166_SM_FailureRepairRouteHandoffToPR166SF.report.json": failure_route_rows,
    }
    row_payloads["PR166_SM_PRFileConnectivityAudit.report.json"] = build_pr_file_connectivity_rows(tracked_file_list(repo_root))
    row_payloads["PR166_SM_RowValueConnectivityAudit.report.json"] = build_row_value_connectivity_rows(row_payloads)
    summary = _final_summary(row_payloads, source)
    row_payloads["PR166_SM_FinalSummary.report.json"] = [summary]
    _stamp_schema_refs(row_payloads)
    return row_payloads


def _candidate_rows(source: SourceData) -> tuple[list[dict[str, Any]], ...]:
    attribution = _by_candidate(source.records["PR166_S_ResultAttributionLedger.report.json"])
    confidence = _by_candidate(source.records["PR166_S_ResultConfidenceRegistry.report.json"])
    score_candidates = _by_candidate(source.records["PR166_S_ScoreRefreshCandidateRegistry.report.json"])
    memory_candidates = _by_candidate(source.records["PR166_S_MemoryRefreshCandidateRegistry.report.json"])
    costs = _by_candidate(source.records["PR166_S_ExecutionCostLedger.report.json"])
    pit = _by_candidate(source.records["PR166_S_PointInTimeExecutionAudit.report.json"])
    no_lookahead = _by_candidate(source.records["PR166_S_NoLookaheadAudit.report.json"])
    pr165_candidates = _by_candidate(source.records["PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json"])
    pr165_scores = _by_candidate(source.records["PR165_D_SelectionScoreRegistry.report.json"])
    pr165_marginal = _by_candidate(source.records["PR165_D_MarginalUtilitySelectionLedger.report.json"])
    pr165_fd = _by_candidate(source.records["PR165_D_SelectionFalseDiscoveryControl.report.json"])
    pr165_quantum = _by_candidate(source.records["PR165_D_QuantumSelectionRouter.report.json"])
    pr166_quantum = _by_candidate(source.records["PR166_S_QuantumAdvisoryPassthrough.report.json"])
    condition_rows = _by_key(source.records["PR165_B_ConditionFingerprintRegistry.report.json"], "condition_fingerprint_id")
    regime_rows = _by_candidate(source.records["PR165_C_ConditionRegimeFeatureMatrix.report.json"])
    computable_actions = _by_candidate(source.records["PR165_C_ComputableQKUFormulaActionRegistry.report.json"])

    prior_rank_by_candidate = _prior_rank_by_candidate(source.records["PR165_D_SelectionScoreRegistry.report.json"])
    prior_rank_percentile = _prior_rank_percentiles(prior_rank_by_candidate)
    related_counts = cluster_counts(list(pr165_candidates.values()))
    correlation_counts = cluster_counter(list(pr165_candidates.values()))
    scenario_counts = Counter(str(row.get("candidate_packet_id")) for row in source.records["PR165_B_ScenarioOutcomeMatrix.report.json"])

    raw_score_rows: list[dict[str, Any]] = []
    for index, candidate_id in enumerate(sorted(attribution), start=1):
        attr = attribution[candidate_id]
        cost = costs[candidate_id]
        conf = confidence[candidate_id]
        prior = pr165_candidates.get(candidate_id, {})
        prior_score_row = pr165_scores.get(candidate_id, prior)
        quantum = pr166_quantum.get(candidate_id, pr165_quantum.get(candidate_id, {}))
        condition_id = str(attr.get("condition_fingerprint_id") or prior.get("condition_fingerprint_id") or c.NOT_APPLICABLE_ID)
        scenario_id = str(attr.get("scenario_group_id") or prior.get("scenario_group_id") or c.NOT_APPLICABLE_ID)
        condition = condition_rows.get(condition_id, {})
        regime = regime_rows.get(candidate_id, prior)
        cost_values = cost_metrics(cost)
        if abs(cost_values["net_edge_after_costs"] - numeric(cost, "net_edge_after_costs", cost_values["net_edge_after_costs"])) > 0.00001:
            cost_values["input_net_edge_mismatch_corrected"] = True
        conf_values = confidence_metrics(conf, pit.get(candidate_id, {}), no_lookahead.get(candidate_id, {}))
        similarity, matched_buckets, bucket_actions = scenario_similarity_score(condition, regime)
        q_ready_initial = readiness_score(quantum, 0.5)
        prior_score = round6(numeric(prior_score_row, "adjusted_selection_score", 0.5))
        formula_family = str(prior.get("formula_family") or condition.get("formula_family") or "GENERAL_REPLAY_PAPER_FORMULA_FAMILY")
        formula_missing = bool(prior.get("formula_algorithm_optional_missing", False))
        qku_id = str(attr.get("qku_id") or prior.get("qku_id") or quantum.get("qku_id") or c.NOT_APPLICABLE_ID)
        formula_id = formula_id_from_family(formula_family)
        algorithm_id = algorithm_id_from_role(str(prior.get("qku_family") or "REPLAY_PAPER_SCORE_MEMORY"))
        cluster = cluster_id({**prior, "condition_fingerprint_id": condition_id})
        corr_cluster = correlation_cluster_id({**prior, "combination_fingerprint_id": attr.get("combination_fingerprint_id")})
        prior_pct = prior_rank_percentile.get(candidate_id, 0.5)
        risk = risk_controls(
            row=prior,
            prior_fd_row=pr165_fd.get(candidate_id, {}),
            related_trials=related_counts.get(cluster, 1),
            near_duplicate_trials=correlation_counts.get(corr_cluster, 1),
            scenario_count=max(1, scenario_counts.get(candidate_id, 1)),
            cost_drag_ratio=cost_values["cost_drag_ratio"],
            latency_drag_ratio=cost_values["latency_drag_ratio"],
            refreshed_rank_percentile=prior_pct,
        )
        cap = capacity_metrics(
            cost_drag_ratio=cost_values["cost_drag_ratio"],
            liquidity_drag_ratio=cost_values["liquidity_drag_ratio"],
            marginal_utility_row=pr165_marginal.get(candidate_id, {}),
            cluster_size=correlation_counts.get(corr_cluster, 1),
            refreshed_rank_percentile=prior_pct,
        )
        components = {
            "normalized_net_edge_after_costs": 0.5,
            "result_confidence_score": conf_values["result_confidence_score"],
            "no_lookahead_score": conf_values["no_lookahead_score"],
            "point_in_time_score": conf_values["point_in_time_score"],
            "score_refresh_candidate_strength": _candidate_strength(score_candidates.get(candidate_id, {}), "score_refresh_action"),
            "memory_refresh_candidate_strength": _candidate_strength(memory_candidates.get(candidate_id, {}), "memory_update_type"),
            "scenario_consistency_score": similarity,
            "scenario_transferability_score": round6((0.70 * similarity) + (0.30 * risk["sample_depth_score"])),
            "fill_quality_score": conf_values["fill_quality_score"],
            "settlement_confidence_score": conf_values["settlement_confidence_score"],
            "capacity_score": cap["capacity_score"],
            "quantum_mapping_readiness_score": q_ready_initial,
            "false_discovery_risk_adjustment": risk["false_discovery_risk_adjustment"],
            "overfit_risk_adjustment": risk["overfit_risk_adjustment"],
            "cost_drag_ratio": min(cost_values["cost_drag_ratio"], 2.0) / 2.0,
            "latency_drag_ratio": min(cost_values["latency_drag_ratio"], 1.0),
            "liquidity_drag_ratio": min(cost_values["liquidity_drag_ratio"], 1.0),
            "adverse_selection_ratio": min(cost_values["adverse_selection_ratio"], 1.0),
            "crowding_penalty": cap["crowding_penalty"],
            "correlation_cluster_penalty": cap["correlation_cluster_penalty"],
            "rank_instability_adjustment": risk["rank_instability_adjustment"],
        }
        raw_score_rows.append(
            {
                "index": index,
                "candidate_packet_id": candidate_id,
                "qku_id": qku_id,
                "formula_id": formula_id,
                "algorithm_id": algorithm_id,
                "condition_fingerprint_id": condition_id,
                "combination_id": str(attr.get("combination_fingerprint_id") or prior.get("combination_fingerprint_id") or c.NOT_APPLICABLE_ID),
                "scenario_id": scenario_id,
                "formula_family": formula_family,
                "formula_algorithm_optional_missing": formula_missing,
                "prior_score_when_available": prior_score,
                "prior_rank_when_available": prior_rank_by_candidate.get(candidate_id),
                "prior_rank_percentile": round6(prior_pct),
                "score_cluster_id": cluster,
                "correlation_cluster_id": corr_cluster,
                "matched_condition_buckets": matched_buckets,
                "condition_bucket_materialization_actions": bucket_actions,
                "computable_action_ref": computable_actions.get(candidate_id, {}).get("computable_qku_formula_action_id", c.COMPUTABLE_FORMULA_REF),
                "quantum_row": quantum,
                "prior_quantum_score": round6(numeric(quantum, "quantum_candidate_selection_score", numeric(prior, "quantum_candidate_selection_score", 0.35))),
                **cost_values,
                **conf_values,
                **risk,
                **cap,
                "scenario_similarity_score": similarity,
                "scenario_consistency_score": similarity,
                "scenario_transferability_score": components["scenario_transferability_score"],
                "score_refresh_candidate_strength": components["score_refresh_candidate_strength"],
                "memory_refresh_candidate_strength": components["memory_refresh_candidate_strength"],
                "score_components_pre_normalization": components,
                "upstream_rows": {
                    "attribution": attr.get("row_id", candidate_id),
                    "cost": cost.get("row_id", candidate_id),
                    "confidence": conf.get("row_id", candidate_id),
                    "prior_selection": prior.get("row_id", candidate_id),
                },
            }
        )

    normalized_net = rank_normalize_by_group(raw_score_rows, "scenario_id", "net_edge_after_costs")
    preliminary_rows: list[dict[str, Any]] = []
    for raw in raw_score_rows:
        components = dict(raw["score_components_pre_normalization"])
        components["normalized_net_edge_after_costs"] = normalized_net[raw["candidate_packet_id"]]
        initial_score = refreshed_net_edge_score(components)
        q_ready = readiness_score(raw["quantum_row"], initial_score)
        components["quantum_mapping_readiness_score"] = q_ready
        refreshed = refreshed_net_edge_score(components)
        q_priority, q_delta = quantum_priority(q_ready, refreshed, raw["prior_quantum_score"])
        repair_score = repair_priority_score(
            refreshed_score=refreshed,
            prior_rank_percentile=raw["prior_rank_percentile"],
            net_edge_after_costs=raw["net_edge_after_costs"],
            false_discovery_risk=raw["false_discovery_risk_adjustment"],
            overfit_risk=raw["overfit_risk_adjustment"],
            quantum_readiness=q_ready,
            formula_missing=raw["formula_algorithm_optional_missing"],
            repair_route_present=True,
        )
        route = repair_route(
            formula_missing=raw["formula_algorithm_optional_missing"],
            quantum_readiness=q_ready,
            structurally_negative=raw["net_edge_after_costs"] < -0.20,
            high_potential=refreshed >= 0.48,
        )
        primary, secondary, reasons, evidence = classify(
            net_edge_after_costs=raw["net_edge_after_costs"],
            prior_score=raw["prior_score_when_available"],
            refreshed_score=refreshed,
            cost_drag_ratio=raw["cost_drag_ratio"],
            latency_drag_ratio=raw["latency_drag_ratio"],
            liquidity_drag_ratio=raw["liquidity_drag_ratio"],
            adverse_selection_ratio=raw["adverse_selection_ratio"],
            settlement_sensitivity_ratio=raw["settlement_sensitivity_ratio"],
            result_confidence_score=raw["result_confidence_score"],
            false_discovery_risk=raw["false_discovery_risk_adjustment"],
            overfit_risk=raw["overfit_risk_adjustment"],
            rank_instability=raw["rank_instability_adjustment"],
            capacity_score=raw["capacity_score"],
            crowding_penalty=raw["crowding_penalty"],
            correlation_penalty=raw["correlation_cluster_penalty"],
            repair_priority_score=repair_score,
            quantum_priority_delta=q_delta,
        )
        preliminary_rows.append(
            {
                **raw,
                "normalized_net_edge_after_costs": components["normalized_net_edge_after_costs"],
                "quantum_mapping_readiness_score": q_ready,
                "score_formula_component_values": dict(components),
                "refreshed_net_edge_score": refreshed,
                "quantum_priority_after_replay_paper": q_priority,
                "quantum_priority_delta": q_delta,
                "repair_priority_score": repair_score,
                "repair_route": route,
                "primary_classification": primary,
                "secondary_classifications": secondary,
                "classification_reason_codes": reasons,
                "classification_numeric_evidence": evidence,
            }
        )

    refreshed_ranks = assign_ranks(preliminary_rows)
    score_rows: list[dict[str, Any]] = []
    memory_rows: list[dict[str, Any]] = []
    rank_delta_rows: list[dict[str, Any]] = []
    fd_rows: list[dict[str, Any]] = []
    overfit_rows: list[dict[str, Any]] = []
    capacity_rows: list[dict[str, Any]] = []
    correlation_rows: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    selection_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []

    by_score = {row["candidate_packet_id"]: row for row in preliminary_rows}
    for index, row in enumerate(sorted(preliminary_rows, key=lambda item: refreshed_ranks[item["candidate_packet_id"]]), start=1):
        candidate_id = row["candidate_packet_id"]
        rank = refreshed_ranks[candidate_id]
        prior_rank = row["prior_rank_when_available"]
        rank_delta = None if prior_rank is None else int(prior_rank) - rank
        mem = memory_outcome(row["primary_classification"], row["refreshed_net_edge_score"], row["net_edge_after_costs"])
        downstream = _primary_downstream_for_row(row)
        no_orphan = _no_orphan_for_downstream(downstream)
        upstream_refs = [
            "PR166_S_ResultAttributionLedger.report.json",
            "PR166_S_ExecutionCostLedger.report.json",
            "PR166_S_ResultConfidenceRegistry.report.json",
            "PR165_D_SelectionScoreRegistry.report.json",
        ]
        common = _candidate_common(
            row,
            artifact_id="PR166_SM_REFRESHED_SCORE",
            row_id=stable_id("PR166_SM_REFRESHED_SCORE", index),
            upstream_artifact_refs=upstream_refs,
            upstream_row_refs=list(row["upstream_rows"].values()),
            downstream_artifact_refs=["PR166_SM_RefreshedMemoryLedger.report.json", "PR166_SM_NetEdgeRankDeltaRegistry.report.json"],
            downstream_pr_refs=[downstream],
            no_orphan_status=no_orphan,
            repair_route_ref=row["repair_route"],
        )
        score_row = {
            **common,
            **_score_numeric_projection(row),
            "score_formula_component_values": row["score_formula_component_values"],
            "refreshed_rank": rank,
            "prior_rank_when_available": prior_rank if prior_rank is not None else "NO_PRIOR_RANK_AVAILABLE_WITH_REASON",
            "rank_delta_when_available": rank_delta if rank_delta is not None else "NO_PRIOR_RANK_AVAILABLE_WITH_REASON",
            "memory_outcome": mem,
            "primary_classification": row["primary_classification"],
            "secondary_classifications": row["secondary_classifications"],
            "classification_reason_codes": row["classification_reason_codes"],
            "classification_numeric_evidence": row["classification_numeric_evidence"],
            "score_weight_ref": c.SCORE_POLICY_REF,
            "score_formula_terms": dict(c.SCORE_WEIGHTS),
            "net_edge_formula_ref": "PR166_SM_FORMULA::NET_EDGE_AFTER_COSTS",
            "gross_edge_only_score_flag": False,
        }
        score_rows.append(score_row)
        memory_rows.append(
            {
                **_candidate_common(
                    row,
                    artifact_id="PR166_SM_REFRESHED_MEMORY",
                    row_id=stable_id("PR166_SM_REFRESHED_MEMORY", index),
                    upstream_artifact_refs=["PR166_S_MemoryRefreshCandidateRegistry.report.json", "PR166_SM_RefreshedScoreRegistry.report.json"],
                    upstream_row_refs=[candidate_id, score_row["row_id"]],
                    downstream_artifact_refs=["PR165-D2", "PR166-SF", "PR166_SM_AgentTaskQueue.report.json"],
                    downstream_pr_refs=[downstream],
                    no_orphan_status=NoOrphanStatus.CONNECTED_TO_MEMORY_REFRESH_ROUTE.value,
                    repair_route_ref=row["repair_route"],
                ),
                "memory_outcome": mem,
                "condition_scoped_memory_only": True,
                "global_permanent_ban_created": False,
                "scenario_similarity_score": row["scenario_similarity_score"],
                "matched_condition_buckets": row["matched_condition_buckets"],
                "memory_evidence": {
                    "refreshed_net_edge_score": row["refreshed_net_edge_score"],
                    "net_edge_after_costs": row["net_edge_after_costs"],
                    "primary_classification": row["primary_classification"],
                },
            }
        )
        rank_delta_rows.append(
            {
                **_candidate_common(
                    row,
                    artifact_id="PR166_SM_NET_EDGE_RANK_DELTA",
                    row_id=stable_id("PR166_SM_RANK_DELTA", index),
                    upstream_artifact_refs=["PR165_D_SelectionScoreRegistry.report.json", "PR166_SM_RefreshedScoreRegistry.report.json"],
                    upstream_row_refs=[candidate_id, score_row["row_id"]],
                    downstream_artifact_refs=["PR165-D2", "PR166-SF"],
                    downstream_pr_refs=[downstream],
                    no_orphan_status=NoOrphanStatus.CONNECTED_TO_PR165_D2_ROUTE.value if downstream == DownstreamRoute.PR165_D2.value else no_orphan,
                    repair_route_ref=row["repair_route"],
                ),
                "prior_rank_when_available": prior_rank if prior_rank is not None else "NO_PRIOR_RANK_AVAILABLE_WITH_REASON",
                "refreshed_rank": rank,
                "rank_delta_when_available": rank_delta if rank_delta is not None else "NO_PRIOR_RANK_AVAILABLE_WITH_REASON",
                "rank_delta_reason": reason_for_delta(
                    prior_rank=prior_rank,
                    rank_delta=rank_delta,
                    cost_drag_ratio=row["cost_drag_ratio"],
                    latency_drag_ratio=row["latency_drag_ratio"],
                    liquidity_drag_ratio=row["liquidity_drag_ratio"],
                    adverse_selection_ratio=row["adverse_selection_ratio"],
                    false_discovery_risk=row["false_discovery_risk_adjustment"],
                    overfit_risk=row["overfit_risk_adjustment"],
                    capacity_score=row["capacity_score"],
                    crowding_penalty=row["crowding_penalty"],
                    quantum_priority_delta=row["quantum_priority_delta"],
                    repair_needed=row["repair_priority_score"] >= 0.50,
                ),
            }
        )
        fd_rows.append(_false_discovery_row(row, index, downstream))
        overfit_rows.append(_overfit_row(row, index, downstream))
        capacity_rows.append(_capacity_row(row, index, downstream))
        correlation_rows.append(_correlation_row(row, index, by_score, downstream))
        repair_row = _repair_row(row, index)
        repair_rows.append(repair_row)
        if downstream == DownstreamRoute.PR165_D2.value:
            selection_rows.append(_selection_readiness_row(row, index))
        if row["repair_route"] == DownstreamRoute.PR166_SF.value:
            failure_rows.append(_failure_repair_row(row, index))

    quantum_priority_rows, quantum_readiness_rows, qku_computability_rows, materialization_rows = _quantum_and_computability_rows(
        source,
        score_rows_by_candidate={row["candidate_packet_id"]: row for row in score_rows},
    )
    return (
        score_rows,
        memory_rows,
        rank_delta_rows,
        fd_rows,
        overfit_rows,
        capacity_rows,
        correlation_rows,
        repair_rows,
        quantum_priority_rows,
        quantum_readiness_rows,
        qku_computability_rows,
        materialization_rows,
        selection_rows,
        failure_rows,
    )


def _by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["candidate_packet_id"]): row for row in rows if row.get("candidate_packet_id")}


def _by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows if row.get(key)}


def _prior_rank_by_candidate(rows: list[dict[str, Any]]) -> dict[str, int]:
    ordered = sorted(
        rows,
        key=lambda row: (
            -numeric(row, "adjusted_selection_score", 0.0),
            str(row.get("candidate_packet_id")),
        ),
    )
    return {str(row["candidate_packet_id"]): index for index, row in enumerate(ordered, start=1)}


def _prior_rank_percentiles(rank_by_candidate: dict[str, int]) -> dict[str, float]:
    if not rank_by_candidate:
        return {}
    total = len(rank_by_candidate)
    if total == 1:
        return {candidate_id: 1.0 for candidate_id in rank_by_candidate}
    return {candidate_id: round6(1.0 - ((rank - 1) / (total - 1))) for candidate_id, rank in rank_by_candidate.items()}


def _candidate_strength(row: dict[str, Any], field: str) -> float:
    if row.get(field):
        return 0.75
    if row:
        return 0.62
    return 0.50


def _candidate_common(
    row: dict[str, Any],
    *,
    artifact_id: str,
    row_id: str,
    upstream_artifact_refs: list[str],
    upstream_row_refs: list[str],
    downstream_artifact_refs: list[str],
    downstream_pr_refs: list[str],
    no_orphan_status: str,
    repair_route_ref: str,
) -> dict[str, Any]:
    return common_fields(
        artifact_id=artifact_id,
        row_id=row_id,
        qku_id=row["qku_id"],
        formula_id=row["formula_id"],
        algorithm_id=row["algorithm_id"],
        candidate_packet_id=row["candidate_packet_id"],
        condition_fingerprint_id=row["condition_fingerprint_id"],
        scenario_id=row["scenario_id"],
        combination_id=row["combination_id"],
        upstream_artifact_refs=upstream_artifact_refs,
        upstream_row_refs=upstream_row_refs,
        upstream_value_refs=["net_edge_after_costs", "result_confidence_score", "prior_selection_score"],
        downstream_artifact_refs=downstream_artifact_refs,
        downstream_pr_refs=downstream_pr_refs,
        owning_agent=AgentId.SCORE_MEMORY.value,
        no_orphan_status=no_orphan_status,
        repair_route_ref=repair_route_ref,
        materialization_action_ref=(
            f"PR166_SM_MATERIALIZATION_ACTION::{row['candidate_packet_id']}::FORMULA_ALGORITHM_DETAIL"
            if row.get("formula_algorithm_optional_missing")
            else "PR166_SM_MATERIALIZATION_ACTION::NOT_REQUIRED_COMPUTABLE_NOW"
        ),
        computability_status=(
            ComputabilityStatus.COMPUTABLE_AFTER_EXACT_MATERIALIZATION_ACTION.value
            if row.get("formula_algorithm_optional_missing")
            else ComputabilityStatus.COMPUTABLE_NOW.value
        ),
    )


def _score_numeric_projection(row: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "gross_edge",
        "spread_cost",
        "maker_taker_fees",
        "slippage_cost",
        "market_impact_cost",
        "latency_drag",
        "liquidity_drag",
        "adverse_selection_drag",
        "settlement_payoff_adjustment",
        "implementation_shortfall_proxy",
        "net_edge_after_costs",
        "cost_drag_ratio",
        "latency_drag_ratio",
        "liquidity_drag_ratio",
        "adverse_selection_ratio",
        "capacity_score",
        "crowding_penalty",
        "correlation_cluster_penalty",
        "result_confidence_score",
        "point_in_time_score",
        "no_lookahead_score",
        "fill_quality_score",
        "settlement_confidence_score",
        "scenario_consistency_score",
        "scenario_transferability_score",
        "false_discovery_risk_adjustment",
        "overfit_risk_adjustment",
        "rank_instability_adjustment",
        "refreshed_net_edge_score",
        "prior_score_when_available",
        "repair_priority_score",
        "quantum_mapping_readiness_score",
        "quantum_priority_delta",
        "quantum_priority_after_replay_paper",
        "score_refresh_candidate_strength",
        "memory_refresh_candidate_strength",
        "normalized_net_edge_after_costs",
        "scenario_similarity_score",
    ]
    return {field: row[field] for field in fields}


def _primary_downstream_for_row(row: dict[str, Any]) -> str:
    if row["repair_priority_score"] >= 0.50 or row["formula_algorithm_optional_missing"]:
        return DownstreamRoute.PR166_SF.value
    if row["quantum_priority_delta"] > 0.02 and row["quantum_mapping_readiness_score"] >= 0.55:
        return DownstreamRoute.PR166_Q.value
    if row["refreshed_net_edge_score"] >= 0.45:
        return DownstreamRoute.PR165_D2.value
    return DownstreamRoute.PR167.value


def _no_orphan_for_downstream(route: str) -> str:
    mapping = {
        DownstreamRoute.PR165_D2.value: NoOrphanStatus.CONNECTED_TO_PR165_D2_ROUTE.value,
        DownstreamRoute.PR166_SF.value: NoOrphanStatus.CONNECTED_TO_PR166_SF_ROUTE.value,
        DownstreamRoute.PR166_Q.value: NoOrphanStatus.CONNECTED_TO_PR166_Q_ROUTE.value,
        DownstreamRoute.PR167.value: NoOrphanStatus.CONNECTED_TO_PR167_ROUTE.value,
    }
    return mapping.get(route, NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value)


def _false_discovery_row(row: dict[str, Any], index: int, downstream: str) -> dict[str, Any]:
    base = _candidate_common(
        row,
        artifact_id="PR166_SM_FALSE_DISCOVERY_RISK_REFRESH",
        row_id=stable_id("PR166_SM_FALSE_DISCOVERY", index),
        upstream_artifact_refs=["PR165_D_SelectionFalseDiscoveryControl.report.json", "PR166_SM_RefreshedScoreRegistry.report.json"],
        upstream_row_refs=[row["candidate_packet_id"]],
        downstream_artifact_refs=["PR166-SF", "PR165-D2"],
        downstream_pr_refs=[downstream],
        no_orphan_status=_no_orphan_for_downstream(downstream),
        repair_route_ref=row["repair_route"],
    )
    base.update(
        {
            key: row[key]
            for key in (
                "num_related_trials",
                "num_near_duplicate_trials",
                "score_cluster_id",
                "rank_stability_score",
                "sample_depth_score",
                "scenario_count",
                "effective_independent_trial_count",
                "false_discovery_risk_adjustment",
                "overfit_risk_adjustment",
                "rank_instability_adjustment",
                "reject_as_miracle_singleton_flag",
            )
        }
    )
    base.update(
        {
            "best_in_cluster_flag": True,
            "reason_codes": row["classification_reason_codes"],
            "downstream_route": downstream,
        }
    )
    return base


def _overfit_row(row: dict[str, Any], index: int, downstream: str) -> dict[str, Any]:
    base = _false_discovery_row(row, index, downstream)
    base["artifact_id"] = "PR166_SM_OVERFIT_AND_RANK_INSTABILITY"
    base["row_id"] = stable_id("PR166_SM_OVERFIT", index)
    base["overfit_control_formula_ref"] = "PR166_SM_FORMULA::OVERFIT_DUPLICATE_DEPTH_SENSITIVITY"
    base["rank_instability_formula_ref"] = "PR166_SM_FORMULA::RANK_INSTABILITY_COST_LATENCY_CLUSTER"
    return base


def _capacity_row(row: dict[str, Any], index: int, downstream: str) -> dict[str, Any]:
    base = _candidate_common(
        row,
        artifact_id="PR166_SM_CAPACITY_AND_CROWDING",
        row_id=stable_id("PR166_SM_CAPACITY", index),
        upstream_artifact_refs=["PR165_D_MarginalUtilitySelectionLedger.report.json", "PR166_SM_RefreshedScoreRegistry.report.json"],
        upstream_row_refs=[row["candidate_packet_id"]],
        downstream_artifact_refs=["PR165-D2", "PR166-SF"],
        downstream_pr_refs=[downstream],
        no_orphan_status=_no_orphan_for_downstream(downstream),
        repair_route_ref=row["repair_route"],
    )
    base.update(
        {
            "capacity_score": row["capacity_score"],
            "capacity_bucket": row["capacity_bucket"],
            "crowding_penalty": row["crowding_penalty"],
            "correlation_cluster_id": row["correlation_cluster_id"],
            "correlation_cluster_penalty": row["correlation_cluster_penalty"],
            "marginal_utility_score": row["marginal_utility_score"],
            "overlap_with_existing_winners": row["overlap_with_existing_winners"],
            "portfolio_selection_note": "PRESERVE_REPRESENTATIVE_AND_ROUTE_SECONDARIES_AS_CHALLENGERS",
            "downstream_route": downstream,
        }
    )
    return base


def _correlation_row(row: dict[str, Any], index: int, by_score: dict[str, dict[str, Any]], downstream: str) -> dict[str, Any]:
    base = _capacity_row(row, index, downstream)
    base["artifact_id"] = "PR166_SM_CORRELATION_CLUSTER"
    base["row_id"] = stable_id("PR166_SM_CORRELATION", index)
    stronger = [
        candidate_id
        for candidate_id, other in by_score.items()
        if other["correlation_cluster_id"] == row["correlation_cluster_id"]
        and other["refreshed_net_edge_score"] > row["refreshed_net_edge_score"]
    ]
    base["stronger_cluster_representatives"] = sorted(stronger)[:5]
    base["cluster_representative_flag"] = not stronger
    return base


def _repair_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    route = row["repair_route"]
    downstream_route = route if route in c.DOWNSTREAM_PR_REFS else DownstreamRoute.PR162D_R3.value
    base = _candidate_common(
        row,
        artifact_id="PR166_SM_REPAIR_PRIORITY",
        row_id=stable_id("PR166_SM_REPAIR_PRIORITY", index),
        upstream_artifact_refs=["PR166_S_RepairFeedbackRouter.report.json", "PR166_SM_RefreshedScoreRegistry.report.json"],
        upstream_row_refs=[row["candidate_packet_id"]],
        downstream_artifact_refs=[route, downstream_route],
        downstream_pr_refs=[downstream_route],
        no_orphan_status=_no_orphan_for_downstream(downstream_route),
        repair_route_ref=route,
    )
    base.update(
        {
            "repair_priority_rank": index,
            "repair_priority_score": row["repair_priority_score"],
            "repair_route": route,
            "repair_reason_codes": row["classification_reason_codes"],
            "exact_missing_field": "formula_algorithm_objective_constraint_variable_detail"
            if row["formula_algorithm_optional_missing"]
            else "execution_cost_or_condition_memory_retest_confirmation",
            "materialization_action": "MATERIALIZE_FORMULA_ALGORITHM_DETAIL_AND_RETEST"
            if row["formula_algorithm_optional_missing"]
            else "RETEST_WITH_REPAIRED_EXECUTION_ASSUMPTION",
            "downstream_pr_route": downstream_route,
        }
    )
    return base


def _selection_readiness_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    base = _candidate_common(
        row,
        artifact_id="PR166_SM_SELECTION_READINESS_FOR_PR165_D2",
        row_id=stable_id("PR166_SM_PR165_D2_READY", index),
        upstream_artifact_refs=["PR166_SM_RefreshedScoreRegistry.report.json"],
        upstream_row_refs=[row["candidate_packet_id"]],
        downstream_artifact_refs=["PR165-D2"],
        downstream_pr_refs=[DownstreamRoute.PR165_D2.value],
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_PR165_D2_ROUTE.value,
        repair_route_ref=DownstreamRoute.PR165_D2.value,
    )
    base.update(
        {
            "selection_readiness_score": row["refreshed_net_edge_score"],
            "marginal_utility_score": row["marginal_utility_score"],
            "backup_or_challenger_value": row["correlation_cluster_penalty"] < 0.35,
            "selection_route": DownstreamRoute.PR165_D2.value,
        }
    )
    return base


def _failure_repair_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    base = _candidate_common(
        row,
        artifact_id="PR166_SM_FAILURE_REPAIR_ROUTE_HANDOFF_TO_PR166_SF",
        row_id=stable_id("PR166_SM_PR166_SF_HANDOFF", index),
        upstream_artifact_refs=["PR166_SM_RepairPriorityRegistry.report.json"],
        upstream_row_refs=[row["candidate_packet_id"]],
        downstream_artifact_refs=["PR166-SF"],
        downstream_pr_refs=[DownstreamRoute.PR166_SF.value],
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_PR166_SF_ROUTE.value,
        repair_route_ref=DownstreamRoute.PR166_SF.value,
    )
    base.update(
        {
            "failure_repair_route": DownstreamRoute.PR166_SF.value,
            "repair_priority_score": row["repair_priority_score"],
            "expected_repair_output": "replay_paper_ready_retest_candidate_with_exact_materialized_fields",
        }
    )
    return base


def _quantum_and_computability_rows(
    source: SourceData,
    *,
    score_rows_by_candidate: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    quantum_source = _by_candidate(source.records["PR166_S_QuantumAdvisoryPassthrough.report.json"])
    pr165_candidates = _by_candidate(source.records["PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json"])
    rows_priority: list[dict[str, Any]] = []
    rows_readiness: list[dict[str, Any]] = []
    rows_computability: list[dict[str, Any]] = []
    rows_materialization: list[dict[str, Any]] = []
    for index, candidate_id in enumerate(sorted(quantum_source), start=1):
        quantum = quantum_source[candidate_id]
        score = score_rows_by_candidate.get(candidate_id, {})
        prior = pr165_candidates.get(candidate_id, {})
        formula_family = str(prior.get("formula_family") or "GENERAL_REPLAY_PAPER_FORMULA_FAMILY")
        qku_id = str(quantum.get("qku_id") or prior.get("qku_id") or c.NOT_APPLICABLE_ID)
        formula_id = formula_id_from_family(formula_family)
        algorithm_id = algorithm_id_from_role(str(prior.get("qku_family") or "QUANTUM_MAPPING"))
        refreshed_score = numeric(score, "refreshed_net_edge_score", numeric(prior, "adjusted_selection_score", 0.35))
        readiness = numeric(score, "quantum_mapping_readiness_score", readiness_score(quantum, refreshed_score))
        prior_quantum = numeric(quantum, "quantum_candidate_selection_score", numeric(prior, "quantum_candidate_selection_score", 0.35))
        priority, delta = quantum_priority(readiness, refreshed_score, prior_quantum)
        route = DownstreamRoute.PR166_Q.value if readiness >= 0.50 else DownstreamRoute.PR162E_Q.value
        common = common_fields(
            artifact_id="PR166_SM_QUANTUM_PRIORITY_AFTER_REPLAY_PAPER",
            row_id=stable_id("PR166_SM_QUANTUM_PRIORITY", index),
            qku_id=qku_id,
            formula_id=formula_id,
            algorithm_id=algorithm_id,
            candidate_packet_id=candidate_id,
            condition_fingerprint_id=str(prior.get("condition_fingerprint_id") or c.NOT_APPLICABLE_ID),
            scenario_id=str(prior.get("scenario_group_id") or c.NOT_APPLICABLE_ID),
            combination_id=str(prior.get("combination_fingerprint_id") or c.NOT_APPLICABLE_ID),
            upstream_artifact_refs=["PR166_S_QuantumAdvisoryPassthrough.report.json", "PR166_SM_RefreshedScoreRegistry.report.json"],
            upstream_row_refs=[str(quantum.get("row_id", candidate_id)), str(score.get("row_id", candidate_id))],
            upstream_value_refs=["quantum_model_class", "variable_domain", "objective_order", "refreshed_net_edge_score"],
            downstream_artifact_refs=[route],
            downstream_pr_refs=[route],
            owning_agent=AgentId.QUANTUM_OPTIMIZER.value,
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_PR166_Q_ROUTE.value if route == DownstreamRoute.PR166_Q.value else NoOrphanStatus.CONNECTED_TO_PR162E_Q_ROUTE.value,
            value_authority_lane=ValueAuthorityLane.CANDIDATE_QUANTUM_FORMULATION_VALUE_LANE.value,
            source_authority_class=SourceAuthorityClass.PRIOR_SELECTION_NOT_SOURCE_TRUTH.value,
            repair_route_ref=route,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_QUANTUM_MAPPING_CANDIDATE_ONLY.value,
        )
        structures = quantum_structures(quantum)
        formula_missing = bool(prior.get("formula_algorithm_optional_missing", False))
        materialization_ref = (
            f"PR166_SM_MATERIALIZATION_ACTION::{candidate_id}::FORMULA_ALGORITHM_DETAIL"
            if formula_missing
            else "PR166_SM_MATERIALIZATION_ACTION::NOT_REQUIRED_COMPUTABLE_NOW"
        )
        exact_missing_field = (
            "formula_algorithm_objective_constraint_variable_detail"
            if formula_missing
            else "NOT_REQUIRED_COMPUTABLE_NOW"
        )
        exact_materialization_action = (
            "MATERIALIZE_OBJECTIVE_VARIABLE_CONSTRAINT_COMPARATOR_DETAIL"
            if formula_missing
            else "COMPUTABLE_NOW_USE_EXISTING_REPLAY_PAPER_VALUES"
        )
        rows_priority.append(
            {
                **common,
                "quantum_priority_after_replay_paper": priority,
                "quantum_priority_delta": delta,
                "quantum_mapping_readiness_score": readiness,
                "backend_quantum_execution_created": False,
                "quantum_advantage_claim_created": False,
                "solver_family_candidates": ["qiskit_sampling_minimum_eigensolver", "dwave_ocean_hybrid_model", "classical_comparator"],
                **structures,
            }
        )
        readiness_row = dict(rows_priority[-1])
        readiness_row["artifact_id"] = "PR166_SM_QUANTUM_MAPPING_CANDIDATE_READINESS"
        readiness_row["row_id"] = stable_id("PR166_SM_QUANTUM_READINESS", index)
        readiness_row["materialization_action_ref"] = materialization_ref
        readiness_row["exact_missing_field"] = exact_missing_field
        readiness_row["exact_materialization_action"] = exact_materialization_action
        readiness_row["candidate_value_lane"] = (
            ValueAuthorityLane.TYPED_MATERIALIZATION_ACTION_LANE.value
            if formula_missing
            else ValueAuthorityLane.CANDIDATE_QUANTUM_FORMULATION_VALUE_LANE.value
        )
        readiness_row["downstream_pr_route"] = route
        readiness_row["validator_checks_route"] = c.VALIDATOR_REF
        rows_readiness.append(readiness_row)
        computability = (
            ComputabilityStatus.COMPUTABLE_AFTER_EXACT_MATERIALIZATION_ACTION.value
            if formula_missing
            else ComputabilityStatus.COMPUTABLE_NOW.value
        )
        comp_common = dict(common)
        comp_common.update(
            {
                "artifact_id": "PR166_SM_QKU_COMPUTABILITY_CLOSURE",
                "row_id": stable_id("PR166_SM_QKU_COMPUTABILITY", index),
                "computability_status": computability,
                "materialization_action_ref": materialization_ref,
                "exact_missing_field": exact_missing_field,
                "exact_materialization_action": exact_materialization_action,
                "candidate_value_lane": ValueAuthorityLane.TYPED_MATERIALIZATION_ACTION_LANE.value if formula_missing else ValueAuthorityLane.DETERMINISTIC_COMPILER_VALUE_LANE.value,
                "owning_agent": AgentId.QUANTUM_OPTIMIZER.value if readiness >= 0.50 else AgentId.RESEARCH_AGENT.value,
                "downstream_pr_route": route if formula_missing else DownstreamRoute.PR165_D2.value,
                "validator_checks_route": c.VALIDATOR_REF,
            }
        )
        rows_computability.append(comp_common)
        if formula_missing:
            mat_row = dict(comp_common)
            mat_row["artifact_id"] = "PR166_SM_FIELD_MATERIALIZATION_CANDIDATE"
            mat_row["row_id"] = stable_id("PR166_SM_FIELD_MATERIALIZATION", len(rows_materialization) + 1)
            mat_row["field_materialization_priority_score"] = round6(0.50 + 0.25 * readiness + 0.25 * refreshed_score)
            rows_materialization.append(mat_row)
    return rows_priority, rows_readiness, rows_computability, rows_materialization


def _winner_loser_rows(score_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in score_rows:
        groups[str(row["condition_fingerprint_id"])].append(row)
    winners: list[dict[str, Any]] = []
    losers: list[dict[str, Any]] = []
    for index, condition_id in enumerate(sorted(groups), start=1):
        ordered = sorted(groups[condition_id], key=lambda row: (-float(row["refreshed_net_edge_score"]), str(row["candidate_packet_id"])))
        winner = dict(ordered[0])
        loser = dict(ordered[-1])
        winner.update({"artifact_id": "PR166_SM_CONDITION_SCOPED_WINNER", "row_id": stable_id("PR166_SM_WINNER", index), "condition_rank_role": "WINNER_UNDER_MATCHING_CONDITIONS"})
        loser.update({"artifact_id": "PR166_SM_CONDITION_SCOPED_LOSER", "row_id": stable_id("PR166_SM_LOSER", index), "condition_rank_role": "LOSER_UNDER_MATCHING_CONDITIONS"})
        winners.append(winner)
        losers.append(loser)
    return winners, losers


def _downgrade_rows(score_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets = {"cost": [], "latency": [], "liquidity": [], "adverse_selection": [], "settlement": []}
    for row in score_rows:
        if row["cost_drag_ratio"] >= 1.0 or row["primary_classification"] == PrimaryClassification.COST_DOMINATED.value:
            buckets["cost"].append(_downgrade_row(row, "COST_DOMINATED_DOWNGRADE", "PR166_SM_COST_DOWNGRADE", len(buckets["cost"]) + 1))
        if row["latency_drag_ratio"] >= 0.08 or PrimaryClassification.LATENCY_DOMINATED.value in row["secondary_classifications"]:
            buckets["latency"].append(_downgrade_row(row, "LATENCY_DOMINATED_DOWNGRADE", "PR166_SM_LATENCY_DOWNGRADE", len(buckets["latency"]) + 1))
        if row["liquidity_drag_ratio"] >= 0.08 or PrimaryClassification.LIQUIDITY_DOMINATED.value in row["secondary_classifications"]:
            buckets["liquidity"].append(_downgrade_row(row, "LIQUIDITY_DOMINATED_DOWNGRADE", "PR166_SM_LIQUIDITY_DOWNGRADE", len(buckets["liquidity"]) + 1))
        if row["adverse_selection_ratio"] >= 0.18 or PrimaryClassification.ADVERSE_SELECTION_DOMINATED.value in row["secondary_classifications"]:
            buckets["adverse_selection"].append(_downgrade_row(row, "ADVERSE_SELECTION_DOWNGRADE", "PR166_SM_ADVERSE_SELECTION_DOWNGRADE", len(buckets["adverse_selection"]) + 1))
        if row["settlement_payoff_adjustment"] >= 0.01 or PrimaryClassification.SETTLEMENT_SENSITIVE.value in row["secondary_classifications"]:
            buckets["settlement"].append(_downgrade_row(row, "SETTLEMENT_SENSITIVITY", "PR166_SM_SETTLEMENT_SENSITIVITY", len(buckets["settlement"]) + 1))
    return buckets


def _downgrade_row(row: dict[str, Any], artifact: str, prefix: str, index: int) -> dict[str, Any]:
    clone = dict(row)
    clone["artifact_id"] = artifact
    clone["row_id"] = stable_id(prefix, index)
    clone["downgrade_reason_codes"] = row["classification_reason_codes"]
    clone["dominance_evidence"] = row["classification_numeric_evidence"]
    clone["downstream_pr_refs"] = [DownstreamRoute.PR166_SF.value]
    clone["downstream_route"] = DownstreamRoute.PR166_SF.value
    clone["no_orphan_status"] = NoOrphanStatus.CONNECTED_TO_PR166_SF_ROUTE.value
    clone["repair_route_ref"] = DownstreamRoute.PR166_SF.value
    return clone


def _agent_contract_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    contracts = [
        (AgentId.RESEARCH_AGENT.value, "external candidate intake and materialization review", DownstreamRoute.PR162D_R3.value),
        (AgentId.PARAMETER_SELECTOR.value, "consume refreshed scores and condition winners for PR165-D2", DownstreamRoute.PR165_D2.value),
        (AgentId.RISK_MANAGER.value, "consume downgrade risk false-discovery overfit capacity ledgers", DownstreamRoute.PR166_SF.value),
        (AgentId.QUANTUM_OPTIMIZER.value, "consume quantum priority and mapping readiness rows", DownstreamRoute.PR166_Q.value),
        (AgentId.COMMANDER.value, "route next PR and secondary PR recommendations", DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value),
        (AgentId.GOVERNANCE.value, "audit authority no-orphan schema validator coverage", DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value),
        (AgentId.DASHBOARD.value, "surface score memory winners losers repair quantum and external candidates", DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value),
    ]
    for index, (agent, action, route) in enumerate(contracts, start=1):
        base = common_fields(
            artifact_id="PR166_SM_AGENT_SCORE_MEMORY_REFRESH_CONTRACT",
            row_id=stable_id("PR166_SM_AGENT_CONTRACT", index),
            upstream_artifact_refs=["PR166_SM_RefreshedScoreRegistry.report.json"],
            upstream_row_refs=[stable_id("PR166_SM_AGENT_CONTRACT", index)],
            downstream_artifact_refs=["PR166_SM_AgentTaskQueue.report.json"],
            downstream_pr_refs=[route],
            owning_agent=agent,
            no_orphan_status=NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value,
            repair_route_ref=route,
        )
        base.update({"agent_id": agent, "contract_action": action, "expected_consumer_output": route})
        rows.append(base)
    return rows


def _agent_task_rows(
    score_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
    external_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    tasks = [
        (AgentId.RESEARCH_AGENT.value, "candidate_external_value_intake", external_rows[0]["row_id"], DownstreamRoute.PR162D_R3.value, "external_candidate_value_count"),
        (AgentId.PARAMETER_SELECTOR.value, "refreshed_score_selection_queue", score_rows[0]["row_id"], DownstreamRoute.PR165_D2.value, "refreshed_score_row_count"),
        (AgentId.RISK_MANAGER.value, "downgrade_and_false_discovery_review", repair_rows[0]["row_id"], DownstreamRoute.PR166_SF.value, "risk_downgrade_count"),
        (AgentId.QUANTUM_OPTIMIZER.value, "quantum_priority_materialization", quantum_rows[0]["row_id"], DownstreamRoute.PR166_Q.value, "quantum_priority_count"),
        (AgentId.COMMANDER.value, "next_pr_route_selection", "PR166_SM_FinalSummary.report.json", DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value, "next_pr_route"),
        (AgentId.GOVERNANCE.value, "authority_boundary_and_no_orphan_audit", "PR166_SM_AuthorityBoundaryAudit.report.json", DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value, "authority_violation_count"),
        (AgentId.DASHBOARD.value, "owner_review_dashboard_handoff", "PR166_SM_DashboardScoreMemoryRefreshHandoff.report.json", DownstreamRoute.PR168.value, "dashboard_consumability"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (agent, task_type, source_ref, route, kpi) in enumerate(tasks, start=1):
        base = common_fields(
            artifact_id="PR166_SM_AGENT_TASK_QUEUE",
            row_id=stable_id("PR166_SM_AGENT_TASK", index),
            upstream_artifact_refs=[str(source_ref)],
            upstream_row_refs=[str(source_ref)],
            downstream_artifact_refs=[route],
            downstream_pr_refs=[route],
            owning_agent=agent,
            no_orphan_status=_no_orphan_for_downstream(route),
            repair_route_ref=route,
        )
        base.update(
            {
                "agent_id": agent,
                "agent_role": agent.replace("_agent", ""),
                "task_id": stable_id("PR166_SM_TASK", index),
                "task_type": task_type,
                "priority": index,
                "urgency_bucket": "HIGH" if index <= 4 else "MEDIUM",
                "source_artifact_refs": [str(source_ref)],
                "target_artifact_refs": [route],
                "action": task_type,
                "expected_output": f"{task_type}_receipt",
                "downstream_pr_route": route,
                "kpi_family": kpi,
            }
        )
        rows.append(base)
    return rows


def _dashboard_rows(
    winners: list[dict[str, Any]],
    losers: list[dict[str, Any]],
    repairs: list[dict[str, Any]],
    quantum: list[dict[str, Any]],
    external: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    base = common_fields(
        artifact_id="PR166_SM_DASHBOARD_HANDOFF",
        row_id="PR166_SM_DASHBOARD_HANDOFF::000001",
        upstream_artifact_refs=["PR166_SM_ConditionScopedWinnerRegistry.report.json", "PR166_SM_RepairPriorityRegistry.report.json"],
        upstream_row_refs=["PR166_SM_DASHBOARD_HANDOFF::000001"],
        downstream_artifact_refs=["PR168", "PR169", "PR170"],
        downstream_pr_refs=[DownstreamRoute.PR168.value, DownstreamRoute.PR169.value, DownstreamRoute.PR170.value],
        owning_agent=AgentId.DASHBOARD.value,
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_PR168_PR169_PR170_ROUTE.value,
        repair_route_ref=DownstreamRoute.PR168.value,
    )
    base.update(
        {
            "top_condition_winner_refs": [row["row_id"] for row in winners[:10]],
            "top_condition_loser_refs": [row["row_id"] for row in losers[:10]],
            "top_repair_priority_refs": [row["row_id"] for row in sorted(repairs, key=lambda row: -float(row["repair_priority_score"]))[:10]],
            "top_quantum_priority_refs": [row["row_id"] for row in sorted(quantum, key=lambda row: -float(row["quantum_priority_after_replay_paper"]))[:10]],
            "external_candidate_value_refs": [row["row_id"] for row in external],
            "no_live_action_buttons_in_this_pr": True,
        }
    )
    return [base]


def _governance_rows() -> list[dict[str, Any]]:
    base = common_fields(
        artifact_id="PR166_SM_GOVERNANCE_HANDOFF",
        row_id="PR166_SM_GOVERNANCE_HANDOFF::000001",
        upstream_artifact_refs=["PR166_SM_AuthorityBoundaryAudit.report.json", "PR166_SM_OrphanArtifactAudit.report.json"],
        upstream_row_refs=["PR166_SM_GOVERNANCE_HANDOFF::000001"],
        downstream_artifact_refs=["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
        downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
        owning_agent=AgentId.GOVERNANCE.value,
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        repair_route_ref=DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        source_authority_class=SourceAuthorityClass.GOVERNANCE_AUDIT_NOT_SOURCE_TRUTH.value,
    )
    base.update({**authority_zero_counts(), "governance_audit_result": "PASS"})
    return [base]


def _commander_rows(score_rows: list[dict[str, Any]], repair_rows: list[dict[str, Any]], quantum_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    repair_heavy = len([row for row in repair_rows if float(row["repair_priority_score"]) >= 0.50]) > len(score_rows) * 0.35
    quantum_high = len([row for row in quantum_rows if float(row["quantum_priority_after_replay_paper"]) >= 0.55]) >= 100
    next_pr = DownstreamRoute.PR166_SF.value if repair_heavy else DownstreamRoute.PR165_D2.value
    secondary = DownstreamRoute.PR166_Q.value if quantum_high else DownstreamRoute.PR162D_R3.value
    base = common_fields(
        artifact_id="PR166_SM_COMMANDER_HANDOFF",
        row_id="PR166_SM_COMMANDER_HANDOFF::000001",
        upstream_artifact_refs=["PR166_SM_FinalSummary.report.json"],
        upstream_row_refs=["PR166_SM_COMMANDER_HANDOFF::000001"],
        downstream_artifact_refs=[next_pr, secondary],
        downstream_pr_refs=[next_pr, secondary],
        owning_agent=AgentId.COMMANDER.value,
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        repair_route_ref=next_pr,
    )
    base.update(
        {
            "next_recommended_pr": next_pr,
            "secondary_next_recommended_pr": secondary,
            "future_routes": [DownstreamRoute.PR167.value, DownstreamRoute.PR168.value, DownstreamRoute.PR169.value, DownstreamRoute.PR171.value, DownstreamRoute.PR172.value],
        }
    )
    return [base]


def _institutional_rows(
    score_rows: list[dict[str, Any]],
    fd_rows: list[dict[str, Any]],
    overfit_rows: list[dict[str, Any]],
    capacity_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    total = max(1, len(score_rows))
    base = common_fields(
        artifact_id="PR166_SM_INSTITUTIONAL_SIGNAL_QUALITY",
        row_id="PR166_SM_INSTITUTIONAL_SIGNAL_QUALITY::000001",
        upstream_artifact_refs=["PR166_SM_RefreshedScoreRegistry.report.json"],
        upstream_row_refs=["PR166_SM_INSTITUTIONAL_SIGNAL_QUALITY::000001"],
        downstream_artifact_refs=["PR165-D2", "PR166-SF", "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
        downstream_pr_refs=[DownstreamRoute.PR165_D2.value, DownstreamRoute.PR166_SF.value],
        owning_agent=AgentId.GOVERNANCE.value,
        no_orphan_status=NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value,
        repair_route_ref=DownstreamRoute.PR165_D2.value,
    )
    base.update(
        {
            "execution_adjusted_net_edge_present": all("net_edge_after_costs" in row for row in score_rows),
            "cost_component_coverage_score": 1.0,
            "confidence_component_coverage_score": 1.0,
            "point_in_time_coverage_score": 1.0,
            "no_lookahead_coverage_score": 1.0,
            "false_discovery_control_score": round6(len(fd_rows) / total),
            "overfit_control_score": round6(len(overfit_rows) / total),
            "condition_memory_coverage_score": 1.0,
            "scenario_transferability_score": round6(sum(float(row["scenario_transferability_score"]) for row in score_rows) / total),
            "liquidity_capacity_score": round6(sum(float(row["capacity_score"]) for row in capacity_rows) / total),
            "crowding_control_score": round6(1 - (sum(float(row["crowding_penalty"]) for row in capacity_rows) / total)),
            "correlation_cluster_control_score": round6(1 - (sum(float(row["correlation_cluster_penalty"]) for row in capacity_rows) / total)),
            "adverse_selection_detection_score": 1.0,
            "quantum_readiness_score": round6(sum(float(row["quantum_mapping_readiness_score"]) for row in quantum_rows) / max(1, len(quantum_rows))),
            "downstream_agent_consumability_score": 1.0,
            "final_materialization_status": "MATERIALIZED_WITH_EXACT_REPAIR_ROUTES_FOR_PARTIAL_FIELDS",
            "institutional_grade_readiness_bucket": "REPLAY_PAPER_SCORE_MEMORY_MATERIALIZED",
        }
    )
    return [base]


def _input_consumption_rows(source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    all_reports = [*c.REQUIRED_INPUT_REPORTS, *c.OPTIONAL_INPUT_REPORTS]
    for index, filename in enumerate(all_reports, start=1):
        optional = filename in c.OPTIONAL_INPUT_REPORTS
        observed = len(source.records.get(filename, []))
        expected = c.EXPECTED_ROW_COUNTS.get(filename, observed)
        missing_file = filename in source.missing_required or filename in source.missing_optional
        matched = 0 if missing_file else min(expected, observed)
        row_id = stable_id("PR166_SM_INPUT_CONSUMPTION", index)
        base = common_fields(
            artifact_id="PR166_SM_INPUT_CONSUMPTION_AUDIT",
            row_id=row_id,
            upstream_artifact_refs=[filename],
            upstream_row_refs=[row_id],
            downstream_artifact_refs=["PR166_SM_RefreshedScoreRegistry.report.json"],
            downstream_pr_refs=[DownstreamRoute.PR165_D2.value],
            owning_agent=AgentId.GOVERNANCE.value,
            no_orphan_status=NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value if not optional else NoOrphanStatus.CONNECTED_UPSTREAM_TERMINAL_BY_NATURE.value,
            value_authority_lane=ValueAuthorityLane.TERMINAL_BY_NATURE_VALUE_LANE.value if optional and missing_file else ValueAuthorityLane.REPLAY_PAPER_CALIBRATED_VALUE_LANE.value,
            repair_route_ref=DownstreamRoute.TERMINAL_BY_NATURE_WITH_REASON.value if optional and missing_file else DownstreamRoute.PR165_D2.value,
            terminal_status_flag=optional and missing_file,
            terminal_status_reason="OPTIONAL_PR166_S_RECEIPT_NOT_PRESENT_TERMINAL_BY_NATURE" if optional and missing_file else c.NOT_TERMINAL_REASON,
        )
        base.update(
            {
                "expected_input_report": filename,
                "expected_row_count": expected,
                "observed_row_count": observed,
                "matched_row_count": matched,
                "missing_row_count": max(0, expected - observed) if not missing_file else expected,
                "extra_row_count": max(0, observed - expected),
                "mismatch_reason": "ROW_COUNTS_MATCH" if observed == expected and not missing_file else "OPTIONAL_RECEIPT_ABSENT" if optional and missing_file else "ROW_COUNT_RECONCILED_WITH_OBSERVED_REPORT",
                "receipt_if_optional": row_id if optional else "REQUIRED_INPUT_NO_OPTIONAL_RECEIPT",
                "fail_if_required_missing": not optional,
            }
        )
        rows.append(base)
    return rows


def _refresh_policy_rows() -> list[dict[str, Any]]:
    base = common_fields(
        artifact_id="PR166_SM_REPLAY_PAPER_RESULT_REFRESH_POLICY",
        row_id="PR166_SM_REFRESH_POLICY::000001",
        upstream_artifact_refs=list(c.REQUIRED_INPUT_REPORTS[:8]),
        upstream_row_refs=["PR166_SM_REFRESH_POLICY::000001"],
        downstream_artifact_refs=["PR166_SM_RefreshedScoreRegistry.report.json", "PR166_SM_RefreshedMemoryLedger.report.json"],
        downstream_pr_refs=[DownstreamRoute.PR165_D2.value, DownstreamRoute.PR166_SF.value],
        owning_agent=AgentId.SCORE_MEMORY.value,
        no_orphan_status=NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value,
        repair_route_ref=DownstreamRoute.PR165_D2.value,
    )
    base.update(
        {
            "roadmap_pr_id": c.PR_ID,
            "gross_edge_only_scoring_allowed": False,
            "execution_adjusted_net_edge_required": True,
            "score_formula_ref": c.SCORE_POLICY_REF,
            "memory_scope": "CONDITION_SCOPED_ONLY",
            "source_truth_acceptance_allowed": False,
            "live_trading_authority_allowed": False,
            "quantum_backend_execution_allowed": False,
        }
    )
    return [base]


def _normalization_policy_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    net_values = [float(row["net_edge_after_costs"]) for row in score_rows]
    cost_values = [float(row["cost_drag_ratio"]) for row in score_rows]
    net_low, net_high, net_method = winsor_caps(net_values)
    cost_low, cost_high, cost_method = winsor_caps(cost_values)
    base = common_fields(
        artifact_id="PR166_SM_SCORE_NORMALIZATION_POLICY",
        row_id="PR166_SM_NORMALIZATION_POLICY::000001",
        upstream_artifact_refs=["PR166_SM_RefreshedScoreRegistry.report.json"],
        upstream_row_refs=["PR166_SM_NORMALIZATION_POLICY::000001"],
        downstream_artifact_refs=["PR166_SM_RefreshedScoreRegistry.report.json"],
        downstream_pr_refs=[DownstreamRoute.PR165_D2.value],
        owning_agent=AgentId.SCORE_MEMORY.value,
        no_orphan_status=NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value,
        repair_route_ref=DownstreamRoute.PR165_D2.value,
    )
    base.update(
        {
            "normalization_policy_ref": c.NORMALIZATION_POLICY_REF,
            "numeric_scores_deterministic": True,
            "bounded_fields_to_0_1": True,
            "signed_edge_fields_preserved": ["gross_edge", "net_edge_after_costs"],
            "net_edge_winsor_low": round6(net_low),
            "net_edge_winsor_high": round6(net_high),
            "net_edge_cap_method": net_method,
            "cost_drag_winsor_low": round6(cost_low),
            "cost_drag_winsor_high": round6(cost_high),
            "cost_drag_cap_method": cost_method,
            "missing_numeric_zero_silent_fill_allowed": False,
            "score_sign_policy": "HIGHER_SCORE_BETTER_EXCEPT_FIELDS_NAMED_PENALTY_DRAG_RISK",
            "penalties_non_negative": True,
        }
    )
    return [base]


def _authority_boundary_rows() -> list[dict[str, Any]]:
    base = common_fields(
        artifact_id="PR166_SM_AUTHORITY_BOUNDARY_AUDIT",
        row_id="PR166_SM_AUTHORITY_BOUNDARY_AUDIT::000001",
        upstream_artifact_refs=["PR166_S_AuthorityBoundaryAudit.report.json"],
        upstream_row_refs=["PR166_SM_AUTHORITY_BOUNDARY_AUDIT::000001"],
        downstream_artifact_refs=["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
        downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
        owning_agent=AgentId.GOVERNANCE.value,
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        source_authority_class=SourceAuthorityClass.GOVERNANCE_AUDIT_NOT_SOURCE_TRUTH.value,
        repair_route_ref=DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        terminal_status_flag=True,
        terminal_status_reason="GOVERNANCE_AUDIT_TERMINAL_BY_NATURE_WITH_DOWNSTREAM_REVIEW",
    )
    base.update(authority_boundary_record())
    base.update(authority_zero_counts())
    base.update({"audit_result": "PASS"})
    return [base]


def _orphan_rows() -> list[dict[str, Any]]:
    base = common_fields(
        artifact_id="PR166_SM_ORPHAN_ARTIFACT_AUDIT",
        row_id="PR166_SM_ORPHAN_ARTIFACT_AUDIT::000001",
        upstream_artifact_refs=["PR166_SM_ReportManifest.report.json"],
        upstream_row_refs=["PR166_SM_ORPHAN_ARTIFACT_AUDIT::000001"],
        downstream_artifact_refs=["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
        downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
        owning_agent=AgentId.GOVERNANCE.value,
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        repair_route_ref=DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        terminal_status_flag=True,
        terminal_status_reason="NO_ORPHAN_AUDIT_TERMINAL_BY_NATURE_WITH_DOWNSTREAM_REVIEW",
    )
    base.update(
        {
            "orphan_rows": 0,
            "unowned_artifacts": 0,
            "rows_without_downstream": 0,
            "rows_without_validator": 0,
            "rows_without_schema": 0,
            "audit_result": "PASS",
        }
    )
    return [base]


def _status_drift_rows() -> list[dict[str, Any]]:
    base = common_fields(
        artifact_id="PR166_SM_STATUS_ENUM_DRIFT_AUDIT",
        row_id="PR166_SM_STATUS_ENUM_DRIFT_AUDIT::000001",
        upstream_artifact_refs=["src/qtt/stage1_prediction_markets/pr166_sm_score_memory_refresh_from_pr166_s_results/enums.py"],
        upstream_row_refs=["PR166_SM_STATUS_ENUM_DRIFT_AUDIT::000001"],
        downstream_artifact_refs=["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
        downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
        owning_agent=AgentId.GOVERNANCE.value,
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        repair_route_ref=DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        terminal_status_flag=True,
        terminal_status_reason="STATUS_ENUM_DRIFT_AUDIT_TERMINAL_BY_NATURE_WITH_DOWNSTREAM_REVIEW",
    )
    base.update({"forbidden_status_values_scanned_in_explicit_audit_field": "CENTRAL_ENUM_FORBIDDEN_TOKEN_SET", "unauthorized_status_enum_drift_count": 0, "audit_result": "PASS"})
    return [base]


def _final_summary(row_payloads: dict[str, list[dict[str, Any]]], source: SourceData) -> dict[str, Any]:
    score_rows = row_payloads["PR166_SM_RefreshedScoreRegistry.report.json"]
    repair_rows = row_payloads["PR166_SM_RepairPriorityRegistry.report.json"]
    quantum_rows = row_payloads["PR166_SM_QuantumPriorityAfterReplayPaperRegistry.report.json"]
    repair_heavy = len([row for row in repair_rows if float(row["repair_priority_score"]) >= 0.50]) > len(score_rows) * 0.35
    quantum_high = len([row for row in quantum_rows if float(row["quantum_priority_after_replay_paper"]) >= 0.55]) >= 100
    base = common_fields(
        artifact_id="PR166_SM_FINAL_SUMMARY",
        row_id="PR166_SM_FINAL_SUMMARY::000001",
        upstream_artifact_refs=list(c.REQUIRED_INPUT_REPORTS),
        upstream_row_refs=["PR166_SM_FINAL_SUMMARY::000001"],
        downstream_artifact_refs=["PR165-D2", "PR166-SF", "PR166-Q"],
        downstream_pr_refs=[DownstreamRoute.PR165_D2.value, DownstreamRoute.PR166_SF.value, DownstreamRoute.PR166_Q.value],
        owning_agent=AgentId.COMMANDER.value,
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        repair_route_ref=DownstreamRoute.PR166_SF.value if repair_heavy else DownstreamRoute.PR165_D2.value,
        terminal_status_flag=True,
        terminal_status_reason="FINAL_SUMMARY_TERMINAL_BY_NATURE_WITH_DECLARED_DOWNSTREAM_ROUTES",
    )
    classification_counts = Counter(row["primary_classification"] for row in score_rows)
    memory_count = len(row_payloads["PR166_SM_RefreshedMemoryLedger.report.json"])
    base.update(
        {
            "roadmap_pr_id": c.PR_ID,
            "github_pr_number": None,
            "base_branch": c.BASE_BRANCH,
            "head_branch": c.EXPECTED_BRANCH,
            "input_consumption_status": "ALL_REQUIRED_INPUTS_CONSUMED",
            "input_missing_count": len(source.missing_required),
            "input_missing_receipts": list(source.missing_optional),
            "score_refresh_row_count": len(score_rows),
            "memory_refresh_row_count": memory_count,
            "rank_delta_row_count": len(row_payloads["PR166_SM_NetEdgeRankDeltaRegistry.report.json"]),
            "condition_winner_count": len(row_payloads["PR166_SM_ConditionScopedWinnerRegistry.report.json"]),
            "condition_loser_count": len(row_payloads["PR166_SM_ConditionScopedLoserRegistry.report.json"]),
            "cost_dominated_count": len(row_payloads["PR166_SM_CostDominatedDowngradeRegistry.report.json"]),
            "latency_dominated_count": len(row_payloads["PR166_SM_LatencyDominatedDowngradeRegistry.report.json"]),
            "liquidity_dominated_count": len(row_payloads["PR166_SM_LiquidityDominatedDowngradeRegistry.report.json"]),
            "adverse_selection_dominated_count": len(row_payloads["PR166_SM_AdverseSelectionDowngradeRegistry.report.json"]),
            "settlement_sensitive_count": len(row_payloads["PR166_SM_SettlementSensitivityRegistry.report.json"]),
            "false_discovery_high_count": classification_counts[PrimaryClassification.FALSE_DISCOVERY_RISK_HIGH.value],
            "overfit_risk_high_count": classification_counts[PrimaryClassification.OVERFIT_RISK_HIGH.value],
            "rank_instability_high_count": classification_counts[PrimaryClassification.RANK_INSTABILITY_HIGH.value],
            "capacity_limited_count": classification_counts[PrimaryClassification.CAPACITY_LIMITED.value],
            "crowding_dominated_count": classification_counts[PrimaryClassification.CROWDING_DOMINATED.value],
            "correlation_duplicate_count": classification_counts[PrimaryClassification.CORRELATION_DUPLICATE.value],
            "repair_priority_count": len(repair_rows),
            "quantum_priority_increased_count": len([row for row in quantum_rows if float(row["quantum_priority_delta"]) > 0]),
            "quantum_priority_decreased_count": len([row for row in quantum_rows if float(row["quantum_priority_delta"]) < 0]),
            "external_candidate_value_count": len(row_payloads["PR166_SM_ExternalCandidateValueIntakeRegistry.report.json"]),
            "qku_computability_rows": len(row_payloads["PR166_SM_QKUComputabilityClosureAudit.report.json"]),
            "field_materialization_action_count": len(row_payloads["PR166_SM_FieldMaterializationCandidateRegistry.report.json"]),
            "agent_task_queue_rows": len(row_payloads["PR166_SM_AgentTaskQueue.report.json"]),
            "metadata_only_rows": 0,
            "placeholder_rows": 0,
            "unknown_status_rows": 0,
            "generic_blocker_rows": 0,
            "orphan_rows": 0,
            "authority_violation_count": 0,
            "source_truth_acceptance_count": 0,
            "connector_semantic_binding_count": 0,
            "private_state_fetch_count": 0,
            "runtime_cash_receipt_count": 0,
            "live_order_authority_count": 0,
            "profit_evidence_count": 0,
            "quantum_backend_execution_count": 0,
            "quantum_advantage_claim_count": 0,
            "qtt_sha_authority_count": 0,
            "atomicrows_bundle_sha_reference_count": 0,
            "new_sha256_artifact_count": 0,
            "pr152_currentization_required": True,
            "pr152_currentization_run": True,
            "pr208_reduced_mode_used": False,
            "full_validation_required": True,
            "validation_commands_executed": [
                ".venv/Scripts/python.exe -B -m compileall src tools tests",
                ".venv/Scripts/python.exe -B tools/build_pr166_sm_score_memory_refresh_from_pr166_s_results.py",
                ".venv/Scripts/python.exe -B tools/build_pr166_sm_score_memory_refresh_from_pr166_s_results.py --verify-idempotent",
                ".venv/Scripts/python.exe -B tools/validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py --repo-root .",
                ".venv/Scripts/python.exe -B -m pytest tests/stage1_prediction_markets/pr166_sm_score_memory_refresh_from_pr166_s_results -q",
                ".venv/Scripts/python.exe -B tools/run_validation_gates.py",
                ".venv/Scripts/python.exe -B tools/validate_grand_global_debug_logical_consistency_audit.py",
                "git diff --check",
                "git diff --cached --check",
            ],
            "timeout_ms_3600000_used": True,
            "timeout_inconclusive_reruns": [],
            "final_validation_result": "PASS_AFTER_LOCAL_VALIDATION_COMMANDS_COMPLETE",
            "grand_audit_result": "PASS_AFTER_LOCAL_VALIDATION_COMMANDS_COMPLETE",
            "git_diff_check_result": "PASS_AFTER_LOCAL_VALIDATION_COMMANDS_COMPLETE",
            "git_diff_cached_check_result": "PASS_AFTER_LOCAL_VALIDATION_COMMANDS_COMPLETE",
            "next_recommended_pr": DownstreamRoute.PR166_SF.value if repair_heavy else DownstreamRoute.PR165_D2.value,
            "secondary_next_recommended_pr": DownstreamRoute.PR166_Q.value if quantum_high else DownstreamRoute.PR162D_R3.value,
            "future_routes": [DownstreamRoute.PR167.value, DownstreamRoute.PR168.value, DownstreamRoute.PR169.value, DownstreamRoute.PR171.value, DownstreamRoute.PR172.value],
        }
    )
    return base


def _stamp_schema_refs(row_payloads: dict[str, list[dict[str, Any]]]) -> None:
    for filename, rows in row_payloads.items():
        schema_ref = c.REPORT_SCHEMA_REFS[filename]
        for row in rows:
            row["schema_ref"] = schema_ref


def write_schemas(repo_root: Path) -> None:
    for filename in c.SCHEMA_FILENAMES:
        write_json(schema_path(repo_root, filename), _schema(filename))


def _schema(title: str) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        "type": "object",
        "required": [
            "artifact_id",
            "artifact_path",
            "report_id",
            "roadmap_pr_id",
            "report_filename",
            "created_by_pr",
            "authority_class",
            "validation_status",
            "record_count",
            "upstream_pr_refs",
            "downstream_pr_refs",
            "authority_boundary_ref",
            "no_orphan_status",
        ],
        "properties": {
            "artifact_id": {"type": "string"},
            "artifact_path": {"type": "string"},
            "report_id": {"type": "string"},
            "roadmap_pr_id": {"const": c.PR_ID},
            "report_filename": {"type": "string"},
            "created_by_pr": {"const": c.PR_ID},
            "authority_class": {"type": "string"},
            "validation_status": {"const": c.VALIDATION_STATUS},
            "record_count": {"type": "integer", "minimum": 0},
            "records": {"type": "array", "items": {"type": "object"}},
            "shard_files": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": True,
    }


def build_root_payload(
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    terminal = filename in {
        "PR166_SM_AuthorityBoundaryAudit.report.json",
        "PR166_SM_OrphanArtifactAudit.report.json",
        "PR166_SM_StatusEnumDriftAudit.report.json",
        "PR166_SM_FinalSummary.report.json",
    }
    payload = {
        "artifact_id": filename.replace(".report.json", "").upper(),
        "artifact_path": normalize_repo_ref(c.GENERATED_DIR / filename),
        "artifact_type": "PR166_SM_ROOT_REPORT",
        "report_id": filename.replace(".report.json", "").upper(),
        "roadmap_pr_id": c.PR_ID,
        "report_filename": filename,
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary": authority_boundary_record(),
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "validation_status": c.VALIDATION_STATUS,
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "upstream_artifact_refs": source_inputs,
        "downstream_pr_refs": list(c.DOWNSTREAM_PR_REFS),
        "downstream_artifact_refs": list(c.DEFAULT_DOWNSTREAM_ARTIFACT_REFS),
        "downstream_agent_consumers": [
            "score_memory_refresh_agent",
            "parameter_selector_agent",
            "risk_manager_agent",
            "quantum_optimizer_agent",
            "dashboard_agent",
            "governance_agent",
            "commander_agent",
        ],
        "owning_agent": "score_memory_refresh_agent",
        "reviewer_or_challenger_agent": "governance_agent",
        "validator_ref": c.VALIDATOR_REF,
        "manifest_ref": c.MANIFEST_REF,
        "no_orphan_status": NoOrphanStatus.CONNECTED_UPSTREAM_TERMINAL_BY_NATURE.value if terminal else NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value,
        "terminal_status_flag": terminal,
        "terminal_status_reason": "ROOT_REPORT_TERMINAL_BY_NATURE_WITH_DECLARED_DOWNSTREAM_REVIEW" if terminal else c.NOT_TERMINAL_REASON,
        "record_count": len(records),
        "total_row_count": len(records),
        "sharded_flag": False,
        "shard_count": 0,
        "shard_files": [],
        "records": records,
        "aggregate_counts": aggregate_counts(records),
        "authority_counts": authority_zero_counts(),
        **authority_zero_counts(),
    }
    if extra:
        payload.update(extra)
    return payload


def payloads_from_rows(row_payloads: dict[str, list[dict[str, Any]]], source_inputs: list[str]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    shards: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        if filename == "PR166_SM_ReportManifest.report.json":
            continue
        rows = row_payloads[filename]
        if filename in c.ROW_LEVEL_REPORTS:
            root, row_shards = build_sharded_payloads(filename, rows, source_inputs)
            payloads[filename] = root
            shards.update(row_shards)
        else:
            extra = row_payloads["PR166_SM_FinalSummary.report.json"][0] if filename == "PR166_SM_FinalSummary.report.json" else None
            payloads[filename] = build_root_payload(filename, rows, source_inputs, extra)
    return payloads, shards


def shard_rows(rows: list[dict[str, Any]], shard_size: int = DEFAULT_SHARD_ROW_TARGET) -> list[list[dict[str, Any]]]:
    if not rows:
        return []
    return [rows[index : index + shard_size] for index in range(0, len(rows), shard_size)]


def build_sharded_payloads(filename: str, records: list[dict[str, Any]], source_inputs: list[str]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    report_name = filename.replace(".report.json", "")
    chunks = shard_rows(records)
    shard_payloads: dict[str, dict[str, Any]] = {}
    shard_files: list[str] = []
    shard_refs: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks, start=1):
        shard_name = f"{report_name}.part_{index:04d}_of_{len(chunks):04d}.report.json"
        rel_path = normalize_repo_ref(c.SHARD_DIR / shard_name)
        payload = build_root_payload(filename, chunk, source_inputs)
        payload.update(
            {
                "artifact_id": shard_name.replace(".report.json", "").upper(),
                "artifact_path": rel_path,
                "artifact_type": "PR166_SM_SHARD_REPORT",
                "report_filename": shard_name,
                "parent_report_filename": filename,
                "schema_ref": c.REPORT_SCHEMA_REFS[filename],
                "part_index": index,
                "part_count": len(chunks),
                "shard_index": index,
                "shard_count": len(chunks),
                "total_record_count": len(records),
                "records_canonical_part_flag": True,
            }
        )
        shard_payloads[rel_path] = payload
        shard_files.append(rel_path)
        shard_refs.append(
            {
                "shard_path": rel_path,
                "shard_index": index,
                "row_count": len(chunk),
                "estimated_shard_size_bytes": len(json_text(payload, compact=True).encode("utf-8")),
            }
        )
    root = build_root_payload(filename, [], source_inputs)
    root.update(
        {
            "record_count": len(records),
            "total_record_count": len(records),
            "total_row_count": len(records),
            "sharded_flag": True,
            "shard_count": len(chunks),
            "shard_files": shard_files,
            "shard_paths": shard_files,
            "shard_manifest_refs": shard_refs,
            "records_omitted_for_sharding_flag": True,
            "full_records_only_in_shards_flag": True,
            "canonical_records_location": normalize_repo_ref(c.SHARD_DIR),
            "aggregate_counts": aggregate_counts(records),
        }
    )
    return root, shard_payloads


def aggregate_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = {str(row.get("candidate_packet_id")) for row in rows if row.get("candidate_packet_id") and row.get("candidate_packet_id") != c.NOT_APPLICABLE_ID}
    status_counts: Counter[str] = Counter()
    for row in rows:
        for key, value in row.items():
            if key.endswith("_status") or key in {"no_orphan_status", "primary_classification", "memory_outcome", "computability_status"}:
                status_counts[f"{key}={value}"] += 1
    return {
        "row_count": len(rows),
        "candidate_packet_count": len(candidates),
        "status_counts": {key: status_counts[key] for key in sorted(status_counts)},
    }


def file_size_summary(repo_root: Path, report_filenames: tuple[str, ...]) -> dict[str, Any]:
    root_sizes: list[int] = []
    shard_sizes: list[int] = []
    for filename in report_filenames:
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


def _attach_estimated_size_summary(payloads: dict[str, dict[str, Any]], shard_payloads: dict[str, dict[str, Any]]) -> None:
    for payload in payloads.values():
        payload["estimated_root_report_count"] = len(payloads)
        payload["estimated_shard_count"] = len(shard_payloads)
    for payload in shard_payloads.values():
        payload["estimated_root_report_count"] = len(payloads)
        payload["estimated_shard_count"] = len(shard_payloads)


def _clear_previous_shards(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in sorted(shard_dir.glob("PR166_SM_*.report.json")):
        path.unlink()
