"""Load PR159 upstream artifacts without network or side effects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .io import as_list, as_mapping, read_json


def _record_count(payload: Any) -> int | None:
    if isinstance(payload, list):
        return len(payload)
    if not isinstance(payload, Mapping):
        return None
    for key in (
        "record_count",
        "row_count",
        "request_count",
        "target_count",
        "total_source_target_records",
        "atomicrows_source_required_total",
        "pr154_retry_total",
    ):
        value = payload.get(key)
        if isinstance(value, int):
            return value
    for key in (
        "records",
        "requests",
        "source_capture_candidate_packets",
        "official_source_retrieval_target_queue",
        "per_target_materialization_records",
    ):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
    return None


def _schema_version(payload: Any) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    for key in ("schema_version", "artifact_version", "report_version", "packet_version"):
        value = payload.get(key)
        if value is not None:
            return str(value)
    return None


def artifact_receipt(
    repo_root: Path,
    path: Path,
    *,
    artifact_role: str,
    required_or_optional: str,
    consumed: bool | None = None,
    fallback_used: bool = False,
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
        "required_or_optional": required_or_optional,
        "fallback_used": fallback_used,
        "record_count_if_available": _record_count(payload),
        "schema_version_if_available": _schema_version(payload),
        "authority_class": c.AUTHORITY_CLASS,
        "no_runtime_execution_confirmation": True,
    }


def load_json_if_present(repo_root: Path, path: Path) -> Mapping[str, Any]:
    full_path = repo_root / path
    if not full_path.exists():
        return {}
    return as_mapping(read_json(full_path))


def load_pr154_retry_records(repo_root: Path) -> list[Mapping[str, Any]]:
    payload = as_mapping(read_json(repo_root / c.PR157_PR154_REGISTRY_PATH))
    records = [
        as_mapping(item)
        for item in as_list(payload.get("records"))
        if item.get("source_population") == "PR154_PUBLIC_EXTERNAL_RETRY"
    ]
    return sorted(records, key=lambda item: str(item.get("target_id")))


def load_pr153r_seed_records(repo_root: Path) -> list[Mapping[str, Any]]:
    payload = read_json(repo_root / c.PR153R_SEED_MAP_PATH)
    return sorted([as_mapping(item) for item in as_list(payload)], key=lambda item: str(item.get("retrieval_target_id")))


def load_atomicrows_source_required_records(repo_root: Path) -> list[Mapping[str, Any]]:
    registry = as_mapping(read_json(repo_root / c.PR157_ATOMICROWS_REGISTRY_PATH))
    records: list[Mapping[str, Any]] = []
    for shard_ref in as_list(registry.get("shards")):
        shard = as_mapping(shard_ref)
        shard_path = shard.get("shard_path")
        if shard_path:
            payload = as_mapping(read_json(repo_root / Path(str(shard_path))))
            records.extend(as_mapping(item) for item in as_list(payload.get("records")))
    wanted = {"PUBLIC_EXTERNAL_SOURCE_REQUIRED", "PARAMETER_RANGE_SOURCE_REQUIRED"}
    return sorted(
        [item for item in records if item.get("source_requirement_class") in wanted],
        key=lambda item: str(item.get("row_id_or_row_ref")),
    )


def load_selection_overlay_records(repo_root: Path) -> list[Mapping[str, Any]]:
    payload = as_mapping(read_json(repo_root / c.PR158_SELECTION_OVERLAY_REGISTRY_PATH))
    return sorted(
        [as_mapping(item) for item in as_list(payload.get("records"))],
        key=lambda item: str(item.get("row_id")),
    )


def overlay_by_row_id(records: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(item.get("row_id")): item for item in records if item.get("row_id")}


def seed_by_retry_target_id(records: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    by_id: dict[str, Mapping[str, Any]] = {}
    for item in records:
        retrieval_target_id = str(item.get("retrieval_target_id"))
        by_id[retrieval_target_id] = item
        by_id[f"PR154_BRIDGE__{retrieval_target_id}"] = item
    return by_id

