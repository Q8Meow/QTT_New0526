from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_atomicrows_compatibility_metadata_only():
    for record in support.atomicrows_records():
        assert record["compatibility_class"] == "PRE_BRIDGE_METADATA_ONLY"
        assert record["bridge_materialization_authorized_now"] is False
        assert record["bundle_materialization_authorized_now"] is False
        assert record["sha_freeze_authorized_now"] is False
