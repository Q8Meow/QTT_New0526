from tools.pr168_data1_validator import run_validation


def test_pr168_data1_no_hard_report_cap_but_every_report_is_essential() -> None:
    run_validation("no_hard_report_cap_but_every_report_is_essential")
