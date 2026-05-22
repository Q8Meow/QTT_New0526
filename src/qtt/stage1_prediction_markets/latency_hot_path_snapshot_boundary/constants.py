"""Central constants for the PR137L latency hot-path snapshot boundary."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR137L"
TITLE = "Latency hot-path snapshot boundary insertion"
BRANCH = "pr137l-latency-hot-path-snapshot-boundary"
BASE_HEAD_PREFIX = "ac3fb2c"
AUTHORITY_CLASS = (
    "CANONICAL_POST_PR137_LATENCY_HOT_PATH_SNAPSHOT_BOUNDARY_NOT_EXECUTION_AUTHORITY"
)
SCOPE_CLASS = "ROADMAP_MAPPING"
READINESS_STATE = "STATIC_CONTRACT_READY"
LATENCY_SCOPE = "PRECOMPUTED_SNAPSHOT_BOUNDARY"
REPORT_TYPE = "QTT_PR137L_LATENCY_HOT_PATH_SNAPSHOT_BOUNDARY_REPORT"
INDEX_TYPE = "QTT_PR137L_LATENCY_HOT_PATH_SNAPSHOT_BOUNDARY_INDEX"
STATIC_TIME = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"

REPORT_PATH = Path(
    "docs/master_plan/generated/PR137L_LatencyHotPathSnapshotBoundary.report.json"
)
INDEX_PATH = Path(
    "docs/master_plan/generated/PR137L_LatencyHotPathSnapshotBoundary.index.json"
)
PR137R_REPORT_PATH = Path(
    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"
)
GATE_TOOL_PATH = "tools/stage1_latency_hot_path_snapshot_boundary_gate.py"

REASON_OK = "PR137L_OK"
REASON_BASELINE_BRANCH_MISMATCH = "PR137L_BASELINE_BRANCH_MISMATCH"
REASON_BASELINE_HEAD_MISMATCH = "PR137L_BASELINE_HEAD_MISMATCH"
REASON_BASELINE_DIRTY_WORKTREE = "PR137L_BASELINE_DIRTY_WORKTREE"
REASON_PR136_SELECTOR_REQUIRED = "PR137L_PR136_SELECTOR_REQUIRED"
REASON_PR137_DEPENDENCY_CONTROLLER_REQUIRED = (
    "PR137L_PR137_DEPENDENCY_CONTROLLER_REQUIRED"
)
REASON_PR137R_REPORT_REQUIRED = "PR137L_PR137R_REPORT_REQUIRED"
REASON_PR137R_STATIC_EVIDENCE_REQUIRED = (
    "PR137L_PR137R_STATIC_EVIDENCE_REQUIRED"
)
REASON_PR137R_STATIC_EVIDENCE_CONTRADICTION = (
    "PR137L_PR137R_STATIC_EVIDENCE_CONTRADICTION"
)
REASON_CROSSWALK_CONTEXT_REQUIRED = "PR137L_CROSSWALK_CONTEXT_REQUIRED"
REASON_UPSTREAM_PR137_REQUIRED = "PR137L_UPSTREAM_PR137_REQUIRED"
REASON_DOWNSTREAM_PR138_REQUIRED = "PR137L_DOWNSTREAM_PR138_REQUIRED"
REASON_DUPLICATE_ENTRY_FORBIDDEN = "PR137L_DUPLICATE_ENTRY_FORBIDDEN"
REASON_DISCONNECTED_ROADMAP_FORBIDDEN = "PR137L_DISCONNECTED_ROADMAP_FORBIDDEN"
REASON_CONTROLLER_MUTATION_SKIPPED_EXISTING_SEQUENCE_VALIDATED = (
    "PR137L_CONTROLLER_MUTATION_SKIPPED_EXISTING_SEQUENCE_VALIDATED"
)
REASON_ACTIVE_SEQUENCE_MISSING = "PR137L_ACTIVE_SEQUENCE_MISSING"
REASON_STATIC_BOUNDARY_ONLY = "PR137L_STATIC_BOUNDARY_ONLY"
REASON_PR138_SCOPE_FORBIDDEN = "PR137L_PR138_SCOPE_FORBIDDEN"
REASON_RUNTIME_AUTHORITY_FORBIDDEN = "PR137L_RUNTIME_AUTHORITY_FORBIDDEN"
REASON_LIVE_AUTHORITY_FORBIDDEN = "PR137L_LIVE_AUTHORITY_FORBIDDEN"
REASON_SOURCE_RETRIEVAL_FORBIDDEN = "PR137L_SOURCE_RETRIEVAL_FORBIDDEN"
REASON_SOURCE_ACCEPTANCE_FORBIDDEN = "PR137L_SOURCE_ACCEPTANCE_FORBIDDEN"
REASON_CONNECTOR_BINDING_FORBIDDEN = "PR137L_CONNECTOR_BINDING_FORBIDDEN"
REASON_REPLAY_PAPER_EXECUTION_FORBIDDEN = (
    "PR137L_REPLAY_PAPER_EXECUTION_FORBIDDEN"
)
REASON_ORDER_AUTHORITY_FORBIDDEN = "PR137L_ORDER_AUTHORITY_FORBIDDEN"
REASON_PROFIT_EVIDENCE_FORBIDDEN = "PR137L_PROFIT_EVIDENCE_FORBIDDEN"
REASON_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN = (
    "PR137L_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN"
)
REASON_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN = (
    "PR137L_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN"
)
REASON_ALPHA_EVIDENCE_FORBIDDEN = "PR137L_ALPHA_EVIDENCE_FORBIDDEN"
REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN = (
    "PR137L_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN"
)
REASON_MARKET_ROADMAP_FORK_FORBIDDEN = "PR137L_MARKET_ROADMAP_FORK_FORBIDDEN"
REASON_FORECASTEX_ALIAS_FORBIDDEN = "PR137L_FORECASTEX_ALIAS_FORBIDDEN"
REASON_QUANTUM_EXECUTION_FORBIDDEN = "PR137L_QUANTUM_EXECUTION_FORBIDDEN"
REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN = (
    "PR137L_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN"
)
REASON_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN = (
    "PR137L_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN"
)
REASON_ATOMICROWS_MUTATION_FORBIDDEN = "PR137L_ATOMICROWS_MUTATION_FORBIDDEN"
REASON_ATOMICROWS_MATERIALIZATION_FORBIDDEN = (
    "PR137L_ATOMICROWS_MATERIALIZATION_FORBIDDEN"
)
REASON_ATOMICROWS_FINAL_READINESS_CLAIM_FORBIDDEN = (
    "PR137L_ATOMICROWS_FINAL_READINESS_CLAIM_FORBIDDEN"
)
REASON_ATOMICROWS_DAY1_LIVE_READY_CLAIM_FORBIDDEN = (
    "PR137L_ATOMICROWS_DAY1_LIVE_READY_CLAIM_FORBIDDEN"
)
REASON_ATOMICROWS_BUNDLE_AS_ORDER_AUTHORITY_FORBIDDEN = (
    "PR137L_ATOMICROWS_BUNDLE_AS_ORDER_AUTHORITY_FORBIDDEN"
)
REASON_ATOMICROWS_BUNDLE_AS_PROFIT_EVIDENCE_FORBIDDEN = (
    "PR137L_ATOMICROWS_BUNDLE_AS_PROFIT_EVIDENCE_FORBIDDEN"
)
REASON_LIVE_PATH_CONTROL_PLANE_DEPENDENCY_FORBIDDEN = (
    "PR137L_LIVE_PATH_CONTROL_PLANE_DEPENDENCY_FORBIDDEN"
)
REASON_IDEMPOTENCY_FAILURE = "PR137L_IDEMPOTENCY_FAILURE"
REASON_ALLOWLIST_EXPANSION_REQUIRED = "PR137L_ALLOWLIST_EXPANSION_REQUIRED"
RECEIPT_CI_DETACHED_HEAD_MODE = "CI_DETACHED_HEAD_MODE_ACTIVE"
RECEIPT_CI_SHALLOW_FETCH_ANCESTRY_SKIPPED = (
    "CI_SHALLOW_FETCH_ANCESTRY_CHECK_SKIPPED"
)
RECEIPT_CI_MERGE_REF_BASELINE_ACCEPTED = "PR137L_CI_MERGE_REF_BASELINE_ACCEPTED"
RECEIPT_LOCAL_BRANCH_DESCENDANT_BASELINE_ACCEPTED = (
    "PR137L_LOCAL_BRANCH_DESCENDANT_BASELINE_ACCEPTED"
)

SUCCESS_RECEIPTS = (
    "QTT_PR137L_LATENCY_HOT_PATH_SNAPSHOT_BOUNDARY_OK",
    "QTT_PR137L_DEPENDENCY_CHAIN_OK",
    "QTT_PR137L_PR137R_STATIC_EVIDENCE_CONSUMED_OK",
    "QTT_PR137L_ATOMICROWS_READ_ONLY_SNAPSHOT_BOUNDARY_OK",
    "QTT_PR137L_NO_PR138_SCOPE_DRIFT_OK",
    "QTT_PR137L_ONE_GLOBAL_ROADMAP_MARKET_OVERLAYS_OK",
    "QTT_PR137L_LIVE_PRETRADE_PRECOMPUTED_SNAPSHOT_ONLY_OK",
    "QTT_PR137L_NO_RUNTIME_LIVE_SOURCE_CONNECTOR_ORDER_PROFIT_AUTHORITY_OK",
    "QTT_PR137L_NO_QTT_SHA_DIGEST_AUTHORITY_OK",
    "QTT_PR137L_QUANTUM_ATOMICROWS_FUTURE_REF_ONLY_OK",
    "QTT_PR137L_IDEMPOTENT_REPORT_OK",
)

CANONICAL_MARKET_SCOPES = (
    "PREDICTION_MARKETS_GENERAL",
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
)
FORBIDDEN_THIRD_VENUE_ALIASES = (
    "FORECASTEX",
    "FORECASTX",
    "IBKR_FORECASTX",
    "forecastx",
)

GLOBAL_ROADMAP_MODEL = "ONE_GLOBAL_ROADMAP_WITH_MARKET_SCOPED_OVERLAYS"

PRECOMPUTED_SNAPSHOT_BOUNDARY_TYPES = (
    "SOURCE_CHANGE_PRECOMPUTED_SNAPSHOT_BOUNDARY",
    "CASH_COMPONENT_PRECOMPUTED_SNAPSHOT_BOUNDARY",
    "RUNTIME_RESOLVER_PRECOMPUTED_SNAPSHOT_BOUNDARY",
    "RISK_STATE_PRECOMPUTED_SNAPSHOT_BOUNDARY",
    "KILL_SWITCH_PRECOMPUTED_SNAPSHOT_BOUNDARY",
    "OWNER_AUTHORIZATION_PRECOMPUTED_SNAPSHOT_BOUNDARY",
    "VENUE_HEALTH_PRECOMPUTED_SNAPSHOT_BOUNDARY",
    "ATOMICROWS_PR137R_STATIC_EVIDENCE_SNAPSHOT_BOUNDARY",
    "QUANTUM_CLASSICAL_COMPARATOR_FUTURE_REF_BOUNDARY",
    "ATOMICROWS_BRIDGE_FUTURE_REF_BOUNDARY",
)

CONTROL_PLANE_PRODUCER_LANES = (
    "SOURCE_CHANGE_CONTROL_PLANE_PRODUCER",
    "CASH_COMPONENT_CONTROL_PLANE_PRODUCER",
    "RUNTIME_RESOLVER_CONTROL_PLANE_PRODUCER",
    "RISK_STATE_CONTROL_PLANE_PRODUCER",
    "KILL_SWITCH_CONTROL_PLANE_PRODUCER",
    "OWNER_AUTHORIZATION_CONTROL_PLANE_PRODUCER",
    "VENUE_HEALTH_CONTROL_PLANE_PRODUCER",
    "ATOMICROWS_PR137R_RECONCILIATION_EVIDENCE_PRODUCER",
    "QUANTUM_CLASSICAL_COMPARATOR_CONTROL_PLANE_PRODUCER",
    "ATOMICROWS_BRIDGE_CONTROL_PLANE_PRODUCER",
)

FUTURE_LIVE_CONSUMER_LANES = ("FUTURE_LIVE_PRETRADE_SNAPSHOT_CONSUMER",)

LIVE_PATH_REQUIRED_TRUE_CONSTRAINTS = (
    "future_live_pretrade_consumes_precomputed_snapshots_only",
    "future_live_pretrade_may_not_call_control_plane_producers",
    "future_live_pretrade_may_not_perform_network_io",
    "future_live_pretrade_may_not_fetch_filesystem_documents",
    "future_live_pretrade_may_not_perform_unbounded_search",
    "future_live_pretrade_may_not_call_llm",
    "future_live_pretrade_may_not_call_dashboard",
    "future_live_pretrade_may_not_execute_replay",
    "future_live_pretrade_may_not_execute_paper",
    "future_live_pretrade_may_not_call_quantum_backend",
    "future_live_pretrade_may_not_call_quantum_simulator",
    "future_live_pretrade_may_not_create_runtime_resolver_snapshot",
    "future_live_pretrade_may_not_create_cash_component_map",
    "future_live_pretrade_may_not_create_source_acceptance",
    "future_live_pretrade_may_not_bind_connector_semantics",
    "future_live_pretrade_may_not_mutate_atomicrows",
    "future_live_pretrade_may_not_generate_atomicrows_bundle",
    "future_live_pretrade_may_not_use_atomicrows_as_final_readiness_authority",
)

LIVE_PATH_REQUIRED_FALSE_FIELDS = (
    "network_io_allowed",
    "file_system_doc_fetch_allowed",
    "unbounded_search_allowed",
    "control_plane_calls_allowed_in_live_path",
    "source_retrieval_allowed_in_live_path",
    "source_acceptance_allowed_in_live_path",
    "source_revalidation_allowed_in_live_path",
    "connector_binding_allowed_in_live_path",
    "runtime_resolver_snapshot_creation_allowed_in_live_path",
    "private_state_fetch_allowed_in_live_path",
    "cash_component_map_construction_allowed_in_live_path",
    "dashboard_rendering_allowed_in_live_path",
    "llm_call_allowed_in_live_path",
    "replay_execution_allowed_in_live_path",
    "paper_execution_allowed_in_live_path",
    "quantum_backend_calls_allowed_in_live_path",
    "quantum_simulator_calls_allowed_in_live_path",
    "atomicrows_materialization_allowed_in_live_path",
    "atomicrows_final_readiness_authority_allowed_in_live_path",
)

LATENCY_DISCIPLINE_TRUE_FIELDS = (
    "live_pretrade_snapshot_boundary_allows_in_memory_snapshot_cache",
    "live_pretrade_snapshot_boundary_allows_static_fixture_validation",
)
LATENCY_DISCIPLINE_FALSE_FIELDS = (
    "live_pretrade_snapshot_boundary_may_not_perform_network_io",
    "live_pretrade_snapshot_boundary_may_not_perform_file_system_doc_fetch",
    "live_pretrade_snapshot_boundary_may_not_perform_unbounded_search",
)
LATENCY_COMPLEXITY_TARGET = "O_1_OR_BOUNDED_LOOKUP_BY_SCOPE"

QUANTUM_ALLOWED_TRUE_FIELDS = (
    "allowed",
    "quantum_future_ref_metadata_allowed",
    "quantum_classical_comparator_planning_metadata_allowed",
    "qubo_compatibility_metadata_allowed",
    "ising_compatibility_metadata_allowed",
    "qaoa_compatibility_metadata_allowed",
    "vqe_compatible_research_metadata_allowed",
    "quantum_annealing_compatibility_metadata_allowed",
    "quantum_kernel_feature_map_metadata_allowed",
    "quantum_optimizer_candidate_lane_reference_allowed",
)
QUANTUM_REQUIRED_FALSE_FIELDS = (
    "execution_allowed",
    "backend_call_allowed",
    "simulator_execution_allowed",
    "optimizer_input_allowed",
    "trading_signal_allowed",
    "advantage_claim_allowed",
    "numeric_parameter_values_created",
    "quantum_parameter_values_created",
    "quantum_backend_call_allowed",
    "quantum_simulator_execution_allowed",
    "qaoa_execution_allowed",
    "vqe_execution_allowed",
    "annealing_execution_allowed",
    "qubo_solving_allowed",
    "ising_solving_allowed",
    "quantum_optimizer_input_packet_allowed",
    "quantum_trading_signal_allowed",
    "quantum_advantage_claim_allowed",
    "quantum_latency_superiority_claim_allowed",
    "quantum_profit_claim_allowed",
)

ATOMICROWS_ALLOWED_TRUE_FIELDS = (
    "allowed",
    "pr137r_static_evidence_snapshot_allowed",
    "bridge_compatibility_metadata_allowed",
    "parameter_inventory_reference_metadata_allowed",
    "selector_compatibility_metadata_allowed",
    "atomicrows_pr137r_static_evidence_snapshot_allowed",
    "atomicrows_bridge_future_ref_metadata_allowed",
    "atomicrows_parameter_inventory_reference_metadata_allowed",
    "atomicrows_selector_compatibility_metadata_allowed",
)
ATOMICROWS_REQUIRED_FALSE_FIELDS = (
    "rows_created",
    "bundle_created",
    "bundle_edited",
    "row_family_sources_edited",
    "runtime_materialization_allowed",
    "atomicrows_runtime_materialization_allowed",
    "materialization_authority_created",
    "final_readiness_authority_created",
    "qtt_sha_integrity_authority_created",
)

NOT_CREATED_FLAGS = (
    "execution_authority_created",
    "runtime_execution_created",
    "live_trading_authority_created",
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_evidence_packet_created",
    "connector_semantic_binding_created",
    "credential_resolution_created",
    "private_state_fetch_created",
    "runtime_cash_authority_created",
    "runtime_cash_receipts_created",
    "runtime_resolver_execution_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "replay_result_created",
    "paper_result_created",
    "replay_paper_result_created",
    "ranking_scoring_arbitration_output_created",
    "trading_signal_created",
    "order_intent_authority_created",
    "order_authority_created",
    "order_execution_created",
    "order_routing_created",
    "fill_receipt_created",
    "profit_evidence_created",
    "profit_claim_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "alpha_evidence_created",
    "day1_live_launch_authority_created",
    "quantum_execution_created",
    "quantum_backend_call_created",
    "quantum_simulator_execution_created",
    "quantum_optimizer_input_created",
    "quantum_trading_signal_created",
    "quantum_advantage_claim_created",
    "atomicrows_rows_created",
    "atomicrows_bundle_created",
    "atomicrows_bundle_edited",
    "atomicrows_row_family_sources_created",
    "atomicrows_row_family_sources_edited",
    "atomicrows_materialization_authority_created",
    "atomicrows_final_readiness_authority_created",
    "atomicrows_qtt_sha_integrity_authority_created",
    "qtt_sha_authority_created",
    "qtt_generated_sha_digest_fields_created",
)

PR136_SELECTOR_ARTIFACTS = (
    "docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json",
    "docs/master_plan/generated/PR136FuturePRCardRegistry.report.json",
    "docs/master_plan/generated/PR136LaunchReadinessDependencyGraph.report.json",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "src/qtt/stage1_prediction_markets/launch_readiness/day1_launch_readiness_roadmap.py",
    "tools/validate_pr136_day1_launch_readiness_roadmap.py",
)
PR137_DEPENDENCY_CONTROLLER_ARTIFACTS = (
    "docs/master_plan/generated/PR137LaunchReadinessDependencyController.report.json",
    "docs/master_plan/generated/PR137DependencyGateStateMatrix.report.json",
    "docs/master_plan/generated/PR137ValidationGateIntegration.report.json",
    "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_controller.py",
    "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_policy.py",
    "tools/validate_pr137_launch_readiness_dependency_controller.py",
)
CROSSWALK_CONTEXT_ARTIFACTS = (
    "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR135MarketSpecificSectionIndex.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/SectionManifest.json",
    "docs/master_plan/generated/MasterPlanSectionCoverageReport.json",
)
ROUTE_TRIAGE_ARTIFACTS = (
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/roadmap/generated/CODEX_PR136_ROUTE_TRIAGE_RECEIPT.json",
    "docs/roadmap/generated/CODEX_PR137_ROUTE_TRIAGE_RECEIPT.json",
)
VALIDATION_GATE_CONTEXT_ARTIFACTS = (
    "tools/validate_pr136_day1_launch_readiness_roadmap.py",
    "tools/validate_pr137_launch_readiness_dependency_controller.py",
    "tools/validate_pr137_generated_integrity_authority_boundary.py",
    "tools/stage1_atomicrows_bundle_reconciliation_gate.py",
    "tools/run_validation_gates.py",
)

PROTECTED_UNTOUCHED_PATHS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
    "docs/master_plan/atomic_rows/pr98_row_family_sources",
    "docs/master_plan/atomic_rows/exact_row_sources",
    "tools/build_atomicrows_bundle.py",
    "tools/materialize_atomicrows_bundle_from_exact_rows.py",
)

PR137L_CREATED_PATHS = (
    "src/qtt/stage1_prediction_markets/latency_hot_path_snapshot_boundary/__init__.py",
    "src/qtt/stage1_prediction_markets/latency_hot_path_snapshot_boundary/constants.py",
    "src/qtt/stage1_prediction_markets/latency_hot_path_snapshot_boundary/model.py",
    "src/qtt/stage1_prediction_markets/latency_hot_path_snapshot_boundary/report.py",
    "src/qtt/stage1_prediction_markets/latency_hot_path_snapshot_boundary/validator.py",
    GATE_TOOL_PATH,
    "tests/stage1_prediction_markets/latency_hot_path_snapshot_boundary/test_pr137l_latency_hot_path_snapshot_boundary.py",
    REPORT_PATH.as_posix(),
    INDEX_PATH.as_posix(),
)

FORBIDDEN_GENERATED_INTEGRITY_KEY = "sha" + "256"

