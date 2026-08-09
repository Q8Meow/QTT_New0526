"""Trace-only quantum evidence validation; it never executes an algorithm."""

from __future__ import annotations

from dataclasses import dataclass, fields
from decimal import Decimal
from types import MappingProxyType
from typing import Mapping

from .context import exact_decimal
from .errors import ContractValidationError, ReasonCode
from .implementation_registry import get_st12f_evidence_math_callable_v1
from .serialization import deterministic_json


_ZERO_EFFECT_COUNTS = MappingProxyType(
    {
        "ansatz_construction": 0,
        "optimizer": 0,
        "estimator": 0,
        "sampler": 0,
        "transpiler": 0,
        "simulator": 0,
        "provider": 0,
        "qpu": 0,
    }
)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            f"{name} must be canonical text",
        )
    return value


def _refs(value: object, name: str) -> tuple[str, ...]:
    if (
        not isinstance(value, tuple)
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            f"{name} must be a unique reference tuple",
        )
    return value


@dataclass(frozen=True, slots=True)
class QAOATracePointV1:
    candidate_id: str
    trace_weight: Decimal
    locked_cost: Decimal
    original_model_feasible: bool
    original_economic_utility: Decimal

    def __post_init__(self) -> None:
        _text(self.candidate_id, "candidate_id")
        object.__setattr__(self, "trace_weight", exact_decimal(self.trace_weight, field_name="trace_weight"))
        object.__setattr__(self, "locked_cost", exact_decimal(self.locked_cost, field_name="locked_cost"))
        object.__setattr__(self, "original_economic_utility", exact_decimal(self.original_economic_utility, field_name="original_economic_utility"))
        if self.trace_weight < 0 or type(self.original_model_feasible) is not bool:
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "QAOA trace points require nonnegative weights and typed feasibility",
            )


@dataclass(frozen=True, slots=True)
class QAOAPreexistingTraceV1:
    trace_id: str
    input_lock_id: str
    formulation_id: str
    objective_id: str
    parameter_order: tuple[str, ...]
    seed_policy_ref: str
    points: tuple[QAOATracePointV1, ...]
    selected_candidate_id: str
    strongest_classical_receipt_ref: str
    no_trade_receipt_ref: str
    trace_complete: bool
    original_model_interpret_back_valid: bool

    def __post_init__(self) -> None:
        for name in (
            "trace_id",
            "input_lock_id",
            "formulation_id",
            "objective_id",
            "seed_policy_ref",
            "selected_candidate_id",
            "strongest_classical_receipt_ref",
            "no_trade_receipt_ref",
        ):
            _text(getattr(self, name), name)
        _refs(self.parameter_order, "parameter_order")
        if (
            not self.points
            or any(type(point) is not QAOATracePointV1 for point in self.points)
            or len({point.candidate_id for point in self.points}) != len(self.points)
            or type(self.trace_complete) is not bool
            or type(self.original_model_interpret_back_valid) is not bool
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "QAOA trace is incomplete or structurally invalid",
            )


@dataclass(frozen=True, slots=True)
class VQETracePointV1:
    parameter_point_id: str
    expectation: Decimal
    variance: Decimal
    original_model_feasible: bool
    original_economic_utility: Decimal

    def __post_init__(self) -> None:
        _text(self.parameter_point_id, "parameter_point_id")
        object.__setattr__(self, "expectation", exact_decimal(self.expectation, field_name="expectation"))
        object.__setattr__(self, "variance", exact_decimal(self.variance, field_name="variance"))
        object.__setattr__(self, "original_economic_utility", exact_decimal(self.original_economic_utility, field_name="original_economic_utility"))
        if self.variance < 0 or type(self.original_model_feasible) is not bool:
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "VQE trace points require nonnegative variance and typed feasibility",
            )


@dataclass(frozen=True, slots=True)
class VQEPreexistingTraceV1:
    trace_id: str
    input_lock_id: str
    formulation_id: str
    hamiltonian_id: str
    ansatz_metadata_ref: str
    parameter_order: tuple[str, ...]
    optimizer_metadata_ref: str
    seed_policy_ref: str
    points: tuple[VQETracePointV1, ...]
    selected_point_id: str
    strongest_classical_receipt_ref: str
    no_trade_receipt_ref: str
    trace_complete: bool
    original_model_interpret_back_valid: bool

    def __post_init__(self) -> None:
        for name in (
            "trace_id",
            "input_lock_id",
            "formulation_id",
            "hamiltonian_id",
            "ansatz_metadata_ref",
            "optimizer_metadata_ref",
            "seed_policy_ref",
            "selected_point_id",
            "strongest_classical_receipt_ref",
            "no_trade_receipt_ref",
        ):
            _text(getattr(self, name), name)
        _refs(self.parameter_order, "parameter_order")
        if (
            not self.points
            or any(type(point) is not VQETracePointV1 for point in self.points)
            or len({point.parameter_point_id for point in self.points}) != len(self.points)
            or type(self.trace_complete) is not bool
            or type(self.original_model_interpret_back_valid) is not bool
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "VQE trace is incomplete or structurally invalid",
            )


@dataclass(frozen=True, slots=True)
class QuantumTraceValidationReceiptV1:
    receipt_id: str
    schema_version: str
    contract_version: str
    math_spec_id: str
    trace_id: str
    input_lock_id: str
    formulation_id: str
    selected_candidate_id: str
    recomputed_objective: Decimal
    recomputed_variance_or_explicit_absence: Decimal | str
    selected_original_model_feasible: bool
    original_model_interpret_back_valid: bool
    strongest_classical_receipt_ref: str
    no_trade_receipt_ref: str
    original_economic_utility: Decimal
    effect_counts: Mapping[str, int]
    terminal_state: str
    quantum_advantage_claim_allowed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "trace_id",
            "input_lock_id",
            "formulation_id",
            "selected_candidate_id",
            "strongest_classical_receipt_ref",
            "no_trade_receipt_ref",
            "terminal_state",
        ):
            _text(getattr(self, name), name)
        if self.schema_version != "QTT_ST12F_QUANTUM_TRACE_VALIDATION_V1_4" or self.contract_version != "1.4" or self.math_spec_id not in {"MATH-50", "MATH-51"}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "quantum receipt schema differs")
        object.__setattr__(self, "recomputed_objective", exact_decimal(self.recomputed_objective, field_name="recomputed_objective"))
        object.__setattr__(self, "original_economic_utility", exact_decimal(self.original_economic_utility, field_name="original_economic_utility"))
        if self.recomputed_variance_or_explicit_absence != "EXPLICIT_ABSENCE":
            object.__setattr__(self, "recomputed_variance_or_explicit_absence", exact_decimal(self.recomputed_variance_or_explicit_absence, field_name="recomputed_variance"))
        if (
            type(self.selected_original_model_feasible) is not bool
            or not self.selected_original_model_feasible
            or type(self.original_model_interpret_back_valid) is not bool
            or not self.original_model_interpret_back_valid
            or type(self.quantum_advantage_claim_allowed) is not bool
            or self.quantum_advantage_claim_allowed
            or dict(self.effect_counts) != dict(_ZERO_EFFECT_COUNTS)
            or self.terminal_state != "VALIDATED_TRACE_ONLY"
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "quantum evidence must be feasible trace-only validation with zero effects",
            )
        object.__setattr__(self, "effect_counts", _ZERO_EFFECT_COUNTS)

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "QuantumTraceValidationReceiptV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "quantum receipt payload fields differ")
        return cls(**dict(value))

    def canonical_json(self) -> str:
        return deterministic_json(self)


@dataclass(frozen=True, slots=True)
class QuantumClassicalNoTradeComparisonV1:
    comparison_id: str
    input_lock_id: str
    formulation_id: str
    validated_quantum_receipt_ref: str
    strongest_classical_receipt_ref: str
    no_trade_receipt_ref: str
    quantum_utility: Decimal
    strongest_classical_utility: Decimal
    no_trade_utility: Decimal
    delta_quantum_vs_classical: Decimal
    delta_quantum_vs_no_trade: Decimal
    winner: str
    same_locked_basis: bool
    quantum_advantage_claim_allowed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "comparison_id",
            "input_lock_id",
            "formulation_id",
            "validated_quantum_receipt_ref",
            "strongest_classical_receipt_ref",
            "no_trade_receipt_ref",
            "winner",
        ):
            _text(getattr(self, name), name)
        for name in (
            "quantum_utility",
            "strongest_classical_utility",
            "no_trade_utility",
            "delta_quantum_vs_classical",
            "delta_quantum_vs_no_trade",
        ):
            object.__setattr__(self, name, exact_decimal(getattr(self, name), field_name=name))
        if (
            not self.same_locked_basis
            or self.quantum_advantage_claim_allowed
            or self.delta_quantum_vs_classical != self.quantum_utility - self.strongest_classical_utility
            or self.delta_quantum_vs_no_trade != self.quantum_utility - self.no_trade_utility
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "quantum comparison requires one exact lock and arithmetic basis",
            )
        utilities = {
            "VALIDATED_QUANTUM": self.quantum_utility,
            "STRONGEST_CLASSICAL": self.strongest_classical_utility,
            "NO_TRADE": self.no_trade_utility,
        }
        expected = sorted(utilities, key=lambda key: (-utilities[key], key))[0]
        if self.winner != expected:
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "comparison winner differs from deterministic same-basis utility",
            )


class QuantumBenchmarkServiceV1:
    """Consumes pre-existing traces and deterministic comparators only."""

    def validate_qaoa_trace(
        self, trace: QAOAPreexistingTraceV1
    ) -> QuantumTraceValidationReceiptV1:
        if type(trace) is not QAOAPreexistingTraceV1 or not trace.trace_complete or not trace.original_model_interpret_back_valid:
            raise ContractValidationError(ReasonCode.ST12F_QUANTUM_TRACE_INVALID, "QAOA trace is not complete")
        result = get_st12f_evidence_math_callable_v1("MATH-50")(
            trace_weights={point.candidate_id: point.trace_weight for point in trace.points},
            locked_costs={point.candidate_id: point.locked_cost for point in trace.points},
            observed_feasibility={point.candidate_id: point.original_model_feasible for point in trace.points},
            same_lock=True,
        )
        selected = next((point for point in trace.points if point.candidate_id == result["selected_candidate_id"]), None)
        if selected is None or trace.selected_candidate_id != selected.candidate_id:
            raise ContractValidationError(ReasonCode.ST12F_QUANTUM_TRACE_INVALID, "QAOA selected candidate differs")
        return QuantumTraceValidationReceiptV1(
            receipt_id=f"ST12F-QUANTUM-TRACE::{trace.trace_id}",
            schema_version="QTT_ST12F_QUANTUM_TRACE_VALIDATION_V1_4",
            contract_version="1.4",
            math_spec_id="MATH-50",
            trace_id=trace.trace_id,
            input_lock_id=trace.input_lock_id,
            formulation_id=trace.formulation_id,
            selected_candidate_id=selected.candidate_id,
            recomputed_objective=result["expected_objective"],
            recomputed_variance_or_explicit_absence="EXPLICIT_ABSENCE",
            selected_original_model_feasible=selected.original_model_feasible,
            original_model_interpret_back_valid=trace.original_model_interpret_back_valid,
            strongest_classical_receipt_ref=trace.strongest_classical_receipt_ref,
            no_trade_receipt_ref=trace.no_trade_receipt_ref,
            original_economic_utility=selected.original_economic_utility,
            effect_counts=_ZERO_EFFECT_COUNTS,
            terminal_state="VALIDATED_TRACE_ONLY",
        )

    def validate_vqe_trace(
        self, trace: VQEPreexistingTraceV1
    ) -> QuantumTraceValidationReceiptV1:
        if type(trace) is not VQEPreexistingTraceV1 or not trace.trace_complete or not trace.original_model_interpret_back_valid:
            raise ContractValidationError(ReasonCode.ST12F_QUANTUM_TRACE_INVALID, "VQE trace is not complete")
        result = get_st12f_evidence_math_callable_v1("MATH-51")(
            parameter_point_ids=tuple(point.parameter_point_id for point in trace.points),
            expectation_trace=tuple(point.expectation for point in trace.points),
            variance_trace=tuple(point.variance for point in trace.points),
            selected_point_id=trace.selected_point_id,
            selected_original_model_feasible=next(
                (point.original_model_feasible for point in trace.points if point.parameter_point_id == trace.selected_point_id),
                False,
            ),
            same_lock=True,
        )
        selected = next((point for point in trace.points if point.parameter_point_id == result["selected_candidate_id"]), None)
        if selected is None:
            raise ContractValidationError(ReasonCode.ST12F_QUANTUM_TRACE_INVALID, "VQE selected point differs")
        return QuantumTraceValidationReceiptV1(
            receipt_id=f"ST12F-QUANTUM-TRACE::{trace.trace_id}",
            schema_version="QTT_ST12F_QUANTUM_TRACE_VALIDATION_V1_4",
            contract_version="1.4",
            math_spec_id="MATH-51",
            trace_id=trace.trace_id,
            input_lock_id=trace.input_lock_id,
            formulation_id=trace.formulation_id,
            selected_candidate_id=selected.parameter_point_id,
            recomputed_objective=result["expected_objective"],
            recomputed_variance_or_explicit_absence=result["variance"],
            selected_original_model_feasible=selected.original_model_feasible,
            original_model_interpret_back_valid=trace.original_model_interpret_back_valid,
            strongest_classical_receipt_ref=trace.strongest_classical_receipt_ref,
            no_trade_receipt_ref=trace.no_trade_receipt_ref,
            original_economic_utility=selected.original_economic_utility,
            effect_counts=_ZERO_EFFECT_COUNTS,
            terminal_state="VALIDATED_TRACE_ONLY",
        )

    def compare_same_lock(
        self,
        *,
        comparison_id: str,
        quantum_receipt: QuantumTraceValidationReceiptV1,
        strongest_classical_receipt_ref: str,
        strongest_classical_input_lock_id: str,
        strongest_classical_formulation_id: str,
        strongest_classical_utility: Decimal,
        no_trade_receipt_ref: str,
        no_trade_input_lock_id: str,
        no_trade_formulation_id: str,
        no_trade_utility: Decimal,
    ) -> QuantumClassicalNoTradeComparisonV1:
        if type(quantum_receipt) is not QuantumTraceValidationReceiptV1 or len({quantum_receipt.input_lock_id, strongest_classical_input_lock_id, no_trade_input_lock_id}) != 1 or len({quantum_receipt.formulation_id, strongest_classical_formulation_id, no_trade_formulation_id}) != 1:
            raise ContractValidationError(
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                "quantum, classical, and NO_TRADE comparators must share one exact lock and formulation",
            )
        result = get_st12f_evidence_math_callable_v1("MATH-52")(
            validated_quantum_utility=quantum_receipt.original_economic_utility,
            strongest_classical_utility=strongest_classical_utility,
            no_trade_utility=no_trade_utility,
            same_lock=True,
            same_cost_basis=True,
        )
        return QuantumClassicalNoTradeComparisonV1(
            comparison_id=comparison_id,
            input_lock_id=quantum_receipt.input_lock_id,
            formulation_id=quantum_receipt.formulation_id,
            validated_quantum_receipt_ref=quantum_receipt.receipt_id,
            strongest_classical_receipt_ref=strongest_classical_receipt_ref,
            no_trade_receipt_ref=no_trade_receipt_ref,
            quantum_utility=quantum_receipt.original_economic_utility,
            strongest_classical_utility=strongest_classical_utility,
            no_trade_utility=no_trade_utility,
            delta_quantum_vs_classical=result["delta_quantum_vs_classical"],
            delta_quantum_vs_no_trade=result["delta_quantum_vs_no_trade"],
            winner=result["winner"],
            same_locked_basis=True,
        )
