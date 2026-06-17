"""Constants for PR166-QC quantum-selected replay/paper retest evidence."""

from __future__ import annotations

from pathlib import Path

PR_ID = "PR166-QC"
BASE_BRANCH = "main"
EXPECTED_BRANCH = "pr166-qc-quantum-selected-replay-paper-retest"
CREATED_AT_UTC = "2026-06-17T00:00:00Z"
AUTHORITY_CLASS = "PR166_QC_NONLIVE_REPLAY_PAPER_EVIDENCE_ONLY"
AUTHORITY_BOUNDARY_REF = (
    "PR166_QC_AUTHORITY_BOUNDARY::NONLIVE_REPLAY_PAPER_NO_LIVE_"
    "NO_SOURCE_TRUTH_CONNECTOR_CASH_PROFIT_CLOUD_OR_ADVANTAGE"
)
VALIDATION_STATUS = "PASS"
VALIDATOR_REF = "tools/validate_pr166_qc_quantum_selected_replay_paper_retest.py"
BUILDER_REF = "tools/build_pr166_qc_quantum_selected_replay_paper_retest.py"
MANIFEST_REF = "PR166_QC_ReportManifest.report.json"
NOT_APPLICABLE = "NOT_APPLICABLE_FOR_THIS_ROW"
NOT_TERMINAL_REASON = "ROW_CONTINUES_TO_DECLARED_DOWNSTREAM_ROUTE"

GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr166_qc_shards"
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "pr166_qc_quantum_selected_replay_paper_retest"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
TEST_DIR = Path(
    "tests/stage1_prediction_markets/"
    "pr166_qc_quantum_selected_replay_paper_retest"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "pr166_qc_quantum_selected_replay_paper_retest"
)
DEFAULT_SHARD_ROW_TARGET = 750

STRICT_INPUT_REPORTS: tuple[str, ...] = (
    "PR166_QB_To_PR166_QC.report.json",
    "PR166_QB_InputConsumption.report.json",
    "PR166_QB_BudgetPolicy.report.json",
    "PR166_QB_SourceBenchmarkParams.report.json",
    "PR166_QB_Eligibility.report.json",
    "PR166_QB_SubsetSelection.report.json",
    "PR166_QB_FairnessNorm.report.json",
    "PR166_QB_ClassicalReceipt.report.json",
    "PR166_QB_QInspiredReceipt.report.json",
    "PR166_QB_AnnealTabuReceipt.report.json",
    "PR166_QB_QAOAReceipt.report.json",
    "PR166_QB_SamplingVQEReceipt.report.json",
    "PR166_QB_QUBOReceipt.report.json",
    "PR166_QB_BQMReceipt.report.json",
    "PR166_QB_IsingReceipt.report.json",
    "PR166_QB_CQMReceipt.report.json",
    "PR166_QB_DQMReceipt.report.json",
    "PR166_QB_QuadProgramReceipt.report.json",
    "PR166_QB_ObjectiveQuality.report.json",
    "PR166_QB_RuntimeLatency.report.json",
    "PR166_QB_SeedStability.report.json",
    "PR166_QB_TCARanking.report.json",
    "PR166_QB_OverfitPenalty.report.json",
    "PR166_QB_PortfolioUtility.report.json",
    "PR166_QB_ChampChallenger.report.json",
    "PR166_QB_RegimeMemory.report.json",
    "PR166_QB_RaceLedger.report.json",
    "PR166_QB_RaceArb.report.json",
    "PR166_QB_BackendReadyNoExec.report.json",
    "PR166_QB_CloudSwitchReady.report.json",
    "PR166_QB_OwnerQuantumControlReady.report.json",
    "PR166_QB_MarketPortability.report.json",
    "PR166_QB_DependencyLedger.report.json",
    "PR166_QB_QuantumRepairLab.report.json",
    "PR166_QB_AgentWorkOrders.report.json",
    "PR166_QB_AgentDAG.report.json",
    "PR166_QB_NoOrphanProof.report.json",
    "PR166_QB_ArtifactMap.report.json",
    "PR166_QB_To_PR162E_Q.report.json",
    "PR166_QB_To_PR167.report.json",
    "PR166_QB_To_PR162E.report.json",
    "PR166_QB_To_PR162F.report.json",
    "PR166_QB_To_CloudSwitchboard.report.json",
    "PR166_QB_To_OwnerDashboard.report.json",
    "PR166_QB_FinalSummary.report.json",
    "PR166_QB_ReportManifest.report.json",
    "PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json",
    "PR166_Q_PR166_QC_QuantumSelectedReplayPaperRetestHandoff.report.json",
    "PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "PR165_D2_AgentDutySourceCrosswalk.report.json",
)

EXPECTED_559_INPUTS: tuple[str, ...] = tuple(
    name
    for name in STRICT_INPUT_REPORTS
    if name
    not in {
        "PR166_QB_InputConsumption.report.json",
        "PR166_QB_BudgetPolicy.report.json",
        "PR166_QB_SourceBenchmarkParams.report.json",
        "PR166_QB_CloudSwitchReady.report.json",
        "PR166_QB_OwnerQuantumControlReady.report.json",
        "PR166_QB_DependencyLedger.report.json",
        "PR166_QB_ArtifactMap.report.json",
        "PR166_QB_FinalSummary.report.json",
        "PR166_QB_ReportManifest.report.json",
        "PR165_D2_AgentRosterDiscoveryAudit.report.json",
        "PR165_D2_AgentDutySourceCrosswalk.report.json",
    }
)

REPORT_FILENAMES: tuple[str, ...] = (
    "PR166_QC_SourceReplayParams.report.json",
    "PR166_QC_InputConsumption.report.json",
    "PR166_QC_RetestBudget.report.json",
    "PR166_QC_RetestEligibility.report.json",
    "PR166_QC_SubsetSelection.report.json",
    "PR166_QC_ReplayEvidence.report.json",
    "PR166_QC_PaperEvidence.report.json",
    "PR166_QC_EvidenceQuality.report.json",
    "PR166_QC_CalibrationEvidence.report.json",
    "PR166_QC_ReplayPaperDivergence.report.json",
    "PR166_QC_TCAEvidence.report.json",
    "PR166_QC_FillNoFillEvidence.report.json",
    "PR166_QC_LatencyEvidence.report.json",
    "PR166_QC_QueueRiskEvidence.report.json",
    "PR166_QC_CapacityCrowdingEvidence.report.json",
    "PR166_QC_OverfitFDRRetest.report.json",
    "PR166_QC_RegimeEvidence.report.json",
    "PR166_QC_ScenarioMemory.report.json",
    "PR166_QC_ExecutionAdjustedRanking.report.json",
    "PR166_QC_PortfolioUtility.report.json",
    "PR166_QC_ChampChallengerPaper.report.json",
    "PR166_QC_StillNegativeAfterCosts.report.json",
    "PR166_QC_ReplayPaperRepairLab.report.json",
    "PR166_QC_QuantumRepairRetest.report.json",
    "PR166_QC_AutomapperNeeds.report.json",
    "PR166_QC_OwnerDashboardReview.report.json",
    "PR166_QC_BenchmarkOnlyResidual.report.json",
    "PR166_QC_OpenTradeSimHandoff.report.json",
    "PR166_QC_PaperPromotionCandidate.report.json",
    "PR166_QC_ReportConsumerCrosswalk.report.json",
    "PR166_QC_ConnectorRouteReadiness.report.json",
    "PR166_QC_NoLiveAuthorityBoundary.report.json",
    "PR166_QC_MarketPortability.report.json",
    "PR166_QC_AgentWorkOrders.report.json",
    "PR166_QC_AgentDAG.report.json",
    "PR166_QC_NoOrphanProof.report.json",
    "PR166_QC_ArtifactMap.report.json",
    "PR166_QC_To_PR162E_Q.report.json",
    "PR166_QC_To_PR167.report.json",
    "PR166_QC_To_PR162E.report.json",
    "PR166_QC_To_PR162F.report.json",
    "PR166_QC_To_OwnerDashboard.report.json",
    "PR166_QC_To_CloudSwitchboard.report.json",
    "PR166_QC_To_FutureConnectors.report.json",
    "PR166_QC_FinalSummary.report.json",
    "PR166_QC_ReportManifest.report.json",
)

ROW_REPORTS: frozenset[str] = frozenset(
    {
        "PR166_QC_RetestEligibility.report.json",
        "PR166_QC_SubsetSelection.report.json",
        "PR166_QC_ReplayEvidence.report.json",
        "PR166_QC_PaperEvidence.report.json",
        "PR166_QC_EvidenceQuality.report.json",
        "PR166_QC_CalibrationEvidence.report.json",
        "PR166_QC_ReplayPaperDivergence.report.json",
        "PR166_QC_TCAEvidence.report.json",
        "PR166_QC_FillNoFillEvidence.report.json",
        "PR166_QC_LatencyEvidence.report.json",
        "PR166_QC_QueueRiskEvidence.report.json",
        "PR166_QC_CapacityCrowdingEvidence.report.json",
        "PR166_QC_OverfitFDRRetest.report.json",
        "PR166_QC_RegimeEvidence.report.json",
        "PR166_QC_ScenarioMemory.report.json",
        "PR166_QC_ExecutionAdjustedRanking.report.json",
        "PR166_QC_PortfolioUtility.report.json",
        "PR166_QC_ChampChallengerPaper.report.json",
        "PR166_QC_StillNegativeAfterCosts.report.json",
        "PR166_QC_ReplayPaperRepairLab.report.json",
        "PR166_QC_QuantumRepairRetest.report.json",
        "PR166_QC_AutomapperNeeds.report.json",
        "PR166_QC_OwnerDashboardReview.report.json",
        "PR166_QC_BenchmarkOnlyResidual.report.json",
        "PR166_QC_OpenTradeSimHandoff.report.json",
        "PR166_QC_PaperPromotionCandidate.report.json",
        "PR166_QC_ConnectorRouteReadiness.report.json",
        "PR166_QC_MarketPortability.report.json",
        "PR166_QC_AgentWorkOrders.report.json",
        "PR166_QC_AgentDAG.report.json",
        "PR166_QC_NoOrphanProof.report.json",
        "PR166_QC_To_PR162E_Q.report.json",
        "PR166_QC_To_PR167.report.json",
        "PR166_QC_To_PR162E.report.json",
        "PR166_QC_To_PR162F.report.json",
        "PR166_QC_To_OwnerDashboard.report.json",
        "PR166_QC_To_CloudSwitchboard.report.json",
        "PR166_QC_To_FutureConnectors.report.json",
    }
)

SUMMARY_REPORTS: frozenset[str] = frozenset(
    name for name in REPORT_FILENAMES if name not in ROW_REPORTS
)

EVIDENCE_DISPOSITIONS: tuple[str, ...] = (
    "REPLAY_EVIDENCE_COMPUTED_BOUNDED",
    "PAPER_EVIDENCE_COMPUTED_BOUNDED",
    "REPLAY_AND_PAPER_EVIDENCE_COMPUTED_BOUNDED",
    "REPLAY_STRUCTURAL_ONLY_DATA_UNAVAILABLE",
    "PAPER_STRUCTURAL_ONLY_RUNTIME_CAP",
    "EVIDENCE_ROUTED_TO_PR162E_Q_AUTOMAPPER",
    "EVIDENCE_ROUTED_TO_OWNER_DASHBOARD_REVIEW",
    "EVIDENCE_ROUTED_TO_PR167_OPEN_TRADE_SIMULATOR",
    "EVIDENCE_ROUTED_TO_PR162E_PLUGIN_FRAMEWORK",
    "EVIDENCE_ROUTED_TO_PR162F_OWNER_AGENT_INTAKE",
    "EVIDENCE_ROUTED_TO_DATA_GAP_REPAIR",
    "EVIDENCE_REMAINS_BENCHMARK_ONLY",
    "EVIDENCE_REPAIR_PROPOSAL_CREATED",
    "EVIDENCE_ROUTED_TO_FUTURE_CONNECTOR_NO_BINDING",
    "EXCLUDED_UNSAFE_OR_IMPOSSIBLE_WITH_EXACT_REASON",
)

FORBIDDEN_EVIDENCE_DISPOSITIONS: tuple[str, ...] = (
    "METADATA_ONLY_EVIDENCED",
    "FUTURE_CONSUMER_NOTE_ONLY_EVIDENCED",
    "PLACEHOLDER_EVIDENCED",
    "UNKNOWN_BUT_PASS",
    "UNBOUNDED_REPLAY_EXECUTED",
    "UNBOUNDED_PAPER_EXECUTED",
    "LIVE_ORDER_EXECUTED",
    "CLOUD_BACKEND_EXECUTED",
    "PROFIT_EVIDENCE_CREATED",
    "LIVE_READY_CLAIMED",
    "SOURCE_TRUTH_ACCEPTED",
    "CONNECTOR_BOUND",
)

EVIDENCE_QUALITY_GRADES: tuple[str, ...] = (
    "A_REPLAY_AND_PAPER_STRONG_NONLIVE",
    "B_REPLAY_STRONG_PAPER_PENDING",
    "C_PAPER_READY_STRUCTURAL",
    "D_RETEST_REQUIRED",
    "E_STILL_NEGATIVE_AFTER_COSTS",
    "F_INSUFFICIENT_DATA_ROUTE_REQUIRED",
    "G_BENCHMARK_ONLY_RESIDUAL",
)

EVIDENCE_LANES: tuple[str, ...] = (
    "REPLAY_CHAMPION_CANDIDATE",
    "REPLAY_CHALLENGER_CANDIDATE",
    "REPLAY_WATCH_CANDIDATE",
    "PAPER_CHAMPION_CANDIDATE",
    "PAPER_CHALLENGER_CANDIDATE",
    "PAPER_WATCH_CANDIDATE",
    "REPLAY_RETEST_REQUIRED",
    "PAPER_RETEST_REQUIRED",
    "STILL_NEGATIVE_AFTER_TCA_LATENCY_FILL_RISK",
    "REPLAY_PAPER_REPAIR_PROPOSAL",
    "AUTOMAPPER_NEEDED",
    "OWNER_DASHBOARD_REVIEW_NEEDED",
    "BENCHMARK_ONLY_RESIDUAL",
    "OPEN_TRADE_SIM_READY",
    "DATA_GAP_REPAIR_NEEDED",
    "PLUGIN_FRAMEWORK_NEEDED",
    "OWNER_AGENT_INTAKE_NEEDED",
    "FUTURE_CONNECTOR_ROUTE_NEEDED_NO_BINDING",
    "NO_TRADE_NONLIVE",
)

RETEST_CAPS: dict[str, int] = {
    "max_actual_replay_paper_rows_default_ci": 64,
    "max_rows_per_role_default_ci": 16,
    "max_walk_forward_slices_default_ci": 4,
    "max_scenario_states_default_ci": 16,
    "max_market_book_states_default_ci": 16,
    "max_random_seeds_default_ci": 3,
    "max_retest_iterations_default_ci": 64,
}

MODEL_FAMILIES: tuple[str, ...] = (
    "QUBO",
    "BQM",
    "Ising",
    "CQM",
    "DQM",
    "QuadraticProgram",
)

FUTURE_MARKET_FAMILIES: tuple[str, ...] = (
    "prediction_market",
    "equity",
    "option",
    "futures",
    "crypto",
    "fx",
    "rates",
    "commodity",
    "other",
)

DOWNSTREAM_PR_REFS: tuple[str, ...] = (
    "PR162E-Q",
    "PR167",
    "PR162E",
    "PR162F",
    "FUTURE_OWNER_DASHBOARD_REVIEW",
    "FUTURE_CLOUD_SWITCHBOARD_ENABLEMENT",
    "FUTURE_CONNECTOR_ROUTES_NO_BINDING",
)

AGENT_IDS: tuple[str, ...] = (
    "Commander",
    "Governance",
    "Research Agent",
    "Source/External Scout Agent",
    "QKU/Formula Materialization Agent",
    "Quantum Optimizer / Quantum Benchmark Agent",
    "Quantum Comparator Agent",
    "Classical Comparator Agent",
    "Portfolio/Risk Agent",
    "Execution/TCA Agent",
    "Replay Agent",
    "Paper Agent",
    "Open Trade Simulator Agent",
    "Dashboard/Owner Review Agent",
    "Quantum AutoMapper Agent",
    "Quantum Cloud Switchboard Agent",
    "Owner Dashboard Control Agent",
    "Race Arbitration Agent",
    "Connector Readiness Agent",
    "External Acquisition Agent",
)
