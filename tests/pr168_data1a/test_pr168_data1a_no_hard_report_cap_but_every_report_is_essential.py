from tests.pr168_data1a._helpers import assert_data1a_valid


def test_pr168_data1a_no_hard_report_cap_but_every_report_is_essential():
    assert_data1a_valid()
