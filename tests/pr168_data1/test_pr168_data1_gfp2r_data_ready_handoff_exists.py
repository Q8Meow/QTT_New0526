from tools.pr168_data1_validator import run_validation


def test_pr168_data1_gfp2r_data_ready_handoff_exists() -> None:
    run_validation("gfp2r_data_ready_handoff_exists")
