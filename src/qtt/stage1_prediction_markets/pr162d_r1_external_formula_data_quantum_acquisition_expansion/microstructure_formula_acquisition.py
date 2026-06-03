"""Microstructure feature formula acquisition facade."""

from __future__ import annotations

from typing import Any


def microstructure_formula_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families = {"bid_ask_spread", "yes_no_cross_spread", "orderbook_depth", "volume_weighted_price", "maker_taker_gap"}
    return [record for record in formulas if record["formula_family"] in families or record["formula_category"] == "PREDICTION_MARKET_FORMULA"][:45]
