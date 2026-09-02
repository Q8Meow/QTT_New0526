from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from threading import RLock
from types import MappingProxyType
from typing import Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest.adapter import (
    PITCanonicalEventCandidateV2,
)
from src.qtt.stage1_prediction_markets.market_data_ingest.binding import (
    SelectedPITPublicDataContractV2,
)
from src.qtt.stage1_prediction_markets.market_data_ingest.validator import (
    validate_pit_ingest_record_v2,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
    NoEffectFlagsV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import (
    PersistenceAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PITAvailabilityStateV2,
    PITDataContractErrorV1,
    PITEventDispositionV1,
    PITReasonCodeV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    CaptureAndGapReceiptV2,
    EconomicReceiptEventSpineV1,
    EconomicRecordTypeV1,
    PITAvailabilityReceiptV1,
    PITCanonicalEventReceiptRecordV2,
    PITCommitCompletionV1,
    PITCommitEvidenceClassV1,
    PITCommitIntentV1,
    PITCheckpointV1,
    PITStorageCommitEvidenceV1,
    _pit_reconstruct_receipt_payload_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
    safe_json_loads,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    Stage1VenueProfileIdV1,
)
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.builder import (
    PITBookTransitionResultV2,
    PITOrderBookStateV2,
    apply_pit_event_v2,
)
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.input_lock import (
    PITReconstructionInputLockV2,
    build_pit_reconstruction_input_lock_v2,
)
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.integrity import (
    DeterministicReconstructionReceiptV2,
    validate_pit_book_integrity_v2,
    validate_pit_reconstruction_v2,
)


def build_downstream_handoff(
    input_locks: list[Mapping[str, object]],
    bindings: list[Mapping[str, object]],
    orderbook_snapshots: list[Mapping[str, object]],
    event_state_snapshots: list[Mapping[str, object]],
    integrity_receipts: list[Mapping[str, object]],
) -> dict[str, object]:
    scope_value = "PREDICTION_MARKETS_GENERAL"
    return {
        **policy.common_record_fields(
            "ORDERBOOK_EVENT_STATE_SNAPSHOT_DOWNSTREAM_HANDOFF",
            scope_value,
        ),
        "handoff_id": "PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_DOWNSTREAM_HANDOFF_V1",
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "upstream_prs": [
            "PR105",
            "PR106",
            "PR107",
            "PR108",
            "PR109",
            "PR110",
            "PR111",
            "PR112",
            "PR113",
            "PR114",
        ],
        "downstream_prs": list(policy.DOWNSTREAM_PR_IDS),
        "future_atomicrows_bridge_recommended_after_repo_pr": (
            policy.RECOMMENDED_ATOMICROWS_BRIDGE_AFTER_REPO_PR
        ),
        "future_atomicrows_bridge_candidate_repo_pr": (
            policy.RECOMMENDED_ATOMICROWS_BRIDGE_CANDIDATE_REPO_PR
        ),
        "venue_specific_scope": list(policy.STAGE1_VENUE_IDS),
        "shared_scope": list(policy.SHARED_SCOPE_IDS),
        "snapshot_input_lock_refs": [record["input_lock_id"] for record in input_locks],
        "snapshot_builder_binding_refs": [record["binding_id"] for record in bindings],
        "orderbook_snapshot_refs": [record["snapshot_id"] for record in orderbook_snapshots],
        "event_state_snapshot_refs": [record["snapshot_id"] for record in event_state_snapshots],
        "snapshot_integrity_receipt_refs": [
            record["integrity_receipt_id"] for record in integrity_receipts
        ],
        "contains_fixture_orderbook_snapshot": True,
        "contains_fixture_event_state_snapshot": True,
        "contains_live_orderbook_snapshot": False,
        "contains_live_event_state_snapshot": False,
        "contains_live_market_data": False,
        "contains_live_credentials": False,
        "contains_private_state_payload": False,
        "contains_runtime_resolver_snapshot": False,
        "contains_historical_dataset_digest": False,
        "contains_feature_vector": False,
        "contains_trading_signal": False,
        "contains_quantum_feature_vector": False,
        "contains_quantum_optimizer_input": False,
        "contains_quantum_trading_signal": False,
        "contains_order_authority": False,
        "contains_profit_evidence": False,
        "contains_quantum_execution": False,
        "contains_atomicrows_materialized_rows": False,
        "contains_atomicrows_bundle": False,
        "contains_atomicrows_sha": False,
        "orderbook_canonicalization_verified": True,
        "event_state_canonicalization_verified": True,
        "downstream_pr116_contract_prepared": True,
        "downstream_pr116_execution_authorized": False,
        "downstream_pr117_contract_prepared": True,
        "downstream_pr117_execution_authorized": False,
        "downstream_quantum_feature_computation_authorized": False,
        "downstream_quantum_optimizer_input_creation_authorized": False,
        "downstream_quantum_trading_signal_creation_authorized": False,
        "downstream_atomicrows_bridge_authorized_now": False,
        "downstream_atomicrows_bridge_recommended_after_pr135": True,
        "downstream_atomicrows_bundle_sha_authorized_now": False,
    }


def _pit_snapshot_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


class PITAdmissionStateV2(StrEnum):
    REFERENCE_COMPLETED_NO_EFFECT = "REFERENCE_COMPLETED_NO_EFFECT"
    STRATEGY_AVAILABLE = "STRATEGY_AVAILABLE"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class PITSnapshotDownstreamHandoffV2:
    handoff_id: str
    schema_version: str
    profile_id: Stage1VenueProfileIdV1
    state_ref: str
    state: PITOrderBookStateV2
    reconstruction_receipt: DeterministicReconstructionReceiptV2
    reconstruction_input_lock: PITReconstructionInputLockV2 | None
    availability_receipt: PITAvailabilityReceiptV1
    canonical_event_ref: str
    capture_and_gap_receipt_ref: str
    commit_completion_ref: str
    provider_sequence_available: bool
    provider_publication_time_available: bool
    change_level_history_available: bool
    full_depth_available: bool
    durable_strategy_admission_available: bool
    no_network_effect: bool
    no_outbox_or_order_effect: bool
    no_capital_or_private_state_effect: bool
    no_llm_or_quantum_effect: bool
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        for name in (
            "handoff_id",
            "schema_version",
            "state_ref",
            "canonical_event_ref",
            "capture_and_gap_receipt_ref",
            "commit_completion_ref",
        ):
            _pit_snapshot_text(getattr(self, name), name)
        if self.schema_version != "PIT_SNAPSHOT_DOWNSTREAM_HANDOFF_V2":
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "snapshot handoff schema version is not exact V2",
            )
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "snapshot handoff profile has the wrong exact type",
            )
        if type(self.state) is not PITOrderBookStateV2 or self.state.profile_id is not (
            self.profile_id
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "snapshot handoff state/profile mismatch",
            )
        if self.state_ref != self.state.state_id:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "snapshot handoff state reference differs from its exact state",
            )
        if type(self.reconstruction_receipt) is not (
            DeterministicReconstructionReceiptV2
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "snapshot handoff reconstruction receipt has wrong exact type",
            )
        if self.reconstruction_input_lock is not None and type(
            self.reconstruction_input_lock
        ) is not PITReconstructionInputLockV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "snapshot handoff input lock has wrong exact type",
            )
        if type(self.availability_receipt) is not PITAvailabilityReceiptV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "snapshot handoff availability receipt has wrong exact type",
            )
        if (
            self.reconstruction_receipt.profile_id is not self.profile_id
            or self.reconstruction_receipt.instrument_id != self.state.instrument_id
            or self.reconstruction_receipt.connection_epoch
            != self.state.connection_epoch
            or self.reconstruction_receipt.expected_state_ref != self.state_ref
            or self.reconstruction_receipt.expected_levels != self.state.levels
            or self.reconstruction_receipt.last_event_ordinal
            != self.state.last_completed_event_ordinal
            or self.reconstruction_receipt.provider_sequence_coverage_or_none
            != (
                None
                if self.state.last_provider_sequence_end_or_none is None
                else (
                    f"{self.state.last_provider_sequence_start_or_none}::"
                    f"{self.state.last_provider_sequence_end_or_none}"
                )
            )
            or self.availability_receipt.profile_id is not self.profile_id
            or self.availability_receipt.snapshot_ref != self.state_ref
            or self.availability_receipt.commit_completion_ref
            != self.commit_completion_ref
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "snapshot handoff lineage references are not exact",
            )
        if self.reconstruction_input_lock is not None and (
            self.reconstruction_input_lock.profile_id is not self.profile_id
            or self.reconstruction_input_lock.market_id != self.state.market_id
            or self.reconstruction_input_lock.instrument_id
            != self.state.instrument_id
            or self.reconstruction_input_lock.capture_session_id
            != self.state.capture_session_id
            or self.reconstruction_input_lock.connection_epoch
            != self.state.connection_epoch
            or self.reconstruction_input_lock.wire_dialect
            != self.state.wire_dialect
            or self.reconstruction_input_lock.state_ref != self.state_ref
            or self.reconstruction_input_lock.state_vector != self.state.state_vector
            or self.reconstruction_input_lock.source_receipt_ref
            != self.state.source_receipt_ref
            or self.reconstruction_input_lock.rights_receipt_ref
            != self.state.rights_receipt_ref
            or self.reconstruction_input_lock.first_completed_event_ordinal
            != self.reconstruction_receipt.first_event_ordinal
            or self.reconstruction_input_lock.last_completed_event_ordinal
            != self.reconstruction_receipt.last_event_ordinal
            or self.reconstruction_input_lock.provider_sequence_start_or_none
            != self.state.last_provider_sequence_start_or_none
            or self.reconstruction_input_lock.provider_sequence_end_or_none
            != self.state.last_provider_sequence_end_or_none
            or self.reconstruction_input_lock.reconstruction_receipt_ref
            != self.reconstruction_receipt.receipt_id
            or self.commit_completion_ref
            not in self.reconstruction_input_lock.commit_completion_refs
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "snapshot handoff reconstruction lock lineage is not exact",
            )
        if (
            self.canonical_event_ref
            not in self.reconstruction_receipt.completed_event_refs
            or self.commit_completion_ref
            not in self.reconstruction_receipt.commit_completion_refs
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "snapshot handoff event/completion refs are outside reconstructed custody",
            )
        if self.reconstruction_input_lock is not None and (
            self.reconstruction_input_lock.commit_completion_refs
            != self.reconstruction_receipt.commit_completion_refs
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "snapshot handoff lock and reconstruction completion sets differ",
            )
        for name in (
            "provider_sequence_available",
            "provider_publication_time_available",
            "change_level_history_available",
            "full_depth_available",
            "durable_strategy_admission_available",
            "no_network_effect",
            "no_outbox_or_order_effect",
            "no_capital_or_private_state_effect",
            "no_llm_or_quantum_effect",
        ):
            if type(getattr(self, name)) is not bool:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact boolean",
                )
        if (
            self.provider_publication_time_available
            or self.durable_strategy_admission_available
            or not self.no_network_effect
            or not self.no_outbox_or_order_effect
            or not self.no_capital_or_private_state_effect
            or not self.no_llm_or_quantum_effect
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "reference snapshot handoff overstates availability or effects",
            )
        expected_sequence_available = (
            self.state.last_provider_sequence_start_or_none is not None
            and self.state.last_provider_sequence_end_or_none is not None
        )
        expected_change_history_available = (
            expected_sequence_available
            and self.state.state_vector.continuity_state.value == "CONTIGUOUS"
        )
        expected_full_depth_available = self.state.state_vector.depth_class.value in {
            "COMPLETE_PROVIDER_SNAPSHOT",
            "INCREMENTAL_FROM_COMPLETE_ANCHOR",
        }
        if (
            self.provider_sequence_available != expected_sequence_available
            or self.change_level_history_available
            != expected_change_history_available
            or self.full_depth_available != expected_full_depth_available
            or self.availability_receipt.availability
            is not PITAvailabilityStateV2.UNAVAILABLE
            or self.availability_receipt.reason_or_none
            is not PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE
            or self.availability_receipt.published_pointer
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "snapshot handoff capability flags differ from exact state/durability facts",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "snapshot handoff must carry exact NO_EFFECTS_V1",
            )


def build_pit_snapshot_downstream_handoff_v2(
    state: PITOrderBookStateV2,
    reconstruction_receipt: DeterministicReconstructionReceiptV2,
    availability_receipt: PITAvailabilityReceiptV1,
    *,
    canonical_event_ref: str,
    capture_and_gap_receipt_ref: str,
    commit_completion_ref: str,
    reconstruction_input_lock: PITReconstructionInputLockV2 | None = None,
    handoff_id: str | None = None,
) -> PITSnapshotDownstreamHandoffV2:
    validate_pit_book_integrity_v2(state)
    if reconstruction_receipt.expected_state_ref != state.state_id:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
            "reconstruction receipt does not bind snapshot state",
        )
    sequence_available = (
        state.last_provider_sequence_start_or_none is not None
        and state.last_provider_sequence_end_or_none is not None
    )
    change_history_available = (
        sequence_available
        and state.state_vector.continuity_state.value == "CONTIGUOUS"
    )
    full_depth_available = state.state_vector.depth_class.value in {
        "COMPLETE_PROVIDER_SNAPSHOT",
        "INCREMENTAL_FROM_COMPLETE_ANCHOR",
    }
    return PITSnapshotDownstreamHandoffV2(
        handoff_id=(
            handoff_id
            or f"PIT-SNAPSHOT-HANDOFF::{state.profile_id.value}::{state.state_id}"
        ),
        schema_version="PIT_SNAPSHOT_DOWNSTREAM_HANDOFF_V2",
        profile_id=state.profile_id,
        state_ref=state.state_id,
        state=state,
        reconstruction_receipt=reconstruction_receipt,
        reconstruction_input_lock=reconstruction_input_lock,
        availability_receipt=availability_receipt,
        canonical_event_ref=canonical_event_ref,
        capture_and_gap_receipt_ref=capture_and_gap_receipt_ref,
        commit_completion_ref=commit_completion_ref,
        provider_sequence_available=sequence_available,
        provider_publication_time_available=False,
        change_level_history_available=change_history_available,
        full_depth_available=full_depth_available,
        durable_strategy_admission_available=False,
        no_network_effect=True,
        no_outbox_or_order_effect=True,
        no_capital_or_private_state_effect=True,
        no_llm_or_quantum_effect=True,
    )


@dataclass(frozen=True, slots=True)
class PITAdmissionResultV2:
    admission_id: str
    admission_state: PITAdmissionStateV2
    reason_code: PITReasonCodeV1
    commit_intent: PITCommitIntentV1 | None
    commit_completion: PITCommitCompletionV1 | None
    storage_commit_evidence: PITStorageCommitEvidenceV1 | None
    availability_receipt: PITAvailabilityReceiptV1 | None
    transition_result: PITBookTransitionResultV2 | None
    downstream_handoff: PITSnapshotDownstreamHandoffV2 | None
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        _pit_snapshot_text(self.admission_id, "admission_id")
        if type(self.admission_state) is not PITAdmissionStateV2 or type(
            self.reason_code
        ) is not PITReasonCodeV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "admission state/reason has the wrong exact type",
            )
        for value, expected_type, name in (
            (self.commit_intent, PITCommitIntentV1, "commit_intent"),
            (self.commit_completion, PITCommitCompletionV1, "commit_completion"),
            (
                self.storage_commit_evidence,
                PITStorageCommitEvidenceV1,
                "storage_commit_evidence",
            ),
            (
                self.availability_receipt,
                PITAvailabilityReceiptV1,
                "availability_receipt",
            ),
            (
                self.transition_result,
                PITBookTransitionResultV2,
                "transition_result",
            ),
            (
                self.downstream_handoff,
                PITSnapshotDownstreamHandoffV2,
                "downstream_handoff",
            ),
        ):
            if value is not None and type(value) is not expected_type:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} has the wrong exact type",
                )
        if self.admission_state is PITAdmissionStateV2.REFERENCE_COMPLETED_NO_EFFECT:
            if (
                self.reason_code
                is not PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE
                or self.commit_completion is None
                or self.storage_commit_evidence is None
                or self.storage_commit_evidence.commit_evidence_class
                is not PITCommitEvidenceClassV1.COORDINATOR_POST_RETURN_UPPER_BOUND_REFERENCE_ONLY
                or self.availability_receipt is None
                or self.commit_intent is None
                or self.transition_result is None
                or self.downstream_handoff is None
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                    "reference completion must remain explicitly unavailable",
                )
            if (
                self.commit_completion.intent_ref != self.commit_intent.intent_id
                or self.commit_completion.commit_evidence
                != self.storage_commit_evidence
                or self.availability_receipt.commit_completion_ref
                != self.commit_completion.completion_id
                or self.availability_receipt.availability
                is not PITAvailabilityStateV2.UNAVAILABLE
                or self.availability_receipt.reason_or_none
                is not PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE
                or self.availability_receipt.published_pointer
                or self.downstream_handoff.commit_completion_ref
                != self.commit_completion.completion_id
                or self.downstream_handoff.state_ref
                != self.transition_result.post_state.state_id
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                    "reference admission lineage or unavailable publication barrier differs",
                )
        elif self.admission_state is PITAdmissionStateV2.STRATEGY_AVAILABLE:
            if (
                self.storage_commit_evidence is None
                or self.storage_commit_evidence.commit_evidence_class
                is not PITCommitEvidenceClassV1.STORAGE_ASSIGNED_ATOMIC_COMMIT_EVIDENCE
                or self.availability_receipt is None
                or self.availability_receipt.availability
                not in {
                    PITAvailabilityStateV2.AVAILABLE_CURRENT_STATE,
                    PITAvailabilityStateV2.AVAILABLE_CHANGE_LEVEL,
                }
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                    "strategy availability requires storage-assigned evidence",
                )
        elif self.admission_state is PITAdmissionStateV2.REJECTED:
            if (
                self.commit_completion is not None
                or self.availability_receipt is not None
                or self.downstream_handoff is not None
                or self.transition_result is None
                or (
                    self.storage_commit_evidence is not None
                    and self.commit_intent is None
                )
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                    "rejected admission cannot expose completion, availability, or handoff",
                )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "admission result must carry exact NO_EFFECTS_V1",
            )


@dataclass(frozen=True, slots=True)
class _PITPendingReferenceCompletionV1:
    completion: PITCommitCompletionV1
    availability: PITAvailabilityReceiptV1
    observed_at_utc: datetime
    partition_id: str


_PIT_COORDINATOR_REGISTRY_LOCK = RLock()
_PIT_PARTITION_LOCKS: dict[
    tuple[int, str], tuple[PersistenceAdapterV1, RLock]
] = {}
_PIT_COMMITTED_ORDINAL_BY_PARTITION: dict[tuple[int, str], int] = {}
_PIT_PENDING_COMPLETION_BY_PARTITION: dict[
    tuple[int, str], _PITPendingReferenceCompletionV1
] = {}


def _pit_partition_lock(
    adapter: PersistenceAdapterV1,
    partition_id: str,
) -> tuple[tuple[int, str], RLock]:
    _pit_snapshot_text(partition_id, "partition_id")
    key = (id(adapter), partition_id)
    with _PIT_COORDINATOR_REGISTRY_LOCK:
        registered = _PIT_PARTITION_LOCKS.get(key)
        if registered is None:
            lock = RLock()
            _PIT_PARTITION_LOCKS[key] = (adapter, lock)
        else:
            registered_adapter, lock = registered
            if registered_adapter is not adapter:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                    "partition registry detected an impossible adapter identity collision",
                )
    return key, lock


def _pit_payload_record_id(payload: object) -> str:
    for name in (
        "intent_id",
        "record_id",
        "receipt_id",
        "completion_id",
        "checkpoint_id",
    ):
        value = getattr(payload, name, None)
        if value is not None:
            return _pit_snapshot_text(value, name)
    raise PITDataContractErrorV1(
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
        "PIT receipt payload has no exact record identity",
    )


def _pit_record_type(payload: object) -> EconomicRecordTypeV1:
    record_type_by_exact_type = {
        PITCommitIntentV1: EconomicRecordTypeV1.PIT_COMMIT_INTENT,
        PITCanonicalEventReceiptRecordV2: EconomicRecordTypeV1.PIT_CANONICAL_EVENT,
        CaptureAndGapReceiptV2: EconomicRecordTypeV1.PIT_CAPTURE_AND_GAP,
        PITCommitCompletionV1: EconomicRecordTypeV1.PIT_COMMIT_COMPLETION,
        PITAvailabilityReceiptV1: EconomicRecordTypeV1.PIT_AVAILABILITY,
        PITCheckpointV1: EconomicRecordTypeV1.PIT_CHECKPOINT,
    }
    try:
        return record_type_by_exact_type[type(payload)]
    except KeyError as exc:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "unsupported exact PIT receipt payload type",
        ) from exc


def _pit_spine_record(
    payload: object,
    *,
    partition_id: str,
    recorded_at_utc: datetime,
    sequence: int,
) -> EconomicReceiptEventSpineV1:
    record_id = _pit_payload_record_id(payload)
    return EconomicReceiptEventSpineV1(
        record_id=record_id,
        record_type=_pit_record_type(payload),
        schema_version="PIT_RECEIPT_SPINE_V2",
        semantic_owner="S1_PIT_DATA_PHASE_A_01",
        implementation_owner="QKU_RECEIPT_SPINE_REFERENCE_COORDINATOR",
        context_ref=partition_id,
        effective_at=recorded_at_utc,
        recorded_at=recorded_at_utc,
        causation_id=f"CAUSE::{record_id}",
        correlation_id=f"CORRELATION::{partition_id}",
        traceparent="TRACEPARENT::S1-PIT-DATA-PHASE-A-01",
        tracestate="NO_EFFECT_REFERENCE_COORDINATOR",
        sequence=sequence,
        aggregate_id=partition_id,
        aggregate_version=sequence,
        authority_class="PIT_REFERENCE_RECEIPT_NO_STRATEGY_AUTHORITY",
        typed_payload=payload,
        no_effect_flags=NO_EFFECTS_V1,
    )


def _pit_persist_receipt_payloads(
    adapter: PersistenceAdapterV1,
    payloads: tuple[object, ...],
    *,
    partition_id: str,
    recorded_at_utc: datetime,
    sequence: int,
) -> None:
    transaction = adapter.begin_transaction()
    try:
        for payload in payloads:
            adapter.insert_receipt_record(
                transaction,
                _pit_spine_record(
                    payload,
                    partition_id=partition_id,
                    recorded_at_utc=recorded_at_utc,
                    sequence=sequence,
                ),
            )
        transaction.commit()
    except Exception:
        if transaction.is_active:
            transaction.rollback()
        raise


def _pit_recover_pending_reference_completion(
    adapter: PersistenceAdapterV1,
    partition_key: tuple[int, str],
) -> None:
    pending = _PIT_PENDING_COMPLETION_BY_PARTITION.get(partition_key)
    if pending is None:
        return
    _pit_persist_receipt_payloads(
        adapter,
        (pending.completion, pending.availability),
        partition_id=pending.partition_id,
        recorded_at_utc=pending.observed_at_utc,
        sequence=pending.completion.committed_event_ordinal,
    )
    _PIT_PENDING_COMPLETION_BY_PARTITION.pop(partition_key, None)


def _pit_partition_receipt_payloads(
    adapter: PersistenceAdapterV1,
    *,
    partition_id: str,
    cutoff_utc: datetime,
) -> tuple[object, ...]:
    rows = adapter.reconstruct_as_of(
        effective_cutoff=cutoff_utc,
        recorded_cutoff=cutoff_utc,
        aggregate_scope=(partition_id,),
    )
    pit_record_types = {
        EconomicRecordTypeV1.PIT_COMMIT_INTENT,
        EconomicRecordTypeV1.PIT_CANONICAL_EVENT,
        EconomicRecordTypeV1.PIT_CAPTURE_AND_GAP,
        EconomicRecordTypeV1.PIT_COMMIT_COMPLETION,
        EconomicRecordTypeV1.PIT_AVAILABILITY,
        EconomicRecordTypeV1.PIT_CHECKPOINT,
    }
    payloads: list[object] = []
    seen_record_ids: set[str] = set()
    exact_spine_fields = set(EconomicReceiptEventSpineV1.__dataclass_fields__)
    for row in rows:
        if type(row) is EconomicReceiptEventSpineV1:
            record_type = row.record_type
            if record_type not in pit_record_types:
                continue
            if (
                row.schema_version != "PIT_RECEIPT_SPINE_V2"
                or row.aggregate_id != partition_id
                or row.context_ref != partition_id
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                    "typed persisted PIT spine row has inconsistent partition custody",
                )
            record_id = row.record_id
            payload = row.typed_payload
            if type(row.sequence) is not int or row.sequence < 0:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                    "typed persisted PIT spine sequence is not exact",
                )
            expected_row = _pit_spine_record(
                payload,
                partition_id=partition_id,
                recorded_at_utc=_pit_coordinator_time(
                    row.recorded_at,
                    "typed persisted PIT spine recorded_at",
                ),
                sequence=row.sequence,
            )
            if row != expected_row:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                    "typed persisted PIT spine metadata is not canonical",
                )
        elif type(row) is dict:
            if set(row) != exact_spine_fields:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    "serialized PIT spine row field set is not exact",
                )
            try:
                record_type = EconomicRecordTypeV1(row["record_type"])
            except (TypeError, ValueError) as exc:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    "serialized PIT spine record discriminator is unknown",
                ) from exc
            if record_type not in pit_record_types:
                continue
            if (
                row["schema_version"] != "PIT_RECEIPT_SPINE_V2"
                or row["aggregate_id"] != partition_id
                or row["context_ref"] != partition_id
                or deterministic_json(row["no_effect_flags"])
                != deterministic_json(NO_EFFECTS_V1)
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                    "serialized PIT spine row has inconsistent partition custody",
                )
            record_id = row["record_id"]
            payload = _pit_reconstruct_receipt_payload_v1(
                record_type,
                row["typed_payload"],
            )
            if type(row["recorded_at"]) is not str or type(
                row["sequence"]
            ) is not int or row["sequence"] < 0:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                    "serialized PIT spine time or sequence is not exact",
                )
            try:
                recorded_at = datetime.fromisoformat(row["recorded_at"])
            except ValueError as exc:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
                    "serialized PIT spine recorded_at is not ISO-8601",
                ) from exc
            expected_serialized_row = safe_json_loads(
                deterministic_json(
                    _pit_spine_record(
                        payload,
                        partition_id=partition_id,
                        recorded_at_utc=_pit_coordinator_time(
                            recorded_at,
                            "serialized PIT spine recorded_at",
                        ),
                        sequence=row["sequence"],
                    )
                )
            )
            if row != expected_serialized_row:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                    "serialized persisted PIT spine metadata is not canonical",
                )
        else:
            continue
        if record_type not in pit_record_types:
            continue
        if type(record_id) is not str or not record_id or record_id in seen_record_ids:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "persisted PIT spine record identity is absent or duplicated",
            )
        if _pit_payload_record_id(payload) != record_id:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "persisted PIT spine and payload identities differ",
            )
        seen_record_ids.add(record_id)
        payloads.append(payload)
    return tuple(payloads)


def _pit_recover_persisted_partition_v1(
    adapter: PersistenceAdapterV1,
    partition_key: tuple[int, str],
    *,
    partition_id: str,
    current_candidate_event_record_id: str,
    cutoff_utc: datetime,
    coordinator_clock: Callable[[], datetime],
) -> None:
    payloads = _pit_partition_receipt_payloads(
        adapter,
        partition_id=partition_id,
        cutoff_utc=cutoff_utc,
    )
    intents = {
        payload.intent_id: payload
        for payload in payloads
        if type(payload) is PITCommitIntentV1
    }
    events = {
        payload.record_id: payload
        for payload in payloads
        if type(payload) is PITCanonicalEventReceiptRecordV2
    }
    captures = {
        payload.receipt_id: payload
        for payload in payloads
        if type(payload) is CaptureAndGapReceiptV2
    }
    completions = {
        payload.completion_id: payload
        for payload in payloads
        if type(payload) is PITCommitCompletionV1
    }
    availability_rows = tuple(
        payload
        for payload in payloads
        if type(payload) is PITAvailabilityReceiptV1
    )
    availabilities = {
        payload.commit_completion_ref: payload for payload in availability_rows
    }
    if len(availabilities) != len(availability_rows):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
            "persisted PIT completion has multiple availability receipts",
        )
    if any(
        availability.commit_completion_ref not in completions
        for availability in availability_rows
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
            "persisted PIT availability has no exact completion custody",
        )
    for completion in completions.values():
        event = events.get(completion.final_event_record_ref)
        capture = captures.get(completion.capture_and_gap_receipt_ref)
        intent = (
            None if event is None else intents.get(event.commit_intent_ref)
        )
        event_json = (
            None
            if event is None
            else safe_json_loads(event.canonical_event_json)
        )
        expected_capture_pre_state = (
            None
            if event_json is None
            else (
                event_json["pre_state_ref_or_none"]
                or f"NO-PRIOR-STATE::{partition_id}"
            )
        )
        if (
            event is None
            or capture is None
            or intent is None
            or type(event_json) is not dict
            or completion.partition_id != partition_id
            or event.partition_id != partition_id
            or intent.partition_id != partition_id
            or completion.intent_ref != event.commit_intent_ref
            or intent.profile_id is not event.profile_id
            or intent.candidate_event_record_id != event.event_record_id
            or intent.capture_session_id != event.capture_session_id
            or intent.connection_epoch != event.connection_epoch
            or intent.validation_receipt_ref != event.validation_receipt_ref
            or completion.profile_id is not event.profile_id
            or completion.profile_id is not capture.profile_id
            or completion.committed_event_ordinal
            != event.committed_event_ordinal
            or completion.completed_at_utc < intent.created_at_utc
            or capture.event_record_id != event.event_record_id
            or capture.connection_epoch != event.connection_epoch
            or capture.pre_state_ref != expected_capture_pre_state
            or capture.post_state_ref != event_json["post_state_ref"]
            or capture.commit_completion_ref_or_none
            != completion.completion_id
            or event_json["commit_completion_ref"] != completion.completion_id
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "persisted PIT completion lineage is not exact",
            )
        availability = availabilities.get(completion.completion_id)
        if availability is None:
            availability = PITAvailabilityReceiptV1(
                receipt_id=f"PIT-AVAILABILITY::{event.event_record_id}",
                profile_id=event.profile_id,
                partition_id=partition_id,
                snapshot_ref=capture.post_state_ref,
                commit_completion_ref=completion.completion_id,
                availability=PITAvailabilityStateV2.UNAVAILABLE,
                reason_or_none=PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                strategy_available_at_utc_or_none=None,
                storage_commit_evidence_ref_or_none=None,
                published_pointer=False,
            )
            _pit_persist_receipt_payloads(
                adapter,
                (availability,),
                partition_id=partition_id,
                recorded_at_utc=completion.completed_at_utc,
                sequence=completion.committed_event_ordinal,
            )
        elif (
            availability.profile_id is not event.profile_id
            or availability.partition_id != partition_id
            or availability.snapshot_ref != capture.post_state_ref
            or availability.commit_completion_ref != completion.completion_id
            or availability.availability is not PITAvailabilityStateV2.UNAVAILABLE
            or availability.published_pointer
            or availability.reason_or_none
            is not PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE
            or availability.strategy_available_at_utc_or_none is not None
            or availability.storage_commit_evidence_ref_or_none is not None
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "persisted PIT availability lineage is not exact",
            )

    completed_event_refs = {
        completion.final_event_record_ref for completion in completions.values()
    }
    for event in sorted(
        events.values(), key=lambda value: value.committed_event_ordinal
    ):
        if event.record_id in completed_event_refs:
            continue
        if event.event_record_id == current_candidate_event_record_id:
            continue
        intent = intents.get(event.commit_intent_ref)
        capture_id = f"PIT-CAPTURE-GAP::{event.event_record_id}"
        capture = captures.get(capture_id)
        completion_id = f"PIT-COMPLETION::{event.event_record_id}"
        event_json = safe_json_loads(event.canonical_event_json)
        expected_capture_pre_state = (
            event_json["pre_state_ref_or_none"]
            or f"NO-PRIOR-STATE::{partition_id}"
        )
        if (
            intent is None
            or capture is None
            or type(event_json) is not dict
            or completion_id in completions
            or capture.commit_completion_ref_or_none != completion_id
            or intent.partition_id != partition_id
            or event.partition_id != partition_id
            or intent.profile_id is not event.profile_id
            or intent.candidate_event_record_id != event.event_record_id
            or intent.capture_session_id != event.capture_session_id
            or intent.connection_epoch != event.connection_epoch
            or intent.validation_receipt_ref != event.validation_receipt_ref
            or capture.profile_id is not event.profile_id
            or capture.event_record_id != event.event_record_id
            or capture.connection_epoch != event.connection_epoch
            or capture.pre_state_ref != expected_capture_pre_state
            or capture.post_state_ref != event_json["post_state_ref"]
            or event_json["commit_completion_ref"] != completion_id
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                "incomplete persisted PIT event cannot be recovered exactly",
            )
        observed = _pit_coordinator_time(
            coordinator_clock(),
            "coordinator_recovery_post_return_observed_at_utc",
        )
        if observed < cutoff_utc:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
                "recovery observation precedes the current coordinator cutoff",
            )
        evidence = PITStorageCommitEvidenceV1(
            adapter_identity=f"{type(adapter).__module__}.{type(adapter).__qualname__}",
            transaction_identity=(
                f"REFERENCE-RECOVERY-TRANSACTION::{intent.intent_id}::"
                f"{event.committed_event_ordinal}"
            ),
            committed_record_refs=(event.record_id, capture.receipt_id),
            commit_evidence_class=(
                PITCommitEvidenceClassV1.COORDINATOR_POST_RETURN_UPPER_BOUND_REFERENCE_ONLY
            ),
            storage_commit_time_utc_or_none=None,
            backend_identity_or_none=None,
            backend_sequence_or_revision_or_none=None,
            coordinator_post_return_observed_at_utc=observed,
        )
        completion = PITCommitCompletionV1(
            completion_id=completion_id,
            intent_ref=intent.intent_id,
            profile_id=event.profile_id,
            partition_id=partition_id,
            final_event_record_ref=event.record_id,
            capture_and_gap_receipt_ref=capture.receipt_id,
            committed_event_ordinal=event.committed_event_ordinal,
            commit_evidence=evidence,
            completed_at_utc=observed,
            recovered_after_crash=True,
        )
        availability = PITAvailabilityReceiptV1(
            receipt_id=f"PIT-AVAILABILITY::{event.event_record_id}",
            profile_id=event.profile_id,
            partition_id=partition_id,
            snapshot_ref=capture.post_state_ref,
            commit_completion_ref=completion.completion_id,
            availability=PITAvailabilityStateV2.UNAVAILABLE,
            reason_or_none=PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
            strategy_available_at_utc_or_none=None,
            storage_commit_evidence_ref_or_none=None,
            published_pointer=False,
        )
        _pit_persist_receipt_payloads(
            adapter,
            (completion, availability),
            partition_id=partition_id,
            recorded_at_utc=observed,
            sequence=event.committed_event_ordinal,
        )
        completions[completion.completion_id] = completion
        completed_event_refs.add(event.record_id)

    ordinals = tuple(
        sorted(completion.committed_event_ordinal for completion in completions.values())
    )
    if ordinals and ordinals != tuple(range(1, ordinals[-1] + 1)):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
            "persisted completed PIT ordinal range contains a gap or duplicate",
        )
    if ordinals:
        _PIT_COMMITTED_ORDINAL_BY_PARTITION[partition_key] = ordinals[-1]


def _pit_reference_event_json(
    candidate: PITCanonicalEventCandidateV2,
    *,
    committed_event_ordinal: int,
    commit_completion_ref: str,
    pre_state_ref_or_none: str | None,
    prior_event_ref_or_none: str | None,
    post_state_ref: str,
) -> str:
    return deterministic_json(
        {
            "record_type": "PIT_CANONICAL_EVENT_REFERENCE_COMPLETED_V2",
            "schema_version": "PIT_CANONICAL_EVENT_V2",
            "event_record_id": candidate.event_record_id,
            "profile_id": candidate.profile_id,
            "market_id": candidate.market_id,
            "instrument_id": candidate.instrument_id,
            "channel": candidate.channel,
            "connection_epoch": candidate.connection_epoch,
            "capture_session_id": candidate.capture_session_id,
            "raw_frame_ref": candidate.raw_frame_ref,
            "committed_event_ordinal": committed_event_ordinal,
            "event_kind": candidate.event_kind,
            "wire_dialect": candidate.wire_dialect,
            "source_currentization_version": (
                candidate.source_currentization_version
            ),
            "provider_sequence_start_or_none": (
                candidate.provider_sequence_start_or_none
            ),
            "provider_sequence_end_or_none": (
                candidate.provider_sequence_end_or_none
            ),
            "provider_trade_id_or_none": candidate.provider_trade_id_or_none,
            "provider_subscription_id_or_none": (
                candidate.provider_subscription_id_or_none
            ),
            "payload": candidate.payload,
            "depth_class": candidate.depth_class,
            "clocks": {
                "provider_event_time_utc_or_none": (
                    candidate.provider_event_time_utc_or_none
                ),
                "provider_publication_time_utc_or_none": None,
                "qtt_received_at_utc": candidate.qtt_received_at_utc,
                "qtt_received_monotonic_ns": candidate.qtt_received_monotonic_ns,
                "qtt_parse_completed_at_utc": candidate.qtt_parse_completed_at_utc,
                "qtt_parse_completed_monotonic_ns": (
                    candidate.qtt_parse_completed_monotonic_ns
                ),
                "durable_commit_completed_at_utc": None,
                "durable_commit_completed_monotonic_ns": None,
                "strategy_available_at_utc": None,
                "strategy_available_monotonic_ns": None,
                "revision_effective_time_utc_or_none": None,
                "settlement_finality_time_utc_or_none": None,
                "process_epoch_id": candidate.process_epoch_id,
                "monotonic_clock_id": candidate.monotonic_clock_id,
                "wall_clock_source_id": candidate.wall_clock_source_id,
                "clock_quality_receipt_ref": (
                    candidate.clock_quality_receipt_ref
                ),
                "wall_clock_uncertainty_ns": candidate.wall_clock_uncertainty_ns,
            },
            "pre_state_ref_or_none": pre_state_ref_or_none,
            "post_state_ref": post_state_ref,
            "event_disposition": PITEventDispositionV1.COMMITTED,
            "failure_reason_or_none": None,
            "rights_receipt_ref": candidate.rights_receipt_ref,
            "source_receipt_ref": candidate.source_receipt_ref,
            "commit_completion_ref": commit_completion_ref,
            "prior_event_ref_or_none": prior_event_ref_or_none,
            "checkpoint_ref_or_none": None,
            "recovery_receipt_ref_or_none": None,
            "commit_evidence_class": (
                PITCommitEvidenceClassV1.COORDINATOR_POST_RETURN_UPPER_BOUND_REFERENCE_ONLY
            ),
            "strategy_availability": "UNAVAILABLE",
            "strategy_unavailability_reason": (
                PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE
            ),
            "no_private_state_authority": candidate.no_private_state_authority,
            "no_order_authority": candidate.no_order_authority,
            "no_profit_claim": candidate.no_profit_claim,
            "no_qpu_effect": candidate.no_qpu_effect,
            "no_llm_effect": candidate.no_llm_effect,
            "no_effect_flags": NO_EFFECTS_V1,
        }
    )


def _pit_prior_event_ref_or_none(
    prior_state_or_none: PITOrderBookStateV2 | None,
) -> str | None:
    if prior_state_or_none is None:
        return None
    prefix = "PIT-STATE::"
    suffix = f"::{prior_state_or_none.last_completed_event_ordinal}"
    state_id = prior_state_or_none.state_id
    if (
        not state_id.startswith(prefix)
        or not state_id.endswith(suffix)
        or len(state_id) <= len(prefix) + len(suffix)
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
            "prior state identity does not retain its exact completed event lineage",
        )
    return state_id[len(prefix) : -len(suffix)]


def _pit_coordinator_time(value: object, name: str) -> datetime:
    if (
        type(value) is not datetime
        or value.tzinfo is None
        or value.utcoffset() is None
        or value.utcoffset().total_seconds() != 0
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
            f"{name} must be an aware UTC datetime",
        )
    return value


def commit_and_publish_pit_state_v2(
    adapter: PersistenceAdapterV1,
    contract: SelectedPITPublicDataContractV2,
    candidate: PITCanonicalEventCandidateV2,
    prior_state_or_none: PITOrderBookStateV2 | None,
    *,
    partition_id: str,
    intent_id: str,
    intent_created_at_utc: datetime,
    coordinator_clock: Callable[[], datetime],
    capability_context_id: str,
) -> PITAdmissionResultV2:
    """Commit one reference event and terminate fail closed before strategy use."""

    if not isinstance(adapter, PersistenceAdapterV1):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
            "adapter must implement the existing PersistenceAdapterV1 owner",
        )
    if type(contract) is not SelectedPITPublicDataContractV2 or type(
        candidate
    ) is not PITCanonicalEventCandidateV2:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "commit coordinator requires exact contract and candidate types",
        )
    if prior_state_or_none is not None and type(prior_state_or_none) is not (
        PITOrderBookStateV2
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "prior state must be exact PITOrderBookStateV2 or absent",
        )
    _pit_snapshot_text(partition_id, "partition_id")
    _pit_snapshot_text(intent_id, "intent_id")
    _pit_snapshot_text(capability_context_id, "capability_context_id")
    intent_time = _pit_coordinator_time(
        intent_created_at_utc, "intent_created_at_utc"
    )
    if intent_time < candidate.qtt_parse_completed_at_utc:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
            "commit intent cannot precede candidate parse completion",
        )
    if not isinstance(coordinator_clock, Callable):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
            "coordinator_clock must be an injected callable",
        )
    validate_pit_ingest_record_v2(candidate, contract=contract)
    partition_key, partition_lock = _pit_partition_lock(adapter, partition_id)
    with partition_lock:
        _pit_recover_pending_reference_completion(adapter, partition_key)
        _pit_recover_persisted_partition_v1(
            adapter,
            partition_key,
            partition_id=partition_id,
            current_candidate_event_record_id=candidate.event_record_id,
            cutoff_utc=intent_time,
            coordinator_clock=coordinator_clock,
        )
        prior_ordinal = (
            0
            if prior_state_or_none is None
            else prior_state_or_none.last_completed_event_ordinal
        )
        remembered_ordinal = _PIT_COMMITTED_ORDINAL_BY_PARTITION.get(
            partition_key, prior_ordinal
        )
        if remembered_ordinal != prior_ordinal:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "coordinator ordinal differs from supplied completed state",
            )
        candidate_ordinal = remembered_ordinal + 1
        transition = apply_pit_event_v2(
            prior_state_or_none,
            candidate,
            candidate_event_ordinal=candidate_ordinal,
        )
        if transition.event_disposition is not PITEventDispositionV1.COMMITTED:
            return PITAdmissionResultV2(
                admission_id=f"PIT-ADMISSION::{candidate.event_record_id}",
                admission_state=PITAdmissionStateV2.REJECTED,
                reason_code=(
                    transition.failure_reason_or_none
                    or PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE
                ),
                commit_intent=None,
                commit_completion=None,
                storage_commit_evidence=None,
                availability_receipt=None,
                transition_result=transition,
                downstream_handoff=None,
            )
        validate_pit_book_integrity_v2(transition.post_state)
        independent_transition = apply_pit_event_v2(
            prior_state_or_none,
            candidate,
            candidate_event_ordinal=candidate_ordinal,
        )
        if independent_transition.event_disposition is not (
            PITEventDispositionV1.COMMITTED
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "independent transition did not reproduce committed state",
            )
        completion_id = f"PIT-COMPLETION::{candidate.event_record_id}"
        capture_receipt_id = f"PIT-CAPTURE-GAP::{candidate.event_record_id}"
        event_receipt_id = f"PIT-EVENT-RECEIPT::{candidate.event_record_id}"
        intent = PITCommitIntentV1(
            intent_id=intent_id,
            profile_id=candidate.profile_id,
            partition_id=partition_id,
            candidate_event_record_id=candidate.event_record_id,
            capture_session_id=candidate.capture_session_id,
            connection_epoch=candidate.connection_epoch,
            created_at_utc=intent_time,
            candidate_ordinal_allocated=False,
            validation_receipt_ref=f"PIT-VALIDATION::{candidate.event_record_id}",
        )
        _pit_persist_receipt_payloads(
            adapter,
            (intent,),
            partition_id=partition_id,
            recorded_at_utc=intent_time,
            sequence=remembered_ordinal,
        )
        event_json = _pit_reference_event_json(
            candidate,
            committed_event_ordinal=candidate_ordinal,
            commit_completion_ref=completion_id,
            pre_state_ref_or_none=(
                prior_state_or_none.state_id
                if prior_state_or_none is not None
                else None
            ),
            prior_event_ref_or_none=_pit_prior_event_ref_or_none(
                prior_state_or_none
            ),
            post_state_ref=transition.post_state.state_id,
        )
        event_receipt = PITCanonicalEventReceiptRecordV2(
            record_id=event_receipt_id,
            event_record_id=candidate.event_record_id,
            schema_version="PIT_CANONICAL_EVENT_RECEIPT_RECORD_V2",
            profile_id=candidate.profile_id,
            partition_id=partition_id,
            capture_session_id=candidate.capture_session_id,
            connection_epoch=candidate.connection_epoch,
            committed_event_ordinal=candidate_ordinal,
            canonical_event_json=event_json,
            validation_receipt_ref=f"PIT-VALIDATION::{candidate.event_record_id}",
            prior_event_ref_or_none=(
                _pit_prior_event_ref_or_none(prior_state_or_none)
            ),
            checkpoint_ref_or_none=None,
            source_receipt_ref=candidate.source_receipt_ref,
            rights_receipt_ref=candidate.rights_receipt_ref,
            commit_intent_ref=intent.intent_id,
        )
        capture_receipt = CaptureAndGapReceiptV2(
            receipt_id=capture_receipt_id,
            event_record_id=candidate.event_record_id,
            profile_id=candidate.profile_id,
            connection_epoch=candidate.connection_epoch,
            provider_identity_or_none=transition.provider_identity,
            pre_state_ref=(
                prior_state_or_none.state_id
                if prior_state_or_none is not None
                else f"NO-PRIOR-STATE::{partition_id}"
            ),
            post_state_ref=transition.post_state.state_id,
            event_disposition=PITEventDispositionV1.COMMITTED,
            continuity_result=transition.continuity_result,
            integrity_result=transition.integrity_result,
            failure_reason_or_none=None,
            recovery_required=False,
            commit_completion_ref_or_none=completion_id,
        )
        _pit_persist_receipt_payloads(
            adapter,
            (event_receipt, capture_receipt),
            partition_id=partition_id,
            recorded_at_utc=intent_time,
            sequence=candidate_ordinal,
        )
        observed_after_commit = _pit_coordinator_time(
            coordinator_clock(),
            "coordinator_post_return_observed_at_utc",
        )
        if observed_after_commit < intent_time:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
                "post-return observation precedes commit intent",
            )
        _PIT_COMMITTED_ORDINAL_BY_PARTITION[partition_key] = candidate_ordinal
        evidence = PITStorageCommitEvidenceV1(
            adapter_identity=(
                f"{type(adapter).__module__}.{type(adapter).__qualname__}"
            ),
            transaction_identity=(
                f"REFERENCE-TRANSACTION::{intent.intent_id}::{candidate_ordinal}"
            ),
            committed_record_refs=(event_receipt_id, capture_receipt_id),
            commit_evidence_class=(
                PITCommitEvidenceClassV1.COORDINATOR_POST_RETURN_UPPER_BOUND_REFERENCE_ONLY
            ),
            storage_commit_time_utc_or_none=None,
            backend_identity_or_none=None,
            backend_sequence_or_revision_or_none=None,
            coordinator_post_return_observed_at_utc=observed_after_commit,
        )
        completion = PITCommitCompletionV1(
            completion_id=completion_id,
            intent_ref=intent.intent_id,
            profile_id=candidate.profile_id,
            partition_id=partition_id,
            final_event_record_ref=event_receipt_id,
            capture_and_gap_receipt_ref=capture_receipt_id,
            committed_event_ordinal=candidate_ordinal,
            commit_evidence=evidence,
            completed_at_utc=observed_after_commit,
            recovered_after_crash=False,
        )
        availability = PITAvailabilityReceiptV1(
            receipt_id=f"PIT-AVAILABILITY::{candidate.event_record_id}",
            profile_id=candidate.profile_id,
            partition_id=partition_id,
            snapshot_ref=transition.post_state.state_id,
            commit_completion_ref=completion.completion_id,
            availability=PITAvailabilityStateV2.UNAVAILABLE,
            reason_or_none=PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
            strategy_available_at_utc_or_none=None,
            storage_commit_evidence_ref_or_none=None,
            published_pointer=False,
        )
        _PIT_PENDING_COMPLETION_BY_PARTITION[partition_key] = (
            _PITPendingReferenceCompletionV1(
                completion=completion,
                availability=availability,
                observed_at_utc=observed_after_commit,
                partition_id=partition_id,
            )
        )
        try:
            _pit_recover_pending_reference_completion(adapter, partition_key)
        except Exception:
            return PITAdmissionResultV2(
                admission_id=f"PIT-ADMISSION::{candidate.event_record_id}",
                admission_state=PITAdmissionStateV2.REJECTED,
                reason_code=PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                commit_intent=intent,
                commit_completion=None,
                storage_commit_evidence=evidence,
                availability_receipt=None,
                transition_result=transition,
                downstream_handoff=None,
            )
        reconstruction = validate_pit_reconstruction_v2(
            transition.post_state,
            independent_transition.post_state,
            receipt_id=f"PIT-RECONSTRUCTION::{candidate.event_record_id}",
            anchor_ref=transition.provider_identity,
            completed_event_refs=(event_receipt_id,),
            commit_completion_refs=(completion_id,),
            unavailable_limits=(
                "STORAGE_ASSIGNED_ATOMIC_COMMIT_EVIDENCE",
                "STRATEGY_AVAILABILITY",
                "PROVIDER_PUBLICATION_TIME",
            ),
        )
        input_lock = build_pit_reconstruction_input_lock_v2(
            lock_id=f"PIT-RECONSTRUCTION-LOCK::{candidate.event_record_id}",
            profile_id=candidate.profile_id,
            market_id=candidate.market_id,
            instrument_id=candidate.instrument_id,
            capture_session_id=candidate.capture_session_id,
            connection_epoch=candidate.connection_epoch,
            wire_dialect=candidate.wire_dialect,
            first_completed_event_ordinal=candidate_ordinal,
            last_completed_event_ordinal=candidate_ordinal,
            provider_sequence_start_or_none=(
                candidate.provider_sequence_start_or_none
            ),
            provider_sequence_end_or_none=candidate.provider_sequence_end_or_none,
            process_epoch_id=candidate.process_epoch_id,
            monotonic_clock_id=candidate.monotonic_clock_id,
            source_receipt_ref=candidate.source_receipt_ref,
            rights_receipt_ref=candidate.rights_receipt_ref,
            commit_completion_refs=(completion_id,),
            state_ref=transition.post_state.state_id,
            state_vector=transition.post_state.state_vector,
            reconstruction_receipt_ref=reconstruction.receipt_id,
            capability_context_id=capability_context_id,
            serializer_version="QKU_DETERMINISTIC_JSON_V1",
        )
        downstream_handoff = build_pit_snapshot_downstream_handoff_v2(
            transition.post_state,
            reconstruction,
            availability,
            canonical_event_ref=event_receipt_id,
            capture_and_gap_receipt_ref=capture_receipt_id,
            commit_completion_ref=completion_id,
            reconstruction_input_lock=input_lock,
        )
        return PITAdmissionResultV2(
            admission_id=f"PIT-ADMISSION::{candidate.event_record_id}",
            admission_state=PITAdmissionStateV2.REFERENCE_COMPLETED_NO_EFFECT,
            reason_code=PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
            commit_intent=intent,
            commit_completion=completion,
            storage_commit_evidence=evidence,
            availability_receipt=availability,
            transition_result=transition,
            downstream_handoff=downstream_handoff,
        )


def project_deterministic_reconstruction_receipt_v1(
    receipt: DeterministicReconstructionReceiptV2,
) -> Mapping[str, object]:
    if type(receipt) is not DeterministicReconstructionReceiptV2:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "V1 projection requires exact V2 reconstruction receipt",
        )
    return MappingProxyType(
        {
            "schema_version": "DETERMINISTIC_RECONSTRUCTION_RECEIPT_V1_PROJECTION",
            "receipt_id": receipt.receipt_id,
            "profile_id": receipt.profile_id.value,
            "instrument_id": receipt.instrument_id,
            "connection_epoch": receipt.connection_epoch,
            "anchor_ref": receipt.anchor_ref,
            "first_event_ordinal": receipt.first_event_ordinal,
            "last_event_ordinal": receipt.last_event_ordinal,
            "provider_sequence_coverage_or_none": (
                receipt.provider_sequence_coverage_or_none
            ),
            "expected_state_ref": receipt.expected_state_ref,
            "reconstructed_state_ref": receipt.reconstructed_state_ref,
            "complete_semantic_state_equal": (
                receipt.complete_semantic_state_equal
            ),
            "unavailable_limits": receipt.unavailable_limits,
            "unsupported_v1_fields": (
                "STORAGE_ASSIGNED_STRATEGY_AVAILABILITY",
            ),
        }
    )
