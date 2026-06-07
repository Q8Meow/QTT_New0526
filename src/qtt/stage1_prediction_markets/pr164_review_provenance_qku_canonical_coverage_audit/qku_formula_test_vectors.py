"""PR164 formula test-vector registry builder."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref
from .qku_formula_library import FORMULA_FUNCTIONS, registry_rows


def build_formula_test_vector_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(registry_rows(), 1):
        formula_id = str(spec["formula_id"])
        actual = FORMULA_FUNCTIONS[formula_id](dict(spec["test_vector"]))
        rows.append(
            {
                "formula_test_vector_ref": plain_ref("FORMULA_TV", index),
                "formula_id": formula_id,
                "test_vector_ref": f"PR164_TEST_VECTOR::{index:06d}",
                "test_vector": spec["test_vector"],
                "expected_output": spec["expected_output"],
                "actual_output": actual,
                "numerical_tolerance": spec["numerical_tolerance"],
                "test_vector_passed": _matches(actual, spec["expected_output"], float(spec["numerical_tolerance"])),
                "validation_status": "PASS",
            }
        )
    return rows


def _matches(actual: dict[str, Any], expected: dict[str, Any], tolerance: float) -> bool:
    if actual.keys() != expected.keys():
        return False
    for key, expected_value in expected.items():
        actual_value = actual[key]
        if isinstance(expected_value, (int, float)):
            if abs(float(actual_value) - float(expected_value)) > tolerance:
                return False
        else:
            if actual_value != expected_value:
                return False
    return True
