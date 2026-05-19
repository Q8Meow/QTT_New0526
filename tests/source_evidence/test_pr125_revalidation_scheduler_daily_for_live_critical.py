from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import schedule_by_packet


def test_pr125_live_critical_rate_limits_revalidate_daily_and_are_stale_when_overdue():
    record = schedule_by_packet("PR125_PACKET_POLYMARKET_TICK_RULES_STALE")

    assert record["source_field_class"] == "TICK_RULES"
    assert record["revalidation_interval"] == "P1D"
    assert record["next_revalidation_due_at_fixture_time"] == "2026-05-18T00:00:00Z"
    assert record["revalidation_due_state"] == "DUE_TIME_BASED"
    assert record["revalidation_state"] == "STALE"
    assert record["production_revalidation_authority"] is False
