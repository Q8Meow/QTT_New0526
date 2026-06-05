"""Authoring-time source candidate policy rows for PR163."""

from __future__ import annotations

from .authority_policy import no_authority_fields


def build_research_queue() -> list[dict]:
    sources = [
        (
            "PR163_SOURCE_CANDIDATE::001",
            "KALSHI_PREDICTION_MARKETS",
            "OFFICIAL_SOURCE_CANDIDATE",
            "https://docs.kalshi.com/welcome",
            "REST_WebSocket_FIX_demo_rate_limit_docs_candidate",
        ),
        (
            "PR163_SOURCE_CANDIDATE::002",
            "POLYMARKET_CLOB",
            "OFFICIAL_SOURCE_CANDIDATE",
            "https://docs.polymarket.com/trading/clients/l2",
            "CLOB_order_lifecycle_GTC_GTD_FOK_FAK_post_only_candidate",
        ),
        (
            "PR163_SOURCE_CANDIDATE::003",
            "POLYMARKET_CLOB",
            "OFFICIAL_SOURCE_CANDIDATE",
            "https://docs.polymarket.us/institutional/fix-api/fix-order-entry-overview",
            "FIX_TIF_limit_market_to_limit_candidate",
        ),
        (
            "PR163_SOURCE_CANDIDATE::004",
            "FORECASTEX_IBKR_EVENT_MARKETS",
            "OFFICIAL_SOURCE_CANDIDATE",
            "https://www.interactivebrokers.com/en/pricing/commissions-events.php",
            "ForecastEx_IBKR_event_contract_fee_candidate",
        ),
        (
            "PR163_SOURCE_CANDIDATE::005",
            "LLM_REVIEW_RESEARCH",
            "RESEARCH_SOURCE_CANDIDATE",
            "https://arxiv.org/abs/2605.19337",
            "LLM_trading_agent_audit_map_future_review_candidate",
        ),
        (
            "PR163_SOURCE_CANDIDATE::006",
            "LLM_REVIEW_RESEARCH",
            "RESEARCH_SOURCE_CANDIDATE",
            "https://arxiv.org/abs/2605.28850",
            "LLM_trading_agent_risk_feedback_future_review_candidate",
        ),
    ]
    rows = []
    for candidate_id, venue, source_class, locator, target in sources:
        rows.append(
            {
                "source_candidate_ref": candidate_id,
                "venue_scope": venue,
                "source_class": source_class,
                "candidate_truth_status": source_class,
                "source_locator": locator,
                "target_field": target,
                "extraction_basis": "authoring-time candidate locator only; no runtime retrieval or source acceptance",
                "paper_allowed": True,
                "promotion_requires_later_source_acceptance": True,
                "promotion_requires_replay_paper_evidence": True,
                "validation_status": "PASS",
                **no_authority_fields(),
            }
        )
    return rows
