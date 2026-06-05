"""Polymarket CLOB paper adapter capability declarations."""

from __future__ import annotations

from .paper_adapter_interface import capability_row


def build_capability_row(index: int = 2) -> dict:
    return capability_row(
        index,
        "POLYMARKET_CLOB",
        [
            "CLOB_orderbook_fields",
            "condition_token_id_candidate_fields",
            "GTC_GTD_FOK_FAK_post_only_semantics",
            "maker_taker_classification",
            "candidate_fee_formula_lane",
            "no_wallet_signature_private_key",
            "no_CLOB_submission",
        ],
        [
            "https://docs.polymarket.com/trading/clients/l2",
            "https://docs.polymarket.us/institutional/fix-api/fix-order-entry-overview",
        ],
    )
