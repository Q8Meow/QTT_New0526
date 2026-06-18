"""Constants for PR162E-Q quantum automapper."""

from __future__ import annotations

from pathlib import Path

PR_ID = "PR162E-Q"
BASE_BRANCH = "main"
EXPECTED_BRANCH = "pr162e-q-quantum-automapper"
CREATED_AT_UTC = "2026-06-17T00:00:00Z"
AUTHORITY_CLASS = "PR162E_Q_NONLIVE_QUANTUM_AUTOMAPPER_ONLY"
AUTHORITY_BOUNDARY_REF = (
    "PR162E_Q_AUTHORITY_BOUNDARY::NONLIVE_MAPPING_NO_LIVE_NO_SOURCE_TRUTH_"
    "NO_CONNECTOR_CASH_PROFIT_CLOUD_BACKEND_OR_ADVANTAGE"
)
VALIDATION_STATUS = "PASS"
VALIDATOR_REF = "tools/validate_pr162e_q_quantum_automapper.py"
BUILDER_REF = "tools/build_pr162e_q_quantum_automapper.py"
MANIFEST_REF = "PR162E_Q_ReportManifest.report.json"
NOT_APPLICABLE = "NOT_APPLICABLE_FOR_THIS_ROW"
NOT_TERMINAL_REASON = "ROW_CONTINUES_TO_DECLARED_DOWNSTREAM_ROUTE"

GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr162e_q_shards"
PACKAGE_DIR = Path("src/qtt/stage1_prediction_markets/pr162e_q_quantum_automapper")
SCHEMA_DIR = PACKAGE_DIR / "schemas"
TEST_DIR = Path("tests/stage1_prediction_markets/pr162e_q_quantum_automapper")
PACKAGE_IMPORT = "src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper"
DEFAULT_SHARD_ROW_TARGET = 750

STRICT_INPUT_REPORTS: tuple[str, ...] = (
    "PR166_QC_To_PR162E_Q.report.json",
    "PR166_QC_AutomapperNeeds.report.json",
    "PR166_QC_ReplayPaperRepairLab.report.json",
    "PR166_QC_StillNegativeAfterCosts.report.json",
    "PR166_QC_PaperPromotionCandidate.report.json",
    "PR166_QC_ChampChallengerPaper.report.json",
    "PR166_QC_OpenTradeSimHandoff.report.json",
    "PR166_QC_BenchmarkOnlyResidual.report.json",
    "PR166_QC_OwnerDashboardReview.report.json",
    "PR166_QC_ConnectorRouteReadiness.report.json",
    "PR166_QC_ExecutionAdjustedRanking.report.json",
    "PR166_QC_TCAEvidence.report.json",
    "PR166_QC_FillNoFillEvidence.report.json",
    "PR166_QC_LatencyEvidence.report.json",
    "PR166_QC_QueueRiskEvidence.report.json",
    "PR166_QC_CapacityCrowdingEvidence.report.json",
    "PR166_QC_OverfitFDRRetest.report.json",
    "PR166_QC_RegimeEvidence.report.json",
    "PR166_QC_ScenarioMemory.report.json",
    "PR166_QC_PortfolioUtility.report.json",
    "PR166_QC_ReportConsumerCrosswalk.report.json",
    "PR166_QC_ArtifactMap.report.json",
    "PR166_QC_AgentWorkOrders.report.json",
    "PR166_QC_AgentDAG.report.json",
    "PR166_QC_NoOrphanProof.report.json",
    "PR166_QC_ReportManifest.report.json",
    "PR166_QC_FinalSummary.report.json",
    "PR166_QB_QUBOReceipt.report.json",
    "PR166_QB_BQMReceipt.report.json",
    "PR166_QB_IsingReceipt.report.json",
    "PR166_QB_CQMReceipt.report.json",
    "PR166_QB_DQMReceipt.report.json",
    "PR166_QB_QuadProgramReceipt.report.json",
    "PR166_QB_ClassicalReceipt.report.json",
    "PR166_QB_QuantumRepairLab.report.json",
    "PR166_QB_RaceArb.report.json",
    "PR166_QB_ArtifactMap.report.json",
    "PR166_QB_ReportManifest.report.json",
    "PR166_QB_FinalSummary.report.json",
    "PR166_Q_QuantumStructuralReadiness.report.json",
    "PR166_Q_QUBOReadinessRegistry.report.json",
    "PR166_Q_BQMReadinessRegistry.report.json",
    "PR166_Q_IsingReadinessRegistry.report.json",
    "PR166_Q_CQMReadinessRegistry.report.json",
    "PR166_Q_DQMReadinessRegistry.report.json",
    "PR166_Q_QuadraticProgramReadinessRegistry.report.json",
    "PR166_Q_ObjectiveVariableConstraintPenaltyMap.report.json",
    "PR166_Q_QuantumClassicalHybridRaceLedger.report.json",
    "PR166_Q_UniversalArtifactConsumerMap.report.json",
    "PR166_Q_NoOrphanProof.report.json",
    "PR166_Q_ReportManifest.report.json",
    "PR166_Q_FinalSummary.report.json",
    "PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "PR165_D2_AgentDutySourceCrosswalk.report.json",
)
EXPECTED_559_INPUTS: tuple[str, ...] = tuple(
    name
    for name in STRICT_INPUT_REPORTS
    if name
    not in {
        "PR166_QC_ReportConsumerCrosswalk.report.json",
        "PR166_QC_ArtifactMap.report.json",
        "PR166_QC_ReportManifest.report.json",
        "PR166_QC_FinalSummary.report.json",
        "PR166_QB_ArtifactMap.report.json",
        "PR166_QB_ReportManifest.report.json",
        "PR166_QB_FinalSummary.report.json",
        "PR166_Q_UniversalArtifactConsumerMap.report.json",
        "PR166_Q_ReportManifest.report.json",
        "PR166_Q_FinalSummary.report.json",
        "PR165_D2_AgentRosterDiscoveryAudit.report.json",
        "PR165_D2_AgentDutySourceCrosswalk.report.json",
    }
)

REPORT_FILENAMES: tuple[str, ...] = (
    "PR162E_Q_InputConsumption.report.json",
    "PR162E_Q_UpstreamReportUse.report.json",
    "PR162E_Q_SourceMapParams.report.json",
    "PR162E_Q_MapBudget.report.json",
    "PR162E_Q_MapEligibility.report.json",
    "PR162E_Q_FormulaObjectiveCanonical.report.json",
    "PR162E_Q_UnitNorm.report.json",
    "PR162E_Q_ModelFamilySelection.report.json",
    "PR162E_Q_ObjectiveMap.report.json",
    "PR162E_Q_VariableEncoding.report.json",
    "PR162E_Q_SolutionInterpretBack.report.json",
    "PR162E_Q_ConstraintMap.report.json",
    "PR162E_Q_PenaltyMap.report.json",
    "PR162E_Q_CoeffScaling.report.json",
    "PR162E_Q_QUBORecipe.report.json",
    "PR162E_Q_BQMRecipe.report.json",
    "PR162E_Q_IsingRecipe.report.json",
    "PR162E_Q_CQMRecipe.report.json",
    "PR162E_Q_DQMRecipe.report.json",
    "PR162E_Q_QuadProgramRecipe.report.json",
    "PR162E_Q_HybridRecipe.report.json",
    "PR162E_Q_TestVectors.report.json",
    "PR162E_Q_MapProof.report.json",
    "PR162E_Q_FeasibilityChecks.report.json",
    "PR162E_Q_ComplexityEstimate.report.json",
    "PR162E_Q_SparsityEmbedding.report.json",
    "PR162E_Q_MapQuality.report.json",
    "PR162E_Q_MapSensitivityStress.report.json",
    "PR162E_Q_EdgeAttribution.report.json",
    "PR162E_Q_MapFairnessNorm.report.json",
    "PR162E_Q_ExecutionAdjustedMapRank.report.json",
    "PR162E_Q_TCAMapImpact.report.json",
    "PR162E_Q_OverfitFDRMapRisk.report.json",
    "PR162E_Q_PortfolioUtilityMap.report.json",
    "PR162E_Q_ChampChallengerMap.report.json",
    "PR162E_Q_RegimeMapMemory.report.json",
    "PR162E_Q_StillNegativeMapRepair.report.json",
    "PR162E_Q_ReplayPaperRetestMap.report.json",
    "PR162E_Q_OpenTradeSimMap.report.json",
    "PR162E_Q_OwnerDashboardMapReview.report.json",
    "PR162E_Q_ConnectorRouteReady.report.json",
    "PR162E_Q_MarketPortability.report.json",
    "PR162E_Q_ReportConsumerCrosswalk.report.json",
    "PR162E_Q_AgentWorkOrders.report.json",
    "PR162E_Q_AgentDAG.report.json",
    "PR162E_Q_NoOrphanProof.report.json",
    "PR162E_Q_ArtifactMap.report.json",
    "PR162E_Q_To_PR166_QC_Retest.report.json",
    "PR162E_Q_To_PR167.report.json",
    "PR162E_Q_To_PR162E.report.json",
    "PR162E_Q_To_PR162F.report.json",
    "PR162E_Q_To_OwnerDashboard.report.json",
    "PR162E_Q_To_CloudSwitchboard.report.json",
    "PR162E_Q_To_FutureConnectors.report.json",
    "PR162E_Q_FinalSummary.report.json",
    "PR162E_Q_ReportManifest.report.json",
)

ROW_REPORTS: frozenset[str] = frozenset(
    name
    for name in REPORT_FILENAMES
    if name
    not in {
        "PR162E_Q_InputConsumption.report.json",
        "PR162E_Q_UpstreamReportUse.report.json",
        "PR162E_Q_SourceMapParams.report.json",
        "PR162E_Q_MapBudget.report.json",
        "PR162E_Q_ReportConsumerCrosswalk.report.json",
        "PR162E_Q_ArtifactMap.report.json",
        "PR162E_Q_FinalSummary.report.json",
        "PR162E_Q_ReportManifest.report.json",
    }
)

SUMMARY_REPORTS: frozenset[str] = frozenset(name for name in REPORT_FILENAMES if name not in ROW_REPORTS)

AUTOMAPPER_DISPOSITIONS: tuple[str, ...] = (
    "MAPPED_QUBO_COMPUTABLE",
    "MAPPED_BQM_COMPUTABLE",
    "MAPPED_ISING_COMPUTABLE",
    "MAPPED_CQM_COMPUTABLE",
    "MAPPED_DQM_COMPUTABLE",
    "MAPPED_QUADRATIC_PROGRAM_COMPUTABLE",
    "MAPPED_HYBRID_MULTI_MODEL_COMPUTABLE",
    "PARTIAL_MAP_WITH_EXACT_FILL_ACTION",
    "MAP_REPAIR_PROPOSAL_CREATED",
    "MAP_ROUTED_TO_PR166_QC_REPLAY_PAPER_RETEST",
    "MAP_ROUTED_TO_PR167_OPEN_TRADE_SIMULATOR",
    "MAP_ROUTED_TO_PR162E_PLUGIN_FRAMEWORK",
    "MAP_ROUTED_TO_PR162F_OWNER_AGENT_INTAKE",
    "MAP_ROUTED_TO_OWNER_DASHBOARD_REVIEW",
    "MAP_ROUTED_TO_DATA_GAP_REPAIR",
    "MAP_ROUTED_TO_FUTURE_CONNECTOR_NO_BINDING",
    "MAP_REMAINS_STRUCTURAL_ONLY",
    "EXCLUDED_UNSAFE_OR_IMPOSSIBLE_WITH_EXACT_REASON",
)

FORBIDDEN_AUTOMAPPER_DISPOSITIONS: tuple[str, ...] = (
    "METADATA_ONLY_MAPPED",
    "FUTURE_CONSUMER_NOTE_ONLY_MAPPED",
    "SOLVER_LABEL_ONLY_MAPPED",
    "PLACEHOLDER_MAPPED",
    "RECIPE_LABEL_ONLY_MAPPED",
    "UNKNOWN_BUT_PASS",
    "UNBOUNDED_MAPPING_EXECUTED",
    "CLOUD_BACKEND_EXECUTED",
    "PROFIT_EVIDENCE_CREATED",
    "LIVE_READY_CLAIMED",
    "SOURCE_TRUTH_ACCEPTED",
    "CONNECTOR_BOUND",
)

MAPPING_QUALITY_GRADES: tuple[str, ...] = (
    "A_FULL_MULTI_MODEL_COMPUTABLE",
    "B_PRIMARY_MODEL_COMPUTABLE_SECONDARY_PARTIAL",
    "C_STRUCTURAL_COMPUTABLE_RETEST_REQUIRED",
    "D_PARTIAL_MAPPING_FILL_ACTION_REQUIRED",
    "E_REPAIR_MAPPING_REQUIRED",
    "F_INSUFFICIENT_DATA_ROUTE_REQUIRED",
    "G_STRUCTURAL_ONLY_RESIDUAL",
)

MODEL_FAMILIES: tuple[str, ...] = (
    "QUBO",
    "BQM",
    "Ising",
    "CQM",
    "DQM",
    "QuadraticProgram",
)

MAP_CAPS: dict[str, int] = {
    "max_deep_mapping_rows_default_ci": 64,
    "max_rows_per_model_family_default_ci": 16,
    "max_penalty_variants_per_row_default_ci": 8,
    "max_encoding_variants_per_row_default_ci": 8,
    "max_coefficient_scaling_variants_default_ci": 8,
    "max_model_family_attempts_per_row_default_ci": 6,
    "max_variables_for_dense_qubo_default_ci": 64,
    "max_variables_for_exact_test_vectors_default_ci": 32,
}

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
    "PR166-QC-R2-OR-SUCCESSOR-RETEST",
    "PR167",
    "PR162E",
    "PR162F",
    "FUTURE_OWNER_DASHBOARD_REVIEW",
    "FUTURE_CLOUD_SWITCHBOARD_ENABLEMENT_NO_EXECUTION",
    "FUTURE_CONNECTOR_ROUTES_NO_BINDING",
)

AGENT_IDS: tuple[str, ...] = (
    "Commander",
    "Governance",
    "Research Agent",
    "Source/External Scout Agent",
    "QKU/Formula Materialization Agent",
    "Quantum AutoMapper Agent",
    "Quantum Optimizer / Quantum Benchmark Agent",
    "Quantum Comparator Agent",
    "Classical Comparator Agent",
    "Portfolio/Risk Agent",
    "Execution/TCA Agent",
    "Replay Agent",
    "Paper Agent",
    "Open Trade Simulator Agent",
    "Dashboard/Owner Review Agent",
    "Quantum Cloud Switchboard Agent",
    "Owner Dashboard Control Agent",
    "Race Arbitration Agent",
    "Connector Readiness Agent",
    "External Acquisition Agent",
)
