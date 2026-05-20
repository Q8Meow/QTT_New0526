from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_atomicrows_pre_bridge_compatibility_and_post_pr135_bridge_readiness():
    report = support.main_report()["PR133_POST_PR135_ATOMICROWS_BRIDGE_READINESS_HANDOFF"]
    assert report["future_atomicrows_bridge_recommended_after_repo_pr"] == "PR135"
    assert report["future_atomicrows_bridge_candidate_repo_pr"] == "PR136"
    assert report["future_atomicrows_bridge_requires_owner_authorization"] is True
