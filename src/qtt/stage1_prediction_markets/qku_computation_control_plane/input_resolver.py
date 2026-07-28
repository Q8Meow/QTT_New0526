"""Evidence-backed required-input resolution for registered computations."""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from datetime import timedelta
from enum import StrEnum
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping

from .authority import (
    CapabilityEnvelopeV1,
    assert_no_effect_authority,
)
from .bindings import (
    BindingResolverV1,
    CanonicalSourceBindingReceiptV1,
)
from .dependency_graph import CompiledDependencyGraphV1
from .errors import (
    ComputationControlPlaneError,
    InputResolutionError,
    ReasonCode,
)
from .freshness import (
    FreshnessPolicyV1,
    FreshnessReceiptV1,
    FreshnessResolverV1,
)
from .models import (
    ComputationReadinessStateV1,
    ComputationBindingProfileV1,
    InputOriginV1,
    TypedValueKindV1,
    TypedValueRecordV1,
    TypedValueV1,
    validate_pure_computation_authority_refs,
)
from .point_in_time import (
    PointInTimeEvidenceV1,
    PointInTimeReceiptV1,
    PointInTimeResolverV1,
)
from .serialization import safe_json_loads
from .specification import (
    ComponentExecutionRequirementV1,
    FormulaExecutionContractV1,
    MATH_IO_CONTRACTS,
    RequirementResolutionStateV1,
    TypedDataContractFieldV1,
    get_component_execution_requirement,
)
from .unit_conversion import (
    EMPTY_UNIT_CONVERSION_REGISTRY,
    UnitConversionReceiptV1,
    UnitConversionRegistryV1,
)


class InputAvailabilityStateV1(StrEnum):
    RESOLVED = "RESOLVED"
    MISSING_REQUIRED = "MISSING_REQUIRED"
    MISSING_OPTIONAL = "MISSING_OPTIONAL"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    POINT_IN_TIME_BLOCKED = "POINT_IN_TIME_BLOCKED"
    STALE_BLOCKED = "STALE_BLOCKED"
    SOURCE_BINDING_BLOCKED = "SOURCE_BINDING_BLOCKED"
    INPUT_ORIGIN_BLOCKED = "INPUT_ORIGIN_BLOCKED"
    DERIVED_LINEAGE_BLOCKED = "DERIVED_LINEAGE_BLOCKED"
    REQUIREMENTS_BLOCKED = "REQUIREMENTS_BLOCKED"
    UNIT_OR_BASIS_BLOCKED = "UNIT_OR_BASIS_BLOCKED"


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputResolutionError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be nonempty text",
        )
    return value


@dataclass(frozen=True, slots=True)
class ContextualInputValueV1:
    """A typed value with one mutually exclusive, non-authoritative origin."""

    typed_value: TypedValueV1
    point_in_time: PointInTimeEvidenceV1
    freshness_policy: FreshnessPolicyV1
    origin: InputOriginV1
    value_lineage_ref: str
    precision_policy: str
    rounding_policy: str
    producer_ref: str
    consumer_refs: tuple[str, ...]
    source_state_id: str | None = None
    source_identity: str | None = None
    source_epoch_id: str | None = None
    rights_state: str | None = None
    upstream_execution_receipt_ref: str | None = None
    upstream_component_id: str | None = None
    compiled_dependency_edge_ref: str | None = None
    lineage_readiness_state: ComputationReadinessStateV1 | None = None
    pure_computation_authority_ref: str | None = None
    fallback_ref: str | None = None
    _service_derived_construction: InitVar[object | None] = None

    def __post_init__(self, _service_derived_construction: object | None) -> None:
        if not isinstance(self.typed_value, TypedValueV1):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "typed_value must be TypedValueV1",
            )
        if not isinstance(self.point_in_time, PointInTimeEvidenceV1):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "point_in_time evidence must be typed",
            )
        if not isinstance(self.freshness_policy, FreshnessPolicyV1):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "freshness_policy must be typed",
            )
        if not isinstance(self.origin, InputOriginV1):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "input origin must be an explicit InputOriginV1",
            )
        for name in (
            "value_lineage_ref",
            "precision_policy",
            "rounding_policy",
            "producer_ref",
        ):
            _required_text(getattr(self, name), name)
        if self.point_in_time.field_id != self.typed_value.name:
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "point-in-time field id must equal typed value name",
            )
        if (
            not isinstance(self.consumer_refs, tuple)
            or not self.consumer_refs
            or any(not isinstance(ref, str) or not ref for ref in self.consumer_refs)
            or len(set(self.consumer_refs)) != len(self.consumer_refs)
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "input epoch and consumer lineage must be exact and complete",
            )
        source_assertions = (
            self.source_identity,
            self.source_state_id,
            self.source_epoch_id,
            self.rights_state,
        )
        derived_refs = (
            self.upstream_execution_receipt_ref,
            self.upstream_component_id,
            self.compiled_dependency_edge_ref,
        )
        if self.origin is InputOriginV1.CANONICAL_SOURCE_STATE:
            if (
                not isinstance(self.source_state_id, str)
                or not self.source_state_id
                or any(value is not None for value in derived_refs)
                or self.lineage_readiness_state is not None
                or self.pure_computation_authority_ref is not None
            ):
                raise InputResolutionError(
                    ReasonCode.SOURCE_BINDING_REQUIRED,
                    "canonical input origin requires only a source-state lookup pointer",
                )
            for value in (
                self.source_identity,
                self.source_epoch_id,
                self.rights_state,
            ):
                if value is not None:
                    _required_text(value, "canonical source assertion")
        elif (
            self.origin
            is InputOriginV1.OWNER_SUPPLIED_PURE_COMPUTATION_INPUT
        ):
            if (
                any(value is not None for value in source_assertions)
                or any(value is not None for value in derived_refs)
                or self.lineage_readiness_state is not None
                or not isinstance(self.pure_computation_authority_ref, str)
                or not self.pure_computation_authority_ref
            ):
                raise InputResolutionError(
                    ReasonCode.INPUT_ORIGIN_NOT_AUTHORIZED,
                    "pure input origin cannot claim source or derived authority",
                )
        else:
            if (
                any(value is not None for value in source_assertions)
                or self.pure_computation_authority_ref is not None
                or any(
                    not isinstance(value, str) or not value
                    for value in derived_refs
                )
                or not isinstance(
                    self.lineage_readiness_state,
                    ComputationReadinessStateV1,
                )
                or self.lineage_readiness_state
                is ComputationReadinessStateV1.BLOCKED
                or _service_derived_construction
                is not _SERVICE_DERIVED_INPUT_TOKEN
            ):
                raise InputResolutionError(
                    ReasonCode.DERIVED_LINEAGE_INVALID,
                    "derived inputs require service construction and exact lineage",
                )
        if self.fallback_ref is not None:
            _required_text(self.fallback_ref, "fallback_ref")

    @classmethod
    def _from_service_derived(
        cls,
        *,
        typed_value: TypedValueV1,
        point_in_time: PointInTimeEvidenceV1,
        freshness_policy: FreshnessPolicyV1,
        value_lineage_ref: str,
        precision_policy: str,
        rounding_policy: str,
        producer_ref: str,
        consumer_refs: tuple[str, ...],
        upstream_execution_receipt_ref: str,
        upstream_component_id: str,
        compiled_dependency_edge_ref: str,
        lineage_readiness_state: ComputationReadinessStateV1,
        fallback_ref: str | None = None,
    ) -> "ContextualInputValueV1":
        return cls(
            typed_value=typed_value,
            point_in_time=point_in_time,
            freshness_policy=freshness_policy,
            origin=InputOriginV1.IN_PROCESS_DERIVED_VALUE,
            value_lineage_ref=value_lineage_ref,
            precision_policy=precision_policy,
            rounding_policy=rounding_policy,
            producer_ref=producer_ref,
            consumer_refs=consumer_refs,
            upstream_execution_receipt_ref=upstream_execution_receipt_ref,
            upstream_component_id=upstream_component_id,
            compiled_dependency_edge_ref=compiled_dependency_edge_ref,
            lineage_readiness_state=lineage_readiness_state,
            fallback_ref=fallback_ref,
            _service_derived_construction=_SERVICE_DERIVED_INPUT_TOKEN,
        )


_SERVICE_DERIVED_INPUT_TOKEN = object()


@dataclass(frozen=True, slots=True)
class ResolvedInputV1:
    component_id: str
    input_field_id: str
    required: bool
    expected_type: str
    expected_shape: str
    supplied_unit: str | None
    required_unit: str
    supplied_basis: str | None
    required_basis: str
    state: InputAvailabilityStateV1
    origin_class: InputOriginV1 | None
    source_readiness_state: ComputationReadinessStateV1
    source_identity: str | None
    source_state_id: str | None
    source_epoch_id: str | None
    rights_state: str | None
    point_in_time_receipt: PointInTimeReceiptV1 | None
    freshness_receipt: FreshnessReceiptV1 | None
    conversion_receipt: UnitConversionReceiptV1 | None
    canonical_source_binding_receipt_ref: str | None
    upstream_execution_receipt_ref: str | None
    compiled_dependency_edge_ref: str | None
    pure_computation_only: bool
    value_lineage_ref: str | None
    precision_policy: str | None
    rounding_policy: str | None
    resolved_value: object | None
    fallback_eligible: bool
    fallback_ref: str | None
    blocker_codes: tuple[ReasonCode, ...]
    producer_ref: str | None
    consumer_refs: tuple[str, ...]
    terminal_route: str

    @property
    def resolved(self) -> bool:
        return self.state is InputAvailabilityStateV1.RESOLVED


@dataclass(frozen=True, slots=True)
class InputResolutionReceiptV1:
    receipt_id: str
    component_id: str
    inputs: tuple[ResolvedInputV1, ...]
    resolved_arguments: tuple[tuple[str, object], ...]
    blocker_codes: tuple[ReasonCode, ...]
    blocker_detail_refs: tuple[str, ...]
    source_readiness_state: ComputationReadinessStateV1
    requirement_resolution_state: RequirementResolutionStateV1
    requirement_evidence_refs: tuple[str, ...]
    canonical_source_binding_receipts: tuple[
        CanonicalSourceBindingReceiptV1, ...
    ]
    dependency_refs: tuple[str, ...]
    parameter_policy_refs: tuple[str, ...]
    parameter_resolution_receipt_refs: tuple[str, ...]
    source_owner_refs: tuple[str, ...]
    downstream_consumer_refs: tuple[str, ...]
    terminal_route: str
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        _required_text(self.receipt_id, "receipt_id")
        _required_text(self.component_id, "component_id")
        _required_text(self.terminal_route, "terminal_route")
        if (
            not isinstance(self.inputs, tuple)
            or not self.inputs
            or any(not isinstance(item, ResolvedInputV1) for item in self.inputs)
            or len({item.input_field_id for item in self.inputs}) != len(self.inputs)
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "input receipt requires a unique typed input tuple",
            )
        names = tuple(name for name, _ in self.resolved_arguments)
        if len(names) != len(set(names)):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "resolved argument names must be unique",
            )
        if (
            not isinstance(self.blocker_codes, tuple)
            or any(not isinstance(code, ReasonCode) for code in self.blocker_codes)
            or len(set(self.blocker_codes)) != len(self.blocker_codes)
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "input blockers must be a unique typed tuple",
            )
        for name in (
            "blocker_detail_refs",
            "requirement_evidence_refs",
            "dependency_refs",
            "parameter_policy_refs",
            "parameter_resolution_receipt_refs",
            "source_owner_refs",
            "downstream_consumer_refs",
        ):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or any(not isinstance(value, str) or not value for value in values)
                or len(values) != len(set(values))
            ):
                raise InputResolutionError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a unique immutable text tuple",
                )
        if (
            not isinstance(
                self.source_readiness_state,
                ComputationReadinessStateV1,
            )
            or not isinstance(
                self.requirement_resolution_state,
                RequirementResolutionStateV1,
            )
            or not isinstance(
                self.canonical_source_binding_receipts,
                tuple,
            )
            or any(
                not isinstance(value, CanonicalSourceBindingReceiptV1)
                for value in self.canonical_source_binding_receipts
            )
            or len(
                {
                    value.receipt_id
                    for value in self.canonical_source_binding_receipts
                }
            )
            != len(self.canonical_source_binding_receipts)
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "input readiness, requirement, and source receipts must be typed",
            )
        if (
            bool(self.blocker_codes)
            != (
                self.source_readiness_state
                is ComputationReadinessStateV1.BLOCKED
            )
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "input blockers and readiness state must agree",
            )
        if type(self.no_authority_flag) is not bool or not self.no_authority_flag:
            raise InputResolutionError(
                ReasonCode.CAPABILITY_DENIED,
                "input resolution cannot create authority",
            )

    @property
    def computable(self) -> bool:
        return not self.blocker_codes

    @property
    def arguments(self) -> Mapping[str, object]:
        return MappingProxyType(dict(self.resolved_arguments))


def _math_id(component_id: str) -> str:
    _required_text(component_id, "component_id")
    candidate = component_id.split("::", 1)[0]
    if candidate not in MATH_IO_CONTRACTS:
        raise InputResolutionError(
            ReasonCode.UNKNOWN_IMPLEMENTATION,
            f"unknown component identity: {component_id}",
        )
    return candidate


def _expected_kind(field: TypedDataContractFieldV1) -> TypedValueKindV1:
    normalized = field.type_name.casefold()
    if normalized == "decimal":
        return TypedValueKindV1.DECIMAL
    if normalized in {"float64", "active probability dtype"}:
        return TypedValueKindV1.FLOAT64
    if normalized in {"int", "even int", "0/1", "binary"}:
        return TypedValueKindV1.INTEGER
    return TypedValueKindV1.TEXT


def _decode_value(
    supplied: TypedValueV1,
    expected: TypedDataContractFieldV1,
) -> object:
    expected_kind = _expected_kind(expected)
    if supplied.kind is not expected_kind:
        raise InputResolutionError(
            ReasonCode.INPUT_TYPE_MISMATCH,
            f"{supplied.name} requires {expected.type_name}, not {supplied.kind.value}",
        )
    if supplied.kind is TypedValueKindV1.INTEGER and expected.type_name in {
        "0/1",
        "binary",
    } and supplied.value not in {0, 1}:
        raise InputResolutionError(
            ReasonCode.INPUT_TYPE_MISMATCH,
            f"{supplied.name} must be an exact binary integer",
        )
    if supplied.kind is TypedValueKindV1.TEXT:
        decoded = safe_json_loads(supplied.value)
        if not isinstance(decoded, dict | list):
            raise InputResolutionError(
                ReasonCode.INPUT_TYPE_MISMATCH,
                f"{supplied.name} structured input must decode to an object or array",
            )
        return decoded
    return supplied.value


def compiled_dependency_edge_ref_v1(edge: object) -> str:
    required = (
        "upstream_id",
        "upstream_output_field",
        "downstream_id",
        "downstream_input_field",
        "supplied_unit",
        "required_unit",
        "supplied_basis",
        "required_basis",
        "timing_class",
    )
    if any(
        not isinstance(getattr(edge, name, None), str)
        or not getattr(edge, name)
        for name in required
    ):
        raise InputResolutionError(
            ReasonCode.DERIVED_LINEAGE_INVALID,
            "compiled dependency edge is incomplete",
        )
    return "|".join(
        (
            "COMPILED-EDGE",
            f"{edge.upstream_id}.{edge.upstream_output_field}",
            f"{edge.downstream_id}.{edge.downstream_input_field}",
            f"{edge.supplied_unit}/{edge.supplied_basis}",
            f"{edge.required_unit}/{edge.required_basis}",
            edge.timing_class,
        )
    )


def _source_ttl(source_ttl: str) -> timedelta | None:
    if not isinstance(source_ttl, str):
        return None
    if source_ttl.startswith("P") and source_ttl.endswith("D"):
        day_text = source_ttl[1:-1]
        if day_text.isdecimal() and int(day_text) > 0:
            return timedelta(days=int(day_text))
    return None


def _blocked_input_state(
    blockers: tuple[ReasonCode, ...],
) -> InputAvailabilityStateV1:
    if ReasonCode.EXECUTION_REQUIREMENTS_UNRESOLVED in blockers:
        return InputAvailabilityStateV1.REQUIREMENTS_BLOCKED
    if any(
        code
        in {
            ReasonCode.INPUT_ORIGIN_NOT_AUTHORIZED,
            ReasonCode.CAPABILITY_DENIED,
        }
        for code in blockers
    ):
        return InputAvailabilityStateV1.INPUT_ORIGIN_BLOCKED
    if ReasonCode.DERIVED_LINEAGE_INVALID in blockers:
        return InputAvailabilityStateV1.DERIVED_LINEAGE_BLOCKED
    if ReasonCode.INPUT_TYPE_MISMATCH in blockers:
        return InputAvailabilityStateV1.TYPE_MISMATCH
    if any(
        code
        in {
            ReasonCode.POINT_IN_TIME_UNAVAILABLE,
            ReasonCode.REVISION_LEAKAGE,
        }
        for code in blockers
    ):
        return InputAvailabilityStateV1.POINT_IN_TIME_BLOCKED
    if any(
        code in {ReasonCode.FIELD_STALE, ReasonCode.FRESHNESS_UNKNOWN}
        for code in blockers
    ):
        return InputAvailabilityStateV1.STALE_BLOCKED
    if any(
        code
        in {
            ReasonCode.SOURCE_BINDING_REQUIRED,
            ReasonCode.SOURCE_CLAIM_BINDING_MISMATCH,
            ReasonCode.SOURCE_EPOCH_MISSING,
            ReasonCode.SOURCE_EPOCH_STALE,
            ReasonCode.SOURCE_CONFLICT,
            ReasonCode.SOURCE_RIGHTS_BLOCKED,
        }
        for code in blockers
    ):
        return InputAvailabilityStateV1.SOURCE_BINDING_BLOCKED
    return InputAvailabilityStateV1.UNIT_OR_BASIS_BLOCKED


class RequiredInputResolverV1:
    """Derive exact requirements from typed contracts and evidence."""

    def __init__(
        self,
        *,
        conversion_registry: UnitConversionRegistryV1 = (
            EMPTY_UNIT_CONVERSION_REGISTRY
        ),
        admitted_pure_computation_authority_refs: tuple[str, ...] = (),
    ) -> None:
        if not isinstance(conversion_registry, UnitConversionRegistryV1):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "conversion registry and pure-computation authority must be exact",
            )
        self._conversion_registry = conversion_registry
        self._admitted_pure_computation_authority_refs = (
            validate_pure_computation_authority_refs(
                admitted_pure_computation_authority_refs
            )
        )

    def unresolved_requirements(
        self,
        *,
        component_id: str,
        context,
        optional_field_ids: tuple[str, ...] = (),
        dependency_refs: tuple[str, ...] = (),
        parameter_policy_refs: tuple[str, ...] | None = None,
        parameter_resolution_receipt_refs: tuple[str, ...] = (),
        downstream_consumer_refs: tuple[str, ...] = (
            "QKUComputationControlPlaneServiceV1",
        ),
    ) -> InputResolutionReceiptV1:
        """Describe exact requirements when no contextual values were supplied.

        This is an evidence-derived missing state, not a synthetic neutral value.
        It lets the public resolution operations return typed field-level
        blockers without weakening ``TypedValueRecordV1``'s nonempty invariant.
        """

        from .context import ComputationContextKeyV1

        math_id = _math_id(component_id)
        if not isinstance(context, ComputationContextKeyV1):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "context must be ComputationContextKeyV1",
            )
        if (
            not isinstance(optional_field_ids, tuple)
            or len(set(optional_field_ids)) != len(optional_field_ids)
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "optional fields must be a unique immutable tuple",
            )
        io_contract = MATH_IO_CONTRACTS[math_id]
        expected_names = {field.name for field in io_contract.inputs}
        if not set(optional_field_ids) <= expected_names:
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "optional fields must exist in the registered input schema",
            )
        requirement = get_component_execution_requirement(math_id)
        central_parameter_refs = requirement.required_parameter_policy_ids
        assertion_mismatch = (
            parameter_policy_refs is not None
            and parameter_policy_refs != central_parameter_refs
        )
        requirement_unresolved = (
            requirement.terminal_requirement_resolution_state
            is RequirementResolutionStateV1.UNRESOLVED_REQUIREMENTS_FAIL_CLOSED
        )
        mandatory_reason = (
            ReasonCode.EXECUTION_REQUIREMENTS_UNRESOLVED
            if requirement_unresolved
            else (
                ReasonCode.PARAMETER_ASSERTION_MISMATCH
                if assertion_mismatch
                else ReasonCode.REQUIRED_INPUT_MISSING
            )
        )
        rows = tuple(
            ResolvedInputV1(
                component_id=math_id,
                input_field_id=field.name,
                required=field.name not in optional_field_ids,
                expected_type=field.type_name,
                expected_shape=field.shape,
                supplied_unit=None,
                required_unit=field.unit,
                supplied_basis=None,
                required_basis=field.basis,
                state=(
                    InputAvailabilityStateV1.MISSING_OPTIONAL
                    if field.name in optional_field_ids
                    else (
                        InputAvailabilityStateV1.REQUIREMENTS_BLOCKED
                        if requirement_unresolved
                        else InputAvailabilityStateV1.MISSING_REQUIRED
                    )
                ),
                origin_class=None,
                source_readiness_state=ComputationReadinessStateV1.BLOCKED,
                source_identity=None,
                source_state_id=None,
                source_epoch_id=None,
                rights_state=None,
                point_in_time_receipt=None,
                freshness_receipt=None,
                conversion_receipt=None,
                canonical_source_binding_receipt_ref=None,
                upstream_execution_receipt_ref=None,
                compiled_dependency_edge_ref=None,
                pure_computation_only=False,
                value_lineage_ref=None,
                precision_policy=None,
                rounding_policy=None,
                resolved_value=None,
                fallback_eligible=False,
                fallback_ref=None,
                blocker_codes=(
                    ()
                    if field.name in optional_field_ids
                    else (mandatory_reason,)
                ),
                producer_ref=None,
                consumer_refs=downstream_consumer_refs,
                terminal_route=(
                    "QKUComputationControlPlaneV1::OPTIONAL_OMISSION"
                    if field.name in optional_field_ids
                    else "research_agent::MATERIALIZE_TYPED_INPUT"
                ),
            )
            for field in io_contract.inputs
        )
        blockers = (
            ()
            if all(not row.required for row in rows)
            else (mandatory_reason,)
        )
        digest = "|".join(
            (
                math_id,
                context.stable_key,
                "NO_CONTEXTUAL_VALUES_SUPPLIED",
                *(row.input_field_id for row in rows),
            )
        )
        return InputResolutionReceiptV1(
            receipt_id=f"INPUT::{sha256(digest.encode('utf-8')).hexdigest()}",
            component_id=math_id,
            inputs=rows,
            resolved_arguments=(),
            blocker_codes=blockers,
            blocker_detail_refs=requirement.missing_owner_refs,
            source_readiness_state=ComputationReadinessStateV1.BLOCKED,
            requirement_resolution_state=(
                requirement.terminal_requirement_resolution_state
            ),
            requirement_evidence_refs=(
                requirement.terminal_resolution_evidence_refs
            ),
            canonical_source_binding_receipts=(),
            dependency_refs=dependency_refs,
            parameter_policy_refs=central_parameter_refs,
            parameter_resolution_receipt_refs=(
                parameter_resolution_receipt_refs
            ),
            source_owner_refs=(),
            downstream_consumer_refs=downstream_consumer_refs,
            terminal_route="research_agent::INPUT_MATERIALIZATION_WORK_ORDER",
        )

    def resolve(
        self,
        *,
        component_id: str,
        context,
        supplied_values: TypedValueRecordV1,
        contextual_evidence: tuple[ContextualInputValueV1, ...],
        formula_contract: FormulaExecutionContractV1 | None = None,
        binding_profile: ComputationBindingProfileV1 | None = None,
        compiled_dependency_graph: CompiledDependencyGraphV1 | None = None,
        optional_field_ids: tuple[str, ...] = (),
        dependency_refs: tuple[str, ...] = (),
        parameter_resolution_receipt_refs: tuple[str, ...] = (),
        downstream_consumer_refs: tuple[str, ...] = (
            "QKUComputationControlPlaneServiceV1",
        ),
        mode: str = "CONTRACT_ONLY",
        authority: CapabilityEnvelopeV1 = CapabilityEnvelopeV1(),
    ) -> InputResolutionReceiptV1:
        from .context import ComputationContextKeyV1

        math_id = _math_id(component_id)
        if not isinstance(context, ComputationContextKeyV1):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "context must be ComputationContextKeyV1",
            )
        if not isinstance(supplied_values, TypedValueRecordV1):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "supplied_values must be TypedValueRecordV1",
            )
        requirement = get_component_execution_requirement(math_id)
        if (
            requirement.terminal_requirement_resolution_state
            is RequirementResolutionStateV1.UNRESOLVED_REQUIREMENTS_FAIL_CLOSED
        ):
            return self.unresolved_requirements(
                component_id=math_id,
                context=context,
                optional_field_ids=optional_field_ids,
                dependency_refs=dependency_refs,
                parameter_policy_refs=(
                    requirement.required_parameter_policy_ids
                ),
                parameter_resolution_receipt_refs=(
                    parameter_resolution_receipt_refs
                ),
                downstream_consumer_refs=downstream_consumer_refs,
            )
        if (
            not isinstance(contextual_evidence, tuple)
            or any(
                not isinstance(item, ContextualInputValueV1)
                for item in contextual_evidence
            )
            or len({item.typed_value.name for item in contextual_evidence})
            != len(contextual_evidence)
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "contextual evidence must be a unique typed tuple",
            )
        if formula_contract is not None and (
            not isinstance(formula_contract, FormulaExecutionContractV1)
            or formula_contract.canonical_formula_id_or_null != math_id
            or formula_contract.context_key != context
            or formula_contract.parameter_policy_refs
            != requirement.required_parameter_policy_ids
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "formula contract identity/context differs from the request",
            )
        if binding_profile is not None and not isinstance(
            binding_profile,
            ComputationBindingProfileV1,
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "binding_profile must be typed when supplied",
            )
        if compiled_dependency_graph is not None and not isinstance(
            compiled_dependency_graph,
            CompiledDependencyGraphV1,
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "compiled dependency graph must be typed when supplied",
            )
        if (
            not isinstance(optional_field_ids, tuple)
            or len(set(optional_field_ids)) != len(optional_field_ids)
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "optional fields must be a unique immutable tuple",
            )
        if (
            mode not in {"CONTRACT_ONLY", "REPLAY", "PAPER"}
            or not isinstance(authority, CapabilityEnvelopeV1)
            or not isinstance(parameter_resolution_receipt_refs, tuple)
            or any(
                not isinstance(value, str) or not value
                for value in parameter_resolution_receipt_refs
            )
            or len(set(parameter_resolution_receipt_refs))
            != len(parameter_resolution_receipt_refs)
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "input mode, authority, and parameter receipts must be exact",
            )
        authority_blocker: ReasonCode | None = None
        try:
            assert_no_effect_authority(authority)
        except ComputationControlPlaneError as exc:
            authority_blocker = exc.reason_code
        if mode not in requirement.allowed_computation_modes:
            authority_blocker = ReasonCode.INPUT_ORIGIN_NOT_AUTHORIZED

        io_contract = MATH_IO_CONTRACTS[math_id]
        expected_names = tuple(field.name for field in io_contract.inputs)
        if not set(optional_field_ids) <= set(expected_names):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "optional fields must exist in the registered input schema",
            )
        if formula_contract is not None and (
            formula_contract.typed_input_contract != io_contract.inputs
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "formula execution contract input schema is not canonical",
            )
        if binding_profile is not None:
            expected_bindings = tuple(
                (field.name, field.unit, field.basis)
                for field in io_contract.inputs
            )
            supplied_bindings = tuple(
                (item.field_name, item.unit, item.basis)
                for item in binding_profile.input_bindings
            )
            if expected_bindings != supplied_bindings:
                raise InputResolutionError(
                    ReasonCode.INVALID_CONTRACT,
                    "binding profile does not equal the registered input schema",
                )

        values_by_name = {item.name: item for item in supplied_values.fields}
        evidence_by_name = {
            item.typed_value.name: item for item in contextual_evidence
        }
        unexpected = (set(values_by_name) | set(evidence_by_name)) - set(
            expected_names
        )
        if unexpected:
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                f"unexpected component input fields: {sorted(unexpected)!r}",
            )

        rows: list[ResolvedInputV1] = []
        arguments: list[tuple[str, object]] = []
        aggregate_blockers: list[ReasonCode] = []
        source_owners: list[str] = []
        binding_receipts: list[CanonicalSourceBindingReceiptV1] = []
        blocker_details: list[str] = []
        for field in io_contract.inputs:
            required = field.name not in optional_field_ids
            supplied = values_by_name.get(field.name)
            evidence = evidence_by_name.get(field.name)
            if supplied is None or evidence is None or (
                evidence is not None and evidence.typed_value != supplied
            ):
                state = (
                    InputAvailabilityStateV1.MISSING_REQUIRED
                    if required
                    else InputAvailabilityStateV1.MISSING_OPTIONAL
                )
                blockers = (
                    (ReasonCode.REQUIRED_INPUT_MISSING,) if required else ()
                )
                aggregate_blockers.extend(blockers)
                rows.append(
                    ResolvedInputV1(
                        component_id=math_id,
                        input_field_id=field.name,
                        required=required,
                        expected_type=field.type_name,
                        expected_shape=field.shape,
                        supplied_unit=None,
                        required_unit=field.unit,
                        supplied_basis=None,
                        required_basis=field.basis,
                        state=state,
                        origin_class=None,
                        source_readiness_state=(
                            ComputationReadinessStateV1.BLOCKED
                        ),
                        source_identity=None,
                        source_state_id=None,
                        source_epoch_id=None,
                        rights_state=None,
                        point_in_time_receipt=None,
                        freshness_receipt=None,
                        conversion_receipt=None,
                        canonical_source_binding_receipt_ref=None,
                        upstream_execution_receipt_ref=None,
                        compiled_dependency_edge_ref=None,
                        pure_computation_only=False,
                        value_lineage_ref=None,
                        precision_policy=None,
                        rounding_policy=None,
                        resolved_value=None,
                        fallback_eligible=False,
                        fallback_ref=None,
                        blocker_codes=blockers,
                        producer_ref=None,
                        consumer_refs=downstream_consumer_refs,
                        terminal_route=(
                            "research_agent::MATERIALIZE_TYPED_INPUT"
                            if required
                            else "QKUComputationControlPlaneV1::OPTIONAL_OMISSION"
                        ),
                    )
                )
                continue

            blockers_list: list[ReasonCode] = []
            if authority_blocker is not None:
                blockers_list.append(authority_blocker)
            accepted_origins = requirement.accepted_origins_for(field.name)
            if evidence.origin not in accepted_origins:
                blockers_list.append(ReasonCode.INPUT_ORIGIN_NOT_AUTHORIZED)

            pit_receipt = PointInTimeResolverV1.resolve(
                evidence.point_in_time,
                context,
            )
            if not pit_receipt.available:
                blockers_list.extend(pit_receipt.blocker_codes)
            effective_freshness_policy = evidence.freshness_policy
            canonical_receipt: CanonicalSourceBindingReceiptV1 | None = None
            effective_source_identity: str | None = None
            effective_source_state_id: str | None = None
            effective_source_epoch_id: str | None = None
            effective_rights_state: str | None = None
            row_readiness = ComputationReadinessStateV1.BLOCKED

            if evidence.origin is InputOriginV1.CANONICAL_SOURCE_STATE:
                try:
                    source_binding, canonical_receipt = (
                        BindingResolverV1.resolve_canonical_source_input(
                            component_id=math_id,
                            input_field_id=field.name,
                            source_state_id=evidence.source_state_id or "",
                            allowed_binding_rule_ids=(
                                requirement.source_rules_for(field.name)
                            ),
                            context_source_epoch_id=context.source_epoch_id,
                            as_of=context.as_of,
                            asserted_source_identity=evidence.source_identity,
                            asserted_source_epoch_id=evidence.source_epoch_id,
                            asserted_rights_state=evidence.rights_state,
                        )
                    )
                except ComputationControlPlaneError as exc:
                    blockers_list.append(exc.reason_code)
                    blocker_details.append(
                        f"{math_id}.{field.name}::{exc.reason_code.value}"
                    )
                else:
                    from .source_policy import get_source_state

                    source_state = get_source_state(
                        source_binding.source_state_id
                    )
                    canonical_ttl = _source_ttl(source_state.ttl)
                    if (
                        canonical_ttl is None
                        or evidence.freshness_policy.ttl != canonical_ttl
                    ):
                        blockers_list.append(ReasonCode.SOURCE_CONFLICT)
                    else:
                        effective_freshness_policy = FreshnessPolicyV1(
                            policy_id=(
                                f"CANONICAL-TTL::{source_state.source_state_id}"
                            ),
                            ttl=canonical_ttl,
                            parameter_policy_ref=(
                                source_state.source_state_id
                            ),
                            stale_behavior=(
                                "FAIL_CLOSED_OR_REGISTERED_FALLBACK"
                            ),
                        )
                    if binding_profile is not None and source_binding not in (
                        binding_profile.source_bindings
                    ):
                        blockers_list.append(ReasonCode.SOURCE_CONFLICT)
                    effective_source_identity = (
                        source_binding.stable_source_identity
                    )
                    effective_source_state_id = source_binding.source_state_id
                    effective_source_epoch_id = source_binding.effective_epoch
                    effective_rights_state = source_binding.rights_state
                    source_owners.extend(
                        (
                            source_binding.source_state_id,
                            canonical_receipt.receipt_id,
                        )
                    )
                    binding_receipts.append(canonical_receipt)
                    row_readiness = (
                        ComputationReadinessStateV1.SOURCE_CONTEXT_COMPUTABLE
                    )
            elif (
                evidence.origin
                is InputOriginV1.OWNER_SUPPLIED_PURE_COMPUTATION_INPUT
            ):
                if (
                    mode != "CONTRACT_ONLY"
                    or evidence.pure_computation_authority_ref
                    not in self._admitted_pure_computation_authority_refs
                ):
                    blockers_list.append(
                        ReasonCode.INPUT_ORIGIN_NOT_AUTHORIZED
                    )
                row_readiness = (
                    ComputationReadinessStateV1.PURE_COMPUTATION_ONLY
                )
            else:
                matching_edges = (
                    ()
                    if compiled_dependency_graph is None
                    else tuple(
                        edge
                        for edge in compiled_dependency_graph.edges
                        if edge.upstream_id
                        == evidence.upstream_component_id
                        and edge.downstream_id == math_id
                        and edge.downstream_input_field == field.name
                        and compiled_dependency_edge_ref_v1(edge)
                        == evidence.compiled_dependency_edge_ref
                    )
                )
                if (
                    len(matching_edges) != 1
                    or evidence.producer_ref
                    != evidence.upstream_component_id
                    or math_id not in evidence.consumer_refs
                    or (
                        "QKUComputationControlPlaneServiceV1"
                        not in evidence.consumer_refs
                    )
                ):
                    blockers_list.append(ReasonCode.DERIVED_LINEAGE_INVALID)
                else:
                    edge = matching_edges[0]
                    if (
                        supplied.unit != edge.required_unit
                        or supplied.basis != edge.required_basis
                    ):
                        blockers_list.append(
                            ReasonCode.DEPENDENCY_UNIT_MISMATCH
                        )
                row_readiness = (
                    evidence.lineage_readiness_state
                    or ComputationReadinessStateV1.BLOCKED
                )

            freshness_receipt = FreshnessResolverV1.resolve_field(
                subject_id=f"{math_id}::{field.name}",
                observed_time=evidence.point_in_time.observed_time,
                as_of_time=context.as_of,
                policy=effective_freshness_policy,
            )
            if not freshness_receipt.fresh:
                blockers_list.extend(freshness_receipt.blocker_codes)
            if (
                evidence.point_in_time.source_epoch_id
                != context.source_epoch_id
            ):
                blockers_list.append(ReasonCode.SOURCE_EPOCH_MISSING)

            decoded: object | None = None
            conversion_receipt: UnitConversionReceiptV1 | None = None
            try:
                decoded = _decode_value(supplied, field)
            except InputResolutionError as exc:
                blockers_list.append(exc.reason_code)
            if decoded is not None and (
                supplied.unit != field.unit or supplied.basis != field.basis
            ):
                if supplied.kind is not TypedValueKindV1.DECIMAL:
                    blockers_list.append(ReasonCode.DEPENDENCY_UNIT_MISMATCH)
                else:
                    try:
                        conversion_receipt = self._conversion_registry.resolve(
                            value=supplied.value,
                            supplied_unit=supplied.unit,
                            required_unit=field.unit,
                            supplied_basis=supplied.basis,
                            required_basis=field.basis,
                            source_epoch_id=context.source_epoch_id,
                            as_of_time=context.as_of,
                        )
                        decoded = conversion_receipt.resolved_value
                    except InputResolutionError as exc:
                        blockers_list.append(exc.reason_code)
                    except ValueError as exc:
                        reason = getattr(
                            exc,
                            "reason_code",
                            ReasonCode.DEPENDENCY_UNIT_MISMATCH,
                        )
                        blockers_list.append(reason)

            blockers = tuple(dict.fromkeys(blockers_list))
            aggregate_blockers.extend(blockers)
            if blockers:
                state = _blocked_input_state(blockers)
                row_readiness = ComputationReadinessStateV1.BLOCKED
            else:
                state = InputAvailabilityStateV1.RESOLVED
                arguments.append((field.name, decoded))
            rows.append(
                ResolvedInputV1(
                    component_id=math_id,
                    input_field_id=field.name,
                    required=required,
                    expected_type=field.type_name,
                    expected_shape=field.shape,
                    supplied_unit=supplied.unit,
                    required_unit=field.unit,
                    supplied_basis=supplied.basis,
                    required_basis=field.basis,
                    state=state,
                    origin_class=evidence.origin,
                    source_readiness_state=row_readiness,
                    source_identity=effective_source_identity,
                    source_state_id=effective_source_state_id,
                    source_epoch_id=effective_source_epoch_id,
                    rights_state=effective_rights_state,
                    point_in_time_receipt=pit_receipt,
                    freshness_receipt=freshness_receipt,
                    conversion_receipt=conversion_receipt,
                    canonical_source_binding_receipt_ref=(
                        None
                        if canonical_receipt is None
                        else canonical_receipt.receipt_id
                    ),
                    upstream_execution_receipt_ref=(
                        evidence.upstream_execution_receipt_ref
                    ),
                    compiled_dependency_edge_ref=(
                        evidence.compiled_dependency_edge_ref
                    ),
                    pure_computation_only=(
                        evidence.origin
                        is InputOriginV1.OWNER_SUPPLIED_PURE_COMPUTATION_INPUT
                    ),
                    value_lineage_ref=evidence.value_lineage_ref,
                    precision_policy=evidence.precision_policy,
                    rounding_policy=evidence.rounding_policy,
                    resolved_value=decoded if not blockers else None,
                    fallback_eligible=bool(evidence.fallback_ref),
                    fallback_ref=evidence.fallback_ref,
                    blocker_codes=blockers,
                    producer_ref=evidence.producer_ref,
                    consumer_refs=evidence.consumer_refs,
                    terminal_route=(
                        "QKUComputationControlPlaneServiceV1"
                        if not blockers
                        else (
                            "risk_manager_agent::REGISTERED_FALLBACK_REVIEW"
                            if evidence.fallback_ref
                            else "research_agent::INPUT_REBINDING_WORK_ORDER"
                        )
                    ),
                )
            )

        aggregate = tuple(dict.fromkeys(aggregate_blockers))
        resolved_required_rows = tuple(
            row for row in rows if row.required and row.resolved
        )
        if aggregate:
            readiness = ComputationReadinessStateV1.BLOCKED
        elif any(
            row.source_readiness_state
            is ComputationReadinessStateV1.PURE_COMPUTATION_ONLY
            for row in resolved_required_rows
        ):
            readiness = ComputationReadinessStateV1.PURE_COMPUTATION_ONLY
        else:
            readiness = (
                ComputationReadinessStateV1.SOURCE_CONTEXT_COMPUTABLE
            )
        digest = "|".join(
            (
                math_id,
                context.stable_key,
                *(
                    f"{row.input_field_id}:{row.state.value}:"
                    f"{'' if row.origin_class is None else row.origin_class.value}:"
                    f"{row.source_readiness_state.value}"
                    for row in rows
                ),
                readiness.value,
                *(code.value for code in aggregate),
            )
        )
        return InputResolutionReceiptV1(
            receipt_id=f"INPUT::{sha256(digest.encode('utf-8')).hexdigest()}",
            component_id=math_id,
            inputs=tuple(rows),
            resolved_arguments=tuple(arguments),
            blocker_codes=aggregate,
            blocker_detail_refs=tuple(dict.fromkeys(blocker_details)),
            source_readiness_state=readiness,
            requirement_resolution_state=(
                requirement.terminal_requirement_resolution_state
            ),
            requirement_evidence_refs=(
                requirement.terminal_resolution_evidence_refs
            ),
            canonical_source_binding_receipts=tuple(
                dict.fromkeys(binding_receipts)
            ),
            dependency_refs=dependency_refs,
            parameter_policy_refs=requirement.required_parameter_policy_ids,
            parameter_resolution_receipt_refs=(
                parameter_resolution_receipt_refs
            ),
            source_owner_refs=tuple(dict.fromkeys(source_owners)),
            downstream_consumer_refs=downstream_consumer_refs,
            terminal_route=(
                "QKUComputationControlPlaneServiceV1::COMPUTE_COMPONENT"
                if not aggregate
                else requirement.registered_failure_fallback_route
            ),
        )

    def require_resolved(self, **kwargs) -> InputResolutionReceiptV1:
        receipt = self.resolve(**kwargs)
        if not receipt.computable:
            raise InputResolutionError(
                receipt.blocker_codes[0],
                f"{receipt.component_id} inputs are not context-computable",
            )
        return receipt
