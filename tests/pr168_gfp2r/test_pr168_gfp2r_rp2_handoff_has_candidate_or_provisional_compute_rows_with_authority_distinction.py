from tests.pr168_gfp2r._helpers import assert_positive_count, rows


def test_pr168_gfp2r_rp2_handoff_has_candidate_or_provisional_compute_rows_with_authority_distinction() -> None:
    assert_positive_count("rp2_candidate_handoff_count")
    rp2_rows = rows("rp2_handoff")
    assert all(row["candidate_only_flag"] is True for row in rp2_rows)
    assert all(row["real_positive_negative_allowed_flag"] is False for row in rp2_rows)
    assert all(row["compute_lane"] in {"PROVISIONAL_DATA_CONSUMER", "EXACT_QKU_FORMULA"} for row in rp2_rows)
