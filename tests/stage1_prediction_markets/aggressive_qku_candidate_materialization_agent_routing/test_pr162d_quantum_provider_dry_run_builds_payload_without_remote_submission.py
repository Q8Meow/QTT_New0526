from .pr162d_test_support import assert_provider_dry_run


def test_pr162d_quantum_provider_dry_run_builds_payload_without_remote_submission():
    assert_provider_dry_run()
