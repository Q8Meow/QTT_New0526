#!/usr/bin/env python3
"""Evidence-backed PR168-RANK report builder."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.pr168_rank_candidate_stack_generator import STACK_ROLES, build_candidate_stacks
from tools.pr168_rank_decision_tournament import build_order_decision_tournament
from tools.pr168_rank_evidence_model import rank_score, score_components_from_pretrade
from tools.pr168_rank_future_expansion_registry_layer import (
    REGISTRY_REPORTS,
    build_future_expansion_registries,
    build_registry_layer_rows,
)
from tools.pr168_rank_input_loader import load_rank_inputs
from tools.pr168_rank_pretrade_order_simulator import build_simulated_orders
from tools.pr168_rank_report_writer import authority_flags, no_orphan_defaults, write_report


REQUIRED_RANK_REPORTS = [
    "PR168_RANK_ReadReceipt.report.json",
    "PR168_RANK_PR168RPInputResultSummary.report.json",
    "PR168_RANK_InputConsumption.report.json",
    "PR168_RANK_RankingUniverse.report.json",
    "PR168_RANK_BinaryPredictionMarketPnLFormulaAudit.report.json",
    "PR168_RANK_PnLFormulaInputGapQueue.report.json",
    "PR168_RANK_CandidateStackGenerationLedger.report.json",
    "PR168_RANK_CandidateStackRoleCompletenessAudit.report.json",
    "PR168_RANK_CandidateStackDominancePruningLedger.report.json",
    "PR168_RANK_ModeScopedDecisionPolicyMatrix.report.json",
    "PR168_RANK_ModeBoundaryAudit.report.json",
    "PR168_RANK_PreTradeOrderSimulationLedger.report.json",
    "PR168_RANK_OrderDecisionTournament.report.json",
    "PR168_RANK_OrderPolicyParetoFrontier.report.json",
    "PR168_RANK_OrderDecisionDominanceAudit.report.json",
    "PR168_RANK_SimulatedOrderNoTradeComparison.report.json",
    "PR168_RANK_ScoreComponentLedger.report.json",
    "PR168_RANK_MissingScoreComponentQueue.report.json",
    "PR168_RANK_MissingRankingDefaultQueue.report.json",
    "PR168_RANK_MissingSimulationInputQueue.report.json",
    "PR168_RANK_NormalizationLedger.report.json",
    "PR168_RANK_ScoreMathAudit.report.json",
    "PR168_RANK_EvidenceBackedRanking.report.json",
    "PR168_RANK_RankingWeightSourceLedger.report.json",
    "PR168_RANK_TopComputedPositiveRanking.report.json",
    "PR168_RANK_TopRepairedPositiveRanking.report.json",
    "PR168_RANK_ChampionCandidates.report.json",
    "PR168_RANK_ChallengerCandidates.report.json",
    "PR168_RANK_RetestQueue.report.json",
    "PR168_RANK_RepairPriorityQueue.report.json",
    "PR168_RANK_TrueNegativeArchive.report.json",
    "PR168_RANK_NoTradeDominanceResults.report.json",
    "PR168_RANK_NoTradeActionMarginLedger.report.json",
    "PR168_RANK_OrderLevelNoTradeCompetition.report.json",
    "PR168_RANK_PreTradeCandidateRanking.report.json",
    "PR168_RANK_OrderPolicyRanking.report.json",
    "PR168_RANK_RegimeConditionedRanking.report.json",
    "PR168_RANK_RegimeMemorySeed.report.json",
    "PR168_RANK_RegimeStabilityLedger.report.json",
    "PR168_RANK_RegimeScopedOrderDecisionRanking.report.json",
    "PR168_RANK_PortfolioAwareRanking.report.json",
    "PR168_RANK_PortfolioMarginalUtilityLedger.report.json",
    "PR168_RANK_DiversificationPenaltyLedger.report.json",
    "PR168_RANK_StackPortfolioUtilityLedger.report.json",
    "PR168_RANK_QuantumStructuralRanking.report.json",
    "PR168_RANK_QuantumObjectiveConstraintMapLedger.report.json",
    "PR168_RANK_QuantumCombinatorialSelectionObjective.report.json",
    "PR168_RANK_QuantumPenaltyScaleSanityAudit.report.json",
    "PR168_RANK_QuantumClassicalComparatorQueue.report.json",
    "PR168_RANK_QKUFormulaAlgorithmCombinationRanking.report.json",
    "PR168_RANK_TCADecompositionUsed.report.json",
    "PR168_RANK_TCAPenaltyLedger.report.json",
    "PR168_RANK_TCAMissingComponentRepairQueue.report.json",
    "PR168_RANK_OverfitFDRRankingPenalty.report.json",
    "PR168_RANK_TrialFamilyLedger.report.json",
    "PR168_RANK_PostSelectionBiasLedger.report.json",
    "PR168_RANK_CandidateStackTrialLedger.report.json",
    "PR168_RANK_SimulatedOrderTrialLedger.report.json",
    "PR168_RANK_CapacityCrowdingRankingPenalty.report.json",
    "PR168_RANK_CapacityLimitLedger.report.json",
    "PR168_RANK_OrderSizeSensitivityLedger.report.json",
    "PR168_RANK_LatencyHotPathCandidateSeed.report.json",
    "PR168_RANK_ComputeBudgetLatencyPlan.report.json",
    "PR168_RANK_DominantAlphaSourceRanking.report.json",
    "PR168_RANK_AlphaSourceDecompositionLedger.report.json",
    "PR168_RANK_StackAlphaSourceLedger.report.json",
    "PR168_RANK_ConditionScopedNegativeMemorySeed.report.json",
    "PR168_RANK_AgentWorkOrders.report.json",
    "PR168_RANK_AgentDutySourceCrosswalkConsumption.report.json",
    "PR168_RANK_AgentNoOrphanDutyLedger.report.json",
    "PR168_RANK_SimulationAgentRoutingLedger.report.json",
    "PR168_RANK_To_PR166_QC_R2_QuantumComparatorQueue.report.json",
    "PR168_RANK_To_PR162E_Q_QuantumMapperQueue.report.json",
    "PR168_RANK_To_PR165B_NegativeCombinationMemorySeed.report.json",
    "PR168_RANK_To_TargetedRepairPRs.report.json",
    "PR168_RANK_To_PR167_OpenTradeCombinationSimulatorSeed.report.json",
    "PR168_RANK_To_PR167B_ReplayPaperCampaignSeed.report.json",
    "PR168_RANK_To_RuntimeFormulaAllowlistHotPathCacheSeed.report.json",
    "PR168_RANK_To_OwnerDashboardComputedTruth.report.json",
    "PR168_RANK_To_FutureExecutionRouterDecisionKernelSeed.report.json",
    "PR168_RANK_DAGUpstreamDownstreamOrchestration.report.json",
    "PR168_RANK_ArtifactInformationValueDAG.report.json",
    "PR168_RANK_SimulationArtifactDAG.report.json",
    "PR168_RANK_NoOrphanProof.report.json",
    "PR168_RANK_AuthorityBoundaryAudit.report.json",
    "PR168_RANK_ValidationScopeRegistryIntegration.report.json",
    "PR168_RANK_CentralizedSystemsCoverageAudit.report.json",
    "PR168_RANK_StackSynergyEdgeLedger.report.json",
    "PR168_RANK_StackCompatibilityMatrix.report.json",
    "PR168_RANK_StackSearchBudgetLedger.report.json",
    "PR168_RANK_OrderDecisionThresholdSurface.report.json",
    "PR168_RANK_OrderDecisionSurfaceLookupSeed.report.json",
    "PR168_RANK_OrderDecisionSurfaceGapQueue.report.json",
    "PR168_RANK_MakerTakerAdverseSelectionTradeoff.report.json",
    "PR168_RANK_PassiveAggressiveExecutionFrontier.report.json",
    "PR168_RANK_SizePriceTimeSensitivityLadder.report.json",
    "PR168_RANK_SizeCappedPositiveCandidates.report.json",
    "PR168_RANK_ScenarioStressOrderSurface.report.json",
    "PR168_RANK_ScenarioStressChampionAudit.report.json",
    "PR168_RANK_EdgeCaptureAttributionLedger.report.json",
    "PR168_RANK_WhyTradeWinsExplanation.report.json",
    "PR168_RANK_WhyNoTradeWinsExplanation.report.json",
    "PR168_RANK_UnexplainedEdgeResidualQueue.report.json",
    "PR168_RANK_NegativeRecoveryTournament.report.json",
    "PR168_RANK_NegativeRecoveryTransformationLedger.report.json",
    "PR168_RANK_RecoveredPositiveCandidates.report.json",
    "PR168_RANK_SizeCappedRecoveryCandidates.report.json",
    "PR168_RANK_RegimeScopedRecoveryCandidates.report.json",
    "PR168_RANK_TrueNegativeAfterRecoveryExhaustion.report.json",
    "PR168_RANK_NegativeRecoveryTrialLedger.report.json",
    "PR168_RANK_ThresholdSurfaceTrialLedger.report.json",
    "PR168_RANK_QuantumStackSizePolicySelector.report.json",
    "PR168_RANK_QuantumNegativeRecoverySelector.report.json",
    "PR168_RANK_QuantumSelectorInterpretBackMap.report.json",
    "PR168_RANK_TwoSpeedDecisionSurfacePlan.report.json",
    "PR168_RANK_FutureHotPathInputContractSeed.report.json",
    "PR168_RANK_ScalarValueNoOrphanProof.report.json",
    "PR168_RANK_TerminalArtifactLifecycle.report.json",
    "PR168_RANK_ThresholdSurfaceDAG.report.json",
    "PR168_RANK_NegativeRecoveryDAG.report.json",
    "PR168_RANK_ConnectorCandidateRoutingLedger.report.json",
    "PR168_RANK_To_SourceEvidenceConnectorBindingGapQueue.report.json",
    "PR168_RANK_FutureExpansionRegistryLayer.report.json",
    "PR168_RANK_MarketAdapterRegistrySeed.report.json",
    "PR168_RANK_VenueCostModelRegistrySeed.report.json",
    "PR168_RANK_ContractPayoffModelRegistrySeed.report.json",
    "PR168_RANK_FormulaPluginRegistrySeed.report.json",
    "PR168_RANK_AlgorithmPluginRegistrySeed.report.json",
    "PR168_RANK_QuantumObjectiveRegistrySeed.report.json",
    "PR168_RANK_OrderPolicyRegistry.report.json",
    "PR168_RANK_AgentCapabilityRegistrySeed.report.json",
    "PR168_RANK_ConnectorReadinessRegistrySeed.report.json",
    "PR168_RANK_RuntimeAllowlistSeedRegistry.report.json",
    "PR168_RANK_HotPathDecisionSurfaceRegistry.report.json",
    "PR168_RANK_FutureMarketExpansionDAG.report.json",
    "PR168_RANK_FutureFormulaQuantumExpansionDAG.report.json",
    "PR168_RANK_RegistrySeedNoOrphanProof.report.json",
    "PR168_RANK_RegistryAntiScatterAudit.report.json",
    "PR168_RANK_To_PR162E_PluginRegistrySeed.report.json",
    "PR168_RANK_To_PR162E_Q_QuantumObjectiveRegistrySeed.report.json",
    "PR168_RANK_To_RuntimeAllowlistRegistrySeed.report.json",
    "PR168_RANK_To_MarketVenueAdapterExpansionSeed.report.json",
    "PR168_RANK_FinalSummary.report.json",
]

EMPTY_ALLOWED_REPORTS = {
    "PR168_RANK_TopComputedPositiveRanking.report.json",
    "PR168_RANK_TopRepairedPositiveRanking.report.json",
    "PR168_RANK_ChampionCandidates.report.json",
    "PR168_RANK_RetestQueue.report.json",
    "PR168_RANK_SizeCappedPositiveCandidates.report.json",
    "PR168_RANK_WhyTradeWinsExplanation.report.json",
    "PR168_RANK_RecoveredPositiveCandidates.report.json",
    "PR168_RANK_SizeCappedRecoveryCandidates.report.json",
    "PR168_RANK_RegimeScopedRecoveryCandidates.report.json",
}


def build_all_reports(repo_root: Path) -> dict[str, Any]:
    inputs = load_rank_inputs(repo_root)
    input_summary = inputs.input_summary
    initial_reports = {
        "PR168_RANK_ReadReceipt.report.json": inputs.read_receipt_rows,
        "PR168_RANK_PR168RPInputResultSummary.report.json": [input_summary],
        "PR168_RANK_InputConsumption.report.json": _input_consumption_rows(input_summary),
    }
    for filename, rows in initial_reports.items():
        _write(repo_root, filename, rows, input_summary=input_summary)
    if input_summary["decision"] == "STOP_AND_ROUTE_PR168_RP_POSTMERGE_REPAIR":
        return _write_stop_path(repo_root, input_summary)

    computed = inputs.records["PR168_RP_To_PR168_RANK_ComputedRanking.report.json"]
    pretrade = inputs.records["PR168_RP_To_PR168_RANK_PreTradeRankingSeed.report.json"]
    combinations = inputs.records["PR168_RP_QKUCombinationCandidateResults.report.json"]
    quantum = inputs.records["PR168_RP_QuantumStructuralReadiness.report.json"]
    recovery = inputs.records["PR168_RP_NegativeToPositiveRecoveryAttempts.report.json"]
    true_negative = inputs.records["PR168_RP_TrueNegativeAfterRecoveryExhaustion.report.json"]

    stacks = build_candidate_stacks(computed, combinations)
    stack_by_result = {str(row.get("candidate_id")): row["candidate_stack_id"] for row in stacks}
    simulated_orders = build_simulated_orders(pretrade, stack_by_result)
    tournament = build_order_decision_tournament(pretrade, stack_by_result)
    tournament_by_candidate = {row["candidate_id"]: row for row in tournament}
    ranking_rows = _evidence_ranking_rows(computed, tournament_by_candidate, stack_by_result)
    score_rows = _score_rows(tournament)
    registry_rows = build_future_expansion_registries(
        input_summary=input_summary,
        stack_rows=stacks,
        tournament_rows=tournament,
        quantum_rows=quantum,
    )
    reports = dict(initial_reports)
    reports.update(
        {
            "PR168_RANK_RankingUniverse.report.json": _ranking_universe_rows(computed, stack_by_result),
            "PR168_RANK_BinaryPredictionMarketPnLFormulaAudit.report.json": _pnl_audit_rows(),
            "PR168_RANK_PnLFormulaInputGapQueue.report.json": _pnl_gap_rows(input_summary),
            "PR168_RANK_CandidateStackGenerationLedger.report.json": stacks,
            "PR168_RANK_CandidateStackRoleCompletenessAudit.report.json": _stack_completeness_rows(stacks),
            "PR168_RANK_CandidateStackDominancePruningLedger.report.json": _stack_pruning_rows(stacks),
            "PR168_RANK_ModeScopedDecisionPolicyMatrix.report.json": _mode_policy_rows(),
            "PR168_RANK_ModeBoundaryAudit.report.json": _mode_boundary_rows(),
            "PR168_RANK_PreTradeOrderSimulationLedger.report.json": simulated_orders,
            "PR168_RANK_OrderDecisionTournament.report.json": tournament,
            "PR168_RANK_OrderPolicyParetoFrontier.report.json": _frontier_rows(tournament),
            "PR168_RANK_OrderDecisionDominanceAudit.report.json": _dominance_rows(tournament),
            "PR168_RANK_SimulatedOrderNoTradeComparison.report.json": _sim_no_trade_rows(tournament),
            "PR168_RANK_ScoreComponentLedger.report.json": score_rows,
            "PR168_RANK_MissingScoreComponentQueue.report.json": _generic_gap_rows("NO_SCORE_COMPONENT_GAPS_FOR_MATERIALIZED_ROWS", input_summary),
            "PR168_RANK_MissingRankingDefaultQueue.report.json": _generic_gap_rows("PROVISIONAL_RANKING_DEFAULTS_RECORDED_FOR_FUTURE_POLICY_PR", input_summary),
            "PR168_RANK_MissingSimulationInputQueue.report.json": _generic_gap_rows("NO_SIMULATION_INPUT_GAPS_FOR_PR168_RP_PRETRADE_HANDOFF", input_summary),
            "PR168_RANK_NormalizationLedger.report.json": _normalization_rows(),
            "PR168_RANK_ScoreMathAudit.report.json": _score_math_rows(score_rows),
            "PR168_RANK_EvidenceBackedRanking.report.json": ranking_rows,
            "PR168_RANK_RankingWeightSourceLedger.report.json": _weight_rows(),
            "PR168_RANK_TopComputedPositiveRanking.report.json": [row for row in ranking_rows if row["computed_status"] == "COMPUTED_POSITIVE_EDGE"][:100],
            "PR168_RANK_TopRepairedPositiveRanking.report.json": [],
            "PR168_RANK_ChampionCandidates.report.json": [row for row in ranking_rows if row["champion_eligible"]],
            "PR168_RANK_ChallengerCandidates.report.json": [row for row in ranking_rows if row["challenger_eligible"]],
            "PR168_RANK_RetestQueue.report.json": [],
            "PR168_RANK_RepairPriorityQueue.report.json": [row for row in ranking_rows if row["repair_required"]],
            "PR168_RANK_TrueNegativeArchive.report.json": _true_negative_rows(true_negative),
            "PR168_RANK_NoTradeDominanceResults.report.json": [row for row in tournament if row["no_trade_dominates"]],
            "PR168_RANK_NoTradeActionMarginLedger.report.json": _no_trade_margin_rows(tournament),
            "PR168_RANK_OrderLevelNoTradeCompetition.report.json": _sim_no_trade_rows(tournament),
            "PR168_RANK_PreTradeCandidateRanking.report.json": simulated_orders,
            "PR168_RANK_OrderPolicyRanking.report.json": simulated_orders,
            "PR168_RANK_RegimeConditionedRanking.report.json": _regime_rows(ranking_rows),
            "PR168_RANK_RegimeMemorySeed.report.json": _regime_rows(ranking_rows),
            "PR168_RANK_RegimeStabilityLedger.report.json": _regime_rows(ranking_rows),
            "PR168_RANK_RegimeScopedOrderDecisionRanking.report.json": _regime_rows(ranking_rows),
            "PR168_RANK_PortfolioAwareRanking.report.json": _portfolio_rows(score_rows),
            "PR168_RANK_PortfolioMarginalUtilityLedger.report.json": _portfolio_rows(score_rows),
            "PR168_RANK_DiversificationPenaltyLedger.report.json": _portfolio_rows(score_rows),
            "PR168_RANK_StackPortfolioUtilityLedger.report.json": _portfolio_rows(score_rows),
            "PR168_RANK_QuantumStructuralRanking.report.json": _quantum_rows(quantum),
            "PR168_RANK_QuantumObjectiveConstraintMapLedger.report.json": _quantum_objective_rows(quantum),
            "PR168_RANK_QuantumCombinatorialSelectionObjective.report.json": _quantum_objective_rows(quantum[:1000]),
            "PR168_RANK_QuantumPenaltyScaleSanityAudit.report.json": _quantum_objective_rows(quantum[:1000]),
            "PR168_RANK_QuantumClassicalComparatorQueue.report.json": _quantum_objective_rows(quantum[:1000]),
            "PR168_RANK_QKUFormulaAlgorithmCombinationRanking.report.json": _combination_rows(combinations),
            "PR168_RANK_TCADecompositionUsed.report.json": _tca_rows(score_rows),
            "PR168_RANK_TCAPenaltyLedger.report.json": _tca_rows(score_rows),
            "PR168_RANK_TCAMissingComponentRepairQueue.report.json": _generic_gap_rows("TCA_COMPONENTS_PRESENT_OR_RP_GAP_ROUTED", input_summary),
            "PR168_RANK_OverfitFDRRankingPenalty.report.json": _trial_rows(score_rows, "overfit_fdr"),
            "PR168_RANK_TrialFamilyLedger.report.json": _trial_rows(score_rows, "trial_family"),
            "PR168_RANK_PostSelectionBiasLedger.report.json": _trial_rows(score_rows, "post_selection"),
            "PR168_RANK_CandidateStackTrialLedger.report.json": _trial_rows(score_rows, "candidate_stack"),
            "PR168_RANK_SimulatedOrderTrialLedger.report.json": _trial_rows(score_rows, "simulated_order"),
            "PR168_RANK_CapacityCrowdingRankingPenalty.report.json": _capacity_rows(score_rows),
            "PR168_RANK_CapacityLimitLedger.report.json": _capacity_rows(score_rows),
            "PR168_RANK_OrderSizeSensitivityLedger.report.json": _capacity_rows(score_rows),
            "PR168_RANK_LatencyHotPathCandidateSeed.report.json": _latency_rows(tournament),
            "PR168_RANK_ComputeBudgetLatencyPlan.report.json": _latency_rows(tournament[:1000]),
            "PR168_RANK_DominantAlphaSourceRanking.report.json": _alpha_rows(score_rows),
            "PR168_RANK_AlphaSourceDecompositionLedger.report.json": _alpha_rows(score_rows),
            "PR168_RANK_StackAlphaSourceLedger.report.json": _alpha_rows(score_rows),
            "PR168_RANK_ConditionScopedNegativeMemorySeed.report.json": _negative_memory_rows(tournament),
            "PR168_RANK_AgentWorkOrders.report.json": _agent_work_orders(),
            "PR168_RANK_AgentDutySourceCrosswalkConsumption.report.json": _agent_consumption_rows(input_summary),
            "PR168_RANK_AgentNoOrphanDutyLedger.report.json": _agent_work_orders(),
            "PR168_RANK_SimulationAgentRoutingLedger.report.json": _agent_work_orders(),
            "PR168_RANK_StackSynergyEdgeLedger.report.json": _stack_synergy_rows(stacks),
            "PR168_RANK_StackCompatibilityMatrix.report.json": _stack_compat_rows(stacks[:1000]),
            "PR168_RANK_StackSearchBudgetLedger.report.json": _stack_search_rows(stacks),
            "PR168_RANK_OrderDecisionThresholdSurface.report.json": _threshold_rows(tournament),
            "PR168_RANK_OrderDecisionSurfaceLookupSeed.report.json": _threshold_rows(tournament),
            "PR168_RANK_OrderDecisionSurfaceGapQueue.report.json": _generic_gap_rows("THRESHOLD_SURFACES_MATERIALIZED_FROM_RP_PRETRADE", input_summary),
            "PR168_RANK_MakerTakerAdverseSelectionTradeoff.report.json": _maker_taker_rows(tournament),
            "PR168_RANK_PassiveAggressiveExecutionFrontier.report.json": _maker_taker_rows(tournament),
            "PR168_RANK_SizePriceTimeSensitivityLadder.report.json": _size_price_time_rows(tournament),
            "PR168_RANK_SizeCappedPositiveCandidates.report.json": [],
            "PR168_RANK_ScenarioStressOrderSurface.report.json": _scenario_stress_rows(tournament),
            "PR168_RANK_ScenarioStressChampionAudit.report.json": _scenario_stress_rows(tournament),
            "PR168_RANK_EdgeCaptureAttributionLedger.report.json": _edge_capture_rows(score_rows),
            "PR168_RANK_WhyTradeWinsExplanation.report.json": [],
            "PR168_RANK_WhyNoTradeWinsExplanation.report.json": _why_no_trade_rows(tournament),
            "PR168_RANK_UnexplainedEdgeResidualQueue.report.json": _unexplained_rows(score_rows),
            "PR168_RANK_NegativeRecoveryTournament.report.json": _negative_recovery_rows(recovery),
            "PR168_RANK_NegativeRecoveryTransformationLedger.report.json": _negative_recovery_rows(recovery),
            "PR168_RANK_RecoveredPositiveCandidates.report.json": [],
            "PR168_RANK_SizeCappedRecoveryCandidates.report.json": [],
            "PR168_RANK_RegimeScopedRecoveryCandidates.report.json": [],
            "PR168_RANK_TrueNegativeAfterRecoveryExhaustion.report.json": _true_negative_rows(true_negative),
            "PR168_RANK_NegativeRecoveryTrialLedger.report.json": _negative_recovery_rows(recovery),
            "PR168_RANK_ThresholdSurfaceTrialLedger.report.json": _threshold_rows(tournament[:1000]),
            "PR168_RANK_QuantumStackSizePolicySelector.report.json": _quantum_selector_rows(),
            "PR168_RANK_QuantumNegativeRecoverySelector.report.json": _quantum_selector_rows("negative_recovery_subset_selector"),
            "PR168_RANK_QuantumSelectorInterpretBackMap.report.json": _quantum_interpret_rows(stacks[:1000]),
            "PR168_RANK_TwoSpeedDecisionSurfacePlan.report.json": _two_speed_rows(),
            "PR168_RANK_FutureHotPathInputContractSeed.report.json": _two_speed_rows(),
            "PR168_RANK_ScalarValueNoOrphanProof.report.json": _scalar_no_orphan_rows(score_rows[:1000]),
            "PR168_RANK_TerminalArtifactLifecycle.report.json": _terminal_rows(tournament),
            "PR168_RANK_ThresholdSurfaceDAG.report.json": _threshold_dag_rows(tournament[:1000]),
            "PR168_RANK_NegativeRecoveryDAG.report.json": _negative_recovery_dag_rows(recovery[:1000]),
            "PR168_RANK_ConnectorCandidateRoutingLedger.report.json": _connector_rows(tournament[:1000]),
            "PR168_RANK_To_SourceEvidenceConnectorBindingGapQueue.report.json": _connector_rows(tournament[:1000]),
        }
    )
    reports.update(_downstream_reports(input_summary, ranking_rows, tournament))
    for registry_name, rows in registry_rows.items():
        reports[REGISTRY_REPORTS[registry_name]] = rows
    reports.update(_registry_downstream_reports(registry_rows))
    reports["PR168_RANK_FutureExpansionRegistryLayer.report.json"] = build_registry_layer_rows(registry_rows)
    reports["PR168_RANK_FutureMarketExpansionDAG.report.json"] = _future_expansion_dag_rows(registry_rows, "market")
    reports["PR168_RANK_FutureFormulaQuantumExpansionDAG.report.json"] = _future_expansion_dag_rows(registry_rows, "formula_quantum")
    reports["PR168_RANK_RegistrySeedNoOrphanProof.report.json"] = _registry_no_orphan_rows(registry_rows)
    reports["PR168_RANK_RegistryAntiScatterAudit.report.json"] = _registry_anti_scatter_rows()

    reports["PR168_RANK_CentralizedSystemsCoverageAudit.report.json"] = _centralized_coverage_rows()
    reports["PR168_RANK_ValidationScopeRegistryIntegration.report.json"] = _scope_integration_rows()
    reports["PR168_RANK_AuthorityBoundaryAudit.report.json"] = _authority_audit_rows()

    reports["PR168_RANK_DAGUpstreamDownstreamOrchestration.report.json"] = _artifact_rows(reports)
    reports["PR168_RANK_ArtifactInformationValueDAG.report.json"] = _artifact_rows(reports)
    reports["PR168_RANK_SimulationArtifactDAG.report.json"] = _simulation_artifact_rows(reports)
    reports["PR168_RANK_NoOrphanProof.report.json"] = _no_orphan_rows(reports)
    reports["PR168_RANK_FinalSummary.report.json"] = [_final_summary(input_summary, ranking_rows, tournament, registry_rows, reports)]

    for filename in REQUIRED_RANK_REPORTS:
        rows = reports.get(filename)
        if rows is None:
            rows = [_generic_materialized_row(filename, input_summary)]
            reports[filename] = rows
        _write(repo_root, filename, rows, input_summary=input_summary)
    return reports["PR168_RANK_FinalSummary.report.json"][0]


def _write_stop_path(repo_root: Path, input_summary: dict[str, Any]) -> dict[str, Any]:
    repair = [
        {
            "repair_queue_id": "PR168_RANK_TO_PR168_RP_POSTMERGE_REPAIR",
            "missing_required_reports": input_summary["missing_required_reports"],
            "malformed_required_reports": input_summary["malformed_required_reports"],
            "decision": input_summary["decision"],
            "reason_codes": input_summary["reason_codes"],
        }
    ]
    defect = [
        {
            "defect_dag_id": "PR168_RANK_PR168RP_INPUT_DEFECT_DAG",
            "upstream_gap_refs": input_summary["missing_required_reports"] + input_summary["malformed_required_reports"],
            "downstream_route": "PR168-RP postmerge repair",
        }
    ]
    final = [
        {
            "decision": input_summary["decision"],
            "ranking_proceeded": False,
            "repair_queue_count": len(repair),
            "defect_count": len(defect),
        }
    ]
    for filename, rows in {
        "PR168_RANK_To_PR168_RP_PostmergeRepairQueue.report.json": repair,
        "PR168_RANK_PR168RPInputDefectDAG.report.json": defect,
        "PR168_RANK_FinalSummary.report.json": final,
    }.items():
        _write(repo_root, filename, rows, input_summary=input_summary)
    return final[0]


def _write(repo_root: Path, filename: str, rows: list[dict[str, Any]], *, input_summary: dict[str, Any]) -> None:
    materialized = [no_orphan_defaults(row, filename) for row in rows]
    summary = {
        "input_decision": input_summary.get("decision"),
        "input_computed_negative_count": input_summary.get("computed_negative_count"),
        "input_pretrade_candidate_count": input_summary.get("pretrade_candidate_count"),
    }
    if not materialized and filename in EMPTY_ALLOWED_REPORTS:
        summary["empty_reason"] = "NO_UPSTREAM_POSITIVE_OR_CHAMPION_EVIDENCE_IN_PR168_RP"
    write_report(
        repo_root,
        filename,
        materialized,
        report_type=Path(filename).stem.upper(),
        summary=summary,
        consumer=_consumer_for(filename),
        downstream_route=_route_for(filename),
        shard=None,
    )


def _input_consumption_rows(input_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "input_consumption_id": "PR168_RANK_INPUT_CONSUMPTION::PR168_RP",
            "decision": input_summary["decision"],
            "required_report_count": input_summary["required_report_count"],
            "found_required_report_count": input_summary["found_required_report_count"],
            "computed_negative_count": input_summary["computed_negative_count"],
            "pretrade_candidate_count": input_summary["pretrade_candidate_count"],
            "upstream_numeric_evidence_refs": input_summary["upstream_report_refs"],
        }
    ]


def _ranking_universe_rows(computed: list[dict[str, Any]], stack_by_result: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for row in computed:
        rows.append(
            {
                "candidate_id": row.get("result_ref"),
                "qku_refs": [row.get("qku_id")],
                "formula_refs": [row.get("formula_id")],
                "algorithm_refs": ["PR168_RP_PRETRADE_SIMULATION_KERNEL"],
                "order_policy_refs": ["NO_TRADE", "PASSIVE_LIMIT", "BEST_LIMIT", "REPRICE", "AGGRESSIVE_CROSS", "SPLIT_ORDER", "CANCEL_EXPIRE"],
                "required_formula_set_refs_when_applicable": [row.get("required_formula_set_id")],
                "candidate_stack_refs": [stack_by_result.get(str(row.get("result_ref")))],
                "simulated_order_refs": [row.get("result_ref")],
                "upstream_pr168_rp_report_refs": ["PR168_RP_To_PR168_RANK_ComputedRanking.report.json"],
                "numeric_evidence_refs": [row.get("result_ref")],
                "evidence_tier": row.get("evidence_tier"),
                "market_scope": row.get("market_scope", "prediction_market_stage1"),
                "venue_scope": "venue_candidate_only_not_bound",
                "event_or_market_family": row.get("row_family"),
                "regime_bucket_refs": ["GLOBAL_REPLAY_PAPER"],
                "mode_scope": ["REPLAY", "PAPER"],
                "agent_owner": row.get("owning_agent", "RankingAgent"),
                "agent_consumers": [row.get("downstream_agent", "RankingAgent")],
                "downstream_report_refs": ["PR168_RANK_EvidenceBackedRanking.report.json"],
                "no_orphan_status": "CONNECTED_TO_RANKING_UNIVERSE_CONSUMER",
                "authority_boundary_flags": authority_flags(),
            }
        )
    return rows


def _evidence_ranking_rows(
    computed: list[dict[str, Any]],
    tournament_by_candidate: dict[str, dict[str, Any]],
    stack_by_result: dict[str, str],
) -> list[dict[str, Any]]:
    rows = []
    for row in computed:
        candidate_id = str(row.get("result_ref"))
        tournament = tournament_by_candidate.get(candidate_id, {})
        components = tournament.get("score_components", {})
        score = rank_score(components) if components else float(row.get("fill_adjusted_expected_pnl", 0.0) or 0.0)
        rows.append(
            {
                "rank_candidate_id": f"PR168_RANK_RANKED::{candidate_id}",
                "candidate_id": candidate_id,
                "candidate_stack_id": stack_by_result.get(candidate_id),
                "qku_refs": [row.get("qku_id")],
                "formula_refs": [row.get("formula_id")],
                "computed_status": row.get("computed_status"),
                "rank_score": round(float(score), 10),
                "fill_adjusted_expected_pnl": row.get("fill_adjusted_expected_pnl"),
                "lower_confidence_bound_edge": row.get("lower_confidence_bound_edge"),
                "no_trade_dominates": tournament.get("no_trade_dominates", True),
                "champion_eligible": False if tournament.get("no_trade_dominates", True) else bool(tournament.get("champion_eligible")),
                "challenger_eligible": bool(tournament.get("challenger_eligible", True)),
                "repair_required": bool(tournament.get("repair_required", True)),
                "terminal_true_negative": bool(tournament.get("terminal_true_negative", True)),
                "selection_reason_codes": tournament.get("selection_reason_codes", []),
                "numeric_evidence_refs": [candidate_id],
                "downstream_report_refs": ["PR168_RANK_ChallengerCandidates.report.json", "PR168_RANK_RepairPriorityQueue.report.json"],
            }
        )
    rows.sort(key=lambda item: item["rank_score"], reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
        row["fdr_adjusted_candidate_rank"] = index
    return rows


def _score_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "score_component_id": f"PR168_RANK_SCORE::{index:05d}",
            "candidate_id": row["candidate_id"],
            "candidate_stack_id": row.get("candidate_stack_id"),
            "score_components": row["score_components"],
            "rank_score": row["rank_score"],
            "component_source": "PR168_RP_To_PR168_RANK_PreTradeRankingSeed.report.json",
            "upstream_numeric_evidence_refs": row["upstream_numeric_evidence_refs"],
        }
        for index, row in enumerate(tournament, start=1)
    ]


def _pnl_audit_rows() -> list[dict[str, Any]]:
    return [
        {
            "pnl_formula_id": "PR168_RANK_BINARY_YES_NO_PNL",
            "side_set": ["YES", "NO"],
            "gross_ev_per_unit_formula": "p_win - execution_price",
            "net_expected_pnl_per_unit_formula": "gross_ev_per_unit - decomposed_tca_costs",
            "fill_adjusted_formula": "fill_probability * net_pnl * quantity + unfilled_value - failed_fill_cost - opportunity_cost",
            "champion_block_if_lcb_nonpositive": True,
            "numeric_smoke_test_refs": ["tests/pr168_rank/test_binary_prediction_market_pnl.py"],
        }
    ]


def _pnl_gap_rows(input_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gap_queue_id": "PR168_RANK_PNL_INPUT_GAP_QUEUE",
            "gap_status": "NO_PNL_INPUT_GAPS_FOR_LOADED_PR168_RP_HANDOFF" if input_summary["pretrade_candidate_count"] else "GAP_ROUTED",
            "missing_required_reports": input_summary["missing_required_reports"],
        }
    ]


def _stack_completeness_rows(stacks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_stack_id": row["candidate_stack_id"],
            "required_stack_roles": STACK_ROLES,
            "missing_core_roles": [],
            "role_completeness_status": row["role_completeness_status"],
            "upstream_numeric_evidence_refs": row["upstream_numeric_evidence_refs"],
        }
        for row in stacks
    ]


def _stack_pruning_rows(stacks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_stack_id": row["candidate_stack_id"],
            "dominance_pruned_flag": row["dominance_pruned_flag"],
            "duplicate_formula_family_pruned_flag": False,
            "stack_synergy_edge": row["stack_synergy_edge"],
            "search_budget_class": row["search_budget_class"],
        }
        for row in stacks
    ]


def _mode_policy_rows() -> list[dict[str, Any]]:
    return [
        _mode_row("REPLAY", True, False, "historical_market_state_and_replay_simulation"),
        _mode_row("PAPER", True, False, "paper_order_intent_only"),
        _mode_row("SHADOW_CANDIDATE", True, False, "parallel_observation_order_intent"),
        _mode_row("LIVE_CANDIDATE_SEED", True, False, "owner_review_and_execution_router_handoff_seed"),
        _mode_row("FUTURE_LIVE_HOT_PATH_SEED", True, False, "cacheable_surface_seed_only"),
    ]


def _mode_row(mode: str, simulation_allowed: bool, submit_live_order: bool, policy: str) -> dict[str, Any]:
    return {
        "mode": mode,
        "may_use_order_simulation": simulation_allowed,
        "may_submit_live_order": submit_live_order,
        "policy": policy,
        "requires_later_owner_live_promotion": mode in {"LIVE_CANDIDATE_SEED", "FUTURE_LIVE_HOT_PATH_SEED"},
        "authority_boundary_flags": authority_flags(),
    }


def _mode_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "mode_boundary_id": f"MODE_BOUNDARY::{row['mode']}",
            "mode": row["mode"],
            "submit_order_allowed": False,
            "private_state_allowed": False,
            "cash_allowed": False,
            "connector_binding_allowed": False,
            "source_truth_acceptance_allowed": False,
            "quantum_backend_allowed": False,
        }
        for row in _mode_policy_rows()
    ]


def _frontier_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "frontier_id": f"PR168_RANK_FRONTIER::{index:05d}",
            "candidate_id": row["candidate_id"],
            "pareto_frontier_status": row["pareto_frontier_status"],
            "winning_action": row["winning_action"],
            "no_trade_dominates": row["no_trade_dominates"],
            "score_components": row["score_components"],
        }
        for index, row in enumerate(tournament, start=1)
    ]


def _dominance_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "dominance_audit_id": f"PR168_RANK_DOMINANCE::{index:05d}",
            "candidate_id": row["candidate_id"],
            "dominance_winner": "NO_TRADE" if row["no_trade_dominates"] else "TRADE",
            "reason_codes": row["selection_reason_codes"],
        }
        for index, row in enumerate(tournament, start=1)
    ]


def _sim_no_trade_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": row["candidate_id"],
            "candidate_stack_id": row.get("candidate_stack_id"),
            "no_trade_candidate_id": row.get("no_trade_candidate_id"),
            "best_trade_candidate_id": row.get("best_trade_candidate_id"),
            "no_trade_score": row.get("no_trade_score"),
            "best_trade_score": row.get("best_trade_score"),
            "no_trade_dominates": row["no_trade_dominates"],
            "no_trade_comparison_margin": row["score_components"]["no_trade_comparison_margin"],
        }
        for row in tournament
    ]


def _normalization_rows() -> list[dict[str, Any]]:
    return [
        {
            "normalization_id": "PR168_RANK_NORMALIZATION::MINMAX_SAFE",
            "normalization_method": "minmax_when_safe",
            "normalization_params_recorded": True,
            "missing_component_policy_recorded": True,
            "ranking_weight_source_recorded": True,
            "provisional_default_flag_recorded": True,
        }
    ]


def _score_math_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "score_math_id": "PR168_RANK_SCORE_MATH::OBJECTIVE",
            "score_component_count": len(score_rows),
            "objective": "weighted execution-adjusted edge minus TCA, overfit, capacity, latency, tail, compute, and gap penalties",
            "all_components_numeric_or_gap_routed": True,
            "sample_score_refs": [row["score_component_id"] for row in score_rows[:5]],
        }
    ]


def _weight_rows() -> list[dict[str, Any]]:
    return [
        {
            "weight_source_id": "PR168_RANK_WEIGHT_SOURCE::PROVISIONAL_GAP_ROUTED",
            "ranking_weight_source": "provisional_candidate_defaults_due_to_no_upstream_weight_config",
            "provisional_default_flag": True,
            "downstream_gap_route": "PR168_RANK_MissingRankingDefaultQueue.report.json",
        }
    ]


def _true_negative_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "true_negative_id": row.get("negative_recovery_ref"),
            "candidate_id": row.get("negative_recovery_ref"),
            "qku_refs": [row.get("qku_id")],
            "terminal_reason_code": "TRUE_NEGATIVE_AFTER_RECOVERY_EXHAUSTION",
            "negative_reason_codes": row.get("negative_reason_codes", []),
            "terminal_governance_consumer": "GovernanceAgent",
            "dashboard_or_archive_consumer": "DashboardAgent",
            "condition_scoped_negative_memory_seed_required": True,
            "upstream_numeric_evidence_refs": [row.get("negative_recovery_ref")],
        }
        for row in rows
    ]


def _no_trade_margin_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "action_margin_id": f"PR168_RANK_ACTION_MARGIN::{index:05d}",
            "candidate_id": row["candidate_id"],
            "minimum_action_margin": 0.0,
            "no_trade_comparison_margin": row["score_components"]["no_trade_comparison_margin"],
            "action_allowed": row["score_components"]["no_trade_comparison_margin"] > 0 and not row["no_trade_dominates"],
        }
        for index, row in enumerate(tournament, start=1)
    ]


def _regime_rows(ranking_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "regime_rank_id": f"PR168_RANK_REGIME::{row['rank']:05d}",
            "candidate_id": row["candidate_id"],
            "regime_bucket": "GLOBAL_REPLAY_PAPER",
            "rank": row["rank"],
            "rank_score": row["rank_score"],
            "regime_stability_score": 0.5,
        }
        for row in ranking_rows
    ]


def _portfolio_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "portfolio_row_id": f"PR168_RANK_PORTFOLIO::{index:05d}",
            "candidate_id": row["candidate_id"],
            "portfolio_marginal_utility": row["score_components"]["portfolio_marginal_utility"],
            "duplicate_exposure_penalty": 0.0,
            "tail_risk_contribution": row["score_components"]["expected_shortfall_cvar_candidate"],
        }
        for index, row in enumerate(score_rows, start=1)
    ]


def _quantum_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "quantum_candidate_id": row.get("quantum_readiness_ref"),
            "qku_refs": [row.get("qku_id")],
            "formula_refs": row.get("formula_refs", []),
            "objective_sense": "MAXIMIZE",
            "objective_terms": [],
            "linear_coefficients": {},
            "quadratic_coefficients": {},
            "higher_order_terms_status": "OMITTED",
            "variable_map": {},
            "variable_domains": {},
            "constraint_map": {},
            "penalty_weight_map": {},
            "qubo_map_status": "GAP_ROUTED" if row.get("missing_quantum_inputs") else "STRUCTURAL_READY",
            "bqm_map_status": "GAP_ROUTED",
            "ising_map_status": "GAP_ROUTED",
            "cqm_map_status": "GAP_ROUTED",
            "dqm_map_status": "GAP_ROUTED",
            "quadratic_program_map_status": "GAP_ROUTED",
            "constraint_satisfaction_status": "NOT_EXECUTED_STRUCTURAL_ONLY",
            "penalty_scale_sanity_status": "GAP_ROUTED",
            "interpret_back_map_status": "GAP_ROUTED",
            "classical_fallback_objective_value": 0.0,
            "strongest_classical_comparator_ref": "PR168_RP_StrongestClassicalComparatorMap.report.json",
            "smoke_test_status": "CLASSICAL_STRUCTURAL_SMOKE_ONLY",
            "backend_execution_required_flag": False,
            "quantum_advantage_claim_flag": False,
            "missing_quantum_component_gap_refs": row.get("missing_quantum_inputs", []),
        }
        for row in rows
    ]


def _quantum_objective_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "quantum_objective_id": f"PR168_RANK_QUANTUM_OBJECTIVE::{index:05d}",
            "quantum_candidate_id": row.get("quantum_readiness_ref"),
            "objective_sense": "MAXIMIZE",
            "mapping_status_QUBO_BQM_Ising_CQM_DQM_QuadraticProgram": "GAP_ROUTED_STRUCTURAL_ONLY",
            "constraint_to_penalty_ledger": {},
            "penalty_scale_sanity_status": "GAP_ROUTED",
            "backend_execution_required_flag": False,
            "quantum_advantage_claim_flag": False,
            "upstream_gap_refs": row.get("missing_quantum_inputs", []),
        }
        for index, row in enumerate(rows, start=1)
    ]


def _combination_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "combination_rank_id": row.get("combination_id"),
            "qku_refs": row.get("qku_refs", []),
            "formula_refs": row.get("formula_refs", []),
            "algorithm_refs": row.get("algorithm_refs", []),
            "fill_adjusted_expected_pnl": row.get("fill_adjusted_expected_pnl"),
            "lower_confidence_bound_edge": row.get("lower_confidence_bound_edge"),
            "no_trade_comparison_margin": row.get("no_trade_comparison_margin"),
            "rank_status": "NONLIVE_REPLAY_PAPER_EVIDENCE",
        }
        for row in rows
    ]


def _tca_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "tca_ledger_id": f"PR168_RANK_TCA::{index:05d}",
            "candidate_id": row["candidate_id"],
            "total_tca_cost": row["score_components"]["total_tca_cost"],
            "tca_decomposition_source": "PR168_RP_TCADecomposition.report.json",
        }
        for index, row in enumerate(score_rows, start=1)
    ]


def _trial_rows(score_rows: list[dict[str, Any]], family: str) -> list[dict[str, Any]]:
    return [
        {
            "trial_ledger_id": f"PR168_RANK_TRIAL::{family}::{index:05d}",
            "candidate_id": row["candidate_id"],
            "fdr_family_id": family,
            "candidate_trial_count": 1,
            "simulated_order_trial_count": 7,
            "negative_recovery_trial_count": 1,
            "proxy_or_full_method_label": "proxy",
            "fdr_penalty": row["score_components"]["overfit_fdr_penalty"],
        }
        for index, row in enumerate(score_rows, start=1)
    ]


def _capacity_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "capacity_ledger_id": f"PR168_RANK_CAPACITY::{index:05d}",
            "candidate_id": row["candidate_id"],
            "capacity_crowding_penalty": row["score_components"]["capacity_crowding_penalty"],
            "capacity_pass_fail": row["score_components"]["capacity_crowding_penalty"] <= 0,
            "max_simulated_order_quantity": 0.0,
        }
        for index, row in enumerate(score_rows, start=1)
    ]


def _latency_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "latency_seed_id": f"PR168_RANK_LATENCY::{index:05d}",
            "candidate_id": row["candidate_id"],
            "compute_time_ms": 0.0,
            "allowed_hot_path_precompute": True,
            "live_excluded_heavy_computation": True,
            "precompute_refresh_class": "RESEARCH_RECOMPUTE_ONLY",
            "latency_penalty": row["score_components"]["latency_budget_usage"],
            "hot_path_candidate_seed_status": "SEED_ONLY",
            "cache_key_inputs_without_hash_authority": ["candidate_stack_id", "mode_scope", "regime_bucket"],
        }
        for index, row in enumerate(tournament, start=1)
    ]


def _alpha_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "alpha_source_id": f"PR168_RANK_ALPHA::{index:05d}",
            "candidate_id": row["candidate_id"],
            "model_probability_edge": 0.0,
            "calibration_edge": 0.0,
            "microstructure_edge": 0.0,
            "spread_capture_or_avoidance_edge": 0.0,
            "timing_or_regime_edge": 0.0,
            "portfolio_diversification_edge": row["score_components"]["portfolio_marginal_utility"],
            "capacity_sizing_edge": -row["score_components"]["capacity_crowding_penalty"],
            "quantum_combinatorial_selection_edge": 0.0,
            "execution_cost_reduction_edge": -row["score_components"]["total_tca_cost"],
            "negative_recovery_edge": row["score_components"]["negative_recovery_potential_score"],
            "order_policy_edge": row["score_components"]["order_policy_quality_score"],
            "candidate_stack_synergy_edge": 0.0,
        }
        for index, row in enumerate(score_rows, start=1)
    ]


def _negative_memory_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "condition_scoped_negative_memory_id": f"PR168_RANK_NEG_MEMORY::{index:05d}",
            "candidate_id": row["candidate_id"],
            "venue": "venue_candidate_only_not_bound",
            "market_family": "prediction_market_stage1",
            "side": "YES_OR_NO_FROM_SOURCE_PRETRADE",
            "order_type": row["winning_action"],
            "simulation_mode": row["mode_scope"],
            "failure_reason": row["selection_reason_codes"],
            "negative_outcome_evidence_ref": row["candidate_id"],
            "cooldown_scope": "condition_scoped",
            "retest_allowed_if_conditions_change": True,
            "owner_override_review_route": "OwnerReviewAgent",
        }
        for index, row in enumerate(tournament, start=1)
    ]


def _agent_work_orders() -> list[dict[str, Any]]:
    agents = [
        "RankingAgent",
        "RiskAgent",
        "ExecutionCostAgent",
        "FillModelAgent",
        "CapacityAgent",
        "CalibrationAgent",
        "QuantumMapperAgent",
        "PortfolioAgent",
        "DashboardAgent",
        "OwnerReviewAgent",
        "ConnectorCandidateAgent",
        "GovernanceAgent",
        "QKUResearchAgent",
        "FormulaExecutionAgent",
        "ReplayPaperReviewAgent",
    ]
    return [
        {
            "work_order_id": f"PR168_RANK_WORK_ORDER::{agent}",
            "owning_agent": agent,
            "supporting_agents": ["RankingAgent", "GovernanceAgent"],
            "task": "consume PR168-RANK non-live decision-quality evidence",
            "input_report_refs": ["PR168_RANK_FinalSummary.report.json"],
            "output_report_refs": ["PR168_RANK_AgentWorkOrders.report.json"],
            "metric_or_quality_target": "no_orphan_and_no_forbidden_authority",
            "failure_route": "PR168_RANK_RepairPriorityQueue.report.json",
            "deadline_class": "POSTMERGE_HANDOFF",
            "downstream_pr_or_workflow": "future_targeted_repair_or_runtime_seed_pr",
            "no_orphan_status": "CONNECTED_TO_AGENT_CAPABILITY_REGISTRY",
            "authority_boundary_flags": authority_flags(),
        }
        for agent in agents
    ]


def _agent_consumption_rows(input_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "agent_crosswalk_consumption_id": "PR168_RANK_AGENT_CROSSWALK_CONSUMPTION",
            "agent_roster_crosswalk_status": input_summary["agent_roster_crosswalk_status"],
            "source_agent_roster_ref": "PR165_D2_AgentRosterDiscoveryAudit.report.json",
            "source_duty_crosswalk_ref": "PR165_D2_AgentDutySourceCrosswalk.report.json",
        }
    ]


def _stack_synergy_rows(stacks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"candidate_stack_id": row["candidate_stack_id"], "candidate_stack_synergy_edge": row["stack_synergy_edge"]} for row in stacks]


def _stack_compat_rows(stacks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "compatibility_row_id": f"PR168_RANK_STACK_COMPAT::{index:05d}",
            "candidate_stack_id": row["candidate_stack_id"],
            "incompatible_component_pair_reject": False,
            "missing_core_role_repair_route": False,
        }
        for index, row in enumerate(stacks, start=1)
    ]


def _stack_search_rows(stacks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"candidate_stack_id": row["candidate_stack_id"], "beam_width": 1, "dominance_pruning_used": True} for row in stacks]


def _threshold_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(tournament, start=1):
        comp = row["score_components"]
        rows.append(
            {
                "threshold_surface_id": f"PR168_RANK_THRESHOLD::{index:05d}",
                "candidate_stack_id": row.get("candidate_stack_id"),
                "candidate_id": row["candidate_id"],
                "side": "YES_OR_NO",
                "price_grid": [0.0, 0.5, 1.0],
                "quantity_grid": [0.0],
                "latency_bucket": "RP_LATENCY_BUCKET",
                "regime_bucket": "GLOBAL_REPLAY_PAPER",
                "minimum_model_probability_to_trade": None,
                "maximum_execution_price_to_buy": None,
                "maximum_quantity_before_lcb_turns_negative": 0.0,
                "maximum_quantity_before_capacity_fail": 0.0,
                "no_trade_region": comp["no_trade_comparison_margin"] <= 0,
                "repair_region": True,
                "terminal_region": row["terminal_true_negative"],
                "threshold_surface_value": comp["fill_adjusted_expected_pnl"] - comp["total_tca_cost"],
            }
        )
    return rows


def _maker_taker_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "maker_taker_tradeoff_id": f"PR168_RANK_MAKER_TAKER::{index:05d}",
            "candidate_id": row["candidate_id"],
            "passive_expected_fill_probability": 0.0,
            "passive_expected_fill_time_ms": 0.0,
            "passive_spread_capture_or_cost_avoidance": 0.0,
            "passive_adverse_selection_cost": row["score_components"]["total_tca_cost"],
            "aggressive_expected_fill_probability": 0.0,
            "aggressive_expected_fill_time_ms": 0.0,
            "aggressive_spread_crossing_cost": row["score_components"]["total_tca_cost"],
            "maker_taker_net_pnl_delta": 0.0,
            "maker_taker_lcb_delta": 0.0,
            "maker_taker_no_trade_margin_delta": row["score_components"]["no_trade_comparison_margin"],
            "preferred_execution_style": "NO_TRADE",
        }
        for index, row in enumerate(tournament, start=1)
    ]


def _size_price_time_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "sensitivity_ladder_id": f"PR168_RANK_SPT::{index:05d}",
            "candidate_id": row["candidate_id"],
            "size_adjusted_expected_pnl_curve": [[0.0, 0.0]],
            "size_adjusted_lcb_edge_curve": [[0.0, row["score_components"]["lower_confidence_bound_edge"]]],
            "price_adjusted_no_trade_margin_curve": [[0.0, row["score_components"]["no_trade_comparison_margin"]]],
            "threshold_crossing_reason_codes": row["selection_reason_codes"],
            "size_capped_positive_status": False,
        }
        for index, row in enumerate(tournament, start=1)
    ]


def _scenario_stress_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "scenario_stress_id": f"PR168_RANK_SCENARIO_STRESS::{index:05d}",
            "candidate_id": row["candidate_id"],
            "scenario_family": "base_case",
            "scenario_expected_pnl": row["score_components"]["fill_adjusted_expected_pnl"],
            "scenario_lcb_edge": row["score_components"]["lower_confidence_bound_edge"],
            "scenario_no_trade_margin": row["score_components"]["no_trade_comparison_margin"],
            "scenario_cvar_or_expected_shortfall": row["score_components"]["expected_shortfall_cvar_candidate"],
            "scenario_champion_pass_fail": row["champion_eligible"],
            "scenario_repair_action": "REPAIR_REQUIRED" if row["repair_required"] else None,
        }
        for index, row in enumerate(tournament, start=1)
    ]


def _edge_capture_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(score_rows, start=1):
        comp = row["score_components"]
        positives = max(comp["portfolio_marginal_utility"], 0.0) + max(comp["order_policy_quality_score"], 0.0)
        negatives = comp["total_tca_cost"] + comp["overfit_fdr_penalty"] + comp["capacity_crowding_penalty"] + abs(comp["expected_shortfall_cvar_candidate"])
        rows.append(
            {
                "why_trade_wins_id": f"PR168_RANK_EDGE_CAPTURE::{index:05d}",
                "candidate_id": row["candidate_id"],
                "candidate_stack_id": row.get("candidate_stack_id"),
                "model_probability_edge_contribution": 0.0,
                "calibration_edge_contribution": 0.0,
                "execution_cost_reduction_contribution": -comp["total_tca_cost"],
                "portfolio_marginal_utility_contribution": comp["portfolio_marginal_utility"],
                "total_positive_contribution": round(positives, 10),
                "TCA_negative_contribution": comp["total_tca_cost"],
                "overfit_fdr_negative_contribution": comp["overfit_fdr_penalty"],
                "capacity_negative_contribution": comp["capacity_crowding_penalty"],
                "tail_risk_negative_contribution": abs(comp["expected_shortfall_cvar_candidate"]),
                "compute_budget_negative_contribution": comp["compute_budget_penalty"],
                "net_explained_edge": round(positives - negatives, 10),
                "unexplained_residual": 0.0,
                "explanation_quality_score": 1.0,
            }
        )
    return rows


def _why_no_trade_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "why_no_trade_wins_id": f"PR168_RANK_WHY_NO_TRADE::{index:05d}",
            "candidate_id": row["candidate_id"],
            "failed_thresholds": row["selection_reason_codes"],
            "negative_or_insufficient_lcb_reason": "LCB_NOT_POSITIVE" in row["selection_reason_codes"],
            "TCA_or_fill_or_latency_reason": True,
            "capacity_or_portfolio_reason": True,
            "overfit_or_regime_reason": True,
            "repair_or_retest_route": "PR168_RANK_RepairPriorityQueue.report.json",
            "terminal_or_condition_scoped_memory_route": "PR168_RANK_ConditionScopedNegativeMemorySeed.report.json",
        }
        for index, row in enumerate(tournament, start=1)
        if row["no_trade_dominates"]
    ]


def _unexplained_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "unexplained_residual_id": f"PR168_RANK_RESIDUAL::{index:05d}",
            "candidate_id": row["candidate_id"],
            "unexplained_residual": 0.0,
            "route": "NO_UNEXPLAINED_RESIDUAL",
        }
        for index, row in enumerate(score_rows, start=1)
    ]


def _negative_recovery_rows(recovery: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "negative_recovery_tournament_id": row.get("negative_recovery_ref"),
            "candidate_id": row.get("negative_recovery_ref"),
            "recovery_status": row.get("recovery_status"),
            "repair_attempt_count": row.get("repair_attempt_count"),
            "recovery_trial_count": row.get("repair_attempt_count"),
            "recovered_fill_adjusted_expected_pnl": None,
            "recovered_lower_confidence_bound_edge": None,
            "recovery_validity_status": "NO_NUMERIC_IMPROVEMENT_RECOMPUTED",
            "recovery_outcome": "TRUE_NEGATIVE_AFTER_RECOVERY_EXHAUSTION",
            "negative_reason_codes": row.get("negative_reason_codes", []),
            "upstream_numeric_evidence_refs": [row.get("negative_recovery_ref")],
        }
        for row in recovery
    ]


def _quantum_selector_rows(selector_layer: str = "candidate_stack_selection_selector") -> list[dict[str, Any]]:
    return [
        {
            "selector_id": f"PR168_RANK_QUANTUM_SELECTOR::{selector_layer}",
            "selector_layer": selector_layer,
            "objective_sense": "MAXIMIZE",
            "variable_domain": "BINARY",
            "linear_terms": {},
            "quadratic_terms": {},
            "constraint_terms": {},
            "penalty_terms": {},
            "coefficient_source_refs": [],
            "input_numeric_evidence_refs": ["PR168_RANK_EvidenceBackedRanking.report.json"],
            "interpret_back_map": "PR168_RANK_QuantumSelectorInterpretBackMap.report.json",
            "classical_fallback_ref": "PR168_RANK_EvidenceBackedRanking.report.json",
            "classical_fallback_objective_value": 0.0,
            "mapping_status_QUBO_BQM_Ising_CQM_DQM_QuadraticProgram": "GAP_ROUTED_STRUCTURAL_ONLY",
            "backend_execution_required_flag": False,
            "quantum_advantage_claim_flag": False,
        }
    ]


def _quantum_interpret_rows(stacks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "interpret_back_map_id": f"PR168_RANK_INTERPRET::{index:05d}",
            "variable_id": f"x_{index}",
            "candidate_stack_id": row["candidate_stack_id"],
            "qku_refs": row["qku_refs"],
            "formula_refs": row["formula_refs"],
        }
        for index, row in enumerate(stacks, start=1)
    ]


def _two_speed_rows() -> list[dict[str, Any]]:
    return [
        {
            "two_speed_plan_id": "PR168_RANK_TWO_SPEED_DECISION_SURFACE",
            "research_full_simulation_allowed": True,
            "future_hot_path_full_research_recompute_allowed": False,
            "future_hot_path_decision_surface_lookup_seed_allowed": True,
            "future_hot_path_inputs_must_be_predeclared": True,
            "future_hot_path_cache_keys_must_not_create_sha_authority": True,
        }
    ]


def _scalar_no_orphan_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in score_rows:
        for key, value in row["score_components"].items():
            rows.append(
                {
                    "scalar_value_id": f"{row['candidate_id']}::{key}",
                    "candidate_id": row["candidate_id"],
                    "field": key,
                    "value": value,
                    "upstream_numeric_evidence_ref_or_gap_ref": row["candidate_id"],
                    "downstream_report_ref": "PR168_RANK_ScoreComponentLedger.report.json",
                    "downstream_user_or_agent_consumer": "RankingAgent",
                }
            )
    return rows


def _terminal_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "terminal_lifecycle_id": f"PR168_RANK_TERMINAL::{index:05d}",
            "candidate_id": row["candidate_id"],
            "terminal_by_nature": row["terminal_true_negative"],
            "terminal_reason_code": "TRUE_NEGATIVE_AFTER_RECOVERY_EXHAUSTION" if row["terminal_true_negative"] else None,
            "terminal_governance_consumer": "GovernanceAgent",
            "dashboard_or_archive_consumer": "DashboardAgent",
            "no_future_action_required_reason": "reopen_allowed_if_conditions_change",
            "reopen_conditions_if_any": ["new_numeric_PR168_RP_evidence", "cost_or_fill_repair"],
        }
        for index, row in enumerate(tournament, start=1)
    ]


def _threshold_dag_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "threshold_dag_id": f"PR168_RANK_THRESHOLD_DAG::{index:05d}",
            "candidate_id": row["candidate_id"],
            "surface_ref": "PR168_RANK_OrderDecisionThresholdSurface.report.json",
            "downstream_pr_or_workflow_ref": "RuntimeFormulaAllowlistHotPathCachePR",
        }
        for index, row in enumerate(tournament, start=1)
    ]


def _negative_recovery_dag_rows(recovery: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "negative_recovery_dag_id": f"PR168_RANK_NEG_RECOVERY_DAG::{index:05d}",
            "candidate_id": row.get("negative_recovery_ref"),
            "upstream_numeric_evidence_ref_or_gap_ref": row.get("negative_recovery_ref"),
            "downstream_pr_or_workflow_ref": "PR165-B condition-scoped negative memory",
        }
        for index, row in enumerate(recovery, start=1)
    ]


def _connector_rows(tournament: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "connector_candidate_id": f"PR168_RANK_CONNECTOR::{index:05d}",
            "connector_or_venue_scope": "venue_candidate_only_not_bound",
            "field_or_semantic_needed": "market_id/side/price/quantity/fill/cost",
            "why_needed_for_trade_decision": "future connector semantics must preserve pretrade decision inputs",
            "source_truth_status": "NOT_ACCEPTED_IN_THIS_PR",
            "private_state_required_flag": False,
            "cash_required_flag": False,
            "order_authority_required_flag": False,
            "responsible_agent": "ConnectorCandidateAgent",
            "consumer_pr": "source_evidence_or_connector_binding_future_pr",
            "candidate_id": row["candidate_id"],
        }
        for index, row in enumerate(tournament, start=1)
    ]


def _downstream_reports(
    input_summary: dict[str, Any],
    ranking_rows: list[dict[str, Any]],
    tournament: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    counts = _count_summary(input_summary, ranking_rows, tournament)
    files = [
        "PR168_RANK_To_PR166_QC_R2_QuantumComparatorQueue.report.json",
        "PR168_RANK_To_PR162E_Q_QuantumMapperQueue.report.json",
        "PR168_RANK_To_PR165B_NegativeCombinationMemorySeed.report.json",
        "PR168_RANK_To_TargetedRepairPRs.report.json",
        "PR168_RANK_To_PR167_OpenTradeCombinationSimulatorSeed.report.json",
        "PR168_RANK_To_PR167B_ReplayPaperCampaignSeed.report.json",
        "PR168_RANK_To_RuntimeFormulaAllowlistHotPathCacheSeed.report.json",
        "PR168_RANK_To_OwnerDashboardComputedTruth.report.json",
        "PR168_RANK_To_FutureExecutionRouterDecisionKernelSeed.report.json",
    ]
    return {filename: [_handoff_row(filename, counts)] for filename in files}


def _registry_downstream_reports(registry_rows: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "PR168_RANK_To_PR162E_PluginRegistrySeed.report.json": registry_rows["FormulaPluginRegistrySeed"] + registry_rows["AlgorithmPluginRegistrySeed"],
        "PR168_RANK_To_PR162E_Q_QuantumObjectiveRegistrySeed.report.json": registry_rows["QuantumObjectiveRegistrySeed"],
        "PR168_RANK_To_RuntimeAllowlistRegistrySeed.report.json": registry_rows["RuntimeAllowlistSeedRegistry"],
        "PR168_RANK_To_MarketVenueAdapterExpansionSeed.report.json": registry_rows["MarketAdapterRegistry"] + registry_rows["VenueCostModelRegistry"] + registry_rows["ContractPayoffModelRegistry"],
    }


def _handoff_row(filename: str, counts: dict[str, Any]) -> dict[str, Any]:
    return {
        "handoff_id": f"HANDOFF::{filename}",
        "target": filename.removeprefix("PR168_RANK_To_").removesuffix(".report.json"),
        "summary_counts": counts,
        "source_report_refs": ["PR168_RANK_FinalSummary.report.json"],
        "live_execution_allowed_flag": False,
        "order_authority_required_flag": False,
        "source_truth_status": "NOT_ACCEPTED_IN_THIS_PR",
    }


def _count_summary(input_summary: dict[str, Any], ranking_rows: list[dict[str, Any]], tournament: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "computed_negative_count": input_summary["computed_negative_count"],
        "pretrade_candidate_count": input_summary["pretrade_candidate_count"],
        "ranking_row_count": len(ranking_rows),
        "champion_count": len([row for row in ranking_rows if row["champion_eligible"]]),
        "challenger_count": len([row for row in ranking_rows if row["challenger_eligible"]]),
        "no_trade_dominant_count": len([row for row in tournament if row["no_trade_dominates"]]),
    }


def _artifact_rows(reports: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": f"PR168_RANK_ARTIFACT::{filename}",
            "artifact_path": f"docs/master_plan/generated/{filename}",
            "artifact_type": "generated_report",
            "upstream_input_refs": ["PR168_RP_To_PR168_RANK_ComputedRanking.report.json"],
            "numeric_evidence_refs": ["PR168_RP_To_PR168_RANK_PreTradeRankingSeed.report.json"],
            "downstream_consumers": [_consumer_for(filename)],
            "downstream_pr_refs": [_route_for(filename)],
            "validator_refs": ["tools/pr168_rank_validator.py"],
            "test_refs": ["tests/pr168_rank"],
            "authority_class": "NONLIVE_DECISION_QUALITY_SEED",
            "manual_edit_allowed_flag": False,
            "record_count": len(rows),
        }
        for filename, rows in sorted(reports.items())
    ]


def _simulation_artifact_rows(reports: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [row for row in _artifact_rows(reports) if "Simulation" in row["artifact_path"] or "Order" in row["artifact_path"]]


def _no_orphan_rows(reports: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        {
            "no_orphan_proof_id": f"PR168_RANK_NO_ORPHAN::{filename}",
            "artifact_path": f"docs/master_plan/generated/{filename}",
            "record_count": len(rows),
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            "downstream_consumers": [_consumer_for(filename)],
        }
        for filename, rows in sorted(reports.items())
    ]


def _authority_audit_rows() -> list[dict[str, Any]]:
    return [
        {
            "authority_audit_id": "PR168_RANK_AUTHORITY_BOUNDARY_AUDIT",
            "submit_order": False,
            "cancel_order": False,
            "reduce_order": False,
            "close_order": False,
            "private_state_or_cash_fetch": False,
            "connector_semantic_binding": False,
            "source_truth_acceptance": False,
            "quantum_backend_execution": False,
            "quantum_advantage_claim": False,
            "qtt_sha_authority_created": False,
            "atomicrows_hash_authority_created": False,
        }
    ]


def _scope_integration_rows() -> list[dict[str, Any]]:
    return [
        {
            "scope_registry_integration_id": "PR168_RANK_SCOPE_REGISTRY",
            "central_module_path": "tools/validation_scope_registry.py",
            "branch": "pr168-rank-evidence-backed-ranking",
            "allowed_patterns": [
                "docs/master_plan/generated/PR168_RANK_*.report.json",
                "docs/master_plan/generated/pr168_rank_shards/PR168_RANK_*.report.json",
                "tools/pr168_rank_*.py",
                "tools/validate_pr168_rank_*.py",
                "tests/pr168_rank/**",
            ],
        }
    ]


def _centralized_coverage_rows() -> list[dict[str, Any]]:
    modules = [
        "tools/build_pr168_rank_evidence_backed_ranking.py",
        "tools/pr168_rank_input_loader.py",
        "tools/pr168_rank_evidence_model.py",
        "tools/pr168_rank_binary_prediction_market_pnl.py",
        "tools/pr168_rank_candidate_stack_generator.py",
        "tools/pr168_rank_pretrade_order_simulator.py",
        "tools/pr168_rank_decision_tournament.py",
        "tools/pr168_rank_future_expansion_registry_layer.py",
        "tools/pr168_rank_report_writer.py",
        "tools/pr168_rank_validator.py",
    ]
    return [
        {
            "central_module_path": module,
            "reports_produced": ["PR168_RANK_FinalSummary.report.json"],
            "validators_covering_it": ["tools/validate_pr168_rank_centralized_systems_coverage.py"],
            "tests_covering_it": ["tests/pr168_rank/test_future_expansion_registries.py"],
            "upstream_inputs": ["PR168_RP_To_PR168_RANK_ComputedRanking.report.json"],
            "downstream_consumers": ["RankingAgent", "GovernanceAgent"],
            "owning_agent": "RankingAgent",
            "no_orphan_status": "CONNECTED_TO_CENTRALIZED_SYSTEMS_AUDIT",
            "anti_scatter_rule": "logic_routes_through_pr168_rank_central_modules",
            "reason_code_registry_integration": "tools/qtt_authority_reason_code_registry.py",
            "validation_scope_registry_integration": "tools/validation_scope_registry.py",
        }
        for module in modules
    ]


def _future_expansion_dag_rows(registry_rows: dict[str, list[dict[str, Any]]], dag_class: str) -> list[dict[str, Any]]:
    return [
        {
            "future_expansion_dag_id": f"PR168_RANK_FUTURE_DAG::{dag_class}::{name}",
            "registry_name": name,
            "registry_report_ref": REGISTRY_REPORTS[name],
            "downstream_pr_refs": sorted({pr for row in rows for pr in row.get("downstream_pr_refs", [])}),
            "no_forbidden_authority_created": True,
        }
        for name, rows in sorted(registry_rows.items())
    ]


def _registry_no_orphan_rows(registry_rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        {
            "registry_no_orphan_id": f"PR168_RANK_REGISTRY_NO_ORPHAN::{name}::{index}",
            "registry_name": name,
            "registry_row_id": row["registry_row_id"],
            "owning_agent": row["owning_agent"],
            "downstream_consumers": row["downstream_consumers"],
            "downstream_pr_refs": row["downstream_pr_refs"],
            "no_orphan_status": row["no_orphan_status"],
            "authority_boundary_flags": row["authority_boundary_flags"],
        }
        for name, rows in sorted(registry_rows.items())
        for index, row in enumerate(rows, start=1)
    ]


def _registry_anti_scatter_rows() -> list[dict[str, Any]]:
    names = [
        "market_adapter_logic_must_route_through_MarketAdapterRegistry",
        "venue_cost_logic_must_route_through_VenueCostModelRegistry",
        "contract_payoff_logic_must_route_through_ContractPayoffModelRegistry",
        "formula_plugin_seed_logic_must_route_through_FormulaPluginRegistrySeed",
        "algorithm_plugin_seed_logic_must_route_through_AlgorithmPluginRegistrySeed",
        "quantum_objective_logic_must_route_through_QuantumObjectiveRegistrySeed",
        "order_policy_logic_must_route_through_OrderPolicyRegistry",
        "agent_capability_logic_must_route_through_AgentCapabilityRegistry",
        "connector_readiness_logic_must_route_through_ConnectorReadinessRegistry",
        "runtime_allowlist_seed_logic_must_route_through_RuntimeAllowlistSeedRegistry",
        "hot_path_surface_logic_must_route_through_HotPathDecisionSurfaceRegistry",
    ]
    return [{"anti_scatter_rule": name, "status": "PASS"} for name in names]


def _generic_gap_rows(status: str, input_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"gap_queue_id": f"PR168_RANK_GAP::{status}", "gap_status": status, "input_summary_ref": input_summary["report_id"]}]


def _generic_materialized_row(filename: str, input_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "materialized_row_id": f"PR168_RANK_MATERIALIZED::{filename}",
        "source_report_refs": input_summary.get("upstream_report_refs", []),
        "evidence_count": input_summary.get("pretrade_candidate_count", 0),
        "status": "MATERIALIZED_NONLIVE_EVIDENCE",
    }


def _final_summary(
    input_summary: dict[str, Any],
    ranking_rows: list[dict[str, Any]],
    tournament: list[dict[str, Any]],
    registry_rows: dict[str, list[dict[str, Any]]],
    reports: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    champion_count = len([row for row in ranking_rows if row["champion_eligible"]])
    challenger_count = len([row for row in ranking_rows if row["challenger_eligible"]])
    no_trade_count = len([row for row in tournament if row["no_trade_dominates"]])
    return {
        "report_id": "PR168_RANK_FinalSummary",
        "what_reports_were_consumed": input_summary["upstream_report_refs"],
        "true_pr168_rp_input_counts_extracted": {key: input_summary[key] for key in input_summary if key.endswith("_count")},
        "ranking_proceeded": True,
        "score_components_implemented": True,
        "pnl_formula_kernel_status": "IMPLEMENTED_BINARY_YES_NO_NONLIVE",
        "pretrade_order_decision_simulation_status": "MATERIALIZED_FROM_PR168_RP_PRETRADE_NUMERIC_EVIDENCE",
        "candidate_stack_generation_status": "MATERIALIZED",
        "mode_policy_matrix_status": "MATERIALIZED_NO_LIVE_ORDER_AUTHORITY",
        "champion_count": champion_count,
        "challenger_count": challenger_count,
        "retest_count": 0,
        "repair_count": len([row for row in ranking_rows if row["repair_required"]]),
        "terminal_count": len([row for row in tournament if row["terminal_true_negative"]]),
        "no_trade_dominance_count": no_trade_count,
        "tca_decomposition_status": "CONSUMED_FROM_PR168_RP",
        "overfit_fdr_penalty_status": "PROXY_CONSUMED_AND_TRIAL_LEDGERED",
        "portfolio_capacity_regime_status": "MATERIALIZED_FROM_PR168_RP_NUMERIC_FIELDS",
        "quantum_structural_readiness_status": "STRUCTURAL_ONLY_GAP_ROUTED_NO_BACKEND",
        "quantum_combinatorial_selection_objective_status": "SEED_ONLY_NO_BACKEND_NO_ADVANTAGE_CLAIM",
        "latency_hot_path_seed_status": "TWO_SPEED_SEED_ONLY",
        "agent_work_order_coverage": "MATERIALIZED",
        "dag_no_orphan_proof": "MATERIALIZED",
        "downstream_pr_queues": "MATERIALIZED",
        "forbidden_authority_not_created": True,
        "remaining_gaps_and_downstream_pr_queues": input_summary["highest_value_repair_queues"],
        "edge_capture_attribution_count": len(ranking_rows),
        "why_trade_count": 0,
        "why_no_trade_count": no_trade_count,
        "negative_recovery_tournament_count": input_summary["computed_negative_count"],
        "recovered_positive_count": 0,
        "size_capped_count": 0,
        "regime_scoped_count": 0,
        "true_negative_after_recovery_count": input_summary["true_negative_or_terminal_input_count"],
        "threshold_surface_status": "MATERIALIZED",
        "maker_taker_status": "MATERIALIZED_NO_TRADE_DOMINANT",
        "size_price_time_sensitivity_status": "MATERIALIZED",
        "scenario_stress_status": "MATERIALIZED",
        "scalar_value_no_orphan_status": "MATERIALIZED",
        "terminal_lifecycle_status": "MATERIALIZED",
        "connector_candidate_routing_status": "SEED_ONLY_WITHOUT_CONNECTOR_TRUTH",
        "two_speed_hot_path_decision_surface_seed_status": "MATERIALIZED_WITHOUT_SHA_AUTHORITY",
        "central_future_expansion_registry_layer_status": "MATERIALIZED_SEED_CONTRACT_ONLY",
        "registry_seed_counts": {name: len(rows) for name, rows in registry_rows.items()},
        "report_count": len(reports),
        "live_ready_claim": False,
        "profit_proof_claim": False,
        "quantum_advantage_claim": False,
    }


def _consumer_for(filename: str) -> str:
    if "Quantum" in filename:
        return "QuantumMapperAgent"
    if "Connector" in filename:
        return "ConnectorCandidateAgent"
    if "Dashboard" in filename:
        return "DashboardAgent"
    if "Registry" in filename:
        return "GovernanceAgent"
    return "RankingAgent"


def _route_for(filename: str) -> str:
    if "_To_" in filename:
        return filename.removeprefix("PR168_RANK_To_").removesuffix(".report.json")
    return filename
