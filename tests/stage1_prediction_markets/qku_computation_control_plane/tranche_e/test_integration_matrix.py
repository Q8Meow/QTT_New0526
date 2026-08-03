"""Compact frozen-owner, mandatory-admission, route, and receipt matrix."""

from __future__ import annotations

from dataclasses import replace
import inspect
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest

from src.qtt.dashboard.owner_action_registry import ACTION_DEFINITIONS
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    HELD_OPERATION_IDS,
    IMPLEMENTED_OPERATION_IDS,
    NO_EFFECT_PROFILE_REF,
    NO_TRADE_REOPTIMIZATION_VARIABLE_IDS,
    ST12E_BINDING_OUTSIDE_SCOPE,
    AgentCapabilityDecisionStateV1,
    AgentCapabilityDecisionV1,
    AgentCapabilityResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    AuthorityDeniedError,
    ContractValidationError,
    NoTradeReoptimizationRouteError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    CanonicalOwnerPacketRegistryV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    QKUComputationControlPlaneV1,
)

from . import (
    TEST_CONTEXT_REF,
    TEST_PRINCIPAL_ID,
    make_resolver,
    policy_store,
    resolve_decision,
)


class _CountingAdmission:
    def __init__(self, decision: AgentCapabilityDecisionV1) -> None:
        self.calls = 0
        self.decision = decision

    def admit_operation(self, request: object) -> AgentCapabilityDecisionV1:
        self.calls += 1
        return self.decision


class _OperationBodyTouched(AssertionError):
    pass


class _AdmissionProbeRequest:
    request_id = "REQUEST::ST12E::TEST"
    operation_name = "resolve_identity"
    principal_id = TEST_PRINCIPAL_ID
    capability_bundle_id = "ST12E_TEST_BUNDLE"
    idempotency_key = "ST12E_IDEMPOTENCY::TEST"
    context = SimpleNamespace(context_id=TEST_CONTEXT_REF)

    def __init__(self) -> None:
        self.operation_body_reads = 0

    @property
    def identity_query(self) -> object:
        self.operation_body_reads += 1
        raise _OperationBodyTouched


def _service(admission: object) -> QKUComputationControlPlaneV1:
    return QKUComputationControlPlaneV1(
        CanonicalOwnerPacketRegistryV1(),
        agent_capability_resolver=admission,
    )


def test_frozen_snapshot_and_task_envelope_are_immutable_indexes() -> None:
    snapshot = policy_store().snapshot
    resolver = make_resolver()
    bundle = next(iter(resolver._bundles.values()))

    assert isinstance(snapshot.policy_rows, MappingProxyType)
    assert isinstance(snapshot.parameter_scope_rows, MappingProxyType)
    assert isinstance(bundle.task_envelope, MappingProxyType)
    with pytest.raises(TypeError):
        snapshot.policy_rows["NEW"] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        bundle.task_envelope["operation_id"] = "compute_stack"  # type: ignore[index]


def test_request_time_resolution_performs_no_file_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolver = make_resolver()

    def _forbidden_read(*_args, **_kwargs):
        raise AssertionError("request-time policy lookup attempted a file read")

    monkeypatch.setattr(Path, "read_text", _forbidden_read)
    decision = resolve_decision(
        resolver,
        requested_scope_refs={
            "qku_scope_refs": ("QKU::ST12E::TEST",),
            "formula_scope_refs": ("MATH-01",),
            "data_scope_refs": ("PUBLIC_TEST_PACKET",),
            "tool_scope_refs": ("QKUComputationControlPlaneV1",),
            "action_scope_refs": ("REQUEST_AGENT_TASK",),
        },
    )

    assert decision.eligible
    assert decision.runtime_effect_authorized is False


def test_service_requires_one_typed_admission_owner_and_no_none_bypass() -> None:
    registry = CanonicalOwnerPacketRegistryV1()

    with pytest.raises(ContractValidationError) as missing:
        QKUComputationControlPlaneV1(
            registry,
            agent_capability_resolver=None,  # type: ignore[arg-type]
        )
    assert missing.value.reason_code is ReasonCode.INVALID_CONTRACT

    class _MalformedAdmission:
        def admit_operation(self, _request: object) -> object:
            return object()

    malformed = _service(_MalformedAdmission())
    request = _AdmissionProbeRequest()
    with pytest.raises(AuthorityDeniedError) as incompatible:
        malformed.resolve_identity(request)  # type: ignore[arg-type]
    assert incompatible.value.reason_code is ReasonCode.TASK_ENVELOPE_MISSING
    assert request.operation_body_reads == 0


def test_all_twelve_public_operations_execute_exactly_one_central_admission() -> None:
    structural_counts = {
        operation_id: inspect.getsource(
            getattr(QKUComputationControlPlaneV1, operation_id)
        ).count("_admit_agent_request(self, request)")
        for operation_id in IMPLEMENTED_OPERATION_IDS
    }

    assert structural_counts == {
        operation_id: 1 for operation_id in IMPLEMENTED_OPERATION_IDS
    }
    assert not any(
        hasattr(QKUComputationControlPlaneV1, operation_id)
        for operation_id in HELD_OPERATION_IDS
    )


def test_eligible_denied_and_no_trade_decisions_control_body_execution() -> None:
    eligible = resolve_decision(make_resolver())
    denied = resolve_decision(
        make_resolver(
            envelope_overrides={"direct_provider_requested": True}
        )
    )
    no_trade = resolve_decision(
        make_resolver(
            envelope_overrides={
                "terminal_no_trade": True,
                "reoptimization_variable_ids": (
                    "market",
                    "venue",
                    "size",
                    "next_target",
                ),
            }
        ),
        requested_scope_refs={
            "qku_scope_refs": ("QKU::ST12E::TEST",),
            "formula_scope_refs": ("MATH-01",),
        },
    )

    eligible_request = _AdmissionProbeRequest()
    with pytest.raises(_OperationBodyTouched):
        _service(_CountingAdmission(eligible)).resolve_identity(
            eligible_request  # type: ignore[arg-type]
        )
    assert eligible_request.operation_body_reads == 1

    denied_request = _AdmissionProbeRequest()
    with pytest.raises(AuthorityDeniedError) as denied_error:
        _service(_CountingAdmission(denied)).resolve_identity(
            denied_request  # type: ignore[arg-type]
        )
    assert not isinstance(
        denied_error.value, NoTradeReoptimizationRouteError
    )
    assert denied_request.operation_body_reads == 0

    no_trade_request = _AdmissionProbeRequest()
    with pytest.raises(NoTradeReoptimizationRouteError) as routed:
        _service(_CountingAdmission(no_trade)).resolve_identity(
            no_trade_request  # type: ignore[arg-type]
        )
    assert routed.value.decision is no_trade
    assert no_trade_request.operation_body_reads == 0
    assert no_trade.decision_state is (
        AgentCapabilityDecisionStateV1.NO_TRADE_REOPTIMIZATION_ROUTED
    )
    assert no_trade.terminal_route == (
        "PRETRADE1_BOUNDED_TRADEPLAN_VARIABLE_REOPTIMIZATION"
    )
    assert {
        "qku_scope_refs=QKU::ST12E::TEST",
        "formula_scope_refs=MATH-01",
        "reoptimization_variable_id=market",
        "reoptimization_variable_id=venue",
        "reoptimization_variable_id=size",
        "reoptimization_variable_id=next_target",
    } <= set(no_trade.scope_refs)
    assert no_trade.agent_orch_receipt_ref
    assert no_trade.st12c_causation_correlation_refs
    assert "OWNER_REVIEW_REQUIRED" in no_trade.alternative_route_refs
    assert no_trade.no_effect_profile_ref == NO_EFFECT_PROFILE_REF
    assert "QKU_AND_FORMULA_IMMUTABLE" in no_trade.limitation_codes
    assert no_trade.runtime_effect_authorized is False
    assert set(("market", "venue", "size", "next_target")) <= set(
        NO_TRADE_REOPTIMIZATION_VARIABLE_IDS
    )


def test_idempotency_and_receipt_links_remain_existing_no_effect_truth() -> None:
    first_resolver = make_resolver()
    first_bundle = next(iter(first_resolver._bundles.values()))
    second_envelope = dict(first_bundle.task_envelope)
    second_envelope["idempotency_key"] = "ST12E_IDEMPOTENCY::SECOND"
    second_bundle = replace(
        first_bundle,
        bundle_id="ST12E_TEST_BUNDLE_SECOND",
        task_envelope=second_envelope,
    )
    resolver = AgentCapabilityResolverV1(
        policy_store(),
        {
            first_bundle.bundle_id: first_bundle,
            second_bundle.bundle_id: second_bundle,
        },
    )

    first = resolve_decision(resolver)
    repeated = resolve_decision(resolver)
    duplicate = resolve_decision(
        resolver,
        capability_bundle_id=second_bundle.bundle_id,
        request_idempotency_key="ST12E_IDEMPOTENCY::SECOND",
    )

    assert first is repeated
    assert first.agent_orch_receipt_ref.startswith(
        "AGENT_ORCH1::AGENTDECISIONRECEIPTV1_"
    )
    assert first.agent_orch_receipt_ref in first.evidence_refs
    assert first.task_id in first.evidence_refs
    assert first.st12c_causation_correlation_refs
    assert first.no_effect_profile_ref == NO_EFFECT_PROFILE_REF
    assert first.runtime_effect_authorized is False
    assert ReasonCode.IDEMPOTENCY_CONFLICT in duplicate.reason_codes
    assert not duplicate.eligible


def test_all_parameter_rows_retain_no_orphan_and_orthogonal_route_fields() -> None:
    rows = policy_store().snapshot.parameter_scope_rows

    assert tuple(rows) == tuple(
        sorted(rows, key=lambda value: int(value.rsplit("::", 1)[1]))
    )
    for parameter_id, row in rows.items():
        assert row.parameter_id == parameter_id
        assert row.upstream_source_universe_ref
        assert row.mapped_compatibility_refs
        assert row.unmapped_compatibility_refs
        assert row.current_principal_refs_or_exact_gap
        assert "ComputationParameterPolicyV1::" in row.value_policy_ref
        assert row.st12e_binding_state
        assert row.st12e_capability_binding_ref_or_explicit_absence
        assert row.st12e_certified_source_universe_ref_or_explicit_absence
        assert row.st12e_current_principal_refs_or_explicit_absence
        assert row.downstream_consumer_refs
        assert row.lifecycle_state
        assert row.timing_state
        assert row.validator_ref
        assert row.terminal_route
        assert row.semantic_owner
        assert row.implementation_owner
        assert row.producer_ref
        assert row.upstream_artifact_refs
        assert row.upstream_row_or_value_refs
        assert row.current_principal_duty_policy_refs
        assert row.activation_state == "NO_EFFECT_CONTRACT_ONLY"


def test_owner_actions_and_outside_e_parameters_remain_request_only() -> None:
    action_ids = policy_store().snapshot.owner_action_ids

    for action_id in action_ids:
        definition = ACTION_DEFINITIONS[action_id]
        semantics = str(definition["semantics"]).casefold()
        assert definition["confirmation_class"] in {
            "OWNER_REVIEW_REQUIRED",
            "CRITICAL_CONFIRMATION",
        }
        assert "request" in semantics or "route" in semantics
        assert not any(
            phrase in semantics
            for phrase in (
                "submits an order",
                "activates live",
                "accepts source truth",
            )
        )

    outside_parameter_id = next(
        parameter_id
        for parameter_id, row in policy_store().snapshot.parameter_scope_rows.items()
        if row.st12e_binding_state == ST12E_BINDING_OUTSIDE_SCOPE
    )
    decision = resolve_decision(
        make_resolver(), requested_parameter_ids=(outside_parameter_id,)
    )
    assert ReasonCode.PARAMETER_SCOPE_MISMATCH in decision.reason_codes
    assert not decision.eligible
