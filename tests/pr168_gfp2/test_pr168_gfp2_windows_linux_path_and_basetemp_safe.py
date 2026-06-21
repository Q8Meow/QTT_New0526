from tests.pr168_gfp2.pr168_gfp2_test_support import validate_windows_linux


def test_windows_linux_path_and_basetemp_safe() -> None:
    validate_windows_linux()
