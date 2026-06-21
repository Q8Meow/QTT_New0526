from tests.pr168_gfp2r._helpers import assert_zero_count


def test_pr168_gfp2r_real_positive_negative_counts_zero_unless_proof_exists() -> None:
    assert_zero_count("real_positive_count")
    assert_zero_count("real_negative_count")
