from __future__ import annotations

import json

from tools.pr168_rp5b_config import report_path, shard_path
from tools.pr168_rp5b_validator import run_validation


def load_report(name: str) -> dict:
    return json.loads(report_path(name).read_text(encoding="utf-8"))


def load_rows(key: str) -> list[dict]:
    path = shard_path(key)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def final_summary() -> dict:
    return load_report("PR168_RP5B_FinalSummary.report.json")


def verification_rows() -> list[dict]:
    return load_rows("safe_deletion_verification_rows")


def assert_rp5b_valid() -> None:
    assert run_validation()["validation"] == "PR168_RP5B_ACTIVE_REGISTRY_SAFE_CLEANUP_OK"
