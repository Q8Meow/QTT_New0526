from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_event_state_lifecycle_classes_are_canonical():
    allowed = set(policy.ALLOWED_EVENT_LIFECYCLE_STATUS_CLASSES)
    for snapshot in support.event_state_snapshots():
        assert {state["qtt_internal_lifecycle_state_class"] for state in snapshot["event_states"]} == allowed
        assert snapshot["event_states"] == sorted(snapshot["event_states"], key=support.canonical_event_state_sort_key)
