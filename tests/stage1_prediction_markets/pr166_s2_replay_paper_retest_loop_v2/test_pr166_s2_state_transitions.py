from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_state_transitions_reference_fill_or_no_fill():
    rows = assert_report_rows("PR166_S2_StateLedger.report.json", 3215)
    assert all(row["state_transition_status"].startswith("REPLAY_PAPER_STATE_UPDATED") for row in rows[:100])
    assert all(row["simulated_fill_or_no_fill_ref"].startswith("PR166_S2_") for row in rows[:100])
