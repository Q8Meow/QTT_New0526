"""Central constants for PR162R-A."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR162R_A"
PR_LABEL = "PR162R_A_REPLAY_PAPER_EXECUTABILITY_CLASSIFICATION_AUDIT"
EXPECTED_BRANCH = "pr162r-a-replay-paper-executability-classification-audit"
SUCCESS_MARKER = "PR162R_A_REPLAY_PAPER_EXECUTABILITY_CLASSIFICATION_AUDIT_VALIDATED"
AUTHORITY_CLASS = "PR162R_A_CLASSIFICATION_AUDIT_NO_REPLAY_PAPER_EXECUTION_NO_LIVE_ORDER_AUTHORITY"

GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "pr162r_a_replay_paper_executability_classification_audit"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"

UPSTREAM_PR_REFS = ("PR136", "PR161F", "PR162", "PR162D", "PR162D_R1")
DOWNSTREAM_PR_ROUTES = ("PR162R", "PR162D_R2", "PR162E", "PR162F", "PR163", "PR164", "PR165")

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
    "executes_replay_adapter": False,
    "executes_paper_adapter": False,
    "ci_requires_network": False,
    "remote_quantum_required_for_ci": False,
}

BOUNDARY_COUNT_FIELDS = {
    "replay_execution_count": 0,
    "paper_execution_count": 0,
    "result_packet_created_count": 0,
    "live_order_authority_count": 0,
    "order_ready_count": 0,
    "live_promotion_ready_count": 0,
    "profit_evidence_count": 0,
    "private_state_fetch_count": 0,
    "qtt_sha_freeze_checksum_authority_count": 0,
    "atomicrows_bundle_mutation_count": 0,
    "quantum_advantage_claim_count": 0,
}

PRIMARY_STATES = (
    "EXECUTABLE_REPLAY_READY",
    "EXECUTABLE_PAPER_READY",
    "EXECUTABLE_REPLAY_AND_PAPER_READY",
    "PARTIAL_EXECUTABLE_REPLAY_READY",
    "PARTIAL_EXECUTABLE_PAPER_READY",
    "PARTIAL_EXECUTABLE_REPLAY_AND_PAPER_READY",
    "NON_EXECUTABLE_CRITICAL_INPUT_MISSING",
    "NON_EXECUTABLE_FORMULA_OR_ALGORITHM_MISSING",
    "NON_EXECUTABLE_DATASET_BINDING_MISSING",
    "NON_EXECUTABLE_SOURCE_LOCATOR_MISSING",
    "NON_EXECUTABLE_QUANTUM_MAPPING_MISSING",
    "DORMANT_NON_STAGE1",
)

COMPUTABILITY_CLASSES = (
    "FULLY_COMPUTABLE",
    "PARTIALLY_COMPUTABLE",
    "PARAMETER_ONLY",
    "FEATURE_ONLY",
    "OBJECTIVE_BACKED",
    "CONSTRAINT_BACKED",
    "SOLVER_BACKED",
    "QUANTUM_FORMULATION_BACKED",
    "METADATA_ONLY_NOT_READY",
)

LATENCY_CLASSES = (
    "HOT_PATH_SAFE",
    "PRECOMPUTE_REQUIRED",
    "BATCH_ONLY",
    "QUANTUM_BATCH_ONLY",
    "REPLAY_ONLY",
    "PAPER_ONLY",
    "NOT_RUNTIME_SAFE_YET",
)

TRADING_UTILITY_CLASSES = (
    "EXPECTED_VALUE_FEATURE",
    "PROBABILITY_CALIBRATION_FEATURE",
    "MARKET_MICROSTRUCTURE_FEATURE",
    "RISK_SIZING_FEATURE",
    "CAPITAL_ALLOCATION_FEATURE",
    "PARAMETER_STACK_SELECTION_FEATURE",
    "QUANTUM_OPTIMIZER_INPUT",
    "QUANTUM_CLASSICAL_COMPARATOR_INPUT",
    "DORMANT_NON_STAGE1",
)

SECONDARY_TAGS = (
    "NON_OFFICIAL_SOURCE",
    "PROVISIONAL_SOURCE",
    "PARAMETER_CALIBRATION_NEEDED",
    "SOURCE_CONFLICT_NEEDS_REVIEW",
    "QUANTUM_COMPARATOR_READY",
    "QUANTUM_BACKEND_OPTIONAL",
    "LATENCY_PROFILE_NEEDED",
    "RISK_REVIEW_NEEDED",
    "CAPITAL_SIZING_REVIEW_NEEDED",
    "OWNER_REVIEW_OPTIONAL",
    "FORMULA_DEDUPE_REVIEW_NEEDED",
    "ENHANCEMENT_ONLY_GAP",
    "MICRO_MATERIALIZED_IN_PR162R_A",
    "TARGETED_CRITICAL_GAP_FOR_PR162D_R2",
)

CORE_REPORT_FILENAMES = (
    "PR162R_A_FinalSummary.report.json",
    "PR162R_A_PR162DR1ConsumptionAudit.report.json",
    "PR162R_A_PR162D6502CoverageRollup.report.json",
    "PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json",
    "PR162R_A_ComputabilityClassMatrix.report.json",
    "PR162R_A_ReplayReadyCandidateQueue.report.json",
    "PR162R_A_PaperReadyCandidateQueue.report.json",
    "PR162R_A_ReplayAndPaperReadyCandidateQueue.report.json",
    "PR162R_A_PartialReplayPaperCandidateQueue.report.json",
    "PR162R_A_NonExecutableCriticalGapMatrix.report.json",
    "PR162R_A_NonCriticalMissingInfoMatrix.report.json",
    "PR162R_A_EnhancementBacklogMatrix.report.json",
    "PR162R_A_DormantNonStage1CandidateMatrix.report.json",
    "PR162R_A_TargetedMicroMaterializationLedger.report.json",
)

COMPATIBILITY_REPORT_FILENAMES = (
    "PR162R_A_FormulaRuntimeCompatibilityMatrix.report.json",
    "PR162R_A_AlgorithmRuntimeCompatibilityMatrix.report.json",
    "PR162R_A_DatasetBindingCompatibilityMatrix.report.json",
    "PR162R_A_InputOutputUnitCompatibilityMatrix.report.json",
    "PR162R_A_ParameterCoverageCompatibilityMatrix.report.json",
    "PR162R_A_SourceLocatorCompatibilityMatrix.report.json",
    "PR162R_A_AgentConsumabilityMatrix.report.json",
    "PR162R_A_ReplayAdapterInputEligibilityMatrix.report.json",
    "PR162R_A_PaperAdapterInputEligibilityMatrix.report.json",
    "PR162R_A_QuantumComparatorCompatibilityMatrix.report.json",
    "PR162R_A_QuantumReplayPaperEligibilityMatrix.report.json",
    "PR162R_A_LatencyClassCompatibilityMatrix.report.json",
    "PR162R_A_TradingUtilityClassMatrix.report.json",
)

DOWNSTREAM_REPORT_FILENAMES = (
    "PR162R_A_PR162RAdapterRerunInputPack.report.json",
    "PR162R_A_PR162D_R2TargetedCriticalGapBacklog.report.json",
    "PR162R_A_PR162D_R2OptionalEnhancementBacklog.report.json",
    "PR162R_A_PR163FutureResultPacketReadinessBridge.report.json",
    "PR162R_A_PR164FutureReviewBridge.report.json",
    "PR162R_A_PR165FutureScoringBridge.report.json",
    "PR162R_A_PR162EFormulaPluginFutureBridge.report.json",
    "PR162R_A_PostLaunchFormulaPluginRequirementBacklog.report.json",
    "PR162R_A_FormulaPluginCandidateReadinessMatrix.report.json",
    "PR162R_A_QuantumPluginCandidateReadinessMatrix.report.json",
    "PR162R_A_OwnerFormulaIntakeFutureBridge.report.json",
    "PR162R_A_AgentFormulaScoutFutureBridge.report.json",
    "PR162R_A_RuntimeFormulaAllowlistFutureBridge.report.json",
    "PR162R_A_FormulaVersionRollbackFutureBridge.report.json",
    "PR162R_A_HotPathFormulaLatencyFutureBridge.report.json",
)

AUDIT_REPORT_FILENAMES = (
    "PR162R_A_NoReplayPaperExecutionAudit.report.json",
    "PR162R_A_NoLiveOrderAuthorityAudit.report.json",
    "PR162R_A_NoProfitEvidenceAudit.report.json",
    "PR162R_A_NoPrivateStateSecretAudit.report.json",
    "PR162R_A_NoQttShaFreezeChecksumAuthorityAudit.report.json",
    "PR162R_A_NoAtomicRowsBundleMutationAudit.report.json",
    "PR162R_A_NoMetadataOnlyReplayReadyAudit.report.json",
    "PR162R_A_NoOrphanCandidateAudit.report.json",
    "PR162R_A_NoOrphanGeneratedFileAudit.report.json",
    "PR162R_A_NoScatteredHardcodedBoundaryLiteralAudit.report.json",
)

REPORT_FILENAMES = (
    *CORE_REPORT_FILENAMES,
    *COMPATIBILITY_REPORT_FILENAMES,
    *DOWNSTREAM_REPORT_FILENAMES,
    *AUDIT_REPORT_FILENAMES,
)

SCHEMA_FILENAMES = tuple(
    filename.replace(".report.json", ".schema.json").lower()
    for filename in REPORT_FILENAMES
)
REPORT_SCHEMA_REFS = {
    report: f"{SCHEMA_DIR.as_posix()}/{schema}"
    for report, schema in zip(REPORT_FILENAMES, SCHEMA_FILENAMES, strict=True)
}

PR162D_R1_REQUIRED_INPUTS = (
    "docs/master_plan/generated/PR162D_R1_FinalSummary.report.json",
    "docs/master_plan/generated/PR162D_R1_ComputableCandidateRegistry.report.json",
    "docs/master_plan/generated/PR162D_R1_QKUExternalCandidateMappingMatrix.report.json",
    "docs/master_plan/generated/PR162D_R1_AgentExternalCandidateRouteMatrix.report.json",
    "docs/master_plan/generated/PR162D_R1_ReplayPaperExternalCandidateQueue.report.json",
    "docs/master_plan/generated/PR162D_R1_PR162RHandoffExpansion.report.json",
    "docs/master_plan/generated/PR162D_R1_FormulaAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_FormulaExpressionExpansionRegistry.report.json",
    "docs/master_plan/generated/PR162D_R1_AlgorithmAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_ParameterRangeAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_DefaultValueScaleAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_PredictionMarketDatasetAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_PredictionMarketFormulaAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_QuantumFormulaAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_QuantumProblemFormulationRegistry.report.json",
    "docs/master_plan/generated/PR162D_R1_QuantumClassicalComparatorMappingLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_TestVectorExpansionRegistry.report.json",
    "docs/master_plan/generated/PR162D_R1_NoMetadataOnlyCandidateAudit.report.json",
    "docs/master_plan/generated/PR162D_R1_NoOrphanExternalCandidateAudit.report.json",
    "docs/master_plan/generated/PR162D_R1_SourceLocatorRegistry.report.json",
    "docs/master_plan/generated/PR162D_R1_SourceTierCoverage.report.json",
)

PR162D_REQUIRED_INPUTS = (
    "docs/master_plan/generated/PR162D_FinalSummary.report.json",
    "docs/master_plan/generated/PR162D_PR162CBlockerReinterpretationLedger.report.json",
    "docs/master_plan/generated/PR162D_ReplayPaperCandidateRouterQueue.report.json",
    "docs/master_plan/generated/PR162D_PR162RReplayPaperAdapterCandidateHandoff.report.json",
    "docs/master_plan/generated/PR162D_QKUToAgentToReplayPaperTraceabilityMatrix.report.json",
    "docs/master_plan/generated/PR162D_QuantumProblemModelRegistry.report.json",
    "docs/master_plan/generated/PR162D_QuantumExecutionModeRegistry.report.json",
)

REPLAY_PAPER_CONTRACT_INPUTS = (
    "docs/master_plan/generated/PR162_ReplayDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162_PaperDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162_RealNonLiveRunArtifactCandidateRegistry.report.json",
    "docs/master_plan/generated/PR161F_ReplayRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PaperRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PairedReplayPaperRunPlan.report.json",
    "docs/master_plan/generated/PR161F_ResultPacketEmissionEligibilityGate.report.json",
)

UPSTREAM_CONTEXT_INPUTS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
    "QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md",
    "docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md",
    "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json",
    "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentWorkflowOrchestrationContract.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentRoleIOContract.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentHandoffMatrix.report.json",
    "docs/master_plan/generated/PR161F_QKUEndToEndTraceabilityMatrix.report.json",
)

ALL_CONSUMPTION_INPUTS = (
    *UPSTREAM_CONTEXT_INPUTS,
    *PR162D_R1_REQUIRED_INPUTS,
    *PR162D_REQUIRED_INPUTS,
    *REPLAY_PAPER_CONTRACT_INPUTS,
    "tools/currentize_pr152_after_generated_artifacts.py",
    "tools/validate_grand_global_debug_logical_consistency_audit.py",
    "tools/run_validation_gates.py",
    "tools/ci_branch_context.py",
)
