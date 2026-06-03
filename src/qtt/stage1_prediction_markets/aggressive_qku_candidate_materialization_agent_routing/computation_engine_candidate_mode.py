"""Safe deterministic candidate computations for formula and algorithm test vectors."""

from __future__ import annotations

from typing import Any

from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.formula_registry import (
    formula_specs,
    get_callable,
)
from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.algorithm_registry import (
    algorithm_specs,
)

from .deterministic_id import deterministic_id


def deterministic_computation_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for spec in formula_specs():
        vector = spec["test_vector"]
        observed = _execute_vector(vector)
        records.append(_computation_record("FORMULA", spec["formula_id"], vector, observed))
    for spec in algorithm_specs():
        vector = spec["test_vector"]
        observed = _execute_vector(vector)
        records.append(_computation_record("ALGORITHM", spec["algorithm_id"], vector, observed))
    return records


def _execute_vector(vector: dict[str, Any]) -> Any:
    function = get_callable(vector["implementation_module"], vector["implementation_function"])
    return function(**vector["inputs"])


def _computation_record(kind: str, ref: str, vector: dict[str, Any], observed: Any) -> dict[str, Any]:
    return {
        "computation_id": deterministic_id("PR162D-DETERMINISTIC-COMPUTE", kind, ref),
        "candidate_ref": ref,
        "candidate_kind": kind,
        "test_vector_ref": vector["test_vector_id"],
        "inputs": vector["inputs"],
        "observed_output": observed,
        "expected_output": vector["expected_output"],
        "tolerance": vector.get("tolerance", 0.0),
        "computation_status": "DETERMINISTIC_CANDIDATE_COMPUTATION_EXECUTED",
        "creates_profit_evidence": False,
        "creates_order_authority": False,
        "live_order_authority": False,
    }


def values_match(observed: Any, expected: Any, tolerance: float = 1e-9) -> bool:
    if isinstance(observed, float) or isinstance(expected, float):
        return abs(float(observed) - float(expected)) <= tolerance
    if isinstance(observed, list) and isinstance(expected, list):
        return len(observed) == len(expected) and all(
            values_match(a, b, tolerance) for a, b in zip(observed, expected, strict=True)
        )
    if isinstance(observed, dict) and isinstance(expected, dict):
        return observed.keys() == expected.keys() and all(
            values_match(observed[key], expected[key], tolerance) for key in observed
        )
    return observed == expected
