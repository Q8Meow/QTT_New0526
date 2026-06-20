from tools.pr168_rp_validator import run_validation


def test_positive_negative_decision() -> None:
    run_validation("no_fake_computed_labels")
