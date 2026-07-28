"""Registered deterministic fallback closure for pure computation failures."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping

from .errors import FallbackResolutionError, ReasonCode
from .implementation_registry import IMPLEMENTATION_REGISTRY
from .models import FallbackEnvelopeV1


_TERMINAL_TARGETS = frozenset(
    {
        "NO_TRADE",
        "SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE",
        "CLASSICAL_EQUIVALENT_OR_NO_TRADE",
    }
)


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FallbackResolutionError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be nonempty text",
        )
    return value


def _unique_text_tuple(values: object, field_name: str) -> tuple[str, ...]:
    if (
        not isinstance(values, tuple)
        or not values
        or any(not isinstance(value, str) or not value for value in values)
        or len(set(values)) != len(values)
    ):
        raise FallbackResolutionError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be a nonempty unique text tuple",
        )
    return values


@dataclass(frozen=True, slots=True)
class RegisteredFallbackV1:
    envelope: FallbackEnvelopeV1
    source_component_ids: tuple[str, ...]
    trigger_reason_codes: tuple[ReasonCode, ...]
    target_component_or_terminal: str
    input_compatibility: str
    output_semantic_mapping: str
    supplied_unit: str
    required_unit: str
    supplied_basis: str
    required_basis: str
    timing_compatibility: str
    freshness_compatibility: str
    mode_compatibility: tuple[str, ...]
    semantic_limitation: str
    consumer_scope: tuple[str, ...]
    receipt_requirements: tuple[str, ...]
    provider_read_allowed: bool = False
    private_state_allowed: bool = False
    llm_allowed: bool = False
    qpu_allowed: bool = False
    hidden_source_selection_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.envelope, FallbackEnvelopeV1):
            raise FallbackResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "fallback envelope must reuse FallbackEnvelopeV1",
            )
        for name in (
            "source_component_ids",
            "mode_compatibility",
            "consumer_scope",
            "receipt_requirements",
        ):
            _unique_text_tuple(getattr(self, name), name)
        if (
            not isinstance(self.trigger_reason_codes, tuple)
            or not self.trigger_reason_codes
            or any(
                not isinstance(value, ReasonCode)
                for value in self.trigger_reason_codes
            )
            or len(set(self.trigger_reason_codes))
            != len(self.trigger_reason_codes)
        ):
            raise FallbackResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "fallback triggers must be a unique typed reason-code tuple",
            )
        for name in (
            "target_component_or_terminal",
            "input_compatibility",
            "output_semantic_mapping",
            "supplied_unit",
            "required_unit",
            "supplied_basis",
            "required_basis",
            "timing_compatibility",
            "freshness_compatibility",
            "semantic_limitation",
        ):
            _required_text(getattr(self, name), name)
        effect_flags = (
            self.provider_read_allowed,
            self.private_state_allowed,
            self.llm_allowed,
            self.qpu_allowed,
            self.hidden_source_selection_allowed,
        )
        if any(type(value) is not bool for value in effect_flags) or any(
            effect_flags
        ):
            raise FallbackResolutionError(
                ReasonCode.CAPABILITY_DENIED,
                "fallbacks may not read providers/private state, call LLM/QPU, "
                "or select hidden sources",
            )
        if self.envelope.target != self.target_component_or_terminal:
            raise FallbackResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "fallback envelope target must equal the registered target",
            )

    @property
    def fallback_id(self) -> str:
        return self.envelope.fallback_id


@dataclass(frozen=True, slots=True)
class FallbackResolutionReceiptV1:
    receipt_id: str
    fallback_id: str
    source_component_id: str
    trigger_reason_code: ReasonCode
    resolved_target: str
    input_compatibility: str
    output_semantic_mapping: str
    timing_compatibility: str
    freshness_compatibility: str
    mode: str
    semantic_limitation: str
    consumer_ref: str
    no_write_effect: bool = True
    no_provider_effect: bool = True
    no_private_state_effect: bool = True
    no_llm_effect: bool = True
    no_qpu_effect: bool = True
    no_order_effect: bool = True

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "fallback_id",
            "source_component_id",
            "resolved_target",
            "input_compatibility",
            "output_semantic_mapping",
            "timing_compatibility",
            "freshness_compatibility",
            "mode",
            "semantic_limitation",
            "consumer_ref",
        ):
            _required_text(getattr(self, name), name)
        if not isinstance(self.trigger_reason_code, ReasonCode):
            raise FallbackResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "fallback receipt trigger must be typed",
            )
        flags = (
            self.no_write_effect,
            self.no_provider_effect,
            self.no_private_state_effect,
            self.no_llm_effect,
            self.no_qpu_effect,
            self.no_order_effect,
        )
        if any(type(value) is not bool for value in flags) or not all(flags):
            raise FallbackResolutionError(
                ReasonCode.CAPABILITY_DENIED,
                "fallback receipt must preserve every no-effect boundary",
            )


class RegisteredFallbackResolverV1:
    def __init__(
        self,
        fallbacks: tuple[RegisteredFallbackV1, ...],
    ) -> None:
        if (
            not isinstance(fallbacks, tuple)
            or not fallbacks
            or any(
                not isinstance(item, RegisteredFallbackV1)
                for item in fallbacks
            )
        ):
            raise FallbackResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "fallback registry must be a nonempty typed tuple",
            )
        ids = tuple(item.fallback_id for item in fallbacks)
        if len(ids) != len(set(ids)):
            raise FallbackResolutionError(
                ReasonCode.FALLBACK_INCOMPATIBLE,
                "fallback ids must be unique",
            )
        self._fallbacks = fallbacks
        self._by_id: Mapping[str, RegisteredFallbackV1] = MappingProxyType(
            {item.fallback_id: item for item in fallbacks}
        )
        self._assert_acyclic()

    @property
    def fallbacks(self) -> tuple[RegisteredFallbackV1, ...]:
        return self._fallbacks

    def _assert_acyclic(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(fallback_id: str) -> None:
            if fallback_id in visiting:
                raise FallbackResolutionError(
                    ReasonCode.FALLBACK_CYCLE,
                    "registered fallback graph contains a cycle",
                )
            if fallback_id in visited:
                return
            visiting.add(fallback_id)
            target = self._by_id[fallback_id].target_component_or_terminal
            if target.startswith("FALLBACK::"):
                if target not in self._by_id:
                    raise FallbackResolutionError(
                        ReasonCode.FALLBACK_UNKNOWN,
                        f"fallback target is not registered: {target}",
                    )
                visit(target)
            elif target not in _TERMINAL_TARGETS and target not in (
                IMPLEMENTATION_REGISTRY
            ):
                raise FallbackResolutionError(
                    ReasonCode.FALLBACK_UNKNOWN,
                    f"fallback target is neither a component nor terminal: {target}",
                )
            visiting.remove(fallback_id)
            visited.add(fallback_id)

        for fallback_id in self._by_id:
            visit(fallback_id)

    def get(self, fallback_id: str) -> RegisteredFallbackV1:
        _required_text(fallback_id, "fallback_id")
        try:
            return self._by_id[fallback_id]
        except KeyError as exc:
            raise FallbackResolutionError(
                ReasonCode.FALLBACK_UNKNOWN,
                f"unknown fallback id: {fallback_id}",
            ) from exc

    def resolve(
        self,
        *,
        fallback_id: str,
        source_component_id: str,
        trigger_reason_code: ReasonCode,
        supplied_unit: str,
        required_unit: str,
        supplied_basis: str,
        required_basis: str,
        timing_class: str,
        freshness_state: str,
        mode: str,
        consumer_ref: str,
    ) -> FallbackResolutionReceiptV1:
        fallback = self.get(fallback_id)
        if source_component_id not in fallback.source_component_ids:
            raise FallbackResolutionError(
                ReasonCode.FALLBACK_INCOMPATIBLE,
                "fallback is not registered for the source component",
            )
        if trigger_reason_code not in fallback.trigger_reason_codes:
            raise FallbackResolutionError(
                ReasonCode.FALLBACK_INCOMPATIBLE,
                "fallback is not registered for the trigger reason",
            )
        if mode not in fallback.mode_compatibility:
            raise FallbackResolutionError(
                ReasonCode.FALLBACK_INCOMPATIBLE,
                "fallback is not compatible with the requested mode",
            )
        if consumer_ref not in fallback.consumer_scope:
            raise FallbackResolutionError(
                ReasonCode.FALLBACK_INCOMPATIBLE,
                "fallback consumer is outside the registered scope",
            )
        if (supplied_unit, required_unit) != (
            fallback.supplied_unit,
            fallback.required_unit,
        ) or (supplied_basis, required_basis) != (
            fallback.supplied_basis,
            fallback.required_basis,
        ):
            raise FallbackResolutionError(
                ReasonCode.FALLBACK_INCOMPATIBLE,
                "fallback unit or basis compatibility differs",
            )
        if timing_class not in fallback.timing_compatibility.split("|"):
            raise FallbackResolutionError(
                ReasonCode.FALLBACK_INCOMPATIBLE,
                "fallback timing class is incompatible",
            )
        if freshness_state not in fallback.freshness_compatibility.split("|"):
            raise FallbackResolutionError(
                ReasonCode.FALLBACK_INCOMPATIBLE,
                "fallback freshness state is incompatible",
            )
        digest = "|".join(
            (
                fallback_id,
                source_component_id,
                trigger_reason_code.value,
                fallback.target_component_or_terminal,
                timing_class,
                freshness_state,
                mode,
                consumer_ref,
            )
        )
        return FallbackResolutionReceiptV1(
            receipt_id=f"FALLBACK::{sha256(digest.encode('utf-8')).hexdigest()}",
            fallback_id=fallback_id,
            source_component_id=source_component_id,
            trigger_reason_code=trigger_reason_code,
            resolved_target=fallback.target_component_or_terminal,
            input_compatibility=fallback.input_compatibility,
            output_semantic_mapping=fallback.output_semantic_mapping,
            timing_compatibility=fallback.timing_compatibility,
            freshness_compatibility=fallback.freshness_compatibility,
            mode=mode,
            semantic_limitation=fallback.semantic_limitation,
            consumer_ref=consumer_ref,
        )


CERTIFIED_FAIL_CLOSED_FALLBACK = RegisteredFallbackV1(
    envelope=FallbackEnvelopeV1(
        fallback_id="FALLBACK::NO_EFFECT_FAIL_CLOSED",
        reason_codes=tuple(
            code.value
            for code in (
                ReasonCode.REQUIRED_INPUT_MISSING,
                ReasonCode.REQUIRED_INPUT_STALE,
                ReasonCode.FIELD_STALE,
                ReasonCode.FRESHNESS_UNKNOWN,
                ReasonCode.POINT_IN_TIME_UNAVAILABLE,
                ReasonCode.REVISION_LEAKAGE,
                ReasonCode.SOURCE_EPOCH_MISSING,
                ReasonCode.SOURCE_EPOCH_STALE,
                ReasonCode.SOURCE_CONFLICT,
                ReasonCode.SOURCE_RIGHTS_BLOCKED,
                ReasonCode.SOURCE_BINDING_REQUIRED,
                ReasonCode.SOURCE_CLAIM_BINDING_MISMATCH,
                ReasonCode.INPUT_ORIGIN_NOT_AUTHORIZED,
                ReasonCode.DERIVED_LINEAGE_INVALID,
                ReasonCode.EXECUTION_REQUIREMENTS_UNRESOLVED,
                ReasonCode.PARAMETER_ASSERTION_MISMATCH,
                ReasonCode.PARAMETER_RUNTIME_BINDING_REQUIRED,
                ReasonCode.PARAMETER_APPLICATION_UNBOUND,
                ReasonCode.PARAMETER_EXPLICIT_FAIL_CLOSED,
                ReasonCode.PARAMETER_CALIBRATION_REQUIRED,
                ReasonCode.PARAMETER_NOT_EDITABLE,
                ReasonCode.PARAMETER_OUT_OF_POLICY,
                ReasonCode.OUT_OF_DOMAIN,
                ReasonCode.NONFINITE_NUMERIC_INPUT,
                ReasonCode.DEADLINE_EXHAUSTED,
                ReasonCode.STACK_NOT_COMPUTABLE,
                ReasonCode.STACK_NOT_APPLICABLE,
            )
        ),
        target="SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE",
    ),
    source_component_ids=tuple(IMPLEMENTATION_REGISTRY),
    trigger_reason_codes=(
        ReasonCode.REQUIRED_INPUT_MISSING,
        ReasonCode.REQUIRED_INPUT_STALE,
        ReasonCode.FIELD_STALE,
        ReasonCode.FRESHNESS_UNKNOWN,
        ReasonCode.POINT_IN_TIME_UNAVAILABLE,
        ReasonCode.REVISION_LEAKAGE,
        ReasonCode.SOURCE_EPOCH_MISSING,
        ReasonCode.SOURCE_EPOCH_STALE,
        ReasonCode.SOURCE_CONFLICT,
        ReasonCode.SOURCE_RIGHTS_BLOCKED,
        ReasonCode.SOURCE_BINDING_REQUIRED,
        ReasonCode.SOURCE_CLAIM_BINDING_MISMATCH,
        ReasonCode.INPUT_ORIGIN_NOT_AUTHORIZED,
        ReasonCode.DERIVED_LINEAGE_INVALID,
        ReasonCode.EXECUTION_REQUIREMENTS_UNRESOLVED,
        ReasonCode.PARAMETER_ASSERTION_MISMATCH,
        ReasonCode.PARAMETER_RUNTIME_BINDING_REQUIRED,
        ReasonCode.PARAMETER_APPLICATION_UNBOUND,
        ReasonCode.PARAMETER_EXPLICIT_FAIL_CLOSED,
        ReasonCode.PARAMETER_CALIBRATION_REQUIRED,
        ReasonCode.PARAMETER_NOT_EDITABLE,
        ReasonCode.PARAMETER_OUT_OF_POLICY,
        ReasonCode.OUT_OF_DOMAIN,
        ReasonCode.NONFINITE_NUMERIC_INPUT,
        ReasonCode.DEADLINE_EXHAUSTED,
        ReasonCode.STACK_NOT_COMPUTABLE,
        ReasonCode.STACK_NOT_APPLICABLE,
    ),
    target_component_or_terminal=(
        "SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE"
    ),
    input_compatibility="IDENTICAL_CERTIFIED_INPUT_SCHEMA_OR_TERMINAL_NO_TRADE",
    output_semantic_mapping=(
        "IDENTICAL_FORMULATION_WHEN_REFERENCE_EXISTS;"
        "EXPLICIT_CAPABILITY_REDUCTION_WHEN_NO_TRADE"
    ),
    supplied_unit="DECLARED",
    required_unit="DECLARED",
    supplied_basis="DECLARED",
    required_basis="DECLARED",
    timing_compatibility="POINT_IN_TIME|SNAPSHOT|NEARLINE|OFFLINE",
    freshness_compatibility="FRESH|STALE|UNKNOWN_FAIL_CLOSED",
    mode_compatibility=("CONTRACT_ONLY", "REPLAY", "PAPER"),
    semantic_limitation=(
        "A fallback may reduce capability and never claims equivalent evidence, "
        "profit, runtime authority, or order authority."
    ),
    consumer_scope=(
        "QKUComputationControlPlaneServiceV1",
        "risk_manager_agent",
        "quantum_optimizer_agent",
        "commander_agent",
    ),
    receipt_requirements=(
        "trigger_reason",
        "source_component",
        "resolved_target",
        "semantic_limitation",
        "no_effect_flags",
    ),
)

REGISTERED_FALLBACK_RESOLVER = RegisteredFallbackResolverV1(
    (CERTIFIED_FAIL_CLOSED_FALLBACK,)
)
