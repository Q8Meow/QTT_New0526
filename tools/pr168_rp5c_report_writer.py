#!/usr/bin/env python3
"""Deterministic report and shard IO for PR168-RP5C."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any

from tools.pr168_rp5c_config import (
    CREATED_AT_UTC,
    HARD_ZERO_COUNTERS,
    MAX_TOTAL_ROWS_PER_SHARD,
    REPORT_VERSION,
    generated_ref,
    manifest_path_for_shard,
    report_path,
    shard_path,
)


NO_AUTHORITY_STATEMENT = (
    "RP5C is immutable identity, provenance, classification, and derived routing "
    "preparation only. It creates no live/order/source-truth/champion/launch/"
    "quantum/hash authority and does not mutate formulas or delete identities."
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
        "identity_row_id",
        "source_artifact_row_id",
        "route_resolution_id",
        "route_rule_id",
        "responsibility_group_id",
        "family_row_id",
        "market_scope_row_id",
        "ontology_role_row_id",
        "formula_assignment_row_id",
        "row_id",
        "generated_surface_ref",
    ):
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return "unidentified_rp5c_row"


def write_shard(
    key: str,
    rows: Iterable[Mapping[str, Any]],
    *,
    schema_name: str,
    source_report_refs: list[str] | None = None,
    source_artifact_refs: list[str] | None = None,
    stable_ordering_key: str = "deterministic_row_id",
    downstream_consumer_refs: list[str] | None = None,
    generated_surface_authority_class: str = "RP5C_CENTRAL_ACTIVE_SURFACE_NOT_SOURCE_TRUTH",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = shard_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    row_refs_limited: list[str] = []
    sample: list[dict[str, Any]] = []
    truncated_by_row_budget = False
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            if row_count >= MAX_TOTAL_ROWS_PER_SHARD:
                truncated_by_row_budget = True
                break
            materialized = dict(row)
            handle.write(json.dumps(materialized, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False) + "\n")
            if len(sample) < 25:
                sample.append(materialized)
            if len(row_refs_limited) < 250:
                row_refs_limited.append(_row_ref(materialized))
            row_count += 1
    manifest_path = manifest_path_for_shard(path)
    manifest = {
        "manifest_id": f"PR168_RP5C_{key.upper()}_MANIFEST",
        "schema_version_name": schema_name,
        "shard_file_path": generated_ref(path),
        "physical_filename": generated_ref(manifest_path),
        "row_count": row_count,
        "max_total_rows_per_shard": MAX_TOTAL_ROWS_PER_SHARD,
        "row_count_within_bound_flag": row_count <= MAX_TOTAL_ROWS_PER_SHARD,
        "row_refs_limited": row_refs_limited,
        "truncated_row_refs_flag": row_count > 250,
        "truncated_by_row_budget_flag": truncated_by_row_budget,
        "source_report_refs": source_report_refs or [],
        "source_artifact_refs": source_artifact_refs or [],
        "stable_ordering_key": stable_ordering_key,
        "no_authority_statement": NO_AUTHORITY_STATEMENT,
        "no_deletion_no_mutation_counters": {
            "deleted_file_count": 0,
            "archived_file_count": 0,
            "moved_file_count": 0,
            "formula_expression_mutation_count": 0,
            "qku_identity_deleted_count": 0,
            "formula_identity_deleted_count": 0,
            "global_formula_ban_count": 0,
            "global_qku_ban_count": 0,
        },
        "generated_surface_authority_class": generated_surface_authority_class,
        "downstream_consumer_refs": downstream_consumer_refs or ["PR168-RP5D", "PR168-RP5E", "RANK4", "QOPT", "Paper", "LiveFutureOnly"],
        "report_version": REPORT_VERSION,
        "created_at_utc": CREATED_AT_UTC,
    }
    write_json(manifest_path, manifest)
    return sample, manifest


def report_payload(
    report_name: str,
    *,
    summary: Mapping[str, Any] | None = None,
    rows_ref: str | None = None,
    manifest_ref: str | None = None,
    records: Any | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        **HARD_ZERO_COUNTERS,
        "hard_zero_counters": dict(HARD_ZERO_COUNTERS),
        "logical_report_id": report_name.removesuffix(".report.json"),
        "physical_filename": report_name,
        "report_version": REPORT_VERSION,
        "created_at_utc": CREATED_AT_UTC,
        "no_authority_statement": NO_AUTHORITY_STATEMENT,
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
    return write_json(
        report_path(report_name),
        report_payload(report_name, summary=summary, rows_ref=rows_ref, manifest_ref=manifest_ref, records=records),
    )
