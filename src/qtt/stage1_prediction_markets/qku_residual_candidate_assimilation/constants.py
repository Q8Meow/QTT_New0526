"""Central PR161C QKU policy, taxonomy, paths, and authority boundaries."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR161C"
EXPECTED_BRANCH = "pr161c-qku-residual-candidate-assimilation-fill-campaign"
EXPECTED_BASE_MAIN_MERGE_COMMIT = "fa46374"
SUCCESS_MARKER = "QTT_PR161C_QKU_RESIDUAL_CANDIDATE_ASSIMILATION_OK"
PREFLIGHT_RECEIPT_MARKER = "PR161C_QKU_RESIDUAL_ASSIMILATION_PREFLIGHT_RECEIPT"
STATE_MISMATCH_MARKER = "PR161C_STATE_MISMATCH_REPORT"

EXPECTED_PR161A_ENTITY_QKUS = 4525
EXPECTED_PR161A_ATOMICROW_QKUS = 4183
EXPECTED_PR161A_PR154_QKUS = 342
EXPECTED_PR161B_RESIDUAL_QKUS = 4835
EXPECTED_PRIMARY_QKU_SOURCE_MEMBERSHIP_RECORDS = 9360
EXPECTED_PR161A_FIELD_VALUE_FACETS = 22625
EXPECTED_EXPANDED_QKU_AND_FIELD_FACET_RECORDS = 31985
EXPECTED_PR161B_QUANTUM_RESIDUALS = 1324
EXPECTED_PR161B_QUBO_RESIDUALS = 23
EXPECTED_PR161B_ISING_RESIDUALS = 11
EXPECTED_PR161B_QAOA_RESIDUALS = 12
EXPECTED_PR161B_VQE_RESIDUALS = 8
EXPECTED_PR161B_ANNEALING_RESIDUALS = 40
EXPECTED_PR161B_HYBRID_QUANTUM_CLASSICAL_RESIDUALS = 7
GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES = 50 * 1024 * 1024

PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/qku_residual_candidate_assimilation"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr161c_qku_report_shards"
BRANCH_CONTEXT_POLICY_PATH = Path("tools/ci_branch_context.py")
RUN_VALIDATION_GATES_PATH = Path("tools/run_validation_gates.py")
MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")
PR152_AUDIT_REPORT_PATH = (
    GENERATED_DIR / "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
)

PR161A_REPORT_PATHS = {
    "atomicrows_entity": GENERATED_DIR / "PR161A_AtomicRowsEntityValueStateInventory.report.json",
    "pr154_entity": GENERATED_DIR / "PR161A_PR154EntityValueStateInventory.report.json",
    "field_value": GENERATED_DIR / "PR161A_FieldValueRecordInventory.report.json",
    "final_summary": GENERATED_DIR / "PR161A_FinalValueStateSummary.report.json",
    "quantum_profiles": GENERATED_DIR / "PR161A_QuantumOptimizerCandidateProfileRegistry.report.json",
    "replay_queue": GENERATED_DIR / "PR161A_ReplayPaperCandidateMaterializationQueue.report.json",
}

PR161B_REPORT_PATHS = {
    "assimilation_queue": GENERATED_DIR / "PR161B_PR161CAssimilationQueue.report.json",
    "field_coverage": GENERATED_DIR / "PR161B_MasterPlanToPR161AFieldRecordCoverage.report.json",
    "final_summary": GENERATED_DIR / "PR161B_ResidualCoverageFinalSummary.report.json",
    "candidate_inventory": GENERATED_DIR / "PR161B_MasterPlanResidualCandidateInventory.report.json",
    "orchestration_graph": GENERATED_DIR / "PR161B_EndToEndCandidateOrchestrationGraph.report.json",
    "upstream_traceability": GENERATED_DIR / "PR161B_UpstreamArtifactTraceabilityMatrix.report.json",
    "downstream_workflow": GENERATED_DIR / "PR161B_DownstreamWorkflowConsumerMatrix.report.json",
    "agent_consumption": GENERATED_DIR / "PR161B_QTTAgentCandidateConsumptionMatrix.report.json",
    "quantum_optimizer": GENERATED_DIR / "PR161B_QuantumOptimizerResidualCoverage.report.json",
    "parameter_range": GENERATED_DIR / "PR161B_ParameterRangeResidualCoverage.report.json",
    "formula_algorithm": GENERATED_DIR / "PR161B_FormulaAlgorithmResidualCoverage.report.json",
    "section_search": GENERATED_DIR / "PR161B_MasterPlanSectionSearchCoverage.report.json",
    "atomicrows_residual": GENERATED_DIR / "PR161B_AtomicRowsResidualCoverage.report.json",
    "pr154_residual": GENERATED_DIR / "PR161B_PR154ResidualCoverage.report.json",
    "replay_paper_route": GENERATED_DIR / "PR161B_ReplayPaperRouteResidualCoverage.report.json",
    "quantum_strategy": GENERATED_DIR / "PR161B_QuantumStrategyResidualCoverage.report.json",
    "quantum_assimilation_queue": GENERATED_DIR / "PR161B_PR161CQuantumAssimilationQueue.report.json",
}

CONTROL_PLANE_PATHS = {
    "pr_identity_roster": Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"),
    "roadmap_execution_state_controller": Path(
        "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"
    ),
    "day1_launch_readiness_roadmap": Path(
        "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"
    ),
    "day1_launch_readiness_policy": Path(
        "src/qtt/stage1_prediction_markets/launch_readiness/"
        "day1_launch_readiness_roadmap_policy.py"
    ),
    "pr136_route_triage": GENERATED_DIR / "PR136RouteTriage.report.json",
    "pr136_section_crosswalk_requested": GENERATED_DIR
    / "PR136MasterPlanSectionCrosswalk.report.json",
    "pr136_section_crosswalk_fallback": GENERATED_DIR
    / "PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "pr136_market_index": GENERATED_DIR
    / "PR136MarketSpecificLaunchReadinessIndex.report.json",
    "pr136_command_action": GENERATED_DIR / "PR136CommandActionMatrix.report.json",
    "pr137r_atomicrows_reconciliation": GENERATED_DIR
    / "PR137R_AtomicRowsBundleReconciliation.report.json",
    "pr138_atomicrows_contract": GENERATED_DIR
    / "PR138_AtomicRowsSemanticRowContract.report.json",
}

PR82_PR96_ARTIFACT_NAMES = (
    "QuantumApplicabilityClassificationRegistry.report.json",
    "OwnerQuantumPriorityPolicyRegistry.report.json",
    "ParameterAlgorithmScoringPolicyRegistry.report.json",
    "ParameterStackScoringAndRankingGate.report.json",
    "QuantumClassicalOptimizerArbitrationGate.report.json",
    "CandidateParameterStackGenerationGate.report.json",
    "TradeContextParameterStackSelectionGate.report.json",
    "SelectedParameterStackHandoffPacket.report.json",
    "ReplayPaperCandidateStackCompetitionGate.report.json",
    "DualResultReviewForParameterStacks.report.json",
    "OwnerLivePromotionReviewForParameterStacks.report.json",
    "Stage1ConcurrentReplayPaperContractCheck.report.json",
    "Stage1DualResultReviewContractCheck.report.json",
    "Stage1OwnerLivePromotionReviewContractCheck.report.json",
)

PR161C_REPORT_FILENAMES = (
    "PR161C_QKU_RESIDUAL_ASSIMILATION_PREFLIGHT_RECEIPT.report.json",
    "PR161C_PR161APrimaryEntityDiagnostic.report.json",
    "PR161C_PR161AFieldValueFacetDiagnostic.report.json",
    "PR161C_PR161BQueueDiagnostic.report.json",
    "PR161C_PR161BToPR161AFieldCoverageDiagnostic.report.json",
    "PR161C_QKUSupplementalArtifactScout.report.json",
    "PR161C_QKUResidualTypeBreakdown.report.json",
    "PR161C_QKUResidualDiagnosticJustification.report.json",
    "PR161C_QKUFillLaneBreakdown.report.json",
    "PR161C_QKUAuthorityAndProvenanceBreakdown.report.json",
    "PR161C_QKUAgentAndWorkflowBreakdown.report.json",
    "PR161C_QKUMarketBreakdown.report.json",
    "PR161C_QKULaunchStageBreakdown.report.json",
    "PR161C_QKUClassicalQuantumHybridBreakdown.report.json",
    "PR161C_QKU9360PrimaryMaterializationRegistry.report.json",
    "PR161C_QKU22625FieldValueFacetLinkage.report.json",
    "PR161C_QKUExpandedRecordAccounting.report.json",
    "PR161C_QKUDefaultMaterializationCoverage.report.json",
    "PR161C_QKUNumericDefaultMaterialization.report.json",
    "PR161C_QKUFormulaDefaultMaterialization.report.json",
    "PR161C_QKUAlgorithmConfigMaterialization.report.json",
    "PR161C_QKUOptimizerDefaultMaterialization.report.json",
    "PR161C_QKUOwnerFallbackDefaultMaterialization.report.json",
    "PR161C_QKUOnlineSourceMaterialization.report.json",
    "PR161C_QKUAgentLaunchReadinessMaterialization.report.json",
    "PR161C_QKUCanonicalRegistry.report.json",
    "PR161C_QKUAliasMap.report.json",
    "PR161C_QKUTypeTaxonomy.report.json",
    "PR161C_QKUResidualAssimilationRegistry.report.json",
    "PR161C_QKUResidualAssimilationDelta.report.json",
    "PR161C_QKUFormulaAlgorithmAssimilation.report.json",
    "PR161C_QKUParameterRangeAssimilation.report.json",
    "PR161C_QKUQuantumAssimilation.report.json",
    "PR161C_QKUQuantumResidualTrace.report.json",
    "PR161C_QKUClassicalHybridAssimilation.report.json",
    "PR161C_QKUReplayPaperRouteBridge.report.json",
    "PR161C_QKUAgentConsumptionBridge.report.json",
    "PR161C_QKUUpstreamDownstreamTraceability.report.json",
    "PR161C_QKUWorkflowProcessBridge.report.json",
    "PR161C_QKUDownstreamPRFileBridge.report.json",
    "PR161C_QKUOrchestrationCompleteness.report.json",
    "PR161C_QKUOrchestrationGraph.report.json",
    "PR161C_QKUOrchestrationGraphEdges.report.json",
    "PR161C_QKUOrchestrationGraphCompleteness.report.json",
    "PR161C_QKUGraphQualityMetrics.report.json",
    "PR161C_QKUIsolatedNodeAudit.report.json",
    "PR161C_QKUSourceUpgradeQueue.report.json",
    "PR161C_QKUOnlineScoutQueue.report.json",
    "PR161C_QKUSourceIntakeAcceptancePolicy.report.json",
    "PR161C_QKUOnlineRetrievalAudit.report.json",
    "PR161C_QKUMasterInventoryBridge.report.json",
    "PR161C_QKUAtomicRowsCompatibilityBridge.report.json",
    "PR161C_QKUPR154CompatibilityBridge.report.json",
    "PR161C_QKUMarketClassificationInventory.report.json",
    "PR161C_QKULaunchStageClassification.report.json",
    "PR161C_QKUClassicalQuantumHybridInventory.report.json",
    "PR161C_QKUAlgorithmFormulaStrategyInventory.report.json",
    "PR161C_QKUQuantumForwardOptimizationInventory.report.json",
    "PR161C_QKUAgentRetrievalIndex.report.json",
    "PR161C_QKUStage1PredictionMarketRetrievalIndex.report.json",
    "PR161C_QKUStage1Day1LaunchPrepIndex.report.json",
    "PR161C_QKUCrossMarketReuseIndex.report.json",
    "PR161C_QKURangeOptimizerMaterializationAudit.report.json",
    "PR161C_QKUFallbackDefaultExhaustionAudit.report.json",
    "PR161C_QKUFinalAssimilationSummary.report.json",
    "PR161C_ForbiddenAuthorityScan.report.json",
    "PR161C_NoScatteredHardcodedAuthorityAudit.report.json",
    "PR161C_QKUReportShardManifest.report.json",
    "PR161C_BranchContextAndDeterministicAudit.report.json",
)
REPORT_PATHS = {
    filename.removesuffix(".report.json").lower(): GENERATED_DIR / filename
    for filename in PR161C_REPORT_FILENAMES
}

QKU_TYPES = (
    "ATOMICROW_QKU",
    "PR154_TARGET_QKU",
    "FIELD_VALUE_FACET_QKU",
    "PARAMETER_QKU",
    "FORMULA_QKU",
    "ALGORITHM_QKU",
    "RANGE_QKU",
    "SCALE_QKU",
    "DEFAULT_VALUE_QKU",
    "CONSTRAINT_QKU",
    "SIGNAL_QKU",
    "FEATURE_QKU",
    "RISK_QKU",
    "CAPITAL_QKU",
    "EXECUTION_QKU",
    "LATENCY_QKU",
    "MARKET_MICROSTRUCTURE_QKU",
    "SOURCE_RECORD_QKU",
    "REPLAY_CANDIDATE_QKU",
    "PAPER_CANDIDATE_QKU",
    "QUANTUM_CANDIDATE_QKU",
    "CLASSICAL_CANDIDATE_QKU",
    "HYBRID_CANDIDATE_QKU",
    "AGENT_BINDING_QKU",
    "MATERIALIZATION_QKU",
    "METADATA_QKU",
    "RESIDUAL_CANDIDATE_QKU",
    "STRATEGY_TEMPLATE_QKU",
    "OPTIMIZER_SETTING_QKU",
    "OWNER_POLICY_QKU",
    "CONNECTOR_FUTURE_QKU",
    "LIVE_FUTURE_QKU",
    "DOCTRINE_ONLY_QKU",
    "SOURCE_UPGRADE_QKU",
    "ONLINE_SCOUT_QKU",
    "FUTURE_RUNTIME_ONLY_QKU",
)
QKU_STATES = (
    "QKU_MATERIALIZED_ACTIVE",
    "QKU_ALIAS_MAPPED",
    "QKU_DOCTRINE_ONLY_MATERIALIZED",
    "QKU_SOURCE_UPGRADE_READY",
    "QKU_ONLINE_SCOUT_READY",
    "QKU_FUTURE_RUNTIME_ROUTE_MATERIALIZED",
    "QKU_UNSAFE_REJECTED",
    "QKU_SECRET_REJECTED",
)
QKU_AUTHORITY_CLASSES = (
    "OWNER_AUTHORIZED_INTERNAL_QKU",
    "MASTER_PLAN_LITERAL_QKU",
    "PRIOR_PR_ARTIFACT_QKU",
    "PR136_ORCHESTRATION_QKU",
    "ATOMICROWS_COMPATIBLE_QKU",
    "PR154_COMPATIBLE_QKU",
    "PUBLIC_SOURCE_RETRIEVED_QKU",
    "NON_OFFICIAL_RESEARCH_QKU",
    "SOCIAL_SIGNAL_QKU",
    "GITHUB_PATTERN_QKU",
    "INSTITUTIONAL_STYLE_CANDIDATE_QKU",
    "OPTIMIZER_DEFAULT_CANDIDATE_QKU",
    "QUANTUM_FORWARD_CANDIDATE_QKU",
    "CLASSICAL_BASELINE_CANDIDATE_QKU",
    "HYBRID_ARBITRATION_CANDIDATE_QKU",
    "REPLAY_PAPER_TESTABLE_QKU",
    "AGENT_RETRIEVAL_READY_QKU",
    "OWNER_REVIEW_READY_QKU",
    "SOURCE_UPGRADE_OPTIONAL_QKU",
    "FUTURE_RUNTIME_ONLY_QKU",
    "UNSAFE_REJECTED_QKU",
    "SECRET_REJECTED_QKU",
)
QKU_SOURCE_PROVENANCE_CLASSES = (
    "PR161A_ENTITY_PROVENANCE",
    "PR161A_FIELD_VALUE_PROVENANCE",
    "PR161B_RESIDUAL_PROVENANCE",
    "PR136_ORCHESTRATION_PROVENANCE",
    "PR137R_PR138_COMPATIBILITY_PROVENANCE",
    "PR154_COMPATIBILITY_PROVENANCE",
    "PRIOR_PR_ARTIFACT_PROVENANCE",
    "MASTER_PLAN_LITERAL_PROVENANCE",
    "OWNER_TEXT_PROVENANCE",
    "QTT_DEFAULT_POLICY_PROVENANCE",
    "ONLINE_SCOUT_PENDING_PROVENANCE",
)
QKU_SOURCE_CLASSES = (
    "OWNER_PROVIDED_SOURCE",
    "MASTER_PLAN_LITERAL_SOURCE",
    "PRIOR_PR_ARTIFACT_SOURCE",
    "PR136_ORCHESTRATION_SOURCE",
    "ATOMICROWS_COMPATIBILITY_SOURCE",
    "PR154_COMPATIBILITY_SOURCE",
    "OFFICIAL_PUBLIC_SOURCE",
    "NON_OFFICIAL_PUBLIC_RESEARCH_SOURCE",
    "ACADEMIC_PUBLIC_SOURCE",
    "INSTITUTIONAL_PUBLIC_SOURCE",
    "BLOG_PUBLIC_SOURCE",
    "FORUM_PUBLIC_SOURCE",
    "SOCIAL_PUBLIC_SOURCE",
    "NEWS_PUBLIC_SOURCE",
    "GITHUB_PUBLIC_SOURCE",
    "PUBLIC_CODE_PATTERN_SOURCE",
    "OPTIMIZER_LIBRARY_DOC_SOURCE",
    "QUANTUM_LIBRARY_DOC_SOURCE",
    "CLASSICAL_BASELINE_REFERENCE_SOURCE",
    "HYBRID_ARBITRATION_REFERENCE_SOURCE",
    "UNKNOWN_PUBLIC_SOURCE",
    "UNSAFE_REJECTED_SOURCE",
    "SECRET_REJECTED_SOURCE",
)
QKU_SOURCE_ACCEPTANCE_STATES = (
    "SOURCE_ACCEPTED_FOR_QKU_CANDIDATE_USE",
    "SOURCE_ACCEPTED_FOR_DEFAULT_MATERIALIZATION",
    "SOURCE_ACCEPTED_FOR_RESEARCH_USE",
    "SOURCE_ACCEPTED_FOR_REPLAY_PAPER_TESTING",
    "SOURCE_ACCEPTED_FOR_AGENT_RETRIEVAL",
    "SOURCE_ACCEPTED_FOR_OWNER_REVIEW",
    "SOURCE_ACCEPTED_FOR_SOURCE_UPGRADE_ROUTE",
    "SOURCE_ACCEPTED_FOR_ONLINE_SCOUT_QUEUE",
    "SOURCE_ACCEPTED_FOR_QKU_GRAPH_LINKAGE",
    "SOURCE_REJECTED_UNSAFE",
    "SOURCE_REJECTED_SECRET",
    "SOURCE_REJECTED_IRRELEVANT",
    "SOURCE_REJECTED_DUPLICATE_NO_NEW_ALIAS_VALUE",
    "SOURCE_REJECTED_UNMAPPABLE",
)
QKU_MARKET_CLASSES = (
    "PREDICTION_MARKET",
    "EQUITY_MARKET",
    "CRYPTO_MARKET",
    "FX_MARKET",
    "FUTURES_MARKET",
    "OPTIONS_MARKET",
    "FIXED_INCOME_MARKET",
    "COMMODITIES_MARKET",
    "MULTI_MARKET",
    "MARKET_AGNOSTIC",
    "FUTURE_MARKET_UNSPECIFIED",
)
QKU_LAUNCH_STAGES = (
    "STAGE1_PREDICTION_MARKET",
    "STAGE2_EQUITIES",
    "STAGE3_CRYPTO",
    "STAGE4_MULTI_ASSET",
    "FUTURE_MARKET_EXPANSION",
    "MARKET_AGNOSTIC_FOUNDATION",
    "DOCTRINE_ONLY_STAGELESS",
)
QKU_STAGE1_APPLICABILITY_CLASSES = (
    "STAGE1_DIRECTLY_APPLICABLE",
    "STAGE1_INDIRECTLY_APPLICABLE",
    "STAGE1_REPLAY_PAPER_ONLY",
    "STAGE1_SOURCE_UPGRADE_OPTIONAL",
    "STAGE1_NOT_APPLICABLE_FUTURE_MARKET",
    "STAGE1_DOCTRINE_ONLY",
)
QKU_COMPUTATIONAL_CLASSES = (
    "CLASSICAL_QKU",
    "QUANTUM_QKU",
    "QUANTUM_INSPIRED_QKU",
    "HYBRID_CLASSICAL_QUANTUM_QKU",
    "NOT_OPTIMIZER_RELEVANT_QKU",
    "COMPUTATIONAL_CLASS_UNCLEAR_QKU",
)
QKU_QUANTUM_SUBCLASSES = (
    "QUBO_QKU",
    "ISING_QKU",
    "QAOA_QKU",
    "VQE_QKU",
    "ANNEALING_QKU",
    "QUANTUM_PORTFOLIO_QKU",
    "QUANTUM_CAPITAL_ALLOCATION_QKU",
    "QUANTUM_MARKET_SELECTION_QKU",
    "QUANTUM_SIGNAL_COMBINATION_QKU",
    "QUANTUM_LATENCY_ROUTING_QKU",
    "QUANTUM_ARBITRAGE_PATH_QKU",
    "HYBRID_QUANTUM_CLASSICAL_QKU",
    "QUANTUM_ADVISORY_QKU",
)
QKU_TRADING_ROLES = (
    "SIGNAL",
    "FEATURE",
    "RISK",
    "CAPITAL",
    "EXECUTION",
    "LATENCY",
    "SCORING",
    "RANKING",
    "OPTIMIZER",
    "PARAMETER_STACK",
    "MARKET_SELECTION",
    "POSITION_SIZING",
    "ARBITRAGE",
    "SIGNAL_COMBINATION",
    "RISK_CONTROL",
    "SOURCE_RECORD",
    "REPLAY_PAPER",
    "OWNER_REVIEW",
    "METADATA_DOCTRINE",
)
QKU_FILL_LANES = tuple(f"LANE_{idx}" for idx in range(22))
QKU_MATERIALIZATION_STATES = (
    "MATERIALIZED_NUMERIC_DEFAULT",
    "MATERIALIZED_RANGE_DEFAULT",
    "MATERIALIZED_FORMULA_DEFAULT",
    "MATERIALIZED_ALGORITHM_CONFIG",
    "MATERIALIZED_OPTIMIZER_CONFIG",
    "MATERIALIZED_STRATEGY_TEMPLATE",
    "MATERIALIZED_QUANTUM_CANDIDATE_CONFIG",
    "MATERIALIZED_CLASSICAL_BASELINE_CONFIG",
    "MATERIALIZED_HYBRID_ARBITRATION_CONFIG",
    "MATERIALIZED_CATEGORICAL_DEFAULT",
    "MATERIALIZED_AGENT_ROUTE",
    "MATERIALIZED_UPSTREAM_DOWNSTREAM_ROUTE",
    "MATERIALIZED_QKU_GRAPH_EDGE_ROUTE",
    "MATERIALIZED_REPLAY_PAPER_ROUTE",
    "MATERIALIZED_SOURCE_RETRIEVAL_RECORD",
    "MATERIALIZED_OWNER_POLICY_RECORD",
    "MATERIALIZED_DOCTRINE_RECORD",
    "MATERIALIZED_FIELD_VALUE_FACET",
    "MATERIALIZED_FUTURE_RUNTIME_ROUTE",
    "MATERIALIZED_UNSAFE_REJECTION_RECORD",
    "MATERIALIZED_SECRET_REJECTION_RECORD",
)
QKU_MATERIALIZATION_PRIORITY_LADDER = tuple(range(16))
QKU_RESIDUAL_DIAGNOSTIC_CLASSES = (
    "TRUE_NEW_QKU_REQUIRED",
    "PR161A_ALIAS_REPAIR_QKU",
    "PR161A_FIELD_MATCH_MISSING_INDEX_QKU",
    "DOCTRINE_ONLY_QKU",
    "DUPLICATE_QKU_ALIAS",
    "SOURCE_UPGRADE_OPTIONAL_QKU",
    "ONLINE_SCOUT_QKU",
    "FUTURE_RUNTIME_ONLY_QKU",
    "UNSAFE_OR_SECRET_REJECTED_QKU",
)
QKU_UPSTREAM_LINKAGE_CLASSES = (
    "MASTER_PLAN_SECTION_UPSTREAM",
    "PR161A_ENTITY_UPSTREAM",
    "PR161A_FIELD_VALUE_UPSTREAM",
    "PR161B_RESIDUAL_UPSTREAM",
    "PR136_ROUTE_TRIAGE_UPSTREAM",
    "PR136_SECTION_CROSSWALK_UPSTREAM",
    "PR136_MARKET_INDEX_UPSTREAM",
    "PR136_COMMAND_ACTION_UPSTREAM",
    "PR137R_ATOMICROWS_RECONCILIATION_UPSTREAM",
    "PR138_ATOMICROWS_SEMANTIC_CONTRACT_UPSTREAM",
    "PR154_TARGET_UPSTREAM",
    "PRIOR_PR_ARTIFACT_UPSTREAM",
    "ONLINE_SOURCE_UPSTREAM",
    "OWNER_TEXT_UPSTREAM",
    "QTT_DEFAULT_POLICY_UPSTREAM",
)
QKU_DOWNSTREAM_LINKAGE_CLASSES = (
    "QTT_AGENT_CONSUMER_DOWNSTREAM",
    "STAGE1_PREDICTION_MARKET_DOWNSTREAM",
    "REPLAY_PAPER_ROUTE_DOWNSTREAM",
    "QUANTUM_ADVISORY_DOWNSTREAM",
    "CLASSICAL_BASELINE_DOWNSTREAM",
    "HYBRID_ARBITRATION_DOWNSTREAM",
    "OPTIMIZER_ARBITRATION_DOWNSTREAM",
    "EDGE_PARAMETER_STACK_DOWNSTREAM",
    "ATOMICROWS_COMPATIBILITY_DOWNSTREAM",
    "PR154_COMPATIBILITY_DOWNSTREAM",
    "SOURCE_INTAKE_DOWNSTREAM",
    "OWNER_REVIEW_DOWNSTREAM",
    "VALIDATOR_DOWNSTREAM",
    "REPORT_DOWNSTREAM",
    "FUTURE_PR_DOWNSTREAM",
    "FUTURE_LIVE_GATE_DOWNSTREAM",
)
QKU_GRAPH_EDGE_TYPES = (
    "UPSTREAM_MASTER_PLAN_SECTION",
    "UPSTREAM_PR161A_ENTITY",
    "UPSTREAM_PR161A_FIELD_VALUE_FACET",
    "UPSTREAM_PR161B_RESIDUAL",
    "UPSTREAM_PR136_ROUTE_TRIAGE",
    "UPSTREAM_PR136_SECTION_CROSSWALK",
    "UPSTREAM_PR136_MARKET_INDEX",
    "UPSTREAM_PR136_COMMAND_ACTION",
    "UPSTREAM_PR137R_ATOMICROWS_RECONCILIATION",
    "UPSTREAM_PR138_ATOMICROWS_SEMANTIC_CONTRACT",
    "UPSTREAM_PR154_TARGET",
    "UPSTREAM_PRIOR_PR_ARTIFACT",
    "UPSTREAM_ONLINE_SOURCE",
    "UPSTREAM_OWNER_TEXT",
    "UPSTREAM_QTT_DEFAULT_POLICY",
    "UPSTREAM_PR161C_FALLBACK_MATERIALIZATION_POLICY",
    "UPSTREAM_ONLINE_SCOUT_PENDING_ROUTE",
    "UPSTREAM_SUPPLEMENTAL_ARTIFACT_SCOUT_ROUTE",
    "DOWNSTREAM_QTT_AGENT",
    "DOWNSTREAM_AGENT_ROLE",
    "DOWNSTREAM_USER",
    "DOWNSTREAM_WORKFLOW",
    "DOWNSTREAM_PROCESS",
    "DOWNSTREAM_PR",
    "DOWNSTREAM_FILE",
    "DOWNSTREAM_REPORT",
    "DOWNSTREAM_VALIDATOR",
    "DOWNSTREAM_REPLAY_PAPER_ROUTE",
    "DOWNSTREAM_QUANTUM_ADVISORY",
    "DOWNSTREAM_CLASSICAL_BASELINE",
    "DOWNSTREAM_HYBRID_ARBITRATION",
    "DOWNSTREAM_OPTIMIZER_ARBITRATION",
    "DOWNSTREAM_EDGE_PARAMETER_STACK",
    "DOWNSTREAM_ATOMICROWS_COMPATIBILITY",
    "DOWNSTREAM_PR154_COMPATIBILITY",
    "DOWNSTREAM_STAGE1_PREDICTION_MARKET",
    "DOWNSTREAM_OWNER_REVIEW",
    "DOWNSTREAM_FUTURE_LIVE_GATE",
    "DOWNSTREAM_AGENT_RETRIEVAL_INDEX",
    "DOWNSTREAM_STAGE1_LAUNCH_PREP_INDEX",
    "DOWNSTREAM_REPLAY_PAPER_QUEUE",
    "DOWNSTREAM_OWNER_REVIEW_QUEUE",
    "DOWNSTREAM_SOURCE_INTAKE_QUEUE",
    "DOWNSTREAM_FUTURE_PR_REVIEW_QUEUE",
)
QKU_GRAPH_NODE_TYPES = (
    "PRIMARY_QKU_NODE",
    "FIELD_VALUE_FACET_NODE",
    "SUPPLEMENTAL_SCOUT_NODE",
)
QKU_GRAPH_FALLBACK_ROUTES = (
    "UPSTREAM_QTT_DEFAULT_POLICY",
    "UPSTREAM_OWNER_TEXT",
    "UPSTREAM_PR161C_FALLBACK_MATERIALIZATION_POLICY",
    "UPSTREAM_ONLINE_SCOUT_PENDING_ROUTE",
    "UPSTREAM_SUPPLEMENTAL_ARTIFACT_SCOUT_ROUTE",
    "DOWNSTREAM_AGENT_RETRIEVAL_INDEX",
    "DOWNSTREAM_STAGE1_LAUNCH_PREP_INDEX",
    "DOWNSTREAM_REPLAY_PAPER_QUEUE",
    "DOWNSTREAM_OWNER_REVIEW_QUEUE",
    "DOWNSTREAM_SOURCE_INTAKE_QUEUE",
    "DOWNSTREAM_FUTURE_PR_REVIEW_QUEUE",
)

FORBIDDEN_AUTHORITY_POLICY = {
    "forbidden_acceptance_states": (
        "SOURCE_ACCEPTED_AS_CONNECTOR_SEMANTIC",
        "SOURCE_ACCEPTED_AS_LIVE_ORDER_AUTHORITY",
        "SOURCE_ACCEPTED_AS_PROFIT_EVIDENCE",
        "SOURCE_ACCEPTED_AS_REPLAY_RESULT",
        "SOURCE_ACCEPTED_AS_PAPER_RESULT",
        "SOURCE_ACCEPTED_AS_OPTIMIZER_EXECUTION_RESULT",
        "SOURCE_ACCEPTED_AS_QUANTUM_BACKEND_EXECUTION_RESULT",
    ),
    "forbidden_evidence_fields": (
        "live_order_authority",
        "profit_evidence",
        "replay_result",
        "paper_result",
        "optimizer_execution_result",
        "quantum_backend_execution_result",
    ),
}
FORBIDDEN_ARTIFACT_POLICY = {
    "master_plan_edit_allowed": False,
    "global_rename_allowed": False,
    "atomicrows_final_bundle_creation_allowed": False,
    "generated_integrity_authority_allowed": False,
}
SOURCE_INTAKE_AUTHORITY_LADDER = (
    "SOURCE_ACCEPTED_FOR_QKU_CANDIDATE_USE",
    "SOURCE_ACCEPTED_FOR_DEFAULT_MATERIALIZATION",
    "SOURCE_ACCEPTED_FOR_REPLAY_PAPER_TESTING",
    "SOURCE_ACCEPTED_FOR_AGENT_RETRIEVAL",
    "SOURCE_ACCEPTED_FOR_OWNER_REVIEW",
)
OWNER_FALLBACK_DEFAULT_POLICY = {
    "boolean_capability_flag": False,
    "neutral_probability": 0.5,
    "neutral_multiplier": 1.0,
    "neutral_additive_score": 0.0,
    "minimum_positive_count": 1,
    "disabled_execution_flag": False,
    "replay_paper_required_flag": True,
    "default_unit": "dimensionless_candidate",
    "default_scale": "normalized_candidate_scale",
    "confidence_class": "OWNER_AUTHORIZED_CANDIDATE_DEFAULT_MEDIUM",
}

OWNER_APPROVALS = {
    "OWNER_GLOBAL_AUTHORITY": True,
    "OWNER_APPROVES_QKU_CANONICAL_UMBRELLA": True,
    "OWNER_APPROVES_NON_BREAKING_QKU_OVERLAY": True,
    "OWNER_APPROVES_NO_GLOBAL_RENAME_POLICY": True,
    "OWNER_APPROVES_PR161C_RESIDUAL_ASSIMILATION": True,
    "OWNER_APPROVES_9360_PRIMARY_QKU_SOURCE_MEMBERSHIP_TARGET": True,
    "OWNER_APPROVES_22625_PR161A_FIELD_VALUE_FACET_LINKING": True,
    "OWNER_APPROVES_EXPANDED_QKU_FIELD_FACET_RECORDING_IF_USEFUL": True,
    "OWNER_APPROVES_ALL_MASTER_PLAN_LISTED_CANDIDATES_FOR_QKU_CLASSIFICATION": True,
    "OWNER_APPROVES_ALL_MASTER_PLAN_LISTED_CANDIDATES_FOR_DEFAULT_MATERIALIZATION": True,
    "OWNER_APPROVES_ALL_PR161B_RESIDUALS_FOR_QKU_CLASSIFICATION": True,
    "OWNER_APPROVES_ALL_PR161B_RESIDUALS_FOR_DEFAULT_MATERIALIZATION": True,
    "OWNER_APPROVES_PR136_ORCHESTRATION_CONSUMPTION": True,
    "OWNER_APPROVES_PRIOR_PR_ARTIFACT_SCOUTING_FOR_QKU_CLASSIFICATION": True,
    "OWNER_APPROVES_OPEN_SOURCE_RESEARCH_SOCIAL_WEB_GITHUB_INTAKE_AS_QKU_SOURCES": True,
    "OWNER_APPROVES_NON_OFFICIAL_SOURCE_INTAKE_FOR_QKU_CANDIDATE_USE": True,
    "OWNER_REMOVES_OFFICIAL_SOURCE_ONLY_RESTRICTION_FOR_PR161C": True,
    "OWNER_APPROVES_ONLINE_SEARCH_FOR_QKU_DEFAULT_FILLING": True,
    "OWNER_APPROVES_MARKET_STAGE_CLASSIFICATION_FOR_ALL_QKUS": True,
    "OWNER_APPROVES_STAGE1_PREDICTION_MARKET_PRIORITIZATION_METADATA": True,
    "OWNER_APPROVES_QUANTUM_FORWARD_QKU_CLASSIFICATION": True,
    "OWNER_APPROVES_CLASSICAL_BASELINE_QKU_CLASSIFICATION": True,
    "OWNER_APPROVES_HYBRID_ARBITRATION_QKU_CLASSIFICATION": True,
    "OWNER_APPROVES_REPLAY_PAPER_ROUTE_FOR_TESTABLE_QKUS": True,
    "OWNER_APPROVES_DOWNSTREAM_QTT_AGENT_QKU_CONSUMPTION_FOR_APPROVED_NON_LIVE_LANES": True,
    "OWNER_APPROVES_UPSTREAM_DOWNSTREAM_QKU_ORCHESTRATION_LINKAGE": True,
    "OWNER_APPROVES_MANDATORY_QKU_ORCHESTRATION_GRAPH": True,
    "OWNER_APPROVES_NO_ISOLATED_NON_REJECTED_QKU_POLICY": True,
    "OWNER_APPROVES_QKU_MASTER_INVENTORY_BRIDGE": True,
    "OWNER_APPROVES_QKU_AGENT_LAUNCH_READINESS_DEFAULT_PAYLOADS": True,
}

NO_AUTHORITY_CONFIRMATION = {
    "live_order_execution_created": False,
    "private_account_state_or_balance_fetched": False,
    "replay_paper_result_created": False,
    "profit_evidence_created": False,
    "optimizer_execution_created": False,
    "quantum_backend_execution_created": False,
    "quantum_advantage_evidence_created": False,
    "global_existing_terms_renamed": False,
    "master_plan_file_edited": False,
}

KNOWN_AGENT_ROLES = (
    "QTT_RESEARCH_AGENT",
    "QTT_ATOMICROWS_ENRICHMENT_AGENT",
    "QTT_REPLAY_AGENT",
    "QTT_QUANTUM_ADVISORY_AGENT",
    "QTT_OPTIMIZER_ARBITRATION_AGENT",
    "QTT_CLASSICAL_BASELINE_AGENT",
    "QTT_HYBRID_ARBITRATION_AGENT",
    "QTT_OWNER_REVIEW_AGENT",
    "QTT_SOURCE_INTAKE_AGENT",
    "QTT_STAGE1_LAUNCH_PREP_AGENT",
    "QTT_AGENT_RETRIEVAL_INDEX",
)
KNOWN_WORKFLOW_STAGES = (
    "QKU_DEFAULT_MATERIALIZATION",
    "QKU_AGENT_RETRIEVAL",
    "STAGE1_PREDICTION_MARKET_LAUNCH_PREP",
    "REPLAY_PAPER_PREP",
    "OWNER_REVIEW",
    "SOURCE_UPGRADE",
    "FUTURE_LIVE_GATE",
)
