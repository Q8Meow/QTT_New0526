from tests.pr168_rp5a._helpers import delete_rows


def test_delete_eligibility_draft_exists() -> None:
    rows = delete_rows()
    assert rows
    assert all(row["delete_now_flag"] is False for row in rows)
