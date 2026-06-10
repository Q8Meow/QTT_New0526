"""Report sharding helpers for PR165-D."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import authority_absence_confirmation, authority_boundary_record, authority_zero_counts
from .central_vocab import AUTHORITY_CLASS, PR_ID, VALIDATION_STATUS
from .json_io import json_text, read_json, records_from_payload

ROOT_REPORT_LIMIT_BYTES = 10 * 1024 * 1024
SHARD_LIMIT_BYTES = 25 * 1024 * 1024
DEFAULT_SHARD_ROW_TARGET = 1000

VOCAB_REFS = (
    "src/qtt/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection/central_vocab.py",
    "src/qtt/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection/authority_policy.py",
    "src/qtt/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection/scenario_selection_policy.py",
    "src/qtt/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection/score_normalization.py",
)


def encoded_json_size(payload: Any, *, compact: bool = False) -> int:
    return len(json_text(payload, compact=compact).encode("utf-8"))


def shard_rows(rows: list[dict[str, Any]], shard_size: int = DEFAULT_SHARD_ROW_TARGET) -> list[list[dict[str, Any]]]:
    if not rows:
        return []
    return [rows[index : index + shard_size] for index in range(0, len(rows), shard_size)]


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
        "authority_policy_module_ref": "src.qtt.stage1_prediction_markets.pr165_d_scenario_qku_combination_selection.authority_policy",
        "authority_boundary": authority_boundary_record(),
        "authority_boundary_ref": authority_boundary_record()["authority_boundary_ref"],
        "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
        "validation_status": VALIDATION_STATUS,
        "source_inputs": source_inputs,
        "upstream_pr_refs": ["PR165", "PR165-B", "PR165-C", "PR208"],
        "downstream_pr_routes": [
            "PR166-S",
            "PR166-Q",
            "PR162E",
            "PR162F",
            "PR162E-Q",
            "dashboard_agent",
            "governance_agent",
            "commander_agent",
        ],
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


def build_sharded_payloads(
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    report_name = filename.replace(".report.json", "")
    chunks = shard_rows(records)
    shard_payloads: dict[str, dict[str, Any]] = {}
    shard_files: list[str] = []
    shard_counts: list[int] = []
    shard_refs: list[dict[str, Any]] = []
    shard_count = len(chunks)
    for index, chunk in enumerate(chunks, start=1):
        shard_name = f"{report_name}.part_{index:04d}_of_{shard_count:04d}.report.json"
        rel_path = p.normalize_repo_ref(p.SHARD_DIR / shard_name)
        shard_payload = _base_payload(
            filename=shard_name,
            records=chunk,
            source_inputs=source_inputs,
            report_name=report_name,
        )
        shard_payload.update(
            {
                "parent_report_filename": filename,
                "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
                "part_ref": f"PR165_D_PART::{index:04d}",
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
        shard_counts.append(len(chunk))
        shard_refs.append(
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
            "shard_manifest_refs": shard_refs,
            "shard_record_counts": shard_counts,
            "largest_shard_record_count": max(shard_counts) if shard_counts else 0,
            "records_omitted_for_sharding_flag": True,
            "full_records_only_in_shards_flag": True,
            "canonical_records_location": p.normalize_repo_ref(p.SHARD_DIR),
            "aggregate_counts": aggregate_counts(records),
            "authority_counts": authority_zero_counts(),
            "authority_absence_confirmation": authority_absence_confirmation(),
        }
    )
    return compact_payload, shard_payloads


def load_report_records(repo_root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    rows: list[dict[str, Any]] = []
    for shard_path in payload.get("shard_files") or []:
        rows.extend(records_from_payload(read_json(p.resolve_repo_relative(repo_root, shard_path))))
    return rows


def aggregate_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counter = Counter()
    candidates: set[str] = set()
    qkus: set[str] = set()
    batches: set[str] = set()
    for row in rows:
        if row.get("candidate_packet_id"):
            candidates.add(str(row["candidate_packet_id"]))
        if row.get("qku_id"):
            qkus.add(str(row["qku_id"]))
        if row.get("batch_id"):
            batches.add(str(row["batch_id"]))
        for key, value in row.items():
            if key.endswith("_status") or key in {
                "computability_action_status",
                "scenario_selection_bucket",
                "readiness_classification",
                "target_future_pr",
                "no_orphan_status",
                "memory_classification",
                "memory_action_policy",
            }:
                status_counter[f"{key}={value}"] += 1
    return {
        "row_count": len(rows),
        "candidate_packet_count": len(candidates),
        "qku_count": len(qkus),
        "batch_count": len(batches),
        "status_counts": {key: status_counter[key] for key in sorted(status_counter)},
    }


def file_size_summary(repo_root: Path, report_filenames: tuple[str, ...]) -> dict[str, Any]:
    root_sizes = []
    shard_sizes = []
    for filename in report_filenames:
        root_path = repo_root / p.GENERATED_DIR / filename
        if root_path.exists():
            root_sizes.append(root_path.stat().st_size)
            payload = read_json(root_path)
            for shard_path in payload.get("shard_files") or []:
                resolved = p.resolve_repo_relative(repo_root, shard_path)
                if resolved.exists():
                    shard_sizes.append(resolved.stat().st_size)
    return {
        "root_report_count": len(root_sizes),
        "shard_report_count": len(shard_sizes),
        "largest_root_report_size_bytes": max(root_sizes) if root_sizes else 0,
        "largest_shard_report_size_bytes": max(shard_sizes) if shard_sizes else 0,
        "root_reports_below_10_mib": all(size <= ROOT_REPORT_LIMIT_BYTES for size in root_sizes),
        "shard_reports_below_25_mib": all(size <= SHARD_LIMIT_BYTES for size in shard_sizes),
    }
