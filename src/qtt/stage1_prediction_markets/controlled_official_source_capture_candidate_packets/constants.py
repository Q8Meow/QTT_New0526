"""Central constants for PR153 controlled official-source capture."""

from __future__ import annotations

from pathlib import Path

from . import reason_codes as rc
from .models import OWNER_DECISION_OPTIONS, OWNER_NON_SOURCE_BACKED_STATUSES


PR_ID = "PR153"
PR_TITLE = "Controlled Official Source Capture Candidate Packets"
REPORT_ID = "QTT_PR153_CONTROLLED_OFFICIAL_SOURCE_CAPTURE_CANDIDATE_PACKETS_REPORT"
REPORT_VERSION = "v1"
AUTHORITY_CLASS = (
    "CONTROLLED_OFFICIAL_SOURCE_CAPTURE_CANDIDATE_PACKETS_ONLY_"
    "NOT_FACT_ACCEPTANCE_NOT_CONNECTOR_NOT_RUNTIME_NOT_ORDER_AUTHORITY"
)
READINESS_CLASS = "PR154_ACCEPTANCE_REVIEW_INPUT_READY_IF_VALIDATED"
SUCCESS_MARKER = "QTT_CONTROLLED_OFFICIAL_SOURCE_CAPTURE_CANDIDATE_PACKETS_OK"
INCOMPLETE_MARKER = "PR153_CAPTURE_INCOMPLETE_WITH_BLOCKER_TRIAGE"
BLOCKER_TRIAGE_OK_MARKER = "PR153_CAPTURE_INCOMPLETE_WITH_BLOCKER_TRIAGE_OK"
FULL_CAPTURE_SUCCESS = "FULL_CAPTURE_SUCCESS"
BLOCKER_TRIAGE_SUCCESS = "BLOCKER_TRIAGE_SUCCESS"
COMPLETION_LABEL = "PR153_CAPTURE_INCOMPLETE_WITH_BLOCKER_TRIAGE"
OWNER_APPROVED_COMMIT_FRAMING = (
    "CONTROLLED_OFFICIAL_SOURCE_CAPTURE_PLUS_BLOCKER_TRIAGE_ARCHITECTURE"
)
REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "PR153_ControlledOfficialSourceCaptureCandidatePackets.report.json"
)
BATCH_SIZE = 25

PR153A_TOTAL_PR151_TARGETS = 342
PR153A_CAPTURED_CANDIDATE_PACKET_COUNT = 92
PR153A_UNRESOLVED_TARGET_COUNT = 250
PR153A_TRUE_EXTERNAL_PUBLIC_SOURCE_VALUE_CAPTURE_TARGET_COUNT = 126
PR153A_REMAINING_EXTERNAL_PUBLIC_CAPTURE_RETRY_TARGET_COUNT = 34
PR153A_INTERNAL_CONTROL_PLANE_TARGET_COUNT = 138
PR153A_TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED_COUNT = 33
PR153A_PRIVATE_DOC_OR_ATTESTATION_REQUIRED_COUNT = 6
PR153A_OWNER_PROVIDED_VALUE_CANDIDATE_ROUTE_COUNT = 39
PR153A_PR154_ACCEPTANCE_REVIEW_ONLY_COUNT = 92

ELIGIBILITY_LANES = (
    "EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET",
    "INTERNAL_QTT_POLICY_OR_CONTROL_PLANE_TARGET",
    "TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED",
    "PRIVATE_DOC_OR_ATTESTATION_REQUIRED",
    "PR154_ACCEPTANCE_REVIEW_ONLY",
    "OWNER_PROVIDED_VALUE_CANDIDATE_ROUTE",
    "OWNER_DISAPPROVAL_OR_DESCOPE_CANDIDATE",
)

OWNER_ROUTE_BY_ELIGIBILITY_LANE = {
    "INTERNAL_QTT_POLICY_OR_CONTROL_PLANE_TARGET": (
        "INTERNAL_POLICY_CONTROL_PLANE_ROUTE_APPROVED"
    ),
    "TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED": (
        "TARGET_SPLIT_RECLASSIFICATION_REVIEW_APPROVED"
    ),
    "PRIVATE_DOC_OR_ATTESTATION_REQUIRED": (
        "PRIVATE_DOC_ACCESS_RIGHTS_ATTESTATION_ROUTE_APPROVED"
    ),
    "OWNER_PROVIDED_VALUE_CANDIDATE_ROUTE": (
        "OWNER_PROVIDED_CANDIDATE_ROUTE_ONLY_NON_SOURCE_BACKED"
    ),
    "EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET": "PR153R_RETRY_CAPTURE",
    "PR154_ACCEPTANCE_REVIEW_ONLY": (
        "PR154_INDEPENDENT_REVIEW_OR_OWNER_NON_SOURCE_BACKED_OVERRIDE_ROUTE"
    ),
    "OWNER_DISAPPROVAL_OR_DESCOPE_CANDIDATE": "AVAILABLE_BUT_NOT_USED",
}

OWNER_NON_SOURCE_BACKED_OVERRIDE_STATUSES = OWNER_NON_SOURCE_BACKED_STATUSES + (
    "OWNER_OVERRIDE_RECORDED_PR154_WORKFLOW_GATE_BYPASSED",
    "OWNER_OVERRIDE_RECORDED_EXTERNAL_FACT_STILL_NON_SOURCE_BACKED",
    "OWNER_OVERRIDE_RECEIPT_REQUIRED",
)

OWNER_NON_SOURCE_BACKED_RISK_FLAGS = {
    "source_backed_fact_created": False,
    "accepted_source_evidence_packet_created": False,
    "official_value_accepted": False,
    "source_truth_status": "OWNER_AUTHORIZED_NON_SOURCE_BACKED",
    "owner_override_receipt_required": True,
    "owner_assumes_external_fact_risk": True,
    "downstream_consumer_warning_required": True,
    "connector_use_allowed_without_later_owner_command": False,
    "runtime_use_allowed_without_later_owner_command": False,
    "order_use_allowed_without_later_owner_command": False,
    "replay_paper_truth_use_allowed_without_later_owner_command": False,
    "launch_readiness_use_allowed_without_later_owner_command": False,
    "atomicrows_materialization_allowed_without_later_owner_command": False,
}

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
PR151_REPORT_PATH = Path(
    "docs/master_plan/generated/PR151_OfficialSourceRetrievalTargetPackForParameterDefaults.report.json"
)
PR152_REPORT_PATH = Path(
    "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
)
SOURCE_EVIDENCE_PACKET_PATH = Path(
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
)
PR151_MODULE_DIR_PATH = Path(
    "src/qtt/stage1_prediction_markets/"
    "official_source_retrieval_target_pack_parameter_defaults"
)
PR150_MODULE_DIR_PATH = Path(
    "src/qtt/stage1_prediction_markets/"
    "source_backed_classical_quantum_parameter_default_target_matrix"
)
PR152_MODULE_DIR_PATH = Path(
    "src/qtt/stage1_prediction_markets/"
    "grand_global_debug_logical_consistency_audit"
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
    PR151_REPORT_PATH,
    PR152_REPORT_PATH,
    SOURCE_EVIDENCE_PACKET_PATH,
    PR151_MODULE_DIR_PATH,
    PR150_MODULE_DIR_PATH,
    PR152_MODULE_DIR_PATH,
    Path("tools/validate_official_source_retrieval_target_pack_parameter_defaults.py"),
    Path("tools/validate_source_backed_classical_quantum_parameter_default_target_matrix.py"),
    Path("tools/validate_grand_global_debug_logical_consistency_audit.py"),
    Path("tools/validate_source_evidence_retrieval_executor.py"),
    Path("tools/validate_source_evidence_acceptance.py"),
    Path("tools/run_validation_gates.py"),
    Path("tests/fail_closed/test_run_validation_gates.py"),
)

VENUE_SCOPES = ("FORECASTEX_IBKR", "KALSHI", "POLYMARKET")

OFFICIAL_SOURCE_CLASS_VALUES = (
    "OFFICIAL_VENUE_DOCS",
    "OFFICIAL_API_DOCS",
    "OFFICIAL_SDK_DOCS",
    "OFFICIAL_RULEBOOKS",
    "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS",
    "OFFICIAL_PROVIDER_DOCS",
    "OFFICIAL_TECHNICAL_SPEC_DOCS",
    "OFFICIAL_CHANGELOG_DOCS",
    "OFFICIAL_PUBLIC_SUPPORT_DOCS",
    "OFFICIAL_REGULATORY_SOURCE_DOCS",
)

OFFICIALITY_ROUTE_VALUES = (
    "OFFICIAL_DOC_SITE_DIRECT",
    "OFFICIAL_API_DOC_SITE_DIRECT",
    "OFFICIAL_SDK_DOC_SITE_DIRECT",
    "OFFICIAL_RULEBOOK_SITE_DIRECT",
    "OFFICIAL_FEE_TICK_SETTLEMENT_DOC_DIRECT",
    "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
    "OFFICIAL_PUBLIC_SUPPORT_DOC_DIRECT",
    "OFFICIAL_DOC_LINKED_REPOSITORY",
    "OFFICIAL_DOC_LINKED_SPEC",
    "OFFICIAL_REGULATORY_SOURCE_DIRECT",
)

BLOCKER_PRIMARY_CATEGORIES = tuple(rc.BLOCKER_CATEGORY_TO_REASON_CODE)
OWNER_DECISION_OPTIONS_LIST = list(OWNER_DECISION_OPTIONS)

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

P0_SOURCE_TARGET_CLASSES = {
    "FEE_RULE_SOURCE_TARGET",
    "TICK_RULE_SOURCE_TARGET",
    "PAYOUT_RULE_SOURCE_TARGET",
    "SETTLEMENT_RULE_SOURCE_TARGET",
    "ORDER_FIELD_SOURCE_TARGET",
    "MARKET_DATA_SOURCE_TARGET",
    "RATE_LIMIT_SOURCE_TARGET",
    "SDK_BEHAVIOR_SOURCE_TARGET",
    "ORDERBOOK_FIELD_SOURCE_TARGET",
    "ORDERBOOK_EVENT_SEQUENCE_SOURCE_TARGET",
    "EXECUTION_LIFECYCLE_SOURCE_TARGET",
    "FILL_INTEGRITY_SOURCE_TARGET",
}
P1_SOURCE_TARGET_CLASSES = {
    "ACCOUNT_PRIVATE_STATE_SOURCE_TARGET",
    "RISK_CAPITAL_SOURCE_TARGET",
    "RECONCILIATION_SOURCE_TARGET",
    "CROSS_VENUE_NORMALIZATION_SOURCE_TARGET",
    "LATENCY_COMPONENT_SOURCE_TARGET",
}
P2_SOURCE_TARGET_CLASSES = {
    "CLASSICAL_STRATEGY_OFFICIAL_SEMANTICS_SOURCE_TARGET",
    "VENUE_API_SOURCE_TARGET",
    "OPTIMIZER_PROVIDER_DOC_SOURCE_TARGET",
    "ATOMICROWS_COMPATIBILITY_SOURCE_TARGET",
}
P3_SOURCE_TARGET_CLASSES = {"QUANTUM_PROVIDER_DOC_SOURCE_TARGET"}

PRIVATE_OR_AUTH_FIELD_IDS = {
    "account_private_state_semantics",
    "runtime_available_cash_receipt",
}

INTERNAL_QTT_FIELD_IDS = {
    "agent_binding_score_input",
    "calibration_confidence",
    "candidate_count",
    "candidate_inventory_links",
    "capital_reserve",
    "drawdown_guard",
    "dual_result_review_input",
    "expected_net_cost_score_target",
    "expected_net_value_score_target",
    "final_stack_score_input",
    "future_agent_family_eligibility_dependencies",
    "future_source_materialization_dependencies",
    "lane_separation",
    "latency_budget_slot",
    "latency_fit_score_input",
    "lifecycle_readiness_score_input",
    "liquidity_guard",
    "live_pretrade_exclusion",
    "new_increased_exposure_block",
    "no_automatic_live_promotion",
    "no_bundle_mutation_state",
    "no_result_fabrication",
    "optimizer_output_receipt",
    "optimizer_promotion_gate",
    "per_agent_exposure",
    "per_market_exposure",
    "per_venue_exposure",
    "platform_applicability_score_input",
    "portfolio_exposure",
    "position_sizing",
    "precomputed_hot_path_snapshot",
    "pr149_materialization_targets",
    "promotion_gate_input",
    "quantum_hot_path_exclusion",
    "quantum_result_receipt",
    "quantum_strongest_classical_comparator",
    "replay_metric",
    "replay_paper_calibration_input",
    "risk_fit_score_input",
    "row_family_references",
    "semantic_field_references",
    "slippage_guard",
    "source_evidence_completeness_input",
    "stop_quarantine_kill_switch_threshold",
    "strategy_fit_score_input",
    "tie_breaker_policy_input",
}

CONTROLLED_DISCOVERY_QUERIES = (
    "Kalshi official API documentation orderbook websocket rate limits fees rulebook",
    "Polymarket official CLOB API documentation orderbook rate limits fees tick size settlement",
    "ForecastEx official API documentation rulebook fees settlement IBKR ForecastTrader",
    "Qiskit official documentation QAOA VQE shots backend simulator options",
    "D-Wave Ocean official documentation QUBO Ising chain embedding annealing schedule",
    "SciPy optimize minimize official documentation optimizer methods constraints",
    "scikit-learn official GridSearchCV RandomizedSearchCV documentation",
)

OFFICIAL_DOMAIN_ROUTE_RECEIPTS = (
    {
        "source_domain": "docs.kalshi.com",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "officiality_evidence": "Kalshi docs index retrieved from docs.kalshi.com/llms.txt.",
        "source_classes": ["OFFICIAL_API_DOCS", "OFFICIAL_SDK_DOCS"],
    },
    {
        "source_domain": "kalshi.com",
        "officiality_route": "OFFICIAL_FEE_TICK_SETTLEMENT_DOC_DIRECT",
        "officiality_evidence": "Kalshi fee schedule PDF retrieved from kalshi.com/docs.",
        "source_classes": ["OFFICIAL_FEE_TICK_SETTLEMENT_DOCS"],
    },
    {
        "source_domain": "docs.polymarket.com",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "officiality_evidence": "Polymarket docs index retrieved from docs.polymarket.com/llms.txt.",
        "source_classes": [
            "OFFICIAL_API_DOCS",
            "OFFICIAL_VENUE_DOCS",
            "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS",
        ],
    },
    {
        "source_domain": "forecastex.com",
        "officiality_route": "OFFICIAL_DOC_SITE_DIRECT",
        "officiality_evidence": "ForecastEx public FAQ and regulatory pages are on forecastex.com.",
        "source_classes": [
            "OFFICIAL_VENUE_DOCS",
            "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS",
        ],
    },
    {
        "source_domain": "data.forecastex.com",
        "officiality_route": "OFFICIAL_RULEBOOK_SITE_DIRECT",
        "officiality_evidence": "ForecastEx rulebook PDF hosted under data.forecastex.com/regulatory.",
        "source_classes": ["OFFICIAL_RULEBOOKS"],
    },
    {
        "source_domain": "www.interactivebrokers.com",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "officiality_evidence": "IBKR Campus API pages document ForecastEx contract handling.",
        "source_classes": ["OFFICIAL_API_DOCS"],
    },
    {
        "source_domain": "quantum.cloud.ibm.com",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "officiality_evidence": "IBM Quantum documentation pages redirect to quantum.cloud.ibm.com.",
        "source_classes": ["OFFICIAL_PROVIDER_DOCS"],
    },
    {
        "source_domain": "docs.dwavequantum.com",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "officiality_evidence": "D-Wave Quantum Computing Products documentation pages.",
        "source_classes": ["OFFICIAL_PROVIDER_DOCS"],
    },
    {
        "source_domain": "docs.scipy.org",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "officiality_evidence": "SciPy reference documentation pages.",
        "source_classes": ["OFFICIAL_PROVIDER_DOCS"],
    },
    {
        "source_domain": "scikit-learn.org",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "officiality_evidence": "scikit-learn stable documentation pages.",
        "source_classes": ["OFFICIAL_PROVIDER_DOCS"],
    },
)

SOURCE_ROUTES = (
    {
        "route_id": "KALSHI_MARKET_DATA_API",
        "platforms": ("KALSHI",),
        "target_field_ids": ("venue_api_semantics", "market_data_semantics"),
        "official_source_class": "OFFICIAL_API_DOCS",
        "source_domain": "docs.kalshi.com",
        "source_url": "https://docs.kalshi.com/getting_started/quick_start_market_data",
        "source_title": "Quick Start: Market Data - Kalshi API Documentation",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 34-51",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "Kalshi provides several public endpoints that don't require API keys.",
        "candidate_observation_type": "PUBLIC_API_DOC_QUOTE",
    },
    {
        "route_id": "KALSHI_ORDERBOOK_RESPONSE",
        "platforms": ("KALSHI",),
        "target_field_ids": ("orderbook_snapshot_freshness",),
        "official_source_class": "OFFICIAL_API_DOCS",
        "source_domain": "docs.kalshi.com",
        "source_url": "https://docs.kalshi.com/getting_started/orderbook_responses",
        "source_title": "Orderbook Responses - Kalshi API Documentation",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 74-111",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "The Get Market Orderbook endpoint returns the current state of bids for a specific market.",
        "candidate_observation_type": "ORDERBOOK_SCHEMA_QUOTE",
    },
    {
        "route_id": "KALSHI_WEBSOCKET_CONNECTION",
        "platforms": ("KALSHI",),
        "target_field_ids": ("websocket_orderbook_event_sequencing",),
        "official_source_class": "OFFICIAL_API_DOCS",
        "source_domain": "docs.kalshi.com",
        "source_url": "https://docs.kalshi.com/websockets/websocket-connection",
        "source_title": "WebSocket Connection - Kalshi API Documentation",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 186-210",
        "locator_type": "MACHINE_FIELD_LOCATOR",
        "quote_or_locator": "Subscribe Command params channels orderbook_delta market_ticker.",
        "candidate_observation_type": "WEBSOCKET_SCHEMA_LOCATOR",
    },
    {
        "route_id": "KALSHI_RATE_LIMITS",
        "platforms": ("KALSHI",),
        "target_field_ids": ("rate_limits", "rate_limit_field"),
        "official_source_class": "OFFICIAL_API_DOCS",
        "source_domain": "docs.kalshi.com",
        "source_url": "https://docs.kalshi.com/getting_started/rate_limits",
        "source_title": "Rate Limits and Tiers - Kalshi API Documentation",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 55-68",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "Every authenticated request costs tokens.",
        "candidate_observation_type": "RATE_LIMIT_DOC_QUOTE",
    },
    {
        "route_id": "KALSHI_CREATE_ORDER",
        "platforms": ("KALSHI",),
        "target_field_ids": (
            "order_fields",
            "order_type_field",
            "limit_price_field",
            "order_intent_parameter",
        ),
        "official_source_class": "OFFICIAL_API_DOCS",
        "source_domain": "docs.kalshi.com",
        "source_url": "https://docs.kalshi.com/api-reference/orders/create-order",
        "source_title": "Create Order - Kalshi API Documentation",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 223-269",
        "locator_type": "MACHINE_FIELD_LOCATOR",
        "quote_or_locator": "POST /portfolio/orders request body ticker count yes_price no_price type.",
        "candidate_observation_type": "ORDER_ENTRY_SCHEMA_LOCATOR",
    },
    {
        "route_id": "KALSHI_MARKET_LIFECYCLE",
        "platforms": ("KALSHI",),
        "target_field_ids": ("settlement_rules", "execution_lifecycle"),
        "official_source_class": "OFFICIAL_API_DOCS",
        "source_domain": "docs.kalshi.com",
        "source_url": "https://docs.kalshi.com/getting_started/market_lifecycle",
        "source_title": "Market Lifecycle - Kalshi API Documentation",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 119-124",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "Once settlement completes, positions are paid out.",
        "candidate_observation_type": "SETTLEMENT_DOC_QUOTE",
    },
    {
        "route_id": "KALSHI_FEE_SCHEDULE",
        "platforms": ("KALSHI",),
        "target_field_ids": ("fee_rules", "fee_settlement_cost_field", "cashflow_pnl_semantics"),
        "official_source_class": "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS",
        "source_domain": "kalshi.com",
        "source_url": "https://kalshi.com/docs/kalshi-fee-schedule.pdf",
        "source_title": "Kalshi Fee Schedule",
        "officiality_route": "OFFICIAL_FEE_TICK_SETTLEMENT_DOC_DIRECT",
        "source_locator": "PDF page 2 lines 27-30",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "There is no settlement fee.",
        "candidate_observation_type": "FEE_SCHEDULE_QUOTE",
    },
    {
        "route_id": "KALSHI_SDK_OVERVIEW",
        "platforms": ("KALSHI",),
        "target_field_ids": ("sdk_behavior",),
        "official_source_class": "OFFICIAL_SDK_DOCS",
        "source_domain": "docs.kalshi.com",
        "source_url": "https://docs.kalshi.com/sdks/overview",
        "source_title": "Kalshi SDKs - API Documentation",
        "officiality_route": "OFFICIAL_SDK_DOC_SITE_DIRECT",
        "source_locator": "docs.kalshi.com llms.txt SDKs entry",
        "locator_type": "MACHINE_FIELD_LOCATOR",
        "quote_or_locator": "Kalshi SDKs: Official SDKs for integrating with the Kalshi API.",
        "candidate_observation_type": "SDK_DOC_INDEX_LOCATOR",
    },
    {
        "route_id": "POLYMARKET_CREATE_ORDER",
        "platforms": ("POLYMARKET",),
        "target_field_ids": (
            "order_fields",
            "order_type_field",
            "limit_price_field",
            "minimum_order_size_field",
            "order_intent_parameter",
        ),
        "official_source_class": "OFFICIAL_API_DOCS",
        "source_domain": "docs.polymarket.com",
        "source_url": "https://docs.polymarket.com/trading/orders/create",
        "source_title": "Create Order - Polymarket Documentation",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 126-185 and 418-426",
        "locator_type": "MACHINE_FIELD_LOCATOR",
        "quote_or_locator": "All orders on Polymarket are expressed as limit orders.",
        "candidate_observation_type": "ORDER_ENTRY_DOC_QUOTE",
    },
    {
        "route_id": "POLYMARKET_TICK_SIZE",
        "platforms": ("POLYMARKET",),
        "target_field_ids": ("tick_rules", "tick_size_field"),
        "official_source_class": "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS",
        "source_domain": "docs.polymarket.com",
        "source_url": "https://docs.polymarket.com/api-reference/market-data/get-tick-size",
        "source_title": "Get tick size - Polymarket Documentation",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "API reference response field minimum_tick_size",
        "locator_type": "MACHINE_FIELD_LOCATOR",
        "quote_or_locator": "minimum_tick_size: Minimum tick size (price increment).",
        "candidate_observation_type": "MARKET_DATA_FIELD_LOCATOR",
    },
    {
        "route_id": "POLYMARKET_FEES",
        "platforms": ("POLYMARKET",),
        "target_field_ids": ("fee_rules", "fee_settlement_cost_field", "cashflow_pnl_semantics"),
        "official_source_class": "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS",
        "source_domain": "docs.polymarket.com",
        "source_url": "https://docs.polymarket.com/trading/fees",
        "source_title": "Fees - Polymarket Documentation",
        "officiality_route": "OFFICIAL_FEE_TICK_SETTLEMENT_DOC_DIRECT",
        "source_locator": "Fees page fee structure section",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "Fees are set by the protocol and applied at match time.",
        "candidate_observation_type": "FEE_DOC_QUOTE",
    },
    {
        "route_id": "POLYMARKET_RATE_LIMITS",
        "platforms": ("POLYMARKET",),
        "target_field_ids": ("rate_limits", "rate_limit_field"),
        "official_source_class": "OFFICIAL_API_DOCS",
        "source_domain": "docs.polymarket.com",
        "source_url": "https://docs.polymarket.com/api-reference/rate-limits",
        "source_title": "Rate Limits - Polymarket Documentation",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 205-349",
        "locator_type": "MACHINE_FIELD_LOCATOR",
        "quote_or_locator": "CLOB API General limit 9,000 req / 10s.",
        "candidate_observation_type": "RATE_LIMIT_FIELD_LOCATOR",
    },
    {
        "route_id": "POLYMARKET_ORDERBOOK",
        "platforms": ("POLYMARKET",),
        "target_field_ids": (
            "orderbook_snapshot_freshness",
            "market_data_semantics",
            "venue_api_semantics",
        ),
        "official_source_class": "OFFICIAL_API_DOCS",
        "source_domain": "docs.polymarket.com",
        "source_url": "https://docs.polymarket.com/concepts/prices-orderbook",
        "source_title": "Prices & Orderbook - Polymarket Documentation",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "Prices & Orderbook page",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "Polymarket uses a Central Limit Order Book (CLOB) for trading.",
        "candidate_observation_type": "ORDERBOOK_DOC_QUOTE",
    },
    {
        "route_id": "POLYMARKET_RESOLUTION",
        "platforms": ("POLYMARKET",),
        "target_field_ids": ("payout_rules", "settlement_rules"),
        "official_source_class": "OFFICIAL_RULEBOOKS",
        "source_domain": "docs.polymarket.com",
        "source_url": "https://docs.polymarket.com/concepts/resolution",
        "source_title": "Resolution - Polymarket Documentation",
        "officiality_route": "OFFICIAL_DOC_SITE_DIRECT",
        "source_locator": "Resolution page opening section",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "Resolution determines which outcome won.",
        "candidate_observation_type": "RESOLUTION_DOC_QUOTE",
    },
    {
        "route_id": "POLYMARKET_WEBSOCKET_MARKET",
        "platforms": ("POLYMARKET",),
        "target_field_ids": ("websocket_orderbook_event_sequencing",),
        "official_source_class": "OFFICIAL_API_DOCS",
        "source_domain": "docs.polymarket.com",
        "source_url": "https://docs.polymarket.com/market-data/websocket/market-channel",
        "source_title": "Market Channel - Polymarket Documentation",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "docs.polymarket.com llms.txt Market Channel entry",
        "locator_type": "MACHINE_FIELD_LOCATOR",
        "quote_or_locator": "Public WebSocket for real-time orderbook, price, and market lifecycle updates.",
        "candidate_observation_type": "WEBSOCKET_DOC_INDEX_LOCATOR",
    },
    {
        "route_id": "FORECASTEX_FAQ_SETTLEMENT_FEES",
        "platforms": ("FORECASTEX_IBKR",),
        "target_field_ids": (
            "fee_rules",
            "fee_settlement_cost_field",
            "payout_rules",
            "settlement_rules",
            "cashflow_pnl_semantics",
        ),
        "official_source_class": "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS",
        "source_domain": "forecastex.com",
        "source_url": "https://forecastex.com/faq",
        "source_title": "Frequently Asked Questions - ForecastEx",
        "officiality_route": "OFFICIAL_FEE_TICK_SETTLEMENT_DOC_DIRECT",
        "source_locator": "HTML lines 35-69",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "ForecastEx charges a $0.01 transaction fee per contract.",
        "candidate_observation_type": "FORECASTEX_FEE_SETTLEMENT_QUOTE",
    },
    {
        "route_id": "FORECASTEX_REGULATORY_RULEBOOK",
        "platforms": ("FORECASTEX_IBKR",),
        "target_field_ids": ("execution_lifecycle", "reconciliation_semantics"),
        "official_source_class": "OFFICIAL_RULEBOOKS",
        "source_domain": "data.forecastex.com",
        "source_url": "https://data.forecastex.com/regulatory/ForecastEx_LLC_Rulebook.pdf",
        "source_title": "ForecastEx LLC Rulebook",
        "officiality_route": "OFFICIAL_RULEBOOK_SITE_DIRECT",
        "source_locator": "PDF page 51 lines 1739-1747",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "Rebalancing will occur at 16:00 CST.",
        "candidate_observation_type": "RULEBOOK_QUOTE",
    },
    {
        "route_id": "IBKR_FORECASTEX_TWS_API",
        "platforms": ("FORECASTEX_IBKR",),
        "target_field_ids": ("venue_api_semantics", "market_data_semantics", "order_fields"),
        "official_source_class": "OFFICIAL_API_DOCS",
        "source_domain": "www.interactivebrokers.com",
        "source_url": "https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/",
        "source_title": "TWS API Documentation - IBKR API",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 4209-4212",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "The ForecastEx exchange value is always listed as FORECASTX.",
        "candidate_observation_type": "IBKR_FORECASTEX_API_QUOTE",
    },
    {
        "route_id": "IBKR_FORECASTEX_WEB_API",
        "platforms": ("FORECASTEX_IBKR",),
        "target_field_ids": ("order_type_field", "order_intent_parameter"),
        "official_source_class": "OFFICIAL_API_DOCS",
        "source_domain": "www.interactivebrokers.com",
        "source_url": "https://www.interactivebrokers.com/campus/ibkr-api-page/cpapi-v1/",
        "source_title": "Web API v1.0 Documentation - IBKR API",
        "officiality_route": "OFFICIAL_API_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 3947-3951",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "ForecastEx forecast contracts are modeled as options or futures options.",
        "candidate_observation_type": "IBKR_FORECASTEX_WEB_API_QUOTE",
    },
    {
        "route_id": "SKLEARN_GRID_SEARCH",
        "platforms": VENUE_SCOPES,
        "target_field_ids": ("grid_search_metadata", "hyperparameter_search_space"),
        "official_source_class": "OFFICIAL_PROVIDER_DOCS",
        "source_domain": "scikit-learn.org",
        "source_url": "https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html",
        "source_title": "GridSearchCV - scikit-learn documentation",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 667-687",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "Exhaustive search over specified parameter values for an estimator.",
        "candidate_observation_type": "OPTIMIZER_PROVIDER_DOC_QUOTE",
    },
    {
        "route_id": "SKLEARN_RANDOM_SEARCH",
        "platforms": VENUE_SCOPES,
        "target_field_ids": ("random_search_metadata",),
        "official_source_class": "OFFICIAL_PROVIDER_DOCS",
        "source_domain": "scikit-learn.org",
        "source_url": "https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.RandomizedSearchCV.html",
        "source_title": "RandomizedSearchCV - scikit-learn documentation",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 667-693",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "Randomized search on hyper parameters.",
        "candidate_observation_type": "OPTIMIZER_PROVIDER_DOC_QUOTE",
    },
    {
        "route_id": "SCIPY_MINIMIZE",
        "platforms": VENUE_SCOPES,
        "target_field_ids": (
            "classical_optimizer_candidate_metadata",
            "constraint_penalty_weight",
            "scoring_weight_optimization",
            "optimizer_score_input",
        ),
        "official_source_class": "OFFICIAL_PROVIDER_DOCS",
        "source_domain": "docs.scipy.org",
        "source_url": "https://docs.scipy.org/doc/scipy-1.11.2/reference/generated/scipy.optimize.minimize.html",
        "source_title": "scipy.optimize.minimize - SciPy Manual",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 37-51 and 243-312",
        "locator_type": "MACHINE_FIELD_LOCATOR",
        "quote_or_locator": "scipy.optimize.minimize(fun, x0, args=(), method=None, ...).",
        "candidate_observation_type": "OPTIMIZER_API_LOCATOR",
    },
    {
        "route_id": "IBM_QISKIT_PRIMITIVES",
        "platforms": VENUE_SCOPES,
        "target_field_ids": ("backend_provider", "simulator", "shot_count"),
        "official_source_class": "OFFICIAL_PROVIDER_DOCS",
        "source_domain": "quantum.cloud.ibm.com",
        "source_url": "https://quantum.cloud.ibm.com/docs/en/api/qiskit/primitives",
        "source_title": "Primitives - IBM Quantum Documentation",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 29-45",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "Samplers are responsible for accepting quantum circuits.",
        "candidate_observation_type": "QUANTUM_PROVIDER_DOC_QUOTE",
    },
    {
        "route_id": "IBM_QISKIT_QAOA_ANSATZ",
        "platforms": VENUE_SCOPES,
        "target_field_ids": ("qaoa_depth_class", "qaoa_mixer_ansatz"),
        "official_source_class": "OFFICIAL_PROVIDER_DOCS",
        "source_domain": "quantum.cloud.ibm.com",
        "source_url": "https://quantum.cloud.ibm.com/docs/en/api/qiskit/1.4/qiskit.circuit.library.QAOAAnsatz",
        "source_title": "QAOAAnsatz - IBM Quantum Documentation",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "source_locator": "HTML lines 26-48",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "A generalized QAOA quantum circuit with a support of custom initial states and mixers.",
        "candidate_observation_type": "QUANTUM_PROVIDER_DOC_QUOTE",
    },
    {
        "route_id": "IBM_QISKIT_LEGACY_QAOA",
        "platforms": VENUE_SCOPES,
        "target_field_ids": ("qaoa_classical_optimizer",),
        "official_source_class": "OFFICIAL_PROVIDER_DOCS",
        "source_domain": "docs.quantum.ibm.com",
        "source_url": "https://docs.quantum.ibm.com/api/qiskit/0.43/qiskit.algorithms.QAOA",
        "source_title": "QAOA - IBM Quantum Documentation",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "source_locator": "API parameter list optimizer",
        "locator_type": "MACHINE_FIELD_LOCATOR",
        "quote_or_locator": "optimizer: A classical optimizer.",
        "candidate_observation_type": "QUANTUM_PROVIDER_DOC_LOCATOR",
    },
    {
        "route_id": "D_WAVE_MODELS",
        "platforms": VENUE_SCOPES,
        "target_field_ids": ("qubo_encoding", "ising_mapping"),
        "official_source_class": "OFFICIAL_PROVIDER_DOCS",
        "source_domain": "docs.dwavequantum.com",
        "source_url": "https://docs.dwavequantum.com/en/latest/concepts/models.html",
        "source_title": "Models - D-Wave Quantum Computing Products documentation",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "source_locator": "Models page Binary Quadratic Model section",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "QUBO problems are traditionally used in computer science.",
        "candidate_observation_type": "QUANTUM_PROVIDER_DOC_QUOTE",
    },
    {
        "route_id": "D_WAVE_ANNEALING_SCHEDULE",
        "platforms": VENUE_SCOPES,
        "target_field_ids": ("annealing_schedule",),
        "official_source_class": "OFFICIAL_PROVIDER_DOCS",
        "source_domain": "docs.dwavesys.com",
        "source_url": "https://docs.dwavesys.com/docs/latest/_downloads/bc40e3beea057f01ec3800ec18029885/09-1301A-G_QPU_Properties_Advantage2_prototype2.6.pdf",
        "source_title": "QPU-Specific Physical Properties: Advantage2_prototype2.6",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "source_locator": "PDF page 4 lines 145-179",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "The standard annealing schedule for this QPU is shown in Figure 2.1.",
        "candidate_observation_type": "QUANTUM_PROVIDER_DOC_QUOTE",
    },
    {
        "route_id": "D_WAVE_MINOR_EMBEDDING",
        "platforms": VENUE_SCOPES,
        "target_field_ids": ("annealing_chain_embedding",),
        "official_source_class": "OFFICIAL_PROVIDER_DOCS",
        "source_domain": "docs.dwavequantum.com",
        "source_url": "https://docs.dwavequantum.com/en/latest/quantum_research/embedding_intro.html",
        "source_title": "Minor Embedding - D-Wave Quantum Computing Products documentation",
        "officiality_route": "OFFICIAL_PROVIDER_DOC_SITE_DIRECT",
        "source_locator": "Minor Embedding page opening section",
        "locator_type": "QUOTE_SPAN",
        "quote_or_locator": "To solve an arbitrarily structured binary quadratic model directly on a D-Wave quantum computer requires mapping.",
        "candidate_observation_type": "QUANTUM_PROVIDER_DOC_QUOTE",
    },
)

REQUIRED_REPORT_KEYS = (
    "report_id",
    "report_version",
    "pr_id",
    "pr_title",
    "authority_class",
    "readiness_class",
    "pr153_completion_status",
    "corrected_denominator_summary",
    "owner_approved_lane_routing_summary",
    "owner_global_authority_override_clarification",
    "pr153r_retry_capture_contract",
    "pr154_or_owner_override_handoff_contract",
    "owner_external_fact_boundary",
    "next_pr_path_recommendation",
    "deterministic_generation_policy",
    "upstream_artifact_inputs",
    "preflight_artifact_receipts",
    "web_capture_environment_receipt",
    "source_discovery_policy",
    "capture_batch_plan",
    "capture_batch_receipts",
    "capture_progress_ledger",
    "capture_resume_cursor",
    "capture_blocker_category_summary",
    "pr136_alignment_summary",
    "pr137r_atomicrows_reconciliation_consumption_summary",
    "pr138_atomicrows_semantic_row_contract_consumption_summary",
    "pr149_bridge_consumption_summary",
    "pr150_target_matrix_consumption_summary",
    "pr151_retrieval_target_pack_consumption_summary",
    "pr152_global_audit_consumption_summary",
    "owner_source_evidence_packet_summary",
    "controlled_capture_policy",
    "official_source_class_policy",
    "discovery_attempt_receipts",
    "official_domain_route_receipts",
    "source_capture_candidate_packets",
    "unresolved_capture_targets",
    "source_locator_index",
    "officiality_evidence_index",
    "quote_span_index",
    "machine_field_locator_index",
    "conflict_review_input_index",
    "revalidation_policy_index",
    "acceptance_readiness_index_for_PR154",
    "acceptance_handoff_contract_for_PR154",
    "owner_blocker_decision_layer",
    "atomicrows_compatibility_surface",
    "quantum_forward_capture_surface",
    "no_claim_boundary",
    "centralized_reason_codes",
    "validation_summary",
    "next_consumer_contract",
)
