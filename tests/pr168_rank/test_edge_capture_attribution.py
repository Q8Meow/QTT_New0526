from tools.pr168_rank_validator import run_validation


def test_edge_capture_attribution() -> None:
    run_validation("edge_capture_attribution")
