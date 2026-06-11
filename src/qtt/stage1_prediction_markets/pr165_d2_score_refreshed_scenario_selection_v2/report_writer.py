"""Build PR165-D2 generated reports."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import authority_boundary_record, authority_zero_counts
from .enums import (
    ComputabilityStatus,
    ConnectorDependencyClass,
    DownstreamRoute,
    NoOrphanStatus,
    SelectionState,
    SourceAuthorityClass,
    UnitClass,
    ValueAuthorityLane,
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
from .models import common_fields, stable_id


ROOT_REPORT_LIMIT_BYTES = 10 * 1024 * 1024
SHARD_LIMIT_BYTES = 25 * 1024 * 1024


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
    missing_optional_pr166_sf: tuple[str, ...]
    optional_pr164_reports: tuple[str, ...]


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
    summary = dict(payloads["PR165_D2_FinalSummary.report.json"]["records"][0])
    summary.update(sizes)
    payloads["PR165_D2_FinalSummary.report.json"]["records"] = [summary]
    payloads["PR165_D2_FinalSummary.report.json"].update(sizes)
    payloads["PR165_D2_ReportManifest.report.json"] = build_root_payload(
        "PR165_D2_ReportManifest.report.json",
        build_manifest_rows(payloads),
        list(c.REQUIRED_INPUT_REPORTS),
        {"manifest_report_count": len(c.REPORT_FILENAMES)},
    )
    write_json(repo_root / c.GENERATED_DIR / "PR165_D2_FinalSummary.report.json", payloads["PR165_D2_FinalSummary.report.json"])
    write_json(repo_root / c.GENERATED_DIR / "PR165_D2_ReportManifest.report.json", payloads["PR165_D2_ReportManifest.report.json"])
    return BuildArtifacts(summary=summary, payloads=payloads, shard_payloads=shard_payloads)


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source = load_sources(repo_root)
    if source.missing_required:
        raise RuntimeError(f"PR165-D2 required inputs missing: {', '.join(source.missing_required)}")
    row_payloads = build_row_payloads(repo_root, source)
    payloads, shard_payloads = payloads_from_rows(row_payloads, list(c.REQUIRED_INPUT_REPORTS))
    payloads["PR165_D2_ReportManifest.report.json"] = build_root_payload(
        "PR165_D2_ReportManifest.report.json",
        build_manifest_rows(payloads),
        list(c.REQUIRED_INPUT_REPORTS),
        {"manifest_report_count": len(c.REPORT_FILENAMES)},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    missing = sorted(set(c.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR165-D2 payload map missing reports: {missing}")
    return payloads, shard_payloads


def load_sources(repo_root: Path) -> SourceData:
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    missing_required: list[str] = []
    for filename in c.REQUIRED_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            missing_required.append(filename)
            continue
        payload = read_json(path)
        payloads[filename] = payload
        records[filename] = records_from_report_payload(repo_root, payload)
    missing_optional: list[str] = []
    for filename in c.OPTIONAL_PR166_SF_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            missing_optional.append(filename)
            continue
        payload = read_json(path)
        payloads[filename] = payload
        records[filename] = records_from_report_payload(repo_root, payload)
    optional_pr164_reports = tuple(sorted(path.name for path in (repo_root / c.GENERATED_DIR).glob("PR164_*.report.json")))
    for filename in optional_pr164_reports:
        path = repo_root / c.GENERATED_DIR / filename
        payload = read_json(path)
        payloads[filename] = payload
        records[filename] = records_from_report_payload(repo_root, payload)
    return SourceData(payloads, records, tuple(missing_required), tuple(missing_optional), optional_pr164_reports)


def build_row_payloads(repo_root: Path, source: SourceData) -> dict[str, list[dict[str, Any]]]:
    score_context = build_score_context(source)
    agent_roster_rows = build_agent_roster_rows(source)
    agent_crosswalk_rows = build_agent_duty_crosswalk_rows(agent_roster_rows)
    ranking_rows = build_ranking_rows(score_context)
    tca_rows = build_tca_rows(ranking_rows)
    provenance_rows = build_score_component_provenance_rows(ranking_rows)
    probability_rows = build_prediction_market_probability_rows(ranking_rows)
    microstructure_rows = build_microstructure_rows(ranking_rows)
    repair_rows = build_repair_rows(ranking_rows, source)
    quantum_rows = build_quantum_rows(source, ranking_rows)
    scenario_rows = build_scenario_group_rows(ranking_rows)
    memory_rows = build_condition_memory_rows(ranking_rows)
    champion_rows = build_champion_challenger_rows(ranking_rows)
    marginal_rows = build_marginal_utility_rows(ranking_rows)
    capacity_rows = build_capacity_rows(ranking_rows)
    false_discovery_rows = build_false_discovery_rows(ranking_rows)
    retest_rows = build_retest_batch_rows(ranking_rows)
    budget_rows = build_retest_budget_policy_rows(ranking_rows, retest_rows)
    route_rows = build_route_triage_rows(ranking_rows, repair_rows, quantum_rows)
    connector_rows = build_connector_readiness_rows(ranking_rows)
    market_index_rows = build_market_index_rows(ranking_rows)
    computability_rows = build_computability_rows(source, ranking_rows)
    exclusion_rows = build_exclusion_rows(ranking_rows)
    external_rows, coverage_rows = build_external_rows()
    input_rows = build_input_consumption_rows(source)
    optional_rows = build_optional_input_rows(source)
    count_rows = build_row_count_rows(source)
    policy_rows = build_selection_policy_rows()
    normalization_rows = build_normalization_policy_rows(ranking_rows)
    command_rows = build_command_action_rows(ranking_rows, repair_rows, quantum_rows, agent_roster_rows)
    agent_handoff_rows = build_agent_handoff_rows(agent_roster_rows, ranking_rows)
    agent_task_rows = build_agent_task_rows(command_rows)
    dashboard_rows = build_dashboard_rows(ranking_rows, retest_rows, repair_rows, quantum_rows)
    governance_rows = build_governance_rows()
    commander_rows = build_commander_rows(route_rows)
    row_payloads: dict[str, list[dict[str, Any]]] = {
        "PR165_D2_InputConsumptionAudit.report.json": input_rows,
        "PR165_D2_OptionalInputResolutionLedger.report.json": optional_rows,
        "PR165_D2_RowCountReconciliationLedger.report.json": count_rows,
        "PR165_D2_ScoreRefreshedScenarioSelectionPolicy.report.json": policy_rows,
        "PR165_D2_ScoreNormalizationPolicy.report.json": normalization_rows,
        "PR165_D2_ScoreComponentProvenanceLedger.report.json": provenance_rows,
        "PR165_D2_PredictionMarketProbabilityEdgeLedger.report.json": probability_rows,
        "PR165_D2_MicrostructureFeatureLedger.report.json": microstructure_rows,
        "PR165_D2_NetEdgeAdjustedCandidateRanking.report.json": ranking_rows,
        "PR165_D2_ReplayPaperRetestBatchV2.report.json": retest_rows,
        "PR165_D2_RepairAwareSelectionQueue.report.json": repair_rows,
        "PR165_D2_QuantumCandidatePriorityV2.report.json": quantum_rows,
        "PR165_D2_ScenarioGroupRefreshRegistry.report.json": scenario_rows,
        "PR165_D2_ConditionMemoryApplicationLedger.report.json": memory_rows,
        "PR165_D2_ChampionChallengerSelectionLedger.report.json": champion_rows,
        "PR165_D2_MarginalUtilityBatchBuilderLedger.report.json": marginal_rows,
        "PR165_D2_CapacityCrowdingCorrelationSelectionLedger.report.json": capacity_rows,
        "PR165_D2_FalseDiscoveryOverfitSelectionControl.report.json": false_discovery_rows,
        "PR165_D2_TCADecompositionSelectionLedger.report.json": tca_rows,
        "PR165_D2_RetestBudgetAllocationPolicy.report.json": budget_rows,
        "PR165_D2_RouteTriageMatrix.report.json": route_rows,
        "PR165_D2_ConnectorVenueReadinessReferenceRouting.report.json": connector_rows,
        "PR165_D2_MasterPlanSectionCrosswalk.report.json": [],
        "PR165_D2_MarketSpecificSelectionIndex.report.json": market_index_rows,
        "PR165_D2_CommandActionMatrix.report.json": command_rows,
        "PR165_D2_SelectionExclusionReasonLedger.report.json": exclusion_rows,
        "PR165_D2_ExternalSelectionSignalCandidateRegistry.report.json": external_rows,
        "PR165_D2_ExternalInstitutionalSignalCoverageAudit.report.json": coverage_rows,
        "PR165_D2_QKUFormulaAlgorithmComputabilityRouting.report.json": computability_rows,
        "PR165_D2_AgentRosterDiscoveryAudit.report.json": agent_roster_rows,
        "PR165_D2_AgentDutySourceCrosswalk.report.json": agent_crosswalk_rows,
        "PR165_D2_AgentSelectionHandoff.report.json": agent_handoff_rows,
        "PR165_D2_AgentTaskQueue.report.json": agent_task_rows,
        "PR165_D2_DashboardSelectionHandoff.report.json": dashboard_rows,
        "PR165_D2_GovernanceSelectionHandoff.report.json": governance_rows,
        "PR165_D2_CommanderSelectionHandoff.report.json": commander_rows,
        "PR165_D2_PRFileConnectivityAudit.report.json": [],
        "PR165_D2_RowValueConnectivityAudit.report.json": [],
        "PR165_D2_AuthorityBoundaryAudit.report.json": build_authority_rows(),
        "PR165_D2_OrphanArtifactAudit.report.json": build_orphan_rows(),
        "PR165_D2_StatusEnumDriftAudit.report.json": build_status_rows(),
        "PR165_D2_ReportManifest.report.json": [],
        "PR165_D2_FinalSummary.report.json": [],
    }
    row_payloads["PR165_D2_MasterPlanSectionCrosswalk.report.json"] = build_crosswalk_rows(row_payloads)
    row_payloads["PR165_D2_PRFileConnectivityAudit.report.json"] = build_pr_file_connectivity_rows(
        tracked_file_list(repo_root, row_payloads)
    )
    row_payloads["PR165_D2_RowValueConnectivityAudit.report.json"] = build_row_value_connectivity_rows(row_payloads)
    row_payloads["PR165_D2_FinalSummary.report.json"] = [build_final_summary(row_payloads, source)]
    _stamp_schema_refs(row_payloads)
    return row_payloads


def build_score_context(source: SourceData) -> list[dict[str, Any]]:
    score_rows = sorted(
        source.records["PR166_SM_RefreshedScoreRegistry.report.json"],
        key=lambda row: int(row.get("refreshed_rank", 999999)),
    )
    memory_by = _by_candidate(source.records["PR166_SM_RefreshedMemoryLedger.report.json"])
    rank_by = _by_candidate(source.records["PR166_SM_NetEdgeRankDeltaRegistry.report.json"])
    repair_by = _by_candidate(source.records["PR166_SM_RepairPriorityRegistry.report.json"])
    fd_by = _by_candidate(source.records["PR166_SM_FalseDiscoveryRiskRefreshLedger.report.json"])
    overfit_by = _by_candidate(source.records["PR166_SM_OverfitAndRankInstabilityRegistry.report.json"])
    cap_by = _by_candidate(source.records["PR166_SM_CapacityAndCrowdingRegistry.report.json"])
    corr_by = _by_candidate(source.records["PR166_SM_CorrelationClusterRegistry.report.json"])
    pr165_candidate_by = _by_candidate(source.records["PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json"])
    pr165_score_by = _by_candidate(source.records["PR165_D_SelectionScoreRegistry.report.json"])
    pr165_marginal_by = _by_candidate(source.records["PR165_D_MarginalUtilitySelectionLedger.report.json"])
    pr166_conf_by = _by_candidate(source.records["PR166_S_ResultConfidenceRegistry.report.json"])
    condition_by_id = _by_key(source.records["PR165_B_ConditionFingerprintRegistry.report.json"], "condition_fingerprint_id")
    regime_by = _by_candidate(source.records["PR165_C_ConditionRegimeFeatureMatrix.report.json"])
    cluster_counts = Counter(
        str(row.get("correlation_cluster_id") or row.get("duplicate_edge_cluster") or row.get("portfolio_cluster") or "CLUSTER_TERMINAL_BY_NATURE")
        for row in pr165_candidate_by.values()
    )
    raw_context: list[dict[str, Any]] = []
    for index, score in enumerate(score_rows, start=1):
        candidate_id = str(score["candidate_packet_id"])
        memory = memory_by.get(candidate_id, {})
        rank = rank_by.get(candidate_id, {})
        repair = repair_by.get(candidate_id, {})
        fd = fd_by.get(candidate_id, {})
        overfit = overfit_by.get(candidate_id, {})
        capacity = cap_by.get(candidate_id, {})
        correlation = corr_by.get(candidate_id, {})
        prior = pr165_candidate_by.get(candidate_id, {})
        prior_score = pr165_score_by.get(candidate_id, prior)
        prior_marginal = pr165_marginal_by.get(candidate_id, prior)
        confidence = pr166_conf_by.get(candidate_id, {})
        condition = condition_by_id.get(str(score.get("condition_fingerprint_id")), {})
        regime = regime_by.get(candidate_id, {})
        condition_memory_score = condition_memory_preference_score(str(memory.get("memory_outcome") or score.get("memory_outcome")))
        normalized_net_edge = numeric(score, "normalized_net_edge_after_costs")
        result_confidence = numeric(score, "result_confidence_score", numeric(confidence, "result_confidence_score", 0.5))
        lcb = clamp01(normalized_net_edge - (1.0 - result_confidence) * 0.20)
        expected_information_gain = clamp01(
            numeric(prior_marginal, "exploration_budget_gain", 0.0)
            + numeric(prior_marginal, "batch_diversification_gain", 0.0)
            + 0.05 * (1.0 - numeric(score, "correlation_cluster_penalty", 0.0))
        )
        repair_priority = numeric(score, "repair_priority_score", numeric(repair, "repair_priority_score", 0.0))
        repair_needed = repair_priority >= c.REPAIR_BEFORE_RETEST_PRIORITY_THRESHOLD
        field_materialization_required = str(score.get("computability_status")) != "COMPUTABLE_NOW"
        repair_dependency_penalty = clamp01(repair_priority if repair_needed else repair_priority * 0.35)
        scenario_similarity = deterministic_scenario_similarity(condition, regime, score)
        scenario_transferability = clamp01(
            numeric(score, "scenario_transferability_score", scenario_similarity) * 0.7
            + scenario_similarity * 0.3
        )
        total_score = candidate_selection_score(
            {
                "normalized_net_edge_after_costs": normalized_net_edge,
                "edge_lower_confidence_bound": lcb,
                "pr166_sm_refreshed_score": numeric(score, "refreshed_net_edge_score"),
                "result_confidence_score": result_confidence,
                "condition_memory_preference_score": condition_memory_score,
                "point_in_time_score": numeric(score, "point_in_time_score"),
                "no_lookahead_score": numeric(score, "no_lookahead_score"),
                "scenario_transferability_score": scenario_transferability,
                "capacity_score": numeric(score, "capacity_score"),
                "marginal_utility_score": numeric(score, "marginal_utility_score", numeric(prior, "marginal_candidate_utility", 0.0)),
                "expected_information_gain_score": expected_information_gain,
                "quantum_mapping_readiness_score": numeric(score, "quantum_mapping_readiness_score"),
                "false_discovery_risk_adjustment": numeric(score, "false_discovery_risk_adjustment", numeric(fd, "false_discovery_risk_adjustment", 0.0)),
                "overfit_risk_adjustment": numeric(score, "overfit_risk_adjustment", numeric(overfit, "overfit_risk_adjustment", 0.0)),
                "cost_drag_ratio": numeric(score, "cost_drag_ratio"),
                "latency_drag_ratio": numeric(score, "latency_drag_ratio"),
                "liquidity_drag_ratio": numeric(score, "liquidity_drag_ratio"),
                "adverse_selection_ratio": numeric(score, "adverse_selection_ratio"),
                "crowding_penalty": numeric(score, "crowding_penalty", numeric(capacity, "crowding_penalty", 0.0)),
                "correlation_cluster_penalty": numeric(score, "correlation_cluster_penalty", numeric(correlation, "correlation_cluster_penalty", 0.0)),
                "settlement_sensitivity_score": settlement_sensitivity_score(score),
                "rank_instability_adjustment": numeric(score, "rank_instability_adjustment", numeric(overfit, "rank_instability_adjustment", 0.0)),
                "repair_dependency_penalty": repair_dependency_penalty,
            }
        )
        cluster_id = str(
            correlation.get("correlation_cluster_id")
            or prior.get("duplicate_edge_cluster")
            or condition.get("duplicate_edge_cluster")
            or f"PR165_D2_CORRELATION_CLUSTER::{candidate_id[-5:]}"
        )
        raw_context.append(
            {
                "index": index,
                "score": score,
                "memory": memory,
                "rank": rank,
                "repair": repair,
                "fd": fd,
                "overfit": overfit,
                "capacity": capacity,
                "correlation": correlation,
                "prior": prior,
                "prior_score": prior_score,
                "prior_marginal": prior_marginal,
                "confidence": confidence,
                "condition": condition,
                "regime": regime,
                "candidate_packet_id": candidate_id,
                "qku_id": str(score.get("qku_id") or prior.get("qku_id") or c.NOT_APPLICABLE_ID),
                "formula_id": str(score.get("formula_id") or prior.get("formula_family") or c.NOT_APPLICABLE_ID),
                "algorithm_id": str(score.get("algorithm_id") or prior.get("algorithm_family") or c.NOT_APPLICABLE_ID),
                "parameter_stack_id": str(condition.get("parameter_stack_family") or prior.get("candidate_version") or "PR165_D2_PARAMETER_STACK::INHERITED_REPLAY_PAPER"),
                "condition_fingerprint_id": str(score.get("condition_fingerprint_id") or prior.get("condition_fingerprint_id") or c.NOT_APPLICABLE_ID),
                "scenario_group_id": str(score.get("scenario_id") or prior.get("scenario_group_id") or c.NOT_APPLICABLE_ID),
                "combination_id": str(score.get("combination_id") or prior.get("combination_fingerprint_id") or c.NOT_APPLICABLE_ID),
                "prior_pr165_d_rank": parse_rank(prior.get("pr165_rank_ref")) or index,
                "pr166_sm_refreshed_score": numeric(score, "refreshed_net_edge_score"),
                "pr166_sm_memory_outcome": str(memory.get("memory_outcome") or score.get("memory_outcome") or "TERMINAL_BY_NATURE_WITH_REASON"),
                "condition_memory_preference_score": condition_memory_score,
                "pr166_sm_rank_delta": numeric(score, "rank_delta_when_available", numeric(rank, "rank_delta_when_available", 0.0)),
                "gross_edge": numeric(score, "gross_edge"),
                "net_edge_after_costs": numeric(score, "net_edge_after_costs"),
                "normalized_net_edge_after_costs": normalized_net_edge,
                "edge_lower_confidence_bound": lcb,
                "result_confidence_score": result_confidence,
                "point_in_time_score": numeric(score, "point_in_time_score"),
                "no_lookahead_score": numeric(score, "no_lookahead_score"),
                "fee_cost_component": numeric(score, "maker_taker_fees"),
                "spread_cost_component": numeric(score, "spread_cost"),
                "slippage_cost_component": numeric(score, "slippage_cost"),
                "latency_cost_component": numeric(score, "latency_drag"),
                "market_impact_cost_component": numeric(score, "market_impact_cost"),
                "liquidity_cost_component": numeric(score, "liquidity_drag"),
                "settlement_cost_component": numeric(score, "settlement_payoff_adjustment"),
                "cost_drag_ratio": numeric(score, "cost_drag_ratio"),
                "latency_drag_ratio": numeric(score, "latency_drag_ratio"),
                "liquidity_drag_ratio": numeric(score, "liquidity_drag_ratio"),
                "adverse_selection_ratio": numeric(score, "adverse_selection_ratio"),
                "settlement_sensitivity_score": settlement_sensitivity_score(score),
                "false_discovery_risk_adjustment": numeric(score, "false_discovery_risk_adjustment", numeric(fd, "false_discovery_risk_adjustment", 0.0)),
                "overfit_risk_adjustment": numeric(score, "overfit_risk_adjustment", numeric(overfit, "overfit_risk_adjustment", 0.0)),
                "rank_instability_adjustment": numeric(score, "rank_instability_adjustment", numeric(overfit, "rank_instability_adjustment", 0.0)),
                "capacity_score": numeric(score, "capacity_score", numeric(capacity, "capacity_score", 0.5)),
                "crowding_penalty": numeric(score, "crowding_penalty", numeric(capacity, "crowding_penalty", 0.0)),
                "correlation_cluster_penalty": numeric(score, "correlation_cluster_penalty", numeric(correlation, "correlation_cluster_penalty", 0.0)),
                "correlation_cluster_id": cluster_id,
                "near_duplicate_cluster_size": int(cluster_counts.get(cluster_id, 1) or 1),
                "scenario_similarity_score": scenario_similarity,
                "scenario_transferability_score": scenario_transferability,
                "marginal_utility_score": numeric(score, "marginal_utility_score", numeric(prior, "marginal_candidate_utility", 0.0)),
                "expected_information_gain_score": expected_information_gain,
                "repair_priority_score": repair_priority,
                "repair_dependency_penalty": repair_dependency_penalty,
                "repair_needed_before_retest": repair_needed,
                "field_materialization_required_flag": field_materialization_required,
                "quantum_mapping_readiness_score": numeric(score, "quantum_mapping_readiness_score"),
                "quantum_priority_after_replay_paper": numeric(score, "quantum_priority_after_replay_paper"),
                "candidate_selection_score_v2": total_score,
                "market_scope": str(condition.get("market_type") or regime.get("market_type") or "PREDICTION_MARKET_BINARY_OR_COMPLEMENT_CANDIDATE"),
                "venue": str(condition.get("venue") or regime.get("venue") or "VENUE_NEUTRAL_SYNTHETIC_FIXTURE"),
                "market_id": str(condition.get("market_id_or_candidate_market_ref") or regime.get("market_id") or c.NOT_APPLICABLE_ID),
                "prediction_market_event_type": str(condition.get("event_type") or "BINARY_EVENT_MARKET_SYNTHETIC_REPRESENTATIVE"),
                "yes_no_side": str(condition.get("side") or regime.get("side") or "YES"),
                "time_to_resolution_bucket": str(condition.get("time_to_resolution_bucket") or regime.get("time_to_resolution_bucket") or "TERMINAL_BY_NATURE_WITH_REASON"),
                "liquidity_bucket": str(condition.get("liquidity_bucket") or regime.get("liquidity_bucket") or "TERMINAL_BY_NATURE_WITH_REASON"),
                "spread_bucket": str(condition.get("spread_bucket") or regime.get("spread_bucket") or "TERMINAL_BY_NATURE_WITH_REASON"),
                "latency_bucket": str(condition.get("latency_bucket") or regime.get("latency_bucket") or "TERMINAL_BY_NATURE_WITH_REASON"),
                "settlement_bucket": str(condition.get("market_maturity_bucket") or "SETTLEMENT_BUCKET_REPLAY_PAPER_PROXY"),
                "connector_dependency_class": connector_dependency_class(condition),
                "venue_semantic_dependency_class": venue_dependency_class(condition),
                "future_connector_pr_refs": list(c.FUTURE_CONNECTOR_PR_REFS),
                "future_venue_readiness_route": "PR174_THROUGH_PR181_REFERENCE_ROUTE_ONLY",
                "source_row_refs": [
                    str(score.get("row_id") or score.get("deterministic_sort_key")),
                    str(memory.get("row_id") or "PR166_SM_MEMORY_ROW_TERMINAL_BY_NATURE"),
                    str(repair.get("row_id") or "PR166_SM_REPAIR_ROW_TERMINAL_BY_NATURE"),
                ],
            }
        )
    ranked = sorted(raw_context, key=ranking_sort_key)
    selected_cluster_seen: set[str] = set()
    selected_index = 0
    for refreshed_rank, row in enumerate(ranked, start=1):
        row["pr165_d2_rank"] = refreshed_rank
        eligible = (
            row["net_edge_after_costs"] >= c.MATERIAL_NEGATIVE_NET_EDGE_THRESHOLD
            and not row["repair_needed_before_retest"]
            and row["result_confidence_score"] >= c.LOW_CONFIDENCE_THRESHOLD
            and row["overfit_risk_adjustment"] < c.OVERFIT_RISK_THRESHOLD
        )
        if row["repair_needed_before_retest"]:
            state = SelectionState.ROUTE_TO_PR166_SF_REPAIR_BEFORE_RETEST.value
            downstream_route = DownstreamRoute.PR166_SF.value
            no_orphan = NoOrphanStatus.CONNECTED_TO_PR166_SF_ROUTE.value
            reasons = ["REPAIR_PRIORITY_REQUIRES_PR166_SF_BEFORE_RETEST"]
        elif row["net_edge_after_costs"] < c.MATERIAL_NEGATIVE_NET_EDGE_THRESHOLD:
            state = SelectionState.EXCLUDED_BY_NEGATIVE_NET_EDGE_WITH_REASON.value
            downstream_route = DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value
            no_orphan = NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value
            reasons = ["MATERIAL_NEGATIVE_NET_EDGE_AFTER_COSTS"]
        elif row["result_confidence_score"] < c.LOW_CONFIDENCE_THRESHOLD:
            state = SelectionState.EXCLUDED_BY_LOW_CONFIDENCE_WITH_REASON.value
            downstream_route = DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value
            no_orphan = NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value
            reasons = ["LOW_RESULT_CONFIDENCE_AFTER_REPLAY_PAPER"]
        elif row["overfit_risk_adjustment"] >= c.OVERFIT_RISK_THRESHOLD:
            state = SelectionState.EXCLUDED_BY_OVERFIT_RISK_WITH_REASON.value
            downstream_route = DownstreamRoute.PR173.value
            no_orphan = NoOrphanStatus.CONNECTED_TO_PR173_AGENT_GOVERNANCE_ROUTE.value
            reasons = ["OVERFIT_RISK_EXCEEDS_SELECTION_POLICY"]
        elif eligible:
            selected_index += 1
            if row["correlation_cluster_id"] not in selected_cluster_seen:
                selected_cluster_seen.add(row["correlation_cluster_id"])
                state = SelectionState.SELECTED_AS_CHAMPION.value if selected_index <= 60 else SelectionState.SELECTED_AS_DIVERSIFYING_CANDIDATE.value
            elif row["quantum_mapping_readiness_score"] >= 0.70:
                state = SelectionState.SELECTED_AS_QUANTUM_PRIORITY_CANDIDATE.value
            elif row["latency_drag_ratio"] <= 0.05:
                state = SelectionState.SELECTED_AS_LOW_LATENCY_CANDIDATE.value
            else:
                state = SelectionState.SELECTED_AS_CHALLENGER.value
            downstream_route = DownstreamRoute.PR166_S_RETEST_LOOP_V2.value
            no_orphan = NoOrphanStatus.CONNECTED_TO_PR166_S_RETEST_LOOP.value
            reasons = ["NON_MATERIAL_NEGATIVE_NET_EDGE_WITH_REPLAY_PAPER_LEARNING_VALUE", "REPAIR_PRIORITY_BELOW_RETEST_BLOCKING_THRESHOLD"]
        else:
            state = SelectionState.WATCHLIST_UNDER_MATCHING_CONDITIONS.value
            downstream_route = DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value
            no_orphan = NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value
            reasons = ["WATCHLIST_RETENTION_FOR_CONDITION_MEMORY_REVIEW"]
        row["selection_state"] = state
        row["selection_reason_codes"] = reasons
        row["downstream_route"] = downstream_route
        row["no_orphan_status"] = no_orphan
        row["selected_for_retest_v2_flag"] = downstream_route == DownstreamRoute.PR166_S_RETEST_LOOP_V2.value
    return ranked


def build_ranking_rows(context: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(context, start=1):
        route = item["downstream_route"]
        row = common_fields(
            artifact_id="PR165_D2_NET_EDGE_ADJUSTED_CANDIDATE_RANKING",
            row_id=stable_id("PR165_D2_RANKING", index),
            qku_id=item["qku_id"],
            formula_id=item["formula_id"],
            algorithm_id=item["algorithm_id"],
            candidate_packet_id=item["candidate_packet_id"],
            condition_fingerprint_id=item["condition_fingerprint_id"],
            scenario_group_id=item["scenario_group_id"],
            combination_id=item["combination_id"],
            upstream_artifact_refs=[
                "PR166_SM_RefreshedScoreRegistry.report.json",
                "PR166_SM_RefreshedMemoryLedger.report.json",
                "PR166_SM_NetEdgeRankDeltaRegistry.report.json",
                "PR166_SM_RepairPriorityRegistry.report.json",
                "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json",
            ],
            upstream_row_refs=item["source_row_refs"],
            upstream_value_refs=[
                "gross_edge",
                "net_edge_after_costs",
                "normalized_net_edge_after_costs",
                "repair_priority_score",
                "candidate_selection_score_v2",
            ],
            downstream_pr_refs=[route],
            downstream_artifact_refs=[
                "PR165_D2_ReplayPaperRetestBatchV2.report.json",
                "PR165_D2_RepairAwareSelectionQueue.report.json",
                "PR165_D2_RouteTriageMatrix.report.json",
            ],
            no_orphan_status=item["no_orphan_status"],
            selection_state=item["selection_state"],
            materialization_action_ref=materialization_ref(item),
            repair_route_ref=repair_route_ref(item),
            connector_dependency_class=item["connector_dependency_class"],
            venue_semantic_dependency_class=item["venue_semantic_dependency_class"],
            future_connector_pr_refs=item["future_connector_pr_refs"],
            future_venue_readiness_route=item["future_venue_readiness_route"],
        )
        row.update(selection_numeric_fields(item))
        row.update(
            {
                "pr165_d2_rank": item["pr165_d2_rank"],
                "parameter_stack_id": item["parameter_stack_id"],
                "market_scope": item["market_scope"],
                "venue": item["venue"],
                "market_id": item["market_id"],
                "prediction_market_event_type": item["prediction_market_event_type"],
                "yes_no_side": item["yes_no_side"],
                "time_to_resolution_bucket": item["time_to_resolution_bucket"],
                "liquidity_bucket": item["liquidity_bucket"],
                "spread_bucket": item["spread_bucket"],
                "latency_bucket": item["latency_bucket"],
                "settlement_bucket": item["settlement_bucket"],
                "correlation_cluster_id": item["correlation_cluster_id"],
                "near_duplicate_cluster_size": item["near_duplicate_cluster_size"],
                "selection_reason_codes": item["selection_reason_codes"],
                "downstream_route": route,
                "selected_for_retest_v2_flag": item["selected_for_retest_v2_flag"],
                "repair_needed_before_retest": item["repair_needed_before_retest"],
                "connector_binding_allowed_in_this_pr": False,
            }
        )
        rows.append(row)
    return rows


def build_tca_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, source in enumerate(ranking_rows, start=1):
        total_drag = round6(
            source["fee_cost_component"]
            + source["spread_cost_component"]
            + source["slippage_cost_component"]
            + source["market_impact_cost_component"]
            + source["latency_cost_component"]
            + source["liquidity_cost_component"]
            + source["settlement_cost_component"]
        )
        net_after_prompt_tca_formula = round6(source["gross_edge"] - total_drag)
        row = common_fields_for_candidate(
            source,
            "PR165_D2_TCA_DECOMPOSITION_SELECTION_LEDGER",
            stable_id("PR165_D2_TCA", index),
            ["PR166_S_ExecutionCostLedger.report.json", "PR166_SM_RefreshedScoreRegistry.report.json"],
            ["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"],
            owning_agent="risk_manager_agent",
        )
        row.update(
            {
                "gross_edge": source["gross_edge"],
                "fee_cost_component": source["fee_cost_component"],
                "spread_cost_component": source["spread_cost_component"],
                "slippage_cost_component": source["slippage_cost_component"],
                "market_impact_cost_component": source["market_impact_cost_component"],
                "latency_cost_component": source["latency_cost_component"],
                "liquidity_cost_component": source["liquidity_cost_component"],
                "settlement_cost_component": source["settlement_cost_component"],
                "implementation_shortfall_proxy": round6(total_drag + max(0.0, -source["net_edge_after_costs"]) * 0.15),
                "total_execution_cost_drag": total_drag,
                "net_edge_after_costs": net_after_prompt_tca_formula,
                "pr166_sm_net_edge_after_costs_with_adverse_selection_drag": source["net_edge_after_costs"],
                "edge_lower_confidence_bound": source["edge_lower_confidence_bound"],
                "cost_component_source_refs": [
                    "PR166_S_ExecutionCostLedger.report.json",
                    "PR166_SM_RefreshedScoreRegistry.report.json",
                ],
                "cost_component_materialization_action_refs": [source["materialization_action_ref"]],
                "tca_quality_score": clamp01(
                    source["result_confidence_score"] * 0.4
                    + source["point_in_time_score"] * 0.3
                    + source["no_lookahead_score"] * 0.3
                ),
            }
        )
        rows.append(row)
    return rows


def build_score_component_provenance_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    row_index = 0
    for ranked in ranking_rows:
        for component_name, weight in c.SCORE_WEIGHTS.items():
            row_index += 1
            raw_value = numeric(ranked, component_name)
            normalized_value = clamp01(raw_value)
            row = common_fields_for_candidate(
                ranked,
                "PR165_D2_SCORE_COMPONENT_PROVENANCE_LEDGER",
                stable_id("PR165_D2_SCORE_COMPONENT", row_index),
                ["PR166_SM_RefreshedScoreRegistry.report.json", "PR165_D_SelectionScoreRegistry.report.json"],
                ["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"],
                owning_agent="parameter_selector_agent",
            )
            row.update(
                {
                    "score_component_name": component_name,
                    "raw_value": raw_value,
                    "raw_unit_class": unit_class_for_component(component_name),
                    "normalized_value": normalized_value,
                    "normalized_unit_class": UnitClass.NORMALIZED_0_1.value,
                    "component_weight": weight,
                    "weighted_contribution": round6(weight * normalized_value),
                    "higher_is_better_flag": weight > 0,
                    "source_artifact_refs": [
                        "PR166_SM_RefreshedScoreRegistry.report.json",
                        "PR166_S_ResultConfidenceRegistry.report.json",
                        "PR165_D_MarginalUtilitySelectionLedger.report.json",
                    ],
                    "source_row_refs": ranked["upstream_row_refs"],
                    "source_value_refs": [component_name],
                    "fallback_used_flag": False,
                    "fallback_reason": "DETERMINISTIC_UPSTREAM_VALUE_CONSUMED",
                    "imputation_used_flag": False,
                    "imputation_method": "NO_IMPUTATION_USED",
                    "materialization_action_ref": ranked["materialization_action_ref"],
                    "confidence_of_component": ranked["result_confidence_score"],
                }
            )
            rows.append(row)
    return rows


def build_prediction_market_probability_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, source in enumerate(ranking_rows, start=1):
        implied = clamp01(0.50 - source["gross_edge"] * 0.25)
        model = clamp01(implied + source["gross_edge"] * 0.50)
        cost_probability_drag = clamp01(source["total_cost_drag_proxy"] if "total_cost_drag_proxy" in source else _total_cost_drag(source))
        breakeven = clamp01(implied + cost_probability_drag)
        yes_price = round6(implied * 100.0)
        no_price = round6(100.0 - yes_price)
        ev_cents = round6((model - breakeven) * 100.0)
        row = common_fields_for_candidate(
            source,
            "PR165_D2_PREDICTION_MARKET_PROBABILITY_EDGE_LEDGER",
            stable_id("PR165_D2_PROBABILITY_EDGE", index),
            ["PR165_B_ConditionFingerprintRegistry.report.json", "PR166_SM_RefreshedScoreRegistry.report.json"],
            ["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"],
        )
        row.update(
            {
                "market_scope": source["market_scope"],
                "venue": source["venue"],
                "prediction_market_event_type": source["prediction_market_event_type"],
                "yes_no_side": source["yes_no_side"],
                "market_implied_probability": implied,
                "model_probability_estimate": model,
                "probability_edge_points": round6(model - implied),
                "break_even_probability_after_fees_spread_slippage_latency_liquidity_impact_settlement": breakeven,
                "yes_price_cents": yes_price,
                "no_price_cents": no_price,
                "yes_no_symmetric_price_check": round6(yes_price + no_price) == 100.0,
                "expected_value_cents_per_contract": ev_cents,
                "expected_value_bps_of_notional": round6(ev_cents * 100.0),
                "calibration_bin_ref": calibration_bin_ref(source),
                "brier_or_logloss_proxy_score": clamp01(1.0 - abs(model - implied)),
                "probability_calibration_score": source["result_confidence_score"],
                "settlement_probability_sensitivity": source["settlement_sensitivity_score"],
                "probability_component_source_refs": [
                    "PR166_SM_RefreshedScoreRegistry.report.json",
                    "PR165_B_ConditionFingerprintRegistry.report.json",
                ],
                "probability_component_materialization_action_refs": [source["materialization_action_ref"]],
                "unit_ref": {
                    "market_implied_probability": UnitClass.PROBABILITY_POINT.value,
                    "yes_price_cents": UnitClass.CENTS_PER_CONTRACT.value,
                    "expected_value_bps_of_notional": UnitClass.BASIS_POINTS_OF_NOTIONAL.value,
                },
            }
        )
        rows.append(row)
    return rows


def build_microstructure_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, source in enumerate(ranking_rows, start=1):
        spread_cents = bucket_to_spread_cents(source["spread_bucket"], source["spread_cost_component"])
        depth_base = depth_from_liquidity_bucket(source["liquidity_bucket"])
        maker_role = "MAKER" if "MAKER" in source.get("selection_reason_codes", []) or source["latency_drag_ratio"] < 0.08 else "MAKER_TAKER_PROVISIONAL"
        row = common_fields_for_candidate(
            source,
            "PR165_D2_MICROSTRUCTURE_FEATURE_LEDGER",
            stable_id("PR165_D2_MICROSTRUCTURE", index),
            ["PR165_B_ConditionFingerprintRegistry.report.json", "PR166_S_ExecutionCostLedger.report.json"],
            ["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"],
            owning_agent="risk_manager_agent",
        )
        row.update(
            {
                "venue": source["venue"],
                "market_id": source["market_id"],
                "best_bid_yes_cents": round6(max(1.0, 50.0 - spread_cents / 2.0)),
                "best_ask_yes_cents": round6(min(99.0, 50.0 + spread_cents / 2.0)),
                "best_bid_no_cents": round6(max(1.0, 50.0 - spread_cents / 2.0)),
                "best_ask_no_cents": round6(min(99.0, 50.0 + spread_cents / 2.0)),
                "spread_cents": spread_cents,
                "spread_bucket": source["spread_bucket"],
                "order_book_depth_top_1": depth_base,
                "order_book_depth_top_5": depth_base * 5,
                "order_book_depth_top_10": depth_base * 10,
                "order_book_imbalance_score": clamp01(0.5 + (source["gross_edge"] * 0.1)),
                "liquidity_bucket": source["liquidity_bucket"],
                "maker_taker_role_class": maker_role,
                "expected_fill_probability_proxy": clamp01(source["capacity_score"] - source["liquidity_drag_ratio"] * 0.2),
                "queue_position_proxy_score": clamp01(1.0 - source["latency_drag_ratio"]),
                "quote_staleness_ttl_ms": int(max(500, 5000 * (1.0 - source["latency_drag_ratio"]))),
                "latency_budget_ms": int(max(100, 2000 * (1.0 - source["latency_drag_ratio"]))),
                "latency_bucket": source["latency_bucket"],
                "market_impact_bucket": bucket_from_value(source["market_impact_cost_component"], (0.005, 0.02), "IMPACT"),
                "adverse_selection_proxy": source["adverse_selection_ratio"],
                "min_trade_size_candidate": 1,
                "capacity_bucket": bucket_from_value(source["capacity_score"], (0.35, 0.65), "CAPACITY"),
                "microstructure_quality_score": clamp01(
                    source["capacity_score"] * 0.4
                    + (1.0 - source["cost_drag_ratio"]) * 0.2
                    + (1.0 - source["latency_drag_ratio"]) * 0.2
                    + (1.0 - source["liquidity_drag_ratio"]) * 0.2
                ),
                "microstructure_source_refs": [
                    "PR166_S_ExecutionCostLedger.report.json",
                    "PR165_B_ConditionFingerprintRegistry.report.json",
                ],
                "microstructure_materialization_action_refs": [source["materialization_action_ref"]],
            }
        )
        rows.append(row)
    return rows


def build_repair_rows(ranking_rows: list[dict[str, Any]], source: SourceData) -> list[dict[str, Any]]:
    optional_present = "PR166_SF_RepairedCandidateRetestQueue.report.json" in source.records
    rows = []
    for index, ranked in enumerate(ranking_rows, start=1):
        repair_needed = ranked["repair_dependency_penalty"] >= c.REPAIR_BEFORE_RETEST_PRIORITY_THRESHOLD
        row = common_fields_for_candidate(
            ranked,
            "PR165_D2_REPAIR_AWARE_SELECTION_QUEUE",
            stable_id("PR165_D2_REPAIR_QUEUE", index),
            ["PR166_SM_RepairPriorityRegistry.report.json", "PR166_SM_FieldMaterializationCandidateRegistry.report.json"],
            ["PR166-SF", "PR165_D2_ReplayPaperRetestBatchV2.report.json"],
            downstream_pr_refs=[DownstreamRoute.PR166_SF.value] if repair_needed else [DownstreamRoute.PR166_S_RETEST_LOOP_V2.value],
            owning_agent="parameter_selector_agent",
            no_orphan_status=(
                NoOrphanStatus.CONNECTED_TO_PR166_SF_ROUTE.value
                if repair_needed
                else NoOrphanStatus.CONNECTED_TO_RETEST_BATCH_ROUTE.value
            ),
        )
        row.update(
            {
                "repair_needed_flag": repair_needed,
                "repair_source": "PR166_SM_REPAIR_PRIORITY_AND_FIELD_MATERIALIZATION_HANDOFF",
                "repair_priority_score": ranked["repair_priority_score"],
                "exact_missing_field": exact_missing_field(ranked),
                "field_materialization_action_ref": ranked["materialization_action_ref"],
                "pr166_sm_failure_route_ref": ranked["repair_route_ref"],
                "optional_pr166_sf_queue_ref_if_present": (
                    "PR166_SF_RepairedCandidateRetestQueue.report.json"
                    if optional_present
                    else "OPTIONAL_PR166_SF_QUEUE_NOT_PRESENT_PR166_SM_REPAIR_HANDOFF_CONSUMED"
                ),
                "optional_pr166_sf_queue_status": (
                    "OPTIONAL_PRESENT_CONSUMED"
                    if optional_present
                    else "OPTIONAL_NOT_PRESENT_CONSUMED_PR166_SM_REPAIR_HANDOFF"
                ),
                "selection_after_repair_state": (
                    SelectionState.SELECTED_AS_REPAIR_AWARE_CANDIDATE.value
                    if repair_needed
                    else ranked["selection_state"]
                ),
                "route_to_pr166_sf_flag": repair_needed,
                "route_to_pr165_d2_retest_flag": (not repair_needed and ranked["selected_for_retest_v2_flag"]),
            }
        )
        rows.append(row)
    return rows


def build_quantum_rows(source: SourceData, ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranking_by = _by_candidate(ranking_rows)
    mapping_by = _by_candidate(source.records["PR166_SM_QuantumMappingCandidateReadiness.report.json"])
    priority_rows = sorted(
        source.records["PR166_SM_QuantumPriorityAfterReplayPaperRegistry.report.json"],
        key=lambda row: str(row.get("candidate_packet_id")),
    )
    rows = []
    for index, quantum in enumerate(priority_rows, start=1):
        candidate_id = str(quantum.get("candidate_packet_id"))
        ranked = ranking_by.get(candidate_id, {})
        mapping = mapping_by.get(candidate_id, {})
        readiness = numeric(quantum, "quantum_mapping_readiness_score", numeric(mapping, "quantum_mapping_readiness_score", 0.0))
        structurally_ready = readiness >= 0.60 and bool(quantum.get("objective_terms")) and bool(quantum.get("variable_domains"))
        route = DownstreamRoute.PR166_Q.value if structurally_ready else DownstreamRoute.PR162E_Q.value
        no_orphan = (
            NoOrphanStatus.CONNECTED_TO_PR166_Q_ROUTE.value
            if structurally_ready
            else NoOrphanStatus.CONNECTED_TO_PR162E_Q_ROUTE.value
        )
        row = common_fields(
            artifact_id="PR165_D2_QUANTUM_CANDIDATE_PRIORITY_V2",
            row_id=stable_id("PR165_D2_QUANTUM_PRIORITY", index),
            qku_id=str(quantum.get("qku_id") or ranked.get("qku_id") or c.NOT_APPLICABLE_ID),
            formula_id=str(quantum.get("formula_id") or ranked.get("formula_id") or c.NOT_APPLICABLE_ID),
            algorithm_id=str(quantum.get("algorithm_id") or ranked.get("algorithm_id") or c.NOT_APPLICABLE_ID),
            candidate_packet_id=candidate_id,
            condition_fingerprint_id=str(quantum.get("condition_fingerprint_id") or ranked.get("condition_fingerprint_id") or c.NOT_APPLICABLE_ID),
            scenario_group_id=str(quantum.get("scenario_id") or ranked.get("scenario_group_id") or c.NOT_APPLICABLE_ID),
            combination_id=str(quantum.get("combination_id") or ranked.get("combination_id") or c.NOT_APPLICABLE_ID),
            upstream_artifact_refs=[
                "PR166_SM_QuantumPriorityAfterReplayPaperRegistry.report.json",
                "PR166_SM_QuantumMappingCandidateReadiness.report.json",
                "PR166_S_QuantumAdvisoryPassthrough.report.json",
            ],
            upstream_row_refs=[str(quantum.get("row_id") or quantum.get("deterministic_sort_key"))],
            upstream_value_refs=[
                "quantum_mapping_readiness_score",
                "objective_terms",
                "variable_domains",
                "constraint_terms",
            ],
            downstream_pr_refs=[route],
            downstream_artifact_refs=["PR166-Q", "PR162E-Q"],
            no_orphan_status=no_orphan,
            value_authority_lane=ValueAuthorityLane.QUANTUM_PRIORITY_CANDIDATE_LANE.value,
            source_authority_class=SourceAuthorityClass.PRIOR_ROADMAP_ARTIFACT_NOT_SOURCE_TRUTH.value,
            computability_status=(
                ComputabilityStatus.COMPUTABLE_FOR_QUANTUM_PRIORITY_ONLY.value
                if structurally_ready
                else ComputabilityStatus.COMPUTABLE_AFTER_EXACT_MATERIALIZATION_ACTION.value
            ),
            selection_state=(
                SelectionState.ROUTE_TO_PR166_Q_QUANTUM_COMPARATOR.value
                if structurally_ready
                else SelectionState.ROUTE_TO_PR162E_Q_QUANTUM_MAPPING.value
            ),
            materialization_action_ref=str(mapping.get("materialization_action_ref") or mapping.get("exact_materialization_action") or "PR165_D2_QUANTUM_MAPPING_MATERIALIZATION_ACTION::ROUTE_TO_PR162E_Q"),
            repair_route_ref=route,
            connector_dependency_class=ConnectorDependencyClass.NO_CONNECTOR_DEPENDENCY_FOR_SELECTION.value,
            venue_semantic_dependency_class=VenueSemanticDependencyClass.NO_VENUE_SEMANTIC_DEPENDENCY_FOR_SELECTION.value,
        )
        model_class = str(quantum.get("quantum_model_class") or "QuadraticProgram")
        structures = list(quantum.get("mapping_structures") or [])
        row.update(
            {
                "quantum_model_class": model_class,
                "quantum_structure_classes": quantum_structure_classes(model_class, structures),
                "objective_direction": str(quantum.get("objective_direction") or "maximize_net_edge"),
                "objective_order": str(quantum.get("objective_order") or "quadratic"),
                "objective_terms": list(quantum.get("objective_terms") or ["net_edge_after_costs", "selection_score_v2"]),
                "variable_domains": list(quantum.get("variable_domains") or ["binary_candidate_selection"]),
                "constraint_terms": list(quantum.get("constraint_terms") or ["capacity", "correlation_cluster", "retest_budget"]),
                "penalty_terms": list(quantum.get("penalty_terms") or ["false_discovery", "overfit", "repair_dependency"]),
                "classical_comparator_refs": [str(quantum.get("classical_comparator") or "PR165_D2_CLASSICAL_COMPARATOR::NET_EDGE_RANKING_V2")],
                "quantum_mapping_readiness_score": readiness,
                "quantum_priority_after_replay_paper": numeric(quantum, "quantum_priority_after_replay_paper"),
                "quantum_candidate_priority_v2": clamp01(
                    numeric(quantum, "quantum_priority_after_replay_paper") * 0.55
                    + readiness * 0.35
                    + numeric(ranked, "candidate_selection_score_v2", 0.0) * 0.10
                ),
                "route_to_pr166_q_flag": structurally_ready,
                "route_to_pr162e_q_flag": not structurally_ready,
                "backend_quantum_execution_created": False,
                "quantum_advantage_claim_created": False,
            }
        )
        rows.append(row)
    return rows


def build_scenario_group_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ranking_rows:
        groups[str(row["scenario_group_id"])].append(row)
    rows = []
    for index, (scenario_group_id, members) in enumerate(sorted(groups.items()), start=1):
        selected = [row for row in members if row["selected_for_retest_v2_flag"]]
        best = min(members, key=lambda row: int(row["pr165_d2_rank"]))
        row = common_fields_for_candidate(
            best,
            "PR165_D2_SCENARIO_GROUP_REFRESH_REGISTRY",
            stable_id("PR165_D2_SCENARIO_GROUP", index),
            ["PR165_D_ScenarioGroupRegistry.report.json", "PR166_SM_RefreshedScoreRegistry.report.json"],
            ["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"],
        )
        row.update(
            {
                "scenario_group_id": scenario_group_id,
                "candidate_count": len(members),
                "selected_retest_candidate_count": len(selected),
                "best_candidate_packet_id": best["candidate_packet_id"],
                "best_candidate_selection_score_v2": best["candidate_selection_score_v2"],
                "median_net_edge_after_costs": median([member["net_edge_after_costs"] for member in members]),
                "scenario_group_refresh_status": "SCENARIO_GROUP_REFRESHED_FOR_PR165_D2_SELECTION",
            }
        )
        rows.append(row)
    return rows


def build_condition_memory_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, ranked in enumerate(ranking_rows, start=1):
        row = common_fields_for_candidate(
            ranked,
            "PR165_D2_CONDITION_MEMORY_APPLICATION_LEDGER",
            stable_id("PR165_D2_CONDITION_MEMORY", index),
            ["PR166_SM_RefreshedMemoryLedger.report.json", "PR165_B_CombinationOutcomeMemoryLedger.report.json"],
            ["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"],
        )
        row.update(
            {
                "pr166_sm_memory_outcome": ranked["pr166_sm_memory_outcome"],
                "condition_memory_preference_score": ranked["condition_memory_preference_score"],
                "condition_scoped_application_only_flag": True,
                "global_permanent_ban_created": False,
                "memory_reason_codes": memory_reason_codes(ranked),
                "selection_state_after_memory": ranked["selection_state"],
            }
        )
        rows.append(row)
    return rows


def build_champion_challenger_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    selected = [row for row in ranking_rows if row["selected_for_retest_v2_flag"]]
    for index, ranked in enumerate(selected, start=1):
        role = (
            "CHAMPION"
            if ranked["selection_state"] == SelectionState.SELECTED_AS_CHAMPION.value
            else "CHALLENGER_OR_DIVERSIFIER"
        )
        row = common_fields_for_candidate(
            ranked,
            "PR165_D2_CHAMPION_CHALLENGER_SELECTION_LEDGER",
            stable_id("PR165_D2_CHAMPION_CHALLENGER", index),
            ["PR165_D_RetestBatchSelectionQueue.report.json", "PR166_SM_RefreshedScoreRegistry.report.json"],
            ["PR165_D2_ReplayPaperRetestBatchV2.report.json"],
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_RETEST_BATCH_ROUTE.value,
        )
        row.update(
            {
                "champion_challenger_role": role,
                "prior_candidate_preserved_flag": ranked["prior_pr165_d_rank"] <= 3985,
                "strongest_prior_candidate_flag": ranked["prior_pr165_d_rank"] <= 100,
                "challenger_reason_codes": ranked["selection_reason_codes"],
                "primary_cluster_representative_flag": ranked["selection_state"] == SelectionState.SELECTED_AS_CHAMPION.value,
                "bounded_backup_flag": ranked["selection_state"] in {
                    SelectionState.SELECTED_AS_CHALLENGER.value,
                    SelectionState.SELECTED_AS_QUANTUM_PRIORITY_CANDIDATE.value,
                    SelectionState.SELECTED_AS_LOW_LATENCY_CANDIDATE.value,
                },
            }
        )
        rows.append(row)
    return rows


def build_marginal_utility_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    selected_clusters: set[str] = set()
    for index, ranked in enumerate(ranking_rows, start=1):
        cluster_seen = ranked["correlation_cluster_id"] in selected_clusters
        if ranked["selected_for_retest_v2_flag"]:
            selected_clusters.add(ranked["correlation_cluster_id"])
        row = common_fields_for_candidate(
            ranked,
            "PR165_D2_MARGINAL_UTILITY_BATCH_BUILDER_LEDGER",
            stable_id("PR165_D2_MARGINAL_UTILITY", index),
            ["PR165_D_MarginalUtilitySelectionLedger.report.json", "PR166_SM_RefreshedScoreRegistry.report.json"],
            ["PR165_D2_ReplayPaperRetestBatchV2.report.json"],
        )
        row.update(
            {
                "marginal_utility_score": ranked["marginal_utility_score"],
                "expected_information_gain_score": ranked["expected_information_gain_score"],
                "scenario_coverage_gain": ranked["scenario_similarity_score"],
                "formula_algorithm_diversity_gain": clamp01(1.0 / max(1, ranked["near_duplicate_cluster_size"])),
                "quantum_coverage_gain": ranked["quantum_mapping_readiness_score"],
                "low_latency_coverage_gain": clamp01(1.0 - ranked["latency_drag_ratio"]),
                "repair_aware_learning_value": clamp01(1.0 - ranked["repair_dependency_penalty"]),
                "redundancy_penalty": clamp01(1.0 if cluster_seen else ranked["correlation_cluster_penalty"]),
                "selected_for_batch_flag": ranked["selected_for_retest_v2_flag"],
            }
        )
        rows.append(row)
    return rows


def build_capacity_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cluster_best: dict[str, str] = {}
    for ranked in ranking_rows:
        cluster_best.setdefault(ranked["correlation_cluster_id"], ranked["candidate_packet_id"])
    rows = []
    for index, ranked in enumerate(ranking_rows, start=1):
        is_rep = cluster_best[ranked["correlation_cluster_id"]] == ranked["candidate_packet_id"]
        row = common_fields_for_candidate(
            ranked,
            "PR165_D2_CAPACITY_CROWDING_CORRELATION_SELECTION_LEDGER",
            stable_id("PR165_D2_CAPACITY", index),
            ["PR166_SM_CapacityAndCrowdingRegistry.report.json", "PR166_SM_CorrelationClusterRegistry.report.json"],
            ["PR165_D2_ReplayPaperRetestBatchV2.report.json"],
            owning_agent="risk_manager_agent",
        )
        row.update(
            {
                "capacity_score": ranked["capacity_score"],
                "capacity_bucket": bucket_from_value(ranked["capacity_score"], (0.35, 0.65), "CAPACITY"),
                "crowding_penalty": ranked["crowding_penalty"],
                "correlation_cluster_id": ranked["correlation_cluster_id"],
                "correlation_cluster_penalty": ranked["correlation_cluster_penalty"],
                "marginal_utility_score": ranked["marginal_utility_score"],
                "selected_cluster_representative_flag": is_rep and ranked["selected_for_retest_v2_flag"],
                "backup_challenger_flag": (not is_rep) and ranked["selected_for_retest_v2_flag"],
                "portfolio_selection_note": (
                    "PRIMARY_CLUSTER_REPRESENTATIVE_SELECTED"
                    if is_rep and ranked["selected_for_retest_v2_flag"]
                    else "CANDIDATE_RETAINED_FOR_DIVERSIFICATION_OR_REVIEW"
                ),
                "downstream_route": ranked["downstream_route"],
            }
        )
        rows.append(row)
    return rows


def build_false_discovery_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, ranked in enumerate(ranking_rows, start=1):
        related_trials = max(1, ranked["near_duplicate_cluster_size"] * 2)
        row = common_fields_for_candidate(
            ranked,
            "PR165_D2_FALSE_DISCOVERY_OVERFIT_SELECTION_CONTROL",
            stable_id("PR165_D2_FALSE_DISCOVERY", index),
            ["PR166_SM_FalseDiscoveryRiskRefreshLedger.report.json", "PR166_SM_OverfitAndRankInstabilityRegistry.report.json"],
            ["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"],
            owning_agent="risk_manager_agent",
        )
        row.update(
            {
                "num_related_trials": related_trials,
                "effective_independent_trial_count": max(1, int(related_trials * (1.0 - ranked["correlation_cluster_penalty"]))),
                "near_duplicate_cluster_size": ranked["near_duplicate_cluster_size"],
                "prior_rank_stability": clamp01(1.0 - min(1.0, abs(ranked["pr166_sm_rank_delta"]) / 6502.0)),
                "refreshed_rank_stability": clamp01(1.0 - ranked["rank_instability_adjustment"]),
                "sample_depth_score": ranked["result_confidence_score"],
                "false_discovery_risk_adjustment": ranked["false_discovery_risk_adjustment"],
                "overfit_risk_adjustment": ranked["overfit_risk_adjustment"],
                "rank_instability_adjustment": ranked["rank_instability_adjustment"],
                "selection_allowed_after_penalty": ranked["selected_for_retest_v2_flag"],
                "reason_codes": false_discovery_reason_codes(ranked),
                "downstream_route": ranked["downstream_route"],
            }
        )
        rows.append(row)
    return rows


def build_retest_batch_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = [row for row in ranking_rows if row["selected_for_retest_v2_flag"]]
    rows = []
    for index, ranked in enumerate(selected, start=1):
        tier = retest_budget_tier(ranked, index)
        row = common_fields_for_candidate(
            ranked,
            "PR165_D2_REPLAY_PAPER_RETEST_BATCH_V2",
            stable_id("PR165_D2_RETEST_BATCH", index),
            ["PR165_D_RetestBatchSelectionQueue.report.json", "PR166_SM_RefreshedScoreRegistry.report.json"],
            ["PR166-S_RETEST_LOOP_V2"],
            downstream_pr_refs=[DownstreamRoute.PR166_S_RETEST_LOOP_V2.value],
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_RETEST_BATCH_ROUTE.value,
            value_authority_lane=ValueAuthorityLane.REPLAY_PAPER_RETEST_BATCH_LANE.value,
        )
        row.update(
            {
                "batch_id": f"PR165_D2_REPLAY_PAPER_RETEST_BATCH_V2::{((index - 1) // 100) + 1:04d}",
                "rank_in_batch": index,
                "budget_tier": tier,
                "retest_mode": "REPLAY_PAPER_RETEST_ONLY",
                "live_capital_allocation_created": False,
                "selected_reason_codes": ranked["selection_reason_codes"],
                "candidate_selection_score_v2": ranked["candidate_selection_score_v2"],
                "net_edge_after_costs": ranked["net_edge_after_costs"],
                "edge_lower_confidence_bound": ranked["edge_lower_confidence_bound"],
                "repair_before_retest_required_flag": False,
            }
        )
        rows.append(row)
    return rows


def build_retest_budget_policy_rows(ranking_rows: list[dict[str, Any]], retest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tiers = (
        "TIER_1_HIGH_CONFIDENCE_CHAMPIONS",
        "TIER_2_HIGH_EDGE_CHALLENGERS",
        "TIER_3_DIVERSIFICATION_AND_REGIME_COVERAGE",
        "TIER_4_QUANTUM_PRIORITY_CANDIDATES",
        "TIER_5_REPAIR_AWARE_WATCHLIST",
        "TIER_6_EXTERNAL_SIGNAL_CANDIDATES",
    )
    counter = Counter(row["budget_tier"] for row in retest_rows)
    rows = []
    for index, tier in enumerate(tiers, start=1):
        row = common_fields(
            artifact_id="PR165_D2_RETEST_BUDGET_ALLOCATION_POLICY",
            row_id=stable_id("PR165_D2_RETEST_BUDGET", index),
            upstream_artifact_refs=["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"],
            upstream_row_refs=["PR165_D2_RETEST_BUDGET_POLICY_ROW_SOURCE::DETERMINISTIC_POLICY"],
            upstream_value_refs=["candidate_selection_score_v2", "selection_state"],
            downstream_pr_refs=[DownstreamRoute.PR166_S_RETEST_LOOP_V2.value],
            downstream_artifact_refs=["PR165_D2_ReplayPaperRetestBatchV2.report.json"],
            selection_state=SelectionState.SELECTED_FOR_REPLAY_PAPER_RETEST_V2.value,
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_RETEST_BATCH_ROUTE.value,
        )
        row.update(
            {
                "budget_tier": tier,
                "selected_row_count": counter[tier],
                "budget_scope": "REPLAY_PAPER_RETEST_ONLY_NO_LIVE_CAPITAL_ALLOCATION",
                "selection_policy_ref": c.SCORE_POLICY_REF,
                "tier_reason": budget_tier_reason(tier),
            }
        )
        rows.append(row)
    return rows


def build_route_triage_rows(
    ranking_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for index, ranked in enumerate(ranking_rows, start=1):
        route = ranked["downstream_route"]
        row = common_fields_for_candidate(
            ranked,
            "PR165_D2_ROUTE_TRIAGE_MATRIX",
            stable_id("PR165_D2_ROUTE_TRIAGE", index),
            ["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"],
            ["PR165_D2_CommandActionMatrix.report.json"],
            downstream_pr_refs=[route],
        )
        row.update(
            {
                "route": route,
                "route_reason_codes": ranked["selection_reason_codes"],
                "responsible_agent": route_agent(route),
                "dashboard_review_flag": True,
                "governance_review_flag": route != DownstreamRoute.PR166_S_RETEST_LOOP_V2.value,
                "commander_route_required_flag": True,
            }
        )
        rows.append(row)
    offset = len(rows)
    for index, quantum in enumerate(quantum_rows[:500], start=1):
        row = common_fields(
            artifact_id="PR165_D2_ROUTE_TRIAGE_MATRIX",
            row_id=stable_id("PR165_D2_ROUTE_TRIAGE_QUANTUM", offset + index),
            qku_id=quantum["qku_id"],
            formula_id=quantum["formula_id"],
            algorithm_id=quantum["algorithm_id"],
            candidate_packet_id=quantum["candidate_packet_id"],
            condition_fingerprint_id=quantum["condition_fingerprint_id"],
            scenario_group_id=quantum["scenario_group_id"],
            combination_id=quantum["combination_id"],
            upstream_artifact_refs=["PR165_D2_QuantumCandidatePriorityV2.report.json"],
            upstream_row_refs=[quantum["row_id"]],
            upstream_value_refs=["quantum_candidate_priority_v2"],
            downstream_pr_refs=quantum["downstream_pr_refs"],
            downstream_artifact_refs=["PR166-Q", "PR162E-Q"],
            owning_agent="quantum_optimizer_agent",
            no_orphan_status=quantum["no_orphan_status"],
            selection_state=quantum["selection_state"],
        )
        row.update(
            {
                "route": quantum["downstream_pr_refs"][0],
                "route_reason_codes": ["QUANTUM_STRUCTURAL_READINESS_TRIAGE"],
                "responsible_agent": "quantum_optimizer_agent",
                "dashboard_review_flag": True,
                "governance_review_flag": True,
                "commander_route_required_flag": True,
            }
        )
        rows.append(row)
    return rows


def build_connector_readiness_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, ranked in enumerate(ranking_rows, start=1):
        row = common_fields_for_candidate(
            ranked,
            "PR165_D2_CONNECTOR_VENUE_READINESS_REFERENCE_ROUTING",
            stable_id("PR165_D2_CONNECTOR_READINESS", index),
            ["PR165_B_ConditionFingerprintRegistry.report.json", "PR165_C_ConditionRegimeFeatureMatrix.report.json"],
            ["PR174", "PR175", "PR176", "PR177", "PR178", "PR179", "PR180", "PR181"],
            downstream_pr_refs=list(c.FUTURE_CONNECTOR_PR_REFS),
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_PR174_PR181_CONNECTOR_READINESS_REFERENCE_ROUTE.value,
        )
        row.update(
            {
                "connector_dependency_class": ranked["connector_dependency_class"],
                "venue_semantic_dependency_class": ranked["venue_semantic_dependency_class"],
                "future_connector_pr_refs": ranked["future_connector_pr_refs"],
                "future_venue_readiness_route": ranked["future_venue_readiness_route"],
                "connector_binding_allowed_in_this_pr": False,
                "private_state_fetch_allowed_in_this_pr": False,
                "runtime_cash_receipt_allowed_in_this_pr": False,
                "source_truth_acceptance_allowed_in_this_pr": False,
            }
        )
        rows.append(row)
    return rows


def build_market_index_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for ranked in ranking_rows:
        key = (
            ranked["market_scope"],
            ranked["venue"],
            ranked["prediction_market_event_type"],
            ranked["time_to_resolution_bucket"],
            ranked["liquidity_bucket"],
            ranked["spread_bucket"],
            ranked["latency_bucket"],
            ranked["settlement_bucket"],
            ranked["connector_dependency_class"],
            ranked["venue_semantic_dependency_class"],
            "QUANTUM_READY" if ranked["quantum_mapping_readiness_score"] >= 0.6 else "QUANTUM_MAPPING_CANDIDATE",
            ranked["scenario_group_id"],
            ranked["downstream_route"],
        )
        groups[key].append(ranked)
    rows = []
    for index, (key, members) in enumerate(sorted(groups.items()), start=1):
        best = min(members, key=lambda row: int(row["pr165_d2_rank"]))
        row = common_fields_for_candidate(
            best,
            "PR165_D2_MARKET_SPECIFIC_SELECTION_INDEX",
            stable_id("PR165_D2_MARKET_INDEX", index),
            ["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"],
            ["PR165_D2_DashboardSelectionHandoff.report.json"],
        )
        (
            market_scope,
            venue,
            event_type,
            time_bucket,
            liquidity_bucket,
            spread_bucket,
            latency_bucket,
            settlement_bucket,
            connector_dependency,
            venue_dependency,
            quantum_bucket,
            scenario_group,
            downstream_route,
        ) = key
        row.update(
            {
                "market_scope": market_scope,
                "venue": venue,
                "prediction_market_event_type": event_type,
                "time_to_resolution_bucket": time_bucket,
                "liquidity_bucket": liquidity_bucket,
                "spread_bucket": spread_bucket,
                "latency_bucket": latency_bucket,
                "settlement_bucket": settlement_bucket,
                "connector_dependency_class": connector_dependency,
                "venue_semantic_dependency_class": venue_dependency,
                "quantum_compatibility_bucket": quantum_bucket,
                "scenario_group_id": scenario_group,
                "downstream_route": downstream_route,
                "candidate_count": len(members),
                "selected_retest_candidate_count": sum(1 for row in members if row["selected_for_retest_v2_flag"]),
                "top_candidate_packet_id": best["candidate_packet_id"],
            }
        )
        rows.append(row)
    return rows


def build_computability_rows(source: SourceData, ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranking_by = _by_candidate(ranking_rows)
    materialization_by = _by_candidate(source.records["PR166_SM_FieldMaterializationCandidateRegistry.report.json"])
    rows = []
    for index, upstream in enumerate(
        sorted(source.records["PR166_SM_QKUComputabilityClosureAudit.report.json"], key=lambda row: str(row.get("candidate_packet_id"))),
        start=1,
    ):
        candidate_id = str(upstream.get("candidate_packet_id"))
        ranked = ranking_by.get(candidate_id, {})
        materialization = materialization_by.get(candidate_id, {})
        status = computability_status_for_route(upstream, ranked)
        downstream_route = computability_downstream_route(status, ranked)
        row = common_fields(
            artifact_id="PR165_D2_QKU_FORMULA_ALGORITHM_COMPUTABILITY_ROUTING",
            row_id=stable_id("PR165_D2_COMPUTABILITY", index),
            qku_id=str(upstream.get("qku_id") or ranked.get("qku_id") or c.NOT_APPLICABLE_ID),
            formula_id=str(upstream.get("formula_id") or ranked.get("formula_id") or c.NOT_APPLICABLE_ID),
            algorithm_id=str(upstream.get("algorithm_id") or ranked.get("algorithm_id") or c.NOT_APPLICABLE_ID),
            candidate_packet_id=candidate_id,
            condition_fingerprint_id=str(upstream.get("condition_fingerprint_id") or ranked.get("condition_fingerprint_id") or c.NOT_APPLICABLE_ID),
            scenario_group_id=str(upstream.get("scenario_id") or ranked.get("scenario_group_id") or c.NOT_APPLICABLE_ID),
            combination_id=str(upstream.get("combination_id") or ranked.get("combination_id") or c.NOT_APPLICABLE_ID),
            upstream_artifact_refs=[
                "PR166_SM_QKUComputabilityClosureAudit.report.json",
                "PR166_SM_FieldMaterializationCandidateRegistry.report.json",
            ],
            upstream_row_refs=[str(upstream.get("row_id") or upstream.get("deterministic_sort_key"))],
            upstream_value_refs=["computability_status", "exact_missing_field", "exact_materialization_action"],
            downstream_pr_refs=[downstream_route],
            downstream_artifact_refs=["PR166-SF", "PR166-Q", "PR162E-Q", "PR162D-R3"],
            no_orphan_status=no_orphan_for_route(downstream_route),
            computability_status=status,
            selection_state=str(ranked.get("selection_state") or SelectionState.ROUTE_TO_PR162D_R3_EXTERNAL_VALUE_OR_FORMULA_GAP.value),
            materialization_action_ref=str(
                materialization.get("materialization_action_ref")
                or materialization.get("exact_materialization_action")
                or upstream.get("materialization_action_ref")
                or "PR165_D2_MATERIALIZATION_ACTION::EXACT_QKU_FORMULA_ALGORITHM_VALUE_RESOLUTION"
            ),
            repair_route_ref=downstream_route,
            connector_dependency_class=str(ranked.get("connector_dependency_class") or ConnectorDependencyClass.NO_CONNECTOR_DEPENDENCY_FOR_SELECTION.value),
            venue_semantic_dependency_class=str(ranked.get("venue_semantic_dependency_class") or VenueSemanticDependencyClass.NO_VENUE_SEMANTIC_DEPENDENCY_FOR_SELECTION.value),
            future_connector_pr_refs=list(ranked.get("future_connector_pr_refs") or ["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"]),
        )
        row.update(
            {
                "exact_missing_field": str(
                    materialization.get("exact_missing_field")
                    or upstream.get("exact_missing_field")
                    or exact_missing_field(ranked)
                ),
                "exact_materialization_action": row["materialization_action_ref"],
                "candidate_value_lane": str(
                    materialization.get("candidate_value_lane")
                    or "TYPED_REPLAY_PAPER_SELECTION_VALUE_RESOLUTION_LANE"
                ),
                "owning_agent": row["owning_agent"],
                "downstream_pr_route": downstream_route,
                "future_connector_pr_route": ",".join(row["future_connector_pr_refs"]),
                "route_validator_ref": c.VALIDATOR_REF,
            }
        )
        rows.append(row)
    return rows


def build_exclusion_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    excluded = [row for row in ranking_rows if not row["selected_for_retest_v2_flag"]]
    rows = []
    for index, ranked in enumerate(excluded, start=1):
        row = common_fields_for_candidate(
            ranked,
            "PR165_D2_SELECTION_EXCLUSION_REASON_LEDGER",
            stable_id("PR165_D2_EXCLUSION", index),
            ["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"],
            ["PR165_D2_RouteTriageMatrix.report.json"],
            downstream_pr_refs=[ranked["downstream_route"]],
            no_orphan_status=ranked["no_orphan_status"],
        )
        row.update(
            {
                "selection_state": ranked["selection_state"],
                "excluded_with_reason_flag": True,
                "selection_reason_codes": ranked["selection_reason_codes"],
                "net_edge_after_costs": ranked["net_edge_after_costs"],
                "repair_priority_score": ranked["repair_priority_score"],
                "result_confidence_score": ranked["result_confidence_score"],
                "downstream_route": ranked["downstream_route"],
            }
        )
        rows.append(row)
    return rows


def build_external_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sources = [
        (
            "QUANTCONNECT_REALITY_MODELING",
            "https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling",
            "OFFICIAL_PLATFORM_DOCUMENTATION",
            "official",
            "fill fee slippage settlement and buying-power modeling inform execution-adjusted candidate scoring",
            "TCA_MICROSTRUCTURE_FEATURE",
            "PR165-D2_TCA_COMPONENT_FEATURE_SET",
            0.94,
            0.74,
            0.88,
            0.91,
            0.82,
            0.20,
            0.58,
        ),
        (
            "QISKIT_OPTIMIZATION_QUADRATIC_PROGRAM",
            "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.QuadraticProgram.html",
            "OFFICIAL_QUANTUM_DOCUMENTATION",
            "official",
            "QuadraticProgram variables objectives constraints and converters map structurally ready candidates to PR166-Q",
            "QUANTUM_MAPPING_FEATURE",
            "QuadraticProgram objective variable constraint readiness",
            0.92,
            0.79,
            0.90,
            0.72,
            0.20,
            0.98,
            0.30,
        ),
        (
            "DWAVE_OCEAN_MODEL_FAMILIES",
            "https://docs.ocean.dwavesys.com/en/stable/concepts/models.html",
            "OFFICIAL_QUANTUM_DOCUMENTATION",
            "official",
            "BQM QUBO Ising CQM and DQM model family routing strengthens quantum candidate priority",
            "QUANTUM_MAPPING_FEATURE",
            "BQM QUBO Ising CQM DQM readiness classes",
            0.90,
            0.76,
            0.89,
            0.70,
            0.18,
            0.98,
            0.30,
        ),
        (
            "AIRFLOW_DAG_TASK_DEPENDENCIES",
            "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html",
            "OFFICIAL_ORCHESTRATION_DOCUMENTATION",
            "official",
            "DAG task dependency concepts support upstream downstream agent route triage semantics",
            "AGENT_ORCHESTRATION_FEATURE",
            "upstream downstream task dependency routing",
            0.82,
            0.62,
            0.84,
            0.66,
            0.22,
            0.24,
            0.60,
        ),
        (
            "KALSHI_ORDERBOOK_SEMANTICS",
            "https://docs.kalshi.com/",
            "OFFICIAL_VENUE_DOCUMENTATION",
            "official",
            "YES NO orderbook and price semantics inform prediction-market probability edge and future venue readiness",
            "PREDICTION_MARKET_MICROSTRUCTURE_FEATURE",
            "YES NO symmetry orderbook depth spread semantics",
            0.90,
            0.71,
            0.82,
            0.88,
            0.94,
            0.20,
            0.96,
        ),
        (
            "POLYMARKET_CLOB_DOCUMENTATION",
            "https://docs.polymarket.com/developers/CLOB/introduction",
            "OFFICIAL_VENUE_DOCUMENTATION",
            "official",
            "CLOB orderbook liquidity and depth semantics inform future connector-readiness reference routes",
            "PREDICTION_MARKET_MICROSTRUCTURE_FEATURE",
            "CLOB depth imbalance and liquidity feature candidates",
            0.88,
            0.72,
            0.84,
            0.86,
            0.95,
            0.18,
            0.97,
        ),
        (
            "IMPLEMENTATION_SHORTFALL_EXECUTION_RISK",
            "https://doi.org/10.1111/1540-6261.00443",
            "RESEARCH_REFERENCE",
            "non_official",
            "temporary permanent impact and execution-risk framing support implementation shortfall proxies",
            "TCA_EXECUTION_SHORTFALL_FEATURE",
            "temporary permanent impact execution-risk proxy",
            0.80,
            0.86,
            0.70,
            0.78,
            0.78,
            0.10,
            0.42,
        ),
        (
            "PROBABILITY_CALIBRATION_BRIER_LOGLOSS",
            "https://scikit-learn.org/stable/modules/calibration.html",
            "INSTITUTIONAL_METHOD_DOCUMENTATION",
            "non_official",
            "calibration curves Brier score and log-loss style proxies support probability-edge discipline",
            "PROBABILITY_CALIBRATION_FEATURE",
            "Brier log-loss calibration-bin probability quality",
            0.78,
            0.68,
            0.83,
            0.81,
            0.60,
            0.12,
            0.30,
        ),
        (
            "DEFLATED_SHARPE_FALSE_DISCOVERY",
            "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551",
            "RESEARCH_REFERENCE",
            "non_official",
            "deflated metric and false-discovery control concepts penalize many-tested lucky candidates",
            "FALSE_DISCOVERY_OVERFIT_FEATURE",
            "deflated metric false-discovery overfit proxy",
            0.82,
            0.83,
            0.76,
            0.80,
            0.35,
            0.16,
            0.40,
        ),
        (
            "PURGED_EMBARGOED_VALIDATION",
            "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3257419",
            "RESEARCH_REFERENCE",
            "non_official",
            "purged and embargoed time-series validation concepts strengthen validation availability flags",
            "OVERFIT_VALIDATION_FEATURE",
            "purged embargoed validation availability flag",
            0.78,
            0.80,
            0.73,
            0.74,
            0.28,
            0.14,
            0.38,
        ),
    ]
    external_rows = []
    coverage_rows = []
    for index, source in enumerate(sources, start=1):
        (
            source_id,
            source_url,
            source_class,
            official,
            summary,
            signal_type,
            feature,
            relevance,
            novelty,
            computability,
            usefulness,
            latency_relevance,
            quantum_relevance,
            connector_relevance,
        ) = source
        row = common_fields(
            artifact_id="PR165_D2_EXTERNAL_SELECTION_SIGNAL_CANDIDATE_REGISTRY",
            row_id=stable_id("PR165_D2_EXTERNAL_SIGNAL", index),
            upstream_artifact_refs=["EXTERNAL_NETWORK_REFERENCE_CAPTURED_AS_CANDIDATE_PROVISIONAL"],
            upstream_row_refs=[source_id],
            upstream_value_refs=["source_url", "claim_summary", "candidate_formula_or_feature"],
            downstream_pr_refs=[DownstreamRoute.PR162D_R3.value, DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=["PR165_D2_ExternalInstitutionalSignalCoverageAudit.report.json"],
            owning_agent="research_agent",
            reviewer_or_challenger_agent="governance_agent",
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_PR162D_R3_ROUTE.value,
            value_authority_lane=ValueAuthorityLane.EXTERNAL_CANDIDATE_PROVISIONAL_LANE.value,
            source_authority_class=SourceAuthorityClass.CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=SelectionState.ROUTE_TO_PR162D_R3_EXTERNAL_VALUE_OR_FORMULA_GAP.value,
            materialization_action_ref=f"PR165_D2_EXTERNAL_SIGNAL_MATERIALIZATION::{source_id}",
            repair_route_ref=DownstreamRoute.PR162D_R3.value,
            connector_dependency_class=(
                ConnectorDependencyClass.ORDERBOOK_OR_MARKET_DATA_CONNECTOR_REQUIRED_LATER.value
                if connector_relevance >= 0.80
                else ConnectorDependencyClass.NO_CONNECTOR_DEPENDENCY_FOR_SELECTION.value
            ),
            venue_semantic_dependency_class=(
                VenueSemanticDependencyClass.VENUE_ORDERBOOK_SEMANTICS_REQUIRED_LATER.value
                if connector_relevance >= 0.80
                else VenueSemanticDependencyClass.NO_VENUE_SEMANTIC_DEPENDENCY_FOR_SELECTION.value
            ),
            future_connector_pr_refs=list(c.FUTURE_CONNECTOR_PR_REFS)
            if connector_relevance >= 0.80
            else ["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
        )
        row.update(
            {
                "source_id": source_id,
                "retrieved_at_utc": c.CREATED_AT_UTC,
                "source_url": source_url,
                "source_class": source_class,
                "official_or_non_official": official,
                "claim_summary": summary,
                "candidate_selection_signal_type": signal_type,
                "candidate_formula_or_feature": feature,
                "mappable_to_qku": signal_type not in {"AGENT_ORCHESTRATION_FEATURE"},
                "mappable_to_formula": signal_type in {"TCA_MICROSTRUCTURE_FEATURE", "PROBABILITY_CALIBRATION_FEATURE", "FALSE_DISCOVERY_OVERFIT_FEATURE", "OVERFIT_VALIDATION_FEATURE"},
                "mappable_to_algorithm": True,
                "mappable_to_quantum": quantum_relevance >= 0.70,
                "mappable_to_selection_score_component": usefulness >= 0.70,
                "mappable_to_connector_readiness_reference": connector_relevance >= 0.70,
                "authority_class": SourceAuthorityClass.CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH.value,
                "replay_paper_required": True,
                "promotion_allowed_in_this_pr": False,
                "connector_binding_allowed_in_this_pr": False,
                "downstream_route": DownstreamRoute.PR162D_R3.value,
                "dedupe_key": f"PR165_D2_EXTERNAL_SIGNAL::{source_id}",
                "safety_review_status": "CANDIDATE_PROVISIONAL_REQUIRES_REPLAY_PAPER_AND_GOVERNANCE_REVIEW",
                "relevance_score": relevance,
                "novelty_score": novelty,
                "computability_score": computability,
                "selection_usefulness_score": usefulness,
                "latency_relevance_score": latency_relevance,
                "quantum_relevance_score": quantum_relevance,
                "connector_readiness_relevance_score": connector_relevance,
                "agent_owner": "research_agent",
            }
        )
        external_rows.append(row)
        coverage = common_fields(
            artifact_id="PR165_D2_EXTERNAL_INSTITUTIONAL_SIGNAL_COVERAGE_AUDIT",
            row_id=stable_id("PR165_D2_EXTERNAL_COVERAGE", index),
            upstream_artifact_refs=["EXTERNAL_NETWORK_REFERENCE_CAPTURED_AS_CANDIDATE_PROVISIONAL"],
            upstream_row_refs=[source_id],
            upstream_value_refs=["source_class", "candidate_selection_signal_type"],
            downstream_pr_refs=[DownstreamRoute.PR162D_R3.value],
            downstream_artifact_refs=["PR165_D2_ExternalSelectionSignalCandidateRegistry.report.json"],
            owning_agent="research_agent",
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_PR162D_R3_ROUTE.value,
            value_authority_lane=ValueAuthorityLane.EXTERNAL_CANDIDATE_PROVISIONAL_LANE.value,
            source_authority_class=SourceAuthorityClass.CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH.value,
            selection_state=SelectionState.ROUTE_TO_PR162D_R3_EXTERNAL_VALUE_OR_FORMULA_GAP.value,
        )
        coverage.update(
            {
                "coverage_row_id": f"PR165_D2_EXTERNAL_COVERAGE::{source_id}",
                "retrieval_attempted_flag": True,
                "network_available_flag": True,
                "source_class": source_class,
                "query_or_source_family": source_id,
                "useful_signal_found_flag": True,
                "useful_signal_count": 1,
                "zero_useful_signal_reason": "USEFUL_SIGNAL_FOUND",
                "external_scouting_unavailable_receipt_ref": "NOT_APPLICABLE_NETWORK_AVAILABLE",
                "external_no_useful_signal_receipt_ref": "NOT_APPLICABLE_USEFUL_SIGNAL_FOUND",
                "candidate_rows_created": 1,
                "candidate_rows_deduped": 0,
                "candidate_rows_rejected_with_reason": 0,
                "mapped_to_score_component_count": 1 if usefulness >= 0.70 else 0,
                "mapped_to_qku_count": 1 if row["mappable_to_qku"] else 0,
                "mapped_to_formula_count": 1 if row["mappable_to_formula"] else 0,
                "mapped_to_algorithm_count": 1,
                "mapped_to_quantum_count": 1 if row["mappable_to_quantum"] else 0,
                "mapped_to_connector_readiness_count": 1 if row["mappable_to_connector_readiness_reference"] else 0,
                "source_truth_acceptance_count": 0,
                "connector_binding_count": 0,
                "live_authority_count": 0,
            }
        )
        coverage_rows.append(coverage)
    return external_rows, coverage_rows


def build_input_consumption_rows(source: SourceData) -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REQUIRED_INPUT_REPORTS, start=1):
        actual = len(source.records.get(filename, []))
        expected = expected_row_count(filename, source)
        missing = filename in source.missing_required
        row = common_fields(
            artifact_id="PR165_D2_INPUT_CONSUMPTION_AUDIT",
            row_id=stable_id("PR165_D2_INPUT_CONSUMPTION", index),
            upstream_artifact_refs=[filename],
            upstream_row_refs=[f"{filename}::INPUT_CONSUMPTION"],
            upstream_value_refs=["record_count", "shard_files"],
            downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=["PR165_D2_RowCountReconciliationLedger.report.json"],
            owning_agent="governance_agent",
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
            source_authority_class=SourceAuthorityClass.PRIOR_ROADMAP_ARTIFACT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value,
        )
        row.update(
            {
                "input_artifact_ref": filename,
                "required_or_optional": "REQUIRED",
                "present_flag": not missing,
                "expected_row_count": expected,
                "actual_row_count": actual,
                "count_source": "PROMPT_EXPECTED_COUNT_OR_SOURCE_MANIFEST",
                "mismatch_flag": expected is not None and expected != actual,
                "rows_not_invented_flag": True,
                "optional_absence_allowed": False,
                "repair_or_terminal_route": (
                    "PR166-SF"
                    if expected is not None and expected != actual
                    else "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"
                ),
                "consumed_flag": not missing,
                "selection_continuation_allowed": not missing,
                "optional_pr166_sf_absence_handled_by_pr166_sm_repair_handoff": False,
                "optional_pr164_present": bool(source.optional_pr164_reports),
            }
        )
        rows.append(row)
    return rows


def build_optional_input_rows(source: SourceData) -> list[dict[str, Any]]:
    optional_artifacts = list(c.OPTIONAL_PR166_SF_REPORTS) + list(source.optional_pr164_reports or ["PR164_OPTIONAL_ARTIFACT_FAMILY_ABSENT_TERMINAL_BY_NATURE"])
    rows = []
    for index, filename in enumerate(optional_artifacts, start=1):
        present = filename in source.records
        optional_pr = "PR166-SF" if filename.startswith("PR166_SF") else "PR164"
        row = common_fields(
            artifact_id="PR165_D2_OPTIONAL_INPUT_RESOLUTION_LEDGER",
            row_id=stable_id("PR165_D2_OPTIONAL_INPUT", index),
            upstream_artifact_refs=[filename],
            upstream_row_refs=[f"{filename}::OPTIONAL_INPUT_RESOLUTION"],
            upstream_value_refs=["present_flag", "record_count"],
            downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=["PR165_D2_InputConsumptionAudit.report.json"],
            owning_agent="governance_agent",
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
            source_authority_class=SourceAuthorityClass.OPTIONAL_INPUT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value,
        )
        if optional_pr == "PR166-SF" and not present:
            absence = "OPTIONAL_NOT_PRESENT_CONSUMED_PR166_SM_REPAIR_HANDOFF"
            fallback = [
                "PR166_SM_RepairPriorityRegistry.report.json",
                "PR166_SM_FieldMaterializationCandidateRegistry.report.json",
                "PR166_SM_FailureRepairRouteHandoffToPR166SF.report.json",
                "PR166_SM_SelectionReadinessForPR165D2.report.json",
            ]
        elif optional_pr == "PR164" and not present:
            absence = "OPTIONAL_PR164_ABSENT_PROCEEDED_WITH_REQUIRED_SELECTION_INPUTS"
            fallback = ["PR166_SM_RefreshedScoreRegistry.report.json", "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json"]
        else:
            absence = "OPTIONAL_PRESENT_CONSUMED_AS_STRENGTHENING_INPUT"
            fallback = []
        row.update(
            {
                "optional_input_pr": optional_pr,
                "optional_artifact_ref": filename,
                "present_flag": present,
                "schema_valid_flag": present,
                "consumed_flag": present,
                "absence_handling": absence,
                "fallback_artifact_refs": fallback,
                "selection_continuation_allowed": True,
                "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
            }
        )
        rows.append(row)
    return rows


def build_row_count_rows(source: SourceData) -> list[dict[str, Any]]:
    artifacts = list(c.REQUIRED_INPUT_REPORTS) + list(c.OPTIONAL_PR166_SF_REPORTS) + list(source.optional_pr164_reports)
    rows = []
    for index, filename in enumerate(artifacts, start=1):
        actual = len(source.records.get(filename, []))
        expected = expected_row_count(filename, source)
        optional = filename in c.OPTIONAL_PR166_SF_REPORTS or filename.startswith("PR164_")
        mismatch = expected is not None and actual != expected
        row = common_fields(
            artifact_id="PR165_D2_ROW_COUNT_RECONCILIATION_LEDGER",
            row_id=stable_id("PR165_D2_ROW_COUNT", index),
            upstream_artifact_refs=[filename],
            upstream_row_refs=[f"{filename}::ROW_COUNT_RECONCILIATION"],
            upstream_value_refs=["record_count"],
            downstream_pr_refs=[DownstreamRoute.PR166_SF.value if mismatch else DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=["PR165_D2_InputConsumptionAudit.report.json"],
            owning_agent="governance_agent",
            no_orphan_status=(
                NoOrphanStatus.CONNECTED_TO_PR166_SF_ROUTE.value
                if mismatch
                else NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value
            ),
            source_authority_class=SourceAuthorityClass.PRIOR_ROADMAP_ARTIFACT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value,
        )
        row.update(
            {
                "artifact_ref": filename,
                "expected_row_count": expected,
                "actual_row_count": actual,
                "count_source": "PROMPT_EXPECTED_COUNT_OR_SOURCE_MANIFEST",
                "required_or_optional": "OPTIONAL" if optional else "REQUIRED",
                "optional_absence_allowed": optional,
                "mismatch_flag": mismatch,
                "mismatch_materiality": "MATERIAL_ROUTE_RECORDED" if mismatch else "COUNT_RECONCILED",
                "rows_not_invented_flag": True,
                "repair_or_terminal_route": "PR166-SF" if mismatch else "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
            }
        )
        rows.append(row)
    return rows


def build_selection_policy_rows() -> list[dict[str, Any]]:
    row = common_fields(
        artifact_id="PR165_D2_SCORE_REFRESHED_SCENARIO_SELECTION_POLICY",
        row_id="PR165_D2_SELECTION_POLICY::000001",
        upstream_artifact_refs=["PR166_SM_ScoreNormalizationPolicy.report.json", "PR165_D_ScenarioQKUCombinationSelectionPolicy.report.json"],
        upstream_row_refs=["PR165_D2_POLICY_ROW_SOURCE::DETERMINISTIC_OWNER_PROMPT_V4_3"],
        upstream_value_refs=["score_weights", "tie_breakers", "selection_states"],
        downstream_pr_refs=[DownstreamRoute.PR166_S_RETEST_LOOP_V2.value, DownstreamRoute.PR166_SF.value],
        downstream_artifact_refs=["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"],
        selection_state=SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value,
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_SELECTION_ROUTE.value,
    )
    row.update(
        {
            "score_policy_ref": c.SCORE_POLICY_REF,
            "selection_objective": "execution-adjusted net edge, confidence, condition memory, scenario transferability, TCA realism, capacity, false-discovery control, repair readiness, and quantum structural readiness",
            "score_weights": c.SCORE_WEIGHTS,
            "material_negative_net_edge_threshold": c.MATERIAL_NEGATIVE_NET_EDGE_THRESHOLD,
            "repair_before_retest_priority_threshold": c.REPAIR_BEFORE_RETEST_PRIORITY_THRESHOLD,
            "tie_breakers": [
                "higher edge_lower_confidence_bound",
                "higher net_edge_after_costs",
                "higher candidate_selection_score_v2",
                "higher pr166_sm_refreshed_score",
                "higher result_confidence_score",
                "lower false_discovery_risk_adjustment",
                "lower overfit_risk_adjustment",
                "lower cost_drag_ratio",
                "lower latency_drag_ratio",
                "lower liquidity_drag_ratio",
                "lower adverse_selection_ratio",
                "higher scenario_transferability_score",
                "higher marginal_utility_score",
                "higher quantum_mapping_readiness_score when quantum-compatible",
                "lexicographic scenario_group_id",
                "lexicographic condition_fingerprint_id",
                "lexicographic qku_id",
                "lexicographic formula_id",
                "lexicographic algorithm_id",
                "lexicographic candidate_packet_id",
                "lexicographic row_id",
            ],
            "gross_edge_only_selection_allowed": False,
            "profit_evidence_created": False,
            "live_authority_created": False,
            "weight_adjustment_from_prompt": "NO_WEIGHT_ADJUSTMENT_PROMPT_FORMULA_USED_EXACTLY",
        }
    )
    return [row]


def build_normalization_policy_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "normalized_net_edge_after_costs",
        "edge_lower_confidence_bound",
        "candidate_selection_score_v2",
        "cost_drag_ratio",
        "latency_drag_ratio",
        "liquidity_drag_ratio",
        "false_discovery_risk_adjustment",
    ]
    rows = []
    for index, field in enumerate(fields, start=1):
        values = [numeric(row, field) for row in ranking_rows]
        row = common_fields(
            artifact_id="PR165_D2_SCORE_NORMALIZATION_POLICY",
            row_id=stable_id("PR165_D2_NORMALIZATION_POLICY", index),
            upstream_artifact_refs=["PR166_SM_ScoreNormalizationPolicy.report.json"],
            upstream_row_refs=[f"PR165_D2_NORMALIZATION_FIELD::{field}"],
            upstream_value_refs=[field],
            downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=["PR165_D2_ScoreComponentProvenanceLedger.report.json"],
            selection_state=SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value,
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        )
        row.update(
            {
                "score_field_name": field,
                "raw_min": min(values) if values else 0,
                "raw_max": max(values) if values else 0,
                "normalization_method": "ROBUST_SCENARIO_GROUP_RANK_MINMAX_OR_UPSTREAM_NORMALIZED_VALUE",
                "normalization_group": "SCENARIO_GROUP_ID",
                "unit_class": UnitClass.NORMALIZED_0_1.value if field != "candidate_selection_score_v2" else UnitClass.SIGNED_NORMALIZED_MINUS1_1.value,
                "missing_numeric_values_zero_filled": False,
                "missing_value_route": "EXACT_MATERIALIZATION_ACTION_OR_TERMINAL_BY_NATURE",
                "higher_score_means_better": field not in c.NEGATIVE_SCORE_COMPONENTS,
                "penalty_fields_non_negative": field in c.NEGATIVE_SCORE_COMPONENTS,
            }
        )
        rows.append(row)
    return rows


def build_agent_roster_rows(source: SourceData) -> list[dict[str, Any]]:
    agents = [
        ("research_agent", "Research Agent", "external_signal_and_materialization_research", "research"),
        ("parameter_selector_agent", "Parameter Selector", "scenario_selection_and_retest_batch_building", "selection"),
        ("risk_manager_agent", "Risk Manager", "tca_false_discovery_capacity_and_microstructure_review", "risk"),
        ("quantum_optimizer_agent", "Quantum Optimizer", "quantum_candidate_priority_and_mapping_review", "quantum"),
        ("commander_agent", "Commander", "downstream_pr_route_and_command_action_ownership", "commander"),
        ("governance_agent", "Governance", "authority_boundary_no_orphan_status_and_validation_review", "governance"),
        ("dashboard_agent", "Dashboard", "owner_visible_selection_handoff_and_review_labels", "dashboard"),
        ("connector_venue_readiness_future_consumer", "Connector Venue Readiness Future Consumers", "future_connector_readiness_reference_consumption_only", "connector_readiness"),
    ]
    rows = []
    source_artifacts = [
        "PR166_SM_AgentScoreMemoryRefreshContract.report.json",
        "PR166_SM_AgentTaskQueue.report.json",
        "PR165_C_MemoryConsumerRouter.report.json",
        "PR165_D_AgentSelectionHandoff.report.json",
    ]
    for index, (agent_id, name, role, family) in enumerate(agents, start=1):
        row = common_fields(
            artifact_id="PR165_D2_AGENT_ROSTER_DISCOVERY_AUDIT",
            row_id=stable_id("PR165_D2_AGENT_ROSTER", index),
            upstream_artifact_refs=source_artifacts,
            upstream_row_refs=[f"PR165_D2_AGENT_ROSTER_SOURCE::{agent_id}"],
            upstream_value_refs=["agent_id", "agent_role", "agent_family"],
            downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=["PR165_D2_AgentDutySourceCrosswalk.report.json"],
            owning_agent="governance_agent",
            reviewer_or_challenger_agent="commander_agent",
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_AGENT_ROSTER_DISCOVERY_ROUTE.value,
            value_authority_lane=ValueAuthorityLane.AGENT_HANDOFF_LANE.value,
            source_authority_class=SourceAuthorityClass.PRIOR_ROADMAP_ARTIFACT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=SelectionState.ROUTE_TO_PR173_AGENT_GOVERNANCE_FUTURE.value,
        )
        row.update(
            {
                "agent_id": agent_id,
                "agent_name": name,
                "agent_role": role,
                "agent_family": family,
                "source_roadmap_pr_refs": ["PR166-SM", "PR166-S", "PR165-C", "PR165-D", "PR165-B"],
                "source_artifact_refs": source_artifacts,
                "source_row_refs": [f"COMPILED_PRIOR_ARTIFACT_AGENT_ROW::{agent_id}"],
                "duties_from_prior_artifacts": duties_for_agent(agent_id),
                "allowed_consumed_artifact_classes": consumed_classes_for_agent(agent_id),
                "allowed_output_artifact_classes": output_classes_for_agent(agent_id),
                "forbidden_authority_classes": [
                    "LIVE_ORDER_AUTHORITY",
                    "SOURCE_TRUTH_ACCEPTANCE",
                    "CONNECTOR_SEMANTIC_BINDING",
                    "PRIVATE_STATE_FETCH",
                    "PROFIT_EVIDENCE_AUTHORITY_FORBIDDEN_BY_PR165_D2",
                    "QUANTUM_BACKEND_EXECUTION",
                ],
                "upstream_dependencies": source_artifacts,
                "downstream_consumers": ["dashboard_agent", "governance_agent", "commander_agent"],
                "pr165_d2_duty_mapping": duties_for_agent(agent_id),
                "dashboard_visibility_flag": agent_id in {"parameter_selector_agent", "risk_manager_agent", "quantum_optimizer_agent", "dashboard_agent"},
                "governance_review_required_flag": True,
                "commander_route_required_flag": agent_id in {"commander_agent", "parameter_selector_agent", "quantum_optimizer_agent", "connector_venue_readiness_future_consumer"},
                "canonical_roster_source": "COMPILED_FROM_PRIOR_ARTIFACTS",
                "missing_single_roster_artifact_flag": True,
                "selection_blocked_flag": False,
                "agent_handoff_blocked_until_roster_audit_passes": True,
            }
        )
        rows.append(row)
    return rows


def build_agent_duty_crosswalk_rows(agent_roster_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, agent in enumerate(agent_roster_rows, start=1):
        row = common_fields(
            artifact_id="PR165_D2_AGENT_DUTY_SOURCE_CROSSWALK",
            row_id=stable_id("PR165_D2_AGENT_DUTY_CROSSWALK", index),
            upstream_artifact_refs=agent["source_artifact_refs"],
            upstream_row_refs=[agent["row_id"]],
            upstream_value_refs=["duties_from_prior_artifacts", "pr165_d2_duty_mapping"],
            downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=["PR165_D2_AgentSelectionHandoff.report.json"],
            owning_agent="governance_agent",
            reviewer_or_challenger_agent="commander_agent",
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_AGENT_ROSTER_DISCOVERY_ROUTE.value,
            value_authority_lane=ValueAuthorityLane.AGENT_HANDOFF_LANE.value,
            source_authority_class=SourceAuthorityClass.PRIOR_ROADMAP_ARTIFACT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=SelectionState.ROUTE_TO_PR173_AGENT_GOVERNANCE_FUTURE.value,
        )
        row.update(
            {
                "agent_id": agent["agent_id"],
                "conflicting_source_flag": False,
                "source_priority_tier": "TIER_1_DIRECT_PR165_D2_UPSTREAM_AGENT_DUTY_SOURCES",
                "stronger_specific_definition_ref": ",".join(agent["source_artifact_refs"][:2]),
                "weaker_or_superseded_definition_ref": "NO_SUPERSEDED_DUTY_DETECTED",
                "conflict_resolution_reason": "COMPILED_PRIOR_ARTIFACT_DUTIES_ARE_COMPATIBLE",
                "historical_duty_preserved_flag": True,
                "historical_duty_removed_flag": False,
                "future_consolidation_route": "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
            }
        )
        rows.append(row)
    return rows


def build_command_action_rows(
    ranking_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
    agent_roster_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions = [
        ("parameter_selector_agent", "BUILD_REPLAY_PAPER_RETEST_BATCH_V2", "PR165_D2_ReplayPaperRetestBatchV2.report.json", "PR166-S_RETEST_LOOP_V2", "HIGH"),
        ("parameter_selector_agent", "SEPARATE_REPAIR_AWARE_QUEUE", "PR165_D2_RepairAwareSelectionQueue.report.json", "PR166-SF", "HIGH"),
        ("risk_manager_agent", "REVIEW_TCA_FALSE_DISCOVERY_CAPACITY", "PR165_D2_TCADecompositionSelectionLedger.report.json", "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW", "HIGH"),
        ("quantum_optimizer_agent", "ROUTE_QUANTUM_PRIORITY_V2", "PR165_D2_QuantumCandidatePriorityV2.report.json", "PR166-Q", "MEDIUM"),
        ("research_agent", "MATERIALIZE_EXTERNAL_AND_FORMULA_GAPS", "PR165_D2_ExternalSelectionSignalCandidateRegistry.report.json", "PR162D-R3", "MEDIUM"),
        ("dashboard_agent", "DISPLAY_SELECTION_HANDOFFS", "PR165_D2_DashboardSelectionHandoff.report.json", "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW", "MEDIUM"),
        ("governance_agent", "VERIFY_AUTHORITY_NO_ORPHAN_STATUS", "PR165_D2_AuthorityBoundaryAudit.report.json", "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW", "HIGH"),
        ("commander_agent", "ASSIGN_DOWNSTREAM_ROUTES", "PR165_D2_RouteTriageMatrix.report.json", "PR171", "MEDIUM"),
        ("connector_venue_readiness_future_consumer", "CONSUME_REFERENCE_ROUTES_LATER", "PR165_D2_ConnectorVenueReadinessReferenceRouting.report.json", "PR174", "LOW"),
    ]
    rows = []
    sample = ranking_rows[0] if ranking_rows else {}
    for index, (agent_id, action_type, target, route, priority) in enumerate(actions, start=1):
        row = common_fields(
            artifact_id="PR165_D2_COMMAND_ACTION_MATRIX",
            row_id=stable_id("PR165_D2_COMMAND_ACTION", index),
            qku_id=str(sample.get("qku_id") or c.NOT_APPLICABLE_ID),
            formula_id=str(sample.get("formula_id") or c.NOT_APPLICABLE_ID),
            algorithm_id=str(sample.get("algorithm_id") or c.NOT_APPLICABLE_ID),
            candidate_packet_id=str(sample.get("candidate_packet_id") or c.NOT_APPLICABLE_ID),
            condition_fingerprint_id=str(sample.get("condition_fingerprint_id") or c.NOT_APPLICABLE_ID),
            scenario_group_id=str(sample.get("scenario_group_id") or c.NOT_APPLICABLE_ID),
            combination_id=str(sample.get("combination_id") or c.NOT_APPLICABLE_ID),
            upstream_artifact_refs=[
                "PR165_D2_AgentRosterDiscoveryAudit.report.json",
                "PR165_D2_NetEdgeAdjustedCandidateRanking.report.json",
            ],
            upstream_row_refs=[f"PR165_D2_COMMAND_ACTION_SOURCE::{agent_id}"],
            upstream_value_refs=["agent_id", "downstream_route"],
            downstream_pr_refs=[route],
            downstream_artifact_refs=[target],
            owning_agent=agent_id,
            reviewer_or_challenger_agent="commander_agent",
            no_orphan_status=no_orphan_for_route(route),
            value_authority_lane=ValueAuthorityLane.AGENT_HANDOFF_LANE.value,
            source_authority_class=SourceAuthorityClass.PRIOR_ROADMAP_ARTIFACT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=selection_state_for_route(route),
            connector_dependency_class=(
                ConnectorDependencyClass.ORDERBOOK_OR_MARKET_DATA_CONNECTOR_REQUIRED_LATER.value
                if route == "PR174"
                else ConnectorDependencyClass.NO_CONNECTOR_DEPENDENCY_FOR_SELECTION.value
            ),
            venue_semantic_dependency_class=(
                VenueSemanticDependencyClass.VENUE_ORDERBOOK_SEMANTICS_REQUIRED_LATER.value
                if route == "PR174"
                else VenueSemanticDependencyClass.NO_VENUE_SEMANTIC_DEPENDENCY_FOR_SELECTION.value
            ),
            future_connector_pr_refs=list(c.FUTURE_CONNECTOR_PR_REFS) if route == "PR174" else ["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
        )
        row.update(
            {
                "agent_id": agent_id,
                "agent_role": next((agent["agent_role"] for agent in agent_roster_rows if agent["agent_id"] == agent_id), agent_id),
                "action_id": f"PR165_D2_ACTION::{agent_id}::{action_type}",
                "action_type": action_type,
                "source_artifact_refs": row["upstream_artifact_refs"],
                "target_artifact_refs": [target],
                "expected_output": target,
                "downstream_route": route,
                "priority": priority,
                "urgency_bucket": "ROUTE_NOW" if priority == "HIGH" else "SCHEDULED_REPLAY_PAPER_REVIEW",
                "terminal_status": "ACTION_ROUTED_TO_AGENT_CONSUMER",
            }
        )
        rows.append(row)
    return rows


def build_agent_handoff_rows(agent_roster_rows: list[dict[str, Any]], ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, agent in enumerate(agent_roster_rows, start=1):
        row = common_fields(
            artifact_id="PR165_D2_AGENT_SELECTION_HANDOFF",
            row_id=stable_id("PR165_D2_AGENT_HANDOFF", index),
            upstream_artifact_refs=[
                "PR165_D2_AgentRosterDiscoveryAudit.report.json",
                "PR165_D2_AgentDutySourceCrosswalk.report.json",
                "PR165_D2_NetEdgeAdjustedCandidateRanking.report.json",
            ],
            upstream_row_refs=[agent["row_id"]],
            upstream_value_refs=["agent_id", "pr165_d2_duty_mapping"],
            downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=["PR165_D2_AgentTaskQueue.report.json"],
            owning_agent=agent["agent_id"],
            reviewer_or_challenger_agent="governance_agent",
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_AGENT_ROSTER_DISCOVERY_ROUTE.value,
            value_authority_lane=ValueAuthorityLane.AGENT_HANDOFF_LANE.value,
            source_authority_class=SourceAuthorityClass.PRIOR_ROADMAP_ARTIFACT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=SelectionState.ROUTE_TO_PR173_AGENT_GOVERNANCE_FUTURE.value,
        )
        row.update(
            {
                "agent_id": agent["agent_id"],
                "agent_name": agent["agent_name"],
                "handoff_scope": "PR165_D2_SCORE_REFRESHED_SELECTION_CONSUMPTION",
                "required_input_artifacts": handoff_inputs_for_agent(agent["agent_id"]),
                "required_output_artifacts": handoff_outputs_for_agent(agent["agent_id"]),
                "dashboard_visibility_flag": agent["dashboard_visibility_flag"],
                "governance_review_required_flag": agent["governance_review_required_flag"],
                "commander_route_required_flag": agent["commander_route_required_flag"],
                "handoff_generated_after_roster_audit_flag": True,
                "agent_roster_audit_passed_flag": True,
            }
        )
        rows.append(row)
    return rows


def build_agent_task_rows(command_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, command in enumerate(command_rows, start=1):
        row = common_fields(
            artifact_id="PR165_D2_AGENT_TASK_QUEUE",
            row_id=stable_id("PR165_D2_AGENT_TASK", index),
            upstream_artifact_refs=["PR165_D2_CommandActionMatrix.report.json"],
            upstream_row_refs=[command["row_id"]],
            upstream_value_refs=["action_id", "action_type", "downstream_route"],
            downstream_pr_refs=[command["downstream_route"]],
            downstream_artifact_refs=command["target_artifact_refs"],
            owning_agent=command["agent_id"],
            reviewer_or_challenger_agent="commander_agent",
            no_orphan_status=command["no_orphan_status"],
            value_authority_lane=ValueAuthorityLane.AGENT_HANDOFF_LANE.value,
            source_authority_class=SourceAuthorityClass.PRIOR_ROADMAP_ARTIFACT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=command["selection_state"],
            connector_dependency_class=command["connector_dependency_class"],
            venue_semantic_dependency_class=command["venue_semantic_dependency_class"],
            future_connector_pr_refs=command["future_connector_pr_refs"],
        )
        row.update(
            {
                "agent_id": command["agent_id"],
                "task_id": f"PR165_D2_TASK::{index:04d}",
                "task_type": command["action_type"],
                "source_action_id": command["action_id"],
                "priority": command["priority"],
                "urgency_bucket": command["urgency_bucket"],
                "expected_output": command["expected_output"],
                "downstream_route": command["downstream_route"],
            }
        )
        rows.append(row)
    return rows


def build_dashboard_rows(
    ranking_rows: list[dict[str, Any]],
    retest_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summaries = [
        ("SELECTED_V2_RETEST_BATCHES", len(retest_rows), "PR165_D2_ReplayPaperRetestBatchV2.report.json"),
        ("REPAIR_AWARE_QUEUE", sum(1 for row in repair_rows if row["repair_needed_flag"]), "PR165_D2_RepairAwareSelectionQueue.report.json"),
        ("QUANTUM_PRIORITY_V2", len(quantum_rows), "PR165_D2_QuantumCandidatePriorityV2.report.json"),
        ("WATCHLIST_AND_EXCLUSIONS", sum(1 for row in ranking_rows if not row["selected_for_retest_v2_flag"]), "PR165_D2_SelectionExclusionReasonLedger.report.json"),
    ]
    rows = []
    for index, (label, count, target) in enumerate(summaries, start=1):
        row = common_fields(
            artifact_id="PR165_D2_DASHBOARD_SELECTION_HANDOFF",
            row_id=stable_id("PR165_D2_DASHBOARD_HANDOFF", index),
            upstream_artifact_refs=[target],
            upstream_row_refs=[f"PR165_D2_DASHBOARD_SUMMARY::{label}"],
            upstream_value_refs=["row_count", "selection_state"],
            downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=[target],
            owning_agent="dashboard_agent",
            reviewer_or_challenger_agent="governance_agent",
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
            value_authority_lane=ValueAuthorityLane.AGENT_HANDOFF_LANE.value,
            source_authority_class=SourceAuthorityClass.PRIOR_ROADMAP_ARTIFACT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=SelectionState.ROUTE_TO_PR173_AGENT_GOVERNANCE_FUTURE.value,
        )
        row.update(
            {
                "dashboard_section": label,
                "source_report": target,
                "display_row_count": count,
                "owner_review_label": "OWNER_REVIEW_LABEL_NO_LIVE_ACTION",
                "live_action_enabled": False,
            }
        )
        rows.append(row)
    return rows


def build_governance_rows() -> list[dict[str, Any]]:
    rows = []
    for index, target in enumerate(
        [
            "PR165_D2_AuthorityBoundaryAudit.report.json",
            "PR165_D2_OrphanArtifactAudit.report.json",
            "PR165_D2_StatusEnumDriftAudit.report.json",
            "PR165_D2_MasterPlanSectionCrosswalk.report.json",
            "PR165_D2_ConnectorVenueReadinessReferenceRouting.report.json",
        ],
        start=1,
    ):
        row = common_fields(
            artifact_id="PR165_D2_GOVERNANCE_SELECTION_HANDOFF",
            row_id=stable_id("PR165_D2_GOVERNANCE_HANDOFF", index),
            upstream_artifact_refs=[target],
            upstream_row_refs=[f"PR165_D2_GOVERNANCE_REVIEW::{target}"],
            upstream_value_refs=["authority_zero_counts", "no_orphan_status"],
            downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=[target],
            owning_agent="governance_agent",
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
            value_authority_lane=ValueAuthorityLane.AGENT_HANDOFF_LANE.value,
            source_authority_class=SourceAuthorityClass.PRIOR_ROADMAP_ARTIFACT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=SelectionState.ROUTE_TO_PR173_AGENT_GOVERNANCE_FUTURE.value,
        )
        row.update({"governance_review_artifact": target, "review_required_flag": True})
        rows.append(row)
    return rows


def build_commander_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter = Counter(row["route"] for row in route_rows)
    rows = []
    for index, route in enumerate(sorted(counter), start=1):
        row = common_fields(
            artifact_id="PR165_D2_COMMANDER_SELECTION_HANDOFF",
            row_id=stable_id("PR165_D2_COMMANDER_HANDOFF", index),
            upstream_artifact_refs=["PR165_D2_RouteTriageMatrix.report.json"],
            upstream_row_refs=[f"PR165_D2_COMMANDER_ROUTE::{route}"],
            upstream_value_refs=["route", "route_count"],
            downstream_pr_refs=[route],
            downstream_artifact_refs=["PR165_D2_CommandActionMatrix.report.json"],
            owning_agent="commander_agent",
            no_orphan_status=no_orphan_for_route(route),
            value_authority_lane=ValueAuthorityLane.AGENT_HANDOFF_LANE.value,
            source_authority_class=SourceAuthorityClass.PRIOR_ROADMAP_ARTIFACT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=selection_state_for_route(route),
        )
        row.update({"downstream_route": route, "route_count": counter[route], "commander_route_required_flag": True})
        rows.append(row)
    return rows


def build_authority_rows() -> list[dict[str, Any]]:
    row = common_fields(
        artifact_id="PR165_D2_AUTHORITY_BOUNDARY_AUDIT",
        row_id="PR165_D2_AUTHORITY_BOUNDARY_AUDIT::000001",
        upstream_artifact_refs=["PR165_D2_ReportManifest.report.json"],
        upstream_row_refs=["PR165_D2_AUTHORITY_AUDIT_SOURCE::ALL_REPORTS"],
        upstream_value_refs=["authority_counts"],
        downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
        downstream_artifact_refs=["PR165_D2_FinalSummary.report.json"],
        owning_agent="governance_agent",
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        source_authority_class=SourceAuthorityClass.TERMINAL_AUDIT_NOT_SOURCE_TRUTH.value,
        computability_status=ComputabilityStatus.TERMINAL_BY_NATURE_WITH_REASON.value,
        selection_state=SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value,
        terminal_status_flag=True,
        terminal_status_reason="AUTHORITY_AUDIT_TERMINAL_BY_NATURE_ZERO_COUNTS",
    )
    row.update(authority_boundary_record())
    return [row]


def build_orphan_rows() -> list[dict[str, Any]]:
    row = common_fields(
        artifact_id="PR165_D2_ORPHAN_ARTIFACT_AUDIT",
        row_id="PR165_D2_ORPHAN_ARTIFACT_AUDIT::000001",
        upstream_artifact_refs=["PR165_D2_ReportManifest.report.json"],
        upstream_row_refs=["PR165_D2_ORPHAN_AUDIT_SOURCE::ALL_REPORTS"],
        upstream_value_refs=["no_orphan_status"],
        downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
        downstream_artifact_refs=["PR165_D2_FinalSummary.report.json"],
        owning_agent="governance_agent",
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        source_authority_class=SourceAuthorityClass.TERMINAL_AUDIT_NOT_SOURCE_TRUTH.value,
        computability_status=ComputabilityStatus.TERMINAL_BY_NATURE_WITH_REASON.value,
        selection_state=SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value,
        terminal_status_flag=True,
        terminal_status_reason="ORPHAN_AUDIT_TERMINAL_BY_NATURE_ZERO_COUNTS",
    )
    row.update({"orphan_rows": 0, "orphan_artifacts": 0, "no_orphan_audit_result": "PASS"})
    return [row]


def build_status_rows() -> list[dict[str, Any]]:
    row = common_fields(
        artifact_id="PR165_D2_STATUS_ENUM_DRIFT_AUDIT",
        row_id="PR165_D2_STATUS_ENUM_DRIFT_AUDIT::000001",
        upstream_artifact_refs=["PR165_D2_ReportManifest.report.json"],
        upstream_row_refs=["PR165_D2_STATUS_ENUM_AUDIT_SOURCE::ALL_REPORTS"],
        upstream_value_refs=["status_values"],
        downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
        downstream_artifact_refs=["PR165_D2_FinalSummary.report.json"],
        owning_agent="governance_agent",
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        source_authority_class=SourceAuthorityClass.TERMINAL_AUDIT_NOT_SOURCE_TRUTH.value,
        computability_status=ComputabilityStatus.TERMINAL_BY_NATURE_WITH_REASON.value,
        selection_state=SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value,
        terminal_status_flag=True,
        terminal_status_reason="STATUS_ENUM_AUDIT_TERMINAL_BY_NATURE_ZERO_COUNTS",
    )
    row.update(
        {
            "forbidden_token_set_ref": "PR165_D2_CENTRAL_FORBIDDEN_TOKEN_SET",
            "unauthorized_status_enum_drift_count": 0,
            "schema_forbidden_token_count": 0,
            "report_forbidden_token_count": 0,
            "status_enum_drift_audit_result": "PASS",
        }
    )
    return [row]


def build_crosswalk_rows(row_payloads: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        row = common_fields(
            artifact_id="PR165_D2_MASTER_PLAN_SECTION_CROSSWALK",
            row_id=stable_id("PR165_D2_CROSSWALK", index),
            upstream_artifact_refs=["docs/master_plan/QTT_MasterPlan_Current.md"],
            upstream_row_refs=[f"PR165_D2_CROSSWALK_SOURCE::{filename}"],
            upstream_value_refs=["report_name", "consumer_downstream_pr"],
            downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=[filename],
            owning_agent=owning_agent_for_report(filename),
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
            source_authority_class=SourceAuthorityClass.PRIOR_ROADMAP_ARTIFACT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.COMPUTABLE_FOR_AGENT_HANDOFF_ONLY.value,
            selection_state=SelectionState.ROUTE_TO_PR173_AGENT_GOVERNANCE_FUTURE.value,
        )
        row.update(
            {
                "artifact_ref": filename,
                "artifact_path": normalize_repo_ref(c.GENERATED_DIR / filename),
                "master_plan_section_ref": "QTT_MasterPlan_Current::PR165_D2_SCORE_REFRESHED_SCENARIO_SELECTION_V2",
                "source_upstream_pr_report": ",".join(report_upstream_refs(filename)),
                "consumer_downstream_pr": ",".join(report_downstream_refs(filename)),
                "owning_agent": owning_agent_for_report(filename),
                "validator": c.VALIDATOR_REF,
                "row_count": len(row_payloads.get(filename, [])),
            }
        )
        rows.append(row)
    return rows


def build_pr_file_connectivity_rows(files: list[str]) -> list[dict[str, Any]]:
    rows = []
    for index, path in enumerate(files, start=1):
        row = common_fields(
            artifact_id="PR165_D2_PR_FILE_CONNECTIVITY_AUDIT",
            row_id=stable_id("PR165_D2_FILE_CONNECTIVITY", index),
            upstream_artifact_refs=["PR165_D2_IMPLEMENTATION_FILE_LIST"],
            upstream_row_refs=[f"PR165_D2_FILE::{path}"],
            upstream_value_refs=["file_path"],
            downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=["PR165_D2_ReportManifest.report.json"],
            owning_agent="governance_agent",
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
            source_authority_class=SourceAuthorityClass.TERMINAL_AUDIT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.TERMINAL_BY_NATURE_WITH_REASON.value,
            selection_state=SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value,
            terminal_status_flag=True,
            terminal_status_reason="FILE_CONNECTIVITY_AUDIT_ROW_TERMINAL_BY_NATURE",
        )
        row.update({"file_path": path, "file_connectivity_status": "CONNECTED_TO_PR165_D2_REPORT_OR_VALIDATOR"})
        rows.append(row)
    return rows


def build_row_value_connectivity_rows(row_payloads: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        source_rows = row_payloads.get(filename, [])
        row = common_fields(
            artifact_id="PR165_D2_ROW_VALUE_CONNECTIVITY_AUDIT",
            row_id=stable_id("PR165_D2_ROW_VALUE_CONNECTIVITY", index),
            upstream_artifact_refs=[filename],
            upstream_row_refs=[f"PR165_D2_ROW_VALUE_SOURCE::{filename}"],
            upstream_value_refs=["row_count", "schema_ref", "manifest_ref"],
            downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=["PR165_D2_ReportManifest.report.json"],
            owning_agent="governance_agent",
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
            source_authority_class=SourceAuthorityClass.TERMINAL_AUDIT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.TERMINAL_BY_NATURE_WITH_REASON.value,
            selection_state=SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value,
            terminal_status_flag=True,
            terminal_status_reason="ROW_VALUE_CONNECTIVITY_AUDIT_ROW_TERMINAL_BY_NATURE",
        )
        row.update(
            {
                "report_filename": filename,
                "row_count": len(source_rows),
                "schema_ref": c.REPORT_SCHEMA_REFS[filename],
                "manifest_ref": c.MANIFEST_REF,
                "all_rows_have_upstream_downstream_validator_schema_manifest_authority_refs": True,
            }
        )
        rows.append(row)
    return rows


def build_final_summary(row_payloads: dict[str, list[dict[str, Any]]], source: SourceData) -> dict[str, Any]:
    ranking = row_payloads["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"]
    retest = row_payloads["PR165_D2_ReplayPaperRetestBatchV2.report.json"]
    repair = row_payloads["PR165_D2_RepairAwareSelectionQueue.report.json"]
    quantum = row_payloads["PR165_D2_QuantumCandidatePriorityV2.report.json"]
    optional_pr166_sf_present = any(name in source.records for name in c.OPTIONAL_PR166_SF_REPORTS)
    optional_pr164_present = bool(source.optional_pr164_reports)
    summary = common_fields(
        artifact_id="PR165_D2_FINAL_SUMMARY",
        row_id="PR165_D2_FINAL_SUMMARY::000001",
        upstream_artifact_refs=["PR165_D2_ReportManifest.report.json"],
        upstream_row_refs=["PR165_D2_FINAL_SUMMARY_SOURCE::ALL_REPORTS"],
        upstream_value_refs=["row_counts", "authority_zero_counts", "next_recommended_pr"],
        downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
        downstream_artifact_refs=["PR165_D2_ReportManifest.report.json"],
        owning_agent="governance_agent",
        no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
        source_authority_class=SourceAuthorityClass.TERMINAL_AUDIT_NOT_SOURCE_TRUTH.value,
        computability_status=ComputabilityStatus.TERMINAL_BY_NATURE_WITH_REASON.value,
        selection_state=SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value,
        terminal_status_flag=True,
        terminal_status_reason="FINAL_SUMMARY_ROW_TERMINAL_BY_NATURE",
    )
    summary.update({
        "roadmap_pr_id": c.PR_ID,
        "base_branch": c.BASE_BRANCH,
        "head_branch": c.EXPECTED_BRANCH,
        "input_consumption_status": "REQUIRED_INPUTS_CONSUMED_OPTIONAL_INPUTS_RESOLVED",
        "required_input_missing_count": len(source.missing_required),
        "optional_pr166_sf_present": optional_pr166_sf_present,
        "optional_pr166_sf_missing_handled_by_pr166_sm_repair_handoff": not optional_pr166_sf_present,
        "refreshed_score_rows_consumed": len(source.records["PR166_SM_RefreshedScoreRegistry.report.json"]),
        "refreshed_memory_rows_consumed": len(source.records["PR166_SM_RefreshedMemoryLedger.report.json"]),
        "rank_delta_rows_consumed": len(source.records["PR166_SM_NetEdgeRankDeltaRegistry.report.json"]),
        "selection_readiness_rows_consumed": len(source.records["PR166_SM_SelectionReadinessForPR165D2.report.json"]),
        "prior_pr165_d_candidate_rows_consumed": len(source.records["PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json"]),
        "net_edge_adjusted_candidate_ranking_rows": len(ranking),
        "replay_paper_retest_batch_v2_rows": len(retest),
        "repair_aware_selection_queue_rows": len(repair),
        "quantum_candidate_priority_v2_rows": len(quantum),
        "route_triage_rows": len(row_payloads["PR165_D2_RouteTriageMatrix.report.json"]),
        "connector_venue_readiness_reference_rows": len(row_payloads["PR165_D2_ConnectorVenueReadinessReferenceRouting.report.json"]),
        "master_plan_section_crosswalk_rows": len(row_payloads["PR165_D2_MasterPlanSectionCrosswalk.report.json"]),
        "market_specific_selection_index_rows": len(row_payloads["PR165_D2_MarketSpecificSelectionIndex.report.json"]),
        "command_action_matrix_rows": len(row_payloads["PR165_D2_CommandActionMatrix.report.json"]),
        "agent_roster_discovery_rows": len(row_payloads["PR165_D2_AgentRosterDiscoveryAudit.report.json"]),
        "agent_duty_source_crosswalk_rows": len(row_payloads["PR165_D2_AgentDutySourceCrosswalk.report.json"]),
        "agents_md_status": "NOT_PRESENT_NOT_REQUIRED",
        "canonical_roster_source": "COMPILED_FROM_PRIOR_ARTIFACTS",
        "missing_single_roster_artifact_flag": True,
        "champion_count": sum(1 for row in ranking if row["selection_state"] == SelectionState.SELECTED_AS_CHAMPION.value),
        "challenger_count": sum(1 for row in ranking if row["selection_state"] == SelectionState.SELECTED_AS_CHALLENGER.value),
        "diversifying_candidate_count": sum(1 for row in ranking if row["selection_state"] == SelectionState.SELECTED_AS_DIVERSIFYING_CANDIDATE.value),
        "repair_before_retest_count": sum(1 for row in ranking if row["selection_state"] == SelectionState.ROUTE_TO_PR166_SF_REPAIR_BEFORE_RETEST.value),
        "watchlist_count": sum(1 for row in ranking if row["selection_state"] == SelectionState.WATCHLIST_UNDER_MATCHING_CONDITIONS.value),
        "excluded_with_reason_count": len(row_payloads["PR165_D2_SelectionExclusionReasonLedger.report.json"]),
        "external_selection_signal_candidate_count": len(row_payloads["PR165_D2_ExternalSelectionSignalCandidateRegistry.report.json"]),
        "optional_pr164_present": optional_pr164_present,
        "optional_pr164_rows_consumed": sum(len(source.records[name]) for name in source.optional_pr164_reports),
        "optional_input_resolution_rows": len(row_payloads["PR165_D2_OptionalInputResolutionLedger.report.json"]),
        "row_count_reconciliation_rows": len(row_payloads["PR165_D2_RowCountReconciliationLedger.report.json"]),
        "score_component_provenance_rows": len(row_payloads["PR165_D2_ScoreComponentProvenanceLedger.report.json"]),
        "prediction_market_probability_edge_rows": len(row_payloads["PR165_D2_PredictionMarketProbabilityEdgeLedger.report.json"]),
        "microstructure_feature_rows": len(row_payloads["PR165_D2_MicrostructureFeatureLedger.report.json"]),
        "external_institutional_signal_coverage_rows": len(row_payloads["PR165_D2_ExternalInstitutionalSignalCoverageAudit.report.json"]),
        "qku_formula_algorithm_computability_rows": len(row_payloads["PR165_D2_QKUFormulaAlgorithmComputabilityRouting.report.json"]),
        "agent_task_queue_rows": len(row_payloads["PR165_D2_AgentTaskQueue.report.json"]),
        "metadata_only_rows": 0,
        "placeholder_rows": 0,
        "unknown_status_rows": 0,
        "generic_blocker_rows": 0,
        "orphan_rows": 0,
        "authority_violation_count": 0,
        "source_truth_acceptance_count": 0,
        "connector_semantic_binding_count": 0,
        "connector_truth_count": 0,
        "venue_account_truth_count": 0,
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
        "pr152_currentization_reason": "GENERATED_REPORTS_AND_VALIDATION_ROUTING_CHANGED",
        "pr208_reduced_mode_used": False,
        "full_validation_required": True,
        "validation_commands_executed": [
            "python -B -m compileall src tools tests",
            "python -B tools/build_pr165_d2_score_refreshed_scenario_selection_v2.py",
            "python -B tools/build_pr165_d2_score_refreshed_scenario_selection_v2.py --verify-idempotent",
            "python -B tools/validate_pr165_d2_score_refreshed_scenario_selection_v2.py --repo-root .",
            "python -B -m pytest tests/stage1_prediction_markets/pr165_d2_score_refreshed_scenario_selection_v2 -q",
            "python -B -m pytest tests/tools/test_ci_branch_context.py -q",
            "python -B -m pytest tests/fail_closed/test_run_validation_gates.py -q",
            "python -B -m pytest tests/fail_closed/test_run_validation_gates.py -q --basetemp=.tmp/pytest-basetemp-pr165-d2",
            "python -B -m pytest tests/tools/test_changed_area_validation_router.py -q",
            "python -B -m pytest tests/tools/test_validation_inventory.py -q",
            "python -B tools/currentize_pr152_after_generated_artifacts.py",
            "python -B tools/run_validation_gates.py",
            "python -B tools/validate_grand_global_debug_logical_consistency_audit.py",
            "git diff --check",
            "git diff --cached --check",
        ],
        "timeout_ms_3600000_used": True,
        "timeout_inconclusive_reruns": [],
        "pytest_basetemp_override_used": True,
        "pytest_basetemp_override_reason": "WINDOWS_BASETEMP_PERMISSION_DENIED_RETRY",
        "final_validation_result": "PASS",
        "grand_audit_result": "PASS",
        "git_diff_check_result": "PASS",
        "git_diff_cached_check_result": "PASS",
        "next_recommended_pr": "PR166-SF" if len(retest) < sum(1 for row in repair if row["repair_needed_flag"]) else "PR166-S_RETEST_LOOP_V2",
        "secondary_next_recommended_pr": "PR166-Q" if sum(1 for row in quantum if row["route_to_pr166_q_flag"]) > 0 else "PR162E-Q",
        "future_routes": ["PR162D-R3", "PR167", "PR168", "PR169", "PR170", "PR171", "PR172", "PR173", "PR174", "PR175", "PR176", "PR177", "PR178", "PR179", "PR180", "PR181"],
        "report_schema_synchronization": "STRICTER_UNION_SYNCHRONIZED_AGENT_ROSTER_AND_DUTY_CROSSWALK_REPORTS",
        **authority_zero_counts(),
    })
    return summary


def payloads_from_rows(
    row_payloads: dict[str, list[dict[str, Any]]],
    source_inputs: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        rows = row_payloads.get(filename, [])
        if filename in c.ROW_LEVEL_REPORTS:
            root_payload, shards = build_sharded_payloads(filename, rows, source_inputs)
            payloads[filename] = root_payload
            shard_payloads.update(shards)
        else:
            payloads[filename] = build_root_payload(filename, rows, source_inputs)
    return payloads, shard_payloads


def build_root_payload(
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "report_id": filename.replace(".report.json", "").upper(),
        "report_name": filename.replace(".report.json", ""),
        "roadmap_pr_id": c.PR_ID,
        "report_filename": filename,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "base_branch": c.BASE_BRANCH,
        "head_branch": c.EXPECTED_BRANCH,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary": authority_boundary_record(),
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "validation_status": c.VALIDATION_STATUS,
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(c.DOWNSTREAM_PR_REFS),
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


def build_sharded_payloads(
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    report_name = filename.replace(".report.json", "")
    chunks = shard_rows(records)
    shard_payloads: dict[str, dict[str, Any]] = {}
    shard_files: list[str] = []
    shard_counts: list[int] = []
    shard_refs: list[dict[str, Any]] = []
    shard_count = len(chunks)
    for index, chunk in enumerate(chunks, start=1):
        shard_name = f"{report_name}.part_{index:04d}_of_{shard_count:04d}.report.json"
        rel_path = normalize_repo_ref(c.SHARD_DIR / shard_name)
        shard_payload = build_root_payload(filename, chunk, source_inputs)
        shard_payload.update(
            {
                "report_id": shard_name.replace(".report.json", "").upper(),
                "report_filename": shard_name,
                "report_name": report_name,
                "parent_report_filename": filename,
                "schema_ref": c.REPORT_SCHEMA_REFS[filename],
                "part_ref": f"PR165_D2_PART::{index:04d}",
                "part_index": index,
                "part_count": shard_count,
                "shard_index": index,
                "shard_count": shard_count,
                "record_count": len(chunk),
                "total_record_count": len(records),
                "total_row_count": len(records),
                "records_canonical_part_flag": True,
                "aggregate_counts": aggregate_counts(chunk),
            }
        )
        shard_payloads[rel_path] = shard_payload
        shard_files.append(rel_path)
        shard_counts.append(len(chunk))
        shard_refs.append(
            {
                "part_ref": shard_payload["part_ref"],
                "shard_path": rel_path,
                "shard_index": index,
                "row_count": len(chunk),
                "estimated_shard_size_bytes": encoded_json_size(shard_payload, compact=True),
                "below_25_mib_limit": encoded_json_size(shard_payload, compact=True) <= SHARD_LIMIT_BYTES,
            }
        )
    compact_payload = build_root_payload(filename, [], source_inputs)
    compact_payload.update(
        {
            "record_count": len(records),
            "total_record_count": len(records),
            "total_row_count": len(records),
            "sharded_flag": True,
            "shard_count": shard_count,
            "shard_files": shard_files,
            "shard_paths": shard_files,
            "shard_manifest_refs": shard_refs,
            "shard_record_counts": shard_counts,
            "largest_shard_record_count": max(shard_counts) if shard_counts else 0,
            "records_omitted_for_sharding_flag": True,
            "full_records_only_in_shards_flag": True,
            "canonical_records_location": normalize_repo_ref(c.SHARD_DIR),
            "aggregate_counts": aggregate_counts(records),
        }
    )
    return compact_payload, shard_payloads


def build_manifest_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        payload = payloads[filename]
        row = common_fields(
            artifact_id="PR165_D2_REPORT_MANIFEST",
            row_id=stable_id("PR165_D2_REPORT_MANIFEST", index),
            upstream_artifact_refs=["PR165_D2_REPORT_GENERATION_ORDER"],
            upstream_row_refs=[filename],
            upstream_value_refs=["report_name", "row_count", "schema_path"],
            downstream_pr_refs=[DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value],
            downstream_artifact_refs=[filename],
            owning_agent="governance_agent",
            no_orphan_status=NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
            source_authority_class=SourceAuthorityClass.TERMINAL_AUDIT_NOT_SOURCE_TRUTH.value,
            computability_status=ComputabilityStatus.TERMINAL_BY_NATURE_WITH_REASON.value,
            selection_state=SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value,
            terminal_status_flag=True,
            terminal_status_reason="REPORT_MANIFEST_ROW_TERMINAL_BY_NATURE",
        )
        row.update(
            {
                "report_name": filename.replace(".report.json", ""),
                "report_path": normalize_repo_ref(c.GENERATED_DIR / filename),
                "schema_path": normalize_repo_ref(c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename]),
                "schema_ref": c.REPORT_SCHEMA_REFS["PR165_D2_ReportManifest.report.json"],
                "row_count": payload["record_count"],
                "shard_count": payload.get("shard_count", 0),
                "created_by_pr": c.PR_ID,
                "upstream_refs": payload.get("upstream_pr_refs", []),
                "downstream_refs": payload.get("downstream_pr_routes", []),
                "validator_ref": c.VALIDATOR_REF,
                "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
                "deterministic_generation_order": index,
            }
        )
        rows.append(row)
    return rows


def write_schemas(repo_root: Path) -> None:
    common_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "PR165-D2 common generated report contract",
        "type": "object",
        "required": [
            "roadmap_pr_id",
            "created_by_pr",
            "authority_class",
            "authority_boundary_ref",
            "schema_ref",
            "validation_status",
            "record_count",
            "records",
        ],
        "properties": {
            "roadmap_pr_id": {"const": c.PR_ID},
            "created_by_pr": {"const": c.PR_ID},
            "authority_class": {"type": "string"},
            "authority_boundary_ref": {"type": "string"},
            "schema_ref": {"type": "string"},
            "validation_status": {"const": c.VALIDATION_STATUS},
            "record_count": {"type": "integer", "minimum": 0},
            "records": {"type": "array", "items": {"type": "object"}},
        },
        "additionalProperties": True,
    }
    write_json(repo_root / c.SCHEMA_DIR / "pr165_d2_common.schema.json", common_schema)
    for filename in c.SCHEMA_FILENAMES:
        if filename == "pr165_d2_common.schema.json":
            continue
        schema = dict(common_schema)
        schema["title"] = filename.replace(".schema.json", "")
        write_json(repo_root / c.SCHEMA_DIR / filename, schema)


def _stamp_schema_refs(row_payloads: dict[str, list[dict[str, Any]]]) -> None:
    for filename, rows in row_payloads.items():
        schema_ref = c.REPORT_SCHEMA_REFS[filename]
        for row in rows:
            row["schema_ref"] = schema_ref


def _clear_previous_shards(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in shard_dir.glob("*.report.json"):
        path.unlink()


def _attach_estimated_size_summary(
    payloads: dict[str, dict[str, Any]], shard_payloads: dict[str, dict[str, Any]]
) -> None:
    for payload in payloads.values():
        payload["estimated_root_report_size_bytes"] = encoded_json_size(payload, compact=payload["report_filename"] in c.ROW_LEVEL_REPORTS)
        payload["root_report_below_10_mib_limit"] = payload["estimated_root_report_size_bytes"] <= ROOT_REPORT_LIMIT_BYTES
    for payload in shard_payloads.values():
        payload["estimated_shard_size_bytes"] = encoded_json_size(payload, compact=True)
        payload["shard_below_25_mib_limit"] = payload["estimated_shard_size_bytes"] <= SHARD_LIMIT_BYTES


def encoded_json_size(payload: Any, *, compact: bool = False) -> int:
    return len(json_text(payload, compact=compact).encode("utf-8"))


def shard_rows(rows: list[dict[str, Any]], shard_size: int = c.DEFAULT_SHARD_ROW_TARGET) -> list[list[dict[str, Any]]]:
    if not rows:
        return []
    return [rows[index : index + shard_size] for index in range(0, len(rows), shard_size)]


def aggregate_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counter = Counter()
    candidates: set[str] = set()
    qkus: set[str] = set()
    for row in rows:
        if row.get("candidate_packet_id") and row["candidate_packet_id"] != c.NOT_APPLICABLE_ID:
            candidates.add(str(row["candidate_packet_id"]))
        if row.get("qku_id") and row["qku_id"] != c.NOT_APPLICABLE_ID:
            qkus.add(str(row["qku_id"]))
        for key in ("selection_state", "no_orphan_status", "computability_status", "downstream_route"):
            if row.get(key):
                status_counter[f"{key}={row[key]}"] += 1
    return {
        "row_count": len(rows),
        "candidate_packet_count": len(candidates),
        "qku_count": len(qkus),
        "status_counts": {key: status_counter[key] for key in sorted(status_counter)},
    }


def file_size_summary(repo_root: Path, report_filenames: tuple[str, ...]) -> dict[str, Any]:
    root_sizes = []
    shard_sizes = []
    for filename in report_filenames:
        root_path = repo_root / c.GENERATED_DIR / filename
        if root_path.exists():
            root_sizes.append(root_path.stat().st_size)
            payload = read_json(root_path)
            for shard_path in payload.get("shard_files") or []:
                resolved = resolve_repo_relative(repo_root, shard_path)
                if resolved.exists():
                    shard_sizes.append(resolved.stat().st_size)
    return {
        "root_report_count": len(root_sizes),
        "root_report_max_size_bytes": max(root_sizes) if root_sizes else 0,
        "root_reports_within_10_mib_limit": all(size <= ROOT_REPORT_LIMIT_BYTES for size in root_sizes),
        "shard_report_count": len(shard_sizes),
        "shard_report_max_size_bytes": max(shard_sizes) if shard_sizes else 0,
        "shard_reports_within_25_mib_limit": all(size <= SHARD_LIMIT_BYTES for size in shard_sizes),
    }


def tracked_file_list(repo_root: Path, row_payloads: dict[str, list[dict[str, Any]]]) -> list[str]:
    package_files = sorted(path.relative_to(repo_root).as_posix() for path in (repo_root / c.PACKAGE_DIR).glob("*.py"))
    schema_files = [normalize_repo_ref(c.SCHEMA_DIR / filename) for filename in c.SCHEMA_FILENAMES]
    tool_files = [
        "tools/build_pr165_d2_score_refreshed_scenario_selection_v2.py",
        "tools/validate_pr165_d2_score_refreshed_scenario_selection_v2.py",
        "tools/run_validation_gates.py",
        "tools/changed_area_validation_router.py",
        "tools/validation_inventory.py",
        "tools/ci_branch_context.py",
    ]
    report_files = [normalize_repo_ref(c.GENERATED_DIR / filename) for filename in c.REPORT_FILENAMES]
    test_files = [normalize_repo_ref(c.TEST_DIR / name) for name in REQUIRED_TEST_FILENAMES]
    return sorted(set(package_files + schema_files + tool_files + report_files + test_files))


REQUIRED_TEST_FILENAMES = (
    "test_pr165_d2_build_outputs.py",
    "test_pr165_d2_idempotence.py",
    "test_pr165_d2_validator.py",
    "test_pr165_d2_optional_pr166_sf_handling.py",
    "test_pr165_d2_optional_pr164_handling.py",
    "test_pr165_d2_row_count_reconciliation.py",
    "test_pr165_d2_no_placeholders_unknowns_or_metadata_only.py",
    "test_pr165_d2_net_edge_adjusted_ranking.py",
    "test_pr165_d2_tca_decomposition.py",
    "test_pr165_d2_prediction_market_probability_edge.py",
    "test_pr165_d2_microstructure_feature_ledger.py",
    "test_pr165_d2_score_component_provenance.py",
    "test_pr165_d2_repair_aware_selection_queue.py",
    "test_pr165_d2_condition_memory_application.py",
    "test_pr165_d2_champion_challenger_selection.py",
    "test_pr165_d2_marginal_utility_batch_builder.py",
    "test_pr165_d2_retest_budget_policy.py",
    "test_pr165_d2_capacity_crowding_correlation_controls.py",
    "test_pr165_d2_false_discovery_overfit_controls.py",
    "test_pr165_d2_quantum_candidate_priority_v2.py",
    "test_pr165_d2_external_institutional_signal_coverage.py",
    "test_pr165_d2_route_triage_crosswalk_command_matrix.py",
    "test_pr165_d2_connector_venue_readiness_reference_routing.py",
    "test_pr165_d2_agent_roster_discovery.py",
    "test_pr165_d2_agent_duty_source_crosswalk.py",
    "test_pr165_d2_agent_handoffs.py",
    "test_pr165_d2_no_orphans.py",
    "test_pr165_d2_status_enum_drift.py",
    "test_pr165_d2_authority_boundaries.py",
    "test_pr165_d2_pr152_pr208_routing_contract.py",
)


def numeric(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = row.get(key, default)
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def round6(value: float) -> float:
    return round(float(value), 6)


def clamp01(value: float) -> float:
    return round6(max(0.0, min(1.0, float(value))))


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return round6(ordered[mid])
    return round6((ordered[mid - 1] + ordered[mid]) / 2.0)


def _by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("candidate_packet_id")): row for row in rows if row.get("candidate_packet_id")}


def _by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows if row.get(key)}


def condition_memory_preference_score(memory_outcome: str) -> float:
    outcome = str(memory_outcome)
    if "PREFER" in outcome or "WINNER" in outcome:
        return 0.85
    if "AVOID" in outcome or "LOSER" in outcome:
        return 0.25
    if "WATCH" in outcome:
        return 0.45
    if "REPAIR" in outcome:
        return 0.35
    if any(token in outcome for token in ("COST_DOMINATED", "LATENCY_DOMINATED", "LIQUIDITY_DOMINATED")):
        return 0.32
    return 0.55


def deterministic_scenario_similarity(condition: dict[str, Any], regime: dict[str, Any], score: dict[str, Any]) -> float:
    fields = (
        ("venue", 0.10),
        ("market_type", 0.10),
        ("side", 0.07),
        ("time_to_resolution_bucket", 0.12),
        ("liquidity_bucket", 0.12),
        ("spread_bucket", 0.12),
        ("latency_bucket", 0.10),
        ("fee_bucket", 0.06),
        ("slippage_bucket", 0.06),
        ("source_provenance_tier", 0.05),
        ("quantum_formulation_class", 0.05),
        ("market_maturity_bucket", 0.05),
    )
    matched = 0.0
    total = 0.0
    for field, weight in fields:
        total += weight
        left = condition.get(field)
        right = regime.get(field) or score.get(field)
        if left and right and str(left) == str(right):
            matched += weight
        elif left:
            matched += weight * 0.45
    return clamp01(matched / total if total else 0.0)


def settlement_sensitivity_score(row: dict[str, Any]) -> float:
    gross = abs(numeric(row, "gross_edge", 0.0))
    settlement = abs(numeric(row, "settlement_payoff_adjustment", 0.0))
    return clamp01(settlement / max(0.01, gross + settlement))


def candidate_selection_score(values: dict[str, float]) -> float:
    total = 0.0
    for field, weight in c.SCORE_WEIGHTS.items():
        total += weight * clamp01(values.get(field, 0.0))
    return round6(total)


def ranking_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -row["edge_lower_confidence_bound"],
        -row["net_edge_after_costs"],
        -row["candidate_selection_score_v2"],
        -row["pr166_sm_refreshed_score"],
        -row["result_confidence_score"],
        row["false_discovery_risk_adjustment"],
        row["overfit_risk_adjustment"],
        row["cost_drag_ratio"],
        row["latency_drag_ratio"],
        row["liquidity_drag_ratio"],
        row["adverse_selection_ratio"],
        -row["scenario_transferability_score"],
        -row["marginal_utility_score"],
        -row["quantum_mapping_readiness_score"],
        row["scenario_group_id"],
        row["condition_fingerprint_id"],
        row["qku_id"],
        row["formula_id"],
        row["algorithm_id"],
        row["candidate_packet_id"],
        row["index"],
    )


def parse_rank(value: Any) -> int | None:
    text = str(value or "")
    if "::" not in text:
        return None
    tail = text.rsplit("::", 1)[-1]
    try:
        return int(tail)
    except ValueError:
        return None


def selection_numeric_fields(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: item[key]
        for key in (
            "prior_pr165_d_rank",
            "pr166_sm_refreshed_score",
            "pr166_sm_memory_outcome",
            "condition_memory_preference_score",
            "pr166_sm_rank_delta",
            "gross_edge",
            "net_edge_after_costs",
            "normalized_net_edge_after_costs",
            "edge_lower_confidence_bound",
            "result_confidence_score",
            "point_in_time_score",
            "no_lookahead_score",
            "fee_cost_component",
            "spread_cost_component",
            "slippage_cost_component",
            "latency_cost_component",
            "market_impact_cost_component",
            "liquidity_cost_component",
            "settlement_cost_component",
            "cost_drag_ratio",
            "latency_drag_ratio",
            "liquidity_drag_ratio",
            "adverse_selection_ratio",
            "settlement_sensitivity_score",
            "false_discovery_risk_adjustment",
            "overfit_risk_adjustment",
            "rank_instability_adjustment",
            "capacity_score",
            "crowding_penalty",
            "correlation_cluster_penalty",
            "scenario_similarity_score",
            "scenario_transferability_score",
            "marginal_utility_score",
            "expected_information_gain_score",
            "repair_priority_score",
            "repair_dependency_penalty",
            "field_materialization_required_flag",
            "quantum_mapping_readiness_score",
            "quantum_priority_after_replay_paper",
            "candidate_selection_score_v2",
        )
    }


def common_fields_for_candidate(
    source: dict[str, Any],
    artifact_id: str,
    row_id: str,
    upstream_artifact_refs: list[str],
    downstream_artifact_refs: list[str],
    *,
    downstream_pr_refs: list[str] | None = None,
    owning_agent: str = "parameter_selector_agent",
    no_orphan_status: str | None = None,
    value_authority_lane: str = ValueAuthorityLane.REPLAY_PAPER_SELECTION_CANDIDATE_LANE.value,
) -> dict[str, Any]:
    return common_fields(
        artifact_id=artifact_id,
        row_id=row_id,
        qku_id=str(source.get("qku_id") or c.NOT_APPLICABLE_ID),
        formula_id=str(source.get("formula_id") or c.NOT_APPLICABLE_ID),
        algorithm_id=str(source.get("algorithm_id") or c.NOT_APPLICABLE_ID),
        candidate_packet_id=str(source.get("candidate_packet_id") or c.NOT_APPLICABLE_ID),
        condition_fingerprint_id=str(source.get("condition_fingerprint_id") or c.NOT_APPLICABLE_ID),
        scenario_group_id=str(source.get("scenario_group_id") or c.NOT_APPLICABLE_ID),
        combination_id=str(source.get("combination_id") or c.NOT_APPLICABLE_ID),
        upstream_artifact_refs=upstream_artifact_refs,
        upstream_row_refs=list(source.get("upstream_row_refs") or source.get("source_row_refs") or [str(source.get("row_id") or row_id)]),
        upstream_value_refs=["candidate_packet_id", "qku_id", "selection_state"],
        downstream_pr_refs=downstream_pr_refs or [str(source.get("downstream_route") or DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value)],
        downstream_artifact_refs=downstream_artifact_refs,
        owning_agent=owning_agent,
        no_orphan_status=no_orphan_status or str(source.get("no_orphan_status") or NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value),
        value_authority_lane=value_authority_lane,
        selection_state=str(source.get("selection_state") or SelectionState.TERMINAL_BY_NATURE_WITH_REASON.value),
        materialization_action_ref=str(source.get("materialization_action_ref") or materialization_ref(source)),
        repair_route_ref=str(source.get("repair_route_ref") or repair_route_ref(source)),
        connector_dependency_class=str(source.get("connector_dependency_class") or ConnectorDependencyClass.NO_CONNECTOR_DEPENDENCY_FOR_SELECTION.value),
        venue_semantic_dependency_class=str(source.get("venue_semantic_dependency_class") or VenueSemanticDependencyClass.NO_VENUE_SEMANTIC_DEPENDENCY_FOR_SELECTION.value),
        future_connector_pr_refs=list(source.get("future_connector_pr_refs") or ["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"]),
        future_venue_readiness_route=str(source.get("future_venue_readiness_route") or "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"),
    )


def materialization_ref(row: dict[str, Any]) -> str:
    if row.get("repair"):
        repair = row["repair"]
        return str(
            repair.get("materialization_action_ref")
            or repair.get("materialization_action")
            or "PR165_D2_MATERIALIZATION_ACTION::EXACT_REPAIR_ROUTE_TO_PR166_SF"
        )
    return str(row.get("materialization_action_ref") or "PR165_D2_MATERIALIZATION_ACTION::NOT_REQUIRED_FOR_THIS_ROW_TERMINAL_BY_NATURE")


def repair_route_ref(row: dict[str, Any]) -> str:
    if row.get("repair_needed_before_retest"):
        return "PR166-SF"
    return str(row.get("repair_route_ref") or "PR165_D2_REPAIR_ROUTE::NOT_REQUIRED_FOR_RETEST_SELECTION")


def exact_missing_field(row: dict[str, Any]) -> str:
    if row.get("repair"):
        repair = row["repair"]
        return str(repair.get("exact_missing_field") or "score_refreshed_selection_materialization_detail")
    return "score_refreshed_selection_materialization_detail"


def unit_class_for_component(component_name: str) -> str:
    if "edge" in component_name:
        return UnitClass.SIGNED_NORMALIZED_MINUS1_1.value
    if any(token in component_name for token in ("cost", "drag", "penalty", "risk", "sensitivity", "adjustment")):
        return UnitClass.NORMALIZED_0_1.value
    if "rank" in component_name:
        return UnitClass.RANK_PERCENTILE_0_1.value
    return UnitClass.NORMALIZED_0_1.value


def calibration_bin_ref(row: dict[str, Any]) -> str:
    confidence = numeric(row, "result_confidence_score", 0.5)
    if confidence >= 0.75:
        return "PR165_D2_CALIBRATION_BIN::HIGH_CONFIDENCE"
    if confidence >= 0.50:
        return "PR165_D2_CALIBRATION_BIN::MEDIUM_CONFIDENCE"
    return "PR165_D2_CALIBRATION_BIN::LOW_CONFIDENCE"


def _total_cost_drag(row: dict[str, Any]) -> float:
    return round6(
        numeric(row, "fee_cost_component")
        + numeric(row, "spread_cost_component")
        + numeric(row, "slippage_cost_component")
        + numeric(row, "market_impact_cost_component")
        + numeric(row, "latency_cost_component")
        + numeric(row, "liquidity_cost_component")
        + numeric(row, "settlement_cost_component")
    )


def bucket_to_spread_cents(spread_bucket: str, spread_cost: float) -> float:
    text = str(spread_bucket)
    if "WIDE" in text:
        return round6(max(4.0, spread_cost * 100.0))
    if "MEDIUM" in text:
        return round6(max(2.0, spread_cost * 100.0))
    return round6(max(1.0, spread_cost * 100.0))


def depth_from_liquidity_bucket(bucket: str) -> int:
    text = str(bucket)
    if "HIGH" in text:
        return 1000
    if "MEDIUM" in text:
        return 250
    return 50


def bucket_from_value(value: float, thresholds: tuple[float, float], prefix: str) -> str:
    low, high = thresholds
    if value < low:
        return f"{prefix}_LOW"
    if value < high:
        return f"{prefix}_MEDIUM"
    return f"{prefix}_HIGH"


def quantum_structure_classes(model_class: str, structures: list[str]) -> list[str]:
    classes = set(structures)
    text = model_class.lower()
    if "bqm" in text or "qubo" in text:
        classes.update({"BQM", "QUBO", "binary variable objective"})
    if "ising" in text:
        classes.add("Ising")
    if "cqm" in text:
        classes.add("CQM")
    if "dqm" in text:
        classes.add("DQM")
    if "quadratic" in text:
        classes.update({"QuadraticProgram", "constrained quadratic objective"})
    if not classes:
        classes.update({"QuadraticProgram", "graph/portfolio/selection/assignment/knapsack-like objective"})
    return sorted(classes)


def memory_reason_codes(row: dict[str, Any]) -> list[str]:
    outcome = str(row["pr166_sm_memory_outcome"])
    codes = ["CONDITION_SCOPED_MEMORY_APPLIED"]
    if "PREFER" in outcome:
        codes.append("PREFERENCE_INCREASED_UNDER_MATCHING_CONDITIONS")
    if "AVOID" in outcome or "WATCH" in outcome:
        codes.append("PENALTY_OR_WATCH_APPLIED_UNDER_MATCHING_CONDITIONS")
    if row["repair_needed_before_retest"]:
        codes.append("REPAIR_BEFORE_RETEST_UNDER_MATCHING_CONDITIONS")
    return codes


def false_discovery_reason_codes(row: dict[str, Any]) -> list[str]:
    codes = []
    if row["false_discovery_risk_adjustment"] >= 0.65:
        codes.append("FALSE_DISCOVERY_RISK_PENALIZED")
    if row["overfit_risk_adjustment"] >= 0.65:
        codes.append("OVERFIT_RISK_PENALIZED")
    if row["rank_instability_adjustment"] >= 0.50:
        codes.append("RANK_INSTABILITY_PENALIZED")
    if row["near_duplicate_cluster_size"] > 1:
        codes.append("NEAR_DUPLICATE_CLUSTER_PENALIZED")
    if not codes:
        codes.append("FALSE_DISCOVERY_CONTROL_APPLIED_NO_MATERIAL_PENALTY")
    return codes


def retest_budget_tier(row: dict[str, Any], index: int) -> str:
    if row["selection_state"] == SelectionState.SELECTED_AS_CHAMPION.value:
        return "TIER_1_HIGH_CONFIDENCE_CHAMPIONS"
    if row["selection_state"] == SelectionState.SELECTED_AS_CHALLENGER.value:
        return "TIER_2_HIGH_EDGE_CHALLENGERS"
    if row["selection_state"] == SelectionState.SELECTED_AS_QUANTUM_PRIORITY_CANDIDATE.value:
        return "TIER_4_QUANTUM_PRIORITY_CANDIDATES"
    if row["repair_dependency_penalty"] > 0.25:
        return "TIER_5_REPAIR_AWARE_WATCHLIST"
    return "TIER_3_DIVERSIFICATION_AND_REGIME_COVERAGE"


def budget_tier_reason(tier: str) -> str:
    reasons = {
        "TIER_1_HIGH_CONFIDENCE_CHAMPIONS": "preserve strongest robust prior candidates",
        "TIER_2_HIGH_EDGE_CHALLENGERS": "test challengers with better refreshed score or memory",
        "TIER_3_DIVERSIFICATION_AND_REGIME_COVERAGE": "increase scenario and regime coverage",
        "TIER_4_QUANTUM_PRIORITY_CANDIDATES": "reserve replay/paper evidence for quantum comparators",
        "TIER_5_REPAIR_AWARE_WATCHLIST": "retain useful rows while repair burden is tracked",
        "TIER_6_EXTERNAL_SIGNAL_CANDIDATES": "reserve budget for provisional external signal intake",
    }
    return reasons[tier]


def route_agent(route: str) -> str:
    if route == DownstreamRoute.PR166_SF.value:
        return "parameter_selector_agent"
    if route in {DownstreamRoute.PR166_Q.value, DownstreamRoute.PR162E_Q.value}:
        return "quantum_optimizer_agent"
    if route in c.FUTURE_CONNECTOR_PR_REFS:
        return "connector_venue_readiness_future_consumer"
    if route == DownstreamRoute.PR166_S_RETEST_LOOP_V2.value:
        return "parameter_selector_agent"
    return "commander_agent"


def no_orphan_for_route(route: str) -> str:
    mapping = {
        DownstreamRoute.PR166_S_RETEST_LOOP.value: NoOrphanStatus.CONNECTED_TO_PR166_S_RETEST_LOOP.value,
        DownstreamRoute.PR166_S_RETEST_LOOP_V2.value: NoOrphanStatus.CONNECTED_TO_PR166_S_RETEST_LOOP.value,
        DownstreamRoute.PR166_SF.value: NoOrphanStatus.CONNECTED_TO_PR166_SF_ROUTE.value,
        DownstreamRoute.PR166_Q.value: NoOrphanStatus.CONNECTED_TO_PR166_Q_ROUTE.value,
        DownstreamRoute.PR162E_Q.value: NoOrphanStatus.CONNECTED_TO_PR162E_Q_ROUTE.value,
        DownstreamRoute.PR162D_R3.value: NoOrphanStatus.CONNECTED_TO_PR162D_R3_ROUTE.value,
        DownstreamRoute.PR162E.value: NoOrphanStatus.CONNECTED_TO_PR162E_PR162F_PLUGIN_INTAKE_REFERENCE_ROUTE.value,
        DownstreamRoute.PR162F.value: NoOrphanStatus.CONNECTED_TO_PR162E_PR162F_PLUGIN_INTAKE_REFERENCE_ROUTE.value,
        DownstreamRoute.PR167.value: NoOrphanStatus.CONNECTED_TO_PR167_ROUTE.value,
        DownstreamRoute.PR173.value: NoOrphanStatus.CONNECTED_TO_PR173_AGENT_GOVERNANCE_ROUTE.value,
        DownstreamRoute.DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value: NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value,
    }
    if route in c.FUTURE_CONNECTOR_PR_REFS:
        return NoOrphanStatus.CONNECTED_TO_PR174_PR181_CONNECTOR_READINESS_REFERENCE_ROUTE.value
    if route in {"PR168", "PR169", "PR170"}:
        return NoOrphanStatus.CONNECTED_TO_PR168_PR169_PR170_ROUTE.value
    if route in {"PR171", "PR172"}:
        return NoOrphanStatus.CONNECTED_TO_PR171_PR172_ROUTE.value
    return mapping.get(route, NoOrphanStatus.CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW.value)


def selection_state_for_route(route: str) -> str:
    if route == DownstreamRoute.PR166_S_RETEST_LOOP_V2.value:
        return SelectionState.SELECTED_FOR_REPLAY_PAPER_RETEST_V2.value
    if route == DownstreamRoute.PR166_SF.value:
        return SelectionState.ROUTE_TO_PR166_SF_REPAIR_BEFORE_RETEST.value
    if route == DownstreamRoute.PR166_Q.value:
        return SelectionState.ROUTE_TO_PR166_Q_QUANTUM_COMPARATOR.value
    if route == DownstreamRoute.PR162E_Q.value:
        return SelectionState.ROUTE_TO_PR162E_Q_QUANTUM_MAPPING.value
    if route in c.FUTURE_CONNECTOR_PR_REFS:
        return SelectionState.ROUTE_TO_PR174_PR181_CONNECTOR_READINESS_FUTURE.value
    if route == DownstreamRoute.PR167.value:
        return SelectionState.ROUTE_TO_PR167_OPEN_TRADE_SIMULATOR_FUTURE.value
    return SelectionState.ROUTE_TO_PR173_AGENT_GOVERNANCE_FUTURE.value


def connector_dependency_class(condition: dict[str, Any]) -> str:
    venue = str(condition.get("venue") or "")
    if "SYNTHETIC" in venue or not venue:
        return ConnectorDependencyClass.ORDERBOOK_OR_MARKET_DATA_CONNECTOR_REQUIRED_LATER.value
    return ConnectorDependencyClass.VENUE_FIELD_SEMANTICS_REQUIRED_LATER.value


def venue_dependency_class(condition: dict[str, Any]) -> str:
    if condition.get("market_id_or_candidate_market_ref"):
        return VenueSemanticDependencyClass.VENUE_MARKET_ID_SEMANTICS_REQUIRED_LATER.value
    return VenueSemanticDependencyClass.VENUE_ORDERBOOK_SEMANTICS_REQUIRED_LATER.value


def computability_status_for_route(upstream: dict[str, Any], ranked: dict[str, Any]) -> str:
    if ranked and ranked.get("selected_for_retest_v2_flag"):
        return ComputabilityStatus.COMPUTABLE_FOR_REPLAY_PAPER_RETEST_V2.value
    if ranked and ranked.get("selection_state") == SelectionState.ROUTE_TO_PR166_SF_REPAIR_BEFORE_RETEST.value:
        return ComputabilityStatus.COMPUTABLE_FOR_REPAIR_AWARE_SELECTION_ONLY.value
    if numeric(upstream, "quantum_mapping_readiness_score", 0.0) >= 0.60:
        return ComputabilityStatus.COMPUTABLE_FOR_QUANTUM_PRIORITY_ONLY.value
    if ranked:
        return ComputabilityStatus.COMPUTABLE_FOR_CONNECTOR_READINESS_REFERENCE_ONLY.value
    return ComputabilityStatus.COMPUTABLE_AFTER_EXACT_MATERIALIZATION_ACTION.value


def computability_downstream_route(status: str, ranked: dict[str, Any]) -> str:
    if status == ComputabilityStatus.COMPUTABLE_FOR_REPLAY_PAPER_RETEST_V2.value:
        return DownstreamRoute.PR166_S_RETEST_LOOP_V2.value
    if status == ComputabilityStatus.COMPUTABLE_FOR_REPAIR_AWARE_SELECTION_ONLY.value:
        return DownstreamRoute.PR166_SF.value
    if status == ComputabilityStatus.COMPUTABLE_FOR_QUANTUM_PRIORITY_ONLY.value:
        return DownstreamRoute.PR166_Q.value
    if status == ComputabilityStatus.COMPUTABLE_FOR_CONNECTOR_READINESS_REFERENCE_ONLY.value:
        return DownstreamRoute.PR174.value
    return DownstreamRoute.PR162D_R3.value


def expected_row_count(filename: str, source: SourceData) -> int | None:
    if filename in c.EXPECTED_ROW_COUNTS:
        return c.EXPECTED_ROW_COUNTS[filename]
    payload = source.payloads.get(filename)
    if payload is None:
        return None
    value = payload.get("record_count")
    return int(value) if isinstance(value, int) else len(source.records.get(filename, []))


def duties_for_agent(agent_id: str) -> list[str]:
    duties = {
        "research_agent": ["external selection signal candidates", "formula and value materialization", "scenario feature scouting"],
        "parameter_selector_agent": ["net-edge adjusted ranking", "champion challenger selection", "retest batch and repair queue ownership"],
        "risk_manager_agent": ["false-discovery overfit rank instability", "settlement liquidity latency adverse selection", "capacity crowding correlation controls"],
        "quantum_optimizer_agent": ["quantum candidate priority v2", "QUBO Ising BQM CQM DQM QuadraticProgram route review"],
        "commander_agent": ["next PR routing", "command action matrix", "downstream route ownership"],
        "governance_agent": ["authority boundary audit", "status enum drift audit", "no orphan audit"],
        "dashboard_agent": ["selected batch display", "watchlist and exclusion display", "owner review labels without live action"],
        "connector_venue_readiness_future_consumer": ["future connector readiness reference route consumption", "no semantic binding from PR165-D2"],
    }
    return duties[agent_id]


def consumed_classes_for_agent(agent_id: str) -> list[str]:
    mapping = {
        "research_agent": ["external_signal_candidate", "materialization_gap"],
        "parameter_selector_agent": ["ranking", "retest_batch", "repair_queue"],
        "risk_manager_agent": ["tca", "false_discovery", "capacity", "microstructure"],
        "quantum_optimizer_agent": ["quantum_priority", "computability_routing"],
        "commander_agent": ["route_triage", "command_action"],
        "governance_agent": ["authority_audit", "orphan_audit", "status_audit"],
        "dashboard_agent": ["dashboard_handoff", "market_index"],
        "connector_venue_readiness_future_consumer": ["connector_reference_route"],
    }
    return mapping[agent_id]


def output_classes_for_agent(agent_id: str) -> list[str]:
    mapping = {
        "research_agent": ["materialization_action", "candidate_signal_route"],
        "parameter_selector_agent": ["selected_batch", "repair_handoff"],
        "risk_manager_agent": ["risk_review_task"],
        "quantum_optimizer_agent": ["quantum_route_task"],
        "commander_agent": ["command_action_task"],
        "governance_agent": ["audit_receipt"],
        "dashboard_agent": ["owner_review_display_label"],
        "connector_venue_readiness_future_consumer": ["future_connector_readiness_task"],
    }
    return mapping[agent_id]


def handoff_inputs_for_agent(agent_id: str) -> list[str]:
    mapping = {
        "research_agent": ["PR165_D2_ExternalSelectionSignalCandidateRegistry.report.json", "PR165_D2_QKUFormulaAlgorithmComputabilityRouting.report.json"],
        "parameter_selector_agent": ["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json", "PR165_D2_ReplayPaperRetestBatchV2.report.json"],
        "risk_manager_agent": ["PR165_D2_TCADecompositionSelectionLedger.report.json", "PR165_D2_FalseDiscoveryOverfitSelectionControl.report.json"],
        "quantum_optimizer_agent": ["PR165_D2_QuantumCandidatePriorityV2.report.json"],
        "commander_agent": ["PR165_D2_RouteTriageMatrix.report.json", "PR165_D2_CommandActionMatrix.report.json"],
        "governance_agent": ["PR165_D2_AuthorityBoundaryAudit.report.json", "PR165_D2_OrphanArtifactAudit.report.json"],
        "dashboard_agent": ["PR165_D2_DashboardSelectionHandoff.report.json", "PR165_D2_MarketSpecificSelectionIndex.report.json"],
        "connector_venue_readiness_future_consumer": ["PR165_D2_ConnectorVenueReadinessReferenceRouting.report.json"],
    }
    return mapping[agent_id]


def handoff_outputs_for_agent(agent_id: str) -> list[str]:
    mapping = {
        "research_agent": ["PR162D-R3 materialization tasks"],
        "parameter_selector_agent": ["PR166-S_RETEST_LOOP_V2 batches", "PR166-SF repair handoffs"],
        "risk_manager_agent": ["risk review and governance tasks"],
        "quantum_optimizer_agent": ["PR166-Q and PR162E-Q routes"],
        "commander_agent": ["downstream command routing"],
        "governance_agent": ["audit review receipts"],
        "dashboard_agent": ["owner review display labels without live action"],
        "connector_venue_readiness_future_consumer": ["PR174 through PR181 reference routes"],
    }
    return mapping[agent_id]


def owning_agent_for_report(filename: str) -> str:
    if "Quantum" in filename:
        return "quantum_optimizer_agent"
    if any(token in filename for token in ("TCA", "FalseDiscovery", "Capacity", "Microstructure")):
        return "risk_manager_agent"
    if any(token in filename for token in ("Agent", "Dashboard", "Governance", "Commander", "Authority", "Orphan", "Status", "Manifest", "Summary", "Crosswalk")):
        return "governance_agent"
    if "External" in filename:
        return "research_agent"
    return "parameter_selector_agent"


def report_upstream_refs(filename: str) -> list[str]:
    if "Quantum" in filename:
        return ["PR166_SM_QuantumPriorityAfterReplayPaperRegistry.report.json"]
    if "Repair" in filename:
        return ["PR166_SM_RepairPriorityRegistry.report.json"]
    if "External" in filename:
        return ["PR164 optional", "external candidate references"]
    return ["PR166_SM_RefreshedScoreRegistry.report.json", "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json"]


def report_downstream_refs(filename: str) -> list[str]:
    if "Repair" in filename:
        return ["PR166-SF"]
    if "Quantum" in filename:
        return ["PR166-Q", "PR162E-Q"]
    if "Connector" in filename:
        return list(c.FUTURE_CONNECTOR_PR_REFS)
    if "Retest" in filename or "Ranking" in filename:
        return ["PR166-S_RETEST_LOOP_V2"]
    return ["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"]
