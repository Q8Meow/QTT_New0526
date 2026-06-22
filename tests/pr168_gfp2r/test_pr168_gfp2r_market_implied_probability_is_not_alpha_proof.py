from tests.pr168_gfp2r._helpers import final_summary, rows


def test_pr168_gfp2r_market_implied_probability_is_not_alpha_proof() -> None:
    assert final_summary()["market_implied_probability_as_alpha_violation_count"] == 0
    assert all(row["market_implied_probability_as_alpha_proof_flag"] is False for row in rows("break_even_threshold"))
