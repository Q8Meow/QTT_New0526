"""Central constants for the PR151 official-source retrieval target pack."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR151"
BRANCH = "pr151-official-source-retrieval-target-pack-parameter-defaults"
PR_TITLE = "Official Source Retrieval Target Pack for Parameter Defaults"
REPORT_ID = (
    "QTT_PR151_OFFICIAL_SOURCE_RETRIEVAL_TARGET_PACK_FOR_PARAMETER_DEFAULTS_REPORT"
)
REPORT_VERSION = "v1"
AUTHORITY_CLASS = (
    "OFFICIAL_SOURCE_RETRIEVAL_TARGET_PACK_ONLY_NOT_RETRIEVAL_NOT_FACT_ACCEPTANCE"
)
READINESS_CLASS = (
    "RETRIEVAL_TARGET_PACK_READY_ONLY_NOT_RETRIEVED_NOT_ACCEPTED_NOT_ORDER_READY"
)
REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "PR151_OfficialSourceRetrievalTargetPackForParameterDefaults.report.json"
)
SUCCESS_MARKER = "QTT_OFFICIAL_SOURCE_RETRIEVAL_TARGET_PACK_PARAMETER_DEFAULTS_OK"
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
PR150_REPORT_PATH = Path(
    "docs/master_plan/generated/PR150_SourceBackedClassicalQuantumParameterDefaultTargetMatrix.report.json"
)
PR150_MODULE_DIR_PATH = Path(
    "src/qtt/stage1_prediction_markets/"
    "source_backed_classical_quantum_parameter_default_target_matrix"
)
SOURCE_EVIDENCE_PACKET_PATH = Path(
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
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
    PR150_REPORT_PATH,
    SOURCE_EVIDENCE_PACKET_PATH,
)

OPTIONAL_CONTEXT_ARTIFACTS = (
    PR150_MODULE_DIR_PATH,
    Path("tools/validate_source_backed_classical_quantum_parameter_default_target_matrix.py"),
    Path("tools/validate_source_evidence_retrieval_executor.py"),
    Path("tools/validate_source_evidence_acceptance.py"),
    Path("tools/validate_source_evidence_static.py"),
    Path("tools/validate_source_evidence_gate_confirmation_static.py"),
    Path("tools/validate_accepted_source_to_connector_semantic_binding.py"),
    Path("tools/validate_connector_semantic_binding_implementation_gate.py"),
    Path("tools/runtime_cash_component_field_map_validate.py"),
    Path("tools/private_state_read_receipt_gate_validate.py"),
    Path("tools/validate_per_venue_execution_lifecycle_model.py"),
    Path("tools/validate_cross_venue_execution_normalization_binding.py"),
)

SOURCE_TARGET_CLASS_VALUES = (
    "VENUE_API_SOURCE_TARGET",
    "ORDER_FIELD_SOURCE_TARGET",
    "ORDER_LIFECYCLE_SOURCE_TARGET",
    "ORDER_TYPE_SOURCE_TARGET",
    "FEE_RULE_SOURCE_TARGET",
    "TICK_RULE_SOURCE_TARGET",
    "PAYOUT_RULE_SOURCE_TARGET",
    "SETTLEMENT_RULE_SOURCE_TARGET",
    "SDK_BEHAVIOR_SOURCE_TARGET",
    "RATE_LIMIT_SOURCE_TARGET",
    "MARKET_DATA_SOURCE_TARGET",
    "ACCOUNT_PRIVATE_STATE_SOURCE_TARGET",
    "EXECUTION_LIFECYCLE_SOURCE_TARGET",
    "FILL_INTEGRITY_SOURCE_TARGET",
    "CASHFLOW_PNL_SOURCE_TARGET",
    "LATENCY_COMPONENT_SOURCE_TARGET",
    "RECONCILIATION_SOURCE_TARGET",
    "CROSS_VENUE_NORMALIZATION_SOURCE_TARGET",
    "ORDERBOOK_FIELD_SOURCE_TARGET",
    "ORDERBOOK_EVENT_SEQUENCE_SOURCE_TARGET",
    "MARKET_STATUS_SOURCE_TARGET",
    "EVENT_LIFECYCLE_SOURCE_TARGET",
    "SETTLEMENT_FINALITY_STATUS_SOURCE_TARGET",
    "TRADE_TICKER_HISTORY_FIELD_SOURCE_TARGET",
    "STREAMING_UPDATE_FIELD_SOURCE_TARGET",
    "RISK_CAPITAL_SOURCE_TARGET",
    "CLASSICAL_STRATEGY_OFFICIAL_SEMANTICS_SOURCE_TARGET",
    "OPTIMIZER_PROVIDER_DOC_SOURCE_TARGET",
    "QUANTUM_PROVIDER_DOC_SOURCE_TARGET",
    "ATOMICROWS_COMPATIBILITY_SOURCE_TARGET",
)

OFFICIAL_SOURCE_CLASS_VALUES = (
    "OFFICIAL_VENUE_DOCS",
    "OFFICIAL_API_DOCS",
    "OFFICIAL_SDK_DOCS",
    "OFFICIAL_RULEBOOKS",
    "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS",
    "OFFICIAL_PROVIDER_DOCS",
)

NON_AUTHORITATIVE_SOURCE_CLASS_VALUES = (
    "BLOG",
    "FORUM",
    "SOCIAL_POST",
    "CHAT_SUMMARY",
    "LLM_MEMORY",
    "AGENT_SUMMARY",
    "RESEARCH_NOTE",
    "UNVERIFIED_SCREENSHOT",
)

RETRIEVAL_METHOD_POLICY_VALUES = (
    "TARGET_ONLY_NO_ONLINE_RETRIEVAL",
    "FUTURE_RETRIEVAL_PR_REQUIRED",
    "FUTURE_CAPTURE_PR_REQUIRED",
)

LOCATOR_REQUIREMENT_CLASS_VALUES = (
    "SOURCE_LOCATOR_REQUIRED",
    "QUOTE_SPAN_REQUIRED",
    "MACHINE_FIELD_LOCATOR_REQUIRED",
    "QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR_REQUIRED",
    "OFFICIAL_PROVIDER_DOC_LOCATOR_REQUIRED",
)

REVALIDATION_CLASS_VALUES = (
    "LIVE_CRITICAL_P1D_AND_EVENT_TRIGGERED",
    "LOW_RISK_P7D_AND_EVENT_TRIGGERED",
    "PROVIDER_DOCS_EVENT_TRIGGERED",
    "OWNER_REVIEW_BEFORE_LIVE_USE",
)

CONFLICT_POLICY_CLASS_VALUES = (
    "OFFICIAL_SOURCE_CONFLICT_REVIEW_REQUIRED",
    "MULTI_OFFICIAL_SOURCE_CONFLICT_REVIEW_REQUIRED",
    "OWNER_REVIEW_REQUIRED_FOR_CONFLICT",
)

ACCEPTANCE_HANDOFF_CLASS_VALUES = (
    "FUTURE_PR153_ACCEPTANCE_REVIEW_REQUIRED",
    "FUTURE_ACCEPTED_TARGET_FIELD_PACKET_REQUIRED",
)

TARGET_QUEUE_STATE_VALUES = (
    "TARGET_DECLARED_NOT_RETRIEVED",
    "TARGET_DECLARED_DOMAIN_SLOT_PENDING_OWNER_APPROVAL",
    "TARGET_DECLARED_OFFICIAL_SOURCE_CLASS_READY",
    "TARGET_DECLARED_REQUIRES_SOURCE_LOCATOR",
    "TARGET_DECLARED_REQUIRES_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR",
    "TARGET_DECLARED_REQUIRES_CONFLICT_CHECK",
    "TARGET_DECLARED_REQUIRES_REVALIDATION_POLICY",
    "TARGET_DECLARED_READY_FOR_FUTURE_RETRIEVAL_PR",
    "TARGET_BLOCKED_NO_PR150_SOURCE_REQUIRED_TARGET",
    "TARGET_BLOCKED_NO_OWNER_SOURCE_SCOPE",
    "TARGET_BLOCKED_NO_OFFICIAL_SOURCE_CLASS",
    "TARGET_BLOCKED_PRIVATE_OR_SECRET_SCOPE",
    "TARGET_BLOCKED_NON_AUTHORITATIVE_SOURCE_CLASS",
    "TARGET_BLOCKED_NO_ACCEPTANCE_HANDOFF",
    "TARGET_BLOCKED_DOMAIN_ROUTE_UNAUTHORIZED",
)

VALUE_CAPTURE_STATE_VALUES = (
    "NOT_CAPTURED_TARGET_ONLY",
    "CAPTURE_REQUIRES_FUTURE_PR",
    "BLOCKED_PENDING_DOMAIN_ROUTE",
    "BLOCKED_PENDING_OFFICIAL_SOURCE_CLASS",
    "BLOCKED_PRIVATE_OR_SECRET_SCOPE",
)

ACCEPTED_VALUE_STATE_VALUES = (
    "NOT_ACCEPTED_TARGET_ONLY",
    "ACCEPTANCE_REQUIRES_FUTURE_PR",
    "ACCEPTANCE_BLOCKED_PENDING_CAPTURE",
    "ACCEPTANCE_BLOCKED_PENDING_CONFLICT_REVIEW",
    "ACCEPTANCE_BLOCKED_PENDING_OWNER_REVIEW",
)

ORDER_USE_ELIGIBILITY_VALUES = (
    "NOT_ORDER_USABLE_RETRIEVAL_TARGET_ONLY",
    "PENDING_FUTURE_RETRIEVAL",
    "PENDING_FUTURE_ACCEPTANCE",
    "PENDING_CONNECTOR_UNLOCK",
    "PENDING_RUNTIME_RECEIPT",
    "PENDING_REPLAY_PAPER_CALIBRATION",
    "PENDING_QUANTUM_EVIDENCE",
    "ORDER_USE_REQUIRES_FUTURE_PR",
)

DOMAIN_ROUTE_STATE_VALUES = (
    "DOMAIN_ROUTE_ALREADY_AUTHORIZED_UPSTREAM",
    "DOMAIN_ROUTE_PENDING_OWNER_APPROVAL",
    "DOMAIN_ROUTE_REQUIRED_FOR_FUTURE_RETRIEVAL",
    "DOMAIN_ROUTE_BLOCKED_UNAUTHORIZED",
    "DOMAIN_ROUTE_NOT_APPLICABLE",
)

DOWNSTREAM_CONSUMER_CLASS_VALUES = (
    "VENUE_SOURCE_EVIDENCE_TARGETING_CONSUMER",
    "EXECUTION_PLANNING_METADATA_CONSUMER",
    "RISK_CAPITAL_CONTROL_METADATA_CONSUMER",
    "PARAMETER_STACK_SELECTION_METADATA_CONSUMER",
    "SCORING_RANKING_METADATA_CONSUMER",
    "OPTIMIZER_PLANNING_METADATA_CONSUMER",
    "QUANTUM_PLANNING_METADATA_CONSUMER",
    "ATOMICROWS_COMPATIBILITY_METADATA_CONSUMER",
    "SOURCE_EVIDENCE_CAPTURE_CONSUMER",
    "SOURCE_EVIDENCE_ACCEPTANCE_CONSUMER",
    "CONNECTOR_SEMANTIC_UNLOCK_CONSUMER",
)

NO_CLAIM_FLAGS = {
    "network_retrieval_executed": False,
    "retrieval_capable_code_created": False,
    "source_capture_created": False,
    "external_fact_value_created": False,
    "source_fact_acceptance_created": False,
    "connector_semantic_value_created": False,
    "runtime_cash_receipt_created": False,
    "order_execution_created": False,
    "live_reachability_created": False,
    "replay_execution_created": False,
    "paper_execution_created": False,
    "replay_paper_result_created": False,
    "profit_proof_created": False,
    "latency_superiority_proof_created": False,
    "quantum_backend_call_created": False,
    "quantum_simulator_call_created": False,
    "quantum_optimizer_output_created": False,
    "quantum_superiority_proof_created": False,
    "launch_readiness_created": False,
    "final_readiness_created": False,
    "atomicrows_bundle_mutated": False,
    "qtt_integrity_authority_created": False,
    "official_domain_invented": False,
    "official_value_invented": False,
    "hidden_default_created": False,
}

REASON_CODES = (
    "PR151_READY",
    "PR151_UPSTREAM_REPORT_MISSING",
    "PR151_UPSTREAM_REPORT_PARSE_ERROR",
    "PR151_PR136_ORCHESTRATION_REQUIRED",
    "PR151_PR137R_RECONCILIATION_REQUIRED",
    "PR151_PR138_SEMANTIC_CONTRACT_REQUIRED",
    "PR151_PR149_BRIDGE_REQUIRED",
    "PR151_PR150_TARGET_MATRIX_REQUIRED",
    "PR151_OWNER_SOURCE_PACKET_REQUIRED",
    "PR151_SOURCE_REQUIRED_TARGET_FOUND",
    "PR151_OFFICIAL_SOURCE_CLASS_READY",
    "PR151_DOMAIN_ROUTE_PENDING_OWNER_APPROVAL",
    "PR151_SOURCE_LOCATOR_REQUIRED",
    "PR151_QUOTE_OR_MACHINE_LOCATOR_REQUIRED",
    "PR151_CONFLICT_POLICY_REQUIRED",
    "PR151_REVALIDATION_POLICY_REQUIRED",
    "PR151_ACCEPTANCE_HANDOFF_REQUIRED",
    "PR151_NOT_RETRIEVED_TARGET_ONLY",
    "PR151_NO_FACT_ACCEPTANCE",
    "PR151_NO_CONNECTOR_VALUE",
    "PR151_NO_RUNTIME_RECEIPT",
    "PR151_NO_ORDER_AUTHORITY",
    "PR151_NO_BUNDLE_MUTATION_AUTHORITY",
    "PR151_NO_QTT_INTEGRITY_AUTHORITY",
    "PR151_NO_VALUE_INVENTION",
    "PR151_NO_DOMAIN_INVENTION",
    "PR151_NO_NETWORK_EXECUTION",
    "PR151_PR150_SOURCE_TARGET_COVERAGE_REQUIRED",
    "PR151_NON_AUTHORITATIVE_SOURCE_CLASS_BLOCKED",
    "PR151_REQUIRED_REPORT_KEY_MISSING",
    "PR151_REPORT_ID_MISMATCH",
    "PR151_REPORT_VERSION_MISMATCH",
    "PR151_AUTHORITY_CLASS_MISMATCH",
    "PR151_READINESS_CLASS_MISMATCH",
    "PR151_ENUMS_NOT_CONSTANT_ALIGNED",
    "PR151_NO_CLAIM_FLAGS_NOT_CONSTANT_ALIGNED",
    "PR151_FORBIDDEN_FLAG_TRUE",
    "PR151_QUEUE_ITEM_SCHEMA_INVALID",
    "PR151_QUEUE_ITEMS_MISSING",
    "PR151_QUEUE_ITEMS_NOT_SORTED",
    "PR151_QUEUE_ITEM_DUPLICATE",
    "PR151_QUEUE_ENUM_INVALID",
    "PR151_REASON_CODE_INVALID",
    "PR151_REPORT_NOT_DETERMINISTIC",
    "PR151_REPORT_INVALID",
    "PR151_REPORT_STALE_OR_NONDETERMINISTIC",
    "PR151_MASTER_PLAN_MUTATION_DETECTED",
    "PR151_ATOMICROWS_BUNDLE_MUTATION_DETECTED",
    "PR151_ATOMICROWS_SIDECAR_REFERENCE_DETECTED",
    "PR151_QTT_INTEGRITY_AUTHORITY_DETECTED",
    "PR151_LOCAL_PATH_FORBIDDEN",
    "PR151_CHANGED_PATH_OUT_OF_SCOPE",
    "PR151_GIT_STATUS_UNAVAILABLE",
    "PR151_NETWORK_SURFACE_DETECTED",
    "PR151_CAPTURED_VALUE_CREATED",
    "PR151_ACCEPTED_VALUE_CREATED",
    "PR151_CONNECTOR_VALUE_CREATED",
    "PR151_RUNTIME_RECEIPT_VALUE_CREATED",
    "PR151_REPLAY_PAPER_RESULT_VALUE_CREATED",
    "PR151_QUANTUM_OUTPUT_VALUE_CREATED",
    "PR151_ORDER_USABLE_CREATED",
    "PR151_DOMAIN_ROUTE_INVENTED",
)

SCAN_SAFE_LITERAL_POLICY = {
    "policy_id": "PR151_OWNER_ADDED_LINE_LITERAL_SAFETY_POLICY",
    "centralized_flags_used_for_absence_checks": True,
    "negative_checks_use_structural_validation": True,
    "owner_scan_phrase_list_repeated_in_added_repo_lines": False,
}

NETWORK_CODE_FORBIDDEN_TOKENS_FOR_STRUCTURAL_TESTS = (
    "requests",
    "urllib",
    "httpx",
    "aiohttp",
    "socket",
    "webbrowser",
    "ftplib",
    "curl ",
    "wget ",
    "Invoke-WebRequest",
    "Invoke-RestMethod",
    "Start-BitsTransfer",
)

EXACT_CHANGED_PATH_CANDIDATES = (
    REPORT_PATH.as_posix(),
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
    "tests/source_evidence/test_official_source_retrieval_target_pack_parameter_defaults.py",
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

QUEUE_ITEM_REQUIRED_FIELDS = (
    "retrieval_target_id",
    "pr150_target_id",
    "pr150_target_domain",
    "pr150_target_name",
    "target_field_id",
    "target_field_path",
    "target_platform_scope",
    "target_market_scope",
    "official_source_class",
    "official_source_domain_slot",
    "owner_approved_domain_route",
    "owner_domain_route_state",
    "retrieval_method_policy",
    "source_locator_requirement",
    "quote_span_requirement",
    "machine_field_locator_requirement",
    "future_capture_requirement",
    "conflict_policy_class",
    "revalidation_class",
    "acceptance_handoff_class",
    "downstream_acceptance_target",
    "connector_unlock_dependency",
    "atomicrows_materialization_dependency",
    "quantum_forward_dependency",
    "queue_state",
    "value_capture_state",
    "accepted_value_state",
    "order_use_eligibility",
    "reason_codes",
    "no_claim_flags",
)

