from tools.pr168_rp_validator import run_validation


def test_windows_linux_compatibility() -> None:
    run_validation("windows_linux_compatibility")
