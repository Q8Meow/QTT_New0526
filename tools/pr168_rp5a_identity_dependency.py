#!/usr/bin/env python3
"""QKU/formula identity dependency detection for PR168-RP5A."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from tools.pr168_rp5a_config import IDENTITY_REGEXES, MAX_IDENTITY_REFS_PER_FILE, REPO_ROOT, should_scan_path
from tools.pr168_rp5a_git_grep_scanner import git_tracked_files


def scan_identity_occurrences(repo_root: Path = REPO_ROOT, files: list[str] | None = None) -> dict[str, dict[str, object]]:
    occurrences: dict[str, dict[str, object]] = {}
    scan_files = files if files is not None else git_tracked_files(repo_root)
    for file_path in scan_files:
        if not should_scan_path(file_path):
            continue
        identity_count_for_file = 0
        try:
            with (repo_root / file_path).open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    for identity_type, regex in IDENTITY_REGEXES.items():
                        for match in regex.finditer(line):
                            if identity_count_for_file >= MAX_IDENTITY_REFS_PER_FILE:
                                break
                            identity_ref = match.group(0)
                            key = f"{identity_type}:{identity_ref}"
                            bucket = occurrences.setdefault(
                                key,
                                {
                                    "identity_ref": identity_ref,
                                    "identity_type": identity_type,
                                    "file_refs": set(),
                                },
                            )
                            bucket["file_refs"].add(file_path)
                            identity_count_for_file += 1
                        if identity_count_for_file >= MAX_IDENTITY_REFS_PER_FILE:
                            break
                    if identity_count_for_file >= MAX_IDENTITY_REFS_PER_FILE:
                        break
        except OSError:
            continue
    return occurrences


def build_identity_dependency_rows(matched_files: list[str], identity_occurrences: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    by_file: dict[str, list[dict[str, object]]] = defaultdict(list)
    for occurrence in identity_occurrences.values():
        for file_ref in occurrence["file_refs"]:
            if file_ref in matched_files:
                by_file[file_ref].append(occurrence)

    rows: list[dict[str, object]] = []
    for index, file_path in enumerate(matched_files, start=1):
        occurrences = by_file.get(file_path, [])
        identity_types = sorted({str(item["identity_type"]) for item in occurrences})
        refs = sorted({str(item["identity_ref"]) for item in occurrences})
        duplicate_elsewhere = bool(refs) and all(
            len(identity_occurrences[f"{item['identity_type']}:{item['identity_ref']}"]["file_refs"]) > 1
            for item in occurrences
        )
        unique_possible = bool(refs) and not duplicate_elsewhere
        recommended = "DELETE_AFTER_QKU_FORMULA_IDENTITY_RECLAIM" if unique_possible else "NO_IDENTITY_BLOCKER_DETECTED"
        rows.append(
            {
                "row_id": f"RP5A_IDENTITY_DEP_{index:07d}",
                "file_path": file_path,
                "identity_type": "MIXED" if len(identity_types) > 1 else (identity_types[0] if identity_types else "NONE"),
                "identity_count": len(refs),
                "sample_identity_refs_limited": refs[:50],
                "unique_identity_possible_flag": unique_possible,
                "duplicate_elsewhere_proven_flag": duplicate_elsewhere,
                "canonical_replacement_file_if_exists": None,
                "delete_requires_reclaim_flag": unique_possible,
                "future_reclaim_target": "PR168_RP5C_IMMUTABLE_LIBRARY" if unique_possible else "UNKNOWN",
                "recommended_classification": recommended,
            }
        )
    return rows
