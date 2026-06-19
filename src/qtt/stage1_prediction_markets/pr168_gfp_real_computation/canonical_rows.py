"""Canonical row-key construction for PR168-GFP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import read_json, read_jsonl


QKU_REPORT = Path("docs/master_plan/generated/PR161C_QKU9360PrimaryMaterializationRegistry.report.json")
CPV1_REPORT = Path("docs/master_plan/generated/PR162D_QKUReplayPaperCandidateExpansion.report.json")
ATOMICROWS_JSONL = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
PR154_REPORT = Path("docs/master_plan/generated/PR154_AtomicRowsParameterDefaultValueMaterializationGate.report.json")
RESIDUAL_REPORT = Path("docs/master_plan/generated/PR161B_MasterPlanResidualCandidateInventory.report.json")


@dataclass(frozen=True)
class Inventory:
    qku_records: list[dict[str, Any]]
    candidate_packet_records: list[dict[str, Any]]
    atomicrows_records: list[dict[str, Any]]
    pr154_records: list[dict[str, Any]]
    residual_records: list[dict[str, Any]]
    qku_manifest: dict[str, Any]
    candidate_manifest: dict[str, Any]
    pr154_manifest: dict[str, Any]
    residual_manifest: dict[str, Any]


def load_inventory(repo_root: Path) -> Inventory:
    qku_manifest = read_json(repo_root / QKU_REPORT)
    qku_records: list[dict[str, Any]] = []
    for shard in qku_manifest["shard_files"]:
        qku_records.extend(read_json(repo_root / shard).get("records", []))

    candidate_manifest = read_json(repo_root / CPV1_REPORT)
    candidate_packet_records: list[dict[str, Any]] = []
    for shard in candidate_manifest["shard_files"]:
        candidate_packet_records.extend(read_json(repo_root / shard).get("records", []))

    pr154_manifest = read_json(repo_root / PR154_REPORT)
    residual_manifest = read_json(repo_root / RESIDUAL_REPORT)
    return Inventory(
        qku_records=qku_records,
        candidate_packet_records=candidate_packet_records,
        atomicrows_records=read_jsonl(repo_root / ATOMICROWS_JSONL),
        pr154_records=pr154_manifest.get("per_target_materialization_records", []),
        residual_records=residual_manifest.get("records", []),
        qku_manifest=qku_manifest,
        candidate_manifest=candidate_manifest,
        pr154_manifest=pr154_manifest,
        residual_manifest=residual_manifest,
    )


def canonical_key_from_qku_id(qku_id: str) -> str:
    return f"QKU::{qku_id}"


def atomicrows_qku_id(row: dict[str, Any]) -> str:
    exact_row_id = str(row.get("exact_row_id") or row.get("source_record_stable_identity") or row.get("row_index"))
    return f"QKU-ATOMICROW-{exact_row_id}"


def canonical_key_for_atomicrow(row: dict[str, Any]) -> str:
    return canonical_key_from_qku_id(atomicrows_qku_id(row))


def canonical_key_for_pr154(row: dict[str, Any]) -> str:
    row_id = str(row.get("pr154_record_id") or row.get("source_pr153s_target_id") or row.get("target_field_path"))
    return f"PR154::{row_id}"


def source_pointer(path: Path | str, index: int, row_id: str | None = None) -> str:
    suffix = f"#{index:06d}"
    if row_id:
        suffix = f"{suffix}:{row_id}"
    return f"{Path(path).as_posix()}{suffix}"
