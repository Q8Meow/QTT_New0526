"""Central constants for the PR150 parameter target matrix."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR150"
BRANCH = "pr150-source-backed-classical-quantum-parameter-default-target-matrix"
PR_TITLE = "Source-Backed Classical and Quantum Parameter Default Target Matrix"
REPORT_ID = "QTT_PR150_SOURCE_BACKED_CLASSICAL_QUANTUM_PARAMETER_DEFAULT_TARGET_MATRIX_REPORT"
REPORT_VERSION = "v1"
AUTHORITY_CLASS = (
    "SOURCE_BACKED_CLASSICAL_QUANTUM_PARAMETER_DEFAULT_TARGET_MATRIX_ONLY_"
    "NOT_VALUE_ACCEPTANCE_NOT_RUNTIME_AUTHORITY"
)
READINESS_CLASS = "PARAMETER_TARGET_MATRIX_READY_ONLY_NOT_ORDER_READY"
REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "PR150_SourceBackedClassicalQuantumParameterDefaultTargetMatrix.report.json"
)
SUCCESS_MARKER = "QTT_SOURCE_BACKED_CLASSICAL_QUANTUM_PARAMETER_DEFAULT_TARGET_MATRIX_OK"
STATIC_TIME = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
QUANTUM_FORWARD_STATE = (
    "OWNER_APPROVED_QUANTUM_PLANNING_RELEASED_EXECUTION_EVIDENCE_PENDING"
)

ROSTER_PATH = Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json")
CONTROLLER_PATH = Path("docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json")
ROADMAP_PATH = Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md")
ROADMAP_POLICY_PATH = Path(
    "src/qtt/stage1_prediction_markets/launch_readiness/"
    "day1_launch_readiness_roadmap_policy.py"
)
PR136_ROUTE_TRIAGE_PATH = Path("docs/master_plan/generated/PR136RouteTriage.report.json")
PR136_SECTION_CROSSWALK_ALIAS_PATH = Path(
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"
)
PR136_SECTION_CROSSWALK_CANONICAL_PATH = Path(
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"
)
PR136_MARKET_INDEX_PATH = Path(
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"
)
PR136_COMMAND_MATRIX_PATH = Path(
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json"
)
PR137R_REPORT_PATH = Path(
    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"
)
PR138_REPORT_PATH = Path(
    "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"
)
PR149_REPORT_PATH = Path(
    "docs/master_plan/generated/PR149_AtomicRowsSemanticValueMaterializationImplementationBridge.report.json"
)
PR149_MODULE_DIR_PATH = Path(
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_implementation_bridge"
)
SOURCE_EVIDENCE_PACKET_PATH = Path(
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
)

PARAMETER_ALGORITHM_SCORING_REPORT_PATH = Path(
    "docs/master_plan/generated/ParameterAlgorithmScoringPolicyRegistry.report.json"
)
PARAMETER_STACK_SCORING_REPORT_PATH = Path(
    "docs/master_plan/generated/ParameterStackScoringAndRankingGate.report.json"
)
QUANTUM_CLASSICAL_ARBITRATION_REPORT_PATH = Path(
    "docs/master_plan/generated/QuantumClassicalOptimizerArbitrationGate.report.json"
)
CANDIDATE_STACK_GENERATION_REPORT_PATH = Path(
    "docs/master_plan/generated/CandidateParameterStackGenerationGate.report.json"
)
TRADE_CONTEXT_SELECTION_REPORT_PATH = Path(
    "docs/master_plan/generated/TradeContextParameterStackSelectionGate.report.json"
)
SELECTED_STACK_HANDOFF_REPORT_PATH = Path(
    "docs/master_plan/generated/SelectedParameterStackHandoffPacket.report.json"
)
ATOMICROWS_BUNDLE_MATERIALIZATION_REPORT_PATH = Path(
    "docs/master_plan/generated/AtomicRowsBundleMaterialization.report.json"
)
ATOMICROWS_BUNDLE_BOUNDARY_REPORT_PATH = Path(
    "docs/master_plan/generated/AtomicRowsBundleBoundaryStateContract.report.json"
)

MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")
ATOMICROWS_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")

REQUIRED_UPSTREAM_ARTIFACTS = (
    ROSTER_PATH,
    CONTROLLER_PATH,
    ROADMAP_PATH,
    ROADMAP_POLICY_PATH,
    PR136_ROUTE_TRIAGE_PATH,
    PR136_SECTION_CROSSWALK_CANONICAL_PATH,
    PR136_MARKET_INDEX_PATH,
    PR136_COMMAND_MATRIX_PATH,
    PR137R_REPORT_PATH,
    PR138_REPORT_PATH,
    PR149_REPORT_PATH,
)
OPTIONAL_CONTEXT_ARTIFACTS = (
    SOURCE_EVIDENCE_PACKET_PATH,
    PR149_MODULE_DIR_PATH,
    PARAMETER_ALGORITHM_SCORING_REPORT_PATH,
    PARAMETER_STACK_SCORING_REPORT_PATH,
    QUANTUM_CLASSICAL_ARBITRATION_REPORT_PATH,
    CANDIDATE_STACK_GENERATION_REPORT_PATH,
    TRADE_CONTEXT_SELECTION_REPORT_PATH,
    SELECTED_STACK_HANDOFF_REPORT_PATH,
    ATOMICROWS_BUNDLE_MATERIALIZATION_REPORT_PATH,
    ATOMICROWS_BUNDLE_BOUNDARY_REPORT_PATH,
    Path("tools/validate_atomicrows_semantic_value_materialization_implementation_bridge.py"),
    Path("tools/validate_parameter_algorithm_scoring_policy_registry.py"),
    Path("tools/validate_parameter_stack_scoring_and_ranking_gate.py"),
    Path("tools/validate_quantum_classical_optimizer_arbitration_gate.py"),
    Path("tools/validate_candidate_parameter_stack_generation_gate.py"),
    Path("tools/validate_trade_context_parameter_stack_selection_gate.py"),
    Path("tools/validate_selected_parameter_stack_handoff_packet.py"),
    Path("tools/validate_atomicrows_bundle_materialization_manifest.py"),
    Path("tools/validate_atomicrows_bundle_boundary_state_contract.py"),
    Path("tools/validate_source_evidence_acceptance.py"),
    Path("tools/validate_accepted_source_to_connector_semantic_binding.py"),
    Path("tools/runtime_cash_component_field_map_validate.py"),
    Path("tools/private_state_read_receipt_gate_validate.py"),
)

PARAMETER_DOMAIN_VALUES = (
    "EDGE_SIGNAL_FAMILY_TARGETS",
    "MARKET_MAKING_TARGETS",
    "ARBITRAGE_MISPRICING_TARGETS",
    "MOMENTUM_FLOW_TARGETS",
    "LIQUIDITY_VOLUME_OPEN_INTEREST_TARGETS",
    "EVENT_MATURITY_TIME_TO_RESOLUTION_TARGETS",
    "FORECAST_PROBABILITY_CALIBRATION_TARGETS",
    "CATEGORY_MARKET_TYPE_TARGETS",
    "YES_NO_ASYMMETRY_TARGETS",
    "LONGSHOT_FAVORITE_BIAS_TARGETS",
    "NEWS_RESEARCH_SIGNAL_TARGETS",
    "MODEL_FREE_BASELINE_COMPARATOR_TARGETS",
    "AGENT_BINDING_SCORE_INPUTS",
    "LIFECYCLE_READINESS_SCORE_INPUTS",
    "PLATFORM_APPLICABILITY_SCORE_INPUTS",
    "STRATEGY_FIT_SCORE_INPUTS",
    "LATENCY_FIT_SCORE_INPUTS",
    "RISK_FIT_SCORE_INPUTS",
    "EXPECTED_NET_VALUE_SCORE_TARGETS",
    "EXPECTED_NET_COST_SCORE_TARGETS",
    "SOURCE_EVIDENCE_COMPLETENESS_INPUTS",
    "REPLAY_PAPER_CALIBRATION_INPUTS",
    "OPTIMIZER_SCORE_INPUTS",
    "QUANTUM_APPLICABILITY_SCORE_INPUTS",
    "FINAL_STACK_SCORE_INPUTS",
    "TIE_BREAKER_POLICY_INPUTS",
    "CANDIDATE_COUNT_TARGETS",
    "POSITION_SIZING_TARGETS",
    "PORTFOLIO_EXPOSURE_TARGETS",
    "PER_MARKET_EXPOSURE_TARGETS",
    "PER_VENUE_EXPOSURE_TARGETS",
    "PER_AGENT_EXPOSURE_TARGETS",
    "MAX_ORDER_NOTIONAL_TARGETS",
    "CAPITAL_RESERVE_TARGETS",
    "DRAWDOWN_GUARD_TARGETS",
    "STOP_QUARANTINE_KILL_SWITCH_THRESHOLD_TARGETS",
    "LIQUIDITY_GUARD_TARGETS",
    "SLIPPAGE_GUARD_TARGETS",
    "NEW_INCREASED_EXPOSURE_BLOCK_TARGETS",
    "RUNTIME_AVAILABLE_CASH_RECEIPT_TARGETS",
    "ORDER_INTENT_PARAMETER_TARGETS",
    "ORDER_TYPE_TARGET_FIELDS",
    "LIMIT_PRICE_TARGET_FIELDS",
    "TICK_SIZE_TARGET_FIELDS",
    "MINIMUM_ORDER_SIZE_TARGET_FIELDS",
    "FEE_SETTLEMENT_COST_TARGET_FIELDS",
    "RATE_LIMIT_TARGET_FIELDS",
    "ORDERBOOK_SNAPSHOT_FRESHNESS_TARGETS",
    "WEBSOCKET_ORDERBOOK_EVENT_SEQUENCING_TARGETS",
    "RETRY_BACKOFF_ERROR_ROUTING_TARGETS",
    "LATENCY_BUDGET_TARGET_SLOTS",
    "PRECOMPUTED_HOT_PATH_SNAPSHOT_TARGETS",
    "LIVE_PRETRADE_EXCLUSION_TARGETS",
    "VENUE_API_SEMANTICS",
    "VENUE_ORDER_FIELDS",
    "VENUE_FEE_RULES",
    "VENUE_TICK_RULES",
    "VENUE_PAYOUT_RULES",
    "VENUE_SETTLEMENT_RULES",
    "VENUE_SDK_BEHAVIOR",
    "VENUE_RATE_LIMITS",
    "VENUE_MARKET_DATA_SEMANTICS",
    "VENUE_ACCOUNT_PRIVATE_STATE_SEMANTICS",
    "VENUE_EXECUTION_LIFECYCLE",
    "VENUE_FILL_INTEGRITY",
    "VENUE_CASHFLOW_PNL_SEMANTICS",
    "VENUE_LATENCY_COMPONENT_SEMANTICS",
    "VENUE_RECONCILIATION_SEMANTICS",
    "VENUE_CROSS_VENUE_NORMALIZATION_DEPENDENCIES",
    "CLASSICAL_OPTIMIZER_CANDIDATE_METADATA",
    "GRID_SEARCH_METADATA_SLOTS",
    "RANDOM_SEARCH_METADATA_SLOTS",
    "BAYESIAN_OPTIMIZER_METADATA_SLOTS",
    "EVOLUTIONARY_OPTIMIZER_METADATA_SLOTS",
    "INTEGER_LINEAR_QUADRATIC_PROGRAM_METADATA_SLOTS",
    "SCORING_WEIGHT_OPTIMIZATION_TARGETS",
    "HYPERPARAMETER_SEARCH_SPACE_TARGETS",
    "CONSTRAINT_PENALTY_WEIGHT_TARGET_SLOTS",
    "STRONGEST_CLASSICAL_COMPARATOR_TARGETS",
    "OPTIMIZER_OUTPUT_RECEIPT_REQUIREMENTS",
    "OPTIMIZER_PROMOTION_GATE_REQUIREMENTS",
    "QUANTUM_APPLICABILITY_METADATA",
    "QUBO_ENCODING_TARGET_SLOTS",
    "ISING_MAPPING_TARGET_SLOTS",
    "QAOA_DEPTH_CLASS_TARGET_SLOTS",
    "QAOA_MIXER_ANSATZ_METADATA_SLOTS",
    "QAOA_CLASSICAL_OPTIMIZER_METADATA_SLOTS",
    "VQE_ANSATZ_CLASS_METADATA_SLOTS",
    "VQE_EXPECTATION_TOLERANCE_TARGET_SLOTS",
    "ANNEALING_SCHEDULE_METADATA_SLOTS",
    "ANNEALING_CHAIN_EMBEDDING_TARGET_SLOTS",
    "QUANTUM_PORTFOLIO_SELECTION_METADATA_SLOTS",
    "QUANTUM_SEARCH_SPACE_METADATA_SLOTS",
    "SHOT_COUNT_TARGET_SLOTS",
    "BACKEND_PROVIDER_TARGET_SLOTS",
    "SIMULATOR_TARGET_SLOTS",
    "QUANTUM_RESULT_RECEIPT_REQUIREMENTS",
    "QUANTUM_STRONGEST_CLASSICAL_COMPARATOR_REQUIREMENTS",
    "QUANTUM_HOT_PATH_EXCLUSION_TARGETS",
    "ATOMICROWS_ROW_FAMILY_REFERENCES",
    "ATOMICROWS_SEMANTIC_FIELD_REFERENCES",
    "ATOMICROWS_PR149_MATERIALIZATION_TARGET_REFERENCES",
    "ATOMICROWS_CANDIDATE_INVENTORY_LINKS",
    "ATOMICROWS_FUTURE_SOURCE_MATERIALIZATION_DEPENDENCIES",
    "ATOMICROWS_FUTURE_AGENT_FAMILY_ELIGIBILITY_DEPENDENCIES",
    "ATOMICROWS_NO_BUNDLE_MUTATION_STATE",
    "REPLAY_METRIC_TARGET_SLOTS",
    "PAPER_METRIC_TARGET_SLOTS",
    "REPLAY_PAPER_LANE_SEPARATION_TARGETS",
    "DUAL_RESULT_REVIEW_INPUT_TARGETS",
    "CALIBRATION_CONFIDENCE_TARGET_SLOTS",
    "PROMOTION_GATE_INPUT_TARGET_SLOTS",
    "NO_REPLAY_PAPER_RESULT_FABRICATION",
    "NO_AUTOMATIC_LIVE_PROMOTION",
)

TARGET_FAMILY_VALUES = (
    "CLASSICAL_STRATEGY_PARAMETER",
    "SCORING_FORMULA_INPUT",
    "RISK_CAPITAL_CONTROL",
    "EXECUTION_LATENCY",
    "VENUE_SOURCE_REQUIRED",
    "OPTIMIZER_PARAMETER",
    "QUANTUM_PARAMETER",
    "ATOMICROWS_COMPATIBILITY",
    "REPLAY_PAPER_CALIBRATION",
    "MARKET_SPECIFIC_PARAMETER",
)

VALUE_AUTHORITY_CLASS_VALUES = (
    "OWNER_POLICY_VALUE",
    "INTERNAL_QTT_ARCHITECTURE_VALUE",
    "ACCEPTED_SOURCE_EVIDENCE_VALUE",
    "SOURCE_EVIDENCE_REQUIRED_VALUE",
    "RUNTIME_RECEIPT_REQUIRED_VALUE",
    "REPLAY_PAPER_CALIBRATION_REQUIRED_VALUE",
    "QUANTUM_METADATA_ONLY_VALUE",
    "QUANTUM_EXECUTION_EVIDENCE_REQUIRED_VALUE",
    "UNRESOLVED_PENDING_UPSTREAM_VALUE",
)

DEFAULT_TARGET_STATE_VALUES = (
    "TARGET_DEFINED_VALUE_FILLED_BY_OWNER_POLICY",
    "TARGET_DEFINED_VALUE_FILLED_BY_INTERNAL_ARCHITECTURE",
    "TARGET_DEFINED_VALUE_FILLED_BY_ACCEPTED_SOURCE_EVIDENCE",
    "TARGET_DEFINED_VALUE_PENDING_SOURCE_EVIDENCE",
    "TARGET_DEFINED_VALUE_PENDING_RUNTIME_RECEIPT",
    "TARGET_DEFINED_VALUE_PENDING_REPLAY_PAPER_CALIBRATION",
    "TARGET_DEFINED_VALUE_QUANTUM_METADATA_ONLY",
    "TARGET_DEFINED_VALUE_PENDING_QUANTUM_EXECUTION_EVIDENCE",
    "TARGET_DEFINED_VALUE_UNRESOLVED_PENDING_UPSTREAM",
    "TARGET_BLOCKED_NO_SOURCE_AUTHORITY",
    "TARGET_BLOCKED_NO_RUNTIME_AUTHORITY",
    "TARGET_BLOCKED_NO_REPLAY_PAPER_AUTHORITY",
    "TARGET_BLOCKED_NO_LIVE_AUTHORITY",
    "TARGET_BLOCKED_NO_ORDER_AUTHORITY",
    "TARGET_BLOCKED_NO_BUNDLE_AUTHORITY",
)

EVIDENCE_REQUIREMENT_CLASS_VALUES = (
    "OWNER_POLICY_RECORD_REQUIRED",
    "INTERNAL_ARCHITECTURE_RECORD_REQUIRED",
    "ACCEPTED_SOURCE_EVIDENCE_REQUIRED",
    "OFFICIAL_SOURCE_EVIDENCE_REQUIRED",
    "RUNTIME_RECEIPT_REQUIRED",
    "REPLAY_PAPER_CALIBRATION_REQUIRED",
    "QUANTUM_METADATA_ONLY",
    "QUANTUM_EXECUTION_EVIDENCE_REQUIRED",
    "UPSTREAM_VALUE_REQUIRED",
)

ORDER_USE_ELIGIBILITY_VALUES = (
    "NOT_ORDER_USABLE_TARGET_ONLY",
    "CONFIGURATION_METADATA_ONLY",
    "REPLAY_PAPER_CANDIDATE_ONLY",
    "PENDING_SOURCE_EVIDENCE",
    "PENDING_RUNTIME_RECEIPT",
    "PENDING_OWNER_POLICY_DECISION",
    "PENDING_QUANTUM_EXECUTION_EVIDENCE",
    "ORDER_USE_REQUIRES_FUTURE_PR",
)

DOWNSTREAM_CONSUMER_CLASS_VALUES = (
    "PARAMETER_STACK_SELECTION_METADATA_CONSUMER",
    "SCORING_RANKING_METADATA_CONSUMER",
    "RISK_CAPITAL_CONTROL_METADATA_CONSUMER",
    "EXECUTION_PLANNING_METADATA_CONSUMER",
    "VENUE_SOURCE_EVIDENCE_TARGETING_CONSUMER",
    "OPTIMIZER_PLANNING_METADATA_CONSUMER",
    "QUANTUM_PLANNING_METADATA_CONSUMER",
    "ATOMICROWS_COMPATIBILITY_METADATA_CONSUMER",
    "REPLAY_PAPER_CALIBRATION_METADATA_CONSUMER",
    "OWNER_DASHBOARD_READ_ONLY_METADATA_CONSUMER",
)

NO_CLAIM_FLAGS = {
    "external_fact_value_created": False,
    "source_fact_acceptance_created": False,
    "connector_semantic_binding_created": False,
    "runtime_cash_receipt_created": False,
    "order_execution_created": False,
    "live_reachability_created": False,
    "replay_execution_created": False,
    "paper_execution_created": False,
    "replay_paper_result_created": False,
    "profit_evidence_created": False,
    "latency_superiority_evidence_created": False,
    "quantum_backend_execution_created": False,
    "quantum_simulator_execution_created": False,
    "quantum_optimizer_output_created": False,
    "quantum_advantage_evidence_created": False,
    "launch_readiness_created": False,
    "final_readiness_created": False,
    "atomicrows_bundle_mutated": False,
    "qtt_integrity_authority_created": False,
    "institutional_parameter_value_invented": False,
    "hidden_default_created": False,
}

REASON_CODES = (
    "PR150_READY",
    "PR150_UPSTREAM_REPORT_MISSING",
    "PR150_UPSTREAM_REPORT_PARSE_ERROR",
    "PR150_PR136_ORCHESTRATION_REQUIRED",
    "PR150_PR137R_RECONCILIATION_REQUIRED",
    "PR150_PR138_SEMANTIC_CONTRACT_REQUIRED",
    "PR150_PR149_BRIDGE_REQUIRED",
    "PR150_OWNER_POLICY_VALUE_AVAILABLE",
    "PR150_INTERNAL_ARCHITECTURE_VALUE_AVAILABLE",
    "PR150_ACCEPTED_SOURCE_VALUE_AVAILABLE",
    "PR150_SOURCE_EVIDENCE_REQUIRED",
    "PR150_RUNTIME_RECEIPT_REQUIRED",
    "PR150_REPLAY_PAPER_CALIBRATION_REQUIRED",
    "PR150_QUANTUM_METADATA_ONLY",
    "PR150_QUANTUM_EXECUTION_EVIDENCE_REQUIRED",
    "PR150_UNRESOLVED_PENDING_UPSTREAM",
    "PR150_NO_HIDDEN_DEFAULTS",
    "PR150_NO_VALUE_INVENTION",
    "PR150_NO_RUNTIME_AUTHORITY",
    "PR150_NO_LIVE_AUTHORITY",
    "PR150_NO_ORDER_AUTHORITY",
    "PR150_NO_PROFIT_AUTHORITY",
    "PR150_NO_QTT_INTEGRITY_AUTHORITY",
    "PR150_NO_BUNDLE_MUTATION_AUTHORITY",
    "PR150_REQUIRED_REPORT_KEY_MISSING",
    "PR150_REPORT_ID_MISMATCH",
    "PR150_REPORT_VERSION_MISMATCH",
    "PR150_AUTHORITY_CLASS_MISMATCH",
    "PR150_READINESS_CLASS_MISMATCH",
    "PR150_ENUMS_NOT_CONSTANT_ALIGNED",
    "PR150_NO_CLAIM_FLAGS_NOT_CONSTANT_ALIGNED",
    "PR150_FORBIDDEN_FLAG_TRUE",
    "PR150_TARGET_FAMILY_CATALOG_MISSING",
    "PR150_TARGET_ITEMS_MISSING",
    "PR150_TARGET_ITEMS_NOT_SORTED",
    "PR150_TARGET_ID_DUPLICATE",
    "PR150_TARGET_ITEM_SCHEMA_INVALID",
    "PR150_REASON_CODE_INVALID",
    "PR150_TARGET_ENUM_INVALID",
    "PR150_UNAUTHORIZED_DEFAULT_VALUE_FILLED",
    "PR150_UNAUTHORIZED_ALLOWED_RANGE_FILLED",
    "PR150_ACCEPTED_SOURCE_FIELD_SCOPE_REQUIRED",
    "PR150_OWNER_POLICY_EXTERNAL_FACT_MISUSE",
    "PR150_LOCAL_PATH_FORBIDDEN",
    "PR150_REPORT_NOT_DETERMINISTIC",
    "PR150_REPORT_INVALID",
    "PR150_REPORT_STALE_OR_NONDETERMINISTIC",
    "PR150_MASTER_PLAN_MUTATION_DETECTED",
    "PR150_ATOMICROWS_BUNDLE_MUTATION_DETECTED",
    "PR150_CHANGED_PATH_OUT_OF_SCOPE",
    "PR150_GIT_STATUS_UNAVAILABLE",
)

SCAN_SAFE_LITERAL_POLICY = {
    "policy_id": "PR150_OWNER_ADDED_LINE_LITERAL_SAFETY_POLICY",
    "centralized_flags_used_for_absence_checks": True,
    "negative_checks_use_structural_validation": True,
    "owner_scan_phrase_list_repeated_in_added_repo_lines": False,
}

EXACT_CHANGED_PATH_CANDIDATES = (
    REPORT_PATH.as_posix(),
    (
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/__init__.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/validator.py"
    ),
    "tools/validate_source_backed_classical_quantum_parameter_default_target_matrix.py",
    "tests/atomicrows/test_source_backed_classical_quantum_parameter_default_target_matrix.py",
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/report.py",
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/"
        "constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/"
        "report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge/report.py"
    ),
)
PR151_RETRIEVAL_TARGET_PACK_CHANGED_PATHS = (
    (
        "docs/master_plan/generated/"
        "PR151_OfficialSourceRetrievalTargetPackForParameterDefaults.report.json"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults/__init__.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults/validator.py"
    ),
    "tools/validate_official_source_retrieval_target_pack_parameter_defaults.py",
    (
        "tests/source_evidence/"
        "test_official_source_retrieval_target_pack_parameter_defaults.py"
    ),
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/"
        "constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/"
        "report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/report.py"
    ),
)

MARKET_SCOPES = (
    "PREDICTION_MARKETS_GENERAL",
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
)
VENUE_SCOPES = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")

TARGET_ITEM_REQUIRED_FIELDS = (
    "target_id",
    "target_family_id",
    "target_domain",
    "target_name",
    "target_description",
    "value_authority_class",
    "default_target_state",
    "evidence_requirement_class",
    "order_use_eligibility",
    "default_value",
    "allowed_range",
    "unit_or_scale",
    "formula_reference",
    "source_artifact_ref",
    "source_target_field_class",
    "runtime_receipt_requirement",
    "replay_paper_calibration_requirement",
    "quantum_execution_evidence_requirement",
    "downstream_consumer_classes",
    "market_scope",
    "agent_scope",
    "atomicrows_refs",
    "pr149_refs",
    "reason_codes",
    "no_claim_flags",
)

