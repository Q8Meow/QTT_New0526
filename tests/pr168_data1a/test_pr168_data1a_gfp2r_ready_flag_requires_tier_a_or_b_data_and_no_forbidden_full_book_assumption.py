from tests.pr168_data1a._helpers import assert_data1a_valid


def test_pr168_data1a_gfp2r_ready_flag_requires_tier_a_or_b_data_and_no_forbidden_full_book_assumption():
    assert_data1a_valid()
