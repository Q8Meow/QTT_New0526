"""Deterministic PR162C report sharding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import encoded_json_size, stable_counter


SUMMARY_COUNT_FIELDS = (
    "source_class",
    "source_lane",
    "source_quality_tier",
    "terminal_status",
    "strict_coverage_status",
    "blocker_code",
    "primary_execution_class",
    "primary_market_scope",
    "stage1_prediction_market_activation_status",
    "dormancy_status",
    "authority_class",
    "access_rights_status",
    "formula_family",
    "algorithm_family",
    "compatible_solver_family",
)


def payloads_for_write(
    payloads: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    main_payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    manifest_records: list[dict[str, Any]] = []
    for filename in c.REPORT_FILENAMES:
        if filename == c.SHARD_MANIFEST_REPORT_FILENAME:
            continue
        payload = dict(payloads[filename])
        records = list(payload.get("records") or [])
        payload["report_filename"] = filename
        payload["schema_ref"] = c.REPORT_SCHEMA_REFS[filename]
        payload["summary_counts"] = _summary_counts(records)
        if not _should_shard(payload, records):
            payload["sharded_flag"] = False
            payload["shard_count"] = 0
            payload["shard_manifest_ref"] = None
            payload["total_record_count"] = len(records)
            payload["shard_files"] = []
            payload["record_count"] = len(records)
            main_payloads[filename] = payload
            continue
        chunks = [
            records[index : index + c.REPORT_SHARD_RECORD_TARGET]
            for index in range(0, len(records), c.REPORT_SHARD_RECORD_TARGET)
        ]
        shard_files: list[str] = []
        shard_records: list[dict[str, Any]] = []
        for index, chunk in enumerate(chunks, start=1):
            shard_name = f"{Path(filename).stem}.shard_{index:04d}.json"
            rel_path = (c.SHARD_DIR / shard_name).as_posix()
            shard_payload = dict(payload)
            shard_payload["records"] = chunk
            shard_payload["record_count"] = len(chunk)
            shard_payload["total_record_count"] = len(records)
            shard_payload["parent_report_filename"] = filename
            shard_payload["shard_index"] = index
            shard_payload["shard_count"] = len(chunks)
            shard_payload["sharded_flag"] = False
            shard_payload["shard_manifest_ref"] = c.SHARD_MANIFEST_REPORT_PATH.as_posix()
            shard_payload["summary_counts"] = _summary_counts(chunk)
            shard_payloads[rel_path] = shard_payload
            shard_files.append(rel_path)
            shard_records.append(
                {
                    "record_count": len(chunk),
                    "schema_ref": payload["schema_ref"],
                    "shard_file": rel_path,
                    "shard_index": index,
                }
            )
        payload["records"] = []
        payload["preview_records"] = records[: c.REPORT_SHARD_PREVIEW_RECORD_LIMIT]
        payload["preview_record_count"] = len(payload["preview_records"])
        payload["record_count"] = len(records)
        payload["total_record_count"] = len(records)
        payload["unsharded_record_count"] = len(records)
        payload["sharded_flag"] = True
        payload["shard_count"] = len(chunks)
        payload["shard_manifest_ref"] = c.SHARD_MANIFEST_REPORT_PATH.as_posix()
        payload["shard_files"] = shard_files
        payload["shard_record_counts"] = [len(chunk) for chunk in chunks]
        payload["largest_shard_record_count"] = max(len(chunk) for chunk in chunks)
        payload["records_omitted_for_sharding_flag"] = True
        payload["full_records_only_in_shards_flag"] = True
        payload["full_records_canonical_location"] = "PR162C_FULL_RECORD_SHARDS"
        main_payloads[filename] = payload
        manifest_records.append(
            {
                "record_id": f"PR162C-SHARD-MANIFEST-{Path(filename).stem}",
                "report_filename": filename,
                "report_type": payload["report_type"],
                "total_record_count": len(records),
                "shard_count": len(chunks),
                "shard_manifest_ref": c.SHARD_MANIFEST_REPORT_PATH.as_posix(),
                "schema_ref": payload["schema_ref"],
                "summary_counts": _summary_counts(records),
                "shard_record_counts": [len(chunk) for chunk in chunks],
                "largest_shard_record_count": max(len(chunk) for chunk in chunks),
                "shard_files": shard_files,
                "shards": shard_records,
                "posix_relative_shard_refs_flag": all("\\" not in path for path in shard_files),
                "full_records_only_in_shards_flag": True,
                "canonical_records_location": "PR162C_FULL_RECORD_SHARDS",
                "created_by_pr": c.PR_ID,
            }
        )
    return main_payloads, shard_payloads, manifest_records


def _should_shard(payload: dict[str, Any], records: list[dict[str, Any]]) -> bool:
    if not records:
        return False
    if len(records) > c.REPORT_SHARD_RECORD_TARGET:
        return True
    return encoded_json_size(payload) > c.REPORT_SHARD_BYTE_THRESHOLD


def _summary_counts(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, Any] = {"total_records": len(records)}
    for field in SUMMARY_COUNT_FIELDS:
        values = [
            record[field]
            for record in records
            if field in record and isinstance(record[field], (str, int, bool))
        ]
        if values:
            counts[f"by_{field}"] = stable_counter(values)
    return counts
