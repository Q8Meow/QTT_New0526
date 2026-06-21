#!/usr/bin/env python3
"""Writers for PR168-GFP2R reports and deterministic row shards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from tools.pr168_gfp2r_config import (
    REPORT_VERSION,
    TOOL_NAME,
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


def row_ref(row: Mapping[str, Any]) -> str:
    for key in (
        "mapping_row_id",
        "formula_variant_id",
        "formula_equivalence_row_id",
        "compute_eligibility_row_id",
        "compute_row_id",
        "receipt_id",
        "numeric_evidence_row_id",
        "break_even_row_id",
        "recovery_variant_id",
        "rp2_candidate_row_id",
        "rank2_candidate_row_id",
        "quantum_mapping_id",
        "action_id",
        "row_id",
    ):
        value = row.get(key)
        if value:
            return str(value)
    return "unidentified_row"


def write_shard(path: Path, rows: Iterable[Mapping[str, Any]], *, manifest_id: str, data_family: str) -> dict[str, Any]:
    materialized = write_jsonl(path, rows)
    manifest = {
        "manifest_id": manifest_id,
        "data_family": data_family,
        "shard_path": generated_ref(path),
        "row_count": len(materialized),
        "row_refs": [row_ref(row) for row in materialized],
        **route_defaults("governance", row_shard_refs=[generated_ref(path)]),
        "authority_class": "PR168_GFP2R_JSONL_SHARD_MANIFEST_NON_PROOF",
    }
    write_json(manifest_path(path), manifest)
    return manifest


def report_payload(
    report_id: str,
    created_at_utc: str,
    records: Any,
    *,
    route_key: str = "governance",
    upstream_refs: list[str] | None = None,
    data1_refs: list[str] | None = None,
    data1a_refs: list[str] | None = None,
    formula_refs: list[str] | None = None,
    formula_variant_refs: list[str] | None = None,
    row_shard_refs: list[str] | None = None,
    numeric_evidence_refs: list[str] | None = None,
    provenance_refs: list[str] | None = None,
    computed_from_refs: list[str] | None = None,
    authority_class: str = "PR168_GFP2R_CANDIDATE_ONLY_NON_PROOF",
    terminal_by_nature_flag: bool = False,
    terminal_reason_code: str | None = None,
) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "report_version": REPORT_VERSION,
        "created_by_tool": TOOL_NAME,
        "created_at_utc": created_at_utc,
        "records": records,
        **route_defaults(
            route_key,
            upstream_refs=upstream_refs,
            data1_refs=data1_refs,
            data1a_refs=data1a_refs,
            formula_refs=formula_refs,
            formula_variant_refs=formula_variant_refs,
            row_shard_refs=row_shard_refs,
            numeric_evidence_refs=numeric_evidence_refs,
            provenance_refs=provenance_refs,
            computed_from_refs=computed_from_refs,
            terminal_by_nature_flag=terminal_by_nature_flag,
            terminal_reason_code=terminal_reason_code,
            authority_class=authority_class,
        ),
    }


def write_report(report_id: str, payload: Mapping[str, Any]) -> None:
    write_json(report_path(report_id), dict(payload))


def summarize_rows(rows: list[dict[str, Any]], *, key: str) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, "MISSING"))
        counts[value] = counts.get(value, 0) + 1
    return {"row_count": len(rows), f"{key}_counts": dict(sorted(counts.items()))}
