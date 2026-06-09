"""Report sharding helpers for PR165-C."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import (
    POLICY_MODULE_REF,
    authority_absence_confirmation,
    authority_boundary_record,
    authority_zero_counts,
)
from .central_vocab import AUTHORITY_CLASS, PR_ID, VALIDATION_STATUS
from .json_io import json_text, read_json, records_from_payload

ROOT_REPORT_LIMIT_BYTES = 10 * 1024 * 1024
SHARD_LIMIT_BYTES = 25 * 1024 * 1024
DEFAULT_SHARD_ROW_TARGET = 1000

VOCAB_REFS = (
    "src/qtt/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/central_vocab.py",
    "src/qtt/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/agent_duty_vocab.py",
    "src/qtt/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/memory_consumer_action_vocab.py",
    "src/qtt/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/retest_ingestion_vocab.py",
    "src/qtt/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/agent_conflict_vocab.py",
    "src/qtt/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/computability_action_vocab.py",
    "src/qtt/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/materialization_candidate_vocab.py",
    "src/qtt/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/authority_policy.py",
)


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
                "part_ref": f"PR165_C_PART::{index:04d}",
                "part_index": index,
                "part_count": shard_count,
                "shard_index": index,
                "shard_count": shard_count,
                "record_count": len(chunk),
                "total_record_count": len(records),
                "total_row_count": len(records),
                "records_canonical_part_flag": True,
                "aggregate_counts": aggregate_counts(chunk),
                "authority_counts": authority_zero_counts(),
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
                "below_25_mib_limit": encoded_json_size(shard_payload, compact=True) <= SHARD_LIMIT_BYTES,
            }
        )
    compact_payload = _base_payload(filename=filename, records=[], source_inputs=source_inputs, report_name=report_name)
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
            "authority_counts": authority_zero_counts(),
            "authority_absence_confirmation": authority_absence_confirmation(),
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
        "authority_boundary": authority_boundary_record(),
        "authority_boundary_ref": authority_boundary_record()["authority_boundary_ref"],
        "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
        "validation_status": VALIDATION_STATUS,
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(__import__(p.PACKAGE_IMPORT + ".central_vocab", fromlist=["UPSTREAM_PR_REFS"]).UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(__import__(p.PACKAGE_IMPORT + ".central_vocab", fromlist=["DOWNSTREAM_PR_ROUTES"]).DOWNSTREAM_PR_ROUTES),
        "vocab_refs": list(VOCAB_REFS),
        "record_count": len(records),
        "total_row_count": len(records),
        "sharded_flag": False,
        "shard_count": 0,
        "shard_manifest_refs": [],
        "records": records,
        **authority_zero_counts(),
    }


def build_root_payload(
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _base_payload(filename=filename, records=records, source_inputs=source_inputs)
    payload["aggregate_counts"] = aggregate_counts(records)
    payload["authority_counts"] = authority_zero_counts()
    payload["authority_absence_confirmation"] = authority_absence_confirmation()
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
    qkus: set[str] = set()
    candidates: set[str] = set()
    condition_ids: set[str] = set()
    combination_ids: set[str] = set()
    core_table_ids: set[str] = set()
    for row in rows:
        if row.get("qku_id"):
            qkus.add(str(row["qku_id"]))
        if row.get("candidate_packet_id"):
            candidates.add(str(row["candidate_packet_id"]))
        if row.get("condition_fingerprint_id"):
            condition_ids.add(str(row["condition_fingerprint_id"]))
        if row.get("combination_fingerprint_id"):
            combination_ids.add(str(row["combination_fingerprint_id"]))
        if row.get("core_table_row_id"):
            core_table_ids.add(str(row["core_table_row_id"]))
        for key, value in row.items():
            if key.endswith("_status") or key in {
                "computability_action_status",
                "route_class",
                "memory_action_policy",
                "memory_classification",
                "task_type",
                "task_priority",
                "retest_priority_bucket",
                "no_orphan_status",
            }:
                status_counter[f"{key}={value}"] += 1
    return {
        "row_count": len(rows),
        "status_counts": {key: status_counter[key] for key in sorted(status_counter)},
        "qku_count": len(qkus),
        "candidate_packet_count": len(candidates),
        "condition_fingerprint_count": len(condition_ids),
        "combination_fingerprint_count": len(combination_ids),
        "core_table_row_count": len(core_table_ids),
    }


def file_size_summary(repo_root: Path, report_filenames: tuple[str, ...]) -> dict[str, Any]:
    root_sizes = []
    shard_sizes = []
    for filename in report_filenames:
        path = repo_root / p.GENERATED_DIR / filename
        if path.exists():
            root_sizes.append((filename, path.stat().st_size))
            payload = read_json(path)
            for shard in payload.get("shard_files") or []:
                shard_path = p.resolve_repo_relative(repo_root, shard)
                if shard_path.exists():
                    shard_sizes.append((shard, shard_path.stat().st_size))
    largest_root = max(root_sizes, key=lambda item: item[1]) if root_sizes else ("", 0)
    largest_shard = max(shard_sizes, key=lambda item: item[1]) if shard_sizes else ("", 0)
    return {
        "root_report_count": len(root_sizes),
        "shard_report_count": len(shard_sizes),
        "largest_root_report_path": largest_root[0],
        "largest_root_report_size": largest_root[1],
        "largest_root_report_size_bytes": largest_root[1],
        "largest_shard_path": largest_shard[0],
        "largest_shard_size": largest_shard[1],
        "largest_shard_size_bytes": largest_shard[1],
    }
