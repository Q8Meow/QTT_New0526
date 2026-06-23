from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_online_verify_uses_source_rows_not_query_logs_only() -> None:
    assert_rank3_valid()
    online = rows("online_verify")
    assert len({row["source_url_or_owner_ref"] for row in online}) >= 16
    assert all(row["accepted_truth_flag"] is False for row in online)
