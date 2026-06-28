from ._helpers import assert_rows_have_contract


def test_source_freshness_requires_accepted_packets_for_future_live_shadow_fields() -> None:
    rows = assert_rows_have_contract("src_fresh.jsonl")

    assert all(row["source_revalidation_required_flag"] is True for row in rows)
    assert all(row["accepted_source_packet_required_flag"] is True for row in rows)
    assert all(row["new_binding_allowed_flag"] is False for row in rows)
    assert all(row["new_live_use_allowed_flag"] is False for row in rows)

