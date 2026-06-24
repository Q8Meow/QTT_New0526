#!/usr/bin/env python3
"""Blast-radius scoring for PR168-RP5A."""

from __future__ import annotations

from tools.pr168_rp5a_config import BLAST_RADIUS_WEIGHTS


def _count_by_file(rows: list[dict[str, object]], key: str, true_field: str | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        file_path = str(row[key])
        if true_field is not None and not row.get(true_field):
            continue
        counts[file_path] = counts.get(file_path, 0) + 1
    return counts


def build_blast_radius_rows(
    matched_files: list[str],
    file_term_map: dict[str, dict[str, object]],
    consumer_rows: list[dict[str, object]],
    validation_rows: list[dict[str, object]],
    identity_rows: list[dict[str, object]],
    agent_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    active_consumers = _count_by_file(consumer_rows, "file_path", "active_consumer_flag")
    validation_deps = {
        str(row["file_path_or_prefix"]): validation_deps_count
        for validation_deps_count, row in enumerate([], start=1)
    }
    validation_deps = {}
    for row in validation_rows:
        if row.get("validation_dependency_type") != "NONE":
            key = str(row["file_path_or_prefix"])
            validation_deps[key] = validation_deps.get(key, 0) + 1
    identity_deps = _count_by_file(identity_rows, "file_path", "unique_identity_possible_flag")
    agent_deps = _count_by_file(agent_rows, "file_path", "active_agent_touchpoint_flag")
    rows: list[dict[str, object]] = []
    for index, file_path in enumerate(matched_files, start=1):
        term_info = file_term_map[file_path]
        critical = int(term_info.get("critical_term_count", 0))
        high = int(term_info.get("high_term_count", 0))
        medium = int(term_info.get("medium_term_count", 0))
        low = int(term_info.get("low_term_count", 0))
        score = (
            critical * BLAST_RADIUS_WEIGHTS["critical_term"]
            + high * BLAST_RADIUS_WEIGHTS["high_term"]
            + medium * BLAST_RADIUS_WEIGHTS["medium_term"]
            + low * BLAST_RADIUS_WEIGHTS["low_term"]
            + active_consumers.get(file_path, 0) * BLAST_RADIUS_WEIGHTS["active_consumer"]
            + validation_deps.get(file_path, 0) * BLAST_RADIUS_WEIGHTS["validation_dependency"]
            + identity_deps.get(file_path, 0) * BLAST_RADIUS_WEIGHTS["identity_dependency"]
            + agent_deps.get(file_path, 0) * BLAST_RADIUS_WEIGHTS["agent_touchpoint"]
        )
        priority = "CRITICAL" if score >= 35 else "HIGH" if score >= 22 else "MEDIUM" if score >= 10 else "LOW"
        rows.append(
            {
                "row_id": f"RP5A_BLAST_{index:07d}",
                "file_path": file_path,
                "stale_term_family_count": len(term_info.get("term_families", [])),
                "critical_term_count": critical,
                "active_consumer_count": active_consumers.get(file_path, 0),
                "validation_dependency_count": validation_deps.get(file_path, 0),
                "identity_dependency_count": identity_deps.get(file_path, 0),
                "agent_touchpoint_count": agent_deps.get(file_path, 0),
                "future_agent_confusion_risk": priority,
                "future_deletion_risk": "HIGH" if identity_deps.get(file_path, 0) or validation_deps.get(file_path, 0) else "MEDIUM",
                "future_cleanup_priority": priority,
                "blast_radius_score": score,
            }
        )
    return rows
