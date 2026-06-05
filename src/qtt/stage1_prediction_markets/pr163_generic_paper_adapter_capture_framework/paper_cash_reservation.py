"""Paper cash reservation receipts."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def estimate_required_cash(side: str, limit_price: float, requested_qty: float, estimated_fee: float, slippage_buffer: float) -> float:
    if side.startswith("SELL"):
        return 0.0
    return round(limit_price * requested_qty + estimated_fee + slippage_buffer, 6)


def build_cash_reservation_receipt(
    index: int,
    order_ref: str,
    side: str,
    limit_price: float,
    requested_qty: float,
    paper_cash: float,
    estimated_fee: float,
    slippage_buffer: float,
    pretrade_status: str,
) -> dict[str, Any]:
    required = estimate_required_cash(side, limit_price, requested_qty, estimated_fee, slippage_buffer)
    reserved_after = required if pretrade_status == "PAPER_PRETRADE_PASS" else 0.0
    available_after = round(paper_cash - reserved_after, 6)
    return {
        "cash_reservation_receipt_ref": plain_ref("CASH_RESERVATION_RECEIPT", index),
        "paper_order_intent_ref": order_ref,
        "paper_cash_before": round(paper_cash, 6),
        "reserved_cash_before": 0.0,
        "buy_required_cash": required,
        "estimated_fee": estimated_fee,
        "slippage_buffer": slippage_buffer,
        "reserved_cash_after": round(reserved_after, 6),
        "available_cash_after": available_after,
        "reservation_status": "PAPER_CASH_RESERVED" if pretrade_status == "PAPER_PRETRADE_PASS" else "PAPER_CASH_NOT_RESERVED_REJECTED_OR_HELD",
        "runtime_cash_receipt_created": False,
        "private_state_fetched": False,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
