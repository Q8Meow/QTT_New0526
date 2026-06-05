"""Paths, branch guard, schemas, fixtures, and report names for PR162R-B."""

from __future__ import annotations

from pathlib import Path
import subprocess

from .authority_policy import EXPECTED_BRANCH, PR_ID


GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "pr162r_b_replay_paper_data_binding_completion"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
FIXTURE_DIR = Path(
    "tests/fixtures/stage1_prediction_markets/"
    "pr162r_b_replay_paper_data_binding_completion"
)
TEST_DIR = Path(
    "tests/stage1_prediction_markets/"
    "pr162r_b_replay_paper_data_binding_completion"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "pr162r_b_replay_paper_data_binding_completion"
)

SCHEMA_FILENAMES = (
    "BindingTaskV1.schema.json",
    "SourceAcquisitionCandidateV1.schema.json",
    "DatasetNormalizationReceiptV1.schema.json",
    "ReplayPaperDatasetBindingV1.schema.json",
    "ReplayHistoricalPriceSeriesBindingV1.schema.json",
    "ReplayOrderbookSnapshotBindingV1.schema.json",
    "ReplayTradePrintBindingV1.schema.json",
    "ReplayEventStateTimelineBindingV1.schema.json",
    "ReplaySettlementOutcomeBindingV1.schema.json",
    "ReplayFeeSlippageCostModelBindingV1.schema.json",
    "PaperMarketStateBindingV1.schema.json",
    "PaperSyntheticFillModelV1.schema.json",
    "PaperPortfolioStateFixtureV1.schema.json",
    "PaperExecutionCostModelV1.schema.json",
    "QuantumObjectiveInputBindingV1.schema.json",
    "QuantumConstraintInputBindingV1.schema.json",
    "QuantumComparatorDatasetBindingV1.schema.json",
    "ClassicalComparatorInputBindingV1.schema.json",
    "RowBindingResolutionV1.schema.json",
    "BindingReadinessDeltaV1.schema.json",
)

FIXTURE_FILENAMES = (
    "synthetic_binary_market_orderbook_1s.fixture.jsonl",
    "synthetic_binary_market_trade_prints.fixture.jsonl",
    "synthetic_event_state_timeline.fixture.jsonl",
    "synthetic_settlement_labels.fixture.jsonl",
    "synthetic_fee_slippage_model.fixture.json",
    "synthetic_latency_observations.fixture.jsonl",
    "synthetic_paper_market_state.fixture.json",
    "synthetic_paper_portfolio_state.fixture.json",
    "synthetic_paper_open_orders.fixture.json",
    "synthetic_paper_fill_events.fixture.jsonl",
    "synthetic_quantum_objective_inputs.fixture.json",
    "synthetic_quantum_constraints.fixture.json",
    "synthetic_classical_comparator_inputs.fixture.json",
)

REPORT_FILENAMES = (
    "PR162R_B_InputConsumptionAudit.report.json",
    "PR162R_B_PR162RMissingActionIngestionLedger.report.json",
    "PR162R_B_BindingActionFamilyCollapse.report.json",
    "PR162R_B_BindingTaskDeduplicationAudit.report.json",
    "PR162R_B_BindingFamilyCoveragePlan.report.json",
    "PR162R_B_DataBindingPriorityQueue.report.json",
    "PR162R_B_SourceAcquisitionCandidateRegistry.report.json",
    "PR162R_B_DatasetNormalizationReceiptRegistry.report.json",
    "PR162R_B_ReplayPaperDatasetBindingRegistry.report.json",
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
    "PR162R_B_QuantumObjectiveInputBindingRegistry.report.json",
    "PR162R_B_QuantumConstraintInputBindingRegistry.report.json",
    "PR162R_B_QuantumComparatorDatasetBindingRegistry.report.json",
    "PR162R_B_ClassicalComparatorInputBindingRegistry.report.json",
    "PR162R_B_FeatureCalculatorBindingRegistry.report.json",
    "PR162R_B_FeeSlippageLatencyBindingRegistry.report.json",
    "PR162R_B_VenueSpecificBindingMap.report.json",
    "PR162R_B_SourceCandidateToBindingMap.report.json",
    "PR162R_B_OnlineDatasetSourceScoutQueue.report.json",
    "PR162R_B_RowBindingResolutionMatrix.report.json",
    "PR162R_B_ReplayBindingFanoutMatrix.report.json",
    "PR162R_B_PaperBindingFanoutMatrix.report.json",
    "PR162R_B_QuantumBindingFanoutMatrix.report.json",
    "PR162R_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json",
    "PR162R_B_ReadinessDeltaVsPR162R.report.json",
    "PR162R_B_MissingActionReductionAudit.report.json",
    "PR162R_B_DatasetFamilyUnavailableReasons.report.json",
    "PR162R_B_LatencyBindingReadinessMatrix.report.json",
    "PR162R_B_PR163PaperAdapterHandoffUpdate.report.json",
    "PR162R_B_PR164ReviewProvenanceHandoffUpdate.report.json",
    "PR162R_B_PR165ScoringRankingHandoffUpdate.report.json",
    "PR162R_B_PR162EPluginBindingCompatibilityUpdate.report.json",
    "PR162R_B_OrphanBindingCandidateReportAudit.report.json",
    "PR162R_B_NoReplayPaperResultPacketAudit.report.json",
    "PR162R_B_NoLiveOrderProfitAuthorityAudit.report.json",
    "PR162R_B_NoSourceAcceptanceConnectorPrivateStateAudit.report.json",
    "PR162R_B_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR162R_B_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR162R_B_FinalSummary.report.json",
    "PR162R_B_DecisionAndNextPRRecommendation.report.json",
    "PR162R_B_ReportManifest.report.json",
)

REPORT_SCHEMA_REFS = {
    "PR162R_B_BindingTaskDeduplicationAudit.report.json": f"{SCHEMA_DIR.as_posix()}/BindingTaskV1.schema.json",
    "PR162R_B_SourceAcquisitionCandidateRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/SourceAcquisitionCandidateV1.schema.json",
    "PR162R_B_DatasetNormalizationReceiptRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/DatasetNormalizationReceiptV1.schema.json",
    "PR162R_B_ReplayPaperDatasetBindingRegistry.report.json": f"{SCHEMA_DIR.as_posix()}/ReplayPaperDatasetBindingV1.schema.json",
    "PR162R_B_RowBindingResolutionMatrix.report.json": f"{SCHEMA_DIR.as_posix()}/RowBindingResolutionV1.schema.json",
    "PR162R_B_ReadinessDeltaVsPR162R.report.json": f"{SCHEMA_DIR.as_posix()}/BindingReadinessDeltaV1.schema.json",
}

UPSTREAM_PR_REFS = (
    "PR136",
    "PR161F",
    "PR162",
    "PR162D",
    "PR162D_R1",
    "PR162R_A",
    "PR162D_R2A",
    "PR162R",
)
DOWNSTREAM_PR_ROUTES = (
    "PR163",
    "PR164",
    "PR165",
    "PR162E",
    "PR162Q",
    "PR162R-C",
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


def fixture_path(repo_root: Path, filename: str) -> Path:
    return repo_root / FIXTURE_DIR / filename
