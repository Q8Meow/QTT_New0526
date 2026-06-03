from .pr162d_test_support import assert_pr162c_records_consumed


def test_pr162d_consumes_pr162c_blocker_records_as_acquisition_targets():
    assert_pr162c_records_consumed()
