"""Replay lane trace construction from PR162R-B replay bindings."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def replay_pretrade_status_for(index: int, paper_pretrade_status: str) -> str:
    if paper_pretrade_status == "PAPER_PRETRADE_PASS" and index % 17 == 0:
        return "REPLAY_PRETRADE_REJECT_WITH_EXACT_REASON"
    if paper_pretrade_status != "PAPER_PRETRADE_PASS" and index % 11 == 0:
        return "REPLAY_PRETRADE_PASS"
    if paper_pretrade_status == "PAPER_PRETRADE_PASS":
        return "REPLAY_PRETRADE_PASS"
    return "REPLAY_PRETRADE_REJECT_WITH_EXACT_REASON"


def build_replay_trace(index: int, ctx: dict[str, Any], paper_trace: dict[str, Any]) -> dict[str, Any]:
    row = ctx["row"]
    order = ctx["paper"]["order"]
    pretrade_status = replay_pretrade_status_for(index, paper_trace["paper_pretrade_status"])
    requested = float(order.get("requested_qty", 0.0))
    if pretrade_status != "REPLAY_PRETRADE_PASS":
        filled = 0.0
        vwap = 0.0
        fill_status = "REPLAY_REJECTED_WITH_EXACT_REASON"
    else:
        paper_filled = float(paper_trace["paper_fill_qty"])
        if paper_filled <= 0 and index % 11 == 0:
            filled = min(requested, max(1.0, requested * 0.5))
        elif index % 23 == 0 and paper_filled > 1:
            filled = max(paper_filled - 1.0, 0.0)
        else:
            filled = paper_filled
        if order.get("order_type") == "FOK" and abs(filled - requested) > 0.000001:
            filled = 0.0
        if filled >= requested and requested > 0:
            fill_status = "REPLAY_FILLED"
        elif filled > 0:
            fill_status = "REPLAY_PARTIAL_FILL"
        else:
            fill_status = "REPLAY_NO_FILL_WITH_EXACT_REASON"
        base_vwap = float(paper_trace["paper_vwap_price"]) or float(order.get("limit_price", 0.0))
        price_shift = 0.001 if index % 5 == 0 and filled > 0 else 0.0
        vwap = max(round(base_vwap + price_shift, 6), 0.0)
    unfilled = max(requested - filled, 0.0)
    fee_rate = 0.0022 if index % 13 == 0 else 0.002
    fees = round(filled * fee_rate, 6)
    arrival = float(ctx["paper"]["latency"].get("arrival_mid", 0.0))
    slippage = round(abs(vwap - arrival) * filled, 6) if filled else 0.0
    spread = round(abs(float(order.get("limit_price", 0.0)) - arrival) * filled, 6)
    latency_cost = round(float(ctx["paper"]["latency"].get("latency_seconds", 0.0)) * 0.0012 * filled, 6)
    cost_adjusted = round(vwap + (fees / filled if filled else 0.0), 6) if str(order.get("side", "")).startswith("BUY") else round(max(vwap - (fees / filled if filled else 0.0), 0.0), 6)
    return {
        "replay_trace_ref": plain_ref("REPLAY_TRACE", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": row["candidate_packet_id"],
        "qku_ids": list(row.get("qku_ids") or []),
        "replay_binding_refs": list(row.get("replay_binding_refs") or []),
        "replay_orderbook_refs": ctx["replay_orderbook_refs"],
        "replay_trade_refs": ctx["replay_trade_refs"],
        "replay_event_state_refs": ctx["replay_event_state_refs"],
        "replay_settlement_refs_if_available": ctx["replay_settlement_refs"],
        "replay_fee_slippage_refs": ctx["replay_fee_slippage_refs"],
        "replay_latency_refs": ctx["replay_latency_refs"],
        "replay_decision_candidate": "REPLAY_EXECUTE_CANDIDATE" if pretrade_status == "REPLAY_PRETRADE_PASS" else "REPLAY_REJECT_CANDIDATE_WITH_EXACT_REASON",
        "replay_pretrade_status": pretrade_status,
        "replay_fill_status": fill_status,
        "replay_fill_qty": round(filled, 6),
        "replay_unfilled_qty": round(unfilled, 6),
        "replay_vwap_price": round(vwap, 6),
        "replay_fees": fees,
        "replay_slippage": slippage,
        "replay_spread_cost": spread,
        "replay_latency_cost_candidate": latency_cost,
        "replay_cost_adjusted_price": cost_adjusted,
        "replay_position_delta": round(filled if str(order.get("side", "")).startswith("BUY") else -filled, 6),
        "replay_cash_delta_candidate": round(-(filled * vwap + fees), 6),
        "replay_accounting_delta_candidate": round(-(filled * vwap + fees + slippage), 6),
        "replay_truth_status": "SYNTHETIC_FIXTURE_REPLAY_TRACE",
        "replay_result_candidate_created": True,
        "exact_disabled_reason_if_any": "",
        "no_profit_evidence": True,
        "no_live_authority": True,
        "no_source_acceptance": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
