from .pr162d_test_support import assert_remote_not_required_for_ci


def test_pr162d_quantum_remote_execution_not_required_for_ci():
    assert_remote_not_required_for_ci()
