from __future__ import annotations

import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge import (
    constants as c,
)


ROOT = Path(__file__).resolve().parents[3]


def load_json(path: Path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def master_report():
    return load_json(c.MASTER_REPORT_PATH)


def master_registry():
    return load_json(c.MASTER_REGISTRY_PATH)


def owner_response():
    return load_json(c.OWNER_RESPONSE_PATH)


def owner_packet():
    return load_json(c.OWNER_REQUEST_PATH)


def lane_a_registry():
    return load_json(c.AGENT_ASSIGNMENT_REGISTRY_PATH)


def lane_b_registry():
    return load_json(c.OWNER_POLICY_DEFAULT_REGISTRY_PATH)


def lane_c_registry():
    return load_json(c.PARAMETER_RANGE_REGISTRY_PATH)


def lane_d_registry():
    return load_json(c.PR154_OWNER_ROUTE_REGISTRY_PATH)


def lane_e_registry():
    return load_json(c.PR154_SPLIT_REGISTRY_PATH)


def lane_f_records():
    return [
        item
        for item in master_registry()["records"]
        if item["lane"] == c.PR158Lane.LANE_F_PR154_PRIVATE_DOC_ATTESTATION.value
    ]


def overlay_report():
    return load_json(c.SELECTION_OVERLAY_REPORT_PATH)


def overlay_registry():
    return load_json(c.SELECTION_OVERLAY_REGISTRY_PATH)


def overlay_records():
    return overlay_registry()["records"]

