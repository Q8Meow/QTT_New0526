from ._pr123_acceptance_helpers import assert_rejected_with


def test_acceptance_executor_rejects_secret_like_unredacted_candidate():
    assert_rejected_with("SECRET_LIKE_UNREDACTED", "SECRET_REDACTION_STATE_BLOCKED")
