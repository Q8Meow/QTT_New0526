"""Central constants for PR162D-R1 acquisition expansion."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR162D_R1"
PR_LABEL = "PR162D_R1_EXTERNAL_FORMULA_DATA_QUANTUM_ACQUISITION_EXPANSION"
EXPECTED_BRANCH = "pr162d-r1-external-formula-data-quantum-acquisition-expansion"
SUCCESS_MARKER = "PR162D_R1_EXTERNAL_FORMULA_DATA_QUANTUM_ACQUISITION_EXPANSION_VALIDATED"
AUTHORITY_CLASS = "PR162D_R1_CANDIDATE_ACQUISITION_ONLY_NO_LIVE_ORDER_AUTHORITY"

GENERATED_DIR = Path("docs/master_plan/generated")
MASTER_PLAN_REF = "docs/master_plan/QTT_MasterPlan_Current.md"
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "pr162d_r1_external_formula_data_quantum_acquisition_expansion"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"

UPSTREAM_PR_REFS = (
    "PR136",
    "PR161C",
    "PR161D",
    "PR161F",
    "PR162",
    "PR162B",
    "PR162C",
    "PR162D",
)
DOWNSTREAM_PR_ROUTES = ("PR162R", "PR163", "PR164", "PR165")

NO_AUTHORITY_FLAGS = {
    "creates_live_authority": False,
    "creates_order_authority": False,
    "creates_private_state": False,
    "creates_profit_evidence": False,
    "creates_result_backed_ranking": False,
    "creates_connector_semantics": False,
    "creates_source_truth_authority": False,
    "creates_qtt_digest_authority": False,
    "mutates_atomicrows_bundle_jsonl": False,
    "emits_result_packets": False,
    "emits_replay_paper_results": False,
    "ci_requires_network": False,
    "remote_quantum_required_for_ci": False,
}

BOUNDARY_COUNT_FIELDS = {
    "live_promotion_ready_count": 0,
    "order_ready_count": 0,
    "profit_evidence_count": 0,
    "private_state_fetch_count": 0,
    "order_execution_count": 0,
    "qtt_sha_freeze_checksum_authority_count": 0,
    "atomicrows_bundle_hash_sha_authority_count": 0,
    "atomicrows_bundle_mutation_count": 0,
    "quantum_advantage_claim_count": 0,
}

REQUIRED_AGENT_ROUTES = (
    "QKU_DATA_ACQUISITION_AGENT",
    "QKU_FORMULA_COMPUTE_ENGINE",
    "FORMULA_ALGORITHM_RUNTIME_CANDIDATE_MODE",
    "FEATURE_BUILDER",
    "PARAMETER_STACK_AGENT",
    "REPLAY_PAPER_CANDIDATE_ROUTER",
    "REPLAY_ENGINE_INPUT_PREP",
    "PAPER_ENGINE_INPUT_PREP",
    "RISK_MANAGER_CANDIDATE_REVIEW",
    "CAPITAL_SIZING_CANDIDATE_REVIEW",
    "QUANTUM_ADVISORY_AGENT",
    "QUANTUM_CLASSICAL_HYBRID_COMPARATOR",
    "STRATEGY_SIGNAL_DECISION_AGENT_CANDIDATE_INTENT",
    "EXECUTION_ROUTER_NON_AUTHORITY_PREVIEW",
    "OWNER_REVIEW_OPTIONAL",
)
QUANTUM_HARNESS_ROUTE = "QUANTUM_EXECUTION_HARNESS"
REPLAY_PAPER_ROUTE = "PR162D_R1_REPLAY_PAPER_CANDIDATE_QUEUE"

PR162D_REQUIRED_INPUTS = (
    "docs/master_plan/generated/PR162D_FinalSummary.report.json",
    "docs/master_plan/generated/PR162D_AggressiveQKUCandidateAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_CandidateSourceIntakeRegistry.report.json",
    "docs/master_plan/generated/PR162D_CandidateFormulaAlgorithmValueInventory.report.json",
    "docs/master_plan/generated/PR162D_FormulaExpressionRegistry.report.json",
    "docs/master_plan/generated/PR162D_QKUFormulaMaterializationExpansion.report.json",
    "docs/master_plan/generated/PR162D_QKUAlgorithmMaterializationExpansion.report.json",
    "docs/master_plan/generated/PR162D_QKUParameterValueFieldFillExpansion.report.json",
    "docs/master_plan/generated/PR162D_QKUParameterRangeScaleExpansion.report.json",
    "docs/master_plan/generated/PR162D_QKUTradableValueCandidateExpansion.report.json",
    "docs/master_plan/generated/PR162D_QKUSolverInputAssemblyExpansion.report.json",
    "docs/master_plan/generated/PR162D_QKUToAgentToReplayPaperTraceabilityMatrix.report.json",
    "docs/master_plan/generated/PR162D_ReplayPaperCandidateRouterQueue.report.json",
    "docs/master_plan/generated/PR162D_PR162RReplayPaperAdapterCandidateHandoff.report.json",
    "docs/master_plan/generated/PR162D_QuantumProblemModelRegistry.report.json",
    "docs/master_plan/generated/PR162D_QuantumExecutionModeRegistry.report.json",
    "docs/master_plan/generated/PR162D_QUBOIsingBqmCqmCandidateInputExpansion.report.json",
    "docs/master_plan/generated/PR162D_QUBOIsingLocalExactSmokeExecution.report.json",
    "docs/master_plan/generated/PR162D_QuantumBackendAdapterReadinessMatrix.report.json",
    "docs/master_plan/generated/PR162D_QuantumProviderDryRunPayloadRegistry.report.json",
    "docs/master_plan/generated/PR162D_QuantumAgentUsabilityAtLaunchMatrix.report.json",
    "docs/master_plan/generated/PR162D_ReportShardManifest.report.json",
)

UPSTREAM_CONTEXT_INPUTS = (
    MASTER_PLAN_REF,
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "docs/master_plan/generated/PR161C_QKUCanonicalRegistry.report.json",
    "docs/master_plan/generated/PR161C_QKUOrchestrationGraph.report.json",
    "docs/master_plan/generated/PR161D_QKUAgentTaskQueue.report.json",
    "docs/master_plan/generated/PR161D_QKUAgentGraphRoutingMatrix.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentWorkflowOrchestrationContract.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentRoleIOContract.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentHandoffMatrix.report.json",
    "docs/master_plan/generated/PR161F_QKUEndToEndTraceabilityMatrix.report.json",
    "docs/master_plan/generated/PR162_ReplayDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162_PaperDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162_QKUQuantumExecutionReadinessBridge.report.json",
    "docs/master_plan/generated/PR162_QKUQuantumProblemEncodingBlueprint.report.json",
    "docs/master_plan/generated/PR162B_QKUFormulaRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUAlgorithmRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUObjectiveFunctionRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUConstraintRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUSolverMappingRegistry.report.json",
    "docs/master_plan/generated/PR162B_QuantumQUBOIsingFormulaMaterialization.report.json",
    "docs/master_plan/generated/PR162B_QuantumSolverSmokeExecutionReport.report.json",
    "docs/master_plan/generated/PR162C_SourceDiscoveryLedger.report.json",
    "docs/master_plan/generated/PR162C_SourcePortfolioRegistry.report.json",
    "docs/master_plan/generated/PR162C_QKUFormulaToAgentRouteMatrix.report.json",
    "docs/master_plan/generated/PR162C_QKUFormulaToDatasetBindingMatrix.report.json",
)

THRESHOLDS = {
    "acquisition_first_effort_ratio": 0.90,
    "master_plan_formula_mentions_scanned_count": 100,
    "master_plan_algorithm_mentions_scanned_count": 50,
    "master_plan_parameter_pack_mentions_scanned_count": 50,
    "master_plan_extracted_formula_candidate_count": 50,
    "master_plan_extracted_algorithm_candidate_count": 25,
    "master_plan_extracted_quantum_candidate_count": 15,
    "master_plan_formula_gap_target_count": 50,
    "external_sources_scouted_count": 75,
    "external_source_candidates_created": 75,
    "official_or_reputable_source_candidates_created": 30,
    "non_official_candidate_intake_count": 30,
    "external_formula_candidates_created": 120,
    "external_algorithm_candidates_created": 40,
    "external_parameter_candidates_created": 150,
    "external_parameter_range_default_scale_candidates_created": 150,
    "external_dataset_candidates_created": 25,
    "prediction_market_dataset_candidates_created": 15,
    "prediction_market_formula_candidates_created": 40,
    "calibration_formula_candidates_created": 15,
    "risk_sizing_formula_candidates_created": 25,
    "technical_indicator_formula_candidates_created": 25,
    "portfolio_optimizer_formula_candidates_created": 20,
    "quantum_formula_candidates_created": 60,
    "quantum_problem_formulation_candidates_created": 35,
    "quantum_classical_comparator_candidates_created": 20,
    "qku_mapped_external_candidate_count": 300,
    "replay_paper_routed_external_candidate_count": 300,
    "agent_routed_external_candidate_count": 300,
}

CORE_REPORT_FILENAMES = (
    "PR162D_R1_FinalSummary.report.json",
    "PR162D_R1_ExternalSourceAcquisitionLedger.report.json",
    "PR162D_R1_WebResearchCandidateRegistry.report.json",
    "PR162D_R1_SourceLocatorRegistry.report.json",
    "PR162D_R1_SourceTierCoverage.report.json",
    "PR162D_R1_AcquiredExternalSourceCoverageSummary.report.json",
    "PR162D_R1_AcquisitionEffortAllocationAudit.report.json",
    "PR162D_R1_AcquisitionShortfallReport.report.json",
    "PR162D_R1_OfflineSafeSourceSnapshotManifest.report.json",
    "PR162D_R1_NoHallucinatedSourceAudit.report.json",
    "PR162D_R1_SourceRiskQuarantineLedger.report.json",
)

MASTER_PLAN_REPORT_FILENAMES = (
    "PR162D_R1_MasterPlanFormulaAlgorithmMiningLedger.report.json",
    "PR162D_R1_MasterPlanQKUFormulaCandidateRegistry.report.json",
    "PR162D_R1_MasterPlanAlgorithmFamilyCandidateRegistry.report.json",
    "PR162D_R1_MasterPlanParameterPackExtractionLedger.report.json",
    "PR162D_R1_MasterPlanQuantumFormulaExtractionLedger.report.json",
    "PR162D_R1_MasterPlanFormulaToExternalAcquisitionGapMatrix.report.json",
    "PR162D_R1_MasterPlanFormulaToQKURouteMatrix.report.json",
    "PR162D_R1_MasterPlanFormulaToAgentRouteMatrix.report.json",
    "PR162D_R1_MasterPlanFormulaToReplayPaperRouteMatrix.report.json",
)

FORMULA_REPORT_FILENAMES = (
    "PR162D_R1_FormulaAcquisitionLedger.report.json",
    "PR162D_R1_FormulaExpressionExpansionRegistry.report.json",
    "PR162D_R1_FormulaEquivalenceAndDedupLedger.report.json",
    "PR162D_R1_AlgorithmAcquisitionLedger.report.json",
    "PR162D_R1_ParameterRangeAcquisitionLedger.report.json",
    "PR162D_R1_DefaultValueScaleAcquisitionLedger.report.json",
    "PR162D_R1_TradableValueCandidateExpansion.report.json",
    "PR162D_R1_TestVectorExpansionRegistry.report.json",
    "PR162D_R1_ComputableCandidateRegistry.report.json",
    "PR162D_R1_NoMetadataOnlyCandidateAudit.report.json",
)

PREDICTION_MARKET_REPORT_FILENAMES = (
    "PR162D_R1_KalshiHistoricalDataCandidateLedger.report.json",
    "PR162D_R1_PolymarketPublicDataCandidateLedger.report.json",
    "PR162D_R1_ForecastExPublicCsvCandidateLedger.report.json",
    "PR162D_R1_PredictionMarketDatasetAcquisitionLedger.report.json",
    "PR162D_R1_PredictionMarketFormulaAcquisitionLedger.report.json",
    "PR162D_R1_MicrostructureFeatureFormulaLedger.report.json",
)

QUANTUM_REPORT_FILENAMES = (
    "PR162D_R1_QuantumFormulaAcquisitionLedger.report.json",
    "PR162D_R1_QuantumProblemFormulationRegistry.report.json",
    "PR162D_R1_QUBOFormulationExpansion.report.json",
    "PR162D_R1_IsingFormulationExpansion.report.json",
    "PR162D_R1_BQMCQMFormulationExpansion.report.json",
    "PR162D_R1_QAOAVQESamplingVQEAnnealingFormulationLedger.report.json",
    "PR162D_R1_QuantumParameterRangeLedger.report.json",
    "PR162D_R1_QuantumClassicalComparatorMappingLedger.report.json",
    "PR162D_R1_QuantumMetadataOnlyRejectionAudit.report.json",
    "PR162D_R1_QuantumNoAdvantageProfitAuthorityAudit.report.json",
)

ORCHESTRATION_REPORT_FILENAMES = (
    "PR162D_R1_QKUExternalCandidateMappingMatrix.report.json",
    "PR162D_R1_AgentExternalCandidateRouteMatrix.report.json",
    "PR162D_R1_ReplayPaperExternalCandidateQueue.report.json",
    "PR162D_R1_PR162DConsumptionAudit.report.json",
    "PR162D_R1_PR162RHandoffExpansion.report.json",
    "PR162D_R1_PR163FutureResultConsumerBridge.report.json",
    "PR162D_R1_PR164FutureReviewBridge.report.json",
    "PR162D_R1_PR165FutureScoringBridge.report.json",
    "PR162D_R1_NoOrphanExternalCandidateAudit.report.json",
)

AUTHORITY_REPORT_FILENAMES = (
    "PR162D_R1_NoLiveOrderAuthorityAudit.report.json",
    "PR162D_R1_NoPrivateStateSecretAudit.report.json",
    "PR162D_R1_NoQttShaFreezeChecksumAuthorityAudit.report.json",
    "PR162D_R1_NoAtomicRowsBundleMutationAudit.report.json",
    "PR162D_R1_NoScatteredHardcodedBoundaryLiteralAudit.report.json",
)

REPORT_FILENAMES = (
    *CORE_REPORT_FILENAMES,
    *MASTER_PLAN_REPORT_FILENAMES,
    *FORMULA_REPORT_FILENAMES,
    *PREDICTION_MARKET_REPORT_FILENAMES,
    *QUANTUM_REPORT_FILENAMES,
    *ORCHESTRATION_REPORT_FILENAMES,
    *AUTHORITY_REPORT_FILENAMES,
)

SCHEMA_FILENAMES = tuple(
    filename.replace(".report.json", ".schema.json").lower()
    for filename in REPORT_FILENAMES
)
REPORT_SCHEMA_REFS = {
    report: f"{SCHEMA_DIR.as_posix()}/{schema}"
    for report, schema in zip(REPORT_FILENAMES, SCHEMA_FILENAMES, strict=True)
}
