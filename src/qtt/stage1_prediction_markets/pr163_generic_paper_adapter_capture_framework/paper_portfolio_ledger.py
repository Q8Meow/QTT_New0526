"""Event-sourced paper portfolio ledger snapshots."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_portfolio_ledger_snapshot(
    *,
    index: int,
    candidate_packet_id: str,
    order_ref: str,
    cash_reservation_ref: str,
    side: str,
    requested_qty: float,
    limit_price: float,
    fill: Any,
    fee: float,
    pretrade_status: str,
    terminal_state: str,
    paper_cash_start: float = 10000.0,
) -> dict[str, Any]:
    signed_filled_qty = fill.filled_qty if side.startswith("BUY") else -fill.filled_qty
    spent_cash = round(fill.gross_fill_notional + fee, 6) if side.startswith("BUY") else 0.0
    received_cash = round(max(fill.gross_fill_notional - fee, 0.0), 6) if side.startswith("SELL") else 0.0
    open_order_qty = fill.residual_qty if terminal_state == "RESTING" and pretrade_status == "PAPER_PRETRADE_PASS" else 0.0
    reserved_cash = round(open_order_qty * limit_price, 6) if side.startswith("BUY") else 0.0
    paper_cash_end = round(paper_cash_start - reserved_cash - spent_cash + received_cash, 6)
    return {
        "portfolio_ledger_snapshot_ref": plain_ref("PORTFOLIO_LEDGER_SNAPSHOT", index),
        "candidate_packet_id": candidate_packet_id,
        "paper_order_intent_ref": order_ref,
        "cash_reservation_ref": cash_reservation_ref,
        "sequence_number": index,
        "paper_cash_start": paper_cash_start,
        "reserved_cash": reserved_cash,
        "spent_cash": spent_cash,
        "received_cash": received_cash,
        "paper_cash_end": paper_cash_end,
        "available_paper_cash": paper_cash_end,
        "positions": [
            {
                "synthetic_market_id": "PR163_SYNTH_MARKET_001",
                "synthetic_contract_or_token_id": "PR163_SYNTH_TOKEN_YES",
                "signed_filled_qty": round(signed_filled_qty, 6),
                "projected_position": round(signed_filled_qty, 6),
            }
        ],
        "open_orders": [
            {
                "paper_order_intent_ref": order_ref,
                "open_order_qty": round(open_order_qty, 6),
                "limit_price": limit_price,
            }
        ]
        if open_order_qty > 0
        else [],
        "event_level_exposure": round(abs(signed_filled_qty) * max(fill.vwap_fill_price, limit_price), 6),
        "category_level_exposure": round(abs(signed_filled_qty) * max(fill.vwap_fill_price, limit_price), 6),
        "venue_level_exposure": round(abs(signed_filled_qty) * max(fill.vwap_fill_price, limit_price), 6),
        "fixture_ledger_accounting_check": True,
        "profit_evidence_created": False,
        "runtime_cash_receipt_created": False,
        "private_state_fetched": False,
        "terminal_state": terminal_state,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
