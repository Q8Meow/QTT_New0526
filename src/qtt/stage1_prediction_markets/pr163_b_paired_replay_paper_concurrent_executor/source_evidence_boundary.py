"""Source-evidence boundary and source-scout queue rows."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


AUTHORING_TIME_SOURCE_SCOUTS: tuple[dict[str, str], ...] = (
    {
        "source_url": "https://help.kalshi.com/kalshi-api",
        "source_label": "Kalshi API help center",
        "source_category": "OFFICIAL_VENUE_DOCS_CANDIDATE",
        "candidate_use": "market data, orderbook, orders, trades, portfolio, public exchange information locator",
    },
    {
        "source_url": "https://docs.kalshi.com/python-sdk/api/MarketsApi",
        "source_label": "Kalshi Markets API docs",
        "source_category": "OFFICIAL_VENUE_DOCS_CANDIDATE",
        "candidate_use": "orderbook and market endpoint locator",
    },
    {
        "source_url": "https://kalshi.com/docs/kalshi-fee-schedule.pdf",
        "source_label": "Kalshi fee schedule",
        "source_category": "OFFICIAL_FEE_DOC_CANDIDATE",
        "candidate_use": "fee source-scout locator only; no accepted fee truth in PR163-B",
    },
    {
        "source_url": "https://docs.polymarket.com/developers/CLOB/trades/trades-data-api",
        "source_label": "Polymarket CLOB trades data API",
        "source_category": "OFFICIAL_VENUE_DOCS_CANDIDATE",
        "candidate_use": "CLOB trade and market data locator",
    },
    {
        "source_url": "https://docs.polymarket.us/api-reference/orders/overview",
        "source_label": "Polymarket US orders API overview",
        "source_category": "OFFICIAL_VENUE_DOCS_CANDIDATE",
        "candidate_use": "order lifecycle and private order stream locator",
    },
    {
        "source_url": "https://www.interactivebrokers.com/en/index.php?f=24356",
        "source_label": "IBKR API developer documentation",
        "source_category": "OFFICIAL_BROKER_DOCS_CANDIDATE",
        "candidate_use": "Web API, TWS API, FIX, market data, and order type locator",
    },
    {
        "source_url": "https://interactivebrokers.github.io/tws-api/basic_orders.html",
        "source_label": "IBKR TWS basic orders docs",
        "source_category": "OFFICIAL_BROKER_DOCS_CANDIDATE",
        "candidate_use": "order type locator for later accepted-source PR",
    },
    {
        "source_url": "https://arxiv.org/abs/2602.00133",
        "source_label": "PredictionMarketBench deterministic event-driven replay paper",
        "source_category": "RESEARCH_SOURCE_CANDIDATE",
        "candidate_use": "event-driven replay, orderbook/trade/lifecycle/settlement simulation locator",
    },
    {
        "source_url": "https://arxiv.org/abs/1901.02327",
        "source_label": "Optimal VWAP execution under transient price impact",
        "source_category": "EXECUTION_RESEARCH_CANDIDATE",
        "candidate_use": "VWAP and market-impact research locator",
    },
    {
        "source_url": "https://www.cis.upenn.edu/~mkearns/finread/impshort.pdf",
        "source_label": "Implementation Shortfall reference",
        "source_category": "EXECUTION_RESEARCH_CANDIDATE",
        "candidate_use": "implementation shortfall benchmark locator",
    },
)


def build_source_queue() -> list[dict[str, Any]]:
    rows = []
    for idx, source in enumerate(AUTHORING_TIME_SOURCE_SCOUTS, 1):
        rows.append(
            {
                "source_candidate_ref": plain_ref("SOURCE_SCOUT", idx),
                **source,
                "candidate_truth_status": "SOURCE_SCOUT_LOCATOR_ONLY_NOT_ACCEPTED_TRUTH",
                "source_accepted": False,
                "connector_semantics_unlocked": False,
                "runtime_retrieval_allowed": False,
                "validation_status": "PASS",
                **no_authority_fields(),
            }
        )
    return rows


def build_boundary_audit() -> dict[str, Any]:
    return {
        "source_evidence_boundary_ref": plain_ref("SOURCE_BOUNDARY", 1),
        "owner_definitions_consumed_as_policy_only": True,
        "owner_definitions_treated_as_external_fact_authority": False,
        "retrieval_target_readiness_treated_as_accepted_source_fact": False,
        "candidate_source_packet_unlocks_connector_semantics": False,
        "polymarket_mechanics_applied_to_other_venues_as_accepted_fact": False,
        "fee_tick_order_field_values_promoted_to_accepted_truth": False,
        "source_acceptance_count": 0,
        "connector_binding_count": 0,
        "source_evidence_boundary_violation_count": 0,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
