"""Canonical PR162 policy constants.

This module is the single PR162 source for blocker codes, authority classes,
readiness states, report names, and forbidden authority boundaries.
"""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR162"
PR_LABEL = "PR162_SAFE_NONLIVE_REPLAY_PAPER_DATA_ADAPTER_QUANTUM_FORWARD_BRIDGE"
EXPECTED_BRANCH = (
    "pr162-safe-nonlive-replay-paper-executor-data-adapter-quantum-forward-bridge"
)
SUCCESS_MARKER = "PR162_SAFE_NONLIVE_REPLAY_PAPER_DATA_ADAPTER_QUANTUM_FORWARD_BRIDGE_VALIDATED"
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "nonlive_replay_paper_data_adapter_quantum_forward_bridge"
)
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
PR152_CURRENTIZATION_REPORT_REF = (
    "docs/master_plan/generated/"
    "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
)
PR152_CURRENTIZATION_VALIDATOR_REF = (
    "tools/validate_grand_global_debug_logical_consistency_audit.py"
)

GENERATED_DIR = Path("docs/master_plan/generated")
SCHEMA_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "nonlive_replay_paper_data_adapter_quantum_forward_bridge/schemas"
)
SHARD_DIR = GENERATED_DIR / "pr162_safe_nonlive_replay_paper_quantum_forward_shards"

AUTHORITY_CLASS = "NONLIVE_ARTIFACT_CANDIDATE_OR_CONTROL_PLANE_ONLY"
ARTIFACT_AUTHORITY_CLASS = "CANDIDATE_NONLIVE_ARTIFACT_UNVALIDATED"
BLUEPRINT_AUTHORITY_CLASS = "CANDIDATE_BLUEPRINT_ONLY"
PARAMETER_UNKNOWN_AUTHORITY_CLASS = "UNKNOWN_REQUIRED"
METRIC_AUTHORITY_CLASS = "CANDIDATE_NONLIVE_ARTIFACT_UNVALIDATED"
EXECUTION_MODE = "SAFE_NONLIVE_REPO_LOCAL"

REPORT_SHARD_RECORD_TARGET = 1000
REPORT_SHARD_PREVIEW_RECORD_LIMIT = 3
REPORT_SHARD_BYTE_THRESHOLD = 900_000

REPORT_FILENAMES = (
    "PR162_FinalSummary.report.json",
    "PR162_SharedDictionary.report.json",
    "PR162_NonLiveDatasetDiscovery.report.json",
    "PR162_DataAuthorityAndProvenanceGate.report.json",
    "PR162_ReplayDataAdapterContract.report.json",
    "PR162_PaperDataAdapterContract.report.json",
    "PR162_AdapterCapabilityDiscovery.report.json",
    "PR162_SyntheticVsRealNonLiveSeparation.report.json",
    "PR162_RealNonLiveRunArtifactCandidateRegistry.report.json",
    "PR162_ResultPacketReadinessHandoffCandidate.report.json",
    "PR162_PR161EIngestionHandoffCandidate.report.json",
    "PR162_QKUArtifactCoverageBridge.report.json",
    "PR162_QTTAgentExecutorHandoffBridge.report.json",
    "PR162_QuantumClassicalHybridArtifactInputBridge.report.json",
    "PR162_ExternalCandidateIntakeRegistry.report.json",
    "PR162_ForbiddenAuthorityScan.report.json",
    "PR162_QKUQuantumExecutionReadinessBridge.report.json",
    "PR162_QKUQuantumProblemEncodingBlueprint.report.json",
    "PR162_QuantumParameterRangeCandidateRegistry.report.json",
    "PR162_QuantumBackendFitCandidateMatrix.report.json",
    "PR162_QuantumClassicalHybridComparatorBlueprint.report.json",
    "PR162_QuantumReplayPaperWorkOrderQueue.report.json",
    "PR162_QuantumLiveModeControlPlaneBridge.report.json",
    "PR162_QuantumLatencyLivePathReadinessBridge.report.json",
    "PR162_QKUQuantumDownstreamAgentRouteMatrix.report.json",
    "PR162_ReportShardManifest.report.json",
)

SHARD_MANIFEST_REPORT_FILENAME = "PR162_ReportShardManifest.report.json"
SHARD_MANIFEST_REPORT_PATH = GENERATED_DIR / SHARD_MANIFEST_REPORT_FILENAME
SHARED_DICTIONARY_REPORT_FILENAME = "PR162_SharedDictionary.report.json"
SHARED_DICTIONARY_REPORT_PATH = GENERATED_DIR / SHARED_DICTIONARY_REPORT_FILENAME

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
}

FORBIDDEN_AUTHORITY_CATEGORIES = (
    "LIVE_TRADING_AUTHORITY",
    "LIVE_ORDER_AUTHORITY",
    "PRIVATE_ACCOUNT_STATE",
    "LIVE_CONNECTOR_SEMANTICS",
    "PAPER_ACCOUNT_VENUE_API_EXECUTION",
    "REPLAY_RESULT_EVIDENCE",
    "PAPER_RESULT_EVIDENCE",
    "PROFIT_EVIDENCE",
    "PROFIT_GUARANTEE",
    "RESULT_BACKED_RANKING_UPDATE",
    "OPTIMIZER_EXECUTION_EVIDENCE",
    "QUANTUM_BACKEND_EXECUTION_EVIDENCE",
    "QUANTUM_SIMULATOR_EXECUTION_EVIDENCE",
    "QUANTUM_ADVANTAGE_EVIDENCE",
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

ALLOWLIST_SCAN_ROOTS = (
    "data",
    "datasets",
    "fixtures",
    "tests/fixtures",
    "docs/master_plan/generated",
)

DATASET_AUTHORITY_CLASSES = (
    "REPO_LOCAL_ACCEPTED_NONLIVE_HISTORICAL_DATASET",
    "REPO_LOCAL_OWNER_PROVIDED_NONLIVE_DATASET",
    "REPO_LOCAL_PUBLIC_RESEARCH_DATASET_CANDIDATE",
    "REPO_LOCAL_SYNTHETIC_FIXTURE",
    "REPO_LOCAL_SMOKE_FIXTURE",
    "ONLINE_DISCOVERED_CANDIDATE_METADATA_ONLY",
    "UNKNOWN_OR_UNMAPPABLE_DATASET",
    "UNSAFE_OR_FORBIDDEN_DATASET",
)
RUN_CAPABLE_DATASET_AUTHORITY_CLASSES = (
    "REPO_LOCAL_ACCEPTED_NONLIVE_HISTORICAL_DATASET",
    "REPO_LOCAL_OWNER_PROVIDED_NONLIVE_DATASET",
    "REPO_LOCAL_PUBLIC_RESEARCH_DATASET_CANDIDATE",
)

SOURCE_CLASSES = (
    "OFFICIAL_SOURCE_CANDIDATE",
    "RESEARCH_SOURCE_CANDIDATE",
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

ARTIFACT_STATUS_ENUMS = (
    "REPLAY_ARTIFACT_CANDIDATE_CREATED",
    "PAPER_ARTIFACT_CANDIDATE_CREATED",
    "REPLAY_BLOCKED_NO_SAFE_DATA",
    "PAPER_BLOCKED_NO_SAFE_DATA",
    "REPLAY_BLOCKED_SYNTHETIC_ONLY",
    "PAPER_BLOCKED_SYNTHETIC_ONLY",
    "REPLAY_BLOCKED_UNSAFE_DATA",
    "PAPER_BLOCKED_UNSAFE_DATA",
    "REPLAY_BLOCKED_UNMAPPABLE",
    "PAPER_BLOCKED_UNMAPPABLE",
    "BOTH_LANES_CANDIDATE_READY",
    "BOTH_LANES_NOT_READY",
    "PARTIAL_LANE_ONLY",
    "NO_REAL_NONLIVE_ARTIFACT_CANDIDATE_CREATED",
)

RESULT_READINESS_STATES = (
    "RESULT_PACKET_HANDOFF_CANDIDATE_ONLY",
    "RESULT_PACKET_BLOCKED_NO_VALIDATED_REAL_NONLIVE_ARTIFACTS",
    "RESULT_PACKET_BLOCKED_PARTIAL_LANE_ONLY",
    "RESULT_PACKET_BLOCKED_SYNTHETIC_ONLY",
    "RESULT_PACKET_BLOCKED_UNSAFE_DATA",
)

PR161E_HANDOFF_STATES = (
    "PR161E_HANDOFF_CANDIDATE_ONLY",
    "PR161E_HANDOFF_BLOCKED_NO_VALIDATED_REAL_NONLIVE_ARTIFACTS",
    "PR161E_HANDOFF_BLOCKED_PARTIAL_LANE_ONLY",
    "PR161E_HANDOFF_BLOCKED_SYNTHETIC_ONLY",
    "PR161E_HANDOFF_BLOCKED_UNSAFE_DATA",
    "PR161E_HANDOFF_BLOCKED_UNMAPPABLE_QKU",
    "PR161E_HANDOFF_BLOCKED_SCHEMA_CONSUMER_NOT_FOUND",
    "PR161E_HANDOFF_BLOCKED_AUTHORITY_DRIFT",
    "PR161E_HANDOFF_BLOCKED_QUANTUM_BLUEPRINT_ONLY",
    "PR161E_HANDOFF_BLOCKED_QUANTUM_BACKEND_EVIDENCE_FORBIDDEN",
)

QKU_COVERAGE_STATES = (
    "QKU_COVERED_WITH_BLOCKED_NONLIVE_LANES",
    "QKU_COVERED_WITH_REAL_NONLIVE_REPLAY_ARTIFACT_CANDIDATE",
    "QKU_COVERED_WITH_REAL_NONLIVE_PAPER_ARTIFACT_CANDIDATE",
    "QKU_COVERED_WITH_BOTH_LANES_CANDIDATE",
    "QKU_BLOCKED_NO_REPO_LOCAL_DATA",
    "QKU_BLOCKED_SYNTHETIC_ONLY",
    "QKU_BLOCKED_UNSAFE_DATA",
    "QKU_BLOCKED_UNMAPPABLE",
)

QTT_AGENT_HANDOFF_STATUSES = (
    "PR162_AGENT_HANDOFF_READY_BLOCKED_INPUTS",
    "PR162_AGENT_HANDOFF_CANDIDATE_ONLY",
    "PR162_AGENT_HANDOFF_QUARANTINE_REQUIRED",
    "PR162_AGENT_HANDOFF_OWNER_ESCALATION_REQUIRED",
)

QUANTUM_FORWARD_PROMOTION_STATES = (
    "QUANTUM_FORWARD_BLUEPRINT_ONLY",
    "QUANTUM_FORWARD_WORK_ORDER_READY",
    "QUANTUM_FORWARD_RESULT_PACKET_BLOCKED",
    "QUANTUM_FORWARD_FUTURE_LIVE_GATED",
)

QUANTUM_READINESS_STATES = (
    "NOT_QUANTUM_APPLICABLE",
    "QUANTUM_APPLICABLE_METADATA_ONLY_BLOCKED",
    "QUANTUM_ENCODING_BLUEPRINT_READY",
    "QUANTUM_PARAMETER_CANDIDATE_READY",
    "QUANTUM_BACKEND_FIT_CANDIDATE_READY",
    "QUANTUM_CLASSICAL_COMPARATOR_BLUEPRINT_READY",
    "QUANTUM_REPLAY_PAPER_WORK_ORDER_READY",
    "QUANTUM_REAL_NONLIVE_ARTIFACT_CANDIDATE_READY",
    "QUANTUM_RESULT_PACKET_HANDOFF_CANDIDATE_READY",
    "QUANTUM_FUTURE_LIVE_CONTROL_PLANE_CANDIDATE",
    "QUANTUM_FUTURE_LIVE_PRECOMPUTED_SNAPSHOT_CANDIDATE",
    "QUANTUM_BLOCKED_NO_QKU_LINEAGE",
    "QUANTUM_BLOCKED_NO_SAFE_DATA",
    "QUANTUM_BLOCKED_NO_CLASSICAL_BASELINE",
    "QUANTUM_BLOCKED_NO_ENCODING",
    "QUANTUM_BLOCKED_BACKEND_UNAVAILABLE_OR_UNVERIFIED",
    "QUANTUM_BLOCKED_LIVE_PATH_LATENCY_UNSAFE",
    "QUANTUM_BLOCKED_NO_OWNER_REVIEW",
    "QUANTUM_BLOCKED_SOURCE_EVIDENCE_REQUIRED",
    "QUANTUM_BLOCKED_RESULT_AUTHENTICITY_REQUIRED",
)

QUANTUM_ENCODING_READINESS_STATES = (
    "QUANTUM_ENCODING_BLUEPRINT_READY",
    "QUANTUM_BLOCKED_NO_ENCODING",
    "QUANTUM_BLOCKED_NO_QKU_LINEAGE",
)

QUANTUM_BACKEND_FIT_CLASSES = (
    "CLASSICAL_BASELINE_ONLY",
    "QUANTUM_INSPIRED_LOCAL_CANDIDATE",
    "QAOA_SIMULATOR_CANDIDATE_FUTURE",
    "QAOA_HARDWARE_CANDIDATE_FUTURE",
    "VQE_SIMULATOR_CANDIDATE_FUTURE",
    "ANNEALING_SIMULATOR_CANDIDATE_FUTURE",
    "ANNEALING_HARDWARE_CANDIDATE_FUTURE",
    "HYBRID_QUANTUM_CLASSICAL_JOB_CANDIDATE_FUTURE",
    "BACKEND_UNVERIFIED_SOURCE_REQUIRED",
    "BACKEND_BLOCKED_NO_DATA",
    "BACKEND_BLOCKED_NO_ENCODING",
    "BACKEND_BLOCKED_LATENCY_UNSAFE",
    "BACKEND_BLOCKED_COST_UNSAFE",
    "BACKEND_BLOCKED_OWNER_REVIEW_REQUIRED",
)

QUANTUM_LIVE_PATH_ADMISSIBILITY_STATES = (
    "PRECOMPUTED_ONLY",
    "ASYNC_CONTROL_PLANE_ONLY",
    "FORBIDDEN",
    "PRECOMPUTED_SNAPSHOT_ONLY",
    "RESEARCH_ONLY",
    "FORBIDDEN_UNTIL_FUTURE_OWNER_GATE",
)

COMPARATOR_STATUSES = (
    "COMPARATOR_BLUEPRINT_READY",
    "COMPARATOR_BLOCKED_NO_CLASSICAL_BASELINE",
    "COMPARATOR_BLOCKED_NO_QUANTUM_CANDIDATE",
    "COMPARATOR_BLOCKED_NO_SAFE_DATA",
    "COMPARATOR_BLOCKED_NO_VALIDATED_RESULT_PACKET",
    "COMPARATOR_BLOCKED_AUTHENTICITY_GATE_REQUIRED",
    "COMPARATOR_BLOCKED_OWNER_REVIEW_REQUIRED",
)

PARAMETER_CANDIDATE_AUTHORITY_CLASSES = (
    "OFFICIAL_DOC_CANDIDATE",
    "RESEARCH_CANDIDATE",
    "INSTITUTIONAL_CANDIDATE",
    "OWNER_CANDIDATE",
    "REPO_EXISTING_CANDIDATE",
    "HEURISTIC_CANDIDATE",
    "UNKNOWN_REQUIRED",
)

PROBLEM_FAMILIES = (
    "PORTFOLIO_SELECTION",
    "CAPITAL_ALLOCATION",
    "BINARY_POSITION_SELECTION",
    "ORDER_CANDIDATE_SELECTION",
    "PARAMETER_STACK_SELECTION",
    "SCENARIO_ARBITRATION",
    "MARKET_BUNDLE_SELECTION",
    "RISK_BUDGET_ALLOCATION",
    "LATENCY_COST_TRADEOFF_SELECTION",
    "CROSS_MARKET_HEDGE_CANDIDATE_SELECTION",
    "PREDICTION_MARKET_EVENT_BUNDLE_OPTIMIZATION",
    "QUBO_COMPATIBLE_FORMULATION",
    "ISING_COMPATIBLE_FORMULATION",
    "BQM_COMPATIBLE_FORMULATION",
    "CQM_COMPATIBLE_FORMULATION",
    "HYBRID_CLASSICAL_QUANTUM_FORMULATION",
    "QUANTUM_INSPIRED_FORMULATION",
)

FUTURE_ALLOWED_LIVE_MODE_QUANTUM_ROLES = (
    "PRECOMPUTED_STACK_SELECTOR",
    "PRECOMPUTED_PORTFOLIO_ALLOCATION_CANDIDATE",
    "PRECOMPUTED_RISK_BUDGET_CANDIDATE",
    "PRECOMPUTED_SCENARIO_ARBITRATION_SIGNAL",
    "PRECOMPUTED_POSITION_SIZING_CANDIDATE",
    "PRECOMPUTED_LATENCY_COST_TRADEOFF_SELECTOR",
    "PRECOMPUTED_MARKET_BUNDLE_SELECTOR",
    "ASYNC_RESEARCH_CONTROL_PLANE_CANDIDATE",
    "ASYNC_REPLAY_PAPER_RECALIBRATION_CANDIDATE",
    "ASYNC_OWNER_REVIEW_SIGNAL_CANDIDATE",
)
FORBIDDEN_LIVE_MODE_QUANTUM_ROLES = (
    "INLINE_ORDER_RELEASE",
    "HOT_PATH_BACKEND_CALL",
    "HOT_PATH_QPU_CALL",
    "HOT_PATH_SIMULATOR_CALL",
    "HOT_PATH_OPTIMIZER_SOLVE",
    "DIRECT_ORDER_SUBMISSION",
    "UNREVIEWED_POSITION_SIZING",
    "UNVALIDATED_PROFIT_SELECTOR",
    "LIVE_CONNECTOR_BINDING",
    "PRIVATE_STATE_FETCH",
)

BLOCKER_CODES = (
    "PR162_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",
    "PR162_BLOCKED_SYNTHETIC_ONLY",
    "PR162_BLOCKED_UNSAFE_PATH",
    "PR162_BLOCKED_UNMAPPABLE_QKU",
    "PR162_BLOCKED_NO_VALIDATED_REAL_NONLIVE_ARTIFACTS",
    "PR162_BLOCKED_PARTIAL_LANE_ONLY",
    "PR162_BLOCKED_QUANTUM_BLUEPRINT_ONLY",
    "PR162_BLOCKED_OWNER_REVIEW_REQUIRED",
    "PR162_BLOCKED_SOURCE_EVIDENCE_REQUIRED",
    "PR162_BLOCKED_RESULT_AUTHENTICITY_REQUIRED",
    "PR162_BLOCKED_LIVE_AUTHORITY_FORBIDDEN",
    "PR162_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "PR162_BLOCKED_PRIVATE_STATE_FORBIDDEN",
    "PR162_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "PR162_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN",
    "PR162_BLOCKED_FORBIDDEN_AUTHORITY_PATTERN",
    "PR162_BLOCKED_ABSOLUTE_PATH",
    "PR162_BLOCKED_SCHEMA_CONSUMER_NOT_FOUND",
    "PR162_BLOCKED_AUTHORITY_DRIFT",
    "PR162_STALE_PRECOMPUTED_SNAPSHOT_BLOCKER",
    *ARTIFACT_STATUS_ENUMS,
    *PR161E_HANDOFF_STATES,
    *QUANTUM_READINESS_STATES,
    *QUANTUM_BACKEND_FIT_CLASSES,
    *COMPARATOR_STATUSES,
)

UNAVAILABLE_REASON_CODES = (
    "NO_SAFE_REPO_LOCAL_RUN_CAPABLE_DATASET_DISCOVERED",
    "ONLY_SYNTHETIC_SMOKE_OR_SCHEMA_FIXTURES_DISCOVERED",
    "ONLINE_DISCOVERY_METADATA_ONLY_NOT_RUN_DATA",
    "REAL_NONLIVE_ARTIFACT_MATERIALIZATION_BLOCKED",
    "SOURCE_EVIDENCE_REQUIRED_BEFORE_FACT_ACCEPTANCE",
    "OWNER_REVIEW_REQUIRED_BEFORE_PROMOTION",
    "QUANTUM_BACKEND_UNVERIFIED_AND_NOT_EXECUTED",
    "LIVE_HOT_PATH_QUANTUM_CALL_FORBIDDEN",
)

DOWNSTREAM_PR_ROUTES = (
    "PR163_RESULT_PACKET_ROUTE_AFTER_VALIDATED_REAL_NONLIVE_ARTIFACTS",
    "PR164_RESULT_AUTHENTICITY_GATE_ROUTE",
    "PR165_RESULT_BACKED_RANKING_GATE_ROUTE",
    "PR168_RISK_CAPITAL_LATENCY_GATE_ROUTE",
    "PR171_RUNTIME_SCHEDULER_GATE_ROUTE",
    "PR177_LIVE_SAFE_PROMOTION_GATE_ROUTE",
    "PR180_CANARY_GATE_ROUTE",
)

UPSTREAM_PR_REFS = (
    "PR136",
    "PR137R",
    "PR138",
    "PR152",
    "PR154",
    "PR161C",
    "PR161D",
    "PR161E",
    "PR161F",
)

REQUIRED_INPUT_REPORTS = (
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json",
    "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json",
    "docs/master_plan/generated/PR161C_QKUCanonicalRegistry.report.json",
    "docs/master_plan/generated/PR161D_QKUReplayPaperScenarioInputs.report.json",
    "docs/master_plan/generated/PR161E_ReplayPaperOutcomeCaptureRegistry.report.json",
    "docs/master_plan/generated/PR161F_ExecutorInputRegistry.report.json",
    "docs/master_plan/generated/PR161F_ReplayRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PaperRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PairedReplayPaperRunPlan.report.json",
    "docs/master_plan/generated/PR161F_ResultPacketEmissionEligibilityGate.report.json",
    "docs/master_plan/generated/PR161F_QKUEndToEndTraceabilityMatrix.report.json",
    "docs/master_plan/generated/PR161F_QuantumClassicalHybridRunPlan.report.json",
    "docs/master_plan/generated/PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json",
    "tools/ci_branch_context.py",
    "tools/run_validation_gates.py",
    "tools/validate_grand_global_debug_logical_consistency_audit.py",
)

PR161F_REPORTS_REQUIRED = (
    "PR161F_ExecutorInputRegistry.report.json",
    "PR161F_ReplayRunRequestRegistry.report.json",
    "PR161F_PaperRunRequestRegistry.report.json",
    "PR161F_PairedReplayPaperRunPlan.report.json",
    "PR161F_RunArtifactEnvelopeRegistry.report.json",
    "PR161F_ResultPacketEmissionEligibilityGate.report.json",
    "PR161F_QKUEndToEndTraceabilityMatrix.report.json",
    "PR161F_QuantumClassicalHybridRunPlan.report.json",
    "PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json",
    "PR161F_QTTAgentWorkflowOrchestrationContract.report.json",
    "PR161F_QTTAgentRoleIOContract.report.json",
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

PARAMETER_CANDIDATE_NAMES = (
    "qaoa_reps_candidate",
    "qaoa_mixer_candidate",
    "qaoa_initial_point_candidate",
    "qaoa_optimizer_candidate",
    "qaoa_shot_budget_candidate",
    "qaoa_depth_budget_candidate",
    "vqe_ansatz_candidate",
    "vqe_optimizer_candidate",
    "vqe_shot_budget_candidate",
    "annealing_time_candidate",
    "annealing_schedule_candidate",
    "chain_strength_candidate",
    "num_reads_candidate",
    "qubo_penalty_lambda_candidate",
    "ising_coupling_scale_candidate",
    "bqm_variable_scale_candidate",
    "cqm_constraint_weight_candidate",
    "hybrid_solver_timeout_candidate",
    "classical_baseline_optimizer_candidate",
    "random_seed_policy_candidate",
    "reproducibility_policy_candidate",
    "latency_budget_candidate",
    "precompute_refresh_interval_candidate",
    "live_snapshot_ttl_candidate",
    "stale_snapshot_blocker_candidate",
)

SCHEMA_ENUM_FIELDS = {
    "authority_class": (AUTHORITY_CLASS,),
    "created_by_pr": (PR_ID,),
    "dataset_authority_class": DATASET_AUTHORITY_CLASSES,
    "source_class": SOURCE_CLASSES,
    "artifact_status": ARTIFACT_STATUS_ENUMS,
    "result_readiness_state": RESULT_READINESS_STATES,
    "pr161e_handoff_state": PR161E_HANDOFF_STATES,
    "qku_coverage_state": QKU_COVERAGE_STATES,
    "agent_handoff_status": QTT_AGENT_HANDOFF_STATUSES,
    "quantum_forward_promotion_state": QUANTUM_FORWARD_PROMOTION_STATES,
    "quantum_readiness_state": QUANTUM_READINESS_STATES,
    "encoding_readiness_state": QUANTUM_ENCODING_READINESS_STATES,
    "candidate_backend_family": QUANTUM_BACKEND_FIT_CLASSES,
    "live_hot_path_admissibility": QUANTUM_LIVE_PATH_ADMISSIBILITY_STATES,
    "comparator_blueprint_status": COMPARATOR_STATUSES,
    "candidate_authority_class": PARAMETER_CANDIDATE_AUTHORITY_CLASSES,
    "blocker_code": BLOCKER_CODES,
}

NO_SCATTERED_POLICY_ALLOWLIST = (
    "constants.py",
    "schema_writer.py",
)
