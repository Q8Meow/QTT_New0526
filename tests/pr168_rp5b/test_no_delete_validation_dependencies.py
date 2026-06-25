from tests.pr168_rp5b._helpers import verification_rows


def test_no_delete_validation_dependencies() -> None:
    rows = [row for row in verification_rows() if row["validation_dependency_found_now_flag"]]
    assert all(row["final_action"] != "DELETE_ACTIVE_TREE_NOW" for row in rows)
