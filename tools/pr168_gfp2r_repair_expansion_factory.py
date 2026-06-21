#!/usr/bin/env python3
"""Repair-and-expansion factory summary helpers."""

from __future__ import annotations

from typing import Any


def expansion_summary(variants: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "formula_variant_generated_count": len(variants),
        "formula_variant_executable_count": sum(1 for row in variants if row.get("provisional_compute_eligible_flag")),
        "formula_variant_duplicate_suppressed_count": sum(1 for row in variants if row.get("duplicate_suppressed_flag")),
        "formula_variant_unit_invalid_count": sum(
            1 for row in variants if row.get("mapping_class") == "FORMULA_VARIANT_UNIT_INVALID"
        ),
        "formula_variant_data_insufficient_count": sum(
            1 for row in variants if row.get("mapping_class") == "FORMULA_VARIANT_DATA_INSUFFICIENT"
        ),
        "formula_equivalence_cluster_count": len(
            {row.get("formula_equivalence_cluster_id") for row in variants if row.get("formula_equivalence_cluster_id")}
        ),
        "bounded_generation_policy": "one fixed template bank per DATA1A market context and side; no unbounded grid search",
    }
