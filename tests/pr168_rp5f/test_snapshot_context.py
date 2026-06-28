from ._helpers import assert_rows_have_contract


def test_snapshot_context_is_source_required_not_live_truth() -> None:
    rows = assert_rows_have_contract("snap_ctx.jsonl")

    assert all(row["snapshot_id"] for row in rows)
    assert all(row["asof_timestamp_utc"] for row in rows)
    assert all(row["side_domain"] == "BOTH_IF_AVAILABLE" for row in rows)
    assert all(row["accepted_source_fact_flag"] is False for row in rows)
    assert all(row["fixture_or_live_source_class"] == "OFFLINE_FIXTURE_SOURCE_REQUIRED_NOT_LIVE_TRUTH" for row in rows)

