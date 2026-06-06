"""Paper lane trace construction from PR163 capture artifacts."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def _paper_fill_status(pretrade_status: str, terminal_state: str, filled_qty: float) -> str:
    if pretrade_status != "PAPER_PRETRADE_PASS":
        return "PAPER_REJECTED_WITH_EXACT_REASON"
    if terminal_state == "FILLED":
        return "PAPER_FILLED"
    if filled_qty > 0:
        return "PAPER_PARTIAL_FILL"
    if terminal_state in {"RESTING", "CANCELLED", "EXPIRED"}:
        return f"PAPER_{terminal_state}_NO_FILL"
    return "PAPER_NO_FILL_WITH_EXACT_REASON"


def build_paper_trace(index: int, ctx: dict[str, Any]) -> dict[str, Any]:
    row = ctx["row"]
    paper = ctx["paper"]
    order = paper["order"]
    pretrade = paper["pretrade"]
    fill = paper["fill"]
    ledger = paper["ledger"]
    cost = paper["cost"]
    latency = paper["latency"]
    requested = float(order.get("requested_qty", 0.0))
    filled = float(fill.get("filled_qty", 0.0))
    unfilled = max(requested - filled, 0.0)
    terminal = str(fill.get("terminal_state") or paper.get("terminal_state") or "")
    return {
        "paper_trace_ref": plain_ref("PAPER_TRACE", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": row["candidate_packet_id"],
        "qku_ids": list(row.get("qku_ids") or []),
        "pr163_paper_adapter_input_ref": paper["adapter_input_ref"],
        "pr163_paper_decision_intent_ref": paper["decision_ref"],
        "pr163_paper_order_intent_ref": paper["order_ref"],
        "pr163_pretrade_receipt_ref": paper["pretrade_ref"],
        "pr163_state_transition_refs": list(paper.get("state_transition_refs") or []),
        "pr163_fill_event_refs": [fill["synthetic_fill_event_ref"]] if fill else [],
        "pr163_portfolio_ledger_refs": [ledger["portfolio_ledger_snapshot_ref"]],
        "pr163_cash_reservation_refs": [paper["cash_ref"]],
        "pr163_cost_receipt_refs": [cost["execution_cost_receipt_ref"]],
        "pr163_latency_slippage_refs": [latency["latency_slippage_receipt_ref"]],
        "paper_decision_candidate": paper["decision_action"],
        "paper_pretrade_status": pretrade["pretrade_status"],
        "paper_fill_status": _paper_fill_status(pretrade["pretrade_status"], terminal, filled),
        "paper_fill_qty": round(filled, 6),
        "paper_unfilled_qty": round(unfilled, 6),
        "paper_vwap_price": round(float(fill.get("vwap_fill_price", 0.0)), 6),
        "paper_fees": round(float(cost.get("total_fee", 0.0)), 6),
        "paper_slippage": round(float(latency.get("slippage_total", 0.0)), 6),
        "paper_spread_cost": round(abs(float(order.get("limit_price", 0.0)) - float(latency.get("arrival_mid", 0.0))) * filled, 6),
        "paper_latency_cost_candidate": round(float(latency.get("latency_seconds", 0.0)) * 0.001 * filled, 6),
        "paper_cost_adjusted_price": round(
            float(cost.get("cost_adjusted_buy_price") or cost.get("cost_adjusted_sell_price") or 0.0),
            6,
        ),
        "paper_position_delta": round(sum(float(pos.get("signed_filled_qty", 0.0)) for pos in ledger.get("positions", [])), 6),
        "paper_cash_delta_candidate": round(float(ledger.get("received_cash", 0.0)) - float(ledger.get("spent_cash", 0.0)), 6),
        "paper_accounting_delta_candidate": round(float(ledger.get("paper_cash_end", 0.0)) - float(ledger.get("paper_cash_start", 0.0)), 6),
        "paper_truth_status": "SYNTHETIC_FIXTURE_PAPER_TRACE",
        "paper_result_candidate_created": True,
        "no_profit_evidence": True,
        "no_live_authority": True,
        "no_source_acceptance": True,
        "no_runtime_cash_receipt": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
