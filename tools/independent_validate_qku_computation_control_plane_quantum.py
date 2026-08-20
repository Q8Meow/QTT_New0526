#!/usr/bin/env python3
"""Independent executable MATH-50 through MATH-52 validation."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.qku_independent_math_row_receipt import (  # noqa: E402
    EVIDENCE_TIER,
    PRODUCTION_SYSTEM_UNDER_TEST_WITH_INDEPENDENT_EXPECTED_RESULT,
    TERMINAL_STATE,
    IndependentMathRowEvidenceV1,
    build_envelope,
    evidence_observation,
    format_evidence_line,
    observed_result,
)

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (  # noqa: E402
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_benchmark import (  # noqa: E402
    EconomicComparatorReceiptV1,
    QAOAPreexistingTraceV1,
    QAOATracePointV1,
    QuantumBenchmarkServiceV1,
    QuantumEconomicBasisV1,
    VQEPreexistingTraceV1,
    VQETracePointV1,
)


PACKAGE = ROOT / "src/qtt/stage1_prediction_markets/qku_computation_control_plane"


def _basis(**overrides: object) -> QuantumEconomicBasisV1:
    values: dict[str, object] = {
        "input_lock_id": "L::1",
        "original_formulation_id": "F::1",
        "objective_sense": "MAXIMIZE",
        "constraint_refs": ("CONSTRAINT::1",),
        "accounting_basis_ref": "ACCOUNTING::1",
        "cost_basis_ref": "COST::1",
        "capacity_basis_ref": "CAPACITY::1",
        "scenario_set_ref": "SCENARIO::1",
        "resource_budget_ref": "RESOURCE::1",
        "ttl_policy_ref": "TTL::1",
        "version_epoch_pins": ("VERSION::1", "SOURCE::1=EPOCH::1"),
    }
    values.update(overrides)
    return QuantumEconomicBasisV1(**values)


def _comparator(
    comparator_class: str,
    *,
    basis: QuantumEconomicBasisV1 | None = None,
    utility: str = "0.65",
    resource_use: str = "2",
    latency: str = "2",
    feasible: bool = True,
    hard_veto: bool = False,
) -> EconomicComparatorReceiptV1:
    return EconomicComparatorReceiptV1(
        receipt_id=f"RECEIPT::{comparator_class}",
        comparator_class=comparator_class,
        comparison_basis=_basis() if basis is None else basis,
        feasible=feasible,
        hard_veto=hard_veto,
        conservative_utility=Decimal(utility),
        resource_use=Decimal(resource_use),
        latency=Decimal(latency),
        deterministic_tie_break=f"TIE::{comparator_class}",
    )


def _qaoa() -> QAOAPreexistingTraceV1:
    classical = _comparator("STRONGEST_CLASSICAL")
    no_trade = _comparator(
        "NO_TRADE", utility="0", resource_use="0", latency="0"
    )
    return QAOAPreexistingTraceV1(
        trace_id="Q::1",
        input_lock_id="L::1",
        formulation_id="F::1",
        objective_id="O::1",
        objective_sense="MAXIMIZE",
        parameter_order=("theta",),
        seed_policy_ref="SEED::1",
        bounds_ref="BOUNDS::1",
        constraint_refs=("CONSTRAINT::1",),
        comparison_basis=_basis(),
        points=(
            QAOATracePointV1(
                "A", Decimal("0.25"), Decimal("2"), True,
                Decimal("0.6"), Decimal("2"), Decimal("2"),
            ),
            QAOATracePointV1(
                "B", Decimal("0.75"), Decimal("1"), True,
                Decimal("0.7"), Decimal("1"), Decimal("1"),
            ),
        ),
        selected_candidate_id="B",
        strongest_classical_receipt_ref=classical.receipt_id,
        no_trade_receipt_ref=no_trade.receipt_id,
        strongest_classical_comparator=classical,
        no_trade_comparator=no_trade,
        trace_complete=True,
        original_model_interpret_back_valid=True,
    )


def _vqe() -> VQEPreexistingTraceV1:
    classical = _comparator("STRONGEST_CLASSICAL")
    no_trade = _comparator(
        "NO_TRADE", utility="0", resource_use="0", latency="0"
    )
    return VQEPreexistingTraceV1(
        trace_id="V::1",
        input_lock_id="L::1",
        formulation_id="F::1",
        objective_sense="MAXIMIZE",
        hamiltonian_id="H::1",
        ansatz_metadata_ref="ANSATZ::SUPPLIED",
        parameter_order=("phi",),
        optimizer_metadata_ref="OPTIMIZER::SUPPLIED",
        seed_policy_ref="SEED::1",
        bounds_ref="BOUNDS::1",
        constraint_refs=("CONSTRAINT::1",),
        comparison_basis=_basis(),
        points=(
            VQETracePointV1(
                "A", Decimal("0.2"), Decimal("0.01"), Decimal("1"),
                True, Decimal("0.55"), Decimal("1"), Decimal("1"),
            ),
            VQETracePointV1(
                "B", Decimal("0.4"), Decimal("0.02"), Decimal("2"),
                True, Decimal("0.5"), Decimal("2"), Decimal("2"),
            ),
        ),
        selected_point_id="A",
        strongest_classical_receipt_ref=classical.receipt_id,
        no_trade_receipt_ref=no_trade.receipt_id,
        strongest_classical_comparator=classical,
        no_trade_comparator=no_trade,
        trace_complete=True,
        original_model_interpret_back_valid=True,
    )


def _st12f_vector_rows() -> dict[str, dict[str, object]]:
    path = PACKAGE / "oracle_contracts.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    node = next(
        item
        for item in tree.body
        if isinstance(item, ast.AnnAssign)
        and isinstance(item.target, ast.Name)
        and item.target.id == "_ST12F_NEW_VECTOR_ROWS_V1"
    )
    if (
        not isinstance(node.value, ast.Call)
        or not isinstance(node.value.func, ast.Name)
        or node.value.func.id != "MappingProxyType"
        or len(node.value.args) != 1
    ):
        raise ValueError("ST12-F tracked vector owner is not an immutable literal")
    rows = ast.literal_eval(node.value.args[0])
    if not isinstance(rows, dict) or any(
        not isinstance(key, str) or not isinstance(value, dict)
        for key, value in rows.items()
    ):
        raise ValueError("ST12-F tracked vector rows are malformed")
    return rows


def _qd(value: object, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{name} must be an exact Decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{name} must be finite")
    return result


_BASIS_FIELDS = (
    "input_lock_id",
    "original_formulation_id",
    "objective_sense",
    "constraint_refs",
    "accounting_basis_ref",
    "cost_basis_ref",
    "capacity_basis_ref",
    "scenario_set_ref",
    "resource_budget_ref",
    "ttl_policy_ref",
    "version_epoch_pins",
)


def _basis_from_raw(raw: object) -> QuantumEconomicBasisV1:
    if not isinstance(raw, Mapping) or tuple(raw) != _BASIS_FIELDS:
        raise ValueError("quantum basis field order or membership differs")
    return QuantumEconomicBasisV1(
        input_lock_id=str(raw["input_lock_id"]),
        original_formulation_id=str(raw["original_formulation_id"]),
        objective_sense=str(raw["objective_sense"]),
        constraint_refs=tuple(raw["constraint_refs"]),  # type: ignore[arg-type]
        accounting_basis_ref=str(raw["accounting_basis_ref"]),
        cost_basis_ref=str(raw["cost_basis_ref"]),
        capacity_basis_ref=str(raw["capacity_basis_ref"]),
        scenario_set_ref=str(raw["scenario_set_ref"]),
        resource_budget_ref=str(raw["resource_budget_ref"]),
        ttl_policy_ref=str(raw["ttl_policy_ref"]),
        version_epoch_pins=tuple(raw["version_epoch_pins"]),  # type: ignore[arg-type]
    )


def _tracked_comparator(
    raw: Mapping[str, object],
    basis: QuantumEconomicBasisV1,
) -> EconomicComparatorReceiptV1:
    comparator_class = str(raw["comparator_class"])
    return EconomicComparatorReceiptV1(
        receipt_id=f"TRACKED::{comparator_class}",
        comparator_class=comparator_class,
        comparison_basis=basis,
        feasible=raw["feasible"],  # type: ignore[arg-type]
        hard_veto=raw["hard_veto"],  # type: ignore[arg-type]
        conservative_utility=_qd(raw["conservative_utility"], "utility"),
        resource_use=_qd(raw["resource_use"], "resource_use"),
        latency=_qd(raw["latency"], "latency"),
        deterministic_tie_break=str(raw["deterministic_tie_break"]),
    )


def _tracked_qaoa(inputs: Mapping[str, object]) -> QAOAPreexistingTraceV1:
    basis = _basis_from_raw(inputs["quantum_basis"])
    classical_basis = _basis_from_raw(inputs["strongest_classical_basis"])
    no_trade_basis = _basis_from_raw(inputs["no_trade_basis"])
    classical = _comparator("STRONGEST_CLASSICAL", basis=classical_basis)
    no_trade = _comparator(
        "NO_TRADE", basis=no_trade_basis, utility="0", resource_use="0", latency="0"
    )
    weights = inputs["trace_weights"]
    costs = inputs["locked_costs"]
    feasibility = inputs["observed_feasibility"]
    utilities = inputs["original_economic_utilities"]
    resources = inputs["resource_use"]
    latencies = inputs["latency"]
    if not all(
        isinstance(value, Mapping)
        for value in (weights, costs, feasibility, utilities, resources, latencies)
    ):
        raise ValueError("MATH-50 tracked traces are not mappings")
    points = tuple(
        QAOATracePointV1(
            candidate_id,
            _qd(weights[candidate_id], "trace_weight"),
            _qd(costs[candidate_id], "locked_cost"),
            feasibility[candidate_id],  # type: ignore[arg-type]
            _qd(utilities[candidate_id], "utility"),
            _qd(resources[candidate_id], "resource_use"),
            _qd(latencies[candidate_id], "latency"),
        )
        for candidate_id in weights
    )
    return QAOAPreexistingTraceV1(
        trace_id="TRACKED::QAOA::MATH-50",
        input_lock_id=str(inputs["input_lock_id"]),
        formulation_id=str(inputs["formulation_id"]),
        objective_id=str(inputs["objective_id"]),
        objective_sense=str(inputs["objective_sense"]),
        parameter_order=tuple(inputs["parameter_order"]),  # type: ignore[arg-type]
        seed_policy_ref=str(inputs["seed_policy_ref"]),
        bounds_ref=str(inputs["bounds_ref"]),
        constraint_refs=tuple(inputs["constraint_refs"]),  # type: ignore[arg-type]
        comparison_basis=basis,
        points=points,
        selected_candidate_id=str(inputs["selected_candidate_id"]),
        strongest_classical_receipt_ref=classical.receipt_id,
        no_trade_receipt_ref=no_trade.receipt_id,
        strongest_classical_comparator=classical,
        no_trade_comparator=no_trade,
        trace_complete=inputs["trace_complete"],  # type: ignore[arg-type]
        original_model_interpret_back_valid=inputs[
            "original_model_interpret_back_valid"
        ],  # type: ignore[arg-type]
    )


def _tracked_vqe(inputs: Mapping[str, object]) -> VQEPreexistingTraceV1:
    basis = _basis_from_raw(inputs["quantum_basis"])
    classical_basis = _basis_from_raw(inputs["strongest_classical_basis"])
    no_trade_basis = _basis_from_raw(inputs["no_trade_basis"])
    classical = _comparator("STRONGEST_CLASSICAL", basis=classical_basis)
    no_trade = _comparator(
        "NO_TRADE", basis=no_trade_basis, utility="0", resource_use="0", latency="0"
    )
    point_ids = tuple(inputs["parameter_point_ids"])  # type: ignore[arg-type]
    sequence_names = (
        "expectation_trace",
        "variance_trace",
        "locked_costs",
        "original_economic_utilities",
        "observed_feasibility",
        "resource_use",
        "latency",
    )
    sequences = {name: tuple(inputs[name]) for name in sequence_names}  # type: ignore[arg-type]
    if any(len(values) != len(point_ids) for values in sequences.values()):
        raise ValueError("MATH-51 tracked trace vectors are misaligned")
    points = tuple(
        VQETracePointV1(
            point_id,
            _qd(sequences["expectation_trace"][index], "expectation"),
            _qd(sequences["variance_trace"][index], "variance"),
            _qd(sequences["locked_costs"][index], "locked_cost"),
            sequences["observed_feasibility"][index],  # type: ignore[arg-type]
            _qd(sequences["original_economic_utilities"][index], "utility"),
            _qd(sequences["resource_use"][index], "resource_use"),
            _qd(sequences["latency"][index], "latency"),
        )
        for index, point_id in enumerate(point_ids)
    )
    return VQEPreexistingTraceV1(
        trace_id="TRACKED::VQE::MATH-51",
        input_lock_id=str(inputs["input_lock_id"]),
        formulation_id=str(inputs["formulation_id"]),
        objective_sense=str(inputs["objective_sense"]),
        hamiltonian_id=str(inputs["hamiltonian_id"]),
        ansatz_metadata_ref=str(inputs["ansatz_metadata_ref"]),
        parameter_order=tuple(inputs["parameter_order"]),  # type: ignore[arg-type]
        optimizer_metadata_ref=str(inputs["optimizer_metadata_ref"]),
        seed_policy_ref=str(inputs["seed_policy_ref"]),
        bounds_ref=str(inputs["bounds_ref"]),
        constraint_refs=tuple(inputs["constraint_refs"]),  # type: ignore[arg-type]
        comparison_basis=basis,
        points=points,
        selected_point_id=str(inputs["selected_point_id"]),
        strongest_classical_receipt_ref=classical.receipt_id,
        no_trade_receipt_ref=no_trade.receipt_id,
        strongest_classical_comparator=classical,
        no_trade_comparator=no_trade,
        trace_complete=inputs["trace_complete"],  # type: ignore[arg-type]
        original_model_interpret_back_valid=inputs[
            "original_model_interpret_back_valid"
        ],  # type: ignore[arg-type]
    )


def _independent_math50(inputs: object) -> dict[str, object]:
    if not isinstance(inputs, Mapping):
        raise ValueError("MATH-50 inputs must be a mapping")
    mappings = tuple(
        inputs[name]
        for name in (
            "trace_weights",
            "locked_costs",
            "observed_feasibility",
            "original_economic_utilities",
            "resource_use",
            "latency",
        )
    )
    if any(not isinstance(value, Mapping) for value in mappings):
        raise ValueError("MATH-50 trace fields must be mappings")
    weights, costs, feasibility, utilities, resources, latencies = mappings
    ids = tuple(weights)
    if any(tuple(value) != ids for value in mappings[1:]):
        raise ValueError("MATH-50 trace identities must align exactly")
    parsed_weights = {key: _qd(weights[key], "trace_weight") for key in ids}
    if any(value < 0 for value in parsed_weights.values()) or sum(
        parsed_weights.values(), Decimal(0)
    ) != 1:
        raise ValueError("MATH-50 trace weights must be nonnegative and normalized")
    if any(type(feasibility[key]) is not bool for key in ids):
        raise ValueError("MATH-50 feasibility must be Boolean")
    expected_cost = sum(
        (
            parsed_weights[key] * _qd(costs[key], "locked_cost")
            for key in ids
        ),
        Decimal(0),
    )
    feasible = tuple(key for key in ids if feasibility[key])
    if not feasible:
        raise ValueError("MATH-50 requires an original-model-feasible point")
    winner = sorted(
        feasible,
        key=lambda key: (-_qd(utilities[key], "utility"), key),
    )[0]
    if winner != inputs["selected_candidate_id"]:
        raise ValueError("MATH-50 selected candidate differs from independent winner")
    if any(_qd(resources[key], "resource_use") < 0 for key in ids) or any(
        _qd(latencies[key], "latency") < 0 for key in ids
    ):
        raise ValueError("MATH-50 resource or latency is negative")
    return {
        "trace_expected_locked_cost": expected_cost,
        "original_economic_objective": _qd(utilities[winner], "utility"),
        "selected_candidate_id": winner,
        "selected_original_model_feasible": True,
        "effect_call_count": 0,
    }


def _independent_math51(inputs: object) -> dict[str, object]:
    if not isinstance(inputs, Mapping):
        raise ValueError("MATH-51 inputs must be a mapping")
    ids = tuple(inputs["parameter_point_ids"])  # type: ignore[arg-type]
    names = (
        "expectation_trace",
        "variance_trace",
        "locked_costs",
        "original_economic_utilities",
        "observed_feasibility",
        "resource_use",
        "latency",
    )
    values = {name: tuple(inputs[name]) for name in names}  # type: ignore[arg-type]
    if not ids or any(len(row) != len(ids) for row in values.values()):
        raise ValueError("MATH-51 trace vectors must be aligned and nonempty")
    variance = tuple(_qd(value, "variance") for value in values["variance_trace"])
    if any(value < 0 for value in variance):
        raise ValueError("MATH-51 variance must be nonnegative")
    feasible = tuple(
        point_id
        for index, point_id in enumerate(ids)
        if values["observed_feasibility"][index] is True
    )
    if not feasible:
        raise ValueError("MATH-51 requires an original-model-feasible point")
    utility = {
        point_id: _qd(values["original_economic_utilities"][index], "utility")
        for index, point_id in enumerate(ids)
    }
    winner = sorted(feasible, key=lambda point_id: (-utility[point_id], point_id))[0]
    if winner != inputs["selected_point_id"]:
        raise ValueError("MATH-51 selected point differs from independent winner")
    index = ids.index(winner)
    return {
        "trace_expectation": _qd(values["expectation_trace"][index], "expectation"),
        "variance": variance[index],
        "original_economic_objective": utility[winner],
        "selected_candidate_id": winner,
        "selected_original_model_feasible": True,
        "effect_call_count": 0,
    }


def _independent_math52(inputs: object) -> dict[str, object]:
    if not isinstance(inputs, Mapping):
        raise ValueError("MATH-52 inputs must be a mapping")
    bases = tuple(
        inputs[name]
        for name in ("quantum_basis", "strongest_classical_basis", "no_trade_basis")
    )
    if any(not isinstance(value, Mapping) for value in bases) or any(
        tuple(value) != _BASIS_FIELDS for value in bases  # type: ignore[arg-type]
    ):
        raise ValueError("MATH-52 basis fields differ")
    if not (dict(bases[0]) == dict(bases[1]) == dict(bases[2])):  # type: ignore[arg-type]
        raise ValueError("MATH-52 comparison bases differ")
    comparator_names = ("validated_quantum", "strongest_classical", "no_trade")
    rows: list[tuple[str, bool, bool, Decimal, Decimal, Decimal, str]] = []
    expected_classes = ("VALIDATED_QUANTUM", "STRONGEST_CLASSICAL", "NO_TRADE")
    for name, expected_class in zip(comparator_names, expected_classes, strict=True):
        raw = inputs[name]
        if not isinstance(raw, Mapping) or raw.get("comparator_class") != expected_class:
            raise ValueError("MATH-52 comparator class differs")
        feasible = raw.get("feasible")
        hard_veto = raw.get("hard_veto")
        if type(feasible) is not bool or type(hard_veto) is not bool:
            raise ValueError("MATH-52 feasibility/veto must be Boolean")
        if expected_class == "NO_TRADE" and (feasible is not True or hard_veto):
            raise ValueError("MATH-52 permanent NO_TRADE must remain feasible")
        resource = _qd(raw.get("resource_use"), "resource_use")
        latency = _qd(raw.get("latency"), "latency")
        if resource < 0 or latency < 0:
            raise ValueError("MATH-52 resource/latency must be nonnegative")
        rows.append(
            (
                expected_class,
                feasible,
                hard_veto,
                _qd(raw.get("conservative_utility"), "utility"),
                resource,
                latency,
                str(raw.get("deterministic_tie_break")),
            )
        )
    priority = {"NO_TRADE": 0, "STRONGEST_CLASSICAL": 1, "VALIDATED_QUANTUM": 2}
    winner = sorted(
        rows,
        key=lambda row: (
            0 if row[1] and not row[2] else 1,
            -row[3],
            row[4],
            row[5],
            priority[row[0]],
            row[6],
        ),
    )[0][0]
    utilities = {row[0]: row[3] for row in rows}
    return {
        "delta_quantum_vs_classical": utilities["VALIDATED_QUANTUM"]
        - utilities["STRONGEST_CLASSICAL"],
        "delta_quantum_vs_no_trade": utilities["VALIDATED_QUANTUM"]
        - utilities["NO_TRADE"],
        "quantum_advantage_claim_allowed": False,
        "winner": winner,
    }


def _result_matches(observed: object, expected: object) -> bool:
    if isinstance(observed, Mapping) and isinstance(expected, Mapping):
        return set(observed) == set(expected) and all(
            _result_matches(observed[key], expected[key]) for key in observed
        )
    if isinstance(observed, bool) or isinstance(expected, bool):
        return type(observed) is bool and observed is expected
    try:
        return _qd(observed, "observed") == _qd(expected, "expected")
    except ValueError:
        return type(observed) is type(expected) and observed == expected


def _independent_rejection(callable_, message: str) -> dict[str, object]:
    try:
        callable_()
    except ValueError as exc:
        if message not in str(exc):
            raise ValueError(f"wrong independent quantum rejection: {exc}") from exc
        return {"exception_type": type(exc).__name__, "message": str(exc)}
    raise ValueError(f"expected independent quantum rejection was accepted: {message}")


def _production_rejection(callable_, reason: ReasonCode) -> dict[str, object]:
    try:
        callable_()
    except ContractValidationError as exc:
        if exc.reason_code is not reason:
            raise ValueError(f"wrong production quantum rejection: {exc.reason_code}") from exc
        return {
            "exception_type": type(exc).__name__,
            "reason_code": exc.reason_code.value,
            "message": str(exc),
        }
    raise ValueError(f"expected production quantum rejection was accepted: {reason.value}")


def _build_quantum_receipt_rows() -> tuple[IndependentMathRowEvidenceV1, ...]:
    material = _st12f_vector_rows()
    rows = {math_id: material[math_id] for math_id in ("MATH-50", "MATH-51", "MATH-52")}
    for math_id, row in rows.items():
        if (
            row.get("comparison")
            not in {
                "EXACT_DECIMAL_AND_TYPED_BASIS_INVARIANTS",
                "LEXICOGRAPHIC_FEASIBILITY_UTILITY_RESOURCE_LATENCY_TIEBREAK",
            }
            or not isinstance(row.get("inputs"), dict)
            or not isinstance(row.get("expected"), dict)
        ):
            raise ValueError(f"{math_id}: tracked quantum material differs")
    inputs50 = rows["MATH-50"]["inputs"]
    inputs51 = rows["MATH-51"]["inputs"]
    inputs52 = rows["MATH-52"]["inputs"]
    assert isinstance(inputs50, dict) and isinstance(inputs51, dict) and isinstance(inputs52, dict)

    independent50 = _independent_math50(inputs50)
    independent51 = _independent_math51(inputs51)
    independent52 = _independent_math52(inputs52)
    if not _result_matches(independent50, rows["MATH-50"]["expected"]):
        raise ValueError("MATH-50 tracked independent result differs")
    if not _result_matches(independent51, rows["MATH-51"]["expected"]):
        raise ValueError("MATH-51 tracked independent result differs")
    if not _result_matches(independent52, rows["MATH-52"]["expected"]):
        raise ValueError("MATH-52 tracked independent result differs")

    service = QuantumBenchmarkServiceV1()
    trace50 = _tracked_qaoa(inputs50)
    trace51 = _tracked_vqe(inputs51)
    receipt50 = service.validate_qaoa_trace(trace50)
    receipt51 = service.validate_vqe_trace(trace51)
    sut50 = {
        "trace_expected_locked_cost": receipt50.recomputed_objective,
        "original_economic_objective": receipt50.original_economic_utility,
        "selected_candidate_id": receipt50.selected_candidate_id,
        "selected_original_model_feasible": receipt50.selected_original_model_feasible,
        "effect_call_count": sum(receipt50.effect_counts.values()),
    }
    sut51 = {
        "trace_expectation": receipt51.recomputed_objective,
        "variance": receipt51.recomputed_variance_or_explicit_absence,
        "original_economic_objective": receipt51.original_economic_utility,
        "selected_candidate_id": receipt51.selected_candidate_id,
        "selected_original_model_feasible": receipt51.selected_original_model_feasible,
        "effect_call_count": sum(receipt51.effect_counts.values()),
    }
    if not _result_matches(sut50, independent50) or not _result_matches(
        sut51, independent51
    ):
        raise ValueError("MATH-50/51 SUT results differ from independent truth")

    basis52 = _basis_from_raw(inputs52["quantum_basis"])
    validated_raw = inputs52["validated_quantum"]
    classical_raw = inputs52["strongest_classical"]
    no_trade_raw = inputs52["no_trade"]
    assert isinstance(validated_raw, Mapping) and isinstance(classical_raw, Mapping) and isinstance(no_trade_raw, Mapping)
    receipt52 = replace(
        receipt50,
        receipt_id="TRACKED::VALIDATED_QUANTUM",
        comparison_basis=basis52,
        input_lock_id=basis52.input_lock_id,
        formulation_id=basis52.original_formulation_id,
        original_economic_utility=_qd(
            validated_raw["conservative_utility"], "quantum utility"
        ),
        resource_use=_qd(validated_raw["resource_use"], "quantum resource"),
        latency=_qd(validated_raw["latency"], "quantum latency"),
        deterministic_tie_break=str(validated_raw["deterministic_tie_break"]),
    )
    classical52 = _tracked_comparator(classical_raw, basis52)
    no_trade52 = _tracked_comparator(no_trade_raw, basis52)
    comparison52 = service.compare_same_lock(
        comparison_id="TRACKED::MATH-52",
        quantum_receipt=receipt52,
        strongest_classical_receipt=classical52,
        no_trade_receipt=no_trade52,
    )
    sut52 = {
        "delta_quantum_vs_classical": comparison52.delta_quantum_vs_classical,
        "delta_quantum_vs_no_trade": comparison52.delta_quantum_vs_no_trade,
        "quantum_advantage_claim_allowed": comparison52.quantum_advantage_claim_allowed,
        "winner": comparison52.winner,
    }
    if not _result_matches(sut52, independent52):
        raise ValueError("MATH-52 SUT result differs from independent truth")

    formula50_inputs = deepcopy(inputs50)
    formula50_inputs["trace_weights"]["00"] = "0.49"
    formula50_inputs["trace_weights"]["01"] = "0.26"
    formula50 = _independent_math50(formula50_inputs)
    precision50_inputs = deepcopy(inputs50)
    precision50_inputs["trace_weights"]["00"] = "0.499999"
    precision50_inputs["trace_weights"]["01"] = "0.250001"
    precision50 = _independent_math50(precision50_inputs)
    if formula50 == independent50 or precision50 == independent50:
        raise ValueError("MATH-50 execution mutations were not observed")
    negative50_inputs = deepcopy(inputs50)
    negative50_inputs["trace_weights"]["00"] = "-0.1"
    negative50 = _independent_rejection(
        lambda: _independent_math50(negative50_inputs),
        "nonnegative and normalized",
    )
    incomplete50 = _production_rejection(
        lambda: service.validate_qaoa_trace(replace(trace50, trace_complete=False)),
        ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
    )
    lock50 = _production_rejection(
        lambda: replace(trace50, input_lock_id="LOCK::OTHER"),
        ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
    )
    basis50 = _production_rejection(
        lambda: service.validate_qaoa_trace(
            replace(
                trace50,
                comparison_basis=replace(
                    trace50.comparison_basis,
                    cost_basis_ref="COST::OTHER",
                ),
            )
        ),
        ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
    )

    formula51_inputs = deepcopy(inputs51)
    formula51_inputs["expectation_trace"][2] = "1.11"
    formula51 = _independent_math51(formula51_inputs)
    precision51_inputs = deepcopy(inputs51)
    precision51_inputs["expectation_trace"][2] = "1.100000000000001"
    precision51 = _independent_math51(precision51_inputs)
    if formula51 == independent51 or precision51 == independent51:
        raise ValueError("MATH-51 execution mutations were not observed")
    negative51_inputs = deepcopy(inputs51)
    negative51_inputs["variance_trace"][2] = "-0.01"
    negative51 = _independent_rejection(
        lambda: _independent_math51(negative51_inputs),
        "variance must be nonnegative",
    )
    incomplete51 = _production_rejection(
        lambda: service.validate_vqe_trace(replace(trace51, trace_complete=False)),
        ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
    )
    lock51 = _production_rejection(
        lambda: replace(trace51, input_lock_id="LOCK::OTHER"),
        ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
    )
    basis51 = _production_rejection(
        lambda: service.validate_vqe_trace(
            replace(
                trace51,
                comparison_basis=replace(
                    trace51.comparison_basis,
                    cost_basis_ref="COST::OTHER",
                ),
            )
        ),
        ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
    )

    formula52_inputs = deepcopy(inputs52)
    formula52_inputs["validated_quantum"]["conservative_utility"] = "1.4"
    formula52 = _independent_math52(formula52_inputs)
    precision52_inputs = deepcopy(inputs52)
    precision52_inputs["validated_quantum"]["conservative_utility"] = "1.300000000000001"
    precision52 = _independent_math52(precision52_inputs)
    if formula52["winner"] != "VALIDATED_QUANTUM" or precision52["winner"] != "VALIDATED_QUANTUM":
        raise ValueError("MATH-52 utility mutations were not observed")
    negative52_inputs = deepcopy(inputs52)
    negative52_inputs["no_trade"]["feasible"] = False
    negative52 = _independent_rejection(
        lambda: _independent_math52(negative52_inputs),
        "permanent NO_TRADE must remain feasible",
    )
    tie52_inputs = deepcopy(inputs52)
    for name in ("validated_quantum", "strongest_classical", "no_trade"):
        tie52_inputs[name]["conservative_utility"] = "1.2"
        tie52_inputs[name]["resource_use"] = "1"
        tie52_inputs[name]["latency"] = "1"
    tie52 = _independent_math52(tie52_inputs)
    if tie52["winner"] != "NO_TRADE":
        raise ValueError("MATH-52 conservative tie boundary failed")

    basis_rejections: dict[str, object] = {}
    basis_mutations: tuple[tuple[str, object], ...] = (
        ("input_lock_id", "LOCK::OTHER"),
        ("original_formulation_id", "FORMULATION::OTHER"),
        ("objective_sense", "MINIMIZE"),
        ("constraint_refs", ("CONSTRAINT::OTHER",)),
        ("accounting_basis_ref", "ACCOUNTING::OTHER"),
        ("cost_basis_ref", "COST::OTHER"),
        ("capacity_basis_ref", "CAPACITY::OTHER"),
        ("scenario_set_ref", "SCENARIO::OTHER"),
        ("resource_budget_ref", "RESOURCE::OTHER"),
        ("ttl_policy_ref", "TTL::OTHER"),
        ("version_epoch_pins", ("EPOCH::OTHER",)),
    )
    for field_name, value in basis_mutations:
        reason = (
            ReasonCode.ST12F_INPUT_LOCK_MISMATCH
            if field_name == "input_lock_id"
            else ReasonCode.ST12F_QUANTUM_TRACE_INVALID
        )
        basis_rejections[field_name] = _production_rejection(
            lambda field_name=field_name, value=value: service.compare_same_lock(
                comparison_id=f"TRACKED::MISMATCH::{field_name}",
                quantum_receipt=receipt52,
                strongest_classical_receipt=_comparator(
                    "STRONGEST_CLASSICAL",
                    basis=replace(basis52, **{field_name: value}),
                ),
                no_trade_receipt=no_trade52,
            ),
            reason,
        )

    common = {
        "domain_owner": (
            "tools/independent_validate_qku_computation_control_plane_quantum.py"
        ),
        "evidence_tier": EVIDENCE_TIER,
        "independence_class": (
            PRODUCTION_SYSTEM_UNDER_TEST_WITH_INDEPENDENT_EXPECTED_RESULT
        ),
        "production_expected_value_import_count": 0,
        "production_oracle_call_count": 0,
        "external_effect_count": 0,
        "terminal_state": TERMINAL_STATE,
    }
    return (
        IndependentMathRowEvidenceV1(
            math_id="MATH-50",
            oracle_id="ORACLE::MATH-50",
            golden_vector_id="GOLDEN::MATH-50",
            comparison_policy=str(rows["MATH-50"]["comparison"]),
            observed_result=observed_result(
                independent_observation=independent50,
                independent_expected_result=rows["MATH-50"]["expected"],  # type: ignore[arg-type]
                system_under_test_observation=sut50,
                comparison_passed=True,
            ),
            boundary_or_invariant_observation=evidence_observation(
                "ORIGINAL_MODEL_FEASIBLE_WINNER_SELECTION",
                "INVARIANT_PASS",
                {
                    "infeasible_high_utility_candidate": "11",
                    "selected_candidate_id": independent50["selected_candidate_id"],
                    "selected_original_model_feasible": True,
                },
            ),
            negative_or_abstention_observation=evidence_observation(
                "INCOMPLETE_QAOA_TRACE_REJECTION",
                "TYPED_REJECTION",
                incomplete50,
            ),
            formula_or_procedure_mutation_observation=evidence_observation(
                "WEIGHTED_QAOA_TRACE_RECOMPUTATION_MUTATION",
                "OBSERVED_OUTPUT_CHANGE",
                {
                    "input_paths": [["trace_weights", "00"], ["trace_weights", "01"]],
                    "baseline_result": independent50,
                    "mutated_result": formula50,
                },
            ),
            domain_guard_observation=evidence_observation(
                "NONNEGATIVE_NORMALIZED_TRACE_WEIGHT_GUARD",
                "TYPED_REJECTION",
                negative50,
            ),
            precision_or_tolerance_observation=evidence_observation(
                "EXACT_DECIMAL_TRACE_WEIGHT_PRECISION_MUTATION",
                "OBSERVED_OUTPUT_CHANGE",
                {"baseline_result": independent50, "mutated_result": precision50},
            ),
            source_unit_or_binding_observation=evidence_observation(
                "QAOA_INPUT_LOCK_AND_IMMUTABLE_BASIS_MUTATION",
                "TYPED_REJECTION",
                {"input_lock_rejection": lock50, "basis_rejection": basis50},
            ),
            production_system_under_test_invocation_count=4,
            **common,
        ),
        IndependentMathRowEvidenceV1(
            math_id="MATH-51",
            oracle_id="ORACLE::MATH-51",
            golden_vector_id="GOLDEN::MATH-51",
            comparison_policy=str(rows["MATH-51"]["comparison"]),
            observed_result=observed_result(
                independent_observation=independent51,
                independent_expected_result=rows["MATH-51"]["expected"],  # type: ignore[arg-type]
                system_under_test_observation=sut51,
                comparison_passed=True,
            ),
            boundary_or_invariant_observation=evidence_observation(
                "SELECTED_EXPECTATION_AND_VARIANCE_RECOMPUTATION",
                "INVARIANT_PASS",
                {
                    "selected_point_id": independent51["selected_candidate_id"],
                    "selected_expectation": independent51["trace_expectation"],
                    "selected_variance": independent51["variance"],
                    "original_model_feasible": True,
                },
            ),
            negative_or_abstention_observation=evidence_observation(
                "INCOMPLETE_VQE_TRACE_REJECTION",
                "TYPED_REJECTION",
                incomplete51,
            ),
            formula_or_procedure_mutation_observation=evidence_observation(
                "SELECTED_VQE_EXPECTATION_MUTATION",
                "OBSERVED_OUTPUT_CHANGE",
                {"baseline_result": independent51, "mutated_result": formula51},
            ),
            domain_guard_observation=evidence_observation(
                "NONNEGATIVE_VARIANCE_GUARD",
                "TYPED_REJECTION",
                negative51,
            ),
            precision_or_tolerance_observation=evidence_observation(
                "EXACT_DECIMAL_EXPECTATION_PRECISION_MUTATION",
                "OBSERVED_OUTPUT_CHANGE",
                {"baseline_result": independent51, "mutated_result": precision51},
            ),
            source_unit_or_binding_observation=evidence_observation(
                "VQE_INPUT_LOCK_AND_IMMUTABLE_BASIS_MUTATION",
                "TYPED_REJECTION",
                {"input_lock_rejection": lock51, "basis_rejection": basis51},
            ),
            production_system_under_test_invocation_count=4,
            **common,
        ),
        IndependentMathRowEvidenceV1(
            math_id="MATH-52",
            oracle_id="ORACLE::MATH-52",
            golden_vector_id="GOLDEN::MATH-52",
            comparison_policy=str(rows["MATH-52"]["comparison"]),
            observed_result=observed_result(
                independent_observation=independent52,
                independent_expected_result=rows["MATH-52"]["expected"],  # type: ignore[arg-type]
                system_under_test_observation=sut52,
                comparison_passed=True,
            ),
            boundary_or_invariant_observation=evidence_observation(
                "PERMANENT_NO_TRADE_CONSERVATIVE_TIE_BOUNDARY",
                "BOUNDARY_PASS",
                {"tied_comparator_result": tie52, "quantum_advantage_claim": False},
            ),
            negative_or_abstention_observation=evidence_observation(
                "PERMANENT_NO_TRADE_FEASIBILITY_REJECTION",
                "TYPED_REJECTION",
                negative52,
            ),
            formula_or_procedure_mutation_observation=evidence_observation(
                "CONSERVATIVE_UTILITY_WINNER_MUTATION",
                "OBSERVED_OUTPUT_CHANGE",
                {"baseline_result": independent52, "mutated_result": formula52},
            ),
            domain_guard_observation=evidence_observation(
                "PERMANENT_NO_TRADE_DOMAIN_GUARD",
                "TYPED_REJECTION",
                negative52,
            ),
            precision_or_tolerance_observation=evidence_observation(
                "EXACT_DECIMAL_UTILITY_PRECISION_MUTATION",
                "OBSERVED_OUTPUT_CHANGE",
                {"baseline_result": independent52, "mutated_result": precision52},
            ),
            source_unit_or_binding_observation=evidence_observation(
                "ELEVEN_DIMENSION_SAME_LOCK_BASIS_MUTATION_MATRIX",
                "TYPED_REJECTION",
                basis_rejections,
            ),
            production_system_under_test_invocation_count=12,
            **common,
        ),
    )
def main() -> int:
    try:
        receipt_rows = _build_quantum_receipt_rows()
    except (AssertionError, ContractValidationError, KeyError, TypeError, ValueError) as exc:
        print(f"QKU_QUANTUM_ROW_EVIDENCE_FAILED: {exc}", file=sys.stderr)
        return 1

    service = QuantumBenchmarkServiceV1()
    qaoa = _qaoa()
    vqe = _vqe()
    q_receipt = service.validate_qaoa_trace(qaoa)
    v_receipt = service.validate_vqe_trace(vqe)

    # These expected values are reconstructed here from raw supplied traces;
    # they are not read from a production result or a generated projection.
    independent_qaoa_trace_cost = sum(
        point.trace_weight * point.locked_cost for point in qaoa.points
    )
    independent_qaoa_winner = sorted(
        (point for point in qaoa.points if point.original_model_feasible),
        key=lambda point: (-point.original_economic_utility, point.candidate_id),
    )[0]
    independent_vqe_winner = sorted(
        (point for point in vqe.points if point.original_model_feasible),
        key=lambda point: (
            -point.original_economic_utility,
            point.parameter_point_id,
        ),
    )[0]

    basis_mutations: tuple[tuple[str, object], ...] = (
        ("input_lock_id", "L::OTHER"),
        ("original_formulation_id", "F::OTHER"),
        ("objective_sense", "MINIMIZE"),
        ("constraint_refs", ("CONSTRAINT::OTHER",)),
        ("accounting_basis_ref", "ACCOUNTING::OTHER"),
        ("cost_basis_ref", "COST::OTHER"),
        ("capacity_basis_ref", "CAPACITY::OTHER"),
        ("scenario_set_ref", "SCENARIO::OTHER"),
        ("resource_budget_ref", "RESOURCE::OTHER"),
        ("ttl_policy_ref", "TTL::OTHER"),
        ("version_epoch_pins", ("VERSION::OTHER",)),
    )
    rejected_dimensions: list[str] = []
    for field_name, value in basis_mutations:
        try:
            service.compare_same_lock(
                comparison_id=f"MISMATCH::{field_name}",
                quantum_receipt=q_receipt,
                strongest_classical_receipt=_comparator(
                    "STRONGEST_CLASSICAL",
                    basis=replace(_basis(), **{field_name: value}),
                ),
                no_trade_receipt=_comparator(
                    "NO_TRADE", utility="0", resource_use="0", latency="0"
                ),
            )
        except ContractValidationError as exc:
            expected = (
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH
                if field_name == "input_lock_id"
                else ReasonCode.ST12F_QUANTUM_TRACE_INVALID
            )
            if exc.reason_code is expected:
                rejected_dimensions.append(field_name)

    infeasible_a = replace(
        qaoa.points[0], original_model_feasible=False, original_economic_utility=Decimal("9")
    )
    feasible_only = service.validate_qaoa_trace(
        replace(qaoa, points=(infeasible_a, qaoa.points[1]))
    )
    infeasible_selection_rejected = False
    try:
        service.validate_qaoa_trace(
            replace(
                qaoa,
                points=(infeasible_a, qaoa.points[1]),
                selected_candidate_id="A",
            )
        )
    except ContractValidationError as exc:
        infeasible_selection_rejected = (
            exc.reason_code is ReasonCode.ST12F_QUANTUM_TRACE_INVALID
        )
    tie = service.compare_same_lock(
        comparison_id="CONSERVATIVE::TIE",
        quantum_receipt=q_receipt,
        strongest_classical_receipt=_comparator(
            "STRONGEST_CLASSICAL",
            utility="0.7",
            resource_use="1",
            latency="1",
        ),
        no_trade_receipt=_comparator(
            "NO_TRADE", utility="0.7", resource_use="1", latency="1"
        ),
    )
    no_trade_rejections = 0
    for feasible, hard_veto in ((False, False), (True, True)):
        try:
            _comparator(
                "NO_TRADE",
                utility="0",
                resource_use="0",
                latency="0",
                feasible=feasible,
                hard_veto=hard_veto,
            )
        except ContractValidationError as exc:
            if exc.reason_code is ReasonCode.ST12F_QUANTUM_TRACE_INVALID:
                no_trade_rejections += 1

    source = (
        ROOT
        / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_benchmark.py"
    ).read_text(encoding="utf-8")
    forbidden_calls = (
        "Estimator(", "Sampler(", "transpile(", ".run(",
        "AerSimulator(", "provider.", "qpu.",
    )
    checks = (
        q_receipt.recomputed_objective == independent_qaoa_trace_cost,
        q_receipt.selected_candidate_id == independent_qaoa_winner.candidate_id,
        q_receipt.original_economic_utility
        == independent_qaoa_winner.original_economic_utility,
        v_receipt.recomputed_objective == independent_vqe_winner.expectation,
        v_receipt.recomputed_variance_or_explicit_absence
        == independent_vqe_winner.variance,
        v_receipt.original_economic_utility
        == independent_vqe_winner.original_economic_utility,
        feasible_only.selected_candidate_id == "B",
        infeasible_selection_rejected,
        tuple(rejected_dimensions)
        == tuple(field_name for field_name, _ in basis_mutations),
        tie.winner == "NO_TRADE",
        tie.quantum_advantage_claim_allowed is False,
        no_trade_rejections == 2,
        not any(token in source for token in forbidden_calls),
        set(q_receipt.effect_counts.values()) == {0},
    )
    if not all(checks):
        print("QKU_QUANTUM_INDEPENDENT_VALIDATION_FAILED", file=sys.stderr)
        return 1
    print(format_evidence_line(build_envelope("QUANTUM", receipt_rows)))
    print(
        "QKU_QUANTUM_INDEPENDENTLY_VALIDATED "
        "checks=14 trace_only=3 math52_basis_dimensions=11 effect_calls=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
