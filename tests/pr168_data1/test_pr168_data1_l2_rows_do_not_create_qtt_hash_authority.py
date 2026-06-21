from tools.pr168_data1_validator import run_validation


def test_pr168_data1_l2_rows_do_not_create_qtt_hash_authority() -> None:
    run_validation("l2_rows_do_not_create_qtt_hash_authority")
