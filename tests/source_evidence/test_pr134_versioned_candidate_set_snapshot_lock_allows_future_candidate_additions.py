from .pr134_runtime_resolver_snapshot_support import artifacts


def test_versioned_candidate_set_snapshot_lock_allows_future_candidate_additions():
    for record in artifacts()["runtime_resolver_snapshots"]:
        assert record["candidate_set_snapshot_lock_metadata_created"] is True
        assert record["candidate_set_snapshot_version_id"]
        assert record["candidate_set_snapshot_parent_version_id"]
        assert record["candidate_set_snapshot_is_global_permanent_freeze"] is False
        assert record["candidate_set_snapshot_allows_future_versions"] is True
        assert record["candidate_set_snapshot_allows_future_candidate_additions"] is True
        assert record["candidate_set_snapshot_immutable_for_replay_audit_only"] is True
