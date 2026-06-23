from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_probability_source_does_not_treat_market_implied_as_alpha() -> None:
    assert_recovery1_valid()
    assert all(not row["independent_alpha_proof_flag"] and row["market_implied_probability_can_only_compute_threshold_flag"] for row in rows("probability_source"))
