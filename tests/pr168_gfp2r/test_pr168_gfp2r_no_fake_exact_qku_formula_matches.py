from tests.pr168_gfp2r._helpers import rows


def test_pr168_gfp2r_no_fake_exact_qku_formula_matches() -> None:
    assert not any(row["exact_candidate_compute_eligible_flag"] for row in rows("formula_variant"))
    assert not any(row["compute_lane"] == "EXACT_QKU_FORMULA" for row in rows("formula_execution"))
