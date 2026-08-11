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
class QuantumEconomicBasisV1:
    input_lock_id: str
    original_formulation_id: str
    objective_sense: str
    constraint_refs: tuple[str, ...]
    accounting_basis_ref: str
    cost_basis_ref: str
    capacity_basis_ref: str
    scenario_set_ref: str
    resource_budget_ref: str
    ttl_policy_ref: str
    version_epoch_pins: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "input_lock_id",
            "original_formulation_id",
            "objective_sense",
            "accounting_basis_ref",
            "cost_basis_ref",
            "capacity_basis_ref",
            "scenario_set_ref",
            "resource_budget_ref",
            "ttl_policy_ref",
        ):
            _text(getattr(self, name), name)
        _refs(self.constraint_refs, "constraint_refs")
        _refs(self.version_epoch_pins, "version_epoch_pins")
        if (
            not self.constraint_refs
            or not self.version_epoch_pins
            or self.objective_sense not in {"MAXIMIZE", "MINIMIZE"}
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "economic comparison basis requires constraints, pins, and exact objective sense",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "QuantumEconomicBasisV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "quantum economic-basis fields differ",
            )
        payload = dict(value)
        payload["constraint_refs"] = tuple(payload["constraint_refs"])
        payload["version_epoch_pins"] = tuple(payload["version_epoch_pins"])
        return cls(**payload)

    def as_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                field.name: getattr(self, field.name)
                for field in fields(type(self))
            }
        )


@dataclass(frozen=True, slots=True)
class EconomicComparatorReceiptV1:
    receipt_id: str
    comparator_class: str
    comparison_basis: QuantumEconomicBasisV1
    feasible: bool
    hard_veto: bool
    conservative_utility: Decimal
    resource_use: Decimal
    latency: Decimal
    deterministic_tie_break: str

    def __post_init__(self) -> None:
        _text(self.receipt_id, "receipt_id")
        _text(self.deterministic_tie_break, "deterministic_tie_break")
        if self.comparator_class not in {
            "VALIDATED_QUANTUM",
            "STRONGEST_CLASSICAL",
            "NO_TRADE",
        } or type(self.comparison_basis) is not QuantumEconomicBasisV1:
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "economic comparator class or basis is invalid",
            )
        if type(self.feasible) is not bool or type(self.hard_veto) is not bool:
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "economic comparator feasibility and veto must be exact booleans",
            )
        if self.comparator_class == "NO_TRADE" and (
            self.feasible is not True or self.hard_veto is not False
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "permanent NO_TRADE must remain feasible and free of a hard veto",
            )
        for name in ("conservative_utility", "resource_use", "latency"):
            value = exact_decimal(getattr(self, name), field_name=name)
            if name != "conservative_utility" and value < 0:
                raise ContractValidationError(
                    ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                    f"{name} must be nonnegative",
                )
            object.__setattr__(self, name, value)

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "EconomicComparatorReceiptV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "economic comparator receipt fields differ",
            )
        payload = dict(value)
        payload["comparison_basis"] = QuantumEconomicBasisV1.from_canonical_mapping(
            payload["comparison_basis"]
        )
        return cls(**payload)

    def as_math_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "comparator_class": self.comparator_class,
                "feasible": self.feasible,
                "hard_veto": self.hard_veto,
                "conservative_utility": self.conservative_utility,
                "resource_use": self.resource_use,
                "latency": self.latency,
                "deterministic_tie_break": self.deterministic_tie_break,
            }
        )


def _comparator_rank(row: EconomicComparatorReceiptV1) -> tuple[object, ...]:
    conservative_priority = {
        "NO_TRADE": 0,
        "STRONGEST_CLASSICAL": 1,
        "VALIDATED_QUANTUM": 2,
    }
    return (
        0 if row.feasible and not row.hard_veto else 1,
        -row.conservative_utility,
        row.resource_use,
        row.latency,
        conservative_priority[row.comparator_class],
        row.deterministic_tie_break,
    )


@dataclass(frozen=True, slots=True)
class QAOATracePointV1:
    candidate_id: str
    trace_weight: Decimal
    locked_cost: Decimal
    original_model_feasible: bool
    original_economic_utility: Decimal
    resource_use: Decimal
    latency: Decimal

    def __post_init__(self) -> None:
        _text(self.candidate_id, "candidate_id")
        object.__setattr__(self, "trace_weight", exact_decimal(self.trace_weight, field_name="trace_weight"))
        object.__setattr__(self, "locked_cost", exact_decimal(self.locked_cost, field_name="locked_cost"))
        object.__setattr__(self, "original_economic_utility", exact_decimal(self.original_economic_utility, field_name="original_economic_utility"))
        object.__setattr__(self, "resource_use", exact_decimal(self.resource_use, field_name="resource_use"))
        object.__setattr__(self, "latency", exact_decimal(self.latency, field_name="latency"))
        if (
            self.trace_weight < 0
            or self.resource_use < 0
            or self.latency < 0
            or type(self.original_model_feasible) is not bool
        ):
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
    objective_sense: str
    parameter_order: tuple[str, ...]
    seed_policy_ref: str
    bounds_ref: str
    constraint_refs: tuple[str, ...]
    comparison_basis: QuantumEconomicBasisV1
    points: tuple[QAOATracePointV1, ...]
    selected_candidate_id: str
    strongest_classical_receipt_ref: str
    no_trade_receipt_ref: str
    strongest_classical_comparator: EconomicComparatorReceiptV1
    no_trade_comparator: EconomicComparatorReceiptV1
    trace_complete: bool
    original_model_interpret_back_valid: bool

    def __post_init__(self) -> None:
        for name in (
            "trace_id",
            "input_lock_id",
            "formulation_id",
            "objective_id",
            "objective_sense",
            "seed_policy_ref",
            "bounds_ref",
            "selected_candidate_id",
            "strongest_classical_receipt_ref",
            "no_trade_receipt_ref",
        ):
            _text(getattr(self, name), name)
        _refs(self.parameter_order, "parameter_order")
        _refs(self.constraint_refs, "constraint_refs")
        if (
            not self.parameter_order
            or not self.constraint_refs
            or not self.points
            or any(type(point) is not QAOATracePointV1 for point in self.points)
            or len({point.candidate_id for point in self.points}) != len(self.points)
            or type(self.trace_complete) is not bool
            or type(self.original_model_interpret_back_valid) is not bool
            or type(self.comparison_basis) is not QuantumEconomicBasisV1
            or type(self.strongest_classical_comparator) is not EconomicComparatorReceiptV1
            or type(self.no_trade_comparator) is not EconomicComparatorReceiptV1
            or self.objective_sense not in {"MAXIMIZE", "MINIMIZE"}
            or self.comparison_basis.input_lock_id != self.input_lock_id
            or self.comparison_basis.original_formulation_id != self.formulation_id
            or self.comparison_basis.objective_sense != self.objective_sense
            or self.comparison_basis.constraint_refs != self.constraint_refs
            or self.strongest_classical_comparator.comparator_class != "STRONGEST_CLASSICAL"
            or self.no_trade_comparator.comparator_class != "NO_TRADE"
            or self.strongest_classical_comparator.receipt_id != self.strongest_classical_receipt_ref
            or self.no_trade_comparator.receipt_id != self.no_trade_receipt_ref
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
    locked_cost: Decimal
    original_model_feasible: bool
    original_economic_utility: Decimal
    resource_use: Decimal
    latency: Decimal

    def __post_init__(self) -> None:
        _text(self.parameter_point_id, "parameter_point_id")
        object.__setattr__(self, "expectation", exact_decimal(self.expectation, field_name="expectation"))
        object.__setattr__(self, "variance", exact_decimal(self.variance, field_name="variance"))
        object.__setattr__(self, "locked_cost", exact_decimal(self.locked_cost, field_name="locked_cost"))
        object.__setattr__(self, "original_economic_utility", exact_decimal(self.original_economic_utility, field_name="original_economic_utility"))
        object.__setattr__(self, "resource_use", exact_decimal(self.resource_use, field_name="resource_use"))
        object.__setattr__(self, "latency", exact_decimal(self.latency, field_name="latency"))
        if (
            self.variance < 0
            or self.resource_use < 0
            or self.latency < 0
            or type(self.original_model_feasible) is not bool
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "VQE trace points require nonnegative variance and typed feasibility",
            )


@dataclass(frozen=True, slots=True)
class VQEPreexistingTraceV1:
    trace_id: str
    input_lock_id: str
    formulation_id: str
    objective_sense: str
    hamiltonian_id: str
    ansatz_metadata_ref: str
    parameter_order: tuple[str, ...]
    optimizer_metadata_ref: str
    seed_policy_ref: str
    bounds_ref: str
    constraint_refs: tuple[str, ...]
    comparison_basis: QuantumEconomicBasisV1
    points: tuple[VQETracePointV1, ...]
    selected_point_id: str
    strongest_classical_receipt_ref: str
    no_trade_receipt_ref: str
    strongest_classical_comparator: EconomicComparatorReceiptV1
    no_trade_comparator: EconomicComparatorReceiptV1
    trace_complete: bool
    original_model_interpret_back_valid: bool

    def __post_init__(self) -> None:
        for name in (
            "trace_id",
            "input_lock_id",
            "formulation_id",
            "objective_sense",
            "hamiltonian_id",
            "ansatz_metadata_ref",
            "optimizer_metadata_ref",
            "seed_policy_ref",
            "bounds_ref",
            "selected_point_id",
            "strongest_classical_receipt_ref",
            "no_trade_receipt_ref",
        ):
            _text(getattr(self, name), name)
        _refs(self.parameter_order, "parameter_order")
        _refs(self.constraint_refs, "constraint_refs")
        if (
            not self.parameter_order
            or not self.constraint_refs
            or not self.points
            or any(type(point) is not VQETracePointV1 for point in self.points)
            or len({point.parameter_point_id for point in self.points}) != len(self.points)
            or type(self.trace_complete) is not bool
            or type(self.original_model_interpret_back_valid) is not bool
            or type(self.comparison_basis) is not QuantumEconomicBasisV1
            or type(self.strongest_classical_comparator) is not EconomicComparatorReceiptV1
            or type(self.no_trade_comparator) is not EconomicComparatorReceiptV1
            or self.objective_sense not in {"MAXIMIZE", "MINIMIZE"}
            or self.comparison_basis.input_lock_id != self.input_lock_id
            or self.comparison_basis.original_formulation_id != self.formulation_id
            or self.comparison_basis.objective_sense != self.objective_sense
            or self.comparison_basis.constraint_refs != self.constraint_refs
            or self.strongest_classical_comparator.comparator_class != "STRONGEST_CLASSICAL"
            or self.no_trade_comparator.comparator_class != "NO_TRADE"
            or self.strongest_classical_comparator.receipt_id != self.strongest_classical_receipt_ref
            or self.no_trade_comparator.receipt_id != self.no_trade_receipt_ref
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
    comparison_basis: QuantumEconomicBasisV1
    selected_candidate_id: str
    recomputed_objective: Decimal
    recomputed_variance_or_explicit_absence: Decimal | str
    selected_original_model_feasible: bool
    selected_hard_veto: bool
    original_model_interpret_back_valid: bool
    strongest_classical_receipt_ref: str
    no_trade_receipt_ref: str
    original_economic_utility: Decimal
    resource_use: Decimal
    latency: Decimal
    deterministic_tie_break: str
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
            "deterministic_tie_break",
            "strongest_classical_receipt_ref",
            "no_trade_receipt_ref",
            "terminal_state",
        ):
            _text(getattr(self, name), name)
        if self.schema_version != "QTT_ST12F_QUANTUM_TRACE_VALIDATION_V1_4" or self.contract_version != "1.4" or self.math_spec_id not in {"MATH-50", "MATH-51"}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "quantum receipt schema differs")
        object.__setattr__(self, "recomputed_objective", exact_decimal(self.recomputed_objective, field_name="recomputed_objective"))
        object.__setattr__(self, "original_economic_utility", exact_decimal(self.original_economic_utility, field_name="original_economic_utility"))
        object.__setattr__(self, "resource_use", exact_decimal(self.resource_use, field_name="resource_use"))
        object.__setattr__(self, "latency", exact_decimal(self.latency, field_name="latency"))
        if self.recomputed_variance_or_explicit_absence != "EXPLICIT_ABSENCE":
            object.__setattr__(self, "recomputed_variance_or_explicit_absence", exact_decimal(self.recomputed_variance_or_explicit_absence, field_name="recomputed_variance"))
        if (
            type(self.selected_original_model_feasible) is not bool
            or not self.selected_original_model_feasible
            or type(self.selected_hard_veto) is not bool
            or self.selected_hard_veto
            or type(self.original_model_interpret_back_valid) is not bool
            or not self.original_model_interpret_back_valid
            or type(self.quantum_advantage_claim_allowed) is not bool
            or self.quantum_advantage_claim_allowed
            or dict(self.effect_counts) != dict(_ZERO_EFFECT_COUNTS)
            or self.terminal_state != "VALIDATED_TRACE_ONLY"
            or type(self.comparison_basis) is not QuantumEconomicBasisV1
            or self.comparison_basis.input_lock_id != self.input_lock_id
            or self.comparison_basis.original_formulation_id != self.formulation_id
            or self.resource_use < 0
            or self.latency < 0
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
        payload = dict(value)
        payload["comparison_basis"] = QuantumEconomicBasisV1.from_canonical_mapping(
            payload["comparison_basis"]
        )
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)

    def as_comparator(self) -> EconomicComparatorReceiptV1:
        return EconomicComparatorReceiptV1(
            receipt_id=self.receipt_id,
            comparator_class="VALIDATED_QUANTUM",
            comparison_basis=self.comparison_basis,
            feasible=self.selected_original_model_feasible,
            hard_veto=self.selected_hard_veto,
            conservative_utility=self.original_economic_utility,
            resource_use=self.resource_use,
            latency=self.latency,
            deterministic_tie_break=self.deterministic_tie_break,
        )


@dataclass(frozen=True, slots=True)
class QuantumClassicalNoTradeComparisonV1:
    comparison_id: str
    input_lock_id: str
    formulation_id: str
    comparison_basis: QuantumEconomicBasisV1
    validated_quantum: EconomicComparatorReceiptV1
    strongest_classical: EconomicComparatorReceiptV1
    no_trade: EconomicComparatorReceiptV1
    validated_quantum_receipt_ref: str
    strongest_classical_receipt_ref: str
    no_trade_receipt_ref: str
    quantum_utility: Decimal
    strongest_classical_utility: Decimal
    no_trade_utility: Decimal
    delta_quantum_vs_classical: Decimal
    delta_quantum_vs_no_trade: Decimal
    winner: str
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
        comparators = (
            self.validated_quantum,
            self.strongest_classical,
            self.no_trade,
        )
        if (
            self.quantum_advantage_claim_allowed
            or type(self.comparison_basis) is not QuantumEconomicBasisV1
            or any(type(row) is not EconomicComparatorReceiptV1 for row in comparators)
            or tuple(row.comparator_class for row in comparators)
            != ("VALIDATED_QUANTUM", "STRONGEST_CLASSICAL", "NO_TRADE")
            or any(row.comparison_basis != self.comparison_basis for row in comparators)
            or self.input_lock_id != self.comparison_basis.input_lock_id
            or self.formulation_id != self.comparison_basis.original_formulation_id
            or self.validated_quantum_receipt_ref != self.validated_quantum.receipt_id
            or self.strongest_classical_receipt_ref != self.strongest_classical.receipt_id
            or self.no_trade_receipt_ref != self.no_trade.receipt_id
            or self.quantum_utility != self.validated_quantum.conservative_utility
            or self.strongest_classical_utility != self.strongest_classical.conservative_utility
            or self.no_trade_utility != self.no_trade.conservative_utility
            or self.delta_quantum_vs_classical != self.quantum_utility - self.strongest_classical_utility
            or self.delta_quantum_vs_no_trade != self.quantum_utility - self.no_trade_utility
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "quantum comparison requires one exact lock and arithmetic basis",
            )
        expected = min(comparators, key=_comparator_rank).comparator_class
        if self.winner != expected:
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "comparison winner differs from deterministic same-basis utility",
            )

    @classmethod
    def from_canonical_mapping(
        cls, value: object
    ) -> "QuantumClassicalNoTradeComparisonV1":
        if not isinstance(value, Mapping) or set(value) != {
            field.name for field in fields(cls)
        }:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "quantum comparison payload fields differ",
            )
        payload = dict(value)
        payload["comparison_basis"] = QuantumEconomicBasisV1.from_canonical_mapping(
            payload["comparison_basis"]
        )
        for name in ("validated_quantum", "strongest_classical", "no_trade"):
            payload[name] = EconomicComparatorReceiptV1.from_canonical_mapping(
                payload[name]
            )
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


class QuantumBenchmarkServiceV1:
    """Consumes pre-existing traces and deterministic comparators only."""

    def validate_qaoa_trace(
        self, trace: QAOAPreexistingTraceV1
    ) -> QuantumTraceValidationReceiptV1:
        if type(trace) is not QAOAPreexistingTraceV1 or not trace.trace_complete or not trace.original_model_interpret_back_valid:
            raise ContractValidationError(ReasonCode.ST12F_QUANTUM_TRACE_INVALID, "QAOA trace is not complete")
        result = get_st12f_evidence_math_callable_v1("MATH-50")(
            input_lock_id=trace.input_lock_id,
            formulation_id=trace.formulation_id,
            objective_id=trace.objective_id,
            parameter_order=trace.parameter_order,
            seed_policy_ref=trace.seed_policy_ref,
            bounds_ref=trace.bounds_ref,
            constraint_refs=trace.constraint_refs,
            trace_complete=trace.trace_complete,
            original_model_interpret_back_valid=trace.original_model_interpret_back_valid,
            trace_weights={point.candidate_id: point.trace_weight for point in trace.points},
            locked_costs={point.candidate_id: point.locked_cost for point in trace.points},
            observed_feasibility={point.candidate_id: point.original_model_feasible for point in trace.points},
            original_economic_utilities={point.candidate_id: point.original_economic_utility for point in trace.points},
            resource_use={point.candidate_id: point.resource_use for point in trace.points},
            latency={point.candidate_id: point.latency for point in trace.points},
            selected_candidate_id=trace.selected_candidate_id,
            objective_sense=trace.objective_sense,
            quantum_basis=trace.comparison_basis.as_mapping(),
            strongest_classical_basis=trace.strongest_classical_comparator.comparison_basis.as_mapping(),
            no_trade_basis=trace.no_trade_comparator.comparison_basis.as_mapping(),
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
            comparison_basis=trace.comparison_basis,
            selected_candidate_id=selected.candidate_id,
            recomputed_objective=result["trace_expected_locked_cost"],
            recomputed_variance_or_explicit_absence="EXPLICIT_ABSENCE",
            selected_original_model_feasible=selected.original_model_feasible,
            selected_hard_veto=False,
            original_model_interpret_back_valid=trace.original_model_interpret_back_valid,
            strongest_classical_receipt_ref=trace.strongest_classical_receipt_ref,
            no_trade_receipt_ref=trace.no_trade_receipt_ref,
            original_economic_utility=selected.original_economic_utility,
            resource_use=selected.resource_use,
            latency=selected.latency,
            deterministic_tie_break=selected.candidate_id,
            effect_counts=_ZERO_EFFECT_COUNTS,
            terminal_state="VALIDATED_TRACE_ONLY",
        )

    def validate_vqe_trace(
        self, trace: VQEPreexistingTraceV1
    ) -> QuantumTraceValidationReceiptV1:
        if type(trace) is not VQEPreexistingTraceV1 or not trace.trace_complete or not trace.original_model_interpret_back_valid:
            raise ContractValidationError(ReasonCode.ST12F_QUANTUM_TRACE_INVALID, "VQE trace is not complete")
        result = get_st12f_evidence_math_callable_v1("MATH-51")(
            input_lock_id=trace.input_lock_id,
            formulation_id=trace.formulation_id,
            hamiltonian_id=trace.hamiltonian_id,
            ansatz_metadata_ref=trace.ansatz_metadata_ref,
            parameter_order=trace.parameter_order,
            optimizer_metadata_ref=trace.optimizer_metadata_ref,
            seed_policy_ref=trace.seed_policy_ref,
            bounds_ref=trace.bounds_ref,
            constraint_refs=trace.constraint_refs,
            trace_complete=trace.trace_complete,
            original_model_interpret_back_valid=trace.original_model_interpret_back_valid,
            parameter_point_ids=tuple(point.parameter_point_id for point in trace.points),
            expectation_trace=tuple(point.expectation for point in trace.points),
            variance_trace=tuple(point.variance for point in trace.points),
            locked_costs=tuple(point.locked_cost for point in trace.points),
            original_economic_utilities=tuple(point.original_economic_utility for point in trace.points),
            observed_feasibility=tuple(point.original_model_feasible for point in trace.points),
            resource_use=tuple(point.resource_use for point in trace.points),
            latency=tuple(point.latency for point in trace.points),
            selected_point_id=trace.selected_point_id,
            objective_sense=trace.objective_sense,
            quantum_basis=trace.comparison_basis.as_mapping(),
            strongest_classical_basis=trace.strongest_classical_comparator.comparison_basis.as_mapping(),
            no_trade_basis=trace.no_trade_comparator.comparison_basis.as_mapping(),
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
            comparison_basis=trace.comparison_basis,
            selected_candidate_id=selected.parameter_point_id,
            recomputed_objective=result["trace_expectation"],
            recomputed_variance_or_explicit_absence=result["variance"],
            selected_original_model_feasible=selected.original_model_feasible,
            selected_hard_veto=False,
            original_model_interpret_back_valid=trace.original_model_interpret_back_valid,
            strongest_classical_receipt_ref=trace.strongest_classical_receipt_ref,
            no_trade_receipt_ref=trace.no_trade_receipt_ref,
            original_economic_utility=selected.original_economic_utility,
            resource_use=selected.resource_use,
            latency=selected.latency,
            deterministic_tie_break=selected.parameter_point_id,
            effect_counts=_ZERO_EFFECT_COUNTS,
            terminal_state="VALIDATED_TRACE_ONLY",
        )

    def compare_same_lock(
        self,
        *,
        comparison_id: str,
        quantum_receipt: QuantumTraceValidationReceiptV1,
        strongest_classical_receipt: EconomicComparatorReceiptV1,
        no_trade_receipt: EconomicComparatorReceiptV1,
    ) -> QuantumClassicalNoTradeComparisonV1:
        if (
            type(quantum_receipt) is not QuantumTraceValidationReceiptV1
            or type(strongest_classical_receipt) is not EconomicComparatorReceiptV1
            or type(no_trade_receipt) is not EconomicComparatorReceiptV1
            or strongest_classical_receipt.comparator_class != "STRONGEST_CLASSICAL"
            or no_trade_receipt.comparator_class != "NO_TRADE"
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                "quantum, classical, and NO_TRADE comparators must be exact typed receipts",
            )
        quantum_comparator = quantum_receipt.as_comparator()
        result = get_st12f_evidence_math_callable_v1("MATH-52")(
            quantum_basis=quantum_comparator.comparison_basis.as_mapping(),
            strongest_classical_basis=strongest_classical_receipt.comparison_basis.as_mapping(),
            no_trade_basis=no_trade_receipt.comparison_basis.as_mapping(),
            validated_quantum=quantum_comparator.as_math_mapping(),
            strongest_classical=strongest_classical_receipt.as_math_mapping(),
            no_trade=no_trade_receipt.as_math_mapping(),
        )
        return QuantumClassicalNoTradeComparisonV1(
            comparison_id=comparison_id,
            input_lock_id=quantum_receipt.input_lock_id,
            formulation_id=quantum_receipt.formulation_id,
            comparison_basis=quantum_receipt.comparison_basis,
            validated_quantum=quantum_comparator,
            strongest_classical=strongest_classical_receipt,
            no_trade=no_trade_receipt,
            validated_quantum_receipt_ref=quantum_receipt.receipt_id,
            strongest_classical_receipt_ref=strongest_classical_receipt.receipt_id,
            no_trade_receipt_ref=no_trade_receipt.receipt_id,
            quantum_utility=quantum_receipt.original_economic_utility,
            strongest_classical_utility=strongest_classical_receipt.conservative_utility,
            no_trade_utility=no_trade_receipt.conservative_utility,
            delta_quantum_vs_classical=result["delta_quantum_vs_classical"],
            delta_quantum_vs_no_trade=result["delta_quantum_vs_no_trade"],
            winner=result["winner"],
        )
