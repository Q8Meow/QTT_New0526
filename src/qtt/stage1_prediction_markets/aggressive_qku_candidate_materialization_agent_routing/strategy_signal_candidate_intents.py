"""Strategy signal candidate intent helpers."""

from __future__ import annotations


def strategy_signal_candidate_intents(routes):
    return [
        {
            "qku_id": record["qku_id"],
            "route_ref": record["route_id"],
            "candidate_trade_intent_only_flag": True,
            "order_authority_flag": False,
            "live_order_authority": False,
        }
        for record in routes
    ]
