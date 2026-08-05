"""Pure ST12-D mode eligibility and immutable snapshot-candidate policy.

This module proposes no-effect decisions only.  It owns no active pointer, mode
activation, ALLOW grant, evidence production, safety state, or order release.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from types import MappingProxyType
from typing import Mapping

from .errors import ContractValidationError, ReasonCode
from .models import (
    ActivationPreconditionStateV1,
    AllowCandidateStateV1,
    FormulaRuntimeSnapshotCandidateV1,
    ImplementationVersionPinV1,
    KillStateV1,
    ModeEligibilityState,
    ModeSnapshotCandidateProposalResultV1,
    ModeSnapshotDecisionV1,
    ModeSnapshotOwnerProjectionV1,
    OwnerActionConfirmationReceiptV1,
    ReadOnlyKillSubmitStateV1,
    ResolvedSnapshotParameterValueV1,
    SnapshotCandidateStateV1,
    SnapshotRetirementStateV1,
    SnapshotRollbackStateV1,
    SnapshotTransitionProposalV1,
    ST12FEvidenceReferenceV1,
    ST12FEvidenceStateV1,
    SubmitDisabledStateV1,
)
from .stack_resolver import RegisteredSnapshotComputationBundleV1


MODE_SNAPSHOT_CANDIDATE_KIND = "MODE_SNAPSHOT_CANDIDATE_V1"
PIN_POLICY_ID = "ST12D-IN-FLIGHT-PIN-POLICY-v1"
ROLLBACK_POLICY_ID = "ST12D-SNAPSHOT-CANDIDATE-ROLLBACK-v1"
EXPLICIT_ABSENCE = "EXPLICIT_ABSENCE"
NO_TRADE_ROUTE = "ROUTE_TO_PRETRADE1_REOPTIMIZATION"

D_REQUIRED_PIN_DIMENSIONS = (
    "formula_spec",
    "implementation_version",
    "binding_profile",
    "parameter_policy_snapshot",
    "resolved_parameter_values",
    "source_epochs",
    "readiness_projection",
    "pretrade_projection",
    "evidence_reference_state",
    "kill_state",
    "submit_disabled_state",
    "owner_action_policy",
)

D_MODE_STATE_REGISTRY: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
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
)


@dataclass(frozen=True, slots=True)
class ModeSnapshotTransitionRuleV1:
    transition_id: str
    source_state: str
    destination_state: str
    trigger: str
    reason_code: ReasonCode
    terminal_route: str
    owner_confirmation_required: bool

    def __post_init__(self) -> None:
        for value in (
            self.transition_id,
            self.source_state,
            self.destination_state,
            self.trigger,
            self.terminal_route,
        ):
            if not isinstance(value, str) or not value.strip():
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    "transition fields must be canonical nonempty text",
                )
        if type(self.reason_code) is not ReasonCode or type(
            self.owner_confirmation_required
        ) is not bool:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "transition reason and owner-confirmation flag must be typed",
            )


MODE_SNAPSHOT_TRANSITIONS = (
    ModeSnapshotTransitionRuleV1("T01", "CONTRACT_ONLY", "INELIGIBLE", "capability denied or identity/policy mismatch", ReasonCode.CAPABILITY_DENIED, "BLOCK", False),
    ModeSnapshotTransitionRuleV1("T02", "CONTRACT_ONLY", "ELIGIBLE_FOR_ALLOW_CANDIDACY_NO_EFFECT", "exact E decision, current inputs, kill clear", ReasonCode.CENTRAL_ADMISSION_PASS, "CONTINUE_NO_EFFECT", False),
    ModeSnapshotTransitionRuleV1("T03", "NOT_EVALUATED", "EVIDENCE_UNAVAILABLE", "F evidence unavailable", ReasonCode.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED, "BLOCK", False),
    ModeSnapshotTransitionRuleV1("T04", "NOT_EVALUATED", "BLOCKED", "policy/source/snapshot stale or conflicting", ReasonCode.POLICY_OR_SNAPSHOT_STALE, "REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE", False),
    ModeSnapshotTransitionRuleV1("T05", "NOT_EVALUATED", "BLOCKED", "kill active or submit disabled", ReasonCode.KILL_OR_SUBMIT_DISABLED, "BLOCK", False),
    ModeSnapshotTransitionRuleV1("T06", "NOT_EVALUATED", "OWNER_CONFIRMATION_REQUIRED", "all automated gates pass but exact owner action absent", ReasonCode.OWNER_CONFIRMATION_REQUIRED, "HOLD", False),
    ModeSnapshotTransitionRuleV1("T07", "OWNER_CONFIRMATION_REQUIRED", "ELIGIBLE_NOT_ACTIVATED", "exact owner confirmation packet is valid", ReasonCode.ALLOW_ELIGIBLE_NOT_ACTIVATED, "RETURN_DECISION_NO_EFFECT", True),
    ModeSnapshotTransitionRuleV1("T08", "ABSENT", "BUILT_IMMUTABLE", "all pinned inputs resolve and candidate builds", ReasonCode.SNAPSHOT_CANDIDATE_BUILT, "VALIDATE", False),
    ModeSnapshotTransitionRuleV1("T09", "BUILT_IMMUTABLE", "VALIDATED_NO_EFFECT", "schema, lineage, version, source, parameter, freshness and oracle checks pass", ReasonCode.SNAPSHOT_CANDIDATE_VALID, "RETURN_PROPOSAL_NO_EFFECT", False),
    ModeSnapshotTransitionRuleV1("T10", "BUILT_IMMUTABLE", "REJECTED", "any candidate validation fails", ReasonCode.SNAPSHOT_CANDIDATE_INVALID, "BLOCK", False),
    ModeSnapshotTransitionRuleV1("T11", "VALIDATED_NO_EFFECT", "STALE", "critical source/policy/evidence/kill state expires", ReasonCode.SNAPSHOT_STALE, "BLOCK_NEW_USE", False),
    ModeSnapshotTransitionRuleV1("T12", "VALIDATED_NO_EFFECT", "ROLLBACK_REQUIRED", "post-validation defect or conflict detected", ReasonCode.ROLLBACK_REQUIRED, "PROPOSE_PRIOR_CANDIDATE_NO_COMMIT", False),
    ModeSnapshotTransitionRuleV1("T13", "ROLLBACK_REQUIRED", "PROPOSED_PRIOR_IMMUTABLE_CANDIDATE", "prior candidate exists, validates and is not stale", ReasonCode.ROLLBACK_PROPOSAL_VALID, "RETURN_PROPOSAL_NO_EFFECT", False),
    ModeSnapshotTransitionRuleV1("T14", "ROLLBACK_REQUIRED", "BLOCKED_NO_VALID_PRIOR_CANDIDATE", "no valid prior candidate", ReasonCode.NO_VALID_ROLLBACK_TARGET, "BLOCK", False),
    ModeSnapshotTransitionRuleV1("T15", "CURRENT", "DRAINING_PINNED_IN_FLIGHT_ONLY", "retirement declared", ReasonCode.RETIREMENT_DRAIN, "NO_NEW_PINS", False),
    ModeSnapshotTransitionRuleV1("T16", "DRAINING_PINNED_IN_FLIGHT_ONLY", "RETIRED", "all in-flight references complete", ReasonCode.RETIRED, "NO_NEW_USE", False),
    ModeSnapshotTransitionRuleV1("T17", "ANY", "BLOCKED", "PRETRADE1 returns typed NO_TRADE", ReasonCode.NO_TRADE_REOPTIMIZATION_ROUTED, NO_TRADE_ROUTE, False),
)

TRANSITION_BY_ID: Mapping[str, ModeSnapshotTransitionRuleV1] = MappingProxyType(
    {row.transition_id: row for row in MODE_SNAPSHOT_TRANSITIONS}
)


def build_snapshot_transition_proposal(
    *,
    proposal_id: str,
    request_id: str,
    principal_id: str,
    task_id: str,
    capability_decision_ref: str,
    context_ref: str,
    source_candidate_ref_or_explicit_absence: str,
    target_candidate_ref: str,
    source_candidate_version_or_explicit_absence: str,
    target_candidate_version: str,
    transition_id: str,
    expected_owner_state_ref: str,
    precondition_receipt_refs: tuple[str, ...],
    predecessor_transition_receipt_proposals: tuple[object, ...] = (),
    proposed_state: (
        ModeEligibilityState
        | AllowCandidateStateV1
        | SnapshotCandidateStateV1
        | SnapshotRollbackStateV1
        | SnapshotRetirementStateV1
    ),
    diagnostic_reason_codes: tuple[ReasonCode, ...] = (),
    causation_id: str,
    correlation_id: str,
) -> SnapshotTransitionProposalV1:
    """Join every runtime proposal to the one frozen transition registry."""

    try:
        rule = TRANSITION_BY_ID[transition_id]
    except KeyError as exc:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"unknown frozen D transition: {transition_id}",
        ) from exc
    if not isinstance(predecessor_transition_receipt_proposals, tuple):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "predecessor receipt proposals must be an immutable tuple",
        )
    predecessor_transition_receipt_refs = tuple(
        getattr(row, "record_id", "")
        for row in predecessor_transition_receipt_proposals
    )
    diagnostics = tuple(
        reason
        for reason in dict.fromkeys(diagnostic_reason_codes)
        if reason is not rule.reason_code
    )
    return SnapshotTransitionProposalV1(
        proposal_id=proposal_id,
        request_id=request_id,
        principal_id=principal_id,
        task_id=task_id,
        capability_decision_ref=capability_decision_ref,
        context_ref=context_ref,
        source_candidate_ref_or_explicit_absence=(
            source_candidate_ref_or_explicit_absence
        ),
        target_candidate_ref=target_candidate_ref,
        source_candidate_version_or_explicit_absence=(
            source_candidate_version_or_explicit_absence
        ),
        target_candidate_version=target_candidate_version,
        transition_id=transition_id,
        source_state=rule.source_state,
        destination_state=rule.destination_state,
        expected_owner_state_ref=expected_owner_state_ref,
        precondition_receipt_refs=precondition_receipt_refs,
        predecessor_transition_receipt_refs=(
            predecessor_transition_receipt_refs
        ),
        predecessor_transition_receipt_proposals=(
            predecessor_transition_receipt_proposals
        ),
        proposed_state=proposed_state,
        primary_reason_code=rule.reason_code,
        diagnostic_reason_codes=diagnostics,
        typed_reason_codes=(rule.reason_code, *diagnostics),
        owner_confirmation_required=rule.owner_confirmation_required,
        causation_id=causation_id,
        correlation_id=correlation_id,
    )


@dataclass(frozen=True, slots=True)
class ModeSnapshotPreconstructionGateV1:
    """Minimal exact state allowed before T05/T03 adjudication."""

    request_id: str
    principal_id: str
    task_id: str
    current_agent_id: str
    capability_decision_ref: str
    context_ref: str
    current_mode: str
    requested_mode: str
    candidate_version: str
    evaluated_at: datetime
    expires_at: datetime
    causation_id: str
    correlation_id: str
    receipt_lineage_refs: tuple[str, ...]
    source_epoch_refs: tuple[str, ...]
    evidence_reference: ST12FEvidenceReferenceV1
    kill_submit_state: ReadOnlyKillSubmitStateV1

    def __post_init__(self) -> None:
        for name in (
            "request_id",
            "principal_id",
            "task_id",
            "current_agent_id",
            "capability_decision_ref",
            "context_ref",
            "current_mode",
            "requested_mode",
            "candidate_version",
            "causation_id",
            "correlation_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    "preconstruction gate identities must be canonical nonempty text",
                )
        for name in ("receipt_lineage_refs", "source_epoch_refs"):
            value = getattr(self, name)
            if (
                not isinstance(value, tuple)
                or not value
                or any(not isinstance(item, str) or not item for item in value)
                or len(value) != len(set(value))
            ):
                raise ContractValidationError(
                    ReasonCode.INPUT_PACKET_MISMATCH,
                    f"{name} must prove the exact consumed early-gate packet",
                )
        if (
            type(self.evidence_reference) is not ST12FEvidenceReferenceV1
            or type(self.kill_submit_state) is not ReadOnlyKillSubmitStateV1
            or self.kill_submit_state.scope_ref != self.context_ref
            or self.kill_submit_state.state_ref not in self.receipt_lineage_refs
        ):
            raise ContractValidationError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "preconstruction gate does not bind the exact safety/evidence state",
            )
        for name in ("evaluated_at", "expires_at"):
            value = getattr(self, name)
            if (
                not isinstance(value, datetime)
                or value.tzinfo is None
                or value.utcoffset() is None
                or value.utcoffset().total_seconds() != 0
            ):
                raise ContractValidationError(
                    ReasonCode.CLOCK_DOMAIN_MISMATCH,
                    f"{name} must be an aware UTC event timestamp",
                )
        if self.evaluated_at > self.expires_at:
            raise ContractValidationError(
                ReasonCode.POLICY_OR_SNAPSHOT_STALE,
                "preconstruction gate expiry precedes evaluation",
            )


@dataclass(frozen=True, slots=True)
class ModeSnapshotCandidateInputsV1:
    """Exact already-resolved inputs consumed after central E admission."""

    request_id: str
    principal_id: str
    task_id: str
    current_agent_id: str
    capability_decision_ref: str
    computation_bundle_ref: str
    context_ref: str
    formula_spec_refs: tuple[str, ...]
    implementation_version_pins: tuple[ImplementationVersionPinV1, ...]
    binding_profile_ref: str
    parameter_policy_snapshot_ref: str
    parameter_value_refs: tuple[str, ...]
    resolved_parameter_values: tuple[ResolvedSnapshotParameterValueV1, ...]
    source_epoch_refs: tuple[str, ...]
    receipt_lineage_refs: tuple[str, ...]
    readiness_state_ref: str
    pretrade_state_ref: str
    owner_action_policy_ref: str
    current_mode: str
    requested_mode: str
    expected_owner_state_ref: str
    candidate_version: str
    created_at: datetime
    evaluated_at: datetime
    expires_at: datetime
    causation_id: str
    correlation_id: str
    evidence_reference: ST12FEvidenceReferenceV1
    kill_submit_state: ReadOnlyKillSubmitStateV1
    computation_bundle_closure: RegisteredSnapshotComputationBundleV1
    owner_action_confirmation: OwnerActionConfirmationReceiptV1
    latency_measurement_ref_or_explicit_absence: str = EXPLICIT_ABSENCE
    latency_profile_present: bool = False

    def __post_init__(self) -> None:
        text_fields = (
            "request_id",
            "principal_id",
            "task_id",
            "current_agent_id",
            "capability_decision_ref",
            "computation_bundle_ref",
            "context_ref",
            "binding_profile_ref",
            "parameter_policy_snapshot_ref",
            "readiness_state_ref",
            "pretrade_state_ref",
            "owner_action_policy_ref",
            "current_mode",
            "requested_mode",
            "expected_owner_state_ref",
            "candidate_version",
            "causation_id",
            "correlation_id",
            "latency_measurement_ref_or_explicit_absence",
        )
        if any(
            not isinstance(getattr(self, name), str)
            or not getattr(self, name).strip()
            for name in text_fields
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "mode snapshot inputs require canonical resolved references",
            )
        for name in (
            "formula_spec_refs",
            "parameter_value_refs",
            "source_epoch_refs",
            "receipt_lineage_refs",
        ):
            value = getattr(self, name)
            if (
                not isinstance(value, tuple)
                or not value
                or any(not isinstance(item, str) or not item.strip() for item in value)
                or len(value) != len(set(value))
            ):
                raise ContractValidationError(
                    ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                    f"{name} must be a nonempty unique immutable tuple",
                )
        if (
            not isinstance(self.implementation_version_pins, tuple)
            or not self.implementation_version_pins
            or any(
                type(pin) is not ImplementationVersionPinV1
                for pin in self.implementation_version_pins
            )
            or type(self.evidence_reference) is not ST12FEvidenceReferenceV1
            or type(self.kill_submit_state) is not ReadOnlyKillSubmitStateV1
            or type(self.computation_bundle_closure)
            is not RegisteredSnapshotComputationBundleV1
            or type(self.owner_action_confirmation)
            is not OwnerActionConfirmationReceiptV1
            or not isinstance(self.resolved_parameter_values, tuple)
            or not self.resolved_parameter_values
            or any(
                type(row) is not ResolvedSnapshotParameterValueV1
                for row in self.resolved_parameter_values
            )
        ):
            raise ContractValidationError(
                ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                "mode snapshot inputs require exact immutable owner pins",
            )
        for name in ("latency_profile_present",):
            if type(getattr(self, name)) is not bool:
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    f"{name} must be an exact boolean",
                )
        for name in ("created_at", "evaluated_at", "expires_at"):
            value = getattr(self, name)
            if (
                not isinstance(value, datetime)
                or value.tzinfo is None
                or value.utcoffset() is None
                or value.utcoffset().total_seconds() != 0
            ):
                raise ContractValidationError(
                    ReasonCode.CLOCK_DOMAIN_MISMATCH,
                    f"{name} must be an aware UTC event timestamp",
                )
        if not self.created_at <= self.evaluated_at <= self.expires_at:
            raise ContractValidationError(
                ReasonCode.POLICY_OR_SNAPSHOT_STALE,
                "candidate event times are not current and ordered",
            )
        bundle = self.computation_bundle_closure
        owner_action = self.owner_action_confirmation
        if (
            self.computation_bundle_ref != bundle.bundle_ref
            or self.context_ref != bundle.execution_context.context_id
            or self.formula_spec_refs
            != tuple(row.math_spec_id for row in bundle.component_closures)
            or self.implementation_version_pins
            != bundle.execution_context.implementation_versions
            or self.parameter_policy_snapshot_ref
            != bundle.parameter_policy_snapshot_ref
            or self.parameter_value_refs != bundle.parameter_value_refs
            or self.resolved_parameter_values != bundle.resolved_parameter_values
            or self.parameter_value_refs
            != tuple(
                row.resolved_value_ref for row in self.resolved_parameter_values
            )
            or self.source_epoch_refs != bundle.source_epoch_refs
            or self.owner_action_policy_ref != owner_action.owner_action_policy_ref
            or owner_action.receipt_ref not in self.receipt_lineage_refs
            or bundle.preflight_receipt_ref not in self.receipt_lineage_refs
        ):
            raise ContractValidationError(
                ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                "mode snapshot inputs do not bind the exact bundle and owner receipts",
            )

    @property
    def all_four_computability_dimensions_closed(self) -> bool:
        """Derived closure fact; callers cannot supply this authority state."""

        return self.computation_bundle_closure.all_four_dimensions_closed

    @property
    def owner_confirmation_present(self) -> bool:
        """Derived identity/currentness fact from the canonical owner receipt."""

        return self.owner_action_confirmation.is_current_for(
            evaluated_at=self.evaluated_at,
            principal_id=self.principal_id,
            task_id=self.task_id,
            capability_decision_ref=self.capability_decision_ref,
            context_ref=self.context_ref,
            request_id=self.request_id,
            snapshot_candidate_ref=f"SNAPSHOT-CANDIDATE::{self.request_id}",
            candidate_version=self.candidate_version,
        )


@dataclass(frozen=True, slots=True)
class PriorSnapshotCandidateV1:
    candidate: FormulaRuntimeSnapshotCandidateV1
    candidate_version: str
    retirement_state: SnapshotRetirementStateV1
    independently_valid: bool
    all_required_pins_current: bool

    def __post_init__(self) -> None:
        if type(self.candidate) is not FormulaRuntimeSnapshotCandidateV1 or type(
            self.retirement_state
        ) is not SnapshotRetirementStateV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "rollback inventory must contain exact immutable candidate rows",
            )
        if not isinstance(self.candidate_version, str) or not self.candidate_version.strip():
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "rollback inventory requires the exact candidate version identity",
            )
        if type(self.independently_valid) is not bool or type(
            self.all_required_pins_current
        ) is not bool:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "rollback validity fields must be exact booleans",
            )


def pre_f_unavailable_reference(
    *,
    observed_at: datetime,
    valid_until: datetime,
    causation_id: str,
    correlation_id: str,
) -> ST12FEvidenceReferenceV1:
    """Return the truthful current pre-F state without synthesizing evidence."""

    return ST12FEvidenceReferenceV1(
        evidence_state=(
            ST12FEvidenceStateV1.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED
        ),
        evidence_ref=EXPLICIT_ABSENCE,
        lane=EXPLICIT_ABSENCE,
        dataset_grade_ref=EXPLICIT_ABSENCE,
        venue_semantic_binding_ref=EXPLICIT_ABSENCE,
        cross_venue_equivalence_ref=EXPLICIT_ABSENCE,
        observed_at=observed_at,
        valid_until=valid_until,
        policy_version="ST12F-INTERFACE-ONLY-v1",
        causation_id=causation_id,
        correlation_id=correlation_id,
        )


def evaluate_mode_snapshot_preconstruction_gate(
    gate: ModeSnapshotPreconstructionGateV1,
    *,
    latency_measurement_ref: str,
) -> ModeSnapshotCandidateProposalResultV1 | None:
    """Return T05/T03 before any candidate-enrichment dependency can run."""

    if type(gate) is not ModeSnapshotPreconstructionGateV1:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "early D adjudication requires the exact preconstruction gate",
        )
    safety_reasons = validate_current_kill_submit_state(
        gate.kill_submit_state,
        evaluated_at=gate.evaluated_at,
    )
    evidence_reason = _evidence_reason(
        gate.evidence_reference,
        evaluated_at=gate.evaluated_at,
    )
    if safety_reasons:
        rule = TRANSITION_BY_ID["T05"]
        diagnostic_reasons = tuple(
            reason for reason in safety_reasons if reason is not rule.reason_code
        )
        eligibility = ModeEligibilityState.INELIGIBLE
        allow_state = AllowCandidateStateV1.BLOCKED
        owner_route = "EXISTING_SAFETY_OWNER_REVALIDATION"
    elif evidence_reason is not None:
        rule = TRANSITION_BY_ID[
            "T03"
            if evidence_reason is ReasonCode.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED
            else "T04"
        ]
        diagnostic_reasons = (
            () if evidence_reason is rule.reason_code else (evidence_reason,)
        )
        eligibility = ModeEligibilityState.ELIGIBLE_FOR_ALLOW_CANDIDACY_NO_EFFECT
        allow_state = (
            AllowCandidateStateV1.EVIDENCE_UNAVAILABLE
            if rule.transition_id == "T03"
            else AllowCandidateStateV1.BLOCKED
        )
        owner_route = "ST12F_EVIDENCE_OWNER_REVALIDATION"
    else:
        return None
    reasons = (rule.reason_code, *diagnostic_reasons)
    decision = ModeSnapshotDecisionV1(
        decision_id=f"MODE-SNAPSHOT-DECISION::{gate.request_id}",
        request_id=gate.request_id,
        task_id=gate.task_id,
        principal_id=gate.principal_id,
        current_agent_id=gate.current_agent_id,
        capability_decision_ref=gate.capability_decision_ref,
        computation_bundle_ref=EXPLICIT_ABSENCE,
        context_ref=gate.context_ref,
        parameter_policy_snapshot_ref=EXPLICIT_ABSENCE,
        receipt_lineage_refs=gate.receipt_lineage_refs,
        readiness_state_ref=EXPLICIT_ABSENCE,
        pretrade_state_ref=EXPLICIT_ABSENCE,
        evidence_state_ref=gate.evidence_reference.evidence_ref,
        kill_state_ref=gate.kill_submit_state.state_ref,
        submit_disabled_state_ref=gate.kill_submit_state.state_ref,
        owner_action_policy_ref=EXPLICIT_ABSENCE,
        current_mode=gate.current_mode,
        requested_mode=gate.requested_mode,
        mode_eligibility_state=eligibility,
        allow_candidate_state=allow_state,
        snapshot_candidate_state=SnapshotCandidateStateV1.ABSENT,
        activation_precondition_state=(
            ActivationPreconditionStateV1.PRECONDITIONS_INCOMPLETE
        ),
        rollback_state=SnapshotRollbackStateV1.NONE,
        rollback_target_ref_or_explicit_absence=EXPLICIT_ABSENCE,
        pin_policy_ref=PIN_POLICY_ID,
        stale_state="CURRENT",
        expires_at=gate.expires_at,
        retirement_state=SnapshotRetirementStateV1.CURRENT,
        implementation_pins=(),
        source_epoch_refs=gate.source_epoch_refs,
        reason_codes=reasons,
        fallback_route=rule.terminal_route,
        owner_review_route=owner_route,
        no_trade_route=NO_TRADE_ROUTE,
        latency_measurement_ref_or_explicit_absence=latency_measurement_ref,
    )
    proposal = build_snapshot_transition_proposal(
        proposal_id=f"SNAPSHOT-TRANSITION::{gate.request_id}",
        request_id=gate.request_id,
        principal_id=gate.principal_id,
        task_id=gate.task_id,
        capability_decision_ref=gate.capability_decision_ref,
        context_ref=gate.context_ref,
        source_candidate_ref_or_explicit_absence=EXPLICIT_ABSENCE,
        target_candidate_ref=EXPLICIT_ABSENCE,
        source_candidate_version_or_explicit_absence=EXPLICIT_ABSENCE,
        target_candidate_version=gate.candidate_version,
        transition_id=rule.transition_id,
        expected_owner_state_ref=EXPLICIT_ABSENCE,
        precondition_receipt_refs=gate.receipt_lineage_refs,
        proposed_state=allow_state,
        diagnostic_reason_codes=diagnostic_reasons,
        causation_id=gate.causation_id,
        correlation_id=gate.correlation_id,
    )
    return ModeSnapshotCandidateProposalResultV1(
        snapshot_candidate_or_explicit_absence=None,
        mode_snapshot_decision=decision,
        snapshot_transition_proposal=proposal,
        control_receipt_refs=(),
    )


def validate_current_kill_submit_state(
    packet: ReadOnlyKillSubmitStateV1,
    *,
    evaluated_at: datetime,
) -> tuple[ReasonCode, ...]:
    """Validate the current safety-owner packet before any candidate-body work."""

    if type(packet) is not ReadOnlyKillSubmitStateV1 or (
        not isinstance(evaluated_at, datetime)
        or evaluated_at.tzinfo is None
        or evaluated_at.utcoffset() is None
        or evaluated_at.utcoffset().total_seconds() != 0
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "kill/submit admission requires an exact packet and aware UTC time",
        )
    if evaluated_at < packet.observed_at or evaluated_at > packet.valid_until:
        return (ReasonCode.KILL_SUBMIT_DISABLED_OR_SAFETY_BLOCK,)
    if packet.kill_active or packet.submit_disabled:
        return (ReasonCode.KILL_OR_SUBMIT_DISABLED,)
    return ()


def _evidence_reason(
    reference: ST12FEvidenceReferenceV1,
    *,
    evaluated_at: datetime,
) -> ReasonCode | None:
    if reference.evidence_state is (
        ST12FEvidenceStateV1.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED
    ):
        return ReasonCode.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED
    if (
        reference.evidence_state
        is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
        or evaluated_at < reference.observed_at
        or evaluated_at > reference.valid_until
    ):
        return (
            ReasonCode.EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH
        )
    return None


def validate_candidate_pin_identity(
    candidate: FormulaRuntimeSnapshotCandidateV1,
    inputs: ModeSnapshotCandidateInputsV1,
) -> tuple[ReasonCode, ...]:
    """Validate exact D operation pins without creating a universal evidence lock."""

    if (
        type(candidate) is not FormulaRuntimeSnapshotCandidateV1
        or type(inputs) is not ModeSnapshotCandidateInputsV1
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "pin identity validation requires exact candidate and input contracts",
        )
    comparisons = (
        (candidate.computation_bundle_ref, inputs.computation_bundle_ref),
        (candidate.context_ref, inputs.context_ref),
        (candidate.formula_spec_refs, inputs.formula_spec_refs),
        (candidate.implementation_version_pins, inputs.implementation_version_pins),
        (candidate.binding_profile_ref, inputs.binding_profile_ref),
        (candidate.parameter_policy_snapshot_ref, inputs.parameter_policy_snapshot_ref),
        (candidate.parameter_value_refs, inputs.parameter_value_refs),
        (candidate.source_epoch_refs, inputs.source_epoch_refs),
        (candidate.readiness_state_ref, inputs.readiness_state_ref),
        (candidate.pretrade_state_ref, inputs.pretrade_state_ref),
        (candidate.evidence_state_ref, inputs.evidence_reference.evidence_ref),
        (candidate.kill_state_ref, inputs.kill_submit_state.state_ref),
        (candidate.submit_disabled_state_ref, inputs.kill_submit_state.state_ref),
        (inputs.kill_submit_state.scope_ref, inputs.context_ref),
    )
    reasons: list[ReasonCode] = []
    if any(actual != expected for actual, expected in comparisons):
        reasons.append(ReasonCode.SNAPSHOT_PIN_CONFLICT)
    if tuple(pin.math_spec_id for pin in candidate.implementation_version_pins) != (
        candidate.formula_spec_refs
    ):
        reasons.append(ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID)
    return tuple(dict.fromkeys(reasons))


def construct_snapshot_candidate(
    inputs: ModeSnapshotCandidateInputsV1,
) -> FormulaRuntimeSnapshotCandidateV1:
    """Execute T08 by constructing one immutable, still-unvalidated candidate."""

    return FormulaRuntimeSnapshotCandidateV1(
        snapshot_candidate_id=f"SNAPSHOT-CANDIDATE::{inputs.request_id}",
        request_id=inputs.request_id,
        principal_id=inputs.principal_id,
        task_id=inputs.task_id,
        capability_decision_ref=inputs.capability_decision_ref,
        computation_bundle_ref=inputs.computation_bundle_ref,
        context_ref=inputs.context_ref,
        formula_spec_refs=inputs.formula_spec_refs,
        implementation_version_pins=inputs.implementation_version_pins,
        binding_profile_ref=inputs.binding_profile_ref,
        parameter_policy_snapshot_ref=inputs.parameter_policy_snapshot_ref,
        parameter_value_refs=inputs.parameter_value_refs,
        source_epoch_refs=inputs.source_epoch_refs,
        receipt_lineage_refs=inputs.receipt_lineage_refs,
        readiness_state_ref=inputs.readiness_state_ref,
        pretrade_state_ref=inputs.pretrade_state_ref,
        evidence_state_ref=inputs.evidence_reference.evidence_ref,
        kill_state_ref=inputs.kill_submit_state.state_ref,
        submit_disabled_state_ref=inputs.kill_submit_state.state_ref,
        created_at=inputs.created_at,
        evaluated_at=inputs.evaluated_at,
        expires_at=inputs.expires_at,
        stale_at=None,
        candidate_state=SnapshotCandidateStateV1.BUILT_IMMUTABLE,
        reason_codes=(ReasonCode.SNAPSHOT_CANDIDATE_BUILT,),
        fallback_route="VALIDATE",
        owner_review_route="EXISTING_OWNER_ACTION_REVIEW",
    )


def validate_snapshot_candidate(
    candidate: FormulaRuntimeSnapshotCandidateV1,
    inputs: ModeSnapshotCandidateInputsV1,
) -> FormulaRuntimeSnapshotCandidateV1:
    """Execute T09 or T10 without mutating the built candidate."""

    if (
        type(candidate) is not FormulaRuntimeSnapshotCandidateV1
        or type(inputs) is not ModeSnapshotCandidateInputsV1
        or candidate.candidate_state is not SnapshotCandidateStateV1.BUILT_IMMUTABLE
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "snapshot validation requires one exact BUILT_IMMUTABLE candidate",
        )
    reasons = validate_candidate_pin_identity(candidate, inputs)
    if reasons:
        return replace(
            candidate,
            candidate_state=SnapshotCandidateStateV1.REJECTED,
            reason_codes=(ReasonCode.SNAPSHOT_CANDIDATE_INVALID, *reasons),
            fallback_route="BLOCK",
        )
    return replace(
        candidate,
        candidate_state=SnapshotCandidateStateV1.VALIDATED_NO_EFFECT,
        reason_codes=(ReasonCode.SNAPSHOT_CANDIDATE_VALID,),
        fallback_route="RETURN_PROPOSAL_NO_EFFECT",
    )


def build_snapshot_candidate(
    inputs: ModeSnapshotCandidateInputsV1,
) -> FormulaRuntimeSnapshotCandidateV1:
    """Construct and validate one candidate through executable T08 then T09/T10."""

    return validate_snapshot_candidate(construct_snapshot_candidate(inputs), inputs)


def _preconstruction_decision_state(
    inputs: ModeSnapshotCandidateInputsV1,
) -> tuple[
    ModeEligibilityState,
    AllowCandidateStateV1,
    ActivationPreconditionStateV1,
    ReasonCode,
    str,
    str,
] | None:
    safety_reasons = validate_current_kill_submit_state(
        inputs.kill_submit_state,
        evaluated_at=inputs.evaluated_at,
    )
    if safety_reasons:
        return (
            ModeEligibilityState.INELIGIBLE,
            AllowCandidateStateV1.BLOCKED,
            ActivationPreconditionStateV1.PRECONDITIONS_INCOMPLETE,
            safety_reasons[0],
            "BLOCK",
            "EXISTING_SAFETY_OWNER_REVALIDATION",
        )
    evidence_reason = _evidence_reason(
        inputs.evidence_reference,
        evaluated_at=inputs.evaluated_at,
    )
    if evidence_reason is not None:
        return (
            ModeEligibilityState.ELIGIBLE_FOR_ALLOW_CANDIDACY_NO_EFFECT,
            (
                AllowCandidateStateV1.EVIDENCE_UNAVAILABLE
                if evidence_reason is ReasonCode.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED
                else AllowCandidateStateV1.BLOCKED
            ),
            ActivationPreconditionStateV1.PRECONDITIONS_INCOMPLETE,
            evidence_reason,
            "BLOCK",
            "ST12F_EVIDENCE_OWNER_REVALIDATION",
        )
    if (
        not inputs.all_four_computability_dimensions_closed
        or not inputs.latency_profile_present
    ):
        reason = (
            ReasonCode.LATENCY_PROFILE_REQUIRED
            if not inputs.latency_profile_present
            else ReasonCode.DEPENDENCY_OR_COMPUTABILITY_INCOMPLETE
        )
        return (
            ModeEligibilityState.INELIGIBLE,
            AllowCandidateStateV1.BLOCKED,
            ActivationPreconditionStateV1.PRECONDITIONS_INCOMPLETE,
            reason,
            "REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
            "CURRENT_INPUT_OWNER_REVALIDATION",
        )
    return None


def _postconstruction_decision_state(
    inputs: ModeSnapshotCandidateInputsV1,
    candidate: FormulaRuntimeSnapshotCandidateV1,
) -> tuple[
    ModeEligibilityState,
    AllowCandidateStateV1,
    ActivationPreconditionStateV1,
    ReasonCode,
    str,
    str,
]:
    if candidate.candidate_state is SnapshotCandidateStateV1.REJECTED:
        return (
            ModeEligibilityState.INELIGIBLE,
            AllowCandidateStateV1.BLOCKED,
            ActivationPreconditionStateV1.PRECONDITIONS_INCOMPLETE,
            ReasonCode.SNAPSHOT_CANDIDATE_INVALID,
            "BLOCK",
            "CURRENT_INPUT_OWNER_REVALIDATION",
        )
    if not inputs.owner_confirmation_present:
        return (
            ModeEligibilityState.ELIGIBLE_FOR_ALLOW_CANDIDACY_NO_EFFECT,
            AllowCandidateStateV1.OWNER_CONFIRMATION_REQUIRED,
            ActivationPreconditionStateV1.PRECONDITIONS_SATISFIED_HELD,
            ReasonCode.OWNER_CONFIRMATION_REQUIRED,
            "HOLD",
            "EXISTING_OWNER_ACTION_REVIEW",
        )
    return (
        ModeEligibilityState.ELIGIBLE_FOR_ALLOW_CANDIDACY_NO_EFFECT,
        AllowCandidateStateV1.ELIGIBLE_NOT_ACTIVATED,
        ActivationPreconditionStateV1.NOT_AUTHORIZED_D_HOLD,
        ReasonCode.ALLOW_ELIGIBLE_NOT_ACTIVATED,
        "RETURN_DECISION_NO_EFFECT",
        "OWNER_CONFIRMED_NO_ACTIVATION",
    )


def _transition_for_decision(
    allow_state: AllowCandidateStateV1,
    reason: ReasonCode,
) -> ModeSnapshotTransitionRuleV1:
    if reason is ReasonCode.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED:
        return TRANSITION_BY_ID["T03"]
    if reason in {
        ReasonCode.KILL_OR_SUBMIT_DISABLED,
        ReasonCode.KILL_SUBMIT_DISABLED_OR_SAFETY_BLOCK,
    }:
        return TRANSITION_BY_ID["T05"]
    if allow_state is AllowCandidateStateV1.BLOCKED:
        return TRANSITION_BY_ID["T04"]
    if allow_state is AllowCandidateStateV1.OWNER_CONFIRMATION_REQUIRED:
        return TRANSITION_BY_ID["T06"]
    return TRANSITION_BY_ID["T07"]


def evaluate_mode_snapshot_candidate(
    inputs: ModeSnapshotCandidateInputsV1,
) -> ModeSnapshotCandidateProposalResultV1:
    """Build and evaluate one immutable candidate with zero state mutation."""

    if type(inputs) is not ModeSnapshotCandidateInputsV1:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "mode snapshot evaluation requires exact typed resolved inputs",
        )
    decision_state = _preconstruction_decision_state(inputs)
    candidate = None
    if decision_state is None:
        candidate = build_snapshot_candidate(inputs)
        decision_state = _postconstruction_decision_state(inputs, candidate)
    (
        eligibility,
        allow_state,
        activation_state,
        decision_reason,
        route,
        owner_route,
    ) = decision_state
    rule = (
        TRANSITION_BY_ID["T10"]
        if candidate is not None
        and candidate.candidate_state is SnapshotCandidateStateV1.REJECTED
        else _transition_for_decision(allow_state, decision_reason)
    )
    snapshot_for_result = (
        candidate
        if candidate is not None
        and candidate.candidate_state is SnapshotCandidateStateV1.VALIDATED_NO_EFFECT
        else None
    )
    primary_reason = rule.reason_code
    decision_reasons = tuple(
        dict.fromkeys((primary_reason, decision_reason))
    )
    decision = ModeSnapshotDecisionV1(
        decision_id=f"MODE-SNAPSHOT-DECISION::{inputs.request_id}",
        request_id=inputs.request_id,
        task_id=inputs.task_id,
        principal_id=inputs.principal_id,
        current_agent_id=inputs.current_agent_id,
        capability_decision_ref=inputs.capability_decision_ref,
        computation_bundle_ref=inputs.computation_bundle_ref,
        context_ref=inputs.context_ref,
        parameter_policy_snapshot_ref=inputs.parameter_policy_snapshot_ref,
        receipt_lineage_refs=inputs.receipt_lineage_refs,
        readiness_state_ref=inputs.readiness_state_ref,
        pretrade_state_ref=inputs.pretrade_state_ref,
        evidence_state_ref=inputs.evidence_reference.evidence_ref,
        kill_state_ref=inputs.kill_submit_state.state_ref,
        submit_disabled_state_ref=inputs.kill_submit_state.state_ref,
        owner_action_policy_ref=inputs.owner_action_policy_ref,
        current_mode=inputs.current_mode,
        requested_mode=inputs.requested_mode,
        mode_eligibility_state=eligibility,
        allow_candidate_state=allow_state,
        snapshot_candidate_state=(
            candidate.candidate_state
            if candidate is not None
            else SnapshotCandidateStateV1.ABSENT
        ),
        activation_precondition_state=activation_state,
        rollback_state=SnapshotRollbackStateV1.NONE,
        rollback_target_ref_or_explicit_absence=EXPLICIT_ABSENCE,
        pin_policy_ref=PIN_POLICY_ID,
        stale_state="CURRENT",
        expires_at=inputs.expires_at,
        retirement_state=SnapshotRetirementStateV1.CURRENT,
        implementation_pins=inputs.implementation_version_pins,
        source_epoch_refs=inputs.source_epoch_refs,
        reason_codes=decision_reasons,
        fallback_route=rule.terminal_route,
        owner_review_route=owner_route,
        no_trade_route=NO_TRADE_ROUTE,
        latency_measurement_ref_or_explicit_absence=(
            inputs.latency_measurement_ref_or_explicit_absence
        ),
    )
    predecessor_proposals = (
        (
            inputs.owner_action_confirmation.predecessor_transition_receipt_proposal_or_explicit_absence,
        )
        if rule.transition_id == "T07"
        else ()
    )
    transition = build_snapshot_transition_proposal(
        proposal_id=f"SNAPSHOT-TRANSITION::{inputs.request_id}",
        request_id=inputs.request_id,
        principal_id=inputs.principal_id,
        task_id=inputs.task_id,
        capability_decision_ref=inputs.capability_decision_ref,
        context_ref=inputs.context_ref,
        source_candidate_ref_or_explicit_absence=(
            candidate.snapshot_candidate_id
            if snapshot_for_result is not None
            else EXPLICIT_ABSENCE
        ),
        target_candidate_ref=(
            candidate.snapshot_candidate_id
            if candidate is not None
            else EXPLICIT_ABSENCE
        ),
        source_candidate_version_or_explicit_absence=(
            inputs.candidate_version
            if snapshot_for_result is not None
            else EXPLICIT_ABSENCE
        ),
        target_candidate_version=inputs.candidate_version,
        transition_id=rule.transition_id,
        expected_owner_state_ref=inputs.expected_owner_state_ref,
        precondition_receipt_refs=(
            *inputs.receipt_lineage_refs,
            inputs.owner_action_policy_ref,
        ),
        predecessor_transition_receipt_proposals=predecessor_proposals,
        proposed_state=(
            candidate.candidate_state
            if rule.transition_id == "T10" and candidate is not None
            else allow_state
        ),
        diagnostic_reason_codes=tuple(
            reason for reason in decision_reasons if reason is not rule.reason_code
        ),
        causation_id=inputs.causation_id,
        correlation_id=inputs.correlation_id,
    )
    return ModeSnapshotCandidateProposalResultV1(
        snapshot_candidate_or_explicit_absence=snapshot_for_result,
        mode_snapshot_decision=decision,
        snapshot_transition_proposal=transition,
        control_receipt_refs=(),
    )


def propose_snapshot_stale_or_rollback_required(
    *,
    request_id: str,
    candidate: FormulaRuntimeSnapshotCandidateV1,
    candidate_version: str,
    expected_owner_state_ref: str,
    observed_owner_state_ref: str,
    observed_current_candidate_ref: str,
    observed_current_candidate_version: str,
    evaluated_at: datetime,
    critical_pins_current: bool,
    post_validation_defect_detected: bool,
    precondition_receipt_refs: tuple[str, ...],
    causation_id: str,
    correlation_id: str,
) -> SnapshotTransitionProposalV1 | None:
    """Execute T11/T12 as an atomic no-effect lifecycle proposal."""

    if (
        type(candidate) is not FormulaRuntimeSnapshotCandidateV1
        or request_id != candidate.request_id
        or candidate.candidate_state is not SnapshotCandidateStateV1.VALIDATED_NO_EFFECT
        or type(critical_pins_current) is not bool
        or type(post_validation_defect_detected) is not bool
        or not isinstance(evaluated_at, datetime)
        or evaluated_at.tzinfo is None
        or evaluated_at.utcoffset() is None
        or evaluated_at.utcoffset().total_seconds() != 0
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "stale/rollback evaluation requires exact validated candidate state",
        )
    stale = not critical_pins_current or evaluated_at > candidate.expires_at
    raced = (
        observed_owner_state_ref != expected_owner_state_ref
        or observed_current_candidate_ref != candidate.snapshot_candidate_id
        or observed_current_candidate_version != candidate_version
    )
    if not stale and not post_validation_defect_detected and not raced:
        return None
    rule = TRANSITION_BY_ID["T11" if stale else "T12"]
    reason_codes = (rule.reason_code,)
    if raced and not stale:
        reason_codes = (*reason_codes, ReasonCode.SNAPSHOT_PIN_CONFLICT)
    return build_snapshot_transition_proposal(
        proposal_id=f"SNAPSHOT-LIFECYCLE::{request_id}::{rule.transition_id}",
        request_id=request_id,
        principal_id=candidate.principal_id,
        task_id=candidate.task_id,
        capability_decision_ref=candidate.capability_decision_ref,
        context_ref=candidate.context_ref,
        source_candidate_ref_or_explicit_absence=candidate.snapshot_candidate_id,
        target_candidate_ref=candidate.snapshot_candidate_id,
        source_candidate_version_or_explicit_absence=candidate_version,
        target_candidate_version=candidate_version,
        transition_id=rule.transition_id,
        expected_owner_state_ref=expected_owner_state_ref,
        precondition_receipt_refs=precondition_receipt_refs,
        proposed_state=(
            SnapshotCandidateStateV1.STALE
            if stale
            else SnapshotCandidateStateV1.ROLLBACK_REQUIRED
        ),
        diagnostic_reason_codes=tuple(reason_codes[1:]),
        causation_id=causation_id,
        correlation_id=correlation_id,
    )


def validate_snapshot_new_use(
    retirement_state: SnapshotRetirementStateV1,
) -> tuple[ReasonCode, ...]:
    """Enforce no-new-pin/no-new-use retirement policy without state mutation."""

    if type(retirement_state) is not SnapshotRetirementStateV1:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "retirement state must be an exact frozen enum",
        )
    if retirement_state is SnapshotRetirementStateV1.CURRENT:
        return ()
    if retirement_state is SnapshotRetirementStateV1.DRAINING_PINNED_IN_FLIGHT_ONLY:
        return (ReasonCode.RETIREMENT_DRAIN,)
    return (ReasonCode.RETIRED,)


def propose_snapshot_retirement(
    *,
    request_id: str,
    principal_id: str,
    task_id: str,
    capability_decision_ref: str,
    context_ref: str,
    candidate_ref: str,
    candidate_version: str,
    expected_owner_state_ref: str,
    current_retirement_state: SnapshotRetirementStateV1,
    retirement_declared: bool,
    in_flight_reference_count: int,
    precondition_receipt_refs: tuple[str, ...],
    causation_id: str,
    correlation_id: str,
) -> SnapshotTransitionProposalV1 | None:
    """Execute T15/T16 while allowing already-pinned in-flight work to drain."""

    if (
        type(current_retirement_state) is not SnapshotRetirementStateV1
        or type(retirement_declared) is not bool
        or isinstance(in_flight_reference_count, bool)
        or not isinstance(in_flight_reference_count, int)
        or in_flight_reference_count < 0
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "retirement evaluation requires exact state, declaration, and bounded count",
        )
    if (
        current_retirement_state is SnapshotRetirementStateV1.CURRENT
        and retirement_declared
    ):
        rule = TRANSITION_BY_ID["T15"]
        proposed_state = SnapshotRetirementStateV1.DRAINING_PINNED_IN_FLIGHT_ONLY
    elif (
        current_retirement_state
        is SnapshotRetirementStateV1.DRAINING_PINNED_IN_FLIGHT_ONLY
        and in_flight_reference_count == 0
    ):
        rule = TRANSITION_BY_ID["T16"]
        proposed_state = SnapshotRetirementStateV1.RETIRED
    else:
        return None
    return build_snapshot_transition_proposal(
        proposal_id=f"SNAPSHOT-RETIREMENT::{request_id}::{rule.transition_id}",
        request_id=request_id,
        principal_id=principal_id,
        task_id=task_id,
        capability_decision_ref=capability_decision_ref,
        context_ref=context_ref,
        source_candidate_ref_or_explicit_absence=candidate_ref,
        target_candidate_ref=candidate_ref,
        source_candidate_version_or_explicit_absence=candidate_version,
        target_candidate_version=candidate_version,
        transition_id=rule.transition_id,
        expected_owner_state_ref=expected_owner_state_ref,
        precondition_receipt_refs=precondition_receipt_refs,
        proposed_state=proposed_state,
        causation_id=causation_id,
        correlation_id=correlation_id,
    )
def select_prior_snapshot_candidate(
    candidates: tuple[PriorSnapshotCandidateV1, ...],
) -> PriorSnapshotCandidateV1 | None:
    """Select the frozen rollback target without committing it."""

    if not isinstance(candidates, tuple) or any(
        type(row) is not PriorSnapshotCandidateV1 for row in candidates
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "rollback inventory must be an immutable typed tuple",
        )
    eligible = tuple(
        row
        for row in candidates
        if row.independently_valid
        and row.all_required_pins_current
        and row.retirement_state is SnapshotRetirementStateV1.CURRENT
        and row.candidate.candidate_state
        is SnapshotCandidateStateV1.VALIDATED_NO_EFFECT
    )
    if not eligible:
        return None
    latest = max(row.candidate.evaluated_at for row in eligible)
    return min(
        (row for row in eligible if row.candidate.evaluated_at == latest),
        key=lambda row: row.candidate.snapshot_candidate_id,
    )


def propose_rollback(
    *,
    request_id: str,
    principal_id: str,
    task_id: str,
    capability_decision_ref: str,
    context_ref: str,
    current_candidate_ref: str,
    current_candidate_version: str,
    expected_owner_state_ref: str,
    observed_owner_state_ref: str,
    observed_current_candidate_ref: str,
    observed_current_candidate_version: str,
    candidates: tuple[PriorSnapshotCandidateV1, ...],
    rollback_required_receipt_proposal: object,
    precondition_receipt_refs: tuple[str, ...],
    causation_id: str,
    correlation_id: str,
) -> SnapshotTransitionProposalV1:
    raced = (
        observed_owner_state_ref != expected_owner_state_ref
        or observed_current_candidate_ref != current_candidate_ref
        or observed_current_candidate_version != current_candidate_version
    )
    target = None if raced else select_prior_snapshot_candidate(candidates)
    rule = TRANSITION_BY_ID["T13" if target is not None else "T14"]
    reasons = (rule.reason_code,)
    if raced:
        reasons = (*reasons, ReasonCode.SNAPSHOT_PIN_CONFLICT)
    return build_snapshot_transition_proposal(
        proposal_id=f"SNAPSHOT-ROLLBACK::{request_id}",
        request_id=request_id,
        principal_id=principal_id,
        task_id=task_id,
        capability_decision_ref=capability_decision_ref,
        context_ref=context_ref,
        source_candidate_ref_or_explicit_absence=current_candidate_ref,
        target_candidate_ref=(
            target.candidate.snapshot_candidate_id
            if target is not None
            else EXPLICIT_ABSENCE
        ),
        source_candidate_version_or_explicit_absence=current_candidate_version,
        target_candidate_version=(
            target.candidate_version if target is not None else EXPLICIT_ABSENCE
        ),
        transition_id=rule.transition_id,
        expected_owner_state_ref=expected_owner_state_ref,
        precondition_receipt_refs=precondition_receipt_refs,
        predecessor_transition_receipt_proposals=(
            rollback_required_receipt_proposal,
        ),
        proposed_state=(
            SnapshotRollbackStateV1.PROPOSED_PRIOR_IMMUTABLE_CANDIDATE
            if target is not None
            else SnapshotRollbackStateV1.BLOCKED_NO_VALID_PRIOR_CANDIDATE
        ),
        diagnostic_reason_codes=tuple(reasons[1:]),
        causation_id=causation_id,
        correlation_id=correlation_id,
    )


def owner_projection(
    decision: ModeSnapshotDecisionV1,
    evidence: ST12FEvidenceReferenceV1,
    safety: ReadOnlyKillSubmitStateV1,
    *,
    snapshot_version: str,
) -> ModeSnapshotOwnerProjectionV1:
    """One-way projection into the existing owner semantic bundle."""

    return ModeSnapshotOwnerProjectionV1(
        decision_id=decision.decision_id,
        mode_eligibility_state=decision.mode_eligibility_state,
        allow_candidate_state=decision.allow_candidate_state,
        snapshot_candidate_state=decision.snapshot_candidate_state,
        evidence_state=evidence.evidence_state,
        kill_state=safety.kill_state,
        submit_disabled_state=safety.submit_disabled_state,
        stale_state=decision.stale_state,
        reason_codes=decision.reason_codes,
        fallback_route=decision.fallback_route,
        owner_review_route=decision.owner_review_route,
        policy_and_snapshot_versions=(
            decision.pin_policy_ref,
            decision.parameter_policy_snapshot_ref,
            snapshot_version,
        ),
    )


if len(MODE_SNAPSHOT_TRANSITIONS) != 17 or sum(
    len(states) for states in D_MODE_STATE_REGISTRY.values()
) != 35:
    raise RuntimeError("ST12-D state/transition registry closure is incomplete")
