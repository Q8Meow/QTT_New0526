"""Frozen data contracts owned by QKUComputationControlPlaneV1."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, StrEnum
from types import MappingProxyType
from typing import Mapping, TypeVar

from .errors import ContractValidationError, ReasonCode


def _required(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT, f"{field_name} is required"
        )


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
    NONE_CONTRACT_ONLY = "NONE_CONTRACT_ONLY"


class OperationSideEffectClass(StrEnum):
    NONE = "NONE"


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
class ComputationEvidenceBundleV1:
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


@dataclass(frozen=True, slots=True)
class OperationRequestEnvelopeV1:
    operation_id: str
    request_contract: str
    request_id: str
    contract_version: str
    payload_json: str

    def __post_init__(self) -> None:
        for name in (
            "operation_id",
            "request_contract",
            "request_id",
            "contract_version",
            "payload_json",
        ):
            _required(getattr(self, name), name)
        from .serialization import deterministic_json, safe_json_loads

        payload = safe_json_loads(self.payload_json)
        if not isinstance(payload, dict):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation request payload must encode an object",
            )
        if self.payload_json != deterministic_json(payload):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation request payload must use deterministic JSON",
            )


@dataclass(frozen=True, slots=True)
class OperationResponseEnvelopeV1:
    operation_id: str
    response_contract: str
    request_id: str
    result_json: str

    def __post_init__(self) -> None:
        for name in (
            "operation_id",
            "response_contract",
            "request_id",
            "result_json",
        ):
            _required(getattr(self, name), name)
        from .serialization import deterministic_json, safe_json_loads

        result = safe_json_loads(self.result_json)
        if not isinstance(result, dict):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation response result must encode an object",
            )
        if self.result_json != deterministic_json(result):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation response result must use deterministic JSON",
            )


@dataclass(frozen=True, slots=True)
class OperationFailureEnvelopeV1:
    operation_id: str
    failure_contract: str
    request_id: str
    reason_code: ReasonCode
    detail: str

    def __post_init__(self) -> None:
        for name in (
            "operation_id",
            "failure_contract",
            "request_id",
            "detail",
        ):
            _required(getattr(self, name), name)
        _typed_enum(self.reason_code, ReasonCode, "reason_code")


@dataclass(frozen=True, slots=True)
class OperationContractV1:
    operation_id: str
    input_contract: str
    output_contract: str
    failure_contract: str
    runtime_effect_authorized: bool = False
    request_fields: tuple[ContractFieldV1, ...] = ()
    response_fields: tuple[ContractFieldV1, ...] = ()
    failure_reason_codes: tuple[ReasonCode, ...] = ()
    capability_class: OperationCapabilityClass = (
        OperationCapabilityClass.NONE_CONTRACT_ONLY
    )
    side_effect_class: OperationSideEffectClass = OperationSideEffectClass.NONE
    metadata: Mapping[str, str] = field(default_factory=immutable_mapping)

    def __post_init__(self) -> None:
        _exact_bool(
            self.runtime_effect_authorized, "runtime_effect_authorized"
        )
        if self.runtime_effect_authorized:
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "Tranche A operation contracts are data-only",
            )
        for name in (
            "operation_id",
            "input_contract",
            "output_contract",
            "failure_contract",
        ):
            _required(getattr(self, name), name)
        for name in ("request_fields", "response_fields"):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or any(not isinstance(value, ContractFieldV1) for value in values)
                or len({value.name for value in values}) != len(values)
            ):
                raise ContractValidationError(
                    ReasonCode.INCOMPLETE_CONTRACT,
                    f"{name} must be a nonempty unique typed schema",
                )
        if (
            not isinstance(self.failure_reason_codes, tuple)
            or not self.failure_reason_codes
            or any(
                not isinstance(reason, ReasonCode)
                for reason in self.failure_reason_codes
            )
            or len(set(self.failure_reason_codes))
            != len(self.failure_reason_codes)
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "failure_reason_codes must be a nonempty typed tuple",
            )
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
            self.capability_class
            is not OperationCapabilityClass.NONE_CONTRACT_ONLY
            or self.side_effect_class is not OperationSideEffectClass.NONE
        ):
            raise ContractValidationError(
                ReasonCode.CAPABILITY_DENIED,
                "Tranche A operation schemas cannot carry effect capabilities",
            )
        object.__setattr__(self, "metadata", immutable_mapping(self.metadata))

    def bind_request(
        self,
        *,
        request_id: str,
        contract_version: str,
        payload_json: str,
    ) -> OperationRequestEnvelopeV1:
        return OperationRequestEnvelopeV1(
            operation_id=self.operation_id,
            request_contract=self.input_contract,
            request_id=request_id,
            contract_version=contract_version,
            payload_json=payload_json,
        )

    def bind_response(
        self,
        request: OperationRequestEnvelopeV1,
        *,
        result_json: str,
    ) -> OperationResponseEnvelopeV1:
        if (
            not isinstance(request, OperationRequestEnvelopeV1)
            or request.operation_id != self.operation_id
            or request.request_contract != self.input_contract
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation response request lineage does not match the contract",
            )
        return OperationResponseEnvelopeV1(
            operation_id=self.operation_id,
            response_contract=self.output_contract,
            request_id=request.request_id,
            result_json=result_json,
        )

    def bind_failure(
        self,
        request: OperationRequestEnvelopeV1,
        *,
        reason_code: ReasonCode,
        detail: str,
    ) -> OperationFailureEnvelopeV1:
        if (
            not isinstance(request, OperationRequestEnvelopeV1)
            or request.operation_id != self.operation_id
            or request.request_contract != self.input_contract
            or reason_code not in self.failure_reason_codes
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation failure lineage or reason is not allowlisted",
            )
        return OperationFailureEnvelopeV1(
            operation_id=self.operation_id,
            failure_contract=self.failure_contract,
            request_id=request.request_id,
            reason_code=reason_code,
            detail=detail,
        )
