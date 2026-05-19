from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import inputs, supersession_records


def test_pr125_supersession_preserves_old_and_new_packet_identity():
    accepted = inputs()["accepted_source_evidence_records"]["accepted_source_evidence_records"]
    accepted_ids = {record["accepted_source_evidence_packet_id"] for record in accepted}
    record = supersession_records()[0]

    assert record["superseded_packet_id"] in accepted_ids
    assert record["superseding_packet_id"] in accepted_ids
    assert record["superseded_packet_id"] != record["superseding_packet_id"]
    assert accepted_ids >= {
        "PR125_PACKET_KALSHI_FEE_RULES_OLD",
        "PR125_PACKET_KALSHI_FEE_RULES_NEW",
    }
