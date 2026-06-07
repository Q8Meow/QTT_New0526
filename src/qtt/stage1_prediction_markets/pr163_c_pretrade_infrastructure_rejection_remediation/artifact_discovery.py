"""Artifact discovery and sharded report loading for PR163-C."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import read_json, records_from_payload


def load_report_payload(repo_root: Path, filename: str) -> dict[str, Any]:
    payload = read_json(repo_root / p.GENERATED_DIR / filename)
    if not isinstance(payload, dict):
        raise ValueError(f"{filename} is not a JSON object")
    return payload


def load_report_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    payload = load_report_payload(repo_root, filename)
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    rows: list[dict[str, Any]] = []
    for shard_path in payload.get("shard_files") or payload.get("shard_paths") or []:
        shard_payload = read_json(p.resolve_repo_relative(repo_root, shard_path))
        rows.extend(records_from_payload(shard_payload))
    return rows


def index_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate = row.get("candidate_id") or row.get("candidate_packet_id")
        if candidate:
            indexed[str(candidate)] = row
    return indexed


def index_by_candidate_qku(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        candidate = row.get("candidate_id") or row.get("candidate_packet_id")
        qku = row.get("qku_id")
        if candidate and qku:
            indexed[(str(candidate), str(qku))] = row
    return indexed
