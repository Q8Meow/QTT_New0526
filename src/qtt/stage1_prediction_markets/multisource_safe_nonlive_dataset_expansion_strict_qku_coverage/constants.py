"""Central PR162C constants for strict dataset and executable QKU coverage."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR162C"
PR_LABEL = "PR162C_MULTISOURCE_SAFE_NONLIVE_DATASET_EXECUTABLE_QKU_STRICT_COVERAGE"
EXPECTED_BRANCH = "pr162c-multisource-safe-nonlive-dataset-executable-qku-strict-coverage"
SUCCESS_MARKER = "PR162C_MULTISOURCE_SAFE_NONLIVE_DATASET_EXECUTABLE_QKU_STRICT_COVERAGE_VALIDATED"
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "multisource_safe_nonlive_dataset_expansion_strict_qku_coverage"
)

GENERATED_DIR = Path("docs/master_plan/generated")
SCHEMA_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "multisource_safe_nonlive_dataset_expansion_strict_qku_coverage/schemas"
)
SHARD_DIR = GENERATED_DIR / "pr162c_multisource_safe_nonlive_dataset_shards"

AUTHORITY_CLASS = "PR162C_CANDIDATE_DATASET_FORMULA_AND_STRICT_COVERAGE_GATE_ONLY"
REPORT_SHARD_RECORD_TARGET = 1000
REPORT_SHARD_PREVIEW_RECORD_LIMIT = 3
REPORT_SHARD_BYTE_THRESHOLD = 900_000

PR152_CURRENTIZATION_RESULT_PENDING = "PENDING_EXTERNAL_VALIDATION_COMMAND"
PR152_CURRENTIZATION_RESULT_PASS = "EXTERNAL_VALIDATION_CONFIRMED_PASS"
PR152_CURRENTIZATION_RESULT_FAILED = "EXTERNAL_VALIDATION_FAILED"
PR152_CURRENTIZATION_VALIDATION_COMMAND = (
    "python tools/validate_grand_global_debug_logical_consistency_audit.py"
)
PR152_FINALIZATION_CURRENTIZATION_COMMAND = (
    "python tools/currentize_pr152_after_generated_artifacts.py"
)
PR152_FINALIZATION_CURRENTIZATION_GUIDANCE = (
    "Run tools/currentize_pr152_after_generated_artifacts.py after final generated "
    "artifacts settle and before validation gates."
)
PR152_CURRENTIZATION_REPORT_REF = (
    "docs/master_plan/generated/"
    "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
)

PREFLIGHT_ALIAS_REPORT_FILENAME = (
    "PR162C_EXECUTABLE_QKU_AND_DATASET_PREFLIGHT_RECEIPT.report.json"
)
PREFLIGHT_REPORT_FILENAME = (
    "PR162C_ExecutableQKUAndDatasetPreflightReceipt.report.json"
)
SHARD_MANIFEST_REPORT_FILENAME = "PR162C_ReportShardManifest.report.json"
SHARD_MANIFEST_REPORT_PATH = GENERATED_DIR / SHARD_MANIFEST_REPORT_FILENAME

REPORT_FILENAMES = (
    "PR162C_FinalSummary.report.json",
    "PR162C_SharedDictionary.report.json",
    PREFLIGHT_REPORT_FILENAME,
    PREFLIGHT_ALIAS_REPORT_FILENAME,
    "PR162C_SourcePortfolioRegistry.report.json",
    "PR162C_DataRequirementClassificationLedger.report.json",
    "PR162C_SourceDiscoveryLedger.report.json",
    "PR162C_DatasetAuthorityAndAccessRightsGate.report.json",
    "PR162C_NormalizedDatasetInventory.report.json",
    "PR162C_DataQualityLeakageTimeWindowAudit.report.json",
    "PR162C_QKUInputFieldCoverageMatrix.report.json",
    "PR162C_StrictQKUCoverageProofMatrix.report.json",
    "PR162C_PR162RAdapterRerunReadinessBridge.report.json",
    "PR162C_PR163ReadinessBlockerStatus.report.json",
    "PR162C_QTTAgentDatasetConsumerRoutingMatrix.report.json",
    "PR162C_QTTAgentExecutableQKURoutingMatrix.report.json",
    "PR162C_ForbiddenAuthorityScan.report.json",
    "PR162C_KalshiOfficialHistoricalDataPack.report.json",
    "PR162C_PolymarketOfficialPublicDataPack.report.json",
    "PR162C_ForecastExOfficialCSVDataPack.report.json",
    "PR162C_IBKRForecastExEventContractCandidatePack.report.json",
    "PR162C_ResearchThirdPartyCandidateDataPack.report.json",
    "PR162C_FormulaSourceRetrievalMatrix.report.json",
    "PR162C_OwnerProvidedLocalDataPack.report.json",
    "PR162C_OwnerMaterializationCommandQueue.report.json",
    "PR162C_QKUExecutionClassificationRegistry.report.json",
    "PR162C_QKUFormulaCoverageAudit.report.json",
    "PR162C_QKUObjectiveFunctionCoverageAudit.report.json",
    "PR162C_QKUConstraintCoverageAudit.report.json",
    "PR162C_QKUParameterValueCoverageAudit.report.json",
    "PR162C_QKUParameterRangeScaleCoverageAudit.report.json",
    "PR162C_QKUTradableValueCoverageAudit.report.json",
    "PR162C_QKUSolverMappingCoverageAudit.report.json",
    "PR162C_QKUExecutableComputeContractCoverageAudit.report.json",
    "PR162C_QKUFormulaTestVectorCoverageAudit.report.json",
    "PR162C_QKUFormulaRegistryDelta.report.json",
    "PR162C_QKUAlgorithmRegistryDelta.report.json",
    "PR162C_QKUObjectiveFunctionRegistryDelta.report.json",
    "PR162C_QKUConstraintRegistryDelta.report.json",
    "PR162C_QKUParameterValueRegistryDelta.report.json",
    "PR162C_QKUParameterRangeScaleRegistryDelta.report.json",
    "PR162C_QKUTradableValueCandidateRegistryDelta.report.json",
    "PR162C_QKUSolverMappingRegistryDelta.report.json",
    "PR162C_QKUExecutableComputeContractRegistryDelta.report.json",
    "PR162C_QKUFormulaTestVectorRegistryDelta.report.json",
    "PR162C_QKUFormulaToDatasetBindingMatrix.report.json",
    "PR162C_QKUFormulaToAgentRouteMatrix.report.json",
    "PR162C_TradableQKUCandidateContractAudit.report.json",
    "PR162C_QKUMarketClassificationContinuityAudit.report.json",
    "PR162C_QKUStage1ActivationContinuityAudit.report.json",
    "PR162C_QKUDormancyContinuityAudit.report.json",
    "PR162C_QKUMarketInputFieldRequirementMatrix.report.json",
    "PR162C_QuantumFeatureDatasetStrictCoverageBridge.report.json",
    "PR162C_QUBOIsingDatasetFeatureCoverage.report.json",
    "PR162C_QUBOIsingFormulaDatasetBindingMatrix.report.json",
    "PR162C_QuantumClassicalHybridDatasetComparatorCoverage.report.json",
    "PR162C_QuantumSolverInputAssemblyCoverageAudit.report.json",
    SHARD_MANIFEST_REPORT_FILENAME,
)
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
    "creates_qtt_digest_authority": False,
    "mutates_atomicrows_bundle_jsonl": False,
    "emits_result_packets": False,
    "emits_replay_paper_results": False,
    "ci_requires_network": False,
}

FORBIDDEN_AUTHORITY_STRINGS = (
    "LIVE_TRADING_AUTHORITY",
    "LIVE_ORDER_ROUTING",
    "PRIVATE_ACCOUNT_STATE_FETCH",
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
    "BROAD_QKU_READINESS_CLAIM",
    "METADATA_ONLY_EXECUTABLE_CLAIM",
)

SOURCE_CLASSES = (
    "OFFICIAL_VENUE_PUBLIC_DATA",
    "OFFICIAL_VENUE_PUBLIC_API",
    "OFFICIAL_VENUE_PUBLIC_CSV",
    "OFFICIAL_DOC_ONLY_FETCH_PLAN",
    "OFFICIAL_LIBRARY_DOC_FORMULA_SOURCE",
    "OFFICIAL_LIBRARY_DOC_SOLVER_SOURCE",
    "PUBLIC_RESEARCH_DATASET_CANDIDATE",
    "PUBLIC_ONCHAIN_DATASET_CANDIDATE",
    "THIRD_PARTY_VENDOR_DATASET_CANDIDATE",
    "SOCIAL_WEB_INSTITUTIONAL_SIGNAL_CANDIDATE",
    "OPEN_SOURCE_CODE_REFERENCE_CANDIDATE",
    "RESEARCH_FORMULA_CANDIDATE",
    "INSTITUTIONAL_FORMULA_CANDIDATE",
    "OWNER_PROVIDED_LOCAL_DATASET_CANDIDATE",
    "OWNER_APPROVED_FORMULA_OR_VALUE_CANDIDATE",
    "FETCH_PLAN_ONLY_OWNER_COMMAND_REQUIRED",
    "BLOCKED_UNSAFE_OR_UNMAPPABLE",
)
AUTHORITY_CLASSES = (
    AUTHORITY_CLASS,
    "OFFICIAL_PUBLIC_SOURCE_CANDIDATE_NOT_ACCEPTED_AS_TRUTH",
    "PUBLIC_RESEARCH_CANDIDATE_NOT_OFFICIAL_TRUTH",
    "OWNER_APPROVED_INTERNAL_CANDIDATE_NOT_EXTERNAL_FACT",
    "FETCH_PLAN_ONLY_NOT_MATERIALIZED",
    "BLOCKED_UNSAFE_OR_ACCESS_UNCLEAR",
)
SOURCE_ACCESS_RIGHTS_STATUSES = (
    "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK",
    "PUBLIC_DOCUMENTATION_ONLY_OK",
    "OWNER_PROVIDED_ATTESTATION_REQUIRED",
    "THIRD_PARTY_TERMS_REVIEW_REQUIRED",
    "AUTHENTICATION_REQUIRED_BLOCKED",
    "PRIVATE_ACCOUNT_STATE_REQUIRED_BLOCKED",
    "LIVE_OR_ORDER_ENDPOINT_BLOCKED",
    "ACCESS_RIGHTS_UNCLEAR_BLOCKED",
)
SOURCE_LANES = (
    "LANE_A_KALSHI_OFFICIAL_PUBLIC_HISTORICAL_CANDIDATE",
    "LANE_B_POLYMARKET_OFFICIAL_PUBLIC_CANDIDATE",
    "LANE_C_FORECASTEX_IBKR_OFFICIAL_CANDIDATE",
    "LANE_D_PUBLIC_RESEARCH_THIRD_PARTY_CANDIDATE",
    "LANE_E_OPEN_SOURCE_PACKAGE_INTROSPECTION",
    "LANE_F_OWNER_PROVIDED_LOCAL_DATA",
    "LANE_G_FETCH_PLAN_ONLY",
)
SOURCE_QUALITY_TIERS = (
    "REGISTERED_PUBLIC_DOC_OR_LOCATOR_ONLY",
    "REPO_LOCAL_CANDIDATE_DATA_PRESENT",
    "FETCH_PLAN_ONLY_OWNER_COMMAND_REQUIRED",
    "BLOCKED_UNSAFE_OR_UNMAPPABLE",
)

TERMINAL_REQUIREMENT_STATUSES = (
    "STRICT_COVERED_REPO_LOCAL",
    "CANDIDATE_COVERED_NEEDS_REPLAY_PAPER",
    "OWNER_MATERIALIZATION_COMMAND_REQUIRED",
    "FETCH_PLAN_ONLY_SOURCE_DISCOVERED",
    "BLOCKED_UNSAFE_SOURCE",
    "BLOCKED_ACCESS_RIGHTS_UNCLEAR",
    "BLOCKED_REQUIRED_FIELDS_MISSING",
    "BLOCKED_ROW_COUNT_INSUFFICIENT",
    "BLOCKED_TIME_WINDOW_INSUFFICIENT",
    "BLOCKED_LEAKAGE_RISK",
    "BLOCKED_MARKET_SCOPE_MISMATCH",
    "BLOCKED_VENUE_SCOPE_MISMATCH",
    "BLOCKED_UNMAPPABLE",
    "BLOCKED_DUPLICATE",
    "BLOCKED_IRRELEVANT",
)
STATUS_STRICT_COVERED_REPO_LOCAL = "STRICT_COVERED_REPO_LOCAL"
STATUS_CANDIDATE_COVERED_NEEDS_REPLAY_PAPER = "CANDIDATE_COVERED_NEEDS_REPLAY_PAPER"
STATUS_OWNER_MATERIALIZATION_COMMAND_REQUIRED = "OWNER_MATERIALIZATION_COMMAND_REQUIRED"
STATUS_FETCH_PLAN_ONLY_SOURCE_DISCOVERED = "FETCH_PLAN_ONLY_SOURCE_DISCOVERED"
STATUS_BLOCKED_REQUIRED_FIELDS_MISSING = "BLOCKED_REQUIRED_FIELDS_MISSING"
STATUS_BLOCKED_ROW_COUNT_INSUFFICIENT = "BLOCKED_ROW_COUNT_INSUFFICIENT"
STATUS_BLOCKED_TIME_WINDOW_INSUFFICIENT = "BLOCKED_TIME_WINDOW_INSUFFICIENT"
STATUS_BLOCKED_LEAKAGE_RISK = "BLOCKED_LEAKAGE_RISK"
STATUS_BLOCKED_VENUE_SCOPE_MISMATCH = "BLOCKED_VENUE_SCOPE_MISMATCH"
STRICT_COVERAGE_STATUSES = (
    "STRICT_COVERAGE_PASS",
    "STRICT_COVERAGE_FAIL_CLOSED",
)
STRICT_COVERAGE_PASS = "STRICT_COVERAGE_PASS"
STRICT_COVERAGE_FAIL_CLOSED = "STRICT_COVERAGE_FAIL_CLOSED"
BLOCKER_CODES = (
    "NONE",
    *tuple(status for status in TERMINAL_REQUIREMENT_STATUSES if status.startswith("BLOCKED_")),
    "PR162C_BLOCKED_NO_STRICT_REPO_LOCAL_DATASET",
    "PR162C_BLOCKED_PR162R_REQUIRES_STRICT_COVERAGE",
    "PR163_BLOCKED_NO_VALIDATED_REAL_NONLIVE_REPLAY_ARTIFACTS",
    "PR163_BLOCKED_NO_VALIDATED_REAL_NONLIVE_PAPER_ARTIFACTS",
    "PACKAGE_NOT_INSTALLED_SOURCE_ONLY_CANDIDATE",
)

QKU_EXECUTION_CLASSES = (
    "COMPUTABLE",
    "PARAMETER_ONLY",
    "FEATURE_ONLY",
    "OBJECTIVE_BACKED",
    "CONSTRAINT_BACKED",
    "SOLVER_BACKED",
    "METADATA_ONLY_BLOCKED",
)
EXECUTION_COMPUTABLE = "COMPUTABLE"
EXECUTION_PARAMETER_ONLY = "PARAMETER_ONLY"
EXECUTION_FEATURE_ONLY = "FEATURE_ONLY"
EXECUTION_OBJECTIVE_BACKED = "OBJECTIVE_BACKED"
EXECUTION_CONSTRAINT_BACKED = "CONSTRAINT_BACKED"
EXECUTION_SOLVER_BACKED = "SOLVER_BACKED"
EXECUTION_METADATA_ONLY_BLOCKED = "METADATA_ONLY_BLOCKED"
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
STAGE1_ACTIVE_ELIGIBLE_MARKET_SCOPES = (
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
    "SPORTSBOOK_ODDS",
    "UNKNOWN_MARKET_SCOPE",
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
    "DORMANT_MISSING_INPUT_BINDING",
    "DORMANT_OWNER_REVIEW_REQUIRED",
)
DORMANCY_STATUSES = (
    "NOT_DORMANT_STAGE1_ACTIVE",
    "DORMANT_NON_STAGE1_MARKET_SPECIFIC",
    "DORMANT_UNKNOWN_MARKET_SCOPE",
    "DORMANT_METADATA_ONLY",
    "DORMANT_MISSING_FORMULA",
    "DORMANT_MISSING_INPUT_BINDING",
    "DORMANT_OWNER_REVIEW_REQUIRED",
)
QKU_TRADE_ROLES = (
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
QTT_AGENT_ROUTES = (
    "QTT_RESEARCH_AGENT",
    "QTT_SOURCE_EVIDENCE_AGENT",
    "QTT_PARAMETER_STACK_AGENT",
    "QTT_QUANTUM_ADVISORY_AGENT",
    "QTT_OPTIMIZER_ARBITRATION_AGENT",
    "QTT_REPLAY_AGENT",
    "QTT_PAPER_AGENT",
    "QTT_RISK_AGENT",
    "QTT_CAPITAL_AGENT",
    "QTT_LATENCY_AGENT",
    "QTT_EXECUTION_PREP_AGENT",
    "QTT_EXECUTION_ROUTER_AGENT",
    "QTT_RANKING_AGENT",
    "QTT_OWNER_REVIEW_AGENT",
)
LIVE_MODE_FORMULA_GATE_STATUSES = (
    "LIVE_BLOCKED_NO_FORMULA",
    "LIVE_BLOCKED_NO_PARAMETER_VALUES",
    "LIVE_BLOCKED_NO_INPUT_BINDING",
    "LIVE_BLOCKED_NO_SOLVER_MAPPING",
    "LIVE_BLOCKED_NO_TEST_VECTOR",
    "LIVE_BLOCKED_NO_REPLAY_PAPER_EVIDENCE",
    "LIVE_BLOCKED_NO_RISK_CAPITAL_LATENCY_GATE",
    "LIVE_BLOCKED_OWNER_REVIEW_REQUIRED",
    "LIVE_CANDIDATE_AFTER_REPLAY_PAPER_ONLY",
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

PREDICTION_MARKET_REQUIRED_FIELDS = (
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
PR162A_NORMALIZED_TO_REQUIRED_FIELD_MAP = {
    "timestamp": ("open_time",),
    "market_id_or_ticker_or_token_or_contract_candidate": ("market_id",),
    "venue_scope": ("venue",),
    "price_candidate": ("yes_price", "implied_probability"),
    "bid_candidate": ("yes_bid",),
    "ask_candidate": ("yes_ask",),
    "spread_candidate": ("spread",),
    "volume_candidate": ("volume",),
    "open_interest_candidate": ("open_interest",),
    "settlement_status_candidate": ("resolution_status",),
    "resolution_candidate": ("settlement_value",),
    "source_event_id_candidate": ("event_id",),
}
POST_RESOLUTION_FIELDS = ("resolution_status", "settlement_value", "resolution_time")

DATASET_IDS = (
    "PR162A-DATASET-KALSHI-HISTORICAL-CANDLES-TRADES-TINY",
)
MIN_STRICT_ROW_COUNT = 1000

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
    "PR162B",
)
DOWNSTREAM_PR_ROUTES = (
    "PR162R_ADAPTER_RERUN_AFTER_STRICT_DATASETS",
    "PR163_RESULT_PACKET_EMISSION_AFTER_VALIDATED_REAL_ARTIFACTS",
    "PR164_AUTHENTICITY_SAMPLE_CONFIDENCE_PROVENANCE_VALIDATION",
    "PR165_RESULT_BACKED_RANKING_AFTER_PR164",
    "FUTURE_LIVE_OWNER_RISK_CAPITAL_LATENCY_SOURCE_GATED",
)

REQUIRED_INPUT_REPORTS = (
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
    "docs/master_plan/generated/PR162_QuantumLiveModeControlPlaneBridge.report.json",
    "docs/master_plan/generated/PR162_QuantumLatencyLivePathReadinessBridge.report.json",
    "docs/master_plan/generated/PR162_QKUQuantumDownstreamAgentRouteMatrix.report.json",
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
    "docs/master_plan/generated/PR162A_ReportShardManifest.report.json",
    "docs/master_plan/generated/PR162B_FinalSummary.report.json",
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
    "docs/master_plan/generated/PR162B_ReportShardManifest.report.json",
    "tools/currentize_pr152_after_generated_artifacts.py",
    "tools/run_validation_gates.py",
    "tools/validate_grand_global_debug_logical_consistency_audit.py",
    "tools/ci_branch_context.py",
    "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
    "tests/fail_closed/test_run_validation_gates.py",
)
FALLBACK_INPUT_REPORTS = {
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json": (
        "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
        "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json",
    ),
}
PR162B_REGISTRY_REPORTS = (
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
    "PR162B_QKUFormulaBindingProofMatrix.report.json",
    "PR162B_QKUMarketClassificationRegistry.report.json",
    "PR162B_QKUStage1PredictionMarketActivationGate.report.json",
    "PR162B_QKUDormancyRegistry.report.json",
    "PR162B_QTTAgentStage1QKUActivationAllowlist.report.json",
    "PR162B_QuantumQUBOIsingFormulaMaterialization.report.json",
    "PR162B_PR162CDataRequirementHandoff.report.json",
)
