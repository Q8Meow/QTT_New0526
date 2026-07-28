"""Evidence-backed required-input resolution for registered computations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping

from .errors import InputResolutionError, ReasonCode
from .freshness import (
    FreshnessPolicyV1,
    FreshnessReceiptV1,
    FreshnessResolverV1,
)
from .models import (
    ComputationBindingProfileV1,
    TypedValueKindV1,
    TypedValueRecordV1,
    TypedValueV1,
)
from .point_in_time import (
    PointInTimeEvidenceV1,
    PointInTimeReceiptV1,
    PointInTimeResolverV1,
)
from .serialization import safe_json_loads
from .specification import (
    FormulaExecutionContractV1,
    MATH_IO_CONTRACTS,
    TypedDataContractFieldV1,
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
    """A typed numeric/structured value plus non-assertive evidence."""

    typed_value: TypedValueV1
    point_in_time: PointInTimeEvidenceV1
    freshness_policy: FreshnessPolicyV1
    source_identity: str
    source_state_id: str
    source_epoch_id: str
    rights_state: str
    value_lineage_ref: str
    precision_policy: str
    rounding_policy: str
    producer_ref: str
    consumer_refs: tuple[str, ...]
    fallback_ref: str | None = None

    def __post_init__(self) -> None:
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
        for name in (
            "source_identity",
            "source_state_id",
            "source_epoch_id",
            "rights_state",
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
            self.point_in_time.source_epoch_id != self.source_epoch_id
            or not isinstance(self.consumer_refs, tuple)
            or not self.consumer_refs
            or any(not isinstance(ref, str) or not ref for ref in self.consumer_refs)
            or len(set(self.consumer_refs)) != len(self.consumer_refs)
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "input epoch and consumer lineage must be exact and complete",
            )
        if self.fallback_ref is not None:
            _required_text(self.fallback_ref, "fallback_ref")


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
    source_identity: str | None
    source_state_id: str | None
    source_epoch_id: str | None
    rights_state: str | None
    point_in_time_receipt: PointInTimeReceiptV1 | None
    freshness_receipt: FreshnessReceiptV1 | None
    conversion_receipt: UnitConversionReceiptV1 | None
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
    dependency_refs: tuple[str, ...]
    parameter_policy_refs: tuple[str, ...]
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
            "dependency_refs",
            "parameter_policy_refs",
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


class RequiredInputResolverV1:
    """Derive exact requirements from typed contracts and evidence."""

    def __init__(
        self,
        *,
        conversion_registry: UnitConversionRegistryV1 = (
            EMPTY_UNIT_CONVERSION_REGISTRY
        ),
    ) -> None:
        if not isinstance(conversion_registry, UnitConversionRegistryV1):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "conversion registry must be typed",
            )
        self._conversion_registry = conversion_registry

    def unresolved_requirements(
        self,
        *,
        component_id: str,
        context,
        optional_field_ids: tuple[str, ...] = (),
        dependency_refs: tuple[str, ...] = (),
        parameter_policy_refs: tuple[str, ...] = (),
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
                    else InputAvailabilityStateV1.MISSING_REQUIRED
                ),
                source_identity=None,
                source_state_id=None,
                source_epoch_id=None,
                rights_state=None,
                point_in_time_receipt=None,
                freshness_receipt=None,
                conversion_receipt=None,
                value_lineage_ref=None,
                precision_policy=None,
                rounding_policy=None,
                resolved_value=None,
                fallback_eligible=False,
                fallback_ref=None,
                blocker_codes=(
                    ()
                    if field.name in optional_field_ids
                    else (ReasonCode.REQUIRED_INPUT_MISSING,)
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
            else (ReasonCode.REQUIRED_INPUT_MISSING,)
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
            dependency_refs=dependency_refs,
            parameter_policy_refs=parameter_policy_refs,
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
        optional_field_ids: tuple[str, ...] = (),
        dependency_refs: tuple[str, ...] = (),
        downstream_consumer_refs: tuple[str, ...] = (
            "QKUComputationControlPlaneServiceV1",
        ),
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
        if (
            not isinstance(optional_field_ids, tuple)
            or len(set(optional_field_ids)) != len(optional_field_ids)
        ):
            raise InputResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "optional fields must be a unique immutable tuple",
            )

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
                        source_identity=None,
                        source_state_id=None,
                        source_epoch_id=None,
                        rights_state=None,
                        point_in_time_receipt=None,
                        freshness_receipt=None,
                        conversion_receipt=None,
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
            pit_receipt = PointInTimeResolverV1.resolve(
                evidence.point_in_time,
                context,
            )
            if not pit_receipt.available:
                blockers_list.extend(pit_receipt.blocker_codes)
            freshness_receipt = FreshnessResolverV1.resolve_field(
                subject_id=f"{math_id}::{field.name}",
                observed_time=evidence.point_in_time.observed_time,
                as_of_time=context.as_of,
                policy=evidence.freshness_policy,
            )
            if not freshness_receipt.fresh:
                blockers_list.extend(freshness_receipt.blocker_codes)
            if evidence.source_epoch_id != context.source_epoch_id:
                blockers_list.append(ReasonCode.SOURCE_EPOCH_MISSING)
            if evidence.rights_state.casefold() in {
                "blocked",
                "denied",
                "unknown",
                "unresolved",
            }:
                blockers_list.append(ReasonCode.SOURCE_RIGHTS_BLOCKED)

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
            if ReasonCode.INPUT_TYPE_MISMATCH in blockers:
                state = InputAvailabilityStateV1.TYPE_MISMATCH
            elif any(
                code
                in {
                    ReasonCode.POINT_IN_TIME_UNAVAILABLE,
                    ReasonCode.REVISION_LEAKAGE,
                }
                for code in blockers
            ):
                state = InputAvailabilityStateV1.POINT_IN_TIME_BLOCKED
            elif any(
                code in {ReasonCode.FIELD_STALE, ReasonCode.FRESHNESS_UNKNOWN}
                for code in blockers
            ):
                state = InputAvailabilityStateV1.STALE_BLOCKED
            elif any(
                code
                in {
                    ReasonCode.SOURCE_EPOCH_MISSING,
                    ReasonCode.SOURCE_RIGHTS_BLOCKED,
                }
                for code in blockers
            ):
                state = InputAvailabilityStateV1.SOURCE_BINDING_BLOCKED
            elif blockers:
                state = InputAvailabilityStateV1.UNIT_OR_BASIS_BLOCKED
            else:
                state = InputAvailabilityStateV1.RESOLVED
                arguments.append((field.name, decoded))
            source_owners.append(evidence.source_identity)
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
                    source_identity=evidence.source_identity,
                    source_state_id=evidence.source_state_id,
                    source_epoch_id=evidence.source_epoch_id,
                    rights_state=evidence.rights_state,
                    point_in_time_receipt=pit_receipt,
                    freshness_receipt=freshness_receipt,
                    conversion_receipt=conversion_receipt,
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
        parameter_refs = (
            ()
            if formula_contract is None
            else formula_contract.parameter_policy_refs
        )
        digest = "|".join(
            (
                math_id,
                context.stable_key,
                *(f"{row.input_field_id}:{row.state.value}" for row in rows),
                *(code.value for code in aggregate),
            )
        )
        return InputResolutionReceiptV1(
            receipt_id=f"INPUT::{sha256(digest.encode('utf-8')).hexdigest()}",
            component_id=math_id,
            inputs=tuple(rows),
            resolved_arguments=tuple(arguments),
            blocker_codes=aggregate,
            dependency_refs=dependency_refs,
            parameter_policy_refs=parameter_refs,
            source_owner_refs=tuple(dict.fromkeys(source_owners)),
            downstream_consumer_refs=downstream_consumer_refs,
            terminal_route=(
                "QKUComputationControlPlaneServiceV1::COMPUTE_COMPONENT"
                if not aggregate
                else "research_agent::INPUT_MATERIALIZATION_OR_REBINDING"
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
