"""Paths, report names, schema names, and branch guard for PR165."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
from typing import Any

from .scoring_authority_policy import EXPECTED_BRANCH


GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path("src/qtt/stage1_prediction_markets/pr165_evidence_backed_scoring_ranking")
SCHEMA_DIR = PACKAGE_DIR / "schemas"
SHARD_DIR = GENERATED_DIR / "pr165_shards"
TEST_DIR = Path("tests/stage1_prediction_markets/pr165_evidence_backed_scoring_ranking")
PACKAGE_IMPORT = "src.qtt.stage1_prediction_markets.pr165_evidence_backed_scoring_ranking"

SCHEMA_FILENAMES = (
    "pr165_report_manifest.schema.json",
    "pr165_input_consumption_audit.schema.json",
    "pr165_row_conservation_audit.schema.json",
    "pr165_computability_coverage_audit.schema.json",
    "pr165_remaining_computability_materialization_plan.schema.json",
    "pr165_score_model_config.schema.json",
    "pr165_score_formula_record.schema.json",
    "pr165_score_formula_coverage_record.schema.json",
    "pr165_score_test_vector_record.schema.json",
    "pr165_score_test_vector_coverage_record.schema.json",
    "pr165_score_component_record.schema.json",
    "pr165_candidate_global_rank_record.schema.json",
    "pr165_regime_slice_rank_record.schema.json",
    "pr165_rank_arbitration_record.schema.json",
    "pr165_score_envelope_rank_stability_record.schema.json",
    "pr165_score_explainability_record.schema.json",
    "pr165_candidate_value_materialization_record.schema.json",
    "pr165_missing_value_rescue_record.schema.json",
    "pr165_probability_calibration_score_record.schema.json",
    "pr165_expected_value_score_record.schema.json",
    "pr165_tca_adjusted_score_record.schema.json",
    "pr165_implementation_shortfall_score_record.schema.json",
    "pr165_latency_adjusted_score_record.schema.json",
    "pr165_latency_lane_assignment_record.schema.json",
    "pr165_liquidity_fill_score_record.schema.json",
    "pr165_maker_taker_route_score_record.schema.json",
    "pr165_automated_trading_control_score_record.schema.json",
    "pr165_model_risk_penalty_record.schema.json",
    "pr165_quantum_priority_score_record.schema.json",
    "pr165_quantum_formulation_materialization_record.schema.json",
    "pr165_portfolio_cluster_record.schema.json",
    "pr165_lineage_graph_record.schema.json",
    "pr165_agent_scoring_orchestration_record.schema.json",
    "pr165_qku_agent_consumer_coverage_record.schema.json",
    "pr165_repair_routing_record.schema.json",
    "pr165_candidate_version_repair_plan_record.schema.json",
    "pr165_repair_retest_route_record.schema.json",
    "pr165_negative_memory_candidate_handoff_record.schema.json",
    "pr165_pr162d_r3_priority_handoff_record.schema.json",
    "pr165_plugin_priority_handoff_record.schema.json",
    "pr165_dashboard_score_handoff_record.schema.json",
    "pr165_external_scouting_record.schema.json",
    "pr165_authority_audit.schema.json",
    "pr165_orphan_artifact_audit.schema.json",
    "pr165_final_summary.schema.json",
)

REPORT_FILENAMES = (
    "PR165_InputConsumptionAudit.report.json",
    "PR165_OptionalContextMissingReceipt.report.json",
    "PR165_RowConservationAudit.report.json",
    "PR165_ComputabilityCoverageAudit.report.json",
    "PR165_Remaining2858ComputabilityMaterializationPlan.report.json",
    "PR165_CandidateValueMaterializationRegistry.report.json",
    "PR165_MissingValueRescueLedger.report.json",
    "PR165_ScoreModelConfiguration.report.json",
    "PR165_ScoreFormulaRegistry.report.json",
    "PR165_ScoreFormulaCoverageMap.report.json",
    "PR165_ScoreTestVectorRegistry.report.json",
    "PR165_ScoreTestVectorCoverageMap.report.json",
    "PR165_CandidateScoreComponentRegistry.report.json",
    "PR165_GlobalCandidateRanking.report.json",
    "PR165_RegimeSlicedRanking.report.json",
    "PR165_RankArbitrationPolicy.report.json",
    "PR165_ScoreEnvelopeAndRankStabilityRegistry.report.json",
    "PR165_ProbabilityCalibrationScoreRegistry.report.json",
    "PR165_ExpectedValueScoreRegistry.report.json",
    "PR165_ReplayScoreRegistry.report.json",
    "PR165_PaperScoreRegistry.report.json",
    "PR165_ReplayPaperAlignmentScoreRegistry.report.json",
    "PR165_DivergencePenaltyRegistry.report.json",
    "PR165_TCAAdjustedScoreRegistry.report.json",
    "PR165_ImplementationShortfallScoreRegistry.report.json",
    "PR165_ScenarioStressRobustnessScoreRegistry.report.json",
    "PR165_WalkForwardHoldoutScoreRegistry.report.json",
    "PR165_LatencyAdjustedScoreRegistry.report.json",
    "PR165_LatencyLaneAssignmentRegistry.report.json",
    "PR165_LiquidityFillProbabilityScoreRegistry.report.json",
    "PR165_MakerTakerRouteScoreRegistry.report.json",
    "PR165_AdverseSelectionPenaltyRegistry.report.json",
    "PR165_RiskAdjustedScoreRegistry.report.json",
    "PR165_AutomatedTradingControlCoverageScoreRegistry.report.json",
    "PR165_ModelRiskPenaltyRegistry.report.json",
    "PR165_ProvenanceQualityScoreRegistry.report.json",
    "PR165_RepairConfidenceScoreRegistry.report.json",
    "PR165_DataQualityScoreRegistry.report.json",
    "PR165_QuantumPriorityScoreRegistry.report.json",
    "PR165_QuantumFormulationMaterializationRegistry.report.json",
    "PR165_PortfolioClusterPreparation.report.json",
    "PR165_LineageGraph.report.json",
    "PR165_ScoreExplainabilityLedger.report.json",
    "PR165_AgentScoringOrchestrationRouter.report.json",
    "PR165_QKUAgentConsumerCoverageMatrix.report.json",
    "PR165_PostLaunchRepairRoutingSemantics.report.json",
    "PR165_RepairRoutingHandoffRegistry.report.json",
    "PR165_CandidateVersionRepairPlan.report.json",
    "PR165_RepairRetestRouteRegistry.report.json",
    "PR165_PR165BNegativeMemoryCandidateHandoff.report.json",
    "PR165_PR162D_R3PriorityHandoff.report.json",
    "PR165_PluginPriorityHandoff.report.json",
    "PR165_DashboardScoreHandoff.report.json",
    "PR165_ExternalCandidateScoutingLedger.report.json",
    "PR165_ExternalFormulaAndParameterCandidateRegistry.report.json",
    "PR165_ExternalMicrostructureSignalCandidateRegistry.report.json",
    "PR165_ExternalQuantumMappingTemplateCandidateRegistry.report.json",
    "PR165_ExternalScoutingMappabilityDecisionLedger.report.json",
    "PR165_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
    "PR165_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR165_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR165_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
    "PR165_OrphanArtifactAudit.report.json",
    "PR165_ReportManifest.report.json",
    "PR165_FinalSummary.report.json",
)

SUMMARY_REPORTS = {
    "PR165_InputConsumptionAudit.report.json",
    "PR165_OptionalContextMissingReceipt.report.json",
    "PR165_RowConservationAudit.report.json",
    "PR165_ComputabilityCoverageAudit.report.json",
    "PR165_ScoreModelConfiguration.report.json",
    "PR165_ScoreFormulaRegistry.report.json",
    "PR165_ScoreTestVectorRegistry.report.json",
    "PR165_RankArbitrationPolicy.report.json",
    "PR165_PostLaunchRepairRoutingSemantics.report.json",
    "PR165_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
    "PR165_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR165_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR165_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
    "PR165_OrphanArtifactAudit.report.json",
    "PR165_ReportManifest.report.json",
    "PR165_FinalSummary.report.json",
}
ROW_LEVEL_REPORTS = frozenset(filename for filename in REPORT_FILENAMES if filename not in SUMMARY_REPORTS)

UPSTREAM_PR_REFS = (
    "PR162R-A",
    "PR162D-R2A",
    "PR162R",
    "PR162R-B",
    "PR163",
    "PR163-B",
    "PR164",
    "PR163-C",
    "PR203",
    "PR204",
)

DOWNSTREAM_PR_ROUTES = (
    "PR165-B",
    "PR162D-R3",
    "PR162E",
    "PR162E-Q",
    "PR166-L",
    "dashboard_future_consumer",
    "governance_agent",
    "commander_agent",
)

REQUIRED_INPUTS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/generated/PR164_ReportManifest.report.json",
    "docs/master_plan/generated/PR164_FinalSummary.report.json",
    "docs/master_plan/generated/PR164_DecisionAndNextPRRecommendation.report.json",
    "docs/master_plan/generated/PR164_PR165ScoringReadinessMatrix.report.json",
    "docs/master_plan/generated/PR164_QKUComputabilityMaterializationRegistry.report.json",
    "docs/master_plan/generated/PR164_ModelRiskInventoryForQKU.report.json",
    "docs/master_plan/generated/PR164_LatencyHotPathClassifier.report.json",
    "docs/master_plan/generated/PR164_QuantumCompatibilityRouter.report.json",
    "docs/master_plan/generated/PR164_QuantumClassicalComparatorPreparation.report.json",
    "docs/master_plan/generated/PR164_AgentOrchestrationRouter.report.json",
    "docs/master_plan/generated/PR164_PR165BNegativeMemoryPreparation.report.json",
    "docs/master_plan/generated/pr164_shards",
    "docs/master_plan/generated/PR163_C_ReportManifest.report.json",
    "docs/master_plan/generated/PR163_C_FinalSummary.report.json",
    "docs/master_plan/generated/PR163_C_PR165ReadinessDelta.report.json",
    "docs/master_plan/generated/PR163_C_RepairDeltaRegistry.report.json",
    "docs/master_plan/generated/PR163_C_TCAComponentRepairRegistry.report.json",
    "docs/master_plan/generated/PR163_C_ImplementationShortfallModelRegistry.report.json",
    "docs/master_plan/generated/PR163_C_LatencyModelRepairRegistry.report.json",
    "docs/master_plan/generated/PR163_C_LatencyErrorBudgetLedger.report.json",
    "docs/master_plan/generated/PR163_C_LiquiditySpreadDepthRepairRegistry.report.json",
    "docs/master_plan/generated/PR163_C_MakerTakerQueueModelRegistry.report.json",
    "docs/master_plan/generated/PR163_C_AdverseSelectionModelRegistry.report.json",
    "docs/master_plan/generated/PR163_C_ModelRiskRepairLedger.report.json",
    "docs/master_plan/generated/PR163_C_PointInTimeRepairLedger.report.json",
    "docs/master_plan/generated/PR163_C_CounterfactualRepairEvaluation.report.json",
    "docs/master_plan/generated/PR163_C_QuantumRepairPrioritizationLedger.report.json",
    "docs/master_plan/generated/PR163_C_PR165BNegativeMemoryHandoff.report.json",
    "docs/master_plan/generated/PR163_C_PR162D_R3RouteSeparator.report.json",
    "docs/master_plan/generated/PR163_C_AgentRepairOrchestrationRouter.report.json",
    "docs/master_plan/generated/pr163_c_shards",
    "docs/master_plan/generated/PR163_B_ReportManifest.report.json",
    "docs/master_plan/generated/pr163_b_shards",
    "tools/run_validation_gates.py",
    "tools/ci_branch_context.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "tests/tools/test_ci_branch_context.py",
)

OPTIONAL_INPUT_GROUPS = {
    "route_triage": (
        "docs/master_plan/generated/PR135RouteTriage.report.json",
        "docs/master_plan/generated/PR136RouteTriage.report.json",
    ),
    "master_plan_section_crosswalk": (
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
        "docs/master_plan/generated/PR161C_QKUAgentConsumptionBridge.report.json",
        "docs/master_plan/generated/PR161D_QKUAgentGraphRoutingMatrix.report.json",
        "docs/master_plan/generated/PR162D_AgentConsumableQKURoutingMatrix.report.json",
    ),
    "pr_dependency_graph": (
        "docs/master_plan/generated/PR136LaunchReadinessDependencyGraph.report.json",
        "docs/master_plan/generated/PR137DependencyGateStateMatrix.report.json",
    ),
    "dashboard_handoff": (
        "docs/master_plan/generated/OwnerDashboardApprovalStaticScreenContract.report.json",
        "docs/master_plan/generated/PR163_C_OperatorDashboardHandoff.report.json",
        "docs/master_plan/generated/PR161B_OwnerDashboardReviewRouteMatrix.report.json",
    ),
}


def _schema_for_report(filename: str) -> str:
    key = filename.removeprefix("PR165_").removesuffix(".report.json").lower()
    explicit = {
        "reportmanifest": "pr165_report_manifest.schema.json",
        "finalsummary": "pr165_final_summary.schema.json",
        "inputconsumptionaudit": "pr165_input_consumption_audit.schema.json",
        "rowconservationaudit": "pr165_row_conservation_audit.schema.json",
        "computabilitycoverageaudit": "pr165_computability_coverage_audit.schema.json",
        "remaining2858computabilitymaterializationplan": "pr165_remaining_computability_materialization_plan.schema.json",
        "scoremodelconfiguration": "pr165_score_model_config.schema.json",
        "scoreformularegistry": "pr165_score_formula_record.schema.json",
        "scoreformulacoveragemap": "pr165_score_formula_coverage_record.schema.json",
        "scoretestvectorregistry": "pr165_score_test_vector_record.schema.json",
        "scoretestvectorcoveragemap": "pr165_score_test_vector_coverage_record.schema.json",
        "candidatescorecomponentregistry": "pr165_score_component_record.schema.json",
        "globalcandidateranking": "pr165_candidate_global_rank_record.schema.json",
        "regimeslicedranking": "pr165_regime_slice_rank_record.schema.json",
        "rankarbitrationpolicy": "pr165_rank_arbitration_record.schema.json",
        "scoreenvelopeandrankstabilityregistry": "pr165_score_envelope_rank_stability_record.schema.json",
        "scoreexplainabilityledger": "pr165_score_explainability_record.schema.json",
        "candidatevaluematerializationregistry": "pr165_candidate_value_materialization_record.schema.json",
        "missingvaluerescueledger": "pr165_missing_value_rescue_record.schema.json",
        "probabilitycalibrationscoreregistry": "pr165_probability_calibration_score_record.schema.json",
        "expectedvaluescoreregistry": "pr165_expected_value_score_record.schema.json",
        "tcaadjustedscoreregistry": "pr165_tca_adjusted_score_record.schema.json",
        "implementationshortfallscoreregistry": "pr165_implementation_shortfall_score_record.schema.json",
        "latencyadjustedscoreregistry": "pr165_latency_adjusted_score_record.schema.json",
        "latencylaneassignmentregistry": "pr165_latency_lane_assignment_record.schema.json",
        "liquidityfillprobabilityscoreregistry": "pr165_liquidity_fill_score_record.schema.json",
        "makertakerroutescoreregistry": "pr165_maker_taker_route_score_record.schema.json",
        "automatedtradingcontrolcoveragescoreregistry": "pr165_automated_trading_control_score_record.schema.json",
        "modelriskpenaltyregistry": "pr165_model_risk_penalty_record.schema.json",
        "quantumpriorityscoreregistry": "pr165_quantum_priority_score_record.schema.json",
        "quantumformulationmaterializationregistry": "pr165_quantum_formulation_materialization_record.schema.json",
        "portfolioclusterpreparation": "pr165_portfolio_cluster_record.schema.json",
        "lineagegraph": "pr165_lineage_graph_record.schema.json",
        "agentscoringorchestrationrouter": "pr165_agent_scoring_orchestration_record.schema.json",
        "qkuagentconsumercoveragematrix": "pr165_qku_agent_consumer_coverage_record.schema.json",
        "repairroutinghandoffregistry": "pr165_repair_routing_record.schema.json",
        "candidateversionrepairplan": "pr165_candidate_version_repair_plan_record.schema.json",
        "repairretestrouteregistry": "pr165_repair_retest_route_record.schema.json",
        "pr165bnegativememorycandidatehandoff": "pr165_negative_memory_candidate_handoff_record.schema.json",
        "pr162d_r3priorityhandoff": "pr165_pr162d_r3_priority_handoff_record.schema.json",
        "pluginpriorityhandoff": "pr165_plugin_priority_handoff_record.schema.json",
        "dashboardscorehandoff": "pr165_dashboard_score_handoff_record.schema.json",
        "externandidatescoutingledger": "pr165_external_scouting_record.schema.json",
    }
    if key.startswith("external"):
        return "pr165_external_scouting_record.schema.json"
    if "authorityaudit" in key or key.startswith("no"):
        return "pr165_authority_audit.schema.json"
    if "orphan" in key:
        return "pr165_orphan_artifact_audit.schema.json"
    if "repairrouting" in key or "postlaunchrepair" in key:
        return "pr165_repair_routing_record.schema.json"
    return explicit.get(key, "pr165_score_component_record.schema.json")


REPORT_SCHEMA_REFS = {
    filename: f"{SCHEMA_DIR.as_posix()}/{_schema_for_report(filename)}" for filename in REPORT_FILENAMES
}


def current_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip()


def ensure_branch(repo_root: Path) -> None:
    branch = current_branch(repo_root)
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"PR165 must build on {EXPECTED_BRANCH}; current branch is {branch!r}")


def resolve_repo_relative(repo_root: Path, path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    text = str(path_value).replace("\\", "/")
    if PureWindowsPath(str(path_value)).is_absolute() or PurePosixPath(text).is_absolute():
        return Path(path_value)
    return repo_root / text


def schema_path(repo_root: Path, filename: str) -> Path:
    return repo_root / SCHEMA_DIR / filename
