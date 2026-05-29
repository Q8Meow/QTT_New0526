from .pr161a_test_support import report


def test_pr161a_orchestration_preflight_receipt():
    payload = report("orchestration_preflight")
    receipt = payload["records"][0]
    assert payload["receipt_marker"] == "PR161A_ORCHESTRATION_PREFLIGHT_RECEIPT"
    assert receipt["active_branch"] == "pr161a-atomicrows-pr154-value-state-materialization-bridge"
    assert receipt["observed_atomicrows_count"] == 4183
    assert receipt["observed_pr154_count"] == 342
    assert receipt["source_intake_posture"] == "OPEN_CANDIDATE_FIRST"

