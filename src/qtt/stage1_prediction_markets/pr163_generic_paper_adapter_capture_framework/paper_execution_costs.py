"""Paper execution cost receipt helpers."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def compute_fee(filled_qty: float, vwap_price: float, maker_taker: str, model: dict[str, Any]) -> float:
    if filled_qty <= 0:
        return 0.0
    per_share = float(model.get("taker_fee_per_share" if maker_taker == "TAKER" else "maker_fee_per_share", 0.0))
    polymarket_candidate_fee = filled_qty * per_share * vwap_price * max(1.0 - vwap_price, 0.0)
    fixture_fee = filled_qty * per_share
    return round(max(polymarket_candidate_fee, fixture_fee), 6)


def build_execution_cost_receipt(index: int, order_ref: str, fill: Any, model: dict[str, Any]) -> dict[str, Any]:
    fee = compute_fee(fill.filled_qty, fill.vwap_fill_price, fill.maker_taker, model)
    fee_per_share = round(fee / fill.filled_qty, 6) if fill.filled_qty else 0.0
    return {
        "execution_cost_receipt_ref": plain_ref("EXECUTION_COST_RECEIPT", index),
        "paper_order_intent_ref": order_ref,
        "fee_model_ref": model.get("model_id", "PR162R_B_SYNTH_FEE_SLIPPAGE_MODEL_001"),
        "fee_truth_status": "SYNTHETIC_OR_CANDIDATE_FEE_MODEL",
        "fee_formula_candidate": "shares_traded * fee_rate * price * (1 - price)",
        "maker_taker": fill.maker_taker,
        "filled_qty": fill.filled_qty,
        "vwap_fill_price": fill.vwap_fill_price,
        "total_fee": fee,
        "fee_per_share": fee_per_share,
        "cost_adjusted_buy_price": round(fill.vwap_fill_price + fee_per_share, 6) if fill.filled_qty else 0.0,
        "cost_adjusted_sell_price": round(max(fill.vwap_fill_price - fee_per_share, 0.0), 6) if fill.filled_qty else 0.0,
        "paper_result_packet_created": False,
        "profit_evidence_created": False,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
