from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_rejects_duplicate_depth_levels_and_snapshot_ids():
    duplicate_depth = support.cloned_artifacts()
    duplicate_depth["orderbook_snapshots"][0]["depth_levels"][1]["synthetic_depth_level_id"] = duplicate_depth["orderbook_snapshots"][0]["depth_levels"][0]["synthetic_depth_level_id"]
    assert any("duplicate synthetic depth" in failure for failure in support.validation_failures(duplicate_depth))

    duplicate_snapshot = support.cloned_artifacts()
    duplicate_snapshot["event_state_snapshots"][0]["snapshot_id"] = duplicate_snapshot["orderbook_snapshots"][0]["snapshot_id"]
    assert any("duplicate snapshot" in failure for failure in support.validation_failures(duplicate_snapshot))
