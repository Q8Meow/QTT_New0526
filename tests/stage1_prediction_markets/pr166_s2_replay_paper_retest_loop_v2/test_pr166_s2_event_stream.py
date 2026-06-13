from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_event_stream_has_ordered_replay_paper_events():
    row = assert_report_rows("PR166_S2_EventStreamLedger.report.json", 3215)[0]
    assert row["event_stream_ref"].startswith("PR166_S2_EVENT_STREAM::")
    assert row["event_sequence"] == ["DECISION", "MARKET_SNAPSHOT", "ORDER_INTENT", "FILL_OR_NO_FILL", "STATE_TRANSITION", "TCA", "NET_EDGE", "ROUTE"]
