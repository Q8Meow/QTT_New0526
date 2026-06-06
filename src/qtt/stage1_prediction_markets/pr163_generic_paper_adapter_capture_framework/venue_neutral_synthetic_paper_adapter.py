"""Venue-neutral synthetic fixture adapter capability declarations."""

from __future__ import annotations

from .paper_adapter_interface import capability_row


def build_capability_row(index: int = 4) -> dict:
    return capability_row(
        index,
        "VENUE_NEUTRAL_SYNTHETIC_FIXTURE",
        [
            "deterministic_orderbook",
            "deterministic_trade_timeline",
            "deterministic_event_lifecycle",
            "synthetic_fee_slippage_latency",
            "paper_portfolio_cash_open_orders",
            "synthetic_fill_events",
            "quantum_objective_fixtures",
        ],
        [
            "tests/fixtures/stage1_prediction_markets/pr162r_b_replay_paper_data_binding_completion/",
        ],
    )
