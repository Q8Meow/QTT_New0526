"""Paths, branch guard, schemas, and report names for PR164."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
from typing import Any

from .authority_policy import EXPECTED_BRANCH, PR_ID


GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "pr164_review_provenance_qku_canonical_coverage_audit"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
SHARD_DIR = GENERATED_DIR / "pr164_shards"
TEST_DIR = Path(
    "tests/stage1_prediction_markets/"
    "pr164_review_provenance_qku_canonical_coverage_audit"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "pr164_review_provenance_qku_canonical_coverage_audit"
)

SCHEMA_FILENAMES = (
    "central_reason_codes.schema.json",
    "pr164_report_manifest.schema.json",
    "pr164_central_reason_codes.schema.json",
    "pr164_authority_decision.schema.json",
    "pr164_input_consumption_audit.schema.json",
    "pr164_qku_identity_record.schema.json",
    "pr164_master_inventory_reconciliation_record.schema.json",
    "pr164_market_scope_record.schema.json",
    "pr164_stage1_activation_record.schema.json",
    "pr164_formula_objective_solver_record.schema.json",
    "pr164_computability_materialization_record.schema.json",
    "pr164_formula_test_vector_record.schema.json",
    "pr164_execution_cost_component_record.schema.json",
    "pr164_missing_value_fill_task.schema.json",
    "pr164_candidate_source_record.schema.json",
    "pr164_provenance_tier_record.schema.json",
    "pr164_divergence_materiality_record.schema.json",
    "pr164_infrastructure_rejection_review_record.schema.json",
    "pr164_quantum_compatibility_record.schema.json",
    "pr164_latency_hot_path_record.schema.json",
    "pr164_agent_orchestration_record.schema.json",
    "pr164_downstream_route_record.schema.json",
    "pr164_negative_memory_preparation_record.schema.json",
    "pr164_model_risk_inventory_record.schema.json",
    "pr164_final_summary.schema.json",
)

REPORT_FILENAMES = (
    "PR164_InputConsumptionAudit.report.json",
    "PR164_PR159SOpenIntakeCurrentizationAudit.report.json",
    "PR164_QKUCanonicalUmbrellaAudit.report.json",
    "PR164_MasterQKUInventoryReconciliation.report.json",
    "PR164_QKUResidual4835ToAtomicRows4183PR154342MergeAudit.report.json",
    "PR164_QKUHistorical9360VsCurrent6502Reconciliation.report.json",
    "PR164_QKUMarketSortedInventory.report.json",
    "PR164_QKUClassicalQuantumHybridInventory.report.json",
    "PR164_QKUFormulaObjectiveSolverCoverageAudit.report.json",
    "PR164_QKUComputabilityMaterializationRegistry.report.json",
    "PR164_QKUFormulaRegistry.report.json",
    "PR164_QKUFormulaTestVectorRegistry.report.json",
    "PR164_QKUMissingValueFillRouter.report.json",
    "PR164_CandidateSourceAcquisitionLedger.report.json",
    "PR164_CandidateOnlineSourceEnrichmentRegistry.report.json",
    "PR164_CandidateSourcePolicyAudit.report.json",
    "PR164_PointInTimeCandidateSourceLedger.report.json",
    "PR164_CandidateSourceToQKUMappingRegistry.report.json",
    "PR164_QKUMarketScopeCoverageAudit.report.json",
    "PR164_QKUStage1ActivationDormancyAudit.report.json",
    "PR164_QKUAgentActivationAllowlistAudit.report.json",
    "PR164_PR163BEvidenceReviewProvenanceRegistry.report.json",
    "PR164_PR163BDivergenceMaterialityReview.report.json",
    "PR164_PR163BInfrastructureRejectionReview.report.json",
    "PR164_ExecutionCostComponentCoverage.report.json",
    "PR164_LatencyHotPathClassifier.report.json",
    "PR164_HotPathCachePreparationLedger.report.json",
    "PR164_QKUGraphPRLabelEdgeEnrichmentPlan.report.json",
    "PR164_QKUOnlineSourceEnrichmentPlan.report.json",
    "PR164_ModelRiskInventoryForQKU.report.json",
    "PR164_ModelAssumptionLimitationLedger.report.json",
    "PR164_ModelValidationTargetLedger.report.json",
    "PR164_QuantumCompatibilityRouter.report.json",
    "PR164_QuantumObjectiveConstraintCompletenessAudit.report.json",
    "PR164_QuantumClassicalComparatorPreparation.report.json",
    "PR164_AgentOrchestrationRouter.report.json",
    "PR164_QKUUpstreamDownstreamClosureMatrix.report.json",
    "PR164_PR162BRepairTriggerMatrix.report.json",
    "PR164_PR162D_R3RepairTriggerMatrix.report.json",
    "PR164_PR163CRepairTriggerMatrix.report.json",
    "PR164_PR165ScoringReadinessMatrix.report.json",
    "PR164_PR165BNegativeMemoryPreparation.report.json",
    "PR164_CentralAuthorityDecisionLedger.report.json",
    "PR164_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
    "PR164_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR164_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
    "PR164_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR164_OrphanArtifactAudit.report.json",
    "PR164_ReportManifest.report.json",
    "PR164_FinalSummary.report.json",
    "PR164_DecisionAndNextPRRecommendation.report.json",
)

ROW_LEVEL_REPORTS = frozenset(
    filename
    for filename in REPORT_FILENAMES
    if filename
    not in {
        "PR164_InputConsumptionAudit.report.json",
        "PR164_PR159SOpenIntakeCurrentizationAudit.report.json",
        "PR164_QKUCanonicalUmbrellaAudit.report.json",
        "PR164_CandidateSourceAcquisitionLedger.report.json",
        "PR164_CandidateOnlineSourceEnrichmentRegistry.report.json",
        "PR164_CandidateSourcePolicyAudit.report.json",
        "PR164_PointInTimeCandidateSourceLedger.report.json",
        "PR164_QKUOnlineSourceEnrichmentPlan.report.json",
        "PR164_CentralAuthorityDecisionLedger.report.json",
        "PR164_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
        "PR164_NoQuantumBackendAdvantageClaimAudit.report.json",
        "PR164_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
        "PR164_NoQTTChecksumFreezeAuthorityAudit.report.json",
        "PR164_OrphanArtifactAudit.report.json",
        "PR164_ReportManifest.report.json",
        "PR164_FinalSummary.report.json",
        "PR164_DecisionAndNextPRRecommendation.report.json",
    }
)

REPORT_SCHEMA_REFS = {
    "PR164_ReportManifest.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_report_manifest.schema.json",
    "PR164_CentralAuthorityDecisionLedger.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_authority_decision.schema.json",
    "PR164_InputConsumptionAudit.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_input_consumption_audit.schema.json",
    "PR164_QKUCanonicalUmbrellaAudit.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_qku_identity_record.schema.json",
    "PR164_MasterQKUInventoryReconciliation.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_master_inventory_reconciliation_record.schema.json",
    "PR164_QKUResidual4835ToAtomicRows4183PR154342MergeAudit.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_master_inventory_reconciliation_record.schema.json",
    "PR164_QKUHistorical9360VsCurrent6502Reconciliation.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_master_inventory_reconciliation_record.schema.json",
    "PR164_QKUMarketSortedInventory.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_market_scope_record.schema.json",
    "PR164_QKUClassicalQuantumHybridInventory.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_qku_identity_record.schema.json",
    "PR164_QKUFormulaObjectiveSolverCoverageAudit.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_formula_objective_solver_record.schema.json",
    "PR164_QKUComputabilityMaterializationRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_computability_materialization_record.schema.json",
    "PR164_QKUFormulaRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_formula_objective_solver_record.schema.json",
    "PR164_QKUFormulaTestVectorRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_formula_test_vector_record.schema.json",
    "PR164_QKUMissingValueFillRouter.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_missing_value_fill_task.schema.json",
    "PR164_CandidateSourceAcquisitionLedger.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_candidate_source_record.schema.json",
    "PR164_CandidateOnlineSourceEnrichmentRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_candidate_source_record.schema.json",
    "PR164_CandidateSourcePolicyAudit.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_candidate_source_record.schema.json",
    "PR164_PointInTimeCandidateSourceLedger.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_candidate_source_record.schema.json",
    "PR164_CandidateSourceToQKUMappingRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_candidate_source_record.schema.json",
    "PR164_QKUMarketScopeCoverageAudit.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_market_scope_record.schema.json",
    "PR164_QKUStage1ActivationDormancyAudit.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_stage1_activation_record.schema.json",
    "PR164_QKUAgentActivationAllowlistAudit.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_stage1_activation_record.schema.json",
    "PR164_PR163BEvidenceReviewProvenanceRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_provenance_tier_record.schema.json",
    "PR164_PR163BDivergenceMaterialityReview.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_divergence_materiality_record.schema.json",
    "PR164_PR163BInfrastructureRejectionReview.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_infrastructure_rejection_review_record.schema.json",
    "PR164_ExecutionCostComponentCoverage.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_execution_cost_component_record.schema.json",
    "PR164_LatencyHotPathClassifier.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_latency_hot_path_record.schema.json",
    "PR164_HotPathCachePreparationLedger.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_latency_hot_path_record.schema.json",
    "PR164_QKUGraphPRLabelEdgeEnrichmentPlan.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_downstream_route_record.schema.json",
    "PR164_ModelRiskInventoryForQKU.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_model_risk_inventory_record.schema.json",
    "PR164_ModelAssumptionLimitationLedger.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_model_risk_inventory_record.schema.json",
    "PR164_ModelValidationTargetLedger.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_model_risk_inventory_record.schema.json",
    "PR164_QuantumCompatibilityRouter.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_quantum_compatibility_record.schema.json",
    "PR164_QuantumObjectiveConstraintCompletenessAudit.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_quantum_compatibility_record.schema.json",
    "PR164_QuantumClassicalComparatorPreparation.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_quantum_compatibility_record.schema.json",
    "PR164_AgentOrchestrationRouter.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_agent_orchestration_record.schema.json",
    "PR164_QKUUpstreamDownstreamClosureMatrix.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_agent_orchestration_record.schema.json",
    "PR164_PR162BRepairTriggerMatrix.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_downstream_route_record.schema.json",
    "PR164_PR162D_R3RepairTriggerMatrix.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_downstream_route_record.schema.json",
    "PR164_PR163CRepairTriggerMatrix.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_downstream_route_record.schema.json",
    "PR164_PR165ScoringReadinessMatrix.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_downstream_route_record.schema.json",
    "PR164_PR165BNegativeMemoryPreparation.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_negative_memory_preparation_record.schema.json",
    "PR164_FinalSummary.report.json": f"{SCHEMA_DIR.as_posix()}/pr164_final_summary.schema.json",
}

REQUIRED_INPUT_FILENAMES = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "tools/ci_branch_context.py",
    "tools/run_validation_gates.py",
    "tools/currentize_pr152_after_generated_artifacts.py",
    "tools/validate_grand_global_debug_logical_consistency_audit.py",
    "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    "docs/master_plan/generated/PR161C_QKUMasterInventoryBridge.report.json",
    "docs/master_plan/generated/PR161C_QKUResidualAssimilationRegistry.report.json",
    "docs/master_plan/generated/PR161C_QKUAtomicRowsCompatibilityBridge.report.json",
    "docs/master_plan/generated/PR161C_QKUPR154CompatibilityBridge.report.json",
    "docs/master_plan/generated/PR162D_R2A_CandidatePacketV1Registry.report.json",
    "docs/master_plan/generated/PR162D_R2A_FormulationRecordRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_FormulaExpressionRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_AlgorithmProcedureRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_QuantumObjectiveRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_ClassicalComparatorRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_FinalSummary.report.json",
    "docs/master_plan/generated/PR163_FinalSummary.report.json",
    "docs/master_plan/generated/PR163_B_FinalSummary.report.json",
    "docs/master_plan/generated/PR163_B_PR164ReviewProvenanceHandoff.report.json",
    "docs/master_plan/generated/PR163_B_PairedReplayPaperComparisonCandidateRegistry.report.json",
    "docs/master_plan/generated/PR163_B_ReplayPaperDivergenceClassificationRegistry.report.json",
    "docs/master_plan/generated/PR163_B_TransactionCostAnalysisCandidateRegistry.report.json",
    "docs/master_plan/generated/PR163_B_ReplayPaperRejectionRemediationCandidateRegistry.report.json",
    "docs/master_plan/generated/PR163_B_ReplayPaperQuantumAdvisoryCarryForwardRegistry.report.json",
    "docs/master_plan/generated/PR163_B_ReportManifest.report.json",
)

OPTIONAL_ARTIFACT_GLOBS = (
    "PR159S_*.report.json",
    "PR159R*.report.json",
    "PR161A_*.report.json",
    "PR161B_*.report.json",
    "PR161C_*.report.json",
    "PR161D_*.report.json",
    "PR162B_*.report.json",
    "PR162D_R1_*.report.json",
    "PR162D_R2A_*.report.json",
    "PR162R_*.report.json",
    "PR162R_B_*.report.json",
    "PR163_*.report.json",
    "PR163_B_*.report.json",
)

UPSTREAM_PR_REFS = (
    "PR159S",
    "PR159R",
    "PR161A",
    "PR161B",
    "PR161C",
    "PR161D",
    "PR162B",
    "PR162D-R1",
    "PR162D-R2A",
    "PR162R",
    "PR162R-B",
    "PR163",
    "PR163-B",
)

DOWNSTREAM_PR_ROUTES = (
    "PR165",
    "PR165-B",
    "PR165-C",
    "PR163-C",
    "PR162B-R",
    "PR162D-R3",
    "PR162E",
    "PR162E-Q",
    "PR166-L",
)


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
        raise RuntimeError(f"{PR_ID} build must run on {EXPECTED_BRANCH}; current branch is {branch}")


def generated_path(repo_root: Path, filename: str) -> Path:
    return repo_root / GENERATED_DIR / filename


def schema_path(repo_root: Path, filename: str) -> Path:
    return repo_root / SCHEMA_DIR / filename


def normalize_repo_relative_ref(repo_root: Path, ref: Any, *, label: str = "PR164 path") -> str:
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
    resolved_root = repo_root.resolve(strict=False)
    try:
        candidate.resolve(strict=False).relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes repo root: {raw_path}") from exc
    return posix_path.as_posix()


def resolve_repo_relative(repo_root: Path, relative_ref: Any) -> Path:
    normalized = normalize_repo_relative_ref(repo_root, relative_ref)
    return repo_root.joinpath(*PurePosixPath(normalized).parts)
