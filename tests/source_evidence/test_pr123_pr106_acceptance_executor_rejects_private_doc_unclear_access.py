from ._pr123_acceptance_helpers import assert_rejected_with


def test_acceptance_executor_rejects_private_doc_unclear_access():
    assert_rejected_with("PRIVATE_DOC_UNCLEAR_ACCESS", "PRIVATE_DOC_ACCESS_RIGHTS_BLOCKED")
