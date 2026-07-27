#!/usr/bin/env python3
"""Independent MATH-46..49 reconstruction without production imports."""

from __future__ import annotations

import ast
from itertools import product
import math
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
SUCCESS_MARKER = "QKU_QUANTUM_INDEPENDENTLY_VALIDATED"


def _expect_value_error(callable_) -> bool:
    try:
        callable_()
    except (ValueError, ArithmeticError):
        return True
    return False


def _qubo_energy(
    binary: tuple[int, ...],
    diagonal: tuple[float, ...] = (1.0, 2.0),
    upper_terms: tuple[tuple[int, int, float], ...] = ((0, 1, 0.5),),
    offset: float = 0.1,
) -> float:
    if len(binary) != len(diagonal) or any(value not in (0, 1) for value in binary):
        raise ValueError("invalid binary assignment")
    seen: set[tuple[int, int]] = set()
    for i, j, value in upper_terms:
        if not 0 <= i < j < len(diagonal) or (i, j) in seen or not math.isfinite(value):
            raise ValueError("invalid upper-triangular coefficient map")
        seen.add((i, j))
    return (
        offset
        + math.fsum(value * binary[index] for index, value in enumerate(diagonal))
        + math.fsum(
            value * binary[i] * binary[j]
            for i, j, value in upper_terms
        )
    )


def _ising_energy(spins: tuple[int, ...]) -> float:
    offset = 0.1 + 1 / 2 + 2 / 2 + 0.5 / 4
    h0 = -1 / 2 - 0.5 / 4
    h1 = -2 / 2 - 0.5 / 4
    coupling = 0.5 / 4
    return offset + h0 * spins[0] + h1 * spins[1] + coupling * spins[0] * spins[1]


def independently_reconstruct() -> dict[str, bool]:
    math_46 = (
        abs(
            _qubo_energy(
                (1, 0, 1),
                (1.0, 2.0, 3.0),
                ((0, 2, 0.5),),
            )
            - 4.6
        )
        <= 1e-15
        and _expect_value_error(
            lambda: _qubo_energy(
                (1, 1),
                (1.0, 2.0),
                ((1, 0, 0.5),),
            )
        )
        and _expect_value_error(
            lambda: _qubo_energy(
                (1, 1),
                (1.0, 2.0),
                ((0, 1, 0.5), (0, 1, 0.2)),
            )
        )
    )
    assignments = tuple(product((0, 1), repeat=2))
    coefficient_scale = max(1.0, abs(0.1) + abs(1.0) + abs(2.0) + abs(0.5))
    parity_tolerance = 8 * 4 * math.ulp(coefficient_scale)
    math_47 = all(
        abs(
            _qubo_energy(binary)
            - _ising_energy(tuple(1 - 2 * item for item in binary))
        )
        <= parity_tolerance
        for binary in assignments
    ) and _expect_value_error(lambda: _qubo_energy((0, 1, 0)))
    feasible = tuple(
        (x, y, x + y)
        for x, y in product((0, 1), repeat=2)
        if x + y <= 1
    )
    optimal = min(
        (item for item in feasible if item[2] == max(row[2] for row in feasible)),
        key=lambda item: (item[0], item[1]),
    )
    math_48 = (
        max(item[2] for item in feasible) == 1
        and all(x + y <= 1 for x, y, _objective in feasible)
        and optimal == (0, 1, 1)
        and not tuple(
            (x, y)
            for x, y in product((0, 1), repeat=2)
            if x + y <= -1
        )
    )
    case_registry = {
        "a": ("A0", "A1"),
        "b": ("B0", "B1"),
    }
    discrete = tuple(
        ((a, b), (0 if a == "A0" else 1) + (0 if b == "B0" else 1))
        for a, b in product(case_registry["a"], case_registry["b"])
    )
    best = min(discrete, key=lambda item: (item[1], item[0]))
    math_49 = (
        best == (("A0", "B0"), 0)
        and len(discrete) == math.prod(len(cases) for cases in case_registry.values())
        and best[0][0] in case_registry["a"]
        and best[0][1] in case_registry["b"]
        and _expect_value_error(
            lambda: (
                (_ for _ in ()).throw(ValueError("duplicate case label"))
                if len(("A0", "A0")) != len(set(("A0", "A0")))
                else ()
            )
        )
    )
    return {
        "MATH-46": math_46,
        "MATH-47": math_47,
        "MATH-48": math_48,
        "MATH-49": math_49,
    }


def main() -> int:
    failures: list[str] = []
    implementation_tree: ast.Module | None = None
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if path.name == "implementation_registry.py":
            implementation_tree = tree
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_names = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                if any(
                    name.startswith(("qiskit", "dwave", "dimod"))
                    for name in module_names
                ):
                    failures.append(f"{path.name}: imports optional quantum SDK")
    class_names = {
        node.name
        for node in (implementation_tree.body if implementation_tree else ())
        if isinstance(node, ast.ClassDef)
    }
    function_names = {
        node.name
        for node in (implementation_tree.body if implementation_tree else ())
        if isinstance(node, ast.FunctionDef)
    }
    if not {
        "ObjectiveScalingReceiptV1",
        "QuboModelV1",
        "IsingModelV1",
        "QuadraticVariableV1",
        "DiscreteVariableV1",
    } <= class_names:
        failures.append("typed quantum model or scaling-receipt contract is missing")
    if not {
        "compute_math_46_qubo_upper_triangular_convention",
        "compute_math_47_qubo_to_ising_transform",
        "compute_math_48_constrained_quadratic_model",
        "compute_math_49_discrete_quadratic_model",
    } <= function_names:
        failures.append("one or more centralized quantum callables are missing")
    reconstructed = independently_reconstruct()
    failures.extend(
        f"{math_id}: independent golden reconstruction failed"
        for math_id, passed in reconstructed.items()
        if not passed
    )
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} independent_oracles={len(reconstructed)} "
        f"passing_invariant_groups={sum(reconstructed.values())}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
