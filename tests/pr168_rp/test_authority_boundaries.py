from tools.pr168_rp_validator import run_validation


def test_authority_boundaries() -> None:
    run_validation("authority_boundaries")
