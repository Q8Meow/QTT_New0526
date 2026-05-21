from .pr134_runtime_resolver_snapshot_support import artifacts


def test_pr134_atomicrows_pre_bridge_compatibility_and_post_pr135_bridge_readiness():
    for record in artifacts()["atomicrows_pre_bridge_compatibility"]:
        assert record["atomicrows_pre_bridge_compatibility_metadata_created"] is True
        assert record["future_atomicrows_bridge_recommended_after_repo_pr"] == "PR135"
        assert record["future_atomicrows_bridge_candidate_repo_pr"] == "PR136"
        assert record["bridge_materialization_authorized_now"] is False
        assert record["bundle_materialization_authorized_now"] is False
        assert record["sha_freeze_authorized_now"] is False
