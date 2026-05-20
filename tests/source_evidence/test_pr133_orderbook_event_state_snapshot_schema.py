import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.validator import SCHEMA_FILES

SCHEMA_DIR = Path("src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot")


def test_pr133_orderbook_event_state_snapshot_schema():
    for filename in SCHEMA_FILES:
        schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False
        for field in ("schema_version", "record_type", "created_by", "authority_class"):
            assert field in schema["required"]
        assert schema["properties"]["authority_class"]["const"] == policy.PACKAGE_AUTHORITY_CLASS
