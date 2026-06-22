from tests.pr168_gfp2r._helpers import final_summary, rows


def test_pr168_gfp2r_no_real_positive_negative_without_accepted_realistic_data() -> None:
    assert final_summary()["real_positive_negative_allowed_count"] == 0
    assert all(row["real_positive_allowed_flag"] is False for row in rows("formula_execution"))
    assert all(row["real_negative_allowed_flag"] is False for row in rows("formula_execution"))
