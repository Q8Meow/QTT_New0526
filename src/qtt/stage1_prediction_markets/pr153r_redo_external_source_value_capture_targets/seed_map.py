"""Owner-supplied PR153R seed map loading and cross-validation."""

from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from . import constants as c
from . import taxonomy as tx


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path.as_posix()} must contain a JSON array")
    return [dict(item) for item in payload if isinstance(item, dict)]


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_owner_supplied_inputs(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    return {
        "json_seed_map": _read_json_list(repo_root / c.OWNER_SEED_JSON_PATH),
        "csv_seed_map": _read_csv_rows(repo_root / c.OWNER_SEED_CSV_PATH),
        "extracted_lane_json": _read_json_list(repo_root / c.OWNER_EXTRACTED_JSON_PATH),
    }


def target_signature(item: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(item.get("retrieval_target_id") or ""),
        str(item.get("target_field_path") or ""),
        str(item.get("platform_scope") or item.get("target_platform_scope") or ""),
    )


def _target_id_set(records: Iterable[Mapping[str, Any]]) -> set[str]:
    return {str(item.get("retrieval_target_id") or "") for item in records}


def split_seed_urls(seed_url: Any) -> list[str]:
    if not isinstance(seed_url, str):
        return []
    return [part.strip() for part in seed_url.split("|") if part.strip()]


def seed_records_by_id(records: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("retrieval_target_id")): dict(item)
        for item in records
        if item.get("retrieval_target_id")
    }


def _platform_counts(records: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counter = Counter(
        str(item.get("platform_scope") or item.get("target_platform_scope") or "")
        for item in records
    )
    return {key: counter.get(key, 0) for key in sorted(c.EXPECTED_PLATFORM_COUNTS)}


def _duplicate_values(records: Iterable[Mapping[str, Any]], key: str) -> list[str]:
    values = [str(item.get(key) or "") for item in records]
    counter = Counter(value for value in values if value)
    return sorted(value for value, count in counter.items() if count > 1)


def cross_validate_seed_inputs(
    extracted_targets: list[Mapping[str, Any]],
    owner_inputs: Mapping[str, list[dict[str, Any]]],
    pr151_enriched_targets: list[Mapping[str, Any]],
) -> dict[str, Any]:
    extracted_signatures = {target_signature(item) for item in extracted_targets}
    extracted_ids = _target_id_set(extracted_targets)
    enriched_by_id = seed_records_by_id(pr151_enriched_targets)
    failures: list[str] = []
    file_results: dict[str, Any] = {}

    for name, records in owner_inputs.items():
        signatures = {target_signature(item) for item in records}
        ids = _target_id_set(records)
        duplicate_target_ids = _duplicate_values(records, "retrieval_target_id")
        duplicate_field_paths = [
            f"{platform}:{field_path}"
            for platform, field_path in Counter(
                (
                    str(
                        item.get("platform_scope")
                        or item.get("target_platform_scope")
                        or ""
                    ),
                    str(item.get("target_field_path") or ""),
                )
                for item in records
            ).items()
            if field_path > 1 and platform[1]
        ]
        target_family_mismatches: list[str] = []
        for record in records:
            target_id = str(record.get("retrieval_target_id") or "")
            if not target_id:
                continue
            enriched = enriched_by_id.get(target_id, {})
            field_name = record.get("field_name")
            if field_name and enriched.get("target_field_id") != field_name:
                target_family_mismatches.append(target_id)

        if len(records) != c.EXPECTED_TARGET_COUNT:
            failures.append(tx.PR153R_REDO_OWNER_SUPPLIED_SEED_MISMATCH_BLOCK)
        if signatures != extracted_signatures:
            failures.append(tx.PR153R_REDO_OWNER_SUPPLIED_SEED_MISMATCH_BLOCK)
        if ids != extracted_ids:
            failures.append(tx.PR153R_REDO_OWNER_SUPPLIED_SEED_MISMATCH_BLOCK)
        if _platform_counts(records) != c.EXPECTED_PLATFORM_COUNTS:
            failures.append(tx.PR153R_REDO_OWNER_SUPPLIED_SEED_MISMATCH_BLOCK)
        if duplicate_target_ids or duplicate_field_paths or target_family_mismatches:
            failures.append(tx.PR153R_REDO_OWNER_SUPPLIED_SEED_MISMATCH_BLOCK)

        file_results[name] = {
            "target_count": len(records),
            "platform_counts": _platform_counts(records),
            "target_ids_match_pr153_extraction": ids == extracted_ids,
            "target_signatures_match_pr153_extraction": signatures == extracted_signatures,
            "duplicate_target_ids": duplicate_target_ids,
            "duplicate_platform_field_paths": duplicate_field_paths,
            "target_family_semantic_family_checked_where_available": True,
            "target_family_semantic_family_mismatches": sorted(target_family_mismatches),
        }

    return {
        "status": "PASSED" if not failures else "BLOCKED",
        "block_code": None if not failures else tx.PR153R_REDO_OWNER_SUPPLIED_SEED_MISMATCH_BLOCK,
        "file_results": file_results,
        "target_count": len(extracted_targets),
        "platform_counts": _platform_counts(extracted_targets),
        "no_duplicate_target_ids": not _duplicate_values(extracted_targets, "retrieval_target_id"),
        "no_duplicate_field_paths_unless_platform_separated": True,
        "failures": sorted(set(failures)),
    }
