"""Central PR162A policy constants.

This module is the single PR162A source for dataset authority classes,
lifecycle states, blocker codes, materialization modes, report names, and
forbidden authority boundaries.
"""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR162A"
PR_LABEL = "PR162A_SAFE_REPO_LOCAL_NONLIVE_DATASET_MATERIALIZATION_AUTHORITY_GATE"
EXPECTED_BRANCH = "pr162a-safe-repo-local-nonlive-dataset-materialization-authority-gate"
SUCCESS_MARKER = "PR162A_SAFE_REPO_LOCAL_NONLIVE_DATASET_MATERIALIZATION_AUTHORITY_GATE_VALIDATED"
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "safe_repo_local_nonlive_dataset_materialization_authority_gate"
)

GENERATED_DIR = Path("docs/master_plan/generated")
SCHEMA_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "safe_repo_local_nonlive_dataset_materialization_authority_gate/schemas"
)
SHARD_DIR = GENERATED_DIR / "pr162a_safe_repo_local_nonlive_dataset_shards"
DATASET_ROOT = Path("data/stage1_prediction_markets/nonlive_datasets/pr162a")
DATASET_MANIFEST_DIR = DATASET_ROOT / "manifests"
RAW_CANDIDATE_DIR = DATASET_ROOT / "raw_candidates"
NORMALIZED_CANDIDATE_DIR = DATASET_ROOT / "normalized_candidates"
FIXTURE_DIR = DATASET_ROOT / "fixtures"
FETCH_PLAN_DIR = DATASET_ROOT / "fetch_plans"
KALSHI_TINY_RAW_PATH = (
    RAW_CANDIDATE_DIR / "kalshi_historical_market_trades_candlesticks_tiny_candidate.raw.json"
)
KALSHI_TINY_NORMALIZED_PATH = (
    NORMALIZED_CANDIDATE_DIR
    / "kalshi_historical_market_trades_candlesticks_tiny_candidate.normalized.jsonl"
)
KALSHI_TINY_MANIFEST_PATH = (
    DATASET_MANIFEST_DIR
    / "kalshi_historical_market_trades_candlesticks_tiny_candidate.manifest.json"
)

AUTHORITY_CLASS = "SAFE_REPO_LOCAL_NONLIVE_DATASET_CANDIDATE_OR_CONTROL_PLANE_ONLY"
PR152_CURRENTIZATION_RESULT_PENDING = "PENDING_EXTERNAL_VALIDATION_COMMAND"
PR152_CURRENTIZATION_RESULT_PASS = "EXTERNAL_VALIDATION_CONFIRMED_PASS"
PR152_CURRENTIZATION_RESULT_FAILED = "EXTERNAL_VALIDATION_FAILED"
PR152_CURRENTIZATION_RESULTS = (
    PR152_CURRENTIZATION_RESULT_PENDING,
    PR152_CURRENTIZATION_RESULT_PASS,
    PR152_CURRENTIZATION_RESULT_FAILED,
)
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
PR152_CURRENTIZATION_VALIDATOR_REF = (
    "tools/validate_grand_global_debug_logical_consistency_audit.py"
)

REPORT_SHARD_RECORD_TARGET = 1000
REPORT_SHARD_PREVIEW_RECORD_LIMIT = 3
REPORT_SHARD_BYTE_THRESHOLD = 900_000

REPORT_FILENAMES = (
    "PR162A_FinalSummary.report.json",
    "PR162A_SharedDictionary.report.json",
    "PR162A_SourceDiscoveryCandidateRegistry.report.json",
    "PR162A_FetchPlanAndOwnerMaterializationCommandQueue.report.json",
    "PR162A_DatasetMaterializationManifest.report.json",
    "PR162A_DatasetAuthorityGate.report.json",
    "PR162A_DatasetProvenanceAccessRightsLedger.report.json",
    "PR162A_DatasetSafetyAndForbiddenPathScan.report.json",
    "PR162A_DatasetLifecycleStateRegistry.report.json",
    "PR162A_DatasetSchemaNormalizationContract.report.json",
    "PR162A_NormalizedDatasetInventory.report.json",
    "PR162A_DataQualityLeakageAndTimeWindowAudit.report.json",
    "PR162A_MarketScenarioQKUMappingMatrix.report.json",
    "PR162A_PR161FRunPlanDatasetCoverageBridge.report.json",
    "PR162A_PR162AdapterRerunReadinessBridge.report.json",
    "PR162A_PR163ReadinessBlockerStatus.report.json",
    "PR162A_QuantumQKUDatasetFeatureBridge.report.json",
    "PR162A_QuantumFeatureMaterializationWorkOrderQueue.report.json",
    "PR162A_QTTAgentDatasetHandoffBridge.report.json",
    "PR162A_MissingValueCandidateRegistry.report.json",
    "PR162A_ForbiddenAuthorityScan.report.json",
    "PR162A_ReportShardManifest.report.json",
)
SHARD_MANIFEST_REPORT_FILENAME = "PR162A_ReportShardManifest.report.json"
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

SOURCE_CLASSES = (
    "OFFICIAL_SOURCE_CANDIDATE",
    "OFFICIAL_PUBLIC_HISTORICAL_DATA_CANDIDATE",
    "OFFICIAL_PUBLIC_PRICE_HISTORY_CANDIDATE",
    "OFFICIAL_PUBLIC_OHLC_EVENT_HISTORY_CANDIDATE",
    "RESEARCH_SOURCE_CANDIDATE",
    "THIRD_PARTY_DATA_VENDOR_CANDIDATE",
    "SOCIAL_SIGNAL_CANDIDATE",
    "WEB_SOURCE_CANDIDATE",
    "INSTITUTIONAL_METHOD_CANDIDATE",
    "OWNER_PROVIDED_CANDIDATE",
    "CLASSICAL_METHOD_CANDIDATE",
    "HYBRID_METHOD_CANDIDATE",
    "QUANTUM_METHOD_CANDIDATE",
    "QUANTUM_BACKEND_DOC_CANDIDATE",
    "QUANTUM_ALGORITHM_DOC_CANDIDATE",
    "QUANTUM_PARAMETER_RANGE_CANDIDATE",
    "QUANTUM_ENCODING_CANDIDATE",
)

DATASET_AUTHORITY_CLASSES = (
    "REPO_LOCAL_ACCEPTED_NONLIVE_HISTORICAL_DATASET",
    "REPO_LOCAL_OWNER_PROVIDED_NONLIVE_DATASET",
    "REPO_LOCAL_OFFICIAL_PUBLIC_HISTORICAL_DATASET_CANDIDATE",
    "REPO_LOCAL_OFFICIAL_PUBLIC_PRICE_HISTORY_DATASET_CANDIDATE",
    "REPO_LOCAL_OFFICIAL_PUBLIC_OHLC_EVENT_HISTORY_DATASET_CANDIDATE",
    "REPO_LOCAL_PUBLIC_RESEARCH_DATASET_CANDIDATE",
    "REPO_LOCAL_THIRD_PARTY_DATA_VENDOR_CANDIDATE",
    "REPO_LOCAL_INSTITUTIONAL_RESEARCH_DATASET_CANDIDATE",
    "REPO_LOCAL_CLASSICAL_BENCHMARK_DATASET_CANDIDATE",
    "REPO_LOCAL_HYBRID_BENCHMARK_DATASET_CANDIDATE",
    "REPO_LOCAL_QUANTUM_BENCHMARK_DATASET_CANDIDATE",
    "REPO_LOCAL_SYNTHETIC_FIXTURE_NOT_REAL_ARTIFACT_DATA",
    "REPO_LOCAL_SMOKE_FIXTURE_NOT_REAL_ARTIFACT_DATA",
    "ONLINE_DISCOVERED_CANDIDATE_METADATA_ONLY",
    "FETCH_PLAN_ONLY_NOT_MATERIALIZED",
    "OWNER_ATTESTATION_REQUIRED_DATASET",
    "UNSAFE_OR_FORBIDDEN_DATASET",
    "UNKNOWN_OR_UNMAPPABLE_DATASET",
    "ACCESS_RIGHTS_UNCLEAR_DATASET",
    "DUPLICATE_DATASET",
    "LIVE_OR_PRIVATE_DATASET_BLOCKED",
)
RUN_CAPABLE_DATASET_AUTHORITY_CLASSES = (
    "REPO_LOCAL_ACCEPTED_NONLIVE_HISTORICAL_DATASET",
    "REPO_LOCAL_OWNER_PROVIDED_NONLIVE_DATASET",
    "REPO_LOCAL_OFFICIAL_PUBLIC_HISTORICAL_DATASET_CANDIDATE",
    "REPO_LOCAL_OFFICIAL_PUBLIC_PRICE_HISTORY_DATASET_CANDIDATE",
    "REPO_LOCAL_OFFICIAL_PUBLIC_OHLC_EVENT_HISTORY_DATASET_CANDIDATE",
    "REPO_LOCAL_PUBLIC_RESEARCH_DATASET_CANDIDATE",
    "REPO_LOCAL_THIRD_PARTY_DATA_VENDOR_CANDIDATE",
)

ACCESS_RIGHTS_STATUSES = (
    "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK",
    "OWNER_PROVIDED_ATTESTED_OK",
    "RESEARCH_USE_CANDIDATE_OK",
    "THIRD_PARTY_TERMS_REVIEW_REQUIRED",
    "AUTHENTICATION_REQUIRED_BLOCKED",
    "PRIVATE_ACCOUNT_STATE_REQUIRED_BLOCKED",
    "LIVE_CONNECTOR_REQUIRED_BLOCKED",
    "ORDER_ENDPOINT_REQUIRED_BLOCKED",
    "ACCESS_RIGHTS_UNCLEAR_BLOCKED",
    "OWNER_ATTESTATION_REQUIRED",
)
MATERIALIZATION_MODES = (
    "DISCOVERY_ONLY",
    "FETCH_PLAN_ONLY",
    "OWNER_LOCAL_FILE_REGISTRATION",
    "BOUNDED_PUBLIC_FETCH_CANDIDATE",
    "NORMALIZE_EXISTING_REPO_LOCAL_DATA",
    "COMMITTED_FIXTURE_ONLY",
    "BLOCKED_WITH_ACTIONABLE_OWNER_COMMAND",
)
DATASET_LIFECYCLE_STATES = (
    "SOURCE_CANDIDATE_DISCOVERED",
    "SOURCE_CLASSIFIED",
    "ACCESS_RIGHTS_CLASSIFIED",
    "MATERIALIZATION_PLAN_CREATED",
    "OWNER_APPROVAL_OR_PUBLIC_ACCESS_CONFIRMED",
    "REPO_LOCAL_CANDIDATE_REGISTERED",
    "REPO_LOCAL_CANDIDATE_NORMALIZED",
    "DATA_QUALITY_AND_LEAKAGE_AUDITED",
    "QKU_SCENARIO_RUNPLAN_MAPPED",
    "RUN_CAPABLE_GATE_PASSED",
    "PR162B_RERUN_READY",
    "BLOCKED_ACCESS_RIGHTS_UNCLEAR",
    "BLOCKED_AUTHENTICATION_REQUIRED",
    "BLOCKED_PRIVATE_STATE_REQUIRED",
    "BLOCKED_LIVE_OR_ORDER_ENDPOINT",
    "BLOCKED_UNBOUNDED_OR_TOO_LARGE",
    "BLOCKED_UNMAPPABLE_SCHEMA",
    "BLOCKED_UNMAPPABLE_QKU",
    "BLOCKED_DATA_LEAKAGE_RISK",
    "BLOCKED_SYNTHETIC_ONLY",
    "BLOCKED_DUPLICATE",
    "BLOCKED_OWNER_ATTESTATION_REQUIRED",
    "BLOCKED_NO_SAFE_REPO_LOCAL_DATA",
)
RUN_CAPABLE_GATE_STATUSES = (
    "RUN_CAPABLE_GATE_PASSED",
    "RUN_CAPABLE_GATE_BLOCKED",
    "RUN_CAPABLE_GATE_NOT_APPLICABLE",
)
DATASET_SEED_CANDIDATE_READY = "DATASET_SEED_CANDIDATE_READY"
ADAPTER_MECHANICS_FIXTURE_READY = "ADAPTER_MECHANICS_FIXTURE_READY"
VENUE_SCOPED_RUN_CAPABLE_READY = "VENUE_SCOPED_RUN_CAPABLE_READY"
RUN_CAPABLE_BLOCKED_INSUFFICIENT_ROWS = "RUN_CAPABLE_BLOCKED_INSUFFICIENT_ROWS"
RUN_CAPABLE_BLOCKED_INSUFFICIENT_TIME_WINDOW = (
    "RUN_CAPABLE_BLOCKED_INSUFFICIENT_TIME_WINDOW"
)
RUN_CAPABLE_BLOCKED_VENUE_SCOPE_MISMATCH = (
    "RUN_CAPABLE_BLOCKED_VENUE_SCOPE_MISMATCH"
)
RUN_CAPABLE_BLOCKED_QKU_SCOPE_TOO_BROAD = "RUN_CAPABLE_BLOCKED_QKU_SCOPE_TOO_BROAD"
RUN_CAPABLE_BLOCKED_SCENARIO_SCOPE_TOO_BROAD = (
    "RUN_CAPABLE_BLOCKED_SCENARIO_SCOPE_TOO_BROAD"
)
RUN_CAPABLE_BLOCKED_PR162B_REQUIRES_STRICT_DATASET_COVERAGE = (
    "RUN_CAPABLE_BLOCKED_PR162B_REQUIRES_STRICT_DATASET_COVERAGE"
)
DATASET_COVERAGE_STATES = (
    DATASET_SEED_CANDIDATE_READY,
    ADAPTER_MECHANICS_FIXTURE_READY,
    VENUE_SCOPED_RUN_CAPABLE_READY,
    RUN_CAPABLE_BLOCKED_INSUFFICIENT_ROWS,
    RUN_CAPABLE_BLOCKED_INSUFFICIENT_TIME_WINDOW,
    RUN_CAPABLE_BLOCKED_VENUE_SCOPE_MISMATCH,
    RUN_CAPABLE_BLOCKED_QKU_SCOPE_TOO_BROAD,
    RUN_CAPABLE_BLOCKED_SCENARIO_SCOPE_TOO_BROAD,
    RUN_CAPABLE_BLOCKED_PR162B_REQUIRES_STRICT_DATASET_COVERAGE,
)
RUN_CAPABLE_BLOCKER_CODES = tuple(
    state for state in DATASET_COVERAGE_STATES if state.startswith("RUN_CAPABLE_BLOCKED_")
)
MIN_STRICT_RUN_CAPABLE_ROW_COUNT = 100
MIN_STRICT_RUN_CAPABLE_TIME_WINDOW_SECONDS = 3600
NORMALIZATION_STATUSES = ("NORMALIZED", "NOT_NORMALIZED", "NORMALIZATION_BLOCKED")
DATA_QUALITY_STATUSES = ("PASS", "FAIL_CLOSED", "WARNING_CANDIDATE_ONLY")
MAPPING_STATUSES = (
    "MAPPED_TO_RUN_CAPABLE_CANDIDATE",
    "MAPPED_TO_CANDIDATE_BLOCKED_FROM_RUN",
    "BLOCKED_UNMAPPABLE_QKU",
)
QUANTUM_FEATURE_STATUSES = (
    "FEATURE_SEED_CANDIDATE_ONLY",
    "QUANTUM_DATASET_FEATURE_RUN_CAPABLE_READY",
    "QUANTUM_DATASET_FEATURE_CANDIDATE_READY",
    "QUANTUM_DATASET_FEATURE_BLOCKED_NO_SAFE_DATA",
)
LIVE_HOT_PATH_ADMISSIBILITY_STATES = (
    "PRECOMPUTED_SNAPSHOT_ONLY",
    "ASYNC_CONTROL_PLANE_ONLY",
    "FORBIDDEN_UNTIL_FUTURE_OWNER_GATE",
)

FORBIDDEN_AUTHORITY_CATEGORIES = (
    "LIVE_TRADING_AUTHORITY",
    "LIVE_ORDER_AUTHORITY",
    "PRIVATE_ACCOUNT_STATE",
    "LIVE_CONNECTOR_SEMANTICS",
    "SOURCE_FACT_ACCEPTANCE_WITHOUT_GATE",
    "REPLAY_RESULT_EVIDENCE",
    "PAPER_RESULT_EVIDENCE",
    "RESULT_PACKET_EMISSION",
    "PR161E_INGESTION_TRUTH",
    "RESULT_BACKED_RANKING_UPDATE",
    "PROFIT_EVIDENCE",
    "PROFIT_GUARANTEE",
    "OPTIMIZER_EXECUTION_EVIDENCE",
    "QUANTUM_BACKEND_EXECUTION_EVIDENCE",
    "QUANTUM_SIMULATOR_EXECUTION_EVIDENCE",
    "QTT_SHA_FREEZE_CHECKSUM_GLOBAL_DIGEST_AUTHORITY",
    "ATOMICROWS_BUNDLE_HASH_FREEZE_AUTHORITY",
)
FORBIDDEN_PATH_PATTERNS = (
    ".git/",
    ".venv/",
    "venv/",
    "__pycache__/",
    ".pytest_cache/",
    "build/",
    "dist/",
    "node_modules/",
    ".ssh/",
    ".aws/",
    ".azure/",
    ".gcp/",
    "secrets/",
    "private_key",
    "credential",
)
ALLOWED_DATASET_PATH_PREFIXES = (
    DATASET_MANIFEST_DIR.as_posix() + "/",
    RAW_CANDIDATE_DIR.as_posix() + "/",
    NORMALIZED_CANDIDATE_DIR.as_posix() + "/",
    FIXTURE_DIR.as_posix() + "/",
    FETCH_PLAN_DIR.as_posix() + "/",
)

BLOCKER_CODES = (
    "NONE",
    "PR162A_BLOCKED_ACCESS_RIGHTS_UNCLEAR",
    "PR162A_BLOCKED_AUTHENTICATION_REQUIRED",
    "PR162A_BLOCKED_PRIVATE_STATE_REQUIRED",
    "PR162A_BLOCKED_LIVE_OR_ORDER_ENDPOINT",
    "PR162A_BLOCKED_UNBOUNDED_OR_TOO_LARGE",
    "PR162A_BLOCKED_UNMAPPABLE_SCHEMA",
    "PR162A_BLOCKED_UNMAPPABLE_QKU",
    "PR162A_BLOCKED_DATA_LEAKAGE_RISK",
    "PR162A_BLOCKED_SYNTHETIC_ONLY",
    "PR162A_BLOCKED_DUPLICATE",
    "PR162A_BLOCKED_OWNER_ATTESTATION_REQUIRED",
    "PR162A_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",
    "PR162A_BLOCKED_FORBIDDEN_PATH",
    "PR162A_BLOCKED_FORBIDDEN_AUTHORITY_PATTERN",
    "PR162A_BLOCKED_SOURCE_EVIDENCE_REQUIRED",
    "PR162A_BLOCKED_NETWORK_DISABLED_BY_DEFAULT",
    "PR162A_BLOCKED_PR163_REQUIRES_VALIDATED_REAL_ARTIFACTS",
    "PR162A_PR162B_RERUN_READY",
    "PR162A_PR162R_RERUN_READY",
    "PR163_BLOCKED_NO_VALIDATED_REAL_NONLIVE_REPLAY_ARTIFACTS",
    "PR163_BLOCKED_NO_VALIDATED_REAL_NONLIVE_PAPER_ARTIFACTS",
    "QUANTUM_BLOCKED_NO_SAFE_DATA",
    *RUN_CAPABLE_BLOCKER_CODES,
)

DOWNSTREAM_PR_ROUTES = (
    "PR162B_RERUN_PR162_WITH_PR162A_DATASETS",
    "PR162R_RERUN_PR162_WITH_PR162A_DATASETS",
    "PR163_RESULT_PACKET_ROUTE_AFTER_VALIDATED_REAL_NONLIVE_ARTIFACTS",
    "PR164_RESULT_AUTHENTICITY_GATE_ROUTE",
    "PR165_RESULT_BACKED_RANKING_GATE_ROUTE",
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
)

REQUIRED_INPUT_REPORTS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "src/qtt/stage1_prediction_markets/launch_readiness/day1_launch_readiness_roadmap_policy.py",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
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
    "docs/master_plan/generated/PR162_NonLiveDatasetDiscovery.report.json",
    "docs/master_plan/generated/PR162_DataAuthorityAndProvenanceGate.report.json",
    "docs/master_plan/generated/PR162_ReplayDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162_PaperDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162_AdapterCapabilityDiscovery.report.json",
    "docs/master_plan/generated/PR162_SyntheticVsRealNonLiveSeparation.report.json",
    "docs/master_plan/generated/PR162_RealNonLiveRunArtifactCandidateRegistry.report.json",
    "docs/master_plan/generated/PR162_ResultPacketReadinessHandoffCandidate.report.json",
    "docs/master_plan/generated/PR162_PR161EIngestionHandoffCandidate.report.json",
    "docs/master_plan/generated/PR162_QKUArtifactCoverageBridge.report.json",
    "docs/master_plan/generated/PR162_QTTAgentExecutorHandoffBridge.report.json",
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
    PR152_CURRENTIZATION_REPORT_REF,
    "tools/ci_branch_context.py",
    "tools/run_validation_gates.py",
    PR152_CURRENTIZATION_VALIDATOR_REF,
)
PR136_SECTION_CROSSWALK_ALIASES = (
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
)

AGENT_ROLES = (
    "QTT_RESEARCH_AGENT",
    "QTT_SOURCE_EVIDENCE_AGENT",
    "QTT_ATOMICROWS_ENRICHMENT_AGENT",
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
    "QTT_OWNER_REVIEW_AGENT",
    "QTT_COMMANDER_AGENT",
    "QTT_GOVERNANCE_AGENT",
    "QTT_VENUE_SPECIALIST_AGENT",
    "QTT_EXECUTION_ROUTER_AGENT",
)

KALSHI_RUN_CAPABLE_DATASET_ID = "PR162A-DATASET-KALSHI-HISTORICAL-CANDLES-TRADES-TINY"
SYNTHETIC_BLOCKED_DATASET_ID = "PR162A-DATASET-SYNTHETIC-SMOKE-BLOCKED"
POLYMARKET_METADATA_DATASET_ID = "PR162A-DATASET-POLYMARKET-METADATA-ONLY-BLOCKED"
IBKR_BLOCKED_DATASET_ID = "PR162A-DATASET-IBKR-FORECASTEX-AUTH-BLOCKED"

QUANTUM_FEATURE_FAMILIES = (
    "binary_outcome_price_series",
    "yes_no_spread_series",
    "liquidity_depth_proxy_series",
    "market_bundle_correlation_candidate",
    "event_category_signal_candidate",
    "scenario_probability_candidate",
    "risk_budget_input_candidate",
    "capital_allocation_input_candidate",
    "position_sizing_input_candidate",
    "latency_cost_tradeoff_input_candidate",
    "QUBO_variable_candidate",
    "Ising_spin_candidate",
    "BQM_variable_candidate",
    "CQM_constraint_candidate",
    "penalty_term_input_candidate",
    "objective_term_input_candidate",
    "coefficient_scale_input_candidate",
    "constraint_weight_input_candidate",
    "classical_baseline_feature_candidate",
    "hybrid_comparator_feature_candidate",
    "future_precomputed_snapshot_feature_candidate",
)

SCHEMA_ENUM_FIELDS = {
    "created_by_pr": (PR_ID,),
    "authority_class": (AUTHORITY_CLASS,),
    "source_class": SOURCE_CLASSES,
    "dataset_authority_class": DATASET_AUTHORITY_CLASSES,
    "dataset_lifecycle_state": DATASET_LIFECYCLE_STATES,
    "access_rights_status": ACCESS_RIGHTS_STATUSES,
    "materialization_mode": MATERIALIZATION_MODES,
    "run_capable_gate_status": RUN_CAPABLE_GATE_STATUSES,
    "dataset_coverage_state": DATASET_COVERAGE_STATES,
    "rerun_readiness_state": DATASET_COVERAGE_STATES,
    "normalization_status": NORMALIZATION_STATUSES,
    "data_quality_status": DATA_QUALITY_STATUSES,
    "schema_validation_status": DATA_QUALITY_STATUSES,
    "leakage_audit_status": DATA_QUALITY_STATUSES,
    "mapping_status": MAPPING_STATUSES,
    "quantum_feature_materialization_status": QUANTUM_FEATURE_STATUSES,
    "live_hot_path_admissibility": LIVE_HOT_PATH_ADMISSIBILITY_STATES,
    "blocker_code": BLOCKER_CODES,
}
NO_SCATTERED_POLICY_ALLOWLIST = ("constants.py", "schema_writer.py")
