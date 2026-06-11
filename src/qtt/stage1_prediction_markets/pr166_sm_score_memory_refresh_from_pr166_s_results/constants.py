"""Constants for PR166-SM report generation and validation."""

from __future__ import annotations

from pathlib import Path

from .enums import DownstreamRoute

PR_ID = "PR166-SM"
BASE_BRANCH = "main"
EXPECTED_BRANCH = "pr166-sm-score-memory-refresh-from-pr166-s-results"
CREATED_AT_UTC = "2026-06-11T00:00:00Z"
AUTHORITY_CLASS = "PR166_SM_REPLAY_PAPER_SCORE_MEMORY_REFRESH_ONLY"
AUTHORITY_BOUNDARY_REF = (
    "PR166_SM_AUTHORITY_BOUNDARY::REPLAY_PAPER_SCORE_MEMORY_ONLY_NO_LIVE_SOURCE_TRUTH_OR_QUANTUM_BACKEND"
)
VALIDATION_STATUS = "PASS"
VALIDATOR_REF = "tools/validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py"
BUILDER_REF = "tools/build_pr166_sm_score_memory_refresh_from_pr166_s_results.py"
MANIFEST_REF = "PR166_SM_ReportManifest.report.json"
SCORE_POLICY_REF = "PR166_SM_SCORE_POLICY::EXECUTION_ADJUSTED_NET_EDGE_V1"
NORMALIZATION_POLICY_REF = "PR166_SM_NORMALIZATION_POLICY::ROBUST_SCENARIO_GROUP_RANK_MINMAX_V1"
CONDITION_SIMILARITY_POLICY_REF = "PR166_SM_CONDITION_SIMILARITY_POLICY::WEIGHTED_BUCKET_EXACT_MATCH_V1"
COMPUTABLE_FORMULA_REF = "PR166_SM_FORMULA::REFRESHED_NET_EDGE_SCORE_V1"
NOT_APPLICABLE_ID = "NOT_APPLICABLE_FOR_THIS_ROW_TERMINAL_BY_NATURE"
NOT_TERMINAL_REASON = "ROW_CONTINUES_TO_DECLARED_DOWNSTREAM_ROUTE"

GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/pr166_sm_score_memory_refresh_from_pr166_s_results"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
SHARD_DIR = GENERATED_DIR / "pr166_sm_shards"
TEST_DIR = Path(
    "tests/stage1_prediction_markets/pr166_sm_score_memory_refresh_from_pr166_s_results"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "pr166_sm_score_memory_refresh_from_pr166_s_results"
)

UPSTREAM_PR_REFS = ("PR165", "PR165-B", "PR165-C", "PR165-D", "PR166-S", "PR208")
DOWNSTREAM_PR_REFS = tuple(route.value for route in DownstreamRoute)
DEFAULT_DOWNSTREAM_ARTIFACT_REFS = (
    "PR166_SM_RefreshedScoreRegistry.report.json",
    "PR166_SM_RefreshedMemoryLedger.report.json",
    "PR165-D2",
    "PR166-SF",
    "PR166-Q",
)

SCORE_WEIGHTS = {
    "normalized_net_edge_after_costs": 0.24,
    "result_confidence_score": 0.12,
    "no_lookahead_score": 0.10,
    "point_in_time_score": 0.10,
    "score_refresh_candidate_strength": 0.08,
    "memory_refresh_candidate_strength": 0.08,
    "scenario_consistency_score": 0.06,
    "scenario_transferability_score": 0.05,
    "fill_quality_score": 0.05,
    "settlement_confidence_score": 0.04,
    "capacity_score": 0.04,
    "quantum_mapping_readiness_score": 0.03,
    "false_discovery_risk_adjustment": -0.05,
    "overfit_risk_adjustment": -0.05,
    "cost_drag_ratio": -0.04,
    "latency_drag_ratio": -0.04,
    "liquidity_drag_ratio": -0.04,
    "adverse_selection_ratio": -0.03,
    "crowding_penalty": -0.03,
    "correlation_cluster_penalty": -0.03,
    "rank_instability_adjustment": -0.02,
}

SCENARIO_SIMILARITY_WEIGHTS = {
    "venue": 0.10,
    "market_scope": 0.08,
    "contract_type": 0.07,
    "side": 0.06,
    "order_type": 0.06,
    "time_to_resolution_bucket": 0.10,
    "liquidity_bucket": 0.10,
    "spread_bucket": 0.10,
    "latency_bucket": 0.08,
    "fee_bucket": 0.04,
    "slippage_bucket": 0.06,
    "settlement_bucket": 0.06,
    "probability_bucket": 0.06,
    "data_quality_bucket": 0.05,
    "quantum_compatibility_bucket": 0.04,
    "source_quality_bucket": 0.04,
}

REQUIRED_INPUT_REPORTS: tuple[str, ...] = (
    "PR166_S_ResultAttributionLedger.report.json",
    "PR166_S_ResultConfidenceRegistry.report.json",
    "PR166_S_ScoreRefreshCandidateRegistry.report.json",
    "PR166_S_MemoryRefreshCandidateRegistry.report.json",
    "PR166_S_RepairFeedbackRouter.report.json",
    "PR166_S_ExecutionCostLedger.report.json",
    "PR166_S_FeeModelLedger.report.json",
    "PR166_S_SpreadModelLedger.report.json",
    "PR166_S_SlippageModelLedger.report.json",
    "PR166_S_LatencyModelLedger.report.json",
    "PR166_S_LiquidityModelLedger.report.json",
    "PR166_S_MarketImpactModelLedger.report.json",
    "PR166_S_SettlementAssumptionLedger.report.json",
    "PR166_S_PointInTimeExecutionAudit.report.json",
    "PR166_S_NoLookaheadAudit.report.json",
    "PR166_S_QuantumAdvisoryPassthrough.report.json",
    "PR166_S_AgentExecutionContract.report.json",
    "PR166_S_AgentExecutionHandoff.report.json",
    "PR166_S_DashboardExecutionHandoff.report.json",
    "PR166_S_GovernanceExecutionHandoff.report.json",
    "PR166_S_CommanderExecutionHandoff.report.json",
    "PR166_S_FinalSummary.report.json",
    "PR166_S_ReportManifest.report.json",
    "PR165_ReportManifest.report.json",
    "PR165_FinalSummary.report.json",
    "PR165_GlobalCandidateRanking.report.json",
    "PR165_RegimeSlicedRanking.report.json",
    "PR165_ExpectedValueScoreRegistry.report.json",
    "PR165_TCAAdjustedScoreRegistry.report.json",
    "PR165_LatencyLaneAssignmentRegistry.report.json",
    "PR165_QuantumFormulationMaterializationRegistry.report.json",
    "PR165_B_ConditionFingerprintRegistry.report.json",
    "PR165_B_CombinationFingerprintRegistry.report.json",
    "PR165_B_ScenarioOutcomeMatrix.report.json",
    "PR165_B_CombinationOutcomeMemoryLedger.report.json",
    "PR165_B_NegativeCombinationAvoidanceRegistry.report.json",
    "PR165_B_PositiveConditionScopedPreferenceRegistry.report.json",
    "PR165_B_FragileCombinationWatchlist.report.json",
    "PR165_C_MemoryConsumerRouter.report.json",
    "PR165_C_ComputableArtifactPayloadRegistry.report.json",
    "PR165_C_ComputableQKUFormulaActionRegistry.report.json",
    "PR165_C_FormulaTestVectorRegistry.report.json",
    "PR165_C_ConditionRegimeFeatureMatrix.report.json",
    "PR165_C_QuantumConsumerRouter.report.json",
    "PR165_D_ScenarioQKUCombinationSelectionPolicy.report.json",
    "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json",
    "PR165_D_RetestBatchSelectionQueue.report.json",
    "PR165_D_RepairBeforeRetestSelectionQueue.report.json",
    "PR165_D_SelectionScoreRegistry.report.json",
    "PR165_D_MarginalUtilitySelectionLedger.report.json",
    "PR165_D_BatchExposureCapacityLedger.report.json",
    "PR165_D_SelectionFalseDiscoveryControl.report.json",
    "PR165_D_PointInTimeSelectionAudit.report.json",
    "PR165_D_AgentSelectionHandoff.report.json",
    "PR165_D_QuantumSelectionRouter.report.json",
    "PR165_D_AuthorityBoundaryAudit.report.json",
    "PR165_D_OrphanArtifactAudit.report.json",
)

OPTIONAL_INPUT_REPORTS: tuple[str, ...] = (
    "PR166_S_OptionalReplayPaperInputMissingReceipt.report.json",
)

EXPECTED_ROW_COUNTS = {
    "PR166_S_ResultAttributionLedger.report.json": 3985,
    "PR166_S_ResultConfidenceRegistry.report.json": 3985,
    "PR166_S_ScoreRefreshCandidateRegistry.report.json": 3985,
    "PR166_S_MemoryRefreshCandidateRegistry.report.json": 3985,
    "PR166_S_RepairFeedbackRouter.report.json": 6497,
    "PR166_S_QuantumAdvisoryPassthrough.report.json": 6502,
    "PR166_S_ExecutionCostLedger.report.json": 3985,
    "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json": 6502,
    "PR165_D_SelectionScoreRegistry.report.json": 6502,
    "PR165_D_QuantumSelectionRouter.report.json": 6502,
}

REPORT_FILENAMES: tuple[str, ...] = (
    "PR166_SM_InputConsumptionAudit.report.json",
    "PR166_SM_ReplayPaperResultRefreshPolicy.report.json",
    "PR166_SM_ScoreNormalizationPolicy.report.json",
    "PR166_SM_RefreshedScoreRegistry.report.json",
    "PR166_SM_RefreshedMemoryLedger.report.json",
    "PR166_SM_NetEdgeRankDeltaRegistry.report.json",
    "PR166_SM_ConditionScopedWinnerRegistry.report.json",
    "PR166_SM_ConditionScopedLoserRegistry.report.json",
    "PR166_SM_CostDominatedDowngradeRegistry.report.json",
    "PR166_SM_LatencyDominatedDowngradeRegistry.report.json",
    "PR166_SM_LiquidityDominatedDowngradeRegistry.report.json",
    "PR166_SM_AdverseSelectionDowngradeRegistry.report.json",
    "PR166_SM_SettlementSensitivityRegistry.report.json",
    "PR166_SM_FalseDiscoveryRiskRefreshLedger.report.json",
    "PR166_SM_OverfitAndRankInstabilityRegistry.report.json",
    "PR166_SM_CapacityAndCrowdingRegistry.report.json",
    "PR166_SM_CorrelationClusterRegistry.report.json",
    "PR166_SM_RepairPriorityRegistry.report.json",
    "PR166_SM_QuantumPriorityAfterReplayPaperRegistry.report.json",
    "PR166_SM_QuantumMappingCandidateReadiness.report.json",
    "PR166_SM_AgentScoreMemoryRefreshContract.report.json",
    "PR166_SM_AgentTaskQueue.report.json",
    "PR166_SM_DashboardScoreMemoryRefreshHandoff.report.json",
    "PR166_SM_GovernanceScoreMemoryRefreshHandoff.report.json",
    "PR166_SM_CommanderScoreMemoryRefreshHandoff.report.json",
    "PR166_SM_PRFileConnectivityAudit.report.json",
    "PR166_SM_RowValueConnectivityAudit.report.json",
    "PR166_SM_AuthorityBoundaryAudit.report.json",
    "PR166_SM_OrphanArtifactAudit.report.json",
    "PR166_SM_StatusEnumDriftAudit.report.json",
    "PR166_SM_ReportManifest.report.json",
    "PR166_SM_FinalSummary.report.json",
    "PR166_SM_ExternalCandidateValueIntakeRegistry.report.json",
    "PR166_SM_FieldMaterializationCandidateRegistry.report.json",
    "PR166_SM_QKUComputabilityClosureAudit.report.json",
    "PR166_SM_InstitutionalSignalQualityAudit.report.json",
    "PR166_SM_SelectionReadinessForPR165D2.report.json",
    "PR166_SM_FailureRepairRouteHandoffToPR166SF.report.json",
)

SUMMARY_REPORTS = frozenset(
    {
        "PR166_SM_InputConsumptionAudit.report.json",
        "PR166_SM_ReplayPaperResultRefreshPolicy.report.json",
        "PR166_SM_ScoreNormalizationPolicy.report.json",
        "PR166_SM_AgentScoreMemoryRefreshContract.report.json",
        "PR166_SM_DashboardScoreMemoryRefreshHandoff.report.json",
        "PR166_SM_GovernanceScoreMemoryRefreshHandoff.report.json",
        "PR166_SM_CommanderScoreMemoryRefreshHandoff.report.json",
        "PR166_SM_PRFileConnectivityAudit.report.json",
        "PR166_SM_RowValueConnectivityAudit.report.json",
        "PR166_SM_AuthorityBoundaryAudit.report.json",
        "PR166_SM_OrphanArtifactAudit.report.json",
        "PR166_SM_StatusEnumDriftAudit.report.json",
        "PR166_SM_ReportManifest.report.json",
        "PR166_SM_FinalSummary.report.json",
        "PR166_SM_ExternalCandidateValueIntakeRegistry.report.json",
        "PR166_SM_InstitutionalSignalQualityAudit.report.json",
    }
)
ROW_LEVEL_REPORTS = frozenset(filename for filename in REPORT_FILENAMES if filename not in SUMMARY_REPORTS)

SCHEMA_FILENAMES: tuple[str, ...] = (
    "pr166_sm_common.schema.json",
    "pr166_sm_input_consumption_audit.schema.json",
    "pr166_sm_replay_paper_result_refresh_policy.schema.json",
    "pr166_sm_score_normalization_policy.schema.json",
    "pr166_sm_refreshed_score_registry.schema.json",
    "pr166_sm_refreshed_memory_ledger.schema.json",
    "pr166_sm_net_edge_rank_delta_registry.schema.json",
    "pr166_sm_condition_scoped_winner_registry.schema.json",
    "pr166_sm_condition_scoped_loser_registry.schema.json",
    "pr166_sm_cost_dominated_downgrade_registry.schema.json",
    "pr166_sm_latency_dominated_downgrade_registry.schema.json",
    "pr166_sm_liquidity_dominated_downgrade_registry.schema.json",
    "pr166_sm_adverse_selection_downgrade_registry.schema.json",
    "pr166_sm_settlement_sensitivity_registry.schema.json",
    "pr166_sm_false_discovery_risk_refresh_ledger.schema.json",
    "pr166_sm_overfit_and_rank_instability_registry.schema.json",
    "pr166_sm_capacity_and_crowding_registry.schema.json",
    "pr166_sm_correlation_cluster_registry.schema.json",
    "pr166_sm_repair_priority_registry.schema.json",
    "pr166_sm_quantum_priority_after_replay_paper_registry.schema.json",
    "pr166_sm_quantum_mapping_candidate_readiness.schema.json",
    "pr166_sm_agent_score_memory_refresh_contract.schema.json",
    "pr166_sm_agent_task_queue.schema.json",
    "pr166_sm_dashboard_score_memory_refresh_handoff.schema.json",
    "pr166_sm_governance_score_memory_refresh_handoff.schema.json",
    "pr166_sm_commander_score_memory_refresh_handoff.schema.json",
    "pr166_sm_pr_file_connectivity_audit.schema.json",
    "pr166_sm_row_value_connectivity_audit.schema.json",
    "pr166_sm_authority_boundary_audit.schema.json",
    "pr166_sm_orphan_artifact_audit.schema.json",
    "pr166_sm_status_enum_drift_audit.schema.json",
    "pr166_sm_report_manifest.schema.json",
    "pr166_sm_final_summary.schema.json",
    "pr166_sm_external_candidate_value_intake.schema.json",
    "pr166_sm_field_materialization_candidate_registry.schema.json",
    "pr166_sm_qku_computability_closure_audit.schema.json",
    "pr166_sm_institutional_signal_quality_audit.schema.json",
    "pr166_sm_selection_readiness_for_pr165_d2.schema.json",
    "pr166_sm_failure_repair_route_handoff_to_pr166_sf.schema.json",
)

REPORT_SCHEMA_REFS = {
    "PR166_SM_InputConsumptionAudit.report.json": "pr166_sm_input_consumption_audit.schema.json",
    "PR166_SM_ReplayPaperResultRefreshPolicy.report.json": "pr166_sm_replay_paper_result_refresh_policy.schema.json",
    "PR166_SM_ScoreNormalizationPolicy.report.json": "pr166_sm_score_normalization_policy.schema.json",
    "PR166_SM_RefreshedScoreRegistry.report.json": "pr166_sm_refreshed_score_registry.schema.json",
    "PR166_SM_RefreshedMemoryLedger.report.json": "pr166_sm_refreshed_memory_ledger.schema.json",
    "PR166_SM_NetEdgeRankDeltaRegistry.report.json": "pr166_sm_net_edge_rank_delta_registry.schema.json",
    "PR166_SM_ConditionScopedWinnerRegistry.report.json": "pr166_sm_condition_scoped_winner_registry.schema.json",
    "PR166_SM_ConditionScopedLoserRegistry.report.json": "pr166_sm_condition_scoped_loser_registry.schema.json",
    "PR166_SM_CostDominatedDowngradeRegistry.report.json": "pr166_sm_cost_dominated_downgrade_registry.schema.json",
    "PR166_SM_LatencyDominatedDowngradeRegistry.report.json": "pr166_sm_latency_dominated_downgrade_registry.schema.json",
    "PR166_SM_LiquidityDominatedDowngradeRegistry.report.json": "pr166_sm_liquidity_dominated_downgrade_registry.schema.json",
    "PR166_SM_AdverseSelectionDowngradeRegistry.report.json": "pr166_sm_adverse_selection_downgrade_registry.schema.json",
    "PR166_SM_SettlementSensitivityRegistry.report.json": "pr166_sm_settlement_sensitivity_registry.schema.json",
    "PR166_SM_FalseDiscoveryRiskRefreshLedger.report.json": "pr166_sm_false_discovery_risk_refresh_ledger.schema.json",
    "PR166_SM_OverfitAndRankInstabilityRegistry.report.json": "pr166_sm_overfit_and_rank_instability_registry.schema.json",
    "PR166_SM_CapacityAndCrowdingRegistry.report.json": "pr166_sm_capacity_and_crowding_registry.schema.json",
    "PR166_SM_CorrelationClusterRegistry.report.json": "pr166_sm_correlation_cluster_registry.schema.json",
    "PR166_SM_RepairPriorityRegistry.report.json": "pr166_sm_repair_priority_registry.schema.json",
    "PR166_SM_QuantumPriorityAfterReplayPaperRegistry.report.json": "pr166_sm_quantum_priority_after_replay_paper_registry.schema.json",
    "PR166_SM_QuantumMappingCandidateReadiness.report.json": "pr166_sm_quantum_mapping_candidate_readiness.schema.json",
    "PR166_SM_AgentScoreMemoryRefreshContract.report.json": "pr166_sm_agent_score_memory_refresh_contract.schema.json",
    "PR166_SM_AgentTaskQueue.report.json": "pr166_sm_agent_task_queue.schema.json",
    "PR166_SM_DashboardScoreMemoryRefreshHandoff.report.json": "pr166_sm_dashboard_score_memory_refresh_handoff.schema.json",
    "PR166_SM_GovernanceScoreMemoryRefreshHandoff.report.json": "pr166_sm_governance_score_memory_refresh_handoff.schema.json",
    "PR166_SM_CommanderScoreMemoryRefreshHandoff.report.json": "pr166_sm_commander_score_memory_refresh_handoff.schema.json",
    "PR166_SM_PRFileConnectivityAudit.report.json": "pr166_sm_pr_file_connectivity_audit.schema.json",
    "PR166_SM_RowValueConnectivityAudit.report.json": "pr166_sm_row_value_connectivity_audit.schema.json",
    "PR166_SM_AuthorityBoundaryAudit.report.json": "pr166_sm_authority_boundary_audit.schema.json",
    "PR166_SM_OrphanArtifactAudit.report.json": "pr166_sm_orphan_artifact_audit.schema.json",
    "PR166_SM_StatusEnumDriftAudit.report.json": "pr166_sm_status_enum_drift_audit.schema.json",
    "PR166_SM_ReportManifest.report.json": "pr166_sm_report_manifest.schema.json",
    "PR166_SM_FinalSummary.report.json": "pr166_sm_final_summary.schema.json",
    "PR166_SM_ExternalCandidateValueIntakeRegistry.report.json": "pr166_sm_external_candidate_value_intake.schema.json",
    "PR166_SM_FieldMaterializationCandidateRegistry.report.json": "pr166_sm_field_materialization_candidate_registry.schema.json",
    "PR166_SM_QKUComputabilityClosureAudit.report.json": "pr166_sm_qku_computability_closure_audit.schema.json",
    "PR166_SM_InstitutionalSignalQualityAudit.report.json": "pr166_sm_institutional_signal_quality_audit.schema.json",
    "PR166_SM_SelectionReadinessForPR165D2.report.json": "pr166_sm_selection_readiness_for_pr165_d2.schema.json",
    "PR166_SM_FailureRepairRouteHandoffToPR166SF.report.json": "pr166_sm_failure_repair_route_handoff_to_pr166_sf.schema.json",
}

SOURCE_FILENAMES = (
    "__init__.py",
    "authority.py",
    "constants.py",
    "enums.py",
    "io.py",
    "models.py",
    "normalization.py",
    "scoring.py",
    "cost_model.py",
    "confidence.py",
    "memory.py",
    "scenario_similarity.py",
    "ranking.py",
    "dominance.py",
    "false_discovery.py",
    "capacity.py",
    "quantum_priority.py",
    "repair_priority.py",
    "external_intake.py",
    "connectivity.py",
    "manifest.py",
    "report_writer.py",
    "validator.py",
)
