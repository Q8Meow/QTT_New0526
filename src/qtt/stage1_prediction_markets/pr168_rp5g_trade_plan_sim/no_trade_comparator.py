"""No-trade comparator formulas."""

from __future__ import annotations

from decimal import Decimal

from .models import score


def compare_to_no_trade(net_expected_pnl_cash: Decimal, required_margin_cash: Decimal = Decimal("0")) -> dict[str, object]:
    margin = net_expected_pnl_cash - Decimal("0")
    no_trade_wins = margin <= required_margin_cash
    return {
        "no_trade_expected_pnl_cash": score(0),
        "candidate_minus_no_trade_cash": score(margin),
        "no_trade_margin_cash": score(margin),
        "no_trade_wins_flag": no_trade_wins,
        "candidate_beats_no_trade_flag": not no_trade_wins,
    }

