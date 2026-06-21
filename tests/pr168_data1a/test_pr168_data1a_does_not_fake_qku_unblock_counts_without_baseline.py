from tests.pr168_data1a._helpers import assert_data1a_valid


def test_pr168_data1a_does_not_fake_qku_unblock_counts_without_baseline():
    assert_data1a_valid()
