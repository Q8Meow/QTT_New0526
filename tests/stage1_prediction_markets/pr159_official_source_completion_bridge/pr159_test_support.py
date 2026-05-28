from __future__ import annotations

import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c


ROOT = Path(__file__).resolve().parents[3]


def load_json(path: Path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def master_report():
    return load_json(c.MASTER_REPORT_PATH)


def target_queue_registry():
    return load_json(c.TARGET_QUEUE_REGISTRY_PATH)


def target_records():
    return target_queue_registry()["records"]


def pr154_registry():
    return load_json(c.PR154_COMPLETION_REGISTRY_PATH)


def pr154_records():
    return pr154_registry()["records"]


def atomicrows_registry():
    return load_json(c.ATOMICROWS_COMPLETION_REGISTRY_PATH)


def atomicrows_records():
    return atomicrows_registry()["records"]


def candidate_registry():
    return load_json(c.CANDIDATE_PACKET_REGISTRY_PATH)


def candidate_records():
    return candidate_registry()["records"]


def accepted_registry():
    return load_json(c.ACCEPTED_PACKET_REGISTRY_PATH)


def accepted_records():
    return accepted_registry()["records"]


def attempt_matrix_report():
    return load_json(c.SOURCE_ACCEPTANCE_ATTEMPT_MATRIX_PATH)


def attempt_matrix_records():
    return attempt_matrix_report()["records"]


def unresolved_report():
    return load_json(c.UNRESOLVED_FILL_PATH_PATH)


def unresolved_records():
    return unresolved_report()["records"]


def report(path: Path):
    return load_json(path)


def no_authority_values():
    return master_report()["no_authority_confirmation"].values()
