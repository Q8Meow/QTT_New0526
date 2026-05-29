from .pr161b_test_support import summary


def test_pr161b_pr152_deterministic_audit_currentization_status_is_recorded():
    assert summary()["pr152_deterministic_audit_currentization_status"] == "PR152_AUDIT_PRESENT_AND_ALLOWED_FOR_PR161B_CURRENTIZATION"
