"""Central constants for PR162D candidate materialization and routing."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR162D"
PR_LABEL = "PR162D_AGGRESSIVE_QKU_CANDIDATE_MATERIALIZATION_AGENT_ROUTING"
EXPECTED_BRANCH = "pr162d-aggressive-qku-candidate-materialization-agent-routing"
SUCCESS_MARKER = (
    "PR162D_AGGRESSIVE_QKU_CANDIDATE_MATERIALIZATION_AGENT_ROUTING_VALIDATED"
)
AUTHORITY_CLASS = (
    "PR162D_CANDIDATE_MATERIALIZATION_AGENT_ROUTING_AND_QUANTUM_SMOKE_ONLY"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "aggressive_qku_candidate_materialization_agent_routing"
)

GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "aggressive_qku_candidate_materialization_agent_routing"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
SHARD_DIR = (
    GENERATED_DIR
    / "pr162d_aggressive_qku_candidate_materialization_agent_routing_shards"
)
REPORT_SHARD_RECORD_TARGET = 1000
REPORT_SHARD_PREVIEW_RECORD_LIMIT = 3
REPORT_SHARD_BYTE_THRESHOLD = 900_000

PR152_CURRENTIZATION_REPORT_REF = (
    "docs/master_plan/generated/"
    "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
)
PR152_FINALIZATION_CURRENTIZATION_COMMAND = (
    ".\\.venv\\Scripts\\python.exe tools\\currentize_pr152_after_generated_artifacts.py"
)
PR152_FINALIZATION_VALIDATION_COMMAND = (
    ".\\.venv\\Scripts\\python.exe tools\\validate_grand_global_debug_logical_consistency_audit.py"
)
PR152_FINAL_VALIDATION_GATES_COMMAND = (
    ".\\.venv\\Scripts\\python.exe tools\\run_validation_gates.py"
)

SHARD_MANIFEST_REPORT_FILENAME = "PR162D_ReportShardManifest.report.json"
SHARD_MANIFEST_REPORT_PATH = GENERATED_DIR / SHARD_MANIFEST_REPORT_FILENAME

CORE_REPORT_FILENAMES = (
    "PR162D_FinalSummary.report.json",
    "PR162D_SharedDictionary.report.json",
    "PR162D_SourceQualityPolicy.report.json",
    "PR162D_SourcePriorityLadder.report.json",
    "PR162D_SourceTierCoverage.report.json",
    "PR162D_PR162CBlockerReinterpretationLedger.report.json",
    "PR162D_AggressiveQKUCandidateAcquisitionLedger.report.json",
    "PR162D_QKUFieldFillExpansionMatrix.report.json",
    "PR162D_QKUMaterializationProgressMatrix.report.json",
    "PR162D_CandidateDatasetInventory.report.json",
    "PR162D_CandidateFormulaAlgorithmValueInventory.report.json",
    "PR162D_CandidateSourceIntakeRegistry.report.json",
    "PR162D_NonOfficialCandidateIntakeRegistry.report.json",
    "PR162D_OfficialPublicCandidateIntakeRegistry.report.json",
    "PR162D_OwnerProvidedCandidateIntakeRegistry.report.json",
    "PR162D_FieldFillProgressSummary.report.json",
    "PR162D_NoAcquisitionGateRegressionAudit.report.json",
    "PR162D_CandidateDeduplicationLedger.report.json",
    "PR162D_SourceRiskQuarantineLedger.report.json",
    "PR162D_CachedOnlineSourceSnapshotManifest.report.json",
    SHARD_MANIFEST_REPORT_FILENAME,
)

TRACK_A_REPORT_FILENAMES = (
    "PR162D_QKUFormulaMaterializationExpansion.report.json",
    "PR162D_QKUAlgorithmMaterializationExpansion.report.json",
    "PR162D_QKUObjectiveFunctionExpansion.report.json",
    "PR162D_QKUConstraintExpansion.report.json",
    "PR162D_QKUParameterValueFieldFillExpansion.report.json",
    "PR162D_QKUParameterRangeScaleExpansion.report.json",
    "PR162D_QKUTradableValueCandidateExpansion.report.json",
    "PR162D_QKUSolverInputAssemblyExpansion.report.json",
    "PR162D_QKUExecutableComputeExpansion.report.json",
    "PR162D_QKUFormulaTestVectorExpansion.report.json",
    "PR162D_QKUAlgorithmTestVectorExpansion.report.json",
    "PR162D_QKUFeatureMaterializationExpansion.report.json",
    "PR162D_QKUReplayPaperCandidateExpansion.report.json",
    "PR162D_FormulaExpressionRegistry.report.json",
    "PR162D_FormulaUnitNormalizationRegistry.report.json",
    "PR162D_DeterministicCandidateComputationLedger.report.json",
    "PR162D_ComputabilityReadinessMatrix.report.json",
    "PR162D_NoMetadataOnlyMaterializationAudit.report.json",
)

TRACK_B_REPORT_FILENAMES = (
    "PR162D_AgentConsumableQKURoutingMatrix.report.json",
    "PR162D_AgentConsumablePartialQKURoutingMatrix.report.json",
    "PR162D_QKUDataAcquisitionAgentRouteMatrix.report.json",
    "PR162D_QKUFormulaComputeEngineRouteMatrix.report.json",
    "PR162D_FormulaAlgorithmRuntimeRouteMatrix.report.json",
    "PR162D_FeatureBuilderRouteMatrix.report.json",
    "PR162D_ParameterStackAgentCandidateRouteMatrix.report.json",
    "PR162D_ReplayPaperCandidateRouterQueue.report.json",
    "PR162D_ReplayPaperResultAnalyzerInputPrepMatrix.report.json",
    "PR162D_RiskCapitalSizingCandidateRouteMatrix.report.json",
    "PR162D_QuantumAdvisoryCandidateRouteMatrix.report.json",
    "PR162D_StrategySignalDecisionCandidateIntentMatrix.report.json",
    "PR162D_ExecutionRouterNonAuthorityPreviewMatrix.report.json",
    "PR162D_AgentRouteResolverTraceMatrix.report.json",
    "PR162D_NoOrphanQKUFormulaDatasetAgentAudit.report.json",
)

TRACK_C_REPORT_FILENAMES = (
    "PR162D_QuantumExecutionModeRegistry.report.json",
    "PR162D_QuantumProblemModelRegistry.report.json",
    "PR162D_QUBOIsingBqmCqmCandidateInputExpansion.report.json",
    "PR162D_QUBOIsingLocalExactSmokeExecution.report.json",
    "PR162D_QuantumBackendAdapterReadinessMatrix.report.json",
    "PR162D_QuantumBackendDependencyStatus.report.json",
    "PR162D_QuantumProviderDryRunPayloadRegistry.report.json",
    "PR162D_QuantumReplayPaperExecutionHarness.report.json",
    "PR162D_QuantumClassicalHybridCandidateExpansion.report.json",
    "PR162D_QuantumClassicalComparatorSmokeResult.report.json",
    "PR162D_QuantumReplayPaperCandidateRouteMatrix.report.json",
    "PR162D_QuantumAgentUsabilityAtLaunchMatrix.report.json",
    "PR162D_QuantumNoLiveOrderAuthorityAudit.report.json",
    "PR162D_QuantumNoProfitAdvantageClaimAudit.report.json",
    "PR162D_QuantumNoLivePretradeRemoteDependencyAudit.report.json",
)

CROSSWALK_REPORT_FILENAMES = (
    "PR162D_PR136CrosswalkConsumptionAudit.report.json",
    "PR162D_PR136MarketSpecificIndexConsumptionAudit.report.json",
    "PR162D_PR136CommandActionMatrixConsumptionAudit.report.json",
    "PR162D_PR161FAgentContractConsumptionAudit.report.json",
    "PR162D_UpstreamDownstreamPRRouteBridge.report.json",
    "PR162D_QKUToPRWorkflowBridge.report.json",
    "PR162D_QKUToAgentToReplayPaperTraceabilityMatrix.report.json",
)

SOURCE_PACK_REPORT_FILENAMES = (
    "PR162D_KalshiCandidateMaterializationPack.report.json",
    "PR162D_PolymarketCandidateMaterializationPack.report.json",
    "PR162D_ForecastExIBKRCandidateMaterializationPack.report.json",
    "PR162D_PublicResearchCandidateMaterializationPack.report.json",
    "PR162D_SocialWebInstitutionalCandidateIntakePack.report.json",
    "PR162D_OpenSourceFormulaLibraryCandidatePack.report.json",
    "PR162D_QuantumHybridFormulaCandidatePack.report.json",
    "PR162D_QuantumBackendProviderCandidatePack.report.json",
    "PR162D_OwnerLocalCandidateMaterializationPack.report.json",
)

DOWNSTREAM_REPORT_FILENAMES = (
    "PR162D_PR162RReplayPaperAdapterCandidateHandoff.report.json",
    "PR162D_PR163ResultPacketStillNotCreatedAudit.report.json",
    "PR162D_PR164ProvenanceReviewStillNotCreatedAudit.report.json",
    "PR162D_PR165ResultBackedRankingStillNotCreatedAudit.report.json",
    "PR162D_LivePromotionOrderProfitEvidenceHardBoundaryReservation.report.json",
)

REPORT_FILENAMES = (
    *CORE_REPORT_FILENAMES,
    *TRACK_A_REPORT_FILENAMES,
    *TRACK_B_REPORT_FILENAMES,
    *TRACK_C_REPORT_FILENAMES,
    *CROSSWALK_REPORT_FILENAMES,
    *SOURCE_PACK_REPORT_FILENAMES,
    *DOWNSTREAM_REPORT_FILENAMES,
)

SCHEMA_FILENAMES = tuple(
    filename.replace(".report.json", ".schema.json").lower()
    for filename in REPORT_FILENAMES
)
REPORT_SCHEMA_REFS = {
    report: f"{SCHEMA_DIR.as_posix()}/{schema}"
    for report, schema in zip(REPORT_FILENAMES, SCHEMA_FILENAMES, strict=True)
}

UPSTREAM_PR_REFS = (
    "PR136",
    "PR137R",
    "PR138",
    "PR161C",
    "PR161D",
    "PR161E",
    "PR161F",
    "PR162",
    "PR162A",
    "PR162B",
    "PR162C",
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
    "quantum_direct_live_order_submission_count": 0,
    "quantum_live_pretrade_remote_dependency_count": 0,
    "quantum_profit_evidence_claim_count": 0,
    "quantum_advantage_claim_count": 0,
    "qtt_sha_freeze_checksum_authority_count": 0,
    "atomicrows_bundle_hash_sha_authority_count": 0,
    "atomicrows_bundle_mutation_count": 0,
}

CENTRALIZED_BOUNDARY_LITERALS = (
    "BLOCKED_REQUIRED_FIELDS_MISSING",
    "AGENT_ROUTE_BLOCKED_REQUIRED_FIELDS_MISSING",
    "AGENT_ROUTE_BLOCKED_STRICT_COVERAGE_MISSING",
    "EXECUTION_ROUTER_ORDER_READY",
    "LIVE_PROMOTION_READY",
    "PROFIT_EVIDENCE_READY",
    "QUANTUM_LIVE_ORDER_READY",
    "QUANTUM_ADVANTAGE_READY",
    "QUANTUM_LIVE_ORDER_SUBMISSION",
    "QUANTUM_DIRECT_EXECUTION_ROUTER_WRITE",
    "QUANTUM_LIVE_PRETRADE_REMOTE_DEPENDENCY",
    "QUANTUM_PROFIT_EVIDENCE_CLAIM",
    "QUANTUM_ADVANTAGE_EVIDENCE_CLAIM",
    "QUANTUM_LATENCY_SUPERIORITY_CLAIM",
    "QUANTUM_EXECUTION_SUPERIORITY_CLAIM",
)

ORIGINAL_PR162C_REQUIRED_FIELD_BLOCKER = "BLOCKED_REQUIRED_FIELDS_MISSING"
REINTERPRETED_REQUIRED_FIELD_TARGET_LABEL = (
    "PR162C_REQUIRED_FIELD_MISSING_REINTERPRETED_AS_CANDIDATE_TARGET"
)

CANDIDATE_PROGRESS_STATUSES = (
    "QKU_CANDIDATE_ACQUISITION_TARGET",
    "CANDIDATE_FIELD_FILL_OPEN",
    "CANDIDATE_FIELD_FILLED_PARTIAL",
    "CANDIDATE_FIELD_FILLED_RESEARCH",
    "CANDIDATE_VALUE_INFERRED_WITH_FORMULA",
    "CANDIDATE_VALUE_INFERRED_WITH_DEFAULT_RANGE",
    "CANDIDATE_VALUE_INFERRED_FROM_RELATED_QKU",
    "CANDIDATE_NEEDS_NORMALIZATION",
    "CANDIDATE_REPLAY_PAPER_ROUTED",
    "CANDIDATE_QUANTUM_FEATURE_READY",
    "CANDIDATE_AGENT_ROUTED_PARTIAL",
)
HARD_QUARANTINE_REASONS = (
    "UNSAFE_PRIVATE_SECRET",
    "ILLEGAL_OR_RIGHTS_BLOCKED",
    "PRIVATE_ACCOUNT_OR_ORDER_ENDPOINT_ONLY",
    "UNMAPPABLE_TO_QKU",
    "DUPLICATE_LOW_VALUE",
    "CORRUPT_UNREADABLE",
    "MALWARE_OR_SUSPICIOUS_CODE",
)

SOURCE_TIERS = ("TIER_0", "TIER_1", "TIER_2", "TIER_3", "TIER_4", "TIER_5")
SOURCE_CLASSES = (
    "REPO_LOCAL_OWNER_PROVIDED",
    "OFFICIAL_VENUE_PUBLIC_DOC",
    "OFFICIAL_VENUE_PUBLIC_API",
    "OFFICIAL_VENUE_PUBLIC_CSV",
    "OFFICIAL_QUANTUM_PROVIDER_DOC",
    "OFFICIAL_OPEN_SOURCE_LIBRARY_DOC",
    "PUBLIC_RESEARCH_FORMULA",
    "PUBLIC_GITHUB_REFERENCE",
    "SOCIAL_WEB_RESEARCH_SIGNAL",
    "OWNER_PROVIDED_INTERNAL_CANDIDATE",
)
AUTHORITY_CLASSES = (
    "REPO_LOCAL_CANDIDATE_NOT_LIVE_TRUTH",
    "OFFICIAL_PUBLIC_CANDIDATE_NOT_LIVE_TRUTH",
    "PUBLIC_RESEARCH_CANDIDATE_NOT_OFFICIAL_TRUTH",
    "SOCIAL_WEB_SIGNAL_REPLAY_PAPER_ONLY",
    "OWNER_APPROVED_INTERNAL_CANDIDATE_NOT_EXTERNAL_FACT",
)
CONFIDENCE_CLASSES = (
    "HIGH_OFFICIAL_LOCATOR",
    "MEDIUM_REPUTABLE_TECHNICAL_SOURCE",
    "MEDIUM_PUBLIC_RESEARCH",
    "LOW_SOCIAL_WEB_SIGNAL",
    "LOW_OWNER_DEFAULT_CANDIDATE",
)

AGENT_PATHS = (
    "QKU_DATA_ACQUISITION_AGENT",
    "QKU_FORMULA_COMPUTE_ENGINE",
    "FORMULA_ALGORITHM_RUNTIME_CANDIDATE_MODE",
    "FEATURE_BUILDER",
    "PARAMETER_STACK_AGENT",
    "REPLAY_PAPER_CANDIDATE_ROUTER",
    "REPLAY_ENGINE_INPUT_PREP",
    "PAPER_ENGINE_INPUT_PREP",
    "REPLAY_PAPER_RESULT_ANALYZER_INPUT_PREP",
    "RISK_MANAGER_CANDIDATE_REVIEW",
    "CAPITAL_SIZING_CANDIDATE_REVIEW",
    "QUANTUM_ADVISORY_AGENT",
    "QUANTUM_EXECUTION_HARNESS",
    "QUANTUM_CLASSICAL_HYBRID_COMPARATOR",
    "STRATEGY_SIGNAL_DECISION_AGENT_CANDIDATE_INTENT",
    "EXECUTION_ROUTER_NON_AUTHORITY_PREVIEW",
    "OWNER_REVIEW_OPTIONAL",
)
AGENT_ROUTE_STATUSES = (
    "AGENT_ROUTED_CANDIDATE",
    "AGENT_ROUTED_PARTIAL",
    "AGENT_ROUTED_REPLAY_PAPER_CANDIDATE",
    "AGENT_ROUTED_NEEDS_FIELD_FILL",
    "AGENT_ROUTED_NEEDS_NORMALIZATION",
    "AGENT_ROUTED_QUANTUM_CANDIDATE",
    "AGENT_ROUTED_QUANTUM_LOCAL_SMOKE_READY",
    "AGENT_ROUTED_QUANTUM_LOCAL_SMOKE_EXECUTED",
    "AGENT_ROUTED_RISK_CAPITAL_CANDIDATE",
    "AGENT_ROUTED_OWNER_REVIEW_OPTIONAL",
)
DISALLOWED_ROUTE_STATUSES = (
    "AGENT_ROUTE_BLOCKED_REQUIRED_FIELDS_MISSING",
    "AGENT_ROUTE_BLOCKED_STRICT_COVERAGE_MISSING",
    "EXECUTION_ROUTER_ORDER_READY",
    "LIVE_PROMOTION_READY",
    "PROFIT_EVIDENCE_READY",
    "QUANTUM_LIVE_ORDER_READY",
    "QUANTUM_ADVANTAGE_READY",
)

QUANTUM_EXECUTION_MODES = (
    "QUANTUM_DESCRIPTOR_ONLY",
    "QUANTUM_LOCAL_EXACT_SMOKE",
    "QUANTUM_LOCAL_SIMULATOR_IF_AVAILABLE",
    "QUANTUM_PROVIDER_DRY_RUN",
    "QUANTUM_REMOTE_SIMULATOR_REPLAY_PAPER_ONLY",
    "QUANTUM_REMOTE_HARDWARE_REPLAY_PAPER_ONLY",
)
FORBIDDEN_QUANTUM_MODES = (
    "QUANTUM_LIVE_ORDER_SUBMISSION",
    "QUANTUM_DIRECT_EXECUTION_ROUTER_WRITE",
    "QUANTUM_LIVE_PRETRADE_REMOTE_DEPENDENCY",
    "QUANTUM_PROFIT_EVIDENCE_CLAIM",
    "QUANTUM_ADVANTAGE_EVIDENCE_CLAIM",
    "QUANTUM_LATENCY_SUPERIORITY_CLAIM",
    "QUANTUM_EXECUTION_SUPERIORITY_CLAIM",
)

MANDATORY_INPUT_REFS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "src/qtt/stage1_prediction_markets/launch_readiness/day1_launch_readiness_roadmap_policy.py",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json",
    "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json",
    "docs/master_plan/generated/PR161C_QKUMasterInventoryBridge.report.json",
    "docs/master_plan/generated/PR161C_QKUCanonicalRegistry.report.json",
    "docs/master_plan/generated/PR161C_QKU9360PrimaryMaterializationRegistry.report.json",
    "docs/master_plan/generated/PR161C_QKUOrchestrationGraph.report.json",
    "docs/master_plan/generated/PR161C_QKUOrchestrationGraphEdges.report.json",
    "docs/master_plan/generated/PR161C_QKUGraphQualityMetrics.report.json",
    "docs/master_plan/generated/PR161D_QKUQualityScoreRegistry.report.json",
    "docs/master_plan/generated/PR161D_QKUReplayPaperPriorityQueue.report.json",
    "docs/master_plan/generated/PR161D_QKUReplayPaperScenarioInputs.report.json",
    "docs/master_plan/generated/PR161D_QKUScenarioOutcomeMatrix.report.json",
    "docs/master_plan/generated/PR161D_QKUCombinationCandidateRegistry.report.json",
    "docs/master_plan/generated/PR161D_QKUCombinationReplayPaperPriorityQueue.report.json",
    "docs/master_plan/generated/PR161D_QKUAgentTaskQueue.report.json",
    "docs/master_plan/generated/PR161D_QKUAgentGraphRoutingMatrix.report.json",
    "docs/master_plan/generated/PR161D_QKUMarketBundleActivationPolicy.report.json",
    "docs/master_plan/generated/PR161E_ReplayPaperOutcomeCaptureRegistry.report.json",
    "docs/master_plan/generated/PR161E_QKUReplayPaperProfitabilityLedger.report.json",
    "docs/master_plan/generated/PR161E_QKUScenarioResultAttribution.report.json",
    "docs/master_plan/generated/PR161E_QuantumClassicalHybridOutcomeComparison.report.json",
    "docs/master_plan/generated/PR161E_AgentOutcomeTaskQueue.report.json",
    "docs/master_plan/generated/PR161E_OwnerReviewResultPromotionQueue.report.json",
    "docs/master_plan/generated/PR161F_ExecutorInputRegistry.report.json",
    "docs/master_plan/generated/PR161F_ReplayRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PaperRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PairedReplayPaperRunPlan.report.json",
    "docs/master_plan/generated/PR161F_RunArtifactEnvelopeRegistry.report.json",
    "docs/master_plan/generated/PR161F_ResultPacketEmissionEligibilityGate.report.json",
    "docs/master_plan/generated/PR161F_QKUEndToEndTraceabilityMatrix.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentWorkflowOrchestrationContract.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentRoleIOContract.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentHandoffMatrix.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentFailureResponseMatrix.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentCommunicationProtocol.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentKPIReadinessBridge.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentRetryRerouteQuarantinePolicy.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentOwnerEscalationQueue.report.json",
    "docs/master_plan/generated/PR161F_QuantumClassicalHybridRunPlan.report.json",
    "docs/master_plan/generated/PR162_ReplayDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162_PaperDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162_RealNonLiveRunArtifactCandidateRegistry.report.json",
    "docs/master_plan/generated/PR162_QKUArtifactCoverageBridge.report.json",
    "docs/master_plan/generated/PR162_QKUQuantumExecutionReadinessBridge.report.json",
    "docs/master_plan/generated/PR162_QKUQuantumProblemEncodingBlueprint.report.json",
    "docs/master_plan/generated/PR162_QuantumParameterRangeCandidateRegistry.report.json",
    "docs/master_plan/generated/PR162_QuantumBackendFitCandidateMatrix.report.json",
    "docs/master_plan/generated/PR162_QuantumClassicalHybridArtifactInputBridge.report.json",
    "docs/master_plan/generated/PR162_QuantumClassicalHybridComparatorBlueprint.report.json",
    "docs/master_plan/generated/PR162_QuantumReplayPaperWorkOrderQueue.report.json",
    "docs/master_plan/generated/PR162_QKUQuantumDownstreamAgentRouteMatrix.report.json",
    "docs/master_plan/generated/PR162A_DatasetMaterializationManifest.report.json",
    "docs/master_plan/generated/PR162A_NormalizedDatasetInventory.report.json",
    "docs/master_plan/generated/PR162A_MarketScenarioQKUMappingMatrix.report.json",
    "docs/master_plan/generated/PR162A_PR161FRunPlanDatasetCoverageBridge.report.json",
    "docs/master_plan/generated/PR162A_PR162AdapterRerunReadinessBridge.report.json",
    "docs/master_plan/generated/PR162A_QuantumQKUDatasetFeatureBridge.report.json",
    "docs/master_plan/generated/PR162A_QuantumFeatureMaterializationWorkOrderQueue.report.json",
    "docs/master_plan/generated/PR162A_QTTAgentDatasetHandoffBridge.report.json",
    "docs/master_plan/generated/PR162B_QKUExecutionClassificationAudit.report.json",
    "docs/master_plan/generated/PR162B_QKUFormulaRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUAlgorithmRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUObjectiveFunctionRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUConstraintRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUParameterValueRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUParameterRangeScaleRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUTradableValueCandidateRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUSolverMappingRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUExecutableComputeContractRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUFormulaTestVectorRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUAlgorithmTestVectorRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUFormulaBindingProofMatrix.report.json",
    "docs/master_plan/generated/PR162B_QKUMarketClassificationRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUStage1PredictionMarketActivationGate.report.json",
    "docs/master_plan/generated/PR162B_QKUDormancyRegistry.report.json",
    "docs/master_plan/generated/PR162B_QTTAgentStage1QKUActivationAllowlist.report.json",
    "docs/master_plan/generated/PR162B_QuantumQUBOIsingFormulaMaterialization.report.json",
    "docs/master_plan/generated/PR162B_QuantumSolverSmokeExecutionReport.report.json",
    "docs/master_plan/generated/PR162B_PR162CDataRequirementHandoff.report.json",
    "docs/master_plan/generated/PR162C_FinalSummary.report.json",
    "docs/master_plan/generated/PR162C_DataRequirementClassificationLedger.report.json",
    "docs/master_plan/generated/PR162C_QKUInputFieldCoverageMatrix.report.json",
    "docs/master_plan/generated/PR162C_QKUFormulaToDatasetBindingMatrix.report.json",
    "docs/master_plan/generated/PR162C_QKUFormulaToAgentRouteMatrix.report.json",
    "docs/master_plan/generated/PR162C_QTTAgentExecutableQKURoutingMatrix.report.json",
    "docs/master_plan/generated/PR162C_QTTAgentDatasetConsumerRoutingMatrix.report.json",
    "docs/master_plan/generated/PR162C_OwnerMaterializationCommandQueue.report.json",
    "docs/master_plan/generated/PR162C_SourcePortfolioRegistry.report.json",
    "docs/master_plan/generated/PR162C_SourceDiscoveryLedger.report.json",
    "docs/master_plan/generated/PR162C_NormalizedDatasetInventory.report.json",
    "docs/master_plan/generated/PR162C_StrictQKUCoverageProofMatrix.report.json",
    "docs/master_plan/generated/PR162C_PR162RAdapterRerunReadinessBridge.report.json",
    "docs/master_plan/generated/PR162C_PR163ReadinessBlockerStatus.report.json",
    "tools/currentize_pr152_after_generated_artifacts.py",
    "tools/run_validation_gates.py",
    "tools/validate_grand_global_debug_logical_consistency_audit.py",
    "tools/ci_branch_context.py",
)
