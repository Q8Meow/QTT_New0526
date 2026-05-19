from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import schedule_by_packet


def test_pr125_low_risk_general_docs_revalidate_weekly_and_remain_fresh_before_due():
    record = schedule_by_packet("PR125_PACKET_POLYMARKET_GENERAL_DOCS")

    assert record["source_field_class"] == "GENERAL_EXPLANATORY_DOCS"
    assert record["revalidation_interval"] == "P7D"
    assert record["next_revalidation_due_at_fixture_time"] == "2026-05-22T00:00:00Z"
    assert record["revalidation_due_state"] == "NOT_DUE"
    assert record["revalidation_state"] == "FRESH"
    assert record["production_revalidation_authority"] is False
