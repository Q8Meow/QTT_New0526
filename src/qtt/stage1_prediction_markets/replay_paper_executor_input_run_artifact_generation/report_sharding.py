"""Deterministic PR161F report sharding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .compact_records import (
    COMPACT_RECORD_VERSION,
    compact_records_for_report,
    hoist_compact_record_defaults,
)
from .json_io import encoded_json_size, stable_counter


SUMMARY_COUNT_FIELDS = (
    "agent_role_id",
    "assigned_agent_role",
    "agent_task_state",
    "audit_status",
    "candidate_source_class",
    "comparison_state",
    "compatibility_state",
    "dataset_authority_class",
    "executor_capability_state",
    "execution_state",
    "failure_class",
    "handoff_state",
    "result_packet_emission_eligibility_state",
    "run_artifact_class",
    "scan_status",
    "source_route",
    "value_authority_class",
)


def payloads_for_write(
    payloads: dict[str, dict[str, Any]],
    *,
    shared_dictionary: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    main_payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    manifest_records: list[dict[str, Any]] = []
    for filename in c.REPORT_FILENAMES:
        payload = dict(payloads[filename])
        records = list(payload.get("records") or [])
        payload["report_filename"] = filename
        payload["schema_ref"] = c.REPORT_SCHEMA_REFS.get(filename)
        payload["summary_counts"] = _summary_counts(records)
        if not _should_shard(payload, records):
            payload["sharded_flag"] = False
            payload["shard_count"] = 0
            payload["shard_manifest_ref"] = None
            payload["total_record_count"] = len(records)
            payload["shard_files"] = []
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
            compact_chunk = compact_records_for_report(
                chunk,
                filename,
                payload["schema_ref"],
                shared_dictionary,
            )
            compact_defaults, compact_chunk = hoist_compact_record_defaults(compact_chunk)
            shard_payload = dict(payload)
            shard_payload["records"] = compact_chunk
            shard_payload["compact_records_flag"] = True
            shard_payload["compact_record_version"] = COMPACT_RECORD_VERSION
            shard_payload["compact_record_defaults"] = compact_defaults
            shard_payload["shared_dictionary_ref"] = c.SHARED_DICTIONARY_REPORT_PATH.as_posix()
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
        payload["full_records_only_in_shards_flag"] = False
        payload["full_records_resolvable_from_compact_records_flag"] = True
        payload["full_records_canonical_location"] = "PR161F_COMPACT_SHARDS_PLUS_SHARED_DICTIONARY"
        payload["compact_records_flag"] = True
        payload["shared_dictionary_ref"] = c.SHARED_DICTIONARY_REPORT_PATH.as_posix()
        main_payloads[filename] = payload
        manifest_records.append(
            {
                "record_id": f"PR161F-SHARD-MANIFEST-{Path(filename).stem}",
                "report_type": payload["report_type"],
                "report_filename": filename,
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
                "full_records_only_in_shards_flag": False,
                "compact_records_canonical_flag": True,
                "shared_dictionary_ref": c.SHARED_DICTIONARY_REPORT_PATH.as_posix(),
                "canonical_records_location": "PR161F_COMPACT_SHARDS_PLUS_SHARED_DICTIONARY",
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
            str(record[field])
            for record in records
            if field in record and isinstance(record[field], (str, int, bool))
        ]
        if values:
            counts[f"by_{field}"] = stable_counter(values)
    return counts

