"""Report sharding helpers for PR163-B row-level registries."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    POLICY_MODULE_REF,
    PR_ID,
)
from .json_io import json_text, read_json, records_from_payload, stable_counter


ROOT_REPORT_LIMIT_BYTES = 10 * 1024 * 1024
SHARD_LIMIT_BYTES = 25 * 1024 * 1024
DEFAULT_SHARD_ROW_TARGET = 2500


def encoded_json_size(payload: Any, *, compact: bool = False) -> int:
    return len(json_text(payload, compact=compact).encode("utf-8"))


def shard_rows(rows: list[dict[str, Any]], shard_size: int = DEFAULT_SHARD_ROW_TARGET) -> list[list[dict[str, Any]]]:
    if not rows:
        return []
    return [rows[index : index + shard_size] for index in range(0, len(rows), shard_size)]


def build_sharded_payloads(
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    report_name = filename.replace(".report.json", "")
    chunks = shard_rows(records)
    shard_payloads: dict[str, dict[str, Any]] = {}
    shard_manifest_refs: list[dict[str, Any]] = []
    shard_files: list[str] = []
    shard_record_counts: list[int] = []
    shard_count = len(chunks)
    for index, chunk in enumerate(chunks, start=1):
        shard_name = f"{report_name}.part_{index:04d}_of_{shard_count:04d}.report.json"
        rel_path = (p.SHARD_DIR / shard_name).as_posix()
        shard_payload = _base_payload(
            filename=shard_name,
            records=chunk,
            source_inputs=source_inputs,
            report_name=report_name,
        )
        shard_payload.update(
            {
                "parent_report_filename": filename,
                "part_ref": f"PR163B_PART::{index:04d}",
                "part_index": index,
                "part_count": shard_count,
                "shard_index": index,
                "shard_count": shard_count,
                "record_count": len(chunk),
                "total_record_count": len(records),
                "total_row_count": len(records),
                "records_canonical_part_flag": True,
                "aggregate_counts": aggregate_counts(chunk),
                "authority_counts": dict(BOUNDARY_COUNT_FIELDS),
            }
        )
        shard_payloads[rel_path] = shard_payload
        shard_files.append(rel_path)
        shard_record_counts.append(len(chunk))
        shard_manifest_refs.append(
            {
                "part_ref": shard_payload["part_ref"],
                "shard_path": rel_path,
                "shard_index": index,
                "row_count": len(chunk),
                "estimated_shard_size_bytes": encoded_json_size(shard_payload, compact=True),
                "below_25_mib_limit": encoded_json_size(shard_payload, compact=True) < SHARD_LIMIT_BYTES,
            }
        )

    compact_payload = _base_payload(
        filename=filename,
        records=[],
        source_inputs=source_inputs,
        report_name=report_name,
    )
    compact_payload.update(
        {
            "record_count": len(records),
            "total_record_count": len(records),
            "total_row_count": len(records),
            "sharded_flag": True,
            "shard_count": shard_count,
            "shard_files": shard_files,
            "shard_paths": shard_files,
            "shard_manifest_refs": shard_manifest_refs,
            "shard_record_counts": shard_record_counts,
            "largest_shard_record_count": max(shard_record_counts) if shard_record_counts else 0,
            "records_omitted_for_sharding_flag": True,
            "full_records_only_in_shards_flag": True,
            "canonical_records_location": p.SHARD_DIR.as_posix(),
            "aggregate_counts": aggregate_counts(records),
            "authority_counts": dict(BOUNDARY_COUNT_FIELDS),
            "authority_absence_confirmation": {
                "replay_result_packet_authority": True,
                "paper_result_packet_authority": True,
                "profit_authority": True,
                "live_order_authority": True,
                "source_acceptance_authority": True,
                "connector_binding_authority": True,
                "private_state_authority": True,
                "runtime_cash_authority": True,
                "quantum_backend_or_advantage_authority": True,
                "llm_runtime_or_order_authority": True,
                "qtt_freeze_checksum_authority": True,
            },
        }
    )
    return compact_payload, shard_payloads


def _base_payload(
    *,
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    report_name: str | None = None,
) -> dict[str, Any]:
    return {
        "report_id": filename.replace(".report.json", "").upper(),
        "report_name": report_name or filename.replace(".report.json", ""),
        "pr_id": PR_ID,
        "report_filename": filename,
        "created_by_pr": PR_ID,
        "authority_class": AUTHORITY_CLASS,
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
        "validation_status": "PASS",
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(p.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(p.DOWNSTREAM_PR_ROUTES),
        "record_count": len(records),
        "total_row_count": len(records),
        "sharded_flag": False,
        "shard_count": 0,
        "shard_manifest_refs": [],
        "records": records,
        **BOUNDARY_COUNT_FIELDS,
        **NO_AUTHORITY_FLAGS,
    }


def build_root_payload(
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _base_payload(filename=filename, records=records, source_inputs=source_inputs)
    payload["aggregate_counts"] = aggregate_counts(records)
    payload["authority_counts"] = dict(BOUNDARY_COUNT_FIELDS)
    if extra:
        payload.update(extra)
    return payload


def load_report_records(repo_root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    rows: list[dict[str, Any]] = []
    for shard_path in payload.get("shard_files") or []:
        shard_payload = read_json(p.resolve_repo_relative(repo_root, shard_path))
        rows.extend(records_from_payload(shard_payload))
    return rows


def aggregate_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counter = Counter()
    for row in rows:
        for key, value in row.items():
            if key.endswith("_status") or key in {
                "lane",
                "primary_divergence_class",
                "remediation_family",
                "repairability",
                "stress_dimension",
                "sensitivity_bucket",
                "truth_status",
            }:
                status_counter[f"{key}={value}"] += 1
    return {
        "row_count": len(rows),
        "status_counts": {key: status_counter[key] for key in sorted(status_counter)},
        "candidate_packet_count": len({row.get("candidate_packet_id") for row in rows if row.get("candidate_packet_id")}),
    }


def file_size_summary(repo_root: Path, filenames: tuple[str, ...]) -> dict[str, Any]:
    root_sizes = []
    shard_sizes = []
    for filename in filenames:
        path = repo_root / p.GENERATED_DIR / filename
        if path.exists():
            root_sizes.append((filename, path.stat().st_size))
            payload = read_json(path)
            for shard_path in payload.get("shard_files") or []:
                resolved = p.resolve_repo_relative(repo_root, shard_path)
                if resolved.exists():
                    shard_sizes.append((shard_path, resolved.stat().st_size))
    largest_root = max(root_sizes, key=lambda item: item[1]) if root_sizes else ("", 0)
    largest_shard = max(shard_sizes, key=lambda item: item[1]) if shard_sizes else ("", 0)
    return {
        "largest_root_report_path": largest_root[0],
        "largest_root_report_size_bytes": largest_root[1],
        "largest_shard_path": largest_shard[0],
        "largest_shard_size_bytes": largest_shard[1],
        "total_shard_count": len(shard_sizes),
        "root_reports_over_10_mib": [name for name, size in root_sizes if size > ROOT_REPORT_LIMIT_BYTES],
        "shards_over_25_mib": [name for name, size in shard_sizes if size > SHARD_LIMIT_BYTES],
        "root_report_size_counts": stable_counter(name for name, _size in root_sizes),
    }
