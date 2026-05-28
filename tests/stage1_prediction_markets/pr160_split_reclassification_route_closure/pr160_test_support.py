from __future__ import annotations

import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import (
    constants as c,
)


ROOT = Path(__file__).resolve().parents[3]


def load_json(path: Path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def master_report():
    return load_json(c.MASTER_REPORT_PATH)


def master_registry():
    return load_json(c.MASTER_REGISTRY_PATH)


def records():
    return master_registry()["records"]


def count_receipt():
    return master_report()["count_invariant_receipt"]


def report(path: Path):
    return load_json(path)


def route_records(route: str):
    return [item for item in records() if item["final_route_class"] == route]


def no_authority_values():
    return master_report()["no_authority_confirmation"].values()


def all_generated_payloads():
    return [load_json(path) for path in c.ALL_JSON_ARTIFACT_PATHS]
