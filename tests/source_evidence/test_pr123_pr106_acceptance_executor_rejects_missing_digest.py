from ._pr123_acceptance_helpers import assert_rejected_with


def test_acceptance_executor_rejects_missing_digest():
    assert_rejected_with("MISSING_DIGEST", "MISSING_OR_MALFORMED_DIGEST")
