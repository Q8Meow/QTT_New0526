from tools.pr168_data1_validator import run_validation


def test_pr168_data1_rp2_first_recompute_batch_exists() -> None:
    run_validation("rp2_first_recompute_batch_exists")
