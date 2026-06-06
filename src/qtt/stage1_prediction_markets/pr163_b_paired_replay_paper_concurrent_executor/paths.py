"""Paths, branch guard, schemas, and report names for PR163-B."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
from typing import Any

from .authority_policy import EXPECTED_BRANCH, PR_ID


GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "pr163_b_paired_replay_paper_concurrent_executor"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
SHARD_DIR = GENERATED_DIR / "pr163_b_shards"
TEST_DIR = Path(
    "tests/stage1_prediction_markets/"
    "pr163_b_paired_replay_paper_concurrent_executor"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "pr163_b_paired_replay_paper_concurrent_executor"
)

SCHEMA_FILENAMES = (
    "PairedReplayPaperRunInputV1.schema.json",
    "PairedReplayPaperClockV1.schema.json",
    "ReplayPaperInputLockReceiptV1.schema.json",
    "ReplayPaperLeakageAsOfGuardReceiptV1.schema.json",
    "ReplayLaneExecutionTraceV1.schema.json",
    "PaperLaneExecutionTraceV1.schema.json",
    "ReplayPaperFillIntegrityReceiptV1.schema.json",
    "ReplayPaperAlignmentReceiptV1.schema.json",
    "ExecutionOutcomeCandidateReceiptV1.schema.json",
    "ReplayExecutionResultCandidateV1.schema.json",
    "PaperExecutionResultCandidateV1.schema.json",
    "PairedReplayPaperResultCandidateV1.schema.json",
    "PairedReplayPaperComparisonCandidateV1.schema.json",
    "ReplayPaperDivergenceClassificationV1.schema.json",
    "ReplayPaperRejectionRemediationCandidateV1.schema.json",
    "TransactionCostAnalysisCandidateV1.schema.json",
    "ReplayPaperScenarioStressCandidateV1.schema.json",
    "ReplayPaperWalkForwardHoldoutReadinessV1.schema.json",
    "ReplayPaperQuantumAdvisoryCarryForwardV1.schema.json",
    "ReplayPaperLLMFutureReviewHandoffV1.schema.json",
    "ReplayPaperPR164ReviewHandoffV1.schema.json",
    "ReplayPaperPR165ScoringHandoffV1.schema.json",
    "ReplayPaperPR166LLMHandoffV1.schema.json",
    "ReplayPaperSourceEvidenceBoundaryV1.schema.json",
)

REPORT_FILENAMES = (
    "PR163_B_InputConsumptionAudit.report.json",
    "PR163_B_PR162RB_PR163_ArtifactConsumptionLedger.report.json",
    "PR163_B_PairedReplayPaperRunInputRegistry.report.json",
    "PR163_B_PairedReplayPaperClockRegistry.report.json",
    "PR163_B_ReplayPaperInputLockReceiptRegistry.report.json",
    "PR163_B_ReplayPaperLeakageAsOfGuardReceiptRegistry.report.json",
    "PR163_B_ReplayLaneExecutionTraceRegistry.report.json",
    "PR163_B_PaperLaneExecutionTraceRegistry.report.json",
    "PR163_B_ReplayPaperFillIntegrityReceiptRegistry.report.json",
    "PR163_B_ReplayPaperAlignmentReceiptRegistry.report.json",
    "PR163_B_ExecutionOutcomeCandidateReceiptRegistry.report.json",
    "PR163_B_ReplayExecutionResultCandidateRegistry.report.json",
    "PR163_B_PaperExecutionResultCandidateRegistry.report.json",
    "PR163_B_PairedReplayPaperResultCandidateRegistry.report.json",
    "PR163_B_PairedReplayPaperComparisonCandidateRegistry.report.json",
    "PR163_B_ReplayPaperDivergenceClassificationRegistry.report.json",
    "PR163_B_ReplayPaperRejectionRemediationCandidateRegistry.report.json",
    "PR163_B_TransactionCostAnalysisCandidateRegistry.report.json",
    "PR163_B_ReplayPaperScenarioStressCandidateRegistry.report.json",
    "PR163_B_ReplayPaperWalkForwardHoldoutReadinessRegistry.report.json",
    "PR163_B_ReplayPaperQuantumAdvisoryCarryForwardRegistry.report.json",
    "PR163_B_ReplayPaperLLMFutureReviewHandoffRegistry.report.json",
    "PR163_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json",
    "PR163_B_PR164ReviewProvenanceHandoff.report.json",
    "PR163_B_PR165ScoringRankingHandoff.report.json",
    "PR163_B_PR166LLMReviewResearchHandoff.report.json",
    "PR163_B_PR162EPluginReplayPaperCompatibilityUpdate.report.json",
    "PR163_B_SourceCandidateReplayPaperResearchQueue.report.json",
    "PR163_B_SourceEvidenceBoundaryAudit.report.json",
    "PR163_B_NoLiveOrderProfitSourceConnectorPrivateStateAudit.report.json",
    "PR163_B_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR163_B_NoLLMRuntimeHotPathOrderReleaseSourceAcceptanceResultRewriteAudit.report.json",
    "PR163_B_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR163_B_OrphanReplayPaperArtifactAudit.report.json",
    "PR163_B_FinalSummary.report.json",
    "PR163_B_DecisionAndNextPRRecommendation.report.json",
    "PR163_B_ReportManifest.report.json",
)

ROW_LEVEL_REPORTS = frozenset(
    filename
    for filename in REPORT_FILENAMES
    if filename
    not in {
        "PR163_B_InputConsumptionAudit.report.json",
        "PR163_B_PR162RB_PR163_ArtifactConsumptionLedger.report.json",
        "PR163_B_SourceCandidateReplayPaperResearchQueue.report.json",
        "PR163_B_SourceEvidenceBoundaryAudit.report.json",
        "PR163_B_NoLiveOrderProfitSourceConnectorPrivateStateAudit.report.json",
        "PR163_B_NoQuantumBackendAdvantageClaimAudit.report.json",
        "PR163_B_NoLLMRuntimeHotPathOrderReleaseSourceAcceptanceResultRewriteAudit.report.json",
        "PR163_B_NoQTTChecksumFreezeAuthorityAudit.report.json",
        "PR163_B_OrphanReplayPaperArtifactAudit.report.json",
        "PR163_B_FinalSummary.report.json",
        "PR163_B_DecisionAndNextPRRecommendation.report.json",
        "PR163_B_ReportManifest.report.json",
    }
)

REPORT_SCHEMA_REFS = {
    "PR163_B_PairedReplayPaperRunInputRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PairedReplayPaperRunInputV1.schema.json",
    "PR163_B_PairedReplayPaperClockRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PairedReplayPaperClockV1.schema.json",
    "PR163_B_ReplayPaperInputLockReceiptRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperInputLockReceiptV1.schema.json",
    "PR163_B_ReplayPaperLeakageAsOfGuardReceiptRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperLeakageAsOfGuardReceiptV1.schema.json",
    "PR163_B_ReplayLaneExecutionTraceRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayLaneExecutionTraceV1.schema.json",
    "PR163_B_PaperLaneExecutionTraceRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperLaneExecutionTraceV1.schema.json",
    "PR163_B_ReplayPaperFillIntegrityReceiptRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperFillIntegrityReceiptV1.schema.json",
    "PR163_B_ReplayPaperAlignmentReceiptRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperAlignmentReceiptV1.schema.json",
    "PR163_B_ExecutionOutcomeCandidateReceiptRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ExecutionOutcomeCandidateReceiptV1.schema.json",
    "PR163_B_ReplayExecutionResultCandidateRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayExecutionResultCandidateV1.schema.json",
    "PR163_B_PaperExecutionResultCandidateRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperExecutionResultCandidateV1.schema.json",
    "PR163_B_PairedReplayPaperResultCandidateRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PairedReplayPaperResultCandidateV1.schema.json",
    "PR163_B_PairedReplayPaperComparisonCandidateRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PairedReplayPaperComparisonCandidateV1.schema.json",
    "PR163_B_ReplayPaperDivergenceClassificationRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperDivergenceClassificationV1.schema.json",
    "PR163_B_ReplayPaperRejectionRemediationCandidateRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperRejectionRemediationCandidateV1.schema.json",
    "PR163_B_TransactionCostAnalysisCandidateRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/TransactionCostAnalysisCandidateV1.schema.json",
    "PR163_B_ReplayPaperScenarioStressCandidateRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperScenarioStressCandidateV1.schema.json",
    "PR163_B_ReplayPaperWalkForwardHoldoutReadinessRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperWalkForwardHoldoutReadinessV1.schema.json",
    "PR163_B_ReplayPaperQuantumAdvisoryCarryForwardRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperQuantumAdvisoryCarryForwardV1.schema.json",
    "PR163_B_ReplayPaperLLMFutureReviewHandoffRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperLLMFutureReviewHandoffV1.schema.json",
    "PR163_B_PR164ReviewProvenanceHandoff.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperPR164ReviewHandoffV1.schema.json",
    "PR163_B_PR165ScoringRankingHandoff.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperPR165ScoringHandoffV1.schema.json",
    "PR163_B_PR166LLMReviewResearchHandoff.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperPR166LLMHandoffV1.schema.json",
    "PR163_B_SourceEvidenceBoundaryAudit.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperSourceEvidenceBoundaryV1.schema.json",
}

REQUIRED_INPUT_FILENAMES = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "docs/master_plan/generated/PR161F_ReplayRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PaperRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PairedReplayPaperRunPlan.report.json",
    "docs/master_plan/generated/PR161F_ResultPacketEmissionEligibilityGate.report.json",
    "docs/master_plan/generated/PR162_ReplayDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162_PaperDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162R_ReplayAdapterInputPacketRegistry.report.json",
    "docs/master_plan/generated/PR162R_PaperAdapterInputPacketRegistry.report.json",
    "docs/master_plan/generated/PR162R_ReplayRunRequestCandidateQueue.report.json",
    "docs/master_plan/generated/PR162R_PaperRunRequestCandidateQueue.report.json",
    "docs/master_plan/generated/PR162R_PairedReplayPaperRunRequestCandidatePlan.report.json",
    "docs/master_plan/generated/PR162R_QKUAgentReplayPaperHandoffMatrix.report.json",
    "docs/master_plan/generated/PR162D_R2A_CandidatePacketV1Registry.report.json",
    "docs/master_plan/generated/PR162D_R2A_FormulationRecordRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_FormulaExpressionRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_AlgorithmProcedureRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_QuantumObjectiveRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_ClassicalComparatorRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_QKUAgentWorkflowTraceabilityMatrix.report.json",
    "docs/master_plan/generated/PR162D_R2A_UpstreamDownstreamQKUOrchestrationMatrix.report.json",
    "docs/master_plan/generated/PR162D_R2A_HotPathPrecomputeCacheabilityMatrix.report.json",
    "docs/master_plan/generated/PR162R_B_FinalSummary.report.json",
    "docs/master_plan/generated/PR162R_B_ReplayPaperDatasetBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_ReplayBindingFanoutMatrix.report.json",
    "docs/master_plan/generated/PR162R_B_PaperBindingFanoutMatrix.report.json",
    "docs/master_plan/generated/PR162R_B_RowBindingResolutionMatrix.report.json",
    "docs/master_plan/generated/PR162R_B_ReplayHistoricalPriceSeriesBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_ReplayOrderbookSnapshotBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_ReplayTradePrintBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_ReplayEventStateTimelineBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_ReplaySettlementOutcomeBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_ReplayFeeSlippageCostModelBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_PaperMarketStateBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_PaperSyntheticFillModelRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_PaperPortfolioStateFixtureRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_PaperExecutionCostModelRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_FeeSlippageLatencyBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json",
    "docs/master_plan/generated/PR162R_B_QuantumObjectiveInputBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_QuantumConstraintInputBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_QuantumComparatorDatasetBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_ClassicalComparatorInputBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_PR163PaperAdapterHandoffUpdate.report.json",
    "docs/master_plan/generated/PR162R_B_PR164ReviewProvenanceHandoffUpdate.report.json",
    "docs/master_plan/generated/PR162R_B_PR165ScoringRankingHandoffUpdate.report.json",
    "docs/master_plan/generated/PR162R_B_PR162EPluginBindingCompatibilityUpdate.report.json",
    "docs/master_plan/generated/PR163_FinalSummary.report.json",
    "docs/master_plan/generated/PR163_PaperAdapterInputRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperDecisionIntentRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperOrderIntentRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperPreTradeCheckReceiptRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperRiskPolicyReceiptRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperOrderStateTransitionRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperSyntheticFillEventRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperPortfolioLedgerSnapshotRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperCashReservationReceiptRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperExecutionCostReceiptRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperLatencySlippageReceiptRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperCaptureEventRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperAdapterRunPlanRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperAdapterCaptureBundleRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperScenarioCoverageMatrix.report.json",
    "docs/master_plan/generated/PR163_PaperLedgerInvariantAudit.report.json",
    "docs/master_plan/generated/PR163_PaperModeQKUFormulaAlgorithmAgentRoutingMatrix.report.json",
    "docs/master_plan/generated/PR163_PaperQKUPrioritizationFeatureHandoffRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperQuantumAdvisoryInputRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperQuantumClassicalComparatorTraceRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperQuantumConstraintProjectionRegistry.report.json",
    "docs/master_plan/generated/PR163_PaperHotPathExclusionMatrix.report.json",
    "docs/master_plan/generated/PR163_PaperReplayParityPreparationMatrix.report.json",
    "docs/master_plan/generated/PR163_PaperLLMFutureHandoffExclusionReceiptRegistry.report.json",
    "docs/master_plan/generated/PR163_PR163BPairedReplayPaperExecutorHandoff.report.json",
    "docs/master_plan/generated/PR163_PR164ReviewProvenanceHandoff.report.json",
    "docs/master_plan/generated/PR163_PR165ScoringRankingHandoff.report.json",
    "docs/master_plan/generated/PR163_PR166LLMReviewResearchHandoff.report.json",
    "docs/master_plan/generated/PR163_PR162EPluginPaperAdapterCompatibilityUpdate.report.json",
    "docs/master_plan/generated/PR163_ReportManifest.report.json",
)

PR162RB_REQUIRED_ARTIFACTS = (
    "PR162R_B_FinalSummary.report.json",
    "PR162R_B_ReplayPaperDatasetBindingRegistry.report.json",
    "PR162R_B_ReplayBindingFanoutMatrix.report.json",
    "PR162R_B_PaperBindingFanoutMatrix.report.json",
    "PR162R_B_RowBindingResolutionMatrix.report.json",
    "PR162R_B_ReplayHistoricalPriceSeriesBindingRegistry.report.json",
    "PR162R_B_ReplayOrderbookSnapshotBindingRegistry.report.json",
    "PR162R_B_ReplayTradePrintBindingRegistry.report.json",
    "PR162R_B_ReplayEventStateTimelineBindingRegistry.report.json",
    "PR162R_B_ReplaySettlementOutcomeBindingRegistry.report.json",
    "PR162R_B_ReplayFeeSlippageCostModelBindingRegistry.report.json",
    "PR162R_B_PaperMarketStateBindingRegistry.report.json",
    "PR162R_B_PaperSyntheticFillModelRegistry.report.json",
    "PR162R_B_PaperPortfolioStateFixtureRegistry.report.json",
    "PR162R_B_PaperExecutionCostModelRegistry.report.json",
    "PR162R_B_FeeSlippageLatencyBindingRegistry.report.json",
    "PR162R_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json",
    "PR162R_B_QuantumObjectiveInputBindingRegistry.report.json",
    "PR162R_B_QuantumConstraintInputBindingRegistry.report.json",
    "PR162R_B_QuantumComparatorDatasetBindingRegistry.report.json",
    "PR162R_B_ClassicalComparatorInputBindingRegistry.report.json",
    "PR162R_B_PR163PaperAdapterHandoffUpdate.report.json",
    "PR162R_B_PR164ReviewProvenanceHandoffUpdate.report.json",
    "PR162R_B_PR165ScoringRankingHandoffUpdate.report.json",
    "PR162R_B_PR162EPluginBindingCompatibilityUpdate.report.json",
)

PR163_REQUIRED_ARTIFACTS = (
    "PR163_FinalSummary.report.json",
    "PR163_PaperAdapterInputRegistry.report.json",
    "PR163_PaperDecisionIntentRegistry.report.json",
    "PR163_PaperOrderIntentRegistry.report.json",
    "PR163_PaperPreTradeCheckReceiptRegistry.report.json",
    "PR163_PaperRiskPolicyReceiptRegistry.report.json",
    "PR163_PaperOrderStateTransitionRegistry.report.json",
    "PR163_PaperSyntheticFillEventRegistry.report.json",
    "PR163_PaperPortfolioLedgerSnapshotRegistry.report.json",
    "PR163_PaperCashReservationReceiptRegistry.report.json",
    "PR163_PaperExecutionCostReceiptRegistry.report.json",
    "PR163_PaperLatencySlippageReceiptRegistry.report.json",
    "PR163_PaperCaptureEventRegistry.report.json",
    "PR163_PaperAdapterRunPlanRegistry.report.json",
    "PR163_PaperAdapterCaptureBundleRegistry.report.json",
    "PR163_PaperModeQKUFormulaAlgorithmAgentRoutingMatrix.report.json",
    "PR163_PaperQKUPrioritizationFeatureHandoffRegistry.report.json",
    "PR163_PaperQuantumAdvisoryInputRegistry.report.json",
    "PR163_PaperQuantumClassicalComparatorTraceRegistry.report.json",
    "PR163_PaperQuantumConstraintProjectionRegistry.report.json",
    "PR163_PaperLLMFutureHandoffExclusionReceiptRegistry.report.json",
    "PR163_PR163BPairedReplayPaperExecutorHandoff.report.json",
    "PR163_PR164ReviewProvenanceHandoff.report.json",
    "PR163_PR165ScoringRankingHandoff.report.json",
    "PR163_PR166LLMReviewResearchHandoff.report.json",
    "PR163_PR162EPluginPaperAdapterCompatibilityUpdate.report.json",
)

UPSTREAM_PR_REFS = (
    "PR136",
    "PR161F",
    "PR162",
    "PR162D-R2A",
    "PR162R",
    "PR162R-B",
    "PR163",
)
DOWNSTREAM_PR_ROUTES = (
    "PR164",
    "PR165",
    "PR162R-C",
    "PR163-C",
    "PR166",
    "PR162E",
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


def normalize_repo_relative_ref(repo_root: Path, ref: Any, *, label: str = "PR163-B path") -> str:
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
