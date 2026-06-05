"""Paths, branch guard, schemas, and report names for PR163."""

from __future__ import annotations

from pathlib import Path
import subprocess

from .authority_policy import EXPECTED_BRANCH, PR_ID


GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "pr163_generic_paper_adapter_capture_framework"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
SHARD_DIR = GENERATED_DIR / "pr163_shards"
TEST_DIR = Path(
    "tests/stage1_prediction_markets/"
    "pr163_generic_paper_adapter_capture_framework"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "pr163_generic_paper_adapter_capture_framework"
)

SCHEMA_FILENAMES = (
    "PaperAdapterInputV1.schema.json",
    "PaperDecisionIntentV1.schema.json",
    "PaperOrderIntentV1.schema.json",
    "PaperPreTradeCheckReceiptV1.schema.json",
    "PaperRiskPolicyReceiptV1.schema.json",
    "PaperOrderStateTransitionV1.schema.json",
    "PaperSyntheticFillEventV1.schema.json",
    "PaperPortfolioLedgerSnapshotV1.schema.json",
    "PaperCashReservationReceiptV1.schema.json",
    "PaperExecutionCostReceiptV1.schema.json",
    "PaperLatencySlippageReceiptV1.schema.json",
    "PaperCaptureEventV1.schema.json",
    "PaperAdapterRunPlanV1.schema.json",
    "PaperAdapterCaptureBundleV1.schema.json",
    "PaperVenueAdapterCapabilityV1.schema.json",
    "PaperScenarioCoverageV1.schema.json",
    "PaperLedgerInvariantAuditV1.schema.json",
    "PaperQuantumAdvisoryInputV1.schema.json",
    "PaperQuantumConstraintProjectionV1.schema.json",
    "PaperQuantumClassicalComparatorTraceV1.schema.json",
    "PaperQKUPrioritizationFeatureHandoffV1.schema.json",
    "PaperLLMFutureHandoffExclusionReceiptV1.schema.json",
    "PaperDownstreamHandoffV1.schema.json",
)

REPORT_FILENAMES = (
    "PR163_InputConsumptionAudit.report.json",
    "PR163_PR162RBArtifactConsumptionLedger.report.json",
    "PR163_PaperAdapterInputRegistry.report.json",
    "PR163_PaperVenueAdapterCapabilityMatrix.report.json",
    "PR163_PaperMarketStateNormalizationRegistry.report.json",
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
    "PR163_PaperScenarioCoverageMatrix.report.json",
    "PR163_PaperLedgerInvariantAudit.report.json",
    "PR163_PaperModeQKUFormulaAlgorithmAgentRoutingMatrix.report.json",
    "PR163_PaperQuantumAdvisoryInputRegistry.report.json",
    "PR163_PaperQuantumConstraintProjectionRegistry.report.json",
    "PR163_PaperQuantumClassicalComparatorTraceRegistry.report.json",
    "PR163_PaperHotPathExclusionMatrix.report.json",
    "PR163_PaperReplayParityPreparationMatrix.report.json",
    "PR163_PaperQKUPrioritizationFeatureHandoffRegistry.report.json",
    "PR163_PaperLLMFutureHandoffExclusionReceiptRegistry.report.json",
    "PR163_PR163BPairedReplayPaperExecutorHandoff.report.json",
    "PR163_PR164ReviewProvenanceHandoff.report.json",
    "PR163_PR165ScoringRankingHandoff.report.json",
    "PR163_PR166LLMReviewResearchHandoff.report.json",
    "PR163_PR162EPluginPaperAdapterCompatibilityUpdate.report.json",
    "PR163_SourceCandidatePaperAdapterResearchQueue.report.json",
    "PR163_NoPaperResultProfitLiveAuthorityAudit.report.json",
    "PR163_NoSourceAcceptanceConnectorPrivateStateAudit.report.json",
    "PR163_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR163_NoLLMHotPathOrderReleaseSourceAcceptanceResultRewriteAudit.report.json",
    "PR163_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR163_OrphanPaperAdapterArtifactAudit.report.json",
    "PR163_FinalSummary.report.json",
    "PR163_DecisionAndNextPRRecommendation.report.json",
    "PR163_ReportManifest.report.json",
)

REPORT_SCHEMA_REFS = {
    "PR163_PaperAdapterInputRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperAdapterInputV1.schema.json",
    "PR163_PaperDecisionIntentRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperDecisionIntentV1.schema.json",
    "PR163_PaperOrderIntentRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperOrderIntentV1.schema.json",
    "PR163_PaperPreTradeCheckReceiptRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperPreTradeCheckReceiptV1.schema.json",
    "PR163_PaperRiskPolicyReceiptRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperRiskPolicyReceiptV1.schema.json",
    "PR163_PaperOrderStateTransitionRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperOrderStateTransitionV1.schema.json",
    "PR163_PaperSyntheticFillEventRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperSyntheticFillEventV1.schema.json",
    "PR163_PaperPortfolioLedgerSnapshotRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperPortfolioLedgerSnapshotV1.schema.json",
    "PR163_PaperCashReservationReceiptRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperCashReservationReceiptV1.schema.json",
    "PR163_PaperExecutionCostReceiptRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperExecutionCostReceiptV1.schema.json",
    "PR163_PaperLatencySlippageReceiptRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperLatencySlippageReceiptV1.schema.json",
    "PR163_PaperCaptureEventRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperCaptureEventV1.schema.json",
    "PR163_PaperAdapterRunPlanRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperAdapterRunPlanV1.schema.json",
    "PR163_PaperAdapterCaptureBundleRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperAdapterCaptureBundleV1.schema.json",
    "PR163_PaperVenueAdapterCapabilityMatrix.report.json": f"{SCHEMA_DIR.as_posix()}/PaperVenueAdapterCapabilityV1.schema.json",
    "PR163_PaperScenarioCoverageMatrix.report.json": f"{SCHEMA_DIR.as_posix()}/PaperScenarioCoverageV1.schema.json",
    "PR163_PaperLedgerInvariantAudit.report.json": f"{SCHEMA_DIR.as_posix()}/PaperLedgerInvariantAuditV1.schema.json",
    "PR163_PaperQuantumAdvisoryInputRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperQuantumAdvisoryInputV1.schema.json",
    "PR163_PaperQuantumConstraintProjectionRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperQuantumConstraintProjectionV1.schema.json",
    "PR163_PaperQuantumClassicalComparatorTraceRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperQuantumClassicalComparatorTraceV1.schema.json",
    "PR163_PaperQKUPrioritizationFeatureHandoffRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperQKUPrioritizationFeatureHandoffV1.schema.json",
    "PR163_PaperLLMFutureHandoffExclusionReceiptRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/PaperLLMFutureHandoffExclusionReceiptV1.schema.json",
    "PR163_PR163BPairedReplayPaperExecutorHandoff.report.json": f"{SCHEMA_DIR.as_posix()}/PaperDownstreamHandoffV1.schema.json",
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
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "docs/master_plan/generated/PR161F_ReplayRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PaperRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PairedReplayPaperRunPlan.report.json",
    "docs/master_plan/generated/PR161F_ResultPacketEmissionEligibilityGate.report.json",
    "docs/master_plan/generated/PR162_ReplayDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162_PaperDataAdapterContract.report.json",
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
    "docs/master_plan/generated/PR162R_ReplayAdapterInputPacketRegistry.report.json",
    "docs/master_plan/generated/PR162R_PaperAdapterInputPacketRegistry.report.json",
    "docs/master_plan/generated/PR162R_ReplayRunRequestCandidateQueue.report.json",
    "docs/master_plan/generated/PR162R_PaperRunRequestCandidateQueue.report.json",
    "docs/master_plan/generated/PR162R_PairedReplayPaperRunRequestCandidatePlan.report.json",
    "docs/master_plan/generated/PR162R_QuantumBatchPrecomputeRoutingPlan.report.json",
    "docs/master_plan/generated/PR162R_LatencyPrecomputeRoutingMatrix.report.json",
    "docs/master_plan/generated/PR162R_QKUAgentReplayPaperHandoffMatrix.report.json",
    "docs/master_plan/generated/PR162R_PR163PaperAdapterHandoffSeed.report.json",
    "docs/master_plan/generated/PR162R_B_FinalSummary.report.json",
    "docs/master_plan/generated/PR162R_B_InputConsumptionAudit.report.json",
    "docs/master_plan/generated/PR162R_B_PaperMarketStateBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_PaperSyntheticFillModelRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_PaperPortfolioStateFixtureRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_PaperExecutionCostModelRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_PaperBindingFanoutMatrix.report.json",
    "docs/master_plan/generated/PR162R_B_RowBindingResolutionMatrix.report.json",
    "docs/master_plan/generated/PR162R_B_ReplayPaperDatasetBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_SourceAcquisitionCandidateRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_SourceCandidateToBindingMap.report.json",
    "docs/master_plan/generated/PR162R_B_DatasetNormalizationReceiptRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_FeeSlippageLatencyBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_FeatureCalculatorBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json",
    "docs/master_plan/generated/PR162R_B_QuantumObjectiveInputBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_QuantumConstraintInputBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_QuantumComparatorDatasetBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_ClassicalComparatorInputBindingRegistry.report.json",
    "docs/master_plan/generated/PR162R_B_PR163PaperAdapterHandoffUpdate.report.json",
    "docs/master_plan/generated/PR162R_B_PR164ReviewProvenanceHandoffUpdate.report.json",
    "docs/master_plan/generated/PR162R_B_PR165ScoringRankingHandoffUpdate.report.json",
    "docs/master_plan/generated/PR162R_B_PR162EPluginBindingCompatibilityUpdate.report.json",
    "docs/master_plan/generated/PR162R_B_ReportManifest.report.json",
)

PR162RB_REQUIRED_ARTIFACTS = (
    "PR162R_B_FinalSummary.report.json",
    "PR162R_B_PaperMarketStateBindingRegistry.report.json",
    "PR162R_B_PaperSyntheticFillModelRegistry.report.json",
    "PR162R_B_PaperPortfolioStateFixtureRegistry.report.json",
    "PR162R_B_PaperExecutionCostModelRegistry.report.json",
    "PR162R_B_PaperBindingFanoutMatrix.report.json",
    "PR162R_B_RowBindingResolutionMatrix.report.json",
    "PR162R_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json",
    "PR162R_B_QuantumObjectiveInputBindingRegistry.report.json",
    "PR162R_B_QuantumConstraintInputBindingRegistry.report.json",
    "PR162R_B_QuantumComparatorDatasetBindingRegistry.report.json",
    "PR162R_B_FeeSlippageLatencyBindingRegistry.report.json",
)

UPSTREAM_PR_REFS = (
    "PR136",
    "PR161F",
    "PR162",
    "PR162D",
    "PR162D_R1",
    "PR162R_A",
    "PR162D_R2A",
    "PR162R",
    "PR162R-B",
)
DOWNSTREAM_PR_ROUTES = ("PR163-B", "PR164", "PR165", "PR166", "PR162E", "PR162R-C")


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
