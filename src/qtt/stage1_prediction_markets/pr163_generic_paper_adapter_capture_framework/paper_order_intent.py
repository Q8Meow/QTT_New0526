"""PaperOrderIntentV1 construction."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def venue_for_index(index: int) -> str:
    venues = (
        "VENUE_NEUTRAL_SYNTHETIC_FIXTURE",
        "POLYMARKET_CLOB",
        "KALSHI_PREDICTION_MARKETS",
        "FORECASTEX_IBKR_EVENT_MARKETS",
    )
    return venues[(index - 1) % len(venues)]


def build_order_intent(
    *,
    index: int,
    candidate_packet_id: str,
    qku_ids: list[str],
    decision_ref: str,
    scenario: Any,
    venue_scope: str,
    market_id: str,
    contract_id: str,
    limit_price: float,
    latency_bucket: str,
    risk_policy_ref: str,
) -> dict[str, Any]:
    return {
        "paper_order_intent_ref": plain_ref("ORDER_INTENT", index),
        "decision_intent_ref": decision_ref,
        "candidate_packet_id": candidate_packet_id,
        "qku_ids": qku_ids,
        "venue_scope": venue_scope,
        "market_scope": "BINARY_EVENT_MARKET_SYNTHETIC_REPRESENTATIVE",
        "synthetic_market_id": market_id,
        "synthetic_contract_or_token_id": contract_id,
        "side": scenario.side,
        "limit_price": limit_price,
        "requested_qty": scenario.requested_qty,
        "order_type": scenario.order_type,
        "time_in_force": scenario.time_in_force,
        "post_only": scenario.post_only,
        "reduce_only_simulated": scenario.reduce_only,
        "created_at_synthetic_time": "2026-01-01T00:00:00Z",
        "latency_bucket": latency_bucket,
        "paper_portfolio_ref": "PR162R_B_PAPER_PORTFOLIO_001",
        "paper_cash_ref": "PR163_PAPER_CASH_LEDGER::SYNTHETIC_FIXTURE",
        "risk_policy_ref": risk_policy_ref,
        "no_venue_order_id": True,
        "no_live_order_authority": True,
        "no_order_submission": True,
        "llm_decision_engine_used": False,
        "llm_order_release_used": False,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
