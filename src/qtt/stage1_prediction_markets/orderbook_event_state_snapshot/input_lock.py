from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
    NoEffectFlagsV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PITDataContractErrorV1,
    PITReasonCodeV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    Stage1VenueProfileIdV1,
)
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.policy import (
    PITStateVectorV1,
)


STATE_BY_SCOPE = {
    "KALSHI": "ACCEPTED_SOURCE_GATED",
    "POLYMARKET": "CONNECTOR_SEMANTIC_GATED",
    "FORECASTEX_IBKR": "SOURCE_REQUIRED",
    "PREDICTION_MARKETS_GENERAL": "CONNECTOR_SEMANTIC_REQUIRED",
}


def input_lock_id(scope_value: str) -> str:
    return f"PR133_{scope_value}_SNAPSHOT_INPUT_LOCK_V1"


def _refs_for_scope(refs: list[object], scope_value: str) -> list[str]:
    return sorted(str(ref) for ref in refs if f"_{scope_value}_" in str(ref))


def build_snapshot_input_locks(
    pr132_handoff: Mapping[str, object],
    pr131_handoff: Mapping[str, object],
) -> list[dict[str, object]]:
    canonical_refs = list(pr132_handoff.get("canonical_market_data_ingest_event_refs", []))
    source_refs = list(pr132_handoff.get("market_data_source_dependency_refs", []))
    credential_ref = str(pr131_handoff["handoff_id"])

    records: list[dict[str, object]] = []
    for sequence, scope_ref in enumerate(policy.stage1_scope_refs(), start=1):
        scope_value = scope_ref.value
        state = STATE_BY_SCOPE[scope_value]
        records.append(
            {
                **policy.common_record_fields(
                    "ORDERBOOK_EVENT_STATE_SNAPSHOT_INPUT_LOCK",
                    scope_value,
                ),
                **policy.scope_field(scope_ref),
                "input_lock_id": input_lock_id(scope_value),
                "market_data_ingest_handoff_ref": str(pr132_handoff["handoff_id"]),
                "canonical_market_data_ingest_event_refs": _refs_for_scope(
                    canonical_refs,
                    scope_value,
                ),
                "accepted_source_dependency_refs": [
                    f"PR106_ACCEPTED_SOURCE_PACKET_REF_METADATA_ONLY_{scope_value}"
                ],
                "connector_semantic_dependency_refs": [
                    f"PR124_CONNECTOR_SEMANTIC_BINDING_REF_METADATA_ONLY_{scope_value}"
                ],
                "market_data_source_dependency_refs": _refs_for_scope(
                    source_refs,
                    scope_value,
                ),
                "credential_readiness_dependency_ref": credential_ref,
                "source_dependency_state": state,
                "snapshot_input_class": (
                    "PR132_MARKET_DATA_INGEST_HANDOFF_INPUT"
                    if state in {"ACCEPTED_SOURCE_GATED", "CONNECTOR_SEMANTIC_GATED"}
                    else "SOURCE_REQUIRED_SNAPSHOT_INPUT_PLACEHOLDER"
                ),
                "input_payload_is_synthetic": True,
                "input_contains_live_market_data": False,
                "input_contains_official_venue_semantic_values": False,
                "deterministic_sequence_id": f"PR133_INPUT_LOCK_SEQUENCE_{sequence:04d}",
                "snapshot_build_allowed": True,
                "live_snapshot_build_allowed": False,
                "runtime_resolver_snapshot_allowed": False,
                "historical_dataset_digest_allowed": False,
                "input_lock_required_for_each_snapshot": True,
                "future_low_latency_snapshot_ref": (
                    f"FUTURE_LOW_LATENCY_SNAPSHOT_REF_METADATA_ONLY_{scope_value}"
                ),
                "future_hot_path_snapshot_ref": (
                    f"FUTURE_HOT_PATH_SNAPSHOT_REF_METADATA_ONLY_{scope_value}"
                ),
                "future_pr116_runtime_resolver_contract_ref": (
                    f"PR116_{scope_value}_RUNTIME_RESOLVER_CONTRACT_REF"
                ),
                "future_pr117_historical_dataset_digest_contract_ref": (
                    f"PR117_{scope_value}_HISTORICAL_DATASET_DIGEST_CONTRACT_REF"
                ),
                "live_use_requires_future_owner_approval": True,
                "live_use_requires_accepted_source_and_connector_semantic_binding": True,
            }
        )
    return records


def _pit_lock_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


@dataclass(frozen=True, slots=True)
class PITReconstructionInputLockV2:
    lock_id: str
    profile_id: Stage1VenueProfileIdV1
    market_id: str
    instrument_id: str
    capture_session_id: str
    connection_epoch: str
    wire_dialect: str
    first_completed_event_ordinal: int
    last_completed_event_ordinal: int
    provider_sequence_start_or_none: int | None
    provider_sequence_end_or_none: int | None
    process_epoch_id: str
    monotonic_clock_id: str
    source_receipt_ref: str
    rights_receipt_ref: str
    commit_completion_refs: tuple[str, ...]
    state_ref: str
    state_vector: PITStateVectorV1
    reconstruction_receipt_ref: str
    capability_context_id: str
    serializer_version: str
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        for name in (
            "lock_id",
            "market_id",
            "instrument_id",
            "capture_session_id",
            "connection_epoch",
            "wire_dialect",
            "process_epoch_id",
            "monotonic_clock_id",
            "source_receipt_ref",
            "rights_receipt_ref",
            "state_ref",
            "reconstruction_receipt_ref",
            "capability_context_id",
            "serializer_version",
        ):
            _pit_lock_text(getattr(self, name), name)
        if self.serializer_version != "QKU_DETERMINISTIC_JSON_V1":
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "reconstruction lock serializer version is not exact",
            )
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "input lock profile has the wrong exact type",
            )
        for name in (
            "first_completed_event_ordinal",
            "last_completed_event_ordinal",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                    f"{name} must be an exact positive integer",
                )
        if self.first_completed_event_ordinal > self.last_completed_event_ordinal:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                "completed ordinal interval is reversed",
            )
        for name in (
            "provider_sequence_start_or_none",
            "provider_sequence_end_or_none",
        ):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE,
                    f"{name} must be an exact nonnegative integer or absent",
                )
        if (
            self.provider_sequence_start_or_none is None
        ) != (self.provider_sequence_end_or_none is None):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE,
                "provider sequence interval must be wholly present or absent",
            )
        if (
            self.provider_sequence_start_or_none is not None
            and self.provider_sequence_start_or_none
            > self.provider_sequence_end_or_none
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SEQUENCE_GAP,
                "provider sequence interval is reversed",
            )
        if type(self.commit_completion_refs) is not tuple or not (
            self.commit_completion_refs
        ) or any(
            type(value) is not str or not value
            for value in self.commit_completion_refs
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                "input lock requires exact commit-completion references",
            )
        if len(self.commit_completion_refs) != len(set(self.commit_completion_refs)):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "input lock commit-completion references must be unique",
            )
        if len(self.commit_completion_refs) != (
            self.last_completed_event_ordinal
            - self.first_completed_event_ordinal
            + 1
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                "input lock completion references do not cover the ordinal interval",
            )
        if type(self.state_vector) is not PITStateVectorV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "input lock state vector has the wrong exact type",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "input lock must carry exact NO_EFFECTS_V1",
            )


def build_pit_reconstruction_input_lock_v2(
    *,
    lock_id: str,
    profile_id: Stage1VenueProfileIdV1,
    market_id: str,
    instrument_id: str,
    capture_session_id: str,
    connection_epoch: str,
    wire_dialect: str,
    first_completed_event_ordinal: int,
    last_completed_event_ordinal: int,
    provider_sequence_start_or_none: int | None,
    provider_sequence_end_or_none: int | None,
    process_epoch_id: str,
    monotonic_clock_id: str,
    source_receipt_ref: str,
    rights_receipt_ref: str,
    commit_completion_refs: tuple[str, ...],
    state_ref: str,
    state_vector: PITStateVectorV1,
    reconstruction_receipt_ref: str,
    capability_context_id: str,
    serializer_version: str,
) -> PITReconstructionInputLockV2:
    return PITReconstructionInputLockV2(
        lock_id=lock_id,
        profile_id=profile_id,
        market_id=market_id,
        instrument_id=instrument_id,
        capture_session_id=capture_session_id,
        connection_epoch=connection_epoch,
        wire_dialect=wire_dialect,
        first_completed_event_ordinal=first_completed_event_ordinal,
        last_completed_event_ordinal=last_completed_event_ordinal,
        provider_sequence_start_or_none=provider_sequence_start_or_none,
        provider_sequence_end_or_none=provider_sequence_end_or_none,
        process_epoch_id=process_epoch_id,
        monotonic_clock_id=monotonic_clock_id,
        source_receipt_ref=source_receipt_ref,
        rights_receipt_ref=rights_receipt_ref,
        commit_completion_refs=commit_completion_refs,
        state_ref=state_ref,
        state_vector=state_vector,
        reconstruction_receipt_ref=reconstruction_receipt_ref,
        capability_context_id=capability_context_id,
        serializer_version=serializer_version,
    )
