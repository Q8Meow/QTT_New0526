"""Paths, branch guard, schemas, and report names for PR163-C."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
from typing import Any

from tools import ci_branch_context

from .pretrade_repair_authority_policy import EXPECTED_BRANCH, PR_ID


GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "pr163_c_pretrade_infrastructure_rejection_remediation"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
SHARD_DIR = GENERATED_DIR / "pr163_c_shards"
TEST_DIR = Path(
    "tests/stage1_prediction_markets/"
    "pr163_c_pretrade_infrastructure_rejection_remediation"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "pr163_c_pretrade_infrastructure_rejection_remediation"
)

SCHEMA_FILENAMES = (
    "pr163_c_report_manifest.schema.json",
    "pr163_c_input_consumption_audit.schema.json",
    "pr163_c_artificial_rejection_taxonomy_record.schema.json",
    "pr163_c_causal_defect_graph_record.schema.json",
    "pr163_c_repair_action_catalog_record.schema.json",
    "pr163_c_pretrade_repair_lattice_record.schema.json",
    "pr163_c_repair_formula_record.schema.json",
    "pr163_c_repair_test_vector_record.schema.json",
    "pr163_c_candidate_value_imputation_record.schema.json",
    "pr163_c_candidate_source_repair_enrichment_record.schema.json",
    "pr163_c_point_in_time_repair_record.schema.json",
    "pr163_c_data_quality_repair_record.schema.json",
    "pr163_c_fee_model_repair_record.schema.json",
    "pr163_c_slippage_model_repair_record.schema.json",
    "pr163_c_latency_model_repair_record.schema.json",
    "pr163_c_latency_error_budget_record.schema.json",
    "pr163_c_liquidity_spread_depth_repair_record.schema.json",
    "pr163_c_maker_taker_queue_record.schema.json",
    "pr163_c_adverse_selection_record.schema.json",
    "pr163_c_market_state_repair_record.schema.json",
    "pr163_c_event_lifecycle_repair_record.schema.json",
    "pr163_c_venue_normalization_repair_record.schema.json",
    "pr163_c_cross_venue_comparability_repair_record.schema.json",
    "pr163_c_order_intent_repair_record.schema.json",
    "pr163_c_order_lifecycle_trace_record.schema.json",
    "pr163_c_duplicate_order_intent_repair_record.schema.json",
    "pr163_c_synthetic_fill_model_repair_record.schema.json",
    "pr163_c_portfolio_exposure_ledger_repair_record.schema.json",
    "pr163_c_tca_component_repair_record.schema.json",
    "pr163_c_implementation_shortfall_record.schema.json",
    "pr163_c_risk_cap_input_repair_record.schema.json",
    "pr163_c_replay_paper_adapter_alignment_repair_record.schema.json",
    "pr163_c_formula_calibration_repair_record.schema.json",
    "pr163_c_model_risk_repair_record.schema.json",
    "pr163_c_counterfactual_repair_evaluation_record.schema.json",
    "pr163_c_quantum_repair_prioritization_record.schema.json",
    "pr163_c_agent_repair_orchestration_record.schema.json",
    "pr163_c_agent_task_handoff_record.schema.json",
    "pr163_c_repair_delta_record.schema.json",
    "pr163_c_pr165_readiness_delta_record.schema.json",
    "pr163_c_pr162d_r3_route_separator_record.schema.json",
    "pr163_c_negative_memory_handoff_record.schema.json",
    "pr163_c_future_live_readiness_field_prep_record.schema.json",
    "pr163_c_operator_dashboard_handoff_record.schema.json",
    "pr163_c_authority_audit.schema.json",
    "pr163_c_final_summary.schema.json",
)

REPORT_FILENAMES = (
    "PR163_C_InputConsumptionAudit.report.json",
    "PR163_C_ArtificialInfrastructureRejectionTaxonomy.report.json",
    "PR163_C_CausalDefectGraph.report.json",
    "PR163_C_RepairActionCatalog.report.json",
    "PR163_C_PretradeRepairLattice.report.json",
    "PR163_C_RepairFormulaRegistry.report.json",
    "PR163_C_RepairTestVectorRegistry.report.json",
    "PR163_C_CandidateValueImputationLedger.report.json",
    "PR163_C_CandidateSourceRepairEnrichmentLedger.report.json",
    "PR163_C_PointInTimeRepairLedger.report.json",
    "PR163_C_DataQualityRepairRegistry.report.json",
    "PR163_C_FeeModelRepairRegistry.report.json",
    "PR163_C_SlippageModelRepairRegistry.report.json",
    "PR163_C_LatencyModelRepairRegistry.report.json",
    "PR163_C_LatencyErrorBudgetLedger.report.json",
    "PR163_C_LiquiditySpreadDepthRepairRegistry.report.json",
    "PR163_C_MakerTakerQueueModelRegistry.report.json",
    "PR163_C_AdverseSelectionModelRegistry.report.json",
    "PR163_C_MarketStateRepairRegistry.report.json",
    "PR163_C_EventLifecycleRepairRegistry.report.json",
    "PR163_C_VenueNormalizationRepairRegistry.report.json",
    "PR163_C_CrossVenueComparabilityRepairRegistry.report.json",
    "PR163_C_OrderIntentRepairRegistry.report.json",
    "PR163_C_OrderLifecycleTraceRepairRegistry.report.json",
    "PR163_C_DuplicateOrderIntentRepairRegistry.report.json",
    "PR163_C_SyntheticFillModelRepairRegistry.report.json",
    "PR163_C_PortfolioExposureLedgerRepairRegistry.report.json",
    "PR163_C_TCAComponentRepairRegistry.report.json",
    "PR163_C_ImplementationShortfallModelRegistry.report.json",
    "PR163_C_RiskCapInputRepairRegistry.report.json",
    "PR163_C_ReplayPaperAdapterAlignmentRepairRegistry.report.json",
    "PR163_C_FormulaCalibrationRepairRegistry.report.json",
    "PR163_C_ModelRiskRepairLedger.report.json",
    "PR163_C_CounterfactualRepairEvaluation.report.json",
    "PR163_C_QuantumRepairPrioritizationLedger.report.json",
    "PR163_C_AgentRepairOrchestrationRouter.report.json",
    "PR163_C_AgentTaskHandoffMatrix.report.json",
    "PR163_C_RepairDeltaRegistry.report.json",
    "PR163_C_PR165ReadinessDelta.report.json",
    "PR163_C_PR162D_R3RouteSeparator.report.json",
    "PR163_C_PR165BNegativeMemoryHandoff.report.json",
    "PR163_C_FutureLiveReadinessFieldPrep.report.json",
    "PR163_C_OperatorDashboardHandoff.report.json",
    "PR163_C_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
    "PR163_C_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR163_C_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR163_C_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
    "PR163_C_OrphanArtifactAudit.report.json",
    "PR163_C_ReportManifest.report.json",
    "PR163_C_FinalSummary.report.json",
)

ROW_LEVEL_REPORTS = frozenset(
    filename
    for filename in REPORT_FILENAMES
    if filename
    not in {
        "PR163_C_InputConsumptionAudit.report.json",
        "PR163_C_RepairActionCatalog.report.json",
        "PR163_C_RepairFormulaRegistry.report.json",
        "PR163_C_RepairTestVectorRegistry.report.json",
        "PR163_C_PR165ReadinessDelta.report.json",
        "PR163_C_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
        "PR163_C_NoQTTChecksumFreezeAuthorityAudit.report.json",
        "PR163_C_NoQuantumBackendAdvantageClaimAudit.report.json",
        "PR163_C_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
        "PR163_C_OrphanArtifactAudit.report.json",
        "PR163_C_ReportManifest.report.json",
        "PR163_C_FinalSummary.report.json",
    }
)

REPORT_SCHEMA_REFS = {
    "PR163_C_ReportManifest.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_report_manifest.schema.json",
    "PR163_C_InputConsumptionAudit.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_input_consumption_audit.schema.json",
    "PR163_C_ArtificialInfrastructureRejectionTaxonomy.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_artificial_rejection_taxonomy_record.schema.json",
    "PR163_C_CausalDefectGraph.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_causal_defect_graph_record.schema.json",
    "PR163_C_RepairActionCatalog.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_repair_action_catalog_record.schema.json",
    "PR163_C_PretradeRepairLattice.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_pretrade_repair_lattice_record.schema.json",
    "PR163_C_RepairFormulaRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_repair_formula_record.schema.json",
    "PR163_C_RepairTestVectorRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_repair_test_vector_record.schema.json",
    "PR163_C_CandidateValueImputationLedger.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_candidate_value_imputation_record.schema.json",
    "PR163_C_CandidateSourceRepairEnrichmentLedger.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_candidate_source_repair_enrichment_record.schema.json",
    "PR163_C_PointInTimeRepairLedger.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_point_in_time_repair_record.schema.json",
    "PR163_C_DataQualityRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_data_quality_repair_record.schema.json",
    "PR163_C_FeeModelRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_fee_model_repair_record.schema.json",
    "PR163_C_SlippageModelRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_slippage_model_repair_record.schema.json",
    "PR163_C_LatencyModelRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_latency_model_repair_record.schema.json",
    "PR163_C_LatencyErrorBudgetLedger.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_latency_error_budget_record.schema.json",
    "PR163_C_LiquiditySpreadDepthRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_liquidity_spread_depth_repair_record.schema.json",
    "PR163_C_MakerTakerQueueModelRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_maker_taker_queue_record.schema.json",
    "PR163_C_AdverseSelectionModelRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_adverse_selection_record.schema.json",
    "PR163_C_MarketStateRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_market_state_repair_record.schema.json",
    "PR163_C_EventLifecycleRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_event_lifecycle_repair_record.schema.json",
    "PR163_C_VenueNormalizationRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_venue_normalization_repair_record.schema.json",
    "PR163_C_CrossVenueComparabilityRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_cross_venue_comparability_repair_record.schema.json",
    "PR163_C_OrderIntentRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_order_intent_repair_record.schema.json",
    "PR163_C_OrderLifecycleTraceRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_order_lifecycle_trace_record.schema.json",
    "PR163_C_DuplicateOrderIntentRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_duplicate_order_intent_repair_record.schema.json",
    "PR163_C_SyntheticFillModelRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_synthetic_fill_model_repair_record.schema.json",
    "PR163_C_PortfolioExposureLedgerRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_portfolio_exposure_ledger_repair_record.schema.json",
    "PR163_C_TCAComponentRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_tca_component_repair_record.schema.json",
    "PR163_C_ImplementationShortfallModelRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_implementation_shortfall_record.schema.json",
    "PR163_C_RiskCapInputRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_risk_cap_input_repair_record.schema.json",
    "PR163_C_ReplayPaperAdapterAlignmentRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_replay_paper_adapter_alignment_repair_record.schema.json",
    "PR163_C_FormulaCalibrationRepairRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_formula_calibration_repair_record.schema.json",
    "PR163_C_ModelRiskRepairLedger.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_model_risk_repair_record.schema.json",
    "PR163_C_CounterfactualRepairEvaluation.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_counterfactual_repair_evaluation_record.schema.json",
    "PR163_C_QuantumRepairPrioritizationLedger.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_quantum_repair_prioritization_record.schema.json",
    "PR163_C_AgentRepairOrchestrationRouter.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_agent_repair_orchestration_record.schema.json",
    "PR163_C_AgentTaskHandoffMatrix.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_agent_task_handoff_record.schema.json",
    "PR163_C_RepairDeltaRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_repair_delta_record.schema.json",
    "PR163_C_PR165ReadinessDelta.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_pr165_readiness_delta_record.schema.json",
    "PR163_C_PR162D_R3RouteSeparator.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_pr162d_r3_route_separator_record.schema.json",
    "PR163_C_PR165BNegativeMemoryHandoff.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_negative_memory_handoff_record.schema.json",
    "PR163_C_FutureLiveReadinessFieldPrep.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_future_live_readiness_field_prep_record.schema.json",
    "PR163_C_OperatorDashboardHandoff.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_operator_dashboard_handoff_record.schema.json",
    "PR163_C_FinalSummary.report.json": f"{SCHEMA_DIR.as_posix()}/pr163_c_final_summary.schema.json",
}
for _audit_name in (
    "PR163_C_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
    "PR163_C_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR163_C_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR163_C_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
    "PR163_C_OrphanArtifactAudit.report.json",
):
    REPORT_SCHEMA_REFS[_audit_name] = f"{SCHEMA_DIR.as_posix()}/pr163_c_authority_audit.schema.json"

PR164_REQUIRED_REPORTS = (
    "PR164_ReportManifest.report.json",
    "PR164_FinalSummary.report.json",
    "PR164_DecisionAndNextPRRecommendation.report.json",
    "PR164_PR163CRepairTriggerMatrix.report.json",
    "PR164_PR163BInfrastructureRejectionReview.report.json",
    "PR164_PR163BEvidenceReviewProvenanceRegistry.report.json",
    "PR164_PR163BDivergenceMaterialityReview.report.json",
    "PR164_PR165ScoringReadinessMatrix.report.json",
    "PR164_QKUMissingValueFillRouter.report.json",
    "PR164_QKUComputabilityMaterializationRegistry.report.json",
    "PR164_ExecutionCostComponentCoverage.report.json",
    "PR164_LatencyHotPathClassifier.report.json",
    "PR164_ModelRiskInventoryForQKU.report.json",
    "PR164_AgentOrchestrationRouter.report.json",
    "PR164_QuantumClassicalComparatorPreparation.report.json",
    "PR164_QuantumCompatibilityRouter.report.json",
    "PR164_CandidateSourceAcquisitionLedger.report.json",
    "PR164_CandidateSourcePolicyAudit.report.json",
    "PR164_PointInTimeCandidateSourceLedger.report.json",
)

OPTIONAL_INPUT_ARTIFACTS = (
    "docs/master_plan/generated/PR163_B_PairedReplayPaperConcurrentExecutorFinalSummary.report.json",
)

DOWNSTREAM_PR_ROUTES = (
    "PR165",
    "PR165-B",
    "PR162D-R3",
    "PR162E",
    "PR162F",
    "PR179",
    "PR180",
    "later replay/paper consumers",
)

UPSTREAM_PR_REFS = ("PR163-B", "PR164")
def current_branch(repo_root: Path) -> str:
    if ci_branch_context.github_actions_main_push_context_active():
        return "main"
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    branch = ci_branch_context.normalize_branch_context(result.stdout)
    if branch:
        return branch
    if ci_branch_context.github_actions_pull_request_detached_context_active(
        branch_returncode=result.returncode,
        branch=result.stdout,
    ):
        return (
            ci_branch_context.github_actions_head_ref_branch_context()
            or ci_branch_context.github_actions_branch_context()
        )
    return ""


def ensure_branch(repo_root: Path) -> None:
    branch = current_branch(repo_root)
    if not ci_branch_context.is_branch_allowed_for_upstream_pr_gate(
        branch,
        "PR163-C",
        ancestry_present=True,
        include_main=True,
    ):
        allowed = " or ".join((EXPECTED_BRANCH, "main"))
        raise RuntimeError(f"{PR_ID} build must run on {allowed}; current branch is {branch}")


def generated_path(repo_root: Path, filename: str) -> Path:
    return repo_root / GENERATED_DIR / filename


def schema_path(repo_root: Path, filename: str) -> Path:
    return repo_root / SCHEMA_DIR / filename


def normalize_repo_relative_ref(repo_root: Path, ref: Any, *, label: str = "PR163-C path") -> str:
    raw_path = str(ref)
    normalized = raw_path.replace("\\", "/")
    windows_path = PureWindowsPath(normalized)
    posix_path = PurePosixPath(normalized)
    if normalized.startswith("//") or normalized.startswith("\\\\"):
        raise ValueError(f"{label} must not be UNC: {raw_path}")
    if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise ValueError(f"{label} must be relative: {raw_path}")
    if any(part == ".." for part in posix_path.parts):
        raise ValueError(f"{label} must not contain '..': {raw_path}")
    candidate = repo_root.joinpath(*posix_path.parts)
    try:
        candidate.resolve(strict=False).relative_to(repo_root.resolve(strict=False))
    except ValueError as exc:
        raise ValueError(f"{label} escapes repo root: {raw_path}") from exc
    return posix_path.as_posix()


def resolve_repo_relative(repo_root: Path, relative_ref: Any) -> Path:
    normalized = normalize_repo_relative_ref(repo_root, relative_ref)
    return repo_root.joinpath(*PurePosixPath(normalized).parts)
