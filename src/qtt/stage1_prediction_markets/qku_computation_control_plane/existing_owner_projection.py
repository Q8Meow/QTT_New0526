"""Read-only ST12-G projections into the existing owner topology.

This module is deliberately a library boundary.  It creates no public QKU
operation, persistence owner, runtime service, economic value, or effect.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, fields
from datetime import datetime
from enum import StrEnum
import re
from types import MappingProxyType
from typing import Final

from .context import parse_utc
from .errors import (
    ComputationControlPlaneError,
    ContractValidationError,
    ReasonCode,
)
from .evidence import (
    ComputationEvidenceBundleV1,
    EvidenceBundleTerminalStateV1,
    FToDEvidenceReferenceQueryV1,
    FToGHandoffReferencesV1,
)
from .input_lock import ImmutableReplayPaperInputLockV1
from .models import (
    ComputationExecutionContextV1,
    NO_EFFECTS_V1,
    NoEffectFlagsV1,
    ST12FEvidenceReferenceV1,
    ST12FEvidenceStateV1,
)
from .protocols import (
    ComputationEvidenceServiceProtocolV1,
    PreloadedOwnerProjectionBundleV1,
)


ST12G_CONTRACT_VERSION_V2: Final = "2.0"
ST12G_RUNTIME_AUTHORITY: Final = "NONE_READ_ONLY_PROJECTION"
ST12G_WRITE_AUTHORITY: Final = "NONE"
ST12G_CURRENT_STATUS_CODE: Final = "ST12G_CURRENT_READ_ONLY"

_CANONICAL_G_RECEIPT = re.compile(
    r"^ST12F-RECEIPT::[A-Za-z0-9._:-]+::G_HANDOFF_REFERENCE$"
)
_CANONICAL_D_RECEIPT = re.compile(
    r"^ST12F-RECEIPT::[A-Za-z0-9._:-]+::D_EVIDENCE_REFERENCE$"
)
_CORE_ID = re.compile(r"^ST12G::CORE::[A-Za-z0-9._:-]+$")
_PROJECTION_ID = re.compile(
    r"^ST12G::PROJECTION::[A-Za-z0-9._:-]+::"
    r"(?:READINESS1|PRETRADE1|AGENT_ORCH1|SVC1)$"
)
_DASHBOARD_ID = re.compile(r"^ST12G::DASH1_UI1::[A-Za-z0-9._:-]+$")


def _contract_error(reason_code: ReasonCode, message: str) -> None:
    raise ContractValidationError(reason_code, message)


def _canonical_text(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        _contract_error(
            ReasonCode.INCOMPLETE_CONTRACT,
            f"{field_name} must be nonempty canonical text",
        )
    return value


def _current_source_text(value: object, field_name: str) -> str:
    text = _canonical_text(value, field_name)
    if text == "EXPLICIT_ABSENCE":
        _contract_error(
            ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
            f"{field_name} cannot be absent in a current projection",
        )
    return text


def _reference_tuple(
    value: object,
    field_name: str,
    *,
    required: bool,
) -> tuple[str, ...]:
    if (
        type(value) is not tuple
        or any(
            type(item) is not str
            or not item
            or item != item.strip()
            or item == "EXPLICIT_ABSENCE"
            for item in value
        )
        or len(value) != len(set(value))
    ):
        _contract_error(
            ReasonCode.SCHEMA_MISMATCH,
            f"{field_name} must be an ordered unique reference tuple",
        )
    if required and not value:
        _contract_error(
            ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
            f"{field_name} cannot be empty for current evidence",
        )
    return value


def _string_mapping(
    value: object,
    field_name: str,
    *,
    required: bool,
) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        _contract_error(
            ReasonCode.SCHEMA_MISMATCH,
            f"{field_name} must be a string mapping",
        )
    copied: dict[str, str] = {}
    for key, item in value.items():
        if (
            type(key) is not str
            or not key
            or key != key.strip()
            or type(item) is not str
            or not item
            or item != item.strip()
        ):
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                f"{field_name} must contain canonical string keys and values",
            )
        copied[key] = item
    if required and not copied:
        _contract_error(
            ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
            f"{field_name} cannot be empty for current evidence",
        )
    return MappingProxyType(copied)


def _require_exact_false(value: object, field_name: str) -> None:
    if type(value) is not bool or value:
        _contract_error(
            ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
            f"{field_name} must remain exact false",
        )


def _require_shared_no_effects(value: object) -> None:
    if value is not NO_EFFECTS_V1:
        _contract_error(
            ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
            "ST12-G contracts require the exact shared no-effect value",
        )


def _canonical_g_receipt_ref(handoff_id: str) -> str:
    return f"ST12F-RECEIPT::{handoff_id}::G_HANDOFF_REFERENCE"


def _canonical_d_receipt_ref(reference_id: str) -> str:
    return f"ST12F-RECEIPT::{reference_id}::D_EVIDENCE_REFERENCE"


def _canonical_lock_receipt_ref(input_lock_id: str) -> str:
    return f"ST12F-RECEIPT::{input_lock_id}::INPUT_LOCK"


def _input_lock_source_epoch_refs(
    input_lock: ImmutableReplayPaperInputLockV1,
) -> tuple[str, ...]:
    return tuple(
        f"{key}={input_lock.source_epochs[key]}"
        for key in sorted(input_lock.source_epochs)
    )


class ST12GProjectionResolutionStateV2(StrEnum):
    CURRENT_READ_ONLY = "CURRENT_READ_ONLY"
    UNAVAILABLE_STALE_NO_AUTHORITY = "UNAVAILABLE_STALE_NO_AUTHORITY"
    UNAVAILABLE_BLOCKED_NO_AUTHORITY = "UNAVAILABLE_BLOCKED_NO_AUTHORITY"


class ST12GReferenceCollectionStateV2(StrEnum):
    PRESENT_REFERENCES = "PRESENT_REFERENCES"
    EXPLICIT_EMPTY_NO_BLOCKER_IN_CLOSED_BUNDLE = (
        "EXPLICIT_EMPTY_NO_BLOCKER_IN_CLOSED_BUNDLE"
    )
    EXPLICIT_EMPTY_NO_APPLICABLE_REFERENCE_DECLARED_AT_F_CLOSURE = (
        "EXPLICIT_EMPTY_NO_APPLICABLE_REFERENCE_DECLARED_AT_F_CLOSURE"
    )
    EXPLICIT_EMPTY_NO_FAILURE_OR_NEGATIVE_EVIDENCE_IN_CLOSED_BUNDLE = (
        "EXPLICIT_EMPTY_NO_FAILURE_OR_NEGATIVE_EVIDENCE_IN_CLOSED_BUNDLE"
    )
    EXPLICIT_EMPTY_NONCURRENT_NO_SOURCE_LINEAGE = (
        "EXPLICIT_EMPTY_NONCURRENT_NO_SOURCE_LINEAGE"
    )


@dataclass(frozen=True, slots=True)
class ST12GReferenceCollectionV2:
    state: ST12GReferenceCollectionStateV2
    reference_values: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.state) is not ST12GReferenceCollectionStateV2:
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "reference collection state must be exact",
            )
        values = _reference_tuple(
            self.reference_values,
            "reference_values",
            required=self.state is ST12GReferenceCollectionStateV2.PRESENT_REFERENCES,
        )
        if (
            self.state is not ST12GReferenceCollectionStateV2.PRESENT_REFERENCES
            and values
        ):
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "an explicit-empty reference state cannot carry references",
            )


class ST12GVersionMappingStateV2(StrEnum):
    PRESENT_VERSION_MAPPING = "PRESENT_VERSION_MAPPING"
    EXPLICIT_EMPTY_NO_STACK_EXECUTED_FOR_COMPONENT_SCOPE = (
        "EXPLICIT_EMPTY_NO_STACK_EXECUTED_FOR_COMPONENT_SCOPE"
    )


@dataclass(frozen=True, slots=True)
class ST12GVersionMappingV2:
    state: ST12GVersionMappingStateV2
    version_mapping: Mapping[str, str]

    def __post_init__(self) -> None:
        if type(self.state) is not ST12GVersionMappingStateV2:
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "version mapping state must be exact",
            )
        mapping = _string_mapping(
            self.version_mapping,
            "version_mapping",
            required=self.state is ST12GVersionMappingStateV2.PRESENT_VERSION_MAPPING,
        )
        if (
            self.state
            is ST12GVersionMappingStateV2.EXPLICIT_EMPTY_NO_STACK_EXECUTED_FOR_COMPONENT_SCOPE
            and mapping
        ):
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "the explicit no-stack state cannot carry a version mapping",
            )
        object.__setattr__(self, "version_mapping", mapping)


class ST12GBlockerSetStateV2(StrEnum):
    EXPLICIT_EMPTY_NO_BLOCKERS = "EXPLICIT_EMPTY_NO_BLOCKERS"
    PRESENT_TYPED_BLOCKERS = "PRESENT_TYPED_BLOCKERS"


@dataclass(frozen=True, slots=True)
class ST12GBlockerStateV2:
    state: ST12GBlockerSetStateV2
    reason_codes: tuple[ReasonCode, ...]

    def __post_init__(self) -> None:
        if type(self.state) is not ST12GBlockerSetStateV2:
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "blocker state must be exact",
            )
        if (
            type(self.reason_codes) is not tuple
            or any(type(code) is not ReasonCode for code in self.reason_codes)
            or len(self.reason_codes) != len(set(self.reason_codes))
        ):
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "blocker reason codes must be an ordered unique ReasonCode tuple",
            )
        if self.state is ST12GBlockerSetStateV2.PRESENT_TYPED_BLOCKERS:
            if not self.reason_codes:
                _contract_error(
                    ReasonCode.SCHEMA_MISMATCH,
                    "present blockers require at least one reason code",
                )
        elif self.reason_codes:
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "the explicit no-blocker state cannot carry reason codes",
            )


@dataclass(frozen=True, slots=True)
class ST12GProjectionRequestV2:
    request_id: str
    context: ComputationExecutionContextV1
    source_handoff_receipt_ref: str
    causation_id: str
    correlation_id: str

    def __post_init__(self) -> None:
        _canonical_text(self.request_id, "request_id")
        if type(self.context) is not ComputationExecutionContextV1:
            _contract_error(
                ReasonCode.INPUT_OWNER_MISMATCH,
                "context must be the exact ComputationExecutionContextV1",
            )
        receipt_ref = _canonical_text(
            self.source_handoff_receipt_ref,
            "source_handoff_receipt_ref",
        )
        if _CANONICAL_G_RECEIPT.fullmatch(receipt_ref) is None:
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "source_handoff_receipt_ref must be a full canonical G receipt reference",
            )
        _canonical_text(self.causation_id, "causation_id")
        _canonical_text(self.correlation_id, "correlation_id")
        if self.causation_id == self.correlation_id:
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "causation and correlation identities must remain distinct",
            )


@dataclass(frozen=True, slots=True)
class ST12GProjectionCoreV2:
    core_id: str
    contract_version: str
    evaluation_context_id: str
    evaluated_at: datetime
    source_handoff_receipt_ref: str
    current_d_reference_receipt_ref: str
    current_d_reference_id: str
    handoff_id: str
    input_lock_id: str
    source_epoch_refs: tuple[str, ...]
    observed_at: datetime
    valid_until: datetime
    terminal_state: str
    evidence_bundle_ref: str
    evidence_id: str
    evidence_bundle_version: str
    component_or_template_ref: str
    independent_review_state: str
    actual_executed_component_versions: Mapping[str, str]
    actual_executed_stack_version_state: ST12GVersionMappingV2
    replay_result_ref: str
    paper_result_ref: str
    divergence_assessment_ref: str
    lane_execution_receipt_refs: tuple[str, ...]
    failure_and_negative_evidence_state: ST12GReferenceCollectionV2
    source_and_provenance_refs: tuple[str, ...]
    bundle_blocker_state: ST12GBlockerStateV2
    no_trade_blocker_reference_state: ST12GReferenceCollectionV2
    champion_challenger_reference_state: ST12GReferenceCollectionV2
    portfolio_utility_reference_state: ST12GReferenceCollectionV2
    quantum_classical_comparison_receipt_ref: str
    runtime_authority: str
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        if len(fields(self)) != 33:
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "ST12-G shared core must contain exactly 33 fields",
            )
        _canonical_text(self.core_id, "core_id")
        if (
            _CORE_ID.fullmatch(self.core_id) is None
            or self.core_id != f"ST12G::CORE::{self.handoff_id}"
        ):
            _contract_error(ReasonCode.SCHEMA_MISMATCH, "core identity differs")
        if self.contract_version != ST12G_CONTRACT_VERSION_V2:
            _contract_error(ReasonCode.SCHEMA_MISMATCH, "core version differs")
        for name in (
            "evaluation_context_id",
            "current_d_reference_id",
            "handoff_id",
            "input_lock_id",
            "terminal_state",
            "evidence_bundle_ref",
            "evidence_id",
            "evidence_bundle_version",
            "component_or_template_ref",
            "independent_review_state",
            "replay_result_ref",
            "paper_result_ref",
            "divergence_assessment_ref",
            "quantum_classical_comparison_receipt_ref",
        ):
            _current_source_text(getattr(self, name), name)
        if (
            _CANONICAL_G_RECEIPT.fullmatch(self.source_handoff_receipt_ref) is None
            or self.source_handoff_receipt_ref
            != _canonical_g_receipt_ref(self.handoff_id)
        ):
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "core G handoff receipt reference differs",
            )
        if (
            _CANONICAL_D_RECEIPT.fullmatch(self.current_d_reference_receipt_ref)
            is None
            or self.current_d_reference_receipt_ref
            != _canonical_d_receipt_ref(self.current_d_reference_id)
        ):
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "core D reference receipt differs",
            )
        evaluated = parse_utc(self.evaluated_at, field_name="evaluated_at")
        observed = parse_utc(self.observed_at, field_name="observed_at")
        valid_until = parse_utc(self.valid_until, field_name="valid_until")
        object.__setattr__(self, "evaluated_at", evaluated)
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "valid_until", valid_until)
        if not observed <= evaluated <= valid_until:
            _contract_error(
                ReasonCode.ST12F_BUNDLE_STALE,
                "core evaluation is outside trusted F-to-G validity",
            )
        if (
            self.terminal_state
            != EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED.value
            or self.independent_review_state != self.terminal_state
        ):
            _contract_error(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "current core requires closed independent validation",
            )
        _reference_tuple(self.source_epoch_refs, "source_epoch_refs", required=True)
        _reference_tuple(
            self.lane_execution_receipt_refs,
            "lane_execution_receipt_refs",
            required=True,
        )
        _reference_tuple(
            self.source_and_provenance_refs,
            "source_and_provenance_refs",
            required=True,
        )
        component_versions = _string_mapping(
            self.actual_executed_component_versions,
            "actual_executed_component_versions",
            required=True,
        )
        object.__setattr__(
            self,
            "actual_executed_component_versions",
            component_versions,
        )
        if type(self.actual_executed_stack_version_state) is not ST12GVersionMappingV2:
            _contract_error(ReasonCode.SCHEMA_MISMATCH, "stack state must be typed")
        for name in (
            "failure_and_negative_evidence_state",
            "no_trade_blocker_reference_state",
            "champion_challenger_reference_state",
            "portfolio_utility_reference_state",
        ):
            if type(getattr(self, name)) is not ST12GReferenceCollectionV2:
                _contract_error(
                    ReasonCode.SCHEMA_MISMATCH,
                    f"{name} must be a typed reference collection",
                )
        if (
            type(self.bundle_blocker_state) is not ST12GBlockerStateV2
            or self.bundle_blocker_state.state
            is not ST12GBlockerSetStateV2.EXPLICIT_EMPTY_NO_BLOCKERS
        ):
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "a current core cannot carry present blockers",
            )
        if self.runtime_authority != ST12G_RUNTIME_AUTHORITY:
            _contract_error(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "core runtime authority must remain read-only",
            )
        _require_shared_no_effects(self.no_effect_flags)


def _validate_owner_wrapper(
    *,
    projection_id: str,
    projection_contract_version: str,
    consumer_id: str,
    expected_consumer_id: str,
    core: object,
    runtime_effect_allowed: object,
    write_authority: str,
) -> ST12GProjectionCoreV2:
    if type(core) is not ST12GProjectionCoreV2:
        _contract_error(
            ReasonCode.SCHEMA_MISMATCH,
            "direct owner projection requires the exact shared core",
        )
    if (
        _PROJECTION_ID.fullmatch(projection_id) is None
        or projection_id
        != f"ST12G::PROJECTION::{core.handoff_id}::{expected_consumer_id}"
        or consumer_id != expected_consumer_id
        or projection_contract_version != ST12G_CONTRACT_VERSION_V2
    ):
        _contract_error(
            ReasonCode.OWNER_DATA_MISSING,
            "direct owner projection identity or consumer differs",
        )
    _require_exact_false(runtime_effect_allowed, "runtime_effect_allowed")
    if write_authority != ST12G_WRITE_AUTHORITY:
        _contract_error(
            ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
            "owner projection write authority must remain NONE",
        )
    return core


@dataclass(frozen=True, slots=True)
class ST12GReadinessEvidenceProjectionV2:
    projection_id: str
    projection_contract_version: str
    consumer_id: str
    core: ST12GProjectionCoreV2
    evidence_readiness_state: str
    runtime_instance_state: str
    activation_authority: str
    runtime_effect_allowed: bool = False
    write_authority: str = ST12G_WRITE_AUTHORITY

    def __post_init__(self) -> None:
        _validate_owner_wrapper(
            projection_id=self.projection_id,
            projection_contract_version=self.projection_contract_version,
            consumer_id=self.consumer_id,
            expected_consumer_id="READINESS1",
            core=self.core,
            runtime_effect_allowed=self.runtime_effect_allowed,
            write_authority=self.write_authority,
        )
        if (
            self.evidence_readiness_state
            != "EVIDENCE_REFERENCE_AVAILABLE_FOR_READ_ONLY_REVIEW"
            or self.runtime_instance_state
            != "CONTRACT_DEFINED_RUNTIME_INSTANCE_DERIVED_ONLY_FROM_DURABLE_F_CUSTODY"
            or self.activation_authority != "NONE"
        ):
            _contract_error(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "READINESS1 overlay differs from the no-authority contract",
            )


@dataclass(frozen=True, slots=True)
class ST12GPretradeEvidenceProjectionV2:
    projection_id: str
    projection_contract_version: str
    consumer_id: str
    core: ST12GProjectionCoreV2
    pretrade_evidence_state: str
    no_trade_route_state: str
    submit_authority_created: bool
    order_authority_created: bool
    profit_claim_created: bool
    runtime_effect_allowed: bool = False
    write_authority: str = ST12G_WRITE_AUTHORITY

    def __post_init__(self) -> None:
        core = _validate_owner_wrapper(
            projection_id=self.projection_id,
            projection_contract_version=self.projection_contract_version,
            consumer_id=self.consumer_id,
            expected_consumer_id="PRETRADE1",
            core=self.core,
            runtime_effect_allowed=self.runtime_effect_allowed,
            write_authority=self.write_authority,
        )
        expected_route = (
            "NO_TRADE_BLOCKERS_PRESENT_READ_ONLY"
            if core.no_trade_blocker_reference_state.state
            is ST12GReferenceCollectionStateV2.PRESENT_REFERENCES
            else "EXPLICIT_EMPTY_NO_TRADE_BLOCKERS_IN_CLOSED_BUNDLE"
        )
        if (
            self.pretrade_evidence_state
            != "EVIDENCE_REFERENCE_AVAILABLE_FOR_READ_ONLY_PRETRADE_REVIEW"
            or self.no_trade_route_state != expected_route
        ):
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "PRETRADE1 evidence or no-trade route state differs",
            )
        for name in (
            "submit_authority_created",
            "order_authority_created",
            "profit_claim_created",
        ):
            _require_exact_false(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class ST12GAgentEvidenceHandoffV2:
    projection_id: str
    projection_contract_version: str
    consumer_id: str
    core: ST12GProjectionCoreV2
    task_class: str
    allowed_operation: str
    self_promotion_allowed: bool
    historical_rewrite_allowed: bool
    owner_review_route: str
    runtime_effect_allowed: bool = False
    write_authority: str = ST12G_WRITE_AUTHORITY

    def __post_init__(self) -> None:
        _validate_owner_wrapper(
            projection_id=self.projection_id,
            projection_contract_version=self.projection_contract_version,
            consumer_id=self.consumer_id,
            expected_consumer_id="AGENT_ORCH1",
            core=self.core,
            runtime_effect_allowed=self.runtime_effect_allowed,
            write_authority=self.write_authority,
        )
        if (
            self.task_class != "READ_ONLY_EVIDENCE_REVIEW_HANDOFF"
            or self.allowed_operation
            != "REVIEW_PROJECTED_EVIDENCE_AND_ROUTE_TYPED_RESPONSE"
            or self.owner_review_route
            != "OWNER_REVIEW_REQUIRED_FOR_ANY_LATER_AUTHORITY"
        ):
            _contract_error(
                ReasonCode.OPERATION_NOT_ALLOWED,
                "AGENT-ORCH1 overlay differs from the read-only review contract",
            )
        _require_exact_false(self.self_promotion_allowed, "self_promotion_allowed")
        _require_exact_false(
            self.historical_rewrite_allowed,
            "historical_rewrite_allowed",
        )


@dataclass(frozen=True, slots=True)
class ST12GServiceEvidenceViewV2:
    projection_id: str
    projection_contract_version: str
    consumer_id: str
    core: ST12GProjectionCoreV2
    read_model_class: str
    stale_state: str
    action_eligibility_state: str
    fake_receipt_allowed: bool
    runtime_execution_allowed: bool
    runtime_effect_allowed: bool = False
    write_authority: str = ST12G_WRITE_AUTHORITY

    def __post_init__(self) -> None:
        _validate_owner_wrapper(
            projection_id=self.projection_id,
            projection_contract_version=self.projection_contract_version,
            consumer_id=self.consumer_id,
            expected_consumer_id="SVC1",
            core=self.core,
            runtime_effect_allowed=self.runtime_effect_allowed,
            write_authority=self.write_authority,
        )
        if (
            self.read_model_class != "OWNER_AND_AGENT_READ_ONLY_EVIDENCE_VIEW"
            or self.stale_state
            != "CURRENT_WITHIN_TRUSTED_F_TO_G_AND_D_REFERENCE_VALIDITY"
            or self.action_eligibility_state != "REVIEW_REQUESTS_ONLY"
        ):
            _contract_error(
                ReasonCode.OPERATION_NOT_ALLOWED,
                "SVC1 overlay differs from the read-only view contract",
            )
        _require_exact_false(self.fake_receipt_allowed, "fake_receipt_allowed")
        _require_exact_false(
            self.runtime_execution_allowed,
            "runtime_execution_allowed",
        )


@dataclass(frozen=True, slots=True)
class ST12GProjectionBundleV2:
    bundle_id: str
    contract_version: str
    core: ST12GProjectionCoreV2
    readiness: ST12GReadinessEvidenceProjectionV2
    pretrade: ST12GPretradeEvidenceProjectionV2
    agent_orch: ST12GAgentEvidenceHandoffV2
    svc: ST12GServiceEvidenceViewV2
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        if type(self.core) is not ST12GProjectionCoreV2:
            _contract_error(ReasonCode.SCHEMA_MISMATCH, "bundle core must be exact")
        expected = (
            (self.readiness, ST12GReadinessEvidenceProjectionV2, "READINESS1"),
            (self.pretrade, ST12GPretradeEvidenceProjectionV2, "PRETRADE1"),
            (self.agent_orch, ST12GAgentEvidenceHandoffV2, "AGENT_ORCH1"),
            (self.svc, ST12GServiceEvidenceViewV2, "SVC1"),
        )
        if (
            self.bundle_id != f"ST12G::BUNDLE::{self.core.handoff_id}"
            or self.contract_version != ST12G_CONTRACT_VERSION_V2
            or any(
                type(projection) is not projection_type
                or projection.consumer_id != consumer_id
                or projection.core is not self.core
                for projection, projection_type, consumer_id in expected
            )
        ):
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "central bundle must contain all four exact projections sharing one core",
            )
        _require_shared_no_effects(self.no_effect_flags)


_STALE_REASON_CODES: Final = frozenset(
    {
        ReasonCode.STALE_CONTEXT,
        ReasonCode.ST12F_BUNDLE_STALE,
    }
)

_BLOCKED_REASON_CODES: Final = frozenset(
    {
        ReasonCode.CAPITAL_EFFECT_FORBIDDEN,
        ReasonCode.DIRECT_PROVIDER_FORBIDDEN,
        ReasonCode.EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH,
        ReasonCode.FORMULA_EXECUTION_REJECTED,
        ReasonCode.IDEMPOTENCY_CONFLICT,
        ReasonCode.INCOMPLETE_CONTRACT,
        ReasonCode.INPUT_OWNER_MISMATCH,
        ReasonCode.INPUT_SCOPE_MISMATCH,
        ReasonCode.LLM_INFERENCE_FORBIDDEN,
        ReasonCode.MODE_ACTIVATION_FORBIDDEN,
        ReasonCode.OPERATION_NOT_ALLOWED,
        ReasonCode.ORDER_RELEASE_FORBIDDEN,
        ReasonCode.OWNER_DATA_MISSING,
        ReasonCode.PARAMETER_NOT_EDITABLE,
        ReasonCode.PATH_UNSAFE,
        ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID,
        ReasonCode.PRIVATE_STATE_FORBIDDEN,
        ReasonCode.QPU_EFFECT_FORBIDDEN,
        ReasonCode.REPLAY_PAPER_EFFECT_FORBIDDEN,
        ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
        ReasonCode.SCHEMA_MISMATCH,
        ReasonCode.SOURCE_CONFLICT,
        ReasonCode.SOURCE_EPOCH_MISSING,
        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
        ReasonCode.ST12F_FIXTURE_NOT_EVIDENCE,
        ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
        ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
    }
)


@dataclass(frozen=True, slots=True)
class ST12GProjectionAbsenceV2:
    absence_id: str
    evaluation_context_id: str
    evaluated_at: datetime
    state: ST12GProjectionResolutionStateV2
    reason_codes: tuple[ReasonCode, ...]
    source_handoff_receipt_ref_or_explicit_absence: str
    runtime_authority: str = ST12G_RUNTIME_AUTHORITY
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        _canonical_text(self.absence_id, "absence_id")
        _canonical_text(self.evaluation_context_id, "evaluation_context_id")
        object.__setattr__(
            self,
            "evaluated_at",
            parse_utc(self.evaluated_at, field_name="evaluated_at"),
        )
        if self.state not in {
            ST12GProjectionResolutionStateV2.UNAVAILABLE_STALE_NO_AUTHORITY,
            ST12GProjectionResolutionStateV2.UNAVAILABLE_BLOCKED_NO_AUTHORITY,
        } or type(self.state) is not ST12GProjectionResolutionStateV2:
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "absence must carry one exact noncurrent state",
            )
        if (
            type(self.reason_codes) is not tuple
            or not self.reason_codes
            or any(type(code) is not ReasonCode for code in self.reason_codes)
            or len(self.reason_codes) != len(set(self.reason_codes))
        ):
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "absence reasons must be an ordered unique nonempty ReasonCode tuple",
            )
        expected_reasons = (
            _STALE_REASON_CODES
            if self.state
            is ST12GProjectionResolutionStateV2.UNAVAILABLE_STALE_NO_AUTHORITY
            else _BLOCKED_REASON_CODES
        )
        if any(code not in expected_reasons for code in self.reason_codes):
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "absence state and reason-code class differ",
            )
        _canonical_text(
            self.source_handoff_receipt_ref_or_explicit_absence,
            "source_handoff_receipt_ref_or_explicit_absence",
        )
        if self.runtime_authority != ST12G_RUNTIME_AUTHORITY:
            _contract_error(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "absence cannot create runtime authority",
            )
        _require_shared_no_effects(self.no_effect_flags)


class _FrozenContractMapping(Mapping[str, object]):
    __slots__ = ("_payload",)

    def __init__(self, payload: Mapping[str, object]) -> None:
        object.__setattr__(self, "_payload", MappingProxyType(dict(payload)))

    def __getitem__(self, key: str) -> object:
        return self._payload[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._payload)

    def __len__(self) -> int:
        return len(self._payload)

    def __getattr__(self, name: str) -> object:
        try:
            return self._payload[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(f"{type(self).__name__} is immutable")

    def __repr__(self) -> str:
        return f"{type(self).__name__}({dict(self._payload)!r})"

    def __eq__(self, other: object) -> bool:
        return type(other) is type(self) and self._payload == other._payload


class ST12GProjectionResolutionV2(_FrozenContractMapping):
    """Exact current-or-absence union without serialized null branch fields."""

    __slots__ = ()

    def __init__(
        self,
        *,
        resolution_id: str,
        request_id: str,
        context_id: str,
        evaluated_at: datetime,
        resolution_state: ST12GProjectionResolutionStateV2,
        payload: ST12GProjectionBundleV2 | ST12GProjectionAbsenceV2,
    ) -> None:
        _canonical_text(resolution_id, "resolution_id")
        _canonical_text(request_id, "request_id")
        _canonical_text(context_id, "context_id")
        evaluated = parse_utc(evaluated_at, field_name="evaluated_at")
        if type(resolution_state) is not ST12GProjectionResolutionStateV2:
            _contract_error(ReasonCode.SCHEMA_MISMATCH, "resolution state must be exact")
        common: dict[str, object] = {
            "resolution_id": resolution_id,
            "contract_version": ST12G_CONTRACT_VERSION_V2,
            "request_id": request_id,
            "context_id": context_id,
            "evaluated_at": evaluated,
            "resolution_state": resolution_state,
        }
        if resolution_state is ST12GProjectionResolutionStateV2.CURRENT_READ_ONLY:
            if type(payload) is not ST12GProjectionBundleV2:
                _contract_error(
                    ReasonCode.SCHEMA_MISMATCH,
                    "current resolution requires the complete projection bundle",
                )
            common["status_code"] = ST12G_CURRENT_STATUS_CODE
            common["projection_bundle"] = payload
        else:
            if (
                type(payload) is not ST12GProjectionAbsenceV2
                or payload.state is not resolution_state
                or payload.evaluation_context_id != context_id
                or payload.evaluated_at != evaluated
            ):
                _contract_error(
                    ReasonCode.SCHEMA_MISMATCH,
                    "noncurrent resolution requires its exact matching absence",
                )
            common["absence"] = payload
        common["no_effect_flags"] = NO_EFFECTS_V1
        super().__init__(common)

    @classmethod
    def current(
        cls,
        *,
        resolution_id: str,
        request_id: str,
        context_id: str,
        evaluated_at: datetime,
        projection_bundle: ST12GProjectionBundleV2,
    ) -> "ST12GProjectionResolutionV2":
        return cls(
            resolution_id=resolution_id,
            request_id=request_id,
            context_id=context_id,
            evaluated_at=evaluated_at,
            resolution_state=ST12GProjectionResolutionStateV2.CURRENT_READ_ONLY,
            payload=projection_bundle,
        )

    @classmethod
    def unavailable(
        cls,
        *,
        resolution_id: str,
        request_id: str,
        context_id: str,
        evaluated_at: datetime,
        absence: ST12GProjectionAbsenceV2,
    ) -> "ST12GProjectionResolutionV2":
        return cls(
            resolution_id=resolution_id,
            request_id=request_id,
            context_id=context_id,
            evaluated_at=evaluated_at,
            resolution_state=absence.state,
            payload=absence,
        )


_OWNER_PROJECTION_TYPES: Final = MappingProxyType(
    {
        "READINESS1": (
            "ST12GReadinessEvidenceProjectionV2",
            ST12GReadinessEvidenceProjectionV2,
        ),
        "PRETRADE1": (
            "ST12GPretradeEvidenceProjectionV2",
            ST12GPretradeEvidenceProjectionV2,
        ),
        "AGENT_ORCH1": (
            "ST12GAgentEvidenceHandoffV2",
            ST12GAgentEvidenceHandoffV2,
        ),
        "SVC1": ("ST12GServiceEvidenceViewV2", ST12GServiceEvidenceViewV2),
    }
)


class ST12GOwnerProjectionResolutionV2(_FrozenContractMapping):
    """One direct owner's exact projection or the unchanged central absence."""

    __slots__ = ()

    def __init__(
        self,
        *,
        consumer_id: str,
        source_request_id: str,
        resolution_state: ST12GProjectionResolutionStateV2,
        payload: (
            ST12GReadinessEvidenceProjectionV2
            | ST12GPretradeEvidenceProjectionV2
            | ST12GAgentEvidenceHandoffV2
            | ST12GServiceEvidenceViewV2
            | ST12GProjectionAbsenceV2
        ),
    ) -> None:
        owner_contract = _OWNER_PROJECTION_TYPES.get(consumer_id)
        if owner_contract is None:
            _contract_error(
                ReasonCode.OWNER_DATA_MISSING,
                "owner projection resolution consumer is not in the direct topology",
            )
        _canonical_text(source_request_id, "source_request_id")
        if type(resolution_state) is not ST12GProjectionResolutionStateV2:
            _contract_error(ReasonCode.SCHEMA_MISMATCH, "owner state must be exact")
        consumer_contract_id, projection_type = owner_contract
        common: dict[str, object] = {
            "consumer_id": consumer_id,
            "consumer_contract_id": consumer_contract_id,
            "source_request_id": source_request_id,
            "resolution_state": resolution_state,
        }
        if resolution_state is ST12GProjectionResolutionStateV2.CURRENT_READ_ONLY:
            if type(payload) is not projection_type or payload.consumer_id != consumer_id:
                _contract_error(
                    ReasonCode.INPUT_OWNER_MISMATCH,
                    "owner resolution projection type or consumer differs",
                )
            common["projection"] = payload
        else:
            if type(payload) is not ST12GProjectionAbsenceV2 or payload.state is not resolution_state:
                _contract_error(
                    ReasonCode.SCHEMA_MISMATCH,
                    "owner noncurrent state must preserve the exact central absence",
                )
            common["absence"] = payload
        common["no_effect_flags"] = NO_EFFECTS_V1
        super().__init__(common)


@dataclass(frozen=True, slots=True)
class ST12GOwnerDashboardEvidenceViewV2:
    projection_id: str
    contract_version: str
    consumer_id: str
    source_svc_resolution_state: ST12GProjectionResolutionStateV2
    source_svc_projection_id_or_explicit_absence: str
    panel_id: str
    availability_badge: str
    stale_banner_state: str
    owner_safe_next_action: str
    direct_f_binding_allowed: bool
    live_control_authority: str
    source_lineage_state: ST12GReferenceCollectionV2
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1
    runtime_effect_allowed: bool = False
    write_authority: str = ST12G_WRITE_AUTHORITY

    def __post_init__(self) -> None:
        if _DASHBOARD_ID.fullmatch(self.projection_id) is None:
            _contract_error(ReasonCode.SCHEMA_MISMATCH, "dashboard identity differs")
        if (
            self.contract_version != ST12G_CONTRACT_VERSION_V2
            or self.consumer_id != "DASH1_UI1"
            or type(self.source_svc_resolution_state)
            is not ST12GProjectionResolutionStateV2
            or self.panel_id != "QKU_COMPUTATION_CONTROL_PLANE"
            or self.owner_safe_next_action != "REVIEW_PROJECTED_EVIDENCE_ONLY"
        ):
            _contract_error(
                ReasonCode.INPUT_OWNER_MISMATCH,
                "dashboard contract or SVC1-derived route differs",
            )
        _canonical_text(
            self.source_svc_projection_id_or_explicit_absence,
            "source_svc_projection_id_or_explicit_absence",
        )
        if type(self.source_lineage_state) is not ST12GReferenceCollectionV2:
            _contract_error(ReasonCode.SCHEMA_MISMATCH, "dashboard lineage must be typed")
        if self.source_svc_resolution_state is ST12GProjectionResolutionStateV2.CURRENT_READ_ONLY:
            if (
                not self.source_svc_projection_id_or_explicit_absence.endswith("::SVC1")
                or self.availability_badge != "CURRENT_CLOSED_EVIDENCE_AVAILABLE"
                or self.stale_banner_state != "CURRENT"
                or self.source_lineage_state.state
                is not ST12GReferenceCollectionStateV2.PRESENT_REFERENCES
            ):
                _contract_error(
                    ReasonCode.SCHEMA_MISMATCH,
                    "current dashboard state must preserve current SVC1 lineage",
                )
        else:
            suffix = (
                "STALE_NO_AUTHORITY"
                if self.source_svc_resolution_state
                is ST12GProjectionResolutionStateV2.UNAVAILABLE_STALE_NO_AUTHORITY
                else "BLOCKED_NO_AUTHORITY"
            )
            if (
                self.source_svc_projection_id_or_explicit_absence != "EXPLICIT_ABSENCE"
                or self.availability_badge != suffix
                or self.stale_banner_state != suffix
                or self.source_lineage_state.state
                is not ST12GReferenceCollectionStateV2.EXPLICIT_EMPTY_NONCURRENT_NO_SOURCE_LINEAGE
            ):
                _contract_error(
                    ReasonCode.SCHEMA_MISMATCH,
                    "noncurrent dashboard state must preserve SVC1 absence without fallback",
                )
        _require_exact_false(self.direct_f_binding_allowed, "direct_f_binding_allowed")
        _require_exact_false(self.runtime_effect_allowed, "runtime_effect_allowed")
        if self.live_control_authority != "NONE" or self.write_authority != "NONE":
            _contract_error(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "dashboard cannot create live or write authority",
            )
        _require_shared_no_effects(self.no_effect_flags)


class ExistingOwnerProjectionCompilerV2:
    """Pure stateless compiler from trusted F custody to four owner views."""

    __slots__ = ()

    def compile_current(
        self,
        context: ComputationExecutionContextV1,
        input_lock: ImmutableReplayPaperInputLockV1,
        handoff: FToGHandoffReferencesV1,
        bundle: ComputationEvidenceBundleV1,
        current_d_reference: ST12FEvidenceReferenceV1,
        owner_views: PreloadedOwnerProjectionBundleV1,
    ) -> ST12GProjectionBundleV2:
        if type(context) is not ComputationExecutionContextV1:
            _contract_error(ReasonCode.INPUT_OWNER_MISMATCH, "context type differs")
        if type(input_lock) is not ImmutableReplayPaperInputLockV1:
            _contract_error(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "input lock type differs")
        if type(handoff) is not FToGHandoffReferencesV1:
            _contract_error(ReasonCode.SCHEMA_MISMATCH, "G handoff type differs")
        if type(bundle) is not ComputationEvidenceBundleV1:
            _contract_error(ReasonCode.SCHEMA_MISMATCH, "parent bundle type differs")
        if type(current_d_reference) is not ST12FEvidenceReferenceV1:
            _contract_error(
                ReasonCode.EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH,
                "current D evidence-reference type differs",
            )
        if type(owner_views) is not PreloadedOwnerProjectionBundleV1:
            _contract_error(ReasonCode.OWNER_DATA_MISSING, "owner view bundle type differs")

        context.assert_fresh()
        self._validate_context_and_lock(context, input_lock, handoff)
        self._validate_current_custody(
            context,
            input_lock,
            handoff,
            bundle,
            current_d_reference,
        )

        stack_versions = _string_mapping(
            bundle.actual_executed_stack_versions,
            "actual_executed_stack_versions",
            required=False,
        )
        stack_state = ST12GVersionMappingV2(
            state=(
                ST12GVersionMappingStateV2.PRESENT_VERSION_MAPPING
                if stack_versions
                else ST12GVersionMappingStateV2.EXPLICIT_EMPTY_NO_STACK_EXECUTED_FOR_COMPONENT_SCOPE
            ),
            version_mapping=stack_versions,
        )

        def reference_state(
            values: tuple[str, ...],
            empty_state: ST12GReferenceCollectionStateV2,
        ) -> ST12GReferenceCollectionV2:
            return ST12GReferenceCollectionV2(
                state=(
                    ST12GReferenceCollectionStateV2.PRESENT_REFERENCES
                    if values
                    else empty_state
                ),
                reference_values=values,
            )

        core = ST12GProjectionCoreV2(
            core_id=f"ST12G::CORE::{handoff.handoff_id}",
            contract_version=ST12G_CONTRACT_VERSION_V2,
            evaluation_context_id=context.context_id,
            evaluated_at=context.as_of,
            source_handoff_receipt_ref=_canonical_g_receipt_ref(handoff.handoff_id),
            current_d_reference_receipt_ref=_canonical_d_receipt_ref(
                current_d_reference.reference_id
            ),
            current_d_reference_id=current_d_reference.reference_id,
            handoff_id=handoff.handoff_id,
            input_lock_id=handoff.input_lock_id,
            source_epoch_refs=handoff.source_epoch_refs,
            observed_at=handoff.observed_at,
            valid_until=handoff.valid_until,
            terminal_state=handoff.terminal_state,
            evidence_bundle_ref=handoff.evidence_bundle_ref,
            evidence_id=bundle.evidence_id,
            evidence_bundle_version=bundle.evidence_bundle_version,
            component_or_template_ref=bundle.component_or_template_ref,
            independent_review_state=bundle.independent_review_state,
            actual_executed_component_versions=_string_mapping(
                bundle.actual_executed_component_versions,
                "actual_executed_component_versions",
                required=True,
            ),
            actual_executed_stack_version_state=stack_state,
            replay_result_ref=bundle.replay_result_ref,
            paper_result_ref=bundle.paper_result_ref,
            divergence_assessment_ref=bundle.divergence_assessment_ref,
            lane_execution_receipt_refs=bundle.lane_execution_receipt_refs,
            failure_and_negative_evidence_state=reference_state(
                bundle.failure_and_negative_evidence_states,
                ST12GReferenceCollectionStateV2.EXPLICIT_EMPTY_NO_FAILURE_OR_NEGATIVE_EVIDENCE_IN_CLOSED_BUNDLE,
            ),
            source_and_provenance_refs=bundle.source_and_provenance_refs,
            bundle_blocker_state=ST12GBlockerStateV2(
                state=ST12GBlockerSetStateV2.EXPLICIT_EMPTY_NO_BLOCKERS,
                reason_codes=(),
            ),
            no_trade_blocker_reference_state=reference_state(
                handoff.no_trade_blocker_refs,
                ST12GReferenceCollectionStateV2.EXPLICIT_EMPTY_NO_BLOCKER_IN_CLOSED_BUNDLE,
            ),
            champion_challenger_reference_state=reference_state(
                handoff.champion_challenger_evidence_refs,
                ST12GReferenceCollectionStateV2.EXPLICIT_EMPTY_NO_APPLICABLE_REFERENCE_DECLARED_AT_F_CLOSURE,
            ),
            portfolio_utility_reference_state=reference_state(
                handoff.portfolio_utility_refs,
                ST12GReferenceCollectionStateV2.EXPLICIT_EMPTY_NO_APPLICABLE_REFERENCE_DECLARED_AT_F_CLOSURE,
            ),
            quantum_classical_comparison_receipt_ref=(
                handoff.quantum_classical_comparison_receipt_ref
            ),
            runtime_authority=ST12G_RUNTIME_AUTHORITY,
        )

        readiness = ST12GReadinessEvidenceProjectionV2(
            projection_id=f"ST12G::PROJECTION::{handoff.handoff_id}::READINESS1",
            projection_contract_version=ST12G_CONTRACT_VERSION_V2,
            consumer_id="READINESS1",
            core=core,
            evidence_readiness_state="EVIDENCE_REFERENCE_AVAILABLE_FOR_READ_ONLY_REVIEW",
            runtime_instance_state="CONTRACT_DEFINED_RUNTIME_INSTANCE_DERIVED_ONLY_FROM_DURABLE_F_CUSTODY",
            activation_authority="NONE",
        )
        pretrade = ST12GPretradeEvidenceProjectionV2(
            projection_id=f"ST12G::PROJECTION::{handoff.handoff_id}::PRETRADE1",
            projection_contract_version=ST12G_CONTRACT_VERSION_V2,
            consumer_id="PRETRADE1",
            core=core,
            pretrade_evidence_state="EVIDENCE_REFERENCE_AVAILABLE_FOR_READ_ONLY_PRETRADE_REVIEW",
            no_trade_route_state=(
                "NO_TRADE_BLOCKERS_PRESENT_READ_ONLY"
                if handoff.no_trade_blocker_refs
                else "EXPLICIT_EMPTY_NO_TRADE_BLOCKERS_IN_CLOSED_BUNDLE"
            ),
            submit_authority_created=False,
            order_authority_created=False,
            profit_claim_created=False,
        )
        agent_orch = ST12GAgentEvidenceHandoffV2(
            projection_id=f"ST12G::PROJECTION::{handoff.handoff_id}::AGENT_ORCH1",
            projection_contract_version=ST12G_CONTRACT_VERSION_V2,
            consumer_id="AGENT_ORCH1",
            core=core,
            task_class="READ_ONLY_EVIDENCE_REVIEW_HANDOFF",
            allowed_operation="REVIEW_PROJECTED_EVIDENCE_AND_ROUTE_TYPED_RESPONSE",
            self_promotion_allowed=False,
            historical_rewrite_allowed=False,
            owner_review_route="OWNER_REVIEW_REQUIRED_FOR_ANY_LATER_AUTHORITY",
        )
        svc = ST12GServiceEvidenceViewV2(
            projection_id=f"ST12G::PROJECTION::{handoff.handoff_id}::SVC1",
            projection_contract_version=ST12G_CONTRACT_VERSION_V2,
            consumer_id="SVC1",
            core=core,
            read_model_class="OWNER_AND_AGENT_READ_ONLY_EVIDENCE_VIEW",
            stale_state="CURRENT_WITHIN_TRUSTED_F_TO_G_AND_D_REFERENCE_VALIDITY",
            action_eligibility_state="REVIEW_REQUESTS_ONLY",
            fake_receipt_allowed=False,
            runtime_execution_allowed=False,
        )
        return ST12GProjectionBundleV2(
            bundle_id=f"ST12G::BUNDLE::{handoff.handoff_id}",
            contract_version=ST12G_CONTRACT_VERSION_V2,
            core=core,
            readiness=readiness,
            pretrade=pretrade,
            agent_orch=agent_orch,
            svc=svc,
        )

    @staticmethod
    def _validate_context_and_lock(
        context: ComputationExecutionContextV1,
        input_lock: ImmutableReplayPaperInputLockV1,
        handoff: FToGHandoffReferencesV1,
    ) -> None:
        if input_lock.input_lock_id != handoff.input_lock_id:
            _contract_error(
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                "durable input lock and handoff identities differ",
            )
        scope = context.scope
        if (
            scope.input_snapshot_id != input_lock.input_lock_id
            or scope.market_scope_id not in input_lock.market_scope
            or scope.venue_scope_id not in input_lock.venue_scope
            or scope.instrument_or_contract_scope_id not in input_lock.instrument_scope
        ):
            _contract_error(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "trusted context scope is outside the durable input lock",
            )
        expected_epochs = _input_lock_source_epoch_refs(input_lock)
        if not expected_epochs:
            _contract_error(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "durable input lock has no source epochs",
            )
        if (
            handoff.source_epoch_refs != expected_epochs
            or context.source_epoch_id not in expected_epochs
        ):
            _contract_error(
                ReasonCode.SOURCE_CONFLICT,
                "context, input-lock, and handoff source epochs differ",
            )

    @staticmethod
    def _validate_current_custody(
        context: ComputationExecutionContextV1,
        input_lock: ImmutableReplayPaperInputLockV1,
        handoff: FToGHandoffReferencesV1,
        bundle: ComputationEvidenceBundleV1,
        current_d_reference: ST12FEvidenceReferenceV1,
    ) -> None:
        cutoff = context.as_of
        if cutoff < handoff.observed_at:
            _contract_error(
                ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID,
                "trusted cutoff precedes the handoff observation",
            )
        if cutoff > handoff.valid_until:
            _contract_error(
                ReasonCode.ST12F_BUNDLE_STALE,
                "F-to-G handoff is stale at the trusted cutoff",
            )
        if (
            handoff.contract_version != "1.4"
            or not handoff.read_only
            or handoff.terminal_state
            != EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED.value
            or bundle.contract_version != "1.4"
        ):
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "F handoff or parent bundle contract version/state differs",
            )
        if (
            bundle.terminal_state
            is not EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
            or bundle.independent_review_state
            != EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED.value
        ):
            _contract_error(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "parent bundle is not closed and independently validated",
            )
        if (
            bundle.input_lock_id != input_lock.input_lock_id
            or bundle.component_or_template_ref not in input_lock.cohort_template_ids
        ):
            _contract_error(
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                "parent bundle differs from the durable input-lock scope",
            )
        if bundle.g_handoff_projection != handoff:
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "parent bundle embedded G handoff differs from durable custody",
            )
        if not bundle.actual_executed_component_versions:
            _contract_error(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "current parent component version mapping is empty",
            )
        if bundle.blocker_codes:
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "current parent bundle cannot carry blockers",
            )
        if (
            current_d_reference.evidence_state
            is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
        ):
            _contract_error(
                ReasonCode.EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH,
                "current D evidence reference is unavailable",
            )
        if cutoff < current_d_reference.observed_at:
            _contract_error(
                ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID,
                "trusted cutoff precedes the D reference observation",
            )
        if cutoff > current_d_reference.valid_until:
            _contract_error(
                ReasonCode.ST12F_BUNDLE_STALE,
                "current D reference is stale at the trusted cutoff",
            )
        if (
            bundle.d_evidence_reference_projection != current_d_reference
            or current_d_reference.evidence_ref != handoff.evidence_bundle_ref
            or current_d_reference.evidence_id != bundle.evidence_id
            or current_d_reference.evidence_bundle_version
            != bundle.evidence_bundle_version
            or current_d_reference.component_or_template_ref
            != bundle.component_or_template_ref
            or current_d_reference.input_lock_id != handoff.input_lock_id
            or current_d_reference.source_epoch_refs != handoff.source_epoch_refs
            or current_d_reference.terminal_state != handoff.terminal_state
            or current_d_reference.contract_version != "1.4"
            or current_d_reference.no_effect_flags is not NO_EFFECTS_V1
        ):
            _contract_error(
                ReasonCode.EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH,
                "current D reference differs from handoff, parent, lock, epoch, or version custody",
            )
        for name in (
            "replay_result_ref",
            "paper_result_ref",
            "divergence_assessment_ref",
        ):
            _current_source_text(getattr(bundle, name), name)
        _current_source_text(
            handoff.quantum_classical_comparison_receipt_ref,
            "quantum_classical_comparison_receipt_ref",
        )
        _reference_tuple(
            bundle.lane_execution_receipt_refs,
            "lane_execution_receipt_refs",
            required=True,
        )


@dataclass(frozen=True, slots=True)
class ExistingOwnerProjectionCoordinatorV2:
    """Stateless coordinator over the existing durable ST12-F read surface."""

    evidence_service: ComputationEvidenceServiceProtocolV1
    owner_views: PreloadedOwnerProjectionBundleV1
    compiler: ExistingOwnerProjectionCompilerV2 = ExistingOwnerProjectionCompilerV2()

    def __post_init__(self) -> None:
        if type(self.owner_views) is not PreloadedOwnerProjectionBundleV1:
            _contract_error(
                ReasonCode.OWNER_DATA_MISSING,
                "coordinator requires one exact preloaded owner bundle",
            )
        if type(self.compiler) is not ExistingOwnerProjectionCompilerV2:
            _contract_error(
                ReasonCode.INPUT_OWNER_MISMATCH,
                "coordinator compiler must be the exact stateless compiler",
            )
        for method_name in (
            "resolve_g_handoff",
            "resolve_control_receipt",
            "resolve_bundle",
            "read_evidence_reference",
        ):
            if not callable(getattr(self.evidence_service, method_name, None)):
                _contract_error(
                    ReasonCode.INPUT_OWNER_MISMATCH,
                    f"evidence service lacks existing read method {method_name}",
                )

    def resolve(
        self,
        request: ST12GProjectionRequestV2,
    ) -> ST12GProjectionResolutionV2:
        if type(request) is not ST12GProjectionRequestV2:
            _contract_error(
                ReasonCode.SCHEMA_MISMATCH,
                "coordinator accepts only the exact ST12-G request",
            )
        cutoff = request.context.as_of
        try:
            request.context.assert_fresh()
            handoff = self.evidence_service.resolve_g_handoff(
                request.source_handoff_receipt_ref,
                decision_cutoff=cutoff,
            )
            if type(handoff) is not FToGHandoffReferencesV1:
                _contract_error(ReasonCode.SCHEMA_MISMATCH, "resolved handoff type differs")
            if request.source_handoff_receipt_ref != _canonical_g_receipt_ref(
                handoff.handoff_id
            ):
                _contract_error(
                    ReasonCode.SCHEMA_MISMATCH,
                    "request receipt reference differs from the durable handoff identity",
                )

            input_lock_receipt_ref = _canonical_lock_receipt_ref(handoff.input_lock_id)
            input_lock = self.evidence_service.resolve_control_receipt(
                input_lock_receipt_ref,
                ImmutableReplayPaperInputLockV1,
                decision_cutoff=cutoff,
            )
            if type(input_lock) is not ImmutableReplayPaperInputLockV1:
                _contract_error(
                    ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                    "resolved input-lock receipt type differs",
                )
            ExistingOwnerProjectionCompilerV2._validate_context_and_lock(
                request.context,
                input_lock,
                handoff,
            )

            bundle = self.evidence_service.resolve_bundle(
                handoff.evidence_bundle_ref,
                decision_cutoff=cutoff,
            )
            if type(bundle) is not ComputationEvidenceBundleV1:
                _contract_error(ReasonCode.SCHEMA_MISMATCH, "resolved bundle type differs")

            query = FToDEvidenceReferenceQueryV1(
                query_id=f"ST12G::D_REFERENCE_QUERY::{request.request_id}",
                requested_evidence_id=bundle.evidence_id,
                requested_component_or_template_ref=bundle.component_or_template_ref,
                expected_input_lock_id=handoff.input_lock_id,
                expected_source_epoch_refs=handoff.source_epoch_refs,
                evaluated_at=cutoff,
                request_read_lineage_refs=(
                    request.source_handoff_receipt_ref,
                    input_lock_receipt_ref,
                    handoff.evidence_bundle_ref,
                ),
            )
            current_d_reference = self.evidence_service.read_evidence_reference(
                request.context,
                causation_id=request.causation_id,
                correlation_id=request.correlation_id,
                query=query,
            )
            if type(current_d_reference) is not ST12FEvidenceReferenceV1:
                _contract_error(
                    ReasonCode.EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH,
                    "existing D reference read returned a noncanonical value",
                )

            projection_bundle = self.compiler.compile_current(
                request.context,
                input_lock,
                handoff,
                bundle,
                current_d_reference,
                self.owner_views,
            )
            return ST12GProjectionResolutionV2.current(
                resolution_id=f"ST12G::RESOLUTION::{request.request_id}",
                request_id=request.request_id,
                context_id=request.context.context_id,
                evaluated_at=cutoff,
                projection_bundle=projection_bundle,
            )
        except ComputationControlPlaneError as exc:
            if exc.reason_code in _STALE_REASON_CODES:
                state = ST12GProjectionResolutionStateV2.UNAVAILABLE_STALE_NO_AUTHORITY
            elif exc.reason_code in _BLOCKED_REASON_CODES:
                state = ST12GProjectionResolutionStateV2.UNAVAILABLE_BLOCKED_NO_AUTHORITY
            else:
                raise
            absence = ST12GProjectionAbsenceV2(
                absence_id=f"ST12G::ABSENCE::{request.request_id}",
                evaluation_context_id=request.context.context_id,
                evaluated_at=cutoff,
                state=state,
                reason_codes=(exc.reason_code,),
                source_handoff_receipt_ref_or_explicit_absence=(
                    request.source_handoff_receipt_ref
                ),
            )
            return ST12GProjectionResolutionV2.unavailable(
                resolution_id=f"ST12G::RESOLUTION::{request.request_id}",
                request_id=request.request_id,
                context_id=request.context.context_id,
                evaluated_at=cutoff,
                absence=absence,
            )


__all__ = [
    "ExistingOwnerProjectionCompilerV2",
    "ExistingOwnerProjectionCoordinatorV2",
    "ST12GAgentEvidenceHandoffV2",
    "ST12GBlockerSetStateV2",
    "ST12GBlockerStateV2",
    "ST12GOwnerDashboardEvidenceViewV2",
    "ST12GOwnerProjectionResolutionV2",
    "ST12GPretradeEvidenceProjectionV2",
    "ST12GProjectionAbsenceV2",
    "ST12GProjectionBundleV2",
    "ST12GProjectionCoreV2",
    "ST12GProjectionRequestV2",
    "ST12GProjectionResolutionStateV2",
    "ST12GProjectionResolutionV2",
    "ST12GReadinessEvidenceProjectionV2",
    "ST12GReferenceCollectionStateV2",
    "ST12GReferenceCollectionV2",
    "ST12GServiceEvidenceViewV2",
    "ST12GVersionMappingStateV2",
    "ST12GVersionMappingV2",
]
