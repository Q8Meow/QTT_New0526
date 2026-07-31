#!/usr/bin/env python3
"""Independently validate frozen latency and point-in-time classification."""

from __future__ import annotations

import ast
from collections import Counter
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    REPO_ROOT
    / "src"
    / "qtt"
    / "stage1_prediction_markets"
    / "qku_computation_control_plane"
)
SPECIFICATION = PACKAGE / "specification.py"
POINT_IN_TIME = PACKAGE / "point_in_time.py"
SUCCESS_MARKER = "QKU_LATENCY_INDEPENDENTLY_VALIDATED"
EXPECTED_POINT_IN_TIME_IDS = (
    "MATH-01",
    "MATH-02",
    "MATH-03",
    "MATH-04",
    "MATH-05",
    "MATH-06",
    "MATH-07",
    "MATH-36",
)
EXPECTED_FIELD_CLASSES = (
    "OBSERVATION",
    "SCHEDULED_EFFECTIVE_FACT",
    "REVISION",
    "EVENT_OUTCOME",
    "SETTLEMENT",
)


def _literal(tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            )
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    raise ValueError(f"missing literal {name}")


def _enum_values(tree: ast.Module, class_name: str) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return tuple(
                str(statement.value.value)
                for statement in node.body
                if isinstance(statement, ast.Assign)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            )
    return ()


def main() -> int:
    failures: list[str] = []
    try:
        specification_tree = ast.parse(
            SPECIFICATION.read_text(encoding="utf-8"),
            filename=str(SPECIFICATION),
        )
        requirements = json.loads(
            _literal(
                specification_tree,
                "_ST12B_FORMULA_REQUIREMENTS_JSON",
            )
        )
        point_in_time_tree = ast.parse(
            POINT_IN_TIME.read_text(encoding="utf-8"),
            filename=str(POINT_IN_TIME),
        )
    except (OSError, SyntaxError, ValueError, json.JSONDecodeError) as exc:
        print(f"latency literals could not be reconstructed: {exc}", file=sys.stderr)
        return 1
    if not isinstance(requirements, list) or any(
        not isinstance(row, dict) for row in requirements
    ):
        failures.append("formula requirements must be a JSON array of objects")
        requirements = []
    latency_counts = Counter(
        str(row.get("latency_class")) for row in requirements
    )
    point_in_time_ids = tuple(
        str(row.get("math_spec_id"))
        for row in requirements
        if row.get("latency_class") == "POINT_IN_TIME"
    )
    if (
        len(requirements) != 30
        or latency_counts
        != {"POINT_IN_TIME": 8, "OFFLINE_OR_NEARLINE": 22}
        or point_in_time_ids != EXPECTED_POINT_IN_TIME_IDS
    ):
        failures.append("latency classes are not the exact frozen 8/22 partition")
    if any(
        row.get("order_or_mode_effect_authorized") is not False
        or row.get("provider_or_private_state_effect_authorized") is not False
        or row.get("qpu_or_simulator_execution_authorized") is not False
        for row in requirements
    ):
        failures.append("a latency class authorizes a provider/mode/order/QPU effect")
    if (
        _enum_values(point_in_time_tree, "PointInTimeFieldClassV1")
        != EXPECTED_FIELD_CLASSES
    ):
        failures.append("the centralized five-class point-in-time roster differs")
    point_in_time_text = POINT_IN_TIME.read_text(encoding="utf-8")
    for required in (
        "observed_time",
        "effective_time",
        "available_time",
        "received_time",
        "processed_time",
        "as_of_time",
        "classify_point_in_time_semantics",
    ):
        if required not in point_in_time_text:
            failures.append(f"point-in-time invariant is absent: {required}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} point_in_time=8 offline_or_nearline=22 "
        f"field_classes={len(EXPECTED_FIELD_CLASSES)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
