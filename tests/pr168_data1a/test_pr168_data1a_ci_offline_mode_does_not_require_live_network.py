from tests.pr168_data1a._helpers import assert_data1a_valid


def test_pr168_data1a_ci_offline_mode_does_not_require_live_network():
    assert_data1a_valid()
