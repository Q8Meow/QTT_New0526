"""Input discovery and read receipts for PR157."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .io import as_list, as_mapping, read_json, rel_path


def _record_count(payload: Any) -> int | None:
    if isinstance(payload, list):
        return len(payload)
    if not isinstance(payload, Mapping):
        return None
    for key in (
        "records",
        "per_target_materialization_records",
        "per_target_closure_records",
        "per_target_records",
        "source_capture_candidate_packets",
        "family_materialization",
        "capture_progress_ledger",
    ):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
    counts = as_mapping(payload.get("counts"))
    for key in (
        "atomicrows_universe_confirmed_count",
        "input_pr155_total_records",
        "input_pr154_total_records",
    ):
        if isinstance(counts.get(key), int):
            return counts[key]
    for key in (
        "atomicrows_total_universe_count",
        "atomicrows_universe_confirmed_count",
        "exact_row_source_record_count",
        "expected_exact_row_record_count",
    ):
        if isinstance(payload.get(key), int):
            return payload[key]
    return None


def _schema_version(payload: Any) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    for key in (
        "schema_version",
        "roster_schema_version",
        "artifact_version",
        "report_version",
        "record_version",
    ):
        value = payload.get(key)
        if value is not None:
            return str(value)
    return None


def artifact_receipt(
    repo_root: Path,
    path: Path,
    *,
    artifact_role: str,
    required: bool,
    fallback_used: bool = False,
    consumed: bool | None = None,
    authority_class: str = c.AUTHORITY_CLASS,
) -> dict[str, Any]:
    full_path = repo_root / path
    exists = full_path.exists()
    payload: Any = None
    if exists and full_path.is_file() and full_path.suffix.lower() in {".json", ".packet"}:
        try:
            payload = read_json(full_path)
        except json.JSONDecodeError:
            payload = None
    if consumed is None:
        consumed = exists
    return {
        "path": path.as_posix(),
        "exists": exists,
        "consumed": bool(consumed and exists),
        "artifact_role": artifact_role,
        "required_or_optional": "required" if required else "optional",
        "fallback_used": fallback_used,
        "record_count_if_available": _record_count(payload),
        "schema_version_if_available": _schema_version(payload),
        "authority_class": authority_class,
        "no_runtime_execution_confirmation": True,
    }


def load_json_if_present(repo_root: Path, path: Path) -> Mapping[str, Any]:
    full_path = repo_root / path
    if not full_path.exists():
        return {}
    payload = read_json(full_path)
    return as_mapping(payload)


def load_jsonl_rows(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((repo_root / c.EXACT_ROW_SOURCE_DIR).glob("*.jsonl")):
        rel = Path(rel_path(repo_root, path))
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = as_mapping(json.loads(line))
            row_copy = dict(row)
            row_copy["_source_jsonl_path"] = rel.as_posix()
            rows.append(row_copy)
    return sorted(rows, key=lambda item: (int(item.get("row_index") or 0), str(item.get("row_id"))))


def pr154_records(repo_root: Path) -> list[Mapping[str, Any]]:
    payload = load_json_if_present(repo_root, c.UPSTREAM_PR154_REPORT_PATH)
    return [as_mapping(record) for record in as_list(payload.get("per_target_materialization_records"))]


def pr155_records_by_pr154_id(repo_root: Path) -> dict[str, Mapping[str, Any]]:
    payload = load_json_if_present(repo_root, c.UPSTREAM_PR155_REGISTRY_PATH)
    records = [as_mapping(record) for record in as_list(payload.get("records"))]
    return {
        str(record.get("source_pr154_record_id")): record
        for record in records
        if record.get("source_pr154_record_id")
    }


def pr156_records_by_source_ref(repo_root: Path) -> dict[str, Mapping[str, Any]]:
    payload = load_json_if_present(repo_root, c.UPSTREAM_PR156_REGISTRY_PATH)
    records = [as_mapping(record) for record in as_list(payload.get("records"))]
    indexed: dict[str, Mapping[str, Any]] = {}
    for record in records:
        for key in ("source_record_ref", "pr154_completion_ref", "pr155_registry_ref"):
            value = record.get(key)
            if value:
                indexed[str(value)] = record
    return indexed
