from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    ComputationContextKeyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    AgentCapabilityDecisionStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    NoTradeReoptimizationRouteError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    ST12D_MATH_IMPLEMENTATION_REGISTRY,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    CanonicalOwnerPacketRegistryV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.mode_snapshot_policy import (
    D_MODE_STATE_REGISTRY,
    D_REQUIRED_PIN_DIMENSIONS,
    MODE_SNAPSHOT_CANDIDATE_KIND,
    MODE_SNAPSHOT_TRANSITIONS,
    ModeSnapshotCandidateInputsV1,
    evaluate_mode_snapshot_candidate,
    pre_f_unavailable_reference,
    validate_current_kill_submit_state,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ActivationPreconditionStateV1,
    AllowCandidateStateV1,
    ImplementationVersionPinV1,
    KillStateV1,
    ModeEligibilityState,
    OperationStatusV1,
    ReadOnlyKillSubmitStateV1,
    SnapshotCandidateStateV1,
    SnapshotRetirementStateV1,
    SnapshotRollbackStateV1,
    ST12FEvidenceReferenceV1,
    ST12FEvidenceStateV1,
    SubmitDisabledStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    QKUComputationControlPlaneV1,
)
from tests.stage1_prediction_markets.qku_computation_control_plane.tranche_e import (
    make_resolver,
    resolve_decision,
)


UTC = timezone.utc


def _inputs(
    *,
    evidence_state: ST12FEvidenceStateV1 = ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE,
    kill_active: bool = False,
    submit_disabled: bool = False,
    owner_confirmation: bool = True,
    computable: bool = True,
    latency_profile: bool = True,
    valid_until_delta: timedelta = timedelta(minutes=5),
) -> ModeSnapshotCandidateInputsV1:
    now = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    evidence = (
        pre_f_unavailable_reference(
            observed_at=now - timedelta(minutes=1),
            valid_until=now + valid_until_delta,
            causation_id="CAUSE::D::EVIDENCE",
            correlation_id="CORRELATION::D::EVIDENCE",
        )
        if evidence_state
        is ST12FEvidenceStateV1.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED
        else ST12FEvidenceReferenceV1(
            evidence_state=evidence_state,
            evidence_ref="ST12F-EVIDENCE::READ-ONLY::1",
            lane="REPLAY",
            dataset_grade_ref="DATASET-GRADE::1",
            venue_semantic_binding_ref="VENUE-SEMANTICS::1",
            cross_venue_equivalence_ref="VENUE-EQUIVALENCE::1",
            observed_at=now - timedelta(minutes=1),
            valid_until=now + valid_until_delta,
            policy_version="ST12F-INTERFACE-v1",
            causation_id="CAUSE::D::EVIDENCE",
            correlation_id="CORRELATION::D::EVIDENCE",
        )
    )
    math_ids = ("MATH-13", "MATH-14", "MATH-15", "MATH-39")
    return ModeSnapshotCandidateInputsV1(
        request_id="REQUEST::D::1",
        principal_id="parameter_selector_agent",
        task_id="AGENT-ORCH1-TASK::D::1",
        current_agent_id="parameter_selector_agent",
        capability_decision_ref="ST12E-DECISION::D::1",
        computation_bundle_ref="COMPUTATION-BUNDLE::D::1",
        context_ref="CONTEXT::D::1",
        formula_spec_refs=math_ids,
        implementation_version_pins=tuple(
            ImplementationVersionPinV1(
                math_spec_id=math_id,
                implementation_id=(
                    ST12D_MATH_IMPLEMENTATION_REGISTRY[
                        math_id
                    ].contract.implementation_id
                ),
            )
            for math_id in math_ids
        ),
        binding_profile_ref="BINDING-PROFILE::D::1",
        parameter_policy_snapshot_ref="PARAMETER-POLICY-SNAPSHOT::D::1",
        parameter_value_refs=("PARAMETER-VALUE::D::1",),
        source_epoch_refs=("SOURCE-EPOCH::D::1",),
        receipt_lineage_refs=("RECEIPT::D::PRECONDITION::1",),
        readiness_state_ref="READINESS::D::CURRENT",
        pretrade_state_ref="PRETRADE1::TRADE-CANDIDATE",
        owner_action_policy_ref="OWNER-ACTION-POLICY::CURRENT",
        current_mode="SAFE_CLASSICAL",
        requested_mode="HOTPATH_CANDIDATE_ONLY",
        expected_owner_state_ref="OWNER-STATE::UNCHANGED::1",
        candidate_version="SNAPSHOT-CANDIDATE-VERSION::1",
        created_at=now - timedelta(minutes=2),
        evaluated_at=now,
        expires_at=now + timedelta(minutes=5),
        causation_id="CAUSE::D::1",
        correlation_id="CORRELATION::D::1",
        evidence_reference=evidence,
        kill_submit_state=ReadOnlyKillSubmitStateV1(
            state_ref="KILL-SUBMIT::READ-ONLY::1",
            scope_ref="CONTEXT::D::1",
            kill_active=kill_active,
            submit_disabled=submit_disabled,
            observed_at=now - timedelta(minutes=1),
            valid_until=now + valid_until_delta,
            policy_version="SAFETY-OWNER::CURRENT",
            causation_id="CAUSE::D::SAFETY",
            correlation_id="CORRELATION::D::SAFETY",
        ),
        all_four_computability_dimensions_closed=computable,
        owner_confirmation_present=owner_confirmation,
        latency_profile_present=latency_profile,
    )


def test_exact_orthogonal_registry_and_transition_matrix() -> None:
    expected = {
        "MODE_ELIGIBILITY": tuple(state.value for state in ModeEligibilityState),
        "ALLOW_CANDIDATE": tuple(state.value for state in AllowCandidateStateV1),
        "ACTIVATION_PRECONDITION": tuple(
            state.value for state in ActivationPreconditionStateV1
        ),
        "SNAPSHOT_CANDIDATE": tuple(
            state.value for state in SnapshotCandidateStateV1
        ),
        "KILL_STATE": tuple(state.value for state in KillStateV1),
        "SUBMIT_DISABLED_STATE": tuple(
            state.value for state in SubmitDisabledStateV1
        ),
        "EVIDENCE_STATE": tuple(state.value for state in ST12FEvidenceStateV1),
        "ROLLBACK_STATE": tuple(state.value for state in SnapshotRollbackStateV1),
        "RETIREMENT_STATE": tuple(
            state.value for state in SnapshotRetirementStateV1
        ),
    }
    assert dict(D_MODE_STATE_REGISTRY) == expected
    assert sum(map(len, expected.values())) == 35
    assert tuple(row.transition_id for row in MODE_SNAPSHOT_TRANSITIONS) == tuple(
        f"T{number:02d}" for number in range(1, 18)
    )
    assert len({(row.source_state, row.destination_state, row.trigger) for row in MODE_SNAPSHOT_TRANSITIONS}) == 17
    assert tuple(row.owner_confirmation_required for row in MODE_SNAPSHOT_TRANSITIONS) == (
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    )
    assert len(D_REQUIRED_PIN_DIMENSIONS) == 12


def test_policy_outcomes_are_typed_fail_closed_and_never_activate() -> None:
    cases = (
        (
            _inputs(
                evidence_state=(
                    ST12FEvidenceStateV1.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED
                )
            ),
            AllowCandidateStateV1.EVIDENCE_UNAVAILABLE,
            ReasonCode.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED,
        ),
        (
            _inputs(owner_confirmation=False),
            AllowCandidateStateV1.OWNER_CONFIRMATION_REQUIRED,
            ReasonCode.OWNER_CONFIRMATION_REQUIRED,
        ),
        (
            _inputs(),
            AllowCandidateStateV1.ELIGIBLE_NOT_ACTIVATED,
            ReasonCode.ALLOW_ELIGIBLE_NOT_ACTIVATED,
        ),
        (
            _inputs(kill_active=True),
            AllowCandidateStateV1.BLOCKED,
            ReasonCode.KILL_OR_SUBMIT_DISABLED,
        ),
        (
            _inputs(submit_disabled=True),
            AllowCandidateStateV1.BLOCKED,
            ReasonCode.KILL_OR_SUBMIT_DISABLED,
        ),
        (
            _inputs(computable=False),
            AllowCandidateStateV1.BLOCKED,
            ReasonCode.DEPENDENCY_OR_COMPUTABILITY_INCOMPLETE,
        ),
        (
            _inputs(latency_profile=False),
            AllowCandidateStateV1.BLOCKED,
            ReasonCode.LATENCY_PROFILE_REQUIRED,
        ),
        (
            _inputs(
                evidence_state=ST12FEvidenceStateV1.EVIDENCE_REFERENCE_STALE
            ),
            AllowCandidateStateV1.BLOCKED,
            ReasonCode.EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH,
        ),
        (
            _inputs(valid_until_delta=timedelta(minutes=-1)),
            AllowCandidateStateV1.BLOCKED,
            ReasonCode.KILL_SUBMIT_DISABLED_OR_SAFETY_BLOCK,
        ),
    )
    for inputs, expected_state, expected_reason in cases:
        result = evaluate_mode_snapshot_candidate(inputs)
        decision = result.mode_snapshot_decision
        proposal = result.snapshot_transition_proposal
        assert decision.allow_candidate_state is expected_state
        assert decision.reason_codes == (expected_reason,)
        assert decision.runtime_effect_authorized is False
        assert decision.active_pointer_commit_allowed is False
        assert decision.order_release_authorized is False
        assert proposal.mutation_allowed is False
        assert proposal.active_pointer_commit_allowed is False
        assert proposal.runtime_effect_authorized is False
        assert proposal.order_release_authorized is False
        assert result.no_authority_flag is True
        candidate = result.snapshot_candidate_or_explicit_absence
        if candidate is not None:
            assert candidate.runtime_effect_authorized is False
            assert candidate.order_release_authorized is False
            assert candidate.activated is False
        if expected_reason in {
            ReasonCode.KILL_OR_SUBMIT_DISABLED,
            ReasonCode.KILL_SUBMIT_DISABLED_OR_SAFETY_BLOCK,
            ReasonCode.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED,
            ReasonCode.EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH,
            ReasonCode.DEPENDENCY_OR_COMPUTABILITY_INCOMPLETE,
            ReasonCode.LATENCY_PROFILE_REQUIRED,
        }:
            assert candidate is None
            assert decision.snapshot_candidate_state is SnapshotCandidateStateV1.ABSENT
    clear_inputs = _inputs()
    assert validate_current_kill_submit_state(
        clear_inputs.kill_submit_state,
        evaluated_at=clear_inputs.evaluated_at,
    ) == ()


def test_pretrade_no_trade_routes_before_any_d_body_access() -> None:
    operation_id = "submit_candidate_proposal"
    no_trade = resolve_decision(
        make_resolver(
            operation_id=operation_id,
            envelope_overrides={
                "terminal_no_trade": True,
                "reoptimization_variable_ids": (
                    "market",
                    "venue",
                    "size",
                    "next_target",
                ),
            },
        ),
        operation_id=operation_id,
        requested_scope_refs={
            "qku_scope_refs": ("QKU::ST12E::TEST",),
            "formula_scope_refs": ("MATH-01",),
        },
    )

    class _Admission:
        def admit_operation(self, _request: object):
            return no_trade

    class _Resolver:
        calls = 0

        def resolve_mode_snapshot_inputs(self, *_args: object):
            self.calls += 1
            raise AssertionError("D body executed after typed NO_TRADE")

    class _Probe:
        request_id = no_trade.request_id
        operation_name = operation_id
        principal_id = no_trade.principal_id
        idempotency_key = no_trade.idempotency_key

        @property
        def candidate_kind(self):
            raise AssertionError("candidate discriminator read before NO_TRADE route")

    resolver = _Resolver()
    service = QKUComputationControlPlaneV1(
        CanonicalOwnerPacketRegistryV1(),
        agent_capability_resolver=_Admission(),
        mode_snapshot_input_resolver=resolver,
    )
    with pytest.raises(NoTradeReoptimizationRouteError):
        service.submit_candidate_proposal(_Probe())  # type: ignore[arg-type]
    assert no_trade.decision_state is (
        AgentCapabilityDecisionStateV1.NO_TRADE_REOPTIMIZATION_ROUTED
    )
    assert resolver.calls == 0

    kill_context = ComputationContextKeyV1(
        context_id="CONTEXT::D::EARLY-SAFETY",
        as_of=_inputs().evaluated_at,
        observed_at=_inputs().evaluated_at - timedelta(seconds=1),
        source_epoch_id="SOURCE-EPOCH::D::EARLY-SAFETY",
        input_version="D::EARLY-SAFETY::V1",
        maximum_age=timedelta(minutes=1),
    )
    kill_decision = resolve_decision(
        make_resolver(
            operation_id=operation_id,
            envelope_overrides={
                "context_ref": kill_context.context_id,
                "idempotency_key": "IDEMPOTENCY::D::EARLY-SAFETY",
            },
        ),
        request_id="REQUEST::D::EARLY-SAFETY",
        operation_id=operation_id,
        context_ref=kill_context.context_id,
        requested_scope_refs={
            "qku_scope_refs": ("QKU::ST12E::TEST",),
            "formula_scope_refs": ("MATH-01",),
        },
        request_idempotency_key="IDEMPOTENCY::D::EARLY-SAFETY",
    )

    class _KillAdmission:
        def admit_operation(self, _request: object):
            return kill_decision

    class _KillResolver:
        def resolve_mode_snapshot_inputs(self, _request: object, decision: object):
            template = _inputs(kill_active=True)
            return replace(
                template,
                request_id=kill_decision.request_id,
                principal_id=kill_decision.principal_id,
                task_id=kill_decision.task_id,
                current_agent_id=kill_decision.current_agent_id,
                capability_decision_ref=kill_decision.decision_id,
                context_ref=kill_context.context_id,
                kill_submit_state=replace(
                    template.kill_submit_state,
                    scope_ref=kill_context.context_id,
                ),
            )

    class _KillBodyProbe:
        request_id = kill_decision.request_id
        operation_name = operation_id
        requested_at = _inputs().evaluated_at
        principal_id = kill_decision.principal_id
        capability_bundle_id = "CAPABILITY::D::EARLY-SAFETY"
        idempotency_key = kill_decision.idempotency_key
        traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        tracestate = "vendor=value"
        candidate_kind = MODE_SNAPSHOT_CANDIDATE_KIND
        context = kill_context

        @property
        def proposed_specification(self):
            raise AssertionError("proposal schema read after current safety block")

        @property
        def source_candidate_refs(self):
            raise AssertionError("candidate source body read after current safety block")

    kill_service = QKUComputationControlPlaneV1(
        CanonicalOwnerPacketRegistryV1(),
        agent_capability_resolver=_KillAdmission(),
        mode_snapshot_input_resolver=_KillResolver(),
    )
    blocked_response = kill_service.submit_candidate_proposal(
        _KillBodyProbe()  # type: ignore[arg-type]
    )
    assert blocked_response.status is OperationStatusV1.BLOCKED
    assert blocked_response.proposal.mode_snapshot_result is not None
    assert (
        blocked_response.proposal.mode_snapshot_result.snapshot_candidate_or_explicit_absence
        is None
    )
    assert blocked_response.proposal.mode_snapshot_result.mode_snapshot_decision.reason_codes == (
        ReasonCode.KILL_OR_SUBMIT_DISABLED,
    )


def test_non_d_public_contract_and_existing_source_owners_remain_bounded() -> None:
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
        IMPLEMENTED_OPERATION_IDS,
    )

    assert len(IMPLEMENTED_OPERATION_IDS) == 12
    assert set(IMPLEMENTED_OPERATION_IDS) == {
        name
        for name, member in vars(QKUComputationControlPlaneV1).items()
        if callable(member) and not name.startswith("_")
    }
    baseline = evaluate_mode_snapshot_candidate(_inputs())
    changed = evaluate_mode_snapshot_candidate(
        replace(_inputs(), owner_confirmation_present=False)
    )
    assert baseline.mode_snapshot_decision.allow_candidate_state is (
        AllowCandidateStateV1.ELIGIBLE_NOT_ACTIVATED
    )
    assert changed.mode_snapshot_decision.allow_candidate_state is (
        AllowCandidateStateV1.OWNER_CONFIRMATION_REQUIRED
    )
    assert baseline.snapshot_transition_proposal.expected_owner_state_ref == (
        changed.snapshot_transition_proposal.expected_owner_state_ref
    )
