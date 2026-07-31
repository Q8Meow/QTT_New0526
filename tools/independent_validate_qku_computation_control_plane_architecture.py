#!/usr/bin/env python3
"""Independent architecture and MATH-01..15 reconstruction.

This validator intentionally does not import the production package or primary
validator.
"""

from __future__ import annotations

import ast
from collections import Counter
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
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
)
EXPECTED_MATH_IDS = tuple(f"MATH-{value:02d}" for value in range(1, 16))
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
SUCCESS_MARKER = "QKU_ARCHITECTURE_INDEPENDENTLY_VALIDATED"
DECIMAL_CONTEXT = Context(prec=34, rounding=ROUND_HALF_EVEN)


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
    actual_names = tuple(
        path.name for path in sorted(PACKAGE.glob("*.py"), key=lambda item: item.name)
    )
    if set(actual_names) != set(PRODUCTION_NAMES) or len(actual_names) != 27:
        failures.append("production core is not the exact 27-file centralized set")
    for name in PRODUCTION_NAMES:
        path = PACKAGE / name
        if not path.is_file():
            failures.append(f"missing production file: {name}")
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            failures.append(f"{name}: {exc}")
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
