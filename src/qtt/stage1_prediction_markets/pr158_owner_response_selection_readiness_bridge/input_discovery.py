"""Load PR157 and prior artifacts for PR158 without side effects."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .io import as_list, as_mapping, read_json


def load_owner_request_packet(repo_root: Path) -> Mapping[str, Any]:
    return as_mapping(read_json(repo_root / c.OWNER_REQUEST_PATH))


def load_pr154_records(repo_root: Path) -> list[Mapping[str, Any]]:
    payload = as_mapping(read_json(repo_root / c.PR157_PR154_REGISTRY_PATH))
    return [as_mapping(item) for item in as_list(payload.get("records"))]


def load_atomicrows_records(repo_root: Path) -> list[Mapping[str, Any]]:
    registry = as_mapping(read_json(repo_root / c.PR157_ATOMICROWS_REGISTRY_PATH))
    records = [as_mapping(item) for item in as_list(registry.get("records"))]
    for shard_ref in as_list(registry.get("shards")):
        shard = as_mapping(shard_ref)
        shard_path = shard.get("shard_path")
        if shard_path:
            payload = as_mapping(read_json(repo_root / Path(str(shard_path))))
            records.extend(as_mapping(item) for item in as_list(payload.get("records")))
    return sorted(records, key=lambda item: str(item.get("row_id_or_row_ref")))


def owner_requests_by_id(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(item.get("request_id")): as_mapping(item)
        for item in as_list(packet.get("requests"))
        if item.get("request_id")
    }


def atomicrows_by_row_id(records: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(item.get("row_id_or_row_ref")): item for item in records}


def pr154_by_target_id(records: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(item.get("target_id")): item for item in records}

