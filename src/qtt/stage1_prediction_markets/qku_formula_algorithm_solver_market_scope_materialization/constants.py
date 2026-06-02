"""Central PR162B policy constants.

This module is the single PR162B source for report names, controlled
taxonomies, blocker codes, authority flags, and branch/path scope.
"""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR162B"
PR_LABEL = "PR162B_QKU_FORMULA_ALGORITHM_SOLVER_MARKET_SCOPE_MATERIALIZATION_GATE"
EXPECTED_BRANCH = "pr162b-qku-formula-algorithm-solver-market-scope-materialization"
SUCCESS_MARKER = "PR162B_QKU_FORMULA_ALGORITHM_SOLVER_MARKET_SCOPE_MATERIALIZATION_VALIDATED"
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "qku_formula_algorithm_solver_market_scope_materialization"
)

GENERATED_DIR = Path("docs/master_plan/generated")
SCHEMA_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "qku_formula_algorithm_solver_market_scope_materialization/schemas"
)
SHARD_DIR = GENERATED_DIR / "pr162b_qku_formula_solver_market_scope_shards"

AUTHORITY_CLASS = "QKU_FORMULA_ALGORITHM_SOLVER_MARKET_SCOPE_CANDIDATE_OR_CONTROL_PLANE_ONLY"
PR152_CURRENTIZATION_RESULT_PENDING = "PENDING_EXTERNAL_VALIDATION_COMMAND"
PR152_CURRENTIZATION_RESULT_PASS = "EXTERNAL_VALIDATION_CONFIRMED_PASS"
PR152_CURRENTIZATION_RESULT_FAILED = "EXTERNAL_VALIDATION_FAILED"
PR152_CURRENTIZATION_VALIDATION_COMMAND = (
    "python tools/validate_grand_global_debug_logical_consistency_audit.py"
)
PR152_FINALIZATION_CURRENTIZATION_COMMAND = (
    "python tools/currentize_pr152_after_generated_artifacts.py"
)
PR152_CURRENTIZATION_REPORT_REF = (
    "docs/master_plan/generated/"
    "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
)

REPORT_SHARD_RECORD_TARGET = 1000
REPORT_SHARD_PREVIEW_RECORD_LIMIT = 3
REPORT_SHARD_BYTE_THRESHOLD = 900_000

REPORT_FILENAMES = (
    "PR162B_FinalSummary.report.json",
    "PR162B_SharedDictionary.report.json",
    "PR162B_FormulaSourceRetrievalTargetMatrix.report.json",
    "PR162B_QKUExecutionClassificationAudit.report.json",
    "PR162B_QKUMarketClassificationRegistry.report.json",
    "PR162B_QKUStage1PredictionMarketActivationGate.report.json",
    "PR162B_QKUDormancyRegistry.report.json",
    "PR162B_QKUTradeRoleRegistry.report.json",
    "PR162B_QKUMarketInputFieldRequirementMatrix.report.json",
    "PR162B_QTTAgentStage1QKUActivationAllowlist.report.json",
    "PR162B_QKUMarketClassificationCoverageAudit.report.json",
    "PR162B_QKUFormulaCoverageAudit.report.json",
    "PR162B_QKUFormulaRegistry.report.json",
    "PR162B_QKUAlgorithmRegistry.report.json",
    "PR162B_QKUObjectiveFunctionRegistry.report.json",
    "PR162B_QKUConstraintRegistry.report.json",
    "PR162B_QKUParameterValueRegistry.report.json",
    "PR162B_QKUParameterRangeScaleRegistry.report.json",
    "PR162B_QKUTradableValueCandidateRegistry.report.json",
    "PR162B_QKUSolverMappingRegistry.report.json",
    "PR162B_QKUExecutableComputeContractRegistry.report.json",
    "PR162B_QKUFormulaTestVectorRegistry.report.json",
    "PR162B_QKUAlgorithmTestVectorRegistry.report.json",
    "PR162B_QKUFormulaImplementationBindingRegistry.report.json",
    "PR162B_QKUFormulaBindingProofMatrix.report.json",
    "PR162B_QuantumQUBOIsingFormulaMaterialization.report.json",
    "PR162B_QuantumSolverSmokeExecutionReport.report.json",
    "PR162B_AgentFormulaConsumerRoutingMatrix.report.json",
    "PR162B_LiveModeFormulaGateStatus.report.json",
    "PR162B_MetadataOnlyBlockerAudit.report.json",
    "PR162B_PR162CDataRequirementHandoff.report.json",
    "PR162B_ForbiddenAuthorityScan.report.json",
    "PR162B_ReportShardManifest.report.json",
)
SHARD_MANIFEST_REPORT_FILENAME = "PR162B_ReportShardManifest.report.json"
SHARD_MANIFEST_REPORT_PATH = GENERATED_DIR / SHARD_MANIFEST_REPORT_FILENAME
SCHEMA_FILENAMES = tuple(
    filename.replace(".report.json", ".schema.json").lower()
    for filename in REPORT_FILENAMES
)
REPORT_SCHEMA_REFS = {
    report: f"{SCHEMA_DIR.as_posix()}/{schema}"
    for report, schema in zip(REPORT_FILENAMES, SCHEMA_FILENAMES, strict=True)
}

NO_AUTHORITY_FLAGS = {
    "creates_live_authority": False,
    "creates_order_authority": False,
    "creates_private_state": False,
    "creates_profit_evidence": False,
    "creates_result_backed_ranking": False,
    "creates_quantum_backend_evidence": False,
    "creates_connector_semantics": False,
    "creates_source_evidence_fact": False,
    "creates_qtt_sha_authority": False,
    "creates_atomicrows_bundle_hash_or_freeze_authority": False,
    "mutates_atomicrows_bundle_jsonl": False,
    "emits_result_packets": False,
    "emits_replay_paper_results": False,
    "ci_requires_network": False,
}

FORBIDDEN_AUTHORITY_CATEGORIES = (
    "LIVE_TRADING_AUTHORITY",
    "LIVE_ORDER_ROUTING",
    "PRIVATE_ACCOUNT_STATE_FETCH",
    "ACCEPTED_SOURCE_FACT_CREATION_WITHOUT_GATE",
    "CONNECTOR_SEMANTIC_BINDING",
    "REPLAY_PAPER_PERFORMANCE_EVIDENCE_PROMOTION",
    "RESULT_PACKET_EMISSION",
    "PR161E_INGESTION_TRUTH",
    "RESULT_BACKED_RANKING_UPDATE",
    "PROFIT_CLAIM_OR_GUARANTEE",
    "OPTIMIZER_EVIDENCE_EXECUTION",
    "QUANTUM_BACKEND_OR_SIMULATOR_EVIDENCE_EXECUTION",
    "CLOUD_QPU_OR_BACKEND_CALL",
    "CREDENTIAL_OR_SECRET_ACCESS",
    "PACKAGE_INSTALLATION",
    "QTT_SHA_FREEZE_CHECKSUM_GLOBAL_DIGEST_AUTHORITY",
    "ATOMICROWS_BUNDLE_HASH_FREEZE_AUTHORITY",
    "ABSOLUTE_LOCAL_PATH_IN_GENERATED_OUTPUT",
    "DORMANT_QKU_IN_STAGE1_EXECUTION_ALLOWLIST",
    "METADATA_ONLY_QKU_MARKED_TRADABLE",
    "FORMULA_TO_QKU_BINDING_WITHOUT_PROOF",
)

SOURCE_CLASSES = (
    "OFFICIAL_DOC_FORMULA_CANDIDATE",
    "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE",
    "OFFICIAL_VENUE_DOC_FIELD_CANDIDATE",
    "OFFICIAL_API_DOC_FIELD_CANDIDATE",
    "RESEARCH_FORMULA_CANDIDATE",
    "TEXTBOOK_FORMULA_CANDIDATE",
    "INSTITUTIONAL_FORMULA_CANDIDATE",
    "OPEN_SOURCE_PACKAGE_FORMULA_CANDIDATE",
    "NON_OFFICIAL_WEB_FORMULA_CANDIDATE",
    "SOCIAL_RESEARCH_FORMULA_CANDIDATE",
    "OWNER_APPROVED_FORMULA_CANDIDATE",
    "REPO_EXISTING_FORMULA",
    "PACKAGE_INTROSPECTION_CANDIDATE",
    "UNKNOWN_REQUIRES_SOURCE",
)

MARKET_SCOPES = (
    "PREDICTION_MARKET_BINARY_EVENT_CONTRACT",
    "PREDICTION_MARKET_MULTIOUTCOME_EVENT_CONTRACT",
    "PREDICTION_MARKET_SCALAR_RANGE_CONTRACT",
    "EQUITY_SPOT",
    "EQUITY_ETF",
    "EQUITY_INDEX",
    "EQUITY_OPTIONS",
    "FUTURES",
    "FUTURES_OPTIONS",
    "CRYPTO_SPOT",
    "CRYPTO_PERPETUAL",
    "CRYPTO_OPTIONS",
    "FX_SPOT",
    "RATES",
    "BONDS_FIXED_INCOME",
    "COMMODITIES_SPOT",
    "COMMODITIES_FUTURES",
    "MACRO_INDICATOR_SERIES",
    "SPORTSBOOK_ODDS",
    "NON_MARKET_SPECIFIC",
    "MARKET_AGNOSTIC_MATH",
    "MARKET_AGNOSTIC_FEATURE",
    "MARKET_AGNOSTIC_RISK",
    "MARKET_AGNOSTIC_OPTIMIZER",
    "MARKET_AGNOSTIC_GOVERNANCE",
    "UNKNOWN_MARKET_SCOPE",
)
STAGE1_ALLOWED_MARKET_SCOPES = (
    "PREDICTION_MARKET_BINARY_EVENT_CONTRACT",
    "PREDICTION_MARKET_MULTIOUTCOME_EVENT_CONTRACT",
    "PREDICTION_MARKET_SCALAR_RANGE_CONTRACT",
    "NON_MARKET_SPECIFIC",
    "MARKET_AGNOSTIC_MATH",
    "MARKET_AGNOSTIC_FEATURE",
    "MARKET_AGNOSTIC_RISK",
    "MARKET_AGNOSTIC_OPTIMIZER",
    "MARKET_AGNOSTIC_GOVERNANCE",
)
DORMANT_DEFAULT_MARKET_SCOPES = (
    "EQUITY_SPOT",
    "EQUITY_ETF",
    "EQUITY_INDEX",
    "EQUITY_OPTIONS",
    "FUTURES",
    "FUTURES_OPTIONS",
    "CRYPTO_SPOT",
    "CRYPTO_PERPETUAL",
    "CRYPTO_OPTIONS",
    "FX_SPOT",
    "RATES",
    "BONDS_FIXED_INCOME",
    "COMMODITIES_SPOT",
    "COMMODITIES_FUTURES",
    "MACRO_INDICATOR_SERIES",
    "SPORTSBOOK_ODDS",
    "UNKNOWN_MARKET_SCOPE",
)
MARKET_SCOPE_CONFIDENCE_LEVELS = (
    "HIGH_EXPLICIT_QKU_FAMILY",
    "HIGH_EXPLICIT_INPUT_FIELD_BINDING",
    "HIGH_EXPLICIT_AGENT_ROUTE",
    "MEDIUM_FORMULA_REQUIREMENT_INFERRED",
    "MEDIUM_DATA_REQUIREMENT_INFERRED",
    "LOW_NAME_HEURISTIC_ONLY",
    "UNKNOWN_REQUIRES_OWNER_REVIEW",
)

QKU_EXECUTION_CLASSES = (
    "FORMULA_EXECUTABLE",
    "ALGORITHM_EXECUTABLE",
    "OBJECTIVE_EXECUTABLE",
    "CONSTRAINT_EXECUTABLE",
    "PARAMETER_VALUE_MATERIALIZED",
    "PARAMETER_ONLY",
    "FEATURE_COMPUTABLE",
    "FEATURE_ONLY",
    "SOLVER_INPUT_ASSEMBLABLE",
    "SOLVER_MAPPING_ONLY",
    "SOLVER_SMOKE_EXECUTABLE",
    "MARKET_SCOPE_CLASSIFIED_ONLY",
    "AGENT_ROUTE_ONLY",
    "GOVERNANCE_ONLY",
    "METADATA_ONLY_BLOCKED",
    "UNKNOWN_REQUIRES_OWNER_OR_SOURCE",
)

ACTIVATION_STATUSES = (
    "ACTIVE_STAGE1_PREDICTION_MARKET_TRADING_CANDIDATE",
    "ACTIVE_STAGE1_PREDICTION_MARKET_SUPPORT",
    "ACTIVE_STAGE1_MARKET_AGNOSTIC_SUPPORT",
    "ACTIVE_STAGE1_REPLAY_PAPER_ONLY",
    "DORMANT_NON_STAGE1_MARKET_SPECIFIC",
    "DORMANT_UNKNOWN_MARKET_SCOPE",
    "DORMANT_METADATA_ONLY",
    "DORMANT_MISSING_FORMULA",
    "DORMANT_MISSING_ALGORITHM",
    "DORMANT_MISSING_INPUT_BINDING",
    "DORMANT_OWNER_REVIEW_REQUIRED",
)
DORMANCY_STATUSES = (
    "NOT_DORMANT_STAGE1_ACTIVE",
    "DORMANT_NON_STAGE1_MARKET_SPECIFIC",
    "DORMANT_UNKNOWN_MARKET_SCOPE",
    "DORMANT_METADATA_ONLY",
    "DORMANT_MISSING_FORMULA",
    "DORMANT_MISSING_ALGORITHM",
    "DORMANT_MISSING_INPUT_BINDING",
    "DORMANT_OWNER_REVIEW_REQUIRED",
)
LIVE_MODE_GATE_STATUSES = (
    "LIVE_BLOCKED_METADATA_ONLY",
    "LIVE_BLOCKED_NO_FORMULA",
    "LIVE_BLOCKED_NO_ALGORITHM",
    "LIVE_BLOCKED_NO_PARAMETER_VALUES",
    "LIVE_BLOCKED_NO_INPUT_BINDING",
    "LIVE_BLOCKED_NO_OUTPUT_BINDING",
    "LIVE_BLOCKED_NO_TEST_VECTOR",
    "LIVE_BLOCKED_NO_SOLVER_MAPPING",
    "LIVE_BLOCKED_NO_REPLAY_PAPER_EVIDENCE",
    "LIVE_BLOCKED_NO_RISK_CAPITAL_LATENCY_GATE",
    "LIVE_BLOCKED_OWNER_REVIEW_REQUIRED",
    "LIVE_BLOCKED_NON_STAGE1_MARKET_SCOPE",
    "LIVE_CANDIDATE_AFTER_REPLAY_PAPER_ONLY",
)

TRADE_ROLES = (
    "SIGNAL_GENERATION",
    "PROBABILITY_ESTIMATION",
    "PRICE_NORMALIZATION",
    "EXPECTED_VALUE",
    "EDGE_DETECTION",
    "POSITION_SIZING",
    "RISK_CONTROL",
    "CAPITAL_ALLOCATION",
    "ORDER_ROUTING_PREP",
    "LATENCY_CONTROL",
    "SLIPPAGE_COST_MODEL",
    "REPLAY_PAPER_EVALUATION",
    "SCORING_RANKING_AFTER_EVIDENCE",
    "QUANTUM_OPTIMIZER_INPUT",
    "QUANTUM_SOLVER_MAPPING",
    "SOURCE_EVIDENCE_GOVERNANCE",
    "OWNER_REVIEW_GOVERNANCE",
    "DATA_QUALITY_CONTROL",
    "NON_TRADING_SUPPORT",
    "UNKNOWN_ROLE",
)

FORMULA_IMPLEMENTATION_STATUSES = (
    "IMPLEMENTED_DETERMINISTIC_PYTHON",
    "IMPLEMENTED_SYMBOLIC_ONLY",
    "IMPLEMENTED_SOLVER_INPUT_ASSEMBLY_ONLY",
    "IMPLEMENTED_TEST_VECTOR_ONLY",
    "BLOCKED_MISSING_INPUTS",
    "BLOCKED_MISSING_SOURCE",
    "BLOCKED_OWNER_REVIEW",
)
SMOKE_EXECUTION_STATUSES = (
    "SMOKE_EXECUTED_NO_TRADING_EVIDENCE",
    "FORMULA_TEST_VECTOR_EXECUTED",
    "ALGORITHM_TEST_VECTOR_EXECUTED",
    "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE",
    "NOT_EXECUTED_BLOCKED",
)
BINDING_PROOF_STATUSES = (
    "STRICT_BINDING_CONFIRMED",
    "CANDIDATE_BINDING_REPLAY_PAPER_REQUIRED",
    "LOW_CONFIDENCE_BINDING_OWNER_REVIEW_REQUIRED",
    "BLOCKED_NO_QKU_FAMILY_MATCH",
    "BLOCKED_NO_MARKET_SCOPE_MATCH",
    "BLOCKED_NO_INPUT_FIELD_MATCH",
    "BLOCKED_NO_AGENT_CONSUMER_MATCH",
    "BLOCKED_FORMULA_NOT_APPLICABLE",
    "BLOCKED_SOLVER_NOT_APPLICABLE",
    "BLOCKED_METADATA_ONLY",
)

SOLVER_FAMILIES = (
    "CLASSICAL_CLOSED_FORM",
    "CLASSICAL_VECTOR_FORMULA",
    "CLASSICAL_LINEAR_PROGRAM",
    "CLASSICAL_QUADRATIC_PROGRAM",
    "CLASSICAL_MIXED_INTEGER_PROGRAM",
    "SCIPY_MINIMIZE_CANDIDATE",
    "PYPORTFOLIOOPT_CANDIDATE",
    "QUBO_EXACT_ENUMERATION_SMOKE",
    "QISKIT_QUBO_CANDIDATE",
    "QISKIT_ISING_QAOA_CANDIDATE",
    "QISKIT_VQE_CANDIDATE",
    "DWAVE_BQM_CANDIDATE",
    "DWAVE_CQM_CANDIDATE",
    "HYBRID_SOLVER_CANDIDATE",
)

BLOCKER_CODES = (
    "NONE",
    "PR162B_BLOCKED_NON_STAGE1_MARKET_SCOPE",
    "PR162B_BLOCKED_UNKNOWN_MARKET_SCOPE",
    "PR162B_BLOCKED_METADATA_ONLY",
    "PR162B_BLOCKED_NO_FORMULA_BINDING_PROOF",
    "PR162B_BLOCKED_NO_ALGORITHM_BINDING_PROOF",
    "PR162B_BLOCKED_NO_INPUT_FIELD_BINDING",
    "PR162B_BLOCKED_NO_OUTPUT_FIELD_BINDING",
    "PR162B_BLOCKED_NO_TEST_VECTOR",
    "PR162B_BLOCKED_NO_REPLAY_PAPER_EVIDENCE",
    "PR162B_BLOCKED_NO_STRICT_DATASET",
    "PR162B_BLOCKED_OWNER_REVIEW_REQUIRED",
    "PR162B_BLOCKED_FORMULA_NOT_APPLICABLE",
    "PR162B_BLOCKED_SOLVER_NOT_APPLICABLE",
    "PR162B_BLOCKED_LOW_CONFIDENCE_MARKET_SCOPE",
    "PR162B_BLOCKED_UNSUPPORTED_QKU_FAMILY",
)

PREDICTION_MARKET_INPUT_FIELDS = (
    "event_id",
    "market_id",
    "question",
    "outcome_yes_id",
    "outcome_no_id",
    "yes_price",
    "no_price",
    "yes_bid",
    "yes_ask",
    "no_bid",
    "no_ask",
    "implied_probability",
    "resolution_status",
    "settlement_value",
    "open_time",
    "close_time",
    "resolution_time",
    "volume",
    "open_interest",
    "liquidity",
    "spread",
    "fee_model_candidate",
    "venue",
)

AGENT_ROLES = (
    "QTT_RESEARCH_AGENT",
    "QTT_SOURCE_EVIDENCE_AGENT",
    "QTT_PARAMETER_STACK_AGENT",
    "QTT_QUANTUM_ADVISORY_AGENT",
    "QTT_OPTIMIZER_ARBITRATION_AGENT",
    "QTT_REPLAY_AGENT",
    "QTT_PAPER_AGENT",
    "QTT_SCORING_AGENT",
    "QTT_RANKING_AGENT",
    "QTT_RISK_AGENT",
    "QTT_CAPITAL_AGENT",
    "QTT_LATENCY_AGENT",
    "QTT_EXECUTION_PREP_AGENT",
    "QTT_EXECUTION_ROUTER_AGENT",
    "QTT_OWNER_REVIEW_AGENT",
    "QTT_GOVERNANCE_AGENT",
)

DOWNSTREAM_PR_ROUTES = (
    "PR162C_STRICT_DATA_EXPANSION",
    "PR162R_ADAPTER_RERUN_AFTER_STRICT_DATASETS",
    "PR163_RESULT_PACKET_EMISSION_AFTER_VALIDATED_REAL_ARTIFACTS",
    "PR164_AUTHENTICITY_SAMPLE_CONFIDENCE_PROVENANCE_VALIDATION",
    "PR165_RESULT_BACKED_RANKING_AFTER_PR164",
    "FUTURE_LIVE_OWNER_RISK_CAPITAL_LATENCY_SOURCE_GATED",
)
UPSTREAM_PR_REFS = (
    "PR136",
    "PR137R",
    "PR138",
    "PR152",
    "PR161C",
    "PR161D",
    "PR161E",
    "PR161F",
    "PR162",
    "PR162A",
)

REQUIRED_INPUT_REPORTS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "src/qtt/stage1_prediction_markets/launch_readiness/day1_launch_readiness_roadmap_policy.py",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json",
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
    "docs/master_plan/generated/PR161D_FinalSummary.report.json",
    "docs/master_plan/generated/PR161D_QKUQualityScoreRegistry.report.json",
    "docs/master_plan/generated/PR161D_QKUReplayPaperPriorityQueue.report.json",
    "docs/master_plan/generated/PR161D_QKUReplayPaperScenarioInputs.report.json",
    "docs/master_plan/generated/PR161D_QKUScenarioOutcomeMatrix.report.json",
    "docs/master_plan/generated/PR161D_QKUCombinationCandidateRegistry.report.json",
    "docs/master_plan/generated/PR161D_QKUCombinationReplayPaperPriorityQueue.report.json",
    "docs/master_plan/generated/PR161D_QKUResultBackedRankingSlots.report.json",
    "docs/master_plan/generated/PR161D_QKUFutureProfitabilityPatternFields.report.json",
    "docs/master_plan/generated/PR161D_QKUAgentTaskQueue.report.json",
    "docs/master_plan/generated/PR161D_QKUAgentGraphRoutingMatrix.report.json",
    "docs/master_plan/generated/PR161D_QKUMarketBundleActivationPolicy.report.json",
    "docs/master_plan/generated/PR161D_ReportShardManifest.report.json",
    "docs/master_plan/generated/PR161E_FinalSummary.report.json",
    "docs/master_plan/generated/PR161E_ReplayPaperOutcomeCaptureRegistry.report.json",
    "docs/master_plan/generated/PR161E_ResultAuthenticityClassification.report.json",
    "docs/master_plan/generated/PR161E_QKUReplayPaperProfitabilityLedger.report.json",
    "docs/master_plan/generated/PR161E_QKUScenarioResultAttribution.report.json",
    "docs/master_plan/generated/PR161E_QKUResultBackedRankingUpdateCandidates.report.json",
    "docs/master_plan/generated/PR161E_QKUFutureProfitabilityPatternUpdateCandidates.report.json",
    "docs/master_plan/generated/PR161E_QuantumClassicalHybridOutcomeComparison.report.json",
    "docs/master_plan/generated/PR161E_AtomicRowsPR154ResultCompatibilityBridge.report.json",
    "docs/master_plan/generated/PR161E_AgentOutcomeTaskQueue.report.json",
    "docs/master_plan/generated/PR161E_OwnerReviewResultPromotionQueue.report.json",
    "docs/master_plan/generated/PR161E_SharedDictionary.report.json",
    "docs/master_plan/generated/PR161E_ReportShardManifest.report.json",
    "docs/master_plan/generated/PR161F_FinalSummary.report.json",
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
    "docs/master_plan/generated/PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json",
    "docs/master_plan/generated/PR161F_ReportShardManifest.report.json",
    "docs/master_plan/generated/PR161F_SharedDictionary.report.json",
    "docs/master_plan/generated/PR162_FinalSummary.report.json",
    "docs/master_plan/generated/PR162_QKUArtifactCoverageBridge.report.json",
    "docs/master_plan/generated/PR162_QKUQuantumExecutionReadinessBridge.report.json",
    "docs/master_plan/generated/PR162_QKUQuantumProblemEncodingBlueprint.report.json",
    "docs/master_plan/generated/PR162_QuantumParameterRangeCandidateRegistry.report.json",
    "docs/master_plan/generated/PR162_QuantumBackendFitCandidateMatrix.report.json",
    "docs/master_plan/generated/PR162_QuantumClassicalHybridArtifactInputBridge.report.json",
    "docs/master_plan/generated/PR162_QuantumClassicalHybridComparatorBlueprint.report.json",
    "docs/master_plan/generated/PR162_QuantumReplayPaperWorkOrderQueue.report.json",
    "docs/master_plan/generated/PR162_QuantumLiveModeControlPlaneBridge.report.json",
    "docs/master_plan/generated/PR162_QuantumLatencyLivePathReadinessBridge.report.json",
    "docs/master_plan/generated/PR162_QKUQuantumDownstreamAgentRouteMatrix.report.json",
    "docs/master_plan/generated/PR162_SharedDictionary.report.json",
    "docs/master_plan/generated/PR162_ReportShardManifest.report.json",
    "docs/master_plan/generated/PR162A_FinalSummary.report.json",
    "docs/master_plan/generated/PR162A_DatasetMaterializationManifest.report.json",
    "docs/master_plan/generated/PR162A_NormalizedDatasetInventory.report.json",
    "docs/master_plan/generated/PR162A_MarketScenarioQKUMappingMatrix.report.json",
    "docs/master_plan/generated/PR162A_PR161FRunPlanDatasetCoverageBridge.report.json",
    "docs/master_plan/generated/PR162A_PR162AdapterRerunReadinessBridge.report.json",
    "docs/master_plan/generated/PR162A_PR163ReadinessBlockerStatus.report.json",
    "docs/master_plan/generated/PR162A_QuantumQKUDatasetFeatureBridge.report.json",
    "docs/master_plan/generated/PR162A_QuantumFeatureMaterializationWorkOrderQueue.report.json",
    "docs/master_plan/generated/PR162A_QTTAgentDatasetHandoffBridge.report.json",
    "docs/master_plan/generated/PR162A_SharedDictionary.report.json",
    "docs/master_plan/generated/PR162A_ReportShardManifest.report.json",
    "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    "tools/currentize_pr152_after_generated_artifacts.py",
    "tools/ci_branch_context.py",
    "tools/run_validation_gates.py",
    "tools/validate_grand_global_debug_logical_consistency_audit.py",
)
MISSING_REQUESTED_INPUT_ALIASES = {
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json": (
        "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json",
        "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    )
}

PR161F_REPORTS_REQUIRED = (
    "PR161F_ExecutorInputRegistry.report.json",
    "PR161F_ReplayRunRequestRegistry.report.json",
    "PR161F_PaperRunRequestRegistry.report.json",
    "PR161F_PairedReplayPaperRunPlan.report.json",
    "PR161F_RunArtifactEnvelopeRegistry.report.json",
    "PR161F_ResultPacketEmissionEligibilityGate.report.json",
    "PR161F_QuantumClassicalHybridRunPlan.report.json",
    "PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json",
    "PR161F_QTTAgentRoleIOContract.report.json",
)

FORMULA_FAMILIES = (
    "prediction_market",
    "calibration",
    "position_sizing",
    "risk_portfolio",
    "technical_feature",
    "classical_optimizer",
    "quantum_hybrid",
)
ALGORITHM_FAMILIES = (
    "signal",
    "expected_value_gate",
    "position_sizing",
    "risk_control",
    "feature_compute",
    "binding_governance",
    "solver_input_assembly",
    "market_scope_governance",
)

NO_SCATTERED_HARDCODING_ALLOWLIST = (
    "constants.py",
    "validator.py",
    "report_builder.py",
    "tests",
)
