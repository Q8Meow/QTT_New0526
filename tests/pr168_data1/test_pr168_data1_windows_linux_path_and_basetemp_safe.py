from tools.pr168_data1_validator import run_validation


def test_pr168_data1_windows_linux_path_and_basetemp_safe() -> None:
    run_validation("windows_linux_path_and_basetemp_safe")
