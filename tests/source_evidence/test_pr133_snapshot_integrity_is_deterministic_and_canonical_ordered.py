from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_snapshot_integrity_is_deterministic_and_canonical_ordered():
    for receipt in support.integrity_receipts():
        assert receipt["deterministic_sorting_verified"] is True
        assert receipt["canonical_sequence_verified"] is True
        assert receipt["duplicate_canonical_sort_key_count"] == 0
