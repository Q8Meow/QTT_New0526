"""Paths, report names, schema names, and branch guard for PR165-B."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess

from .negative_memory_authority_policy import EXPECTED_BRANCH


GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/pr165_b_condition_scoped_negative_memory"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
SHARD_DIR = GENERATED_DIR / "pr165_b_shards"
TEST_DIR = Path(
    "tests/stage1_prediction_markets/pr165_b_condition_scoped_negative_memory"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets.pr165_b_condition_scoped_negative_memory"
)

SCHEMA_FILENAMES = (
    "pr165_b_report_manifest.schema.json",
    "pr165_b_input_consumption_audit.schema.json",
    "pr165_b_asof_leakage_audit.schema.json",
    "pr165_b_evidence_sufficiency_record.schema.json",
    "pr165_b_false_discovery_control_record.schema.json",
    "pr165_b_condition_fingerprint.schema.json",
    "pr165_b_combination_fingerprint.schema.json",
    "pr165_b_scenario_outcome_record.schema.json",
    "pr165_b_negative_memory_record.schema.json",
    "pr165_b_positive_memory_record.schema.json",
    "pr165_b_fragile_memory_record.schema.json",
    "pr165_b_outcome_attribution_record.schema.json",
    "pr165_b_counterfactual_attribution_record.schema.json",
    "pr165_b_cooldown_policy_record.schema.json",
    "pr165_b_retest_policy_record.schema.json",
    "pr165_b_memory_decay_policy_record.schema.json",
    "pr165_b_similarity_match_policy_record.schema.json",
    "pr165_b_allowed_when_policy_record.schema.json",
    "pr165_b_repair_route_record.schema.json",
    "pr165_b_retest_queue_record.schema.json",
    "pr165_b_candidate_version_memory_record.schema.json",
    "pr165_b_quantum_negative_memory_record.schema.json",
    "pr165_b_agent_selection_overlay_record.schema.json",
    "pr165_b_agent_memory_route_record.schema.json",
    "pr165_b_lineage_graph_record.schema.json",
    "pr165_b_dashboard_handoff_record.schema.json",
    "pr165_b_governance_handoff_record.schema.json",
    "pr165_b_authority_audit.schema.json",
    "pr165_b_orphan_audit.schema.json",
    "pr165_b_final_summary.schema.json",
)

REPORT_FILENAMES = (
    "PR165_B_InputConsumptionAudit.report.json",
    "PR165_B_OptionalContextMissingReceipt.report.json",
    "PR165_B_AsOfLeakageAudit.report.json",
    "PR165_B_EvidenceSufficiencyRegistry.report.json",
    "PR165_B_FalseDiscoveryControlRegistry.report.json",
    "PR165_B_ConditionFingerprintRegistry.report.json",
    "PR165_B_CombinationFingerprintRegistry.report.json",
    "PR165_B_ScenarioOutcomeMatrix.report.json",
    "PR165_B_CombinationOutcomeMemoryLedger.report.json",
    "PR165_B_NegativeCombinationAvoidanceRegistry.report.json",
    "PR165_B_PositiveConditionScopedPreferenceRegistry.report.json",
    "PR165_B_FragileCombinationWatchlist.report.json",
    "PR165_B_OutcomeAttributionLedger.report.json",
    "PR165_B_CounterfactualAttributionLedger.report.json",
    "PR165_B_CooldownPolicyRegistry.report.json",
    "PR165_B_RetestEligibilityRegistry.report.json",
    "PR165_B_MemoryDecayAndOverridePolicy.report.json",
    "PR165_B_SimilarityMatchPolicyRegistry.report.json",
    "PR165_B_AllowedWhenConditionRegistry.report.json",
    "PR165_B_RepairRouteHandoffRegistry.report.json",
    "PR165_B_ReplayPaperRetestQueue.report.json",
    "PR165_B_CandidateVersionMemoryRegistry.report.json",
    "PR165_B_QuantumNegativeMemoryRegistry.report.json",
    "PR165_B_AgentSelectionOverlayHandoff.report.json",
    "PR165_B_AgentMemoryRouter.report.json",
    "PR165_B_LineageGraph.report.json",
    "PR165_B_DashboardMemoryHandoff.report.json",
    "PR165_B_GovernanceMemoryHandoff.report.json",
    "PR165_B_ExternalConditionMemoryScoutingLedger.report.json",
    "PR165_B_ExternalFailureAttributionCandidateRegistry.report.json",
    "PR165_B_ExternalMicrostructureConditionRegistry.report.json",
    "PR165_B_ExternalQuantumFailureAttributionRegistry.report.json",
    "PR165_B_ExternalScoutingMappabilityDecisionLedger.report.json",
    "PR165_B_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
    "PR165_B_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR165_B_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR165_B_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
    "PR165_B_OrphanArtifactAudit.report.json",
    "PR165_B_ReportManifest.report.json",
    "PR165_B_FinalSummary.report.json",
)

SUMMARY_REPORTS = frozenset(
    {
        "PR165_B_InputConsumptionAudit.report.json",
        "PR165_B_OptionalContextMissingReceipt.report.json",
        "PR165_B_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
        "PR165_B_NoQTTChecksumFreezeAuthorityAudit.report.json",
        "PR165_B_NoQuantumBackendAdvantageClaimAudit.report.json",
        "PR165_B_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
        "PR165_B_OrphanArtifactAudit.report.json",
        "PR165_B_ReportManifest.report.json",
        "PR165_B_FinalSummary.report.json",
    }
)
ROW_LEVEL_REPORTS = frozenset(
    filename for filename in REPORT_FILENAMES if filename not in SUMMARY_REPORTS
)

UPSTREAM_PR_REFS = (
    "PR162R-A",
    "PR162D-R2A",
    "PR162R",
    "PR162R-B",
    "PR163",
    "PR163-B",
    "PR164",
    "PR163-C",
    "PR165",
    "PR203",
    "PR204",
)

DOWNSTREAM_PR_ROUTES = (
    "PR162D-R3",
    "PR162E",
    "PR162F",
    "PR165-C",
    "PR166-Q",
    "PR167",
    "runtime/cache/dashboard",
    "governance_agent",
    "commander_agent",
)

REQUIRED_INPUTS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/generated/PR165_ReportManifest.report.json",
    "docs/master_plan/generated/PR165_FinalSummary.report.json",
    "docs/master_plan/generated/PR165_InputConsumptionAudit.report.json",
    "docs/master_plan/generated/PR165_RowConservationAudit.report.json",
    "docs/master_plan/generated/PR165_ComputabilityCoverageAudit.report.json",
    "docs/master_plan/generated/PR165_CandidateScoreComponentRegistry.report.json",
    "docs/master_plan/generated/PR165_GlobalCandidateRanking.report.json",
    "docs/master_plan/generated/PR165_RegimeSlicedRanking.report.json",
    "docs/master_plan/generated/PR165_RankArbitrationPolicy.report.json",
    "docs/master_plan/generated/PR165_ScoreEnvelopeAndRankStabilityRegistry.report.json",
    "docs/master_plan/generated/PR165_ExpectedValueScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_ProbabilityCalibrationScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_ReplayScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_PaperScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_ReplayPaperAlignmentScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_DivergencePenaltyRegistry.report.json",
    "docs/master_plan/generated/PR165_TCAAdjustedScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_ImplementationShortfallScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_ScenarioStressRobustnessScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_LatencyAdjustedScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_LatencyLaneAssignmentRegistry.report.json",
    "docs/master_plan/generated/PR165_LiquidityFillProbabilityScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_MakerTakerRouteScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_AdverseSelectionPenaltyRegistry.report.json",
    "docs/master_plan/generated/PR165_RiskAdjustedScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_ModelRiskPenaltyRegistry.report.json",
    "docs/master_plan/generated/PR165_RepairConfidenceScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_DataQualityScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_ProvenanceQualityScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_QuantumPriorityScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_QuantumFormulationMaterializationRegistry.report.json",
    "docs/master_plan/generated/PR165_PortfolioClusterPreparation.report.json",
    "docs/master_plan/generated/PR165_LineageGraph.report.json",
    "docs/master_plan/generated/PR165_ScoreExplainabilityLedger.report.json",
    "docs/master_plan/generated/PR165_AgentScoringOrchestrationRouter.report.json",
    "docs/master_plan/generated/PR165_QKUAgentConsumerCoverageMatrix.report.json",
    "docs/master_plan/generated/PR165_PR165BNegativeMemoryCandidateHandoff.report.json",
    "docs/master_plan/generated/PR165_PR162D_R3PriorityHandoff.report.json",
    "docs/master_plan/generated/PR165_PluginPriorityHandoff.report.json",
    "docs/master_plan/generated/PR165_DashboardScoreHandoff.report.json",
    "docs/master_plan/generated/PR165_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
    "docs/master_plan/generated/PR165_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "docs/master_plan/generated/PR165_NoQuantumBackendAdvantageClaimAudit.report.json",
    "docs/master_plan/generated/PR165_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
    "docs/master_plan/generated/PR165_OrphanArtifactAudit.report.json",
    "docs/master_plan/generated/pr165_shards",
    "tools/run_validation_gates.py",
    "tools/ci_branch_context.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "tests/tools/test_ci_branch_context.py",
)

OPTIONAL_INPUT_GROUPS = {
    "pr165_repair_routing": (
        "docs/master_plan/generated/PR165_PostLaunchRepairRoutingSemantics.report.json",
        "docs/master_plan/generated/PR165_RepairRoutingHandoffRegistry.report.json",
        "docs/master_plan/generated/PR165_CandidateVersionRepairPlan.report.json",
        "docs/master_plan/generated/PR165_RepairRetestRouteRegistry.report.json",
    ),
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
    explicit = {
        "PR165_B_ReportManifest.report.json": "pr165_b_report_manifest.schema.json",
        "PR165_B_InputConsumptionAudit.report.json": "pr165_b_input_consumption_audit.schema.json",
        "PR165_B_AsOfLeakageAudit.report.json": "pr165_b_asof_leakage_audit.schema.json",
        "PR165_B_EvidenceSufficiencyRegistry.report.json": "pr165_b_evidence_sufficiency_record.schema.json",
        "PR165_B_FalseDiscoveryControlRegistry.report.json": "pr165_b_false_discovery_control_record.schema.json",
        "PR165_B_ConditionFingerprintRegistry.report.json": "pr165_b_condition_fingerprint.schema.json",
        "PR165_B_CombinationFingerprintRegistry.report.json": "pr165_b_combination_fingerprint.schema.json",
        "PR165_B_ScenarioOutcomeMatrix.report.json": "pr165_b_scenario_outcome_record.schema.json",
        "PR165_B_NegativeCombinationAvoidanceRegistry.report.json": "pr165_b_negative_memory_record.schema.json",
        "PR165_B_PositiveConditionScopedPreferenceRegistry.report.json": "pr165_b_positive_memory_record.schema.json",
        "PR165_B_FragileCombinationWatchlist.report.json": "pr165_b_fragile_memory_record.schema.json",
        "PR165_B_OutcomeAttributionLedger.report.json": "pr165_b_outcome_attribution_record.schema.json",
        "PR165_B_CounterfactualAttributionLedger.report.json": "pr165_b_counterfactual_attribution_record.schema.json",
        "PR165_B_CooldownPolicyRegistry.report.json": "pr165_b_cooldown_policy_record.schema.json",
        "PR165_B_RetestEligibilityRegistry.report.json": "pr165_b_retest_policy_record.schema.json",
        "PR165_B_MemoryDecayAndOverridePolicy.report.json": "pr165_b_memory_decay_policy_record.schema.json",
        "PR165_B_SimilarityMatchPolicyRegistry.report.json": "pr165_b_similarity_match_policy_record.schema.json",
        "PR165_B_AllowedWhenConditionRegistry.report.json": "pr165_b_allowed_when_policy_record.schema.json",
        "PR165_B_RepairRouteHandoffRegistry.report.json": "pr165_b_repair_route_record.schema.json",
        "PR165_B_ReplayPaperRetestQueue.report.json": "pr165_b_retest_queue_record.schema.json",
        "PR165_B_CandidateVersionMemoryRegistry.report.json": "pr165_b_candidate_version_memory_record.schema.json",
        "PR165_B_QuantumNegativeMemoryRegistry.report.json": "pr165_b_quantum_negative_memory_record.schema.json",
        "PR165_B_AgentSelectionOverlayHandoff.report.json": "pr165_b_agent_selection_overlay_record.schema.json",
        "PR165_B_AgentMemoryRouter.report.json": "pr165_b_agent_memory_route_record.schema.json",
        "PR165_B_LineageGraph.report.json": "pr165_b_lineage_graph_record.schema.json",
        "PR165_B_DashboardMemoryHandoff.report.json": "pr165_b_dashboard_handoff_record.schema.json",
        "PR165_B_GovernanceMemoryHandoff.report.json": "pr165_b_governance_handoff_record.schema.json",
        "PR165_B_FinalSummary.report.json": "pr165_b_final_summary.schema.json",
    }
    if filename.startswith("PR165_B_External"):
        return "pr165_b_input_consumption_audit.schema.json"
    if filename.startswith("PR165_B_No"):
        return "pr165_b_authority_audit.schema.json"
    if "Orphan" in filename:
        return "pr165_b_orphan_audit.schema.json"
    if filename == "PR165_B_CombinationOutcomeMemoryLedger.report.json":
        return "pr165_b_candidate_version_memory_record.schema.json"
    if filename == "PR165_B_OptionalContextMissingReceipt.report.json":
        return "pr165_b_input_consumption_audit.schema.json"
    return explicit.get(filename, "pr165_b_candidate_version_memory_record.schema.json")


REPORT_SCHEMA_REFS = {
    filename: f"{SCHEMA_DIR.as_posix()}/{_schema_for_report(filename)}"
    for filename in REPORT_FILENAMES
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
        raise RuntimeError(f"PR165-B must build on {EXPECTED_BRANCH}; current branch is {branch!r}")


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
