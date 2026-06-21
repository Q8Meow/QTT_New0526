from tools.pr168_data1_validator import run_validation


def test_pr168_data1_closed_pr232_not_merged_guard() -> None:
    run_validation("closed_pr232_not_merged_guard")
