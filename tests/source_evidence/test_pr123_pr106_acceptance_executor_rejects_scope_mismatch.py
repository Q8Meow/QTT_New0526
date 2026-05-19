from ._pr123_acceptance_helpers import assert_rejected_with


def test_acceptance_executor_rejects_scope_mismatch():
    assert_rejected_with("SCOPE_MISMATCH", "TARGET_FIELD_OR_SCOPE_INVALID")
