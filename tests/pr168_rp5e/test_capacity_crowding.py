from ._helpers import read_jsonl


def test_capacity_crowding_rows_cover_liquidity_depth_spread_and_time_to_close() -> None:
    rows = read_jsonl("capacity.jsonl")
    assert rows
    for row in rows[:10]:
        assert row["depth_bucket"]
        assert row["spread_bucket"]
        assert row["liquidity_bucket"]
        assert row["volume_bucket"]
        assert row["time_to_close_bucket"]
        assert row["future_rp5g_capacity_model_required_flag"] is True
