import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.validator import SCHEMA_FILES

SCHEMA_DIR = Path("src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot")


def test_pr133_schema_enums_quantum_atomicrows_and_snapshot_canonicalization_match_policy_constants():
    for filename in SCHEMA_FILES:
        schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
        props = schema["properties"]
        assert tuple(props["venue_id"]["enum"]) == policy.STAGE1_VENUE_IDS
        assert tuple(props["scope_id"]["enum"]) == policy.SHARED_SCOPE_IDS
        for field in policy.QUANTUM_FORWARD_SNAPSHOT_METADATA_FIELDS:
            assert field in props
        for field in policy.ATOMICROWS_PRE_BRIDGE_METADATA_FIELDS:
            assert field in props
    orderbook = json.loads((SCHEMA_DIR / "orderbook_snapshot.schema.json").read_text(encoding="utf-8"))
    event_state = json.loads((SCHEMA_DIR / "event_state_snapshot.schema.json").read_text(encoding="utf-8"))
    assert tuple(orderbook["properties"]["canonical_depth_side"]["enum"]) == policy.ALLOWED_CANONICAL_DEPTH_SIDES
    assert tuple(event_state["properties"]["qtt_internal_lifecycle_state_class"]["enum"]) == policy.ALLOWED_EVENT_LIFECYCLE_STATUS_CLASSES
