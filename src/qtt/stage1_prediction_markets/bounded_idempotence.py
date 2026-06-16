"""Bounded deterministic idempotence helpers for generated Stage 1 reports."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


DEFAULT_STABLE_ROW_FIELDS = (
    "row_id",
    "candidate_packet_id",
    "artifact_id",
    "repair_action_id",
    "repaired_packet_id",
    "report_filename",
    "report_name",
    "deterministic_sort_key",
    "qku_id",
    "formula_id",
    "algorithm_id",
)


def stable_row_key(
    row: dict[str, Any],
    preferred_fields: tuple[str, ...] = DEFAULT_STABLE_ROW_FIELDS,
) -> tuple[str, str]:
    for field in preferred_fields:
        value = row.get(field)
        if value not in (None, ""):
            return (field, str(value))
    return ("canonical_json", json.dumps(row, sort_keys=True, separators=(",", ":")))


def sample_rows(
    rows: list[dict[str, Any]],
    preferred_fields: tuple[str, ...] = DEFAULT_STABLE_ROW_FIELDS,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    ordered = sorted(rows, key=lambda row: stable_row_key(row, preferred_fields))
    indexes = sorted({0, len(ordered) // 2, len(ordered) - 1})
    return [deepcopy(ordered[index]) for index in indexes]


def report_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "report_filename": payload.get("report_filename"),
        "report_name": payload.get("report_name"),
        "schema_ref": payload.get("schema_ref"),
        "record_count": payload.get("record_count"),
        "sharded_flag": payload.get("sharded_flag"),
        "records_omitted_for_sharding_flag": payload.get(
            "records_omitted_for_sharding_flag"
        ),
        "shard_count": payload.get("shard_count"),
        "shard_files": tuple(payload.get("shard_files") or ()),
    }


def _manifest_report_filename(row: dict[str, Any]) -> str:
    report_filename = row.get("report_filename")
    if report_filename:
        return str(report_filename)
    report_path = row.get("report_path")
    if report_path:
        return Path(str(report_path)).name
    report_name = row.get("report_name")
    if report_name:
        name = str(report_name)
        return name if name.endswith(".report.json") else f"{name}.report.json"
    return ""


def manifest_coverage(
    payloads: dict[str, dict[str, Any]],
    *,
    constants: Any,
    manifest_report_filename: str,
) -> dict[str, Any]:
    manifest_rows = list(payloads[manifest_report_filename].get("records") or [])
    root_rows = [
        row
        for row in manifest_rows
        if row.get("manifest_entry_class") == "ROOT_REPORT"
    ]
    shard_rows = [
        row
        for row in manifest_rows
        if row.get("manifest_entry_class") == "SHARD_REPORT"
    ]
    return {
        "constant_report_filenames": tuple(constants.REPORT_FILENAMES),
        "constant_schema_filenames": tuple(constants.SCHEMA_FILENAMES),
        "manifest_root_report_filenames": tuple(
            sorted(_manifest_report_filename(row) for row in root_rows)
        ),
        "manifest_root_schema_paths": tuple(
            sorted(str(row.get("schema_path")) for row in root_rows)
        ),
        "manifest_root_entry_count": len(root_rows),
        "manifest_shard_entry_count": len(shard_rows),
        "manifest_shard_report_paths": tuple(
            sorted(str(row.get("report_path")) for row in shard_rows)
        ),
    }


def bounded_snapshot(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
    *,
    constants: Any,
    required_exact_reports: tuple[str, ...],
    manifest_report_filename: str,
    stable_row_fields: tuple[str, ...] = DEFAULT_STABLE_ROW_FIELDS,
) -> dict[str, Any]:
    missing_required = sorted(set(required_exact_reports) - set(payloads))
    assert (
        not missing_required
    ), f"bounded idempotence missing required reports: {missing_required}"
    missing_inventory = sorted(set(constants.REPORT_FILENAMES) - set(payloads))
    assert (
        not missing_inventory
    ), f"bounded idempotence missing inventory reports: {missing_inventory}"
    return {
        "required_exact_reports": {
            filename: deepcopy(payloads[filename])
            for filename in required_exact_reports
        },
        "report_envelopes": {
            filename: report_envelope(payloads[filename])
            for filename in constants.REPORT_FILENAMES
        },
        "manifest_coverage": {
            manifest_report_filename: manifest_coverage(
                payloads,
                constants=constants,
                manifest_report_filename=manifest_report_filename,
            )
        },
        "sampled_shards": {
            shard_ref: {
                "report_filename": payload.get("report_filename"),
                "report_name": payload.get("report_name"),
                "parent_report_filename": payload.get("parent_report_filename"),
                "schema_ref": payload.get("schema_ref"),
                "record_count": payload.get("record_count"),
                "sampled_rows": sample_rows(
                    list(payload.get("records") or []),
                    stable_row_fields,
                ),
            }
            for shard_ref, payload in sorted(shard_payloads.items())
        },
    }


def bounded_idempotence_differences(
    left: dict[str, Any],
    right: dict[str, Any],
) -> tuple[str, ...]:
    differences: list[str] = []
    for section in (
        "required_exact_reports",
        "report_envelopes",
        "manifest_coverage",
        "sampled_shards",
    ):
        left_values = left.get(section, {})
        right_values = right.get(section, {})
        for key in sorted(set(left_values) | set(right_values)):
            if left_values.get(key) != right_values.get(key):
                differences.append(f"{section}:{key}")
    return tuple(differences)


def assert_bounded_idempotence_equal(
    left: dict[str, Any],
    right: dict[str, Any],
) -> None:
    differences = bounded_idempotence_differences(left, right)
    assert not differences, "bounded idempotence drift: " + ", ".join(differences)
