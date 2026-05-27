from __future__ import annotations

import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge import (
    constants as c,
)
from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge.owner_input_validator import (
    validate_owner_response_payload,
)


ROOT = Path(__file__).resolve().parents[3]


def load_json(path: Path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def pr154_report():
    return load_json(c.PR154_REPORT_PATH)


def pr154_registry():
    return load_json(c.PR154_REGISTRY_PATH)


def atomic_report():
    return load_json(c.ATOMICROWS_REPORT_PATH)


def atomic_registry():
    return load_json(c.ATOMICROWS_REGISTRY_PATH)


def atomic_records():
    registry = atomic_registry()
    records = list(registry.get("records", []))
    for shard in registry.get("shards", []):
        records.extend(load_json(Path(shard["shard_path"]))["records"])
    return records


def owner_packet():
    return load_json(c.OWNER_REQUEST_PATH)


def assert_pr157_ok():
    assert pr154_report()["validation_result"]["status"] == "PASS"
    assert atomic_report()["validation_result"]["status"] == "PASS"


def assert_owner_response_rejected(payload, expected_fragment: str):
    failures = validate_owner_response_payload(payload, owner_packet())
    assert any(expected_fragment in failure for failure in failures)
