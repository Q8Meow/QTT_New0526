from tools.pr168_rp_validator import run_validation


def test_replay_paper_pnl_math() -> None:
    run_validation("replay_paper_results")
    run_validation("tca_pnl_math")
