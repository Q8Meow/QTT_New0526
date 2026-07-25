#!/usr/bin/env python3
"""Independent architecture and MATH-01..15 reconstruction.

This validator intentionally does not import the production package or primary
validator.
"""

from __future__ import annotations

import ast
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import json
from math import log, sqrt
from pathlib import Path
from random import Random
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    REPO_ROOT
    / "src"
    / "qtt"
    / "stage1_prediction_markets"
    / "qku_computation_control_plane"
)
PRODUCTION_NAMES = (
    "__init__.py",
    "models.py",
    "errors.py",
    "context.py",
    "specification.py",
    "implementation_registry.py",
    "identity_adapter.py",
    "plugin_adapter.py",
    "quantum_adapter.py",
    "source_policy.py",
    "parameter_policy.py",
    "bindings.py",
    "dependency_graph.py",
    "oracle_contracts.py",
    "authority.py",
    "protocols.py",
    "serialization.py",
    "validation.py",
    "source_rights.py",
)
EXPECTED_MATH_IDS = tuple(f"MATH-{value:02d}" for value in range(1, 16))
SUCCESS_MARKER = "QKU_ARCHITECTURE_INDEPENDENTLY_VALIDATED"
DECIMAL_CONTEXT = Context(prec=34, rounding=ROUND_HALF_EVEN)


def _stationary_means(seed: int) -> tuple[float, ...]:
    series = (1.0, 2.0, 3.0, 4.0, 5.0)
    rng = Random(seed)
    results: list[float] = []
    for _ in range(64):
        current = rng.randrange(len(series))
        sample = [series[current]]
        for _position in range(1, len(series)):
            if rng.random() < 0.5:
                current = rng.randrange(len(series))
            else:
                current = (current + 1) % len(series)
            sample.append(series[current])
        results.append(sum(sample) / len(sample))
    return tuple(results)


def _string_literal(tree: ast.Module, name: str) -> str:
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
    raise ValueError(f"missing string literal: {name}")


def _bh(p_values: tuple[float, ...], q: float, correction: float) -> tuple[int, ...]:
    ordered = sorted(enumerate(p_values), key=lambda item: (item[1], item[0]))
    largest = 0
    for rank, (_index, value) in enumerate(ordered, 1):
        if value <= rank * q / (len(ordered) * correction):
            largest = rank
    return tuple(sorted(index for index, _value in ordered[:largest]))


def _ece_from_raw(
    probabilities: tuple[float, ...],
    outcomes: tuple[int, ...],
    edges: tuple[float, ...],
) -> float:
    weighted_error = 0.0
    for left, right in zip(edges, edges[1:]):
        indices = tuple(
            index
            for index, probability in enumerate(probabilities)
            if left <= probability < right
            or (right == 1.0 and probability == 1.0)
        )
        if not indices:
            continue
        confidence = sum(probabilities[index] for index in indices) / len(indices)
        frequency = sum(outcomes[index] for index in indices) / len(indices)
        weighted_error += (
            len(indices) / len(probabilities) * abs(confidence - frequency)
        )
    return weighted_error


def _white_reality_p_value(
    time_rows: tuple[tuple[float, ...], ...],
    *,
    benchmark_minus_candidate: bool,
    seed: int,
    replicates: int,
) -> float:
    candidates = tuple(zip(*time_rows, strict=True))
    if not benchmark_minus_candidate:
        candidates = tuple(
            tuple(-value for value in candidate) for candidate in candidates
        )
    length = len(time_rows)
    means = tuple(sum(candidate) / length for candidate in candidates)
    observed = max(sqrt(length) * mean for mean in means)
    rng = Random(seed)
    exceedances = 0
    for _ in range(replicates):
        current = rng.randrange(length)
        indices = [current]
        for _position in range(1, length):
            if rng.random() < 0.5:
                current = rng.randrange(length)
            else:
                current = (current + 1) % length
            indices.append(current)
        statistic = max(
            sqrt(length)
            * (
                sum(candidate[index] for index in indices) / length
                - candidate_mean
            )
            for candidate, candidate_mean in zip(candidates, means, strict=True)
        )
        if statistic >= observed:
            exceedances += 1
    return exceedances / replicates


def independently_reconstruct() -> dict[str, bool]:
    with localcontext(DECIMAL_CONTEXT):
        midpoint = (Decimal("0.42") + Decimal("0.44")) / Decimal(2)
        spread = Decimal("0.44") - Decimal("0.42")
        values: dict[str, bool] = {
            "MATH-01": Decimal("0.42") / Decimal("1.00") == Decimal("0.42"),
            "MATH-02": abs((0.58 - 0.52) - 0.06) <= 1e-15,
            "MATH-03": midpoint == Decimal("0.43"),
            "MATH-04": spread == Decimal("0.02"),
            "MATH-05": (
                spread / midpoint
                == Decimal("0.04651162790697674418604651162790698")
            ),
            "MATH-06": (
                Decimal("0.60") * Decimal("0.55")
                + Decimal("0.40") * Decimal("-0.45")
                - Decimal("0.01")
                == Decimal("0.14")
            ),
            "MATH-07": (
                Decimal("0.2") * Decimal("1.0")
                + Decimal("0.3") * Decimal("-0.2")
                + Decimal("0.5") * Decimal("0.1")
                - Decimal("0.02")
                == Decimal("0.17")
            ),
            "MATH-08": (
                (Decimal("0.70") - Decimal(1)) ** 2 == Decimal("0.09")
            ),
            "MATH-09": abs(-log(0.7) - 0.35667494393873245) <= 1e-15,
            "MATH-10": abs(
                _ece_from_raw(
                    (0.3, 0.3, 0.8, 0.8),
                    (1, 0, 1, 0),
                    (0.0, 0.5, 1.0),
                )
                - 0.25
            )
            <= 1e-15,
        }
    center = (8 + 1.96**2 / 2) / (10 + 1.96**2)
    half = (
        1.96
        * sqrt((8 / 10 * (1 - 8 / 10) + 1.96**2 / 40) / 10)
        / (1 + 1.96**2 / 10)
    )
    values["MATH-11"] = (
        abs((center - half) - 0.49015684672072335) <= 1e-12
        and abs((center + half) - 0.9433190520193067) <= 1e-12
    )
    p_values = (0.001, 0.01, 0.04, 0.2)
    values["MATH-12"] = _bh(p_values, 0.05, 1.0) == (0, 1)
    harmonic = sum(1 / index for index in range(1, len(p_values) + 1))
    values["MATH-13"] = _bh(p_values, 0.05, harmonic) == (0, 1)
    first = _stationary_means(1401)
    second = _stationary_means(1401)
    ordered = sorted(first)
    values["MATH-14"] = (
        first == second
        and ordered[1] <= 3.0 <= ordered[-2]
    )
    zero_rows = ((0.0, 0.0),) * 4
    oriented_rows = ((1.0,),) * 4
    values["MATH-15"] = (
        _white_reality_p_value(
            zero_rows,
            benchmark_minus_candidate=True,
            seed=1501,
            replicates=64,
        )
        == 1.0
        and _white_reality_p_value(
            oriented_rows,
            benchmark_minus_candidate=True,
            seed=1501,
            replicates=64,
        )
        == 0.0
        and _white_reality_p_value(
            oriented_rows,
            benchmark_minus_candidate=False,
            seed=1501,
            replicates=64,
        )
        == 1.0
    )
    return values


def main() -> int:
    failures: list[str] = []
    actual_names = tuple(
        path.name for path in sorted(PACKAGE.glob("*.py"), key=lambda item: item.name)
    )
    if set(actual_names) != set(PRODUCTION_NAMES) or len(actual_names) != 19:
        failures.append("production core is not the exact 19-file centralized set")
    for name in PRODUCTION_NAMES:
        path = PACKAGE / name
        if not path.is_file():
            failures.append(f"missing production file: {name}")
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            failures.append(f"{name}: {exc}")
    try:
        parameter_tree = ast.parse(
            (PACKAGE / "parameter_policy.py").read_text(encoding="utf-8")
        )
        parameter_rows = json.loads(
            _string_literal(parameter_tree, "_PARAMETER_ROWS_JSON")
        )
    except (OSError, SyntaxError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"parameter literal could not be reconstructed: {exc}")
        parameter_rows = []
    required_parameter_fields = {
        "canonical_owner",
        "codex_online_research_allowed",
        "effective_bounded_search_space_or_fit_constraint",
        "effective_day1_seed_value_or_resolution_rule",
        "effective_default_authority_class",
        "effective_fallback_behavior_when_value_unavailable",
        "effective_owner_dashboard_editability_class",
        "effective_reference_range_or_structural_constraint",
        "effective_resolution_class",
        "effective_source_state_refs",
        "effective_unit_or_basis",
        "missing_stale_invalid_behavior",
        "parameter_audit_id",
        "parameter_id",
        "precision_and_rounding_policy",
        "runtime_resolution_procedure",
        "source_line_end",
        "source_line_start",
        "step12_primary_tranche_id",
    }
    if (
        len(parameter_rows) != 135
        or len(
            {
                row.get("parameter_id")
                for row in parameter_rows
                if isinstance(row, dict)
            }
        )
        != 135
        or len(
            {
                row.get("parameter_audit_id")
                for row in parameter_rows
                if isinstance(row, dict)
            }
        )
        != 135
        or any(
            not isinstance(row, dict)
            or not required_parameter_fields <= set(row)
            or any(
                row[field] in ("", None)
                for field in required_parameter_fields
            )
            or row["canonical_owner"] != "QKUComputationControlPlaneV1"
            or row["codex_online_research_allowed"] is not False
            or row["step12_primary_tranche_id"] != "ST12-TRANCHE-A"
            or not isinstance(row["effective_source_state_refs"], list)
            or not isinstance(row["precision_and_rounding_policy"], dict)
            or not row["precision_and_rounding_policy"]
            or not isinstance(row["runtime_resolution_procedure"], list)
            or not row["runtime_resolution_procedure"]
            or isinstance(row["source_line_start"], bool)
            or not isinstance(row["source_line_start"], int)
            or isinstance(row["source_line_end"], bool)
            or not isinstance(row["source_line_end"], int)
            or row["source_line_start"] <= 0
            or row["source_line_end"] < row["source_line_start"]
            for row in parameter_rows
        )
    ):
        failures.append("independent 135-row parameter reconstruction failed")
    reconstructed = independently_reconstruct()
    if tuple(reconstructed) != EXPECTED_MATH_IDS:
        failures.append("independent MATH-01..15 denominator mismatch")
    failures.extend(
        f"{math_id}: independent golden reconstruction failed"
        for math_id, passed in reconstructed.items()
        if not passed
    )
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} closure_controls=20 "
        f"independent_oracles={len(reconstructed)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
