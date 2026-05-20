from __future__ import annotations

from typing import Any

from src.qtt.source_evidence.execution_lifecycle.phases import (
    GENERIC_FIXTURE_PHASE_FAMILIES,
)
from src.qtt.source_evidence.execution_lifecycle.transitions import (
    GENERIC_FIXTURE_TRANSITION_FAMILIES,
)


DETERMINISTIC_FIXTURE_TIME = "2026-05-19T00:00:00Z"
FIXTURE_AUTHORITY_CLASS = "TEST_FIXTURE_NOT_EXTERNAL_FACT"
NOT_ARBITRAGE_AUTHORITY = "NOT_ARBITRAGE_AUTHORITY"

ACTIVE_STAGE1_VENUES: tuple[str, ...] = (
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
)
SHARED_SCOPE_METADATA_VENUES: tuple[str, ...] = ("PREDICTION_MARKETS_GENERAL",)

READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION = (
    "READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION"
)
REJECTED_MISSING_PER_VENUE_LIFECYCLE_MODEL = (
    "REJECTED_MISSING_PER_VENUE_LIFECYCLE_MODEL"
)
REJECTED_MISSING_PR127_HANDOFF = "REJECTED_MISSING_PR127_HANDOFF"
REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE = (
    "REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE"
)
REJECTED_STALE_ACCEPTED_PACKET = "REJECTED_STALE_ACCEPTED_PACKET"
REJECTED_SUPERSEDED_ACCEPTED_PACKET = "REJECTED_SUPERSEDED_ACCEPTED_PACKET"
REJECTED_REVALIDATION_REQUIRED = "REJECTED_REVALIDATION_REQUIRED"
REJECTED_CONNECTOR_BLOCKING_MATERIALITY = (
    "REJECTED_CONNECTOR_BLOCKING_MATERIALITY"
)
REJECTED_TRADING_BLOCKING_MATERIALITY = "REJECTED_TRADING_BLOCKING_MATERIALITY"
REJECTED_SCOPE_OR_VENUE_MISMATCH = "REJECTED_SCOPE_OR_VENUE_MISMATCH"
REJECTED_MISSING_PHASE_MAPPING = "REJECTED_MISSING_PHASE_MAPPING"
REJECTED_MISSING_TRANSITION_MAPPING = "REJECTED_MISSING_TRANSITION_MAPPING"
REJECTED_MISSING_FILL_INTEGRITY_NORMALIZATION_SUPPORT = (
    "REJECTED_MISSING_FILL_INTEGRITY_NORMALIZATION_SUPPORT"
)
REJECTED_MISSING_CASHFLOW_PNL_NORMALIZATION_SUPPORT = (
    "REJECTED_MISSING_CASHFLOW_PNL_NORMALIZATION_SUPPORT"
)
REJECTED_MISSING_LATENCY_COMPONENT_NORMALIZATION_SUPPORT = (
    "REJECTED_MISSING_LATENCY_COMPONENT_NORMALIZATION_SUPPORT"
)
REJECTED_MISSING_SETTLEMENT_FINALITY_NORMALIZATION_SUPPORT = (
    "REJECTED_MISSING_SETTLEMENT_FINALITY_NORMALIZATION_SUPPORT"
)
REJECTED_MISSING_RECONCILIATION_NORMALIZATION_SUPPORT = (
    "REJECTED_MISSING_RECONCILIATION_NORMALIZATION_SUPPORT"
)

NORMALIZATION_STATES: tuple[str, ...] = (
    READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION,
    REJECTED_MISSING_PER_VENUE_LIFECYCLE_MODEL,
    REJECTED_MISSING_PR127_HANDOFF,
    REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE,
    REJECTED_STALE_ACCEPTED_PACKET,
    REJECTED_SUPERSEDED_ACCEPTED_PACKET,
    REJECTED_REVALIDATION_REQUIRED,
    REJECTED_CONNECTOR_BLOCKING_MATERIALITY,
    REJECTED_TRADING_BLOCKING_MATERIALITY,
    REJECTED_SCOPE_OR_VENUE_MISMATCH,
    REJECTED_MISSING_PHASE_MAPPING,
    REJECTED_MISSING_TRANSITION_MAPPING,
    REJECTED_MISSING_FILL_INTEGRITY_NORMALIZATION_SUPPORT,
    REJECTED_MISSING_CASHFLOW_PNL_NORMALIZATION_SUPPORT,
    REJECTED_MISSING_LATENCY_COMPONENT_NORMALIZATION_SUPPORT,
    REJECTED_MISSING_SETTLEMENT_FINALITY_NORMALIZATION_SUPPORT,
    REJECTED_MISSING_RECONCILIATION_NORMALIZATION_SUPPORT,
)

REQUIRED_PLACEHOLDER_DIMENSIONS: tuple[str, ...] = (
    "fill_integrity",
    "cashflow_pnl",
    "latency_component",
    "settlement_finality",
    "reconciliation",
)

PLACEHOLDER_REJECTION_STATE_BY_DIMENSION = {
    "fill_integrity": REJECTED_MISSING_FILL_INTEGRITY_NORMALIZATION_SUPPORT,
    "cashflow_pnl": REJECTED_MISSING_CASHFLOW_PNL_NORMALIZATION_SUPPORT,
    "latency_component": REJECTED_MISSING_LATENCY_COMPONENT_NORMALIZATION_SUPPORT,
    "settlement_finality": REJECTED_MISSING_SETTLEMENT_FINALITY_NORMALIZATION_SUPPORT,
    "reconciliation": REJECTED_MISSING_RECONCILIATION_NORMALIZATION_SUPPORT,
}

REQUIRED_NORMALIZATION_DIMENSIONS: tuple[str, ...] = (
    "execution_phase_taxonomy",
    "execution_transition_taxonomy",
    "fill_integrity_taxonomy",
    "cashflow_pnl_taxonomy",
    "latency_component_taxonomy",
    "settlement_finality_taxonomy",
    "reconciliation_taxonomy",
    "order_state_taxonomy",
    "cancellation_state_taxonomy",
    "partial_fill_state_taxonomy",
    "rejection_error_taxonomy",
)

FUTURE_PR_MAPPING = {
    "runtime_cash_component_field_map_future_pr": "PR111",
    "private_state_read_receipt_future_pr": "PR112",
    "credential_alias_secret_no_capture_future_pr": "PR113",
    "market_data_ingest_future_pr": "PR114",
    "orderbook_event_snapshot_future_pr": "PR115",
    "runtime_resolver_snapshot_future_pr": "PR116",
}

REQUIRED_FUTURE_PRS: tuple[str, ...] = (
    "PR111",
    "PR112",
    "PR113",
    "PR114",
    "PR115",
    "PR116",
)

AUTHORITY_FALSE_FLAGS: tuple[str, ...] = (
    "production_connector_use_allowed_flag",
    "order_execution_allowed_flag",
    "order_routing_authority_allowed_flag",
    "network_io_allowed_flag",
    "runtime_cash_receipt_allowed_flag",
    "private_state_fetch_allowed_flag",
    "replay_paper_execution_allowed_flag",
    "runtime_resolver_snapshot_creation_allowed_flag",
)


def false_authority_flags() -> dict[str, bool]:
    return {field: False for field in AUTHORITY_FALSE_FLAGS}


def build_taxonomy_record() -> dict[str, Any]:
    transition_families = [
        transition_family
        for transition_family, _from_phase, _to_phase in GENERIC_FIXTURE_TRANSITION_FAMILIES
    ]
    return {
        "cross_venue_execution_normalization_taxonomy_id": (
            "PR128_CROSS_VENUE_EXECUTION_NORMALIZATION_TAXONOMY_FIXTURE_V1"
        ),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "taxonomy_authority_class": FIXTURE_AUTHORITY_CLASS,
        "taxonomy_scope": "QTT_PR128_FIXTURE_SCOPE_NOT_EXTERNAL_FACT",
        "production_cross_venue_normalization_authority": False,
        "production_arbitrage_comparability_authority": False,
        "production_order_authority": False,
        "venue_ids_in_scope": list(ACTIVE_STAGE1_VENUES),
        "shared_scope_metadata_ids": list(SHARED_SCOPE_METADATA_VENUES),
        "execution_phase_taxonomy": list(GENERIC_FIXTURE_PHASE_FAMILIES),
        "execution_transition_taxonomy": transition_families,
        "fill_integrity_taxonomy": ["FILL_INTEGRITY_PLACEHOLDER_REQUIRES_ACCEPTED_SOURCE"],
        "cashflow_pnl_taxonomy": ["CASHFLOW_PNL_PLACEHOLDER_REQUIRES_PR111_RECEIPTS"],
        "latency_component_taxonomy": ["LATENCY_COMPONENT_PLACEHOLDER_REQUIRES_FUTURE_SOURCE"],
        "settlement_finality_taxonomy": [
            "SETTLEMENT_FINALITY_PLACEHOLDER_REQUIRES_FUTURE_SOURCE"
        ],
        "reconciliation_taxonomy": [
            "RECONCILIATION_PLACEHOLDER_REQUIRES_FUTURE_RECEIPTS"
        ],
        "order_state_taxonomy": ["ORDER_STATE_PLACEHOLDER_NOT_VENUE_FACT"],
        "cancellation_state_taxonomy": [
            "CANCELLATION_STATE_PLACEHOLDER_NOT_VENUE_FACT"
        ],
        "partial_fill_state_taxonomy": [
            "PARTIAL_FILL_STATE_PLACEHOLDER_NOT_VENUE_FACT"
        ],
        "rejection_error_taxonomy": ["REJECTION_ERROR_PLACEHOLDER_NOT_VENUE_FACT"],
        "normalization_state": READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "future_production_launch_path_preserved": True,
    }
