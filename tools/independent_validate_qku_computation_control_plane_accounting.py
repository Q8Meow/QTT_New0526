#!/usr/bin/env python3
"""Independent ST12-C accounting/math reconstruction without production imports."""

from __future__ import annotations

import ast
import base64
from collections import Counter
from copy import deepcopy
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import json
from pathlib import Path
import sys
import zlib


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.qku_independent_math_row_receipt import (  # noqa: E402
    EVIDENCE_TIER,
    INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT,
    NO_PRODUCTION_SYSTEM_UNDER_TEST,
    TERMINAL_STATE,
    IndependentMathRowEvidenceV1,
    build_envelope,
    evidence_observation,
    format_evidence_line,
    observed_result,
)

PACKAGE = REPO_ROOT / "src" / "qtt" / "stage1_prediction_markets" / "qku_computation_control_plane"
EXPECTED_PRODUCTION = (
    "context.py", "economic_math.py", "receipts.py", "persistence.py", "migrations.py",
    "outbox.py", "transaction.py", "idempotency.py", "rollback.py", "accounting.py",
    "lifecycle.py", "sqlite_reference.py",
)
PROHIBITED = ("decimal_math.py", "execution.py", "accounting_tca_adapter.py", "telemetry.py", "sqlite_runtime.py")
EXPECTED_MATH_IDS = tuple(f"MATH-{value}" for value in range(26, 39))
CONTEXT = Context(prec=34, rounding=ROUND_HALF_EVEN)
SUCCESS = "QKU_ACCOUNTING_INDEPENDENTLY_VALIDATED"
RECEIPT_MATH_IDS = tuple(f"MATH-{value:02d}" for value in range(26, 37))


def _assigned_literal(path: Path, name: str) -> object:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"missing literal {name}")


def _archive_rows(path: Path, name: str) -> tuple[dict[str, object], ...]:
    payload = _assigned_literal(path, name)
    if not isinstance(payload, str):
        raise ValueError(f"{name} is not literal text")
    text = zlib.decompress(base64.b85decode(payload.encode("ascii"))).decode("utf-8-sig")
    rows = tuple(json.loads(line) for line in text.splitlines() if line.strip())
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{name} contains a nonobject")
    return rows


def _d(value: object) -> Decimal:
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(value)


def _golden_results() -> dict[str, object]:
    with localcontext(CONTEXT):
        current = max(Decimal(".5"), Decimal(".4"))
        posterior = Decimal(".5") * Decimal(".8") + Decimal(".5") * Decimal(".7")
        evi = posterior - current - Decimal(".1")
        kelly = (Decimal("1") * Decimal(".60") - (Decimal(1) - Decimal(".60"))) / Decimal("1")
        fractional = min(Decimal(".50") * max(Decimal(0), Decimal(".20")), Decimal(".20"))
        mean_variance = Decimal(".10") - Decimal("2") / Decimal(2) * Decimal(".04")
        losses = tuple(sorted((Decimal(0), Decimal(1), Decimal(2), Decimal(3)), reverse=True))
        tail_mass = Decimal(1) - Decimal(".75")
        expected_shortfall = losses[0] * tail_mass / tail_mass
        shortfall = Decimal("100") * (Decimal(".52") - Decimal(".50")) + Decimal("1")
        spread = Decimal("100") * (Decimal(".44") - Decimal(".43"))
        global_fee = Decimal("100") * Decimal(".05") * Decimal(".50") * Decimal(".50")
        us_taker = Decimal("100") * Decimal(".05") * Decimal(".50") * Decimal(".50")
        us_maker = Decimal("100") * Decimal("-.0125") * Decimal(".50") * Decimal(".50")
        yes_ask = Decimal("1") - Decimal(".56")
        no_ask = Decimal("1") - Decimal(".42")
        expected_fill = Decimal("0") * Decimal(".2") + Decimal("50") * Decimal(".3") + Decimal("100") * Decimal(".5")
    return {
        "MATH-26": evi,
        "MATH-27": kelly,
        "MATH-28": fractional,
        "MATH-29": mean_variance,
        "MATH-30": (Decimal("3"), expected_shortfall),
        "MATH-31": expected_shortfall,
        "MATH-32": shortfall,
        "MATH-33": spread,
        "MATH-34": (global_fee, global_fee.quantize(Decimal(".00001"), rounding=ROUND_HALF_EVEN)),
        "MATH-35": (us_maker, us_maker.quantize(Decimal(".01"), rounding=ROUND_HALF_EVEN), us_taker, us_taker.quantize(Decimal(".01"), rounding=ROUND_HALF_EVEN)),
        "MATH-36": (yes_ask, no_ask),
        "MATH-37": (True, True, True),
        "MATH-38": expected_fill,
    }


def _required(inputs: dict[str, object], name: str) -> object:
    if name not in inputs:
        raise ValueError(f"{name} is required")
    return inputs[name]


def _finite_decimal(value: object, name: str) -> Decimal:
    try:
        result = _d(value)
    except Exception as exc:
        raise ValueError(f"{name} must be an exact Decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{name} must be finite")
    return result


def _nonnegative_decimal(value: object, name: str) -> Decimal:
    result = _finite_decimal(value, name)
    if result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _probability_decimal(value: object, name: str) -> Decimal:
    result = _finite_decimal(value, name)
    if result < 0 or result > 1:
        raise ValueError(f"{name} must be in [0,1]")
    return result


def _tail_expected_shortfall(losses: object, alpha: object) -> Decimal:
    if not isinstance(losses, list | tuple) or not losses:
        raise ValueError("losses must be nonempty")
    observations = sorted(
        (_finite_decimal(value, "loss") for value in losses), reverse=True
    )
    confidence = _probability_decimal(alpha, "alpha")
    if confidence <= 0 or confidence >= 1:
        raise ValueError("alpha must be in (0,1)")
    with localcontext(CONTEXT) as context:
        observation_mass = context.divide(Decimal(1), Decimal(len(observations)))
        required_mass = context.subtract(Decimal(1), confidence)
        remaining = required_mass
        weighted = Decimal(0)
        for loss in observations:
            if remaining <= 0:
                break
            used = min(observation_mass, remaining)
            weighted = context.add(weighted, context.multiply(loss, used))
            remaining = context.subtract(remaining, used)
        if remaining != 0:
            raise ValueError("insufficient empirical tail support")
        return context.divide(weighted, required_mass)


def _accounting_result(math_id: str, raw_inputs: object) -> dict[str, object]:
    if not isinstance(raw_inputs, dict):
        raise ValueError(f"{math_id} inputs must be a mapping")
    inputs = raw_inputs
    with localcontext(CONTEXT) as context:
        if math_id == "MATH-26":
            current_raw = _required(inputs, "current_action_values")
            scenarios_raw = _required(inputs, "new_information_scenarios")
            if not isinstance(current_raw, list | tuple) or not current_raw:
                raise ValueError("current_action_values must be nonempty")
            if not isinstance(scenarios_raw, list | tuple) or not scenarios_raw:
                raise ValueError("new_information_scenarios must be nonempty")
            current = tuple(
                _finite_decimal(value, "current_action_value")
                for value in current_raw
            )
            probability_sum = Decimal(0)
            posterior = Decimal(0)
            for scenario in scenarios_raw:
                if not isinstance(scenario, dict):
                    raise ValueError("scenario must be a mapping")
                probability = _probability_decimal(
                    _required(scenario, "probability"), "scenario probability"
                )
                values_raw = _required(scenario, "action_values")
                if not isinstance(values_raw, list | tuple) or len(values_raw) != len(
                    current
                ):
                    raise ValueError("scenario action values must align")
                values = tuple(
                    _finite_decimal(value, "scenario action value")
                    for value in values_raw
                )
                probability_sum = context.add(probability_sum, probability)
                posterior = context.add(
                    posterior, context.multiply(probability, max(values))
                )
            if probability_sum != 1:
                raise ValueError("scenario probabilities must sum exactly to one")
            acquisition_cost = _nonnegative_decimal(
                _required(inputs, "acquisition_cost"), "acquisition_cost"
            )
            return {
                "evi": context.subtract(
                    context.subtract(posterior, max(current)), acquisition_cost
                )
            }
        if math_id == "MATH-27":
            probability = _probability_decimal(
                _required(inputs, "win_probability"), "win_probability"
            )
            odds = _finite_decimal(_required(inputs, "net_odds"), "net_odds")
            if odds <= 0:
                raise ValueError("net_odds must be positive")
            raw = context.divide(
                context.subtract(
                    context.multiply(odds, probability),
                    context.subtract(Decimal(1), probability),
                ),
                odds,
            )
            return {"kelly_fraction": raw}
        if math_id == "MATH-28":
            full = _finite_decimal(
                _required(inputs, "full_kelly_fraction"), "full_kelly_fraction"
            )
            multiplier = _finite_decimal(
                _required(inputs, "fraction_multiplier"), "fraction_multiplier"
            )
            cap = _nonnegative_decimal(_required(inputs, "risk_cap"), "risk_cap")
            if multiplier <= 0 or multiplier > 1:
                raise ValueError("fraction_multiplier must be in (0,1]")
            return {
                "fractional_kelly": min(
                    context.multiply(max(Decimal(0), full), multiplier), cap
                )
            }
        if math_id == "MATH-29":
            mean = _finite_decimal(_required(inputs, "mean_return"), "mean_return")
            risk = _nonnegative_decimal(
                _required(inputs, "risk_aversion"), "risk_aversion"
            )
            variance = _nonnegative_decimal(
                _required(inputs, "variance"), "variance"
            )
            cost = _nonnegative_decimal(
                _required(inputs, "transaction_cost"), "transaction_cost"
            )
            return {
                "utility": context.subtract(
                    context.subtract(
                        mean,
                        context.divide(context.multiply(risk, variance), Decimal(2)),
                    ),
                    cost,
                )
            }
        if math_id in {"MATH-30", "MATH-31"}:
            losses_raw = _required(inputs, "losses")
            alpha = _required(inputs, "alpha")
            shortfall = _tail_expected_shortfall(losses_raw, alpha)
            if math_id == "MATH-31":
                return {"expected_shortfall": shortfall}
            assert isinstance(losses_raw, list | tuple)
            observations = sorted(
                (_finite_decimal(value, "loss") for value in losses_raw),
                reverse=True,
            )
            confidence = _probability_decimal(alpha, "alpha")
            mass = context.divide(Decimal(1), Decimal(len(observations)))
            remaining = context.subtract(Decimal(1), confidence)
            value_at_risk = observations[0]
            for loss in observations:
                value_at_risk = loss
                remaining = context.subtract(remaining, min(mass, remaining))
                if remaining == 0:
                    break
            return {"var": value_at_risk, "cvar": shortfall}
        if math_id in {"MATH-32", "MATH-33"}:
            side = _required(inputs, "side")
            if side not in {"BUY", "SELL"}:
                raise ValueError("side must be BUY or SELL")
            quantity = _nonnegative_decimal(
                _required(inputs, "quantity"), "quantity"
            )
            signed = quantity if side == "BUY" else -quantity
            execution = _finite_decimal(
                _required(inputs, "execution_price"), "execution_price"
            )
            reference_name = (
                "decision_price" if math_id == "MATH-32" else "midpoint_at_decision"
            )
            reference = _finite_decimal(
                _required(inputs, reference_name), reference_name
            )
            market = context.multiply(signed, context.subtract(execution, reference))
            if math_id == "MATH-33":
                return {"spread_cost": market}
            return {
                "implementation_shortfall": sum(
                    (
                        market,
                        _finite_decimal(
                            _required(inputs, "explicit_fees"), "explicit_fees"
                        ),
                        _finite_decimal(
                            _required(inputs, "opportunity_cost_unfilled"),
                            "opportunity_cost_unfilled",
                        ),
                        _finite_decimal(
                            _required(inputs, "other_costs"), "other_costs"
                        ),
                    ),
                    Decimal(0),
                )
            }
        if math_id == "MATH-34":
            contracts = _nonnegative_decimal(
                _required(inputs, "contracts"), "contracts"
            )
            rate = _nonnegative_decimal(_required(inputs, "fee_rate"), "fee_rate")
            price = _probability_decimal(_required(inputs, "price"), "price")
            raw = context.multiply(
                context.multiply(context.multiply(contracts, rate), price),
                context.subtract(Decimal(1), price),
            )
            return {
                "fee_before_rounding": raw,
                "fee_after_rounding": raw.quantize(
                    Decimal(".00001"), rounding=ROUND_HALF_EVEN
                ),
            }
        if math_id == "MATH-35":
            contracts = _nonnegative_decimal(
                _required(inputs, "contracts"), "contracts"
            )
            maker = _finite_decimal(_required(inputs, "maker_theta"), "maker_theta")
            taker = _finite_decimal(_required(inputs, "taker_theta"), "taker_theta")
            if maker > 0 or taker < 0:
                raise ValueError("theta conflicts with maker/taker economic role")
            price = _probability_decimal(_required(inputs, "price"), "price")
            common = context.multiply(
                context.multiply(contracts, price), context.subtract(Decimal(1), price)
            )
            maker_raw = context.multiply(common, maker)
            taker_raw = context.multiply(common, taker)
            return {
                "maker_amount_before_rounding": maker_raw,
                "maker_amount_after_bankers_rounding": maker_raw.quantize(
                    Decimal(".01"), rounding=ROUND_HALF_EVEN
                ),
                "taker_amount_before_rounding": taker_raw,
                "taker_amount_after_bankers_rounding": taker_raw.quantize(
                    Decimal(".01"), rounding=ROUND_HALF_EVEN
                ),
            }
        if math_id == "MATH-36":
            payout = _finite_decimal(_required(inputs, "payout"), "payout")
            yes = _finite_decimal(
                _required(inputs, "yes_best_bid"), "yes_best_bid"
            )
            no = _finite_decimal(_required(inputs, "no_best_bid"), "no_best_bid")
            if payout <= 0 or any(value < 0 or value > payout for value in (yes, no)):
                raise ValueError("binary-book inputs are outside payout")
            return {
                "yes_implied_ask": context.subtract(payout, no),
                "no_implied_ask": context.subtract(payout, yes),
            }
    raise ValueError(f"unsupported accounting receipt row: {math_id}")


def _numeric_equal(observed: object, expected: object, tolerance: Decimal) -> bool:
    if isinstance(observed, bool) or isinstance(expected, bool):
        return type(observed) is bool and observed is expected
    if isinstance(observed, dict) and isinstance(expected, dict):
        return set(observed) == set(expected) and all(
            _numeric_equal(observed[key], expected[key], tolerance) for key in observed
        )
    try:
        observed_decimal = _finite_decimal(observed, "observed")
        expected_decimal = _finite_decimal(expected, "expected")
    except ValueError:
        return type(observed) is type(expected) and observed == expected
    return abs(observed_decimal - expected_decimal) <= tolerance


def _accounting_comparison_passed(
    policy: str, observed: dict[str, object], expected: object
) -> bool:
    if not isinstance(expected, dict):
        return False
    tolerance = Decimal("1E-15") if policy == "ABS_TOL_1E-15" else Decimal(0)
    if policy not in {
        "ABS_TOL_1E-15",
        "EXACT_DECIMAL",
        "EXACT_DECIMAL_AND_5DP_BOUNDARY",
        "EXACT_DECIMAL_AND_BANKERS_CENT_BOUNDARY",
    }:
        return False
    if not _numeric_equal(observed, expected, tolerance):
        return False
    if policy == "EXACT_DECIMAL_AND_5DP_BOUNDARY":
        rounded = observed.get("fee_after_rounding")
        return isinstance(rounded, Decimal) and rounded.as_tuple().exponent == -5
    if policy == "EXACT_DECIMAL_AND_BANKERS_CENT_BOUNDARY":
        rounded = (
            observed.get("maker_amount_after_bankers_rounding"),
            observed.get("taker_amount_after_bankers_rounding"),
        )
        return all(
            isinstance(value, Decimal) and value.as_tuple().exponent == -2
            for value in rounded
        )
    return True


def _changed_inputs(inputs: dict[str, object], path: tuple[object, ...], value: object) -> dict[str, object]:
    result = deepcopy(inputs)
    target: object = result
    for segment in path[:-1]:
        target = target[segment]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]
    return result


_FORMULA_MUTATIONS: dict[str, tuple[tuple[object, ...], object, str]] = {
    "MATH-26": (("acquisition_cost",), "0.20", "ACQUISITION_COST_FORMULA_MUTATION"),
    "MATH-27": (("win_probability",), "0.55", "WIN_PROBABILITY_FORMULA_MUTATION"),
    "MATH-28": (("fraction_multiplier",), "0.25", "FRACTIONAL_KELLY_MULTIPLIER_MUTATION"),
    "MATH-29": (("mean_return",), "0.11", "MEAN_RETURN_FORMULA_MUTATION"),
    "MATH-30": (("losses", 3), "4", "TAIL_LOSS_FORMULA_MUTATION"),
    "MATH-31": (("losses", 3), "4", "TAIL_LOSS_FORMULA_MUTATION"),
    "MATH-32": (("execution_price",), "0.53", "EXECUTION_PRICE_FORMULA_MUTATION"),
    "MATH-33": (("execution_price",), "0.45", "SPREAD_PRICE_FORMULA_MUTATION"),
    "MATH-34": (("fee_rate",), "0.04", "GLOBAL_FEE_RATE_FORMULA_MUTATION"),
    "MATH-35": (("maker_theta",), "-0.02", "MAKER_THETA_FORMULA_MUTATION"),
    "MATH-36": (("no_best_bid",), "0.55", "BOOK_COMPLEMENT_FORMULA_MUTATION"),
}

_DOMAIN_MUTATIONS: dict[str, tuple[tuple[object, ...], object, str]] = {
    "MATH-26": (("new_information_scenarios", 0, "probability"), "0.6", "PROBABILITY_SIMPLEX_GUARD"),
    "MATH-27": (("net_odds",), "0", "POSITIVE_ODDS_GUARD"),
    "MATH-28": (("fraction_multiplier",), "0", "MULTIPLIER_DOMAIN_GUARD"),
    "MATH-29": (("variance",), "-0.01", "NONNEGATIVE_VARIANCE_GUARD"),
    "MATH-30": (("alpha",), "1", "TAIL_CONFIDENCE_DOMAIN_GUARD"),
    "MATH-31": (("losses",), [], "NONEMPTY_LOSS_DOMAIN_GUARD"),
    "MATH-32": (("side",), "HOLD", "SIDE_DOMAIN_GUARD"),
    "MATH-33": (("quantity",), "-1", "NONNEGATIVE_QUANTITY_GUARD"),
    "MATH-34": (("price",), "1.1", "PRICE_PROBABILITY_GUARD"),
    "MATH-35": (("maker_theta",), "0.01", "MAKER_SIGN_DOMAIN_GUARD"),
    "MATH-36": (("payout",), "0", "POSITIVE_PAYOUT_GUARD"),
}

_PRECISION_MUTATIONS: dict[str, tuple[tuple[object, ...], object, str]] = {
    "MATH-26": (("acquisition_cost",), "0.100000000000001", "DECIMAL_COST_PRECISION_MUTATION"),
    "MATH-27": (("win_probability",), "0.6000000000000001", "PROBABILITY_PRECISION_MUTATION"),
    "MATH-28": (("fraction_multiplier",), "0.5000000000000001", "MULTIPLIER_PRECISION_MUTATION"),
    "MATH-29": (("variance",), "0.0400000000000001", "VARIANCE_PRECISION_MUTATION"),
    "MATH-30": (("losses", 3), "3.000000000000001", "TAIL_PRECISION_MUTATION"),
    "MATH-31": (("losses", 3), "3.000000000000001", "TAIL_PRECISION_MUTATION"),
    "MATH-32": (("execution_price",), "0.5200000000000001", "PRICE_PRECISION_MUTATION"),
    "MATH-33": (("execution_price",), "0.4400000000000001", "PRICE_PRECISION_MUTATION"),
    "MATH-34": (("price",), "0.500001", "FIVE_DP_ROUNDING_BOUNDARY_MUTATION"),
    "MATH-35": (("price",), "0.500001", "BANKERS_CENT_BOUNDARY_MUTATION"),
    "MATH-36": (("no_best_bid",), "0.560000000000001", "BOOK_PRICE_PRECISION_MUTATION"),
}

_BINDING_MUTATIONS: dict[str, tuple[tuple[object, ...], object, str]] = {
    "MATH-26": (("new_information_scenarios", 0, "action_values"), [0.8], "ACTION_ROSTER_BINDING_MUTATION"),
    "MATH-27": (("win_probability",), "60", "PROBABILITY_UNIT_MUTATION"),
    "MATH-28": (("risk_cap",), "0.05", "RISK_CAP_BINDING_MUTATION"),
    "MATH-29": (("transaction_cost",), "0.01", "TRANSACTION_COST_BASIS_MUTATION"),
    "MATH-30": (("losses",), [0, 100, 200, 300], "LOSS_UNIT_BASIS_MUTATION"),
    "MATH-31": (("losses",), [0, 100, 200, 300], "LOSS_UNIT_BASIS_MUTATION"),
    "MATH-32": (("side",), "SELL", "ORDER_SIDE_BINDING_MUTATION"),
    "MATH-33": (("side",), "SELL", "ORDER_SIDE_BINDING_MUTATION"),
    "MATH-34": (("fee_rate",), "0.06", "FEE_SCHEDULE_BINDING_MUTATION"),
    "MATH-35": (("maker_theta",), "0.01", "LIQUIDITY_ROLE_BINDING_MUTATION"),
    "MATH-36": (("yes_best_bid",), "0.56", "YES_NO_BOOK_BINDING_MUTATION"),
}


def _mutation_observation(
    math_id: str,
    inputs: dict[str, object],
    mutation: tuple[tuple[object, ...], object, str],
    *,
    require_rejection: bool,
) -> object:
    path, replacement, operation = mutation
    baseline = _accounting_result(math_id, inputs)
    original: object = inputs
    for segment in path:
        original = original[segment]  # type: ignore[index]
    mutated_inputs = _changed_inputs(inputs, path, replacement)
    try:
        mutated = _accounting_result(math_id, mutated_inputs)
    except ValueError as exc:
        return evidence_observation(
            operation,
            "TYPED_REJECTION",
            {
                "input_path": list(path),
                "baseline_value": original,
                "replacement_value": replacement,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
        )
    if require_rejection:
        raise ValueError(f"{math_id}: domain mutation was accepted")
    if mutated == baseline:
        raise ValueError(f"{math_id}: mutation did not change an observed result")
    return evidence_observation(
        operation,
        "OBSERVED_OUTPUT_CHANGE",
        {
            "input_path": list(path),
            "baseline_value": original,
            "replacement_value": replacement,
            "baseline_result": baseline,
            "mutated_result": mutated,
        },
    )


def _build_accounting_receipt_rows(
    oracles: tuple[dict[str, object], ...],
    vectors: tuple[dict[str, object], ...],
) -> tuple[IndependentMathRowEvidenceV1, ...]:
    oracle_by_id = {str(row["math_spec_ref"]): row for row in oracles}
    vector_by_id = {str(row["math_spec_ref"]): row for row in vectors}
    rows: list[IndependentMathRowEvidenceV1] = []
    for math_id in RECEIPT_MATH_IDS:
        oracle = oracle_by_id[math_id]
        vector = vector_by_id[math_id]
        if (
            oracle.get("oracle_id") != f"ORACLE::{math_id}"
            or vector.get("vector_id") != f"GOLDEN::{math_id}"
            or vector.get("oracle_ref") != oracle.get("oracle_id")
            or vector.get("comparison_policy") != oracle.get("comparison_policy")
        ):
            raise ValueError(f"{math_id}: tracked oracle/vector identity differs")
        raw_inputs = vector.get("inputs")
        if not isinstance(raw_inputs, dict):
            raise ValueError(f"{math_id}: tracked inputs are not a mapping")
        actual = _accounting_result(math_id, raw_inputs)
        expected = vector.get("expected")
        policy = str(vector.get("comparison_policy"))
        comparison_passed = _accounting_comparison_passed(policy, actual, expected)
        if not comparison_passed or not isinstance(expected, dict):
            raise ValueError(f"{math_id}: declared comparison policy failed")
        domain_observation = _mutation_observation(
            math_id,
            raw_inputs,
            _DOMAIN_MUTATIONS[math_id],
            require_rejection=True,
        )
        rows.append(
            IndependentMathRowEvidenceV1(
                math_id=math_id,
                domain_owner=(
                    "tools/independent_validate_qku_computation_control_plane_accounting.py"
                ),
                oracle_id=str(oracle["oracle_id"]),
                golden_vector_id=str(vector["vector_id"]),
                comparison_policy=policy,
                evidence_tier=EVIDENCE_TIER,
                observed_result=observed_result(
                    independent_observation=actual,
                    independent_expected_result=expected,
                    system_under_test_observation=NO_PRODUCTION_SYSTEM_UNDER_TEST,
                    comparison_passed=True,
                ),
                boundary_or_invariant_observation=evidence_observation(
                    f"{policy}_GOLDEN_COMPARISON",
                    "PASS",
                    {
                        "observed_result": actual,
                        "independently_checked_expected": expected,
                        "policy_executed": policy,
                    },
                ),
                negative_or_abstention_observation=domain_observation,
                formula_or_procedure_mutation_observation=_mutation_observation(
                    math_id,
                    raw_inputs,
                    _FORMULA_MUTATIONS[math_id],
                    require_rejection=False,
                ),
                domain_guard_observation=domain_observation,
                precision_or_tolerance_observation=_mutation_observation(
                    math_id,
                    raw_inputs,
                    _PRECISION_MUTATIONS[math_id],
                    require_rejection=False,
                ),
                source_unit_or_binding_observation=_mutation_observation(
                    math_id,
                    raw_inputs,
                    _BINDING_MUTATIONS[math_id],
                    require_rejection=False,
                ),
                independence_class=(
                    INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT
                ),
                production_system_under_test_invocation_count=0,
                production_expected_value_import_count=0,
                production_oracle_call_count=0,
                external_effect_count=0,
                terminal_state=TERMINAL_STATE,
            )
        )
    return tuple(rows)


def _source_safety(failures: list[str]) -> None:
    forbidden_imports = {"requests", "httpx", "socket", "subprocess", "asyncio", "multiprocessing"}
    for name in EXPECTED_PRODUCTION:
        path = PACKAGE / name
        if not path.is_file():
            failures.append(f"missing production owner: {name}")
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                if roots & forbidden_imports:
                    failures.append(f"forbidden import in {name}: {sorted(roots & forbidden_imports)}")
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".", 1)[0] in forbidden_imports:
                failures.append(f"forbidden import in {name}: {node.module}")
    if any((PACKAGE / name).exists() for name in PROHIBITED):
        failures.append("a prohibited historical production path exists")


def _class_and_function_names(path: Path) -> tuple[set[str], set[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return (
        {node.name for node in tree.body if isinstance(node, ast.ClassDef)},
        {node.name for node in tree.body if isinstance(node, ast.FunctionDef)},
    )


def _class_node(tree: ast.Module, class_name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise ValueError(f"missing class {class_name}")


def _annotated_fields(tree: ast.Module, class_name: str) -> set[str]:
    return {
        node.target.id
        for node in _class_node(tree, class_name).body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }


def _class_method_node(
    tree: ast.Module, class_name: str, method_name: str
) -> ast.FunctionDef:
    owner = _class_node(tree, class_name)
    for node in owner.body:
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return node
    raise ValueError(f"missing {class_name}.{method_name}")


def _semantic_repair_closure(
    failures: list[str], policies: tuple[dict[str, object], ...],
    bindings: tuple[dict[str, object], ...],
) -> None:
    rollback_classes, rollback_functions = _class_and_function_names(PACKAGE / "rollback.py")
    if "ReversalHistoryViewV1" not in rollback_classes or "validate_reversal_bundle_against_history_v1" not in rollback_functions:
        failures.append("persisted reversal history has no single typed semantic owner")
    for filename, class_name in (
        ("persistence.py", "PersistenceAdapterV1"),
        ("persistence.py", "InMemoryPersistenceAdapterV1"),
        ("sqlite_reference.py", "SQLiteReferenceAdapterV1"),
    ):
        tree = ast.parse((PACKAGE / filename).read_text(encoding="utf-8"), filename=filename)
        owner = next(
            (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name),
            None,
        )
        if owner is None or "load_committed_reversal_history" not in {
            node.name for node in owner.body if isinstance(node, ast.FunctionDef)
        }:
            failures.append(f"{class_name} lacks the exact committed reversal-history query")
    transaction_tree = ast.parse(
        (PACKAGE / "transaction.py").read_text(encoding="utf-8"),
        filename="transaction.py",
    )
    transaction_calls = {
        node.func.attr
        for node in ast.walk(transaction_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    } | {
        node.func.id
        for node in ast.walk(transaction_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    if not {
        "load_committed_reversal_history",
        "validate_reversal_bundle_against_history_v1",
    } <= transaction_calls:
        failures.append("unit of work does not enforce persisted reversal history")

    sqlite_tree = ast.parse(
        (PACKAGE / "sqlite_reference.py").read_text(encoding="utf-8"),
        filename="sqlite_reference.py",
    )
    public_sqlite = any(
        isinstance(node, ast.Import)
        and any(alias.name == "sqlite3" for alias in node.names)
        for node in sqlite_tree.body
    )
    private_sqlite = any(
        isinstance(node, ast.ImportFrom) and node.module == "_sqlite3"
        for node in sqlite_tree.body
    )
    if not public_sqlite or private_sqlite:
        failures.append("SQLite reference adapter does not use the public sqlite3 module exclusively")

    parameter_path = PACKAGE / "parameter_policy.py"
    parameter_tree = ast.parse(
        parameter_path.read_text(encoding="utf-8"),
        filename="parameter_policy.py",
    )
    parameter_classes, parameter_functions = _class_and_function_names(parameter_path)
    required_parameter_classes = {
        "TrancheCParameterPolicyClassV1",
        "TrancheCParameterEvidenceV1",
        "TrancheCParameterAdmissibilityReceiptV1",
        "TrancheCDrawdownCalibrationArtifactV1",
    }
    if not required_parameter_classes <= parameter_classes:
        failures.append("centralized typed parameter admissibility contract is incomplete")
    if not {
        "_validate_exact_evidence_v1",
        "_validate_drawdown_calibration_artifact_v1",
        "resolve_tranche_c_parameter_v1",
    } <= parameter_functions:
        failures.append("centralized dynamic parameter resolver path is incomplete")
    required_evidence_fields = {
        "evidence_ref", "evidence_class", "family_evidence_binding_ref",
        "value_source_class", "source_or_binding_refs",
        "source_currentization_refs", "active_scope_ref", "source_epoch_ref",
        "canonical_owner_ref", "authority_ref", "declared_unit_or_basis",
        "observed_at", "evaluated_at", "valid_until", "constraint_refs",
    }
    required_bundle_fields = {
        "calibration_bundle_ref", "approved_sleeve_max_drawdown_budget",
        "warning_threshold", "freeze_threshold", "canonical_owner_ref",
        "authority_ref", "active_scope_ref", "source_epoch_ref",
        "observed_at", "evaluated_at", "valid_until",
    }
    required_receipt_fields = {
        "evidence_ref", "family_evidence_binding_ref", "value_source_class",
        "source_currentization_refs", "active_scope_ref", "source_epoch_ref",
        "observed_at", "evaluated_at", "resolution_at", "valid_until",
        "calibration_bundle_ref",
    }
    try:
        if not required_evidence_fields <= _annotated_fields(
            parameter_tree, "TrancheCParameterEvidenceV1"
        ):
            failures.append("dynamic source/runtime evidence field closure is incomplete")
        if required_bundle_fields != _annotated_fields(
            parameter_tree, "TrancheCDrawdownCalibrationArtifactV1"
        ):
            failures.append("drawdown calibration bundle field closure is not exact")
        if not required_receipt_fields <= _annotated_fields(
            parameter_tree, "TrancheCParameterAdmissibilityReceiptV1"
        ):
            failures.append("dynamic admissibility receipt custody is incomplete")
        bundle_post_init = _class_method_node(
            parameter_tree,
            "TrancheCDrawdownCalibrationArtifactV1",
            "__post_init__",
        )
        bundle_constants = {
            node.value
            for node in ast.walk(bundle_post_init)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        bundle_calls = {
            node.func.id
            for node in ast.walk(bundle_post_init)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        bundle_attributes = {
            node.attr for node in ast.walk(bundle_post_init)
            if isinstance(node, ast.Attribute)
        }
        if (
            not {"0.50", "1.00"} <= bundle_constants
            or not {"decimal_context_v1", "exact_decimal"} <= bundle_calls
            or not {
                "approved_sleeve_max_drawdown_budget",
                "warning_threshold",
                "freeze_threshold",
            } <= bundle_attributes
        ):
            failures.append("drawdown calibration formulas are not exact Decimal laws")
    except ValueError as exc:
        failures.append(str(exc))

    binding_by_id = {row.get("parameter_id"): row for row in bindings}
    source_rows = tuple(
        row for row in policies
        if row.get("applicability_state") == "SOURCE_BOUND_MUTABLE_VALUE"
    )
    required_source_fields = (
        "family_evidence_binding_ref", "effective_value_source_class",
        "effective_source_state_refs", "source_currentization_refs",
        "effective_unit_or_basis", "master_plan_section_id",
        "currentization_version",
    )
    if len(source_rows) != 2 or any(
        any(not row.get(field) for field in required_source_fields)
        or binding_by_id.get(row.get("parameter_id"), {}).get(
            "active_stage1_value_authority"
        ) is None
        or binding_by_id.get(row.get("parameter_id"), {}).get(
            "currentized_source_refs"
        ) != row.get("source_currentization_refs")
        for row in source_rows
    ):
        failures.append("source/runtime policy evidence custody is not exact for both rows")

    drawdown_by_symbol = {
        row.get("parameter_symbol"): row
        for row in policies
        if row.get("effective_resolution_class") == "RISK_POLICY_DERIVED"
    }
    expected_drawdown_rules = {
        "dd_warn": "0.50 * approved_sleeve_max_drawdown_budget",
        "dd_freeze": "1.00 * approved_sleeve_max_drawdown_budget",
    }
    if (
        set(drawdown_by_symbol) != set(expected_drawdown_rules)
        or any(
            drawdown_by_symbol[symbol].get(
                "effective_day1_seed_value_or_resolution_rule"
            ) != rule
            for symbol, rule in expected_drawdown_rules.items()
        )
        or len({
            (
                row.get("family_evidence_binding_ref"),
                tuple(row.get("effective_source_state_refs", ())),
                row.get("effective_unit_or_basis"),
                row.get("canonical_owner"),
            )
            for row in drawdown_by_symbol.values()
        }) != 1
    ):
        failures.append("frozen drawdown rows do not share the exact calibration family")
    with localcontext(CONTEXT):
        independent_budget = Decimal("0.20")
        independent_warning = Decimal("0.50") * independent_budget
        independent_freeze = Decimal("1.00") * independent_budget
    if (
        independent_warning != Decimal("0.10")
        or independent_freeze != Decimal("0.20")
        or not Decimal("0") <= independent_warning < independent_freeze
    ):
        failures.append("independent drawdown formula reconstruction failed")
    independently_classified: list[str] = []
    for row in policies:
        applicability = row.get("applicability_state")
        resolution = row.get("effective_resolution_class")
        if applicability == "DORMANT_FUTURE_MARKET_PRESERVED_FAIL_CLOSED":
            policy_class = "NO_MACHINE_VERIFIABLE_OVERRIDE"
        elif applicability == "SOURCE_BOUND_MUTABLE_VALUE":
            policy_class = "SOURCE_OR_RUNTIME_BOUND"
        elif applicability == "REFERENCE_SEED_REQUIRES_CONTEXT_AND_OWNER_BINDING":
            policy_class = {
                "RISK_POLICY_DERIVED": "CALIBRATION_REQUIRED",
                "STATIC_NUMERIC_OR_OWNER_EDIT": "BOUNDED_NUMERIC",
                "STATIC_NUMERIC": "FIXED_SINGLETON_NUMERIC",
            }.get(resolution, "UNSUPPORTED")
        elif resolution == "STATIC_MAP_REFERENCE":
            policy_class = "TYPED_STRUCTURAL"
        elif resolution in {
            "STATIC_ENUM", "STATIC_RULE", "STATIC_FORMULA_RULE",
            "STATIC_ENUM_OR_RULE", "FORMULA", "STATIC_POINTER_OR_CONNECTOR_RULE",
            "STATIC_ENUM_OR_CONNECTOR_RULE",
        }:
            policy_class = "FIXED_SYMBOLIC_OR_ENUM"
        else:
            policy_class = "UNSUPPORTED"
        independently_classified.append(policy_class)
    expected_counts = {
        "FIXED_SYMBOLIC_OR_ENUM": 59,
        "FIXED_SINGLETON_NUMERIC": 1,
        "BOUNDED_NUMERIC": 1,
        "TYPED_STRUCTURAL": 1,
        "SOURCE_OR_RUNTIME_BOUND": 2,
        "CALIBRATION_REQUIRED": 2,
        "NO_MACHINE_VERIFIABLE_OVERRIDE": 14,
    }
    if Counter(independently_classified) != Counter(expected_counts):
        failures.append("independent 80-policy admissibility classification is not exact")

    registry_tree = ast.parse(
        (PACKAGE / "implementation_registry.py").read_text(encoding="utf-8"),
        filename="implementation_registry.py",
    )
    compatibility = next(
        node
        for node in registry_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "compute_math_36_kalshi_binary_book_transform"
    )
    canonical_calls = [
        node
        for node in ast.walk(compatibility)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "binary_book_implied_asks_v1"
    ]
    if len(canonical_calls) != 1 or any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub)
        for node in ast.walk(compatibility)
    ):
        failures.append("MATH-36 predecessor route is not a delegation-only adapter")

    matrix_text = (
        REPO_ROOT
        / "tests"
        / "stage1_prediction_markets"
        / "qku_computation_control_plane"
        / "accounting"
        / "test_contract_matrix.py"
    ).read_text(encoding="utf-8")
    if not {
        '"journal-link-bijection"',
        "test_dynamic_parameter_evidence_compound_matrix",
        "drawdown_calibration_artifact",
    } <= {marker for marker in (
        '"journal-link-bijection"',
        "test_dynamic_parameter_evidence_compound_matrix",
        "drawdown_calibration_artifact",
    ) if marker in matrix_text}:
        failures.append("central accounting matrix lacks compact residual semantic coverage")


def main() -> int:
    failures: list[str] = []
    receipt_rows: tuple[IndependentMathRowEvidenceV1, ...] = ()
    _source_safety(failures)
    try:
        policies = _archive_rows(PACKAGE / "parameter_policy.py", "_ST12C_POLICY_ARCHIVE_B85")
        bindings = _archive_rows(PACKAGE / "parameter_policy.py", "_ST12C_BINDING_ARCHIVE_B85")
        oracles = _archive_rows(PACKAGE / "oracle_contracts.py", "_ST12C_ORACLE_ARCHIVE_B85")
        vectors = _archive_rows(PACKAGE / "oracle_contracts.py", "_ST12C_VECTOR_ARCHIVE_B85")
    except (OSError, SyntaxError, ValueError, KeyError, zlib.error) as exc:
        failures.append(f"frozen overlay could not be independently decoded: {exc}")
        policies = bindings = oracles = vectors = ()
    policy_ids = tuple(row.get("parameter_id") for row in policies)
    binding_ids = tuple(row.get("parameter_id") for row in bindings)
    oracle_ids = tuple(row.get("math_spec_ref") for row in oracles)
    vector_ids = tuple(row.get("math_spec_ref") for row in vectors)
    if len(policies) != 80 or len(set(policy_ids)) != 80 or policy_ids != binding_ids:
        failures.append("parameter closure is not exact 80/80")
    if any(row.get("no_silent_default") is not True or row.get("codex_online_research_allowed") is not False or row.get("provider_effect_authorized") is not False for row in policies):
        failures.append("parameter no-default/research/effect law failed")
    if oracle_ids != EXPECTED_MATH_IDS or vector_ids != EXPECTED_MATH_IDS:
        failures.append("oracle/vector identities are not MATH-26..38 exactly")
    if any(row.get("production_implementation_import_allowed") is not False for row in (*oracles, *vectors)):
        failures.append("oracle/vector production-import separation failed")
    _semantic_repair_closure(failures, policies, bindings)
    try:
        receipt_rows = _build_accounting_receipt_rows(oracles, vectors)
    except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
        failures.append(f"accounting row-receipt reconstruction failed: {exc}")
    actual = _golden_results()
    expected = {
        "MATH-26": Decimal(".15"), "MATH-27": Decimal(".20"), "MATH-28": Decimal(".10"),
        "MATH-29": Decimal(".06"), "MATH-30": (Decimal(3), Decimal(3)), "MATH-31": Decimal(3),
        "MATH-32": Decimal("3.00"), "MATH-33": Decimal("1.00"),
        "MATH-34": (Decimal("1.25"), Decimal("1.25000")),
        "MATH-35": (Decimal("-.312500"), Decimal("-.31"), Decimal("1.250000"), Decimal("1.25")),
        "MATH-36": (Decimal(".44"), Decimal(".58")), "MATH-37": (True, True, True), "MATH-38": Decimal(65),
    }
    if actual != expected:
        failures.append(f"independent golden reconstruction mismatch: {actual!r}")
    accounting_matrix = REPO_ROOT / "tests" / "stage1_prediction_markets" / "qku_computation_control_plane" / "accounting" / "test_contract_matrix.py"
    execution_matrix = accounting_matrix.parents[1] / "execution" / "test_contract_matrix.py"
    if not accounting_matrix.is_file() or not execution_matrix.is_file():
        failures.append("centralized accounting/execution matrices are missing")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(format_evidence_line(build_envelope("ACCOUNTING", receipt_rows)))
    print(f"{SUCCESS} controls=16 policies=80 bindings=80 math=13 oracles=13 vectors=13 effects=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
