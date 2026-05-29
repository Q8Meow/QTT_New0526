from .pr161a_test_support import report, summary


def test_pr161a_owner_approval_not_blocking_candidate_creation():
    approvals = report("orchestration_preflight")["owner_approval_state"]
    assert approvals["OWNER_PR161A_CANDIDATE_MATERIALIZATION_APPROVAL"] is True
    assert summary()["owner_internal_default_count"] > 0
    assert summary()["quantum_ready_candidate_count"] == 4525

