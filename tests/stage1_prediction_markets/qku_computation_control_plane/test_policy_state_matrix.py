from __future__ import annotations

from dataclasses import replace
from datetime import timedelta, timezone
from functools import lru_cache
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    AgentCapabilityDecisionStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    NoTradeReoptimizationRouteError,
    OwnerAdapterError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    CanonicalOwnerPacketRegistryV1,
    CurrentModeSnapshotInputResolverV1,
    OwnerValuePacketV1,
    ST12D_OWNER_ACTION_BINDING_ID,
    ST12D_SAFETY_BINDING_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.mode_snapshot_policy import (
    D_MODE_STATE_REGISTRY,
    D_REQUIRED_PIN_DIMENSIONS,
    MODE_SNAPSHOT_CANDIDATE_KIND,
    MODE_SNAPSHOT_TRANSITIONS,
    ModeSnapshotCandidateInputsV1,
    build_snapshot_transition_proposal,
    evaluate_mode_snapshot_candidate,
    pre_f_unavailable_reference,
    validate_current_kill_submit_state,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ActivationPreconditionStateV1,
    AllowCandidateStateV1,
    KillStateV1,
    ModeEligibilityState,
    OwnerActionConfirmationReceiptV1,
    OwnerActionConfirmationStateV1,
    OperationStatusV1,
    ReadOnlyKillSubmitStateV1,
    SnapshotCandidateStateV1,
    SnapshotRetirementStateV1,
    SnapshotRollbackStateV1,
    ST12FEvidenceReferenceV1,
    ST12FEvidenceStateV1,
    SubmitDisabledStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    EconomicReceiptEventSpineV1,
    EconomicRecordTypeV1,
    ModeSnapshotControlClassV1,
    ModeSnapshotControlReceiptRecordV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    QKUComputationControlPlaneV1,
)
from tests.stage1_prediction_markets.qku_computation_control_plane.tranche_e import (
    make_resolver,
    resolve_decision,
)
from tools.build_qku_computation_control_plane import _build_st12d_audit_bundle


UTC = timezone.utc


@lru_cache(maxsize=1)
def _audit_bundle_fixture():
    return _build_st12d_audit_bundle()


def _transition_receipt_proposal(
    *,
    transition_id: str,
    request_id: str,
    principal_id: str,
    task_id: str,
    capability_decision_ref: str,
    context_ref: str,
    snapshot_candidate_ref: str,
    candidate_version: str,
    expected_owner_state_ref: str,
    effective_at: object,
) -> EconomicReceiptEventSpineV1:
    rule = next(
        row for row in MODE_SNAPSHOT_TRANSITIONS if row.transition_id == transition_id
    )
    record_id = f"MODE-SNAPSHOT-CONTROL::{request_id}::{transition_id}"
    payload = ModeSnapshotControlReceiptRecordV1(
        control_receipt_id=record_id,
        control_class=ModeSnapshotControlClassV1.MODE_SNAPSHOT_EVALUATION,
        request_id=request_id,
        task_id=task_id,
        principal_id=principal_id,
        capability_decision_ref=capability_decision_ref,
        context_ref=context_ref,
        snapshot_candidate_ref_or_explicit_absence=snapshot_candidate_ref,
        mode_snapshot_decision_ref=f"MODE-SNAPSHOT-DECISION::{request_id}",
        transition_proposal_ref=f"SNAPSHOT-TRANSITION::{request_id}::{transition_id}",
        transition_id=transition_id,
        source_state=rule.source_state,
        destination_state=rule.destination_state,
        target_candidate_version=candidate_version,
        implementation_pin_refs=(),
        parameter_value_refs=(),
        source_epoch_refs=(f"SOURCE-EPOCH::{request_id}",),
        predecessor_transition_receipt_refs=(),
        state_before_refs=(
            rule.source_state,
            expected_owner_state_ref,
            snapshot_candidate_ref,
        ),
        state_after_refs=(rule.destination_state, snapshot_candidate_ref),
        typed_reason_codes=(rule.reason_code,),
        fallback_route=rule.terminal_route,
        owner_review_route="EXISTING_OWNER_ACTION_REVIEW",
        latency_measurement_ref_or_explicit_absence=(
            f"LATENCY-MEASUREMENT::{request_id}"
        ),
        owner_action_policy_ref="OWNER-ACTION-POLICY::CURRENT",
    )
    return EconomicReceiptEventSpineV1(
        record_id=record_id,
        record_type=EconomicRecordTypeV1.MODE_SNAPSHOT_CONTROL,
        schema_version="ST12D_MODE_SNAPSHOT_CONTROL_V1",
        semantic_owner="QKUComputationControlPlaneV1",
        implementation_owner="QKUComputationControlPlaneV1",
        context_ref=context_ref,
        effective_at=effective_at,
        recorded_at=effective_at,
        causation_id=f"CAUSE::{request_id}::{transition_id}",
        correlation_id=f"CORRELATION::{request_id}::{transition_id}",
        traceparent=f"TRACEPARENT::{request_id}::{transition_id}",
        tracestate="vendor=value",
        sequence=0,
        aggregate_id=f"MODE-SNAPSHOT::{request_id}",
        aggregate_version=0,
        authority_class="NO_EFFECT_MODE_SNAPSHOT_CONTROL_ONLY",
        typed_payload=payload,
    )


def _inputs(
    *,
    evidence_state: ST12FEvidenceStateV1 = ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE,
    kill_active: bool = False,
    submit_disabled: bool = False,
    owner_confirmation: bool = True,
    latency_profile: bool = True,
    valid_until_delta: timedelta = timedelta(minutes=5),
) -> ModeSnapshotCandidateInputsV1:
    bundle, _registry = _audit_bundle_fixture()
    now = bundle.execution_context.as_of
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
            input_lock_id="ST12F-INPUT-LOCK::D::1",
            component_or_template_ref="ST12F-TEMPLATE::D::1",
            evidence_bundle_version="ST12F-EVIDENCE-BUNDLE::D::1::V1",
            source_epoch_refs=("SOURCE-EPOCH::D::1",),
            terminal_state="CLOSED_INDEPENDENTLY_VALIDATED",
        )
    )
    predecessor_proposal = (
        _transition_receipt_proposal(
            transition_id="T06",
            request_id="REQUEST::D::1",
            principal_id="parameter_selector_agent",
            task_id="AGENT-ORCH1-TASK::D::1",
            capability_decision_ref="ST12E-DECISION::D::1",
            context_ref=bundle.execution_context.context_id,
            snapshot_candidate_ref="SNAPSHOT-CANDIDATE::REQUEST::D::1",
            candidate_version="SNAPSHOT-CANDIDATE-VERSION::1",
            expected_owner_state_ref="OWNER-STATE::UNCHANGED::1",
            effective_at=now,
        )
        if owner_confirmation
        else None
    )
    owner_action = OwnerActionConfirmationReceiptV1(
        receipt_ref="OWNER-ACTION-RECEIPT::D::1",
        owner_action_policy_ref="OWNER-ACTION-POLICY::CURRENT",
        state=(
            OwnerActionConfirmationStateV1.CONFIRMED_CURRENT
            if owner_confirmation
            else OwnerActionConfirmationStateV1.ABSENT
        ),
        principal_id="parameter_selector_agent",
        task_id="AGENT-ORCH1-TASK::D::1",
        capability_decision_ref="ST12E-DECISION::D::1",
        context_ref=bundle.execution_context.context_id,
        observed_at=now - timedelta(minutes=1),
        valid_until=now + timedelta(minutes=5),
        causation_id="CAUSE::D::OWNER-ACTION",
        correlation_id="CORRELATION::D::OWNER-ACTION",
        predecessor_transition_id_or_explicit_absence=(
            "T06" if owner_confirmation else "EXPLICIT_ABSENCE"
        ),
        predecessor_transition_receipt_ref_or_explicit_absence=(
            predecessor_proposal.record_id
            if owner_confirmation
            else "EXPLICIT_ABSENCE"
        ),
        predecessor_transition_receipt_proposal_or_explicit_absence=(
            predecessor_proposal
        ),
    )
    return ModeSnapshotCandidateInputsV1(
        request_id="REQUEST::D::1",
        principal_id="parameter_selector_agent",
        task_id="AGENT-ORCH1-TASK::D::1",
        current_agent_id="parameter_selector_agent",
        capability_decision_ref="ST12E-DECISION::D::1",
        computation_bundle_ref=bundle.bundle_ref,
        context_ref=bundle.execution_context.context_id,
        formula_spec_refs=tuple(
            row.math_spec_id for row in bundle.component_closures
        ),
        implementation_version_pins=(
            bundle.execution_context.implementation_versions
        ),
        binding_profile_ref=bundle.execution_context.binding_profile_version,
        parameter_policy_snapshot_ref=bundle.parameter_policy_snapshot_ref,
        parameter_value_refs=bundle.parameter_value_refs,
        resolved_parameter_values=bundle.resolved_parameter_values,
        source_epoch_refs=bundle.source_epoch_refs,
        receipt_lineage_refs=(owner_action.receipt_ref,),
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
            scope_ref=bundle.execution_context.context_id,
            kill_active=kill_active,
            submit_disabled=submit_disabled,
            observed_at=now - timedelta(minutes=1),
            valid_until=now + valid_until_delta,
            policy_version="SAFETY-OWNER::CURRENT",
            causation_id="CAUSE::D::SAFETY",
            correlation_id="CORRELATION::D::SAFETY",
        ),
        computation_bundle_closure=bundle,
        owner_action_confirmation=owner_action,
        latency_profile_present=latency_profile,
    )


def _current_owner_registry(
    decision: object,
    *,
    kill_active: bool = False,
    submit_disabled: bool = False,
):
    bundle, base_registry = _audit_bundle_fixture()
    context = bundle.execution_context
    safety = ReadOnlyKillSubmitStateV1(
        state_ref=f"KILL-SUBMIT::READ-ONLY::{decision.request_id}",
        scope_ref=context.context_id,
        kill_active=kill_active,
        submit_disabled=submit_disabled,
        observed_at=context.as_of - timedelta(seconds=1),
        valid_until=context.as_of + timedelta(minutes=1),
        policy_version="SAFETY-OWNER::CURRENT",
        causation_id=f"CAUSE::D::SAFETY::{decision.request_id}",
        correlation_id=f"CORRELATION::D::SAFETY::{decision.request_id}",
    )
    predecessor_proposal = _transition_receipt_proposal(
        transition_id="T06",
        request_id=decision.request_id,
        principal_id=decision.principal_id,
        task_id=decision.task_id,
        capability_decision_ref=decision.decision_id,
        context_ref=context.context_id,
        snapshot_candidate_ref=f"SNAPSHOT-CANDIDATE::{decision.request_id}",
        candidate_version=context.input_version,
        expected_owner_state_ref="SVC1::CURRENT",
        effective_at=context.as_of,
    )
    owner_action = OwnerActionConfirmationReceiptV1(
        receipt_ref=f"OWNER-ACTION-RECEIPT::{decision.request_id}",
        owner_action_policy_ref="OWNER-ACTION-POLICY::CURRENT",
        state=OwnerActionConfirmationStateV1.CONFIRMED_CURRENT,
        principal_id=decision.principal_id,
        task_id=decision.task_id,
        capability_decision_ref=decision.decision_id,
        context_ref=context.context_id,
        observed_at=context.as_of - timedelta(seconds=1),
        valid_until=context.as_of + timedelta(minutes=1),
        causation_id=f"CAUSE::D::OWNER::{decision.request_id}",
        correlation_id=f"CORRELATION::D::OWNER::{decision.request_id}",
        predecessor_transition_id_or_explicit_absence="T06",
        predecessor_transition_receipt_ref_or_explicit_absence=(
            predecessor_proposal.record_id
        ),
        predecessor_transition_receipt_proposal_or_explicit_absence=(
            predecessor_proposal
        ),
    )
    clocks = base_registry.packets[0].clocks
    safety_packet = OwnerValuePacketV1(
        packet_id=f"PACKET::D::SAFETY::{decision.request_id}",
        owner_id="SafetyStateProjectionProtocolV1",
        packet_type="ReadOnlyKillSubmitStateV1",
        schema_id="ReadOnlyKillSubmitStateV1::SCHEMA",
        schema_version="1.0.0",
        context_id=context.context_id,
        scope=context.scope,
        source_epoch_id=context.source_epoch_id,
        input_version=context.input_version,
        clocks=clocks,
        ttl=timedelta(minutes=5),
        values={"safety.kill_submit_state": safety},
        authorized_binding_ids=(ST12D_SAFETY_BINDING_ID,),
        producer_receipt_id=safety.state_ref,
        producer_receipt_type="SafetyStateReceiptV1",
        source_state_and_claim_lineage="SafetyStateProjectionProtocolV1 -> D gate",
        revision=1,
    )
    owner_packet = OwnerValuePacketV1(
        packet_id=f"PACKET::D::OWNER::{decision.request_id}",
        owner_id="OwnerActionSemanticProtocolV1",
        packet_type="OwnerActionConfirmationReceiptV1",
        schema_id="OwnerActionConfirmationReceiptV1::SCHEMA",
        schema_version="1.0.0",
        context_id=context.context_id,
        scope=context.scope,
        source_epoch_id=context.source_epoch_id,
        input_version=context.input_version,
        clocks=clocks,
        ttl=timedelta(minutes=5),
        values={"owner_action.confirmation": owner_action},
        authorized_binding_ids=(ST12D_OWNER_ACTION_BINDING_ID,),
        producer_receipt_id=owner_action.receipt_ref,
        producer_receipt_type="OwnerActionConfirmationReceiptV1",
        source_state_and_claim_lineage="OwnerActionSemanticProtocolV1 -> D gate",
        revision=1,
    )
    return bundle, CanonicalOwnerPacketRegistryV1(
        (*base_registry.packets, safety_packet, owner_packet)
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
    expected_transitions = (
        ("T01", "CONTRACT_ONLY", "INELIGIBLE", "capability denied or identity/policy mismatch", ReasonCode.CAPABILITY_DENIED, "BLOCK", False),
        ("T02", "CONTRACT_ONLY", "ELIGIBLE_FOR_ALLOW_CANDIDACY_NO_EFFECT", "exact E decision, current inputs, kill clear", ReasonCode.CENTRAL_ADMISSION_PASS, "CONTINUE_NO_EFFECT", False),
        ("T03", "NOT_EVALUATED", "EVIDENCE_UNAVAILABLE", "F evidence unavailable", ReasonCode.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED, "BLOCK", False),
        ("T04", "NOT_EVALUATED", "BLOCKED", "policy/source/snapshot stale or conflicting", ReasonCode.POLICY_OR_SNAPSHOT_STALE, "REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE", False),
        ("T05", "NOT_EVALUATED", "BLOCKED", "kill active or submit disabled", ReasonCode.KILL_OR_SUBMIT_DISABLED, "BLOCK", False),
        ("T06", "NOT_EVALUATED", "OWNER_CONFIRMATION_REQUIRED", "all automated gates pass but exact owner action absent", ReasonCode.OWNER_CONFIRMATION_REQUIRED, "HOLD", False),
        ("T07", "OWNER_CONFIRMATION_REQUIRED", "ELIGIBLE_NOT_ACTIVATED", "exact owner confirmation packet is valid", ReasonCode.ALLOW_ELIGIBLE_NOT_ACTIVATED, "RETURN_DECISION_NO_EFFECT", True),
        ("T08", "ABSENT", "BUILT_IMMUTABLE", "all pinned inputs resolve and candidate builds", ReasonCode.SNAPSHOT_CANDIDATE_BUILT, "VALIDATE", False),
        ("T09", "BUILT_IMMUTABLE", "VALIDATED_NO_EFFECT", "schema, lineage, version, source, parameter, freshness and oracle checks pass", ReasonCode.SNAPSHOT_CANDIDATE_VALID, "RETURN_PROPOSAL_NO_EFFECT", False),
        ("T10", "BUILT_IMMUTABLE", "REJECTED", "any candidate validation fails", ReasonCode.SNAPSHOT_CANDIDATE_INVALID, "BLOCK", False),
        ("T11", "VALIDATED_NO_EFFECT", "STALE", "critical source/policy/evidence/kill state expires", ReasonCode.SNAPSHOT_STALE, "BLOCK_NEW_USE", False),
        ("T12", "VALIDATED_NO_EFFECT", "ROLLBACK_REQUIRED", "post-validation defect or conflict detected", ReasonCode.ROLLBACK_REQUIRED, "PROPOSE_PRIOR_CANDIDATE_NO_COMMIT", False),
        ("T13", "ROLLBACK_REQUIRED", "PROPOSED_PRIOR_IMMUTABLE_CANDIDATE", "prior candidate exists, validates and is not stale", ReasonCode.ROLLBACK_PROPOSAL_VALID, "RETURN_PROPOSAL_NO_EFFECT", False),
        ("T14", "ROLLBACK_REQUIRED", "BLOCKED_NO_VALID_PRIOR_CANDIDATE", "no valid prior candidate", ReasonCode.NO_VALID_ROLLBACK_TARGET, "BLOCK", False),
        ("T15", "CURRENT", "DRAINING_PINNED_IN_FLIGHT_ONLY", "retirement declared", ReasonCode.RETIREMENT_DRAIN, "NO_NEW_PINS", False),
        ("T16", "DRAINING_PINNED_IN_FLIGHT_ONLY", "RETIRED", "all in-flight references complete", ReasonCode.RETIRED, "NO_NEW_USE", False),
        ("T17", "ANY", "BLOCKED", "PRETRADE1 returns typed NO_TRADE", ReasonCode.NO_TRADE_REOPTIMIZATION_ROUTED, "ROUTE_TO_PRETRADE1_REOPTIMIZATION", False),
    )
    assert tuple(
        (
            row.transition_id,
            row.source_state,
            row.destination_state,
            row.trigger,
            row.reason_code,
            row.terminal_route,
            row.owner_confirmation_required,
        )
        for row in MODE_SNAPSHOT_TRANSITIONS
    ) == expected_transitions
    state_types = {
        **{state.value: state for state in ModeEligibilityState},
        **{state.value: state for state in AllowCandidateStateV1},
        **{state.value: state for state in SnapshotCandidateStateV1},
        **{state.value: state for state in SnapshotRollbackStateV1},
        **{state.value: state for state in SnapshotRetirementStateV1},
    }
    for rule in MODE_SNAPSHOT_TRANSITIONS:
        request_id = f"REQUEST::{rule.transition_id}"
        principal_id = "parameter_selector_agent"
        task_id = f"TASK::{rule.transition_id}"
        capability_ref = f"CAPABILITY::{rule.transition_id}"
        context_ref = f"CONTEXT::{rule.transition_id}"
        source_candidate_ref = (
            f"CURRENT-CANDIDATE::{rule.transition_id}"
            if rule.transition_id in {"T13", "T14"}
            else "EXPLICIT_ABSENCE"
        )
        source_candidate_version = (
            f"CURRENT-VERSION::{rule.transition_id}"
            if rule.transition_id in {"T13", "T14"}
            else "EXPLICIT_ABSENCE"
        )
        target_candidate_ref = f"CANDIDATE::{rule.transition_id}"
        target_candidate_version = f"VERSION::{rule.transition_id}"
        predecessor_transition_id = (
            "T06"
            if rule.transition_id == "T07"
            else "T12"
            if rule.transition_id in {"T13", "T14"}
            else None
        )
        predecessor_proposal = (
            _transition_receipt_proposal(
                transition_id=predecessor_transition_id,
                request_id=request_id,
                principal_id=principal_id,
                task_id=task_id,
                capability_decision_ref=capability_ref,
                context_ref=context_ref,
                snapshot_candidate_ref=(
                    target_candidate_ref
                    if rule.transition_id == "T07"
                    else source_candidate_ref
                ),
                candidate_version=(
                    target_candidate_version
                    if rule.transition_id == "T07"
                    else source_candidate_version
                ),
                expected_owner_state_ref="OWNER-STATE::UNCHANGED",
                effective_at=_audit_bundle_fixture()[0].execution_context.as_of,
            )
            if predecessor_transition_id is not None
            else None
        )
        predecessor_proposals = (
            (predecessor_proposal,) if predecessor_proposal is not None else ()
        )
        proposal = build_snapshot_transition_proposal(
            proposal_id=f"PROPOSAL::{rule.transition_id}",
            request_id=request_id,
            principal_id=principal_id,
            task_id=task_id,
            capability_decision_ref=capability_ref,
            context_ref=context_ref,
            source_candidate_ref_or_explicit_absence=source_candidate_ref,
            target_candidate_ref=target_candidate_ref,
            source_candidate_version_or_explicit_absence=source_candidate_version,
            target_candidate_version=target_candidate_version,
            transition_id=rule.transition_id,
            expected_owner_state_ref="OWNER-STATE::UNCHANGED",
            precondition_receipt_refs=(f"PRECONDITION::{rule.transition_id}",),
            predecessor_transition_receipt_proposals=predecessor_proposals,
            proposed_state=state_types[rule.destination_state],
            causation_id=f"CAUSE::{rule.transition_id}",
            correlation_id=f"CORRELATION::{rule.transition_id}",
        )
        assert (
            proposal.source_state,
            proposal.destination_state,
            proposal.primary_reason_code,
            proposal.predecessor_transition_receipt_refs,
            proposal.no_mutation_flag,
            proposal.no_activation_flag,
            proposal.no_order_release_flag,
        ) == (
            rule.source_state,
            rule.destination_state,
            rule.reason_code,
            tuple(row.record_id for row in predecessor_proposals),
            True,
            True,
            True,
        )
        mutations = (
            {"source_state": f"MUTATED::{rule.source_state}"},
            {"destination_state": f"MUTATED::{rule.destination_state}"},
            {
                "primary_reason_code": ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "typed_reason_codes": (ReasonCode.CONTRACT_OR_TYPE_INVALID,),
            },
            {
                "predecessor_transition_receipt_refs": (
                    ("MODE-SNAPSHOT-CONTROL::MUTATED::T05",)
                    if predecessor_proposals
                    else ("TRANSITION-RECEIPT::INAPPLICABLE",)
                )
            },
        )
        for mutation in mutations:
            with pytest.raises(ContractValidationError):
                replace(proposal, **mutation)
        if predecessor_proposals:
            predecessor = predecessor_proposals[0]
            mutated_predecessor = replace(
                predecessor,
                typed_payload=replace(
                    predecessor.typed_payload,
                    request_id=f"MUTATED::{request_id}",
                ),
            )
            with pytest.raises(ContractValidationError):
                replace(
                    proposal,
                    predecessor_transition_receipt_proposals=(
                        mutated_predecessor,
                    ),
                )


def test_policy_outcomes_are_typed_fail_closed_and_never_activate() -> None:
    cases = (
        (
            _inputs(
                evidence_state=(
                    ST12FEvidenceStateV1.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED
                )
            ),
            AllowCandidateStateV1.EVIDENCE_UNAVAILABLE,
            "T03",
            ("T03",),
            (ReasonCode.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED,),
        ),
        (
            _inputs(owner_confirmation=False),
            AllowCandidateStateV1.OWNER_CONFIRMATION_REQUIRED,
            "T06",
            ("T08", "T09", "T06"),
            (ReasonCode.OWNER_CONFIRMATION_REQUIRED,),
        ),
        (
            _inputs(),
            AllowCandidateStateV1.ELIGIBLE_NOT_ACTIVATED,
            "T07",
            ("T08", "T09", "T07"),
            (ReasonCode.ALLOW_ELIGIBLE_NOT_ACTIVATED,),
        ),
        (
            _inputs(kill_active=True),
            AllowCandidateStateV1.BLOCKED,
            "T05",
            ("T05",),
            (ReasonCode.KILL_OR_SUBMIT_DISABLED,),
        ),
        (
            _inputs(submit_disabled=True),
            AllowCandidateStateV1.BLOCKED,
            "T05",
            ("T05",),
            (ReasonCode.KILL_OR_SUBMIT_DISABLED,),
        ),
        (
            _inputs(latency_profile=False),
            AllowCandidateStateV1.BLOCKED,
            "T04",
            ("T04",),
            (
                ReasonCode.POLICY_OR_SNAPSHOT_STALE,
                ReasonCode.LATENCY_PROFILE_REQUIRED,
            ),
        ),
        (
            _inputs(
                evidence_state=ST12FEvidenceStateV1.EVIDENCE_REFERENCE_STALE
            ),
            AllowCandidateStateV1.BLOCKED,
            "T04",
            ("T04",),
            (
                ReasonCode.POLICY_OR_SNAPSHOT_STALE,
                ReasonCode.EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH,
            ),
        ),
        (
            _inputs(valid_until_delta=timedelta(minutes=-1)),
            AllowCandidateStateV1.BLOCKED,
            "T05",
            ("T05",),
            (
                ReasonCode.KILL_OR_SUBMIT_DISABLED,
                ReasonCode.KILL_SUBMIT_DISABLED_OR_SAFETY_BLOCK,
            ),
        ),
    )
    for (
        inputs,
        expected_state,
        expected_transition_id,
        expected_trace,
        expected_reasons,
    ) in cases:
        result = evaluate_mode_snapshot_candidate(inputs)
        decision = result.mode_snapshot_decision
        proposal = result.snapshot_transition_proposal
        assert decision.allow_candidate_state is expected_state
        assert decision.reason_codes == expected_reasons
        assert proposal.transition_id == expected_transition_id
        assert tuple(
            row.transition_id for row in result.executed_transition_trace.proposals
        ) == expected_trace
        assert result.executed_transition_trace.final_proposal is proposal
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
        if expected_state is not AllowCandidateStateV1.ELIGIBLE_NOT_ACTIVATED and (
            expected_state is not AllowCandidateStateV1.OWNER_CONFIRMATION_REQUIRED
        ):
            assert candidate is None
            assert decision.snapshot_candidate_state is SnapshotCandidateStateV1.ABSENT
    clear_inputs = _inputs()
    assert validate_current_kill_submit_state(
        clear_inputs.kill_submit_state,
        evaluated_at=clear_inputs.evaluated_at,
    ) == ()


def test_pretrade_no_trade_routes_before_any_d_body_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

        def resolve_mode_snapshot_preconstruction_gate(self, *_args: object):
            self.calls += 1
            raise AssertionError("D body executed after typed NO_TRADE")

        def enrich_mode_snapshot_candidate(self, *_args: object):
            self.calls += 1
            raise AssertionError("D enrichment executed after typed NO_TRADE")

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

    bundle, _base_registry = _audit_bundle_fixture()
    kill_context = bundle.execution_context
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

    _bundle, owner_registry = _current_owner_registry(
        kill_decision,
        kill_active=True,
    )

    class _KillBodyProbe:
        request_id = kill_decision.request_id
        operation_name = operation_id
        requested_at = kill_context.as_of
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

    current_resolver = CurrentModeSnapshotInputResolverV1(
        repo_root=Path(__file__).resolve().parents[3],
        owner_registry=owner_registry,
    )

    late_calls = 0

    def _forbid_enrichment(_self: object, *_args: object) -> object:
        nonlocal late_calls
        late_calls += 1
        raise AssertionError("late D owner/bundle resolution ran after T05")

    monkeypatch.setattr(
        CurrentModeSnapshotInputResolverV1,
        "enrich_mode_snapshot_candidate",
        _forbid_enrichment,
    )
    def _forbid_hotpath_file_read(*_args: object, **_kwargs: object) -> str:
        raise AssertionError("repository file read entered the T05 HOTPATH")

    monkeypatch.setattr(Path, "read_text", _forbid_hotpath_file_read)
    kill_service = QKUComputationControlPlaneV1(
        owner_registry,
        agent_capability_resolver=_KillAdmission(),
        mode_snapshot_input_resolver=current_resolver,
    )
    blocked_response = kill_service.submit_candidate_proposal(
        _KillBodyProbe()  # type: ignore[arg-type]
    )
    assert blocked_response.status is OperationStatusV1.BLOCKED
    assert late_calls == 0
    assert blocked_response.proposal.mode_snapshot_result is not None
    assert (
        blocked_response.proposal.mode_snapshot_result.snapshot_candidate_or_explicit_absence
        is None
    )
    assert blocked_response.proposal.mode_snapshot_result.mode_snapshot_decision.reason_codes == (
        ReasonCode.KILL_OR_SUBMIT_DISABLED,
    )
    assert tuple(
        row.transition_id
        for row in blocked_response.proposal.mode_snapshot_result.executed_transition_trace.proposals
    ) == ("T05",)


def test_non_d_public_contract_and_existing_source_owners_remain_bounded() -> None:
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
        IMPLEMENTED_OPERATION_IDS,
    )

    assert len(IMPLEMENTED_OPERATION_IDS) == 15
    assert {"compile_replay_paper_cohort", "register_replay_paper_result", "build_evidence_bundle"} <= set(IMPLEMENTED_OPERATION_IDS)
    assert set(IMPLEMENTED_OPERATION_IDS) == {
        name
        for name, member in vars(QKUComputationControlPlaneV1).items()
        if callable(member) and not name.startswith("_")
    }
    baseline = evaluate_mode_snapshot_candidate(_inputs())
    changed = evaluate_mode_snapshot_candidate(
        replace(
            _inputs(),
            owner_action_confirmation=replace(
                _inputs().owner_action_confirmation,
                state=OwnerActionConfirmationStateV1.ABSENT,
                predecessor_transition_id_or_explicit_absence="EXPLICIT_ABSENCE",
                predecessor_transition_receipt_ref_or_explicit_absence=(
                    "EXPLICIT_ABSENCE"
                ),
                predecessor_transition_receipt_proposal_or_explicit_absence=None,
            ),
        )
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
