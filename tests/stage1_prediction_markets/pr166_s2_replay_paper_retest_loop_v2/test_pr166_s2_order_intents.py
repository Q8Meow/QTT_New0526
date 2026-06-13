from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_order_intents_are_nonlive_and_fill_model_ready():
    rows = assert_report_rows("PR166_S2_OrderIntentLedger.report.json", 3215)
    assert all(row["simulated_order_authority"] == "NONLIVE_REPLAY_PAPER_ONLY" for row in rows[:100])
    assert all(row["live_order_authority_allowed"] is False for row in rows[:100])
    assert all(row["expected_fill_probability"] >= 0 for row in rows[:100])
