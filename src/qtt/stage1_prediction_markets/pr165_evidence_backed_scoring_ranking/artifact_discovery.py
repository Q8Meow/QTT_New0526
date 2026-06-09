"""PR165 upstream artifact discovery and sharded report loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import read_json, records_from_payload


@dataclass(frozen=True)
class Discovery:
    rows: list[dict[str, Any]]
    source_inputs: list[str]
    missing_required_inputs: list[str]
    optional_present: dict[str, list[str]]
    optional_missing: dict[str, list[str]]


def discover_inputs(repo_root: Path) -> Discovery:
    rows: list[dict[str, Any]] = []
    source_inputs: set[str] = set()
    missing_required: list[str] = []
    for index, rel_path in enumerate(p.REQUIRED_INPUTS, start=1):
        exists = (repo_root / rel_path).exists()
        if not exists:
            missing_required.append(rel_path)
        if exists:
            source_inputs.add(rel_path)
        rows.append(
            {
                "input_consumption_ref": f"PR165_INPUT::{index:06d}",
                "input_path": rel_path,
                "required": True,
                "present": exists,
                "consumption_status": "CONSUMED" if exists else "MISSING_REQUIRED_INPUT",
            }
        )
    optional_present: dict[str, list[str]] = {}
    optional_missing: dict[str, list[str]] = {}
    offset = len(rows)
    for group_index, (group, rel_paths) in enumerate(sorted(p.OPTIONAL_INPUT_GROUPS.items()), start=1):
        present = [rel for rel in rel_paths if (repo_root / rel).exists()]
        missing = [rel for rel in rel_paths if not (repo_root / rel).exists()]
        optional_present[group] = present
        optional_missing[group] = missing
        for item_index, rel_path in enumerate(rel_paths, start=1):
            exists = (repo_root / rel_path).exists()
            if exists:
                source_inputs.add(rel_path)
            rows.append(
                {
                    "input_consumption_ref": f"PR165_OPTIONAL_INPUT::{offset + group_index:04d}::{item_index:04d}",
                    "input_group": group,
                    "input_path": rel_path,
                    "required": False,
                    "present": exists,
                    "consumption_status": "OPTIONAL_CONTEXT_CONSUMED" if exists else "OPTIONAL_CONTEXT_MISSING_RECEIPT_EMITTED",
                }
            )
    for manifest_name in (
        "PR163_B_ReportManifest.report.json",
        "PR163_C_ReportManifest.report.json",
        "PR164_ReportManifest.report.json",
    ):
        manifest_path = repo_root / p.GENERATED_DIR / manifest_name
        if manifest_path.exists():
            source_inputs.add(str((p.GENERATED_DIR / manifest_name).as_posix()))
            for record in load_records(repo_root, manifest_name):
                report_filename = record.get("report_filename")
                if report_filename:
                    report_path = str((p.GENERATED_DIR / str(report_filename)).as_posix())
                    if (repo_root / report_path).exists():
                        source_inputs.add(report_path)
                for shard_path in record.get("shard_paths") or []:
                    if (repo_root / str(shard_path)).exists():
                        source_inputs.add(str(shard_path))
    return Discovery(
        rows=rows,
        source_inputs=sorted(source_inputs),
        missing_required_inputs=missing_required,
        optional_present=optional_present,
        optional_missing=optional_missing,
    )


def load_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    payload = read_json(repo_root / p.GENERATED_DIR / filename)
    rows = records_from_payload(payload)
    for shard in payload.get("shard_files") or payload.get("shard_paths") or []:
        shard_path = p.resolve_repo_relative(repo_root, shard)
        if shard_path.exists():
            rows.extend(records_from_payload(read_json(shard_path)))
    return rows


def load_single_record(repo_root: Path, filename: str) -> dict[str, Any]:
    rows = load_records(repo_root, filename)
    if not rows:
        payload = read_json(repo_root / p.GENERATED_DIR / filename)
        return {key: value for key, value in payload.items() if key != "records"}
    return rows[0]


def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows if row.get(key)}
