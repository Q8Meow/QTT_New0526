"""Input discovery and consumption audit for PR165-D."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import authority_zero_counts
from .central_vocab import (
    AUTHORITY_BOUNDARY_REF,
    DOWNSTREAM_PR_ROUTES,
    NO_ORPHAN_STATUS,
    UPSTREAM_PR_REFS,
    VALIDATION_STATUS,
)
from .deterministic_ids import ordinal_ref, stable_ref
from .json_io import read_json, records_from_payload


@dataclass(frozen=True)
class InputDiscovery:
    required_inputs: tuple[str, ...]
    missing_required_inputs: tuple[str, ...]
    optional_present: dict[str, tuple[str, ...]]
    optional_missing: dict[str, tuple[str, ...]]


def discover_inputs(repo_root: Path) -> InputDiscovery:
    required_inputs = tuple(p.normalize_repo_ref(rel) for rel in p.REQUIRED_INPUTS)
    missing_required = tuple(
        rel for rel in required_inputs if not p.resolve_repo_relative(repo_root, rel).exists()
    )
    optional_present: dict[str, tuple[str, ...]] = {}
    optional_missing: dict[str, tuple[str, ...]] = {}
    for group, refs in p.OPTIONAL_INPUT_GROUPS.items():
        normalized = tuple(p.normalize_repo_ref(ref) for ref in refs)
        present = tuple(ref for ref in normalized if p.resolve_repo_relative(repo_root, ref).exists())
        missing = tuple(ref for ref in normalized if not p.resolve_repo_relative(repo_root, ref).exists())
        optional_present[group] = present
        optional_missing[group] = missing
    return InputDiscovery(
        required_inputs=required_inputs,
        missing_required_inputs=missing_required,
        optional_present=optional_present,
        optional_missing=optional_missing,
    )


def source_inputs(discovery: InputDiscovery) -> list[str]:
    inputs = list(discovery.required_inputs)
    for refs in discovery.optional_present.values():
        inputs.extend(refs)
    return sorted(dict.fromkeys(inputs))


def build_input_consumption_records(discovery: InputDiscovery) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, rel in enumerate(discovery.required_inputs, start=1):
        status = (
            "REQUIRED_INPUT_CONSUMED"
            if rel not in discovery.missing_required_inputs
            else "REQUIRED_INPUT_CONSUMPTION_FAILURE"
        )
        records.append(
            {
                "input_consumption_id": ordinal_ref("PR165_D_INPUT_CONSUMPTION", index),
                "source_artifact_ref": rel,
                "input_requirement_type": "REQUIRED_PR165_PR165B_PR165C_PR208_INPUT",
                "consumption_status": status,
                "selection_use": "CANONICAL_SELECTION_INPUT",
                "source_authority_label": "UPSTREAM_QTT_GENERATED_ARTIFACT",
                "upstream_source_pr_refs": list(UPSTREAM_PR_REFS),
                "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
                "owning_agent": "selection_agent",
                "validator": "tools/validate_pr165_d_scenario_qku_combination_selection.py",
                "manifest_entry_ref": "PR165_D_ReportManifest.report.json",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": VALIDATION_STATUS,
                **authority_zero_counts(),
            }
        )
    start = len(records) + 1
    for offset, group in enumerate(sorted(discovery.optional_present), start=start):
        present = list(discovery.optional_present[group])
        missing = list(discovery.optional_missing[group])
        records.append(
            {
                "input_consumption_id": ordinal_ref("PR165_D_INPUT_CONSUMPTION", offset),
                "optional_input_group": group,
                "present_artifact_refs": present,
                "missing_artifact_refs": missing,
                "input_requirement_type": "OPTIONAL_CANDIDATE_OR_PROVISIONAL_INPUT",
                "consumption_status": (
                    "OPTIONAL_INPUT_PRESENT_CANDIDATE_ONLY"
                    if present
                    else "OPTIONAL_INPUT_MISSING_RECEIPT_CREATED"
                ),
                "selection_use": (
                    "PROVISIONAL_SCORING_CONTEXT"
                    if present
                    else "DOWNSTREAM_ROUTE_WITHOUT_SCORE_PROMOTION"
                ),
                "source_authority_label": (
                    "LEGACY_OR_PREPARATORY_QTT_ARTIFACT"
                    if present
                    else "OPTIONAL_UPSTREAM_OUTPUT_NOT_MATERIALIZED"
                ),
                "upstream_source_pr_refs": list(UPSTREAM_PR_REFS),
                "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
                "owning_agent": "selection_agent",
                "validator": "tools/validate_pr165_d_scenario_qku_combination_selection.py",
                "manifest_entry_ref": "PR165_D_ReportManifest.report.json",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": VALIDATION_STATUS,
                **authority_zero_counts(),
            }
        )
    return records


def load_report_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    payload = read_json(repo_root / p.GENERATED_DIR / filename)
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    rows: list[dict[str, Any]] = []
    for shard_path in payload.get("shard_files") or []:
        rows.extend(records_from_payload(read_json(p.resolve_repo_relative(repo_root, shard_path))))
    return rows


def try_load_report_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    path = repo_root / p.GENERATED_DIR / filename
    if not path.exists():
        return []
    return load_report_records(repo_root, filename)


def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows if key in row}


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if key in row:
            grouped.setdefault(str(row[key]), []).append(row)
    return grouped


def artifact_timestamp_or_commit_metadata(repo_root: Path, rel_path: str) -> dict[str, str]:
    path = p.resolve_repo_relative(repo_root, rel_path)
    if not path.exists():
        return {"source_artifact_ref": rel_path, "artifact_state": "NOT_MATERIALIZED"}
    stat = path.stat()
    return {
        "source_artifact_ref": rel_path,
        "artifact_state": "MATERIALIZED",
        "artifact_mtime_epoch": str(int(stat.st_mtime)),
        "artifact_size_bytes": str(stat.st_size),
        "artifact_identity_ref": stable_ref("PR165_D_ARTIFACT_IDENTITY", rel_path, stat.st_size, int(stat.st_mtime)),
    }
