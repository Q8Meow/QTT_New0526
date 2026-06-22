#!/usr/bin/env python3
"""Mapping repair confidence summaries for PR168-GFP2R."""

from __future__ import annotations

from typing import Any


def mapping_confidence_summary(mapping_rows: list[dict[str, Any]]) -> dict[str, Any]:
    class_counts: dict[str, int] = {}
    confidence_counts: dict[str, int] = {}
    for row in mapping_rows:
        class_counts[str(row.get("mapping_class"))] = class_counts.get(str(row.get("mapping_class")), 0) + 1
        confidence_counts[str(row.get("mapping_confidence"))] = (
            confidence_counts.get(str(row.get("mapping_confidence")), 0) + 1
        )
    return {
        "mapping_row_count": len(mapping_rows),
        "mapping_class_counts": dict(sorted(class_counts.items())),
        "mapping_confidence_counts": dict(sorted(confidence_counts.items())),
        "exact_candidate_compute_ready_count": sum(
            1 for row in mapping_rows if row.get("mapping_class") == "EXACT_QKU_FORMULA_CANDIDATE_COMPUTE_READY"
        ),
        "exact_repaired_candidate_compute_ready_count": sum(
            1
            for row in mapping_rows
            if row.get("mapping_class") == "EXACT_REPAIRED_QKU_FORMULA_CANDIDATE_COMPUTE_READY"
        ),
        "provisional_data_consumer_compute_ready_count": sum(
            1
            for row in mapping_rows
            if row.get("mapping_class") == "PROVISIONAL_DATA_CONSUMER_FORMULA_COMPUTE_READY"
        ),
        "repair_only_count": sum(
            1 for row in mapping_rows if str(row.get("GFP2R_consumption_scope", "")).startswith("REPAIR")
        ),
    }
