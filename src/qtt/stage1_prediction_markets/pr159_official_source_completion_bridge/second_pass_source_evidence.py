"""Narrow PR159 second-pass exact source evidence.

These entries are static extracts from official sources already present in the
PR159 discovery catalog. They are intentionally limited to target fields where
the official source gives an exact field/value basis, unit/scale, locator,
freshness classification, and conflict clearance.
"""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


ExactEvidenceKey = tuple[str, str]


EXACT_SOURCE_EVIDENCE_BY_PLATFORM_FIELD: dict[ExactEvidenceKey, dict[str, Any]] = {
    (
        "FORECASTEX_IBKR",
        "rate_limit_field",
    ): {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_IBKR_WEB_API",
        "locator_type": c.LocatorType.URL_SECTION_HEADING.value,
        "locator": "Web API Documentation > Pacing Limitations",
        "quote_span": "global request rate limit of 10 requests per second",
        "accepted_value_or_range_or_enum": {
            "limit": 10,
            "unit": "requests",
            "window": "1_second",
            "scope": "IBKR Web API global request pacing",
        },
        "canonical_unit_or_basis": "requests_per_second",
        "canonical_scale": "10_requests_per_second_global_web_api",
    },
    (
        "FORECASTEX_IBKR",
        "tick_size_field",
    ): {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_IBKR_EVENT_TRADING",
        "locator_type": c.LocatorType.URL_SECTION_HEADING.value,
        "locator": "TWSAPI Methods Event Trading > ForecastEx Forecast Contracts",
        "quote_span": "Forecast Contracts are quoted in USD 0.01 increments.",
        "accepted_value_or_range_or_enum": {
            "tick_size": "0.01",
            "currency": "USD",
            "instrument_scope": "ForecastEx Forecast Contracts",
        },
        "canonical_unit_or_basis": "usd_contract_price_increment",
        "canonical_scale": "0.01_usd",
    },
    (
        "FORECASTEX_IBKR",
        "tick_rules",
    ): {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_IBKR_EVENT_TRADING",
        "locator_type": c.LocatorType.URL_SECTION_HEADING.value,
        "locator": "TWSAPI Methods Event Trading > ForecastEx Forecast Contracts",
        "quote_span": "Forecast Contracts are quoted in USD 0.01 increments.",
        "accepted_value_or_range_or_enum": {
            "tick_rule": "fixed_usd_increment",
            "tick_size": "0.01",
            "currency": "USD",
            "instrument_scope": "ForecastEx Forecast Contracts",
        },
        "canonical_unit_or_basis": "usd_contract_price_increment",
        "canonical_scale": "0.01_usd",
    },
    (
        "FORECASTEX_IBKR",
        "payout_rules",
    ): {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_IBKR_EVENT_TRADING",
        "locator_type": c.LocatorType.URL_SECTION_HEADING.value,
        "locator": "TWSAPI Methods Event Trading > ForecastEx Forecast Contracts",
        "quote_span": "Each contract pays USD 1.00 at expiry",
        "accepted_value_or_range_or_enum": {
            "payout": "1.00",
            "currency": "USD",
            "condition": "expiring_in_the_money",
            "basis": "per ForecastEx Forecast Contract",
        },
        "canonical_unit_or_basis": "usd_payout_per_in_the_money_contract",
        "canonical_scale": "1.00_usd_per_contract",
    },
    (
        "KALSHI",
        "retry_backoff_error_routing",
    ): {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_KALSHI_RATE_LIMITS",
        "locator_type": c.LocatorType.URL_QUOTE_SPAN.value,
        "locator": "Rate Limits and Tiers > When you hit the limit",
        "quote_span": "Apply exponential backoff on 429 until your bucket refills.",
        "accepted_value_or_range_or_enum": {
            "http_status": 429,
            "error": "too many requests",
            "routing": "exponential_backoff_until_bucket_refill",
            "retry_after_header": "not_currently_included",
        },
        "canonical_unit_or_basis": "http_429_exponential_backoff_until_token_bucket_refill",
        "canonical_scale": "per_authenticated_request_bucket",
    },
    (
        "KALSHI",
        "tick_size_field",
    ): {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_KALSHI_FIXED_POINT",
        "locator_type": c.LocatorType.TABLE_ROW_COLUMN.value,
        "locator": "Fixed-Point Migration > Price Level Structures table",
        "quote_span": "price_ranges array provides the exact valid price intervals and tick sizes",
        "accepted_value_or_range_or_enum": {
            "linear_cent": [{"range": "0.00-1.00", "tick_size": "0.01"}],
            "tapered_deci_cent": [
                {"range": "0.00-0.10", "tick_size": "0.001"},
                {"range": "0.10-0.90", "tick_size": "0.01"},
                {"range": "0.90-1.00", "tick_size": "0.001"},
            ],
            "deci_cent": [{"range": "0.00-1.00", "tick_size": "0.001"}],
        },
        "canonical_unit_or_basis": "fixed_point_dollar_price_tick_size",
        "canonical_scale": "market_price_level_structure_specific",
    },
    (
        "KALSHI",
        "tick_rules",
    ): {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_KALSHI_FIXED_POINT",
        "locator_type": c.LocatorType.TABLE_ROW_COLUMN.value,
        "locator": "Fixed-Point Migration > Price Level Structures table",
        "quote_span": "price_ranges array provides the exact valid price intervals and tick sizes",
        "accepted_value_or_range_or_enum": {
            "price_level_structure_field": "price_level_structure",
            "price_ranges_field": "price_ranges",
            "tick_size_basis": "per market price interval",
        },
        "canonical_unit_or_basis": "fixed_point_dollar_price_tick_rule",
        "canonical_scale": "market_price_level_structure_specific",
    },
    (
        "KALSHI",
        "payout_rules",
    ): {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_KALSHI_MARKET_SETTLEMENT",
        "locator_type": c.LocatorType.URL_SECTION_HEADING.value,
        "locator": "Market Settlement > How It Works",
        "quote_span": "Yes contract holders receive $1 per contract",
        "accepted_value_or_range_or_enum": {
            "yes_outcome_payout": "1.00",
            "no_outcome_payout": "1.00",
            "currency": "USD",
            "basis": "winning outcome holder per contract",
        },
        "canonical_unit_or_basis": "usd_payout_per_winning_yes_no_contract",
        "canonical_scale": "1.00_usd_per_contract",
    },
    (
        "KALSHI",
        "settlement_rules",
    ): {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_KALSHI_MARKET_SETTLEMENT",
        "locator_type": c.LocatorType.URL_SECTION_HEADING.value,
        "locator": "Market Settlement > How It Works",
        "quote_span": "Only net positions are settled (after netting)",
        "accepted_value_or_range_or_enum": {
            "settlement_event": "market_outcome_determined",
            "settled_position_basis": "net_positions_after_netting",
            "winning_contract_payout": "1.00_usd_per_contract",
        },
        "canonical_unit_or_basis": "net_position_settlement_basis",
        "canonical_scale": "per_market_after_outcome_determination",
    },
    (
        "POLYMARKET",
        "retry_backoff_error_routing",
    ): {
        "official_source_ref": "PR159_OFFICIAL_SOURCE_POLYMARKET_ERROR_CODES",
        "locator_type": c.LocatorType.URL_QUOTE_SPAN.value,
        "locator": "Error Codes > Status Code Reference",
        "quote_span": "implement exponential backoff",
        "accepted_value_or_range_or_enum": {
            "http_status": 429,
            "meaning": "too_many_requests",
            "routing": "implement_exponential_backoff",
        },
        "canonical_unit_or_basis": "http_429_rate_limit_exponential_backoff",
        "canonical_scale": "per_rate_limited_request",
    },
}


def exact_evidence_for_target(target: Mapping[str, Any]) -> Mapping[str, Any] | None:
    platform = str(target.get("platform_scope") or "")
    target_field_id = str(target.get("target_field_id") or "")
    evidence = EXACT_SOURCE_EVIDENCE_BY_PLATFORM_FIELD.get((platform, target_field_id))
    if evidence is None:
        return None
    return {
        **evidence,
        "freshness_state": c.FreshnessState.FRESH.value,
        "conflict_clearance_status": c.ConflictStatus.NO_CONFLICT.value,
        "acceptance_decision": c.SourceAcceptanceDecision.ACCEPTED_TARGET_FIELD_EXACT.value,
        "candidate_validation_state": c.SourceEvidenceState.CANDIDATE_PACKET_VALIDATED.value,
        "revalidation_class": target.get("revalidation_class") or c.RevalidationClass.LIVE_CRITICAL_P1D.value,
        "materiality_class": target.get("source_materiality_class")
        or c.SourceMaterialityClass.CONNECTOR_BLOCKING.value,
    }


def exact_source_ref_for(platform: str, target_field_id: str) -> str | None:
    evidence = EXACT_SOURCE_EVIDENCE_BY_PLATFORM_FIELD.get((platform, target_field_id))
    if evidence is None:
        return None
    return str(evidence["official_source_ref"])
