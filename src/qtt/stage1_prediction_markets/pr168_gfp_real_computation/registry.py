"""In-memory formula registry helpers for PR168-GFP."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .formula_discovery import SELECTED_FORMULAS, required_formula_set_records, selected_formula_records


def get_formula_registry() -> dict[str, dict[str, Any]]:
    return {str(row["formula_id"]): deepcopy(row) for row in selected_formula_records()}


def get_required_formula_set_registry() -> dict[str, dict[str, Any]]:
    return {str(row["required_formula_set_id"]): deepcopy(row) for row in required_formula_set_records()}


def get_formula_by_family(formula_family: str) -> dict[str, Any]:
    if formula_family not in SELECTED_FORMULAS:
        raise KeyError(f"unknown formula family: {formula_family}")
    return deepcopy(SELECTED_FORMULAS[formula_family])


def validate_formula_registry_contract() -> dict[str, int]:
    missing_expression = 0
    missing_source = 0
    missing_variable_map = 0
    missing_function_path = 0
    for row in selected_formula_records():
        missing_expression += int(not bool(row.get("formula_expression")))
        missing_source += int(not bool(row.get("formula_source_ref")))
        missing_variable_map += int(not bool(row.get("variable_map")))
        missing_function_path += int(not bool(row.get("computation_function_path")))
    return {
        "formula_count": len(selected_formula_records()),
        "missing_expression": missing_expression,
        "missing_source": missing_source,
        "missing_variable_map": missing_variable_map,
        "missing_function_path": missing_function_path,
    }
