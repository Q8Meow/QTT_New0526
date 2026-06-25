from tests.pr168_rp5b._helpers import final_summary, verification_rows


def test_no_unique_identity_loss() -> None:
    summary = final_summary()
    identity_rows = [row for row in verification_rows() if row["contains_unique_qku_formula_identity_now_flag"]]
    assert summary["unique_qku_formula_identity_lost_count"] == 0
    assert summary["unique_identity_kept_count"] == len(identity_rows)
    assert all(row["final_action"] != "DELETE_ACTIVE_TREE_NOW" for row in identity_rows)
