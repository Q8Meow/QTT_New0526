#!/usr/bin/env python3
"""Writers for PR168-DATA1A reports and row shards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from tools.pr168_data1a_config import (
    REPORT_VERSION,
    TOOL_NAME,
    authority_flags,
    generated_ref,
    manifest_path,
    report_path,
    route_defaults,
)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    materialized = [dict(row) for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in materialized:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return materialized


def write_shard(path: Path, rows: Iterable[Mapping[str, Any]], *, manifest_id: str, data_family: str) -> dict[str, Any]:
    materialized = write_jsonl(path, rows)
    row_refs = [
        str(
            row.get("inventory_row_id")
            or row.get("qku_unblock_row_id")
            or row.get("data_quality_row_id")
            or row.get("alpha_capture_row_id")
            or row.get("recovery_row_id")
            or row.get("historical_full_book_row_id")
            or row.get("gfp2r_readiness_row_id")
            or row.get("quantum_usability_row_id")
            or row.get("action_id")
            or row.get("row_id")
        )
        for row in materialized
    ]
    manifest = {
        "manifest_id": manifest_id,
        "data_family": data_family,
        "shard_path": generated_ref(path),
        "row_count": len(materialized),
        "row_refs": row_refs,
        **route_defaults("governance", row_shard_refs=[generated_ref(path)]),
        "authority_class": "PR168_DATA1A_PUBLIC_READ_ONLY_JSONL_SHARD_MANIFEST",
    }
    write_json(manifest_path(path), manifest)
    return manifest


def report_payload(
    report_id: str,
    created_at_utc: str,
    records: Any,
    *,
    route_key: str = "governance",
    upstream_input_refs: list[str] | None = None,
    data1_artifact_refs: list[str] | None = None,
    row_shard_refs: list[str] | None = None,
    data_provenance_refs: list[str] | None = None,
    authority_class: str = "PR168_DATA1A_PUBLIC_READ_ONLY_AUDIT",
    terminal_by_nature_flag: bool = False,
    terminal_reason_code: str | None = None,
) -> dict[str, Any]:
    route = route_defaults(
        route_key,
        upstream_refs=upstream_input_refs,
        data1_refs=data1_artifact_refs,
        row_shard_refs=row_shard_refs,
        provenance_refs=data_provenance_refs,
        terminal_by_nature_flag=terminal_by_nature_flag,
        terminal_reason_code=terminal_reason_code,
        authority_class=authority_class,
    )
    return {
        "report_id": report_id,
        "report_version": REPORT_VERSION,
        "created_by_tool": TOOL_NAME,
        "created_at_utc": created_at_utc,
        "records": records,
        **route,
    }


def write_report(report_id: str, payload: Mapping[str, Any]) -> None:
    write_json(report_path(report_id), dict(payload))


def assert_no_forbidden_true_flags(value: Any, *, path: str = "root") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in authority_flags() and item is True:
                failures.append(f"{path}.{key}")
            failures.extend(assert_no_forbidden_true_flags(item, path=f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            failures.extend(assert_no_forbidden_true_flags(item, path=f"{path}[{index}]"))
    return failures
