#!/usr/bin/env python3
"""Report and shard IO for PR168-RP5B."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any

from tools.pr168_rp5b_config import (
    CREATED_AT_UTC,
    MAX_TOTAL_ROWS_PER_SHARD,
    REPORT_VERSION,
    generated_ref,
    manifest_path_for_shard,
    report_path,
    shard_path,
)


def write_json(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    materialized = dict(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(materialized, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return materialized


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    materialized = [dict(row) for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in materialized:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False) + "\n")
    return materialized


def _row_ref(row: Mapping[str, Any]) -> str:
    for key in (
        "row_id",
        "artifact_id",
        "file_path",
        "artifact_path",
        "legacy_term",
        "source_file_path",
        "rule_id",
    ):
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return "unidentified_rp5b_row"


def write_shard(key: str, rows: Iterable[Mapping[str, Any]], *, logical_family_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = shard_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    row_refs_limited: list[str] = []
    truncated_by_row_budget = False
    materialized: list[dict[str, Any]] = []
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            if row_count >= MAX_TOTAL_ROWS_PER_SHARD:
                truncated_by_row_budget = True
                break
            materialized_row = dict(row)
            handle.write(json.dumps(materialized_row, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False) + "\n")
            if len(materialized) < 25:
                materialized.append(materialized_row)
            row_count += 1
            if len(row_refs_limited) < 250:
                row_refs_limited.append(_row_ref(materialized_row))
    manifest_path = manifest_path_for_shard(path)
    manifest = {
        "logical_shard_family_id": logical_family_id,
        "manifest_id": f"{logical_family_id}_MANIFEST",
        "physical_filename": generated_ref(manifest_path),
        "shard_path": generated_ref(path),
        "row_count": row_count,
        "max_total_rows_per_shard": MAX_TOTAL_ROWS_PER_SHARD,
        "row_count_within_bound_flag": row_count <= MAX_TOTAL_ROWS_PER_SHARD,
        "row_refs_limited": row_refs_limited,
        "truncated_row_refs_flag": row_count > 250,
        "truncated_by_row_budget_flag": truncated_by_row_budget,
        "report_version": REPORT_VERSION,
        "created_at_utc": CREATED_AT_UTC,
    }
    write_json(manifest_path, manifest)
    return materialized, manifest


def report_payload(
    report_name: str,
    *,
    summary: Mapping[str, Any] | None = None,
    rows_ref: str | None = None,
    manifest_ref: str | None = None,
    records: Any | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "logical_report_id": report_name.removesuffix(".report.json"),
        "physical_filename": report_name,
        "report_version": REPORT_VERSION,
        "created_at_utc": CREATED_AT_UTC,
        "records": [] if records is None else records,
    }
    if rows_ref is not None:
        payload["rows_ref"] = rows_ref
    if manifest_ref is not None:
        payload["manifest_ref"] = manifest_ref
    if summary:
        payload.update(dict(summary))
    return payload


def write_report(
    report_name: str,
    *,
    summary: Mapping[str, Any] | None = None,
    rows_ref: str | None = None,
    manifest_ref: str | None = None,
    records: Any | None = None,
) -> dict[str, Any]:
    payload = report_payload(
        report_name,
        summary=summary,
        rows_ref=rows_ref,
        manifest_ref=manifest_ref,
        records=records,
    )
    return write_json(report_path(report_name), payload)
