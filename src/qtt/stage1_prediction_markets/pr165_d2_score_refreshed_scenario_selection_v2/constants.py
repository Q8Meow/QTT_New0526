"""Constants for PR165-D2 score-refreshed scenario selection v2."""

from __future__ import annotations

from pathlib import Path

PR_ID = "PR165-D2"
BASE_BRANCH = "main"
EXPECTED_BRANCH = "pr165-d2-score-refreshed-scenario-selection-v2"
CREATED_AT_UTC = "2026-06-11T00:00:00Z"
AUTHORITY_CLASS = "PR165_D2_REPLAY_PAPER_SELECTION_ONLY_NO_LIVE_OR_SOURCE_TRUTH"
AUTHORITY_BOUNDARY_REF = (
    "PR165_D2_AUTHORITY_BOUNDARY::REPLAY_PAPER_SELECTION_ONLY_NO_LIVE_SOURCE_TRUTH_CONNECTOR_OR_QUANTUM_BACKEND"
)
VALIDATION_STATUS = "PASS"
VALIDATOR_REF = "tools/validate_pr165_d2_score_refreshed_scenario_selection_v2.py"
BUILDER_REF = "tools/build_pr165_d2_score_refreshed_scenario_selection_v2.py"
MANIFEST_REF = "PR165_D2_ReportManifest.report.json"
SCORE_POLICY_REF = "PR165_D2_SCORE_POLICY::EXECUTION_ADJUSTED_SCENARIO_SELECTION_V2"
NORMALIZATION_POLICY_REF = "PR165_D2_NORMALIZATION_POLICY::ROBUST_SCENARIO_GROUP_RANK_MINMAX_V2"
CONDITION_MEMORY_POLICY_REF = "PR165_D2_CONDITION_MEMORY_POLICY::CONDITION_SCOPED_PREFERENCE_V2"
CONNECTOR_READINESS_POLICY_REF = "PR165_D2_CONNECTOR_READINESS_POLICY::REFERENCE_ROUTE_ONLY_V1"
NOT_APPLICABLE_ID = "NOT_APPLICABLE_FOR_THIS_ROW_TERMINAL_BY_NATURE"
NOT_TERMINAL_REASON = "ROW_CONTINUES_TO_DECLARED_DOWNSTREAM_ROUTE"
MATERIAL_NEGATIVE_NET_EDGE_THRESHOLD = -0.10
REPAIR_BEFORE_RETEST_PRIORITY_THRESHOLD = 0.50
LOW_CONFIDENCE_THRESHOLD = 0.35
OVERFIT_RISK_THRESHOLD = 0.85
DEFAULT_SHARD_ROW_TARGET = 1000

GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr165_d2_shards"
PACKAGE_DIR = Path("src/qtt/stage1_prediction_markets/pr165_d2_score_refreshed_scenario_selection_v2")
SCHEMA_DIR = PACKAGE_DIR / "schemas"
TEST_DIR = Path("tests/stage1_prediction_markets/pr165_d2_score_refreshed_scenario_selection_v2")
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2"
)

UPSTREAM_PR_REFS = ("PR165", "PR165-B", "PR165-C", "PR165-D", "PR166-S", "PR166-SM", "PR164")
DOWNSTREAM_PR_REFS = (
    "PR166-S_RETEST_LOOP",
    "PR166-S_RETEST_LOOP_V2",
    "PR166-SF",
    "PR166-Q",
    "PR162E-Q",
    "PR162D-R3",
    "PR162E",
    "PR162F",
    "PR167",
    "PR168",
    "PR169",
    "PR170",
    "PR171",
    "PR172",
    "PR173",
    "PR174",
    "PR175",
    "PR176",
    "PR177",
    "PR178",
    "PR179",
    "PR180",
    "PR181",
    "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
    "TERMINAL_BY_NATURE_WITH_REASON",
)

FUTURE_CONNECTOR_PR_REFS = ("PR174", "PR175", "PR176", "PR177", "PR178", "PR179", "PR180", "PR181")

SCORE_WEIGHTS = {
    "normalized_net_edge_after_costs": 0.24,
    "edge_lower_confidence_bound": 0.12,
    "pr166_sm_refreshed_score": 0.11,
    "result_confidence_score": 0.09,
    "condition_memory_preference_score": 0.08,
    "point_in_time_score": 0.07,
    "no_lookahead_score": 0.07,
    "scenario_transferability_score": 0.05,
    "capacity_score": 0.05,
    "marginal_utility_score": 0.04,
    "expected_information_gain_score": 0.03,
    "quantum_mapping_readiness_score": 0.03,
    "false_discovery_risk_adjustment": -0.05,
    "overfit_risk_adjustment": -0.05,
    "cost_drag_ratio": -0.04,
    "latency_drag_ratio": -0.04,
    "liquidity_drag_ratio": -0.04,
    "adverse_selection_ratio": -0.03,
    "crowding_penalty": -0.03,
    "correlation_cluster_penalty": -0.03,
    "settlement_sensitivity_score": -0.02,
    "rank_instability_adjustment": -0.02,
    "repair_dependency_penalty": -0.02,
}

POSITIVE_SCORE_COMPONENTS = tuple(name for name, weight in SCORE_WEIGHTS.items() if weight > 0)
NEGATIVE_SCORE_COMPONENTS = tuple(name for name, weight in SCORE_WEIGHTS.items() if weight < 0)

REQUIRED_INPUT_REPORTS: tuple[str, ...] = (
    "PR166_SM_FinalSummary.report.json",
    "PR166_SM_ReportManifest.report.json",
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
    "PR166_SM_ExternalCandidateValueIntakeRegistry.report.json",
    "PR166_SM_FieldMaterializationCandidateRegistry.report.json",
    "PR166_SM_QKUComputabilityClosureAudit.report.json",
    "PR166_SM_InstitutionalSignalQualityAudit.report.json",
    "PR166_SM_SelectionReadinessForPR165D2.report.json",
    "PR166_SM_FailureRepairRouteHandoffToPR166SF.report.json",
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
    "PR166_S_FinalSummary.report.json",
    "PR166_S_ReportManifest.report.json",
    "PR166_S_ResultAttributionLedger.report.json",
    "PR166_S_ResultConfidenceRegistry.report.json",
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
    "PR165_D_FinalSummary.report.json",
    "PR165_D_ScenarioQKUCombinationSelectionPolicy.report.json",
    "PR165_D_ScenarioGroupRegistry.report.json",
    "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json",
    "PR165_D_RetestBatchSelectionQueue.report.json",
    "PR165_D_RepairBeforeRetestSelectionQueue.report.json",
    "PR165_D_SelectedExcludedReasonLedger.report.json",
    "PR165_D_SelectionScoreRegistry.report.json",
    "PR165_D_MarginalUtilitySelectionLedger.report.json",
    "PR165_D_BatchExposureCapacityLedger.report.json",
    "PR165_D_SelectionFalseDiscoveryControl.report.json",
    "PR165_D_PointInTimeSelectionAudit.report.json",
    "PR165_D_QuantumSelectionRouter.report.json",
    "PR165_D_FormulaAlgorithmOptionalRouteRegistry.report.json",
    "PR165_D_AuthorityBoundaryAudit.report.json",
    "PR165_D_OrphanArtifactAudit.report.json",
    "PR165_B_ConditionFingerprintRegistry.report.json",
    "PR165_B_CombinationFingerprintRegistry.report.json",
    "PR165_B_ScenarioOutcomeMatrix.report.json",
    "PR165_B_CombinationOutcomeMemoryLedger.report.json",
    "PR165_B_NegativeCombinationAvoidanceRegistry.report.json",
    "PR165_B_PositiveConditionScopedPreferenceRegistry.report.json",
    "PR165_B_FragileCombinationWatchlist.report.json",
    "PR165_C_MemoryConsumerRouter.report.json",
    "PR165_C_PendingRetestQueue.report.json",
    "PR165_C_RepairToRetestHandoff.report.json",
    "PR165_C_ComputableArtifactPayloadRegistry.report.json",
    "PR165_C_ComputableQKUFormulaActionRegistry.report.json",
    "PR165_C_FormulaTestVectorRegistry.report.json",
    "PR165_C_ConditionRegimeFeatureMatrix.report.json",
    "PR165_C_QuantumConsumerRouter.report.json",
)

OPTIONAL_PR166_SF_REPORTS: tuple[str, ...] = (
    "PR166_SF_RepairedCandidateRetestQueue.report.json",
    "PR166_SF_FinalSummary.report.json",
    "PR166_SF_ReportManifest.report.json",
)

EXPECTED_ROW_COUNTS = {
    "PR166_SM_RefreshedScoreRegistry.report.json": 3985,
    "PR166_SM_RefreshedMemoryLedger.report.json": 3985,
    "PR166_SM_NetEdgeRankDeltaRegistry.report.json": 3985,
    "PR166_SM_RepairPriorityRegistry.report.json": 3985,
    "PR166_SM_QKUComputabilityClosureAudit.report.json": 6502,
    "PR166_SM_FieldMaterializationCandidateRegistry.report.json": 6502,
    "PR166_SM_QuantumPriorityAfterReplayPaperRegistry.report.json": 6502,
    "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json": 6502,
    "PR165_D_RetestBatchSelectionQueue.report.json": 6497,
    "PR165_D_RepairBeforeRetestSelectionQueue.report.json": 2512,
}

REPORT_FILENAMES: tuple[str, ...] = (
    "PR165_D2_InputConsumptionAudit.report.json",
    "PR165_D2_OptionalInputResolutionLedger.report.json",
    "PR165_D2_RowCountReconciliationLedger.report.json",
    "PR165_D2_ScoreRefreshedScenarioSelectionPolicy.report.json",
    "PR165_D2_ScoreNormalizationPolicy.report.json",
    "PR165_D2_ScoreComponentProvenanceLedger.report.json",
    "PR165_D2_PredictionMarketProbabilityEdgeLedger.report.json",
    "PR165_D2_MicrostructureFeatureLedger.report.json",
    "PR165_D2_NetEdgeAdjustedCandidateRanking.report.json",
    "PR165_D2_ReplayPaperRetestBatchV2.report.json",
    "PR165_D2_RepairAwareSelectionQueue.report.json",
    "PR165_D2_QuantumCandidatePriorityV2.report.json",
    "PR165_D2_ScenarioGroupRefreshRegistry.report.json",
    "PR165_D2_ConditionMemoryApplicationLedger.report.json",
    "PR165_D2_ChampionChallengerSelectionLedger.report.json",
    "PR165_D2_MarginalUtilityBatchBuilderLedger.report.json",
    "PR165_D2_CapacityCrowdingCorrelationSelectionLedger.report.json",
    "PR165_D2_FalseDiscoveryOverfitSelectionControl.report.json",
    "PR165_D2_TCADecompositionSelectionLedger.report.json",
    "PR165_D2_RetestBudgetAllocationPolicy.report.json",
    "PR165_D2_RouteTriageMatrix.report.json",
    "PR165_D2_ConnectorVenueReadinessReferenceRouting.report.json",
    "PR165_D2_MasterPlanSectionCrosswalk.report.json",
    "PR165_D2_MarketSpecificSelectionIndex.report.json",
    "PR165_D2_CommandActionMatrix.report.json",
    "PR165_D2_SelectionExclusionReasonLedger.report.json",
    "PR165_D2_ExternalSelectionSignalCandidateRegistry.report.json",
    "PR165_D2_ExternalInstitutionalSignalCoverageAudit.report.json",
    "PR165_D2_QKUFormulaAlgorithmComputabilityRouting.report.json",
    "PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "PR165_D2_AgentDutySourceCrosswalk.report.json",
    "PR165_D2_AgentSelectionHandoff.report.json",
    "PR165_D2_AgentTaskQueue.report.json",
    "PR165_D2_DashboardSelectionHandoff.report.json",
    "PR165_D2_GovernanceSelectionHandoff.report.json",
    "PR165_D2_CommanderSelectionHandoff.report.json",
    "PR165_D2_PRFileConnectivityAudit.report.json",
    "PR165_D2_RowValueConnectivityAudit.report.json",
    "PR165_D2_AuthorityBoundaryAudit.report.json",
    "PR165_D2_OrphanArtifactAudit.report.json",
    "PR165_D2_StatusEnumDriftAudit.report.json",
    "PR165_D2_ReportManifest.report.json",
    "PR165_D2_FinalSummary.report.json",
)

SUMMARY_REPORTS = frozenset(
    {
        "PR165_D2_InputConsumptionAudit.report.json",
        "PR165_D2_OptionalInputResolutionLedger.report.json",
        "PR165_D2_RowCountReconciliationLedger.report.json",
        "PR165_D2_ScoreRefreshedScenarioSelectionPolicy.report.json",
        "PR165_D2_ScoreNormalizationPolicy.report.json",
        "PR165_D2_RetestBudgetAllocationPolicy.report.json",
        "PR165_D2_ExternalSelectionSignalCandidateRegistry.report.json",
        "PR165_D2_ExternalInstitutionalSignalCoverageAudit.report.json",
        "PR165_D2_AgentRosterDiscoveryAudit.report.json",
        "PR165_D2_AgentDutySourceCrosswalk.report.json",
        "PR165_D2_AgentSelectionHandoff.report.json",
        "PR165_D2_AgentTaskQueue.report.json",
        "PR165_D2_DashboardSelectionHandoff.report.json",
        "PR165_D2_GovernanceSelectionHandoff.report.json",
        "PR165_D2_CommanderSelectionHandoff.report.json",
        "PR165_D2_PRFileConnectivityAudit.report.json",
        "PR165_D2_RowValueConnectivityAudit.report.json",
        "PR165_D2_AuthorityBoundaryAudit.report.json",
        "PR165_D2_OrphanArtifactAudit.report.json",
        "PR165_D2_StatusEnumDriftAudit.report.json",
        "PR165_D2_ReportManifest.report.json",
        "PR165_D2_FinalSummary.report.json",
    }
)
ROW_LEVEL_REPORTS = frozenset(filename for filename in REPORT_FILENAMES if filename not in SUMMARY_REPORTS)

SCHEMA_FILENAMES: tuple[str, ...] = (
    "pr165_d2_common.schema.json",
    "pr165_d2_input_consumption_audit.schema.json",
    "pr165_d2_optional_input_resolution_ledger.schema.json",
    "pr165_d2_row_count_reconciliation_ledger.schema.json",
    "pr165_d2_score_refreshed_scenario_selection_policy.schema.json",
    "pr165_d2_score_normalization_policy.schema.json",
    "pr165_d2_score_component_provenance_ledger.schema.json",
    "pr165_d2_prediction_market_probability_edge_ledger.schema.json",
    "pr165_d2_microstructure_feature_ledger.schema.json",
    "pr165_d2_net_edge_adjusted_candidate_ranking.schema.json",
    "pr165_d2_replay_paper_retest_batch_v2.schema.json",
    "pr165_d2_repair_aware_selection_queue.schema.json",
    "pr165_d2_quantum_candidate_priority_v2.schema.json",
    "pr165_d2_scenario_group_refresh_registry.schema.json",
    "pr165_d2_condition_memory_application_ledger.schema.json",
    "pr165_d2_champion_challenger_selection_ledger.schema.json",
    "pr165_d2_marginal_utility_batch_builder_ledger.schema.json",
    "pr165_d2_capacity_crowding_correlation_selection_ledger.schema.json",
    "pr165_d2_false_discovery_overfit_selection_control.schema.json",
    "pr165_d2_tca_decomposition_selection_ledger.schema.json",
    "pr165_d2_retest_budget_allocation_policy.schema.json",
    "pr165_d2_route_triage_matrix.schema.json",
    "pr165_d2_connector_venue_readiness_reference_routing.schema.json",
    "pr165_d2_master_plan_section_crosswalk.schema.json",
    "pr165_d2_market_specific_selection_index.schema.json",
    "pr165_d2_command_action_matrix.schema.json",
    "pr165_d2_selection_exclusion_reason_ledger.schema.json",
    "pr165_d2_external_selection_signal_candidate_registry.schema.json",
    "pr165_d2_external_institutional_signal_coverage_audit.schema.json",
    "pr165_d2_qku_formula_algorithm_computability_routing.schema.json",
    "pr165_d2_agent_roster_discovery_audit.schema.json",
    "pr165_d2_agent_duty_source_crosswalk.schema.json",
    "pr165_d2_agent_selection_handoff.schema.json",
    "pr165_d2_agent_task_queue.schema.json",
    "pr165_d2_dashboard_selection_handoff.schema.json",
    "pr165_d2_governance_selection_handoff.schema.json",
    "pr165_d2_commander_selection_handoff.schema.json",
    "pr165_d2_pr_file_connectivity_audit.schema.json",
    "pr165_d2_row_value_connectivity_audit.schema.json",
    "pr165_d2_authority_boundary_audit.schema.json",
    "pr165_d2_orphan_artifact_audit.schema.json",
    "pr165_d2_status_enum_drift_audit.schema.json",
    "pr165_d2_report_manifest.schema.json",
    "pr165_d2_final_summary.schema.json",
)

REPORT_SCHEMA_REFS = {
    "PR165_D2_InputConsumptionAudit.report.json": "pr165_d2_input_consumption_audit.schema.json",
    "PR165_D2_OptionalInputResolutionLedger.report.json": "pr165_d2_optional_input_resolution_ledger.schema.json",
    "PR165_D2_RowCountReconciliationLedger.report.json": "pr165_d2_row_count_reconciliation_ledger.schema.json",
    "PR165_D2_ScoreRefreshedScenarioSelectionPolicy.report.json": "pr165_d2_score_refreshed_scenario_selection_policy.schema.json",
    "PR165_D2_ScoreNormalizationPolicy.report.json": "pr165_d2_score_normalization_policy.schema.json",
    "PR165_D2_ScoreComponentProvenanceLedger.report.json": "pr165_d2_score_component_provenance_ledger.schema.json",
    "PR165_D2_PredictionMarketProbabilityEdgeLedger.report.json": "pr165_d2_prediction_market_probability_edge_ledger.schema.json",
    "PR165_D2_MicrostructureFeatureLedger.report.json": "pr165_d2_microstructure_feature_ledger.schema.json",
    "PR165_D2_NetEdgeAdjustedCandidateRanking.report.json": "pr165_d2_net_edge_adjusted_candidate_ranking.schema.json",
    "PR165_D2_ReplayPaperRetestBatchV2.report.json": "pr165_d2_replay_paper_retest_batch_v2.schema.json",
    "PR165_D2_RepairAwareSelectionQueue.report.json": "pr165_d2_repair_aware_selection_queue.schema.json",
    "PR165_D2_QuantumCandidatePriorityV2.report.json": "pr165_d2_quantum_candidate_priority_v2.schema.json",
    "PR165_D2_ScenarioGroupRefreshRegistry.report.json": "pr165_d2_scenario_group_refresh_registry.schema.json",
    "PR165_D2_ConditionMemoryApplicationLedger.report.json": "pr165_d2_condition_memory_application_ledger.schema.json",
    "PR165_D2_ChampionChallengerSelectionLedger.report.json": "pr165_d2_champion_challenger_selection_ledger.schema.json",
    "PR165_D2_MarginalUtilityBatchBuilderLedger.report.json": "pr165_d2_marginal_utility_batch_builder_ledger.schema.json",
    "PR165_D2_CapacityCrowdingCorrelationSelectionLedger.report.json": "pr165_d2_capacity_crowding_correlation_selection_ledger.schema.json",
    "PR165_D2_FalseDiscoveryOverfitSelectionControl.report.json": "pr165_d2_false_discovery_overfit_selection_control.schema.json",
    "PR165_D2_TCADecompositionSelectionLedger.report.json": "pr165_d2_tca_decomposition_selection_ledger.schema.json",
    "PR165_D2_RetestBudgetAllocationPolicy.report.json": "pr165_d2_retest_budget_allocation_policy.schema.json",
    "PR165_D2_RouteTriageMatrix.report.json": "pr165_d2_route_triage_matrix.schema.json",
    "PR165_D2_ConnectorVenueReadinessReferenceRouting.report.json": "pr165_d2_connector_venue_readiness_reference_routing.schema.json",
    "PR165_D2_MasterPlanSectionCrosswalk.report.json": "pr165_d2_master_plan_section_crosswalk.schema.json",
    "PR165_D2_MarketSpecificSelectionIndex.report.json": "pr165_d2_market_specific_selection_index.schema.json",
    "PR165_D2_CommandActionMatrix.report.json": "pr165_d2_command_action_matrix.schema.json",
    "PR165_D2_SelectionExclusionReasonLedger.report.json": "pr165_d2_selection_exclusion_reason_ledger.schema.json",
    "PR165_D2_ExternalSelectionSignalCandidateRegistry.report.json": "pr165_d2_external_selection_signal_candidate_registry.schema.json",
    "PR165_D2_ExternalInstitutionalSignalCoverageAudit.report.json": "pr165_d2_external_institutional_signal_coverage_audit.schema.json",
    "PR165_D2_QKUFormulaAlgorithmComputabilityRouting.report.json": "pr165_d2_qku_formula_algorithm_computability_routing.schema.json",
    "PR165_D2_AgentRosterDiscoveryAudit.report.json": "pr165_d2_agent_roster_discovery_audit.schema.json",
    "PR165_D2_AgentDutySourceCrosswalk.report.json": "pr165_d2_agent_duty_source_crosswalk.schema.json",
    "PR165_D2_AgentSelectionHandoff.report.json": "pr165_d2_agent_selection_handoff.schema.json",
    "PR165_D2_AgentTaskQueue.report.json": "pr165_d2_agent_task_queue.schema.json",
    "PR165_D2_DashboardSelectionHandoff.report.json": "pr165_d2_dashboard_selection_handoff.schema.json",
    "PR165_D2_GovernanceSelectionHandoff.report.json": "pr165_d2_governance_selection_handoff.schema.json",
    "PR165_D2_CommanderSelectionHandoff.report.json": "pr165_d2_commander_selection_handoff.schema.json",
    "PR165_D2_PRFileConnectivityAudit.report.json": "pr165_d2_pr_file_connectivity_audit.schema.json",
    "PR165_D2_RowValueConnectivityAudit.report.json": "pr165_d2_row_value_connectivity_audit.schema.json",
    "PR165_D2_AuthorityBoundaryAudit.report.json": "pr165_d2_authority_boundary_audit.schema.json",
    "PR165_D2_OrphanArtifactAudit.report.json": "pr165_d2_orphan_artifact_audit.schema.json",
    "PR165_D2_StatusEnumDriftAudit.report.json": "pr165_d2_status_enum_drift_audit.schema.json",
    "PR165_D2_ReportManifest.report.json": "pr165_d2_report_manifest.schema.json",
    "PR165_D2_FinalSummary.report.json": "pr165_d2_final_summary.schema.json",
}

if set(REPORT_SCHEMA_REFS) != set(REPORT_FILENAMES):  # pragma: no cover - import-time guard
    missing = sorted(set(REPORT_FILENAMES) - set(REPORT_SCHEMA_REFS))
    extra = sorted(set(REPORT_SCHEMA_REFS) - set(REPORT_FILENAMES))
    raise RuntimeError(f"PR165-D2 report/schema mapping drift missing={missing} extra={extra}")
