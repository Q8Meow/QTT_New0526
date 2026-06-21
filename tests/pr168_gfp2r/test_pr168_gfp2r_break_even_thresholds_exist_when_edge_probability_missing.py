from tests.pr168_gfp2r._helpers import assert_positive_count, record_rows


def test_pr168_gfp2r_break_even_thresholds_exist_when_edge_probability_missing() -> None:
    assert_positive_count("break_even_threshold_computed_count")
    assert_positive_count("required_edge_threshold_computed_count")
    gaps = record_rows("PR168_GFP2R_IndependentProbabilityInputGapLedger")
    assert any(row["independent_probability_missing_flag"] for row in gaps)
