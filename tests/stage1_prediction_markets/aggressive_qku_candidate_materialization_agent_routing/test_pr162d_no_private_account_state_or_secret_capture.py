from .pr162d_test_support import assert_no_private_state_or_secrets


def test_pr162d_no_private_account_state_or_secret_capture():
    assert_no_private_state_or_secrets()
