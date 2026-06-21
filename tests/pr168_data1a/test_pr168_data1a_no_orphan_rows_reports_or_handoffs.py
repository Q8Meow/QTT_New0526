from tests.pr168_data1a._helpers import assert_data1a_valid


def test_pr168_data1a_no_orphan_rows_reports_or_handoffs():
    assert_data1a_valid()
