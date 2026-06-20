from tools.pr168_rp_validator import run_validation


def test_input_gap_routing() -> None:
    run_validation("formula_execution")
    run_validation("strict_input_consumption")
