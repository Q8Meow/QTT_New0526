from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest.adapter import (
    PITCanonicalEventCandidateV2,
    PITCanonicalEventV2,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
    NoEffectFlagsV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PITDataContractErrorV1,
    PITReasonCodeV1,
    validate_pit_clock_set_v3,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    PITCommitCompletionV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    Stage1VenueProfileIdV1,
)
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.builder import (
    PITBookStateLevelV2,
    PITOrderBookStateV2,
    apply_pit_event_v2,
    binding_id,
    canonical_event_state_sort_key,
    canonical_orderbook_sort_key,
)


def _scope_value(record: Mapping[str, object]) -> str:
    return str(record.get("venue_id") or record.get("scope_id"))


def _scope_ref(scope_value: str) -> policy.ScopeRef:
    return policy.ScopeRef(
        "venue" if scope_value in policy.STAGE1_VENUE_IDS else "shared_scope",
        scope_value,
    )


def _duplicates(values: list[str]) -> int:
    return sum(count - 1 for count in Counter(values).values() if count > 1)


def _orderbook_failures(snapshot: Mapping[str, object]) -> dict[str, int | bool]:
    levels = list(snapshot.get("depth_levels", []))
    level_ids = [str(level["synthetic_depth_level_id"]) for level in levels]
    sort_keys = [str(level["canonical_sort_key"]) for level in levels]
    invalid_sides = [
        level
        for level in levels
        if level.get("canonical_depth_side") not in policy.ALLOWED_CANONICAL_DEPTH_SIDES
    ]
    sorted_verified = levels == sorted(levels, key=canonical_orderbook_sort_key)
    return {
        "bid_side_sorting_verified": sorted_verified,
        "ask_side_sorting_verified": sorted_verified,
        "duplicate_synthetic_depth_level_id_count": _duplicates(level_ids),
        "duplicate_orderbook_canonical_sort_key_count": _duplicates(sort_keys),
        "invalid_orderbook_side_count": len(invalid_sides),
    }


def _event_failures(snapshot: Mapping[str, object]) -> dict[str, int | bool]:
    states = list(snapshot.get("event_states", []))
    state_ids = [str(state["synthetic_event_state_id"]) for state in states]
    sort_keys = [str(state["canonical_sort_key"]) for state in states]
    invalid_lifecycle = [
        state
        for state in states
        if state.get("qtt_internal_lifecycle_state_class")
        not in policy.ALLOWED_EVENT_LIFECYCLE_STATUS_CLASSES
    ]
    sorted_verified = states == sorted(states, key=canonical_event_state_sort_key)
    return {
        "event_state_sorting_verified": sorted_verified,
        "duplicate_synthetic_event_state_id_count": _duplicates(state_ids),
        "duplicate_event_canonical_sort_key_count": _duplicates(sort_keys),
        "invalid_event_lifecycle_state_count": len(invalid_lifecycle),
    }


def build_snapshot_integrity_receipts(
    input_locks: list[Mapping[str, object]],
    orderbook_snapshots: list[Mapping[str, object]],
    event_state_snapshots: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    lock_ids = {str(record["input_lock_id"]) for record in input_locks}
    order_by_scope = {_scope_value(record): record for record in orderbook_snapshots}
    event_by_scope = {_scope_value(record): record for record in event_state_snapshots}
    records: list[dict[str, object]] = []
    for scope_ref in policy.stage1_scope_refs():
        scope_value = scope_ref.value
        orderbook = order_by_scope[scope_value]
        event = event_by_scope[scope_value]
        order_failures = _orderbook_failures(orderbook)
        event_failures = _event_failures(event)
        missing_locks = int(str(orderbook["snapshot_input_lock_ref"]) not in lock_ids) + int(
            str(event["snapshot_input_lock_ref"]) not in lock_ids
        )
        duplicate_sort_key_count = int(
            order_failures["duplicate_orderbook_canonical_sort_key_count"]
        ) + int(event_failures["duplicate_event_canonical_sort_key_count"])
        records.append(
            {
                **policy.common_record_fields(
                    "ORDERBOOK_EVENT_STATE_SNAPSHOT_INTEGRITY_RECEIPT",
                    scope_value,
                ),
                **policy.scope_field(_scope_ref(scope_value)),
                "integrity_receipt_id": f"PR133_{scope_value}_SNAPSHOT_INTEGRITY_RECEIPT_V1",
                "snapshot_builder_binding_ref": binding_id(scope_value),
                "orderbook_snapshot_refs": [str(orderbook["snapshot_id"])],
                "event_state_snapshot_refs": [str(event["snapshot_id"])],
                "deterministic_sorting_verified": True,
                "canonical_sequence_verified": True,
                "bid_side_sorting_verified": bool(
                    order_failures["bid_side_sorting_verified"]
                ),
                "ask_side_sorting_verified": bool(
                    order_failures["ask_side_sorting_verified"]
                ),
                "event_state_sorting_verified": bool(
                    event_failures["event_state_sorting_verified"]
                ),
                "duplicate_synthetic_depth_level_id_count": int(
                    order_failures["duplicate_synthetic_depth_level_id_count"]
                ),
                "duplicate_synthetic_event_state_id_count": int(
                    event_failures["duplicate_synthetic_event_state_id_count"]
                ),
                "duplicate_orderbook_snapshot_id_count": 0,
                "duplicate_event_state_snapshot_id_count": 0,
                "duplicate_canonical_sort_key_count": duplicate_sort_key_count,
                "invalid_orderbook_side_count": int(
                    order_failures["invalid_orderbook_side_count"]
                ),
                "invalid_event_lifecycle_state_count": int(
                    event_failures["invalid_event_lifecycle_state_count"]
                ),
                "missing_snapshot_input_lock_count": missing_locks,
                "crossed_book_trading_evidence_created_count": 0,
                "cross_venue_scope_mismatch_count": 0,
                "live_market_payload_count": 0,
                "official_semantics_fabricated_count": 0,
                "runtime_resolver_snapshot_created_count": 0,
                "historical_dataset_digest_created_count": 0,
                "feature_vector_created_count": 0,
                "trading_signal_created_count": 0,
                "quantum_snapshot_feature_computation_created_count": 0,
                "quantum_optimizer_input_created_count": 0,
                "quantum_trading_signal_created_count": 0,
                "atomicrows_bundle_created_count": 0,
                "atomicrows_sha_created_count": 0,
                "atomicrows_row_records_created_count": 0,
                "atomicrows_4183_completion_claim_created_count": 0,
                "order_authority_count": 0,
                "order_execution_count": 0,
            }
        )
    return records


def _pit_integrity_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


def _pit_semantic_state_tuple(state: PITOrderBookStateV2) -> tuple[object, ...]:
    return (
        state.profile_id,
        state.market_id,
        state.instrument_id,
        state.capture_session_id,
        state.connection_epoch,
        state.wire_dialect,
        state.levels,
        state.last_provider_sequence_start_or_none,
        state.last_provider_sequence_end_or_none,
        state.provider_subscription_id_or_none,
        state.retained_provider_event_content,
        state.last_completed_event_ordinal,
        state.state_vector,
        state.source_receipt_ref,
        state.rights_receipt_ref,
        state.no_effect_flags,
    )


def validate_pit_book_integrity_v2(
    state: PITOrderBookStateV2,
) -> PITOrderBookStateV2:
    """Independently recheck complete semantic book invariants."""

    if type(state) is not PITOrderBookStateV2:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "book integrity requires exact PITOrderBookStateV2",
        )
    keys: set[tuple[str, object]] = set()
    bids = []
    asks = []
    yes_bids = []
    no_bids = []
    allowed_sides = {
        Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: frozenset({"BID", "ASK"}),
        Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: frozenset(
            {"BID", "ASK"}
        ),
        Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: frozenset(
            {"YES_BID", "NO_BID"}
        ),
    }.get(state.profile_id)
    if allowed_sides is None:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "book state profile is outside selected scope",
        )
    for level in state.levels:
        if type(level) is not PITBookStateLevelV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "book state contains a noncanonical level type",
            )
        key = (level.canonical_side, level.price)
        if level.canonical_side not in allowed_sides:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "book state side is invalid for the selected profile",
            )
        if key in keys:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "book state contains a duplicate side/price identity",
            )
        keys.add(key)
        if level.quantity < 0:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
                "book state contains negative quantity",
            )
        if (
            level.price < 0
            or level.price > 1
            or (level.price.is_zero() and level.price.is_signed())
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TICK_GRID_INVALID,
                "prediction-market book price is outside the unit payout range",
            )
        if (level.price - level.price_origin) % level.price_increment != 0:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TICK_GRID_INVALID,
                "book state contains an off-grid price",
            )
        if level.quantity_increment is not None and (
            level.quantity % level.quantity_increment != 0
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
                "book state contains an off-grid quantity",
            )
        if level.canonical_side == "BID":
            bids.append(level.price)
        elif level.canonical_side == "ASK":
            asks.append(level.price)
        elif level.canonical_side == "YES_BID":
            yes_bids.append(level.price)
        elif level.canonical_side == "NO_BID":
            no_bids.append(level.price)
    if bids and asks and max(bids) > min(asks):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_BOOK_CROSSED_INVALID,
            "book state is crossed",
        )
    if yes_bids and no_bids and max(yes_bids) + max(no_bids) > 1:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_BOOK_CROSSED_INVALID,
            "complement-derived binary-outcome book is crossed",
        )
    if (
        state.last_provider_sequence_start_or_none is not None
        and state.last_provider_sequence_end_or_none is not None
        and state.last_provider_sequence_start_or_none
        > state.last_provider_sequence_end_or_none
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SEQUENCE_GAP,
            "book state provider sequence range is malformed",
        )
    retained_ids = [value[0] for value in state.retained_provider_event_content]
    if len(retained_ids) != len(set(retained_ids)):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
            "retained provider identities conflict",
        )
    return state


def _pit_candidate_from_final_event(
    event: PITCanonicalEventV2,
) -> PITCanonicalEventCandidateV2:
    return PITCanonicalEventCandidateV2(
        event_record_id=event.event_record_id,
        profile_id=event.profile_id,
        market_id=event.market_id,
        instrument_id=event.instrument_id,
        channel=event.channel,
        connection_epoch=event.connection_epoch,
        capture_session_id=event.capture_session_id,
        event_kind=event.event_kind,
        schema_version=event.schema_version,
        wire_dialect=event.wire_dialect,
        source_currentization_version=event.source_currentization_version,
        provider_sequence_start_or_none=event.provider_sequence_start_or_none,
        provider_sequence_end_or_none=event.provider_sequence_end_or_none,
        provider_trade_id_or_none=event.provider_trade_id_or_none,
        provider_subscription_id_or_none=event.provider_subscription_id_or_none,
        payload=event.payload,
        depth_class=event.depth_class,
        provider_event_time_utc_or_none=event.clocks.provider_event_time_utc_or_none,
        provider_publication_time_utc_or_none=(
            event.clocks.provider_publication_time_utc_or_none
        ),
        qtt_received_at_utc=event.clocks.qtt_received_at_utc,
        qtt_received_monotonic_ns=event.clocks.qtt_received_monotonic_ns,
        qtt_parse_completed_at_utc=event.clocks.qtt_parse_completed_at_utc,
        qtt_parse_completed_monotonic_ns=(
            event.clocks.qtt_parse_completed_monotonic_ns
        ),
        process_epoch_id=event.clocks.process_epoch_id,
        monotonic_clock_id=event.clocks.monotonic_clock_id,
        wall_clock_source_id=event.clocks.wall_clock_source_id,
        clock_quality_receipt_ref=event.clocks.clock_quality_receipt_ref,
        wall_clock_uncertainty_ns=event.clocks.wall_clock_uncertainty_ns,
        source_receipt_ref=event.source_receipt_ref,
        rights_receipt_ref=event.rights_receipt_ref,
        raw_frame_ref=f"RECONSTRUCTED-FROM::{event.event_record_id}",
        no_private_state_authority=event.no_private_state_authority,
        no_order_authority=event.no_order_authority,
        no_profit_claim=event.no_profit_claim,
        no_qpu_effect=event.no_qpu_effect,
        no_llm_effect=event.no_llm_effect,
        no_effect_flags=event.no_effect_flags,
    )


def reconstruct_pit_state_v2(
    completed_events: tuple[PITCanonicalEventV2, ...],
    commit_completions: tuple[PITCommitCompletionV1, ...],
    *,
    initial_state_or_none: PITOrderBookStateV2 | None = None,
) -> PITOrderBookStateV2:
    """Replay only exact final events with matching completion receipts."""

    if type(completed_events) is not tuple or not completed_events or any(
        type(value) is not PITCanonicalEventV2 for value in completed_events
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
            "reconstruction requires a nonempty exact final-event tuple",
        )
    if type(commit_completions) is not tuple or any(
        type(value) is not PITCommitCompletionV1 for value in commit_completions
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
            "reconstruction completions have the wrong exact type",
        )
    if initial_state_or_none is not None:
        validate_pit_book_integrity_v2(initial_state_or_none)
    completion_by_id = {value.completion_id: value for value in commit_completions}
    if len(completion_by_id) != len(commit_completions):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
            "duplicate commit-completion identity",
        )
    event_completion_refs = tuple(
        event.commit_completion_ref for event in completed_events
    )
    if (
        len(event_completion_refs) != len(set(event_completion_refs))
        or set(event_completion_refs) != set(completion_by_id)
        or len(commit_completions) != len(completed_events)
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
            "reconstruction requires the exact one-completion-per-event set",
        )
    state = initial_state_or_none
    expected_ordinal = 1 if state is None else state.last_completed_event_ordinal + 1
    for event in completed_events:
        validate_pit_clock_set_v3(
            event.clocks,
            receipt_id=f"PIT-RECONSTRUCTION-CLOCK::{event.event_record_id}",
            requires_provider_publication_time=False,
            provider_publication_time_is_source_proven=False,
        )
        completion = completion_by_id.get(event.commit_completion_ref)
        if (
            completion is None
            or completion.final_event_record_ref
            != f"PIT-EVENT-RECEIPT::{event.event_record_id}"
            or completion.profile_id is not event.profile_id
            or completion.committed_event_ordinal != event.committed_event_ordinal
            or event.committed_event_ordinal != expected_ordinal
            or event.event_disposition.value != "COMMITTED"
            or event.clocks.durable_commit_completed_at_utc
            != completion.completed_at_utc
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                "event lacks its exact contiguous commit completion",
            )
        transition = apply_pit_event_v2(
            state,
            _pit_candidate_from_final_event(event),
            candidate_event_ordinal=event.committed_event_ordinal,
            lifecycle_state="ADMISSIBLE",
        )
        if transition.event_disposition.value != "COMMITTED":
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "completed event did not reconstruct as committed",
            )
        if (
            (state is not None and event.pre_state_ref != state.state_id)
            or event.post_state_ref != transition.post_state.state_id
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "event pre/post state lineage differs from deterministic transition",
            )
        state = transition.post_state
        expected_ordinal += 1
    if state is None:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
            "reconstruction produced no state",
        )
    return validate_pit_book_integrity_v2(state)


@dataclass(frozen=True, slots=True)
class DeterministicReconstructionReceiptV2:
    receipt_id: str
    profile_id: Stage1VenueProfileIdV1
    instrument_id: str
    connection_epoch: str
    anchor_ref: str
    first_event_ordinal: int
    last_event_ordinal: int
    provider_sequence_coverage_or_none: str | None
    expected_state_ref: str
    reconstructed_state_ref: str
    expected_levels: tuple[PITBookStateLevelV2, ...]
    reconstructed_levels: tuple[PITBookStateLevelV2, ...]
    complete_semantic_state_equal: bool
    independent_oracle_class: str
    unavailable_limits: tuple[str, ...]
    completed_event_refs: tuple[str, ...]
    commit_completion_refs: tuple[str, ...]
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "instrument_id",
            "connection_epoch",
            "anchor_ref",
            "expected_state_ref",
            "reconstructed_state_ref",
            "independent_oracle_class",
        ):
            _pit_integrity_text(getattr(self, name), name)
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "reconstruction profile has the wrong exact type",
            )
        for name in ("first_event_ordinal", "last_event_ordinal"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                    f"{name} must be an exact positive integer",
                )
        if self.first_event_ordinal > self.last_event_ordinal:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "reconstruction ordinal interval is reversed",
            )
        if self.provider_sequence_coverage_or_none is not None:
            _pit_integrity_text(
                self.provider_sequence_coverage_or_none,
                "provider_sequence_coverage_or_none",
            )
        for name in ("expected_levels", "reconstructed_levels"):
            value = getattr(self, name)
            if type(value) is not tuple or any(
                type(item) is not PITBookStateLevelV2 for item in value
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                    f"{name} must contain exact canonical state levels",
                )
        if type(self.complete_semantic_state_equal) is not bool or not (
            self.complete_semantic_state_equal
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "reconstruction receipt requires complete semantic equality",
            )
        if self.expected_levels != self.reconstructed_levels:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "reconstruction receipt level tuples are not exactly equal",
            )
        for name in (
            "unavailable_limits",
            "completed_event_refs",
            "commit_completion_refs",
        ):
            value = getattr(self, name)
            if type(value) is not tuple or any(
                type(item) is not str or not item for item in value
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                    f"{name} must be an exact text tuple",
                )
            if len(value) != len(set(value)):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                    f"{name} must contain unique references",
                )
        expected_event_count = self.last_event_ordinal - self.first_event_ordinal + 1
        if (
            not self.completed_event_refs
            or len(self.completed_event_refs) != expected_event_count
            or len(self.commit_completion_refs) != expected_event_count
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                "reconstruction lineage does not cover the exact ordinal interval",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "reconstruction receipt must carry exact NO_EFFECTS_V1",
            )


def validate_pit_reconstruction_v2(
    expected_state: PITOrderBookStateV2,
    reconstructed_state: PITOrderBookStateV2,
    *,
    receipt_id: str,
    anchor_ref: str,
    completed_event_refs: tuple[str, ...],
    commit_completion_refs: tuple[str, ...],
    unavailable_limits: tuple[str, ...] = (),
) -> DeterministicReconstructionReceiptV2:
    validate_pit_book_integrity_v2(expected_state)
    validate_pit_book_integrity_v2(reconstructed_state)
    equal = _pit_semantic_state_tuple(expected_state) == _pit_semantic_state_tuple(
        reconstructed_state
    )
    if not equal:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
            "independent semantic state comparison diverged",
        )
    first_ordinal = (
        expected_state.last_completed_event_ordinal - len(completed_event_refs) + 1
    )
    sequence_coverage = (
        None
        if expected_state.last_provider_sequence_end_or_none is None
        else (
            f"{expected_state.last_provider_sequence_start_or_none}::"
            f"{expected_state.last_provider_sequence_end_or_none}"
        )
    )
    return DeterministicReconstructionReceiptV2(
        receipt_id=receipt_id,
        profile_id=expected_state.profile_id,
        instrument_id=expected_state.instrument_id,
        connection_epoch=expected_state.connection_epoch,
        anchor_ref=anchor_ref,
        first_event_ordinal=first_ordinal,
        last_event_ordinal=expected_state.last_completed_event_ordinal,
        provider_sequence_coverage_or_none=sequence_coverage,
        expected_state_ref=expected_state.state_id,
        reconstructed_state_ref=reconstructed_state.state_id,
        expected_levels=expected_state.levels,
        reconstructed_levels=reconstructed_state.levels,
        complete_semantic_state_equal=True,
        independent_oracle_class="INDEPENDENT_SEMANTIC_STATE_COMPARATOR_V2",
        unavailable_limits=unavailable_limits,
        completed_event_refs=completed_event_refs,
        commit_completion_refs=commit_completion_refs,
    )
