from tests.pr168_gfp2r._helpers import assert_gfp2r_valid, records


def test_pr168_gfp2r_pr234_merged_guard() -> None:
    assert_gfp2r_valid()
    discovery = records("PR168_GFP2R_InputDiscovery")
    assert discovery["pr234_required_state"] == "MERGED"
    assert discovery["pr234_merge_commit_required"].startswith("dd31ba51")
    assert discovery["DATA1A_missing_required_artifact_count"] == 0
