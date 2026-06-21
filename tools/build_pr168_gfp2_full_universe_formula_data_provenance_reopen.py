#!/usr/bin/env python3
"""Build PR168-GFP2 full-universe provenance reopening reports."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_gfp2_agent_router import agent_consumption_rows, qku_routing_rows
from tools.pr168_gfp2_alpha_capture_seed import (
    alpha_capture_rows,
    candidate_stack_search_space_rows,
    execution_adjusted_formula_rows,
    order_policy_rows,
)
from tools.pr168_gfp2_artifact_locator import pr165_d2_missing
from tools.pr168_gfp2_computability_classifier import all_qku_computability_rows
from tools.pr168_gfp2_constants import BASELINE_COUNTS, REQUIRED_REPORTS
from tools.pr168_gfp2_dag_orchestrator import no_orphan_rows, report_dag_rows, terminal_exception_rows
from tools.pr168_gfp2_data_tier_classifier import accepted_real_data_discovery_rows, data_tier_rows
from tools.pr168_gfp2_execution_adjusted_ranking_seed import ranking_seed_rows
from tools.pr168_gfp2_external_candidate_source_acquisition import external_candidate_source_rows, venue_binding_rows
from tools.pr168_gfp2_formula_provenance_model import formula_assignment_audit, selected_formula_provenance
from tools.pr168_gfp2_input_loader import load_inputs
from tools.pr168_gfp2_negative_recovery_ladder import (
    recovery_dimension_rows,
    recovery_opportunity_rows,
    repair_ladder_rows,
)
from tools.pr168_gfp2_optimizer_default_registry import optimizer_default_rows
from tools.pr168_gfp2_prior_result_authority_supersession import (
    champion_strip_rows,
    fake_negative_rows,
    fake_neutral_zero_rows,
    fake_positive_rows,
    prior_result_correction_rows,
)
from tools.pr168_gfp2_quantum_structural_readiness import (
    quantum_portfolio_objective_seed_rows,
    quantum_readiness_rows,
)
from tools.pr168_gfp2_real_data_computation_eligibility import computation_eligibility_rows
from tools.pr168_gfp2_real_data_formula_executor import real_data_formula_execution_rows
from tools.pr168_gfp2_real_market_replay_readiness import replay_recompute_handoff_rows
from tools.pr168_gfp2_report_writer import GENERATED_DIR, write_report
from tools.pr168_gfp2_selection_downgrade_engine import (
    computability_downgrade_rows,
    selection_decision_rows,
    selection_summary,
    unselected_reopen_rows,
)
from tools.pr168_gfp2_tca_capacity_fdr_portfolio_seed import (
    calibration_rows,
    capacity_rows,
    overfit_fdr_rows,
    portfolio_rows,
    tca_rows,
)
from tools.pr168_gfp2_universe_reconciler import (
    atomicrows_bridge_rows,
    candidate_packet_rows,
    qku_reconciliation_rows,
    reconciliation_rows,
)


def build_all_reports(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    inputs = load_inputs(repo_root)
    if pr165_d2_missing(inputs.artifact_rows):
        blocker = [
            row
            for row in inputs.artifact_rows
            if "PR165_D2_Agent" in str(row.get("artifact_path")) and not row.get("found_flag")
        ]
        write_report(
            repo_root,
            "PR168_GFP2_MissingAgentCrosswalkBlocker.report.json",
            blocker,
            summary={"blocker_status": "FAIL_PR165_D2_AGENT_CROSSWALK_REQUIRED"},
            terminal_by_nature_flag=True,
            terminal_reason_code="MISSING_REQUIRED_PR165_D2_AGENT_CROSSWALK",
            downstream_consumers=["Governance Agent"],
            downstream_pr_refs=["PR168-GFP2"],
        )
        raise RuntimeError("PR165-D2 agent crosswalk artifacts are required")

    universe = all_qku_computability_rows(inputs)
    formula_rows = selected_formula_provenance(inputs)
    assignment_rows = formula_assignment_audit(inputs)
    data_rows = data_tier_rows(inputs)
    eligibility = computation_eligibility_rows(inputs)
    real_exec = real_data_formula_execution_rows(eligibility)
    prior_rows = prior_result_correction_rows(inputs)
    positive_corrections = fake_positive_rows(prior_rows)
    negative_reopen = fake_negative_rows(prior_rows)
    neutral_reopen = fake_neutral_zero_rows(prior_rows)
    champion_rows = champion_strip_rows(prior_rows)
    source_rows = external_candidate_source_rows()
    binding_rows = venue_binding_rows()
    recovery_rows = recovery_opportunity_rows(universe)
    repair_rows = repair_ladder_rows(universe)
    quantum_rows = quantum_readiness_rows(universe)
    alpha_rows = alpha_capture_rows()
    stack_rows = candidate_stack_search_space_rows()
    ev_formula_rows = execution_adjusted_formula_rows()
    policy_rows = order_policy_rows()
    ranking_rows = ranking_seed_rows(universe)
    tca_seed_rows = tca_rows()
    capacity_seed_rows = capacity_rows()
    calibration_seed_rows = calibration_rows()
    fdr_rows = overfit_fdr_rows()
    portfolio_seed_rows = portfolio_rows()
    optimizer_rows = optimizer_default_rows()
    replay_handoff = replay_recompute_handoff_rows(universe)
    report_names = list(REQUIRED_REPORTS)
    upstream_refs = [row["artifact_path"] for row in inputs.artifact_rows if row.get("found_flag")]
    dag_rows = report_dag_rows(report_names, upstream_refs)
    no_orphan = no_orphan_rows(report_names)
    terminal_rows = terminal_exception_rows(report_names)

    written: list[str] = []

    def emit(name: str, records: list[dict[str, Any]], **kwargs: Any) -> None:
        write_report(repo_root, name, records, upstream_input_refs=upstream_refs, **kwargs)
        written.append(name)

    rec_rows = reconciliation_rows(inputs)
    emit("PR168_GFP2_FullUniverseInputDiscovery.report.json", inputs.artifact_rows, summary=_artifact_summary(inputs.artifact_rows))
    emit("PR168_GFP2_9360QKUUniverseReconciliation.report.json", qku_reconciliation_rows(inputs), summary=_count_summary(rec_rows, "historical_master_qku_count"))
    emit("PR168_GFP2_6502CandidatePacketReconciliation.report.json", candidate_packet_rows(inputs), summary=_count_summary(rec_rows, "candidate_packet_v1_count"))
    emit("PR168_GFP2_AtomicRows4183Bridge.report.json", atomicrows_bridge_rows(inputs), summary=_count_summary(rec_rows, "atomic_rows_bridge_count"))
    emit("PR168_GFP2_FormulaAssignment20387Audit.report.json", assignment_rows, summary=_count_summary(rec_rows, "formula_assignment_count"))
    emit("PR168_GFP2_Selected35FormulaProvenance.report.json", formula_rows, summary=_count_summary(rec_rows, "selected_formula_count"))
    emit("PR168_GFP2_UnselectedQKUReopenLedger.report.json", unselected_reopen_rows(universe), summary=selection_summary(universe))
    emit("PR168_GFP2_SelectionDecisionProvenanceLedger.report.json", selection_decision_rows(universe), summary=selection_summary(universe))
    emit("PR168_GFP2_ComputabilityDowngradeLedger.report.json", computability_downgrade_rows(universe), summary=selection_summary(universe))
    emit("PR168_GFP2_AllQKUComputabilityClassificationLedger.report.json", universe, summary=selection_summary(universe))
    emit("PR168_GFP2_DataTierClassification.report.json", data_rows, summary=_data_summary(data_rows))
    emit("PR168_GFP2_RealMarketDataUsageAudit.report.json", accepted_real_data_discovery_rows(inputs), summary={"production_accepted_real_market_data_count": len(inputs.production_accepted_source_rows)})
    emit("PR168_GFP2_AcceptedRealDataDiscovery.report.json", accepted_real_data_discovery_rows(inputs), summary={"production_accepted_real_market_data_count": len(inputs.production_accepted_source_rows)})
    emit("PR168_GFP2_AcceptedRealDataComputationEligibility.report.json", eligibility, summary=_proof_summary(eligibility))
    emit("PR168_GFP2_RealDataFormulaExecutionLedger.report.json", real_exec, summary=_proof_summary(eligibility))
    emit("PR168_GFP2_RealPositiveNegativeProofLedger.report.json", eligibility, summary=_proof_summary(eligibility))
    emit("PR168_GFP2_ZeroPositiveNotFinalTruthAudit.report.json", [_zero_positive_row(inputs, eligibility)], summary={"zero_positive_final_truth_allowed_count": 0})
    emit("PR168_GFP2_RealDataMissingProofComponentQueue.report.json", eligibility, summary=_proof_summary(eligibility))
    emit("PR168_GFP2_RealDataAsOfAndReplayLockAudit.report.json", eligibility, summary={"missing_replay_lock_count": len(eligibility)})
    emit("PR168_GFP2_RealDataSampleSizeAndCoverageAudit.report.json", eligibility, summary={"sample_size_lcb_allowed_count": 0})
    emit("PR168_GFP2_NumericEvidenceProvenanceMatrix.report.json", data_rows, summary=_data_summary(data_rows))
    emit("PR168_GFP2_ExternalCandidateSourceAcquisitionLedger.report.json", source_rows, summary={"candidate_source_count": len(source_rows)})
    emit("PR168_GFP2_NonOfficialCandidateSourceLane.report.json", [row for row in source_rows if row["non_official_source_flag"]], summary={"non_official_candidate_source_count": len([row for row in source_rows if row["non_official_source_flag"]])})
    emit("PR168_GFP2_SourceConflictAndStalenessAudit.report.json", source_rows, summary={"staleness_pending_count": len(source_rows)})
    emit("PR168_GFP2_VenueDataBindingCandidateSurface.report.json", binding_rows, summary={"binding_candidate_count": len(binding_rows)})
    emit("PR168_GFP2_ProxySyntheticGeneratedEvidenceAudit.report.json", [row for row in universe if row["repo_local_generated_flag"]], summary={"repo_local_generated_evidence_count": len([row for row in universe if row["repo_local_generated_flag"]])})
    emit("PR168_GFP2_PriorPositiveNegativeAuthorityDowngradeLedger.report.json", prior_rows, summary=_prior_summary(prior_rows))
    emit("PR168_GFP2_PriorResultSupersessionLedger.report.json", prior_rows, summary=_prior_summary(prior_rows))
    emit("PR168_GFP2_FakePositiveCorrectionQueue.report.json", positive_corrections, summary={"fake_positive_correction_count": len(positive_corrections)})
    emit("PR168_GFP2_FakeNegativeReopenQueue.report.json", negative_reopen, summary={"fake_negative_reopen_count": len(negative_reopen)})
    emit("PR168_GFP2_FakeNeutralZeroNoTradeReopenQueue.report.json", neutral_reopen, summary={"fake_neutral_zero_no_trade_reopen_count": len(neutral_reopen)})
    emit("PR168_GFP2_MetadataNonComputableReopenQueue.report.json", [], summary={"metadata_noncomputable_reopen_count": 0, "empty_reason": "NO_PRIOR_METADATA_ONLY_NONCOMPUTABLE_ROWS_FOUND_IN_REQUIRED_INPUTS"})
    emit("PR168_GFP2_ChampionAuthorityStripLedger.report.json", champion_rows, summary={"champion_authority_stripped_count": len(champion_rows)})
    emit("PR168_GFP2_RealMarketRecomputeRequiredLedger.report.json", prior_rows, summary=_prior_summary(prior_rows))
    emit("PR168_GFP2_ResultAuthorityTransitionAudit.report.json", prior_rows, summary=_prior_summary(prior_rows))
    emit("PR168_GFP2_PriorResultAgentBeliefRoutingLedger.report.json", prior_rows, summary=_prior_summary(prior_rows))
    _emit_repair_and_seed_reports(emit, universe, binding_rows, alpha_rows, stack_rows, ev_formula_rows, policy_rows, ranking_rows, tca_seed_rows, capacity_seed_rows, calibration_seed_rows, fdr_rows, portfolio_seed_rows, optimizer_rows, recovery_rows, repair_rows, quantum_rows, replay_handoff, source_rows, prior_rows, inputs)
    _emit_agent_and_dag_reports(emit, inputs, universe, formula_rows, data_rows, recovery_rows, quantum_rows, prior_rows, dag_rows, no_orphan, terminal_rows, replay_handoff, ranking_rows, source_rows)
    emit(
        "PR168_GFP2_FinalSummary.report.json",
        [_final_summary_row(inputs, universe, prior_rows, written)],
        summary=_final_summary(inputs, universe, prior_rows, written),
        terminal_by_nature_flag=True,
        terminal_reason_code="FINAL_SUMMARY_TERMINAL_BY_NATURE",
        downstream_consumers=["Owner Dashboard", "Governance Agent"],
        downstream_pr_refs=["PR168-RP2", "PR168-RANK2"],
    )

    missing = sorted(set(REQUIRED_REPORTS) - set(written))
    if missing:
        raise RuntimeError(f"missing required GFP2 reports: {missing}")
    return _final_summary(inputs, universe, prior_rows, written)


def _emit_repair_and_seed_reports(emit, universe, binding_rows, alpha_rows, stack_rows, ev_formula_rows, policy_rows, ranking_rows, tca_seed_rows, capacity_seed_rows, calibration_seed_rows, fdr_rows, portfolio_seed_rows, optimizer_rows, recovery_rows, repair_rows, quantum_rows, replay_handoff, source_rows, prior_rows, inputs) -> None:
    gap_rows = [{"canonical_row_key": row["canonical_row_key"], "qku_id": row["qku_id"], "gap_reason_codes": row["gap_reason_codes"], "repair_queue_refs": row["repair_queue_refs"], "downstream_pr_refs": row["downstream_pr_refs"], "agent_owner": row["agent_owner"], "no_orphan_status": row["no_orphan_status"]} for row in universe]
    formula_gap_rows = [row for row in gap_rows if "FORMULA_INPUT_BINDING_REPAIR_REQUIRED" in row["gap_reason_codes"]]
    emit("PR168_GFP2_GapRoutedUniverseRepairQueue.report.json", gap_rows, summary={"gap_routed_count": len(gap_rows)})
    emit("PR168_GFP2_FormulaInputMapRepairQueue.report.json", formula_gap_rows, summary={"formula_input_repair_count": len(formula_gap_rows)})
    _emit_binding_family(emit, "PR168_GFP2_MarketVenuePayoffDataBindingQueue.report.json", binding_rows, "market_venue_payoff")
    _emit_binding_family(emit, "PR168_GFP2_OrderbookTradeResolutionDataBindingQueue.report.json", binding_rows, "orderbook_trade_resolution")
    _emit_binding_family(emit, "PR168_GFP2_FeeSlippageFillLatencyTCADataBindingQueue.report.json", binding_rows, "fee_slippage_fill_latency_tca")
    _emit_binding_family(emit, "PR168_GFP2_CurrentMarketDataCandidateBindingQueue.report.json", binding_rows, "current_market_data")
    _emit_binding_family(emit, "PR168_GFP2_HistoricalReplayDataCandidateBindingQueue.report.json", binding_rows, "historical_replay_data")
    emit("PR168_GFP2_AlphaCaptureMechanismRegistry.report.json", alpha_rows, summary={"alpha_capture_seed_count": len(alpha_rows)})
    emit("PR168_GFP2_CandidateStackSearchSpaceManifest.report.json", stack_rows, summary={"candidate_stack_seed_count": len(stack_rows)})
    emit("PR168_GFP2_TradeOrderSimulationStackSpecQueue.report.json", stack_rows, summary={"trade_order_simulation_stack_seed_count": len(stack_rows)})
    emit("PR168_GFP2_ExecutionAdjustedExpectedValueFormulaRegistry.report.json", ev_formula_rows, summary={"ev_formula_seed_count": len(ev_formula_rows)})
    emit("PR168_GFP2_OrderPolicyAlternativeSeed.report.json", policy_rows, summary={"order_policy_seed_count": len(policy_rows)})
    emit("PR168_GFP2_NoTradePermanentCompetitorSeed.report.json", [row for row in policy_rows if row["order_policy"] == "no_trade"], summary={"no_trade_permanent_competitor_count": 1})
    emit("PR168_GFP2_ExecutionAdjustedRankingSeed.report.json", ranking_rows, summary={"ranking_seed_count": len(ranking_rows)})
    emit("PR168_GFP2_TCADecompositionSeed.report.json", tca_seed_rows, summary={"tca_component_count": len(tca_seed_rows)})
    emit("PR168_GFP2_TCAComponentFormulaRegistry.report.json", tca_seed_rows, summary={"tca_component_count": len(tca_seed_rows)})
    emit("PR168_GFP2_OverfitFDRTrialFamilyLedger.report.json", fdr_rows, summary={"overfit_fdr_seed_count": len(fdr_rows)})
    emit("PR168_GFP2_PurgedWalkForwardCPCVSeed.report.json", fdr_rows, summary={"cpcv_seed_count": len(fdr_rows)})
    emit("PR168_GFP2_CapacityCrowdingLimitSeed.report.json", capacity_seed_rows, summary={"capacity_seed_count": len(capacity_seed_rows)})
    emit("PR168_GFP2_ProbabilityCalibrationSeed.report.json", calibration_seed_rows, summary={"calibration_seed_count": len(calibration_seed_rows)})
    emit("PR168_GFP2_DataQualitySampleSizeLCBRegistry.report.json", calibration_seed_rows, summary={"lcb_seed_count": len(calibration_seed_rows)})
    emit("PR168_GFP2_PortfolioDiversificationMarginalUtilitySeed.report.json", portfolio_seed_rows, summary={"portfolio_seed_count": len(portfolio_seed_rows)})
    emit("PR168_GFP2_ChampionChallengerNoTradeSeed.report.json", alpha_rows, summary={"champion_challenger_seed_no_live_authority_count": len(alpha_rows)})
    emit("PR168_GFP2_RegimeConditionedMemorySeed.report.json", alpha_rows, summary={"regime_seed_count": len(alpha_rows)})
    emit("PR168_GFP2_MarginalUtilitySelectionSeed.report.json", portfolio_seed_rows, summary={"marginal_utility_seed_count": len(portfolio_seed_rows)})
    emit("PR168_GFP2_OptimizerDefaultAndParameterRangeSeed.report.json", optimizer_rows, summary={"optimizer_default_gap_routed_count": len(optimizer_rows)})
    emit("PR168_GFP2_NegativeToPositiveRecoveryOpportunityLedger.report.json", recovery_rows, summary={"recovery_opportunity_count": len(recovery_rows)})
    emit("PR168_GFP2_NegativeCandidateRepairLadderQueue.report.json", repair_rows, summary={"repair_ladder_count": len(repair_rows)})
    emit("PR168_GFP2_RecoveryDimensionDiagnosis.report.json", recovery_dimension_rows(), summary={"recovery_dimension_count": len(recovery_dimension_rows())})
    emit("PR168_GFP2_RecoveryEligibleCandidateStackQueue.report.json", recovery_rows, summary={"recovery_eligible_count": len(recovery_rows)})
    emit("PR168_GFP2_RealNegativeAfterRecoveryProofRequirements.report.json", [{"requirement": "accepted_real_data_and_recovery_ladder_exhaustion_required_before_real_negative", "real_negative_after_recovery_exhaustion_count": 0, "downstream_pr_refs": ["PR168-RP2"], "agent_owner": "Alpha Recovery Agent", "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER"}], summary={"real_negative_after_recovery_exhaustion_count": 0})
    emit("PR168_GFP2_ConditionScopedNegativeMemorySeed.report.json", recovery_rows, summary={"negative_memory_seed_count": len(recovery_rows)})
    emit("PR168_GFP2_RecoveryRetestToPR168_RP2Handoff.report.json", replay_handoff, summary={"retest_handoff_count": len(replay_handoff)})
    emit("PR168_GFP2_QuantumStructuralReadinessFullUniverse.report.json", quantum_rows, summary={"quantum_structural_row_count": len(quantum_rows), "quantum_backend_execution_count": 0, "quantum_advantage_claim_count": 0})
    emit("PR168_GFP2_QuantumObjectiveCoefficientConstraintMap.report.json", quantum_rows, summary={"quantum_mapping_gap_count": len([row for row in quantum_rows if row['structural_readiness_state'] == 'QUANTUM_STRUCTURAL_GAP_ROUTED'])})
    emit("PR168_GFP2_QUBO_BQM_CQM_Ising_QuadraticProgramMappingQueue.report.json", quantum_rows, summary={"quantum_mapping_queue_count": len(quantum_rows)})
    emit("PR168_GFP2_QuantumPenaltyScalingGapQueue.report.json", quantum_rows, summary={"penalty_scaling_gap_count": len([row for row in quantum_rows if not row['penalty_scaling_exists']])})
    emit("PR168_GFP2_ClassicalFallbackComparatorMap.report.json", quantum_rows, summary={"classical_comparator_count": len(quantum_rows)})
    emit("PR168_GFP2_QuantumInterpretBackMapRepairQueue.report.json", quantum_rows, summary={"interpret_back_gap_count": len([row for row in quantum_rows if not row['interpret_back_map_exists']])})
    emit("PR168_GFP2_NoQuantumBackendNoAdvantageAudit.report.json", quantum_rows, summary={"quantum_backend_execution_count": 0, "quantum_advantage_claim_count": 0})
    emit("PR168_GFP2_QuantumPortfolioStackSelectionObjectiveSeed.report.json", quantum_portfolio_objective_seed_rows(), summary={"quantum_portfolio_objective_seed_count": 1})
    emit("PR168_GFP2_QuantumClassicalComparatorRaceSeed.report.json", quantum_portfolio_objective_seed_rows(), summary={"quantum_classical_comparator_seed_count": 1})


def _emit_agent_and_dag_reports(emit, inputs, universe, formula_rows, data_rows, recovery_rows, quantum_rows, prior_rows, dag_rows, no_orphan, terminal_rows, replay_handoff, ranking_rows, source_rows) -> None:
    emit("PR168_GFP2_AgentRosterDiscoveryAuditConsumption.report.json", agent_consumption_rows(inputs, "PR165_D2_AgentRosterDiscoveryAudit.report.json", inputs.agent_roster_rows), summary={"agent_roster_consumed_count": len(inputs.agent_roster_rows)})
    emit("PR168_GFP2_AgentDutySourceCrosswalkConsumption.report.json", agent_consumption_rows(inputs, "PR165_D2_AgentDutySourceCrosswalk.report.json", inputs.agent_duty_rows), summary={"agent_duty_crosswalk_consumed_count": len(inputs.agent_duty_rows)})
    emit("PR168_GFP2_AgentConsumableQKURoutingLedger.report.json", qku_routing_rows(universe), summary={"qku_routing_count": len(universe)})
    emit("PR168_GFP2_AgentConsumableFormulaRoutingLedger.report.json", formula_rows, summary={"formula_routing_count": len(formula_rows)})
    emit("PR168_GFP2_AgentConsumableDataValueRoutingLedger.report.json", data_rows, summary={"data_value_routing_count": len(data_rows)})
    emit("PR168_GFP2_AgentConsumableRecoveryQueueRoutingLedger.report.json", recovery_rows, summary={"recovery_queue_routing_count": len(recovery_rows)})
    emit("PR168_GFP2_AgentConsumableQuantumMappingRoutingLedger.report.json", quantum_rows, summary={"quantum_mapping_routing_count": len(quantum_rows)})
    emit("PR168_GFP2_AgentConsumablePriorResultCorrectionRoutingLedger.report.json", prior_rows, summary={"prior_result_correction_routing_count": len(prior_rows)})
    emit("PR168_GFP2_ArtifactInformationValueDAG.report.json", dag_rows, summary={"dag_node_count": len(dag_rows)})
    emit("PR168_GFP2_AgentDutyDAG.report.json", dag_rows, summary={"agent_duty_dag_node_count": len(dag_rows)})
    emit("PR168_GFP2_NoOrphanProof.report.json", no_orphan, summary={"no_orphan_report_count": len(no_orphan), "orphan_count": 0})
    emit("PR168_GFP2_FileValueUpstreamDownstreamOrchestrationMatrix.report.json", dag_rows, summary={"orchestration_matrix_node_count": len(dag_rows)})
    emit("PR168_GFP2_TerminalArtifactExceptionLedger.report.json", terminal_rows, summary={"terminal_exception_count": len(terminal_rows)})
    emit("PR168_GFP2_To_PR168_RP2_RealMarketReplayRecompute.report.json", replay_handoff, summary={"rp2_handoff_count": len(replay_handoff)})
    emit("PR168_GFP2_To_PR168_RANK2_ProvenanceAwareRankingSeed.report.json", ranking_rows, summary={"rank2_handoff_count": len(ranking_rows)})
    emit("PR168_GFP2_To_PR162E_PluginIntakeCandidateQueue.report.json", source_rows, summary={"plugin_intake_candidate_count": len(source_rows)})
    emit("PR168_GFP2_To_PR162D_R3_ExternalAcquisitionRepairQueue.report.json", source_rows, summary={"external_acquisition_repair_count": len(source_rows)})
    emit("PR168_GFP2_To_PR165_B_NegativeMemorySeed.report.json", recovery_rows, summary={"negative_memory_handoff_count": len(recovery_rows)})
    emit("PR168_GFP2_To_PR167_OpenTradeCombinationReadiness.report.json", replay_handoff, summary={"open_trade_combination_readiness_count": len(replay_handoff)})
    emit("PR168_GFP2_To_RuntimeFormulaAllowlistHotPathCacheSeed.report.json", formula_rows, summary={"runtime_formula_allowlist_seed_count": len(formula_rows)})
    emit("PR168_GFP2_To_DashboardFormulaTradeControlSeed.report.json", formula_rows, summary={"dashboard_control_seed_count": len(formula_rows)})


def _emit_binding_family(emit, name: str, rows: list[dict[str, Any]], family: str) -> None:
    selected = [row for row in rows if row["binding_family"] == family]
    emit(name, selected, summary={"binding_family": family, "binding_queue_count": len(selected)})


def _artifact_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "required_artifact_count": len(rows),
        "found_count": len([row for row in rows if row["found_flag"]]),
        "missing_count": len([row for row in rows if not row["found_flag"]]),
    }


def _count_summary(rows: list[dict[str, Any]], count_name: str) -> dict[str, Any]:
    row = next(item for item in rows if item["count_name"] == count_name)
    return dict(row)


def _data_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"input_data_tier_counts": dict(Counter(row["input_data_tier"] for row in rows))}


def _proof_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "proof_eligible_count": len([row for row in rows if row["proof_eligible_flag"]]),
        "real_positive_claim_allowed_count": len([row for row in rows if row["real_positive_claim_allowed_flag"]]),
        "real_negative_claim_allowed_count": len([row for row in rows if row["real_negative_claim_allowed_flag"]]),
        "zero_positive_final_truth_allowed_count": len([row for row in rows if row["zero_positive_final_truth_allowed_flag"]]),
        "record_count": len(rows),
    }


def _prior_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "prior_result_correction_count": len(rows),
        "classification_counts": dict(Counter(row["new_classification"] for row in rows)),
        "requires_real_market_recompute_count": len([row for row in rows if row["requires_real_market_recompute_flag"]]),
        "champion_eligible_count": len([row for row in rows if row["champion_eligible"]]),
        "live_candidate_worthy_count": len([row for row in rows if row["live_candidate_worthy"]]),
    }


def _zero_positive_row(inputs, eligibility) -> dict[str, Any]:
    return {
        "zero_positive_result_label": "0_REAL_POSITIVES_PROVEN_WITH_ACCEPTED_DATA",
        "old_zero_positive_final_truth_allowed_flag": False,
        "zero_positive_final_truth_allowed_flag": False,
        "computed_positive_count_from_pr168_rp": len(inputs.rp_positive_rows),
        "accepted_real_data_proof_eligible_count": len([row for row in eligibility if row["proof_eligible_flag"]]),
        "recovery_audit_complete_for_real_data_flag": False,
        "reason_code": "ZERO_POSITIVE_NOT_FINAL_TRUTH_WITHOUT_ACCEPTED_REAL_DATA_AND_RECOVERY_AUDIT",
        "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
        "agent_owner": "Governance Agent",
        "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
    }


def _final_summary(inputs, universe, prior_rows, written) -> dict[str, Any]:
    return {
        "reports_written_count": len(written),
        "full_universe_formula_assignment_count": len(universe),
        **BASELINE_COUNTS,
        "accepted_real_market_data_production_count": len(inputs.production_accepted_source_rows),
        "real_positive_count": 0,
        "real_negative_count": 0,
        "zero_positive_final_truth_allowed_flag": False,
        "prior_result_authority_downgraded_count": len(prior_rows),
        "prior_fake_negative_reopened_count": len([row for row in prior_rows if row["prior_fake_negative_flag"]]),
        "prior_fake_neutral_zero_notrade_unproven_count": len([row for row in prior_rows if row["prior_fake_neutral_zero_flag"]]),
        "champion_live_profit_authority_created_flag": False,
        "live_authority_created_flag": False,
        "source_truth_acceptance_created_flag": False,
        "connector_semantic_binding_created_flag": False,
        "private_state_accessed_flag": False,
        "cash_accessed_flag": False,
        "quantum_backend_execution_flag": False,
        "quantum_advantage_claim_flag": False,
        "qku_sha_or_atomicrows_hash_authority_flag": False,
        "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2", "PR162D-R3", "PR162E", "PR165-B", "PR167"],
    }


def _final_summary_row(inputs, universe, prior_rows, written) -> dict[str, Any]:
    row = _final_summary(inputs, universe, prior_rows, written)
    row.update(
        {
            "report_id": "PR168_GFP2_FINAL_SUMMARY_ROW",
            "owning_agent": "Governance Agent",
            "consumer_agents": ["Owner Dashboard", "Governance Agent"],
            "validator_refs": ["tools/pr168_gfp2_validator.py"],
            "test_refs": ["tests/pr168_gfp2"],
            "no_orphan_status": "TERMINAL_WITH_EXACT_REASON_AND_GOVERNANCE_CONSUMER",
            "terminal_by_nature_flag": True,
            "terminal_reason_code": "FINAL_SUMMARY_TERMINAL_BY_NATURE",
        }
    )
    return row


def main() -> int:
    summary = build_all_reports(REPO_ROOT)
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
