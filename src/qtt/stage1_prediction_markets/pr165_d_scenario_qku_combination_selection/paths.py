"""Paths, report names, schema names, and branch guard for PR165-D."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess

from .central_vocab import EXPECTED_BRANCH

GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
SHARD_DIR = GENERATED_DIR / "pr165_d_shards"
TEST_DIR = Path("tests/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection")
PACKAGE_IMPORT = "src.qtt.stage1_prediction_markets.pr165_d_scenario_qku_combination_selection"

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
    "docs/master_plan/generated/pr165_shards",
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
    "docs/master_plan/generated/pr165_b_shards",
    "docs/master_plan/generated/PR165_C_ReportManifest.report.json",
    "docs/master_plan/generated/PR165_C_FinalSummary.report.json",
    "docs/master_plan/generated/PR165_C_MemoryConsumerRouter.report.json",
    "docs/master_plan/generated/PR165_C_PendingRetestQueue.report.json",
    "docs/master_plan/generated/PR165_C_RepairToRetestHandoff.report.json",
    "docs/master_plan/generated/PR165_C_RetestPriorityRanking.report.json",
    "docs/master_plan/generated/PR165_C_ComputableArtifactPayloadRegistry.report.json",
    "docs/master_plan/generated/PR165_C_ComputableQKUFormulaActionRegistry.report.json",
    "docs/master_plan/generated/PR165_C_FormulaTestVectorRegistry.report.json",
    "docs/master_plan/generated/PR165_C_ConditionRegimeFeatureMatrix.report.json",
    "docs/master_plan/generated/PR165_C_QuantumConsumerRouter.report.json",
    "docs/master_plan/generated/PR165_C_AgentTaskQueue.report.json",
    "docs/master_plan/generated/PR165_C_AgentTaskReceiptRequirementMatrix.report.json",
    "docs/master_plan/generated/PR165_C_DashboardConsumerHandoff.report.json",
    "docs/master_plan/generated/PR165_C_GovernanceConsumerHandoff.report.json",
    "docs/master_plan/generated/PR165_C_CommanderConsumerHandoff.report.json",
    "docs/master_plan/generated/PR165_C_LineageGraph.report.json",
    "docs/master_plan/generated/PR165_C_AuthorityBoundaryAudit.report.json",
    "docs/master_plan/generated/PR165_C_OrphanArtifactAudit.report.json",
    "docs/master_plan/generated/pr165_c_shards",
    "docs/master_plan/generated/PR208_FinalSummary.report.json",
    "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    "docs/master_plan/generated/PR208_ChangedAreaRoutingPolicy.report.json",
    "docs/master_plan/generated/PR208_CrossPlatformPathInvariant.report.json",
    "tools/run_validation_gates.py",
    "tools/ci_branch_context.py",
    "tools/changed_area_validation_router.py",
    "tools/validation_inventory.py",
    "tools/repo_path_refs.py",
    "tools/cross_platform_path_invariant.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "tests/tools/test_ci_branch_context.py",
    "tests/tools/test_changed_area_validation_router.py",
    "tests/tools/test_validation_inventory.py",
    "tests/tools/test_cross_platform_path_invariant.py",
)

OPTIONAL_INPUT_GROUPS = {
    "pr162e_formula_plugin_authority_outputs": (
        "docs/master_plan/generated/PR162E_FormulaPluginRegistry.report.json",
        "docs/master_plan/generated/PR162E_FormulaPluginAcceptanceLedger.report.json",
    ),
    "pr162f_owner_agent_formula_intake_outputs": (
        "docs/master_plan/generated/PR162F_FormulaAlgorithmIntakeRegistry.report.json",
        "docs/master_plan/generated/PR162F_OwnerAgentFormulaAcceptanceLedger.report.json",
    ),
    "pr162e_q_quantum_auto_mapper_outputs": (
        "docs/master_plan/generated/PR162E_Q_QuantumAutoMapperRegistry.report.json",
        "docs/master_plan/generated/PR162E-Q_QuantumAutoMapperRegistry.report.json",
    ),
    "pr166_q_quantum_comparator_outputs": (
        "docs/master_plan/generated/PR166_Q_QuantumClassicalComparatorResultRegistry.report.json",
        "docs/master_plan/generated/PR166-Q_QuantumClassicalComparatorResultRegistry.report.json",
    ),
    "legacy_formula_algorithm_candidate_artifacts": (
        "docs/master_plan/generated/PR162B_QKUFormulaRegistry.report.json",
        "docs/master_plan/generated/PR162B_QKUAlgorithmRegistry.report.json",
        "docs/master_plan/generated/PR162D_R2A_FormulaExpressionRegistry.report.json",
        "docs/master_plan/generated/PR162D_R2A_AlgorithmProcedureRegistry.report.json",
        "docs/master_plan/generated/PR164_QKUFormulaRegistry.report.json",
        "docs/master_plan/generated/PR165_ScoreFormulaRegistry.report.json",
    ),
    "legacy_quantum_comparator_candidate_artifacts": (
        "docs/master_plan/generated/PR162D_QuantumClassicalComparatorSmokeResult.report.json",
        "docs/master_plan/generated/PR162D_R1_QuantumClassicalComparatorMappingLedger.report.json",
        "docs/master_plan/generated/PR164_QuantumClassicalComparatorPreparation.report.json",
        "docs/master_plan/generated/PR165_QuantumFormulationMaterializationRegistry.report.json",
    ),
    "unexpected_retest_result_artifacts": (
        "docs/master_plan/generated/PR166_S_ReplayPaperRetestResultRegistry.report.json",
        "docs/master_plan/generated/PR166-S_ReplayPaperRetestResultRegistry.report.json",
    ),
}

REPORT_FILENAMES = (
    "PR165_D_InputConsumptionAudit.report.json",
    "PR165_D_OptionalInputMissingReceipt.report.json",
    "PR165_D_ExternalDesignScoutCandidateLedger.report.json",
    "PR165_D_ScenarioQKUCombinationSelectionPolicy.report.json",
    "PR165_D_ScenarioGroupRegistry.report.json",
    "PR165_D_CandidateFeatureVectorRegistry.report.json",
    "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json",
    "PR165_D_SelectionScoreComponentRegistry.report.json",
    "PR165_D_SelectionScoreRegistry.report.json",
    "PR165_D_DiversificationAdjustmentLedger.report.json",
    "PR165_D_MarginalUtilitySelectionLedger.report.json",
    "PR165_D_BatchExposureCapacityLedger.report.json",
    "PR165_D_SelectedExcludedReasonLedger.report.json",
    "PR165_D_SelectionFalseDiscoveryControl.report.json",
    "PR165_D_PointInTimeSelectionAudit.report.json",
    "PR165_D_RetestBatchSelectionQueue.report.json",
    "PR165_D_RepairBeforeRetestSelectionQueue.report.json",
    "PR165_D_FormulaAlgorithmOptionalRouteRegistry.report.json",
    "PR165_D_QuantumSelectionRouter.report.json",
    "PR165_D_AgentSelectionContract.report.json",
    "PR165_D_AgentSelectionHandoff.report.json",
    "PR165_D_DashboardSelectionHandoff.report.json",
    "PR165_D_GovernanceSelectionHandoff.report.json",
    "PR165_D_CommanderSelectionHandoff.report.json",
    "PR165_D_LineageGraph.report.json",
    "PR165_D_AuthorityBoundaryAudit.report.json",
    "PR165_D_OrphanArtifactAudit.report.json",
    "PR165_D_ReportManifest.report.json",
    "PR165_D_FinalSummary.report.json",
)

SUMMARY_REPORTS = frozenset(
    {
        "PR165_D_InputConsumptionAudit.report.json",
        "PR165_D_OptionalInputMissingReceipt.report.json",
        "PR165_D_ExternalDesignScoutCandidateLedger.report.json",
        "PR165_D_ScenarioQKUCombinationSelectionPolicy.report.json",
        "PR165_D_ScenarioGroupRegistry.report.json",
        "PR165_D_BatchExposureCapacityLedger.report.json",
        "PR165_D_AuthorityBoundaryAudit.report.json",
        "PR165_D_OrphanArtifactAudit.report.json",
        "PR165_D_ReportManifest.report.json",
        "PR165_D_FinalSummary.report.json",
    }
)
ROW_LEVEL_REPORTS = frozenset(filename for filename in REPORT_FILENAMES if filename not in SUMMARY_REPORTS)

SCHEMA_FILENAMES = (
    "pr165_d_report_manifest.schema.json",
    "pr165_d_input_consumption_audit.schema.json",
    "pr165_d_optional_input_missing_receipt.schema.json",
    "pr165_d_external_design_scouting.schema.json",
    "pr165_d_selection_policy.schema.json",
    "pr165_d_scenario_group.schema.json",
    "pr165_d_candidate_feature_vector.schema.json",
    "pr165_d_combination_candidate.schema.json",
    "pr165_d_selection_score_component.schema.json",
    "pr165_d_selection_score.schema.json",
    "pr165_d_diversification_adjustment.schema.json",
    "pr165_d_marginal_utility_selection.schema.json",
    "pr165_d_batch_exposure_capacity.schema.json",
    "pr165_d_selected_excluded_reason.schema.json",
    "pr165_d_false_discovery_control.schema.json",
    "pr165_d_point_in_time_selection_audit.schema.json",
    "pr165_d_retest_batch_selection_record.schema.json",
    "pr165_d_repair_before_retest_selection_record.schema.json",
    "pr165_d_formula_algorithm_optional_route.schema.json",
    "pr165_d_quantum_selection_route.schema.json",
    "pr165_d_agent_selection_contract.schema.json",
    "pr165_d_agent_selection_handoff.schema.json",
    "pr165_d_dashboard_selection_handoff.schema.json",
    "pr165_d_governance_selection_handoff.schema.json",
    "pr165_d_commander_selection_handoff.schema.json",
    "pr165_d_lineage_graph_record.schema.json",
    "pr165_d_orphan_audit.schema.json",
    "pr165_d_authority_boundary_audit.schema.json",
    "pr165_d_final_summary.schema.json",
)

REPORT_SCHEMA_REFS = {
    "PR165_D_InputConsumptionAudit.report.json": "pr165_d_input_consumption_audit.schema.json",
    "PR165_D_OptionalInputMissingReceipt.report.json": "pr165_d_optional_input_missing_receipt.schema.json",
    "PR165_D_ExternalDesignScoutCandidateLedger.report.json": "pr165_d_external_design_scouting.schema.json",
    "PR165_D_ScenarioQKUCombinationSelectionPolicy.report.json": "pr165_d_selection_policy.schema.json",
    "PR165_D_ScenarioGroupRegistry.report.json": "pr165_d_scenario_group.schema.json",
    "PR165_D_CandidateFeatureVectorRegistry.report.json": "pr165_d_candidate_feature_vector.schema.json",
    "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json": "pr165_d_combination_candidate.schema.json",
    "PR165_D_SelectionScoreComponentRegistry.report.json": "pr165_d_selection_score_component.schema.json",
    "PR165_D_SelectionScoreRegistry.report.json": "pr165_d_selection_score.schema.json",
    "PR165_D_DiversificationAdjustmentLedger.report.json": "pr165_d_diversification_adjustment.schema.json",
    "PR165_D_MarginalUtilitySelectionLedger.report.json": "pr165_d_marginal_utility_selection.schema.json",
    "PR165_D_BatchExposureCapacityLedger.report.json": "pr165_d_batch_exposure_capacity.schema.json",
    "PR165_D_SelectedExcludedReasonLedger.report.json": "pr165_d_selected_excluded_reason.schema.json",
    "PR165_D_SelectionFalseDiscoveryControl.report.json": "pr165_d_false_discovery_control.schema.json",
    "PR165_D_PointInTimeSelectionAudit.report.json": "pr165_d_point_in_time_selection_audit.schema.json",
    "PR165_D_RetestBatchSelectionQueue.report.json": "pr165_d_retest_batch_selection_record.schema.json",
    "PR165_D_RepairBeforeRetestSelectionQueue.report.json": "pr165_d_repair_before_retest_selection_record.schema.json",
    "PR165_D_FormulaAlgorithmOptionalRouteRegistry.report.json": "pr165_d_formula_algorithm_optional_route.schema.json",
    "PR165_D_QuantumSelectionRouter.report.json": "pr165_d_quantum_selection_route.schema.json",
    "PR165_D_AgentSelectionContract.report.json": "pr165_d_agent_selection_contract.schema.json",
    "PR165_D_AgentSelectionHandoff.report.json": "pr165_d_agent_selection_handoff.schema.json",
    "PR165_D_DashboardSelectionHandoff.report.json": "pr165_d_dashboard_selection_handoff.schema.json",
    "PR165_D_GovernanceSelectionHandoff.report.json": "pr165_d_governance_selection_handoff.schema.json",
    "PR165_D_CommanderSelectionHandoff.report.json": "pr165_d_commander_selection_handoff.schema.json",
    "PR165_D_LineageGraph.report.json": "pr165_d_lineage_graph_record.schema.json",
    "PR165_D_AuthorityBoundaryAudit.report.json": "pr165_d_authority_boundary_audit.schema.json",
    "PR165_D_OrphanArtifactAudit.report.json": "pr165_d_orphan_audit.schema.json",
    "PR165_D_ReportManifest.report.json": "pr165_d_report_manifest.schema.json",
    "PR165_D_FinalSummary.report.json": "pr165_d_final_summary.schema.json",
}


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
        raise RuntimeError(f"PR165-D must build on {EXPECTED_BRANCH}, got {branch}")


def normalize_repo_ref(value: str | Path) -> str:
    raw = value.as_posix() if isinstance(value, (PurePosixPath, PureWindowsPath)) else str(value)
    windows_ref = PureWindowsPath(raw)
    if windows_ref.drive or windows_ref.root:
        raise ValueError(f"repo ref must be relative: {raw}")
    normalized = raw.replace("\\", "/")
    posix_ref = PurePosixPath(normalized)
    if posix_ref.is_absolute():
        raise ValueError(f"repo ref must be relative: {raw}")
    parts = tuple(part for part in posix_ref.parts if part != ".")
    if not parts:
        raise ValueError("repo ref must not be empty")
    if any(part == ".." for part in parts):
        raise ValueError(f"repo ref must not contain '..': {raw}")
    return "/".join(parts)


def to_repo_posix(path: Path, repo_root: Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        root = Path(repo_root).resolve()
        try:
            candidate = candidate.resolve().relative_to(root)
        except ValueError as exc:
            raise ValueError(f"path is outside repo root: {path}") from exc
    return normalize_repo_ref(candidate)


def resolve_repo_relative(repo_root: Path, repo_ref: str | Path) -> Path:
    normalized = normalize_repo_ref(repo_ref)
    return Path(repo_root).joinpath(*normalized.split("/"))


def schema_path(repo_root: Path, filename: str) -> Path:
    return repo_root / SCHEMA_DIR / filename
