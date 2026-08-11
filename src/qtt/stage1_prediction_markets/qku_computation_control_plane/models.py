"""Frozen data contracts owned by QKUComputationControlPlaneV1."""

from __future__ import annotations

from dataclasses import dataclass, field, fields as dataclass_fields
from datetime import datetime
from decimal import Decimal
from enum import Enum, StrEnum
import re
from types import MappingProxyType
from typing import ClassVar, Mapping, TypeVar

from .context import ComputationContextKeyV1, parse_utc
from .errors import ContractValidationError, ReasonCode


def _required(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT, f"{field_name} is required"
        )


def _canonical_text(value: object, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be nonempty canonical text",
        )
    return value


@dataclass(frozen=True, slots=True)
class NoEffectFlagsV1:
    """One shared exact-false custody value for every ST12 no-effect record."""

    provider_connection_allowed: bool = False
    private_state_read_allowed: bool = False
    replay_or_paper_execution_allowed: bool = False
    llm_inference_allowed: bool = False
    qpu_execution_allowed: bool = False
    mode_or_allow_activation_allowed: bool = False
    order_release_allowed: bool = False
    capital_mutation_allowed: bool = False

    def __post_init__(self) -> None:
        for field_definition in dataclass_fields(self):
            value = getattr(self, field_definition.name)
            if type(value) is not bool or value:
                raise ContractValidationError(
                    ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                    f"no-effect flag {field_definition.name} must be exact false",
                )


NO_EFFECTS_V1 = NoEffectFlagsV1()


@dataclass(frozen=True, slots=True)
class ComputationScopeV1:
    """Exact economic/data scope; it creates no runtime or trading authority."""

    market_scope_id: str
    venue_scope_id: str
    event_scope_id: str
    instrument_or_contract_scope_id: str
    mode_context_id: str
    input_snapshot_id: str

    def __post_init__(self) -> None:
        for name in (
            "market_scope_id",
            "venue_scope_id",
            "event_scope_id",
            "instrument_or_contract_scope_id",
            "mode_context_id",
            "input_snapshot_id",
        ):
            _canonical_text(getattr(self, name), name)

    @property
    def identity_tuple(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.market_scope_id,
            self.venue_scope_id,
            self.event_scope_id,
            self.instrument_or_contract_scope_id,
            self.mode_context_id,
            self.input_snapshot_id,
        )


@dataclass(frozen=True, slots=True)
class ImplementationVersionPinV1:
    """One exact implementation identity for one declared mathematical ID."""

    math_spec_id: str
    implementation_id: str

    def __post_init__(self) -> None:
        _canonical_text(self.math_spec_id, "math_spec_id")
        _canonical_text(self.implementation_id, "implementation_id")


@dataclass(frozen=True, slots=True)
class ComputationExecutionContextV1(ComputationContextKeyV1):
    """One temporal, economic/data, and computation-plan execution identity."""

    scope: ComputationScopeV1
    binding_profile_version: str
    parameter_policy_version: str
    implementation_versions: tuple[ImplementationVersionPinV1, ...]
    dependency_graph_id: str | None = None
    dependency_graph_version: str | None = None

    def __post_init__(self) -> None:
        ComputationContextKeyV1.__post_init__(self)
        if type(self.scope) is not ComputationScopeV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "scope must be an exact ComputationScopeV1",
            )
        _canonical_text(
            self.binding_profile_version,
            "binding_profile_version",
        )
        _canonical_text(
            self.parameter_policy_version,
            "parameter_policy_version",
        )
        if (
            not isinstance(self.implementation_versions, tuple)
            or not self.implementation_versions
            or any(
                type(pin) is not ImplementationVersionPinV1
                for pin in self.implementation_versions
            )
            or len(
                {pin.math_spec_id for pin in self.implementation_versions}
            )
            != len(self.implementation_versions)
            or len(
                {pin.implementation_id for pin in self.implementation_versions}
            )
            != len(self.implementation_versions)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "implementation_versions must be ordered, nonempty, and unique",
            )
        graph_values = (
            self.dependency_graph_id,
            self.dependency_graph_version,
        )
        if (graph_values[0] is None) != (graph_values[1] is None):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "dependency graph ID and version must be both present or both absent",
            )
        if graph_values[0] is not None:
            _canonical_text(graph_values[0], "dependency_graph_id")
            _canonical_text(graph_values[1], "dependency_graph_version")

    @property
    def execution_identity_tuple(self) -> tuple[object, ...]:
        return (
            self.context_id,
            self.as_of,
            self.observed_at,
            self.source_epoch_id,
            self.input_version,
            self.maximum_age,
            *self.scope.identity_tuple,
            self.binding_profile_version,
            self.parameter_policy_version,
            tuple(
                (pin.math_spec_id, pin.implementation_id)
                for pin in self.implementation_versions
            ),
            self.dependency_graph_id,
            self.dependency_graph_version,
        )

    @property
    def stable_key(self) -> str:
        """Diagnostic projection only; the typed object is semantic authority."""

        return repr(self.execution_identity_tuple)


def _exact_bool(value: object, field_name: str) -> None:
    if type(value) is not bool:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT, f"{field_name} must be a boolean"
        )


def _text_tuple(
    values: object,
    field_name: str,
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if not isinstance(values, tuple) or any(
        not isinstance(value, str) or not value.strip() for value in values
    ):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be a tuple of nonempty strings",
        )
    if require_nonempty and not values:
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT, f"{field_name} must be nonempty"
        )
    return values


_EnumT = TypeVar("_EnumT", bound=Enum)


def _typed_enum(value: object, enum_type: type[_EnumT], field_name: str) -> _EnumT:
    if not isinstance(value, enum_type):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be a typed {enum_type.__name__} value",
        )
    return value


def _reason_tuple(
    values: object,
    field_name: str,
    *,
    require_nonempty: bool = False,
) -> tuple[ReasonCode, ...]:
    if (
        not isinstance(values, tuple)
        or any(type(value) is not ReasonCode for value in values)
        or len(values) != len(set(values))
        or (require_nonempty and not values)
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{field_name} must be an ordered unique tuple of ReasonCode values",
        )
    return values


def _utc_timestamp(value: object, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
        or value.utcoffset().total_seconds() != 0
    ):
        raise ContractValidationError(
            ReasonCode.CLOCK_DOMAIN_MISMATCH,
            f"{field_name} must be a timezone-aware UTC datetime",
        )
    return value


def _must_be_false(value: object, field_name: str) -> None:
    _exact_bool(value, field_name)
    if value is not False:
        raise ContractValidationError(
            ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
            f"{field_name} must remain exact false in ST12-D",
        )


def immutable_mapping(values: Mapping[str, str] | None = None) -> Mapping[str, str]:
    if values is None:
        return MappingProxyType({})
    if not isinstance(values, Mapping) or any(
        not isinstance(key, str)
        or not key.strip()
        or not isinstance(value, str)
        or not value.strip()
        for key, value in values.items()
    ):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "metadata must map nonempty string keys to nonempty string values",
        )
    return MappingProxyType(dict(values))


class ObjectiveSense(StrEnum):
    MINIMIZE = "MINIMIZE"
    MAXIMIZE = "MAXIMIZE"


class VariableDomain(StrEnum):
    BINARY = "BINARY"
    INTEGER = "INTEGER"
    REAL = "REAL"
    DISCRETE = "DISCRETE"


class BenchmarkSignConvention(StrEnum):
    BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS = (
        "BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS"
    )
    CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS = (
        "CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS"
    )


class ModeEligibilityState(StrEnum):
    INELIGIBLE = "INELIGIBLE"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    ELIGIBLE_FOR_ALLOW_CANDIDACY_NO_EFFECT = (
        "ELIGIBLE_FOR_ALLOW_CANDIDACY_NO_EFFECT"
    )


class AllowCandidateStateV1(StrEnum):
    NOT_EVALUATED = "NOT_EVALUATED"
    BLOCKED = "BLOCKED"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"
    OWNER_CONFIRMATION_REQUIRED = "OWNER_CONFIRMATION_REQUIRED"
    ELIGIBLE_NOT_ACTIVATED = "ELIGIBLE_NOT_ACTIVATED"


class ActivationPreconditionStateV1(StrEnum):
    NOT_AUTHORIZED_D_HOLD = "NOT_AUTHORIZED_D_HOLD"
    PRECONDITIONS_INCOMPLETE = "PRECONDITIONS_INCOMPLETE"
    PRECONDITIONS_SATISFIED_HELD = "PRECONDITIONS_SATISFIED_HELD"


class SnapshotCandidateStateV1(StrEnum):
    ABSENT = "ABSENT"
    BUILT_IMMUTABLE = "BUILT_IMMUTABLE"
    VALIDATED_NO_EFFECT = "VALIDATED_NO_EFFECT"
    REJECTED = "REJECTED"
    STALE = "STALE"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    RETIRED = "RETIRED"


class KillStateV1(StrEnum):
    CLEAR_CURRENT = "CLEAR_CURRENT"
    ACTIVE = "ACTIVE"
    MISSING_STALE_OR_CONFLICTING = "MISSING_STALE_OR_CONFLICTING"


class SubmitDisabledStateV1(StrEnum):
    SUBMIT_ENABLED_READ_ONLY = "SUBMIT_ENABLED_READ_ONLY"
    SUBMIT_DISABLED = "SUBMIT_DISABLED"
    MISSING_STALE_OR_CONFLICTING = "MISSING_STALE_OR_CONFLICTING"


class ST12FEvidenceStateV1(StrEnum):
    EVIDENCE_REFERENCE_AVAILABLE = "EVIDENCE_REFERENCE_AVAILABLE"
    EVIDENCE_REFERENCE_STALE = "EVIDENCE_REFERENCE_STALE"
    EVIDENCE_REFERENCE_CONFLICTING = "EVIDENCE_REFERENCE_CONFLICTING"
    EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED = (
        "EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED"
    )
    EVIDENCE_INSUFFICIENT_FAIL_CLOSED = "EVIDENCE_INSUFFICIENT_FAIL_CLOSED"


class SnapshotParameterResolutionStateV1(StrEnum):
    """Finite resolution states owned by ComputationParameterPolicyV1."""

    OWNER_VALUE_RESOLVED = "OWNER_VALUE_RESOLVED"
    DETERMINISTIC_POLICY_VALUE_MATERIALIZED = (
        "DETERMINISTIC_POLICY_VALUE_MATERIALIZED"
    )
    REQUIRED_OWNER_VALUE_UNAVAILABLE = "REQUIRED_OWNER_VALUE_UNAVAILABLE"


class OwnerActionConfirmationStateV1(StrEnum):
    CONFIRMED_CURRENT = "CONFIRMED_CURRENT"
    ABSENT = "ABSENT"
    STALE_OR_CONFLICTING = "STALE_OR_CONFLICTING"


class SnapshotRollbackStateV1(StrEnum):
    NONE = "NONE"
    PROPOSED_PRIOR_IMMUTABLE_CANDIDATE = (
        "PROPOSED_PRIOR_IMMUTABLE_CANDIDATE"
    )
    BLOCKED_NO_VALID_PRIOR_CANDIDATE = "BLOCKED_NO_VALID_PRIOR_CANDIDATE"


class SnapshotRetirementStateV1(StrEnum):
    CURRENT = "CURRENT"
    DRAINING_PINNED_IN_FLIGHT_ONLY = "DRAINING_PINNED_IN_FLIGHT_ONLY"
    RETIRED = "RETIRED"


class EvidenceState(StrEnum):
    UNVALIDATED = "UNVALIDATED"
    INDEPENDENTLY_VALIDATED = "INDEPENDENTLY_VALIDATED"
    REJECTED = "REJECTED"


class SnapshotState(StrEnum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    VERSION_PINNED = "VERSION_PINNED"
    INVALID = "INVALID"


class TransactionState(StrEnum):
    IN_MEMORY_ONLY = "IN_MEMORY_ONLY"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class HealthState(StrEnum):
    UNKNOWN = "UNKNOWN"
    HEALTHY_CONTRACT = "HEALTHY_CONTRACT"
    DEGRADED_CONTRACT = "DEGRADED_CONTRACT"
    HALTED_CONTRACT = "HALTED_CONTRACT"


class OperationCapabilityClass(StrEnum):
    CONTRACT_DEFINITION_ONLY = "CONTRACT_DEFINITION_ONLY"
    PURE_DETERMINISTIC_COMPUTATION = "PURE_DETERMINISTIC_COMPUTATION"
    READ_ONLY_PROJECTION = "READ_ONLY_PROJECTION"
    NO_EFFECT_RECORD = "NO_EFFECT_RECORD"


class OperationSideEffectClass(StrEnum):
    PURE_OR_APPEND_ONLY_NON_PROVIDER_EFFECT = (
        "PURE_OR_APPEND_ONLY_NON_PROVIDER_EFFECT"
    )


class OperationStatusV1(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"


class OperationBlockerCodeV1(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHORITY_DENIED = "AUTHORITY_DENIED"
    IDENTITY_UNVERIFIED = "IDENTITY_UNVERIFIED"
    SPECIFICATION_INCOMPLETE = "SPECIFICATION_INCOMPLETE"
    FIXTURE_UNAVAILABLE = "FIXTURE_UNAVAILABLE"
    CONTEXT_BINDING_INVALID = "CONTEXT_BINDING_INVALID"
    CONTEXT_STALE = "CONTEXT_STALE"
    STACK_INCOMPLETE = "STACK_INCOMPLETE"
    DEPENDENCY_UNRESOLVED = "DEPENDENCY_UNRESOLVED"
    ORACLE_UNAVAILABLE = "ORACLE_UNAVAILABLE"
    RUNTIME_EFFECT_FORBIDDEN = "RUNTIME_EFFECT_FORBIDDEN"
    NO_APPLICABLE_STACK = "NO_APPLICABLE_STACK"
    INPUT_OWNER_MISSING = "INPUT_OWNER_MISSING"
    INPUT_OWNER_MISMATCH = "INPUT_OWNER_MISMATCH"
    INPUT_PACKET_MISMATCH = "INPUT_PACKET_MISMATCH"
    INPUT_SCHEMA_MISMATCH = "INPUT_SCHEMA_MISMATCH"
    INPUT_SCOPE_MISMATCH = "INPUT_SCOPE_MISMATCH"
    INPUT_VALUE_CONFLICT = "INPUT_VALUE_CONFLICT"
    POINT_IN_TIME_VIOLATION = "POINT_IN_TIME_VIOLATION"
    FRESHNESS_VIOLATION = "FRESHNESS_VIOLATION"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    PARAMETER_OWNER_MISSING = "PARAMETER_OWNER_MISSING"
    PARAMETER_BINDING_MISMATCH = "PARAMETER_BINDING_MISMATCH"
    UNIT_CONVERSION_FAILED = "UNIT_CONVERSION_FAILED"
    OUTPUT_SCHEMA_MISMATCH = "OUTPUT_SCHEMA_MISMATCH"
    FORMULA_EXECUTION_REJECTED = "FORMULA_EXECUTION_REJECTED"
    MODE_SNAPSHOT_BLOCKED = "MODE_SNAPSHOT_BLOCKED"
    EVIDENCE_REFERENCE_UNAVAILABLE = "EVIDENCE_REFERENCE_UNAVAILABLE"
    KILL_OR_SUBMIT_DISABLED = "KILL_OR_SUBMIT_DISABLED"
    LATENCY_PROFILE_REQUIRED = "LATENCY_PROFILE_REQUIRED"


class TypedValueKindV1(StrEnum):
    TEXT = "TEXT"
    DECIMAL = "DECIMAL"
    FLOAT64 = "FLOAT64"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"


@dataclass(frozen=True, slots=True)
class TypedValueV1:
    name: str
    kind: TypedValueKindV1
    value: str | Decimal | float | int | bool
    unit: str
    basis: str

    def __post_init__(self) -> None:
        _required(self.name, "name")
        _typed_enum(self.kind, TypedValueKindV1, "kind")
        _required(self.unit, "unit")
        _required(self.basis, "basis")
        valid = (
            self.kind is TypedValueKindV1.TEXT
            and isinstance(self.value, str)
            or self.kind is TypedValueKindV1.DECIMAL
            and isinstance(self.value, Decimal)
            and not isinstance(self.value, bool)
            and self.value.is_finite()
            or self.kind is TypedValueKindV1.FLOAT64
            and isinstance(self.value, float)
            and self.value == self.value
            and self.value not in (float("inf"), float("-inf"))
            or self.kind is TypedValueKindV1.INTEGER
            and isinstance(self.value, int)
            and not isinstance(self.value, bool)
            or self.kind is TypedValueKindV1.BOOLEAN
            and type(self.value) is bool
        )
        if not valid:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                f"{self.name} does not match typed value kind {self.kind.value}",
            )


@dataclass(frozen=True, slots=True)
class TypedValueRecordV1:
    fields: tuple[TypedValueV1, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.fields, tuple)
            or not self.fields
            or any(not isinstance(value, TypedValueV1) for value in self.fields)
            or len({value.name for value in self.fields}) != len(self.fields)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "typed records require a nonempty unique TypedValueV1 tuple",
            )


class ComputabilityClassV1(StrEnum):
    SPECIFICATION_COMPUTABLE = "SPECIFICATION_COMPUTABLE"
    FIXTURE_COMPUTABLE = "FIXTURE_COMPUTABLE"
    CONTEXT_COMPUTABLE = "CONTEXT_COMPUTABLE"
    STACK_COMPUTABLE = "STACK_COMPUTABLE"


class ComputabilityBlockerCodeV1(StrEnum):
    SPECIFICATION_SEMANTICS_INCOMPLETE = "SPECIFICATION_SEMANTICS_INCOMPLETE"
    IMPLEMENTATION_CALLABLE_MISSING = "IMPLEMENTATION_CALLABLE_MISSING"
    INDEPENDENT_ORACLE_MISSING = "INDEPENDENT_ORACLE_MISSING"
    INDEPENDENT_VECTOR_MISSING = "INDEPENDENT_VECTOR_MISSING"
    CONTEXT_BINDING_MISMATCH = "CONTEXT_BINDING_MISMATCH"
    SOURCE_EPOCH_MISMATCH = "SOURCE_EPOCH_MISMATCH"
    UNIT_OR_BASIS_MISMATCH = "UNIT_OR_BASIS_MISMATCH"
    CONTEXT_STALE = "CONTEXT_STALE"
    PARAMETER_BINDING_MISMATCH = "PARAMETER_BINDING_MISMATCH"
    AUTHORITY_ENVELOPE_INVALID = "AUTHORITY_ENVELOPE_INVALID"
    DEPENDENCY_CLOSURE_INCOMPLETE = "DEPENDENCY_CLOSURE_INCOMPLETE"
    FALLBACK_CLOSURE_INCOMPLETE = "FALLBACK_CLOSURE_INCOMPLETE"
    ORPHAN_CONSUMER = "ORPHAN_CONSUMER"
    INPUT_OWNER_MISSING = "INPUT_OWNER_MISSING"
    INPUT_OWNER_MISMATCH = "INPUT_OWNER_MISMATCH"
    INPUT_PACKET_MISMATCH = "INPUT_PACKET_MISMATCH"
    INPUT_SCHEMA_MISMATCH = "INPUT_SCHEMA_MISMATCH"
    INPUT_SCOPE_MISMATCH = "INPUT_SCOPE_MISMATCH"
    INPUT_VALUE_CONFLICT = "INPUT_VALUE_CONFLICT"
    POINT_IN_TIME_VIOLATION = "POINT_IN_TIME_VIOLATION"
    FRESHNESS_VIOLATION = "FRESHNESS_VIOLATION"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    PARAMETER_OWNER_MISSING = "PARAMETER_OWNER_MISSING"
    NO_APPLICABLE_STACK = "NO_APPLICABLE_STACK"


class ComputabilityTerminalRouteV1(StrEnum):
    CONTRACT_ONLY_COMPUTATION = "CONTRACT_ONLY_COMPUTATION"
    SPECIFICATION_OWNER_REVIEW = "SPECIFICATION_OWNER_REVIEW"
    FIXTURE_MATERIALIZATION = "FIXTURE_MATERIALIZATION"
    CONTEXT_REBINDING = "CONTEXT_REBINDING"
    STACK_CLOSURE = "STACK_CLOSURE"
    OWNER_PACKET_REFRESH = "OWNER_PACKET_REFRESH"
    SOURCE_RECONCILIATION = "SOURCE_RECONCILIATION"
    PARAMETER_OWNER_REFRESH = "PARAMETER_OWNER_REFRESH"
    NO_RESULT_NO_TRADE = "NO_RESULT_NO_TRADE"


@dataclass(frozen=True, slots=True)
class ComputabilityStateResultV1:
    state: ComputabilityClassV1
    computable: bool
    blocker_codes: tuple[ComputabilityBlockerCodeV1, ...]
    dependency_receipt_refs: tuple[str, ...]
    oracle_receipt_refs: tuple[str, ...]
    terminal_route: ComputabilityTerminalRouteV1
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        _typed_enum(self.state, ComputabilityClassV1, "state")
        _exact_bool(self.computable, "computable")
        if (
            not isinstance(self.blocker_codes, tuple)
            or any(
                not isinstance(value, ComputabilityBlockerCodeV1)
                for value in self.blocker_codes
            )
            or len(set(self.blocker_codes)) != len(self.blocker_codes)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "computability blocker codes must be a unique typed tuple",
            )
        for name in ("dependency_receipt_refs", "oracle_receipt_refs"):
            values = _text_tuple(getattr(self, name), name)
            if len(set(values)) != len(values):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be unique",
                )
        _typed_enum(
            self.terminal_route,
            ComputabilityTerminalRouteV1,
            "terminal_route",
        )
        _exact_bool(self.no_authority_flag, "no_authority_flag")
        if not self.no_authority_flag:
            raise ContractValidationError(
                ReasonCode.CAPABILITY_DENIED,
                "computability state cannot create authority",
            )
        if self.computable == bool(self.blocker_codes):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "computable states have no blockers and blocked states require blockers",
            )


@dataclass(frozen=True, slots=True)
class ContextualComputabilityResolutionV1:
    specification: ComputabilityStateResultV1
    fixture: ComputabilityStateResultV1
    context: ComputabilityStateResultV1
    stack: ComputabilityStateResultV1

    def __post_init__(self) -> None:
        expected = (
            ComputabilityClassV1.SPECIFICATION_COMPUTABLE,
            ComputabilityClassV1.FIXTURE_COMPUTABLE,
            ComputabilityClassV1.CONTEXT_COMPUTABLE,
            ComputabilityClassV1.STACK_COMPUTABLE,
        )
        values = (self.specification, self.fixture, self.context, self.stack)
        if any(
            not isinstance(value, ComputabilityStateResultV1)
            for value in values
        ) or tuple(value.state for value in values) != expected:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "computability resolution must carry the four independent states",
            )


@dataclass(frozen=True, slots=True)
class ContractFieldV1:
    name: str
    type_name: str
    required: bool = True

    def __post_init__(self) -> None:
        _required(self.name, "name")
        _required(self.type_name, "type_name")
        _exact_bool(self.required, "required")


@dataclass(frozen=True, slots=True)
class SnapshotBoundaryOwnerViewV1:
    owner_id: str
    source_version: str
    source_path: str
    authority_class: str
    readiness_state: str
    latency_scope: str
    report_contracts: tuple[str, ...]
    boundary_types: tuple[str, ...]
    producer_lanes: tuple[str, ...]
    future_consumer_lanes: tuple[str, ...]
    not_created_flags: tuple[str, ...]
    activation_allowed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "owner_id",
            "source_version",
            "source_path",
            "authority_class",
            "readiness_state",
            "latency_scope",
        ):
            _required(getattr(self, name), name)
        for name in (
            "report_contracts",
            "boundary_types",
            "producer_lanes",
            "future_consumer_lanes",
            "not_created_flags",
        ):
            values = _text_tuple(
                getattr(self, name), name, require_nonempty=True
            )
            if len(set(values)) != len(values):
                raise ContractValidationError(
                    ReasonCode.OWNER_DATA_CONTRADICTORY,
                    f"{name} contains duplicate owner facts",
                )
        _exact_bool(self.activation_allowed, "activation_allowed")
        if self.activation_allowed:
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "snapshot owner view cannot activate the hot path",
            )
        from .serialization import validate_relative_path

        validate_relative_path(self.source_path)


class LatencyHotPathSnapshotBoundaryAdapterV1:
    """Explicit immutable view over the existing PR137L boundary owner."""

    @staticmethod
    def load_view() -> SnapshotBoundaryOwnerViewV1:
        from src.qtt.stage1_prediction_markets.latency_hot_path_snapshot_boundary.constants import (
            AUTHORITY_CLASS,
            CONTROL_PLANE_PRODUCER_LANES,
            FUTURE_LIVE_CONSUMER_LANES,
            LATENCY_SCOPE,
            NOT_CREATED_FLAGS,
            PR_ID,
            PRECOMPUTED_SNAPSHOT_BOUNDARY_TYPES,
            READINESS_STATE,
        )
        from src.qtt.stage1_prediction_markets.latency_hot_path_snapshot_boundary.model import (
            DependencyChainSnapshot,
            PR137RStaticEvidenceSnapshot,
            ValidationOutcome,
        )

        return SnapshotBoundaryOwnerViewV1(
            owner_id="LATENCY_HOT_PATH_SNAPSHOT_BOUNDARY",
            source_version=PR_ID,
            source_path=(
                "src/qtt/stage1_prediction_markets/"
                "latency_hot_path_snapshot_boundary/constants.py"
            ),
            authority_class=AUTHORITY_CLASS,
            readiness_state=READINESS_STATE,
            latency_scope=LATENCY_SCOPE,
            report_contracts=(
                PR137RStaticEvidenceSnapshot.__name__,
                DependencyChainSnapshot.__name__,
                ValidationOutcome.__name__,
            ),
            boundary_types=tuple(PRECOMPUTED_SNAPSHOT_BOUNDARY_TYPES),
            producer_lanes=tuple(CONTROL_PLANE_PRODUCER_LANES),
            future_consumer_lanes=tuple(FUTURE_LIVE_CONSUMER_LANES),
            not_created_flags=tuple(NOT_CREATED_FLAGS),
        )


@dataclass(frozen=True, slots=True)
class OwnerLineageV1:
    owner_id: str
    source_identity: str
    source_version: str
    source_path: str

    def __post_init__(self) -> None:
        for name in ("owner_id", "source_identity", "source_version", "source_path"):
            _required(getattr(self, name), name)
        from .serialization import validate_relative_path

        validate_relative_path(self.source_path)


@dataclass(frozen=True, slots=True)
class UnitBindingV1:
    field_name: str
    unit: str
    basis: str

    def __post_init__(self) -> None:
        _required(self.field_name, "field_name")
        _required(self.unit, "unit")
        _required(self.basis, "basis")


@dataclass(frozen=True, slots=True)
class ComputationSpecificationV1:
    qku_id: str
    formula_id: str
    specification_version: str
    implementation_id: str
    binding_id: str
    oracle_id: str
    context_key: str
    units: tuple[UnitBindingV1, ...]
    parameter_ids: tuple[str, ...] = ()
    dependency_ids: tuple[str, ...] = ()
    source_epoch_ids: tuple[str, ...] = ()
    deterministic_seed: int | None = None

    def __post_init__(self) -> None:
        for name in (
            "qku_id",
            "formula_id",
            "specification_version",
            "implementation_id",
            "binding_id",
            "oracle_id",
            "context_key",
        ):
            _required(getattr(self, name), name)
        if not self.units:
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT, "at least one unit binding is required"
            )
        if not isinstance(self.units, tuple) or any(
            not isinstance(unit, UnitBindingV1) for unit in self.units
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "units must be a tuple of typed UnitBindingV1 values",
            )
        if len({unit.field_name for unit in self.units}) != len(self.units):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "unit binding field names must be unique",
            )
        for values, label in (
            (self.parameter_ids, "parameter_ids"),
            (self.dependency_ids, "dependency_ids"),
            (self.source_epoch_ids, "source_epoch_ids"),
        ):
            _text_tuple(values, label)
            if len(values) != len(set(values)):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT, f"{label} contains duplicates"
                )
        from .parameter_policy import get_parameter_policy

        for parameter_id in self.parameter_ids:
            get_parameter_policy(parameter_id)
        if self.deterministic_seed is not None and (
            isinstance(self.deterministic_seed, bool)
            or not isinstance(self.deterministic_seed, int)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "deterministic_seed must be an integer when declared",
            )


@dataclass(frozen=True, slots=True)
class ComputationImplementationV1:
    implementation_id: str
    math_spec_id: str
    callable_name: str
    specification_version: str
    deterministic: bool
    seed_required: bool
    mandatory_external_dependency: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "implementation_id",
            "math_spec_id",
            "callable_name",
            "specification_version",
        ):
            _required(getattr(self, name), name)
        _exact_bool(self.deterministic, "deterministic")
        _exact_bool(self.seed_required, "seed_required")
        if self.mandatory_external_dependency is not None:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "Tranche A implementations may not require external dependencies",
            )


@dataclass(frozen=True, slots=True)
class SourceBindingV1:
    source_state_id: str
    stable_source_identity: str
    effective_epoch: str
    rights_state: str
    freshness_policy: str

    def __post_init__(self) -> None:
        for name in (
            "source_state_id",
            "stable_source_identity",
            "effective_epoch",
            "rights_state",
            "freshness_policy",
        ):
            _required(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class ComputationBindingProfileV1:
    binding_id: str
    version: str
    input_bindings: tuple[UnitBindingV1, ...]
    source_bindings: tuple[SourceBindingV1, ...]
    venue_scope: tuple[str, ...] = ()
    portfolio_scope: str = "NO_PRIVATE_STATE"

    def __post_init__(self) -> None:
        _required(self.binding_id, "binding_id")
        _required(self.version, "version")
        _required(self.portfolio_scope, "portfolio_scope")
        if not isinstance(self.input_bindings, tuple) or any(
            not isinstance(item, UnitBindingV1) for item in self.input_bindings
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "input_bindings must be typed UnitBindingV1 values",
            )
        if not isinstance(self.source_bindings, tuple) or any(
            not isinstance(item, SourceBindingV1) for item in self.source_bindings
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "source_bindings must be typed SourceBindingV1 values",
            )
        _text_tuple(self.venue_scope, "venue_scope")
        if len({item.field_name for item in self.input_bindings}) != len(
            self.input_bindings
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT, "input bindings contain duplicates"
            )
        if len({item.source_state_id for item in self.source_bindings}) != len(
            self.source_bindings
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT, "source bindings contain duplicates"
            )
        if len(set(self.venue_scope)) != len(self.venue_scope):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT, "venue_scope contains duplicates"
            )
        if self.portfolio_scope != "NO_PRIVATE_STATE":
            raise ContractValidationError(
                ReasonCode.CAPABILITY_DENIED,
                "Tranche A binding profiles cannot authorize private state",
            )


@dataclass(frozen=True, slots=True)
class DependencyNodeV1:
    node_id: str
    output_unit: str
    timing_class: str
    material: bool = True

    def __post_init__(self) -> None:
        _required(self.node_id, "node_id")
        _required(self.output_unit, "output_unit")
        _required(self.timing_class, "timing_class")
        _exact_bool(self.material, "material")


@dataclass(frozen=True, slots=True)
class DependencyEdgeV1:
    upstream_id: str
    downstream_id: str
    supplied_unit: str
    required_unit: str
    timing_class: str

    def __post_init__(self) -> None:
        for name in (
            "upstream_id",
            "downstream_id",
            "supplied_unit",
            "required_unit",
            "timing_class",
        ):
            _required(getattr(self, name), name)
        if self.upstream_id == self.downstream_id:
            raise ContractValidationError(
                ReasonCode.DEPENDENCY_CYCLE, "self-dependencies are forbidden"
            )


@dataclass(frozen=True, slots=True)
class OracleContractV1:
    oracle_id: str
    math_spec_id: str
    oracle_version: str
    comparison_policy: str
    expected_value_json: str
    independent_algorithm_steps: tuple[str, ...]
    production_import_allowed: bool = False
    primary_validator_import_allowed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "oracle_id",
            "math_spec_id",
            "oracle_version",
            "comparison_policy",
            "expected_value_json",
        ):
            _required(getattr(self, name), name)
        _text_tuple(
            self.independent_algorithm_steps,
            "independent_algorithm_steps",
            require_nonempty=True,
        )
        _exact_bool(self.production_import_allowed, "production_import_allowed")
        _exact_bool(
            self.primary_validator_import_allowed,
            "primary_validator_import_allowed",
        )
        from .serialization import safe_json_loads

        safe_json_loads(self.expected_value_json)
        if (
            self.production_import_allowed
            or self.primary_validator_import_allowed
            or not self.independent_algorithm_steps
        ):
            raise ContractValidationError(
                ReasonCode.ORACLE_NOT_INDEPENDENT,
                "oracle must be independently specified without production imports",
            )


@dataclass(frozen=True, slots=True)
class GoldenVectorV1:
    vector_id: str
    math_spec_id: str
    oracle_id: str
    vector_kind: str
    comparison_policy: str
    inputs_json: str
    expected_json: str
    seed: int | None
    production_import_allowed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "vector_id",
            "math_spec_id",
            "oracle_id",
            "vector_kind",
            "comparison_policy",
            "inputs_json",
            "expected_json",
        ):
            _required(getattr(self, name), name)
        if self.seed is not None and (
            isinstance(self.seed, bool) or not isinstance(self.seed, int)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT, "golden-vector seed must be an integer"
            )
        _exact_bool(self.production_import_allowed, "production_import_allowed")
        from .serialization import safe_json_loads

        safe_json_loads(self.inputs_json)
        safe_json_loads(self.expected_json)
        if self.production_import_allowed:
            raise ContractValidationError(
                ReasonCode.ORACLE_NOT_INDEPENDENT,
                "golden vectors may not authorize production expected-value imports",
            )


@dataclass(frozen=True, slots=True)
class LegacyComputationEvidenceOrthogonalityViewV1:
    """Retained architecture-only provenance; never canonical F evidence."""

    evidence_id: str
    specification_id: str
    oracle_id: str
    state: EvidenceState
    independent_results: tuple[str, ...]
    mutation_results: tuple[str, ...]

    def __post_init__(self) -> None:
        _required(self.evidence_id, "evidence_id")
        _required(self.specification_id, "specification_id")
        _required(self.oracle_id, "oracle_id")
        _typed_enum(self.state, EvidenceState, "state")
        _text_tuple(self.independent_results, "independent_results")
        _text_tuple(self.mutation_results, "mutation_results")


@dataclass(frozen=True, slots=True)
class ComputationModeEligibilityV1:
    mode_id: str
    state: ModeEligibilityState = ModeEligibilityState.CONTRACT_ONLY
    allow_activation: bool = False
    grant_activation: bool = False
    order_release: bool = False

    def __post_init__(self) -> None:
        _required(self.mode_id, "mode_id")
        _typed_enum(self.state, ModeEligibilityState, "state")
        for name in ("allow_activation", "grant_activation", "order_release"):
            _exact_bool(getattr(self, name), name)
        if self.allow_activation or self.grant_activation or self.order_release:
            raise ContractValidationError(
                ReasonCode.CAPABILITY_DENIED,
                "Tranche A mode envelopes are contract-only and cannot activate authority",
            )


@dataclass(frozen=True, slots=True)
class ComputationExecutionReceiptV1:
    receipt_id: str
    specification_id: str
    implementation_id: str
    input_version: str
    output_json: str
    warnings: tuple[str, ...] = ()
    provider_effect: bool = False
    private_state_effect: bool = False
    replay_or_paper_effect: bool = False
    order_effect: bool = False
    qpu_effect: bool = False

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "specification_id",
            "implementation_id",
            "input_version",
            "output_json",
        ):
            _required(getattr(self, name), name)
        _text_tuple(self.warnings, "warnings")
        from .serialization import safe_json_loads

        safe_json_loads(self.output_json)
        for name in (
            "provider_effect",
            "private_state_effect",
            "replay_or_paper_effect",
            "order_effect",
            "qpu_effect",
        ):
            _exact_bool(getattr(self, name), name)
        if any(
            (
                self.provider_effect,
                self.private_state_effect,
                self.replay_or_paper_effect,
                self.order_effect,
                self.qpu_effect,
            )
        ):
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "Tranche A receipts cannot record an exercised runtime effect",
            )


@dataclass(frozen=True, slots=True)
class FormulaRuntimeSnapshotV1:
    snapshot_id: str
    specification_id: str
    implementation_version: str
    binding_version: str
    parameter_version: str
    source_epoch_ids: tuple[str, ...]
    state: SnapshotState = SnapshotState.CONTRACT_ONLY
    activated: bool = False

    def __post_init__(self) -> None:
        for name in (
            "snapshot_id",
            "specification_id",
            "implementation_version",
            "binding_version",
            "parameter_version",
        ):
            _required(getattr(self, name), name)
        _text_tuple(self.source_epoch_ids, "source_epoch_ids")
        if len(set(self.source_epoch_ids)) != len(self.source_epoch_ids):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "snapshot source epochs must be unique",
            )
        _typed_enum(self.state, SnapshotState, "state")
        _exact_bool(self.activated, "activated")
        if self.activated:
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "Tranche A snapshots cannot be activated",
            )


@dataclass(frozen=True, slots=True)
class ReadOnlyKillSubmitStateV1:
    """Current-owner safety state that ST12-D can only inspect."""

    state_ref: str
    scope_ref: str
    kill_active: bool
    submit_disabled: bool
    observed_at: datetime
    valid_until: datetime
    policy_version: str
    causation_id: str
    correlation_id: str

    def __post_init__(self) -> None:
        for name in (
            "state_ref",
            "scope_ref",
            "policy_version",
            "causation_id",
            "correlation_id",
        ):
            _canonical_text(getattr(self, name), name)
        _exact_bool(self.kill_active, "kill_active")
        _exact_bool(self.submit_disabled, "submit_disabled")
        observed = _utc_timestamp(self.observed_at, "observed_at")
        valid_until = _utc_timestamp(self.valid_until, "valid_until")
        if observed > valid_until:
            raise ContractValidationError(
                ReasonCode.POLICY_OR_SNAPSHOT_STALE,
                "kill/submit validity cannot precede its observation",
            )

    @property
    def kill_state(self) -> KillStateV1:
        return KillStateV1.ACTIVE if self.kill_active else KillStateV1.CLEAR_CURRENT

    @property
    def submit_disabled_state(self) -> SubmitDisabledStateV1:
        return (
            SubmitDisabledStateV1.SUBMIT_DISABLED
            if self.submit_disabled
            else SubmitDisabledStateV1.SUBMIT_ENABLED_READ_ONLY
        )


@dataclass(frozen=True, slots=True)
class ST12FEvidenceReferenceV1:
    """Typed reference boundary only; ST12-D never produces F evidence."""

    evidence_state: ST12FEvidenceStateV1
    evidence_ref: str
    lane: str
    dataset_grade_ref: str
    venue_semantic_binding_ref: str
    cross_venue_equivalence_ref: str
    observed_at: datetime
    valid_until: datetime
    policy_version: str
    causation_id: str
    correlation_id: str
    input_lock_id: str = "EXPLICIT_ABSENCE"
    component_or_template_ref: str = "EXPLICIT_ABSENCE"
    evidence_bundle_version: str = "EXPLICIT_ABSENCE"
    source_epoch_refs: tuple[str, ...] = ()
    terminal_state: str = "UNAVAILABLE"
    reference_id: str = "EXPLICIT_ABSENCE"
    evidence_id: str = "EXPLICIT_ABSENCE"
    contract_version: str = "1.4"
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        _typed_enum(self.evidence_state, ST12FEvidenceStateV1, "evidence_state")
        for name in (
            "evidence_ref",
            "lane",
            "dataset_grade_ref",
            "venue_semantic_binding_ref",
            "cross_venue_equivalence_ref",
            "policy_version",
            "causation_id",
            "correlation_id",
            "input_lock_id",
            "component_or_template_ref",
            "evidence_bundle_version",
            "terminal_state",
            "reference_id",
            "evidence_id",
            "contract_version",
        ):
            _canonical_text(getattr(self, name), name)
        _text_tuple(self.source_epoch_refs, "source_epoch_refs")
        if len(self.source_epoch_refs) != len(set(self.source_epoch_refs)):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "source_epoch_refs must contain unique identities",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1:
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "F evidence references require the shared no-effect custody type",
            )
        if self.contract_version != "1.4":
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "F evidence reference contract version differs",
            )
        observed = _utc_timestamp(self.observed_at, "observed_at")
        valid_until = _utc_timestamp(self.valid_until, "valid_until")
        if observed > valid_until:
            raise ContractValidationError(
                ReasonCode.POLICY_OR_SNAPSHOT_STALE,
                "evidence validity cannot precede its observation",
            )
        if self.evidence_state is ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE:
            if self.lane not in {"REPLAY", "PAPER", "REPLAY_PAPER"}:
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    "available F evidence must declare REPLAY, PAPER, or REPLAY_PAPER",
                )
            if any(
                getattr(self, name) == "EXPLICIT_ABSENCE"
                for name in (
                    "evidence_ref",
                    "dataset_grade_ref",
                    "venue_semantic_binding_ref",
                    "cross_venue_equivalence_ref",
                    "input_lock_id",
                    "component_or_template_ref",
                    "evidence_bundle_version",
                    "reference_id",
                    "evidence_id",
                )
            ):
                raise ContractValidationError(
                    ReasonCode.EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH,
                    "available evidence cannot carry an absent evidence pin",
                )
            if (
                not self.source_epoch_refs
                or self.terminal_state != "CLOSED_INDEPENDENTLY_VALIDATED"
            ):
                raise ContractValidationError(
                    ReasonCode.EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH,
                    "available evidence requires current source epochs and closed review",
                )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "ST12FEvidenceReferenceV1":
        if not isinstance(value, Mapping) or set(value) != {
            field.name for field in dataclass_fields(cls)
        }:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "F evidence-reference payload fields differ",
            )
        payload = dict(value)
        payload["evidence_state"] = ST12FEvidenceStateV1(payload["evidence_state"])
        payload["source_epoch_refs"] = tuple(payload["source_epoch_refs"])
        payload["observed_at"] = parse_utc(
            payload["observed_at"], field_name="observed_at"
        )
        payload["valid_until"] = parse_utc(
            payload["valid_until"], field_name="valid_until"
        )
        payload["no_effect_flags"] = NO_EFFECTS_V1
        return cls(**payload)

    def canonical_json(self) -> str:
        from .serialization import deterministic_json

        return deterministic_json(self)


@dataclass(frozen=True, slots=True)
class OwnerActionConfirmationReceiptV1:
    """Exact current-owner action receipt; it grants no activation authority."""

    receipt_ref: str
    owner_action_policy_ref: str
    state: OwnerActionConfirmationStateV1
    principal_id: str
    task_id: str
    capability_decision_ref: str
    context_ref: str
    observed_at: datetime
    valid_until: datetime
    causation_id: str
    correlation_id: str
    predecessor_transition_id_or_explicit_absence: str = "EXPLICIT_ABSENCE"
    predecessor_transition_receipt_ref_or_explicit_absence: str = (
        "EXPLICIT_ABSENCE"
    )
    predecessor_transition_receipt_proposal_or_explicit_absence: object | None = None
    runtime_effect_authorized: bool = False
    order_release_authorized: bool = False

    def __post_init__(self) -> None:
        for name in (
            "receipt_ref",
            "owner_action_policy_ref",
            "principal_id",
            "task_id",
            "capability_decision_ref",
            "context_ref",
            "causation_id",
            "correlation_id",
            "predecessor_transition_id_or_explicit_absence",
            "predecessor_transition_receipt_ref_or_explicit_absence",
        ):
            _canonical_text(getattr(self, name), name)
        _typed_enum(self.state, OwnerActionConfirmationStateV1, "state")
        observed = _utc_timestamp(self.observed_at, "observed_at")
        valid_until = _utc_timestamp(self.valid_until, "valid_until")
        if observed > valid_until:
            raise ContractValidationError(
                ReasonCode.POLICY_OR_SNAPSHOT_STALE,
                "owner-action receipt validity cannot precede observation",
            )
        if self.causation_id == self.correlation_id:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "owner-action causation and correlation identities must differ",
            )
        predecessor = (
            self.predecessor_transition_id_or_explicit_absence,
            self.predecessor_transition_receipt_ref_or_explicit_absence,
        )
        predecessor_proposal = (
            self.predecessor_transition_receipt_proposal_or_explicit_absence
        )
        if self.state is OwnerActionConfirmationStateV1.CONFIRMED_CURRENT:
            from .receipts import (
                EconomicReceiptEventSpineV1,
                EconomicRecordTypeV1,
                ModeSnapshotControlReceiptRecordV1,
            )

            if (
                predecessor[0] != "T06"
                or predecessor[1] == "EXPLICIT_ABSENCE"
                or type(predecessor_proposal) is not EconomicReceiptEventSpineV1
                or predecessor_proposal.record_type
                is not EconomicRecordTypeV1.MODE_SNAPSHOT_CONTROL
                or predecessor_proposal.record_id != predecessor[1]
                or type(predecessor_proposal.typed_payload)
                is not ModeSnapshotControlReceiptRecordV1
                or predecessor_proposal.typed_payload.transition_id != "T06"
                or predecessor_proposal.typed_payload.principal_id
                != self.principal_id
                or predecessor_proposal.typed_payload.task_id != self.task_id
                or predecessor_proposal.typed_payload.capability_decision_ref
                != self.capability_decision_ref
                or predecessor_proposal.typed_payload.context_ref != self.context_ref
                or predecessor_proposal.typed_payload.source_state != "NOT_EVALUATED"
                or predecessor_proposal.typed_payload.destination_state
                != "OWNER_CONFIRMATION_REQUIRED"
                or predecessor_proposal.typed_payload.typed_reason_codes[0]
                is not ReasonCode.OWNER_CONFIRMATION_REQUIRED
            ):
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    "confirmed owner action requires the exact typed prior T06 hold receipt",
                )
        elif (
            predecessor != ("EXPLICIT_ABSENCE", "EXPLICIT_ABSENCE")
            or predecessor_proposal is not None
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "unconfirmed owner action cannot claim a predecessor transition receipt",
            )
        _must_be_false(self.runtime_effect_authorized, "runtime_effect_authorized")
        _must_be_false(self.order_release_authorized, "order_release_authorized")

    def is_current_for(
        self,
        *,
        evaluated_at: datetime,
        principal_id: str,
        task_id: str,
        capability_decision_ref: str,
        context_ref: str,
        request_id: str,
        snapshot_candidate_ref: str,
        candidate_version: str,
    ) -> bool:
        """Return a derived fact only when the exact receipt identity is current."""

        evaluated = _utc_timestamp(evaluated_at, "evaluated_at")
        predecessor = self.predecessor_transition_receipt_proposal_or_explicit_absence
        payload = (
            predecessor.typed_payload
            if predecessor is not None
            else None
        )
        return (
            self.state is OwnerActionConfirmationStateV1.CONFIRMED_CURRENT
            and self.observed_at <= evaluated <= self.valid_until
            and self.principal_id == principal_id
            and self.task_id == task_id
            and self.capability_decision_ref == capability_decision_ref
            and self.context_ref == context_ref
            and getattr(payload, "request_id", None) == request_id
            and getattr(payload, "snapshot_candidate_ref_or_explicit_absence", None)
            == snapshot_candidate_ref
            and getattr(payload, "target_candidate_version", None)
            == candidate_version
        )


@dataclass(frozen=True, slots=True)
class ResolvedSnapshotParameterValueV1:
    """One exact snapshot-bound value pin under the existing parameter owner."""

    parameter_id: str
    parameter_symbol: str
    resolved_value_ref: str
    canonical_typed_value_or_explicit_unavailable: str | int | bool | Decimal
    value_kind: str
    unit_or_basis: str
    resolution_state: SnapshotParameterResolutionStateV1
    policy_ref: str
    parameter_policy_set_version: str
    producer_receipt_refs: tuple[str, ...]
    point_in_time_receipt_refs: tuple[str, ...]
    freshness_receipt_refs: tuple[str, ...]
    source_epoch_refs: tuple[str, ...]
    observed_at_or_explicit_absence: datetime | str
    valid_until_or_explicit_absence: datetime | str
    diagnostic_reason_codes: tuple[ReasonCode, ...] = ()
    no_mutation_flag: bool = True

    def __post_init__(self) -> None:
        for name in (
            "parameter_id",
            "parameter_symbol",
            "resolved_value_ref",
            "value_kind",
            "unit_or_basis",
            "policy_ref",
            "parameter_policy_set_version",
        ):
            _canonical_text(getattr(self, name), name)
        if self.resolved_value_ref == self.policy_ref:
            raise ContractValidationError(
                ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                "a parameter policy identity cannot occupy a resolved-value slot",
            )
        value = self.canonical_typed_value_or_explicit_unavailable
        if type(value) not in {str, int, bool, Decimal} or (
            isinstance(value, str) and not value
        ):
            raise ContractValidationError(
                ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                "resolved snapshot parameter values require one canonical typed value",
            )
        _typed_enum(
            self.resolution_state,
            SnapshotParameterResolutionStateV1,
            "resolution_state",
        )
        for name in (
            "producer_receipt_refs",
            "point_in_time_receipt_refs",
            "freshness_receipt_refs",
            "source_epoch_refs",
        ):
            _validate_unique_text(getattr(self, name), name)
        unavailable = (
            self.resolution_state
            is SnapshotParameterResolutionStateV1.REQUIRED_OWNER_VALUE_UNAVAILABLE
        )
        deterministic = (
            self.resolution_state
            is SnapshotParameterResolutionStateV1.DETERMINISTIC_POLICY_VALUE_MATERIALIZED
        )
        owner_resolved = (
            self.resolution_state
            is SnapshotParameterResolutionStateV1.OWNER_VALUE_RESOLVED
        )
        validate_reference_identity_classes(
            policy_refs=(self.policy_ref,),
            semantic_policy_set_versions=(self.parameter_policy_set_version,),
            source_epoch_refs=self.source_epoch_refs,
            receipt_refs=(
                *self.producer_receipt_refs,
                *self.point_in_time_receipt_refs,
                *self.freshness_receipt_refs,
            ),
        )
        if unavailable:
            if (
                not isinstance(value, str)
                or not value.startswith("EXPLICIT_UNAVAILABLE::")
                or not self.diagnostic_reason_codes
                or self.producer_receipt_refs
                or self.point_in_time_receipt_refs
                or self.freshness_receipt_refs
                or self.source_epoch_refs
            ):
                raise ContractValidationError(
                    ReasonCode.PARAMETER_OWNER_MISSING,
                    "unavailable owner values require an exact typed blocker",
                )
        elif deterministic and (
            self.producer_receipt_refs
            or self.point_in_time_receipt_refs
            or self.freshness_receipt_refs
            or self.source_epoch_refs
        ):
            raise ContractValidationError(
                ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                "deterministic policy values cannot synthesize receipt or epoch lineage",
            )
        elif owner_resolved and (
            not self.producer_receipt_refs
            or not self.point_in_time_receipt_refs
            or not self.freshness_receipt_refs
            or not self.source_epoch_refs
        ):
            raise ContractValidationError(
                ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                "owner-resolved values require producer, PIT, freshness, and source-epoch proof",
            )
        for name in (
            "observed_at_or_explicit_absence",
            "valid_until_or_explicit_absence",
        ):
            timestamp = getattr(self, name)
            if timestamp != "EXPLICIT_ABSENCE":
                _utc_timestamp(timestamp, name)
        if (
            self.observed_at_or_explicit_absence == "EXPLICIT_ABSENCE"
        ) != (
            self.valid_until_or_explicit_absence == "EXPLICIT_ABSENCE"
        ):
            raise ContractValidationError(
                ReasonCode.CLOCK_DOMAIN_MISMATCH,
                "resolved parameter validity must be exact timestamps or exact absence",
            )
        if (
            self.observed_at_or_explicit_absence != "EXPLICIT_ABSENCE"
            and self.observed_at_or_explicit_absence
            > self.valid_until_or_explicit_absence
        ):
            raise ContractValidationError(
                ReasonCode.POLICY_OR_SNAPSHOT_STALE,
                "resolved parameter validity cannot precede observation",
            )
        if (
            not isinstance(self.diagnostic_reason_codes, tuple)
            or any(type(reason) is not ReasonCode for reason in self.diagnostic_reason_codes)
            or len(self.diagnostic_reason_codes) != len(set(self.diagnostic_reason_codes))
            or self.no_mutation_flag is not True
        ):
            raise ContractValidationError(
                ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                "resolved parameter diagnostics and no-mutation custody are invalid",
            )


@dataclass(frozen=True, slots=True)
class FormulaRuntimeSnapshotCandidateV1:
    """Deeply immutable, version-pinned ST12-D candidate; never active state."""

    snapshot_candidate_id: str
    request_id: str
    principal_id: str
    task_id: str
    capability_decision_ref: str
    computation_bundle_ref: str
    context_ref: str
    formula_spec_refs: tuple[str, ...]
    implementation_version_pins: tuple[ImplementationVersionPinV1, ...]
    binding_profile_ref: str
    parameter_policy_snapshot_ref: str
    parameter_value_refs: tuple[str, ...]
    source_epoch_refs: tuple[str, ...]
    receipt_lineage_refs: tuple[str, ...]
    readiness_state_ref: str
    pretrade_state_ref: str
    evidence_state_ref: str
    kill_state_ref: str
    submit_disabled_state_ref: str
    created_at: datetime
    evaluated_at: datetime
    expires_at: datetime
    stale_at: datetime | None
    candidate_state: SnapshotCandidateStateV1
    reason_codes: tuple[ReasonCode, ...]
    fallback_route: str
    owner_review_route: str
    runtime_effect_authorized: bool = False
    order_release_authorized: bool = False
    activated: bool = False

    def __post_init__(self) -> None:
        for name in (
            "snapshot_candidate_id",
            "request_id",
            "principal_id",
            "task_id",
            "capability_decision_ref",
            "computation_bundle_ref",
            "context_ref",
            "binding_profile_ref",
            "parameter_policy_snapshot_ref",
            "readiness_state_ref",
            "pretrade_state_ref",
            "evidence_state_ref",
            "kill_state_ref",
            "submit_disabled_state_ref",
            "fallback_route",
            "owner_review_route",
        ):
            _canonical_text(getattr(self, name), name)
        for name in (
            "formula_spec_refs",
            "parameter_value_refs",
            "source_epoch_refs",
            "receipt_lineage_refs",
        ):
            _validate_unique_text(getattr(self, name), name, nonempty=True)
        if (
            not isinstance(self.implementation_version_pins, tuple)
            or not self.implementation_version_pins
            or any(
                type(pin) is not ImplementationVersionPinV1
                for pin in self.implementation_version_pins
            )
            or len(
                {pin.math_spec_id for pin in self.implementation_version_pins}
            )
            != len(self.implementation_version_pins)
        ):
            raise ContractValidationError(
                ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                "implementation_version_pins must be exact, ordered, and unique",
            )
        created = _utc_timestamp(self.created_at, "created_at")
        evaluated = _utc_timestamp(self.evaluated_at, "evaluated_at")
        expires = _utc_timestamp(self.expires_at, "expires_at")
        if not created <= evaluated <= expires:
            raise ContractValidationError(
                ReasonCode.POLICY_OR_SNAPSHOT_STALE,
                "candidate times must satisfy created <= evaluated <= expires",
            )
        if self.stale_at is not None:
            stale = _utc_timestamp(self.stale_at, "stale_at")
            if stale < created:
                raise ContractValidationError(
                    ReasonCode.POLICY_OR_SNAPSHOT_STALE,
                    "stale_at cannot precede candidate creation",
                )
        _typed_enum(self.candidate_state, SnapshotCandidateStateV1, "candidate_state")
        _reason_tuple(self.reason_codes, "reason_codes", require_nonempty=True)
        for name in (
            "runtime_effect_authorized",
            "order_release_authorized",
            "activated",
        ):
            _must_be_false(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class ModeSnapshotDecisionV1:
    decision_id: str
    request_id: str
    task_id: str
    principal_id: str
    current_agent_id: str
    capability_decision_ref: str
    computation_bundle_ref: str
    context_ref: str
    parameter_policy_snapshot_ref: str
    receipt_lineage_refs: tuple[str, ...]
    readiness_state_ref: str
    pretrade_state_ref: str
    evidence_state_ref: str
    kill_state_ref: str
    submit_disabled_state_ref: str
    owner_action_policy_ref: str
    current_mode: str
    requested_mode: str
    mode_eligibility_state: ModeEligibilityState
    allow_candidate_state: AllowCandidateStateV1
    snapshot_candidate_state: SnapshotCandidateStateV1
    activation_precondition_state: ActivationPreconditionStateV1
    rollback_state: SnapshotRollbackStateV1
    rollback_target_ref_or_explicit_absence: str
    pin_policy_ref: str
    stale_state: str
    expires_at: datetime
    retirement_state: SnapshotRetirementStateV1
    implementation_pins: tuple[ImplementationVersionPinV1, ...]
    source_epoch_refs: tuple[str, ...]
    reason_codes: tuple[ReasonCode, ...]
    fallback_route: str
    owner_review_route: str
    no_trade_route: str
    latency_measurement_ref_or_explicit_absence: str
    runtime_effect_authorized: bool = False
    active_pointer_commit_allowed: bool = False
    order_release_authorized: bool = False

    def __post_init__(self) -> None:
        for name in (
            "decision_id",
            "request_id",
            "task_id",
            "principal_id",
            "current_agent_id",
            "capability_decision_ref",
            "computation_bundle_ref",
            "context_ref",
            "parameter_policy_snapshot_ref",
            "readiness_state_ref",
            "pretrade_state_ref",
            "evidence_state_ref",
            "kill_state_ref",
            "submit_disabled_state_ref",
            "owner_action_policy_ref",
            "current_mode",
            "requested_mode",
            "rollback_target_ref_or_explicit_absence",
            "pin_policy_ref",
            "stale_state",
            "fallback_route",
            "owner_review_route",
            "no_trade_route",
            "latency_measurement_ref_or_explicit_absence",
        ):
            _canonical_text(getattr(self, name), name)
        _validate_unique_text(self.receipt_lineage_refs, "receipt_lineage_refs", nonempty=True)
        if not isinstance(self.implementation_pins, tuple) or any(
            type(pin) is not ImplementationVersionPinV1
            for pin in self.implementation_pins
        ):
            raise ContractValidationError(
                ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                "implementation_pins require exact typed pins",
            )
        early_terminal = (
            self.computation_bundle_ref == "EXPLICIT_ABSENCE"
            and self.snapshot_candidate_state is SnapshotCandidateStateV1.ABSENT
            and self.allow_candidate_state
            in {AllowCandidateStateV1.BLOCKED, AllowCandidateStateV1.EVIDENCE_UNAVAILABLE}
        )
        if not early_terminal and not self.implementation_pins:
            raise ContractValidationError(
                ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                "candidate-body decisions require exact implementation pins",
            )
        _validate_unique_text(
            self.source_epoch_refs,
            "source_epoch_refs",
            nonempty=not early_terminal,
        )
        for value, enum_type, name in (
            (self.mode_eligibility_state, ModeEligibilityState, "mode_eligibility_state"),
            (self.allow_candidate_state, AllowCandidateStateV1, "allow_candidate_state"),
            (self.snapshot_candidate_state, SnapshotCandidateStateV1, "snapshot_candidate_state"),
            (self.activation_precondition_state, ActivationPreconditionStateV1, "activation_precondition_state"),
            (self.rollback_state, SnapshotRollbackStateV1, "rollback_state"),
            (self.retirement_state, SnapshotRetirementStateV1, "retirement_state"),
        ):
            _typed_enum(value, enum_type, name)
        _utc_timestamp(self.expires_at, "expires_at")
        _reason_tuple(self.reason_codes, "reason_codes", require_nonempty=True)
        for name in (
            "runtime_effect_authorized",
            "active_pointer_commit_allowed",
            "order_release_authorized",
        ):
            _must_be_false(getattr(self, name), name)


_D_TRANSITION_STATE_TYPES = (
    ModeEligibilityState,
    AllowCandidateStateV1,
    SnapshotCandidateStateV1,
    SnapshotRollbackStateV1,
    SnapshotRetirementStateV1,
)


@dataclass(frozen=True, slots=True)
class SnapshotTransitionProposalV1:
    proposal_id: str
    request_id: str
    principal_id: str
    task_id: str
    capability_decision_ref: str
    context_ref: str
    source_candidate_ref_or_explicit_absence: str
    target_candidate_ref: str
    source_candidate_version_or_explicit_absence: str
    target_candidate_version: str
    transition_id: str
    source_state: str
    destination_state: str
    expected_owner_state_ref: str
    precondition_receipt_refs: tuple[str, ...]
    predecessor_transition_receipt_refs: tuple[str, ...]
    predecessor_transition_receipt_proposals: tuple[object, ...]
    proposed_state: ModeEligibilityState | AllowCandidateStateV1 | SnapshotCandidateStateV1 | SnapshotRollbackStateV1 | SnapshotRetirementStateV1
    primary_reason_code: ReasonCode
    diagnostic_reason_codes: tuple[ReasonCode, ...]
    typed_reason_codes: tuple[ReasonCode, ...]
    owner_confirmation_required: bool
    causation_id: str
    correlation_id: str
    no_mutation_flag: bool = True
    no_activation_flag: bool = True
    no_order_release_flag: bool = True
    active_pointer_commit_allowed: bool = False
    mutation_allowed: bool = False
    runtime_effect_authorized: bool = False
    order_release_authorized: bool = False

    def __post_init__(self) -> None:
        for name in (
            "proposal_id",
            "request_id",
            "principal_id",
            "task_id",
            "capability_decision_ref",
            "context_ref",
            "source_candidate_ref_or_explicit_absence",
            "target_candidate_ref",
            "source_candidate_version_or_explicit_absence",
            "target_candidate_version",
            "transition_id",
            "source_state",
            "destination_state",
            "expected_owner_state_ref",
            "causation_id",
            "correlation_id",
        ):
            _canonical_text(getattr(self, name), name)
        _validate_unique_text(
            self.precondition_receipt_refs,
            "precondition_receipt_refs",
            nonempty=True,
        )
        _validate_unique_text(
            self.predecessor_transition_receipt_refs,
            "predecessor_transition_receipt_refs",
        )
        from .receipts import (
            EconomicReceiptEventSpineV1,
            EconomicRecordTypeV1,
            ModeSnapshotControlReceiptRecordV1,
        )

        if (
            not isinstance(self.predecessor_transition_receipt_proposals, tuple)
            or any(
                type(row) is not EconomicReceiptEventSpineV1
                or row.record_type is not EconomicRecordTypeV1.MODE_SNAPSHOT_CONTROL
                or type(row.typed_payload) is not ModeSnapshotControlReceiptRecordV1
                for row in self.predecessor_transition_receipt_proposals
            )
            or tuple(
                row.record_id
                for row in self.predecessor_transition_receipt_proposals
            )
            != self.predecessor_transition_receipt_refs
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "predecessor transition refs require exact typed receipt-spine proposals",
            )
        if type(self.proposed_state) not in _D_TRANSITION_STATE_TYPES:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "proposed_state must be an exact frozen D transition state",
            )
        _typed_enum(self.primary_reason_code, ReasonCode, "primary_reason_code")
        _reason_tuple(self.diagnostic_reason_codes, "diagnostic_reason_codes")
        _reason_tuple(self.typed_reason_codes, "typed_reason_codes", require_nonempty=True)
        if self.typed_reason_codes != (
            self.primary_reason_code,
            *self.diagnostic_reason_codes,
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "transition reasons must be canonical primary reason then ordered diagnostics",
            )
        if type(self.owner_confirmation_required) is not bool:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "owner-confirmation requirement must be an exact boolean",
            )
        from .mode_snapshot_policy import TRANSITION_BY_ID

        try:
            rule = TRANSITION_BY_ID[self.transition_id]
        except KeyError as exc:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "transition proposal references an unknown frozen transition",
            ) from exc
        if (
            self.source_state != rule.source_state
            or self.destination_state != rule.destination_state
            or self.primary_reason_code is not rule.reason_code
            or self.owner_confirmation_required is not rule.owner_confirmation_required
            or self.proposed_state.value != rule.destination_state
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "transition proposal does not join the frozen transition registry exactly",
            )
        required_predecessor = (
            "T06"
            if self.transition_id == "T07"
            else "T12"
            if self.transition_id in {"T13", "T14"}
            else None
        )
        if required_predecessor is not None:
            predecessor_rule = TRANSITION_BY_ID[required_predecessor]
            if len(self.predecessor_transition_receipt_proposals) != 1:
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    "transition proposal lacks its required predecessor receipt proof",
                )
            predecessor_proposal = self.predecessor_transition_receipt_proposals[0]
            predecessor_payload = predecessor_proposal.typed_payload
            expected_candidate_ref = (
                self.target_candidate_ref
                if self.transition_id == "T07"
                else self.source_candidate_ref_or_explicit_absence
            )
            expected_candidate_version = (
                self.target_candidate_version
                if self.transition_id == "T07"
                else self.source_candidate_version_or_explicit_absence
            )
            if (
                predecessor_payload.transition_id != required_predecessor
                or predecessor_payload.request_id != self.request_id
                or predecessor_payload.principal_id != self.principal_id
                or predecessor_payload.task_id != self.task_id
                or predecessor_payload.capability_decision_ref
                != self.capability_decision_ref
                or predecessor_payload.context_ref != self.context_ref
                or predecessor_payload.source_state != predecessor_rule.source_state
                or predecessor_payload.destination_state
                != predecessor_rule.destination_state
                or predecessor_payload.destination_state != rule.source_state
                or predecessor_payload.typed_reason_codes[0]
                is not predecessor_rule.reason_code
                or predecessor_payload.snapshot_candidate_ref_or_explicit_absence
                != expected_candidate_ref
                or predecessor_payload.target_candidate_version
                != expected_candidate_version
                or self.expected_owner_state_ref
                not in predecessor_payload.state_before_refs
                or predecessor_payload.no_mutation_flag is not True
                or predecessor_payload.no_activation_flag is not True
                or predecessor_payload.no_order_authority_flag is not True
            ):
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    "predecessor receipt does not prove the exact transition and candidate scope",
                )
        if required_predecessor is None and (
            self.predecessor_transition_receipt_refs
            or self.predecessor_transition_receipt_proposals
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "transition proposal claims an inapplicable predecessor receipt",
            )
        if self.causation_id == self.correlation_id:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "causation and correlation identities must remain distinct",
            )
        for name in (
            "no_mutation_flag",
            "no_activation_flag",
            "no_order_release_flag",
        ):
            if getattr(self, name) is not True:
                raise ContractValidationError(
                    ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                    f"{name} must remain exact true",
                )
        for name in (
            "active_pointer_commit_allowed",
            "mutation_allowed",
            "runtime_effect_authorized",
            "order_release_authorized",
        ):
            _must_be_false(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class ExecutedModeSnapshotTransitionTraceV1:
    """One ordered, immutable account of the D transitions actually executed."""

    proposals: tuple[SnapshotTransitionProposalV1, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.proposals, tuple)
            or not self.proposals
            or any(type(row) is not SnapshotTransitionProposalV1 for row in self.proposals)
            or len({row.proposal_id for row in self.proposals}) != len(self.proposals)
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "executed transition trace requires unique exact proposal rows",
            )
        first = self.proposals[0]
        identity_fields = (
            "request_id",
            "principal_id",
            "task_id",
            "capability_decision_ref",
            "context_ref",
            "target_candidate_version",
            "causation_id",
            "correlation_id",
        )
        if any(
            getattr(row, name) != getattr(first, name)
            for row in self.proposals[1:]
            for name in identity_fields
        ):
            raise ContractValidationError(
                ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,
                "executed transition rows do not share one admitted request identity",
            )
        transition_ids = tuple(row.transition_id for row in self.proposals)
        allowed_shapes = {
            ("T03",),
            ("T04",),
            ("T05",),
            ("T08",),
            ("T08", "T09", "T06"),
            ("T08", "T09", "T07"),
            ("T08", "T10"),
            ("T08", "T09", "T04"),
        }
        if transition_ids not in allowed_shapes:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                f"executed transition trace has a noncanonical D shape: {transition_ids!r}",
            )
        if transition_ids[0] == "T08":
            candidate_ref = first.target_candidate_ref
            if (
                candidate_ref == "EXPLICIT_ABSENCE"
                or any(row.target_candidate_ref != candidate_ref for row in self.proposals)
                or any(
                    row.source_candidate_ref_or_explicit_absence != candidate_ref
                    for row in self.proposals[1:]
                )
            ):
                raise ContractValidationError(
                    ReasonCode.SNAPSHOT_PIN_CONFLICT,
                    "candidate-stage transition rows do not preserve one candidate identity",
                )

    @property
    def final_proposal(self) -> SnapshotTransitionProposalV1:
        return self.proposals[-1]


_MODE_SNAPSHOT_TERMINAL_OUTCOME_MATRIX_V1: Mapping[
    tuple[str, ...],
    tuple[bool, AllowCandidateStateV1, SnapshotCandidateStateV1],
] = MappingProxyType(
    {
        ("T03",): (
            False,
            AllowCandidateStateV1.EVIDENCE_UNAVAILABLE,
            SnapshotCandidateStateV1.ABSENT,
        ),
        ("T04",): (
            False,
            AllowCandidateStateV1.BLOCKED,
            SnapshotCandidateStateV1.ABSENT,
        ),
        ("T05",): (
            False,
            AllowCandidateStateV1.BLOCKED,
            SnapshotCandidateStateV1.ABSENT,
        ),
        ("T08", "T09", "T06"): (
            True,
            AllowCandidateStateV1.OWNER_CONFIRMATION_REQUIRED,
            SnapshotCandidateStateV1.VALIDATED_NO_EFFECT,
        ),
        ("T08", "T09", "T07"): (
            True,
            AllowCandidateStateV1.ELIGIBLE_NOT_ACTIVATED,
            SnapshotCandidateStateV1.VALIDATED_NO_EFFECT,
        ),
        ("T08", "T10"): (
            False,
            AllowCandidateStateV1.BLOCKED,
            SnapshotCandidateStateV1.REJECTED,
        ),
        ("T08", "T09", "T04"): (
            True,
            AllowCandidateStateV1.BLOCKED,
            SnapshotCandidateStateV1.VALIDATED_NO_EFFECT,
        ),
    }
)


def _validate_mode_snapshot_terminal_outcome_consistency(
    *,
    candidate: FormulaRuntimeSnapshotCandidateV1 | None,
    decision: ModeSnapshotDecisionV1,
    trace: ExecutedModeSnapshotTransitionTraceV1,
    final_proposal: SnapshotTransitionProposalV1,
) -> None:
    """Fail closed unless all returned terminal D surfaces describe one outcome."""

    transition_ids = tuple(row.transition_id for row in trace.proposals)
    try:
        (
            candidate_required,
            expected_allow_state,
            expected_snapshot_state,
        ) = _MODE_SNAPSHOT_TERMINAL_OUTCOME_MATRIX_V1[transition_ids]
    except KeyError as exc:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"terminal mode-snapshot result has no registered outcome: {transition_ids!r}",
        ) from exc

    if candidate_required != (candidate is not None):
        raise ContractValidationError(
            ReasonCode.SNAPSHOT_CANDIDATE_INVALID,
            "terminal trace and returned candidate presence do not match",
        )
    if (
        decision.allow_candidate_state is not expected_allow_state
        or decision.snapshot_candidate_state is not expected_snapshot_state
        or final_proposal.transition_id != transition_ids[-1]
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "terminal trace and decision states do not match the registered outcome",
        )

    trace_identity_fields = (
        "request_id",
        "principal_id",
        "task_id",
        "capability_decision_ref",
        "context_ref",
    )
    if any(
        getattr(proposal, field_name) != getattr(decision, field_name)
        for proposal in trace.proposals
        for field_name in trace_identity_fields
    ):
        raise ContractValidationError(
            ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,
            "decision and executed trace do not share one admitted identity",
        )
    if any(
        proposal.precondition_receipt_refs != decision.receipt_lineage_refs
        for proposal in trace.proposals
    ):
        raise ContractValidationError(
            ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,
            "executed trace preconditions differ from decision receipt lineage",
        )

    from .mode_snapshot_policy import TRANSITION_BY_ID

    terminal_rule = TRANSITION_BY_ID[final_proposal.transition_id]
    expected_proposed_state = (
        decision.snapshot_candidate_state
        if final_proposal.transition_id == "T10"
        else decision.allow_candidate_state
    )
    if (
        final_proposal.primary_reason_code is not decision.reason_codes[0]
        or final_proposal.diagnostic_reason_codes != decision.reason_codes[1:]
        or final_proposal.typed_reason_codes != decision.reason_codes
        or final_proposal.proposed_state is not expected_proposed_state
        or terminal_rule.terminal_route != decision.fallback_route
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "final proposal reason, state, or registered terminal route differs from the decision",
        )

    early_absence_shapes = {("T03",), ("T04",), ("T05",)}
    if transition_ids in early_absence_shapes and any(
        proposal.source_candidate_ref_or_explicit_absence != "EXPLICIT_ABSENCE"
        or proposal.target_candidate_ref != "EXPLICIT_ABSENCE"
        or proposal.source_candidate_version_or_explicit_absence
        != "EXPLICIT_ABSENCE"
        for proposal in trace.proposals
    ):
        raise ContractValidationError(
            ReasonCode.SNAPSHOT_PIN_CONFLICT,
            "candidate-absence terminal trace contains a candidate identity or source version",
        )

    if transition_ids == ("T08", "T10"):
        build_proposal, rejected_proposal = trace.proposals
        rejected_candidate_ref = build_proposal.target_candidate_ref
        if (
            build_proposal.source_candidate_ref_or_explicit_absence
            != "EXPLICIT_ABSENCE"
            or build_proposal.source_candidate_version_or_explicit_absence
            != "EXPLICIT_ABSENCE"
            or rejected_candidate_ref == "EXPLICIT_ABSENCE"
            or rejected_proposal.source_candidate_ref_or_explicit_absence
            != rejected_candidate_ref
            or rejected_proposal.target_candidate_ref != rejected_candidate_ref
            or rejected_proposal.source_candidate_version_or_explicit_absence
            != build_proposal.target_candidate_version
        ):
            raise ContractValidationError(
                ReasonCode.SNAPSHOT_PIN_CONFLICT,
                "rejected candidate trace does not preserve its build identity and version",
            )

    if candidate is None:
        return

    candidate_decision_fields = (
        ("request_id", "request_id"),
        ("principal_id", "principal_id"),
        ("task_id", "task_id"),
        ("capability_decision_ref", "capability_decision_ref"),
        ("computation_bundle_ref", "computation_bundle_ref"),
        ("context_ref", "context_ref"),
        ("implementation_version_pins", "implementation_pins"),
        ("parameter_policy_snapshot_ref", "parameter_policy_snapshot_ref"),
        ("source_epoch_refs", "source_epoch_refs"),
        ("receipt_lineage_refs", "receipt_lineage_refs"),
        ("readiness_state_ref", "readiness_state_ref"),
        ("pretrade_state_ref", "pretrade_state_ref"),
        ("evidence_state_ref", "evidence_state_ref"),
        ("kill_state_ref", "kill_state_ref"),
        ("submit_disabled_state_ref", "submit_disabled_state_ref"),
        ("expires_at", "expires_at"),
    )
    if any(
        getattr(candidate, candidate_field) != getattr(decision, decision_field)
        for candidate_field, decision_field in candidate_decision_fields
    ):
        raise ContractValidationError(
            ReasonCode.SNAPSHOT_PIN_CONFLICT,
            "validated candidate and decision identity or pins differ",
        )
    if (
        candidate.candidate_state is not SnapshotCandidateStateV1.VALIDATED_NO_EFFECT
        or candidate.runtime_effect_authorized is not False
        or candidate.order_release_authorized is not False
        or candidate.activated is not False
    ):
        raise ContractValidationError(
            ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
            "returned candidate must be validated and retain exact no-effect custody",
        )

    build_proposal, validated_proposal, terminal_proposal = trace.proposals
    candidate_ref = candidate.snapshot_candidate_id
    candidate_version = build_proposal.target_candidate_version
    if (
        build_proposal.source_candidate_ref_or_explicit_absence
        != "EXPLICIT_ABSENCE"
        or build_proposal.source_candidate_version_or_explicit_absence
        != "EXPLICIT_ABSENCE"
        or build_proposal.target_candidate_ref != candidate_ref
        or validated_proposal.source_candidate_ref_or_explicit_absence
        != candidate_ref
        or validated_proposal.target_candidate_ref != candidate_ref
        or validated_proposal.source_candidate_version_or_explicit_absence
        != candidate_version
        or terminal_proposal.source_candidate_ref_or_explicit_absence
        != candidate_ref
        or terminal_proposal.target_candidate_ref != candidate_ref
        or terminal_proposal.source_candidate_version_or_explicit_absence
        != candidate_version
    ):
        raise ContractValidationError(
            ReasonCode.SNAPSHOT_PIN_CONFLICT,
            "validated candidate and executed trace identity or version differ",
        )


@dataclass(frozen=True, slots=True)
class ModeSnapshotCandidateProposalResultV1:
    snapshot_candidate_or_explicit_absence: FormulaRuntimeSnapshotCandidateV1 | None
    mode_snapshot_decision: ModeSnapshotDecisionV1
    snapshot_transition_proposal: SnapshotTransitionProposalV1
    executed_transition_trace: ExecutedModeSnapshotTransitionTraceV1
    control_receipt_refs: tuple[str, ...]
    owner_projection_or_explicit_absence: ModeSnapshotOwnerProjectionV1 | None = None
    latency_measurement_or_explicit_absence: LatencyMeasurementV1 | None = None
    control_receipt_proposals: tuple[object, ...] = ()
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        if self.snapshot_candidate_or_explicit_absence is not None and type(
            self.snapshot_candidate_or_explicit_absence
        ) is not FormulaRuntimeSnapshotCandidateV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "snapshot candidate must be exact typed candidate or explicit None",
            )
        if (
            type(self.mode_snapshot_decision) is not ModeSnapshotDecisionV1
            or type(self.snapshot_transition_proposal) is not SnapshotTransitionProposalV1
            or type(self.executed_transition_trace)
            is not ExecutedModeSnapshotTransitionTraceV1
            or self.snapshot_transition_proposal
            is not self.executed_transition_trace.final_proposal
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "mode snapshot result requires one exact trace and its final proposal",
            )
        _validate_mode_snapshot_terminal_outcome_consistency(
            candidate=self.snapshot_candidate_or_explicit_absence,
            decision=self.mode_snapshot_decision,
            trace=self.executed_transition_trace,
            final_proposal=self.snapshot_transition_proposal,
        )
        _validate_unique_text(self.control_receipt_refs, "control_receipt_refs")
        if (
            self.owner_projection_or_explicit_absence is not None
            and type(self.owner_projection_or_explicit_absence)
            is not ModeSnapshotOwnerProjectionV1
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "owner projection must be the exact final projection or explicit None",
            )
        if self.owner_projection_or_explicit_absence is not None:
            projection = self.owner_projection_or_explicit_absence
            decision = self.mode_snapshot_decision
            if (
                projection.decision_id != decision.decision_id
                or projection.mode_eligibility_state
                is not decision.mode_eligibility_state
                or projection.allow_candidate_state is not decision.allow_candidate_state
                or projection.snapshot_candidate_state
                is not decision.snapshot_candidate_state
                or projection.reason_codes != decision.reason_codes
                or projection.fallback_route != decision.fallback_route
                or projection.owner_review_route != decision.owner_review_route
            ):
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    "returned owner projection must describe the final decision exactly",
                )
        if self.latency_measurement_or_explicit_absence is not None:
            if type(self.latency_measurement_or_explicit_absence) is not LatencyMeasurementV1:
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    "returned latency measurement must use the exact typed contract",
                )
            if (
                self.mode_snapshot_decision.latency_measurement_ref_or_explicit_absence
                != self.latency_measurement_or_explicit_absence.measurement_ref
            ):
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    "returned latency measurement identity differs from the decision pin",
                )
        if not isinstance(self.control_receipt_proposals, tuple):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "control receipt proposals must be an immutable tuple",
            )
        if self.control_receipt_proposals:
            from .receipts import (
                EconomicReceiptEventSpineV1,
                ModeSnapshotControlClassV1,
            )

            if (
                any(
                    type(row) is not EconomicReceiptEventSpineV1
                    for row in self.control_receipt_proposals
                )
                or tuple(row.record_id for row in self.control_receipt_proposals)
                != self.control_receipt_refs
            ):
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    "control receipt refs must resolve to the exact returned typed proposals",
                )
            proposal_by_class = {
                ModeSnapshotControlClassV1.MODE_SNAPSHOT_EVALUATION: (
                    self.executed_transition_trace.final_proposal
                ),
                ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_BUILD: next(
                    (
                        row
                        for row in self.executed_transition_trace.proposals
                        if row.transition_id == "T08"
                    ),
                    None,
                ),
                ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_VALIDATION: next(
                    (
                        row
                        for row in self.executed_transition_trace.proposals
                        if row.transition_id in {"T09", "T10"}
                    ),
                    None,
                ),
            }
            expected_classes = (
                ModeSnapshotControlClassV1.MODE_SNAPSHOT_EVALUATION,
                *(
                    (ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_BUILD,)
                    if proposal_by_class[
                        ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_BUILD
                    ]
                    is not None
                    else ()
                ),
                *(
                    (ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_VALIDATION,)
                    if proposal_by_class[
                        ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_VALIDATION
                    ]
                    is not None
                    else ()
                ),
            )
            if any(
                (mapped := proposal_by_class.get(row.typed_payload.control_class)) is None
                or (
                    row.typed_payload.transition_proposal_ref,
                    row.typed_payload.transition_id,
                    row.typed_payload.source_state,
                    row.typed_payload.destination_state,
                    row.typed_payload.target_candidate_version,
                    row.typed_payload.state_before_refs,
                    row.typed_payload.state_after_refs,
                    row.typed_payload.typed_reason_codes,
                    row.typed_payload.predecessor_transition_receipt_refs,
                    row.causation_id,
                    row.correlation_id,
                )
                != (
                    mapped.proposal_id,
                    mapped.transition_id,
                    mapped.source_state,
                    mapped.destination_state,
                    mapped.target_candidate_version,
                    tuple(
                        dict.fromkeys(
                            (
                                mapped.source_state,
                                mapped.expected_owner_state_ref,
                                mapped.source_candidate_ref_or_explicit_absence,
                                *mapped.predecessor_transition_receipt_refs,
                            )
                        )
                    ),
                    tuple(
                        dict.fromkeys(
                            (mapped.destination_state, mapped.target_candidate_ref)
                        )
                    ),
                    mapped.typed_reason_codes,
                    mapped.predecessor_transition_receipt_refs,
                    mapped.causation_id,
                    mapped.correlation_id,
                )
                for row in self.control_receipt_proposals
            ) or tuple(
                row.typed_payload.control_class
                for row in self.control_receipt_proposals
            ) != expected_classes:
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    "control receipt cardinality and transition fields must resolve to the exact executed trace rows",
                )
        elif self.control_receipt_refs:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "string-only control receipt references are forbidden",
            )
        _exact_bool(self.no_authority_flag, "no_authority_flag")
        if self.no_authority_flag is not True:
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "mode snapshot proposal must retain its no-authority flag",
            )


@dataclass(frozen=True, slots=True)
class ModeSnapshotOwnerProjectionV1:
    decision_id: str
    mode_eligibility_state: ModeEligibilityState
    allow_candidate_state: AllowCandidateStateV1
    snapshot_candidate_state: SnapshotCandidateStateV1
    evidence_state: ST12FEvidenceStateV1
    kill_state: KillStateV1
    submit_disabled_state: SubmitDisabledStateV1
    stale_state: str
    reason_codes: tuple[ReasonCode, ...]
    fallback_route: str
    owner_review_route: str
    policy_and_snapshot_versions: tuple[str, ...]
    runtime_effect_authorized: bool = False
    order_release_authorized: bool = False

    def __post_init__(self) -> None:
        for name in ("decision_id", "stale_state", "fallback_route", "owner_review_route"):
            _canonical_text(getattr(self, name), name)
        for value, enum_type, name in (
            (self.mode_eligibility_state, ModeEligibilityState, "mode_eligibility_state"),
            (self.allow_candidate_state, AllowCandidateStateV1, "allow_candidate_state"),
            (self.snapshot_candidate_state, SnapshotCandidateStateV1, "snapshot_candidate_state"),
            (self.evidence_state, ST12FEvidenceStateV1, "evidence_state"),
            (self.kill_state, KillStateV1, "kill_state"),
            (self.submit_disabled_state, SubmitDisabledStateV1, "submit_disabled_state"),
        ):
            _typed_enum(value, enum_type, name)
        _reason_tuple(self.reason_codes, "reason_codes", require_nonempty=True)
        _validate_unique_text(
            self.policy_and_snapshot_versions,
            "policy_and_snapshot_versions",
            nonempty=True,
        )
        _must_be_false(self.runtime_effect_authorized, "runtime_effect_authorized")
        _must_be_false(self.order_release_authorized, "order_release_authorized")


@dataclass(frozen=True, slots=True)
class LatencyStageDurationsV1:
    central_capability_admission_ns: int
    request_validation_ns: int
    identity_and_context_resolution_ns: int
    parameter_and_source_binding_ns: int
    snapshot_candidate_resolution_ns: int
    formula_compute_ns: int
    output_validation_ns: int
    receipt_materialization_ns: int
    owner_projection_ns: int
    total_local_no_effect_ns: int

    def __post_init__(self) -> None:
        component_names = tuple(
            field.name
            for field in dataclass_fields(self)
            if field.name != "total_local_no_effect_ns"
        )
        if any(
            isinstance(getattr(self, name), bool)
            or not isinstance(getattr(self, name), int)
            or getattr(self, name) < 0
            for name in (*component_names, "total_local_no_effect_ns")
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "latency stage durations must be nonnegative integer nanoseconds",
            )
        if self.total_local_no_effect_ns != sum(
            getattr(self, name) for name in component_names
        ):
            raise ContractValidationError(
                ReasonCode.CLOCK_DOMAIN_MISMATCH,
                "total_local_no_effect_ns must equal the exact stage decomposition",
            )


@dataclass(frozen=True, slots=True)
class LatencyMeasurementLabelsV1:
    cold_or_warm: str
    concurrency_level: int
    platform_profile_id: str
    operation_id: str
    success_or_blocker: str
    fallback_used: bool

    def __post_init__(self) -> None:
        for name in (
            "cold_or_warm",
            "platform_profile_id",
            "operation_id",
            "success_or_blocker",
        ):
            _canonical_text(getattr(self, name), name)
        if self.cold_or_warm not in {"COLD", "WARM"}:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "cold_or_warm must be exact COLD or WARM",
            )
        if (
            isinstance(self.concurrency_level, bool)
            or not isinstance(self.concurrency_level, int)
            or self.concurrency_level < 1
        ):
            raise ContractValidationError(
                ReasonCode.RESOURCE_BOUND_EXCEEDED,
                "concurrency_level must be a positive integer",
            )
        _exact_bool(self.fallback_used, "fallback_used")


@dataclass(frozen=True, slots=True)
class LatencyMeasurementV1:
    measurement_ref: str
    event_time_utc: datetime
    local_duration_clock_id: str
    clock_implementation: str
    clock_resolution_ns: int
    platform_description: str
    stages: LatencyStageDurationsV1
    labels: LatencyMeasurementLabelsV1
    cumulative_stage_ns: tuple[int, ...]
    rejection_count: int
    observer_overhead_ns: int
    runtime_effect_authorized: bool = False

    def __post_init__(self) -> None:
        for name in (
            "measurement_ref",
            "local_duration_clock_id",
            "clock_implementation",
            "platform_description",
        ):
            _canonical_text(getattr(self, name), name)
        _utc_timestamp(self.event_time_utc, "event_time_utc")
        if self.local_duration_clock_id not in {
            "LOCAL_DURATION",
            "LOCAL_DURATION_FALLBACK",
        }:
            raise ContractValidationError(
                ReasonCode.CLOCK_DOMAIN_MISMATCH,
                "local durations require a registered monotonic clock",
            )
        if type(self.stages) is not LatencyStageDurationsV1 or type(
            self.labels
        ) is not LatencyMeasurementLabelsV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "latency measurement requires exact stage and label contracts",
            )
        if (
            isinstance(self.clock_resolution_ns, bool)
            or not isinstance(self.clock_resolution_ns, int)
            or self.clock_resolution_ns < 0
            or not isinstance(self.cumulative_stage_ns, tuple)
            or len(self.cumulative_stage_ns) != 9
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value < 0
                for value in self.cumulative_stage_ns
            )
            or tuple(sorted(self.cumulative_stage_ns)) != self.cumulative_stage_ns
            or self.cumulative_stage_ns[-1] != self.stages.total_local_no_effect_ns
        ):
            raise ContractValidationError(
                ReasonCode.CLOCK_DOMAIN_MISMATCH,
                "latency clock metadata or cumulative decomposition is invalid",
            )
        for name in ("rejection_count", "observer_overhead_ns"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    f"{name} must be a nonnegative integer",
                )
        _must_be_false(self.runtime_effect_authorized, "runtime_effect_authorized")


@dataclass(frozen=True, slots=True)
class LatencyBudgetProfileV1:
    profile_id: str
    component_budget_ns: tuple[tuple[str, int], ...]
    histogram_boundaries_ns: tuple[int, ...]
    maximum_observer_overhead_ns: int
    alert_threshold_ns: int
    policy_version: str

    def __post_init__(self) -> None:
        _canonical_text(self.profile_id, "profile_id")
        _canonical_text(self.policy_version, "policy_version")
        if (
            not isinstance(self.component_budget_ns, tuple)
            or not self.component_budget_ns
            or any(
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not item[0]
                or isinstance(item[1], bool)
                or not isinstance(item[1], int)
                or item[1] < 0
                for item in self.component_budget_ns
            )
            or len({item[0] for item in self.component_budget_ns})
            != len(self.component_budget_ns)
        ):
            raise ContractValidationError(
                ReasonCode.LATENCY_PROFILE_REQUIRED,
                "component budgets must be exact unique owner-supplied nanosecond rows",
            )
        if (
            not isinstance(self.histogram_boundaries_ns, tuple)
            or not self.histogram_boundaries_ns
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value < 0
                for value in self.histogram_boundaries_ns
            )
            or tuple(sorted(set(self.histogram_boundaries_ns)))
            != self.histogram_boundaries_ns
        ):
            raise ContractValidationError(
                ReasonCode.LATENCY_PROFILE_REQUIRED,
                "histogram boundaries must be strictly increasing nanoseconds",
            )
        for name in ("maximum_observer_overhead_ns", "alert_threshold_ns"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractValidationError(
                    ReasonCode.LATENCY_PROFILE_REQUIRED,
                    f"{name} must be owner-supplied nonnegative nanoseconds",
                )


@dataclass(frozen=True, slots=True)
class ResourceBoundsProfileV1:
    profile_id: str
    maximum_input_cardinality: int
    maximum_input_bytes: int
    maximum_dependency_depth: int
    maximum_bootstrap_repetitions: int
    maximum_concurrency: int

    def __post_init__(self) -> None:
        _canonical_text(self.profile_id, "profile_id")
        for name in (
            "maximum_input_cardinality",
            "maximum_input_bytes",
            "maximum_dependency_depth",
            "maximum_bootstrap_repetitions",
            "maximum_concurrency",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ContractValidationError(
                    ReasonCode.RESOURCE_BOUND_EXCEEDED,
                    f"{name} must be an explicit positive bound",
                )


@dataclass(frozen=True, slots=True)
class TransactionEnvelopeV1:
    transaction_id: str
    snapshot_id: str
    relative_output_path: str | None = None
    state: TransactionState = TransactionState.IN_MEMORY_ONLY
    committed: bool = False

    def __post_init__(self) -> None:
        _required(self.transaction_id, "transaction_id")
        _required(self.snapshot_id, "snapshot_id")
        _typed_enum(self.state, TransactionState, "state")
        _exact_bool(self.committed, "committed")
        if self.relative_output_path is not None:
            from .serialization import validate_relative_path

            validate_relative_path(self.relative_output_path)
        if self.committed:
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "Tranche A transaction envelopes cannot commit durable state",
            )


@dataclass(frozen=True, slots=True)
class ConfigurationEnvelopeV1:
    configuration_id: str
    version: str
    parameter_ids: tuple[str, ...]
    mutable_runtime: bool = False

    def __post_init__(self) -> None:
        _required(self.configuration_id, "configuration_id")
        _required(self.version, "version")
        _text_tuple(self.parameter_ids, "parameter_ids")
        if len(set(self.parameter_ids)) != len(self.parameter_ids):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "configuration parameter ids must be unique",
            )
        from .parameter_policy import get_parameter_policy

        for parameter_id in self.parameter_ids:
            get_parameter_policy(parameter_id)
        _exact_bool(self.mutable_runtime, "mutable_runtime")
        if self.mutable_runtime:
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "Tranche A configuration is immutable contract metadata",
            )


@dataclass(frozen=True, slots=True)
class HealthEnvelopeV1:
    component_id: str
    state: HealthState
    reasons: tuple[str, ...] = ()
    starts_process: bool = False

    def __post_init__(self) -> None:
        _required(self.component_id, "component_id")
        _typed_enum(self.state, HealthState, "state")
        _text_tuple(self.reasons, "reasons")
        _exact_bool(self.starts_process, "starts_process")
        if self.starts_process:
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "health contracts cannot start a process",
            )


@dataclass(frozen=True, slots=True)
class SupervisionEnvelopeV1:
    supervision_id: str
    component_ids: tuple[str, ...]
    process_supervision_enabled: bool = False

    def __post_init__(self) -> None:
        _required(self.supervision_id, "supervision_id")
        _text_tuple(self.component_ids, "component_ids", require_nonempty=True)
        if len(set(self.component_ids)) != len(self.component_ids):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "supervision component ids must be unique",
            )
        _exact_bool(
            self.process_supervision_enabled, "process_supervision_enabled"
        )
        if self.process_supervision_enabled:
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "process supervision is outside Tranche A",
            )


@dataclass(frozen=True, slots=True)
class FallbackEnvelopeV1:
    fallback_id: str
    reason_codes: tuple[str, ...]
    target: str
    permits_new_writes: bool = False

    def __post_init__(self) -> None:
        _required(self.fallback_id, "fallback_id")
        _required(self.target, "target")
        _text_tuple(self.reason_codes, "reason_codes", require_nonempty=True)
        _exact_bool(self.permits_new_writes, "permits_new_writes")
        if self.permits_new_writes:
            raise ContractValidationError(
                ReasonCode.CAPABILITY_DENIED,
                "Tranche A fallback contracts cannot permit new writes",
            )


_TRACEPARENT_RE = re.compile(
    r"^00-(?P<trace>[0-9a-f]{32})-(?P<span>[0-9a-f]{16})-(?P<flags>[0-9a-f]{2})$"
)
_TRACESTATE_KEY_RE = re.compile(
    r"^(?:[a-z][_0-9a-z\-\*/]{0,255}|"
    r"[a-z0-9][_0-9a-z\-\*/]{0,240}@[a-z][_0-9a-z\-\*/]{0,13})$"
)


def _validate_timestamp(value: object, field_name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be a timezone-aware datetime",
        )


def _validate_trace_context(
    traceparent: object,
    tracestate: object,
) -> tuple[str, str]:
    if not isinstance(traceparent, str):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "traceparent must be W3C trace-context text",
        )
    match = _TRACEPARENT_RE.fullmatch(traceparent)
    if (
        match is None
        or match.group("trace") == "0" * 32
        or match.group("span") == "0" * 16
    ):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "traceparent must be a valid W3C version-00 value",
        )
    if not isinstance(tracestate, str) or len(tracestate) > 512:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "tracestate must be text bounded to 512 characters",
        )
    if tracestate:
        members = tracestate.split(",")
        if len(members) > 32 or any(
            member != member.strip() or "=" not in member for member in members
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "tracestate must contain at most 32 canonical members",
            )
        keys: list[str] = []
        for member in members:
            key, value = member.split("=", 1)
            if (
                _TRACESTATE_KEY_RE.fullmatch(key) is None
                or not value
                or len(value) > 256
                or value[0] == " "
                or value[-1] == " "
                or any(
                    ord(character) < 0x20
                    or ord(character) > 0x7E
                    or character in ",="
                    for character in value
                )
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    "tracestate contains a noncanonical W3C member",
                )
            keys.append(key)
        if len(keys) != len(set(keys)):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "tracestate member keys must be unique",
            )
    return match.group("trace"), match.group("span")


def _validate_unique_text(values: object, field_name: str, *, nonempty: bool = False) -> None:
    typed = _text_tuple(values, field_name, require_nonempty=nonempty)
    if len(typed) != len(set(typed)):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must not contain duplicates",
        )


def validate_reference_identity_classes(
    *,
    policy_refs: tuple[str, ...] = (),
    semantic_policy_set_versions: tuple[str, ...] = (),
    source_snapshot_refs: tuple[str, ...] = (),
    source_epoch_refs: tuple[str, ...] = (),
    receipt_refs: tuple[str, ...] = (),
    candidate_or_decision_refs: tuple[str, ...] = (),
    explicit_absence_refs: tuple[str, ...] = (),
) -> None:
    """Enforce the non-overlapping D reference ontology at existing boundaries."""

    classes = {
        "policy_ref": policy_refs,
        "semantic_policy_set_version": semantic_policy_set_versions,
        "source_snapshot_ref": source_snapshot_refs,
        "source_epoch_ref": source_epoch_refs,
        "receipt_ref": receipt_refs,
        "candidate_or_decision_ref": candidate_or_decision_refs,
    }
    for name, values in classes.items():
        _validate_unique_text(values, name)
        if "EXPLICIT_ABSENCE" in values:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                f"explicit absence cannot occupy the {name} class",
            )
    _validate_unique_text(explicit_absence_refs, "explicit_absence")
    if any(value != "EXPLICIT_ABSENCE" for value in explicit_absence_refs):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "explicit-absence references must use the exact typed absence identity",
        )
    typed_sets = {name: set(values) for name, values in classes.items()}
    names = tuple(typed_sets)
    collisions = {
        value
        for index, name in enumerate(names)
        for other in names[index + 1 :]
        for value in typed_sets[name] & typed_sets[other]
    }
    if collisions:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "reference identities cannot satisfy multiple semantic classes: "
            + ", ".join(sorted(collisions)),
        )
    forbidden_receipt_prefixes = (
        "ComputationParameterPolicyV1::",
        "OWNER-PROJECTION-RECEIPT::",
    )
    forbidden_epoch_prefixes = (
        "PARAMETER-POLICY-EPOCH::",
        "OWNER-PROJECTION-EPOCH::",
        "EVIDENCE-EPOCH::",
    )
    if any(ref.startswith(forbidden_receipt_prefixes) for ref in receipt_refs):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "policy or projection identities cannot satisfy receipt fields",
        )
    if any(ref.startswith(forbidden_epoch_prefixes) for ref in source_epoch_refs):
        raise ContractValidationError(
            ReasonCode.SOURCE_EPOCH_STALE,
            "semantic policy or projection versions cannot satisfy source epochs",
        )


def _validate_execution_context(context: object) -> None:
    if not isinstance(context, ComputationExecutionContextV1):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "computation-plan operations require ComputationExecutionContextV1",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class OperationRequestEnvelopeV1:
    request_id: str
    operation_name: str
    requested_at: datetime
    principal_id: str
    capability_bundle_id: str
    context: ComputationContextKeyV1
    idempotency_key: str
    traceparent: str
    tracestate: str
    EXPECTED_OPERATION_NAME: ClassVar[str] = ""

    def __post_init__(self) -> None:
        for name in (
            "request_id",
            "principal_id",
            "capability_bundle_id",
            "idempotency_key",
        ):
            _required(getattr(self, name), name)
        if self.operation_name != self.EXPECTED_OPERATION_NAME:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation_name must exactly equal the certified operation name",
            )
        _validate_timestamp(self.requested_at, "requested_at")
        from .context import ComputationContextKeyV1

        if not isinstance(self.context, ComputationContextKeyV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "context must be a typed ComputationContextKeyV1",
            )
        trace_id, span_id = _validate_trace_context(
            self.traceparent,
            self.tracestate,
        )
        if (
            len(self.idempotency_key) > 256
            or self.idempotency_key == self.request_id
            or self.idempotency_key == self.traceparent
            or (
                bool(self.tracestate)
                and self.idempotency_key == self.tracestate
            )
            or trace_id in self.idempotency_key.casefold()
            or span_id in self.idempotency_key.casefold()
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "economic idempotency must be distinct from request and trace correlation",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolveIdentityRequestV1(OperationRequestEnvelopeV1):
    identity_query: TypedValueRecordV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "resolve_identity"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        if not isinstance(self.identity_query, TypedValueRecordV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "identity_query must be a typed record",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolveContextualComputabilityRequestV1(OperationRequestEnvelopeV1):
    component_id: str
    required_computability_classes: tuple[ComputabilityClassV1, ...]
    EXPECTED_OPERATION_NAME: ClassVar[str] = "resolve_contextual_computability"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        _validate_execution_context(self.context)
        _required(self.component_id, "component_id")
        if (
            not isinstance(self.required_computability_classes, tuple)
            or not self.required_computability_classes
            or any(
                not isinstance(value, ComputabilityClassV1)
                for value in self.required_computability_classes
            )
            or len(set(self.required_computability_classes))
            != len(self.required_computability_classes)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "required computability classes must be a unique typed tuple",
            )
        if (
            ComputabilityClassV1.STACK_COMPUTABLE
            in self.required_computability_classes
            and self.context.dependency_graph_id is None
        ):
            raise ContractValidationError(
                ReasonCode.NO_APPLICABLE_STACK,
                "STACK_COMPUTABLE requires an exact selected dependency graph",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolveApplicableStackRequestV1(OperationRequestEnvelopeV1):
    trade_plan_candidate_id: str
    required_launch_roles: tuple[str, ...]
    EXPECTED_OPERATION_NAME: ClassVar[str] = "resolve_applicable_stack"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        _validate_execution_context(self.context)
        _required(self.trade_plan_candidate_id, "trade_plan_candidate_id")
        _validate_unique_text(
            self.required_launch_roles,
            "required_launch_roles",
            nonempty=True,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolveRequiredInputsRequestV1(OperationRequestEnvelopeV1):
    component_ids: tuple[str, ...]
    include_optional: bool
    EXPECTED_OPERATION_NAME: ClassVar[str] = "resolve_required_inputs"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        _validate_execution_context(self.context)
        _validate_unique_text(self.component_ids, "component_ids", nonempty=True)
        _exact_bool(self.include_optional, "include_optional")


@dataclass(frozen=True, slots=True, kw_only=True)
class ComputeComponentRequestV1(OperationRequestEnvelopeV1):
    component_id: str
    input_values: TypedValueRecordV1
    expected_output_schema_ref: str
    EXPECTED_OPERATION_NAME: ClassVar[str] = "compute_component"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        _validate_execution_context(self.context)
        _required(self.component_id, "component_id")
        _required(self.expected_output_schema_ref, "expected_output_schema_ref")
        if not isinstance(self.input_values, TypedValueRecordV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "input_values must be a typed record",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ComputeStackRequestV1(OperationRequestEnvelopeV1):
    stack_id: str
    component_ids: tuple[str, ...]
    input_values: TypedValueRecordV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "compute_stack"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        _validate_execution_context(self.context)
        _required(self.stack_id, "stack_id")
        _validate_unique_text(self.component_ids, "component_ids", nonempty=True)
        if not isinstance(self.input_values, TypedValueRecordV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "input_values must be a typed record",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class CompareWithNoTradeRequestV1(OperationRequestEnvelopeV1):
    trade_plan_candidate_id: str
    no_trade_candidate_id: str
    comparison_basis: str
    EXPECTED_OPERATION_NAME: ClassVar[str] = "compare_with_no_trade"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        for name in (
            "trade_plan_candidate_id",
            "no_trade_candidate_id",
            "comparison_basis",
        ):
            _required(getattr(self, name), name)
        if self.trade_plan_candidate_id == self.no_trade_candidate_id:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "trade and no-trade candidates must be distinct",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluateTradePlanRequestV1(OperationRequestEnvelopeV1):
    trade_plan_candidate_id: str
    stack_id: str
    accounting_tca_view_ref: str
    risk_cash_state_ref: str
    no_trade_candidate_id: str
    EXPECTED_OPERATION_NAME: ClassVar[str] = "evaluate_trade_plan"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        for name in (
            "trade_plan_candidate_id",
            "stack_id",
            "accounting_tca_view_ref",
            "risk_cash_state_ref",
            "no_trade_candidate_id",
        ):
            _required(getattr(self, name), name)
        if self.trade_plan_candidate_id == self.no_trade_candidate_id:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "trade-plan evaluation requires a distinct no-trade comparator",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class GetSnapshotViewRequestV1(OperationRequestEnvelopeV1):
    snapshot_id: str
    view_class: str
    include_value_lineage: bool
    EXPECTED_OPERATION_NAME: ClassVar[str] = "get_snapshot_view"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        _required(self.snapshot_id, "snapshot_id")
        _required(self.view_class, "view_class")
        _exact_bool(self.include_value_lineage, "include_value_lineage")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExplainResolutionRequestV1(OperationRequestEnvelopeV1):
    resolution_receipt_id: str
    explanation_scope: str
    max_evidence_items: int
    EXPECTED_OPERATION_NAME: ClassVar[str] = "explain_resolution"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        _required(self.resolution_receipt_id, "resolution_receipt_id")
        _required(self.explanation_scope, "explanation_scope")
        if (
            isinstance(self.max_evidence_items, bool)
            or not isinstance(self.max_evidence_items, int)
            or self.max_evidence_items <= 0
            or self.max_evidence_items > 10_000
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "max_evidence_items must be an integer in [1, 10000]",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class SubmitCandidateProposalRequestV1(OperationRequestEnvelopeV1):
    candidate_kind: str
    proposed_specification: TypedValueRecordV1
    source_candidate_refs: tuple[str, ...]
    requested_owner_review: bool
    EXPECTED_OPERATION_NAME: ClassVar[str] = "submit_candidate_proposal"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        _required(self.candidate_kind, "candidate_kind")
        if not isinstance(self.proposed_specification, TypedValueRecordV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "proposed_specification must be a typed record",
            )
        _validate_unique_text(
            self.source_candidate_refs,
            "source_candidate_refs",
            nonempty=True,
        )
        _exact_bool(self.requested_owner_review, "requested_owner_review")


@dataclass(frozen=True, slots=True, kw_only=True)
class RequestMaterializationWorkOrderRequestV1(OperationRequestEnvelopeV1):
    missing_contract_ids: tuple[str, ...]
    reason_codes: tuple[OperationBlockerCodeV1, ...]
    priority: str
    requested_owner: str
    EXPECTED_OPERATION_NAME: ClassVar[str] = "request_materialization_work_order"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        _validate_unique_text(
            self.missing_contract_ids,
            "missing_contract_ids",
            nonempty=True,
        )
        if (
            not isinstance(self.reason_codes, tuple)
            or not self.reason_codes
            or any(
                not isinstance(value, OperationBlockerCodeV1)
                for value in self.reason_codes
            )
            or len(set(self.reason_codes)) != len(self.reason_codes)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "reason_codes must be a nonempty unique typed blocker tuple",
            )
        _required(self.priority, "priority")
        _required(self.requested_owner, "requested_owner")


@dataclass(frozen=True, slots=True, kw_only=True)
class CompileReplayPaperCohortRequestV1(OperationRequestEnvelopeV1):
    template_ids: tuple[str, ...]
    requested_lanes: tuple[str, ...]
    input_lock_id: str
    campaign_execution_requested: bool
    EXPECTED_OPERATION_NAME: ClassVar[str] = "compile_replay_paper_cohort"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        _validate_unique_text(self.template_ids, "template_ids", nonempty=True)
        _validate_unique_text(
            self.requested_lanes,
            "requested_lanes",
            nonempty=True,
        )
        if not set(self.requested_lanes) <= {"REPLAY", "PAPER"}:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "requested_lanes must use only the REPLAY/PAPER contract labels",
            )
        _required(self.input_lock_id, "input_lock_id")
        _exact_bool(
            self.campaign_execution_requested,
            "campaign_execution_requested",
        )
        if self.campaign_execution_requested:
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "Tranche A may define a cohort but cannot execute a campaign",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class RegisterReplayPaperResultRequestV1(OperationRequestEnvelopeV1):
    cohort_instance_id: str
    lane: str
    input_lock_id: str
    result_packet: TypedValueRecordV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "register_replay_paper_result"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        _required(self.cohort_instance_id, "cohort_instance_id")
        _required(self.input_lock_id, "input_lock_id")
        if self.lane not in {"REPLAY", "PAPER"}:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "lane must be an exact REPLAY or PAPER contract label",
            )
        if not isinstance(self.result_packet, TypedValueRecordV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "result_packet must be a typed pre-existing result record",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class BuildEvidenceBundleRequestV1(OperationRequestEnvelopeV1):
    component_id: str
    input_lock_id: str
    evidence_record_refs: tuple[str, ...]
    required_lanes: tuple[str, ...]
    EXPECTED_OPERATION_NAME: ClassVar[str] = "build_evidence_bundle"

    def __post_init__(self) -> None:
        OperationRequestEnvelopeV1.__post_init__(self)
        _required(self.component_id, "component_id")
        _required(self.input_lock_id, "input_lock_id")
        _validate_unique_text(
            self.evidence_record_refs,
            "evidence_record_refs",
            nonempty=True,
        )
        _validate_unique_text(
            self.required_lanes,
            "required_lanes",
            nonempty=True,
        )
        if not set(self.required_lanes) <= {"REPLAY", "PAPER"}:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "required_lanes must use only REPLAY/PAPER contract labels",
            )


@dataclass(frozen=True, slots=True)
class _TypedOperationResultV1:
    result_id: str
    terminal_route: str
    evidence_refs: tuple[str, ...]
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        _required(self.result_id, "result_id")
        _required(self.terminal_route, "terminal_route")
        _validate_unique_text(self.evidence_refs, "evidence_refs")
        _exact_bool(self.no_authority_flag, "no_authority_flag")
        if not self.no_authority_flag:
            raise ContractValidationError(
                ReasonCode.CAPABILITY_DENIED,
                "operation results cannot create authority",
            )


@dataclass(frozen=True, slots=True)
class FrozenFormulaOutputV1:
    """One version-pinned ST12B_OUTPUT_V3_4 result kept in native typed form."""

    math_spec_id: str
    implementation_id: str
    mathematical_semantic_version: str
    repository_specification_version: str
    output_schema_ref: str
    output_schema_version: str
    output_name: str
    value: object
    execution_context: ComputationExecutionContextV1
    receipt_refs: tuple[str, ...] = ()
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        for name in (
            "math_spec_id",
            "implementation_id",
            "mathematical_semantic_version",
            "repository_specification_version",
            "output_schema_ref",
            "output_schema_version",
            "output_name",
        ):
            _required(getattr(self, name), name)
        if not isinstance(
            self.execution_context, ComputationExecutionContextV1
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "formula output requires the exact execution context",
            )
        if self.output_schema_version not in {
            "ST12B_OUTPUT_V3_4",
            "ST12D_OUTPUT_V1",
        }:
            raise ContractValidationError(
                ReasonCode.OUTPUT_SCHEMA_MISMATCH,
                "formula outputs must use an exact current output schema version",
            )
        _validate_unique_text(self.receipt_refs, "receipt_refs")
        _exact_bool(self.no_authority_flag, "no_authority_flag")
        if not self.no_authority_flag:
            raise ContractValidationError(
                ReasonCode.CAPABILITY_DENIED,
                "formula output envelopes cannot create authority",
            )

    @property
    def context_id(self) -> str:
        return self.execution_context.context_id


@dataclass(frozen=True, slots=True)
class IdentityResolutionV1(_TypedOperationResultV1):
    identity_ref: str = ""


@dataclass(frozen=True, slots=True)
class StackResolutionV1(_TypedOperationResultV1):
    stack_id: str = ""
    component_ids: tuple[str, ...] = ()
    dependency_receipt_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class InputResolutionV1(_TypedOperationResultV1):
    component_ids: tuple[str, ...] = ()
    resolved_input_names: tuple[str, ...] = ()
    owner_packet_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ComponentResultV1(_TypedOperationResultV1):
    component_id: str = ""
    formula_output: FrozenFormulaOutputV1 | None = None


@dataclass(frozen=True, slots=True)
class StackResultV1(_TypedOperationResultV1):
    stack_id: str = ""
    component_outputs: tuple[FrozenFormulaOutputV1, ...] = ()
    conversion_receipt_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NoTradeComparisonV1(_TypedOperationResultV1):
    comparison_basis: str = ""
    downstream_blocker_ref: str = ""


@dataclass(frozen=True, slots=True)
class TradePlanEvaluationV1(_TypedOperationResultV1):
    downstream_blocker_ref: str = ""


@dataclass(frozen=True, slots=True)
class SnapshotViewV1(_TypedOperationResultV1):
    snapshot_id: str = ""
    view_class: str = ""


@dataclass(frozen=True, slots=True)
class ResolutionExplanationV1(_TypedOperationResultV1):
    blocker_codes: tuple[OperationBlockerCodeV1, ...] = ()
    next_safe_route: str = ""


@dataclass(frozen=True, slots=True)
class CandidateProposalV1(_TypedOperationResultV1):
    candidate_id: str = ""
    proposal_state: str = "NO_EFFECT_RECORD"
    mode_snapshot_result: ModeSnapshotCandidateProposalResultV1 | None = None

    def __post_init__(self) -> None:
        _TypedOperationResultV1.__post_init__(self)
        _canonical_text(self.candidate_id, "candidate_id")
        _canonical_text(self.proposal_state, "proposal_state")
        if self.mode_snapshot_result is not None and type(
            self.mode_snapshot_result
        ) is not ModeSnapshotCandidateProposalResultV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "mode_snapshot_result must be the exact optional D result",
            )


@dataclass(frozen=True, slots=True)
class MaterializationWorkOrderV1(_TypedOperationResultV1):
    work_order_id: str = ""
    requested_owner: str = ""
    work_order_state: str = "NO_EFFECT_RECORD"


@dataclass(frozen=True, slots=True)
class ReplayPaperCohortCompilationV1(_TypedOperationResultV1):
    pass


@dataclass(frozen=True, slots=True)
class ReplayPaperResultRegistrationV1(_TypedOperationResultV1):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceBundleResultV1(_TypedOperationResultV1):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class OperationResponseEnvelopeV1:
    response_id: str
    operation_name: str
    request_id: str
    completed_at: datetime
    status: OperationStatusV1
    context: ComputationContextKeyV1
    warnings: tuple[str, ...]
    blocker_codes: tuple[OperationBlockerCodeV1, ...]
    receipt_refs: tuple[str, ...]
    traceparent: str
    tracestate: str
    EXPECTED_OPERATION_NAME: ClassVar[str] = ""

    def __post_init__(self) -> None:
        _required(self.response_id, "response_id")
        _required(self.request_id, "request_id")
        if self.operation_name != self.EXPECTED_OPERATION_NAME:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation_name must exactly equal the certified operation name",
            )
        _validate_timestamp(self.completed_at, "completed_at")
        _typed_enum(self.status, OperationStatusV1, "status")
        from .context import ComputationContextKeyV1

        if not isinstance(self.context, ComputationContextKeyV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "context must be a typed ComputationContextKeyV1",
            )
        _validate_unique_text(self.warnings, "warnings")
        _validate_unique_text(self.receipt_refs, "receipt_refs")
        if (
            not isinstance(self.blocker_codes, tuple)
            or any(
                not isinstance(value, OperationBlockerCodeV1)
                for value in self.blocker_codes
            )
            or len(set(self.blocker_codes)) != len(self.blocker_codes)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "blocker_codes must be a unique typed tuple",
            )
        if (
            self.status is OperationStatusV1.SUCCEEDED
            and self.blocker_codes
        ) or (
            self.status is not OperationStatusV1.SUCCEEDED
            and not self.blocker_codes
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "response status and typed blocker codes are inconsistent",
            )
        _validate_trace_context(self.traceparent, self.tracestate)


def _validate_response_result(value: object, expected: type[object], name: str) -> None:
    if not isinstance(value, expected):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{name} must be a typed {expected.__name__}",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolveIdentityResponseV1(OperationResponseEnvelopeV1):
    identity_resolution: IdentityResolutionV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "resolve_identity"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.identity_resolution,
            IdentityResolutionV1,
            "identity_resolution",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolveContextualComputabilityResponseV1(OperationResponseEnvelopeV1):
    computability: ContextualComputabilityResolutionV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "resolve_contextual_computability"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.computability,
            ContextualComputabilityResolutionV1,
            "computability",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolveApplicableStackResponseV1(OperationResponseEnvelopeV1):
    stack_resolution: StackResolutionV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "resolve_applicable_stack"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.stack_resolution,
            StackResolutionV1,
            "stack_resolution",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolveRequiredInputsResponseV1(OperationResponseEnvelopeV1):
    input_resolution: InputResolutionV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "resolve_required_inputs"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.input_resolution,
            InputResolutionV1,
            "input_resolution",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ComputeComponentResponseV1(OperationResponseEnvelopeV1):
    component_result: ComponentResultV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "compute_component"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.component_result,
            ComponentResultV1,
            "component_result",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ComputeStackResponseV1(OperationResponseEnvelopeV1):
    stack_result: StackResultV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "compute_stack"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(self.stack_result, StackResultV1, "stack_result")


@dataclass(frozen=True, slots=True, kw_only=True)
class CompareWithNoTradeResponseV1(OperationResponseEnvelopeV1):
    comparison: NoTradeComparisonV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "compare_with_no_trade"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.comparison,
            NoTradeComparisonV1,
            "comparison",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluateTradePlanResponseV1(OperationResponseEnvelopeV1):
    evaluation: TradePlanEvaluationV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "evaluate_trade_plan"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.evaluation,
            TradePlanEvaluationV1,
            "evaluation",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class GetSnapshotViewResponseV1(OperationResponseEnvelopeV1):
    snapshot_view: SnapshotViewV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "get_snapshot_view"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.snapshot_view,
            SnapshotViewV1,
            "snapshot_view",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ExplainResolutionResponseV1(OperationResponseEnvelopeV1):
    explanation: ResolutionExplanationV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "explain_resolution"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.explanation,
            ResolutionExplanationV1,
            "explanation",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class SubmitCandidateProposalResponseV1(OperationResponseEnvelopeV1):
    proposal: CandidateProposalV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "submit_candidate_proposal"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.proposal,
            CandidateProposalV1,
            "proposal",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class RequestMaterializationWorkOrderResponseV1(OperationResponseEnvelopeV1):
    work_order: MaterializationWorkOrderV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "request_materialization_work_order"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.work_order,
            MaterializationWorkOrderV1,
            "work_order",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class CompileReplayPaperCohortResponseV1(OperationResponseEnvelopeV1):
    cohort_compilation: ReplayPaperCohortCompilationV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "compile_replay_paper_cohort"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.cohort_compilation,
            ReplayPaperCohortCompilationV1,
            "cohort_compilation",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class RegisterReplayPaperResultResponseV1(OperationResponseEnvelopeV1):
    registration: ReplayPaperResultRegistrationV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "register_replay_paper_result"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.registration,
            ReplayPaperResultRegistrationV1,
            "registration",
        )
        if self.receipt_refs != self.registration.evidence_refs:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "OP14 response and result must carry the same ordered produced-receipt tuple",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class BuildEvidenceBundleResponseV1(OperationResponseEnvelopeV1):
    evidence_bundle: EvidenceBundleResultV1
    EXPECTED_OPERATION_NAME: ClassVar[str] = "build_evidence_bundle"

    def __post_init__(self) -> None:
        OperationResponseEnvelopeV1.__post_init__(self)
        _validate_response_result(
            self.evidence_bundle,
            EvidenceBundleResultV1,
            "evidence_bundle",
        )
        if self.receipt_refs != self.evidence_bundle.evidence_refs:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "OP15 response and result must carry the same ordered produced-receipt tuple",
            )


@dataclass(frozen=True, slots=True)
class OperationFailureEnvelopeV1:
    operation_id: str
    operation_name: str
    request_id: str
    blocker_codes: tuple[OperationBlockerCodeV1, ...]
    receipt_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("operation_id", "operation_name", "request_id"):
            _required(getattr(self, name), name)
        if (
            not isinstance(self.blocker_codes, tuple)
            or not self.blocker_codes
            or any(
                not isinstance(value, OperationBlockerCodeV1)
                for value in self.blocker_codes
            )
            or len(set(self.blocker_codes)) != len(self.blocker_codes)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation failure requires typed unique blocker codes",
            )
        _validate_unique_text(self.receipt_refs, "receipt_refs")


@dataclass(frozen=True, slots=True)
class OperationContractV1:
    operation_id: str
    operation_name: str
    owner: str
    request_type: str
    response_type: str
    schema_version: str
    request_fields: tuple[ContractFieldV1, ...]
    response_fields: tuple[ContractFieldV1, ...]
    request_model: type[OperationRequestEnvelopeV1]
    response_model: type[OperationResponseEnvelopeV1]
    resolver_name: str | None = None
    runtime_effect_authorized: bool = False
    provider_effect_authorized: bool = False
    capability_class: OperationCapabilityClass = (
        OperationCapabilityClass.CONTRACT_DEFINITION_ONLY
    )
    side_effect_class: OperationSideEffectClass = (
        OperationSideEffectClass.PURE_OR_APPEND_ONLY_NON_PROVIDER_EFFECT
    )
    metadata: Mapping[str, str] = field(default_factory=immutable_mapping)

    def __post_init__(self) -> None:
        for name in (
            "operation_id",
            "operation_name",
            "owner",
            "request_type",
            "response_type",
            "schema_version",
        ):
            _required(getattr(self, name), name)
        if self.schema_version != "1.4.0":
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "certified operation schema version must be 1.4.0",
            )
        if (
            not isinstance(self.request_model, type)
            or not issubclass(self.request_model, OperationRequestEnvelopeV1)
            or self.request_model is OperationRequestEnvelopeV1
            or not isinstance(self.response_model, type)
            or not issubclass(self.response_model, OperationResponseEnvelopeV1)
            or self.response_model is OperationResponseEnvelopeV1
            or self.request_type != self.request_model.__name__
            or self.response_type != self.response_model.__name__
            or self.request_model.EXPECTED_OPERATION_NAME != self.operation_name
            or self.response_model.EXPECTED_OPERATION_NAME != self.operation_name
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation model lineage does not match its certified schema",
            )
        for name, model in (
            ("request_fields", self.request_model),
            ("response_fields", self.response_model),
        ):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or any(not isinstance(value, ContractFieldV1) for value in values)
                or len({value.name for value in values}) != len(values)
                or tuple(value.name for value in values)
                != tuple(value.name for value in dataclass_fields(model))
                or any(not value.required for value in values)
            ):
                raise ContractValidationError(
                    ReasonCode.INCOMPLETE_CONTRACT,
                    f"{name} must exactly match the typed top-level model",
                )
        if self.resolver_name is not None:
            _required(self.resolver_name, "resolver_name")
        for name in ("runtime_effect_authorized", "provider_effect_authorized"):
            _exact_bool(getattr(self, name), name)
        _typed_enum(
            self.capability_class,
            OperationCapabilityClass,
            "capability_class",
        )
        _typed_enum(
            self.side_effect_class,
            OperationSideEffectClass,
            "side_effect_class",
        )
        if (
            self.runtime_effect_authorized
            or self.provider_effect_authorized
            or self.capability_class
            is not OperationCapabilityClass.CONTRACT_DEFINITION_ONLY
            or self.side_effect_class
            is not OperationSideEffectClass.PURE_OR_APPEND_ONLY_NON_PROVIDER_EFFECT
        ):
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "Tranche A operation schemas cannot authorize runtime/provider effects",
            )
        object.__setattr__(self, "metadata", immutable_mapping(self.metadata))

    @property
    def input_contract(self) -> str:
        return self.request_type

    @property
    def output_contract(self) -> str:
        return self.response_type

    @property
    def failure_contract(self) -> str:
        return self.response_type

    def bind_request(self, **values: object) -> OperationRequestEnvelopeV1:
        expected = tuple(field.name for field in self.request_fields)
        if set(values) != set(expected):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation request has missing or extra top-level fields",
            )
        request = self.request_model(**values)
        if request.operation_name != self.operation_name:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation request name does not match the registry",
            )
        return request

    def bind_response(
        self,
        request: OperationRequestEnvelopeV1,
        **values: object,
    ) -> OperationResponseEnvelopeV1:
        expected = tuple(field.name for field in self.response_fields)
        if set(values) != set(expected):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation response has missing or extra top-level fields",
            )
        if not isinstance(request, self.request_model):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation response request lineage does not match the contract",
            )
        response = self.response_model(**values)
        if (
            response.operation_name != self.operation_name
            or response.request_id != request.request_id
            or response.traceparent != request.traceparent
            or response.tracestate != request.tracestate
            or response.context != request.context
            or response.completed_at < request.requested_at
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation response correlation does not match the request",
            )
        return response

    def request_json(self, request: OperationRequestEnvelopeV1) -> str:
        if not isinstance(request, self.request_model):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "request does not match the certified operation type",
            )
        from .serialization import deterministic_json

        return deterministic_json(request)

    def response_json(self, response: OperationResponseEnvelopeV1) -> str:
        if not isinstance(response, self.response_model):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "response does not match the certified operation type",
            )
        from .serialization import deterministic_json

        return deterministic_json(response)

    def validate_request_json(
        self,
        request: OperationRequestEnvelopeV1,
        text: str,
    ) -> None:
        from .serialization import safe_json_loads

        decoded = safe_json_loads(text)
        if (
            not isinstance(decoded, dict)
            or tuple(sorted(decoded)) != tuple(
                sorted(field.name for field in self.request_fields)
            )
            or text != self.request_json(request)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "request JSON is not the exact deterministic operation schema",
            )

    def validate_response_json(
        self,
        response: OperationResponseEnvelopeV1,
        text: str,
    ) -> None:
        from .serialization import safe_json_loads

        decoded = safe_json_loads(text)
        if (
            not isinstance(decoded, dict)
            or tuple(sorted(decoded)) != tuple(
                sorted(field.name for field in self.response_fields)
            )
            or text != self.response_json(response)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "response JSON is not the exact deterministic operation schema",
            )
