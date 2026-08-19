#!/usr/bin/env python3
"""Independent architecture and its exact 29-row mathematical reconstruction.

This validator intentionally does not import the production package or primary
validator.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from itertools import combinations, product
import json
import math
from math import log, sqrt
from pathlib import Path
from random import Random
from statistics import NormalDist
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
    "agent_policy.py",
    "protocols.py",
    "serialization.py",
    "validation.py",
    "source_rights.py",
    "contextual_computability.py",
    "fallback.py",
    "freshness.py",
    "input_resolver.py",
    "point_in_time.py",
    "service.py",
    "stack_resolver.py",
    "unit_conversion.py",
    "accounting.py",
    "economic_math.py",
    "idempotency.py",
    "lifecycle.py",
    "latency_policy.py",
    "migrations.py",
    "outbox.py",
    "persistence.py",
    "receipts.py",
    "rollback.py",
    "sqlite_reference.py",
    "transaction.py",
    "mode_snapshot_policy.py",
    "cohort_compiler.py",
    "input_lock.py",
    "evidence.py",
    "model_risk.py",
    "quantum_benchmark.py",
    "llm_gateway.py",
)
EXPECTED_MATH_IDS = tuple(f"MATH-{value:02d}" for value in range(1, 16))
ARCHITECTURE_MATH_IDS = (
    *(f"MATH-{value:02d}" for value in range(1, 26)),
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
CURRENT_ST12B_ARCHITECTURE_MATH_IDS = (
    *(f"MATH-{value:02d}" for value in range(16, 26)),
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
EXPECTED_ALL_MATH_IDS = (
    *EXPECTED_MATH_IDS,
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
EXPECTED_ST12B_MATH_IDS = (
    *(f"MATH-{value:02d}" for value in range(1, 26)),
    "MATH-36",
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
SHARED_VALIDATION_TEST_PATHS = (
    "tests/fail_closed/test_run_validation_gates.py",
    "tests/tools/test_changed_area_validation_router.py",
    "tests/tools/test_validation_inventory.py",
    "tests/tools/test_validation_scope_registry.py",
    "tests/tools/test_ci_branch_context.py",
)
FORMULA_EXECUTION_FIELDS = (
    "canonical_component_id",
    "canonical_qku_ids",
    "canonical_formula_id_or_null",
    "canonical_algorithm_id_or_null",
    "semantic_version",
    "contract_version",
    "component_kind",
    "identity_authority_state",
    "specification_ref",
    "implementation_ref",
    "binding_profile_ref",
    "parameter_policy_refs",
    "dependency_graph_ref",
    "oracle_pack_ref",
    "evidence_bundle_ref",
    "mode_eligibility_ref",
    "registered_fallback_ref",
    "latency_class",
    "consumer_refs",
    "typed_input_contract",
    "typed_output_contract",
    "context_key",
    "authority_envelope",
)
EVIDENCE_BUNDLE_FIELDS = (
    "evidence_id",
    "schema_version",
    "contract_version",
    "evidence_bundle_version",
    "component_or_template_ref",
    "input_lock_id",
    "actual_executed_component_versions",
    "actual_executed_stack_versions",
    "replay_result_ref",
    "paper_result_ref",
    "divergence_assessment_ref",
    "lane_execution_receipt_refs",
    "calibration_and_probability_quality",
    "transaction_cost_decomposition",
    "fill_and_queue_quality",
    "latency_and_staleness",
    "capacity_and_crowding",
    "portfolio_marginal_contribution",
    "false_discovery_and_overfit_controls",
    "regime_and_scenario_outcomes",
    "uncertainty_and_model_risk_reserves",
    "agent_and_model_disagreement",
    "no_trade_comparison",
    "independent_review_state",
    "failure_and_negative_evidence_states",
    "source_and_provenance_refs",
    "d_evidence_reference_projection",
    "g_handoff_projection",
    "terminal_state",
    "blocker_codes",
)
SUCCESS_MARKER = "QKU_ARCHITECTURE_INDEPENDENTLY_VALIDATED"
EVIDENCE_MARKER = "ST12_ARCHITECTURE_MATH_EVIDENCE_V1"
DECIMAL_CONTEXT = Context(prec=34, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class _ArchitectureMathEvidenceV1:
    math_id: str
    oracle_id: str
    golden_vector_id: str
    comparison_policy: str
    independent_algorithm_id: str
    independent_observed_result: object
    golden_comparison_passed: bool
    formula_or_procedure_mutation_observed: bool
    domain_guard_rejection_observed: bool
    precision_or_tolerance_mutation_observed: bool
    semantic_binding_mutation_observed: bool
    production_import_count: int
    production_callable_count: int
    terminal_state: str
    boundary_vector_id: str | None = None
    negative_vector_id: str | None = None
    property_id: str | None = None
    output_schema_version: str | None = None
    compiled_comparison_policy: str | None = None
    golden_observed_result: object | None = None
    boundary_observed_result: object | None = None
    negative_exception_evidence: object | None = None
    property_mutation_result: object | None = None
    precision_boundary_mutation_result: object | None = None
    semantic_binding_mutation_result: object | None = None
    input_binding_mutation_observed: bool | None = None
    unit_or_basis_mutation_observed_or_not_applicable: str | None = None
    source_binding_mutation_observed_or_not_applicable: str | None = None
    representation_or_convention_mutation_observed_or_not_applicable: str | None = None


def _stationary_means(
    seed: int,
    series: tuple[float, ...] = (1.0, 2.0, 3.0, 4.0, 5.0),
) -> tuple[float, ...]:
    if len(series) < 2:
        raise ValueError("series too short")
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


def _json_rows(tree: ast.Module, name: str) -> list[dict[str, object]]:
    value = json.loads(_string_literal(tree, name))
    if not isinstance(value, list) or any(
        not isinstance(row, dict) for row in value
    ):
        raise ValueError(f"{name} must be a JSON array of objects")
    return value


def _tracked_architecture_material() -> dict[str, dict[str, object]]:
    """Read immutable oracle/vector data without importing production code."""

    tree = ast.parse(
        (PACKAGE / "oracle_contracts.py").read_text(encoding="utf-8"),
        filename=str(PACKAGE / "oracle_contracts.py"),
    )
    legacy_oracle_rows = _json_rows(tree, "_ORACLE_ROWS_JSON")
    legacy_vector_rows = _json_rows(tree, "_GOLDEN_VECTOR_ROWS_JSON")
    st12b_oracle_rows = _json_rows(tree, "_ST12B_ORACLE_CONTRACTS_JSON")
    st12b_vector_rows = _json_rows(tree, "_ST12B_VECTOR_PACK_JSON")
    st12b_property_rows = _json_rows(tree, "_ST12B_PROPERTY_PACK_JSON")

    def unique_by(
        rows: Sequence[Mapping[str, object]],
        key_name: str,
        family: str,
    ) -> dict[str, Mapping[str, object]]:
        counts = Counter(str(row.get(key_name)) for row in rows)
        duplicates = tuple(sorted(key for key, count in counts.items() if count != 1))
        if duplicates:
            raise ValueError(f"{family} identities are not unique: {duplicates!r}")
        return {str(row[key_name]): row for row in rows}

    legacy_oracles = unique_by(legacy_oracle_rows, "math_spec_ref", "legacy oracle")
    legacy_vectors = unique_by(legacy_vector_rows, "math_spec_ref", "legacy vector")
    st12b_oracles = unique_by(st12b_oracle_rows, "math_spec_id", "ST12-B oracle")
    st12b_vectors: dict[str, dict[str, dict[str, object]]] = {}
    vector_keys: set[tuple[str, str]] = set()
    for row in st12b_vector_rows:
        key = (str(row["math_spec_id"]), str(row["case_type"]))
        if key in vector_keys:
            raise ValueError(f"ST12-B vector class is ambiguous: {key!r}")
        vector_keys.add(key)
        st12b_vectors.setdefault(key[0], {})[key[1]] = row
    st12b_properties = unique_by(
        st12b_property_rows,
        "math_spec_id",
        "ST12-B property",
    )

    material: dict[str, dict[str, object]] = {}
    for math_id in ARCHITECTURE_MATH_IDS:
        if math_id in EXPECTED_MATH_IDS:
            oracle = legacy_oracles.get(math_id)
            golden = legacy_vectors.get(math_id)
            if oracle is None or golden is None:
                raise ValueError(f"missing legacy architecture material: {math_id}")
            material[math_id] = {
                "oracle": oracle,
                "golden": golden,
                "boundary": None,
                "negative": None,
                "property": None,
                "oracle_id": str(oracle["oracle_id"]),
                "golden_vector_id": str(golden["vector_id"]),
                "comparison_policy": str(golden["comparison_policy"]),
            }
            continue

        if math_id not in CURRENT_ST12B_ARCHITECTURE_MATH_IDS:
            raise ValueError(f"unrouted architecture material: {math_id}")
        oracle = st12b_oracles.get(math_id)
        vectors = st12b_vectors.get(math_id, {})
        property_row = st12b_properties.get(math_id)
        if (
            oracle is None
            or set(vectors) != {"GOLDEN", "BOUNDARY", "NEGATIVE"}
            or property_row is None
        ):
            raise ValueError(f"missing ST12-B architecture material: {math_id}")
        assert isinstance(oracle, Mapping)
        assert isinstance(property_row, Mapping)
        declared_keys = oracle.get("input_keys")
        if (
            not isinstance(declared_keys, list)
            or not declared_keys
            or len(declared_keys) != len(set(declared_keys))
            or any(not isinstance(key, str) or not key for key in declared_keys)
            or oracle.get("output_schema_ref") != f"{math_id}::OUTPUT"
            or oracle.get("output_schema_version") != "ST12B_OUTPUT_V3_4"
        ):
            raise ValueError(f"invalid current ST12-B oracle contract: {math_id}")
        for case_type in ("GOLDEN", "BOUNDARY", "NEGATIVE"):
            vector = vectors[case_type]
            if (
                vector.get("math_spec_id") != math_id
                or vector.get("case_type") != case_type
                or vector.get("input_keys") != declared_keys
                or not isinstance(vector.get("inputs"), Mapping)
                or len(vector["inputs"]) != len(declared_keys)
                or set(vector["inputs"]) != set(declared_keys)
            ):
                raise ValueError(
                    f"invalid current ST12-B {case_type} binding: {math_id}"
                )
        if (
            property_row.get("math_spec_id") != math_id
            or not isinstance(property_row.get("base_inputs"), Mapping)
            or len(property_row["base_inputs"]) != len(declared_keys)
            or set(property_row["base_inputs"]) != set(declared_keys)
            or not isinstance(property_row.get("mutation"), Mapping)
            or not isinstance(property_row.get("property_id"), str)
            or not property_row.get("property_id")
        ):
            raise ValueError(f"invalid current ST12-B property binding: {math_id}")
        material[math_id] = {
            "oracle": oracle,
            "golden": vectors["GOLDEN"],
            "boundary": vectors["BOUNDARY"],
            "negative": vectors["NEGATIVE"],
            "property": property_row,
            "oracle_id": str(oracle["oracle_id"]),
            "golden_vector_id": str(vectors["GOLDEN"]["vector_id"]),
            "boundary_vector_id": str(vectors["BOUNDARY"]["vector_id"]),
            "negative_vector_id": str(vectors["NEGATIVE"]["vector_id"]),
            "property_id": str(property_row["property_id"]),
            "output_schema_version": str(oracle["output_schema_version"]),
            "comparison_policy": (
                "CANONICAL_STRUCTURE_WITH_DECLARED_NUMERIC_TOLERANCE"
            ),
        }

    if tuple(material) != ARCHITECTURE_MATH_IDS:
        raise ValueError("architecture material denominator/order is not exact")
    if len({row["oracle_id"] for row in material.values()}) != 29 or len(
        {row["golden_vector_id"] for row in material.values()}
    ) != 29:
        raise ValueError("architecture oracle/vector identities are not unique")
    current_rows = tuple(material[math_id] for math_id in CURRENT_ST12B_ARCHITECTURE_MATH_IDS)
    for identity_field in (
        "oracle_id",
        "golden_vector_id",
        "boundary_vector_id",
        "negative_vector_id",
        "property_id",
    ):
        values = tuple(row[identity_field] for row in current_rows)
        if len(values) != 14 or len(set(values)) != 14:
            raise ValueError(
                f"current ST12-B architecture {identity_field} identities are not exact"
            )
    return material


def _finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float | Decimal):
        raise ValueError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _positive_int(value: object, name: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _sequence(value: object, name: str, minimum: int = 1) -> list[object]:
    if (
        isinstance(value, str | bytes)
        or not isinstance(value, Sequence)
        or len(value) < minimum
    ):
        raise ValueError(f"{name} must contain at least {minimum} item(s)")
    return list(value)


def _matrix(value: object, name: str) -> list[list[float]]:
    rows = _sequence(value, name)
    if any(
        isinstance(row, str | bytes)
        or not isinstance(row, Sequence)
        or not row
        for row in rows
    ):
        raise ValueError(f"{name} must be a nonempty rectangular matrix")
    width = len(rows[0])  # type: ignore[arg-type]
    if any(len(row) != width for row in rows):  # type: ignore[arg-type]
        raise ValueError(f"{name} must be rectangular")
    return [
        [
            _finite(item, f"{name}[{row_index}][{column_index}]")
            for column_index, item in enumerate(row)  # type: ignore[union-attr]
        ]
        for row_index, row in enumerate(rows)
    ]


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires data")
    return math.fsum(values) / len(values)


def _sample_variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        raise ValueError("sample variance requires at least two values")
    center = _mean(values)
    return math.fsum((value - center) ** 2 for value in values) / (len(values) - 1)


def _json_ready(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    return value


def _payload_matches(
    observed: object,
    expected: object,
    *,
    absolute_tolerance: float = 1e-12,
) -> bool:
    if isinstance(expected, Mapping):
        return (
            isinstance(observed, Mapping)
            and set(observed) == set(expected)
            and all(
                _payload_matches(
                    observed[key],
                    expected[key],
                    absolute_tolerance=absolute_tolerance,
                )
                for key in expected
            )
        )
    if isinstance(expected, list | tuple):
        return (
            isinstance(observed, list | tuple)
            and len(observed) == len(expected)
            and all(
                _payload_matches(
                    observed_item,
                    expected_item,
                    absolute_tolerance=absolute_tolerance,
                )
                for observed_item, expected_item in zip(
                    observed,
                    expected,
                    strict=True,
                )
            )
        )
    if (
        isinstance(expected, int | float)
        and not isinstance(expected, bool)
        and isinstance(observed, int | float)
        and not isinstance(observed, bool)
    ):
        return math.isclose(
            float(observed),
            float(expected),
            rel_tol=0.0,
            abs_tol=absolute_tolerance,
        )
    return observed == expected


@dataclass(frozen=True)
class _CompiledComparisonPolicyV1:
    declared_policy: str
    operational_policy: str
    absolute_tolerance: float | None
    exact_mapping_order: bool
    exact_decimal_representation: bool


_CURRENT_NUMERIC_TOLERANCE_BY_MATH_ID = {
    "MATH-16": 1e-12,
    "MATH-17": 1e-12,
    "MATH-18": 1e-12,
    "MATH-19": 1e-15,
    "MATH-20": 1e-12,
    "MATH-21": 1e-12,
    "MATH-22": 1e-12,
    "MATH-23": 1e-12,
    "MATH-24": 1e-12,
    "MATH-25": 1e-12,
    "MATH-46": 1e-15,
    "MATH-47": 1e-15,
    "MATH-48": 1e-12,
    "MATH-49": 1e-15,
}


def _compile_comparison_policy(
    declared_policy: str,
    *,
    math_id: str | None = None,
) -> _CompiledComparisonPolicyV1:
    if declared_policy == "CANONICAL_STRUCTURE_WITH_DECLARED_NUMERIC_TOLERANCE":
        if math_id not in _CURRENT_NUMERIC_TOLERANCE_BY_MATH_ID:
            raise ValueError(
                "current nested comparison policy requires an exact math identity"
            )
        tolerance = _CURRENT_NUMERIC_TOLERANCE_BY_MATH_ID[math_id]
        exponent = "1E-15" if tolerance == 1e-15 else "1E-12"
        return _CompiledComparisonPolicyV1(
            declared_policy=declared_policy,
            operational_policy=f"{declared_policy}::{exponent}",
            absolute_tolerance=tolerance,
            exact_mapping_order=False,
            exact_decimal_representation=False,
        )
    definitions = {
        "ABS_TOL_1E-15": (1e-15, False, False),
        "ABS_TOL_1E-12": (1e-12, False, False),
        "EXACT_BOOLEAN_INVARIANT": (None, False, False),
        "EXACT_ORDERING_INDEX_INVARIANT": (None, True, False),
        "EXACT_CANONICAL_STRUCTURE": (None, True, False),
        "EXACT_DECIMAL_FIXED_REPRESENTATION": (None, True, True),
        "ENUMERATION_INVARIANT": (1e-15, False, False),
        "BRUTE_FORCE_ENUMERATION": (1e-12, False, False),
        "EXACT_DISCRETE_ENUMERATION": (1e-15, False, False),
    }
    definition = definitions.get(declared_policy)
    if definition is None:
        raise ValueError(f"unknown comparison policy: {declared_policy}")
    tolerance, exact_order, exact_decimal = definition
    return _CompiledComparisonPolicyV1(
        declared_policy=declared_policy,
        operational_policy=declared_policy,
        absolute_tolerance=tolerance,
        exact_mapping_order=exact_order,
        exact_decimal_representation=exact_decimal,
    )


def _compiled_payload_matches(
    observed: object,
    expected: object,
    policy: _CompiledComparisonPolicyV1,
) -> bool:
    if isinstance(expected, Mapping):
        if not isinstance(observed, Mapping):
            return False
        if policy.exact_mapping_order:
            if tuple(observed) != tuple(expected):
                return False
        elif set(observed) != set(expected):
            return False
        return all(
            _compiled_payload_matches(observed[key], expected[key], policy)
            for key in expected
        )
    if isinstance(expected, list | tuple):
        return (
            isinstance(observed, list | tuple)
            and len(observed) == len(expected)
            and all(
                _compiled_payload_matches(left, right, policy)
                for left, right in zip(observed, expected, strict=True)
            )
        )
    if isinstance(expected, bool):
        return isinstance(observed, bool) and observed is expected
    if isinstance(expected, Decimal):
        return (
            isinstance(observed, Decimal)
            and observed == expected
            and (
                not policy.exact_decimal_representation
                or observed.as_tuple() == expected.as_tuple()
            )
        )
    if (
        isinstance(expected, int | float)
        and not isinstance(expected, bool)
        and isinstance(observed, int | float)
        and not isinstance(observed, bool)
    ):
        if not math.isfinite(float(expected)) or not math.isfinite(float(observed)):
            return False
        if policy.absolute_tolerance is None:
            return type(observed) is type(expected) and observed == expected
        return math.isclose(
            float(observed),
            float(expected),
            rel_tol=0.0,
            abs_tol=policy.absolute_tolerance,
        )
    return type(observed) is type(expected) and observed == expected


def _mutated_copy(value: object, path: Sequence[object], replacement_value: object) -> object:
    clone = json.loads(json.dumps(_json_ready(value), allow_nan=False))
    cursor = clone
    for component in path[:-1]:
        cursor = cursor[component]  # type: ignore[index]
    cursor[path[-1]] = replacement_value  # type: ignore[index]
    return clone


def _comparison_policy_self_rejections() -> int:
    strict = _compile_comparison_policy("ABS_TOL_1E-15")
    if _compiled_payload_matches(0.0, 5e-13, strict):
        raise ValueError("1e-15 comparison was weakened to 1e-12")
    ordered = _compile_comparison_policy("EXACT_ORDERING_INDEX_INVARIANT")
    if _compiled_payload_matches({"b": 2, "a": 1}, {"a": 1, "b": 2}, ordered):
        raise ValueError("exact ordered comparison accepted reordered output")
    decimal_policy = _compile_comparison_policy("EXACT_DECIMAL_FIXED_REPRESENTATION")
    if _compiled_payload_matches(1.25, Decimal("1.25"), decimal_policy):
        raise ValueError("exact Decimal comparison accepted float coercion")
    try:
        _compile_comparison_policy("UNKNOWN_COMPARISON_POLICY")
    except ValueError as exc:
        if "unknown comparison policy" not in str(exc):
            raise
    else:
        raise ValueError("unknown comparison policy was accepted")
    return 4


def _apply_declared_mutation(inputs: object, mutation: Mapping[str, object]) -> object:
    path = mutation.get("path")
    if not isinstance(path, list) or not path:
        raise ValueError("property mutation path must be nonempty")
    return _mutated_copy(inputs, path, mutation.get("replacement"))


def _v34_frozen_literal_checks(failures: list[str]) -> None:
    try:
        trees = {
            name: ast.parse(
                (PACKAGE / name).read_text(encoding="utf-8"),
                filename=str(PACKAGE / name),
            )
            for name in (
                "specification.py",
                "bindings.py",
                "parameter_policy.py",
                "oracle_contracts.py",
                "quantum_adapter.py",
                "validation.py",
            )
        }
        requirements = _json_rows(
            trees["specification.py"], "_ST12B_FORMULA_REQUIREMENTS_JSON"
        )
        input_contracts = _json_rows(
            trees["specification.py"], "_ST12B_FORMULA_INPUT_CONTRACTS_JSON"
        )
        output_contracts = _json_rows(
            trees["specification.py"], "_ST12B_FORMULA_OUTPUT_CONTRACTS_JSON"
        )
        formula_dispositions = _json_rows(
            trees["specification.py"], "_ST12B_FORMULA_DISPOSITIONS_JSON"
        )
        formula_input_owners = _json_rows(
            trees["bindings.py"], "_ST12B_FORMULA_INPUT_AUTHORITY_JSON"
        )
        primary_sources = _json_rows(
            trees["bindings.py"], "_ST12B_PRIMARY_SOURCE_REGISTRY_JSON"
        )
        source_conflicts = _json_rows(
            trees["bindings.py"], "_ST12B_SOURCE_CONFLICT_RESOLUTION_JSON"
        )
        source_currentizations = _json_rows(
            trees["bindings.py"], "_ST12B_SOURCE_CURRENTIZATION_JSON"
        )
        numeric_authorities = _json_rows(
            trees["bindings.py"], "_ST12B_NUMERIC_VALUE_AUTHORITY_JSON"
        )
        online_currentizations = _json_rows(
            trees["bindings.py"], "_ST12B_ONLINE_CURRENTIZATION_JSON"
        )
        parameter_crosswalk = _json_rows(
            trees["parameter_policy.py"], "_ST12B_PARAMETER_CROSSWALK_JSON"
        )
        parameter_applications = _json_rows(
            trees["parameter_policy.py"], "_ST12B_PARAMETER_APPLICATION_JSON"
        )
        parameter_ultimate = _json_rows(
            trees["parameter_policy.py"], "_ST12B_PARAMETER_ULTIMATE_JSON"
        )
        parameter_runtime = _json_rows(
            trees["parameter_policy.py"],
            "_ST12B_RUNTIME_PARAMETER_OWNER_JSON",
        )
        parameter_dispositions = _json_rows(
            trees["parameter_policy.py"], "_ST12B_PARAMETER_DISPOSITION_JSON"
        )
        optimizer_currentizations = _json_rows(
            trees["parameter_policy.py"],
            "_ST12B_OPTIMIZER_DEFAULT_CURRENTIZATION_JSON",
        )
        oracles = _json_rows(
            trees["oracle_contracts.py"], "_ST12B_ORACLE_CONTRACTS_JSON"
        )
        vectors = _json_rows(
            trees["oracle_contracts.py"], "_ST12B_VECTOR_PACK_JSON"
        )
        properties = _json_rows(
            trees["oracle_contracts.py"], "_ST12B_PROPERTY_PACK_JSON"
        )
        quantum = _json_rows(
            trees["quantum_adapter.py"],
            "_ST12B_QUANTUM_STRUCTURAL_READINESS_JSON",
        )
        agent_dag = _json_rows(
            trees["validation.py"], "_ST12B_AGENT_CONSUMER_DAG_JSON"
        )
    except (OSError, SyntaxError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"v3.4 frozen literals could not be reconstructed: {exc}")
        return

    formula_ids = tuple(str(row.get("math_spec_id")) for row in requirements)
    if formula_ids != EXPECTED_ST12B_MATH_IDS:
        failures.append("v3.4 formula requirement identities are not exact")
    if any(
        tuple(str(row.get("math_spec_id")) for row in rows)
        != EXPECTED_ST12B_MATH_IDS
        for rows in (
            input_contracts,
            output_contracts,
            formula_dispositions,
            oracles,
        )
    ):
        failures.append("v3.4 formula/input/output/oracle identities are not aligned")
    if (
        len(output_contracts) != 30
        or sum(len(row.get("members", ())) for row in output_contracts) != 130
        or any(row.get("schema_version") != "ST12B_OUTPUT_V3_4" for row in output_contracts)
    ):
        failures.append("v3.4 named output closure is not 30 schemas/130 members")
    if Counter(str(row.get("disposition")) for row in formula_dispositions) != {
        "REUSE_EXISTING_EXACT_VERSION": 10,
        "REGISTER_SEMANTIC_SUCCESSOR": 9,
        "NEW_TRANCHE_B_IMPLEMENTATION": 11,
    }:
        failures.append("v3.4 formula repository dispositions are not 10/9/11")
    if (
        len(formula_input_owners) != 142
        or len({row.get("binding_id") for row in formula_input_owners}) != 142
    ):
        failures.append("v3.4 formula-input owner denominator is not 142")
    if (
        len(primary_sources) != 55
        or Counter(
            str(row.get("normalized_source_class")) for row in primary_sources
        )
        != {
            "EXTERNAL_PRIMARY_OR_OFFICIAL_SOURCE": 24,
            "OWNER_FORMAL_DERIVATION": 30,
            "OWNER_ARCHITECTURE_OR_POLICY": 1,
        }
        or len(source_conflicts) != 1
        or len(source_currentizations) != 7
        or len(online_currentizations) != 5
    ):
        failures.append("v3.4 source/currentization population is not exact")
    if (
        len(numeric_authorities) != 621
        or Counter(str(row.get("subject_kind")) for row in numeric_authorities)
        != {"PARAMETER": 479, "FORMULA_INPUT": 142}
    ):
        failures.append("v3.4 numeric-value authority population is not 479+142")

    parameter_sets = tuple(
        {str(row.get("parameter_id")) for row in rows}
        for rows in (
            parameter_crosswalk,
            parameter_applications,
            parameter_ultimate,
            parameter_dispositions,
            optimizer_currentizations,
        )
    )
    if (
        any(len(rows) != 479 for rows in parameter_sets)
        or any(rows != parameter_sets[0] for rows in parameter_sets[1:])
        or len(parameter_runtime) != 190
        or not {
            str(row.get("parameter_id")) for row in parameter_runtime
        } <= parameter_sets[0]
        or any(
            row.get("generic_compiler_is_sole_terminal_consumer") is not False
            for row in parameter_ultimate
        )
    ):
        failures.append("v3.4 parameter owner/application closure is not exact")
    if (
        len(vectors) != 90
        or Counter(str(row.get("math_spec_id")) for row in vectors)
        != {math_id: 3 for math_id in EXPECTED_ST12B_MATH_IDS}
        or len(properties) != 30
        or tuple(str(row.get("math_spec_id")) for row in properties)
        != EXPECTED_ST12B_MATH_IDS
    ):
        failures.append("v3.4 oracle/vector/property closure is not 30/90/30")
    if (
        tuple(str(row.get("math_spec_id")) for row in quantum)
        != ("MATH-46", "MATH-47", "MATH-48", "MATH-49")
        or any(row.get("qpu_or_simulator_authority") is not False for row in quantum)
    ):
        failures.append("v3.4 quantum structural readiness is not exact/no-QPU")
    if (
        len(agent_dag) != 1351
        or len({row.get("edge_id") for row in agent_dag}) != 1351
        or any(row.get("orphan_state") is not False for row in agent_dag)
        or Counter(str(row.get("edge_kind")) for row in agent_dag)
        != {
            "FORMULA_SPECIFICATION_TO_CENTRAL_EXECUTION_CONTRACT": 30,
            "NUMERIC_VALUE_OWNER_TO_FORMULA_INPUT": 142,
            "DATA_FLOW_EDGE": 1,
            "CALLABLE_OR_SUBROUTINE_DEPENDENCY": 4,
            "SHARED_POLICY_OR_METHOD_DEPENDENCY": 1,
            "PARAMETER_POLICY_TO_CENTRAL_COMPILER": 479,
            "PARAMETER_POLICY_TO_ULTIMATE_BEHAVIOR_OR_HELD_OWNER": 479,
            "RUNTIME_VALUE_OWNER_TO_PARAMETER_POLICY": 190,
            "PARAMETER_TO_DIRECT_FORMULA_POLICY": 25,
        }
    ):
        failures.append("v3.4 agent/consumer DAG is not the exact 1,351 routes")


def _bh(p_values: tuple[float, ...], q: float, correction: float) -> tuple[int, ...]:
    if (
        not p_values
        or any(not math.isfinite(value) or not 0 <= value <= 1 for value in p_values)
        or not 0 < q <= 1
        or not math.isfinite(correction)
        or correction < 1
    ):
        raise ValueError("invalid multiple-testing inputs")
    ordered = sorted(enumerate(p_values), key=lambda item: (item[1], item[0]))
    largest = 0
    for rank, (_index, value) in enumerate(ordered, 1):
        if value <= rank * q / (len(ordered) * correction):
            largest = rank
    return tuple(sorted(index for index, _value in ordered[:largest]))


def _adjusted_p(
    p_values: tuple[float, ...],
    correction: float,
) -> tuple[float, ...]:
    _bh(p_values, 1.0, correction)
    ordered = sorted(enumerate(p_values), key=lambda item: (item[1], item[0]))
    adjusted_by_rank = [1.0] * len(ordered)
    running = 1.0
    for rank in range(len(ordered), 0, -1):
        running = min(
            running,
            ordered[rank - 1][1] * len(ordered) * correction / rank,
            1.0,
        )
        adjusted_by_rank[rank - 1] = running
    result = [0.0] * len(ordered)
    for (original_index, _value), adjusted in zip(
        ordered,
        adjusted_by_rank,
        strict=True,
    ):
        result[original_index] = adjusted
    return tuple(result)


def _expect_value_error(callable_) -> bool:
    try:
        callable_()
    except (ValueError, ArithmeticError, OverflowError):
        return True
    return False


def _probability_decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(
        value,
        Decimal | str | int | float,
    ):
        raise ValueError("invalid probability type")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("nonfinite probability")
        converted = Decimal(repr(value))
    else:
        converted = Decimal(value)
    if not Decimal(0) <= converted <= Decimal(1):
        raise ValueError("probability outside [0,1]")
    return converted


def _binary_net(
    quantity: object,
    probability: object,
    win_cash: object,
    lose_cash: object,
    *friction: object,
) -> Decimal:
    quantity_value = Decimal(quantity)
    if quantity_value < 0:
        raise ValueError("negative quantity")
    p = _probability_decimal(probability)
    friction_values = tuple(Decimal(value) for value in friction)
    if any(value < 0 for value in friction_values):
        raise ValueError("negative friction")
    return (
        quantity_value
        * (p * Decimal(win_cash) + (Decimal(1) - p) * Decimal(lose_cash))
        - sum(friction_values, Decimal(0))
    )


def _normalize_probabilities(values: tuple[object, ...]) -> tuple[Decimal, ...]:
    if not values:
        raise ValueError("empty probabilities")
    floats = tuple(float(value) for value in values)
    if any(not math.isfinite(value) or not 0 <= value <= 1 for value in floats):
        raise ValueError("invalid probability")
    tolerance = 8 * math.ulp(1.0) * len(values)
    if abs(math.fsum(floats) - 1.0) > tolerance:
        raise ValueError("probability closure")
    canonical = tuple(_probability_decimal(value) for value in values)
    total = sum(canonical, Decimal(0))
    if total <= 0 or abs(total - Decimal(1)) > Decimal(repr(tolerance)):
        raise ValueError("decimal probability closure")
    return tuple(value / total for value in canonical)


def _multi_net(
    probabilities: tuple[object, ...],
    payoffs: tuple[object, ...],
    quantity: object,
    *friction: object,
) -> Decimal:
    if len(probabilities) != len(payoffs):
        raise ValueError("vector mismatch")
    normalized = _normalize_probabilities(probabilities)
    products = sorted(
        probability * Decimal(payoff)
        for probability, payoff in zip(normalized, payoffs, strict=True)
    )
    return (
        Decimal(quantity) * sum(products, Decimal(0))
        - sum((Decimal(value) for value in friction), Decimal(0))
    )


def _brier(p: object, y: object) -> float:
    if isinstance(p, tuple):
        if not isinstance(y, tuple) or len(p) != len(y):
            raise ValueError("vector mismatch")
        probabilities = tuple(float(value) for value in p)
        if (
            abs(math.fsum(probabilities) - 1.0)
            > 8 * math.ulp(1.0) * len(probabilities)
            or any(value not in (0, 1) for value in y)
            or sum(y) != 1
        ):
            raise ValueError("invalid multiclass brier inputs")
        return math.fsum(
            (probability - outcome) ** 2
            for probability, outcome in zip(probabilities, y, strict=True)
        )
    probability = float(_probability_decimal(p))
    if isinstance(y, bool) or y not in (0, 1):
        raise ValueError("unresolved outcome")
    return (probability - y) ** 2


def _log_loss(p: object, y: int, epsilon: float = math.ulp(1.0)) -> float:
    probability = float(_probability_decimal(p))
    if isinstance(y, bool) or y not in (0, 1):
        raise ValueError("unresolved outcome")
    if not 0 < epsilon < 0.5:
        raise ValueError("invalid clipping")
    clipped = min(max(probability, epsilon), 1.0 - epsilon)
    result = -(y * log(clipped) + (1 - y) * log(1 - clipped))
    if not math.isfinite(result):
        raise ValueError("nonfinite loss")
    return result


def _wilson(successes: int, trials: int, confidence: float) -> tuple[float, float]:
    if (
        isinstance(successes, bool)
        or isinstance(trials, bool)
        or trials <= 0
        or not 0 <= successes <= trials
        or not 0 < confidence < 1
    ):
        raise ValueError("invalid Wilson inputs")
    z = NormalDist().inv_cdf(1.0 - (1.0 - confidence) / 2.0)
    phat = successes / trials
    denominator = 1.0 + z * z / trials
    center = (phat + z * z / (2.0 * trials)) / denominator
    half = (
        z
        / denominator
        * sqrt(
            phat * (1.0 - phat) / trials
            + z * z / (4.0 * trials * trials)
        )
    )
    return max(0.0, center - half), min(1.0, center + half)


def _ece_from_raw(
    probabilities: tuple[float, ...],
    outcomes: tuple[int, ...],
    edges: tuple[float, ...],
) -> float:
    if (
        not probabilities
        or len(probabilities) != len(outcomes)
        or len(edges) < 2
        or edges[0] != 0.0
        or edges[-1] != 1.0
        or any(left >= right for left, right in zip(edges, edges[1:]))
        or any(not 0 <= value <= 1 for value in probabilities)
        or any(value not in (0, 1) for value in outcomes)
    ):
        raise ValueError("invalid calibration rows")
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
    if (
        not time_rows
        or not time_rows[0]
        or not any(value != 0.0 for row in time_rows for value in row)
    ):
        raise ValueError("uninformative loss differentials")
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


def _stationary_sample_indices(
    length: int,
    expected_block_length: float,
    rng: Random,
) -> tuple[int, ...]:
    restart_probability = 1.0 / expected_block_length
    current = rng.randrange(length)
    indices = [current]
    for _ in range(1, length):
        if rng.random() < restart_probability:
            current = rng.randrange(length)
        else:
            current = (current + 1) % length
        indices.append(current)
    return tuple(indices)


def _spa_long_run_variance(values: Sequence[float], block: float) -> float:
    count = len(values)
    center = _mean(values)
    demeaned = tuple(value - center for value in values)
    restart_probability = 1.0 / block
    variance = math.fsum(value * value for value in demeaned) / count
    for lag in range(1, count):
        weight = (1.0 - lag / count) * (
            (1.0 - restart_probability) ** lag
        ) + (lag / count) * (
            (1.0 - restart_probability) ** (count - lag)
        )
        covariance = math.fsum(
            demeaned[index] * demeaned[index + lag]
            for index in range(count - lag)
        ) / count
        variance += 2.0 * weight * covariance
    return max(0.0, variance)


def _independent_math_16(inputs: Mapping[str, object]) -> dict[str, object]:
    matrix = _matrix(inputs.get("loss_differentials"), "loss_differentials")
    convention = inputs.get("sign_convention")
    if convention == "BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER":
        pass
    elif convention == (
        "CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS_NEGATED_TO_POSITIVE_IS_BETTER"
    ):
        matrix = [[-value for value in row] for row in matrix]
    else:
        raise ValueError("unsupported loss-differential sign convention")
    observation_count = len(matrix)
    if observation_count < 3:
        raise ValueError("Hansen SPA requires at least three observations")
    if inputs.get("recenter_variant") != "HANSEN_CONSISTENT_LOG_LOG_THRESHOLD":
        raise ValueError("unsupported Hansen SPA recentering rule")
    seed = inputs.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("Hansen SPA seed must be an integer")
    replicates = _positive_int(inputs.get("replicates"), "replicates")
    block = _finite(inputs.get("expected_block_length"), "expected_block_length")
    if not 1.0 <= block <= observation_count:
        raise ValueError("expected block length must be in [1,n]")
    alpha = _finite(inputs.get("alpha"), "alpha")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0,1)")

    candidates = tuple(zip(*matrix, strict=True))
    means = tuple(_mean(candidate) for candidate in candidates)
    variances = tuple(
        _spa_long_run_variance(candidate, block) for candidate in candidates
    )
    valid: list[bool] = []
    standardized: list[float] = []
    for index, (center, variance) in enumerate(
        zip(means, variances, strict=True)
    ):
        if variance <= 0.0:
            if center > 0.0:
                raise ValueError(
                    f"candidate {index} has positive mean and zero long-run variance"
                )
            valid.append(False)
            standardized.append(float("-inf"))
            continue
        threshold = -math.sqrt(
            variance
            / observation_count
            * 2.0
            * math.log(math.log(observation_count))
        )
        valid.append(center >= threshold)
        standardized.append(
            math.sqrt(observation_count) * center / math.sqrt(variance)
        )
    statistic = max(
        0.0,
        max((value for value in standardized if math.isfinite(value)), default=0.0),
    )
    recentered = tuple(
        center if admitted else 0.0
        for center, admitted in zip(means, valid, strict=True)
    )
    rng = Random(seed)
    simulated: list[float] = []
    exceedances = 0
    for _ in range(replicates):
        indices = _stationary_sample_indices(observation_count, block, rng)
        draw = max(
            0.0,
            max(
                (
                    math.sqrt(observation_count)
                    * (
                        math.fsum(candidate[index] for index in indices)
                        / observation_count
                        - center
                    )
                    / math.sqrt(variance)
                    for candidate, center, variance in zip(
                        candidates,
                        recentered,
                        variances,
                        strict=True,
                    )
                    if variance > 0.0
                ),
                default=0.0,
            ),
        )
        simulated.append(draw)
        if draw >= statistic:
            exceedances += 1
    p_value = (1 + exceedances) / (replicates + 1)
    return {
        "statistic": statistic,
        "p_value": p_value,
        "reject": p_value <= alpha,
        "candidate_means": list(means),
        "long_run_variances": list(variances),
        "consistent_valid_columns": valid,
        "simulated_statistics": simulated,
        "recenter_variant": inputs["recenter_variant"],
    }


def _probabilistic_sharpe(
    observed_sharpe: object,
    reference_sharpe: object,
    observations: object,
    skewness: object,
    kurtosis: object,
) -> dict[str, float]:
    observed = _finite(observed_sharpe, "observed_sharpe")
    reference = _finite(reference_sharpe, "reference_sharpe")
    count = _positive_int(
        observations,
        "independent_equivalent_observations",
        minimum=2,
    )
    skew = _finite(skewness, "skewness")
    non_excess_kurtosis = _finite(kurtosis, "kurtosis")
    if non_excess_kurtosis < 1.0:
        raise ValueError("non-excess kurtosis must be at least one")
    denominator_squared = (
        1.0
        - skew * observed
        + ((non_excess_kurtosis - 1.0) / 4.0) * observed * observed
    )
    if denominator_squared <= 0.0:
        raise ValueError("probabilistic Sharpe denominator must be positive")
    z_score = (
        (observed - reference)
        * math.sqrt(count - 1)
        / math.sqrt(denominator_squared)
    )
    return {
        "probabilistic_sharpe_ratio": NormalDist().cdf(z_score),
        "z_score": z_score,
    }


def _independent_math_17(inputs: Mapping[str, object]) -> dict[str, float]:
    return _probabilistic_sharpe(
        inputs.get("estimated_sharpe"),
        inputs.get("reference_sharpe"),
        inputs.get("independent_equivalent_observations"),
        inputs.get("sample_skewness"),
        inputs.get("sample_non_excess_kurtosis"),
    )


def _expected_maximum_sharpe(
    trial_mean: float,
    trial_variance: float,
    effective_count: float,
) -> float:
    if not effective_count > 1.0:
        raise ValueError(
            "effective independent trial count must be greater than one"
        )
    euler_mascheroni = 0.5772156649015329
    return trial_mean + math.sqrt(trial_variance) * (
        (1.0 - euler_mascheroni)
        * NormalDist().inv_cdf(1.0 - 1.0 / effective_count)
        + euler_mascheroni
        * NormalDist().inv_cdf(1.0 - 1.0 / (effective_count * math.e))
    )


def _independent_math_18(inputs: Mapping[str, object]) -> dict[str, float]:
    sharpes = tuple(
        _finite(value, f"complete_material_trial_sharpes[{index}]")
        for index, value in enumerate(
            _sequence(
                inputs.get("complete_material_trial_sharpes"),
                "complete_material_trial_sharpes",
                minimum=2,
            )
        )
    )
    effective_count = _finite(
        inputs.get("effective_independent_trial_count"),
        "effective_independent_trial_count",
    )
    if not 1.0 < effective_count <= len(sharpes):
        raise ValueError(
            "effective independent trial count must be in "
            "(1, material trial count]"
        )
    trial_mean = _mean(sharpes)
    trial_variance = _sample_variance(sharpes)
    expected_maximum = _expected_maximum_sharpe(
        trial_mean,
        trial_variance,
        effective_count,
    )
    psr = _probabilistic_sharpe(
        inputs.get("candidate_estimated_sharpe"),
        expected_maximum,
        inputs.get("candidate_independent_equivalent_observations"),
        inputs.get("candidate_sample_skewness"),
        inputs.get("candidate_sample_non_excess_kurtosis"),
    )
    return {
        "deflated_sharpe_ratio": psr["probabilistic_sharpe_ratio"],
        "expected_maximum_sharpe_threshold": expected_maximum,
        "trial_mean_sharpe": trial_mean,
        "trial_sharpe_variance": trial_variance,
    }


def _stable_midranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: (values[index], index))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        midrank = ((cursor + 1) + end) / 2.0
        for index in order[cursor:end]:
            ranks[index] = midrank
        cursor = end
    return ranks


def _independent_math_19(inputs: Mapping[str, object]) -> dict[str, object]:
    matrix = _matrix(inputs.get("performance_matrix"), "performance_matrix")
    strategy_ids = _sequence(inputs.get("strategy_ids"), "strategy_ids")
    if (
        len(strategy_ids) != len(matrix[0])
        or len(strategy_ids) != len(set(strategy_ids))
        or any(not isinstance(value, str) or not value for value in strategy_ids)
    ):
        raise ValueError("strategy IDs must uniquely identify every column")
    group_count = _positive_int(inputs.get("S"), "S", minimum=2)
    if group_count % 2 or len(matrix) % group_count:
        raise ValueError("S must be even and exactly partition the observations")
    width = len(matrix) // group_count
    groups = tuple(
        tuple(range(group * width, (group + 1) * width))
        for group in range(group_count)
    )
    split_rows: list[dict[str, object]] = []
    logits: list[float] = []
    for train_groups_tuple in combinations(range(group_count), group_count // 2):
        train_groups = set(train_groups_tuple)
        train_indices = tuple(
            index for group in train_groups for index in groups[group]
        )
        test_indices = tuple(
            index
            for group in range(group_count)
            if group not in train_groups
            for index in groups[group]
        )
        train_means = tuple(
            math.fsum(matrix[index][column] for index in train_indices)
            / len(train_indices)
            for column in range(len(strategy_ids))
        )
        best = max(train_means)
        winner = min(
            (
                column
                for column, value in enumerate(train_means)
                if value == best
            ),
            key=lambda column: str(strategy_ids[column]),
        )
        test_means = tuple(
            math.fsum(matrix[index][column] for index in test_indices)
            / len(test_indices)
            for column in range(len(strategy_ids))
        )
        ranks = _stable_midranks(test_means)
        relative_rank = ranks[winner] / (len(strategy_ids) + 1.0)
        logit_value = math.log(relative_rank / (1.0 - relative_rank))
        logits.append(logit_value)
        split_rows.append(
            {
                "train_groups": list(train_groups_tuple),
                "is_winner_strategy_id": strategy_ids[winner],
                "oos_midrank_worst_1_best_n": ranks[winner],
                "relative_rank": relative_rank,
                "logit": logit_value,
            }
        )
    return {
        "probability_of_backtest_overfitting": (
            sum(value <= 0.0 for value in logits) / len(logits)
        ),
        "S": group_count,
        "split_count": len(split_rows),
        "logits": logits,
        "splits": split_rows,
    }


def _parsed_intervals(value: object) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    identifiers: set[str] = set()
    for index, raw in enumerate(_sequence(value, "sample_intervals")):
        if not isinstance(raw, Mapping):
            raise ValueError("sample interval must be a mapping")
        identifier = raw.get("sample_id")
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in identifiers
        ):
            raise ValueError("sample IDs must be unique nonempty strings")
        identifiers.add(identifier)
        start = _finite(raw.get("start"), f"interval[{index}].start")
        end = _finite(raw.get("end"), f"interval[{index}].end")
        if not start < end:
            raise ValueError(
                "intervals use half-open [start,end) semantics and require start<end"
            )
        rows.append({"sample_id": identifier, "start": start, "end": end})
    return sorted(
        rows,
        key=lambda row: (
            float(row["start"]),
            float(row["end"]),
            str(row["sample_id"]),
        ),
    )


def _balanced_blocks(length: int, count: int) -> list[list[int]]:
    if not 2 <= count <= length:
        raise ValueError("fold/group count must be in [2,n]")
    base, remainder = divmod(length, count)
    blocks: list[list[int]] = []
    cursor = 0
    for index in range(count):
        width = base + (1 if index < remainder else 0)
        blocks.append(list(range(cursor, cursor + width)))
        cursor += width
    return blocks


def _intervals_overlap(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return float(left["start"]) < float(right["end"]) and float(
        right["start"]
    ) < float(left["end"])


def _merged_intervals(rows: Sequence[Mapping[str, object]]) -> list[tuple[float, float]]:
    ordered = sorted((float(row["start"]), float(row["end"])) for row in rows)
    merged: list[tuple[float, float]] = []
    for start, end in ordered:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _purged_split(
    intervals: Sequence[Mapping[str, object]],
    test_indices: Sequence[int],
    embargo_duration: float,
) -> dict[str, object]:
    if any(index < 0 or index >= len(intervals) for index in test_indices):
        raise ValueError("test index is outside the interval population")
    test_set = set(test_indices)
    test = [intervals[index] for index in test_indices]
    merged = _merged_intervals(test)
    train: list[str] = []
    purged: list[str] = []
    embargoed: list[str] = []
    for index, row in enumerate(intervals):
        if index in test_set:
            continue
        identifier = str(row["sample_id"])
        if any(_intervals_overlap(row, test_row) for test_row in test):
            purged.append(identifier)
        elif any(
            end <= float(row["start"]) < end + embargo_duration
            for _, end in merged
        ):
            embargoed.append(identifier)
        else:
            train.append(identifier)
    return {
        "test_sample_ids": [str(row["sample_id"]) for row in test],
        "train_sample_ids": train,
        "purged_sample_ids": purged,
        "embargoed_sample_ids": embargoed,
        "merged_test_intervals": [list(value) for value in merged],
    }


def _independent_math_20(inputs: Mapping[str, object]) -> dict[str, object]:
    intervals = _parsed_intervals(inputs.get("sample_intervals"))
    fold_count = _positive_int(inputs.get("folds"), "folds", minimum=2)
    embargo = _finite(inputs.get("embargo_duration"), "embargo_duration")
    if embargo < 0.0:
        raise ValueError("embargo duration must be nonnegative")
    results: list[dict[str, object]] = []
    for fold_id, indices in enumerate(_balanced_blocks(len(intervals), fold_count)):
        row = _purged_split(intervals, indices, embargo)
        row["fold_id"] = fold_id
        results.append(row)
    return {
        "ordered_sample_ids": [str(row["sample_id"]) for row in intervals],
        "interval_semantics": "HALF_OPEN_START_INCLUSIVE_END_EXCLUSIVE",
        "embargo_basis": "TIME_DURATION_AFTER_MERGED_TEST_INTERVAL",
        "folds": results,
    }


def _set_partitions(
    items: tuple[int, ...],
    block_size: int,
) -> list[tuple[tuple[int, ...], ...]]:
    if not items:
        return [tuple()]
    first = items[0]
    results: list[tuple[tuple[int, ...], ...]] = []
    for rest in combinations(items[1:], block_size - 1):
        block = tuple(sorted((first, *rest)))
        remaining = tuple(item for item in items if item not in block)
        for suffix in _set_partitions(remaining, block_size):
            results.append(tuple(sorted((block, *suffix))))
    return sorted(set(results))


def _resolvable_paths(
    group_count: int,
    test_group_count: int,
) -> list[list[tuple[int, ...]]]:
    if group_count % test_group_count:
        raise ValueError(
            "frozen CPCV path assembly requires k_test_groups to divide N_groups"
        )
    splits = list(combinations(range(group_count), test_group_count))
    partitions = _set_partitions(tuple(range(group_count)), test_group_count)
    target_count = math.comb(group_count - 1, test_group_count - 1)
    candidates = {
        split: tuple(partition for partition in partitions if split in partition)
        for split in splits
    }

    def solve(
        uncovered: frozenset[tuple[int, ...]],
        chosen: tuple[tuple[tuple[int, ...], ...], ...],
    ) -> tuple[tuple[tuple[int, ...], ...], ...] | None:
        if not uncovered:
            return chosen if len(chosen) == target_count else None
        if len(chosen) >= target_count:
            return None
        pivot = min(
            uncovered,
            key=lambda split: (
                sum(set(partition) <= uncovered for partition in candidates[split]),
                split,
            ),
        )
        for partition in candidates[pivot]:
            members = frozenset(partition)
            if members <= uncovered:
                answer = solve(uncovered - members, (*chosen, partition))
                if answer is not None:
                    return answer
        return None

    answer = solve(frozenset(splits), tuple())
    if answer is None:
        raise ValueError("deterministic CPCV path design does not exist")
    return [[tuple(block) for block in partition] for partition in answer]


def _independent_math_21(inputs: Mapping[str, object]) -> dict[str, object]:
    intervals = _parsed_intervals(inputs.get("sample_intervals"))
    group_count = _positive_int(inputs.get("N_groups"), "N_groups", minimum=2)
    test_group_count = _positive_int(inputs.get("k_test_groups"), "k_test_groups")
    if (
        not 1 <= test_group_count < group_count
        or group_count > len(intervals)
        or group_count > 8
    ):
        raise ValueError("CPCV requires 1<=k<N<=sample_count and N<=8")
    embargo = _finite(inputs.get("embargo_duration"), "embargo_duration")
    if embargo < 0.0:
        raise ValueError("embargo duration must be nonnegative")
    aggregation_rule = inputs.get("aggregation_rule")
    if aggregation_rule != "ALL_PATHS_NO_CHERRY_PICKING":
        raise ValueError(
            "aggregation_rule must equal ALL_PATHS_NO_CHERRY_PICKING"
        )
    groups = _balanced_blocks(len(intervals), group_count)
    split_rows: list[dict[str, object]] = []
    lookup: dict[tuple[int, ...], int] = {}
    for split_id, group_tuple in enumerate(
        combinations(range(group_count), test_group_count)
    ):
        test_indices = [index for group in group_tuple for index in groups[group]]
        row = _purged_split(intervals, test_indices, embargo)
        row.update({"split_id": split_id, "test_groups": list(group_tuple)})
        split_rows.append(row)
        lookup[group_tuple] = split_id
    partitions = _resolvable_paths(group_count, test_group_count)
    paths = [
        {
            "path_id": path_id,
            "split_ids": [lookup[tuple(block)] for block in partition],
            "test_group_partition": [list(block) for block in partition],
        }
        for path_id, partition in enumerate(partitions)
    ]
    expected_path_count = math.comb(group_count - 1, test_group_count - 1)
    if (
        len(paths) != expected_path_count
        or sorted(split_id for path in paths for split_id in path["split_ids"])
        != list(range(len(split_rows)))
    ):
        raise ValueError("CPCV path coverage invariant failed")
    return {
        "N_groups": group_count,
        "k_test_groups": test_group_count,
        "split_count": len(split_rows),
        "expected_path_count": expected_path_count,
        "path_count": len(paths),
        "aggregation_rule": aggregation_rule,
        "splits": split_rows,
        "paths": paths,
    }


def _logged_rows(value: object) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row_index, raw in enumerate(_sequence(value, "logged_rows")):
        if not isinstance(raw, Mapping):
            raise ValueError("logged row must be a mapping")
        behavior = tuple(
            _finite(item, f"behavior[{index}]")
            for index, item in enumerate(
                _sequence(
                    raw.get("behavior_action_probabilities"),
                    "behavior probabilities",
                )
            )
        )
        target = tuple(
            _finite(item, f"target[{index}]")
            for index, item in enumerate(
                _sequence(
                    raw.get("target_action_probabilities"),
                    "target probabilities",
                )
            )
        )
        predictions = tuple(
            _finite(item, f"reward_model[{index}]")
            for index, item in enumerate(
                _sequence(
                    raw.get("cross_fitted_reward_model_predictions"),
                    "reward-model predictions",
                )
            )
        )
        if not len(behavior) == len(target) == len(predictions):
            raise ValueError("behavior, target, and model vectors must align")
        if (
            any(value < 0.0 or value > 1.0 for value in (*behavior, *target))
            or abs(math.fsum(behavior) - 1.0) > 1e-12
            or abs(math.fsum(target) - 1.0) > 1e-12
            or any(
                pi > 0.0 and mu <= 0.0
                for mu, pi in zip(behavior, target, strict=True)
            )
        ):
            raise ValueError(
                "target support must be contained in behavior support and both "
                "policies must be probability simplexes"
            )
        action = raw.get("logged_action_index")
        fold_id = raw.get("fold_id")
        if (
            isinstance(action, bool)
            or not isinstance(action, int)
            or not 0 <= action < len(behavior)
            or isinstance(fold_id, bool)
            or not isinstance(fold_id, int)
            or fold_id < 0
            or raw.get("cross_fitted_prediction") is not True
        ):
            if raw.get("cross_fitted_prediction") is not True:
                raise ValueError("reward-model prediction must be cross-fitted")
            raise ValueError("logged action and fold state is invalid")
        rows.append(
            {
                "row_id": str(raw.get("row_id")),
                "behavior": behavior,
                "target": target,
                "model": predictions,
                "action": action,
                "reward": _finite(raw.get("reward"), f"reward[{row_index}]"),
                "fold_id": fold_id,
            }
        )
    return rows


def _logged_terms(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    action = int(row["action"])
    behavior = row["behavior"]
    target = row["target"]
    model = row["model"]
    if not isinstance(behavior, tuple) or not isinstance(target, tuple) or not isinstance(model, tuple):
        raise ValueError("parsed logged vectors are unavailable")
    mu = float(behavior[action])
    pi = float(target[action])
    if pi > 0.0 and mu <= 0.0:
        raise ValueError("logged row violates positivity")
    weight = 0.0 if pi == 0.0 else pi / mu
    direct = math.fsum(
        float(probability) * float(prediction)
        for probability, prediction in zip(target, model, strict=True)
    )
    reward = float(row["reward"])
    residual = reward - float(model[action])
    return direct, weight, residual, reward


def _effective_sample_size(weights: Sequence[float]) -> float:
    total = math.fsum(weights)
    squares = math.fsum(value * value for value in weights)
    if total <= 0.0 or squares <= 0.0:
        raise ValueError("weights require positive total and squared total")
    return total * total / squares


def _independent_math_22(inputs: Mapping[str, object]) -> dict[str, object]:
    values: list[float] = []
    weights: list[float] = []
    for row in _logged_rows(inputs.get("logged_rows")):
        direct, weight, residual, _ = _logged_terms(row)
        values.append(direct + weight * residual)
        weights.append(weight)
    return {
        "doubly_robust_estimate": _mean(values),
        "row_values": values,
        "importance_weights": weights,
        "effective_sample_size": (
            _effective_sample_size(weights) if any(weight > 0.0 for weight in weights) else 0.0
        ),
        "clipping_applied": False,
    }


def _independent_math_23(inputs: Mapping[str, object]) -> dict[str, object]:
    values: list[float] = []
    weights: list[float] = []
    for row in _logged_rows(inputs.get("logged_rows")):
        _, weight, _, reward = _logged_terms(row)
        values.append(weight * reward)
        weights.append(weight)
    return {
        "inverse_propensity_score_estimate": _mean(values),
        "row_values": values,
        "importance_weights": weights,
        "effective_sample_size": (
            _effective_sample_size(weights) if any(weight > 0.0 for weight in weights) else 0.0
        ),
        "clipping_applied": False,
    }


def _independent_math_24(inputs: Mapping[str, object]) -> dict[str, float]:
    weights = tuple(
        _finite(item, f"weight[{index}]")
        for index, item in enumerate(_sequence(inputs.get("weights"), "weights"))
    )
    rewards = tuple(
        _finite(item, f"reward[{index}]")
        for index, item in enumerate(_sequence(inputs.get("rewards"), "rewards"))
    )
    if len(weights) != len(rewards):
        raise ValueError("weights and rewards must align")
    if any(weight < 0.0 for weight in weights):
        raise ValueError("weights must be nonnegative with positive total")
    total = math.fsum(weights)
    if total <= 0.0:
        raise ValueError("weights must be nonnegative with positive total")
    return {
        "self_normalized_ips_estimate": math.fsum(
            weight * reward for weight, reward in zip(weights, rewards, strict=True)
        )
        / total,
        "weight_sum": total,
        "effective_sample_size": _effective_sample_size(weights),
    }


def _tau(value: object) -> float:
    if value == "INF":
        return math.inf
    result = _finite(value, "tau")
    if result < 0.0:
        raise ValueError("tau must be nonnegative")
    return result


def _switch_value(row: Mapping[str, object], tau: float) -> float:
    direct, weight, residual, _ = _logged_terms(row)
    return direct + (weight * residual if weight <= tau else 0.0)


def _switch_bias_bound(
    rows: Sequence[Mapping[str, object]],
    tau: float,
    reward_range: float,
) -> float:
    masses: list[float] = []
    for row in rows:
        behavior = row["behavior"]
        target = row["target"]
        if not isinstance(behavior, tuple) or not isinstance(target, tuple):
            raise ValueError("parsed logged policy is unavailable")
        masses.append(
            math.fsum(
                float(pi)
                for mu, pi in zip(behavior, target, strict=True)
                if float(pi) > 0.0 and float(pi) / float(mu) > tau
            )
        )
    return reward_range * _mean(masses)


def _independent_math_25(inputs: Mapping[str, object]) -> dict[str, object]:
    rows = _logged_rows(inputs.get("logged_rows"))
    lower = _finite(inputs.get("reward_lower_bound"), "reward_lower_bound")
    upper = _finite(inputs.get("reward_upper_bound"), "reward_upper_bound")
    if not lower < upper or any(
        not lower <= float(row["reward"]) <= upper for row in rows
    ):
        raise ValueError("reward bounds must be ordered and cover rewards")
    fold_count = _positive_int(inputs.get("outer_fold_count"), "outer_fold_count", minimum=2)
    if {int(row["fold_id"]) for row in rows} != set(range(fold_count)):
        raise ValueError("fold IDs must cover 0..outer_fold_count-1")
    taus = [_tau(value) for value in _sequence(inputs.get("tau_grid"), "tau_grid")]
    if taus != sorted(set(taus)):
        raise ValueError("tau_grid must be unique and ascending")
    fold_results: list[dict[str, object]] = []
    held_out_values: list[float] = []
    for fold in range(fold_count):
        train = [row for row in rows if int(row["fold_id"]) != fold]
        held = [row for row in rows if int(row["fold_id"]) == fold]
        if len(train) < 2 or not held:
            raise ValueError("each fold requires training and held-out support")
        criteria: list[dict[str, object]] = []
        for tau in taus:
            values = [_switch_value(row, tau) for row in train]
            variance_of_mean = _sample_variance(values) / len(values)
            bias = _switch_bias_bound(train, tau, upper - lower)
            criteria.append(
                {
                    "tau": "INF" if math.isinf(tau) else tau,
                    "variance_of_mean": variance_of_mean,
                    "bias_upper_bound": bias,
                    "estimated_mse_upper_bound": variance_of_mean + bias * bias,
                }
            )
        selected_index = min(
            range(len(criteria)),
            key=lambda index: (
                float(criteria[index]["estimated_mse_upper_bound"]),
                taus[index],
            ),
        )
        selected_tau = taus[selected_index]
        values = [_switch_value(row, selected_tau) for row in held]
        held_out_values.extend(values)
        fold_results.append(
            {
                "outer_fold": fold,
                "selected_tau": "INF" if math.isinf(selected_tau) else selected_tau,
                "criteria": criteria,
                "held_out_row_values": values,
            }
        )
    return {
        "switch_ope_estimate": _mean(held_out_values),
        "held_out_row_values": held_out_values,
        "outer_fold_results": fold_results,
        "selection_rule": "MIN_ESTIMATED_MSE_UPPER_BOUND_THEN_SMALLEST_TAU",
        "clipping_applied": False,
    }


def _upper_qubo(
    diagonal_value: object,
    upper_terms_value: object,
    constant_value: object,
) -> tuple[tuple[float, ...], dict[tuple[int, int], float], float]:
    diagonal = tuple(
        _finite(value, f"diagonal[{index}]")
        for index, value in enumerate(_sequence(diagonal_value, "diagonal"))
    )
    upper: dict[tuple[int, int], float] = {}
    for index, raw in enumerate(_sequence(upper_terms_value, "upper_terms", minimum=0)):
        if not isinstance(raw, Mapping):
            raise ValueError("upper-triangular term must be a mapping")
        left = raw.get("i")
        right = raw.get("j")
        if isinstance(left, int) and isinstance(right, int) and (left, right) in upper:
            raise ValueError("duplicate upper-triangular interaction")
        if (
            isinstance(left, bool)
            or not isinstance(left, int)
            or isinstance(right, bool)
            or not isinstance(right, int)
            or not 0 <= left < right < len(diagonal)
        ):
            raise ValueError("QUBO interactions require unique indices with 0<=i<j<n")
        upper[(left, right)] = _finite(raw.get("value"), f"upper_terms[{index}].value")
    return diagonal, upper, _finite(constant_value, "constant")


def _canonical_qubo_from_current_inputs(
    inputs: Mapping[str, object],
) -> tuple[tuple[float, ...], dict[tuple[int, int], float], float, dict[str, object]]:
    representation = inputs.get("representation")
    diagonal = tuple(
        _finite(value, f"diagonal[{index}]")
        for index, value in enumerate(_sequence(inputs.get("diagonal"), "diagonal"))
    )
    if len(diagonal) > 12:
        raise ValueError("bounded exact QUBO enumeration supports at most 12 variables")
    constant = _finite(inputs.get("constant"), "constant")
    raw_upper = _sequence(inputs.get("upper_terms"), "upper_terms", minimum=0)
    raw_matrix = _sequence(
        inputs.get("full_symmetric_matrix"),
        "full_symmetric_matrix",
        minimum=0,
    )
    if representation == "CANONICAL_UPPER_TRIANGULAR":
        if raw_matrix:
            raise ValueError(
                "canonical upper-triangular representation conflicts with full matrix"
            )
        parsed_diagonal, upper, parsed_constant = _upper_qubo(
            diagonal,
            raw_upper,
            constant,
        )
    elif representation == "FULL_SYMMETRIC_ADAPTER_SUM_OFF_DIAGONAL_PAIRS":
        if raw_upper:
            raise ValueError(
                "full-symmetric representation conflicts with upper-triangular terms"
            )
        if len(raw_matrix) != len(diagonal):
            raise ValueError("full symmetric matrix must be square with declared dimension")
        matrix: list[list[float]] = []
        for row_index, raw_row in enumerate(raw_matrix):
            if (
                isinstance(raw_row, str | bytes)
                or not isinstance(raw_row, Sequence)
                or len(raw_row) != len(diagonal)
            ):
                raise ValueError(
                    "full symmetric matrix must be square with declared dimension"
                )
            matrix.append(
                [
                    _finite(value, f"full_symmetric_matrix[{row_index}][{column}]")
                    for column, value in enumerate(raw_row)
                ]
            )
        if any(matrix[index][index] != diagonal[index] for index in range(len(diagonal))):
            raise ValueError("full symmetric matrix diagonal conflicts with explicit diagonal")
        parsed_diagonal = diagonal
        upper = {
            (left, right): matrix[left][right] + matrix[right][left]
            for left in range(len(diagonal))
            for right in range(left + 1, len(diagonal))
        }
        parsed_constant = constant
    else:
        raise ValueError("unknown QUBO representation")
    canonical = {
        "constant": parsed_constant,
        "diagonal": list(parsed_diagonal),
        "representation": "CANONICAL_UPPER_TRIANGULAR",
        "schema_version": "CANONICAL_QUBO_MODEL_V1",
        "upper_terms": [
            {"i": left, "j": right, "value": coefficient}
            for (left, right), coefficient in sorted(upper.items())
        ],
        "variable_count": len(parsed_diagonal),
    }
    return parsed_diagonal, upper, parsed_constant, canonical


def _binary_assignment(value: object, variable_count: int) -> tuple[int, ...]:
    raw = _sequence(value, "binary_assignment")
    if (
        len(raw) != variable_count
        or any(isinstance(item, bool) or not isinstance(item, int) or item not in (0, 1) for item in raw)
    ):
        raise ValueError(
            "binary_assignment must contain one binary integer per variable"
        )
    return tuple(raw)


def _qubo_energy(
    diagonal: Sequence[float],
    upper: Mapping[tuple[int, int], float],
    offset: float,
    assignment_value: object,
) -> float:
    assignment = _binary_assignment(assignment_value, len(diagonal))
    return (
        offset
        + math.fsum(diagonal[index] * int(value) for index, value in enumerate(assignment))
        + math.fsum(
            coefficient * int(assignment[left]) * int(assignment[right])
            for (left, right), coefficient in upper.items()
        )
    )


def _independent_math_46(inputs: Mapping[str, object]) -> dict[str, object]:
    diagonal, upper, constant, canonical = _canonical_qubo_from_current_inputs(inputs)
    selected = _binary_assignment(inputs.get("binary_assignment"), len(diagonal))
    ledger = [
        {
            "binary_assignment": list(assignment),
            "energy": _qubo_energy(diagonal, upper, constant, assignment),
        }
        for assignment in product((0, 1), repeat=len(diagonal))
    ]
    if len(ledger) != 2 ** len(diagonal):
        raise ValueError("bounded QUBO enumeration is incomplete")
    return {
        "binary_assignment": list(selected),
        "canonical_qubo": canonical,
        "energy": _qubo_energy(diagonal, upper, constant, selected),
        "exhaustive_assignments": ledger,
    }


def _ising_from_qubo(
    diagonal: Sequence[float],
    upper: Mapping[tuple[int, int], float],
    offset: float,
) -> tuple[float, tuple[float, ...], dict[tuple[int, int], float]]:
    constant = offset + math.fsum(diagonal) / 2.0 + math.fsum(upper.values()) / 4.0
    linear = [-(value / 2.0) for value in diagonal]
    interactions: dict[tuple[int, int], float] = {}
    for (left, right), coefficient in upper.items():
        linear[left] -= coefficient / 4.0
        linear[right] -= coefficient / 4.0
        interactions[(left, right)] = coefficient / 4.0
    return constant, tuple(linear), interactions


def _ising_energy(
    constant: float,
    linear: Sequence[float],
    interactions: Mapping[tuple[int, int], float],
    spins: Sequence[int],
) -> float:
    if len(spins) != len(linear) or any(value not in (-1, 1) for value in spins):
        raise ValueError("spin assignment must contain one -1/+1 value per variable")
    return (
        constant
        + math.fsum(linear[index] * value for index, value in enumerate(spins))
        + math.fsum(
            coefficient * spins[left] * spins[right]
            for (left, right), coefficient in interactions.items()
        )
    )


def _independent_math_47(inputs: Mapping[str, object]) -> dict[str, object]:
    diagonal, upper, qubo_constant, _canonical = _canonical_qubo_from_current_inputs(inputs)
    selected = _binary_assignment(inputs.get("binary_assignment"), len(diagonal))
    offset, linear, interactions = _ising_from_qubo(diagonal, upper, qubo_constant)
    parity_rows: list[dict[str, object]] = []
    for assignment in product((0, 1), repeat=len(diagonal)):
        spins = tuple(1 - 2 * value for value in assignment)
        qubo_energy = _qubo_energy(diagonal, upper, qubo_constant, assignment)
        ising_energy = _ising_energy(offset, linear, interactions, spins)
        if not math.isclose(qubo_energy, ising_energy, rel_tol=0.0, abs_tol=1e-15):
            raise ValueError("QUBO/Ising assignment-energy parity failed")
        parity_rows.append(
            {
                "binary_assignment": list(assignment),
                "ising_energy": ising_energy,
                "qubo_energy": qubo_energy,
                "spin_assignment": list(spins),
            }
        )
    selected_spins = tuple(1 - 2 * value for value in selected)
    return {
        "binary_assignment": list(selected),
        "binary_to_spin_convention": (
            "x_i=(1-s_i)/2; s=+1 maps to x=0 and s=-1 maps to x=1"
        ),
        "couplers_J": [
            {"i": left, "j": right, "value": coefficient}
            for (left, right), coefficient in sorted(interactions.items())
        ],
        "exhaustive_parity_rows": parity_rows,
        "ising_energy": _ising_energy(offset, linear, interactions, selected_spins),
        "linear_fields_h": list(linear),
        "offset": offset,
        "qubo_energy": _qubo_energy(diagonal, upper, qubo_constant, selected),
        "spin_assignment": list(selected_spins),
    }


def _cqm_expression(
    constant: float,
    linear: Mapping[str, float],
    quadratic: Sequence[tuple[str, str, float]],
    assignment: Mapping[str, float],
) -> float:
    return constant + math.fsum(
        coefficient * assignment[name] for name, coefficient in linear.items()
    ) + math.fsum(
        coefficient * assignment[left] * assignment[right]
        for left, right, coefficient in quadratic
    )


def _parse_cqm_model(
    value: object,
) -> tuple[
    tuple[str, ...],
    tuple[tuple[float, ...], ...],
    tuple[str, ...],
    str,
    float,
    dict[str, float],
    list[tuple[str, str, float]],
    list[dict[str, object]],
    float,
    float,
]:
    if not isinstance(value, Mapping) or set(value) != {
        "constraints",
        "conversion_penalty_candidate",
        "feasibility_tolerance",
        "objective_constant",
        "objective_linear",
        "objective_quadratic",
        "objective_sense",
        "schema_version",
        "variables",
    }:
        raise ValueError("CQM model must match QTT_CQM_GRAMMAR_V1 exactly")
    if value.get("schema_version") != "QTT_CQM_GRAMMAR_V1":
        raise ValueError("unsupported CQM schema version")
    raw_variables = _sequence(value.get("variables"), "CQM variables")
    names: list[str] = []
    domains: list[tuple[float, ...]] = []
    units: list[str] = []
    for index, raw in enumerate(raw_variables):
        if not isinstance(raw, Mapping) or set(raw) != {
            "enumeration_values", "id", "lower", "type", "unit", "upper"
        }:
            raise ValueError("CQM variable must match the typed grammar")
        name = raw.get("id")
        variable_type = raw.get("type")
        unit = raw.get("unit")
        if (
            not isinstance(name, str)
            or not name
            or name in names
            or variable_type not in {"BINARY", "INTEGER"}
            or not isinstance(unit, str)
            or not unit
        ):
            raise ValueError("CQM variable identity/domain/unit is invalid")
        lower = _finite(raw.get("lower"), f"variables[{index}].lower")
        upper = _finite(raw.get("upper"), f"variables[{index}].upper")
        raw_values = _sequence(
            raw.get("enumeration_values"),
            f"variables[{index}].enumeration_values",
        )
        values = tuple(
            _finite(item, f"variables[{index}].enumeration_values")
            for item in raw_values
        )
        if (
            lower > upper
            or len(values) != len(set(values))
            or tuple(sorted(values)) != values
            or any(not lower <= item <= upper for item in values)
            or variable_type == "BINARY" and values != (0.0, 1.0)
            or variable_type == "INTEGER" and any(not item.is_integer() for item in values)
        ):
            raise ValueError("CQM enumeration values violate the declared domain")
        names.append(name)
        domains.append(values)
        units.append(unit)
    if math.prod(len(domain) for domain in domains) > 4096:
        raise ValueError("CQM exact enumeration resource ceiling exceeded")
    known = set(names)

    def linear_terms(raw: object, label: str) -> dict[str, float]:
        if not isinstance(raw, Mapping) or any(key not in known for key in raw):
            raise ValueError(f"{label} contains an unknown variable")
        return {str(key): _finite(item, f"{label}.{key}") for key, item in raw.items()}

    def quadratic_terms(raw: object, label: str) -> list[tuple[str, str, float]]:
        rows: list[tuple[str, str, float]] = []
        seen: set[tuple[str, str]] = set()
        for index, item in enumerate(_sequence(raw, label, minimum=0)):
            if not isinstance(item, Mapping) or set(item) != {"coefficient", "u", "v"}:
                raise ValueError(f"{label} term is malformed")
            left, right = item.get("u"), item.get("v")
            if not isinstance(left, str) or not isinstance(right, str) or left not in known or right not in known:
                raise ValueError(f"{label} contains an unknown variable")
            key = (left, right) if names.index(left) <= names.index(right) else (right, left)
            if key in seen:
                raise ValueError(f"{label} contains duplicate quadratic terms")
            seen.add(key)
            rows.append((left, right, _finite(item.get("coefficient"), f"{label}[{index}]")))
        return rows

    sense = value.get("objective_sense")
    if sense not in {"MINIMIZE", "MAXIMIZE"}:
        raise ValueError("CQM objective sense must be MINIMIZE or MAXIMIZE")
    objective_constant = _finite(value.get("objective_constant"), "objective_constant")
    objective_linear = linear_terms(value.get("objective_linear"), "objective_linear")
    objective_quadratic = quadratic_terms(value.get("objective_quadratic"), "objective_quadratic")
    constraints: list[dict[str, object]] = []
    identifiers: set[str] = set()
    for index, raw in enumerate(_sequence(value.get("constraints"), "constraints", minimum=0)):
        if not isinstance(raw, Mapping) or set(raw) != {
            "constant", "hard", "id", "linear", "quadratic", "rhs", "sense", "soft_penalty_weight"
        }:
            raise ValueError("CQM constraint must match the typed grammar")
        identifier = raw.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in identifiers:
            raise ValueError("CQM constraint IDs must be unique")
        identifiers.add(identifier)
        constraint_sense = raw.get("sense")
        if constraint_sense not in {"LE", "GE", "EQ"}:
            raise ValueError("CQM constraint sense must be LE, GE, or EQ")
        hard = raw.get("hard")
        if not isinstance(hard, bool):
            raise ValueError("CQM constraint hard flag must be Boolean")
        penalty = _finite(raw.get("soft_penalty_weight"), "soft_penalty_weight")
        if penalty < 0.0 or hard and penalty != 0.0 or not hard and penalty <= 0.0:
            raise ValueError("CQM soft penalty weight conflicts with hard/soft state")
        constraints.append(
            {
                "id": identifier,
                "hard": hard,
                "constant": _finite(raw.get("constant"), f"constraints[{index}].constant"),
                "linear": linear_terms(raw.get("linear"), f"constraints[{index}].linear"),
                "quadratic": quadratic_terms(raw.get("quadratic"), f"constraints[{index}].quadratic"),
                "sense": constraint_sense,
                "rhs": _finite(raw.get("rhs"), f"constraints[{index}].rhs"),
                "penalty": penalty,
            }
        )
    tolerance = _finite(value.get("feasibility_tolerance"), "feasibility_tolerance")
    penalty_candidate = _finite(value.get("conversion_penalty_candidate"), "conversion_penalty_candidate")
    if tolerance < 0.0 or penalty_candidate <= 0.0:
        raise ValueError("CQM tolerance and conversion penalty must be positive")
    return (
        tuple(names), tuple(domains), tuple(units), str(sense), objective_constant,
        objective_linear, objective_quadratic, constraints, tolerance, penalty_candidate,
    )


def _constraint_violation(lhs: float, sense: str, rhs: float) -> float:
    if sense == "LE":
        return max(0.0, lhs - rhs)
    if sense == "GE":
        return max(0.0, rhs - lhs)
    return abs(lhs - rhs)


def _independent_math_48(inputs: Mapping[str, object]) -> dict[str, object]:
    (
        names, domains, _units, sense, objective_constant, objective_linear,
        objective_quadratic, constraints, tolerance, conversion_penalty,
    ) = _parse_cqm_model(inputs.get("model"))
    raw_assignment = inputs.get("assignment")
    if not isinstance(raw_assignment, Mapping) or tuple(raw_assignment) != names:
        raise ValueError("assignment must provide every variable exactly once")

    def parsed_assignment(values: Sequence[float] | Mapping[str, object]) -> dict[str, float]:
        if isinstance(values, Mapping):
            result = {name: _finite(values[name], f"assignment.{name}") for name in names}
        else:
            result = {name: float(item) for name, item in zip(names, values, strict=True)}
        if any(result[name] not in domains[index] for index, name in enumerate(names)):
            raise ValueError("assignment value violates the declared variable domain")
        return result

    selected = parsed_assignment(raw_assignment)

    def evaluate(assignment: Mapping[str, float]) -> dict[str, object]:
        raw_objective = _cqm_expression(
            objective_constant, objective_linear, objective_quadratic, assignment
        )
        constraint_rows: list[dict[str, object]] = []
        hard_feasible = True
        soft_penalty = 0.0
        hard_penalty = 0.0
        for row in constraints:
            lhs = _cqm_expression(
                float(row["constant"]),
                row["linear"],  # type: ignore[arg-type]
                row["quadratic"],  # type: ignore[arg-type]
                assignment,
            )
            violation = _constraint_violation(lhs, str(row["sense"]), float(row["rhs"]))
            hard = bool(row["hard"])
            hard_feasible = hard_feasible and (not hard or violation <= tolerance)
            if hard:
                hard_penalty += conversion_penalty * violation * violation
            else:
                soft_penalty += float(row["penalty"]) * violation * violation
            constraint_rows.append(
                {
                    "hard": hard,
                    "id": row["id"],
                    "lhs": lhs,
                    "rhs": float(row["rhs"]),
                    "sense": row["sense"],
                    "soft_penalty_weight": float(row["penalty"]),
                    "violation": violation,
                }
            )
        penalized = raw_objective + soft_penalty if sense == "MINIMIZE" else raw_objective - soft_penalty
        converted = penalized + hard_penalty if sense == "MINIMIZE" else penalized - hard_penalty
        return {
            "assignment": dict(assignment),
            "raw": raw_objective,
            "constraints": constraint_rows,
            "feasible": hard_feasible,
            "soft_penalty": soft_penalty,
            "penalized": penalized,
            "converted": converted,
        }

    ledger = [evaluate(parsed_assignment(values)) for values in product(*domains)]
    feasible = [row for row in ledger if row["feasible"] is True]
    if not feasible:
        raise ValueError("CQM exact fixture has no native feasible assignment")

    def objective_key(row: Mapping[str, object], field: str) -> tuple[object, ...]:
        value = float(row[field])
        assignment = row["assignment"]
        assert isinstance(assignment, Mapping)
        ordered = tuple(float(assignment[name]) for name in names)
        return ((value if sense == "MINIMIZE" else -value), ordered)

    native = min(feasible, key=lambda row: objective_key(row, "penalized"))
    converted = min(ledger, key=lambda row: objective_key(row, "converted"))
    if converted["assignment"] != native["assignment"] or converted["feasible"] is not True:
        raise ValueError("conversion penalty is inadequate for the exact CQM fixture")
    selected_result = evaluate(selected)
    native_assignment = native["assignment"]
    converted_assignment = converted["assignment"]
    assert isinstance(native_assignment, Mapping) and isinstance(converted_assignment, Mapping)
    return {
        "assignment": dict(selected),
        "constraint_evaluations": selected_result["constraints"],
        "conversion_penalty_adequacy": {
            "converted_best_assignment": dict(converted_assignment),
            "matches_native_feasible_optimum": True,
            "penalty": conversion_penalty,
            "state": "ADEQUATE_FOR_EXACT_ENUMERATED_FIXTURE",
        },
        "interpret_back_state": "EXACT_ORIGINAL_VARIABLE_LABELS_AND_UNITS_PRESERVED",
        "objective_sense": sense,
        "original_model_feasible": selected_result["feasible"],
        "penalized_objective": selected_result["penalized"],
        "raw_objective": selected_result["raw"],
        "schema_version": "QTT_CQM_GRAMMAR_V1",
        "small_exact_solution": {
            "assignment": dict(native_assignment),
            "enumerated_assignment_count": len(ledger),
            "feasible_assignment_count": len(feasible),
            "penalized_objective": native["penalized"],
            "raw_objective": native["raw"],
            "state": "EXACT_FEASIBLE_OPTIMUM",
        },
        "soft_penalty": selected_result["soft_penalty"],
    }


def _independent_math_49(inputs: Mapping[str, object]) -> dict[str, object]:
    model = inputs.get("model")
    if not isinstance(model, Mapping) or set(model) != {
        "constant", "linear_biases", "pairwise_biases", "schema_version", "variables"
    }:
        raise ValueError("DQM model must match QTT_DQM_GRAMMAR_V1 exactly")
    if model.get("schema_version") != "QTT_DQM_GRAMMAR_V1":
        raise ValueError("unsupported DQM schema version")
    raw_variables = _sequence(model.get("variables"), "DQM variables")
    variable_names: list[str] = []
    case_sets: list[tuple[str, ...]] = []
    for raw in raw_variables:
        if not isinstance(raw, Mapping) or set(raw) != {"cases", "id"}:
            raise ValueError("DQM variable row is malformed")
        name = raw.get("id")
        cases = raw.get("cases")
        if (
            not isinstance(name, str)
            or not name
            or name in variable_names
            or
            isinstance(cases, str | bytes)
            or not isinstance(cases, Sequence)
            or not cases
            or len(set(cases)) != len(cases)
            or any(not isinstance(case, str) or not case for case in cases)
        ):
            raise ValueError("each DQM variable needs unique nonempty cases")
        variable_names.append(name)
        case_sets.append(tuple(cases))
    if math.prod(len(cases) for cases in case_sets) > 4096:
        raise ValueError("DQM exact enumeration resource ceiling exceeded")
    known_cases = {
        (name, case)
        for name, cases in zip(variable_names, case_sets, strict=True)
        for case in cases
    }
    linear: dict[tuple[str, str], float] = {}
    for index, raw in enumerate(_sequence(model.get("linear_biases"), "linear_biases")):
        if not isinstance(raw, Mapping) or set(raw) != {"bias", "case", "variable"}:
            raise ValueError("DQM linear bias row is malformed")
        key = (raw.get("variable"), raw.get("case"))
        if key not in known_cases or key in linear:
            raise ValueError("DQM linear biases must cover each variable/case exactly once")
        linear[key] = _finite(raw.get("bias"), f"linear_biases[{index}].bias")
    if set(linear) != known_cases:
        raise ValueError("DQM linear biases must cover each variable/case exactly once")
    pairwise: dict[tuple[str, str, str, str], float] = {}
    for index, raw in enumerate(_sequence(model.get("pairwise_biases"), "pairwise_biases", minimum=0)):
        if not isinstance(raw, Mapping) or set(raw) != {"bias", "case_u", "case_v", "u", "v"}:
            raise ValueError("DQM pairwise bias row is malformed")
        left, right = raw.get("u"), raw.get("v")
        left_case, right_case = raw.get("case_u"), raw.get("case_v")
        if (
            not isinstance(left, str) or not isinstance(right, str) or left == right
            or (left, left_case) not in known_cases or (right, right_case) not in known_cases
        ):
            raise ValueError("DQM pairwise bias references an unknown variable or case")
        if variable_names.index(left) > variable_names.index(right):
            left, right, left_case, right_case = right, left, right_case, left_case
        key = (left, str(left_case), right, str(right_case))
        if key in pairwise:
            raise ValueError("DQM pairwise bias is duplicate or conflicting")
        pairwise[key] = _finite(raw.get("bias"), f"pairwise_biases[{index}].bias")
    constant = _finite(model.get("constant"), "DQM constant")

    def energy(assignment: Mapping[str, str]) -> float:
        return constant + math.fsum(
            linear[(name, assignment[name])] for name in variable_names
        ) + math.fsum(
            coefficient
            for (left, left_case, right, right_case), coefficient in pairwise.items()
            if assignment[left] == left_case and assignment[right] == right_case
        )

    raw_assignment = inputs.get("assignment")
    if not isinstance(raw_assignment, Mapping) or tuple(raw_assignment) != tuple(variable_names):
        raise ValueError("assignment must select one known case per variable")
    selected = {name: raw_assignment[name] for name in variable_names}
    if any((name, selected[name]) not in known_cases for name in variable_names):
        raise ValueError("assignment must select one known case per variable")
    ledger: list[dict[str, object]] = []
    for assignment in product(*case_sets):
        mapped = {
            name: case for name, case in zip(variable_names, assignment, strict=True)
        }
        ledger.append({"assignment": mapped, "energy": energy(mapped)})
    optimum = _ordered_dqm_optimum(ledger, variable_names)
    if optimum != _ordered_dqm_optimum(tuple(reversed(ledger)), variable_names):
        raise ValueError("DQM deterministic tie-break drift observed")
    return {
        "assignment": selected,
        "energy": energy(selected),
        "exhaustive_assignments": ledger,
        "interpret_back_state": "EXACT_ORDERED_VARIABLE_AND_CASE_LABELS_PRESERVED",
        "one_hot_expansion_applied": False,
        "schema_version": "QTT_DQM_GRAMMAR_V1",
    }


def _ordered_dqm_optimum(
    ledger: Sequence[Mapping[str, object]],
    variable_names: Sequence[str],
) -> dict[str, object]:
    if not ledger:
        raise ValueError("DQM optimum requires a nonempty assignment ledger")
    selected = min(
        ledger,
        key=lambda row: (
            float(row["energy"]),
            tuple(
                str(row["assignment"][name])  # type: ignore[index]
                for name in variable_names
            ),
        ),
    )
    return _json_ready(selected)  # type: ignore[return-value]


_NEW_ARCHITECTURE_ALGORITHMS = {
    "MATH-16": _independent_math_16,
    "MATH-17": _independent_math_17,
    "MATH-18": _independent_math_18,
    "MATH-19": _independent_math_19,
    "MATH-20": _independent_math_20,
    "MATH-21": _independent_math_21,
    "MATH-22": _independent_math_22,
    "MATH-23": _independent_math_23,
    "MATH-24": _independent_math_24,
    "MATH-25": _independent_math_25,
    "MATH-46": _independent_math_46,
    "MATH-47": _independent_math_47,
    "MATH-48": _independent_math_48,
    "MATH-49": _independent_math_49,
}


def _declared_input_keys(material: Mapping[str, object]) -> tuple[str, ...]:
    oracle = material["oracle"]
    golden = material["golden"]
    if not isinstance(oracle, Mapping) or not isinstance(golden, Mapping):
        raise ValueError("tracked oracle/vector material must be mappings")
    raw = oracle.get("input_keys")
    if raw is None:
        inputs = golden.get("inputs")
        if not isinstance(inputs, Mapping):
            raise ValueError("legacy golden inputs must be a mapping")
        return tuple(str(key) for key in inputs)
    if not isinstance(raw, list) or any(not isinstance(key, str) for key in raw):
        raise ValueError("tracked oracle input keys must be exact strings")
    return tuple(raw)


def _legacy_stationary_bootstrap_means(
    inputs: Mapping[str, object],
) -> tuple[float, ...]:
    series = tuple(
        _finite(value, "stationary bootstrap series value")
        for value in _sequence(inputs.get("series"), "series", minimum=2)
    )
    seed = _positive_int(inputs.get("seed"), "seed", minimum=0)
    replicates = _positive_int(inputs.get("replicates"), "replicates")
    expected_block_length = _finite(
        inputs.get("expected_block_length"),
        "expected_block_length",
    )
    if expected_block_length < 1.0:
        raise ValueError("expected block length must be >= 1")
    restart_probability = 1.0 / expected_block_length
    rng = Random(seed)
    results: list[float] = []
    for _ in range(replicates):
        current = rng.randrange(len(series))
        sample = [series[current]]
        for _position in range(1, len(series)):
            if rng.random() < restart_probability:
                current = rng.randrange(len(series))
            else:
                current = (current + 1) % len(series)
            sample.append(series[current])
        results.append(math.fsum(sample) / len(sample))
    return tuple(results)


def _canonical_decimal_text(value: Decimal) -> str:
    return format(value.normalize(DECIMAL_CONTEXT), "f")


def _execute_legacy_architecture_row(
    math_id: str,
    inputs: object,
    material: Mapping[str, object],
) -> dict[str, object]:
    """Execute the tracked MATH-01..15 vector with independent local arithmetic."""

    if not isinstance(inputs, Mapping):
        raise ValueError("legacy architecture row inputs must be a mapping")
    declared = _declared_input_keys(material)
    if len(inputs) != len(declared) or set(inputs) != set(declared):
        raise ValueError("legacy architecture input binding differs from tracked vector")

    with localcontext(DECIMAL_CONTEXT):
        if math_id == "MATH-01":
            price = Decimal(str(inputs["contract_price"]))
            payout = Decimal(str(inputs["payout_per_winning_contract"]))
            if payout <= 0 or price < 0 or price > payout:
                raise ValueError("invalid binary contract")
            return {"p_market": _canonical_decimal_text(price / payout)}
        if math_id == "MATH-02":
            model = _probability_decimal(inputs["calibrated_model_probability"])
            market = _probability_decimal(inputs["market_implied_probability"])
            return {"edge_probability": _canonical_decimal_text(model - market)}
        if math_id in {"MATH-03", "MATH-04", "MATH-05"}:
            bid = Decimal(str(inputs["best_bid"]))
            ask = Decimal(str(inputs["best_ask"]))
            if bid < 0 or ask < bid:
                raise ValueError("crossed book")
            midpoint = (bid + ask) / Decimal(2)
            spread = ask - bid
            if math_id == "MATH-03":
                return {"mid": _canonical_decimal_text(midpoint)}
            if math_id == "MATH-04":
                return {"spread": _canonical_decimal_text(spread)}
            if midpoint <= 0:
                raise ValueError("zero midpoint")
            return {"relative_spread": _canonical_decimal_text(spread / midpoint)}
        if math_id == "MATH-06":
            result = _binary_net(
                inputs["quantity"],
                inputs["p"],
                inputs["win_cash"],
                inputs["lose_cash"],
                inputs["fees"],
                inputs["acquisition_cost"],
                inputs["expected_slippage"],
                inputs["expected_impact"],
            )
            return {"expected_net_cash": _canonical_decimal_text(result)}
        if math_id == "MATH-07":
            probabilities = tuple(
                _sequence(inputs["probabilities"], "probabilities")
            )
            payoffs = tuple(_sequence(inputs["payoffs"], "payoffs"))
            result = _multi_net(
                probabilities,
                payoffs,
                inputs["quantity"],
                inputs["acquisition_cost"],
                inputs["fees"],
                inputs["expected_slippage"],
                inputs["expected_impact"],
            )
            return {"expected_net_cash": _canonical_decimal_text(result)}
        if math_id == "MATH-08":
            probability = _probability_decimal(inputs["p"])
            outcome = inputs["y"]
            if isinstance(outcome, bool) or outcome not in (0, 1):
                raise ValueError("unresolved outcome")
            return {
                "brier_score": _canonical_decimal_text(
                    (probability - Decimal(outcome)) ** 2
                )
            }

    if math_id == "MATH-09":
        return {
            "log_loss": _log_loss(
                inputs["p"],
                inputs["y"],  # type: ignore[arg-type]
                _finite(inputs["clip_epsilon"], "clip_epsilon"),
            )
        }
    if math_id == "MATH-10":
        raw_bins = _sequence(inputs["bins"], "bins")
        parsed: list[tuple[int, float, float]] = []
        for raw in raw_bins:
            if not isinstance(raw, Mapping) or set(raw) != {
                "count",
                "empirical_frequency",
                "mean_confidence",
            }:
                raise ValueError("invalid calibration bin")
            count = _positive_int(raw["count"], "bin count")
            frequency = float(_probability_decimal(raw["empirical_frequency"]))
            confidence = float(_probability_decimal(raw["mean_confidence"]))
            parsed.append((count, frequency, confidence))
        total = sum(count for count, _frequency, _confidence in parsed)
        return {
            "ece": math.fsum(
                count / total * abs(confidence - frequency)
                for count, frequency, confidence in parsed
            )
        }
    if math_id == "MATH-11":
        successes = _positive_int(inputs["successes"], "successes", minimum=0)
        trials = _positive_int(inputs["trials"], "trials")
        confidence = _finite(inputs["confidence"], "confidence")
        lower, upper = _wilson(successes, trials, confidence)
        return {"lower": lower, "upper": upper}
    if math_id in {"MATH-12", "MATH-13"}:
        p_values = tuple(
            _finite(value, "p value")
            for value in _sequence(inputs["p_values"], "p_values")
        )
        q = _finite(inputs["q"], "q")
        correction = (
            1.0
            if math_id == "MATH-12"
            else math.fsum(1.0 / rank for rank in range(1, len(p_values) + 1))
        )
        rejected = _bh(p_values, q, correction)
        return {
            "largest_rank": len(rejected),
            "rejected_original_indices": list(rejected),
        }
    if math_id == "MATH-14":
        first = _legacy_stationary_bootstrap_means(inputs)
        second = _legacy_stationary_bootstrap_means(inputs)
        series = tuple(
            _finite(value, "series value")
            for value in _sequence(inputs["series"], "series", minimum=2)
        )
        ordered = sorted(first)
        sample_mean = math.fsum(series) / len(series)
        return {
            "interval_contains_sample_mean": ordered[1] <= sample_mean <= ordered[-2],
            "same_seed_reproducible": first == second,
        }
    if math_id == "MATH-15":
        raw_rows = _sequence(
            inputs["loss_differentials"],
            "loss_differentials",
            minimum=2,
        )
        rows = tuple(
            tuple(
                _finite(value, "loss differential")
                for value in _sequence(raw, "loss differential row")
            )
            for raw in raw_rows
        )
        if len({len(row) for row in rows}) != 1:
            raise ValueError("loss differential dimensions differ")
        seed = _positive_int(inputs["seed"], "seed", minimum=0)
        replicates = _positive_int(inputs["replicates"], "replicates")
        p_value = _white_reality_p_value(
            rows,
            benchmark_minus_candidate=True,
            seed=seed,
            replicates=replicates,
        )
        return {"p_value": p_value, "reject": p_value < 0.05}
    raise ValueError(f"no legacy architecture algorithm: {math_id}")


def _legacy_formula_mutation_observed(
    math_id: str,
    material: Mapping[str, object],
    observed: object,
) -> bool:
    golden = material["golden"]
    if not isinstance(golden, Mapping) or not isinstance(golden.get("inputs"), Mapping):
        return False
    inputs = golden["inputs"]
    if math_id == "MATH-14":
        mutated = dict(inputs)
        mutated["seed"] = int(inputs["seed"]) + 1
        return _legacy_stationary_bootstrap_means(inputs) != _legacy_stationary_bootstrap_means(mutated)
    if math_id == "MATH-15":
        mutated = dict(inputs)
        rows = _sequence(inputs["loss_differentials"], "loss differentials")
        mutated["loss_differentials"] = [
            [-_finite(value, "loss differential") for value in _sequence(row, "row")]
            for row in rows
        ]
    else:
        mutations: dict[str, tuple[tuple[object, ...], object]] = {
            "MATH-01": (("contract_price",), "0.43"),
            "MATH-02": (("calibrated_model_probability",), "0.59"),
            "MATH-03": (("best_ask",), "0.45"),
            "MATH-04": (("best_ask",), "0.45"),
            "MATH-05": (("best_ask",), "0.45"),
            "MATH-06": (("p",), "0.70"),
            "MATH-07": (("payoffs", 0), "1.1"),
            "MATH-08": (("p",), "0.60"),
            "MATH-09": (("p",), 0.6),
            "MATH-10": (("bins", 0, "mean_confidence"), 0.7),
            "MATH-11": (("successes",), 7),
            "MATH-12": (("p_values", 0), 0.1),
            "MATH-13": (("p_values", 0), 0.1),
        }
        path, replacement = mutations[math_id]
        mutated = _mutated_copy(inputs, path, replacement)
    changed = _execute_legacy_architecture_row(math_id, mutated, material)
    return not _payload_matches(observed, changed)


def _legacy_domain_rejection_observed(
    math_id: str,
    material: Mapping[str, object],
) -> bool:
    golden = material["golden"]
    if not isinstance(golden, Mapping) or not isinstance(golden.get("inputs"), Mapping):
        return False
    inputs = golden["inputs"]
    mutations: dict[str, tuple[tuple[object, ...], object]] = {
        "MATH-01": (("payout_per_winning_contract",), "0"),
        "MATH-02": (("calibrated_model_probability",), "1.1"),
        "MATH-03": (("best_bid",), "0.50"),
        "MATH-04": (("best_bid",), "0.50"),
        "MATH-05": (("best_ask",), "0.00"),
        "MATH-06": (("p",), "1.1"),
        "MATH-07": (("probabilities", 0), "0.1"),
        "MATH-08": (("y",), 2),
        "MATH-09": (("clip_epsilon",), 0.6),
        "MATH-10": (("bins",), []),
        "MATH-11": (("successes",), 11),
        "MATH-12": (("q",), 0.0),
        "MATH-13": (("q",), 0.0),
        "MATH-14": (("series",), [1.0]),
        "MATH-15": (("loss_differentials",), [[0.0], [0.0], [0.0], [0.0]]),
    }
    path, replacement = mutations[math_id]
    invalid = _mutated_copy(inputs, path, replacement)
    return _expect_rejection(
        lambda: _execute_legacy_architecture_row(math_id, invalid, material)
    )


def _legacy_semantic_binding_mutation_observed(
    math_id: str,
    material: Mapping[str, object],
) -> bool:
    golden = material["golden"]
    if not isinstance(golden, Mapping):
        return False
    observed = _execute_legacy_architecture_row(
        math_id,
        golden.get("inputs"),
        material,
    )
    return _legacy_formula_mutation_observed(math_id, material, observed)


def _execute_new_architecture_row(
    math_id: str,
    inputs: object,
    material: Mapping[str, object],
) -> dict[str, object] | dict[str, float]:
    if not isinstance(inputs, Mapping):
        raise ValueError("architecture row inputs must be a mapping")
    declared = _declared_input_keys(material)
    if len(inputs) != len(declared) or set(inputs) != set(declared):
        raise ValueError("architecture row input binding differs from tracked vector")
    algorithm = _NEW_ARCHITECTURE_ALGORITHMS.get(math_id)
    if algorithm is None:
        raise ValueError(f"missing architecture algorithm: {math_id}")
    return algorithm(inputs)


def _expect_rejection(operation) -> bool:
    try:
        operation()
    except (ValueError, ArithmeticError, OverflowError):
        return True
    return False


def _exact_value_error_message(operation: Callable[[], object]) -> str:
    try:
        operation()
    except ValueError as exc:
        return str(exc)
    raise _EvidenceContractMismatch("invalid operation was accepted")


class _EvidenceContractMismatch(ValueError):
    pass


def _execute_observed_mutation(
    math_id: str,
    material: Mapping[str, object],
    baseline_inputs: Mapping[str, object],
    mutated_inputs: object,
    policy: _CompiledComparisonPolicyV1,
    *,
    mutation_family: str,
) -> dict[str, object]:
    baseline = _execute_new_architecture_row(math_id, baseline_inputs, material)
    try:
        mutated = _execute_new_architecture_row(math_id, mutated_inputs, material)
    except ValueError as exc:
        return {
            "baseline_observed": _json_ready(baseline),
            "mutation_family": mutation_family,
            "mutation_outcome": "TYPED_REJECTION",
            "mutation_exception_type": type(exc).__name__,
            "mutation_exception_message": str(exc),
            "mutation_observed": True,
        }
    changed = not _compiled_payload_matches(baseline, mutated, policy)
    if not changed:
        raise _EvidenceContractMismatch(
            f"{math_id} {mutation_family} produced no observed result change"
        )
    return {
        "baseline_observed": _json_ready(baseline),
        "mutated_observed": _json_ready(mutated),
        "mutation_family": mutation_family,
        "mutation_outcome": "OBSERVED_OUTPUT_CHANGE",
        "mutation_observed": True,
    }


def _observe_exact_negative_operation(
    operation: Callable[[], object],
    *,
    math_id: str,
    vector_id: object,
    expected_name: object,
    expected_message: object,
) -> dict[str, object]:
    if expected_name != "ValueError" or not isinstance(expected_message, str) or not expected_message:
        raise _EvidenceContractMismatch(
            f"{math_id} NEGATIVE exception contract is not exact"
        )
    try:
        operation()
    except ValueError as exc:
        if expected_message not in str(exc):
            raise _EvidenceContractMismatch(
                f"{math_id} NEGATIVE reason mismatch: expected {expected_message!r}; "
                f"observed {str(exc)!r}"
            ) from exc
        return {
            "attempted_execution": True,
            "exception_type": type(exc).__name__,
            "failure_family": f"{math_id}::TRACKED_NEGATIVE_CONTRACT",
            "message": str(exc),
            "message_substring_matched": True,
            "vector_id": vector_id,
        }
    raise _EvidenceContractMismatch(f"{math_id} NEGATIVE vector was accepted")


def _exact_negative_evidence(
    math_id: str,
    material: Mapping[str, object],
) -> dict[str, object]:
    negative = material.get("negative")
    if not isinstance(negative, Mapping):
        raise _EvidenceContractMismatch(f"{math_id} NEGATIVE vector is absent")
    return _observe_exact_negative_operation(
        lambda: _execute_new_architecture_row(
            math_id,
            negative.get("inputs"),
            material,
        ),
        math_id=math_id,
        vector_id=negative.get("vector_id"),
        expected_name=negative.get("expected_exception"),
        expected_message=negative.get("expected_message_contains"),
    )


def _property_mutation_evidence(
    math_id: str,
    material: Mapping[str, object],
    policy: _CompiledComparisonPolicyV1,
) -> dict[str, object]:
    property_row = material.get("property")
    if not isinstance(property_row, Mapping):
        raise _EvidenceContractMismatch(f"{math_id} property row is absent")
    baseline = property_row.get("base_inputs")
    mutation = property_row.get("mutation")
    if not isinstance(baseline, Mapping) or not isinstance(mutation, Mapping):
        raise _EvidenceContractMismatch(f"{math_id} property row is malformed")
    mutated = _apply_declared_mutation(baseline, mutation)
    evidence = _execute_observed_mutation(
        math_id,
        material,
        baseline,
        mutated,
        policy,
        mutation_family="TRACKED_PROPERTY_FORMULA_OR_PROCEDURE_MUTATION",
    )
    evidence.update(
        {
            "property_id": property_row.get("property_id"),
            "required_outcome": property_row.get("required_outcome"),
            "test_id": property_row.get("test_id"),
        }
    )
    return evidence


_PRECISION_INPUT_MUTATIONS: dict[str, tuple[tuple[object, ...], object, str]] = {
    "MATH-16": (("expected_block_length",), 2.25, "BOOTSTRAP_BLOCK_LENGTH_PRECISION"),
    "MATH-17": (("estimated_sharpe",), 0.500001, "SHARPE_INPUT_TOLERANCE"),
    "MATH-18": (("candidate_estimated_sharpe",), 0.500001, "DSR_INPUT_TOLERANCE"),
    "MATH-19": (("performance_matrix", 0, 0), 2.0, "RANK_AND_TIE_BOUNDARY"),
    "MATH-20": (("embargo_duration",), 2.0, "HALF_OPEN_EMBARGO_BOUNDARY"),
    "MATH-21": (("embargo_duration",), 1.5, "CPCV_PATH_EMBARGO_BOUNDARY"),
    "MATH-22": (("logged_rows", 0, "reward"), 0.999999, "DR_REWARD_PRECISION"),
    "MATH-23": (("logged_rows", 0, "reward"), 0.5, "IPS_WEIGHTED_REWARD_PRECISION"),
    "MATH-24": (("weights", 0), 1.600001, "SNIPS_NORMALIZATION_PRECISION"),
    "MATH-25": (("tau_grid", 1), 1.000001, "SWITCH_TAU_INEQUALITY_BOUNDARY"),
    "MATH-46": (("diagonal", 0), 1.000001, "QUBO_COEFFICIENT_PRECISION"),
    "MATH-47": (("diagonal", 0), 1.000001, "QUBO_ISING_PARITY_PRECISION"),
    "MATH-48": (("model", "conversion_penalty_candidate"), 1.0, "CQM_PENALTY_ADEQUACY_BOUNDARY"),
    "MATH-49": (("model", "pairwise_biases", 0, "bias"), -1.999999, "DQM_PAIRWISE_TIE_PRECISION"),
}


def _precision_boundary_mutation_evidence(
    math_id: str,
    material: Mapping[str, object],
    policy: _CompiledComparisonPolicyV1,
) -> dict[str, object]:
    golden = material.get("golden")
    boundary = material.get("boundary")
    if (
        not isinstance(golden, Mapping)
        or not isinstance(golden.get("inputs"), Mapping)
        or not isinstance(boundary, Mapping)
    ):
        raise _EvidenceContractMismatch(f"{math_id} precision/boundary material is absent")
    path, replacement, label = _PRECISION_INPUT_MUTATIONS[math_id]
    mutated = _mutated_copy(golden["inputs"], path, replacement)
    evidence = _execute_observed_mutation(
        math_id,
        material,
        golden["inputs"],
        mutated,
        policy,
        mutation_family=label,
    )
    boundary_observed = _execute_new_architecture_row(
        math_id,
        boundary.get("inputs"),
        material,
    )
    if not _compiled_payload_matches(boundary_observed, boundary.get("expected"), policy):
        raise _EvidenceContractMismatch(f"{math_id} BOUNDARY vector comparison failed")
    evidence.update(
        {
            "boundary_observed": _json_ready(boundary_observed),
            "boundary_vector_id": boundary.get("vector_id"),
            "expected_output_mutated": False,
        }
    )
    return evidence


_BINDING_MUTATIONS: dict[str, tuple[tuple[object, ...], object, str]] = {
    "MATH-16": (("sign_convention",), "CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS_NEGATED_TO_POSITIVE_IS_BETTER", "SIGN_CONVENTION"),
    "MATH-17": (("independent_equivalent_observations",), 101, "SAMPLE_STATISTIC_BASIS"),
    "MATH-18": (("effective_independent_trial_count",), 4.0, "MATERIAL_EFFECTIVE_TRIAL_BASIS"),
    "MATH-19": (("strategy_ids",), ["S-B", "S-A", "S-C"], "STRATEGY_IDENTITY_PARTITION_BINDING"),
    "MATH-20": (("sample_intervals", 0, "start"), -0.25, "HALF_OPEN_INTERVAL_TIME_BASIS"),
    "MATH-21": (("aggregation_rule",), "CHERRY_PICK_ONE_PATH", "ALL_PATHS_AGGREGATION_RULE"),
    "MATH-22": (("logged_rows", 0, "behavior_action_probabilities"), [0.0, 1.0], "BEHAVIOR_TARGET_SUPPORT_BINDING"),
    "MATH-23": (("logged_rows", 0, "logged_action_index"), 1, "LOGGED_ACTION_BINDING"),
    "MATH-24": (("rewards",), [1.0], "WEIGHT_REWARD_ALIGNMENT_BASIS"),
    "MATH-25": (("tau_grid",), [2.0, 1.0], "TAU_GRID_AND_OUTER_FOLD_BINDING"),
    "MATH-46": (("representation",), "UNKNOWN_QUBO_REPRESENTATION", "QUBO_REPRESENTATION_CONVENTION"),
    "MATH-47": (("representation",), "UNKNOWN_BINARY_TO_SPIN_MAPPING", "BINARY_TO_SPIN_MAPPING_CONVENTION"),
    "MATH-48": (("model", "objective_sense"), "MAXIMIZE", "CQM_SCHEMA_UNIT_DOMAIN_OBJECTIVE_SENSE"),
    "MATH-49": (("model", "schema_version"), "QTT_DQM_GRAMMAR_V0", "DQM_SCHEMA_VARIABLE_CASE_PAIRWISE_BINDING"),
}


def _semantic_binding_mutation_evidence(
    math_id: str,
    material: Mapping[str, object],
    policy: _CompiledComparisonPolicyV1,
) -> dict[str, object]:
    golden = material.get("golden")
    if not isinstance(golden, Mapping) or not isinstance(golden.get("inputs"), Mapping):
        raise _EvidenceContractMismatch(f"{math_id} binding material is absent")
    if math_id == "MATH-47":
        baseline = _execute_new_architecture_row(
            math_id,
            golden["inputs"],
            material,
        )
        diagonal, upper, constant, _canonical = _canonical_qubo_from_current_inputs(
            golden["inputs"]
        )
        offset, linear, interactions = _ising_from_qubo(diagonal, upper, constant)
        drift_rows: list[dict[str, object]] = []
        for assignment in product((0, 1), repeat=len(diagonal)):
            wrong_spins = tuple(2 * value - 1 for value in assignment)
            qubo = _qubo_energy(diagonal, upper, constant, assignment)
            wrong_ising = _ising_energy(offset, linear, interactions, wrong_spins)
            if not math.isclose(qubo, wrong_ising, rel_tol=0.0, abs_tol=1e-15):
                drift_rows.append(
                    {
                        "binary_assignment": list(assignment),
                        "drifted_spin_assignment": list(wrong_spins),
                        "ising_energy": wrong_ising,
                        "qubo_energy": qubo,
                    }
                )
        if not drift_rows:
            raise _EvidenceContractMismatch(
                "MATH-47 mapping-convention drift did not break parity"
            )
        return {
            "baseline_observed": _json_ready(baseline),
            "input_binding_mutation_observed": True,
            "mutated_observed": drift_rows,
            "mutation_family": "BINARY_TO_SPIN_MAPPING_CONVENTION",
            "mutation_observed": True,
            "mutation_outcome": "OBSERVED_PARITY_REJECTION",
            "representation_or_convention_mutation_observed_or_not_applicable": (
                "OBSERVED::BINARY_TO_SPIN_MAPPING_CONVENTION"
            ),
            "source_binding_mutation_observed_or_not_applicable": (
                "NOT_APPLICABLE_WITH_PROOF::PURE_TRACKED_VECTOR_HAS_NO_SOURCE_FIELD"
            ),
            "unit_or_basis_mutation_observed_or_not_applicable": (
                "NOT_APPLICABLE_WITH_PROOF::NO_DISTINCT_UNIT_OR_BASIS_FIELD"
            ),
        }
    path, replacement, label = _BINDING_MUTATIONS[math_id]
    mutated = _mutated_copy(golden["inputs"], path, replacement)
    evidence = _execute_observed_mutation(
        math_id,
        material,
        golden["inputs"],
        mutated,
        policy,
        mutation_family=label,
    )
    representation_ids = {"MATH-16", "MATH-20", "MATH-21", "MATH-25", "MATH-46", "MATH-47", "MATH-48", "MATH-49"}
    unit_basis_ids = {"MATH-17", "MATH-18", "MATH-19", "MATH-20", "MATH-21", "MATH-22", "MATH-23", "MATH-24", "MATH-25", "MATH-48"}
    evidence.update(
        {
            "input_binding_mutation_observed": True,
            "unit_or_basis_mutation_observed_or_not_applicable": (
                f"OBSERVED::{label}"
                if math_id in unit_basis_ids
                else "NOT_APPLICABLE_WITH_PROOF::NO_DISTINCT_UNIT_OR_BASIS_FIELD"
            ),
            "source_binding_mutation_observed_or_not_applicable": (
                "NOT_APPLICABLE_WITH_PROOF::PURE_TRACKED_VECTOR_HAS_NO_SOURCE_FIELD"
            ),
            "representation_or_convention_mutation_observed_or_not_applicable": (
                f"OBSERVED::{label}"
                if math_id in representation_ids
                else "NOT_APPLICABLE_WITH_PROOF::NO_DISTINCT_REPRESENTATION_FIELD"
            ),
        }
    )
    return evidence


def _legacy_precision_or_boundary_mutation_observed(
    math_id: str,
    material: Mapping[str, object],
    observed: object,
) -> bool:
    """Use a real legacy-input execution; never mutate stored expected output."""

    return _legacy_formula_mutation_observed(math_id, material, observed)


def _build_architecture_evidence(
    reconstructed_01_15: Mapping[str, bool],
    *,
    production_import_count: int,
    production_callable_count: int,
) -> tuple[_ArchitectureMathEvidenceV1, ...]:
    material = _tracked_architecture_material()
    rows: list[_ArchitectureMathEvidenceV1] = []
    for math_id in ARCHITECTURE_MATH_IDS:
        tracked = material[math_id]
        if math_id in EXPECTED_MATH_IDS:
            golden = tracked["golden"]
            if not isinstance(golden, Mapping):
                raise ValueError(f"legacy golden row is not a mapping: {math_id}")
            observed = _execute_legacy_architecture_row(
                math_id,
                golden.get("inputs"),
                tracked,
            )
            regression_passed = reconstructed_01_15.get(math_id) is True
            comparison_passed = regression_passed and _payload_matches(
                observed,
                golden.get("expected"),
            )
            rows.append(
                _ArchitectureMathEvidenceV1(
                    math_id=math_id,
                    oracle_id=str(tracked["oracle_id"]),
                    golden_vector_id=str(tracked["golden_vector_id"]),
                    comparison_policy=str(tracked["comparison_policy"]),
                    independent_algorithm_id=(
                        f"ARCHITECTURE_LEGACY_INDEPENDENT_RECONSTRUCTION::{math_id}"
                    ),
                    independent_observed_result={
                        "tracked_golden": _json_ready(observed),
                        "legacy_regression_group_passed": regression_passed,
                    },
                    golden_comparison_passed=comparison_passed,
                    formula_or_procedure_mutation_observed=(
                        _legacy_formula_mutation_observed(
                            math_id,
                            tracked,
                            observed,
                        )
                    ),
                    domain_guard_rejection_observed=(
                        _legacy_domain_rejection_observed(math_id, tracked)
                    ),
                    precision_or_tolerance_mutation_observed=(
                        _legacy_precision_or_boundary_mutation_observed(
                            math_id,
                            tracked,
                            observed,
                        )
                    ),
                    semantic_binding_mutation_observed=(
                        _legacy_semantic_binding_mutation_observed(math_id, tracked)
                    ),
                    production_import_count=production_import_count,
                    production_callable_count=production_callable_count,
                    terminal_state=(
                        "INDEPENDENT_ROW_RECONSTRUCTED"
                        if comparison_passed
                        else "INDEPENDENT_ROW_HELD"
                    ),
                )
            )
            continue

        golden = tracked["golden"]
        if not isinstance(golden, Mapping):
            raise ValueError(f"golden row is not a mapping: {math_id}")
        policy = _compile_comparison_policy(
            str(tracked["comparison_policy"]),
            math_id=math_id,
        )
        observed = _execute_new_architecture_row(math_id, golden.get("inputs"), tracked)
        expected = golden.get("expected")
        comparison_passed = _compiled_payload_matches(observed, expected, policy)
        boundary = tracked.get("boundary")
        if not isinstance(boundary, Mapping):
            raise ValueError(f"boundary row is not a mapping: {math_id}")
        boundary_observed = _execute_new_architecture_row(
            math_id,
            boundary.get("inputs"),
            tracked,
        )
        if not _compiled_payload_matches(boundary_observed, boundary.get("expected"), policy):
            raise ValueError(f"{math_id} BOUNDARY vector comparison failed")
        negative_evidence = _exact_negative_evidence(math_id, tracked)
        property_evidence = _property_mutation_evidence(math_id, tracked, policy)
        precision_evidence = _precision_boundary_mutation_evidence(
            math_id,
            tracked,
            policy,
        )
        binding_evidence = _semantic_binding_mutation_evidence(
            math_id,
            tracked,
            policy,
        )
        rows.append(
            _ArchitectureMathEvidenceV1(
                math_id=math_id,
                oracle_id=str(tracked["oracle_id"]),
                golden_vector_id=str(tracked["golden_vector_id"]),
                comparison_policy=str(tracked["comparison_policy"]),
                independent_algorithm_id=(
                    f"ARCHITECTURE_STANDARD_LIBRARY_RECONSTRUCTION::{math_id}::V2"
                ),
                independent_observed_result={
                    "boundary": _json_ready(boundary_observed),
                    "golden": _json_ready(observed),
                    "negative": _json_ready(negative_evidence),
                    "precision_boundary_mutation": _json_ready(precision_evidence),
                    "property_mutation": _json_ready(property_evidence),
                    "semantic_binding_mutation": _json_ready(binding_evidence),
                },
                golden_comparison_passed=comparison_passed,
                formula_or_procedure_mutation_observed=True,
                domain_guard_rejection_observed=True,
                precision_or_tolerance_mutation_observed=True,
                semantic_binding_mutation_observed=True,
                production_import_count=production_import_count,
                production_callable_count=production_callable_count,
                terminal_state=(
                    "INDEPENDENT_ROW_RECONSTRUCTED"
                    if comparison_passed
                    else "INDEPENDENT_ROW_HELD"
                ),
                boundary_vector_id=str(tracked["boundary_vector_id"]),
                negative_vector_id=str(tracked["negative_vector_id"]),
                property_id=str(tracked["property_id"]),
                output_schema_version=str(tracked["output_schema_version"]),
                compiled_comparison_policy=policy.operational_policy,
                golden_observed_result=_json_ready(observed),
                boundary_observed_result=_json_ready(boundary_observed),
                negative_exception_evidence=_json_ready(negative_evidence),
                property_mutation_result=_json_ready(property_evidence),
                precision_boundary_mutation_result=_json_ready(precision_evidence),
                semantic_binding_mutation_result=_json_ready(binding_evidence),
                input_binding_mutation_observed=True,
                unit_or_basis_mutation_observed_or_not_applicable=str(
                    binding_evidence[
                        "unit_or_basis_mutation_observed_or_not_applicable"
                    ]
                ),
                source_binding_mutation_observed_or_not_applicable=str(
                    binding_evidence[
                        "source_binding_mutation_observed_or_not_applicable"
                    ]
                ),
                representation_or_convention_mutation_observed_or_not_applicable=str(
                    binding_evidence[
                        "representation_or_convention_mutation_observed_or_not_applicable"
                    ]
                ),
            )
        )
    return tuple(rows)


def _evidence_contract_failures(
    rows: Sequence[_ArchitectureMathEvidenceV1],
) -> tuple[str, ...]:
    failures: list[str] = []
    material = _tracked_architecture_material()
    if tuple(row.math_id for row in rows) != ARCHITECTURE_MATH_IDS:
        failures.append("architecture evidence identities/order differ")
    if len(rows) != 29 or len({row.math_id for row in rows}) != 29:
        failures.append("architecture evidence denominator/uniqueness differ")
    for row in rows:
        tracked = material.get(row.math_id)
        if tracked is None:
            failures.append(f"{row.math_id}: wrong owner routing")
            continue
        if row.oracle_id != tracked["oracle_id"]:
            failures.append(f"{row.math_id}: wrong oracle ID")
        if row.golden_vector_id != tracked["golden_vector_id"]:
            failures.append(f"{row.math_id}: wrong golden vector ID")
        if row.comparison_policy != tracked["comparison_policy"]:
            failures.append(f"{row.math_id}: wrong comparison policy")
        if row.independent_observed_result in (None, {}, SUCCESS_MARKER):
            failures.append(f"{row.math_id}: missing or marker-only observed result")
        if row.independent_observed_result == {"declared_steps_only": True}:
            failures.append(f"{row.math_id}: declared steps are not execution")
        if row.independent_observed_result == {"stored_expected_object_parity": True}:
            failures.append(f"{row.math_id}: stored expected parity is not execution")
        if "H_AGGREGATE" in row.independent_algorithm_id:
            failures.append(f"{row.math_id}: wrong owner routing")
        if not row.golden_comparison_passed:
            failures.append(f"{row.math_id}: golden comparison failed")
        if not row.formula_or_procedure_mutation_observed:
            failures.append(f"{row.math_id}: formula/procedure mutation missing")
        if not row.domain_guard_rejection_observed:
            failures.append(f"{row.math_id}: domain mutation missing")
        if not row.precision_or_tolerance_mutation_observed:
            failures.append(f"{row.math_id}: precision mutation missing")
        if not row.semantic_binding_mutation_observed:
            failures.append(f"{row.math_id}: semantic binding mutation missing")
        if row.production_import_count != 0:
            failures.append(f"{row.math_id}: production import observed")
        if row.production_callable_count != 0:
            failures.append(f"{row.math_id}: production callable observed")
        if row.terminal_state != "INDEPENDENT_ROW_RECONSTRUCTED":
            failures.append(f"{row.math_id}: row is held")
        if row.math_id in CURRENT_ST12B_ARCHITECTURE_MATH_IDS:
            expected_policy = _compile_comparison_policy(
                str(tracked["comparison_policy"]),
                math_id=row.math_id,
            )
            if row.boundary_vector_id != tracked.get("boundary_vector_id"):
                failures.append(f"{row.math_id}: wrong boundary vector ID")
            if row.negative_vector_id != tracked.get("negative_vector_id"):
                failures.append(f"{row.math_id}: wrong negative vector ID")
            if row.property_id != tracked.get("property_id"):
                failures.append(f"{row.math_id}: wrong property ID")
            if row.output_schema_version != "ST12B_OUTPUT_V3_4":
                failures.append(f"{row.math_id}: wrong current output schema version")
            if row.compiled_comparison_policy != expected_policy.operational_policy:
                failures.append(f"{row.math_id}: comparison policy was not compiled")
            if row.golden_observed_result is None:
                failures.append(f"{row.math_id}: current GOLDEN execution missing")
            if row.boundary_observed_result is None:
                failures.append(f"{row.math_id}: current BOUNDARY execution missing")
            negative = row.negative_exception_evidence
            if (
                not isinstance(negative, Mapping)
                or negative.get("attempted_execution") is not True
                or negative.get("exception_type") != "ValueError"
                or negative.get("message_substring_matched") is not True
            ):
                failures.append(f"{row.math_id}: exact NEGATIVE evidence missing")
            property_result = row.property_mutation_result
            if (
                not isinstance(property_result, Mapping)
                or property_result.get("mutation_observed") is not True
            ):
                failures.append(f"{row.math_id}: property execution evidence missing")
            precision = row.precision_boundary_mutation_result
            if (
                not isinstance(precision, Mapping)
                or precision.get("mutation_observed") is not True
                or precision.get("expected_output_mutated") is not False
                or precision.get("boundary_observed") is None
            ):
                failures.append(f"{row.math_id}: actual precision/boundary evidence missing")
            binding = row.semantic_binding_mutation_result
            if (
                not isinstance(binding, Mapping)
                or binding.get("mutation_observed") is not True
                or row.input_binding_mutation_observed is not True
            ):
                failures.append(f"{row.math_id}: semantic binding evidence missing")
            for label, value in (
                ("unit/basis", row.unit_or_basis_mutation_observed_or_not_applicable),
                ("source", row.source_binding_mutation_observed_or_not_applicable),
                (
                    "representation/convention",
                    row.representation_or_convention_mutation_observed_or_not_applicable,
                ),
            ):
                if not isinstance(value, str) or not value.startswith(
                    ("OBSERVED::", "NOT_APPLICABLE_WITH_PROOF::")
                ):
                    failures.append(
                        f"{row.math_id}: false or absent {label} mutation disposition"
                    )
            if ("tracked_legacy_" + "golden_is_locked_fixture") in json.dumps(
                _json_ready(asdict(row)),
                sort_keys=True,
            ):
                failures.append(f"{row.math_id}: stale legacy fixture evidence emitted")
    return tuple(failures)


def _exercise_evidence_contract_mutations(
    rows: tuple[_ArchitectureMathEvidenceV1, ...],
) -> int:
    first = rows[0]
    current_index = len(EXPECTED_MATH_IDS)
    current = rows[current_index]

    def replace_current(value: _ArchitectureMathEvidenceV1) -> tuple[_ArchitectureMathEvidenceV1, ...]:
        return (*rows[:current_index], value, *rows[current_index + 1 :])

    mutations: tuple[Sequence[_ArchitectureMathEvidenceV1], ...] = (
        rows[1:],
        (*rows, first),
        (replace(first, oracle_id="WRONG::ORACLE"), *rows[1:]),
        (replace(first, golden_vector_id="WRONG::VECTOR"), *rows[1:]),
        (replace(first, comparison_policy="WRONG_POLICY"), *rows[1:]),
        (replace(first, independent_observed_result=None), *rows[1:]),
        (replace(first, independent_observed_result=SUCCESS_MARKER), *rows[1:]),
        (replace(first, independent_observed_result={"declared_steps_only": True}), *rows[1:]),
        (replace(first, independent_observed_result={"stored_expected_object_parity": True}), *rows[1:]),
        (replace(first, formula_or_procedure_mutation_observed=False), *rows[1:]),
        (replace(first, domain_guard_rejection_observed=False), *rows[1:]),
        (replace(first, precision_or_tolerance_mutation_observed=False), *rows[1:]),
        (replace(first, semantic_binding_mutation_observed=False), *rows[1:]),
        (replace(first, production_import_count=1), *rows[1:]),
        (replace(first, production_callable_count=1), *rows[1:]),
        (replace(first, independent_algorithm_id="H_AGGREGATE_VALIDATOR"), *rows[1:]),
        replace_current(replace(current, boundary_vector_id="WRONG::BOUNDARY")),
        replace_current(replace(current, negative_vector_id="WRONG::NEGATIVE")),
        replace_current(replace(current, property_id="WRONG::PROPERTY")),
        replace_current(replace(current, compiled_comparison_policy=None)),
        replace_current(replace(current, golden_observed_result=None)),
        replace_current(replace(current, boundary_observed_result=None)),
        replace_current(replace(current, negative_exception_evidence=None)),
        replace_current(replace(current, property_mutation_result=None)),
        replace_current(replace(current, precision_boundary_mutation_result=None)),
        replace_current(replace(current, semantic_binding_mutation_result=None)),
        replace_current(replace(current, input_binding_mutation_observed=False)),
        replace_current(
            replace(
                current,
                source_binding_mutation_observed_or_not_applicable="RENAMED_KEY_ONLY",
            )
        ),
        replace_current(
            replace(
                current,
                precision_boundary_mutation_result={
                    "boundary_observed": {},
                    "expected_output_mutated": True,
                    "mutation_observed": True,
                },
            )
        ),
    )
    if any(not _evidence_contract_failures(candidate) for candidate in mutations):
        raise ValueError("architecture grouped evidence mutation escaped rejection")

    material = _tracked_architecture_material()
    for math_id in ("MATH-46", "MATH-47", "MATH-48", "MATH-49"):
        row = next(item for item in rows if item.math_id == math_id)
        stale_index = rows.index(row)
        stale = (
            *rows[:stale_index],
            replace(
                row,
                oracle_id=f"ORACLE::{math_id}::LEGACY",
                boundary_vector_id=None,
                negative_vector_id=None,
                property_id=None,
            ),
            *rows[stale_index + 1 :],
        )
        if not _evidence_contract_failures(stale):
            raise ValueError(f"legacy material selection escaped for {math_id}")

    try:
        _observe_exact_negative_operation(
            lambda: (_ for _ in ()).throw(ValueError("wrong ValueError")),
            math_id="MATH-18",
            vector_id="VECTOR::MATH-18::NEGATIVE",
            expected_name="ValueError",
            expected_message="effective independent trial count",
        )
    except _EvidenceContractMismatch:
        pass
    else:
        raise ValueError("generic ValueError satisfied an exact negative contract")

    operational_checks = 0
    for math_id in CURRENT_ST12B_ARCHITECTURE_MATH_IDS:
        _exact_negative_evidence(math_id, material[math_id])
        operational_checks += 1

    math_18 = material["MATH-18"]
    golden_18 = math_18["golden"]
    assert isinstance(golden_18, Mapping) and isinstance(golden_18.get("inputs"), Mapping)
    invalid_18 = dict(golden_18["inputs"])
    invalid_18["effective_independent_trial_count"] = 1.0
    if "(1, material trial count]" not in _exact_value_error_message(
        lambda: _execute_new_architecture_row("MATH-18", invalid_18, math_18)
    ):
        raise ValueError("MATH-18 effective trial count 1.0 was not rejected exactly")
    operational_checks += 1

    math_21 = material["MATH-21"]
    golden_21 = math_21["golden"]
    assert isinstance(golden_21, Mapping) and isinstance(golden_21.get("inputs"), Mapping)
    invalid_21 = dict(golden_21["inputs"])
    invalid_21["aggregation_rule"] = "NONEMPTY_BUT_WRONG"
    if "ALL_PATHS_NO_CHERRY_PICKING" not in _exact_value_error_message(
        lambda: _execute_new_architecture_row("MATH-21", invalid_21, math_21)
    ):
        raise ValueError("MATH-21 accepted a wrong nonempty aggregation token")
    operational_checks += 1

    math_46 = material["MATH-46"]
    golden_46 = math_46["golden"]
    assert isinstance(golden_46, Mapping)
    full_symmetric_46 = {
        "representation": "FULL_SYMMETRIC_ADAPTER_SUM_OFF_DIAGONAL_PAIRS",
        "diagonal": [1.0, -2.0],
        "upper_terms": [],
        "full_symmetric_matrix": [[1.0, 1.0], [2.0, -2.0]],
        "constant": 0.5,
        "binary_assignment": [1, 0],
    }
    converted_46 = _execute_new_architecture_row(
        "MATH-46",
        full_symmetric_46,
        math_46,
    )
    policy_46 = _compile_comparison_policy(
        str(math_46["comparison_policy"]),
        math_id="MATH-46",
    )
    if not _compiled_payload_matches(converted_46, golden_46.get("expected"), policy_46):
        raise ValueError("MATH-46 full-symmetric adapter changed canonical QUBO meaning")
    conflicting_46 = dict(full_symmetric_46)
    conflicting_46["upper_terms"] = [{"i": 0, "j": 1, "value": 3.0}]
    if "conflicts" not in _exact_value_error_message(
        lambda: _execute_new_architecture_row("MATH-46", conflicting_46, math_46)
    ):
        raise ValueError("MATH-46 conflicting representations were accepted")
    operational_checks += 2

    math_47 = material["MATH-47"]
    golden_47 = math_47["golden"]
    assert isinstance(golden_47, Mapping)
    output_47 = _execute_new_architecture_row("MATH-47", golden_47.get("inputs"), math_47)
    drifted_47 = _mutated_copy(output_47, ("offset",), float(output_47["offset"]) + 1.0)
    policy_47 = _compile_comparison_policy(str(math_47["comparison_policy"]), math_id="MATH-47")
    if _compiled_payload_matches(drifted_47, golden_47.get("expected"), policy_47):
        raise ValueError("MATH-47 sign/offset parity drift escaped comparison")
    operational_checks += 1

    math_48 = material["MATH-48"]
    golden_48 = math_48["golden"]
    assert isinstance(golden_48, Mapping) and isinstance(golden_48.get("inputs"), Mapping)
    inadequate_48 = _mutated_copy(
        golden_48["inputs"],
        ("model", "conversion_penalty_candidate"),
        1.0,
    )
    if "conversion penalty is inadequate" not in _exact_value_error_message(
        lambda: _execute_new_architecture_row("MATH-48", inadequate_48, math_48)
    ):
        raise ValueError("MATH-48 inadequate conversion penalty was accepted")
    if _execute_new_architecture_row("MATH-48", golden_48["inputs"], math_48).get(
        "schema_version"
    ) != "QTT_CQM_GRAMMAR_V1":
        raise ValueError("MATH-48 current CQM grammar was not executed")
    operational_checks += 2

    math_49 = material["MATH-49"]
    golden_49 = math_49["golden"]
    assert isinstance(golden_49, Mapping) and isinstance(golden_49.get("inputs"), Mapping)
    with_pairwise = _execute_new_architecture_row("MATH-49", golden_49["inputs"], math_49)
    without_pairwise_inputs = _mutated_copy(
        golden_49["inputs"],
        ("model", "pairwise_biases"),
        [],
    )
    without_pairwise = _execute_new_architecture_row(
        "MATH-49",
        without_pairwise_inputs,
        math_49,
    )
    if with_pairwise["energy"] == without_pairwise["energy"]:
        raise ValueError("MATH-49 pairwise interaction was ignored")
    operational_checks += 1

    source_text = Path(__file__).read_text(encoding="utf-8")
    renamed_key_token = "WRONG_" + "UNIT_OR_SOURCE"
    stale_fixture_token = "tracked_legacy_" + "golden_is_locked_fixture"
    if renamed_key_token in source_text or stale_fixture_token in source_text:
        raise ValueError("false renamed-key or legacy evidence design remains")
    operational_checks += 1
    return (
        len(mutations)
        + 4
        + operational_checks
        + _comparison_policy_self_rejections()
        + _exercise_independence_guard_mutations()
    )


def _independent_source_boundary_counts_for_tree(
    tree: ast.Module,
) -> tuple[int, int]:
    production_import_count = 0
    production_callable_count = 0
    forbidden_aliases: set[str] = set()

    def production_module(name: str) -> bool:
        return (
            name == "qtt"
            or name.startswith("qtt.")
            or name == "src.qtt"
            or name.startswith("src.qtt.")
        )

    def forbidden_symbol(name: str) -> bool:
        lowered = name.lower()
        return (
            name == "IMPLEMENTATION_REGISTRY"
            or name.startswith("TRANCHE_A_ORACLE_BY_MATH_ID")
            or name.startswith("compute_math_")
            or "production" in lowered and "registry" in lowered
            or lowered in {
                "validate_domain",
                "validate_qku_computation_control_plane",
                "import_module",
            }
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if production_module(alias.name) or alias.name == "importlib" or alias.name.startswith("importlib."):
                    production_import_count += 1
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if (
                node.level > 0
                or production_module(module)
                or module == "src"
                and any(alias.name == "qtt" for alias in node.names)
                or module == "importlib"
                or module.startswith("importlib.")
            ):
                production_import_count += 1
        elif isinstance(node, ast.Assign):
            value_name = ""
            if isinstance(node.value, ast.Name):
                value_name = node.value.id
            elif isinstance(node.value, ast.Attribute):
                value_name = node.value.attr
            if forbidden_symbol(value_name):
                forbidden_aliases.update(
                    target.id for target in node.targets if isinstance(target, ast.Name)
                )
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                production_callable_count += int(
                    node.func.id in {"eval", "exec", "__import__"}
                    or forbidden_symbol(node.func.id)
                    or node.func.id in forbidden_aliases
                )
            elif isinstance(node.func, ast.Attribute):
                production_callable_count += int(
                    forbidden_symbol(node.func.attr)
                    or (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "importlib"
                    )
                )
        elif isinstance(node, ast.Name):
            production_callable_count += int(
                node.id == "IMPLEMENTATION_REGISTRY"
                or node.id.startswith("TRANCHE_A_ORACLE_BY_MATH_ID")
            )
        elif isinstance(node, ast.Attribute):
            production_callable_count += int(
                node.attr == "IMPLEMENTATION_REGISTRY"
                or node.attr.startswith("TRANCHE_A_ORACLE_BY_MATH_ID")
            )
    return production_import_count, production_callable_count


def _independent_source_boundary_counts() -> tuple[int, int]:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"), filename=__file__)
    return _independent_source_boundary_counts_for_tree(tree)


def _exercise_independence_guard_mutations() -> int:
    prohibited_sources = (
        "import qtt",
        "import src.qtt.validation",
        "from src import qtt",
        "from qtt.foo import compute_math_46\ncompute_math_46()",
        "from src.qtt.foo import validate_domain\nvalidate_domain()",
        "from .production import oracle",
        "import importlib\nimportlib.import_module('src.qtt.validation')",
        "eval('1 + 1')",
        "exec('answer = 2')",
        "__import__('qtt')",
        "runner = compute_math_46\nrunner()",
        "registry = IMPLEMENTATION_REGISTRY",
    )
    for source in prohibited_sources:
        counts = _independent_source_boundary_counts_for_tree(ast.parse(source))
        if counts == (0, 0):
            raise ValueError(
                f"independence guard accepted prohibited source: {source!r}"
            )
    return len(prohibited_sources)


def independently_reconstruct() -> dict[str, bool]:
    with localcontext(DECIMAL_CONTEXT):
        def implied(price: object, payout: object) -> Decimal:
            price_value = Decimal(price)
            payout_value = Decimal(payout)
            if payout_value <= 0 or not 0 <= price_value <= payout_value:
                raise ValueError("invalid binary contract")
            return price_value / payout_value

        def edge(model: object, market: object) -> float:
            model_value = float(_probability_decimal(model))
            market_value = float(_probability_decimal(market))
            return model_value - market_value

        def book(bid: object, ask: object) -> tuple[Decimal, Decimal, Decimal]:
            bid_value = Decimal(bid)
            ask_value = Decimal(ask)
            if bid_value < 0 or ask_value < bid_value:
                raise ValueError("crossed book")
            midpoint = (bid_value + ask_value) / Decimal(2)
            spread = ask_value - bid_value
            if midpoint <= 0:
                raise ValueError("zero midpoint")
            return midpoint, spread, spread / midpoint

        midpoint = (Decimal("0.42") + Decimal("0.44")) / Decimal(2)
        spread = Decimal("0.44") - Decimal("0.42")
        math_01 = (
            implied("0.42", "1.00") == Decimal("0.42")
            and implied("0.84", "2.00") == implied("0.42", "1.00")
            and implied("0", "1") == 0
            and implied("1", "1") == 1
            and _expect_value_error(lambda: implied("1", "0"))
        )
        math_02 = (
            abs(edge(0.58, 0.52) - 0.06) <= 1e-15
            and edge(0.58, 0.52) == -edge(0.52, 0.58)
            and _expect_value_error(lambda: edge(1.01, 0.5))
        )
        translated = book("10.42", "10.44")
        base_book = book("0.42", "0.44")
        scaled_book = book("0.84", "0.88")
        math_03 = (
            midpoint == Decimal("0.43")
            and (Decimal("0.44") + Decimal("0.42")) / Decimal(2) == midpoint
            and Decimal("0.42") <= midpoint <= Decimal("0.44")
            and _expect_value_error(lambda: book("0.5", "0.4"))
        )
        math_04 = (
            spread == Decimal("0.02")
            and spread >= 0
            and translated[1] == spread
            and _expect_value_error(lambda: book("0.5", "0.4"))
        )
        math_05 = (
            base_book[2]
            == Decimal("0.04651162790697674418604651162790698")
            and scaled_book[2] == base_book[2]
            and _expect_value_error(lambda: book("0", "0"))
        )
        math_06_golden = _binary_net(
            "1",
            0.60,
            "0.55",
            "-0.45",
            "0.01",
            "0",
            "0",
            "0",
        )
        math_06 = (
            math_06_golden == Decimal("0.14")
            and math_06_golden
            == _binary_net(
                "1",
                "0.60",
                "0.55",
                "-0.45",
                "0.01",
                "0",
                "0",
                "0",
            )
            and _binary_net("1", 0.0, "2", "-1", "0", "0", "0", "0")
            == Decimal("-1")
            and _binary_net("1", 1.0, "2", "-1", "0", "0", "0", "0")
            == Decimal("2")
            and _binary_net("2", 0.6, "2", "-1", "0", "0", "0", "0")
            == 2 * _binary_net("1", 0.6, "2", "-1", "0", "0", "0", "0")
            and _expect_value_error(
                lambda: _binary_net("1", float("nan"), "1", "0", "0", "0", "0", "0")
            )
            and _expect_value_error(
                lambda: _binary_net("1", 1.1, "1", "0", "0", "0", "0", "0")
            )
        )
        math_07_golden = _multi_net(
            (0.2, 0.3, 0.5),
            ("1.0", "-0.2", "0.1"),
            "1",
            "0.02",
            "0",
            "0",
            "0",
        )
        math_07_permuted = _multi_net(
            (0.5, 0.2, 0.3),
            ("0.1", "1.0", "-0.2"),
            "1",
            "0.02",
            "0",
            "0",
            "0",
        )
        math_07 = (
            math_07_golden == Decimal("0.17")
            and math_07_golden
            == _multi_net(
                ("0.2", "0.3", "0.5"),
                ("1.0", "-0.2", "0.1"),
                "1",
                "0.02",
                "0",
                "0",
                "0",
            )
            and math_07_permuted == math_07_golden
            and _multi_net((1.0, 0.0), ("2", "-9"), "1", "0", "0", "0", "0")
            == Decimal("2")
            and _expect_value_error(
                lambda: _multi_net((0.4, 0.4), ("1", "2"), "1", "0", "0", "0", "0")
            )
            and _expect_value_error(
                lambda: _multi_net((float("inf"), 0.0), ("1", "2"), "1", "0", "0", "0", "0")
            )
            and _expect_value_error(
                lambda: _multi_net((0.5, 0.5), ("1",), "1", "0", "0", "0", "0")
            )
        )
        math_08 = (
            abs(_brier("0.70", 1) - 0.09) <= 1e-15
            and _brier(1.0, 1) == 0.0
            and _brier(0.0, 0) == 0.0
            and _brier((0.7, 0.3), (1, 0))
            == _brier(0.7, 1) + _brier(0.3, 0)
            and _expect_value_error(lambda: _brier((0.6, 0.3), (1, 0)))
        )
        math_09 = (
            abs(_log_loss(0.7, 1, 1e-15) - 0.35667494393873245)
            <= 1e-15
            and math.isfinite(_log_loss(0.0, 1))
            and math.isfinite(_log_loss(1.0, 0))
            and _log_loss(0.9, 1) < _log_loss(0.6, 1)
            and _log_loss(0.1, 0) < _log_loss(0.4, 0)
            and _expect_value_error(lambda: _log_loss(float("nan"), 1))
        )
        ece_golden = _ece_from_raw(
            (0.3, 0.3, 0.8, 0.8),
            (1, 0, 1, 0),
            (0.0, 0.5, 1.0),
        )
        ece_boundary = _ece_from_raw(
            (0.0, 1.0),
            (0, 1),
            (0.0, 0.5, 1.0),
        )
        values: dict[str, bool] = {
            "MATH-01": math_01,
            "MATH-02": math_02,
            "MATH-03": math_03,
            "MATH-04": math_04,
            "MATH-05": math_05,
            "MATH-06": math_06,
            "MATH-07": math_07,
            "MATH-08": math_08,
            "MATH-09": math_09,
            "MATH-10": (
                abs(ece_golden - 0.25) <= 1e-15
                and ece_boundary == 0.0
                and _expect_value_error(
                    lambda: _ece_from_raw(
                        (0.2, 0.8),
                        (1,),
                        (0.0, 0.5, 1.0),
                    )
                )
            ),
        }
    lower, upper = _wilson(8, 10, 0.95)
    low_boundary = _wilson(0, 10, 0.95)
    high_boundary = _wilson(10, 10, 0.95)
    values["MATH-11"] = (
        abs(lower - 0.49016247153664183) <= 1e-12
        and abs(upper - 0.9433178485456247) <= 1e-12
        and 0 <= low_boundary[0] <= low_boundary[1] <= 1
        and 0 <= high_boundary[0] <= high_boundary[1] <= 1
        and low_boundary[1] <= high_boundary[1]
        and _expect_value_error(lambda: _wilson(11, 10, 0.95))
    )
    p_values = (0.001, 0.01, 0.04, 0.2)
    bh_adjusted = _adjusted_p(p_values, 1.0)
    tied = _adjusted_p((0.01, 0.01, 0.2), 1.0)
    values["MATH-12"] = (
        _bh(p_values, 0.05, 1.0) == (0, 1)
        and tuple(sorted(bh_adjusted)) == bh_adjusted
        and tied[0] == tied[1]
        and _bh((0.01, 0.01, 0.2), 0.05, 1.0) == (0, 1)
        and _expect_value_error(lambda: _bh((0.1,), -0.1, 1.0))
    )
    harmonic = sum(1 / index for index in range(1, len(p_values) + 1))
    by_rejections = _bh(p_values, 0.05, harmonic)
    by_adjusted = _adjusted_p(p_values, harmonic)
    values["MATH-13"] = (
        by_rejections == (0, 1)
        and set(by_rejections) <= set(_bh(p_values, 0.05, 1.0))
        and all(
            by_value >= bh_value
            for by_value, bh_value in zip(
                by_adjusted,
                bh_adjusted,
                strict=True,
            )
        )
        and _expect_value_error(lambda: _bh((), 0.05, harmonic))
    )
    first = _stationary_means(1401)
    second = _stationary_means(1401)
    ordered = sorted(first)
    values["MATH-14"] = (
        first == second
        and ordered[1] <= 3.0 <= ordered[-2]
        and ordered[1] <= ordered[-2]
        and _stationary_means(1402) != first
        and _expect_value_error(lambda: _stationary_means(1401, (1.0,)))
    )
    oriented_rows = ((1.0,),) * 4
    values["MATH-15"] = (
        _white_reality_p_value(
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
        and _expect_value_error(
            lambda: _white_reality_p_value(
                ((0.0, 0.0),) * 4,
                benchmark_minus_candidate=True,
                seed=1501,
                replicates=64,
            )
        )
    )
    return values


def main() -> int:
    failures: list[str] = []
    expected_names = frozenset(PRODUCTION_NAMES)
    actual_names = frozenset(path.name for path in PACKAGE.glob("*.py"))
    if len(expected_names) != len(PRODUCTION_NAMES):
        failures.append(
            "independent production module roster contains duplicate names"
        )
    missing_names = tuple(sorted(expected_names - actual_names))
    unexpected_names = tuple(sorted(actual_names - expected_names))
    if missing_names or unexpected_names:
        failures.append(
            "production core differs from the exact independently declared "
            f"centralized module roster: missing={missing_names!r} "
            f"unexpected={unexpected_names!r}"
        )
    data_names = frozenset(path.name for path in (PACKAGE / "data").glob("*") if path.is_file())
    if len(data_names) != 13 or "st12f_parameter_resources_manifest.json" not in data_names or "__init__.py" in data_names:
        failures.append("certified ST12-F data directory differs from 13 exact non-package resources")
    for name in PRODUCTION_NAMES:
        path = PACKAGE / name
        if not path.is_file():
            failures.append(f"missing production file: {name}")
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            failures.append(f"{name}: {exc}")
    for file_name, class_name, expected_count in (
        ("input_lock.py", "ImmutableReplayPaperInputLockV1", 33),
        ("evidence.py", "ReplayResultContractV1", 26),
        ("evidence.py", "PaperResultContractV1", 26),
        ("evidence.py", "DivergenceAssessmentV1", 18),
        ("evidence.py", "ComputationEvidenceBundleV1", 30),
    ):
        tree = ast.parse((PACKAGE / file_name).read_text(encoding="utf-8"))
        classes = tuple(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
        field_names = tuple(
            node.target.id
            for node in (classes[0].body if len(classes) == 1 else ())
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
        )
        field_count = len(field_names)
        if field_count != expected_count:
            failures.append(f"{class_name}: canonical field count={field_count}, expected={expected_count}")
        if (
            class_name == "ComputationEvidenceBundleV1"
            and field_names != EVIDENCE_BUNDLE_FIELDS
        ):
            failures.append(
                "ComputationEvidenceBundleV1 exact 30-field roster differs"
            )
    specification_tree = ast.parse(
        (PACKAGE / "specification.py").read_text(encoding="utf-8")
    )
    formula_class = next(
        (
            node
            for node in specification_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "FormulaExecutionContractV1"
        ),
        None,
    )
    formula_fields = tuple(
        statement.target.id
        for statement in (formula_class.body if formula_class else ())
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
    )
    if formula_fields != FORMULA_EXECUTION_FIELDS:
        failures.append("FormulaExecutionContractV1 mandatory fields differ")
    alias_is_same_class = any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "CompiledComputationEnvelopeV1"
            for target in node.targets
        )
        and isinstance(node.value, ast.Name)
        and node.value.id == "FormulaExecutionContractV1"
        for node in specification_tree.body
    )
    if not alias_is_same_class:
        failures.append("historical contract name is not a same-class alias")
    math_io_assignment = next(
        (
            node.value
            for node in specification_tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "_MATH_IO_ROWS"
                for target in node.targets
            )
        ),
        None,
    )
    math_io_ids = (
        tuple(
            ast.literal_eval(item.args[0])
            for item in math_io_assignment.elts
            if isinstance(item, ast.Call) and item.args
        )
        if isinstance(math_io_assignment, ast.Tuple)
        else ()
    )
    if math_io_ids != EXPECTED_ALL_MATH_IDS:
        failures.append("typed math I/O contract identities differ")
    if (
        not isinstance(math_io_assignment, ast.Tuple)
        or not math_io_assignment.elts
        or not isinstance(math_io_assignment.elts[0], ast.Call)
        or tuple(
            field[0]
            for field in ast.literal_eval(math_io_assignment.elts[0].args[2])
        )
        != ("contract_price", "payout_per_winning_contract")
    ):
        failures.append("MATH-01 payout input is absent from the typed contract")
    specification_text = (PACKAGE / "specification.py").read_text(encoding="utf-8")
    if (
        "identity_binding: CanonicalIdentityBindingV1" not in specification_text
        or "qku_id:" in specification_text[
            specification_text.find("class ComputationContractCompilerV1") :
        ]
    ):
        failures.append("compiler accepts a free-form QKU identity")
    validation_text = (PACKAGE / "validation.py").read_text(encoding="utf-8")
    if (
        any(path not in validation_text for path in SHARED_VALIDATION_TEST_PATHS)
        or "ST12A-TEST::INDEPENDENT::" in validation_text
    ):
        failures.append(
            "derived test coverage does not reference the exact shared test paths"
        )
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
    _v34_frozen_literal_checks(failures)
    reconstructed = independently_reconstruct()
    if tuple(reconstructed) != EXPECTED_MATH_IDS:
        failures.append("independent MATH-01..15 denominator mismatch")
    failures.extend(
        f"{math_id}: independent golden reconstruction failed"
        for math_id, passed in reconstructed.items()
        if not passed
    )
    evidence_rows: tuple[_ArchitectureMathEvidenceV1, ...] = tuple()
    grouped_mutation_count = 0
    production_import_count, production_callable_count = (
        _independent_source_boundary_counts()
    )
    try:
        evidence_rows = _build_architecture_evidence(
            reconstructed,
            production_import_count=production_import_count,
            production_callable_count=production_callable_count,
        )
        failures.extend(_evidence_contract_failures(evidence_rows))
        grouped_mutation_count = _exercise_evidence_contract_mutations(evidence_rows)
    except (OSError, SyntaxError, ValueError, KeyError, TypeError) as exc:
        failures.append(f"architecture row evidence reconstruction failed: {exc}")
    if production_import_count or production_callable_count:
        failures.append(
            "architecture validator crossed the production import/call boundary"
        )
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    evidence_payload = {
        "architecture_math_count": len(evidence_rows),
        "rows": [_json_ready(asdict(row)) for row in evidence_rows],
        "schema_version": EVIDENCE_MARKER,
    }
    print(
        f"{EVIDENCE_MARKER} "
        + json.dumps(
            evidence_payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    print(
        f"{SUCCESS_MARKER} independent_oracles={len(evidence_rows)} "
        f"passing_invariant_groups={sum(row.golden_comparison_passed for row in evidence_rows)} "
        f"formula_mutations={sum(row.formula_or_procedure_mutation_observed for row in evidence_rows)} "
        f"domain_mutations={sum(row.domain_guard_rejection_observed for row in evidence_rows)} "
        f"precision_mutations={sum(row.precision_or_tolerance_mutation_observed for row in evidence_rows)} "
        f"semantic_binding_mutations={sum(row.semantic_binding_mutation_observed for row in evidence_rows)} "
        f"grouped_contract_mutations={grouped_mutation_count} "
        f"production_imports={production_import_count} "
        f"production_calls={production_callable_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
