from __future__ import annotations

import json
from typing import Any

from tools.pr168_gfp2r_config import AUTHORITY_FALSE_FLAGS, REQUIRED_REPORT_IDS, ROW_SHARDS, report_path
from tools.pr168_gfp2r_validator import validate_generated_reports


def assert_gfp2r_valid() -> None:
    assert validate_generated_reports() == []


def load_report(report_id: str) -> dict[str, Any]:
    path = report_path(report_id)
    assert path.exists(), report_id
    return json.loads(path.read_text(encoding="utf-8"))


def records(report_id: str) -> Any:
    return load_report(report_id)["records"]


def record_rows(report_id: str) -> list[dict[str, Any]]:
    value = records(report_id)
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        if isinstance(value.get("rows"), list):
            return value["rows"]
        if isinstance(value.get("sample_rows"), list):
            return value["sample_rows"]
    raise AssertionError(f"{report_id} has no row list")


def record_count(report_id: str) -> int:
    value = records(report_id)
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in (
            "row_count",
            "gap_count",
            "quantum_formula_variant_coverage_count",
        ):
            if isinstance(value.get(key), int):
                return int(value[key])
        summary = value.get("summary")
        if isinstance(summary, dict):
            for item in summary.values():
                if isinstance(item, int):
                    return item
    return len(record_rows(report_id))


def final_summary() -> dict[str, Any]:
    return records("PR168_GFP2R_FinalSummary")


def rows(shard_key: str) -> list[dict[str, Any]]:
    path = ROW_SHARDS[shard_key]
    assert path.exists(), shard_key
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def assert_positive_count(name: str) -> None:
    assert int(final_summary().get(name, 0) or 0) > 0, name


def assert_zero_count(name: str) -> None:
    assert final_summary().get(name) == 0, name


def assert_all_reports_have_records() -> None:
    for report_id in REQUIRED_REPORT_IDS:
        payload = load_report(report_id)
        assert payload["no_orphan_status"] == "NO_ORPHAN_ROUTED", report_id
        assert payload["records"] or payload["terminal_by_nature_flag"], report_id


def assert_no_forbidden_authority(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in AUTHORITY_FALSE_FLAGS:
                assert item is False, key
            if key in {
                "real_positive_allowed_flag",
                "real_negative_allowed_flag",
                "real_positive_negative_allowed_flag",
                "forced_positive_flag",
                "quantum_backend_execution_flag",
                "quantum_advantage_claim_flag",
            }:
                assert item is False, key
            assert_no_forbidden_authority(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_forbidden_authority(item)


def all_generated_payloads() -> list[Any]:
    payloads: list[Any] = [load_report(report_id) for report_id in REQUIRED_REPORT_IDS]
    for shard_key in ROW_SHARDS:
        payloads.extend(rows(shard_key))
    return payloads
