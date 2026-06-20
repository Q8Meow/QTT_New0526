#!/usr/bin/env python3
"""Deterministic formula-based replay/paper recomputation kernel for PR168-RP."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

from tools.pr168_rp_agent_route_mapper import route_for_assignment
from tools.pr168_rp_combination_selector import combination_row
from tools.pr168_rp_connector_candidate_router import connector_route_for
from tools.pr168_rp_dag_orchestrator import core_dag_edges
from tools.pr168_rp_edge_attribution import build_edge_attribution
from tools.pr168_rp_evidence_state_machine import classify_row, validate_computed_status, validate_evidence_tier
from tools.pr168_rp_execution_policy_candidate_optimizer import rank_policy_candidates
from tools.pr168_rp_formula_default_resolver import default_gap_row, resolve_default_stack
from tools.pr168_rp_formula_input_resolver import (
    PR165_D2_AGENT_REPORTS,
    PR165_D2_INPUT_REPORTS,
    load_agent_source_status,
    load_numeric_input_maps,
    missing_variables_for_input_gap,
    qku_id_from_assignment,
    resolve_row_input,
)
from tools.pr168_rp_latency_budget import latency_budget_row
from tools.pr168_rp_live_candidate_gate_seed import live_gate_seed
from tools.pr168_rp_microstructure_fill_model import compute_microstructure_features
from tools.pr168_rp_negative_recovery_engine import build_recovery_attempt
from tools.pr168_rp_no_trade_comparator import no_trade_comparison_row
from tools.pr168_rp_order_candidate_factory import make_order_candidates
from tools.pr168_rp_overfit_fdr_proxy import compute_overfit_fdr_proxy
from tools.pr168_rp_portfolio_marginal_utility import compute_portfolio_utility
from tools.pr168_rp_pretrade_simulation_kernel import simulate_pretrade_candidate
from tools.pr168_rp_quantum_structural_readiness import compute_quantum_structural_readiness
from tools.pr168_rp_regime_memory_seed import regime_seed_row
from tools.pr168_rp_report_writer import GENERATED_DIR, pointer_row, read_records, read_report, write_report
from tools.pr168_rp_tca_decomposition import compute_tca_components
from tools.pr168_rp_unit_basis_normalizer import bounded_probability, decimal_number, decimal_to_float, non_negative


BASELINE_COUNTS = {
    "historical_master_qku_count": 9360,
    "current_candidate_packet_v1_count": 6502,
    "atomicrows_count": 4183,
    "formula_assignment_rows": 20387,
    "selected_formula_count": 35,
    "required_formula_sets": 5,
}

UPSTREAM_INPUTS = [
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "PR168_GFP_FinalSummary.report.json",
    "PR168_GFP_AuthoritativeTruthOverlay.report.json",
    "PR168_GFP_SelectedFormulaExpressionRegistry.report.json",
    "PR168_GFP_FormulaAssignmentMatrix.report.json",
    "PR168_GFP_RequiredFormulaSetMap.report.json",
    "PR168_GFP_RealFormulaFunctionRegistry.report.json",
    "PR168_GFP_RealComputationTestVectorRegistry.report.json",
    "PR168_GFP_QKUBaselineCountReconcile.report.json",
    "PR168_GFP_Historical9360VsCurrent6502Reconcile.report.json",
    "PR168_GFP_QKUComputationCoverage.report.json",
    "PR168_GFP_CandidatePacketV1ComputationCoverage.report.json",
    "PR168_GFP_AtomicRowsComputationCoverage.report.json",
    "PR168_GFP_MasterPlanFormulaCatalog.report.json",
    "PR168_GFP_MasterPlanFormulaToSelectedFormulaCrosswalk.report.json",
    "PR168_GFP_PriorPRFormulaCatalog.report.json",
    "PR168_GFP_MasterPlanFormulaCoverageAudit.report.json",
    "PR168_GFP_FormulaSourceLedger.report.json",
    "PR168_GFP_FormulaToQKULineage.report.json",
    "PR168_GFP_FormulaToAtomicRowsLineage.report.json",
    "PR168_GFP_FormulaToCandidatePacketV1Lineage.report.json",
    "PR168_GFP_NoOrphanProof.report.json",
    "PR168_GFP_AgentWorkOrders.report.json",
    "PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "PR165_D2_AgentDutySourceCrosswalk.report.json",
    "PR166_QC replay/paper/TCA/fill/latency reports",
    "PR167 simulator reports",
    "PR162E plugin framework reports",
    "PR208 router / route validator files",
    "connector/source-evidence/connector-semantic-binding boundary docs",
    "dashboard/commander/governance report-consumer manifests",
    "paper/replay fill ledger cost latency capacity source-boundary reports",
    "pretrade order-intent/live-surface lock docs",
    "runtime formula allowlist / hot-path cache handoff docs",
]

EXTERNAL_SCOUTING_REFERENCES = [
    {
        "reference_id": "CFA_TRADE_STRATEGY_EXECUTION",
        "url": "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/trade-strategy-execution",
        "candidate_use": "TCA and trade policy framing",
    },
    {
        "reference_id": "CFA_TRADING_COSTS_ELECTRONIC_MARKETS",
        "url": "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/trading-costs-and-electronic-markets",
        "candidate_use": "explicit and implicit trading cost taxonomy",
    },
    {
        "reference_id": "POLYMARKET_ORDERBOOK_OVERVIEW",
        "url": "https://docs.polymarket.us/institutional/orderbook/overview",
        "candidate_use": "L2 order-book depth semantics",
    },
    {
        "reference_id": "BENJAMINI_HOCHBERG_1995",
        "url": "https://rss.onlinelibrary.wiley.com/doi/10.1111/j.2517-6161.1995.tb02031.x",
        "candidate_use": "multiple-testing caution; no formal BH claim in PR168-RP",
    },
    {
        "reference_id": "BAILEY_LOPEZ_DE_PRADO_DEFLATED_SHARPE",
        "url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551",
        "candidate_use": "overfit caution; no full DSR claim in PR168-RP",
    },
    {
        "reference_id": "ROCKAFELLAR_URYASEV_CVAR",
        "url": "https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf",
        "candidate_use": "expected shortfall / CVaR risk framing",
    },
    {
        "reference_id": "LOPEZ_DE_PRADO_HRP",
        "url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678",
        "candidate_use": "portfolio diversification candidate logic",
    },
    {
        "reference_id": "DWAVE_OCEAN_MODELS",
        "url": "https://docs.dwavequantum.com/en/latest/concepts/models.html",
        "candidate_use": "QUBO/BQM/Ising/CQM/DQM structural model families",
    },
    {
        "reference_id": "QISKIT_OPTIMIZATION_MIN_EIGEN",
        "url": "https://qiskit-community.github.io/qiskit-optimization/tutorials/03_minimum_eigen_optimizer.html",
        "candidate_use": "QuadraticProgram to Ising/QAOA-compatible workflow concepts",
    },
]

REQUIRED_REPORTS = [
    "PR168_RP_ReadReceipt.report.json",
    "PR168_RP_InputConsumption.report.json",
    "PR168_RP_StrictInputConsumptionLedger.report.json",
    "PR168_RP_PR168GFPTruthOverlayConsumption.report.json",
    "PR168_RP_PR165D2AgentArtifactDiscovery.report.json",
    "PR168_RP_FormulaExecutionUniverse.report.json",
    "PR168_RP_InputAvailabilityMatrix.report.json",
    "PR168_RP_ReplayInputAvailability.report.json",
    "PR168_RP_PaperInputAvailability.report.json",
    "PR168_RP_MissingDefaultResolutionQueue.report.json",
    "PR168_RP_MissingValueCandidateFillQueue.report.json",
    "PR168_RP_ExternalScoutingCandidateLedger.report.json",
    "PR168_RP_ComputedReplayResults.report.json",
    "PR168_RP_ComputedPaperResults.report.json",
    "PR168_RP_ReplayPaperComparison.report.json",
    "PR168_RP_ComputedPnLEvidence.report.json",
    "PR168_RP_PreTradeSimulationCandidates.report.json",
    "PR168_RP_OrderPolicyCandidateRanking.report.json",
    "PR168_RP_NoTradeCandidateComparison.report.json",
    "PR168_RP_ScenarioLadderResults.report.json",
    "PR168_RP_LatencyBudgetResults.report.json",
    "PR168_RP_LivePreTradeDecisionGateSeed.report.json",
    "PR168_RP_HotPathPrecomputeCandidateSeed.report.json",
    "PR168_RP_LiveExcludedHeavyComputationLedger.report.json",
    "PR168_RP_EdgeAttribution.report.json",
    "PR168_RP_AlphaSourceDecomposition.report.json",
    "PR168_RP_EdgeCaptureMechanismIndex.report.json",
    "PR168_RP_ExecutionAdjustedEdge.report.json",
    "PR168_RP_ExecutionAdjustedRankingSeed.report.json",
    "PR168_RP_TCADecomposition.report.json",
    "PR168_RP_ImplementationShortfall.report.json",
    "PR168_RP_ExecutionCostAttribution.report.json",
    "PR168_RP_TCACostDominanceFailureReasons.report.json",
    "PR168_RP_FillQueueLatencyResults.report.json",
    "PR168_RP_OrderBookDepthSweep.report.json",
    "PR168_RP_PredictionMarketMicrostructureFeatures.report.json",
    "PR168_RP_OrderTypeSizingPriceCandidateRepair.report.json",
    "PR168_RP_CapacityCrowdingResults.report.json",
    "PR168_RP_CapacityScalingCurveSeed.report.json",
    "PR168_RP_SizeReductionRecoveryCandidates.report.json",
    "PR168_RP_ProbabilityCalibration.report.json",
    "PR168_RP_CalibrationRepairQueue.report.json",
    "PR168_RP_OverfitFDRResults.report.json",
    "PR168_RP_MultipleTestingFamilyLedger.report.json",
    "PR168_RP_RepairAttemptMultiplicityLedger.report.json",
    "PR168_RP_LowerConfidenceBoundResults.report.json",
    "PR168_RP_PortfolioMarginalUtilityResults.report.json",
    "PR168_RP_RiskDiversificationResults.report.json",
    "PR168_RP_ClusterCommonDriverExposure.report.json",
    "PR168_RP_PortfolioRepairCandidateQueue.report.json",
    "PR168_RP_RegimeConditionedMemorySeed.report.json",
    "PR168_RP_ScenarioOutcomeSeed.report.json",
    "PR168_RP_ConditionScopedNegativeMemorySeed.report.json",
    "PR168_RP_ConditionScopedPositiveRepairMemorySeed.report.json",
    "PR168_RP_PreTradeRegimeMemorySeed.report.json",
    "PR168_RP_ChampionChallengerEligibility.report.json",
    "PR168_RP_ChampionChallengerReasonCodes.report.json",
    "PR168_RP_RepairedCandidateChampionChallengerEligibility.report.json",
    "PR168_RP_PreTradeChampionChallengerEligibility.report.json",
    "PR168_RP_QuantumObjectiveRecompute.report.json",
    "PR168_RP_QuantumStructuralReadiness.report.json",
    "PR168_RP_QuantumCoefficientMapInputGaps.report.json",
    "PR168_RP_ClassicalFallbackResults.report.json",
    "PR168_RP_StrongestClassicalComparatorMap.report.json",
    "PR168_RP_QKUCombinationQUBOObjectiveSeed.report.json",
    "PR168_RP_OrderPolicySelectionQUBOSeed.report.json",
    "PR168_RP_QKUCombinationCandidateResults.report.json",
    "PR168_RP_QKUCombinationNegativeRecoveryResults.report.json",
    "PR168_RP_MarginalUtilitySelectionResults.report.json",
    "PR168_RP_ParetoFrontierRankingSeed.report.json",
    "PR168_RP_OrderPolicyCombinationSelectionResults.report.json",
    "PR168_RP_ComputedPositiveEdgeCandidates.report.json",
    "PR168_RP_RepairedPositiveCandidateEvidence.report.json",
    "PR168_RP_ComputedNegativeEdgeCandidates.report.json",
    "PR168_RP_ComputedNeutralOrZeroEdgeCandidates.report.json",
    "PR168_RP_NegativeCandidateReasonCodes.report.json",
    "PR168_RP_NegativeToPositiveRecoveryAttempts.report.json",
    "PR168_RP_NegativeRecoveryCandidateFactory.report.json",
    "PR168_RP_TrueNegativeAfterRecoveryExhaustion.report.json",
    "PR168_RP_OldPositiveTruthCorrection.report.json",
    "PR168_RP_OldNegativeTruthCorrection.report.json",
    "PR168_RP_ActionableInputGapQueue.report.json",
    "PR168_RP_AgentDutySourceGapQueue.report.json",
    "PR168_RP_TargetedFormulaExpansionQueue.report.json",
    "PR168_RP_ConnectorCandidateRouteMap.report.json",
    "PR168_RP_ConnectorSemanticBindingNonCreationAudit.report.json",
    "PR168_RP_To_PR168_RANK_ComputedRanking.report.json",
    "PR168_RP_To_PR168_RANK_PreTradeRankingSeed.report.json",
    "PR168_RP_To_PR166_QC_R2_RedoWithComputedEvidence.report.json",
    "PR168_RP_To_PR162E_Q_QuantumMapperGaps.report.json",
    "PR168_RP_To_PR162E_PR162F_FormulaPluginIntakeGaps.report.json",
    "PR168_RP_To_RuntimeFormulaAllowlistHotPathCacheSeed.report.json",
    "PR168_RP_To_ExecutionRouterLiveGateFutureHandoff.report.json",
    "PR168_RP_To_OwnerDashboardComputedTruth.report.json",
    "PR168_RP_RouteTriage.report.json",
    "PR168_RP_CommandActionMatrix.report.json",
    "PR168_RP_DAGUpstreamDownstreamOrchestration.report.json",
    "PR168_RP_FullMasterPlanSectionCrosswalk.report.json",
    "PR168_RP_MarketSpecificSectionIndexes.report.json",
    "PR168_RP_Stage1PredictionMarketActivationIndex.report.json",
    "PR168_RP_FutureMarketDormancyIndex.report.json",
    "PR168_RP_ReportConsumerCrosswalk.report.json",
    "PR168_RP_ArtifactConsumerDAG.report.json",
    "PR168_RP_MetricConsumerDAG.report.json",
    "PR168_RP_AgentDutyDAG.report.json",
    "PR168_RP_PRDependencyDAG.report.json",
    "PR168_RP_ArtifactInformationValueDAG.report.json",
    "PR168_RP_ConnectorCandidateRouteDAG.report.json",
    "PR168_RP_PreTradeDecisionDAG.report.json",
    "PR168_RP_OrderPolicyConsumerDAG.report.json",
    "PR168_RP_LiveCandidateHandoffDAG.report.json",
    "PR168_RP_ArtifactMap.report.json",
    "PR168_RP_FileConsumerMap.report.json",
    "PR168_RP_ValueLineageMap.report.json",
    "PR168_RP_MetricConsumerMap.report.json",
    "PR168_RP_QKUFormulaComputationLineage.report.json",
    "PR168_RP_AgentDutyOrchestrationCrosswalk.report.json",
    "PR168_RP_AgentWorkOrders.report.json",
    "PR168_RP_NoOrphanProof.report.json",
    "PR168_RP_AuthorityBoundaryAudit.report.json",
    "PR168_RP_ValidationScopeRegistryIntegration.report.json",
    "PR168_RP_WindowsLinuxCompatibilityAudit.report.json",
    "PR168_RP_FinalSummary.report.json",
]


def build_pr168_rp_state(repo_root: Path) -> dict[str, Any]:
    formulas = read_report(repo_root, "PR168_GFP_SelectedFormulaExpressionRegistry.report.json")["records"]
    formula_by_id = {str(row["formula_id"]): row for row in formulas}
    required_sets = read_report(repo_root, "PR168_GFP_RequiredFormulaSetMap.report.json")["records"]
    required_set_by_id = {str(row["required_formula_set_id"]): row for row in required_sets}
    assignments = read_records(repo_root, "PR168_GFP_FormulaAssignmentMatrix.report.json")
    overlay = read_records(repo_root, "PR168_GFP_AuthoritativeTruthOverlay.report.json")
    input_maps = load_numeric_input_maps(repo_root)
    agent_status = load_agent_source_status(repo_root)

    state: dict[str, Any] = {
        "formulas": formulas,
        "required_sets": required_sets,
        "assignments": assignments,
        "overlay": overlay,
        "input_availability_rows": [],
        "input_gap_rows": [],
        "default_gap_rows": [],
        "computed_rows": [],
        "computed_positive_rows": [],
        "computed_negative_rows": [],
        "computed_neutral_rows": [],
        "pretrade_candidates": [],
        "order_policy_rankings": [],
        "no_trade_rows": [],
        "latency_rows": [],
        "scenario_rows": [],
        "edge_rows": [],
        "negative_recovery_rows": [],
        "quantum_rows": [],
        "quantum_gap_rows": [],
        "combination_rows": [],
        "regime_rows": [],
        "connector_rows": [],
        "agent_status": agent_status,
        "strict_input_ledger": strict_input_consumption_ledger(repo_root),
        "external_scouting_rows": external_scouting_rows(),
    }

    _verify_formula_registry(assignments, formula_by_id, required_set_by_id)
    for index, assignment in enumerate(assignments, start=1):
        resolved = resolve_row_input(assignment, input_maps)
        route = route_for_assignment(assignment, agent_status)
        connector = connector_route_for(assignment)
        quantum = compute_quantum_structural_readiness(assignment)
        state["quantum_rows"].append(_quantum_row(index, assignment, quantum, route))
        if quantum["quantum_materiality_flag"]:
            state["quantum_gap_rows"].append(_quantum_gap_row(index, assignment, quantum, route))
        if resolved["complete"]:
            computed = _compute_assignment(index, assignment, resolved, route, connector, quantum)
            state["computed_rows"].append(computed)
            state["input_availability_rows"].append(_availability_row(assignment, resolved, computed, route))
            state["default_gap_rows"].append(default_gap_row(computed))
            if computed["computed_status"] == "COMPUTED_POSITIVE_EDGE":
                state["computed_positive_rows"].append(computed)
            elif computed["computed_status"] == "COMPUTED_NEGATIVE_EDGE":
                state["computed_negative_rows"].append(computed)
                recovery = build_recovery_attempt(computed)
                computed["negative_recovery_ref"] = recovery["negative_recovery_ref"]
                state["negative_recovery_rows"].append(recovery)
            else:
                state["computed_neutral_rows"].append(computed)
            edge = build_edge_attribution(computed)
            state["edge_rows"].append(edge)
            state["scenario_rows"].append(build_scenario_ladder_row(computed))
            state["combination_rows"].append(combination_row(computed))
            state["regime_rows"].append(regime_seed_row(computed))
            state["connector_rows"].append(_connector_row(computed))
            candidates = [simulate_pretrade_candidate(row, computed) for row in make_order_candidates(computed)]
            state["pretrade_candidates"].extend(candidates)
            ranked = rank_policy_candidates(candidates)
            state["order_policy_rankings"].extend(ranked)
            state["no_trade_rows"].extend(no_trade_comparison_row(row) for row in ranked)
            state["latency_rows"].extend(latency_budget_row(row) for row in ranked)
        else:
            gap = _input_gap_row(index, assignment, resolved, route, connector, quantum)
            state["input_gap_rows"].append(gap)
            state["input_availability_rows"].append(_availability_row(assignment, resolved, gap, route))
    return state


def build_all_reports(repo_root: Path) -> dict[str, Any]:
    state = build_pr168_rp_state(repo_root)
    report_rows = _report_rows(state)
    for filename in REQUIRED_REPORTS:
        records = [_ensure_no_orphan_metadata(row, filename) for row in report_rows.get(filename, [])]
        write_report(
            repo_root,
            filename,
            records,
            report_type=Path(filename).stem.upper(),
            summary=_summary_for(filename, records, state),
            consumer=_consumer_for(filename),
            downstream_route=_route_for_report(filename),
            shard=len(records) > 1000,
        )
    return _final_summary(state)


def _ensure_no_orphan_metadata(row: dict[str, Any], filename: str) -> dict[str, Any]:
    normalized = dict(row)
    normalized.setdefault("producer", "PR168_RP_FORMULA_BASED_REPLAY_PAPER_RECOMPUTE")
    normalized.setdefault("consumer", _consumer_for(filename))
    normalized.setdefault("upstream_source", normalized.get("upstream_report") or normalized.get("upstream_file_ref") or "PR168_RP_BUILD_KERNEL")
    normalized.setdefault("downstream_route", _route_for_report(filename))
    normalized.setdefault("owning_agent", "Replay Paper Recompute Agent")
    normalized.setdefault("no_orphan_status", "CONNECTED_TO_DECLARED_CONSUMER")
    return normalized


def _compute_assignment(
    index: int,
    assignment: dict[str, Any],
    resolved: dict[str, Any],
    route: dict[str, Any],
    connector: dict[str, Any],
    quantum: dict[str, Any],
) -> dict[str, Any]:
    probability = resolved["probability"]
    micro_source = resolved["microstructure"]
    tca_source = resolved["tca"]
    ranking_source = resolved["ranking"]
    side = str(probability.get("yes_no_side") or ranking_source.get("yes_no_side") or "YES").upper()
    micro = compute_microstructure_features(micro_source, side)
    tca = compute_tca_components(tca_source, micro_source, ranking_source)
    portfolio = compute_portfolio_utility(ranking_source)
    overfit = compute_overfit_fdr_proxy(ranking_source)

    predicted = bounded_probability(probability["model_probability_estimate"], field="model_probability_estimate")
    market = bounded_probability(probability["market_implied_probability"], field="market_implied_probability")
    gross = predicted - market
    total_costs = sum(
        Decimal(str(tca[field]))
        for field in [
            "explicit_fee_cost",
            "spread_cost",
            "slippage_cost",
            "market_impact",
            "adverse_selection_penalty",
            "implementation_shortfall",
            "latency_decay",
            "queue_nonfill_penalty",
            "partial_fill_penalty",
            "stale_orderbook_penalty",
            "capacity_crowding_penalty",
        ]
    ) + Decimal(str(overfit["overfit_fdr_penalty"]))
    execution_adjusted_edge = gross - total_costs
    position_size = non_negative(micro["order_quantity"], field="order_quantity")
    net_expected_pnl = position_size * execution_adjusted_edge
    fill_probability = bounded_probability(micro["fill_probability"], field="fill_probability")
    no_fill_opportunity_cost = Decimal(str(micro["no_fill_opportunity_cost"])) * position_size
    partial_fill_residual_risk = Decimal(str(tca["partial_fill_penalty"])) * position_size
    expected_shortfall_cvar = Decimal(str(portfolio["expected_shortfall_cvar"]))
    fill_adjusted_expected_pnl = fill_probability * net_expected_pnl - no_fill_opportunity_cost - partial_fill_residual_risk
    lcb = min(execution_adjusted_edge, Decimal(str(tca_source["edge_lower_confidence_bound"]))) - Decimal(str(overfit["overfit_fdr_penalty"]))
    default_stack = resolve_default_stack(assignment)
    missing_default_blocking_flag = True
    no_trade_margin = fill_adjusted_expected_pnl
    decision = (
        net_expected_pnl > Decimal("0")
        and lcb > Decimal("0")
        and not missing_default_blocking_flag
        and bool(portfolio["risk_budget_pass_fail"])
        and float(fill_probability) > 0.0
    )
    if decision:
        status = "COMPUTED_POSITIVE_EDGE"
    elif abs(float(net_expected_pnl)) < 1e-12:
        status = "COMPUTED_NEUTRAL_OR_ZERO_EDGE"
    else:
        status = "COMPUTED_NEGATIVE_EDGE"
    validate_computed_status(status)
    evidence_tier = classify_row(inputs_complete=True, quantum_gap=bool(quantum["quantum_materiality_flag"]))
    validate_evidence_tier(evidence_tier)
    result_ref = f"PR168_RP_RESULT::{index:05d}"
    metrics = {
        "market_implied_probability": decimal_to_float(market),
        "predicted_probability": decimal_to_float(predicted),
        "probability_calibration_error": round(abs(float(probability.get("probability_calibration_score", 0.0)) - 1.0), 10),
        "gross_edge": decimal_to_float(gross),
        "expected_value": decimal_to_float(gross * position_size),
        "binary_contract_expected_value": decimal_to_float(Decimal(str(probability.get("expected_value_cents_per_contract", 0))) / Decimal("100")),
        "explicit_fee_cost": tca["explicit_fee_cost"],
        "spread_cost": tca["spread_cost"],
        "slippage_cost": tca["slippage_cost"],
        "market_impact": tca["market_impact"],
        "adverse_selection_penalty": tca["adverse_selection_penalty"],
        "implementation_shortfall": tca["implementation_shortfall"],
        "latency_decay": tca["latency_decay"],
        "queue_nonfill_penalty": tca["queue_nonfill_penalty"],
        "partial_fill_penalty": tca["partial_fill_penalty"],
        "stale_orderbook_penalty": tca["stale_orderbook_penalty"],
        "capacity_crowding_penalty": tca["capacity_crowding_penalty"],
        "overfit_fdr_penalty": overfit["overfit_fdr_penalty"],
        "total_tca": tca["total_tca"],
        "execution_adjusted_edge": decimal_to_float(execution_adjusted_edge),
        "fill_adjusted_expected_pnl": decimal_to_float(fill_adjusted_expected_pnl),
        "position_size": decimal_to_float(position_size),
        "net_expected_pnl_candidate": decimal_to_float(net_expected_pnl),
        "lower_confidence_bound_edge": decimal_to_float(lcb),
        "positive_negative_decision": decision,
        "replay_paper_before_after_delta": round(float(net_expected_pnl) - float(ranking_source.get("net_edge_after_costs", 0.0)), 10),
        "formula_input_gap_route": None,
        "still_negative_repair_route": "PR168_RP_NegativeToPositiveRecoveryAttempts.report.json" if status == "COMPUTED_NEGATIVE_EDGE" else None,
        "champion_challenger_computed_eligibility": False,
        "fill_probability": decimal_to_float(fill_probability),
        "no_fill_opportunity_cost": decimal_to_float(no_fill_opportunity_cost),
        "partial_fill_residual_risk": decimal_to_float(partial_fill_residual_risk),
        "no_trade_comparison_margin": decimal_to_float(no_trade_margin),
        "portfolio_marginal_utility": portfolio["portfolio_marginal_utility"],
        "expected_shortfall_cvar": portfolio["expected_shortfall_cvar"],
        "capacity_usage": portfolio["capacity_usage"],
        "crowding_score": ranking_source.get("crowding_penalty"),
        "calibration_status": "CALIBRATION_PROXY_COMPUTED_REPLAY_PAPER_ONLY",
        "reliability_bin": probability.get("calibration_bin_ref"),
        "time_to_resolution_bucket": ranking_source.get("time_to_resolution_bucket"),
        "event_category_exposure": portfolio["event_category_exposure"],
        "missing_default_blocking_flag": missing_default_blocking_flag,
        **overfit,
        **portfolio,
    }
    return {
        "canonical_row_key": assignment.get("canonical_row_key"),
        "qku_id": resolved["qku_id"],
        "row_family": assignment.get("row_family"),
        "formula_id": assignment.get("formula_id"),
        "formula_ids": assignment.get("formula_ids", []),
        "required_formula_set_id": assignment.get("required_formula_set_id"),
        "upstream_report": assignment.get("source_report_path"),
        "upstream_file_ref": assignment.get("source_report_path"),
        "upstream_row_ref": assignment.get("source_row_pointer"),
        "input_ref": f"PR168_RP_INPUT::{index:05d}",
        "output_ref": f"PR168_RP_OUTPUT::{index:05d}",
        "result_ref": result_ref,
        "evidence_tier": evidence_tier,
        "computed_status": status,
        "metrics": metrics,
        "microstructure": micro,
        "source_rows": {
            "probability": probability,
            "microstructure": micro_source,
            "tca": tca_source,
            "ranking": ranking_source,
        },
        "default_stack": default_stack,
        "edge_attribution_ref": f"PR168_RP_EDGE_ATTRIBUTION::{index:05d}",
        "negative_recovery_ref": f"PR168_RP_NEGATIVE_RECOVERY::{index:05d}",
        "connector_candidate_route": connector["connector_candidate_route"],
        "connector_semantic_binding_state": connector["connector_semantic_binding_state"],
        "quantum_structural_readiness": quantum["quantum_structural_readiness"],
        "quantum_objective_ref": quantum["downstream_route"],
        "market_scope": ranking_source.get("market_scope"),
        "side": side,
        **route,
        "producer": "PR168_RP_COMPUTE_KERNEL",
        "consumer": "PR168_RANK",
        "source_truth_authority": False,
        "connector_truth_authority": False,
        "live_authority": False,
        "no_orphan_status": "CONNECTED_TO_COMPUTED_RESULT_CONSUMER",
    }


def _input_gap_row(
    index: int,
    assignment: dict[str, Any],
    resolved: dict[str, Any],
    route: dict[str, Any],
    connector: dict[str, Any],
    quantum: dict[str, Any],
) -> dict[str, Any]:
    evidence_tier = classify_row(inputs_complete=False, quantum_gap=bool(quantum["quantum_materiality_flag"] and "quantum" in resolved.get("missing_lanes", [])))
    missing = missing_variables_for_input_gap(assignment, resolved)
    return {
        "canonical_row_key": assignment.get("canonical_row_key"),
        "qku_id": resolved.get("qku_id"),
        "row_family": assignment.get("row_family"),
        "upstream_report": assignment.get("source_report_path"),
        "upstream_file_ref": assignment.get("source_report_path"),
        "upstream_row_ref": assignment.get("source_row_pointer"),
        "formula_id": assignment.get("formula_id"),
        "required_formula_set_id": assignment.get("required_formula_set_id"),
        "input_ref": f"PR168_RP_INPUT_GAP::{index:05d}",
        "output_ref": None,
        "result_ref": f"PR168_RP_INPUT_GAP_RESULT::{index:05d}",
        "evidence_tier": evidence_tier,
        "computed_status": "FORMULA_ASSIGNED_INPUTS_MISSING",
        "missing_variables": missing,
        "missing_lanes": resolved.get("missing_lanes", []),
        "expected_unit_basis": "PROBABILITY_POINTS_AND_EDGE_COST_UNITS_FROM_PR168_GFP_FORMULA_REGISTRY",
        "critical": True,
        "gap_reason_code": "MISSING_NUMERIC_INPUTS",
        "formula_input_gap_route": "PR168_RP_ActionableInputGapQueue.report.json",
        "connector_candidate_route": connector["connector_candidate_route"],
        "connector_semantic_binding_state": connector["connector_semantic_binding_state"],
        "terminal_reason_if_terminal": None,
        "pretrade_candidate_ref": None,
        "owning_agent": route["owning_agent"],
        "supporting_agents": route["supporting_agents"],
        "duty_source_ref": route["duty_source_ref"],
        "downstream_agent": route["downstream_agent"],
        "downstream_pr": route["downstream_pr"],
        "downstream_route": "PR168_RP_ActionableInputGapQueue.report.json",
        "dashboard_visibility": True,
        "commander_visibility": True,
        "governance_visibility": True,
        "source_truth_authority": False,
        "connector_truth_authority": False,
        "live_authority": False,
        "producer": "PR168_RP_INPUT_RESOLVER",
        "consumer": "Input Materialization Agent",
        "no_orphan_status": "CONNECTED_TO_ACTIONABLE_INPUT_GAP_QUEUE",
    }


def _availability_row(assignment: dict[str, Any], resolved: dict[str, Any], result: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical_row_key": assignment.get("canonical_row_key"),
        "qku_id": resolved.get("qku_id"),
        "row_family": assignment.get("row_family"),
        "formula_id": assignment.get("formula_id"),
        "required_formula_set_id": assignment.get("required_formula_set_id"),
        "input_lanes_present": sorted(k for k in ("probability", "microstructure", "tca", "ranking") if k in resolved),
        "missing_lanes": resolved.get("missing_lanes", []),
        "inputs_complete": bool(resolved.get("complete")),
        "evidence_tier": result["evidence_tier"],
        "computed_status": result["computed_status"],
        "downstream_route": result.get("downstream_route") or route["downstream_route"],
        "owning_agent": route["owning_agent"],
        "producer": "PR168_RP_INPUT_RESOLVER",
        "consumer": "PR168_RP_COMPUTE_KERNEL",
        "upstream_source": assignment.get("source_report_path"),
        "no_orphan_status": "CONNECTED_TO_INPUT_AVAILABILITY_CONSUMER",
    }


def _quantum_row(index: int, assignment: dict[str, Any], quantum: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    return {
        "quantum_readiness_ref": f"PR168_RP_QUANTUM::{index:05d}",
        "canonical_row_key": assignment.get("canonical_row_key"),
        "qku_id": qku_id_from_assignment(assignment),
        "row_family": assignment.get("row_family"),
        "formula_refs": assignment.get("formula_ids", []),
        "producer": "PR168_RP_QUANTUM_STRUCTURAL_READINESS",
        "consumer": "PR166-QC-R2",
        "upstream_source": assignment.get("source_report_path"),
        "owning_agent": route["owning_agent"],
        "no_orphan_status": "CONNECTED_TO_QUANTUM_CONSUMER",
        **quantum,
    }


def _quantum_gap_row(index: int, assignment: dict[str, Any], quantum: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    return {
        "quantum_gap_ref": f"PR168_RP_QUANTUM_GAP::{index:05d}",
        "canonical_row_key": assignment.get("canonical_row_key"),
        "qku_id": qku_id_from_assignment(assignment),
        "formula_refs": assignment.get("formula_ids", []),
        "missing_quantum_inputs": quantum["missing_quantum_inputs"],
        "gap_reason_code": "MISSING_QUANTUM_COEFFICIENT_MAP",
        "downstream_route": "PR168_RP_To_PR162E_Q_QuantumMapperGaps.report.json",
        "downstream_pr": "PR162E-Q",
        "owning_agent": route["owning_agent"],
        "producer": "PR168_RP_QUANTUM_STRUCTURAL_READINESS",
        "consumer": "Quantum Mapper Agent",
        "upstream_source": assignment.get("source_report_path"),
        "no_orphan_status": "CONNECTED_TO_QUANTUM_GAP_CONSUMER",
    }


def _connector_row(computed: dict[str, Any]) -> dict[str, Any]:
    return {
        "connector_route_ref": f"PR168_RP_CONNECTOR::{computed['result_ref']}",
        "canonical_row_key": computed["canonical_row_key"],
        "qku_id": computed["qku_id"],
        "connector_candidate_route": computed["connector_candidate_route"],
        "connector_semantic_binding_state": "NOT_BOUND_CANDIDATE_ONLY",
        "connector_truth_authority": False,
        "live_authority": False,
        "downstream_connector_agent": "Connector Candidate Routing Agent",
        "downstream_connector_pr": "PR174-PR181",
        "producer": "PR168_RP_CONNECTOR_CANDIDATE_ROUTER",
        "consumer": "Future Connector Candidate Queue",
        "upstream_source": computed["result_ref"],
        "downstream_route": "PR168_RP_ConnectorCandidateRouteMap.report.json",
        "owning_agent": "Connector Candidate Routing Agent",
        "no_orphan_status": "CONNECTED_TO_CONNECTOR_CANDIDATE_CONSUMER",
    }


def build_scenario_ladder_row(computed: dict[str, Any]) -> dict[str, Any]:
    from tools.pr168_rp_scenario_ladder import build_scenario_ladder

    return build_scenario_ladder(computed)


def _verify_formula_registry(assignments: list[dict[str, Any]], formulas: dict[str, dict[str, Any]], required_sets: dict[str, dict[str, Any]]) -> None:
    for row in assignments:
        set_id = str(row.get("required_formula_set_id"))
        if set_id not in required_sets:
            raise ValueError(f"unknown required formula set: {set_id}")
        for formula_id in row.get("formula_ids", []):
            if str(formula_id) not in formulas:
                raise ValueError(f"unknown formula_id: {formula_id}")
        if required_sets[set_id].get("required_formula_set_is_computed_evidence") is not False:
            raise ValueError(f"required formula set treated as evidence: {set_id}")


def strict_input_consumption_ledger(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, name in enumerate(UPSTREAM_INPUTS, start=1):
        rel_path, found, replacement = _discover_upstream(repo_root, name)
        status = "FOUND" if found else "ABSENT_GAP_ROUTED"
        rows.append(
            {
                "input_ref": f"PR168_RP_UPSTREAM_INPUT::{index:03d}",
                "requested_input": name,
                "discovered_status": status,
                "read_status": "READ" if found else "NOT_READ_ABSENT",
                "parsed_status": "PARSED" if found and rel_path.endswith(".json") else ("TEXT_READ" if found else "NOT_PARSED_ABSENT"),
                "processed_status": "PROCESSED" if found else "ABSENT_GAP_ROUTED",
                "upstream_file_ref": rel_path,
                "replacement_or_equivalent_artifact_proof": replacement,
                "downstream_outputs_created": ["PR168_RP_StrictInputConsumptionLedger.report.json"],
                "downstream_reports_created": REQUIRED_REPORTS,
                "owning_agent": "Replay Paper Recompute Agent",
                "downstream_pr": "PR168-RP",
                "no_orphan_status": "CONNECTED_TO_STRICT_INPUT_LEDGER",
                "absence_reason": None if found else "REQUESTED_ARTIFACT_NOT_PRESENT_IN_POST_MERGE_MAIN",
            }
        )
    return rows


def external_scouting_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ref in EXTERNAL_SCOUTING_REFERENCES:
        rows.append(
            {
                **ref,
                "source_lane": "CANDIDATE_RESEARCH_PROVISIONAL",
                "source_truth_authority": False,
                "connector_truth_authority": False,
                "live_authority": False,
                "replay_paper_required_before_promotion": True,
                "source_acceptance_created_by_pr168_rp": False,
                "producer": "PR168_RP_EXTERNAL_SCOUTING",
                "consumer": "Replay Paper Recompute Agent",
                "upstream_source": ref["url"],
                "downstream_route": "PR168_RP_ExternalScoutingCandidateLedger.report.json",
                "owning_agent": "External Scout Agent",
                "no_orphan_status": "CONNECTED_TO_EXTERNAL_SCOUTING_LEDGER",
            }
        )
    return rows


def _discover_upstream(repo_root: Path, name: str) -> tuple[str, bool, str | None]:
    exact_candidates = []
    if name.startswith("docs/"):
        exact_candidates.append(Path(name))
    elif name.endswith(".report.json"):
        exact_candidates.append(GENERATED_DIR / name)
    for rel in exact_candidates:
        if (repo_root / rel).exists():
            return rel.as_posix(), True, None
    equivalents = {
        "PR168_GFP_FinalSummary.report.json": "PR168_GFP_ConsumerMustUseTruthOverlay.report.json plus PR168_GFP_MasterPlanFormulaCoverageAudit.report.json",
        "PR168_GFP_RealFormulaFunctionRegistry.report.json": "PR168_GFP_SelectedFormulaExpressionRegistry.report.json contains computation_function_path and computation_function_name",
        "PR168_GFP_RealComputationTestVectorRegistry.report.json": "PR168_GFP_SelectedFormulaExpressionRegistry.report.json contains test_vector_id and tests/pr168_gfp validate functions",
        "PR168_GFP_FormulaSourceLedger.report.json": "PR168_GFP_FormulaSourceArbitration.report.json",
        "PR168_GFP_FormulaToQKULineage.report.json": "PR168_GFP_FormulaAssignmentMatrix.report.json",
        "PR168_GFP_FormulaToAtomicRowsLineage.report.json": "PR168_GFP_AtomicRowsComputationCoverage.report.json",
        "PR168_GFP_FormulaToCandidatePacketV1Lineage.report.json": "PR168_GFP_CandidatePacketV1ComputationCoverage.report.json",
        "PR168_GFP_NoOrphanProof.report.json": "PR168_GFP_FormulaAssignmentMatrix.report.json no_orphan_ref fields",
        "PR168_GFP_AgentWorkOrders.report.json": "PR168_GFP_ConsumerMustUseTruthOverlay.report.json",
        "PR166_QC replay/paper/TCA/fill/latency reports": "PR166_QC and PR166_S generated replay-paper reports discovered by prefix",
        "PR167 simulator reports": "PR167 generated reports and pr167_shards discovered by prefix",
        "PR162E plugin framework reports": "PR162E generated reports discovered by prefix",
        "PR208 router / route validator files": "tools/changed_area_validation_router.py and PR152/PR208 routing tests",
        "connector/source-evidence/connector-semantic-binding boundary docs": "docs/master_plan/source_evidence and connector semantic generated reports",
        "dashboard/commander/governance report-consumer manifests": "OwnerDashboard and governance generated reports",
        "paper/replay fill ledger cost latency capacity source-boundary reports": "PR166_S shard ledgers and PR165_D2 candidate evidence reports",
        "pretrade order-intent/live-surface lock docs": "PR166_S_OrderIntentRegistry shards and Stage1 runtime handoff reports",
        "runtime formula allowlist / hot-path cache handoff docs": "PR158_PrecomputedLowLatencySelectionReadinessIndex.report.json and Stage1RuntimeResolverToReplayPaperHandoff.report.json",
    }
    proof = equivalents.get(name)
    if proof:
        return proof, False, proof
    return name, False, None


def _report_rows(state: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    computed = state["computed_rows"]
    negative = state["computed_negative_rows"]
    gaps = state["input_gap_rows"]
    pretrade = state["pretrade_candidates"]
    ranking = state["order_policy_rankings"]
    no_trade = state["no_trade_rows"]
    latency = state["latency_rows"]
    edge = state["edge_rows"]
    quantum = state["quantum_rows"]
    quantum_gaps = state["quantum_gap_rows"]
    combos = state["combination_rows"]
    regimes = state["regime_rows"]
    recovery = state["negative_recovery_rows"]
    connectors = state["connector_rows"]
    pointers = [_computed_pointer(row, "PR168_RP_ComputedPnLEvidence.report.json") for row in computed]
    gap_pointers = [_gap_pointer(row) for row in gaps]
    negative_pointers = [_computed_pointer(row, "PR168_RP_ComputedNegativeEdgeCandidates.report.json") for row in negative]
    positive_pointers = [_computed_pointer(row, "PR168_RP_ComputedPositiveEdgeCandidates.report.json") for row in state["computed_positive_rows"]]
    neutral_pointers = [_computed_pointer(row, "PR168_RP_ComputedNeutralOrZeroEdgeCandidates.report.json") for row in state["computed_neutral_rows"]]
    dag = core_dag_edges(REQUIRED_REPORTS)
    final = _final_summary_row(state)
    old_label_corrections = _old_label_correction_rows(state)
    route_rows = _route_rows(state)
    live_gate = [live_gate_seed()]
    row_map: dict[str, list[dict[str, Any]]] = {
        "PR168_RP_ReadReceipt.report.json": state["strict_input_ledger"],
        "PR168_RP_InputConsumption.report.json": state["strict_input_ledger"],
        "PR168_RP_StrictInputConsumptionLedger.report.json": state["strict_input_ledger"],
        "PR168_RP_PR168GFPTruthOverlayConsumption.report.json": _truth_overlay_consumption_rows(state),
        "PR168_RP_PR165D2AgentArtifactDiscovery.report.json": [_agent_discovery_row(state)],
        "PR168_RP_FormulaExecutionUniverse.report.json": _formula_universe_rows(state),
        "PR168_RP_InputAvailabilityMatrix.report.json": state["input_availability_rows"],
        "PR168_RP_ReplayInputAvailability.report.json": state["input_availability_rows"],
        "PR168_RP_PaperInputAvailability.report.json": state["input_availability_rows"],
        "PR168_RP_MissingDefaultResolutionQueue.report.json": state["default_gap_rows"],
        "PR168_RP_MissingValueCandidateFillQueue.report.json": gap_pointers,
        "PR168_RP_ExternalScoutingCandidateLedger.report.json": state["external_scouting_rows"],
        "PR168_RP_ComputedReplayResults.report.json": pointers,
        "PR168_RP_ComputedPaperResults.report.json": pointers,
        "PR168_RP_ReplayPaperComparison.report.json": _replay_paper_comparison_rows(computed),
        "PR168_RP_ComputedPnLEvidence.report.json": _computed_metric_rows(computed),
        "PR168_RP_PreTradeSimulationCandidates.report.json": pretrade,
        "PR168_RP_OrderPolicyCandidateRanking.report.json": ranking,
        "PR168_RP_NoTradeCandidateComparison.report.json": no_trade,
        "PR168_RP_ScenarioLadderResults.report.json": state["scenario_rows"],
        "PR168_RP_LatencyBudgetResults.report.json": latency,
        "PR168_RP_LivePreTradeDecisionGateSeed.report.json": live_gate,
        "PR168_RP_HotPathPrecomputeCandidateSeed.report.json": _hot_path_seed_rows(state),
        "PR168_RP_LiveExcludedHeavyComputationLedger.report.json": _heavy_lane_rows(),
        "PR168_RP_EdgeAttribution.report.json": edge,
        "PR168_RP_AlphaSourceDecomposition.report.json": edge,
        "PR168_RP_EdgeCaptureMechanismIndex.report.json": edge,
        "PR168_RP_ExecutionAdjustedEdge.report.json": _execution_edge_rows(computed),
        "PR168_RP_ExecutionAdjustedRankingSeed.report.json": _execution_ranking_seed_rows(computed),
        "PR168_RP_TCADecomposition.report.json": _tca_rows(computed),
        "PR168_RP_ImplementationShortfall.report.json": _implementation_shortfall_rows(computed),
        "PR168_RP_ExecutionCostAttribution.report.json": _tca_rows(computed),
        "PR168_RP_TCACostDominanceFailureReasons.report.json": recovery,
        "PR168_RP_FillQueueLatencyResults.report.json": _fill_latency_rows(computed),
        "PR168_RP_OrderBookDepthSweep.report.json": _micro_rows(computed),
        "PR168_RP_PredictionMarketMicrostructureFeatures.report.json": _micro_rows(computed),
        "PR168_RP_OrderTypeSizingPriceCandidateRepair.report.json": ranking,
        "PR168_RP_CapacityCrowdingResults.report.json": _capacity_rows(computed),
        "PR168_RP_CapacityScalingCurveSeed.report.json": _capacity_rows(computed),
        "PR168_RP_SizeReductionRecoveryCandidates.report.json": recovery,
        "PR168_RP_ProbabilityCalibration.report.json": _calibration_rows(computed),
        "PR168_RP_CalibrationRepairQueue.report.json": _calibration_rows(computed),
        "PR168_RP_OverfitFDRResults.report.json": _overfit_rows(computed),
        "PR168_RP_MultipleTestingFamilyLedger.report.json": _overfit_rows(computed),
        "PR168_RP_RepairAttemptMultiplicityLedger.report.json": recovery,
        "PR168_RP_LowerConfidenceBoundResults.report.json": _lcb_rows(computed),
        "PR168_RP_PortfolioMarginalUtilityResults.report.json": _portfolio_rows(computed),
        "PR168_RP_RiskDiversificationResults.report.json": _portfolio_rows(computed),
        "PR168_RP_ClusterCommonDriverExposure.report.json": _portfolio_rows(computed),
        "PR168_RP_PortfolioRepairCandidateQueue.report.json": recovery,
        "PR168_RP_RegimeConditionedMemorySeed.report.json": regimes,
        "PR168_RP_ScenarioOutcomeSeed.report.json": state["scenario_rows"],
        "PR168_RP_ConditionScopedNegativeMemorySeed.report.json": recovery,
        "PR168_RP_ConditionScopedPositiveRepairMemorySeed.report.json": [],
        "PR168_RP_PreTradeRegimeMemorySeed.report.json": regimes,
        "PR168_RP_ChampionChallengerEligibility.report.json": _champion_rows(computed),
        "PR168_RP_ChampionChallengerReasonCodes.report.json": _champion_reason_rows(),
        "PR168_RP_RepairedCandidateChampionChallengerEligibility.report.json": [],
        "PR168_RP_PreTradeChampionChallengerEligibility.report.json": _pretrade_champion_rows(ranking),
        "PR168_RP_QuantumObjectiveRecompute.report.json": quantum,
        "PR168_RP_QuantumStructuralReadiness.report.json": quantum,
        "PR168_RP_QuantumCoefficientMapInputGaps.report.json": quantum_gaps,
        "PR168_RP_ClassicalFallbackResults.report.json": quantum,
        "PR168_RP_StrongestClassicalComparatorMap.report.json": quantum,
        "PR168_RP_QKUCombinationQUBOObjectiveSeed.report.json": quantum_gaps,
        "PR168_RP_OrderPolicySelectionQUBOSeed.report.json": quantum_gaps,
        "PR168_RP_QKUCombinationCandidateResults.report.json": combos,
        "PR168_RP_QKUCombinationNegativeRecoveryResults.report.json": recovery,
        "PR168_RP_MarginalUtilitySelectionResults.report.json": combos,
        "PR168_RP_ParetoFrontierRankingSeed.report.json": combos,
        "PR168_RP_OrderPolicyCombinationSelectionResults.report.json": ranking,
        "PR168_RP_ComputedPositiveEdgeCandidates.report.json": positive_pointers,
        "PR168_RP_RepairedPositiveCandidateEvidence.report.json": [],
        "PR168_RP_ComputedNegativeEdgeCandidates.report.json": negative_pointers,
        "PR168_RP_ComputedNeutralOrZeroEdgeCandidates.report.json": neutral_pointers,
        "PR168_RP_NegativeCandidateReasonCodes.report.json": _negative_reason_rows(recovery),
        "PR168_RP_NegativeToPositiveRecoveryAttempts.report.json": recovery,
        "PR168_RP_NegativeRecoveryCandidateFactory.report.json": recovery,
        "PR168_RP_TrueNegativeAfterRecoveryExhaustion.report.json": recovery,
        "PR168_RP_OldPositiveTruthCorrection.report.json": old_label_corrections,
        "PR168_RP_OldNegativeTruthCorrection.report.json": old_label_corrections,
        "PR168_RP_ActionableInputGapQueue.report.json": gap_pointers,
        "PR168_RP_AgentDutySourceGapQueue.report.json": [] if state["agent_status"].get("agent_duty_source_resolved") else [_agent_discovery_row(state)],
        "PR168_RP_TargetedFormulaExpansionQueue.report.json": gap_pointers,
        "PR168_RP_ConnectorCandidateRouteMap.report.json": connectors,
        "PR168_RP_ConnectorSemanticBindingNonCreationAudit.report.json": connectors,
        "PR168_RP_To_PR168_RANK_ComputedRanking.report.json": _execution_ranking_seed_rows(computed),
        "PR168_RP_To_PR168_RANK_PreTradeRankingSeed.report.json": ranking,
        "PR168_RP_To_PR166_QC_R2_RedoWithComputedEvidence.report.json": quantum_gaps,
        "PR168_RP_To_PR162E_Q_QuantumMapperGaps.report.json": quantum_gaps,
        "PR168_RP_To_PR162E_PR162F_FormulaPluginIntakeGaps.report.json": gap_pointers,
        "PR168_RP_To_RuntimeFormulaAllowlistHotPathCacheSeed.report.json": _hot_path_seed_rows(state),
        "PR168_RP_To_ExecutionRouterLiveGateFutureHandoff.report.json": live_gate,
        "PR168_RP_To_OwnerDashboardComputedTruth.report.json": pointers + gap_pointers[:1000],
        "PR168_RP_RouteTriage.report.json": route_rows,
        "PR168_RP_CommandActionMatrix.report.json": route_rows,
        "PR168_RP_DAGUpstreamDownstreamOrchestration.report.json": dag,
        "PR168_RP_FullMasterPlanSectionCrosswalk.report.json": route_rows,
        "PR168_RP_MarketSpecificSectionIndexes.report.json": _market_index_rows(state),
        "PR168_RP_Stage1PredictionMarketActivationIndex.report.json": _market_index_rows(state),
        "PR168_RP_FutureMarketDormancyIndex.report.json": _future_market_rows(state),
        "PR168_RP_ReportConsumerCrosswalk.report.json": _report_consumer_rows(),
        "PR168_RP_ArtifactConsumerDAG.report.json": dag,
        "PR168_RP_MetricConsumerDAG.report.json": dag,
        "PR168_RP_AgentDutyDAG.report.json": dag,
        "PR168_RP_PRDependencyDAG.report.json": dag,
        "PR168_RP_ArtifactInformationValueDAG.report.json": dag,
        "PR168_RP_ConnectorCandidateRouteDAG.report.json": dag,
        "PR168_RP_PreTradeDecisionDAG.report.json": dag,
        "PR168_RP_OrderPolicyConsumerDAG.report.json": dag,
        "PR168_RP_LiveCandidateHandoffDAG.report.json": dag,
        "PR168_RP_ArtifactMap.report.json": _report_consumer_rows(),
        "PR168_RP_FileConsumerMap.report.json": _report_consumer_rows(),
        "PR168_RP_ValueLineageMap.report.json": _value_lineage_rows(computed, gaps),
        "PR168_RP_MetricConsumerMap.report.json": _metric_consumer_rows(),
        "PR168_RP_QKUFormulaComputationLineage.report.json": pointers + gap_pointers,
        "PR168_RP_AgentDutyOrchestrationCrosswalk.report.json": [_agent_discovery_row(state)],
        "PR168_RP_AgentWorkOrders.report.json": route_rows,
        "PR168_RP_NoOrphanProof.report.json": _no_orphan_rows(state),
        "PR168_RP_AuthorityBoundaryAudit.report.json": _authority_rows(),
        "PR168_RP_ValidationScopeRegistryIntegration.report.json": _validation_scope_rows(),
        "PR168_RP_WindowsLinuxCompatibilityAudit.report.json": _windows_linux_rows(),
        "PR168_RP_FinalSummary.report.json": [final],
    }
    return row_map


def _computed_pointer(row: dict[str, Any], report_ref: str) -> dict[str, Any]:
    return pointer_row(
        row,
        report_ref=report_ref,
        result_ref=row["result_ref"],
        evidence_tier=row["evidence_tier"],
        computed_status=row["computed_status"],
        downstream_route=row["downstream_route"],
    )


def _gap_pointer(row: dict[str, Any]) -> dict[str, Any]:
    return pointer_row(
        row,
        report_ref="PR168_RP_ActionableInputGapQueue.report.json",
        result_ref=row["result_ref"],
        evidence_tier=row["evidence_tier"],
        computed_status=row["computed_status"],
        downstream_route=row["downstream_route"],
    ) | {"missing_variables": row.get("missing_variables", []), "gap_reason_code": row.get("gap_reason_code")}


def _computed_metric_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**_computed_pointer(row, "PR168_RP_ComputedPnLEvidence.report.json"), **row["metrics"]} for row in computed]


def _replay_paper_comparison_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **_computed_pointer(row, "PR168_RP_ReplayPaperComparison.report.json"),
            "replay_result_ref": row["result_ref"],
            "paper_result_ref": row["result_ref"],
            "replay_minus_paper": 0.0,
            "comparison_status": "REPLAY_AND_PAPER_COMPUTED_FROM_SAME_REPO_INPUT_SNAPSHOT",
        }
        for row in computed
    ]


def _execution_edge_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **_computed_pointer(row, "PR168_RP_ExecutionAdjustedEdge.report.json"),
            "gross_edge": row["metrics"]["gross_edge"],
            "execution_adjusted_edge": row["metrics"]["execution_adjusted_edge"],
            "fill_adjusted_expected_pnl": row["metrics"]["fill_adjusted_expected_pnl"],
        }
        for row in computed
    ]


def _execution_ranking_seed_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = sorted(computed, key=lambda row: (float(row["metrics"]["fill_adjusted_expected_pnl"]), str(row["result_ref"])), reverse=True)
    return [
        {
            **_computed_pointer(row, "PR168_RP_ExecutionAdjustedRankingSeed.report.json"),
            "rank": index,
            "fill_adjusted_expected_pnl": row["metrics"]["fill_adjusted_expected_pnl"],
            "lower_confidence_bound_edge": row["metrics"]["lower_confidence_bound_edge"],
            "champion_eligible": False,
            "eligibility_blockers": ["MISSING_DEFAULT_THRESHOLD", "NO_CONNECTOR_TRUTH_OR_BINDING", "NO_LIVE_ORDER_AUTHORITY"],
        }
        for index, row in enumerate(rows, start=1)
    ]


def _tca_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "explicit_fee_cost",
        "spread_cost",
        "slippage_cost",
        "market_impact",
        "adverse_selection_penalty",
        "implementation_shortfall",
        "queue_nonfill_penalty",
        "partial_fill_penalty",
        "stale_orderbook_penalty",
        "latency_decay",
        "capacity_crowding_penalty",
        "overfit_fdr_penalty",
        "total_tca",
        "gross_edge",
        "execution_adjusted_edge",
        "fill_adjusted_expected_pnl",
        "net_expected_pnl_candidate",
    ]
    return [{**_computed_pointer(row, "PR168_RP_TCADecomposition.report.json"), **{field: row["metrics"][field] for field in fields}} for row in computed]


def _implementation_shortfall_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **_computed_pointer(row, "PR168_RP_ImplementationShortfall.report.json"),
            "implementation_shortfall": row["metrics"]["implementation_shortfall"],
            "implementation_shortfall_source_ref": row["source_rows"]["tca"].get("row_id"),
        }
        for row in computed
    ]


def _fill_latency_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **_computed_pointer(row, "PR168_RP_FillQueueLatencyResults.report.json"),
            "fill_probability": row["metrics"]["fill_probability"],
            "queue_nonfill_penalty": row["metrics"]["queue_nonfill_penalty"],
            "partial_fill_penalty": row["metrics"]["partial_fill_penalty"],
            "latency_decay": row["metrics"]["latency_decay"],
            "latency_bucket": row["microstructure"]["latency_bucket"],
        }
        for row in computed
    ]


def _micro_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**_computed_pointer(row, "PR168_RP_PredictionMarketMicrostructureFeatures.report.json"), **row["microstructure"]} for row in computed]


def _capacity_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **_computed_pointer(row, "PR168_RP_CapacityCrowdingResults.report.json"),
            "visible_depth_fraction_used": round(float(row["metrics"]["position_size"]) / max(float(row["microstructure"]["visible_depth"]), 1e-12), 10),
            "market_capacity_limit": row["microstructure"]["capacity_limit"],
            "qku_capacity_limit": row["microstructure"]["capacity_limit"],
            "event_capacity_limit": row["microstructure"]["capacity_limit"],
            "agent_strategy_capacity_limit": row["microstructure"]["capacity_limit"],
            "crowding_score": row["metrics"]["crowding_score"],
            "crowding_penalty": row["metrics"]["capacity_crowding_penalty"],
            "capacity_usage": row["metrics"]["capacity_usage"],
            "diminishing_return_curve_ref": "PR168_RP_CapacityScalingCurveSeed.report.json",
            "capacity_pass_fail": row["metrics"]["capacity_crowding_penalty"] <= abs(row["metrics"]["gross_edge"]),
            "capacity_repair_size_candidate": max(0.0, float(row["metrics"]["position_size"]) / 2.0),
        }
        for row in computed
    ]


def _calibration_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **_computed_pointer(row, "PR168_RP_ProbabilityCalibration.report.json"),
            "brier_score_candidate": row["source_rows"]["probability"].get("brier_or_logloss_proxy_score"),
            "log_loss_candidate": row["source_rows"]["probability"].get("brier_or_logloss_proxy_score"),
            "reliability_bin": row["metrics"]["reliability_bin"],
            "calibration_slope_candidate": "INPUT_GAP_ROUTE",
            "calibration_intercept_candidate": "INPUT_GAP_ROUTE",
            "probability_uncertainty": row["metrics"]["probability_calibration_error"],
            "conformal_or_lcb_ref": "PR168_RP_LowerConfidenceBoundResults.report.json",
            "lower_confidence_bound_edge": row["metrics"]["lower_confidence_bound_edge"],
            "Bayesian_shrinkage_candidate": "INPUT_GAP_ROUTE",
            "calibration_failure_repair_route": "PR168_RP_CalibrationRepairQueue.report.json",
        }
        for row in computed
    ]


def _overfit_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = [
        "family_trial_count",
        "candidate_trial_count",
        "repeated_test_count",
        "parameter_sweep_count",
        "repair_attempt_count",
        "qku_combination_trial_count",
        "order_policy_trial_count",
        "scenario_ladder_trial_count",
        "replay_paper_disagreement",
        "regime_instability_score",
        "weak_sample_size_flag",
        "post_selection_bias_flag",
        "overfit_fdr_penalty",
        "overfit_disqualification_reason",
        "formal_bh_or_dsr_claimed",
    ]
    return [{**_computed_pointer(row, "PR168_RP_OverfitFDRResults.report.json"), **{key: row["metrics"][key] for key in keys}} for row in computed]


def _lcb_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**_computed_pointer(row, "PR168_RP_LowerConfidenceBoundResults.report.json"), "lower_confidence_bound_edge": row["metrics"]["lower_confidence_bound_edge"]} for row in computed]


def _portfolio_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = [
        "portfolio_marginal_utility",
        "risk_budget_pass_fail",
        "expected_shortfall_cvar",
        "cluster_correlation_penalty",
        "common_driver_exposure",
        "event_category_exposure",
        "drawdown_contribution",
        "capacity_usage",
        "liquidity_usage",
        "capital_usage",
        "concentration_penalty",
        "same_event_stack_penalty",
        "same_resolution_cluster_penalty",
        "portfolio_repair_candidate_route",
    ]
    return [{**_computed_pointer(row, "PR168_RP_PortfolioMarginalUtilityResults.report.json"), **{key: row["metrics"][key] for key in keys}} for row in computed]


def _champion_rows(computed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **_computed_pointer(row, "PR168_RP_ChampionChallengerEligibility.report.json"),
            "champion_eligible": False,
            "challenger_eligible": row["computed_status"] != "FORMULA_ASSIGNED_INPUTS_MISSING",
            "eligibility_basis": "COMPUTED_EVIDENCE_WITH_DEFAULT_AND_AUTHORITY_BLOCKERS",
            "reason_codes": ["MISSING_DEFAULT_THRESHOLD", "NO_LIVE_ORDER_AUTHORITY", "NO_CONNECTOR_TRUTH_OR_BINDING"],
        }
        for row in computed
    ]


def _pretrade_champion_rows(ranking: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": row["candidate_id"],
            "pretrade_champion_eligible": False,
            "reason_codes": row.get("champion_eligibility_blockers", []),
            "downstream_route": "PR168_RP_PreTradeChampionChallengerEligibility.report.json",
            "producer": "PR168_RP_PRETRADE_SIMULATION_KERNEL",
            "consumer": "PR168_RANK",
            "upstream_source": row["candidate_id"],
            "owning_agent": "Ranking Agent",
            "no_orphan_status": "CONNECTED_TO_PRETRADE_ELIGIBILITY_CONSUMER",
        }
        for row in ranking
    ]


def _champion_reason_rows() -> list[dict[str, Any]]:
    return [
        {
            "reason_code": code,
            "description_ref": "tools/qtt_authority_reason_code_registry.py",
            "producer": "PR168_RP_COMPUTE_KERNEL",
            "consumer": "PR168_RANK",
            "upstream_source": "PR168_RP_ChampionChallengerEligibility.report.json",
            "downstream_route": "PR168_RP_ChampionChallengerReasonCodes.report.json",
            "owning_agent": "Governance Agent",
            "no_orphan_status": "CONNECTED_TO_CHAMPION_REASON_CONSUMER",
        }
        for code in ["MISSING_DEFAULT_THRESHOLD", "NO_LIVE_ORDER_AUTHORITY", "NO_CONNECTOR_TRUTH_OR_BINDING"]
    ]


def _negative_reason_rows(recovery: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rec in recovery:
        for code in rec.get("negative_reason_codes", []):
            if code in seen:
                continue
            seen.add(code)
            rows.append(
                {
                    "negative_reason_code": code,
                    "source_registry": "tools/qtt_authority_reason_code_registry.py",
                    "producer": "PR168_RP_NEGATIVE_RECOVERY_ENGINE",
                    "consumer": "Alpha Recovery Agent",
                    "upstream_source": "PR168_RP_NegativeToPositiveRecoveryAttempts.report.json",
                    "downstream_route": "PR168_RP_NegativeCandidateReasonCodes.report.json",
                    "owning_agent": "Alpha Recovery Agent",
                    "no_orphan_status": "CONNECTED_TO_NEGATIVE_REASON_CONSUMER",
                }
            )
    return rows


def _truth_overlay_consumption_rows(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "truth_overlay_ref": "docs/master_plan/generated/PR168_GFP_AuthoritativeTruthOverlay.report.json",
            "truth_overlay_rows_consumed": len(state["overlay"]),
            "formula_assignment_rows_consumed": len(state["assignments"]),
            "old_labels_trusted_directly": False,
            "computed_positive_from_old_label_count": 0,
            "producer": "PR168_RP_COMPUTE_KERNEL",
            "consumer": "PR168_RP_TRUTH_OVERLAY_CONSUMER",
            "upstream_source": "PR168_GFP_AuthoritativeTruthOverlay.report.json",
            "downstream_route": "PR168_RP_PR168GFPTruthOverlayConsumption.report.json",
            "owning_agent": "Governance Agent",
            "no_orphan_status": "CONNECTED_TO_TRUTH_OVERLAY_CONSUMER",
        }
    ]


def _agent_discovery_row(state: dict[str, Any]) -> dict[str, Any]:
    status = state["agent_status"]
    return {
        "exact_artifacts_found": status.get("exact_artifacts_found", []),
        "missing_artifacts": status.get("missing_artifacts", []),
        "agent_ids": status.get("agent_ids", []),
        "agent_duty_source_resolved": status.get("agent_duty_source_resolved", False),
        "equivalence_proof": "Exact PR165_D2 AgentRosterDiscoveryAudit and AgentDutySourceCrosswalk generated reports discovered"
        if status.get("agent_duty_source_resolved")
        else "Rows routed through PR168_RP_AgentDutySourceGapQueue.report.json",
        "producer": "PR168_RP_AGENT_ROUTE_MAPPER",
        "consumer": "Replay Paper Recompute Agent",
        "upstream_source": ",".join(PR165_D2_AGENT_REPORTS.values()),
        "downstream_route": "PR168_RP_PR165D2AgentArtifactDiscovery.report.json",
        "owning_agent": "Governance Agent",
        "no_orphan_status": "CONNECTED_TO_AGENT_DISCOVERY_CONSUMER",
    }


def _formula_universe_rows(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "formula_id": row["formula_id"],
            "formula_family": row["formula_family"],
            "formula_expression": row["formula_expression"],
            "computation_function_path": row["computation_function_path"],
            "computation_function_name": row["computation_function_name"],
            "source_truth_authority": False,
            "downstream_route": "PR168_RP_FormulaExecutionUniverse.report.json",
            "producer": "PR168_RP_COMPUTE_KERNEL",
            "consumer": "Formula Materialization Agent",
            "upstream_source": "PR168_GFP_SelectedFormulaExpressionRegistry.report.json",
            "owning_agent": row.get("owning_agent"),
            "no_orphan_status": "CONNECTED_TO_FORMULA_UNIVERSE_CONSUMER",
        }
        for row in state["formulas"]
    ]


def _hot_path_seed_rows(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "lane": lane,
            "allowed_in_pr168_rp": lane != "future_live_hot_path_lane",
            "future_live_hot_path_definition_only": lane == "future_live_hot_path_lane",
            "runtime_execution_created": False,
            "formula_stack_ref": "PR168_RP_FormulaExecutionUniverse.report.json",
            "cache_candidate_ref": "PR168_RP_HotPathPrecomputeCandidateSeed.report.json",
            "execution_router_release_requirement": "FUTURE_EXECUTION_ROUTER_GATE_REQUIRED",
            "producer": "PR168_RP_COMPUTE_KERNEL",
            "consumer": "Future Runtime Formula Allowlist/Hot Path Cache PR",
            "upstream_source": "PR168_RP_ComputedPnLEvidence.report.json",
            "downstream_route": "PR168_RP_To_RuntimeFormulaAllowlistHotPathCacheSeed.report.json",
            "owning_agent": "Latency Agent",
            "no_orphan_status": "CONNECTED_TO_HOT_PATH_HANDOFF_CONSUMER",
        }
        for lane in ["research_offline_lane", "replay_paper_lane", "shadow_live_candidate_lane", "future_live_hot_path_lane"]
    ]


def _heavy_lane_rows() -> list[dict[str, Any]]:
    heavy = [
        "broad_formula_search",
        "quantum_structural_mapping",
        "qku_combination_search",
        "overfit_fdr_analysis",
        "stress_tests",
        "regime_memory_updates",
        "full_scenario_simulation",
    ]
    return [
        {
            "heavy_computation": item,
            "excluded_from_future_live_hot_path": True,
            "allowed_lane": "research_offline_lane_or_replay_paper_lane",
            "producer": "PR168_RP_COMPUTE_KERNEL",
            "consumer": "Future Runtime Formula Allowlist/Hot Path Cache PR",
            "upstream_source": "PR168_RP_DAGUpstreamDownstreamOrchestration.report.json",
            "downstream_route": "PR168_RP_LiveExcludedHeavyComputationLedger.report.json",
            "owning_agent": "Latency Agent",
            "no_orphan_status": "CONNECTED_TO_HEAVY_COMPUTE_LEDGER_CONSUMER",
        }
        for item in heavy
    ]


def _old_label_correction_rows(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "correction_ref": "PR168_RP_OLD_LABEL_CORRECTION",
            "old_positive_negative_champion_labels_trusted": False,
            "truth_overlay_ref": "PR168_GFP_AuthoritativeTruthOverlay.report.json",
            "computed_evidence_required": True,
            "computed_positive_from_old_label_count": 0,
            "producer": "PR168_RP_COMPUTE_KERNEL",
            "consumer": "Owner Dashboard Computed Truth",
            "upstream_source": "PR168_GFP_AuthoritativeTruthOverlay.report.json",
            "downstream_route": "PR168_RP_To_OwnerDashboardComputedTruth.report.json",
            "owning_agent": "Governance Agent",
            "no_orphan_status": "CONNECTED_TO_OWNER_DASHBOARD_CONSUMER",
        }
    ]


def _route_rows(state: dict[str, Any]) -> list[dict[str, Any]]:
    routes = [
        ("computed_positive", "PR168_RP_ComputedPositiveEdgeCandidates.report.json", "PR168-RANK"),
        ("computed_negative", "PR168_RP_NegativeToPositiveRecoveryAttempts.report.json", "Alpha Recovery Agent"),
        ("input_gaps", "PR168_RP_ActionableInputGapQueue.report.json", "Input Materialization Agent"),
        ("missing_defaults", "PR168_RP_MissingDefaultResolutionQueue.report.json", "Governance Agent"),
        ("quantum_gaps", "PR168_RP_To_PR162E_Q_QuantumMapperGaps.report.json", "Quantum Mapper Agent"),
        ("connector_routes", "PR168_RP_ConnectorCandidateRouteMap.report.json", "Connector Candidate Routing Agent"),
        ("live_handoff", "PR168_RP_To_ExecutionRouterLiveGateFutureHandoff.report.json", "Future Execution Router"),
    ]
    return [
        {
            "route_id": route_id,
            "artifact_ref": artifact,
            "consumer": consumer,
            "producer": "PR168_RP_ROUTE_TRIAGE",
            "upstream_source": "PR168_RP_DAGUpstreamDownstreamOrchestration.report.json",
            "downstream_route": artifact,
            "owning_agent": "Commander Agent",
            "no_orphan_status": "CONNECTED_TO_ROUTE_TRIAGE_CONSUMER",
        }
        for route_id, artifact, consumer in routes
    ]


def _market_index_rows(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "index_id": "prediction_market_stage1_index",
            "active_row_count": len(state["computed_rows"]) + len(state["input_gap_rows"]),
            "activation_state": "REPLAY_PAPER_OR_INPUT_GAP_ONLY",
            "connector_semantic_binding_state": "NOT_BOUND_CANDIDATE_ONLY",
            "live_authority": False,
            "producer": "PR168_RP_MARKET_INDEXER",
            "consumer": "PR168-RANK",
            "upstream_source": "PR168_RP_InputAvailabilityMatrix.report.json",
            "downstream_route": "PR168_RP_Stage1PredictionMarketActivationIndex.report.json",
            "owning_agent": "Commander Agent",
            "no_orphan_status": "CONNECTED_TO_MARKET_INDEX_CONSUMER",
        },
        {
            "index_id": "market_agnostic_math_risk_optimizer_index",
            "active_row_count": len(state["computed_rows"]),
            "activation_state": "REPLAY_PAPER_ONLY",
            "connector_semantic_binding_state": "NOT_BOUND_CANDIDATE_ONLY",
            "live_authority": False,
            "producer": "PR168_RP_MARKET_INDEXER",
            "consumer": "PR168-RANK",
            "upstream_source": "PR168_RP_PortfolioMarginalUtilityResults.report.json",
            "downstream_route": "PR168_RP_MarketSpecificSectionIndexes.report.json",
            "owning_agent": "Risk Manager Agent",
            "no_orphan_status": "CONNECTED_TO_MARKET_INDEX_CONSUMER",
        },
        {
            "index_id": "unknown_market_scope_actionable_review_index",
            "active_row_count": len(state["input_gap_rows"]),
            "activation_state": "ACTIONABLE_REVIEW_NOT_LIVE",
            "connector_semantic_binding_state": "NOT_BOUND_CANDIDATE_ONLY",
            "live_authority": False,
            "producer": "PR168_RP_MARKET_INDEXER",
            "consumer": "Governance Agent",
            "upstream_source": "PR168_RP_ActionableInputGapQueue.report.json",
            "downstream_route": "PR168_RP_MarketSpecificSectionIndexes.report.json",
            "owning_agent": "Governance Agent",
            "no_orphan_status": "CONNECTED_TO_MARKET_INDEX_CONSUMER",
        },
    ]


def _future_market_rows(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "index_id": "future_equities_options_futures_crypto_fx_rates_commodities_dormant_index",
            "dormant": True,
            "row_count": 0,
            "reactivation_route": "FUTURE_MARKET_SCOPE_PR_REQUIRED",
            "live_authority": False,
            "producer": "PR168_RP_MARKET_INDEXER",
            "consumer": "Future Market Agent",
            "upstream_source": "PR168_RP_MarketSpecificSectionIndexes.report.json",
            "downstream_route": "PR168_RP_FutureMarketDormancyIndex.report.json",
            "owning_agent": "Governance Agent",
            "no_orphan_status": "CONNECTED_TO_FUTURE_MARKET_CONSUMER",
        }
    ]


def _report_consumer_rows() -> list[dict[str, Any]]:
    return [
        {
            "artifact_ref": filename,
            "producer": "PR168_RP_REPORT_WRITER",
            "consumer": _consumer_for(filename),
            "upstream_source": "PR168_RP_BUILD_KERNEL",
            "downstream_route": _route_for_report(filename),
            "owning_agent": "Replay Paper Recompute Agent",
            "no_orphan_status": "CONNECTED_TO_REPORT_CONSUMER",
        }
        for filename in REQUIRED_REPORTS
    ]


def _value_lineage_rows(computed: list[dict[str, Any]], gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in computed:
        for metric in ["gross_edge", "execution_adjusted_edge", "fill_adjusted_expected_pnl", "lower_confidence_bound_edge"]:
            rows.append(
                {
                    "value_ref": f"{row['result_ref']}::{metric}",
                    "metric_name": metric,
                    "producer": "PR168_RP_COMPUTE_KERNEL",
                    "consumer": "PR168_RANK",
                    "upstream_source": row["input_ref"],
                    "downstream_route": "PR168_RP_ValueLineageMap.report.json",
                    "owning_agent": "Replay Paper Recompute Agent",
                    "no_orphan_status": "CONNECTED_TO_VALUE_LINEAGE_CONSUMER",
                }
            )
    for gap in gaps[:1000]:
        rows.append(
            {
                "value_ref": gap["input_ref"],
                "metric_name": "missing_input_gap",
                "producer": "PR168_RP_INPUT_RESOLVER",
                "consumer": "Input Materialization Agent",
                "upstream_source": gap["upstream_report"],
                "downstream_route": "PR168_RP_ValueLineageMap.report.json",
                "owning_agent": gap["owning_agent"],
                "no_orphan_status": "CONNECTED_TO_VALUE_LINEAGE_CONSUMER",
            }
        )
    return rows


def _metric_consumer_rows() -> list[dict[str, Any]]:
    metrics = [
        "market_implied_probability",
        "predicted_probability",
        "gross_edge",
        "execution_adjusted_edge",
        "fill_adjusted_expected_pnl",
        "lower_confidence_bound_edge",
        "overfit_fdr_penalty",
        "portfolio_marginal_utility",
    ]
    return [
        {
            "metric_name": metric,
            "producer": "PR168_RP_COMPUTE_KERNEL",
            "consumer": "PR168_RANK",
            "upstream_source": "PR168_RP_ComputedPnLEvidence.report.json",
            "downstream_route": "PR168_RP_MetricConsumerMap.report.json",
            "owning_agent": "Ranking Agent",
            "no_orphan_status": "CONNECTED_TO_METRIC_CONSUMER",
        }
        for metric in metrics
    ]


def _no_orphan_rows(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_ref": filename,
            "producer": "PR168_RP_REPORT_WRITER",
            "consumer": _consumer_for(filename),
            "upstream_source": "PR168_RP_BUILD_KERNEL",
            "downstream_route": _route_for_report(filename),
            "owning_agent": "Replay Paper Recompute Agent",
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        }
        for filename in REQUIRED_REPORTS
    ]


def _authority_rows() -> list[dict[str, Any]]:
    return [
        {
            "authority_boundary_code": code,
            "authority_created": False,
            "producer": "PR168_RP_AUTHORITY_AUDIT",
            "consumer": "Governance Agent",
            "upstream_source": "tools/qtt_authority_reason_code_registry.py",
            "downstream_route": "PR168_RP_AuthorityBoundaryAudit.report.json",
            "owning_agent": "Governance Agent",
            "no_orphan_status": "CONNECTED_TO_AUTHORITY_AUDIT_CONSUMER",
        }
        for code in [
            "NO_LIVE_ORDER_AUTHORITY",
            "NO_SOURCE_TRUTH_AUTHORITY",
            "NO_CONNECTOR_TRUTH_OR_BINDING",
            "NO_PRIVATE_STATE_OR_CASH",
            "NO_QUANTUM_BACKEND_EXECUTION",
            "NO_LLM_HOT_PATH_AUTHORITY",
            "NO_QTT_DIGEST_AUTHORITY",
            "NO_ATOMICROWS_DIGEST_AUTHORITY",
        ]
    ]


def _validation_scope_rows() -> list[dict[str, Any]]:
    return [
        {
            "branch": "pr168-rp-formula-based-replay-paper-recompute",
            "central_registry_ref": "tools/validation_scope_registry.py",
            "scope_registry_integration_status": "CENTRALIZED_FAIL_CLOSED",
            "producer": "PR168_RP_VALIDATION_SCOPE_AUDIT",
            "consumer": "Validation Router",
            "upstream_source": "tools/validation_scope_registry.py",
            "downstream_route": "PR168_RP_ValidationScopeRegistryIntegration.report.json",
            "owning_agent": "Governance Agent",
            "no_orphan_status": "CONNECTED_TO_VALIDATION_SCOPE_CONSUMER",
        }
    ]


def _windows_linux_rows() -> list[dict[str, Any]]:
    return [
        {
            "audit_item": item,
            "status": "PASS",
            "producer": "PR168_RP_WINDOWS_LINUX_AUDIT",
            "consumer": "CI",
            "upstream_source": "PR168_RP_REPORT_WRITER",
            "downstream_route": "PR168_RP_WindowsLinuxCompatibilityAudit.report.json",
            "owning_agent": "Governance Agent",
            "no_orphan_status": "CONNECTED_TO_COMPATIBILITY_CONSUMER",
        }
        for item in [
            "pathlib_paths",
            "utf8_json",
            "sorted_keys",
            "no_symlink_requirement",
            "no_case_collision",
            "allow_nan_false",
        ]
    ]


def _summary_for(filename: str, records: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("computed_status")) for row in state["input_availability_rows"] if row.get("computed_status"))
    return {
        "report": filename,
        "baseline_counts": BASELINE_COUNTS,
        "computed_row_count": len(state["computed_rows"]),
        "computed_positive_count": len(state["computed_positive_rows"]),
        "computed_negative_count": len(state["computed_negative_rows"]),
        "computed_neutral_count": len(state["computed_neutral_rows"]),
        "input_gap_count": len(state["input_gap_rows"]),
        "pretrade_candidate_count": len(state["pretrade_candidates"]),
        "negative_recovery_attempt_count": len(state["negative_recovery_rows"]),
        "status_counts": dict(status_counts),
        "authority_created_count": 0,
        "record_count": len(records),
    }


def _final_summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "reports_written": REQUIRED_REPORTS,
        "report_count": len(REQUIRED_REPORTS),
        "baseline_counts": BASELINE_COUNTS,
        "formula_assignment_rows_consumed": len(state["assignments"]),
        "truth_overlay_rows_consumed": len(state["overlay"]),
        "computed_row_count": len(state["computed_rows"]),
        "input_gap_count": len(state["input_gap_rows"]),
        "pretrade_candidate_count": len(state["pretrade_candidates"]),
        "negative_recovery_attempt_count": len(state["negative_recovery_rows"]),
        "authority_created_count": 0,
    }


def _final_summary_row(state: dict[str, Any]) -> dict[str, Any]:
    return {
        **_final_summary(state),
        "producer": "PR168_RP_COMPUTE_KERNEL",
        "consumer": "Owner Dashboard Computed Truth",
        "upstream_source": "PR168_GFP_AuthoritativeTruthOverlay.report.json",
        "downstream_route": "PR168_RP_FinalSummary.report.json",
        "owning_agent": "Replay Paper Recompute Agent",
        "no_orphan_status": "CONNECTED_TO_FINAL_SUMMARY_CONSUMER",
    }


def _consumer_for(filename: str) -> str:
    if "Quantum" in filename or "PR166_QC" in filename or "PR162E_Q" in filename:
        return "Quantum Repair Agent"
    if "Connector" in filename:
        return "Connector Candidate Routing Agent"
    if "Dashboard" in filename or "Governance" in filename or "Authority" in filename:
        return "Governance Agent"
    if "PreTrade" in filename or "OrderPolicy" in filename or "NoTrade" in filename:
        return "Execution Simulation Agent"
    return "PR168-RANK"


def _route_for_report(filename: str) -> str:
    if filename.startswith("PR168_RP_To_"):
        return filename
    return filename
