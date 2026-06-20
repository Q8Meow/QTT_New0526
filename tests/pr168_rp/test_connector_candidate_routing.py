from tools.pr168_rp_validator import run_validation


def test_connector_candidate_routing() -> None:
    run_validation("connector_candidate_routing")
