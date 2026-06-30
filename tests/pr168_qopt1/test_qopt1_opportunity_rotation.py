from ._helpers import rows


def test_opportunity_rotation_packets_are_future_retest_routes() -> None:
    for filename in ("venue_side_rotate.jsonl", "next_target_rotate.jsonl", "tradeable_recovery_batch.jsonl"):
        row = rows(filename)[0]
        assert row["current_snapshot_revalidation_required_flag"] is True
        assert row["live_authority_created_flag"] is False
