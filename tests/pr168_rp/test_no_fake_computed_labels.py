from tools.pr168_rp_validator import run_validation


def test_no_fake_computed_labels() -> None:
    run_validation("no_fake_computed_labels")
