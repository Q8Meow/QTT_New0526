"""Paths, branch guard, and report names for PR162R."""

from __future__ import annotations

from pathlib import Path
import subprocess

from .authority_policy import EXPECTED_BRANCH, PR_ID


GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets.pr162r_generic_replay_paper_adapter_rerun"
)

SCHEMA_FILENAMES = (
    "ReplayPaperAdapterInputV1.schema.json",
    "ReplayRunRequestCandidateV1.schema.json",
    "PaperRunRequestCandidateV1.schema.json",
    "QKUComputabilityRouteV1.schema.json",
    "MissingBindingActionV1.schema.json",
    "QuantumBatchPrecomputeRouteV1.schema.json",
    "SourceCandidateMaterializationV1.schema.json",
)

REPORT_FILENAMES = (
    "PR162R_InputConsumptionAudit.report.json",
    "PR162R_CandidatePacketV1IngestionLedger.report.json",
    "PR162R_CandidatePacketSchemaCompatibilityAudit.report.json",
    "PR162R_QKUComputabilityClassificationMatrix.report.json",
    "PR162R_QKUNonPlaceholderCompletionAudit.report.json",
    "PR162R_FormulationCallableImportAudit.report.json",
    "PR162R_FormulationSmokeExecutionLedger.report.json",
    "PR162R_SourceCandidateMaterializationQueue.report.json",
    "PR162R_OnlineSourceScoutQueue.report.json",
    "PR162R_ReplayPaperDataBindingRequirementMatrix.report.json",
    "PR162R_MissingDataBindingActionQueue.report.json",
    "PR162R_ReplayAdapterInputPacketRegistry.report.json",
    "PR162R_PaperAdapterInputPacketRegistry.report.json",
    "PR162R_ReplayRunRequestCandidateQueue.report.json",
    "PR162R_PaperRunRequestCandidateQueue.report.json",
    "PR162R_PairedReplayPaperRunRequestCandidatePlan.report.json",
    "PR162R_QuantumBatchPrecomputeRoutingPlan.report.json",
    "PR162R_LatencyPrecomputeRoutingMatrix.report.json",
    "PR162R_RouteTriageCrosswalkConsumptionAudit.report.json",
    "PR162R_MarketSpecificQKUAdapterIndex.report.json",
    "PR162R_CommandActionQKUBindingMatrix.report.json",
    "PR162R_QKUAgentReplayPaperHandoffMatrix.report.json",
    "PR162R_PR163PaperAdapterHandoffSeed.report.json",
    "PR162R_PR164ReviewProvenanceHandoffSeed.report.json",
    "PR162R_PR165ScoringRankingHandoffSeed.report.json",
    "PR162R_PR162EPluginReplayPaperCompatibilitySeed.report.json",
    "PR162R_OrphanCandidateReportAudit.report.json",
    "PR162R_NoReplayPaperResultPacketAudit.report.json",
    "PR162R_NoLiveOrderProfitAuthorityAudit.report.json",
    "PR162R_NoSourceAcceptanceConnectorPrivateStateAudit.report.json",
    "PR162R_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR162R_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR162R_Old548CompatibilityTrace.report.json",
    "PR162R_FinalSummary.report.json",
    "PR162R_DecisionAndNextPRRecommendation.report.json",
    "PR162R_ReportManifest.report.json",
)

UPSTREAM_PR_REFS = ("PR136", "PR161F", "PR162", "PR162D", "PR162D_R1", "PR162R_A", "PR162D_R2A")
DOWNSTREAM_PR_ROUTES = ("PR163", "PR164", "PR165", "PR162E", "PR162D_R2", "PR162Q")

REPORT_SCHEMA_REFS = {
    "PR162R_QKUComputabilityClassificationMatrix.report.json": f"{SCHEMA_DIR.as_posix()}/QKUComputabilityRouteV1.schema.json",
    "PR162R_MissingDataBindingActionQueue.report.json": f"{SCHEMA_DIR.as_posix()}/MissingBindingActionV1.schema.json",
    "PR162R_ReplayAdapterInputPacketRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperAdapterInputV1.schema.json",
    "PR162R_PaperAdapterInputPacketRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperAdapterInputV1.schema.json",
    "PR162R_ReplayRunRequestCandidateQueue.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayRunRequestCandidateV1.schema.json",
    "PR162R_PaperRunRequestCandidateQueue.report.json": f"{SCHEMA_DIR.as_posix()}/PaperRunRequestCandidateV1.schema.json",
    "PR162R_QuantumBatchPrecomputeRoutingPlan.report.json": f"{SCHEMA_DIR.as_posix()}/QuantumBatchPrecomputeRouteV1.schema.json",
    "PR162R_SourceCandidateMaterializationQueue.report.json": f"{SCHEMA_DIR.as_posix()}/SourceCandidateMaterializationV1.schema.json",
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
        raise RuntimeError(f"{PR_ID} build must run on {EXPECTED_BRANCH}; current branch is {branch}")


def generated_path(repo_root: Path, filename: str) -> Path:
    return repo_root / GENERATED_DIR / filename


def schema_path(repo_root: Path, filename: str) -> Path:
    return repo_root / SCHEMA_DIR / filename
