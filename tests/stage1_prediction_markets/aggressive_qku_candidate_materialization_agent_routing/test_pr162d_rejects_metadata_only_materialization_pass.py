from .pr162d_test_support import assert_no_metadata_only


def test_pr162d_rejects_metadata_only_materialization_pass():
    assert_no_metadata_only()
