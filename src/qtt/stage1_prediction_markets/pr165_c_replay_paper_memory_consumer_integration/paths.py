"""Paths, report names, schema names, and branch guard for PR165-C."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess

from .central_vocab import EXPECTED_BRANCH

GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
SHARD_DIR = GENERATED_DIR / "pr165_c_shards"
TEST_DIR = Path("tests/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration")
PACKAGE_IMPORT = "src.qtt.stage1_prediction_markets.pr165_c_replay_paper_memory_consumer_integration"

SCHEMA_FILENAMES = (
    "pr165_c_report_manifest.schema.json",
    "pr165_c_input_consumption_audit.schema.json",
    "pr165_c_optional_context_missing_receipt.schema.json",
    "pr165_c_main_freshness_triage_receipt.schema.json",
    "pr165_c_github_pr_discovery_unavailable_receipt.schema.json",
    "pr165_c_upstream_agent_pr_discovery.schema.json",
    "pr165_c_older_agent_artifact_consumption_audit.schema.json",
    "pr165_c_agent_pr_connectivity_record.schema.json",
    "pr165_c_canonical_core_table_manifest.schema.json",
    "pr165_c_agent_duty_record.schema.json",
    "pr165_c_agent_field_ownership_record.schema.json",
    "pr165_c_agent_task_queue_record.schema.json",
    "pr165_c_agent_task_receipt_requirement_record.schema.json",
    "pr165_c_agent_overlap_conflict_record.schema.json",
    "pr165_c_model_quality_challenge_record.schema.json",
    "pr165_c_memory_consumer_record.schema.json",
    "pr165_c_computable_artifact_payload.schema.json",
    "pr165_c_computable_qku_formula_action_record.schema.json",
    "pr165_c_formula_test_vector_record.schema.json",
    "pr165_c_condition_regime_feature_record.schema.json",
    "pr165_c_replay_paper_consumer_action_record.schema.json",
    "pr165_c_scenario_memory_route_record.schema.json",
    "pr165_c_retest_result_ingestion_record.schema.json",
    "pr165_c_pending_retest_queue_record.schema.json",
    "pr165_c_retest_priority_record.schema.json",
    "pr165_c_score_memory_refresh_trigger_record.schema.json",
    "pr165_c_closed_loop_score_memory_retest_dag.schema.json",
    "pr165_c_bounded_missing_value_materialization_record.schema.json",
    "pr165_c_qku_missing_value_fill_plan.schema.json",
    "pr165_c_repair_to_retest_handoff_record.schema.json",
    "pr165_c_quantum_consumer_route_record.schema.json",
    "pr165_c_dashboard_handoff_record.schema.json",
    "pr165_c_governance_handoff_record.schema.json",
    "pr165_c_commander_handoff_record.schema.json",
    "pr165_c_lineage_graph_record.schema.json",
    "pr165_c_crosswalk_route_triage_command_matrix_consumption_audit.schema.json",
    "pr165_c_pr_file_connectivity_record.schema.json",
    "pr165_c_authority_boundary_audit.schema.json",
    "pr165_c_orphan_audit.schema.json",
    "pr165_c_final_summary.schema.json",
)

REPORT_FILENAMES = (
    "PR165_C_InputConsumptionAudit.report.json",
    "PR165_C_OptionalContextMissingReceipt.report.json",
    "PR165_C_ExternalDesignScoutCandidateLedger.report.json",
    "PR165_C_WebScoutCandidateValueLedger.report.json",
    "PR165_C_MainFreshnessTriageReceipt.report.json",
    "PR165_C_UpstreamAgentPRDiscovery.report.json",
    "PR165_C_OlderAgentArtifactConsumptionAudit.report.json",
    "PR165_C_AgentPRConnectivityReconciliation.report.json",
    "PR165_C_CanonicalCoreTableManifest.report.json",
    "PR165_C_AgentDutyDistinctnessMatrix.report.json",
    "PR165_C_AgentFieldOwnershipMatrix.report.json",
    "PR165_C_AgentTaskQueue.report.json",
    "PR165_C_AgentTaskReceiptRequirementMatrix.report.json",
    "PR165_C_AgentOverlapConflictAudit.report.json",
    "PR165_C_ModelQualityChallengeLedger.report.json",
    "PR165_C_MemoryConsumerRouter.report.json",
    "PR165_C_ComputableArtifactPayloadRegistry.report.json",
    "PR165_C_ComputableQKUFormulaActionRegistry.report.json",
    "PR165_C_FormulaTestVectorRegistry.report.json",
    "PR165_C_BoundedMissingValueMaterializationLedger.report.json",
    "PR165_C_QKUMissingValueFillPlan.report.json",
    "PR165_C_ConditionRegimeFeatureMatrix.report.json",
    "PR165_C_ReplayPaperConsumerActionRegistry.report.json",
    "PR165_C_ScenarioMemoryRouter.report.json",
    "PR165_C_RetestResultIngestionRegistry.report.json",
    "PR165_C_PendingRetestQueue.report.json",
    "PR165_C_RetestPriorityRanking.report.json",
    "PR165_C_ScoreMemoryRefreshTriggerRegistry.report.json",
    "PR165_C_ClosedLoopScoreMemoryRetestDAG.report.json",
    "PR165_C_ComputabilityAndMaterializationCoverageAudit.report.json",
    "PR165_C_RepairToRetestHandoff.report.json",
    "PR165_C_QuantumConsumerRouter.report.json",
    "PR165_C_DashboardConsumerHandoff.report.json",
    "PR165_C_GovernanceConsumerHandoff.report.json",
    "PR165_C_CommanderConsumerHandoff.report.json",
    "PR165_C_LineageGraph.report.json",
    "PR165_C_CrosswalkRouteTriageCommandMatrixConsumptionAudit.report.json",
    "PR165_C_PRFileConnectivityAudit.report.json",
    "PR165_C_AuthorityBoundaryAudit.report.json",
    "PR165_C_OrphanArtifactAudit.report.json",
    "PR165_C_ReportManifest.report.json",
    "PR165_C_FinalSummary.report.json",
)

SUMMARY_REPORTS = frozenset(
    {
        "PR165_C_InputConsumptionAudit.report.json",
        "PR165_C_OptionalContextMissingReceipt.report.json",
        "PR165_C_ExternalDesignScoutCandidateLedger.report.json",
        "PR165_C_WebScoutCandidateValueLedger.report.json",
        "PR165_C_MainFreshnessTriageReceipt.report.json",
        "PR165_C_UpstreamAgentPRDiscovery.report.json",
        "PR165_C_OlderAgentArtifactConsumptionAudit.report.json",
        "PR165_C_AgentPRConnectivityReconciliation.report.json",
        "PR165_C_CanonicalCoreTableManifest.report.json",
        "PR165_C_ClosedLoopScoreMemoryRetestDAG.report.json",
        "PR165_C_ComputabilityAndMaterializationCoverageAudit.report.json",
        "PR165_C_CrosswalkRouteTriageCommandMatrixConsumptionAudit.report.json",
        "PR165_C_AuthorityBoundaryAudit.report.json",
        "PR165_C_OrphanArtifactAudit.report.json",
        "PR165_C_ReportManifest.report.json",
        "PR165_C_FinalSummary.report.json",
    }
)
ROW_LEVEL_REPORTS = frozenset(filename for filename in REPORT_FILENAMES if filename not in SUMMARY_REPORTS)

REQUIRED_INPUTS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/generated/PR165_ReportManifest.report.json",
    "docs/master_plan/generated/PR165_FinalSummary.report.json",
    "docs/master_plan/generated/PR165_CandidateScoreComponentRegistry.report.json",
    "docs/master_plan/generated/PR165_GlobalCandidateRanking.report.json",
    "docs/master_plan/generated/PR165_RegimeSlicedRanking.report.json",
    "docs/master_plan/generated/PR165_RankArbitrationPolicy.report.json",
    "docs/master_plan/generated/PR165_ScoreEnvelopeAndRankStabilityRegistry.report.json",
    "docs/master_plan/generated/PR165_ExpectedValueScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_TCAAdjustedScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_LatencyLaneAssignmentRegistry.report.json",
    "docs/master_plan/generated/PR165_QuantumFormulationMaterializationRegistry.report.json",
    "docs/master_plan/generated/PR165_LineageGraph.report.json",
    "docs/master_plan/generated/PR165_AgentScoringOrchestrationRouter.report.json",
    "docs/master_plan/generated/PR165_QKUAgentConsumerCoverageMatrix.report.json",
    "docs/master_plan/generated/PR165_DashboardScoreHandoff.report.json",
    "docs/master_plan/generated/PR165_B_ReportManifest.report.json",
    "docs/master_plan/generated/PR165_B_FinalSummary.report.json",
    "docs/master_plan/generated/PR165_B_ConditionFingerprintRegistry.report.json",
    "docs/master_plan/generated/PR165_B_CombinationFingerprintRegistry.report.json",
    "docs/master_plan/generated/PR165_B_ScenarioOutcomeMatrix.report.json",
    "docs/master_plan/generated/PR165_B_CombinationOutcomeMemoryLedger.report.json",
    "docs/master_plan/generated/PR165_B_NegativeCombinationAvoidanceRegistry.report.json",
    "docs/master_plan/generated/PR165_B_PositiveConditionScopedPreferenceRegistry.report.json",
    "docs/master_plan/generated/PR165_B_FragileCombinationWatchlist.report.json",
    "docs/master_plan/generated/PR165_B_OutcomeAttributionLedger.report.json",
    "docs/master_plan/generated/PR165_B_CooldownPolicyRegistry.report.json",
    "docs/master_plan/generated/PR165_B_RetestEligibilityRegistry.report.json",
    "docs/master_plan/generated/PR165_B_ReplayPaperRetestQueue.report.json",
    "docs/master_plan/generated/PR165_B_RepairRouteHandoffRegistry.report.json",
    "docs/master_plan/generated/PR165_B_AgentMemoryRouter.report.json",
    "docs/master_plan/generated/PR165_B_LineageGraph.report.json",
    "docs/master_plan/generated/PR165_B_DashboardMemoryHandoff.report.json",
    "docs/master_plan/generated/PR165_B_GovernanceMemoryHandoff.report.json",
    "docs/master_plan/generated/PR165_B_OrphanArtifactAudit.report.json",
    "docs/master_plan/generated/pr165_shards",
    "docs/master_plan/generated/pr165_b_shards",
    "tools/run_validation_gates.py",
    "tools/ci_branch_context.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "tests/tools/test_ci_branch_context.py",
)

OPTIONAL_INPUT_GROUPS = {
    "pr165_model_quality": ("docs/master_plan/generated/PR165_ModelQualityPenaltyRegistry.report.json",),
    "pr165_repair_routes": (
        "docs/master_plan/generated/PR165_RepairRoutingHandoffRegistry.report.json",
        "docs/master_plan/generated/PR165_RepairRetestRouteRegistry.report.json",
    ),
    "pr165_b_counterfactual_and_authority": (
        "docs/master_plan/generated/PR165_B_CounterfactualAttributionLedger.report.json",
        "docs/master_plan/generated/PR165_B_AuthorityBoundaryAudit.report.json",
        "docs/master_plan/generated/PR165_B_AgentSelectionOverlayHandoff.report.json",
    ),
    "route_triage": (
        "docs/master_plan/generated/PR135RouteTriage.report.json",
        "docs/master_plan/generated/PR136RouteTriage.report.json",
    ),
    "full_master_plan_crosswalk": (
        "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json",
        "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json",
    ),
    "market_specific_section_index": (
        "docs/master_plan/generated/PR135MarketSpecificSectionIndex.report.json",
        "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    ),
    "command_action_matrix": (
        "docs/master_plan/generated/PR135CommandActionMatrix.report.json",
        "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
        "docs/master_plan/generated/LocalGateCommandMatrix.json",
    ),
    "qku_agent_ownership_matrix": (
        "docs/master_plan/generated/PR161D_QKUAgentGraphRoutingMatrix.report.json",
        "docs/master_plan/generated/PR161D_QKUAgentTaskQueue.report.json",
        "docs/master_plan/generated/PR161D_QTTAgentRoleNetworkRegistry.report.json",
        "docs/master_plan/generated/PR164_AgentOrchestrationRouter.report.json",
    ),
    "dashboard_handoff": (
        "docs/master_plan/generated/PR161B_OwnerDashboardReviewRouteMatrix.report.json",
        "docs/master_plan/generated/PR163_C_OperatorDashboardHandoff.report.json",
        "docs/master_plan/generated/PR165_DashboardScoreHandoff.report.json",
    ),
    "retest_result_artifacts": (
        "docs/master_plan/generated/PR161E_ReplayResultPacketValidation.report.json",
        "docs/master_plan/generated/PR161E_PaperResultPacketValidation.report.json",
        "docs/master_plan/generated/PR163_B_PairedReplayPaperResultCandidateRegistry.report.json",
    ),
}


def _schema_for_report(filename: str) -> str:
    explicit = {
        "PR165_C_ReportManifest.report.json": "pr165_c_report_manifest.schema.json",
        "PR165_C_FinalSummary.report.json": "pr165_c_final_summary.schema.json",
        "PR165_C_InputConsumptionAudit.report.json": "pr165_c_input_consumption_audit.schema.json",
        "PR165_C_OptionalContextMissingReceipt.report.json": "pr165_c_optional_context_missing_receipt.schema.json",
        "PR165_C_MainFreshnessTriageReceipt.report.json": "pr165_c_main_freshness_triage_receipt.schema.json",
        "PR165_C_UpstreamAgentPRDiscovery.report.json": "pr165_c_upstream_agent_pr_discovery.schema.json",
        "PR165_C_OlderAgentArtifactConsumptionAudit.report.json": "pr165_c_older_agent_artifact_consumption_audit.schema.json",
        "PR165_C_AgentPRConnectivityReconciliation.report.json": "pr165_c_agent_pr_connectivity_record.schema.json",
        "PR165_C_CanonicalCoreTableManifest.report.json": "pr165_c_canonical_core_table_manifest.schema.json",
        "PR165_C_AgentDutyDistinctnessMatrix.report.json": "pr165_c_agent_duty_record.schema.json",
        "PR165_C_AgentFieldOwnershipMatrix.report.json": "pr165_c_agent_field_ownership_record.schema.json",
        "PR165_C_AgentTaskQueue.report.json": "pr165_c_agent_task_queue_record.schema.json",
        "PR165_C_AgentTaskReceiptRequirementMatrix.report.json": "pr165_c_agent_task_receipt_requirement_record.schema.json",
        "PR165_C_AgentOverlapConflictAudit.report.json": "pr165_c_agent_overlap_conflict_record.schema.json",
        "PR165_C_ModelQualityChallengeLedger.report.json": "pr165_c_model_quality_challenge_record.schema.json",
        "PR165_C_MemoryConsumerRouter.report.json": "pr165_c_memory_consumer_record.schema.json",
        "PR165_C_ComputableArtifactPayloadRegistry.report.json": "pr165_c_computable_artifact_payload.schema.json",
        "PR165_C_ComputableQKUFormulaActionRegistry.report.json": "pr165_c_computable_qku_formula_action_record.schema.json",
        "PR165_C_FormulaTestVectorRegistry.report.json": "pr165_c_formula_test_vector_record.schema.json",
        "PR165_C_ConditionRegimeFeatureMatrix.report.json": "pr165_c_condition_regime_feature_record.schema.json",
        "PR165_C_ReplayPaperConsumerActionRegistry.report.json": "pr165_c_replay_paper_consumer_action_record.schema.json",
        "PR165_C_ScenarioMemoryRouter.report.json": "pr165_c_scenario_memory_route_record.schema.json",
        "PR165_C_RetestResultIngestionRegistry.report.json": "pr165_c_retest_result_ingestion_record.schema.json",
        "PR165_C_PendingRetestQueue.report.json": "pr165_c_pending_retest_queue_record.schema.json",
        "PR165_C_RetestPriorityRanking.report.json": "pr165_c_retest_priority_record.schema.json",
        "PR165_C_ScoreMemoryRefreshTriggerRegistry.report.json": "pr165_c_score_memory_refresh_trigger_record.schema.json",
        "PR165_C_ClosedLoopScoreMemoryRetestDAG.report.json": "pr165_c_closed_loop_score_memory_retest_dag.schema.json",
        "PR165_C_BoundedMissingValueMaterializationLedger.report.json": "pr165_c_bounded_missing_value_materialization_record.schema.json",
        "PR165_C_QKUMissingValueFillPlan.report.json": "pr165_c_qku_missing_value_fill_plan.schema.json",
        "PR165_C_RepairToRetestHandoff.report.json": "pr165_c_repair_to_retest_handoff_record.schema.json",
        "PR165_C_QuantumConsumerRouter.report.json": "pr165_c_quantum_consumer_route_record.schema.json",
        "PR165_C_DashboardConsumerHandoff.report.json": "pr165_c_dashboard_handoff_record.schema.json",
        "PR165_C_GovernanceConsumerHandoff.report.json": "pr165_c_governance_handoff_record.schema.json",
        "PR165_C_CommanderConsumerHandoff.report.json": "pr165_c_commander_handoff_record.schema.json",
        "PR165_C_LineageGraph.report.json": "pr165_c_lineage_graph_record.schema.json",
        "PR165_C_CrosswalkRouteTriageCommandMatrixConsumptionAudit.report.json": "pr165_c_crosswalk_route_triage_command_matrix_consumption_audit.schema.json",
        "PR165_C_PRFileConnectivityAudit.report.json": "pr165_c_pr_file_connectivity_record.schema.json",
        "PR165_C_AuthorityBoundaryAudit.report.json": "pr165_c_authority_boundary_audit.schema.json",
        "PR165_C_OrphanArtifactAudit.report.json": "pr165_c_orphan_audit.schema.json",
    }
    return explicit.get(filename, "pr165_c_report_manifest.schema.json")


REPORT_SCHEMA_REFS = {filename: _schema_for_report(filename) for filename in REPORT_FILENAMES}


def current_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def ensure_branch(repo_root: Path) -> None:
    branch = current_branch(repo_root)
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"PR165-C must build on {EXPECTED_BRANCH}, got {branch}")


def resolve_repo_relative(repo_root: Path, rel_path: str | Path) -> Path:
    if isinstance(rel_path, PureWindowsPath):
        rel_path = rel_path.as_posix()
    if isinstance(rel_path, PurePosixPath):
        rel_path = rel_path.as_posix()
    return repo_root / Path(str(rel_path).replace("/", "\\"))


def schema_path(repo_root: Path, filename: str) -> Path:
    return repo_root / SCHEMA_DIR / filename
