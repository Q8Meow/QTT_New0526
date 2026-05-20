from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_snapshot_records_are_not_trading_signals_or_feature_vectors():
    for snapshot in [*support.orderbook_snapshots(), *support.event_state_snapshots()]:
        assert snapshot.get("orderbook_snapshot_is_trading_signal", snapshot.get("event_state_snapshot_is_trading_signal")) is False
        assert snapshot.get("orderbook_snapshot_is_feature_vector", snapshot.get("event_state_snapshot_is_feature_vector")) is False
