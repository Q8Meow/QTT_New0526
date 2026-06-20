from tools.pr168_rp_validator import run_validation


def test_edge_attribution() -> None:
    run_validation("edge_attribution")
