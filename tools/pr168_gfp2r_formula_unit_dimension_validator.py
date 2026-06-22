#!/usr/bin/env python3
"""Unit and dimension checks for PR168-GFP2R formula variants."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2r_formula_alias_normalizer import UNITS, normalize_required_inputs


def validate_variant_units(template: dict[str, Any], available_inputs: dict[str, Any]) -> dict[str, Any]:
    required = normalize_required_inputs(list(template.get("required_formula_inputs", [])))
    missing = [name for name in required if name not in available_inputs or available_inputs.get(name) is None]
    unknown_units = [name for name in required if name not in UNITS]
    unit_invalid = bool(template.get("force_unit_invalid_flag")) or bool(unknown_units)
    return {
        "required_formula_inputs": required,
        "available_formula_inputs": sorted(name for name in required if name not in missing),
        "missing_formula_inputs": missing,
        "formula_units_valid_flag": not unit_invalid,
        "formula_dimension_validation_state": "UNIT_DIMENSION_VALID"
        if not unit_invalid
        else "UNIT_DIMENSION_INVALID_REPAIR_REQUIRED",
        "unit_invalid_reasons": [
            *(f"unknown_unit:{name}" for name in unknown_units),
            *(["forced_invalid_template_for_validator_receipt"] if template.get("force_unit_invalid_flag") else []),
        ],
    }


def build_unit_rows(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, variant in enumerate(variants, start=1):
        rows.append(
            {
                "row_id": f"unit_dimension_{index:05d}",
                "formula_variant_id": variant.get("formula_variant_id"),
                "template_id": variant.get("template_id"),
                "formula_units_valid_flag": variant.get("formula_units_valid_flag"),
                "formula_dimension_validation_state": variant.get("formula_dimension_validation_state"),
                "missing_formula_inputs": list(variant.get("missing_formula_inputs", [])),
                "input_units": variant.get("input_units", {}),
            }
        )
    return rows
