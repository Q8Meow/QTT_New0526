from tests.pr168_rp5b._helpers import verification_rows


def test_no_delete_unclear_files() -> None:
    unclear = [row for row in verification_rows() if row["rp5a_classification"] == "UNCLEAR_DO_NOT_DELETE"]
    assert unclear
    assert all(row["final_action"] == "UNCLEAR_DO_NOT_DELETE" for row in unclear)
