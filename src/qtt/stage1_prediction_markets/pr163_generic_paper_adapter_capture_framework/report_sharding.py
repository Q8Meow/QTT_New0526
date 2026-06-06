"""Report sharding helpers for large PR163 generated registries."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import BOUNDARY_COUNT_FIELDS, NO_AUTHORITY_FLAGS, PR_ID
from .json_io import json_text, read_json, records_from_payload, stable_counter


TRANSITION_REGISTRY_REPORT_FILENAME = "PR163_PaperOrderStateTransitionRegistry.report.json"
TRANSITION_REGISTRY_REPORT_NAME = "PR163_PaperOrderStateTransitionRegistry"
TRANSITION_REGISTRY_SHARD_ROW_TARGET = 5000
GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES = 50 * 1024 * 1024


def shard_rows(rows: list[dict[str, Any]], shard_size: int) -> list[list[dict[str, Any]]]:
    if shard_size <= 0:
        return [rows]
    return [rows[index : index + shard_size] for index in range(0, len(rows), shard_size)]


def encoded_json_size(payload: Any, *, compact: bool = False) -> int:
    return len(json_text(payload, compact=compact).encode("utf-8"))


def build_transition_registry_payloads(
    payload: dict[str, Any],
    *,
    shard_size: int = TRANSITION_REGISTRY_SHARD_ROW_TARGET,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    rows = records_from_payload(payload)
    chunks = shard_rows(rows, shard_size)
    shard_payloads: dict[str, dict[str, Any]] = {}
    shard_manifest_refs: list[dict[str, Any]] = []
    shard_files: list[str] = []
    shard_record_counts: list[int] = []
    shard_count = len(chunks)

    for index, chunk in enumerate(chunks, start=1):
        shard_name = (
            f"{TRANSITION_REGISTRY_REPORT_NAME}.shard_{index:04d}_of_{shard_count:04d}.report.json"
        )
        rel_path = (p.SHARD_DIR / shard_name).as_posix()
        shard_payload = {
            **payload,
            **BOUNDARY_COUNT_FIELDS,
            "pr_id": PR_ID,
            "report_name": TRANSITION_REGISTRY_REPORT_NAME,
            "records": chunk,
            "record_count": len(chunk),
            "total_record_count": len(rows),
            "total_row_count": len(rows),
            "parent_report_filename": TRANSITION_REGISTRY_REPORT_FILENAME,
            "shard_ref": f"PR163_PAPER_ORDER_STATE_TRANSITION_SHARD::{index:04d}",
            "shard_index": index,
            "shard_count": shard_count,
            "sharded_flag": False,
            "records_canonical_shard_flag": True,
            "aggregate_transition_counts": aggregate_transition_counts(chunk),
            "aggregate_state_counts": aggregate_state_counts(chunk),
            "authority_counts": dict(BOUNDARY_COUNT_FIELDS),
        }
        shard_payloads[rel_path] = shard_payload
        shard_files.append(rel_path)
        shard_record_counts.append(len(chunk))
        shard_manifest_refs.append(
            {
                "shard_ref": shard_payload["shard_ref"],
                "shard_path": rel_path,
                "shard_index": index,
                "row_count": len(chunk),
                "first_state_transition_ref": chunk[0]["state_transition_ref"] if chunk else None,
                "last_state_transition_ref": chunk[-1]["state_transition_ref"] if chunk else None,
                "estimated_shard_size_bytes": encoded_json_size(shard_payload, compact=True),
                "below_github_recommended_warning_threshold": (
                    encoded_json_size(shard_payload, compact=True)
                    < GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES
                ),
            }
        )

    compact_payload = {
        **payload,
        **BOUNDARY_COUNT_FIELDS,
        "pr_id": PR_ID,
        "report_name": TRANSITION_REGISTRY_REPORT_NAME,
        "records": [],
        "record_count": len(rows),
        "total_record_count": len(rows),
        "total_row_count": len(rows),
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
        "aggregate_transition_counts": aggregate_transition_counts(rows),
        "aggregate_state_counts": aggregate_state_counts(rows),
        "authority_counts": dict(BOUNDARY_COUNT_FIELDS),
        "authority_absence_confirmation": {
            "paper_result_authority": True,
            "profit_authority": True,
            "live_order_authority": True,
            "source_acceptance_authority": True,
            "connector_binding_authority": True,
            "private_state_authority": True,
            "quantum_backend_or_advantage_authority": True,
            "llm_runtime_or_order_authority": True,
            "checksum_authority": True,
        },
        **NO_AUTHORITY_FLAGS,
    }
    return compact_payload, shard_payloads


def load_transition_registry_records(
    repo_root: Path,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    rows: list[dict[str, Any]] = []
    for shard_ref in payload.get("shard_files") or []:
        shard_payload = read_json(p.resolve_repo_relative(repo_root, shard_ref))
        rows.extend(records_from_payload(shard_payload))
    return rows


def aggregate_transition_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(f"{row.get('prior_state')}->{row.get('next_state')}" for row in rows)
    return {key: counts[key] for key in sorted(counts)}


def aggregate_state_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return stable_counter(row.get("next_state") for row in rows)
