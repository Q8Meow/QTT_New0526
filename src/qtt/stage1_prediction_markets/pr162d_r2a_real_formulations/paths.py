"""Paths and report names for PR162D-R2A."""

from __future__ import annotations

from pathlib import Path
import subprocess

from .authority_policy import EXPECTED_BRANCH, PR_ID


GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path("src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations")
SCHEMA_DIR = PACKAGE_DIR / "schemas"
SHARD_DIR = GENERATED_DIR / "pr162d_aggressive_qku_candidate_materialization_agent_routing_shards"
PACKAGE_IMPORT = "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations"

FORMULATION_RECORD_SCHEMA = "FormulationRecordV1.schema.json"
CANDIDATE_PACKET_SCHEMA = "CandidatePacketV1.schema.json"

REPORT_FILENAMES = (
    "PR162D_R2A_AuthorityBoundaryAudit.report.json",
    "PR162D_R2A_FormulationRecordRegistry.report.json",
    "PR162D_R2A_FormulaExpressionRegistry.report.json",
    "PR162D_R2A_AlgorithmProcedureRegistry.report.json",
    "PR162D_R2A_QuantumObjectiveRegistry.report.json",
    "PR162D_R2A_ClassicalComparatorRegistry.report.json",
    "PR162D_R2A_TestVectorRegistry.report.json",
    "PR162D_R2A_FamilySubfamilyVariantHierarchy.report.json",
    "PR162D_R2A_FormulationCoverageAudit.report.json",
    "PR162D_R2A_CandidatePacketV1Registry.report.json",
    "PR162D_R2A_PR162RGenericCandidateInputExtension.report.json",
    "PR162D_R2A_PR162EPluginSeedCandidateRegistry.report.json",
    "PR162D_R2A_ExactFieldFillActionQueue.report.json",
    "PR162D_R2A_RouteFillActionQueue.report.json",
    "PR162D_R2A_HumanReviewTopFormulations.report.json",
    "PR162D_R2A_FormulaLatencyClassRegistry.report.json",
    "PR162D_R2A_HotPathPrecomputeCacheabilityMatrix.report.json",
    "PR162D_R2A_LatencySensitiveCandidateQueue.report.json",
    "PR162D_R2A_UpstreamDownstreamQKUOrchestrationMatrix.report.json",
    "PR162D_R2A_QKUAgentWorkflowTraceabilityMatrix.report.json",
    "PR162D_R2A_CandidateIntakeLaneMatrix.report.json",
    "PR162D_R2A_FormulaPluginSeedRegistry.report.json",
    "PR162D_R2A_AlgorithmPluginSeedRegistry.report.json",
    "PR162D_R2A_QuantumPluginSeedRegistry.report.json",
    "PR162D_R2A_FormulaVersionAndRollbackSeedLedger.report.json",
    "PR162D_R2A_FormulaEquivalenceDedupeMatrix.report.json",
    "PR162D_R2A_MaterializationExpansionPriorityQueue.report.json",
    "PR162D_R2A_HighPriorityStage1ComputabilityQueue.report.json",
    "PR162D_R2A_QuantumPriorityMaterializationQueue.report.json",
    "PR162D_R2A_RouteFillPriorityQueue.report.json",
    "PR162D_R2A_OnlineSourceSearchQueue.report.json",
    "PR162D_R2A_ReportManifest.report.json",
    "PR162D_R2A_FinalSummary.report.json",
    "PR162D_R2A_DecisionGateRecommendation.report.json",
    "PR162D_R2A_NoPlaceholderOnlyCompletionAudit.report.json",
    "PR162D_R2A_NoMetadataOnlyCountedAsMaterializedAudit.report.json",
    "PR162D_R2A_NoProtectedArtifactMutationAudit.report.json",
    "PR162D_R2A_NoLiveOrderProfitReplayExecutionAudit.report.json",
    "PR162D_R2A_NoScatteredHardcodedAuthorityLiteralAudit.report.json",
)

HUMAN_REVIEW_MD = "PR162D_R2A_HumanReviewTopFormulations.report.md"

REPORT_SCHEMA_REFS = {
    filename: f"{SCHEMA_DIR.as_posix()}/{filename.replace('.report.json', '.schema.json')}"
    for filename in REPORT_FILENAMES
}

UPSTREAM_PR_REFS = ("PR136", "PR161F", "PR162D", "PR162D_R1", "PR162R_A")
DOWNSTREAM_PR_ROUTES = (
    "QKU_COMPUTE_ENGINE",
    "FORMULA_ALGORITHM_RUNTIME_CANDIDATE_LANE",
    "FEATURE_BUILDER",
    "PARAMETER_STACK_AGENT",
    "QUANTUM_ADVISORY_MAPPING_AGENT",
    "REPLAY_PAPER_CANDIDATE_ROUTER",
    "PR162R",
    "PR163",
    "PR164",
    "PR165",
    "PR162D_R2",
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


def resolve_repo_relative(repo_root: Path, ref: str | Path) -> Path:
    path = Path(ref)
    if path.is_absolute():
        return path
    return repo_root / path


def generated_path(repo_root: Path, filename: str) -> Path:
    return repo_root / GENERATED_DIR / filename


def schema_path(repo_root: Path, filename: str) -> Path:
    return repo_root / SCHEMA_DIR / filename


def ensure_branch(repo_root: Path) -> None:
    branch = current_branch(repo_root)
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"{PR_ID} build must run on {EXPECTED_BRANCH}; current branch is {branch}")
