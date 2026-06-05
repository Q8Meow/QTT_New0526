"""Paper latency and slippage receipt helpers."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_latency_slippage_receipt(index: int, order_ref: str, side: str, fill: Any, latency_row: dict[str, Any]) -> dict[str, Any]:
    if fill.filled_qty <= 0:
        slippage = 0.0
    elif side.startswith("BUY"):
        slippage = max(0.0, fill.vwap_fill_price - fill.arrival_mid)
    else:
        slippage = max(0.0, fill.arrival_mid - fill.vwap_fill_price)
    return {
        "latency_slippage_receipt_ref": plain_ref("LATENCY_SLIPPAGE_RECEIPT", index),
        "paper_order_intent_ref": order_ref,
        "latency_bucket": latency_row.get("latency_bucket", "LOW"),
        "latency_seconds": float(latency_row.get("latency_seconds", 0.02)),
        "selected_snapshot_ref": fill.selected_snapshot_ref,
        "latency_data_quality": "SYNTHETIC_FIXTURE_BOUND",
        "arrival_mid": fill.arrival_mid,
        "vwap_fill_price": fill.vwap_fill_price,
        "slippage_per_share": round(slippage, 6),
        "slippage_total": round(slippage * fill.filled_qty, 6),
        "slippage_convention": "BUY_MAX_0_VWAP_MINUS_ARRIVAL_MID_SELL_MAX_0_ARRIVAL_MID_MINUS_VWAP",
        "latency_receipt_truth_status": "SYNTHETIC_OR_CANDIDATE_PAPER_CAPTURE",
        "validation_status": "PASS",
        **no_authority_fields(),
    }
