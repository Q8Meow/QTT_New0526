"""Interpret-back maps for future QOPT1 consumers."""

from __future__ import annotations


def interpret_back(candidate: dict) -> dict[str, object]:
    return {
        "trade_seed_id": candidate["trade_seed_id"],
        "target_id": candidate["target_id"],
        "grid_id": candidate["grid_id"],
        "stack_preview_refs": candidate.get("formula_stack_preview_refs", []),
        "side": candidate["side"],
        "entry_price_domain": candidate["entry_price_candidate"],
        "size_domain": candidate["order_size_candidate"],
        "hold_duration_domain": candidate["hold_duration_candidate"],
        "exit_rule_domain": candidate["exit_rule_candidate"],
        "maker_taker_split_domain": candidate["maker_taker_split_candidate"],
        "cancel_replace_domain": candidate["cancel_replace_interval_candidate"],
        "portfolio_exposure_domain": candidate["portfolio_exposure_candidate"],
        "no_trade_selected_flag": False,
    }

