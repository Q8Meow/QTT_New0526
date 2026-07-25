"""Default-deny authority boundary for every public Tranche-A operation."""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import StrEnum

from .errors import AuthorityDeniedError, ReasonCode


class Capability(StrEnum):
    PROVIDER_CONNECTION = "PROVIDER_CONNECTION"
    PRIVATE_STATE_READ = "PRIVATE_STATE_READ"
    REPLAY_OR_PAPER_EXECUTION = "REPLAY_OR_PAPER_EXECUTION"
    MODE_OR_GRANT_ACTIVATION = "MODE_OR_GRANT_ACTIVATION"
    ORDER_RELEASE = "ORDER_RELEASE"
    QPU_EXECUTION = "QPU_EXECUTION"
    PROFIT_OR_QUANTUM_ADVANTAGE_CLAIM = "PROFIT_OR_QUANTUM_ADVANTAGE_CLAIM"
    MASTER_PLAN_MUTATION = "MASTER_PLAN_MUTATION"
    MERGE_CANARY_LIVE_OR_LAUNCH = "MERGE_CANARY_LIVE_OR_LAUNCH"
    LLM_INFERENCE = "LLM_INFERENCE"


class TrustBoundary(StrEnum):
    DATA_FLOW = "DATA_FLOW"
    PRINCIPAL = "PRINCIPAL"
    TOOL = "TOOL"
    STORE = "STORE"
    PROVIDER_INTERFACE = "PROVIDER_INTERFACE"
    DASHBOARD_REQUEST = "DASHBOARD_REQUEST"
    RELEASE_SURFACE = "RELEASE_SURFACE"


def _required_text(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AuthorityDeniedError(
            ReasonCode.INCOMPLETE_CONTRACT, f"{field_name} is required"
        )


def _exact_bool(value: object, field_name: str) -> None:
    if type(value) is not bool:
        raise AuthorityDeniedError(
            ReasonCode.INVALID_CONTRACT, f"{field_name} must be a boolean"
        )


@dataclass(frozen=True, slots=True)
class AuthenticationBindingV1:
    principal_identity: str
    session_boundary_id: str
    request_identity: str
    trace_identity: str
    economic_idempotency_key: str

    def __post_init__(self) -> None:
        values = (
            self.principal_identity,
            self.session_boundary_id,
            self.request_identity,
            self.trace_identity,
            self.economic_idempotency_key,
        )
        for field_name, value in zip(
            (
                "principal_identity",
                "session_boundary_id",
                "request_identity",
                "trace_identity",
                "economic_idempotency_key",
            ),
            values,
            strict=True,
        ):
            _required_text(value, field_name)
        if len(set(values)) != len(values):
            raise AuthorityDeniedError(
                ReasonCode.INVALID_CONTRACT,
                "principal, session, request, trace, and idempotency identities "
                "must remain distinct",
            )


@dataclass(frozen=True, slots=True)
class CapabilityRequirementV1:
    principal_identity: str
    operation_id: str
    required_capabilities: tuple[Capability, ...]
    direct_agent_authority: bool = False
    direct_provider_authority: bool = False
    granted: bool = False

    def __post_init__(self) -> None:
        _required_text(self.principal_identity, "principal_identity")
        _required_text(self.operation_id, "operation_id")
        if not isinstance(self.required_capabilities, tuple) or any(
            not isinstance(capability, Capability)
            for capability in self.required_capabilities
        ):
            raise AuthorityDeniedError(
                ReasonCode.INVALID_CONTRACT,
                "required_capabilities must be a tuple of Capability values",
            )
        if len(set(self.required_capabilities)) != len(
            self.required_capabilities
        ):
            raise AuthorityDeniedError(
                ReasonCode.INVALID_CONTRACT,
                "capability requirements must be exact and unique",
            )
        for name in (
            "direct_agent_authority",
            "direct_provider_authority",
            "granted",
        ):
            _exact_bool(getattr(self, name), name)
        if (
            self.direct_agent_authority
            or self.direct_provider_authority
            or self.granted
        ):
            raise AuthorityDeniedError(
                ReasonCode.CAPABILITY_DENIED,
                "Tranche A may describe requirements but cannot grant authority",
            )


@dataclass(frozen=True, slots=True)
class CapabilityEnvelopeV1:
    provider_connection_allowed: bool = False
    private_state_read_allowed: bool = False
    replay_or_paper_execution_allowed: bool = False
    mode_or_grant_activation_allowed: bool = False
    order_release_allowed: bool = False
    qpu_execution_allowed: bool = False
    profit_or_quantum_advantage_claim_allowed: bool = False
    master_plan_mutation_authorized: bool = False
    merge_canary_live_or_launch_allowed: bool = False
    llm_inference_allowed: bool = False

    def __post_init__(self) -> None:
        for item in fields(self):
            _exact_bool(getattr(self, item.name), item.name)
        enabled = [item.name for item in fields(self) if getattr(self, item.name)]
        if enabled:
            raise AuthorityDeniedError(
                ReasonCode.CAPABILITY_DENIED,
                f"Tranche A capabilities must remain false: {', '.join(enabled)}",
            )

    def deny(self, capability: Capability) -> None:
        if not isinstance(capability, Capability):
            raise AuthorityDeniedError(
                ReasonCode.INVALID_CONTRACT,
                "capability denial requires an allowlisted Capability value",
            )
        raise AuthorityDeniedError(
            ReasonCode.CAPABILITY_DENIED,
            f"{capability} is outside the authorized Tranche-A contract boundary",
        )


TRANCHE_A_AUTHORITY = CapabilityEnvelopeV1()
TRANCHE_A_TRUST_BOUNDARIES = tuple(TrustBoundary)


def assert_no_effect_authority(envelope: CapabilityEnvelopeV1) -> None:
    if not isinstance(envelope, CapabilityEnvelopeV1):
        raise AuthorityDeniedError(
            ReasonCode.INVALID_CONTRACT,
            "authority must be a typed CapabilityEnvelopeV1",
        )
    for item in fields(envelope):
        if getattr(envelope, item.name):
            raise AuthorityDeniedError(
                ReasonCode.CAPABILITY_DENIED, f"{item.name} must remain false"
            )
