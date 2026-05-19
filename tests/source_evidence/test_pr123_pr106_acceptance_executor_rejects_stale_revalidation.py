from ._pr123_acceptance_helpers import assert_rejected_with


def test_acceptance_executor_rejects_stale_revalidation():
    assert_rejected_with("STALE_REVALIDATION", "REVALIDATION_STATE_BLOCKED")
