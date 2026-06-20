from tools.pr168_rp_validator import run_validation


def test_live_candidate_handoff_no_order_authority() -> None:
    run_validation("live_candidate_handoff_no_order_authority")
