from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import (
    schedule_by_packet,
    snapshot,
    supersession_records,
)


def test_pr125_supersession_marks_prior_packet_without_deleting_it():
    record = supersession_records()[0]
    old_schedule = schedule_by_packet("PR125_PACKET_KALSHI_FEE_RULES_OLD")
    snap = snapshot()

    assert record["superseded_packet_id"] == "PR125_PACKET_KALSHI_FEE_RULES_OLD"
    assert record["supersession_state"] == "SUPERSEDED_BY_NEW_ACCEPTED_PACKET"
    assert old_schedule["revalidation_state"] == "SUPERSEDED"
    assert "PR125_PACKET_KALSHI_FEE_RULES_OLD" in snap["superseded_accepted_packet_ids"]
    assert record["production_source_change_authority"] is False
