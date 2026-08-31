from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
from datetime import timedelta
from decimal import Decimal
import json
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch

import pytest

import src.qtt.plugins as generic_plugins
import src.qtt.stage1_prediction_markets.qku_computation_control_plane as qku_control_plane
from src.qtt.plugins.contracts import (
    PluginPackageContractError,
    _canonical_package_json,
    _normalize_package_serialization_value,
)
from src.qtt.source_evidence.cross_venue_execution_normalization.taxonomy import (
    ACTIVE_STAGE1_VENUES as SOURCE_EVIDENCE_ACTIVE_STAGE1_VENUES,
)
from src.qtt.stage1_prediction_markets.capital_risk.field_map_constants import (
    ACTIVE_STAGE1_VENUES as CAPITAL_RISK_ACTIVE_STAGE1_VENUES,
)
from src.qtt.stage1_prediction_markets.credential_readiness.policy import (
    STAGE1_VENUE_IDS as CREDENTIAL_READINESS_STAGE1_VENUE_IDS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ComputationControlPlaneError,
    ContractValidationError,
    InputAuthorityError,
    NumericDomainError,
    OwnerAdapterError,
    ReasonCode,
    SerializationSafetyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    IMPLEMENTATION_REGISTRY,
    ST12D_MATH_IMPLEMENTATION_REGISTRY,
    TRANCHE_D_NEW_IMPLEMENTATION_REGISTRY,
    compute_math_39_queue_position_estimate,
    validate_math_39_event_context,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.mode_snapshot_policy import (
    MODE_SNAPSHOT_CANDIDATE_KIND,
    PriorSnapshotCandidateV1,
    build_snapshot_transition_proposal,
    build_snapshot_candidate,
    construct_snapshot_candidate,
    evaluate_mode_snapshot_candidate,
    finalize_mode_snapshot_latency_block,
    owner_projection,
    propose_rollback,
    propose_snapshot_retirement,
    propose_snapshot_stale_or_rollback_required,
    select_prior_snapshot_candidate,
    validate_candidate_pin_identity,
    validate_snapshot_candidate,
    validate_snapshot_new_use,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ActivationPreconditionStateV1,
    AllowCandidateStateV1,
    ComputeComponentRequestV1,
    ExecutedModeSnapshotTransitionTraceV1,
    ImplementationVersionPinV1,
    LatencyBudgetProfileV1,
    ModeEligibilityState,
    ModeSnapshotCandidateProposalResultV1,
    NO_EFFECTS_V1,
    OperationStatusV1,
    ResourceBoundsProfileV1,
    SnapshotCandidateStateV1,
    SnapshotParameterResolutionStateV1,
    SnapshotRetirementStateV1,
    SnapshotRollbackStateV1,
    ST12FEvidenceStateV1,
    SubmitCandidateProposalRequestV1,
    TypedValueKindV1,
    TypedValueRecordV1,
    TypedValueV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    ORACLE_BY_MATH_ID,
    ST12D_GOLDEN_VECTOR_BY_MATH_ID,
    ST12D_ORACLE_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
    PARAMETER_POLICY_BY_ID,
    ST12D_PARAMETER_APPLICATION_BINDINGS,
    ST12D_PARAMETER_POLICIES,
    ST12D_SNAPSHOT_PARAMETER_BINDING_IDS,
    resolve_st12d_snapshot_parameter_values,
    resolve_st12d_value_policy_refs,
    st12d_snapshot_parameter_binding_id,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import (
    ExistingOwnerProjectionAdapterV1,
    OwnerProjectionViewV1,
    PreloadedOwnerProjectionBundleV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    EconomicRecordTypeV1,
    ModeSnapshotControlClassV1,
    ModeSnapshotControlReceiptRecordV1,
    materialize_mode_snapshot_control_receipts,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    CanonicalOwnerPacketRegistryV1,
    CurrentModeSnapshotInputResolverV1,
    FormulaInputResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    FORMULA_INPUT_AUTHORITY_BINDINGS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.latency_policy import (
    STAGE_NAMES,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    QKUComputationControlPlaneV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    FROZEN_FORMULA_REQUIREMENTS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stack_resolver import (
    REGISTERED_FORMULA_STACKS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
    safe_json_loads,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.plugin_adapter import (
    _qku_projection_serialization_value,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    ST12D_ACTUAL_CONTROL_MUTATION_CASES,
    ST12D_CLOSURE_ROWS,
    ST12D_GENERATED_PROJECTION_PATHS,
    ST12D_HISTORICAL_PATH_DISPOSITIONS,
    ST12D_SEMANTIC_TEST_ROWS,
    adjudicate_st12d_semantic_test,
    run_st12d_actual_control_mutation_case,
    st12d_acceptance_counts,
)
from tests.stage1_prediction_markets.qku_computation_control_plane.test_policy_state_matrix import (
    _audit_bundle_fixture,
    _current_owner_registry,
    _inputs,
    _transition_receipt_proposal,
)
from tests.stage1_prediction_markets.qku_computation_control_plane.tranche_e import (
    make_resolver,
    resolve_decision,
)
from tools.build_qku_computation_control_plane import build_payload
from tools.independent_validate_qku_computation_control_plane_architecture import (
    _independent_selected_component_package_core_v1,
    _selected_component_package_failures,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _jsonl(path: Path) -> tuple[dict[str, object], ...]:
    return tuple(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def test_snapshot_value_is_deeply_immutable_deterministic_and_exactly_pinned() -> None:
    inputs = _inputs()
    built = construct_snapshot_candidate(inputs)
    assert built.candidate_state is SnapshotCandidateStateV1.BUILT_IMMUTABLE
    assert built.reason_codes == (ReasonCode.SNAPSHOT_CANDIDATE_BUILT,)
    candidate = validate_snapshot_candidate(built, inputs)
    assert candidate.candidate_state is SnapshotCandidateStateV1.VALIDATED_NO_EFFECT
    assert candidate == build_snapshot_candidate(inputs)
    assert validate_candidate_pin_identity(candidate, inputs) == ()
    assert deterministic_json(candidate) == deterministic_json(candidate)
    assert tuple(pin.math_spec_id for pin in candidate.implementation_version_pins) == (
        "MATH-13",
        "MATH-14",
        "MATH-15",
        "MATH-39",
    )
    assert candidate.parameter_value_refs is inputs.parameter_value_refs
    assert candidate.source_epoch_refs is inputs.source_epoch_refs
    assert len(inputs.resolved_parameter_values) == 21
    assert inputs.parameter_value_refs == tuple(
        row.resolved_value_ref for row in inputs.resolved_parameter_values
    )
    assert not set(inputs.parameter_value_refs).intersection(
        row.policy_ref for row in inputs.resolved_parameter_values
    )
    with pytest.raises(FrozenInstanceError):
        candidate.activated = True  # type: ignore[misc]
    with pytest.raises(TypeError):
        candidate.parameter_value_refs[0] = "SILENT-REPIN"  # type: ignore[index]

    repinned = replace(
        built,
        parameter_policy_snapshot_ref="UNEXPECTED-LATEST",
    )
    assert validate_candidate_pin_identity(repinned, inputs) == (
        ReasonCode.SNAPSHOT_PIN_CONFLICT,
    )
    rejected = validate_snapshot_candidate(repinned, inputs)
    assert rejected.candidate_state is SnapshotCandidateStateV1.REJECTED
    assert rejected.reason_codes == (
        ReasonCode.SNAPSHOT_CANDIDATE_INVALID,
        ReasonCode.SNAPSHOT_PIN_CONFLICT,
    )
    mutated_value_receipt = replace(
        inputs.resolved_parameter_values[0],
        resolved_value_ref=(
            f"{inputs.resolved_parameter_values[0].resolved_value_ref}::MUTATED"
        ),
    )
    mutated_value_pin = replace(
        built,
        parameter_value_refs=(
            mutated_value_receipt.resolved_value_ref,
            *built.parameter_value_refs[1:],
        ),
    )
    assert validate_candidate_pin_identity(mutated_value_pin, inputs) == (
        ReasonCode.SNAPSHOT_PIN_CONFLICT,
    )
    policy_in_value_slot = replace(
        built,
        parameter_value_refs=(
            inputs.resolved_parameter_values[0].policy_ref,
            *built.parameter_value_refs[1:],
        ),
    )
    assert validate_candidate_pin_identity(policy_in_value_slot, inputs) == (
        ReasonCode.SNAPSHOT_PIN_CONFLICT,
    )

    bundle, registry = _audit_bundle_fixture()
    required_owner_parameter = "ST10-PARAM::0764"
    missing_owner_registry = CanonicalOwnerPacketRegistryV1(
        tuple(
            packet
            for packet in registry.packets
            if st12d_snapshot_parameter_binding_id(required_owner_parameter)
            not in packet.authorized_binding_ids
        )
    )
    unresolved = resolve_st12d_snapshot_parameter_values(
        context=bundle.execution_context,
        owner_registry=missing_owner_registry,
    )
    assert len(unresolved) == 21
    unavailable = next(
        row for row in unresolved if row.parameter_id == required_owner_parameter
    )
    assert unavailable.resolution_state is (
        SnapshotParameterResolutionStateV1.REQUIRED_OWNER_VALUE_UNAVAILABLE
    )
    assert unavailable.diagnostic_reason_codes == (
        ReasonCode.INPUT_OWNER_MISSING,
    )


def test_candidate_rejection_and_rollback_are_atomic_proposals_only() -> None:
    inputs = _inputs()
    current = build_snapshot_candidate(inputs)
    older = replace(
        current,
        snapshot_candidate_id="SNAPSHOT-CANDIDATE::A",
        evaluated_at=current.evaluated_at - timedelta(seconds=2),
    )
    tied_b = replace(
        current,
        snapshot_candidate_id="SNAPSHOT-CANDIDATE::B",
        evaluated_at=current.evaluated_at - timedelta(seconds=1),
    )
    tied_a = replace(tied_b, snapshot_candidate_id="SNAPSHOT-CANDIDATE::A2")
    rows = tuple(
        PriorSnapshotCandidateV1(
            candidate=candidate,
            candidate_version=candidate_version,
            retirement_state=retirement,
            independently_valid=valid,
            all_required_pins_current=pins_current,
        )
        for candidate, candidate_version, retirement, valid, pins_current in (
            (older, "SNAPSHOT-VERSION::OLDER", SnapshotRetirementStateV1.CURRENT, True, True),
            (tied_b, "SNAPSHOT-VERSION::TIED-B", SnapshotRetirementStateV1.CURRENT, True, True),
            (tied_a, "SNAPSHOT-VERSION::TIED-A2", SnapshotRetirementStateV1.CURRENT, True, True),
            (current, "SNAPSHOT-VERSION::CURRENT-RETIRED", SnapshotRetirementStateV1.RETIRED, True, True),
        )
    )
    before = deterministic_json(current)
    selected = select_prior_snapshot_candidate(rows)
    assert selected is rows[2]
    assert selected.candidate is tied_a
    rollback_required_receipt = _transition_receipt_proposal(
        transition_id="T12",
        request_id=inputs.request_id,
        principal_id=inputs.principal_id,
        task_id=inputs.task_id,
        capability_decision_ref=inputs.capability_decision_ref,
        context_ref=inputs.context_ref,
        snapshot_candidate_ref=current.snapshot_candidate_id,
        candidate_version=inputs.candidate_version,
        expected_owner_state_ref="OWNER-STATE::EXPECTED",
        effective_at=current.evaluated_at,
    )
    proposal = propose_rollback(
        request_id=inputs.request_id,
        principal_id=inputs.principal_id,
        task_id=inputs.task_id,
        capability_decision_ref=inputs.capability_decision_ref,
        context_ref=inputs.context_ref,
        current_candidate_ref=current.snapshot_candidate_id,
        current_candidate_version=inputs.candidate_version,
        expected_owner_state_ref="OWNER-STATE::EXPECTED",
        observed_owner_state_ref="OWNER-STATE::EXPECTED",
        observed_current_candidate_ref=current.snapshot_candidate_id,
        observed_current_candidate_version=inputs.candidate_version,
        candidates=rows,
        rollback_required_receipt_proposal=rollback_required_receipt,
        precondition_receipt_refs=inputs.receipt_lineage_refs,
        causation_id="CAUSE::ROLLBACK",
        correlation_id="CORRELATION::ROLLBACK",
    )
    assert proposal.proposed_state is (
        SnapshotRollbackStateV1.PROPOSED_PRIOR_IMMUTABLE_CANDIDATE
    )
    assert proposal.target_candidate_ref == tied_a.snapshot_candidate_id
    assert proposal.target_candidate_version == "SNAPSHOT-VERSION::TIED-A2"
    assert proposal.target_candidate_version != tied_a.evaluated_at.isoformat()
    assert proposal.expected_owner_state_ref == "OWNER-STATE::EXPECTED"
    assert proposal.mutation_allowed is False
    assert proposal.active_pointer_commit_allowed is False
    assert deterministic_json(current) == before

    raced_rollback_required_receipt = _transition_receipt_proposal(
        transition_id="T12",
        request_id=inputs.request_id,
        principal_id=inputs.principal_id,
        task_id=inputs.task_id,
        capability_decision_ref=inputs.capability_decision_ref,
        context_ref=inputs.context_ref,
        snapshot_candidate_ref=current.snapshot_candidate_id,
        candidate_version=inputs.candidate_version,
        expected_owner_state_ref="OWNER-STATE::MISMATCH",
        effective_at=current.evaluated_at,
    )
    blocked = propose_rollback(
        request_id=inputs.request_id,
        principal_id=inputs.principal_id,
        task_id=inputs.task_id,
        capability_decision_ref=inputs.capability_decision_ref,
        context_ref=inputs.context_ref,
        current_candidate_ref=current.snapshot_candidate_id,
        current_candidate_version=inputs.candidate_version,
        expected_owner_state_ref="OWNER-STATE::MISMATCH",
        observed_owner_state_ref="OWNER-STATE::CHANGED",
        observed_current_candidate_ref="SNAPSHOT-CANDIDATE::RACED",
        observed_current_candidate_version="SNAPSHOT-CANDIDATE-VERSION::RACED",
        candidates=rows,
        rollback_required_receipt_proposal=raced_rollback_required_receipt,
        precondition_receipt_refs=inputs.receipt_lineage_refs,
        causation_id="CAUSE::ROLLBACK::BLOCK",
        correlation_id="CORRELATION::ROLLBACK::BLOCK",
    )
    assert blocked.proposed_state is (
        SnapshotRollbackStateV1.BLOCKED_NO_VALID_PRIOR_CANDIDATE
    )
    assert blocked.typed_reason_codes == (
        ReasonCode.NO_VALID_ROLLBACK_TARGET,
        ReasonCode.SNAPSHOT_PIN_CONFLICT,
    )
    assert deterministic_json(current) == before

    stale = propose_snapshot_stale_or_rollback_required(
        request_id=inputs.request_id,
        candidate=current,
        candidate_version=inputs.candidate_version,
        expected_owner_state_ref=inputs.expected_owner_state_ref,
        observed_owner_state_ref=inputs.expected_owner_state_ref,
        observed_current_candidate_ref=current.snapshot_candidate_id,
        observed_current_candidate_version=inputs.candidate_version,
        evaluated_at=current.expires_at + timedelta(microseconds=1),
        critical_pins_current=True,
        post_validation_defect_detected=False,
        precondition_receipt_refs=inputs.receipt_lineage_refs,
        causation_id="CAUSE::STALE",
        correlation_id="CORRELATION::STALE",
    )
    assert stale is not None
    assert stale.transition_id == "T11"
    assert stale.proposed_state is SnapshotCandidateStateV1.STALE
    rollback_required = propose_snapshot_stale_or_rollback_required(
        request_id=inputs.request_id,
        candidate=current,
        candidate_version=inputs.candidate_version,
        expected_owner_state_ref=inputs.expected_owner_state_ref,
        observed_owner_state_ref="OWNER-STATE::RACED",
        observed_current_candidate_ref=current.snapshot_candidate_id,
        observed_current_candidate_version=inputs.candidate_version,
        evaluated_at=current.evaluated_at,
        critical_pins_current=True,
        post_validation_defect_detected=False,
        precondition_receipt_refs=inputs.receipt_lineage_refs,
        causation_id="CAUSE::DEFECT",
        correlation_id="CORRELATION::DEFECT",
    )
    assert rollback_required is not None
    assert rollback_required.transition_id == "T12"
    assert rollback_required.proposed_state is SnapshotCandidateStateV1.ROLLBACK_REQUIRED

    draining = propose_snapshot_retirement(
        request_id=inputs.request_id,
        principal_id=inputs.principal_id,
        task_id=inputs.task_id,
        capability_decision_ref=inputs.capability_decision_ref,
        context_ref=inputs.context_ref,
        candidate_ref=current.snapshot_candidate_id,
        candidate_version=inputs.candidate_version,
        expected_owner_state_ref=inputs.expected_owner_state_ref,
        current_retirement_state=SnapshotRetirementStateV1.CURRENT,
        retirement_declared=True,
        in_flight_reference_count=2,
        precondition_receipt_refs=inputs.receipt_lineage_refs,
        causation_id="CAUSE::RETIREMENT",
        correlation_id="CORRELATION::RETIREMENT",
    )
    assert draining is not None
    assert draining.transition_id == "T15"
    assert validate_snapshot_new_use(draining.proposed_state) == (
        ReasonCode.RETIREMENT_DRAIN,
    )
    retired = propose_snapshot_retirement(
        request_id=inputs.request_id,
        principal_id=inputs.principal_id,
        task_id=inputs.task_id,
        capability_decision_ref=inputs.capability_decision_ref,
        context_ref=inputs.context_ref,
        candidate_ref=current.snapshot_candidate_id,
        candidate_version=inputs.candidate_version,
        expected_owner_state_ref=inputs.expected_owner_state_ref,
        current_retirement_state=SnapshotRetirementStateV1.DRAINING_PINNED_IN_FLIGHT_ONLY,
        retirement_declared=True,
        in_flight_reference_count=0,
        precondition_receipt_refs=inputs.receipt_lineage_refs,
        causation_id="CAUSE::RETIRED",
        correlation_id="CORRELATION::RETIRED",
    )
    assert retired is not None
    assert retired.transition_id == "T16"
    assert validate_snapshot_new_use(retired.proposed_state) == (ReasonCode.RETIRED,)
    assert deterministic_json(current) == before


def test_parameter_math_oracle_and_source_semantics_close_under_existing_owners() -> None:
    assert isinstance(ST12D_PARAMETER_POLICIES, MappingProxyType)
    assert len(ST12D_PARAMETER_POLICIES) == 28
    assert len(ST12D_PARAMETER_APPLICATION_BINDINGS) == 28
    assert len(ST12D_SNAPSHOT_PARAMETER_BINDING_IDS) == 21
    assert {
        policy.canonical_owner for policy in ST12D_PARAMETER_POLICIES.values()
    } == {"QKUComputationControlPlaneV1.ComputationParameterPolicyV1"}
    assert all(
        PARAMETER_POLICY_BY_ID[parameter_id] is policy
        and policy.effective_source_state_refs
        and policy.runtime_resolution_procedure
        for parameter_id, policy in ST12D_PARAMETER_POLICIES.items()
    )
    refs = resolve_st12d_value_policy_refs(tuple(ST12D_PARAMETER_POLICIES))
    assert set(refs) == set(ST12D_PARAMETER_POLICIES)
    assert all(value.startswith("ComputationParameterPolicyV1::") for value in refs.values())

    assert tuple(ST12D_MATH_IMPLEMENTATION_REGISTRY) == (
        "MATH-13",
        "MATH-14",
        "MATH-15",
        "MATH-39",
    )
    assert len(TRANCHE_D_NEW_IMPLEMENTATION_REGISTRY) == 1
    for math_id in ("MATH-13", "MATH-14", "MATH-15"):
        assert ST12D_MATH_IMPLEMENTATION_REGISTRY[math_id] is IMPLEMENTATION_REGISTRY[math_id]
        assert ST12D_ORACLE_BY_MATH_ID[math_id] is ORACLE_BY_MATH_ID[math_id]
    assert compute_math_39_queue_position_estimate("100", "20", "10", "30") == Decimal("80")
    assert compute_math_39_queue_position_estimate("1", "0", "2", "3") == Decimal("0")
    vector = ST12D_GOLDEN_VECTOR_BY_MATH_ID["MATH-39"]
    oracle = ST12D_ORACLE_BY_MATH_ID["MATH-39"]
    assert json.loads(vector.expected_json) == {"queue_ahead": "80"}
    assert json.loads(oracle.expected_value_json) == {"queue_ahead": "80"}
    validate_math_39_event_context(
        sequence_continuous=True,
        matching_priority_known=True,
        unit="units",
        basis="ACKNOWLEDGED_INSERTION_POINT",
        venue_evidence_ref="VENUE-EVIDENCE::1",
    )
    with pytest.raises(NumericDomainError) as gap:
        validate_math_39_event_context(
            sequence_continuous=False,
            matching_priority_known=True,
            unit="units",
            basis="ACKNOWLEDGED_INSERTION_POINT",
            venue_evidence_ref="VENUE-EVIDENCE::1",
        )
    assert gap.value.reason_code is ReasonCode.SEQUENCE_GAP

    bundle, owner_registry = _audit_bundle_fixture()
    deterministic_rows = tuple(
        row
        for row in bundle.resolved_parameter_values
        if row.resolution_state
        is SnapshotParameterResolutionStateV1.DETERMINISTIC_POLICY_VALUE_MATERIALIZED
    )
    owner_rows = tuple(
        row
        for row in bundle.resolved_parameter_values
        if row.resolution_state is SnapshotParameterResolutionStateV1.OWNER_VALUE_RESOLVED
    )
    assert all(
        not (
            row.producer_receipt_refs
            or row.point_in_time_receipt_refs
            or row.freshness_receipt_refs
            or row.source_epoch_refs
        )
        for row in deterministic_rows
    )
    assert all(
        row.producer_receipt_refs
        and row.point_in_time_receipt_refs
        and row.freshness_receipt_refs
        and row.source_epoch_refs
        for row in owner_rows
    )
    assert len(FROZEN_FORMULA_REQUIREMENTS) == 30
    assert len(FORMULA_INPUT_AUTHORITY_BINDINGS) == 142
    assert tuple(REGISTERED_FORMULA_STACKS) == (
        "STACK::MATH-01::MATH-02::V3_4",
    )
    assert bundle.data_edge_refs == ()
    assert bundle.all_four_dimensions_closed is True
    assert tuple(row.math_spec_id for row in bundle.component_closures) == (
        "MATH-13",
        "MATH-14",
        "MATH-15",
        "MATH-39",
    )
    assert all(
        len(component.dimension_receipts) == 4
        and all(row.computable for row in component.dimension_receipts)
        for component in bundle.component_closures
    )

    events_packet = next(
        packet
        for packet in owner_registry.packets
        if "FIVAB::sequenced_book_events::MATH-39"
        in packet.authorized_binding_ids
    )
    ack_packet = next(
        packet
        for packet in owner_registry.packets
        if "FIVAB::order_ack::MATH-39" in packet.authorized_binding_ids
    )
    events = events_packet.values["book.sequenced_book_events"]
    acknowledgement = ack_packet.values["execution.order_ack"]

    def registry_with(replacement_packet):
        return CanonicalOwnerPacketRegistryV1(
            tuple(
                replacement_packet
                if packet.packet_id == replacement_packet.packet_id
                else packet
                for packet in owner_registry.packets
            )
        )

    sequence_gap_events = (
        events[0],
        replace(events[1], sequence=events[1].sequence + 1),
        *events[2:],
    )
    venue_mismatch_events = (
        events[0],
        replace(events[1], venue_evidence_ref="VENUE-EVIDENCE::MISMATCH"),
        *events[2:],
    )
    raw_resolution_mutations = (
        (
            replace(
                events_packet,
                values={"book.sequenced_book_events": sequence_gap_events},
            ),
            ReasonCode.SEQUENCE_GAP,
        ),
        (
            replace(
                events_packet,
                values={"book.sequenced_book_events": venue_mismatch_events},
            ),
            ReasonCode.INPUT_SCOPE_MISMATCH,
        ),
        (
            replace(events_packet, ttl=timedelta(microseconds=1)),
            ReasonCode.FRESHNESS_VIOLATION,
        ),
        (
            replace(
                ack_packet,
                values={
                    "execution.order_ack": replace(
                        acknowledgement,
                        available_at=bundle.execution_context.as_of
                        + timedelta(seconds=1),
                    )
                },
            ),
            ReasonCode.POINT_IN_TIME_VIOLATION,
        ),
    )
    for replacement_packet, expected_reason in raw_resolution_mutations:
        with pytest.raises(ComputationControlPlaneError) as rejected:
            FormulaInputResolverV1.resolve(
                "MATH-39",
                context=bundle.execution_context,
                owner_registry=registry_with(replacement_packet),
            )
        assert rejected.value.reason_code is expected_reason

    typed_record_mutations = (
        (acknowledgement, {"matching_priority": "UNKNOWN"}, ReasonCode.MATCHING_PRIORITY_UNKNOWN),
        (acknowledgement, {"basis": "UNKNOWN"}, ReasonCode.UNIT_BASIS_OR_PRECISION_INVALID),
        (events[0], {"unit": "contracts"}, ReasonCode.UNIT_BASIS_OR_PRECISION_INVALID),
        (events[0], {"quantity": Decimal("-1")}, ReasonCode.INPUT_VALUE_CONFLICT),
        (events[0], {"quantity": Decimal("NaN")}, ReasonCode.INPUT_VALUE_CONFLICT),
    )
    for record, mutation, expected_reason in typed_record_mutations:
        with pytest.raises(InputAuthorityError) as rejected:
            replace(record, **mutation)
        assert rejected.value.reason_code is expected_reason

    snapshot_operation_id = "submit_candidate_proposal"
    snapshot_admission = resolve_decision(
        make_resolver(
            operation_id=snapshot_operation_id,
            envelope_overrides={
                "context_ref": bundle.execution_context.context_id,
                "idempotency_key": "IDEMPOTENCY::D::CONSUMED-EPOCHS",
            },
        ),
        request_id="REQUEST::D::CONSUMED-EPOCHS",
        operation_id=snapshot_operation_id,
        context_ref=bundle.execution_context.context_id,
        requested_scope_refs={
            "qku_scope_refs": ("QKU::ST12E::TEST",),
            "formula_scope_refs": ("MATH-01",),
        },
        request_idempotency_key="IDEMPOTENCY::D::CONSUMED-EPOCHS",
    )

    class _SnapshotRequestProbe:
        request_id = snapshot_admission.request_id
        principal_id = snapshot_admission.principal_id
        context = bundle.execution_context

    _bundle, snapshot_registry = _current_owner_registry(snapshot_admission)
    snapshot_resolver = CurrentModeSnapshotInputResolverV1(
        repo_root=_repo_root(),
        owner_registry=snapshot_registry,
    )
    early_gate = snapshot_resolver.resolve_mode_snapshot_preconstruction_gate(
        _SnapshotRequestProbe(),
        snapshot_admission,
    )
    current_gate = replace(
        early_gate,
        evidence_reference=_inputs().evidence_reference,
    )
    preloaded_projections = ExistingOwnerProjectionAdapterV1(
        _repo_root()
    ).load_bundle()
    assert preloaded_projections.receipt_refs == ()
    assert preloaded_projections.source_epoch_refs == ()
    assert preloaded_projections.source_snapshot_refs == tuple(
        row.source_path
        for row in (
            preloaded_projections.readiness,
            preloaded_projections.pretrade,
            preloaded_projections.svc,
            preloaded_projections.agent_orch,
        )
    )
    baseline_enriched = snapshot_resolver.enrich_mode_snapshot_candidate(
        _SnapshotRequestProbe(),
        snapshot_admission,
        current_gate,
        preloaded_projections,
    )
    unrelated_packet = replace(
        snapshot_registry.packets[0],
        packet_id="PACKET::D::UNRELATED",
        source_epoch_id="SOURCE-EPOCH::D::UNRELATED",
        authorized_binding_ids=("ST12D::UNRELATED::NOT-CONSUMED",),
        producer_receipt_id="RECEIPT::D::UNRELATED",
        values={"unrelated.value": "NOT-CONSUMED"},
    )
    unrelated_registry = CanonicalOwnerPacketRegistryV1(
        (*snapshot_registry.packets, unrelated_packet)
    )
    unrelated_enriched = CurrentModeSnapshotInputResolverV1(
        repo_root=_repo_root(),
        owner_registry=unrelated_registry,
    ).enrich_mode_snapshot_candidate(
        _SnapshotRequestProbe(),
        snapshot_admission,
        current_gate,
        preloaded_projections,
    )
    assert unrelated_enriched.source_epoch_refs == baseline_enriched.source_epoch_refs
    assert "SOURCE-EPOCH::D::UNRELATED" not in unrelated_enriched.source_epoch_refs
    assert not set(preloaded_projections.source_snapshot_refs).intersection(
        baseline_enriched.source_epoch_refs
    )
    assert not {
        row.policy_ref for row in baseline_enriched.resolved_parameter_values
    }.intersection(baseline_enriched.receipt_lineage_refs)
    assert (
        baseline_enriched.computation_bundle_closure.preflight_receipt_ref
        not in baseline_enriched.receipt_lineage_refs
    )
    assert deterministic_json(
        evaluate_mode_snapshot_candidate(unrelated_enriched)
    ) == deterministic_json(evaluate_mode_snapshot_candidate(baseline_enriched))

    consumed_binding = st12d_snapshot_parameter_binding_id(
        "ST10-PARAM::0764"
    )
    consumed_packet = next(
        packet
        for packet in snapshot_registry.packets
        if consumed_binding in packet.authorized_binding_ids
    )
    stale_consumed_registry = CanonicalOwnerPacketRegistryV1(
        tuple(
            replace(packet, source_epoch_id="SOURCE-EPOCH::D::MUTATED")
            if packet.packet_id == consumed_packet.packet_id
            else packet
            for packet in snapshot_registry.packets
        )
    )
    with pytest.raises(ComputationControlPlaneError) as stale_epoch:
        CurrentModeSnapshotInputResolverV1(
            repo_root=_repo_root(),
            owner_registry=stale_consumed_registry,
        ).enrich_mode_snapshot_candidate(
            _SnapshotRequestProbe(),
            snapshot_admission,
            current_gate,
            preloaded_projections,
        )
    assert stale_epoch.value.reason_code is ReasonCode.SOURCE_EPOCH_STALE

    math39_context = replace(
        bundle.execution_context,
        implementation_versions=tuple(
            pin
            for pin in bundle.execution_context.implementation_versions
            if pin.math_spec_id == "MATH-39"
        ),
    )
    operation_id = "compute_component"
    admitted = resolve_decision(
        make_resolver(
            operation_id=operation_id,
            envelope_overrides={
                "context_ref": math39_context.context_id,
                "idempotency_key": "IDEMPOTENCY::D::MATH39-SERVICE",
                "formula_scope_refs": ("MATH-39",),
                "implementation_version_requirements": (
                    "MATH-39::1.1R1",
                ),
            },
        ),
        request_id="REQUEST::D::MATH39-SERVICE",
        operation_id=operation_id,
        context_ref=math39_context.context_id,
        requested_scope_refs={
            "qku_scope_refs": ("QKU::ST12E::TEST",),
            "formula_scope_refs": ("MATH-39",),
        },
        request_idempotency_key="IDEMPOTENCY::D::MATH39-SERVICE",
    )

    class _Admission:
        def admit_operation(self, _request: object):
            return admitted

    assertions = TypedValueRecordV1(
        tuple(
            TypedValueV1(
                name=name,
                kind=TypedValueKindV1.DECIMAL,
                value=value,
                unit="units",
                basis="ACKNOWLEDGED_INSERTION_POINT",
            )
            for name, value in (
                ("displayed_quantity_before_order", Decimal("100")),
                ("net_prior_additions", Decimal("20")),
                ("observed_prior_cancellations", Decimal("10")),
                ("observed_trades_ahead", Decimal("30")),
            )
        )
    )
    component_service = QKUComputationControlPlaneV1(
        owner_registry,
        agent_capability_resolver=_Admission(),
    )
    component_request = ComputeComponentRequestV1(
        request_id=admitted.request_id,
        operation_name=operation_id,
        requested_at=math39_context.as_of,
        principal_id=admitted.principal_id,
        capability_bundle_id="CAPABILITY::D::MATH39-SERVICE",
        context=math39_context,
        idempotency_key=admitted.idempotency_key,
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        tracestate="vendor=value",
        component_id="MATH-39",
        input_values=assertions,
        expected_output_schema_ref="MATH-39::OUTPUT",
    )
    response = component_service.compute_component(component_request)
    assert response.status is OperationStatusV1.SUCCEEDED
    assert response.component_result.formula_output is not None
    assert response.component_result.formula_output.value == Decimal("80")
    assert response.component_result.formula_output.output_schema_version == (
        "ST12D_OUTPUT_V1"
    )
    assert {
        "RECEIPT::ST12D-AUDIT::MATH39-ACK",
        "RECEIPT::ST12D-AUDIT::MATH39-BOOK",
    }.issubset(response.receipt_refs)
    pin_mismatch = component_service.compute_component(
        replace(
            component_request,
            context=replace(
                math39_context,
                implementation_versions=(
                    ImplementationVersionPinV1(
                        math_spec_id="MATH-39",
                        implementation_id="MATH-39::IMPLEMENTATION::MISMATCH",
                    ),
                ),
            ),
        )
    )
    assert pin_mismatch.status is OperationStatusV1.BLOCKED
    assert pin_mismatch.component_result.formula_output is None
    assert ReasonCode.DEPENDENCY_CLOSURE_FAILED.value in pin_mismatch.receipt_refs


def test_receipt_spine_and_svc_projection_are_one_way_no_effect_views(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _inputs()
    result = evaluate_mode_snapshot_candidate(inputs)
    receipts = materialize_mode_snapshot_control_receipts(
        result,
        parameter_value_refs=inputs.parameter_value_refs,
        effective_at=inputs.evaluated_at,
        recorded_at=inputs.evaluated_at,
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        tracestate="vendor=value",
    )
    assert tuple(row.typed_payload.control_class for row in receipts) == (
        ModeSnapshotControlClassV1.MODE_SNAPSHOT_EVALUATION,
        ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_BUILD,
        ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_VALIDATION,
    )
    assert all(row.record_type is EconomicRecordTypeV1.MODE_SNAPSHOT_CONTROL for row in receipts)
    assert all(type(row.typed_payload) is ModeSnapshotControlReceiptRecordV1 for row in receipts)
    assert all(row.typed_payload.no_order_authority_flag is True for row in receipts)
    expected_stage_transitions = (
        (ModeSnapshotControlClassV1.MODE_SNAPSHOT_EVALUATION, "T07"),
        (ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_BUILD, "T08"),
        (ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_VALIDATION, "T09"),
    )
    assert tuple(
        (row.typed_payload.control_class, row.typed_payload.transition_id)
        for row in receipts
    ) == expected_stage_transitions
    trace_by_id = {
        proposal.transition_id: proposal
        for proposal in result.executed_transition_trace.proposals
    }
    for receipt, (_control_class, transition_id) in zip(
        receipts, expected_stage_transitions, strict=True
    ):
        proposal = trace_by_id[transition_id]
        assert (
            receipt.typed_payload.transition_proposal_ref,
            receipt.typed_payload.source_state,
            receipt.typed_payload.destination_state,
            receipt.typed_payload.typed_reason_codes,
            receipt.typed_payload.predecessor_transition_receipt_refs,
        ) == (
            proposal.proposal_id,
            proposal.source_state,
            proposal.destination_state,
            proposal.typed_reason_codes,
            proposal.predecessor_transition_receipt_refs,
        )
    with pytest.raises(ContractValidationError):
        replace(
            result,
            control_receipt_refs=tuple(row.record_id for row in receipts),
            control_receipt_proposals=(
                receipts[0],
                replace(
                    receipts[1],
                    typed_payload=replace(
                        receipts[1].typed_payload,
                        transition_proposal_ref=result.snapshot_transition_proposal.proposal_id,
                        transition_id=result.snapshot_transition_proposal.transition_id,
                        source_state=result.snapshot_transition_proposal.source_state,
                        destination_state=result.snapshot_transition_proposal.destination_state,
                        typed_reason_codes=result.snapshot_transition_proposal.typed_reason_codes,
                    ),
                ),
                receipts[2],
            ),
        )
    assert all(
        row.no_effect_flags.mode_or_allow_activation_allowed is False
        and row.no_effect_flags.order_release_allowed is False
        and row.no_effect_flags.capital_mutation_allowed is False
        and row.no_effect_flags.provider_connection_allowed is False
        and row.no_effect_flags.private_state_read_allowed is False
        and row.no_effect_flags.replay_or_paper_execution_allowed is False
        and row.no_effect_flags.llm_inference_allowed is False
        and row.no_effect_flags.qpu_execution_allowed is False
        for row in receipts
    )

    direct = owner_projection(
        result.mode_snapshot_decision,
        inputs.evidence_reference,
        inputs.kill_submit_state,
        snapshot_version=inputs.candidate_version,
    )
    adapter = ExistingOwnerProjectionAdapterV1(_repo_root())
    preloaded_owner_projections = adapter.load_bundle()
    assert type(preloaded_owner_projections) is PreloadedOwnerProjectionBundleV1
    svc = OwnerProjectionViewV1(
        owner_id="SVC1",
        authority_domain="OWNER_READ_MODEL_AND_ACTION_PROJECTION",
        source_path="src/qtt/service/pr169_svc1_resolvers.py",
        source_version="SVC1::CURRENT",
        source_snapshot_ref="src/qtt/service/pr169_svc1_resolvers.py",
        consume_interfaces=("DashboardReadModelService",),
        row_count=1,
        identity_refs=("read_model_snapshots.generated.jsonl",),
    )
    projected = adapter.project_mode_snapshot(
        result.mode_snapshot_decision,
        inputs.evidence_reference,
        inputs.kill_submit_state,
        snapshot_version=inputs.candidate_version,
        svc_view=svc,
    )
    assert projected == direct
    assert projected.runtime_effect_authorized is False
    assert projected.order_release_authorized is False
    assert svc.projection_mutation_allowed is False

    operation_id = "submit_candidate_proposal"
    bundle, _audit_registry = _audit_bundle_fixture()
    context = bundle.execution_context
    admitted = resolve_decision(
        make_resolver(
            operation_id=operation_id,
            envelope_overrides={
                "context_ref": context.context_id,
                "idempotency_key": "IDEMPOTENCY::D::SERVICE",
            },
        ),
        request_id="REQUEST::D::SERVICE",
        operation_id=operation_id,
        context_ref=context.context_id,
        requested_scope_refs={
            "qku_scope_refs": ("QKU::ST12E::TEST",),
            "formula_scope_refs": ("MATH-01",),
        },
        request_idempotency_key="IDEMPOTENCY::D::SERVICE",
    )
    class _Admission:
        def admit_operation(self, _request: object):
            return admitted

    proposal_record = TypedValueRecordV1(
        (
            TypedValueV1(
                name="candidate_contract_id",
                kind=TypedValueKindV1.TEXT,
                value=MODE_SNAPSHOT_CANDIDATE_KIND,
                unit="identity",
                basis="canonical",
            ),
        )
    )
    request = SubmitCandidateProposalRequestV1(
        request_id=admitted.request_id,
        operation_name=operation_id,
        requested_at=context.as_of,
        principal_id=admitted.principal_id,
        capability_bundle_id="CAPABILITY::D::SERVICE",
        context=context,
        idempotency_key=admitted.idempotency_key,
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        tracestate="vendor=value",
        candidate_kind=MODE_SNAPSHOT_CANDIDATE_KIND,
        proposed_specification=proposal_record,
        source_candidate_refs=("SOURCE-CANDIDATE::D::SERVICE",),
        requested_owner_review=True,
    )
    _bundle, owner_registry = _current_owner_registry(admitted)
    current_resolver = CurrentModeSnapshotInputResolverV1(
        repo_root=_repo_root(),
        owner_registry=owner_registry,
    )

    late_calls = 0

    def _forbid_pre_f_enrichment(*_args: object) -> object:
        nonlocal late_calls
        late_calls += 1
        raise AssertionError("late D enrichment entered the T03 HOTPATH")

    monkeypatch.setattr(
        current_resolver,
        "enrich_mode_snapshot_candidate",
        _forbid_pre_f_enrichment,
    )
    service = QKUComputationControlPlaneV1(
        owner_registry,
        agent_capability_resolver=_Admission(),
        mode_snapshot_input_resolver=current_resolver,
        latency_budget_profile=LatencyBudgetProfileV1(
            profile_id="LATENCY-PROFILE::D::SERVICE",
            component_budget_ns=tuple((name, 10**12) for name in STAGE_NAMES),
            histogram_boundaries_ns=(1, 10**6, 10**12),
            maximum_observer_overhead_ns=10**9,
            alert_threshold_ns=10**12,
            policy_version="LATENCY-POLICY::D::SERVICE",
        ),
        resource_bounds_profile=ResourceBoundsProfileV1(
            profile_id="RESOURCE-BOUNDS::D::SERVICE",
            maximum_input_cardinality=32,
            maximum_input_bytes=100_000,
            maximum_dependency_depth=16,
            maximum_bootstrap_repetitions=1,
            maximum_concurrency=1,
        ),
    )
    def _forbid_hotpath_file_read(*_args: object, **_kwargs: object) -> str:
        raise AssertionError("repository file read entered the D request HOTPATH")

    monkeypatch.setattr(Path, "read_text", _forbid_hotpath_file_read)
    response = service.submit_candidate_proposal(request)
    assert response.status is OperationStatusV1.BLOCKED
    assert response.proposal.mode_snapshot_result is not None
    service_result = response.proposal.mode_snapshot_result
    assert service_result.no_authority_flag is True
    assert service_result.snapshot_transition_proposal.transition_id == "T03"
    assert tuple(
        row.transition_id
        for row in service_result.executed_transition_trace.proposals
    ) == ("T03",)
    assert service_result.snapshot_candidate_or_explicit_absence is None
    assert service_result.mode_snapshot_decision.reason_codes == (
        ReasonCode.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED,
    )
    assert len(service_result.control_receipt_refs) == 1
    assert service_result.owner_projection_or_explicit_absence is None
    assert service_result.latency_measurement_or_explicit_absence is not None
    assert tuple(
        row.record_id for row in service_result.control_receipt_proposals
    ) == service_result.control_receipt_refs
    assert response.receipt_refs == (
        *service_result.control_receipt_refs,
        service_result.latency_measurement_or_explicit_absence.measurement_ref,
    )
    assert late_calls == 0

    class _CustomEvidenceAvailableResolver:
        gate_calls = 0
        enrich_calls = 0
        evidence_reference = _inputs().evidence_reference

        def resolve_mode_snapshot_preconstruction_gate(self, *_args: object):
            self.gate_calls += 1
            raise AssertionError("custom resolver reached the production D gate")

        def enrich_mode_snapshot_candidate(self, *_args: object):
            self.enrich_calls += 1
            raise AssertionError("custom resolver reached production D enrichment")

    custom_resolver = _CustomEvidenceAvailableResolver()
    custom_service = QKUComputationControlPlaneV1(
        owner_registry,
        agent_capability_resolver=_Admission(),
        mode_snapshot_input_resolver=custom_resolver,
    )
    with pytest.raises(OwnerAdapterError):
        custom_service.submit_candidate_proposal(request)
    assert (custom_resolver.gate_calls, custom_resolver.enrich_calls) == (0, 0)

    wrong_registry_resolver = CurrentModeSnapshotInputResolverV1(
        repo_root=_repo_root(),
        owner_registry=CanonicalOwnerPacketRegistryV1(owner_registry.packets),
    )
    wrong_registry_service = QKUComputationControlPlaneV1(
        owner_registry,
        agent_capability_resolver=_Admission(),
        mode_snapshot_input_resolver=wrong_registry_resolver,
    )
    with pytest.raises(OwnerAdapterError):
        wrong_registry_service.submit_candidate_proposal(request)

    held_result = evaluate_mode_snapshot_candidate(_inputs(owner_confirmation=False))
    latency_result = finalize_mode_snapshot_latency_block(result)
    validated_candidate = result.snapshot_candidate_or_explicit_absence
    assert validated_candidate is not None
    build_proposal = result.executed_transition_trace.proposals[0]
    rejected_proposal = build_snapshot_transition_proposal(
        proposal_id=f"{build_proposal.proposal_id}::T10",
        request_id=build_proposal.request_id,
        principal_id=build_proposal.principal_id,
        task_id=build_proposal.task_id,
        capability_decision_ref=build_proposal.capability_decision_ref,
        context_ref=build_proposal.context_ref,
        source_candidate_ref_or_explicit_absence=(
            build_proposal.target_candidate_ref
        ),
        target_candidate_ref=build_proposal.target_candidate_ref,
        source_candidate_version_or_explicit_absence=(
            build_proposal.target_candidate_version
        ),
        target_candidate_version=build_proposal.target_candidate_version,
        transition_id="T10",
        expected_owner_state_ref=build_proposal.expected_owner_state_ref,
        precondition_receipt_refs=build_proposal.precondition_receipt_refs,
        proposed_state=SnapshotCandidateStateV1.REJECTED,
        causation_id=build_proposal.causation_id,
        correlation_id=build_proposal.correlation_id,
    )
    rejected_trace = ExecutedModeSnapshotTransitionTraceV1(
        (build_proposal, rejected_proposal)
    )
    rejected_result = ModeSnapshotCandidateProposalResultV1(
        snapshot_candidate_or_explicit_absence=None,
        mode_snapshot_decision=replace(
            result.mode_snapshot_decision,
            mode_eligibility_state=ModeEligibilityState.INELIGIBLE,
            allow_candidate_state=AllowCandidateStateV1.BLOCKED,
            snapshot_candidate_state=SnapshotCandidateStateV1.REJECTED,
            activation_precondition_state=(
                ActivationPreconditionStateV1.PRECONDITIONS_INCOMPLETE
            ),
            reason_codes=(ReasonCode.SNAPSHOT_CANDIDATE_INVALID,),
            fallback_route="BLOCK",
            owner_review_route="CURRENT_INPUT_OWNER_REVALIDATION",
        ),
        snapshot_transition_proposal=rejected_proposal,
        executed_transition_trace=rejected_trace,
        control_receipt_refs=(),
    )
    evidence_unavailable_result = evaluate_mode_snapshot_candidate(
        _inputs(
            evidence_state=(
                ST12FEvidenceStateV1.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED
            )
        )
    )
    stale_result = evaluate_mode_snapshot_candidate(
        _inputs(evidence_state=ST12FEvidenceStateV1.EVIDENCE_REFERENCE_STALE)
    )
    safety_result = evaluate_mode_snapshot_candidate(_inputs(kill_active=True))
    valid_terminal_rows = (
        (
            evidence_unavailable_result,
            ("T03",),
            False,
            AllowCandidateStateV1.EVIDENCE_UNAVAILABLE,
            SnapshotCandidateStateV1.ABSENT,
        ),
        (
            stale_result,
            ("T04",),
            False,
            AllowCandidateStateV1.BLOCKED,
            SnapshotCandidateStateV1.ABSENT,
        ),
        (
            safety_result,
            ("T05",),
            False,
            AllowCandidateStateV1.BLOCKED,
            SnapshotCandidateStateV1.ABSENT,
        ),
        (
            held_result,
            ("T08", "T09", "T06"),
            True,
            AllowCandidateStateV1.OWNER_CONFIRMATION_REQUIRED,
            SnapshotCandidateStateV1.VALIDATED_NO_EFFECT,
        ),
        (
            result,
            ("T08", "T09", "T07"),
            True,
            AllowCandidateStateV1.ELIGIBLE_NOT_ACTIVATED,
            SnapshotCandidateStateV1.VALIDATED_NO_EFFECT,
        ),
        (
            rejected_result,
            ("T08", "T10"),
            False,
            AllowCandidateStateV1.BLOCKED,
            SnapshotCandidateStateV1.REJECTED,
        ),
        (
            latency_result,
            ("T08", "T09", "T04"),
            True,
            AllowCandidateStateV1.BLOCKED,
            SnapshotCandidateStateV1.VALIDATED_NO_EFFECT,
        ),
    )
    for (
        traced_result,
        expected_trace,
        candidate_required,
        expected_allow_state,
        expected_snapshot_state,
    ) in valid_terminal_rows:
        assert tuple(
            row.transition_id
            for row in traced_result.executed_transition_trace.proposals
        ) == expected_trace
        assert (
            traced_result.snapshot_candidate_or_explicit_absence is not None
        ) is candidate_required
        assert (
            traced_result.mode_snapshot_decision.allow_candidate_state
            is expected_allow_state
        )
        assert (
            traced_result.mode_snapshot_decision.snapshot_candidate_state
            is expected_snapshot_state
        )
        assert (
            traced_result.snapshot_transition_proposal
            is traced_result.executed_transition_trace.final_proposal
        )
        assert (
            traced_result.snapshot_transition_proposal.typed_reason_codes
            == traced_result.mode_snapshot_decision.reason_codes
        )

    t08_only_trace = ExecutedModeSnapshotTransitionTraceV1((build_proposal,))
    decision_field_mutations = (
        (result, "request_id", "REQUEST::D::MISMATCH"),
        (result, "principal_id", "principal_mismatch"),
        (result, "task_id", "TASK::D::MISMATCH"),
        (result, "capability_decision_ref", "CAPABILITY::D::MISMATCH"),
        (result, "context_ref", "CONTEXT::D::MISMATCH"),
        (result, "receipt_lineage_refs", ("RECEIPT::D::MISMATCH",)),
        (
            latency_result,
            "reason_codes",
            tuple(reversed(latency_result.mode_snapshot_decision.reason_codes)),
        ),
        (result, "fallback_route", "BLOCK"),
        (result, "allow_candidate_state", AllowCandidateStateV1.BLOCKED),
        (
            result,
            "snapshot_candidate_state",
            SnapshotCandidateStateV1.BUILT_IMMUTABLE,
        ),
        (
            rejected_result,
            "snapshot_candidate_state",
            SnapshotCandidateStateV1.ABSENT,
        ),
    )
    candidate_field_mutations = (
        ("snapshot_candidate_id", "SNAPSHOT-CANDIDATE::D::MISMATCH"),
        ("request_id", "REQUEST::D::MISMATCH"),
        ("principal_id", "principal_mismatch"),
        ("task_id", "TASK::D::MISMATCH"),
        ("capability_decision_ref", "CAPABILITY::D::MISMATCH"),
        ("computation_bundle_ref", "SNAPSHOT-BUNDLE::D::MISMATCH"),
        ("context_ref", "CONTEXT::D::MISMATCH"),
        (
            "implementation_version_pins",
            (
                replace(
                    validated_candidate.implementation_version_pins[0],
                    implementation_id="IMPLEMENTATION::D::MISMATCH",
                ),
                *validated_candidate.implementation_version_pins[1:],
            ),
        ),
        ("parameter_policy_snapshot_ref", "PARAMETER-POLICY::D::MISMATCH"),
        ("source_epoch_refs", ("SOURCE-EPOCH::D::MISMATCH",)),
        ("receipt_lineage_refs", ("RECEIPT::D::MISMATCH",)),
        ("readiness_state_ref", "READINESS::D::MISMATCH"),
        ("pretrade_state_ref", "PRETRADE1::D::MISMATCH"),
        ("evidence_state_ref", "EVIDENCE::D::MISMATCH"),
        ("kill_state_ref", "KILL::D::MISMATCH"),
        ("submit_disabled_state_ref", "SUBMIT-DISABLED::D::MISMATCH"),
        ("expires_at", validated_candidate.expires_at + timedelta(seconds=1)),
        ("candidate_state", SnapshotCandidateStateV1.BUILT_IMMUTABLE),
    )
    outcome_contradiction_matrix = (
        lambda: replace(
            held_result, snapshot_candidate_or_explicit_absence=None
        ),
        lambda: replace(
            evidence_unavailable_result,
            snapshot_candidate_or_explicit_absence=validated_candidate,
        ),
        lambda: replace(
            stale_result,
            snapshot_candidate_or_explicit_absence=validated_candidate,
        ),
        lambda: replace(
            safety_result,
            snapshot_candidate_or_explicit_absence=validated_candidate,
        ),
        lambda: replace(
            rejected_result,
            snapshot_candidate_or_explicit_absence=validated_candidate,
        ),
        lambda: replace(
            result,
            snapshot_transition_proposal=t08_only_trace.final_proposal,
            executed_transition_trace=t08_only_trace,
        ),
        *(
            lambda base=base, field_name=field_name, value=value: replace(
                base,
                mode_snapshot_decision=replace(
                    base.mode_snapshot_decision,
                    **{field_name: value},
                ),
            )
            for base, field_name, value in decision_field_mutations
        ),
        *(
            lambda field_name=field_name, value=value: replace(
                result,
                snapshot_candidate_or_explicit_absence=replace(
                    validated_candidate,
                    **{field_name: value},
                ),
            )
            for field_name, value in candidate_field_mutations
        ),
    )
    for contradiction in outcome_contradiction_matrix:
        with pytest.raises(ContractValidationError):
            contradiction()

    latency_receipts = materialize_mode_snapshot_control_receipts(
        latency_result,
        parameter_value_refs=inputs.parameter_value_refs,
        effective_at=inputs.evaluated_at,
        recorded_at=inputs.evaluated_at,
        traceparent=request.traceparent,
        tracestate=request.tracestate,
    )
    assert tuple(
        row.typed_payload.transition_id for row in latency_receipts
    ) == ("T04", "T08", "T09")

    non_d = service.submit_candidate_proposal(
        replace(
            request,
            candidate_kind="FORMULA_SUCCESSOR",
            proposed_specification=TypedValueRecordV1(
                (
                    TypedValueV1(
                        name="candidate_state",
                        kind=TypedValueKindV1.TEXT,
                        value="PROVISIONAL",
                        unit="identity",
                        basis="canonical",
                    ),
                )
            ),
        )
    )
    assert non_d.proposal.mode_snapshot_result is None


def test_generated_d_universe_and_connectivity_are_terminal_reference_only() -> None:
    root = _repo_root()
    generated = root / "docs/master_plan/generated/qku_control_plane/mode_snapshot"
    assert tuple(
        str(path.relative_to(root)).replace("\\", "/")
        for path in sorted(generated.glob("*"))
    ) == tuple(sorted(ST12D_GENERATED_PROJECTION_PATHS))
    manifest = json.loads((generated / "manifest.json").read_text(encoding="utf-8"))
    universe = _jsonl(generated / "d_input_universe.jsonl")
    connectivity = _jsonl(generated / "artifact_connectivity.jsonl")
    assert manifest["acceptance_counts"] == dict(st12d_acceptance_counts())
    assert len(ST12D_CLOSURE_ROWS) == 23
    assert len(ST12D_HISTORICAL_PATH_DISPOSITIONS) == 7
    assert len(ST12D_SEMANTIC_TEST_ROWS) == 26
    assert len(ST12D_ACTUAL_CONTROL_MUTATION_CASES) == 23
    control_results = tuple(
        run_st12d_actual_control_mutation_case(control_id)
        for control_id in ST12D_ACTUAL_CONTROL_MUTATION_CASES
    )
    assert all(
        result.positive_passed
        and result.actual_mutation_rejected
        and result.positive_terminal_state
        != result.negative_reason_or_terminal_state
        for result in control_results
    )
    assert all(
        adjudicate_st12d_semantic_test(str(row["test_id"]))
        for row in ST12D_SEMANTIC_TEST_ROWS
    )
    assert universe and connectivity
    assert all(row["terminal_disposition"] != "UNRESOLVED" for row in universe)
    assert all(row["consumption_status"] == "TERMINAL" for row in connectivity)
    assert {row["artifact_ref"] for row in connectivity} >= {
        row["member_ref"] for row in universe
    }
    assert not {
        "decision_quality_artifact_classes.jsonl",
        "agent_consumption_routes.jsonl",
        "external_candidate_ledger.jsonl",
        "owner_workflow_ledger.jsonl",
        "llm_routes.jsonl",
        "quantum_backend_snapshots.jsonl",
    }.intersection(path.name for path in generated.iterdir())
    summary = json.loads(
        (generated / "validation_summary.json").read_text(encoding="utf-8")
    )
    assert summary["actual_control_mutation_case_count"] == 23
    assert summary["semantic_test_identity_count"] == 26
    assert summary["synthetic_override_mutation_count"] == 0
    runtime_rows = tuple(
        row
        for row in connectivity
        if row["artifact_or_row_class"] == "runtime_no_effect_output"
    )
    assert len(runtime_rows) == 8
    assert all(
        row["consumer_acknowledgment_ref_or_explicit_absence"]
        != "EXPLICIT_ABSENCE"
        and all(
            "independent_validate" not in consumer
            for consumer in row["downstream_consumer_refs"]
        )
        for row in runtime_rows
    )
    assert summary["external_candidate_discovery_count"] == 0
    assert all(
        count == 0
        for count in summary[
            "provider_private_replay_paper_llm_qpu_counts"
        ].values()
    )

    launch_exports = (
        "STAGE1_LAUNCH_DEPENDENCY_EDGES_V1",
        "STAGE1_LAUNCH_ROLES_V2",
        "STAGE1_OPERATION_DEPENDENCY_PROFILES_V1",
        "STAGE1_SELECTED_PROFILE_IDS_V2",
        "STAGE1_SELECTED_SCOPE_V2",
        "build_stage1_launch_graph_v2",
        "stage1_launch_graph_projection_v2",
        "validate_stage1_launch_graph_v2",
    )
    assert len(launch_exports) == 8
    assert tuple(qku_control_plane.__all__[-12:-4]) == launch_exports
    assert all(qku_control_plane.__all__.count(name) == 1 for name in launch_exports)
    assert all(hasattr(qku_control_plane, name) for name in launch_exports)
    assert not {
        "Stage1VenueProfileV1",
        "Stage1SelectedScopeV2",
        "SelectedLaunchGraphV2",
        "_STAGE1_VENUE_PROFILE_ROWS_JSON",
    }.intersection(qku_control_plane.__all__)
    first_payload = build_payload()
    second_payload = build_payload()
    assert tuple(first_payload).count("stage1_launch_graph_v2") == 1
    assert tuple(first_payload).count("selected_component_package_v1") == 1
    payload_keys = tuple(first_payload)
    launch_key_index = payload_keys.index("stage1_launch_graph_v2")
    assert payload_keys[launch_key_index + 1] == "selected_component_package_v1"
    assert set(first_payload["stage1_launch_graph_v2"]) == {
        "package_ref",
        "graph",
        "validation",
    }
    assert (
        first_payload["stage1_launch_graph_v2"]
        == second_payload["stage1_launch_graph_v2"]
        == qku_control_plane.stage1_launch_graph_projection_v2()
    )
    package_projection = first_payload["selected_component_package_v1"]
    assert tuple(package_projection) == (
        "manifest",
        "compatibility_and_dependency",
        "rollback_and_supersession",
        "reproducibility",
    )
    assert package_projection == second_payload["selected_component_package_v1"]
    assert package_projection == (
        qku_control_plane.SelectedComponentPackageAdapterV1.build_projection(
            first_payload["stage1_launch_graph_v2"]
        )
    )
    view = qku_control_plane.SelectedComponentPackageAdapterV1.build_view(
        first_payload["stage1_launch_graph_v2"]
    )
    repeated_view = qku_control_plane.SelectedComponentPackageAdapterV1.build_view(
        first_payload["stage1_launch_graph_v2"]
    )
    assert view == repeated_view
    assert view.package_id == "S1-PLUGIN-PACKAGE-CURRENTIZATION-01"
    assert view.package_version == "1.0.0"
    assert (
        view.entry_count,
        view.admitted_count,
        view.evidence_held_count,
        view.implementation_held_count,
        view.edge_count,
        view.operation_count,
    ) == (28, 11, 5, 12, 102, 5)
    assert view.selected_profile_ids == (
        "GEMINI_TITAN_DIRECT",
        "POLYMARKET_US_RETAIL_DIRECT",
        "KALSHI_US_DCM_DIRECT",
    )
    assert view.excluded_profile_ids == (
        "FORECASTEX_IBKR",
        "FORECASTEX_DIRECT_MEMBER",
    )
    assert view.active_live_profile_ids == ()
    assert tuple(len(row.blocking_component_ids) for row in view.operations) == (
        16,
        2,
        7,
        12,
        5,
    )
    assert view.no_effects is NO_EFFECTS_V1

    normalized_projection = _qku_projection_serialization_value(
        package_projection
    )
    assert safe_json_loads(view.canonical_projection_json) == (
        normalized_projection
    )
    serializable_payload = dict(first_payload)
    serializable_payload["selected_component_package_v1"] = (
        normalized_projection
    )
    complete_payload_json = deterministic_json(serializable_payload)
    assert safe_json_loads(complete_payload_json) == json.loads(
        complete_payload_json
    )

    accepted_path_payloads = (
        {"path": "docs/master_plan/generated/example.json"},
        {"optional_path": None},
        {
            "manifest": {
                "entries": [
                    {
                        "existing_owner_paths": [],
                        "future_owner_paths": [],
                    }
                ]
            }
        },
        {"manifest": {"authority_envelope": {"no_llm_hot_path": True}}},
        {"manifest": {"authority_envelope": {"no_llm_hot_path": False}}},
    )
    for accepted_path_payload in accepted_path_payloads:
        encoded_path_payload = deterministic_json(accepted_path_payload)
        assert safe_json_loads(encoded_path_payload) == accepted_path_payload

    class PathTextSubclass(str):
        pass

    class PathListSubclass(list):
        pass

    class PathKeySubclass(str):
        pass

    rejected_path_payloads = (
        {"numeric_path": 1},
        {"boolean_path": True},
        {"unknown_paths": []},
        {"manifest": {"no_llm_hot_path": True}},
        {"manifest": {"authority_envelope": {"No_Llm_Hot_Path": True}}},
        {"manifest": {"entries": [{"existing_owner_paths": None}]}},
        {"existing_owner_paths": []},
        {"absolute_path": "C:/owner/private.json"},
        {"reserved_path": "CON"},
        {"subclass_path": PathTextSubclass("docs/example.json")},
        {"subclass_paths": PathListSubclass(["docs/example.json"])},
        {PathKeySubclass("path"): "docs/example.json"},
        {"api_key": "secret-material"},
    )
    for rejected_path_payload in rejected_path_payloads:
        with pytest.raises(SerializationSafetyError):
            deterministic_json(rejected_path_payload)
    with pytest.raises(SerializationSafetyError) as normalized_numeric_path:
        deterministic_json(
            _qku_projection_serialization_value({"numeric_path": 1})
        )
    assert normalized_numeric_path.value.reason_code is ReasonCode.PATH_UNSAFE
    with pytest.raises(SerializationSafetyError) as duplicate_key:
        safe_json_loads('{"path":"docs/a.json","path":"docs/b.json"}')
    assert duplicate_key.value.reason_code is ReasonCode.SERIALIZATION_UNSAFE
    with pytest.raises(SerializationSafetyError) as reader_secret:
        safe_json_loads('{"api_key":"secret-material"}')
    assert reader_secret.value.reason_code is ReasonCode.SECRET_MATERIAL_REJECTED

    altered_launch_projection = deepcopy(
        first_payload["stage1_launch_graph_v2"]
    )
    altered_launch_projection["graph"]["roles"][26]["latency_class"] = (
        "WRONG_NONEMPTY_LATENCY_CLASS"
    )
    with pytest.raises(OwnerAdapterError) as altered_launch_error:
        qku_control_plane.SelectedComponentPackageAdapterV1.build_projection(
            altered_launch_projection
        )
    assert altered_launch_error.value.reason_code is (
        ReasonCode.OWNER_DATA_CONTRADICTORY
    )
    assert isinstance(
        altered_launch_error.value.__cause__,
        PluginPackageContractError,
    )

    independent_core = _independent_selected_component_package_core_v1()
    actual_core = MappingProxyType(
        {
            "manifest": package_projection["manifest"],
            "compatibility_and_dependency": package_projection[
                "compatibility_and_dependency"
            ],
            "rollback_and_supersession": package_projection[
                "rollback_and_supersession"
            ],
        }
    )
    oracle_json = json.dumps(
        independent_core,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    production_json = _canonical_package_json(actual_core)
    assert production_json.encode("utf-8") == oracle_json.encode("utf-8")
    normalized_actual_core = _normalize_package_serialization_value(actual_core)
    assert normalized_actual_core == independent_core
    assert len(independent_core["manifest"]) == 17
    assert len(independent_core["manifest"]["entries"]) == 28
    assert all(
        len(entry) == 21 for entry in independent_core["manifest"]["entries"]
    )
    assert len(independent_core["compatibility_and_dependency"]) == 10
    assert len(independent_core["rollback_and_supersession"]) == 11
    assert all(
        len(operation) == 6
        for operation in independent_core["manifest"][
            "operation_eligibility_rows"
        ]
    )
    assert len(independent_core["manifest"]["authority_envelope"]) == 16

    reproducibility = package_projection["reproducibility"]
    normalized_reproducibility = _normalize_package_serialization_value(
        reproducibility
    )
    assert set(normalized_reproducibility) == {
        field.name for field in fields(generic_plugins.PackageReproducibilityReceiptV1)
    }
    assert len(normalized_reproducibility) == 12
    assert normalized_reproducibility == {
        "package_id": independent_core["manifest"]["package_id"],
        "package_version": independent_core["manifest"]["package_version"],
        "canonical_input_refs": [
            "S1-LAUNCH-GRAPH-MATERIALIZATION-01",
            "SELECTED_LAUNCH_GRAPH_V2",
            "STAGE1_SELECTED_SCOPE_V2",
        ],
        "builder_runtime_implementation": "CPython",
        "builder_runtime_version": "3.14.6",
        "canonical_serialization_policy": independent_core["manifest"][
            "canonical_serialization_policy"
        ],
        "canonical_core_projection_json": oracle_json,
        "second_build_byte_equal": True,
        "pure_build_effect_count": 0,
        "terminal_state": "VALIDATED_NO_EFFECT_WITH_HELD_DEPENDENCIES",
        "reason_codes": [],
        "authority_envelope": independent_core["manifest"][
            "authority_envelope"
        ],
    }

    omitted_entry_field_mutations = {
        "compatibility_state": "WRONG_COMPATIBILITY_STATE",
        "compatibility_reason_codes": ["IMPLEMENTATION_MISSING"],
        "existing_owner_paths": list(
            reversed(
                independent_core["manifest"]["entries"][0][
                    "existing_owner_paths"
                ]
            )
        ),
        "future_owner_paths": ["src/wrong/future_owner.py"],
        "canonical_output_contract": "WRONG_NONEMPTY_OUTPUT_CONTRACT",
        "default_failure_route": "WRONG_NONEMPTY_FAILURE_ROUTE",
        "latency_class": "WRONG_NONEMPTY_LATENCY_CLASS",
        "authority_envelope_id": "WRONG_AUTHORITY_ENVELOPE",
    }
    assert len(omitted_entry_field_mutations) == 8
    for field_name, mutation_value in omitted_entry_field_mutations.items():
        mutated_core = deepcopy(normalized_actual_core)
        mutated_core["manifest"]["entries"][0][field_name] = mutation_value
        assert json.dumps(
            mutated_core,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ) != oracle_json

    assert _selected_component_package_failures() == []
    registry_path = root / "src/qtt/plugins/registry.py"
    registry_text = registry_path.read_text(encoding="utf-8")
    output_anchor = 'canonical_output_contract=role["frozen_output"],'
    assert registry_text.count(output_anchor) == 1
    mutated_registry_text = registry_text.replace(
        output_anchor,
        'canonical_output_contract="WRONG_NONEMPTY_OUTPUT_CONTRACT",',
        1,
    )
    original_read_text = Path.read_text

    def in_memory_registry_read(
        path: Path,
        *args: object,
        **kwargs: object,
    ) -> str:
        if path.resolve() == registry_path.resolve():
            return mutated_registry_text
        return original_read_text(path, *args, **kwargs)

    with patch.object(Path, "read_text", in_memory_registry_read):
        mutation_failures = _selected_component_package_failures()
    assert mutation_failures
    assert any("entry constructor binding" in failure for failure in mutation_failures)

    # Append inside the existing grouped integration function. These deliberately
    # unique local aliases do not rebind any existing module-level serializer name.
    import json as _pr292_json
    import pathlib as _pr292_pathlib
    from unittest import mock as _pr292_mock
    import tools.build_qku_computation_control_plane as _pr292_builder
    import src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy as _pr292_policy
    import src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization as _pr292_serialization
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
        AuthorityDeniedError as _pr292_denied,
        ReasonCode as _pr292_reason,
    )

    _pr292_manifest_path = (
        _pr292_builder.REPO_ROOT
        / 'docs/master_plan/generated/qku_control_plane/agent_capability/manifest.json'
    )
    _pr292_persisted_bytes = _pr292_manifest_path.read_bytes()
    _pr292_generated = _pr292_builder.build_st12e_projections()[0]
    assert _pr292_persisted_bytes == (
        _pr292_serialization.deterministic_json(_pr292_generated) + '\n'
    ).encode('utf-8')
    assert type(_pr292_generated['implemented_operation_ids']) is list
    assert type(_pr292_generated['held_operation_ids']) is list
    assert tuple(_pr292_generated['implemented_operation_ids']) == _pr292_policy.IMPLEMENTED_OPERATION_IDS
    assert tuple(_pr292_generated['held_operation_ids']) == _pr292_policy.HELD_OPERATION_IDS == ()
    assert len(_pr292_policy.IMPLEMENTED_OPERATION_IDS) == len(set(_pr292_policy.IMPLEMENTED_OPERATION_IDS)) == 15
    assert _pr292_generated['activation_state'] == 'NO_EFFECT_CONTRACT_ONLY'
    assert _pr292_generated['runtime_effect_authorized'] is False
    assert _pr292_generated['manual_edit_allowed'] is False
    assert _pr292_generated['llm_inference_allowed'] is False
    assert _pr292_generated['quantum_mapping_or_execution_allowed'] is False
    assert _pr292_generated['qku_formula_mutation_authorized'] is False
    assert _pr292_generated['no_effect_authority_closed'] is True
    assert _pr292_generated['final_release_owner'] == 'ExecutionRouterV1'
    assert _pr292_generated['no_effect_authority_flags']
    assert all(type(flag) is bool and flag is False for flag in _pr292_generated['no_effect_authority_flags'].values())

    # Use the actual persisted reader. Do not mock the loader or its authority gates.
    _pr292_store = _pr292_policy.AgentCapabilityPolicyStoreV1.from_generated(_pr292_builder.REPO_ROOT)
    assert type(_pr292_store) is _pr292_policy.AgentCapabilityPolicyStoreV1
    assert type(_pr292_store.snapshot) is _pr292_policy.AgentCapabilityPolicySnapshotV1
    assert _pr292_store.snapshot.policy_version == _pr292_policy.POLICY_VERSION

    # Only the exact manifest text is substituted in memory. All source, policy,
    # parameter and orchestration reads still delegate to the original file reader.
    _pr292_original_read = _pr292_pathlib.Path.read_text
    _pr292_missing = object()
    _pr292_bad_rosters = (
        {'implemented_operation_ids': list(_pr292_policy._PRE_ST12F_IMPLEMENTED_OPERATION_IDS),
         'held_operation_ids': list(_pr292_policy._PRE_ST12F_HELD_OPERATION_IDS)},
        {'implemented_operation_ids': _pr292_missing},
        {'held_operation_ids': _pr292_missing},
        {'implemented_operation_ids': None},
        {'held_operation_ids': None},
        {'implemented_operation_ids': list(reversed(_pr292_policy.IMPLEMENTED_OPERATION_IDS))},
        {'implemented_operation_ids': list(_pr292_policy.IMPLEMENTED_OPERATION_IDS) + [_pr292_policy.IMPLEMENTED_OPERATION_IDS[0]]},
        {'implemented_operation_ids': [True, *_pr292_policy.IMPLEMENTED_OPERATION_IDS[1:]]},
        {'implemented_operation_ids': {'unexpected': 'mapping'}},
        {'held_operation_ids': ''},
        {'held_operation_ids': ['submit_order']},
        {'runtime_effect_authorized': True},
        {'llm_inference_allowed': True},
    )
    for _pr292_change in _pr292_bad_rosters:
        _pr292_mutated = _pr292_json.loads(_pr292_persisted_bytes.decode('utf-8'))
        for _pr292_key, _pr292_value in _pr292_change.items():
            if _pr292_value is _pr292_missing:
                del _pr292_mutated[_pr292_key]
            else:
                _pr292_mutated[_pr292_key] = _pr292_value
        _pr292_mutated_text = _pr292_json.dumps(_pr292_mutated, allow_nan=False)
        with _pr292_mock.patch.object(
            _pr292_pathlib.Path,
            'read_text',
            autospec=True,
            side_effect=lambda path, *args, **kwargs: (
                _pr292_mutated_text
                if path.resolve() == _pr292_manifest_path.resolve()
                else _pr292_original_read(path, *args, **kwargs)
            ),
        ):
            with pytest.raises(_pr292_denied) as _pr292_error:
                _pr292_policy.AgentCapabilityPolicyStoreV1.from_generated(_pr292_builder.REPO_ROOT)
            assert _pr292_error.value.reason_code is _pr292_reason.TASK_ENVELOPE_STALE
    assert _pr292_pathlib.Path.read_text is _pr292_original_read
    assert _pr292_manifest_path.read_bytes() == _pr292_persisted_bytes
    # A negative test must not poison the real reader or rewrite the fixture.
    assert _pr292_policy.AgentCapabilityPolicyStoreV1.from_generated(
        _pr292_builder.REPO_ROOT
    ).snapshot.policy_version == _pr292_policy.POLICY_VERSION

    regression_intentions = (
        "canonical_manifest_positive_control",
        "canonical_view_reader_round_trip",
        "ordinary_safe_path_positive_control",
        "ordinary_numeric_path_negative_control",
        "numeric_path_through_adapter_workaround",
        "manifest_output_contract_replacement",
        "manifest_quantum_latency_class_replacement",
        "manifest_writer_failure_route_replacement",
        "manifest_future_owner_promoted_to_existing",
        "manifest_numeric_authority_flag",
        "launch_quantum_latency_replacement_at_qku_boundary",
        "launch_boolean_profile_ordinal",
        "launch_float_validation_count",
        "mutable_dataclass_normalization",
        "float_enum_normalization",
        "list_enum_normalization",
        "plain_float_normalization_negative_control",
    )
    assert len(regression_intentions) == len(set(regression_intentions)) == 17
    qku_exports = (
        "SelectedComponentPackageEntryViewV1",
        "SelectedComponentOperationViewV1",
        "SelectedComponentPackageViewV1",
        "SelectedComponentPackageAdapterV1",
    )
    assert tuple(qku_control_plane.__all__[-4:]) == qku_exports
    assert all(qku_control_plane.__all__.count(name) == 1 for name in qku_exports)
    generic_exports = (
        "PluginPackageReasonCodeV1",
        "PluginPackageContractError",
        "PackageVersionV1",
        "PackageAdmissionStateV1",
        "PackageCompatibilityStateV1",
        "PackageRollbackTargetKindV1",
        "PackageOperationEligibilityStateV1",
        "PackageValidationTerminalStateV1",
        "PackageSupersessionStateV1",
        "PackageOperationEligibilityV1",
        "SelectedComponentPackageEntryV1",
        "SelectedComponentPackageManifestV1",
        "CompatibilityAndDependencyReceiptV1",
        "RollbackAndSupersessionReceiptV1",
        "PackageReproducibilityReceiptV1",
        "compile_selected_package_dependency_order_v1",
        "build_selected_component_package_manifest_v1",
        "validate_selected_component_package_v1",
        "derive_rollback_and_supersession_receipt_v1",
        "validate_package_supersession_v1",
        "rebuild_selected_component_package_v1",
        "selected_component_package_projection_v1",
    )
    assert tuple(generic_plugins.__all__[-22:]) == generic_exports
    historical_families = qku_control_plane.PR162EPluginAdapterV1(
        root
    ).load_families()
    assert len(historical_families) == 95
    assert all(
        isinstance(row, qku_control_plane.PluginFamilyViewV1)
        for row in historical_families
    )
    historical_fixture_scope = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
    assert CAPITAL_RISK_ACTIVE_STAGE1_VENUES == historical_fixture_scope
    assert CREDENTIAL_READINESS_STAGE1_VENUE_IDS == historical_fixture_scope
    assert SOURCE_EVIDENCE_ACTIVE_STAGE1_VENUES == historical_fixture_scope
    assert not (
        root / "docs/master_plan/generated/qku_control_plane/stage1_launch_graph"
    ).exists()
