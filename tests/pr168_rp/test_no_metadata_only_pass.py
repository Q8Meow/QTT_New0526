from tools.pr168_rp_validator import run_validation


def test_no_metadata_only_pass() -> None:
    run_validation("no_metadata_only_pass")
