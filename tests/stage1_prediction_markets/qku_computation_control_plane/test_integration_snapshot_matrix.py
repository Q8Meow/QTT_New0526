from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
from decimal import Decimal
import json
from pathlib import Path
from types import MappingProxyType

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ComputationControlPlaneError,
    InputAuthorityError,
    NumericDomainError,
    ReasonCode,
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
    ModeSnapshotPreconstructionGateV1,
    PriorSnapshotCandidateV1,
    build_snapshot_candidate,
    construct_snapshot_candidate,
    evaluate_mode_snapshot_candidate,
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
    ComputeComponentRequestV1,
    ImplementationVersionPinV1,
    LatencyBudgetProfileV1,
    OperationStatusV1,
    ResourceBoundsProfileV1,
    SnapshotCandidateStateV1,
    SnapshotParameterResolutionStateV1,
    SnapshotRetirementStateV1,
    SnapshotRollbackStateV1,
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
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import (
    InMemoryPersistenceAdapterV1,
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

    class _PreFGateProbe:
        late_calls = 0

        def __init__(self) -> None:
            self.owner_registry = owner_registry

        def resolve_mode_snapshot_preconstruction_gate(self, *args: object):
            return current_resolver.resolve_mode_snapshot_preconstruction_gate(*args)

        def enrich_mode_snapshot_candidate(self, *_args: object):
            self.late_calls += 1
            raise AssertionError("late D enrichment entered the T03 HOTPATH")

    pre_f_gate_probe = _PreFGateProbe()
    service = QKUComputationControlPlaneV1(
        owner_registry,
        agent_capability_resolver=_Admission(),
        mode_snapshot_input_resolver=pre_f_gate_probe,
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
    assert pre_f_gate_probe.late_calls == 0

    base_inputs = _inputs()
    admitted_t06_receipt = _transition_receipt_proposal(
        transition_id="T06",
        request_id=admitted.request_id,
        principal_id=admitted.principal_id,
        task_id=admitted.task_id,
        capability_decision_ref=admitted.decision_id,
        context_ref=context.context_id,
        snapshot_candidate_ref=f"SNAPSHOT-CANDIDATE::{admitted.request_id}",
        candidate_version=base_inputs.candidate_version,
        expected_owner_state_ref=base_inputs.expected_owner_state_ref,
        effective_at=context.as_of,
    )
    owner_action = replace(
        base_inputs.owner_action_confirmation,
        principal_id=admitted.principal_id,
        task_id=admitted.task_id,
        capability_decision_ref=admitted.decision_id,
        context_ref=context.context_id,
        predecessor_transition_receipt_ref_or_explicit_absence=(
            admitted_t06_receipt.record_id
        ),
        predecessor_transition_receipt_proposal_or_explicit_absence=(
            admitted_t06_receipt
        ),
    )
    enriched_inputs = replace(
        base_inputs,
        request_id=admitted.request_id,
        principal_id=admitted.principal_id,
        task_id=admitted.task_id,
        current_agent_id=admitted.current_agent_id,
        capability_decision_ref=admitted.decision_id,
        owner_action_confirmation=owner_action,
        receipt_lineage_refs=(
            base_inputs.computation_bundle_closure.preflight_receipt_ref,
            owner_action.receipt_ref,
        ),
    )
    nonterminal_gate = ModeSnapshotPreconstructionGateV1(
        request_id=enriched_inputs.request_id,
        principal_id=enriched_inputs.principal_id,
        task_id=enriched_inputs.task_id,
        current_agent_id=enriched_inputs.current_agent_id,
        capability_decision_ref=enriched_inputs.capability_decision_ref,
        context_ref=enriched_inputs.context_ref,
        current_mode=enriched_inputs.current_mode,
        requested_mode=enriched_inputs.requested_mode,
        candidate_version=enriched_inputs.candidate_version,
        evaluated_at=enriched_inputs.evaluated_at,
        expires_at=enriched_inputs.expires_at,
        causation_id=enriched_inputs.causation_id,
        correlation_id=enriched_inputs.correlation_id,
        receipt_lineage_refs=(
            admitted.agent_orch_receipt_ref,
            enriched_inputs.kill_submit_state.state_ref,
        ),
        source_epoch_refs=(context.source_epoch_id,),
        evidence_reference=enriched_inputs.evidence_reference,
        kill_submit_state=enriched_inputs.kill_submit_state,
    )

    class _NonterminalResolver:
        gate_calls = 0
        enrich_calls = 0

        def __init__(self) -> None:
            self.owner_registry = owner_registry

        def resolve_mode_snapshot_preconstruction_gate(self, *_args: object):
            self.gate_calls += 1
            return nonterminal_gate

        def enrich_mode_snapshot_candidate(
            self,
            _request: object,
            _decision: object,
            gate: object,
            projections: object,
        ):
            self.enrich_calls += 1
            assert gate is nonterminal_gate
            assert projections is preloaded_owner_projections
            return enriched_inputs

    def _full_proposal_record() -> TypedValueRecordV1:
        values = (
            ("candidate_contract_id", MODE_SNAPSHOT_CANDIDATE_KIND),
            ("computation_bundle_ref", enriched_inputs.computation_bundle_ref),
            ("context_ref", enriched_inputs.context_ref),
            ("formula_spec_refs", ",".join(enriched_inputs.formula_spec_refs)),
            (
                "implementation_version_pins",
                ",".join(
                    f"{pin.math_spec_id}={pin.implementation_id}"
                    for pin in enriched_inputs.implementation_version_pins
                ),
            ),
            ("binding_profile_ref", enriched_inputs.binding_profile_ref),
            (
                "parameter_policy_snapshot_ref",
                enriched_inputs.parameter_policy_snapshot_ref,
            ),
            (
                "parameter_value_refs",
                ",".join(enriched_inputs.parameter_value_refs),
            ),
            ("source_epoch_refs", ",".join(enriched_inputs.source_epoch_refs)),
            (
                "receipt_lineage_refs",
                ",".join(enriched_inputs.receipt_lineage_refs),
            ),
            ("readiness_state_ref", enriched_inputs.readiness_state_ref),
            ("pretrade_state_ref", enriched_inputs.pretrade_state_ref),
            ("owner_action_policy_ref", enriched_inputs.owner_action_policy_ref),
            ("current_mode", enriched_inputs.current_mode),
            ("requested_mode", enriched_inputs.requested_mode),
            (
                "expected_owner_state_ref",
                enriched_inputs.expected_owner_state_ref,
            ),
            ("candidate_version", enriched_inputs.candidate_version),
        )
        return TypedValueRecordV1(
            tuple(
                TypedValueV1(
                    name=name,
                    kind=TypedValueKindV1.TEXT,
                    value=value,
                    unit="identity",
                    basis="canonical",
                )
                for name, value in values
            )
        )

    full_request = replace(
        request,
        proposed_specification=_full_proposal_record(),
    )
    nonterminal_resolver = _NonterminalResolver()
    common_service_fields = {
        "agent_capability_resolver": _Admission(),
        "mode_snapshot_input_resolver": nonterminal_resolver,
        "mode_snapshot_owner_projection_adapter": adapter,
        "mode_snapshot_projection_bundle": preloaded_owner_projections,
        "resource_bounds_profile": service.resource_bounds_profile,
    }
    full_service = QKUComputationControlPlaneV1(
        owner_registry,
        latency_budget_profile=service.latency_budget_profile,
        **common_service_fields,
    )
    full_response = full_service.submit_candidate_proposal(full_request)
    assert full_response.status is OperationStatusV1.SUCCEEDED
    full_result = full_response.proposal.mode_snapshot_result
    assert full_result is not None
    assert len(full_result.control_receipt_proposals) == 3
    assert tuple(
        row.record_id for row in full_result.control_receipt_proposals
    ) == full_result.control_receipt_refs
    full_measurement = full_result.latency_measurement_or_explicit_absence
    assert full_measurement is not None
    assert full_measurement.stages.receipt_materialization_ns > 0
    assert full_measurement.stages.owner_projection_ns > 0
    assert full_response.receipt_refs == (
        *full_result.control_receipt_refs,
        full_measurement.measurement_ref,
    )

    persistence = InMemoryPersistenceAdapterV1()
    tight_profile = LatencyBudgetProfileV1(
        profile_id="LATENCY-PROFILE::D::FINAL-NINE-STAGE",
        component_budget_ns=tuple(
            (
                name,
                0
                if name in {"receipt_materialization_ns", "owner_projection_ns"}
                else 10**12,
            )
            for name in STAGE_NAMES
        ),
        histogram_boundaries_ns=(1, 10**6, 10**12),
        maximum_observer_overhead_ns=10**9,
        alert_threshold_ns=10**12,
        policy_version="LATENCY-POLICY::D::FINAL-NINE-STAGE",
    )
    tight_service = QKUComputationControlPlaneV1(
        owner_registry,
        persistence_adapter=persistence,
        latency_budget_profile=tight_profile,
        **common_service_fields,
    )
    tight_response = tight_service.submit_candidate_proposal(full_request)
    assert tight_response.status is OperationStatusV1.BLOCKED
    tight_result = tight_response.proposal.mode_snapshot_result
    assert tight_result is not None
    assert ReasonCode.LATENCY_PROFILE_REQUIRED in (
        tight_result.mode_snapshot_decision.reason_codes
    )
    assert tight_result.snapshot_transition_proposal.transition_id == "T04"
    tight_measurement = tight_result.latency_measurement_or_explicit_absence
    assert tight_measurement is not None
    assert tight_measurement.stages.receipt_materialization_ns > 0
    assert tight_measurement.stages.owner_projection_ns > 0
    assert tuple(
        getattr(tight_measurement.stages, name) for name in STAGE_NAMES
    )
    assert tight_measurement.cumulative_stage_ns[-1] == (
        tight_measurement.stages.total_local_no_effect_ns
    )
    assert all(
        persistence.get_record(row.record_id) == row
        for row in tight_result.control_receipt_proposals
    )
    assert len(tight_result.control_receipt_refs) == len(
        set(tight_result.control_receipt_refs)
    )
    assert nonterminal_resolver.gate_calls == 2
    assert nonterminal_resolver.enrich_calls == 2

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
