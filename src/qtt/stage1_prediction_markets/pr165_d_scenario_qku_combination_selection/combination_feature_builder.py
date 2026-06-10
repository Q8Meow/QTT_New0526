"""Canonical PR165-D core-table builder."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .authority_policy import authority_boundary_record, authority_zero_counts
from .central_vocab import (
    AUTHORITY_BOUNDARY_REF,
    DOWNSTREAM_PR_ROUTES,
    NO_ORPHAN_STATUS,
    UPSTREAM_PR_REFS,
    VALIDATION_STATUS,
)
from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import group_by, index_by, load_report_records, try_load_report_records
from .optional_input_receipts import receipt_id
from .scenario_selection_policy import scenario_bucket
from .score_normalization import bounded_numeric, bucketize, clamp_0_1, positive_rank_strength, score_points

BATCH_SIZE = 50


@dataclass(frozen=True)
class CandidateContext:
    index: int
    candidate_packet_id: str
    qku_id: str
    qku_family: str
    qku_type: str
    candidate_version: str
    condition_fingerprint_id: str
    combination_fingerprint_id: str
    memory: dict[str, Any]
    pending: dict[str, Any] | None
    repair: dict[str, Any] | None
    priority: dict[str, Any]
    condition_feature: dict[str, Any]
    score: dict[str, Any]
    component: dict[str, Any]
    expected_value: dict[str, Any]
    tca: dict[str, Any]
    latency: dict[str, Any]
    regime_rows: list[dict[str, Any]]
    scenario: dict[str, Any]
    quantum: dict[str, Any]
    pr165_c_quantum: dict[str, Any]
    lineage: dict[str, Any]


def build_core_tables(repo_root: Path, optional_receipts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    loaded = _load_inputs(repo_root)
    memory_rows = loaded["memory_rows"]
    pending_by_candidate = index_by(loaded["pending_rows"], "candidate_packet_id")
    repair_by_candidate = index_by(loaded["repair_rows"], "candidate_packet_id")
    priority_by_candidate = index_by(loaded["priority_rows"], "candidate_packet_id")
    condition_by_candidate = index_by(loaded["condition_feature_rows"], "candidate_packet_id")
    pr165_c_quantum_by_candidate = index_by(loaded["pr165_c_quantum_rows"], "candidate_packet_id")
    pr165_c_lineage_by_candidate = index_by(loaded["pr165_c_lineage_rows"], "candidate_packet_id")
    contexts = _build_contexts(
        memory_rows=memory_rows,
        pending_by_candidate=pending_by_candidate,
        repair_by_candidate=repair_by_candidate,
        priority_by_candidate=priority_by_candidate,
        condition_by_candidate=condition_by_candidate,
        pr165_c_quantum_by_candidate=pr165_c_quantum_by_candidate,
        pr165_c_lineage_by_candidate=pr165_c_lineage_by_candidate,
        pr165=loaded["pr165"],
        pr165_b=loaded["pr165_b"],
    )
    family_counts = Counter(context.qku_family for context in contexts)
    scenario_counts = Counter(_scenario_group_id(context) for context in contexts)
    missing_refs = _missing_receipt_refs(optional_receipts)

    feature_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    score_rows: list[dict[str, Any]] = []
    diversification_rows: list[dict[str, Any]] = []
    marginal_rows: list[dict[str, Any]] = []
    false_discovery_rows: list[dict[str, Any]] = []
    point_in_time_rows: list[dict[str, Any]] = []
    formula_route_rows: list[dict[str, Any]] = []
    quantum_route_rows: list[dict[str, Any]] = []
    selected_reason_rows: list[dict[str, Any]] = []
    agent_contract_rows: list[dict[str, Any]] = []
    agent_handoff_rows: list[dict[str, Any]] = []
    dashboard_rows: list[dict[str, Any]] = []
    governance_rows: list[dict[str, Any]] = []
    lineage_rows: list[dict[str, Any]] = []

    enriched: list[dict[str, Any]] = []
    for context in contexts:
        features = _feature_vector(context, family_counts, scenario_counts, missing_refs)
        components = _score_components(context, features)
        score_record = _score_record(context, features, components)
        diversification = _diversification_record(context, features, score_record)
        adjusted_score = clamp_0_1(
            score_record["base_selection_score"]
            + score_record["combination_synergy_score"]
            + diversification["scenario_coverage_gain"]
            + diversification["exploration_budget_gain"]
            - diversification["correlation_overlap_penalty"]
            - diversification["batch_concentration_penalty"]
        )
        score_record["adjusted_selection_score"] = adjusted_score
        features["adjusted_selection_score"] = adjusted_score
        enriched.append(
            {
                "context": context,
                "features": features,
                "components": components,
                "score_record": score_record,
                "diversification": diversification,
            }
        )

    batch_assignments, batch_rows = _select_batches(enriched)
    for row in enriched:
        context: CandidateContext = row["context"]
        features = row["features"]
        components = row["components"]
        score_record = row["score_record"]
        diversification = row["diversification"]
        assignment = batch_assignments.get(context.candidate_packet_id, {})
        features["batch_id"] = assignment.get(
            "batch_id",
            stable_ref("PR165_D_BATCH_NOT_REQUIRED_REF", context.candidate_packet_id),
        )
        marginal = _marginal_record(context, features, score_record, diversification, assignment)
        features["marginal_candidate_utility"] = marginal["marginal_candidate_utility"]
        score_record["marginal_candidate_utility"] = marginal["marginal_candidate_utility"]
        selected_state = _selected_state(context, features, assignment)
        features.update(selected_state)

        feature_rows.append(features)
        candidate_rows.append(_combination_candidate_record(context, features))
        component_rows.append(components)
        score_rows.append(score_record)
        diversification_rows.append(diversification)
        marginal_rows.append(marginal)
        false_discovery_rows.append(_false_discovery_record(context, features))
        point_in_time_rows.append(_point_in_time_record(context, features))
        formula_route_rows.append(_formula_route_record(context, features, missing_refs))
        quantum_route_rows.append(_quantum_route_record(context, features, missing_refs))
        selected_reason_rows.append(_selected_excluded_reason_record(context, features, components, assignment))
        agent_contract_rows.append(_agent_contract_record(context, features))
        agent_handoff_rows.append(_agent_handoff_record(context, features))
        dashboard_rows.append(_dashboard_record(context, features))
        governance_rows.append(_governance_record(context, features))
        lineage_rows.append(_lineage_record(context, features))

    retest_rows = _retest_batch_rows(enriched, batch_assignments)
    repair_rows = _repair_before_retest_rows(enriched, batch_assignments)
    commander_rows = _commander_rows(retest_rows, repair_rows)

    return {
        "SelectionUniverseCoverageTable": candidate_rows,
        "ScenarioGroupTable": _scenario_group_rows(enriched),
        "ScenarioFeatureTable": feature_rows,
        "CandidateFeatureVectorTable": feature_rows,
        "SelectionScoreComponentTable": component_rows,
        "SelectionScoreTable": score_rows,
        "DiversificationAdjustmentTable": diversification_rows,
        "MarginalUtilitySelectionTable": marginal_rows,
        "BatchConstraintTable": batch_rows,
        "RetestBatchSelectionTable": retest_rows,
        "RepairBeforeRetestSelectionTable": repair_rows,
        "QuantumSelectionRouteTable": quantum_route_rows,
        "FormulaAlgorithmOptionalRouteTable": formula_route_rows,
        "AgentSelectionContractTable": agent_contract_rows,
        "AgentSelectionHandoffTable": agent_handoff_rows,
        "DashboardGovernanceCommanderHandoffTable": dashboard_rows + governance_rows + commander_rows,
        "DashboardSelectionHandoffTable": dashboard_rows,
        "GovernanceSelectionHandoffTable": governance_rows,
        "CommanderSelectionHandoffTable": commander_rows,
        "SelectedExcludedReasonTable": selected_reason_rows,
        "LineageGraphTable": lineage_rows,
        "AuthorityBoundaryAuditTable": _authority_rows(),
        "OrphanArtifactAuditTable": _orphan_rows(candidate_rows, retest_rows, repair_rows, lineage_rows),
        "ScenarioQKUCombinationCandidateTable": candidate_rows,
        "BatchExposureCapacityTable": batch_rows,
        "SelectionFalseDiscoveryControlTable": false_discovery_rows,
        "PointInTimeSelectionAuditTable": point_in_time_rows,
    }


def _load_inputs(repo_root: Path) -> dict[str, Any]:
    pr165_reports = {
        "components": "PR165_CandidateScoreComponentRegistry.report.json",
        "global": "PR165_GlobalCandidateRanking.report.json",
        "regime": "PR165_RegimeSlicedRanking.report.json",
        "expected": "PR165_ExpectedValueScoreRegistry.report.json",
        "tca": "PR165_TCAAdjustedScoreRegistry.report.json",
        "latency": "PR165_LatencyLaneAssignmentRegistry.report.json",
        "quantum": "PR165_QuantumFormulationMaterializationRegistry.report.json",
    }
    pr165_b_reports = {
        "scenario": "PR165_B_ScenarioOutcomeMatrix.report.json",
        "condition": "PR165_B_ConditionFingerprintRegistry.report.json",
        "combination": "PR165_B_CombinationFingerprintRegistry.report.json",
        "negative": "PR165_B_NegativeCombinationAvoidanceRegistry.report.json",
        "positive": "PR165_B_PositiveConditionScopedPreferenceRegistry.report.json",
        "fragile": "PR165_B_FragileCombinationWatchlist.report.json",
    }
    pr165 = {name: load_report_records(repo_root, filename) for name, filename in pr165_reports.items()}
    pr165_b = {name: load_report_records(repo_root, filename) for name, filename in pr165_b_reports.items()}
    return {
        "memory_rows": load_report_records(repo_root, "PR165_C_MemoryConsumerRouter.report.json"),
        "pending_rows": load_report_records(repo_root, "PR165_C_PendingRetestQueue.report.json"),
        "repair_rows": load_report_records(repo_root, "PR165_C_RepairToRetestHandoff.report.json"),
        "priority_rows": load_report_records(repo_root, "PR165_C_RetestPriorityRanking.report.json"),
        "condition_feature_rows": load_report_records(repo_root, "PR165_C_ConditionRegimeFeatureMatrix.report.json"),
        "pr165_c_quantum_rows": load_report_records(repo_root, "PR165_C_QuantumConsumerRouter.report.json"),
        "pr165_c_lineage_rows": load_report_records(repo_root, "PR165_C_LineageGraph.report.json"),
        "optional_legacy_formula_rows": try_load_report_records(repo_root, "PR164_QKUFormulaRegistry.report.json"),
        "pr165": {
            "components": index_by(pr165["components"], "candidate_packet_id"),
            "global": index_by(pr165["global"], "candidate_packet_id"),
            "regime": group_by(pr165["regime"], "candidate_packet_id"),
            "expected": index_by(pr165["expected"], "candidate_packet_id"),
            "tca": index_by(pr165["tca"], "candidate_packet_id"),
            "latency": index_by(pr165["latency"], "candidate_packet_id"),
            "quantum": index_by(pr165["quantum"], "candidate_packet_id"),
        },
        "pr165_b": {
            "scenario": index_by(pr165_b["scenario"], "candidate_packet_id"),
            "condition": index_by(pr165_b["condition"], "condition_fingerprint_id"),
            "combination": index_by(pr165_b["combination"], "combination_fingerprint_id"),
            "negative": index_by(pr165_b["negative"], "candidate_packet_id"),
            "positive": index_by(pr165_b["positive"], "candidate_packet_id"),
            "fragile": index_by(pr165_b["fragile"], "candidate_packet_id"),
        },
    }


def _build_contexts(
    *,
    memory_rows: list[dict[str, Any]],
    pending_by_candidate: dict[str, dict[str, Any]],
    repair_by_candidate: dict[str, dict[str, Any]],
    priority_by_candidate: dict[str, dict[str, Any]],
    condition_by_candidate: dict[str, dict[str, Any]],
    pr165_c_quantum_by_candidate: dict[str, dict[str, Any]],
    pr165_c_lineage_by_candidate: dict[str, dict[str, Any]],
    pr165: dict[str, Any],
    pr165_b: dict[str, Any],
) -> list[CandidateContext]:
    contexts: list[CandidateContext] = []
    for index, memory in enumerate(memory_rows, start=1):
        candidate_id = str(memory["candidate_packet_id"])
        contexts.append(
            CandidateContext(
                index=index,
                candidate_packet_id=candidate_id,
                qku_id=str(memory["qku_id"]),
                qku_family=str(memory.get("qku_family") or _qku_family(str(memory["qku_id"]))),
                qku_type=str(memory.get("qku_type") or "PREDICTION_MARKET_REPLAY_PAPER_CANDIDATE"),
                candidate_version=str(memory.get("candidate_version") or f"{candidate_id}::VERSION::PR165_D_SELECTION"),
                condition_fingerprint_id=str(memory["condition_fingerprint_id"]),
                combination_fingerprint_id=str(memory["combination_fingerprint_id"]),
                memory=memory,
                pending=pending_by_candidate.get(candidate_id),
                repair=repair_by_candidate.get(candidate_id),
                priority=priority_by_candidate.get(candidate_id, {}),
                condition_feature=condition_by_candidate.get(candidate_id, {}),
                score=pr165["global"].get(candidate_id, {}),
                component=pr165["components"].get(candidate_id, {}),
                expected_value=pr165["expected"].get(candidate_id, {}),
                tca=pr165["tca"].get(candidate_id, {}),
                latency=pr165["latency"].get(candidate_id, {}),
                regime_rows=pr165["regime"].get(candidate_id, []),
                scenario=pr165_b["scenario"].get(candidate_id, {}),
                quantum=pr165["quantum"].get(candidate_id, {}),
                pr165_c_quantum=pr165_c_quantum_by_candidate.get(candidate_id, {}),
                lineage=pr165_c_lineage_by_candidate.get(candidate_id, {}),
            )
        )
    return contexts


def _feature_vector(
    context: CandidateContext,
    family_counts: Counter[str],
    scenario_counts: Counter[str],
    missing_refs: dict[str, str],
) -> dict[str, Any]:
    memory_status = str(context.memory.get("computability_action_status"))
    quantum_repair_required = _quantum_repair_required(context.quantum)
    status = "COMPUTABLE_AFTER_QUANTUM_FORMULATION_REPAIR" if quantum_repair_required else memory_status
    repair_required = status == "COMPUTABLE_AFTER_REPAIR" or context.repair is not None
    retest_required = bool(context.memory.get("retest_required")) or context.pending is not None
    scenario_match = _scenario_match_score(context)
    evidence_confidence = _evidence_confidence_score(context)
    expected_score = _expected_value_score(context)
    positive_memory = context.memory.get("memory_classification") == "POSITIVE_CONDITION_SCOPED_PREFERRED"
    fragile_memory = context.memory.get("memory_classification") in {
        "FRAGILE_HIGH_VARIANCE",
        "FALSE_DISCOVERY_RISK_WATCH",
        "REPAIR_CONFIDENCE_WEAK",
    }
    bucket = scenario_bucket(
        repair_required=repair_required,
        quantum_repair_required=quantum_repair_required,
        positive_memory=positive_memory,
        fragile_memory=fragile_memory,
        expected_value_score=expected_score,
        evidence_confidence_score=evidence_confidence,
    )
    readiness = _readiness_classification(
        retest_required=retest_required,
        repair_required=repair_required,
        quantum_repair_required=quantum_repair_required,
        formula_missing=bool(missing_refs.get("formula_algorithm")),
        optional_quantum_missing=bool(missing_refs.get("quantum_comparator")),
    )
    target_mode = _target_retest_mode(readiness)
    target_future_pr = _target_future_pr(readiness)
    scenario_group_id = _scenario_group_id(context)
    duplicate_penalty = clamp_0_1((family_counts[context.qku_family] - 1) / max(len(family_counts), 1) / 12.0)
    correlation_penalty = clamp_0_1((scenario_counts[scenario_group_id] - 1) / max(sum(scenario_counts.values()), 1))
    tca_drag = _tca_drag(context)
    latency_drag = _latency_drag(context)
    liquidity_fragility = _liquidity_fragility(context)
    adverse_selection = score_points(context.scenario.get("adverse_selection_penalty"), default=2.0)
    false_discovery = clamp_0_1(1.0 - evidence_confidence)
    repair_readiness = _repair_readiness(context, repair_required)
    quantum_score = _quantum_candidate_score(context)
    feature = {
        "candidate_feature_vector_id": ordinal_ref("PR165_D_CANDIDATE_FEATURE_VECTOR", context.index),
        "selection_universe_coverage_id": ordinal_ref("PR165_D_SELECTION_UNIVERSE", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "qku_family": context.qku_family,
        "qku_type": context.qku_type,
        "candidate_version": context.candidate_version,
        "condition_fingerprint_id": context.condition_fingerprint_id,
        "combination_fingerprint_id": context.combination_fingerprint_id,
        "pr165_score_ref": context.memory.get("pr165_score_ref") or context.component.get("score_component_ref", ""),
        "pr165_rank_ref": context.memory.get("pr165_rank_ref") or context.score.get("candidate_global_rank_ref", ""),
        "pr165_b_memory_ref": context.memory.get("pr165_b_memory_ref", ""),
        "pr165_c_memory_consumer_ref": context.memory.get("memory_consumer_id", ""),
        "pr165_c_pending_retest_ref": _pending_retest_ref(context),
        "pr165_c_repair_to_retest_ref": _repair_to_retest_ref(context),
        "pr165_c_quantum_consumer_route_ref": context.pr165_c_quantum.get("quantum_consumer_route_id", ""),
        "memory_classification": context.memory.get("memory_classification"),
        "memory_action_policy": context.memory.get("memory_action_policy"),
        "computability_action_status": status,
        "pr165_c_computability_action_status": memory_status,
        "retest_required": retest_required,
        "repair_required": repair_required,
        "quantum_formulation_repair_required": quantum_repair_required,
        "formula_algorithm_optional_missing": bool(missing_refs.get("formula_algorithm")),
        "scenario_group_id": scenario_group_id,
        "scenario_selection_bucket": bucket,
        "scenario_match_score": scenario_match,
        "base_selection_score": 0.0,
        "adjusted_selection_score": 0.0,
        "marginal_candidate_utility": 0.0,
        "combination_synergy_score": _combination_synergy(context, positive_memory),
        "diversity_penalty": clamp_0_1(duplicate_penalty + correlation_penalty),
        "duplicate_family_penalty": duplicate_penalty,
        "correlation_overlap_penalty": correlation_penalty,
        "TCA_drag_penalty": tca_drag,
        "latency_drag_penalty": latency_drag,
        "liquidity_fragility_penalty": liquidity_fragility,
        "adverse_selection_penalty": adverse_selection,
        "evidence_confidence_score": evidence_confidence,
        "false_discovery_penalty": false_discovery,
        "repair_readiness_score": repair_readiness,
        "quantum_candidate_selection_score": quantum_score,
        "formula_algorithm_availability_status": _formula_availability_status(missing_refs),
        "optional_formula_algorithm_input_receipt_ref": missing_refs.get("formula_algorithm", ""),
        "optional_quantum_comparator_input_receipt_ref": missing_refs.get("quantum_comparator", ""),
        "selected_for_retest_batch_flag": False,
        "selected_for_repair_before_retest_flag": False,
        "selected_for_quantum_repair_flag": False,
        "excluded_from_selected_batch_reason_codes": [],
        "readiness_classification": readiness,
        "target_retest_mode": target_mode,
        "target_future_pr": target_future_pr,
        "primary_agent_owner": _primary_agent(readiness, context),
        "secondary_agent_reviewers": ["risk_agent", "tca_agent", "latency_agent", "liquidity_agent", "governance_agent"],
        "effective_challenger_agent": _challenger_agent(readiness),
        "downstream_agent_consumer": _downstream_agent(readiness),
        "dashboard_visibility": "SELECTION_QUEUE_VISIBLE",
        "governance_visibility": "SELECTION_AUTHORITY_BOUNDARY_VISIBLE",
        "commander_visibility": "FUTURE_PR_ROUTE_VISIBLE",
        "lineage_graph_ref": ordinal_ref("PR165_D_LINEAGE", context.index),
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "no_orphan_status": NO_ORPHAN_STATUS,
        "upstream_source_pr_refs": list(UPSTREAM_PR_REFS),
        "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
        "owning_agent": "selection_agent",
        "validator": "tools/validate_pr165_d_scenario_qku_combination_selection.py",
        "manifest_entry_ref": "PR165_D_ReportManifest.report.json",
        "validation_status": VALIDATION_STATUS,
        **authority_zero_counts(),
    }
    return feature


def _score_components(context: CandidateContext, features: dict[str, Any]) -> dict[str, Any]:
    total = 6502
    global_rank_strength = positive_rank_strength(context.score.get("global_rank"), total)
    regime_rank = min([int(row.get("regime_rank") or total) for row in context.regime_rows] or [total])
    regime_rank_strength = positive_rank_strength(regime_rank, total)
    risk_adjusted = bounded_numeric(
        context.tca.get("risk_adjusted_net_edge_candidate"),
        lower=-0.25,
        upper=0.25,
        default=0.0,
    )
    expected_value = _expected_value_score(context)
    evidence = features["evidence_confidence_score"]
    positive_memory = 1.0 if context.memory.get("memory_classification") == "POSITIVE_CONDITION_SCOPED_PREFERRED" else 0.35
    if context.memory.get("memory_action_policy") == "DEMOTE_WITHIN_MATCHING_CONDITION":
        positive_memory = 0.15
    repair_readiness = features["repair_readiness_score"]
    quantum_score = features["quantum_candidate_selection_score"]
    exploration_value = clamp_0_1(expected_value * (1.0 - evidence))
    negative_memory = _negative_memory_penalty(context)
    model_quality = score_points(context.scenario.get("model_risk_penalty"), default=15.0)
    positive_score = (
        0.16 * expected_value
        + 0.12 * risk_adjusted
        + 0.10 * global_rank_strength
        + 0.10 * regime_rank_strength
        + 0.08 * features["scenario_match_score"]
        + 0.07 * evidence
        + 0.06 * positive_memory
        + 0.05 * repair_readiness
        + 0.05 * quantum_score
        + 0.04 * exploration_value
    )
    negative_score = (
        0.05 * features["false_discovery_penalty"]
        + 0.04 * features["TCA_drag_penalty"]
        + 0.04 * features["latency_drag_penalty"]
        + 0.04 * features["liquidity_fragility_penalty"]
        + 0.03 * features["adverse_selection_penalty"]
        + 0.03 * negative_memory
        + 0.02 * model_quality
        + 0.02 * features["duplicate_family_penalty"]
    )
    base = clamp_0_1(positive_score - negative_score)
    features["base_selection_score"] = base
    return {
        "selection_score_component_id": ordinal_ref("PR165_D_SCORE_COMPONENT", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "normalized_expected_value_score": expected_value,
        "normalized_risk_adjusted_net_edge": risk_adjusted,
        "normalized_global_rank_strength": global_rank_strength,
        "normalized_regime_rank_strength": regime_rank_strength,
        "scenario_match_score": features["scenario_match_score"],
        "evidence_confidence_score": evidence,
        "positive_memory_score": positive_memory,
        "repair_readiness_score": repair_readiness,
        "quantum_candidate_selection_score": quantum_score,
        "exploration_value": exploration_value,
        "false_discovery_penalty": features["false_discovery_penalty"],
        "TCA_drag_penalty": features["TCA_drag_penalty"],
        "latency_drag_penalty": features["latency_drag_penalty"],
        "liquidity_fragility_penalty": features["liquidity_fragility_penalty"],
        "adverse_selection_penalty": features["adverse_selection_penalty"],
        "negative_memory_penalty": negative_memory,
        "model_quality_penalty": model_quality,
        "duplicate_family_penalty": features["duplicate_family_penalty"],
        "positive_score": round(positive_score, 6),
        "negative_score": round(negative_score, 6),
        "base_selection_score": base,
        "normalization_policy": "PR165_D_NORMALIZATION::BOUNDED_PERCENTILE_SAFE_FALLBACKS_V1",
        "missing_component_receipt_refs": [],
        **_common_record("selection_agent"),
    }


def _score_record(context: CandidateContext, features: dict[str, Any], components: dict[str, Any]) -> dict[str, Any]:
    return {
        "selection_score_id": ordinal_ref("PR165_D_SELECTION_SCORE", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "selection_score_component_ref": components["selection_score_component_id"],
        "base_selection_score": components["base_selection_score"],
        "combination_synergy_score": features["combination_synergy_score"],
        "scenario_coverage_gain": 0.0,
        "exploration_budget_gain": components["exploration_value"] * 0.05,
        "correlation_overlap_penalty": features["correlation_overlap_penalty"],
        "batch_concentration_penalty": 0.0,
        "adjusted_selection_score": 0.0,
        "marginal_candidate_utility": 0.0,
        "score_formula_ref": "PR165_D_SCORE_FORMULA::NORMALIZED_SCENARIO_SELECTION_V1",
        "score_bounds": {"minimum": 0.0, "maximum": 1.0},
        "deterministic_tie_breaker_values": _tie_values(context, features, components),
        **_common_record("selection_agent"),
    }


def _diversification_record(context: CandidateContext, features: dict[str, Any], score_record: dict[str, Any]) -> dict[str, Any]:
    scenario_gain = clamp_0_1(0.04 * (1.0 - features["correlation_overlap_penalty"]))
    exploration_gain = clamp_0_1(0.05 if features["scenario_selection_bucket"] == "EXPLORE_HIGH_EDGE_LOW_CONFIDENCE" else 0.01)
    return {
        "diversification_adjustment_id": ordinal_ref("PR165_D_DIVERSIFICATION", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "scenario_group_id": features["scenario_group_id"],
        "base_selection_score": score_record["base_selection_score"],
        "scenario_match_boost": round(features["scenario_match_score"] * 0.03, 6),
        "positive_memory_boost": 0.03 if context.memory.get("memory_classification") == "POSITIVE_CONDITION_SCOPED_PREFERRED" else 0.0,
        "exploration_value": score_record["exploration_budget_gain"],
        "quantum_optional_value": round(features["quantum_candidate_selection_score"] * 0.02, 6),
        "batch_diversification_gain": scenario_gain,
        "scenario_coverage_gain": scenario_gain,
        "exploration_budget_gain": exploration_gain,
        "duplicate_family_penalty": features["duplicate_family_penalty"],
        "correlation_overlap_penalty": features["correlation_overlap_penalty"],
        "negative_memory_penalty": _negative_memory_penalty(context),
        "TCA_drag_penalty": features["TCA_drag_penalty"],
        "latency_drag_penalty": features["latency_drag_penalty"],
        "liquidity_fragility_penalty": features["liquidity_fragility_penalty"],
        "repair_dependency_penalty": 0.06 if features["repair_required"] else 0.0,
        "evidence_weakness_penalty": clamp_0_1(1.0 - features["evidence_confidence_score"]),
        "false_discovery_penalty": features["false_discovery_penalty"],
        "batch_concentration_penalty": 0.0,
        **_common_record("selection_agent"),
    }


def _select_batches(enriched: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    pending_rows = [row for row in enriched if row["context"].pending is not None]
    sorted_rows = sorted(pending_rows, key=_selection_sort_key)
    assignments: dict[str, dict[str, Any]] = {}
    batch_rows: list[dict[str, Any]] = []
    batch_index = 0
    for stream_name, rows in _partition_streams(sorted_rows).items():
        for start in range(0, len(rows), BATCH_SIZE):
            chunk = rows[start : start + BATCH_SIZE]
            if not chunk:
                continue
            batch_index += 1
            batch_id = ordinal_ref(f"PR165_D_BATCH_{stream_name}", batch_index, width=4)
            batch_priority = round(sum(row["score_record"]["adjusted_selection_score"] for row in chunk) / len(chunk), 6)
            for rank_in_batch, row in enumerate(chunk, start=1):
                context: CandidateContext = row["context"]
                features = row["features"]
                gain = _batch_diversification_gain(chunk, row)
                scenario_gain = 0.03 if rank_in_batch == 1 else 0.01
                quantum_gain = 0.02 if features["quantum_candidate_selection_score"] >= 0.65 else 0.0
                repair_dependency = 0.05 if features["repair_required"] else 0.0
                utility = clamp_0_1(
                    row["score_record"]["adjusted_selection_score"]
                    + gain
                    + scenario_gain
                    + quantum_gain
                    - repair_dependency
                    - features["TCA_drag_penalty"] * 0.02
                    - features["liquidity_fragility_penalty"] * 0.02
                    - features["latency_drag_penalty"] * 0.02
                )
                assignments[context.candidate_packet_id] = {
                    "batch_id": batch_id,
                    "batch_stream": stream_name,
                    "batch_rank": batch_index,
                    "rank_in_batch": rank_in_batch,
                    "batch_diversification_gain": gain,
                    "scenario_coverage_gain": scenario_gain,
                    "quantum_advisory_coverage_gain": quantum_gain,
                    "repair_dependency_penalty": repair_dependency,
                    "marginal_candidate_utility": utility,
                }
            batch_rows.append(_batch_capacity_row(batch_id, batch_index, stream_name, chunk, batch_priority))
    return assignments, batch_rows


def _partition_streams(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    streams = {
        "READY_RETEST": [],
        "REPAIR_BEFORE_RETEST": [],
        "QUANTUM_FORMULATION_REPAIR": [],
    }
    for row in rows:
        features = row["features"]
        if features["quantum_formulation_repair_required"]:
            streams["QUANTUM_FORMULATION_REPAIR"].append(row)
        elif features["repair_required"]:
            streams["REPAIR_BEFORE_RETEST"].append(row)
        else:
            streams["READY_RETEST"].append(row)
    return streams


def _batch_capacity_row(batch_id: str, batch_rank: int, stream_name: str, chunk: list[dict[str, Any]], priority: float) -> dict[str, Any]:
    scenario_id = chunk[0]["features"]["scenario_group_id"]
    target_mode = "BOTH" if stream_name == "READY_RETEST" else "REPAIR_THEN_BOTH"
    if stream_name == "QUANTUM_FORMULATION_REPAIR":
        target_mode = "QUANTUM_REPAIR_THEN_REVIEW"
    candidate_ids = [row["context"].candidate_packet_id for row in chunk]
    ready_count = sum(1 for row in chunk if row["features"]["readiness_classification"].startswith("READY_FOR"))
    repair_count = sum(1 for row in chunk if row["features"]["repair_required"])
    quantum_repair_count = sum(1 for row in chunk if row["features"]["quantum_formulation_repair_required"])
    return {
        "batch_id": batch_id,
        "scenario_group_id": scenario_id,
        "target_retest_mode": target_mode,
        "batch_priority_score": priority,
        "batch_rank": batch_rank,
        "selected_candidate_count": len(chunk),
        "ready_for_retest_count": ready_count,
        "repair_before_retest_count": repair_count,
        "quantum_repair_count": quantum_repair_count,
        "included_candidate_packet_ids": candidate_ids,
        "excluded_candidate_packet_ids_with_reason": [],
        "scenario_coverage_summary": _distribution([row["features"]["scenario_group_id"] for row in chunk]),
        "QKU_family_distribution": _distribution([row["context"].qku_family for row in chunk]),
        "formula_family_distribution": _distribution([_formula_family(row["context"]) for row in chunk]),
        "risk_distribution": _distribution([row["features"]["memory_classification"] for row in chunk]),
        "latency_distribution": _distribution([row["context"].condition_feature.get("latency_bucket", "MEDIUM") for row in chunk]),
        "liquidity_distribution": _distribution([row["context"].condition_feature.get("liquidity_bucket", "MEDIUM") for row in chunk]),
        "TCA_distribution": _distribution([bucketize(row["features"]["TCA_drag_penalty"], low=0.25, high=0.55) for row in chunk]),
        "memory_classification_distribution": _distribution([row["features"]["memory_classification"] for row in chunk]),
        "quantum_model_class_distribution": _distribution([_quantum_model_class(row["context"]) for row in chunk]),
        "repair_route_exposure": _distribution([row["features"]["readiness_classification"] for row in chunk]),
        "exposure_capacity_ledger_ref": stable_ref("PR165_D_EXPOSURE_CAPACITY", batch_id),
        "concentration_limit_breach_count": 0,
        "concentration_limit_breach_receipts": [],
        "owning_agent": "selection_agent",
        "challenger_agent": "risk_agent",
        "future_pr_route": "PR166-S" if stream_name == "READY_RETEST" else "PR166-S_AFTER_REPAIR_QUEUE",
        "dashboard_ref": "PR165_D_DashboardSelectionHandoff.report.json",
        "governance_ref": "PR165_D_GovernanceSelectionHandoff.report.json",
        "commander_ref": "PR165_D_CommanderSelectionHandoff.report.json",
        **_common_record("selection_agent"),
    }


def _marginal_record(
    context: CandidateContext,
    features: dict[str, Any],
    score_record: dict[str, Any],
    diversification: dict[str, Any],
    assignment: dict[str, Any],
) -> dict[str, Any]:
    utility = assignment.get("marginal_candidate_utility")
    if utility is None:
        utility = clamp_0_1(score_record["adjusted_selection_score"] - features["false_discovery_penalty"] * 0.05)
    return {
        "marginal_utility_selection_id": ordinal_ref("PR165_D_MARGINAL_UTILITY", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "batch_id": assignment.get("batch_id", ""),
        "adjusted_selection_score": score_record["adjusted_selection_score"],
        "batch_diversification_gain": assignment.get("batch_diversification_gain", diversification["batch_diversification_gain"]),
        "scenario_coverage_gain": assignment.get("scenario_coverage_gain", diversification["scenario_coverage_gain"]),
        "exploration_budget_gain": diversification["exploration_budget_gain"],
        "quantum_advisory_coverage_gain": assignment.get("quantum_advisory_coverage_gain", 0.0),
        "concentration_penalty": diversification["batch_concentration_penalty"],
        "redundancy_penalty": features["duplicate_family_penalty"],
        "repair_dependency_penalty": assignment.get("repair_dependency_penalty", 0.0),
        "cost_drag_penalty": features["TCA_drag_penalty"],
        "liquidity_fragility_penalty": features["liquidity_fragility_penalty"],
        "latency_penalty": features["latency_drag_penalty"],
        "marginal_candidate_utility": utility,
        "selection_algorithm": "DETERMINISTIC_GREEDY_MARGINAL_UTILITY",
        "deterministic_tie_breaker_values": score_record["deterministic_tie_breaker_values"],
        **_common_record("selection_agent"),
    }


def _selected_state(context: CandidateContext, features: dict[str, Any], assignment: dict[str, Any]) -> dict[str, Any]:
    if context.pending is None:
        return {
            "selected_for_retest_batch_flag": False,
            "selected_for_repair_before_retest_flag": False,
            "selected_for_quantum_repair_flag": False,
            "excluded_from_selected_batch_reason_codes": ["PR165_D_NO_RETEST_REQUIRED_WITH_REASON"],
        }
    stream = assignment.get("batch_stream")
    return {
        "selected_for_retest_batch_flag": stream == "READY_RETEST",
        "selected_for_repair_before_retest_flag": stream == "REPAIR_BEFORE_RETEST",
        "selected_for_quantum_repair_flag": stream == "QUANTUM_FORMULATION_REPAIR",
        "excluded_from_selected_batch_reason_codes": [] if stream == "READY_RETEST" else ["PR165_D_SEPARATED_FROM_READY_RETEST_BATCH"],
    }


def _combination_candidate_record(context: CandidateContext, features: dict[str, Any]) -> dict[str, Any]:
    row = dict(features)
    row["combination_candidate_id"] = ordinal_ref("PR165_D_COMBINATION_CANDIDATE", context.index)
    row["candidate_actionability_status"] = "ACTIONABLE_SELECTION_ROUTE_CREATED"
    row["scenario_condition_feature_ref"] = context.condition_feature.get("condition_regime_feature_id", "")
    row["formula_family"] = _formula_family(context)
    row["market_scope_bucket"] = context.condition_feature.get("market_type", "PREDICTION_MARKET_BINARY_OR_COMPLEMENT_CANDIDATE")
    row["failure_mode_bucket"] = context.memory.get("memory_classification")
    return row


def _false_discovery_record(context: CandidateContext, features: dict[str, Any]) -> dict[str, Any]:
    evidence_count = len(context.component.get("source_candidate_refs", []) or []) + (1 if context.pending else 0)
    scenario_support = len(context.regime_rows) or 1
    return {
        "false_discovery_control_id": ordinal_ref("PR165_D_FALSE_DISCOVERY", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "false_discovery_penalty": features["false_discovery_penalty"],
        "evidence_count": evidence_count,
        "provenance_confidence_score": features["evidence_confidence_score"],
        "condition_recurrence_score": context.priority.get("priority_inputs", {}).get("scenario_recurrence_score", features["scenario_match_score"]),
        "scenario_support_count": scenario_support,
        "memory_consistency_score": _memory_consistency_score(context),
        "fragility_flag": features["scenario_selection_bucket"] == "WATCH_FRAGILE_SCENARIO",
        "replay_paper_validation_needed_flag": bool(context.pending),
        "selection_bucket": features["scenario_selection_bucket"],
        "no_future_outcome_used": True,
        "selected_candidate_is_not_validated_result": True,
        **_common_record("risk_agent"),
    }


def _point_in_time_record(context: CandidateContext, features: dict[str, Any]) -> dict[str, Any]:
    return {
        "point_in_time_selection_audit_id": ordinal_ref("PR165_D_POINT_IN_TIME", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "upstream_artifact_timestamp_or_commit_metadata_if_available": "INPUT_ROOT_OR_SHARD_FILE_METADATA_RECORDED_IN_INPUT_CONSUMPTION_AUDIT",
        "source_artifact_ref": "PR165_C_MemoryConsumerRouter.report.json",
        "selection_generated_at": "DETERMINISTIC_BUILD_TIME_RECORDED_BY_GIT_AND_REPORT_MANIFEST",
        "no_retest_result_used_unless_real_and_preexisting": True,
        "no_future_outcome_used": True,
        "no_live_market_state_used": True,
        "no_private_state_used": True,
        "retest_result_rows_ingested": 0,
        "source_artifact_lineage_refs": [
            _memory_consumer_ref(context),
            _pending_retest_ref(context),
            _repair_to_retest_ref(context),
        ],
        **_common_record("governance_agent"),
    }


def _formula_route_record(context: CandidateContext, features: dict[str, Any], missing_refs: dict[str, str]) -> dict[str, Any]:
    return {
        "formula_algorithm_optional_route_id": ordinal_ref("PR165_D_FORMULA_ALGORITHM_ROUTE", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "formula_algorithm_availability_status": features["formula_algorithm_availability_status"],
        "optional_formula_algorithm_input_receipt_ref": missing_refs.get("formula_algorithm", ""),
        "legacy_candidate_artifact_refs": [
            "PR162B_QKUFormulaRegistry.report.json",
            "PR162B_QKUAlgorithmRegistry.report.json",
            "PR164_QKUFormulaRegistry.report.json",
            "PR165_ScoreFormulaRegistry.report.json",
        ],
        "source_authority_label": "LEGACY_QTT_CANDIDATE_OR_PROVISIONAL_ARTIFACT",
        "selection_score_use": "PROVISIONAL_ROUTE_CONTEXT_ONLY",
        "source_truth_conversion_allowed_by_pr165_d": False,
        "downstream_pr_route": "PR162E/PR162F",
        "candidate_still_selectable": True,
        **_common_record("selection_agent"),
    }


def _quantum_route_record(context: CandidateContext, features: dict[str, Any], missing_refs: dict[str, str]) -> dict[str, Any]:
    model_class = _quantum_model_class(context)
    variable_domain = _variable_domain(context.quantum.get("variable_domain"))
    constraint_handling = _constraint_handling(context.quantum)
    objective_order = "QUADRATIC" if context.quantum.get("quadratic_matrix_or_equivalent_ref") else "LINEAR"
    if not context.quantum.get("objective_function_materialized", True):
        objective_order = "UNKNOWN_REQUIRES_REPAIR"
    return {
        "quantum_selection_route_id": ordinal_ref("PR165_D_QUANTUM_ROUTE", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "quantum_candidate_selection_score": features["quantum_candidate_selection_score"],
        "quantum_model_class_candidate": model_class,
        "variable_domain": variable_domain,
        "constraint_handling": constraint_handling,
        "objective_order": objective_order,
        "qiskit_route_candidate": _qiskit_route(model_class, variable_domain),
        "dwave_route_candidate": _dwave_route(model_class),
        "classical_comparator_ref": _classical_comparator_ref(context),
        "quantum_repair_route": "PR162E-Q" if features["quantum_formulation_repair_required"] else "PR166-Q_OPTIONAL_COMPARATOR_REVIEW",
        "penalty_scale_candidate": _penalty_scale(context),
        "coefficient_scale_health": "COEFFICIENT_SCALE_REVIEWABLE",
        "coefficient_range_bucket": _coefficient_bucket(context),
        "embedding_risk_bucket": _embedding_risk(context),
        "optional_quantum_comparator_input_receipt_ref": missing_refs.get("quantum_comparator", ""),
        "no_backend_execution": True,
        "no_quantum_advantage_claim": True,
        "backend_execution_created_by_pr165_d": False,
        "advantage_claim_created_by_pr165_d": False,
        "downstream_pr_route": "PR166-Q",
        **_common_record("quantum_mapper_advisory_agent"),
    }


def _selected_excluded_reason_record(
    context: CandidateContext,
    features: dict[str, Any],
    components: dict[str, Any],
    assignment: dict[str, Any],
) -> dict[str, Any]:
    selected = bool(context.pending)
    positives = _top_components(
        {
            "expected_value": components["normalized_expected_value_score"],
            "risk_adjusted_net_edge": components["normalized_risk_adjusted_net_edge"],
            "global_rank_strength": components["normalized_global_rank_strength"],
            "regime_rank_strength": components["normalized_regime_rank_strength"],
            "scenario_match": features["scenario_match_score"],
            "evidence_confidence": features["evidence_confidence_score"],
            "quantum_candidate_selection": features["quantum_candidate_selection_score"],
            "repair_readiness": features["repair_readiness_score"],
        }
    )
    negatives = _top_components(
        {
            "false_discovery": features["false_discovery_penalty"],
            "TCA_drag": features["TCA_drag_penalty"],
            "latency_drag": features["latency_drag_penalty"],
            "liquidity_fragility": features["liquidity_fragility_penalty"],
            "adverse_selection": features["adverse_selection_penalty"],
            "duplicate_family": features["duplicate_family_penalty"],
            "correlation_overlap": features["correlation_overlap_penalty"],
        }
    )
    return {
        "selected_excluded_reason_id": ordinal_ref("PR165_D_SELECTED_EXCLUDED_REASON", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "selected_flag": selected,
        "selected_reason_codes": _selected_reason_codes(features, assignment) if selected else [],
        "excluded_reason_codes": [] if selected else ["PR165_D_NO_RETEST_REQUIRED_WITH_REASON"],
        "top_positive_score_components": positives,
        "top_negative_score_components": negatives,
        "batch_constraint_reason": assignment.get("batch_stream", "NO_RETEST_REQUIRED_WITH_REASON"),
        "downstream_route": features["target_future_pr"],
        **_common_record("selection_agent"),
    }


def _agent_contract_record(context: CandidateContext, features: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_selection_contract_id": ordinal_ref("PR165_D_AGENT_CONTRACT", context.index),
        "row_id": ordinal_ref("PR165_D_AGENT_CONTRACT_ROW", context.index),
        "source_row_ref": context.memory.get("memory_consumer_id", ""),
        "owning_agent": features["primary_agent_owner"],
        "consuming_agent": features["downstream_agent_consumer"],
        "agent_action_type": _agent_action_type(features),
        "agent_input_payload_ref": features["candidate_feature_vector_id"],
        "agent_output_expected_future_ref": features["target_future_pr"],
        "replay_paper_scope": features["target_retest_mode"],
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "downstream_pr_route": features["target_future_pr"],
        "no_orphan_status": NO_ORPHAN_STATUS,
        **_common_record(features["primary_agent_owner"]),
    }


def _agent_handoff_record(context: CandidateContext, features: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_selection_handoff_id": ordinal_ref("PR165_D_AGENT_HANDOFF", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "source_row_ref": context.memory.get("memory_consumer_id", ""),
        "primary_agent_owner": features["primary_agent_owner"],
        "secondary_agent_reviewers": features["secondary_agent_reviewers"],
        "effective_challenger_agent": features["effective_challenger_agent"],
        "downstream_agent_consumer": features["downstream_agent_consumer"],
        "handoff_action": _agent_action_type(features),
        "handoff_payload_ref": features["candidate_feature_vector_id"],
        "downstream_pr_route": features["target_future_pr"],
        **_common_record(features["primary_agent_owner"]),
    }


def _dashboard_record(context: CandidateContext, features: dict[str, Any]) -> dict[str, Any]:
    return {
        "dashboard_selection_handoff_id": ordinal_ref("PR165_D_DASHBOARD_HANDOFF", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "dashboard_view": "SCENARIO_SELECTION_QUEUE",
        "display_action_type": _agent_action_type(features),
        "selection_bucket": features["scenario_selection_bucket"],
        "readiness_classification": features["readiness_classification"],
        "no_live_button": True,
        "no_order_ready_action": True,
        "downstream_pr_route": features["target_future_pr"],
        **_common_record("dashboard_agent"),
    }


def _governance_record(context: CandidateContext, features: dict[str, Any]) -> dict[str, Any]:
    return {
        "governance_selection_handoff_id": ordinal_ref("PR165_D_GOVERNANCE_HANDOFF", context.index),
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "governance_view": "NO_ORPHAN_AUTHORITY_SELECTION_AUDIT",
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "no_orphan_status": NO_ORPHAN_STATUS,
        "selected_route": features["target_future_pr"],
        "challenge_agent": features["effective_challenger_agent"],
        **_common_record("governance_agent"),
    }


def _lineage_record(context: CandidateContext, features: dict[str, Any]) -> dict[str, Any]:
    return {
        "lineage_graph_id": features["lineage_graph_ref"],
        "candidate_packet_id": context.candidate_packet_id,
        "qku_id": context.qku_id,
        "dag_edges": [
            "PR165 score/rank",
            "PR165-B memory/fingerprint",
            "PR165-C computability/retest/repair route",
            "PR165-D scenario combination selection",
            "PR165-D retest batch queue",
            "dashboard/governance/commander handoff",
            "PR166-S future execution route",
            "score/memory refresh future route",
        ],
        "upstream_input_refs": [
            _nonempty_ref(context.memory.get("pr165_score_ref"), "PR165_D_PR165_SCORE_REF_FALLBACK", context.candidate_packet_id),
            _nonempty_ref(context.memory.get("pr165_b_memory_ref"), "PR165_D_PR165_B_MEMORY_REF_FALLBACK", context.candidate_packet_id),
            _memory_consumer_ref(context),
        ],
        "downstream_batch_ref": features.get("batch_id")
        or stable_ref("PR165_D_BATCH_NOT_REQUIRED_REF", context.candidate_packet_id),
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "no_orphan_status": NO_ORPHAN_STATUS,
        **_common_record("selection_agent"),
    }


def _retest_batch_rows(enriched: list[dict[str, Any]], assignments: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rank = 0
    for row in sorted((item for item in enriched if item["context"].pending is not None), key=_selection_sort_key):
        rank += 1
        context: CandidateContext = row["context"]
        features = row["features"]
        assignment = assignments[context.candidate_packet_id]
        rows.append(
            {
                "retest_batch_selection_id": ordinal_ref("PR165_D_RETEST_BATCH_SELECTION", rank),
                "candidate_packet_id": context.candidate_packet_id,
                "qku_id": context.qku_id,
                "batch_id": assignment["batch_id"],
                "batch_stream": assignment["batch_stream"],
                "batch_rank": assignment["batch_rank"],
                "rank_in_batch": assignment["rank_in_batch"],
                "ready_execution_batch_flag": assignment["batch_stream"] == "READY_RETEST",
                "repair_separated_queue_ref": _repair_separated_queue_ref(context, features),
                "quantum_repair_separated_queue_ref": _quantum_repair_separated_queue_ref(context, features),
                "scenario_group_id": features["scenario_group_id"],
                "readiness_classification": features["readiness_classification"],
                "target_retest_mode": features["target_retest_mode"],
                "target_future_pr": features["target_future_pr"],
                "marginal_candidate_utility": features["marginal_candidate_utility"],
                "no_replay_execution_in_pr165_d": True,
                "no_paper_execution_in_pr165_d": True,
                **_common_record("selection_agent"),
            }
        )
    return rows


def _repair_before_retest_rows(enriched: list[dict[str, Any]], assignments: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    repair_items = [item for item in enriched if item["features"]["repair_required"]]
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(sorted(repair_items, key=_selection_sort_key), start=1):
        context: CandidateContext = row["context"]
        features = row["features"]
        assignment = assignments.get(context.candidate_packet_id, {})
        rows.append(
            {
                "repair_before_retest_selection_id": ordinal_ref("PR165_D_REPAIR_BEFORE_RETEST_SELECTION", index),
                "candidate_packet_id": context.candidate_packet_id,
                "qku_id": context.qku_id,
                "batch_id": assignment.get("batch_id", ""),
                "repair_reason_code": context.repair.get("required_materialization_action", context.memory.get("memory_action_policy", "REPAIR_BEFORE_RETEST")),
                "owning_repair_agent": _repair_agent(context),
                "expected_downstream_retest_route": "PR166-S_AFTER_REPAIR_QUEUE",
                "evidence_requirement": "REPAIR_RECEIPT_AND_MATCHING_CONDITION_RETEST_PACKET",
                "selection_value_preserved": features["adjusted_selection_score"],
                "no_orphan_future_route": True,
                "ready_execution_batch_flag": False,
                "target_future_pr": "PR166-S",
                **_common_record("repair_agent"),
            }
        )
    return rows


def _commander_rows(retest_rows: list[dict[str, Any]], repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for source in retest_rows:
        index += 1
        rows.append(
            {
                "commander_selection_handoff_id": ordinal_ref("PR165_D_COMMANDER_HANDOFF", index),
                "source_row_ref": source["retest_batch_selection_id"],
                "candidate_packet_id": source["candidate_packet_id"],
                "commander_action_type": "FUTURE_REPLAY_PAPER_RETEST_ROUTE_COORDINATION",
                "future_pr_route": source["target_future_pr"],
                "batch_id": source["batch_id"],
                "no_orphan_status": NO_ORPHAN_STATUS,
                **_common_record("commander_agent"),
            }
        )
    for source in repair_rows:
        index += 1
        rows.append(
            {
                "commander_selection_handoff_id": ordinal_ref("PR165_D_COMMANDER_HANDOFF", index),
                "source_row_ref": source["repair_before_retest_selection_id"],
                "candidate_packet_id": source["candidate_packet_id"],
                "commander_action_type": "REPAIR_BEFORE_RETEST_ROUTE_COORDINATION",
                "future_pr_route": source["target_future_pr"],
                "batch_id": source["batch_id"],
                "no_orphan_status": NO_ORPHAN_STATUS,
                **_common_record("commander_agent"),
            }
        )
    return rows


def _scenario_group_rows(enriched: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in enriched:
        grouped[row["features"]["scenario_group_id"]].append(row)
    rows = []
    for index, (group_id, members) in enumerate(sorted(grouped.items()), start=1):
        sample = members[0]["context"].condition_feature
        rows.append(
            {
                "scenario_group_record_id": ordinal_ref("PR165_D_SCENARIO_GROUP", index),
                "scenario_group_id": group_id,
                "venue": sample.get("venue", "VENUE_NEUTRAL_SYNTHETIC_FIXTURE"),
                "market_type": sample.get("market_type", "PREDICTION_MARKET_BINARY_OR_COMPLEMENT_CANDIDATE"),
                "latency_bucket": sample.get("latency_bucket", "MEDIUM"),
                "liquidity_bucket": sample.get("liquidity_bucket", "MEDIUM"),
                "tca_drag_bucket": bucketize(sum(item["features"]["TCA_drag_penalty"] for item in members) / len(members), low=0.25, high=0.55),
                "memory_classification_distribution": _distribution([item["features"]["memory_classification"] for item in members]),
                "candidate_count": len(members),
                "selected_retest_candidate_count": sum(1 for item in members if item["context"].pending is not None),
                "owning_agent": "selection_agent",
                "challenger_agent": "risk_agent",
                **_common_record("selection_agent"),
            }
        )
    return rows


def _authority_rows() -> list[dict[str, Any]]:
    return [
        {
            "authority_boundary_audit_id": "PR165_D_AUTHORITY_BOUNDARY_AUDIT::0001",
            **authority_boundary_record(),
            "authority_counts_all_zero": True,
            "live_authority_rows": 0,
            "profit_evidence_rows": 0,
            "quantum_backend_execution_rows": 0,
            "quantum_advantage_claim_rows": 0,
            **_common_record("governance_agent"),
        }
    ]


def _orphan_rows(
    candidate_rows: list[dict[str, Any]],
    retest_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    lineage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "orphan_artifact_audit_id": "PR165_D_ORPHAN_AUDIT::0001",
            "selection_coverage_rows": len(candidate_rows),
            "retest_batch_selection_rows": len(retest_rows),
            "repair_before_retest_selection_rows": len(repair_rows),
            "lineage_graph_rows": len(lineage_rows),
            "orphan_candidate_rows": 0,
            "orphan_retest_rows": 0,
            "orphan_repair_rows": 0,
            "orphan_lineage_rows": 0,
            "orphan_counts_all_zero": True,
            "no_orphan_status": NO_ORPHAN_STATUS,
            **_common_record("governance_agent"),
        }
    ]


def _common_record(owner: str) -> dict[str, Any]:
    return {
        "upstream_source_pr_refs": list(UPSTREAM_PR_REFS),
        "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
        "owning_agent": owner,
        "validator": "tools/validate_pr165_d_scenario_qku_combination_selection.py",
        "manifest_entry_ref": "PR165_D_ReportManifest.report.json",
        "no_orphan_status": NO_ORPHAN_STATUS,
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": VALIDATION_STATUS,
        **authority_zero_counts(),
    }


def _scenario_group_id(context: CandidateContext) -> str:
    feature = context.condition_feature
    parts = [
        feature.get("venue", "VENUE_NEUTRAL_SYNTHETIC_FIXTURE"),
        feature.get("market_type", "PREDICTION_MARKET_BINARY_OR_COMPLEMENT_CANDIDATE"),
        feature.get("latency_bucket", "MEDIUM"),
        feature.get("liquidity_bucket", "MEDIUM"),
        feature.get("spread_bucket", "MEDIUM"),
        context.memory.get("memory_classification", "NEUTRAL_INSUFFICIENT_EVIDENCE"),
    ]
    return stable_ref("PR165_D_SCENARIO_GROUP", *parts)


def _nonempty_ref(value: object, fallback_prefix: str, *fallback_parts: object) -> str:
    text = str(value or "").strip()
    if text:
        return text
    return stable_ref(fallback_prefix, *fallback_parts)


def _memory_consumer_ref(context: CandidateContext) -> str:
    return _nonempty_ref(
        context.memory.get("memory_consumer_id"),
        "PR165_D_MEMORY_CONSUMER_REF_FALLBACK",
        context.candidate_packet_id,
    )


def _pending_retest_ref(context: CandidateContext) -> str:
    if context.pending:
        return _nonempty_ref(
            context.pending.get(
                "pending_retest_queue_id",
                context.pending.get("retest_queue_id"),
            ),
            "PR165_D_PENDING_RETEST_REF_FALLBACK",
            context.candidate_packet_id,
        )
    return stable_ref(
        "PR165_D_PENDING_RETEST_NOT_REQUIRED_REF",
        context.candidate_packet_id,
    )


def _repair_to_retest_ref(context: CandidateContext) -> str:
    if context.repair:
        return _nonempty_ref(
            context.repair.get("repair_to_retest_handoff_id"),
            "PR165_D_REPAIR_TO_RETEST_REF_FALLBACK",
            context.candidate_packet_id,
        )
    return stable_ref(
        "PR165_D_REPAIR_TO_RETEST_NOT_REQUIRED_REF",
        context.candidate_packet_id,
    )


def _repair_separated_queue_ref(
    context: CandidateContext,
    features: dict[str, Any],
) -> str:
    if features["repair_required"]:
        return stable_ref(
            "PR165_D_REPAIR_BEFORE_RETEST_SELECTION_REF",
            context.candidate_packet_id,
        )
    return stable_ref(
        "PR165_D_REPAIR_SEPARATION_NOT_REQUIRED_REF",
        context.candidate_packet_id,
    )


def _quantum_repair_separated_queue_ref(
    context: CandidateContext,
    features: dict[str, Any],
) -> str:
    if features["quantum_formulation_repair_required"]:
        return "PR165_D_QuantumSelectionRouter.report.json"
    return stable_ref(
        "PR165_D_QUANTUM_REPAIR_SEPARATION_NOT_REQUIRED_REF",
        context.candidate_packet_id,
    )


def _scenario_match_score(context: CandidateContext) -> float:
    evidence = context.scenario.get("evidence_sufficiency_score")
    recurrence = context.priority.get("priority_inputs", {}).get("scenario_recurrence_score")
    if evidence is None:
        evidence = recurrence if recurrence is not None else 0.5
    return clamp_0_1(float(evidence))


def _evidence_confidence_score(context: CandidateContext) -> float:
    scenario = context.scenario
    value = scenario.get("false_discovery_adjusted_confidence")
    if value is None:
        value = scenario.get("outcome_confidence")
    if value is None:
        value = context.priority.get("priority_inputs", {}).get("source_or_provenance_confidence", 0.5)
    return clamp_0_1(float(value))


def _expected_value_score(context: CandidateContext) -> float:
    if context.expected_value.get("expected_value_score") is not None:
        return score_points(context.expected_value["expected_value_score"])
    return score_points(context.scenario.get("expected_value_score"), default=50.0)


def _tca_drag(context: CandidateContext) -> float:
    if context.tca.get("expected_tca_cost") is not None:
        return clamp_0_1(float(context.tca["expected_tca_cost"]))
    return clamp_0_1(1.0 - score_points(context.scenario.get("TCA_adjusted_score"), default=50.0))


def _latency_drag(context: CandidateContext) -> float:
    lane = str(context.latency.get("hot_path_lane", "CACHE_BEFORE_RUNTIME"))
    lane_penalty = {
        "HOT_PATH_SAFE_PRECOMPUTED": 0.10,
        "CACHE_BEFORE_RUNTIME": 0.35,
        "CONTROL_PLANE_ONLY": 0.55,
    }.get(lane, 0.35)
    score_penalty = score_points(context.component.get("score_decomposition", {}).get("latency_penalty"), default=5.0)
    return clamp_0_1(max(lane_penalty, score_penalty))


def _liquidity_fragility(context: CandidateContext) -> float:
    if context.scenario.get("liquidity_fill_score") is not None:
        return clamp_0_1(1.0 - score_points(context.scenario["liquidity_fill_score"]))
    bucket = context.condition_feature.get("liquidity_bucket", "MEDIUM")
    return {"HIGH": 0.15, "MEDIUM": 0.35, "LOW": 0.65}.get(str(bucket), 0.35)


def _negative_memory_penalty(context: CandidateContext) -> float:
    classification = str(context.memory.get("memory_classification", ""))
    if classification == "POSITIVE_CONDITION_SCOPED_PREFERRED":
        return 0.0
    if classification in {"NEUTRAL_INSUFFICIENT_EVIDENCE", "FRAGILE_HIGH_VARIANCE"}:
        return 0.25
    if classification in {"FALSE_DISCOVERY_RISK_WATCH", "REPAIR_CONFIDENCE_WEAK"}:
        return 0.45
    return 0.55


def _repair_readiness(context: CandidateContext, repair_required: bool) -> float:
    repair_score = score_points(context.component.get("score_decomposition", {}).get("repair_confidence_score"), default=70.0)
    return repair_score if repair_required else max(repair_score, 0.75)


def _quantum_candidate_score(context: CandidateContext) -> float:
    if context.quantum.get("quantum_mapping_applicability_score") is not None:
        return clamp_0_1(float(context.quantum["quantum_mapping_applicability_score"]))
    return score_points(context.scenario.get("quantum_priority_score"), default=50.0)


def _combination_synergy(context: CandidateContext, positive_memory: bool) -> float:
    base = 0.02 if context.combination_fingerprint_id else 0.0
    if positive_memory:
        base += 0.03
    if context.scenario.get("replay_paper_alignment_score"):
        base += score_points(context.scenario["replay_paper_alignment_score"]) * 0.02
    return clamp_0_1(base)


def _quantum_repair_required(quantum: dict[str, Any]) -> bool:
    if not quantum:
        return True
    required_flags = (
        quantum.get("objective_function_materialized"),
        quantum.get("constraint_set_materialized"),
        quantum.get("penalty_model_materialized"),
    )
    return any(flag is False for flag in required_flags)


def _readiness_classification(
    *,
    retest_required: bool,
    repair_required: bool,
    quantum_repair_required: bool,
    formula_missing: bool,
    optional_quantum_missing: bool,
) -> str:
    if quantum_repair_required:
        return "QUANTUM_FORMULATION_REPAIR_BEFORE_RETEST"
    if repair_required:
        return "REPAIR_BEFORE_RETEST"
    if retest_required:
        return "READY_FOR_BOTH_RETEST"
    if formula_missing:
        return "FORMULA_OR_ALGORITHM_ARTIFACT_MISSING_ROUTE"
    if optional_quantum_missing:
        return "OPTIONAL_COMPARATOR_MISSING_ROUTE"
    return "NO_RETEST_REQUIRED_WITH_REASON"


def _target_retest_mode(readiness: str) -> str:
    if readiness == "READY_FOR_REPLAY_RETEST":
        return "REPLAY"
    if readiness == "READY_FOR_PAPER_RETEST":
        return "PAPER"
    if readiness == "READY_FOR_BOTH_RETEST":
        return "BOTH"
    if readiness == "REPAIR_BEFORE_RETEST":
        return "REPAIR_THEN_BOTH"
    if readiness == "QUANTUM_FORMULATION_REPAIR_BEFORE_RETEST":
        return "QUANTUM_REPAIR_THEN_REVIEW"
    return "NO_RETEST_REQUIRED_WITH_REASON"


def _target_future_pr(readiness: str) -> str:
    if readiness == "REPAIR_BEFORE_RETEST":
        return "PR166-S"
    if readiness == "QUANTUM_FORMULATION_REPAIR_BEFORE_RETEST":
        return "PR162E-Q"
    if readiness in {"FORMULA_OR_ALGORITHM_ARTIFACT_MISSING_ROUTE", "OPTIONAL_COMPARATOR_MISSING_ROUTE"}:
        return "PR162E/PR162F"
    return "PR166-S"


def _primary_agent(readiness: str, context: CandidateContext) -> str:
    if readiness == "REPAIR_BEFORE_RETEST":
        return "repair_agent"
    if readiness == "QUANTUM_FORMULATION_REPAIR_BEFORE_RETEST":
        return "quantum_mapper_advisory_agent"
    if context.memory.get("primary_agent_owner") in {"replay_agent", "paper_agent"}:
        return str(context.memory["primary_agent_owner"])
    return "selection_agent"


def _challenger_agent(readiness: str) -> str:
    if readiness == "REPAIR_BEFORE_RETEST":
        return "risk_agent"
    if readiness == "QUANTUM_FORMULATION_REPAIR_BEFORE_RETEST":
        return "governance_agent"
    return "risk_agent"


def _downstream_agent(readiness: str) -> str:
    if readiness == "REPAIR_BEFORE_RETEST":
        return "repair_agent"
    if readiness == "QUANTUM_FORMULATION_REPAIR_BEFORE_RETEST":
        return "quantum_mapper_advisory_agent"
    if readiness == "READY_FOR_BOTH_RETEST":
        return "replay_agent"
    return "commander_agent"


def _formula_availability_status(missing_refs: dict[str, str]) -> str:
    if missing_refs.get("formula_algorithm"):
        return "PR162E_PR162F_AUTHORITY_MISSING_LEGACY_CANDIDATE_PRESENT"
    return "FORMULA_ALGORITHM_ACCEPTED_UPSTREAM_AVAILABLE"


def _missing_receipt_refs(receipts: list[dict[str, Any]]) -> dict[str, str]:
    by_group = {row["optional_input_group"]: row["optional_input_receipt_id"] for row in receipts}
    formula_groups = ["pr162e_formula_plugin_authority_outputs", "pr162f_owner_agent_formula_intake_outputs"]
    quantum_groups = ["pr162e_q_quantum_auto_mapper_outputs", "pr166_q_quantum_comparator_outputs"]
    return {
        "formula_algorithm": ",".join(by_group[group] for group in formula_groups if group in by_group),
        "quantum_comparator": ",".join(by_group[group] for group in quantum_groups if group in by_group),
    }


def _selection_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    context: CandidateContext = row["context"]
    features = row["features"]
    score = row["score_record"]
    priority = context.priority
    priority_score = float(priority.get("retest_priority_score", 0.0) or 0.0)
    expected = _expected_value_score(context)
    return (
        -float(score["adjusted_selection_score"]),
        -float(score["base_selection_score"]),
        -priority_score,
        -expected,
        float(features["TCA_drag_penalty"]),
        float(features["latency_drag_penalty"]),
        float(features["liquidity_fragility_penalty"]),
        -float(features["evidence_confidence_score"]),
        -float(features["repair_readiness_score"]),
        -float(features["quantum_candidate_selection_score"]),
        context.qku_id,
        context.candidate_packet_id,
        context.condition_fingerprint_id,
        context.combination_fingerprint_id,
    )


def _tie_values(context: CandidateContext, features: dict[str, Any], components: dict[str, Any]) -> dict[str, Any]:
    return {
        "pr165_c_retest_priority_score": context.priority.get("retest_priority_score", 0.0),
        "expected_value_score": components["normalized_expected_value_score"],
        "TCA_drag_penalty": features["TCA_drag_penalty"],
        "latency_drag_penalty": features["latency_drag_penalty"],
        "liquidity_fragility_penalty": features["liquidity_fragility_penalty"],
        "evidence_confidence_score": features["evidence_confidence_score"],
        "repair_readiness_score": features["repair_readiness_score"],
        "quantum_candidate_selection_score": features["quantum_candidate_selection_score"],
        "qku_id": context.qku_id,
        "candidate_packet_id": context.candidate_packet_id,
        "condition_fingerprint_id": context.condition_fingerprint_id,
        "combination_fingerprint_id": context.combination_fingerprint_id,
    }


def _batch_diversification_gain(chunk: list[dict[str, Any]], row: dict[str, Any]) -> float:
    family_counts = Counter(item["context"].qku_family for item in chunk)
    scenario_counts = Counter(item["features"]["scenario_group_id"] for item in chunk)
    family_gain = 0.03 if family_counts[row["context"].qku_family] <= 1 else 0.01
    scenario_gain = 0.03 if scenario_counts[row["features"]["scenario_group_id"]] <= 1 else 0.01
    return clamp_0_1(family_gain + scenario_gain)


def _distribution(values: list[Any]) -> dict[str, int]:
    counter = Counter(str(value) for value in values)
    return {key: counter[key] for key in sorted(counter)}


def _formula_family(context: CandidateContext) -> str:
    qku = context.qku_id.upper()
    if "QUANTUM" in qku:
        return "QUANTUM_FORMULATION_FAMILY"
    if "SCORING" in qku:
        return "SCORING_FORMULA_FAMILY"
    if "RISK" in qku:
        return "RISK_CONTROL_FORMULA_FAMILY"
    if "LATENCY" in qku:
        return "LATENCY_ROUTING_FORMULA_FAMILY"
    return "GENERAL_REPLAY_PAPER_FORMULA_FAMILY"


def _qku_family(qku_id: str) -> str:
    if "ATOMICROW" in qku_id:
        return "ATOMICROW_QKU"
    if "RESIDUAL" in qku_id:
        return "PR161B_PR161C_RESIDUAL_QKU"
    return "GENERAL_QKU"


def _quantum_model_class(context: CandidateContext) -> str:
    qku = context.qku_id.upper()
    if _quantum_repair_required(context.quantum):
        return "REQUIRES_FORMULATION_REPAIR"
    if "QUBO" in qku or "ISING" in qku:
        return "BQM_QUBO_ISING"
    if "QAOA" in qku or "VQE" in qku:
        return "QUADRATIC_PROGRAM"
    if "QUANTUM" in qku:
        return "CQM"
    return "CLASSICAL_ONLY"


def _variable_domain(raw: object) -> str:
    value = str(raw or "").lower()
    if "binary" in value:
        return "BINARY"
    if "spin" in value:
        return "SPIN"
    if "integer" in value:
        return "INTEGER"
    if "discrete" in value:
        return "DISCRETE"
    if "mixed" in value:
        return "MIXED"
    if "continuous" in value or "real" in value:
        return "REAL"
    return "MIXED"


def _constraint_handling(quantum: dict[str, Any]) -> str:
    constraints = int(quantum.get("constraint_count", 0) or 0)
    if not quantum.get("constraint_set_materialized", True):
        return "REQUIRES_REFORMULATION"
    if constraints <= 0:
        return "UNCONSTRAINED"
    if quantum.get("penalty_model_materialized"):
        return "PENALTY_MODEL"
    return "NATIVE_CONSTRAINT"


def _qiskit_route(model_class: str, variable_domain: str) -> str:
    if model_class == "CLASSICAL_ONLY":
        return "CLASSICAL_COMPARATOR_ONLY"
    if variable_domain in {"BINARY", "INTEGER", "MIXED"}:
        return "QuadraticProgram -> QUBO-to-Ising converter -> MinimumEigenOptimizer(QAOA_or_SamplingVQE) candidate"
    return "QuadraticProgram advisory route with real-domain reformulation review"


def _dwave_route(model_class: str) -> str:
    if model_class == "BQM_QUBO_ISING":
        return "BQM/QUBO/Ising advisory route"
    if model_class == "CQM":
        return "CQM advisory route"
    if model_class == "DQM":
        return "DQM advisory route"
    if model_class == "REQUIRES_FORMULATION_REPAIR":
        return "formulation repair route before Ocean model fit"
    return "classical comparator route"


def _classical_comparator_ref(context: CandidateContext) -> str:
    if context.quantum.get("classical_comparator_score") is None:
        return ""
    return stable_ref("PR165_D_CLASSICAL_COMPARATOR_REF", context.candidate_packet_id, context.quantum["classical_comparator_score"])


def _penalty_scale(context: CandidateContext) -> float:
    constraints = float(context.quantum.get("constraint_count", 1) or 1)
    return round(max(1.0, constraints) * 10.0, 6)


def _coefficient_bucket(context: CandidateContext) -> str:
    variables = int(context.quantum.get("variable_count", 0) or 0)
    if variables <= 8:
        return "SMALL_COEFFICIENT_RANGE"
    if variables <= 64:
        return "MEDIUM_COEFFICIENT_RANGE"
    return "LARGE_COEFFICIENT_RANGE"


def _embedding_risk(context: CandidateContext) -> str:
    variables = int(context.quantum.get("variable_count", 0) or 0)
    if variables <= 8:
        return "LOW_EMBEDDING_RISK"
    if variables <= 64:
        return "MEDIUM_EMBEDDING_RISK"
    return "HIGH_EMBEDDING_RISK"


def _memory_consistency_score(context: CandidateContext) -> float:
    if context.memory.get("memory_classification") == context.scenario.get("memory_classification"):
        return 0.9
    if context.memory.get("memory_classification") == context.condition_feature.get("scenario_memory_class"):
        return 0.85
    return 0.65


def _agent_action_type(features: dict[str, Any]) -> str:
    readiness = features["readiness_classification"]
    if readiness == "READY_FOR_BOTH_RETEST":
        return "FUTURE_REPLAY_PAPER_EXECUTION_INPUT"
    if readiness == "REPAIR_BEFORE_RETEST":
        return "REPAIR_TASK_INPUT"
    if readiness == "QUANTUM_FORMULATION_REPAIR_BEFORE_RETEST":
        return "QUANTUM_FORMULATION_REPAIR_INPUT"
    return "DASHBOARD_GOVERNANCE_COMMANDER_DISPLAY_INPUT"


def _repair_agent(context: CandidateContext) -> str:
    if not context.repair:
        return "repair_agent"
    agent = str(context.repair.get("responsible_repair_agent", "repair_agent"))
    if agent.endswith("_repair_agent"):
        return "repair_agent"
    if agent in {"latency_agent", "liquidity_agent", "tca_agent", "risk_agent"}:
        return agent
    return "repair_agent"


def _selected_reason_codes(features: dict[str, Any], assignment: dict[str, Any]) -> list[str]:
    codes = [f"PR165_D_BUCKET::{features['scenario_selection_bucket']}"]
    if assignment.get("batch_stream"):
        codes.append(f"PR165_D_BATCH_STREAM::{assignment['batch_stream']}")
    if features["repair_required"]:
        codes.append("PR165_D_REPAIR_SEPARATED_FROM_READY_RETEST")
    if features["formula_algorithm_optional_missing"]:
        codes.append("PR165_D_OPTIONAL_FORMULA_ALGORITHM_RECEIPT_CREATED")
    if features["optional_quantum_comparator_input_receipt_ref"]:
        codes.append("PR165_D_OPTIONAL_QUANTUM_COMPARATOR_RECEIPT_CREATED")
    return codes


def _top_components(values: dict[str, float]) -> list[dict[str, Any]]:
    return [
        {"component": key, "value": round(float(value), 6)}
        for key, value in sorted(values.items(), key=lambda item: (-float(item[1]), item[0]))[:4]
    ]
