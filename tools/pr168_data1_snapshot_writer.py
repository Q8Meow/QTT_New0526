#!/usr/bin/env python3
"""Deterministic JSON/JSONL artifact writers for PR168-DATA1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

from tools.pr168_data1_config import (
    authority_flags,
    generated_ref,
    manifest_path,
    route_defaults,
)


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    materialized = [dict(row) for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in materialized:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return materialized


def write_shard_manifest(
    jsonl_path: Path,
    rows: list[Mapping[str, object]],
    *,
    manifest_id: str,
    venue: str,
    data_family: str,
    created_at_utc: str,
    source_refs: list[str],
) -> dict[str, object]:
    route = route_defaults("market_data")
    row_id_key = "l2_replay_row_id" if data_family.startswith("forward_l2") else "snapshot_row_id"
    manifest = {
        "manifest_id": manifest_id,
        "created_at_utc": created_at_utc,
        "venue": venue,
        "data_family": data_family,
        "shard_path": generated_ref(jsonl_path),
        "row_count": len(rows),
        "row_refs": [str(row.get(row_id_key) or row.get("action_id") or row.get("feature_row_id")) for row in rows],
        "source_refs": source_refs,
        "downstream_consumers": route["downstream_consumers"],
        "downstream_pr_refs": route["downstream_pr_refs"],
        "owning_agent": route["owning_agent"],
        "consumer_agents": route["consumer_agents"],
        "validator_refs": route["validator_refs"],
        "test_refs": route["test_refs"],
        "no_orphan_status": "NO_ORPHAN_ROUTED",
        "authority_class": "PUBLIC_READ_ONLY_JSONL_SHARD_MANIFEST",
        "terminal_by_nature_flag": False,
        "terminal_reason_code": None,
        **authority_flags(),
    }
    write_json(manifest_path(jsonl_path), manifest)
    return manifest
