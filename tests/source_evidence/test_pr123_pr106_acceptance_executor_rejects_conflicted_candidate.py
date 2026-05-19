from ._pr123_acceptance_helpers import assert_rejected_with


def test_acceptance_executor_rejects_conflicted_candidate():
    assert_rejected_with("CONFLICTED_CANDIDATE", "CONFLICT_STATE_BLOCKED")
