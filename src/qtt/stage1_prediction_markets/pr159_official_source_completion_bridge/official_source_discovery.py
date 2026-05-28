"""Static PR159 official-source discovery receipts captured from this work session."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


OFFICIAL_SOURCE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_KALSHI_RATE_LIMITS",
        "platform_scope": "KALSHI",
        "source_url": "https://docs.kalshi.com/getting_started/rate_limits",
        "source_title": "Rate Limits and Tiers - API Documentation",
        "source_publisher": "Kalshi",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.URL_SECTION_HEADING.value,
        "locator": "Rate Limits and Tiers > Token-based limits",
        "quote_span": "Every authenticated request costs tokens.",
        "source_version_or_date_or_null": None,
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["rate_limit_field", "rate_limits", "retry_backoff_error_routing"],
        "canonical_unit_or_basis": "tokens_per_second_budget",
        "canonical_scale": "tier_specific_budget",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_KALSHI_MARKET_SETTLEMENT",
        "platform_scope": "KALSHI",
        "source_url": "https://docs.kalshi.com/getting_started/market_settlement",
        "source_title": "Market Settlement - API Documentation",
        "source_publisher": "Kalshi",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_FEE_TICK_SETTLEMENT_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.URL_SECTION_HEADING.value,
        "locator": "Market Settlement > How It Works",
        "quote_span": "Positions are automatically resolved and funds transferred.",
        "source_version_or_date_or_null": None,
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["payout_rules", "settlement_rules", "cashflow_pnl_semantics"],
        "canonical_unit_or_basis": "settlement_outcome_rules",
        "canonical_scale": "per_contract",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_KALSHI_CREATE_ORDER_V2",
        "platform_scope": "KALSHI",
        "source_url": "https://docs.kalshi.com/api-reference/orders/create-order-v2",
        "source_title": "Create Order (V2) - API Documentation",
        "source_publisher": "Kalshi",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.API_SCHEMA_FIELD.value,
        "locator": "Body fields: side, count, price, time_in_force",
        "quote_span": "Endpoint for submitting event-market orders using the V2 request/response shape.",
        "source_version_or_date_or_null": "legacy endpoint deprecation no earlier than 2026-05-06",
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["limit_price_field", "minimum_order_size_field", "order_entry_fields"],
        "canonical_unit_or_basis": "fixed_point_dollar_price_and_contract_count",
        "canonical_scale": "request_body_schema",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_KALSHI_FIXED_POINT",
        "platform_scope": "KALSHI",
        "source_url": "https://docs.kalshi.com/getting_started/fixed_point_migration",
        "source_title": "Fixed-Point Migration - API Documentation",
        "source_publisher": "Kalshi",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.TABLE_ROW_COLUMN.value,
        "locator": "Fixed-Point Migration > Fractional Contracts",
        "quote_span": "Minimum granularity is 0.01 contracts.",
        "source_version_or_date_or_null": "Last Updated: 2026-04-17",
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["minimum_order_size_field", "tick_size_field", "tick_rules", "parameter_range"],
        "canonical_unit_or_basis": "contracts",
        "canonical_scale": "0.01_contract_granularity",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_KALSHI_ORDERBOOK",
        "platform_scope": "KALSHI",
        "source_url": "https://docs.kalshi.com/api-reference/market/get-multiple-market-orderbooks",
        "source_title": "Get Multiple Market Orderbooks - API Documentation",
        "source_publisher": "Kalshi",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.API_SCHEMA_FIELD.value,
        "locator": "Response field: orderbook_fp.yes_dollars/no_dollars",
        "quote_span": "The order book shows all active bid orders for both yes and no sides.",
        "source_version_or_date_or_null": None,
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["orderbook_schema", "market_data_schema", "reconciliation_semantics"],
        "canonical_unit_or_basis": "fixed_point_orderbook_price_quantity_levels",
        "canonical_scale": "per_market_ticker",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_POLYMARKET_RATE_LIMITS",
        "platform_scope": "POLYMARKET",
        "source_url": "https://docs.polymarket.com/quickstart/introduction/rate-limits",
        "source_title": "Rate Limits - Polymarket Documentation",
        "source_publisher": "Polymarket",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.TABLE_ROW_COLUMN.value,
        "locator": "CLOB API rate-limit tables",
        "quote_span": "API rate limits for all Polymarket endpoints.",
        "source_version_or_date_or_null": None,
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["rate_limit_field", "rate_limits", "retry_backoff_error_routing"],
        "canonical_unit_or_basis": "requests_per_time_window",
        "canonical_scale": "endpoint_specific",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_POLYMARKET_ORDER_OVERVIEW",
        "platform_scope": "POLYMARKET",
        "source_url": "https://docs.polymarket.com/trading/orders/overview",
        "source_title": "Orders API Overview - Polymarket Documentation",
        "source_publisher": "Polymarket",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.TABLE_ROW_COLUMN.value,
        "locator": "Orders overview > Tick Sizes",
        "quote_span": "Markets have different minimum price increments.",
        "source_version_or_date_or_null": None,
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["tick_rules", "minimum_order_size_field", "order_entry_fields"],
        "canonical_unit_or_basis": "market_specific_tick_size",
        "canonical_scale": "market_object_or_sdk_field",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_POLYMARKET_ERROR_CODES",
        "platform_scope": "POLYMARKET",
        "source_url": "https://docs.polymarket.com/resources/error-codes",
        "source_title": "Error Codes - Polymarket Documentation",
        "source_publisher": "Polymarket",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.URL_QUOTE_SPAN.value,
        "locator": "Order Processing Errors",
        "quote_span": "The order size is below the market minimum.",
        "source_version_or_date_or_null": None,
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": [
            "error_reject_throttle_semantics",
            "fill_integrity",
            "minimum_order_size_field",
            "retry_backoff_error_routing",
        ],
        "canonical_unit_or_basis": "clob_error_message_semantics",
        "canonical_scale": "per_order_response",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_IBKR_EVENT_TRADING",
        "platform_scope": "FORECASTEX_IBKR",
        "source_url": "https://www.interactivebrokers.com/campus/ibkr-api-page/event-trading/",
        "source_title": "TWSAPI Methods Event Trading | IBKR API | IBKR Campus",
        "source_publisher": "Interactive Brokers",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.URL_SECTION_HEADING.value,
        "locator": "ForecastEx Forecast Contracts",
        "quote_span": "Forecast Contracts are quoted in USD 0.01 increments.",
        "source_version_or_date_or_null": "Published: 2025-03-19",
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["limit_price_field", "tick_rules", "payout_rules", "execution_lifecycle"],
        "canonical_unit_or_basis": "usd_contract_price_increment",
        "canonical_scale": "0.01_usd",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_IBKR_WEB_API",
        "platform_scope": "FORECASTEX_IBKR",
        "source_url": "https://www.interactivebrokers.com/campus/ibkr-api-page/webapi-doc/",
        "source_title": "Web API Documentation | IBKR API | IBKR Campus",
        "source_publisher": "Interactive Brokers",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.URL_SECTION_HEADING.value,
        "locator": "Pacing Limitations; Top-of-Book Snapshots",
        "quote_span": "Interactive Brokers currently enforces a global request rate limit of 10 requests per second.",
        "source_version_or_date_or_null": None,
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["rate_limit_field", "rate_limits", "orderbook_snapshot_freshness", "market_data_schema"],
        "canonical_unit_or_basis": "requests_per_second_and_snapshot_fields",
        "canonical_scale": "authenticated_session",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_FORECASTEX_RULEBOOK",
        "platform_scope": "FORECASTEX_IBKR",
        "source_url": "https://data.forecastex.com/regulatory/ForecastEx_LLC_Rulebook.pdf",
        "source_title": "ForecastEx LLC Rulebook",
        "source_publisher": "ForecastEx LLC",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_RULEBOOKS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.PDF_PAGE_SECTION.value,
        "locator": "PDF page 7, defined terms: Settlement and Settlement Value",
        "quote_span": "Settlement Value - The value of an Event Question at Resolution Time.",
        "source_version_or_date_or_null": None,
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["settlement_rules", "payout_rules", "reconciliation_semantics"],
        "canonical_unit_or_basis": "rulebook_defined_settlement_terms",
        "canonical_scale": "event_question_resolution",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_DWAVE_QUBO_ISING",
        "platform_scope": "QUANTUM_PROVIDER",
        "source_url": "https://docs.dwavequantum.com/en/latest/quantum_research/qubo_ising.html",
        "source_title": "QUBOs and Ising Models - D-Wave Quantum Computing Products documentation",
        "source_publisher": "D-Wave",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_QUANTUM_PROVIDER_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.URL_SECTION_HEADING.value,
        "locator": "QUBOs and Ising Models > Binary Quadratic Models",
        "quote_span": "For the QPU, two formulations for objective functions are the Ising Model and QUBO.",
        "source_version_or_date_or_null": None,
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["quantum_provider_metadata", "qubo_ising_compatibility"],
        "canonical_unit_or_basis": "metadata_only",
        "canonical_scale": "not_execution_authority",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_AWS_BRAKET",
        "platform_scope": "QUANTUM_PROVIDER",
        "source_url": "https://docs.aws.amazon.com/braket/",
        "source_title": "Amazon Braket Documentation",
        "source_publisher": "Amazon Web Services",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_QUANTUM_PROVIDER_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.URL_SECTION_HEADING.value,
        "locator": "Amazon Braket Documentation landing page",
        "quote_span": "Amazon Braket is a fully managed service.",
        "source_version_or_date_or_null": None,
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["quantum_provider_metadata", "backend_options"],
        "canonical_unit_or_basis": "metadata_only",
        "canonical_scale": "not_execution_authority",
    },
    {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_IBM_QISKIT_QAOA",
        "platform_scope": "QUANTUM_PROVIDER",
        "source_url": "https://quantum.cloud.ibm.com/docs/api/qiskit/0.46/qiskit.algorithms.minimum_eigensolvers.QAOA",
        "source_title": "QAOA - IBM Quantum Documentation",
        "source_publisher": "IBM Quantum",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_QUANTUM_PROVIDER_DOCS.value,
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
        "locator_type": c.LocatorType.SDK_REFERENCE_FIELD.value,
        "locator": "QAOA class reference",
        "quote_span": "The Quantum Approximate Optimization Algorithm (QAOA).",
        "source_version_or_date_or_null": "Qiskit API v0.46 reference",
        "freshness_state": c.FreshnessState.FRESH.value,
        "field_classes": ["quantum_provider_metadata", "qaoa_compatibility"],
        "canonical_unit_or_basis": "metadata_only",
        "canonical_scale": "not_execution_authority",
    },
)


NON_AUTHORITATIVE_REJECTIONS: tuple[dict[str, Any], ...] = (
    {
        "seed_ref": "PR159_NONAUTH_REJECTION_REDDIT_IBKR_API_RATE_LIMIT_DISCUSSION",
        "source_url": "https://www.reddit.com/",
        "source_class": c.NonAuthoritativeSourceClass.FORUM.value,
        "rejection_decision": c.SourceAcceptanceDecision.REJECTED_NOT_OFFICIAL.value,
        "reason": "Forum result may seed official-source search only and cannot authorize QTT facts.",
    },
    {
        "seed_ref": "PR159_NONAUTH_REJECTION_REDDIT_POLYMARKET_TICK_SIZE_DISCUSSION",
        "source_url": "https://www.reddit.com/",
        "source_class": c.NonAuthoritativeSourceClass.FORUM.value,
        "rejection_decision": c.SourceAcceptanceDecision.REJECTED_NOT_OFFICIAL.value,
        "reason": "Social/forum result rejected as source evidence; official Polymarket docs used instead.",
    },
    {
        "seed_ref": "PR159_NONAUTH_REJECTION_ARXIV_POLYMARKET_MICROSTRUCTURE",
        "source_url": "https://arxiv.org/",
        "source_class": c.NonAuthoritativeSourceClass.RESEARCH_NOTE.value,
        "rejection_decision": c.SourceAcceptanceDecision.REJECTED_NOT_OFFICIAL.value,
        "reason": "Research paper cannot authorize venue semantics for PR159 target fields.",
    },
    {
        "seed_ref": "PR159_NONAUTH_REJECTION_WIKIPEDIA_QISKIT",
        "source_url": "https://en.wikipedia.org/wiki/Qiskit",
        "source_class": c.NonAuthoritativeSourceClass.UNKNOWN_NON_OFFICIAL.value,
        "rejection_decision": c.SourceAcceptanceDecision.REJECTED_NOT_OFFICIAL.value,
        "reason": "Encyclopedic page rejected; IBM Quantum documentation used for metadata discovery.",
    },
)


AMBIGUOUS_OFFICIAL_DISCOVERY: tuple[dict[str, Any], ...] = (
    {
        "classifier_record_id": "PR159_AMBIGUOUS_OFFICIAL_POLYMARKET_US_SCOPE_BLOCK",
        "source_url": "https://docs.polymarket.us/",
        "source_title": "Polymarket US Documentation",
        "publisher": "Polymarket US",
        "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_AMBIGUOUS_BLOCKED.value,
        "blocked_reason": "Different venue scope than PR159 POLYMARKET target population; no target-field authority created.",
    },
)


SEARCH_RECEIPTS: tuple[dict[str, Any], ...] = (
    {
        "search_receipt_id": "PR159_SEARCH_KALSHI_DOCS",
        "query": "site:docs.kalshi.com rate limits create order v2 fixed point migration Kalshi API docs",
        "official_domains_targeted": ["docs.kalshi.com"],
        "retrieval_timestamp_utc": c.OFFICIAL_SEARCH_RETRIEVAL_TIMESTAMP_UTC,
        "result_refs": [
            "PR159_OFFICIAL_SOURCE_KALSHI_RATE_LIMITS",
            "PR159_OFFICIAL_SOURCE_KALSHI_CREATE_ORDER_V2",
            "PR159_OFFICIAL_SOURCE_KALSHI_FIXED_POINT",
            "PR159_OFFICIAL_SOURCE_KALSHI_ORDERBOOK",
            "PR159_OFFICIAL_SOURCE_KALSHI_MARKET_SETTLEMENT",
        ],
        "accepted_fact_created": False,
    },
    {
        "search_receipt_id": "PR159_SEARCH_POLYMARKET_DOCS",
        "query": "Polymarket docs order lifecycle tick size minimum order size rate limits official docs",
        "official_domains_targeted": ["docs.polymarket.com"],
        "retrieval_timestamp_utc": c.OFFICIAL_SEARCH_RETRIEVAL_TIMESTAMP_UTC,
        "result_refs": [
            "PR159_OFFICIAL_SOURCE_POLYMARKET_RATE_LIMITS",
            "PR159_OFFICIAL_SOURCE_POLYMARKET_ORDER_OVERVIEW",
            "PR159_OFFICIAL_SOURCE_POLYMARKET_ERROR_CODES",
        ],
        "accepted_fact_created": False,
    },
    {
        "search_receipt_id": "PR159_SEARCH_FORECASTEX_IBKR_DOCS",
        "query": "Interactive Brokers API event trading order types rate limits official docs ForecastEx rulebook",
        "official_domains_targeted": ["interactivebrokers.com", "data.forecastex.com"],
        "retrieval_timestamp_utc": c.OFFICIAL_SEARCH_RETRIEVAL_TIMESTAMP_UTC,
        "result_refs": [
            "PR159_OFFICIAL_SOURCE_IBKR_EVENT_TRADING",
            "PR159_OFFICIAL_SOURCE_IBKR_WEB_API",
            "PR159_OFFICIAL_SOURCE_FORECASTEX_RULEBOOK",
        ],
        "accepted_fact_created": False,
    },
    {
        "search_receipt_id": "PR159_SEARCH_QUANTUM_PROVIDER_DOCS",
        "query": "official quantum provider documentation QUBO Ising QAOA Braket",
        "official_domains_targeted": [
            "docs.dwavequantum.com",
            "docs.aws.amazon.com",
            "quantum.cloud.ibm.com",
        ],
        "retrieval_timestamp_utc": c.OFFICIAL_SEARCH_RETRIEVAL_TIMESTAMP_UTC,
        "result_refs": [
            "PR159_OFFICIAL_SOURCE_DWAVE_QUBO_ISING",
            "PR159_OFFICIAL_SOURCE_AWS_BRAKET",
            "PR159_OFFICIAL_SOURCE_IBM_QISKIT_QAOA",
        ],
        "accepted_fact_created": False,
    },
)


def official_source_by_ref() -> dict[str, Mapping[str, Any]]:
    return {item["official_source_ref"]: item for item in OFFICIAL_SOURCE_CATALOG}


def candidate_sources_for(platform: str, field_name: str) -> list[Mapping[str, Any]]:
    field = field_name.lower()
    matches: list[Mapping[str, Any]] = []
    for source in OFFICIAL_SOURCE_CATALOG:
        if platform and source["platform_scope"] not in {platform, "QUANTUM_PROVIDER"}:
            continue
        if any(str(field_class).lower() in field or field in str(field_class).lower() for field_class in source["field_classes"]):
            matches.append(source)
    if matches:
        return matches[:2]
    return [source for source in OFFICIAL_SOURCE_CATALOG if source["platform_scope"] == platform][:1]


def official_domain_records() -> list[dict[str, Any]]:
    domains: dict[str, dict[str, Any]] = {}
    for source in OFFICIAL_SOURCE_CATALOG:
        domain = source["source_url"].split("/")[2]
        domains.setdefault(
            domain,
            {
                "domain": domain,
                "official_source_refs": [],
                "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
                "officialness_basis": "Official documentation publisher and page context captured in PR159 online search session.",
                "accepted_fact_created": False,
            },
        )
        domains[domain]["official_source_refs"].append(source["official_source_ref"])
    return [
        {**record, "official_source_refs": sorted(record["official_source_refs"])}
        for record in sorted(domains.values(), key=lambda item: item["domain"])
    ]
