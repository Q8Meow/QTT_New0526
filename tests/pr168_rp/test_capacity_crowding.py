from tools.pr168_rp_validator import run_validation


def test_capacity_crowding() -> None:
    run_validation("capacity_crowding")
