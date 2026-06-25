from tests.pr168_rp5b._helpers import load_rows


def test_safe_deletion_verification_exists() -> None:
    rows = load_rows("safe_deletion_verification_rows")
    assert rows
    assert all(row["final_action"] for row in rows)
    assert all("safe_to_delete_now_flag" in row for row in rows)
