"""Deterministic callable smoke execution for PR162R."""

from __future__ import annotations

import math
from typing import Any

from .formulation_callable_resolver import import_callable


def build_smoke_execution_rows(
    formulations: list[dict[str, Any]],
    test_vectors: list[dict[str, Any]],
    comparators: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    tv_by_id = {row.get("test_vector_id"): row for row in test_vectors}
    rows: list[dict[str, Any]] = []
    for index, formulation in enumerate(formulations, start=1):
        tv_refs = list(formulation.get("test_vector_refs", []))
        tv = tv_by_id.get(tv_refs[0]) if tv_refs else None
        row = _smoke_formulation(index, formulation, tv)
        rows.append(row)
    offset = len(rows)
    for index, comparator in enumerate(comparators, start=1):
        rows.append(_smoke_comparator(offset + index, comparator))
    return rows


def smoke_status_by_formulation(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("formulation_ref")): row
        for row in rows
        if row.get("formulation_ref") and row.get("callable_family") != "CLASSICAL_COMPARATOR"
    }


def smoke_status_by_comparator(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("formulation_ref")): row
        for row in rows
        if row.get("callable_family") == "CLASSICAL_COMPARATOR"
    }


def _smoke_formulation(
    index: int,
    formulation: dict[str, Any],
    test_vector: dict[str, Any] | None,
) -> dict[str, Any]:
    family = _callable_family(formulation.get("formulation_type"))
    base = {
        "smoke_execution_id": f"PR162R_SMOKE::{index:04d}",
        "callable_family": family,
        "formulation_ref": formulation.get("formulation_id"),
        "callable_ref": formulation.get("callable_ref"),
        "test_vector_ref": test_vector.get("test_vector_id") if test_vector else None,
        "deterministic_seed": None,
        "backend_execution_flag": False,
        "simulator_execution_flag": False,
        "quantum_advantage_claim_flag": False,
        "live_order_authority": False,
    }
    if not formulation.get("callable_ref") or not test_vector:
        return {
            **base,
            "smoke_execution_status": "SMOKE_EXECUTION_SKIPPED_WITH_EXACT_REASON",
            "exact_reason": "missing callable_ref or test vector",
            "actual_output_shape": None,
            "finite_numeric_status": "NOT_APPLICABLE",
            "tolerance": None,
            "validation_status": "FILL_REQUIRED_WITH_EXACT_REASON",
        }
    try:
        callable_obj = import_callable(str(formulation["callable_ref"]))
        actual = callable_obj(dict(test_vector.get("inputs", {})))
        if family == "QUANTUM_SHAPE_BUILDER":
            passed = _matches_quantum_expected(actual, test_vector.get("expected_outputs", {})) and _quantum_shape_valid(actual)
        else:
            passed = _matches_expected(actual, test_vector.get("expected_outputs", {}), float(test_vector.get("tolerance", 0.0)))
        return {
            **base,
            "smoke_execution_status": "SMOKE_EXECUTION_PASSED" if passed else "SMOKE_EXECUTION_FAILED",
            "exact_reason": None if passed else "actual output did not match expected test-vector contract",
            "actual_output_shape": _shape(actual),
            "output_type": type(actual).__name__,
            "unit_or_scale": "from_PR162D_R2A_TestVectorRegistry_if_present",
            "finite_numeric_status": _finite_numeric_status(actual),
            "tolerance": float(test_vector.get("tolerance", 0.0)),
            "proof": {
                "callable_imported": True,
                "test_vector_executed": True,
                "expected_output_checked": True,
                "quantum_shape_checked_without_backend": family == "QUANTUM_SHAPE_BUILDER",
            },
            "validation_status": "PASS" if passed else "FILL_REQUIRED_WITH_EXACT_REASON",
        }
    except Exception as exc:  # pragma: no cover - validator reports exact failure
        return {
            **base,
            "smoke_execution_status": "SMOKE_EXECUTION_FAILED",
            "exact_reason": str(exc),
            "actual_output_shape": None,
            "finite_numeric_status": "NOT_APPLICABLE",
            "tolerance": float(test_vector.get("tolerance", 0.0)),
            "validation_status": "FILL_REQUIRED_WITH_EXACT_REASON",
        }


def _smoke_comparator(index: int, comparator: dict[str, Any]) -> dict[str, Any]:
    family = str(comparator.get("comparator_family") or "")
    base = {
        "smoke_execution_id": f"PR162R_SMOKE::{index:04d}",
        "callable_family": "CLASSICAL_COMPARATOR",
        "formulation_ref": comparator.get("classical_comparator_id"),
        "callable_ref": comparator.get("callable_ref"),
        "test_vector_ref": comparator.get("test_vector_ref"),
        "deterministic_seed": None,
        "backend_execution_flag": False,
        "simulator_execution_flag": False,
        "quantum_advantage_claim_flag": False,
        "live_order_authority": False,
    }
    try:
        callable_obj = import_callable(str(comparator["callable_ref"]))
        actual = callable_obj(_comparator_inputs(family))
        return {
            **base,
            "smoke_execution_status": "SMOKE_EXECUTION_PASSED" if isinstance(actual, dict) and actual else "SMOKE_EXECUTION_FAILED",
            "exact_reason": None if isinstance(actual, dict) and actual else "comparator returned empty/non-dict output",
            "actual_output_shape": _shape(actual),
            "comparator_output_shape": _shape(actual),
            "comparator_metric_family": family,
            "finite_numeric_status": _finite_numeric_status(actual),
            "tolerance": 0.0,
            "proof": {
                "callable_imported": True,
                "synthetic_candidate_shape_executed": True,
                "comparator_output_shape_recorded": True,
            },
            "validation_status": "PASS" if isinstance(actual, dict) and actual else "FILL_REQUIRED_WITH_EXACT_REASON",
        }
    except Exception as exc:  # pragma: no cover - validator reports exact failure
        return {
            **base,
            "smoke_execution_status": "SMOKE_EXECUTION_FAILED",
            "exact_reason": str(exc),
            "actual_output_shape": None,
            "comparator_output_shape": None,
            "comparator_metric_family": family,
            "finite_numeric_status": "NOT_APPLICABLE",
            "tolerance": 0.0,
            "validation_status": "FILL_REQUIRED_WITH_EXACT_REASON",
        }


def _callable_family(formulation_type: Any) -> str:
    if formulation_type in {"FORMULA", "FEATURE"}:
        return "FORMULA"
    if formulation_type in {"ALGORITHM", "PARAMETER_PACK"}:
        return "ALGORITHM"
    if formulation_type == "QUANTUM_FORMULATION":
        return "QUANTUM_SHAPE_BUILDER"
    return "UNKNOWN_CALLABLE_FAMILY"


def _matches_expected(actual: Any, expected: Any, tolerance: float) -> bool:
    if isinstance(expected, dict) and isinstance(actual, dict):
        return all(key in actual and _matches_expected(actual[key], value, tolerance) for key, value in expected.items())
    if isinstance(expected, list) and isinstance(actual, list):
        return len(actual) == len(expected) and all(_matches_expected(a, e, tolerance) for a, e in zip(actual, expected, strict=True))
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(float(actual) - float(expected)) <= tolerance
    return actual == expected


def _quantum_shape_valid(shape: Any) -> bool:
    if not isinstance(shape, dict):
        return False
    if not shape.get("objective") or not shape.get("variables") or not shape.get("domains"):
        return False
    if not shape.get("constraints") and not shape.get("no_constraint_reason"):
        return False
    if not shape.get("penalties") and not shape.get("no_penalty_reason"):
        return False
    if not shape.get("classical_comparator_ref"):
        return False
    return shape.get("backend_execution") is False and shape.get("quantum_advantage_claim") is False


def _matches_quantum_expected(actual: Any, expected: Any) -> bool:
    if not isinstance(actual, dict) or not isinstance(expected, dict):
        return False
    if expected.get("shape_type") and actual.get("shape_type") != expected["shape_type"]:
        return False
    if expected.get("variable_count") is not None and len(actual.get("variables", [])) != int(expected["variable_count"]):
        return False
    if expected.get("classical_comparator_ref") and actual.get("classical_comparator_ref") != expected["classical_comparator_ref"]:
        return False
    return True


def _shape(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {"type": "dict", "keys": sorted(str(key) for key in value)}
    if isinstance(value, list):
        return {"type": "list", "length": len(value)}
    return {"type": type(value).__name__}


def _finite_numeric_status(value: Any) -> str:
    numbers: list[float] = []
    _collect_numbers(value, numbers)
    if not numbers:
        return "NO_NUMERIC_OUTPUT"
    return "FINITE_NUMERIC_OUTPUT" if all(math.isfinite(item) for item in numbers) else "NONFINITE_NUMERIC_OUTPUT"


def _collect_numbers(value: Any, output: list[float]) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        output.append(float(value))
    elif isinstance(value, dict):
        for item in value.values():
            _collect_numbers(item, output)
    elif isinstance(value, list):
        for item in value:
            _collect_numbers(item, output)


def _comparator_inputs(family: str) -> dict[str, Any]:
    candidates = [
        {"candidate_id": "A", "final_score": 0.8, "score": 0.8, "latency_class": "HOT", "risk_class": "LOW", "valid_flag": True, "expected_net_value": 10.0, "capital_required": 40.0, "risk_exposure": 20.0, "family": "F1"},
        {"candidate_id": "B", "final_score": 0.7, "score": 0.7, "latency_class": "BATCH", "risk_class": "LOW", "valid_flag": True, "expected_net_value": 8.0, "capital_required": 20.0, "risk_exposure": 10.0, "family": "F2"},
    ]
    if family in {"GREEDY_MARKET_BUNDLE_SELECTION", "MIXED_INTEGER_PROGRAMMING_COMPARATOR"}:
        return {"budget": 100.0, "max_exposure": 80.0, "candidates": candidates}
    if family in {"DETERMINISTIC_CANDIDATE_RANKING", "REPLAY_VALUE_RANKING_COMPARATOR", "PAPER_VALUE_RANKING_COMPARATOR"}:
        return {"candidates": candidates}
    if family == "RISK_ADJUSTED_SCORE_RANKING":
        return {"expected_net_value": 0.2, "drawdown_penalty_lambda": 0.1, "drawdown_risk": 0.2, "latency_penalty_lambda": 0.1, "latency_cost": 0.01, "slippage_penalty_lambda": 0.1, "slippage_estimate": 0.01, "complexity_penalty_lambda": 0.1, "complexity_score": 0.2}
    if family == "BRUTE_FORCE_BINARY_ENUMERATION":
        return {"candidates": candidates, "k": 1}
    if family in {"MEAN_VARIANCE_GREEDY_COMPARATOR", "DIVERSIFIED_GREEDY_COMPARATOR"}:
        return {"candidates": candidates}
    if family == "PARAMETER_STACK_SELECTOR":
        return {"stacks": [{"stack_id": "S1", "compatible_flag": True, "compatibility_score": 0.7, "replay_value_score": 0.4, "risk_score": 0.1}]}
    if family == "ROUTE_FILL_PRIORITY_ORDER":
        return {"actions": [{"route_fill_action_id": "R1", "route_fill_need_score": 0.6}, {"route_fill_action_id": "R2", "route_fill_need_score": 0.4}]}
    return {"candidates": candidates}
