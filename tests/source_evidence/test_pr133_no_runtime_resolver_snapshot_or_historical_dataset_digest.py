from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_no_runtime_resolver_snapshot_or_historical_dataset_digest():
    report = support.main_report()["PR133_SNAPSHOT_INTEGRITY_EVIDENCE"]
    assert report["runtime_resolver_snapshot_created_count"] == 0
    assert report["historical_dataset_digest_created_count"] == 0
