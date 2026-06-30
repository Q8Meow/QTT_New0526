from ._helpers import rows


def test_latency_sla_and_live_ladder_are_revalidation_only() -> None:
    assert all(row["snapshot_revalidation_required_flag"] is True for row in rows("rank_latency_sla.jsonl"))
    assert all(row["live_canary_authority_created_flag"] is False for row in rows("rank_live_ladder.jsonl"))

