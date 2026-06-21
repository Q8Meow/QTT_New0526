from tests.pr168_gfp2.pr168_gfp2_test_support import validate_nonofficial_sources


def test_nonofficial_sources_route_to_candidate_lane_not_truth() -> None:
    validate_nonofficial_sources()
