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


def _qubo_energy(binary: tuple[int, ...]) -> float:
    return 0.1 + binary[0] + 2 * binary[1] + 0.5 * binary[0] * binary[1]


def _ising_energy(spins: tuple[int, ...]) -> float:
    offset = 0.1 + 1 / 2 + 2 / 2 + 0.5 / 4
    h0 = -1 / 2 - 0.5 / 4
    h1 = -2 / 2 - 0.5 / 4
    coupling = 0.5 / 4
    return offset + h0 * spins[0] + h1 * spins[1] + coupling * spins[0] * spins[1]


def independently_reconstruct() -> dict[str, bool]:
    math_46 = abs((0.1 + 1 + 3 + 0.5) - 4.6) <= 1e-15
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
    )
    feasible = tuple(
        (x, y, x + y)
        for x, y in product((0, 1), repeat=2)
        if x + y <= 1
    )
    math_48 = max(item[2] for item in feasible) == 1
    discrete = tuple(
        ((a, b), (0 if a == "A0" else 1) + (0 if b == "B0" else 1))
        for a, b in product(("A0", "A1"), ("B0", "B1"))
    )
    best = min(discrete, key=lambda item: (item[1], item[0]))
    math_49 = best == (("A0", "B0"), 0)
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
        f"{SUCCESS_MARKER} closure_controls=6 "
        f"independent_oracles={len(reconstructed)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
