from .pr134_runtime_resolver_snapshot_support import artifacts


def test_pr134_preserves_low_latency_hot_path_boundary():
    for snapshot in artifacts()["runtime_resolver_snapshots"]:
        assert snapshot["future_low_latency_runtime_resolver_snapshot_ref"]
        assert snapshot["future_hot_path_runtime_resolver_snapshot_ref"]
        assert snapshot["live_use_requires_future_owner_approval"] is True
        assert snapshot["live_candidate_discovery_requires_later_authorization"] is True
        assert snapshot["live_runtime_resolver_authority_created"] is False
        assert snapshot["network_io_created"] is False
