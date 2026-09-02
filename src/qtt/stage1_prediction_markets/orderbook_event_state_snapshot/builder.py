from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest.adapter import (
    PITCanonicalEventCandidateV2,
    _PITBookAbsoluteUpdatePayloadV2,
    _PITBookDeltaPayloadV2,
    _PITBookReplacementPayloadV2,
    _PITBookSnapshotPayloadV2,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
    NoEffectFlagsV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PITAnchorStateV1,
    PITContinuityStateV3,
    PITDataContractErrorV1,
    PITDepthClassV2,
    PITEventDispositionV1,
    PITEventKindV2,
    PITIntegrityStateV1,
    PITReasonCodeV1,
    PITTransportStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    Stage1VenueProfileIdV1,
)
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.policy import (
    PITStateVectorV1,
    _derive_pit_availability_v2,
)


def _scope_value(record: Mapping[str, object]) -> str:
    return str(record.get("venue_id") or record.get("scope_id"))


def _scope_ref_from_value(scope_value: str) -> policy.ScopeRef:
    return policy.ScopeRef(
        "venue" if scope_value in policy.STAGE1_VENUE_IDS else "shared_scope",
        scope_value,
    )


def orderbook_snapshot_id(scope_value: str) -> str:
    return f"PR133_{scope_value}_ORDERBOOK_SNAPSHOT_V1"


def event_state_snapshot_id(scope_value: str) -> str:
    return f"PR133_{scope_value}_EVENT_STATE_SNAPSHOT_V1"


def binding_id(scope_value: str) -> str:
    return f"PR133_{scope_value}_SNAPSHOT_BUILDER_BINDING_V1"


def canonical_orderbook_sort_key(level: Mapping[str, object]) -> tuple[object, ...]:
    side = str(level["canonical_depth_side"])
    if side == "BID_METADATA":
        return (
            side,
            -int(level["canonical_price_rank"]),
            -int(level["canonical_quantity_rank"]),
            str(level["synthetic_depth_level_id"]),
        )
    if side == "ASK_METADATA":
        return (
            side,
            int(level["canonical_price_rank"]),
            -int(level["canonical_quantity_rank"]),
            str(level["synthetic_depth_level_id"]),
        )
    return (
        side,
        str(level["synthetic_depth_level_id"]),
    )


def canonical_event_state_sort_key(state: Mapping[str, object]) -> tuple[object, ...]:
    lifecycle = str(state["qtt_internal_lifecycle_state_class"])
    return (
        int(state["canonical_event_state_rank"]),
        str(state["synthetic_event_state_id"]),
        lifecycle,
    )


def _depth_levels(scope_value: str) -> list[dict[str, object]]:
    raw = [
        ("BID_METADATA", 20, 9, "BID_A"),
        ("BID_METADATA", 10, 7, "BID_B"),
        ("ASK_METADATA", 30, 8, "ASK_A"),
        ("ASK_METADATA", 40, 6, "ASK_B"),
        ("UNKNOWN_SOURCE_REQUIRED", 0, 0, "UNKNOWN_A"),
    ]
    levels = []
    for side, price_rank, quantity_rank, suffix in raw:
        level_id = f"PR133_{scope_value}_DEPTH_LEVEL_{suffix}_V1"
        levels.append(
            {
                "synthetic_depth_level_id": level_id,
                "canonical_depth_side": side,
                "canonical_price_rank": price_rank,
                "canonical_quantity_rank": quantity_rank,
                "canonical_sort_key": (
                    f"{side}|{price_rank:04d}|{quantity_rank:04d}|{level_id}"
                ),
                "qtt_internal_orderbook_side_class": side,
                "qtt_internal_price_level_class": "QTT_INTERNAL_PRICE_RANK_METADATA_ONLY",
                "qtt_internal_quantity_level_class": (
                    "QTT_INTERNAL_QUANTITY_RANK_METADATA_ONLY"
                ),
                "deterministic_sequence_id": f"PR133_{scope_value}_{suffix}_DEPTH_SEQUENCE",
            }
        )
    return sorted(levels, key=canonical_orderbook_sort_key)


def _event_states(scope_value: str) -> list[dict[str, object]]:
    states = []
    for lifecycle in policy.ALLOWED_EVENT_LIFECYCLE_STATUS_CLASSES:
        state_id = f"PR133_{scope_value}_{lifecycle}_EVENT_STATE_V1"
        rank = policy.EVENT_LIFECYCLE_RANKS[lifecycle]
        states.append(
            {
                "synthetic_event_state_id": state_id,
                "canonical_event_state_rank": rank,
                "canonical_sort_key": f"{rank:04d}|{state_id}",
                "qtt_internal_event_status_class": lifecycle,
                "qtt_internal_lifecycle_state_class": lifecycle,
                "qtt_internal_settlement_state_class": (
                    "QTT_INTERNAL_SETTLEMENT_METADATA_ONLY"
                ),
                "deterministic_sequence_id": (
                    f"PR133_{scope_value}_{lifecycle}_EVENT_STATE_SEQUENCE"
                ),
            }
        )
    return sorted(states, key=canonical_event_state_sort_key)


def build_orderbook_snapshots(
    input_locks: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for sequence, lock in enumerate(input_locks, start=1):
        scope_value = _scope_value(lock)
        scope_ref = _scope_ref_from_value(scope_value)
        levels = _depth_levels(scope_value)
        records.append(
            {
                **policy.common_record_fields("ORDERBOOK_SNAPSHOT_RECORD", scope_value),
                **policy.scope_field(scope_ref),
                "snapshot_id": orderbook_snapshot_id(scope_value),
                "snapshot_input_lock_ref": str(lock["input_lock_id"]),
                "snapshot_class": "SYNTHETIC_FIXTURE_ORDERBOOK_SNAPSHOT",
                "qtt_internal_snapshot_class": "QTT_INTERNAL_ORDERBOOK_DEPTH_METADATA_SNAPSHOT",
                "deterministic_sequence_id": f"PR133_ORDERBOOK_SEQUENCE_{sequence:04d}",
                "synthetic_depth_level_refs": [
                    str(level["synthetic_depth_level_id"]) for level in levels
                ],
                "synthetic_depth_level_id": f"PR133_{scope_value}_ORDERBOOK_AGGREGATE_V1",
                "depth_levels": levels,
                "canonical_depth_side": "UNKNOWN_SOURCE_REQUIRED",
                "canonical_price_rank": 0,
                "canonical_quantity_rank": 0,
                "canonical_sort_key": f"PR133_{scope_value}_ORDERBOOK_AGGREGATE_SORT_KEY",
                "qtt_internal_orderbook_side_class": "QTT_INTERNAL_DEPTH_METADATA_MIXED",
                "qtt_internal_price_level_class": "QTT_INTERNAL_PRICE_RANK_METADATA_ONLY",
                "qtt_internal_quantity_level_class": (
                    "QTT_INTERNAL_QUANTITY_RANK_METADATA_ONLY"
                ),
                "official_venue_field_value_source_state": str(
                    lock["source_dependency_state"]
                ),
                "fixture_orderbook_snapshot_created": True,
                "crossed_book_valid_trading_evidence_created": False,
                "orderbook_snapshot_is_trading_signal": False,
                "orderbook_snapshot_is_feature_vector": False,
                "orderbook_snapshot_is_quantum_feature_vector": False,
                "orderbook_snapshot_is_atomicrows_row": False,
                "orderbook_snapshot_is_order_authority": False,
                "orderbook_snapshot_is_runtime_resolver_snapshot": False,
                "no_live_fetch": True,
                "no_network_io": True,
                "no_order_authority": True,
                "no_profit_evidence": True,
                "no_quantum_execution": True,
            }
        )
    return records


def _pit_book_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


def _pit_book_decimal(value: object, name: str) -> tuple[str, Decimal, int]:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", value) is None
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
            f"{name} must be exact decimal text",
        )
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
            f"{name} is not an exact decimal",
        ) from exc
    if not parsed.is_finite() or str(parsed) != value:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
            f"{name} must be finite canonical decimal text",
        )
    exponent = parsed.as_tuple().exponent
    return value, parsed, -exponent if exponent < 0 else 0


def _validate_pit_level_numeric_fields(
    *,
    price_text: str,
    price: Decimal,
    quantity_text: str,
    quantity: Decimal,
    price_scale: int,
    quantity_scale: int,
    quantity_nonnegative: bool,
) -> None:
    _, parsed_price, parsed_price_scale = _pit_book_decimal(
        price_text, "price_text"
    )
    _, parsed_quantity, parsed_quantity_scale = _pit_book_decimal(
        quantity_text, "quantity_text"
    )
    if (
        type(price) is not Decimal
        or price != parsed_price
        or type(quantity) is not Decimal
        or quantity != parsed_quantity
        or type(price_scale) is not int
        or price_scale != parsed_price_scale
        or type(quantity_scale) is not int
        or quantity_scale != parsed_quantity_scale
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
            "level text, Decimal, and declared scale differ",
        )
    if price.is_zero() and price.is_signed():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
            "book price cannot use a negative-zero representation",
        )
    if quantity_nonnegative and (quantity < 0 or quantity.is_signed()):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
            "book state/absolute quantity cannot be negative",
        )
    if not quantity_nonnegative and quantity.is_zero() and quantity.is_signed():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
            "signed delta cannot use a negative-zero representation",
        )


@dataclass(frozen=True, slots=True)
class PITBookStateLevelV2:
    source_side: str
    canonical_side: str
    price_text: str
    price: Decimal
    quantity_text: str
    quantity: Decimal
    price_scale: int
    quantity_scale: int
    price_increment: Decimal
    price_origin: Decimal
    quantity_increment: Decimal | None

    def __post_init__(self) -> None:
        _pit_book_text(self.source_side, "source_side")
        _pit_book_text(self.canonical_side, "canonical_side")
        _validate_pit_level_numeric_fields(
            price_text=self.price_text,
            price=self.price,
            quantity_text=self.quantity_text,
            quantity=self.quantity,
            price_scale=self.price_scale,
            quantity_scale=self.quantity_scale,
            quantity_nonnegative=True,
        )
        if (
            type(self.price_increment) is not Decimal
            or not self.price_increment.is_finite()
            or self.price_increment <= 0
            or type(self.price_origin) is not Decimal
            or not self.price_origin.is_finite()
            or (self.price - self.price_origin) % self.price_increment != 0
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TICK_GRID_INVALID,
                "state level price is off its exact origin/increment grid",
            )
        if self.quantity_increment is not None and (
            type(self.quantity_increment) is not Decimal
            or not self.quantity_increment.is_finite()
            or self.quantity_increment <= 0
            or self.quantity % self.quantity_increment != 0
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
                "state level quantity is off its exact increment grid",
            )


@dataclass(frozen=True, slots=True)
class PITBookAbsoluteLevelUpdateV2:
    source_side: str
    canonical_side: str
    price_text: str
    price: Decimal
    absolute_quantity_text: str
    absolute_quantity: Decimal
    price_scale: int
    quantity_scale: int

    def __post_init__(self) -> None:
        _pit_book_text(self.source_side, "source_side")
        _pit_book_text(self.canonical_side, "canonical_side")
        _validate_pit_level_numeric_fields(
            price_text=self.price_text,
            price=self.price,
            quantity_text=self.absolute_quantity_text,
            quantity=self.absolute_quantity,
            price_scale=self.price_scale,
            quantity_scale=self.quantity_scale,
            quantity_nonnegative=True,
        )


@dataclass(frozen=True, slots=True)
class PITBookDeltaLevelV2:
    source_side: str
    canonical_side: str
    price_text: str
    price: Decimal
    quantity_delta_text: str
    quantity_delta: Decimal
    price_scale: int
    quantity_scale: int

    def __post_init__(self) -> None:
        _pit_book_text(self.source_side, "source_side")
        _pit_book_text(self.canonical_side, "canonical_side")
        _validate_pit_level_numeric_fields(
            price_text=self.price_text,
            price=self.price,
            quantity_text=self.quantity_delta_text,
            quantity=self.quantity_delta,
            price_scale=self.price_scale,
            quantity_scale=self.quantity_scale,
            quantity_nonnegative=False,
        )


def _pit_state_level_sort_key(level: PITBookStateLevelV2) -> tuple[object, ...]:
    if level.canonical_side == "BID":
        return (0, -level.price, level.source_side)
    if level.canonical_side == "ASK":
        return (1, level.price, level.source_side)
    return (2, level.canonical_side, level.price, level.source_side)


@dataclass(frozen=True, slots=True)
class PITOrderBookStateV2:
    state_id: str
    profile_id: Stage1VenueProfileIdV1
    market_id: str
    instrument_id: str
    capture_session_id: str
    connection_epoch: str
    wire_dialect: str
    levels: tuple[PITBookStateLevelV2, ...]
    last_provider_sequence_start_or_none: int | None
    last_provider_sequence_end_or_none: int | None
    provider_subscription_id_or_none: str | None
    retained_provider_event_content: tuple[tuple[str, str], ...]
    last_completed_event_ordinal: int
    state_vector: PITStateVectorV1
    source_receipt_ref: str
    rights_receipt_ref: str
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        for name in (
            "state_id",
            "market_id",
            "instrument_id",
            "capture_session_id",
            "connection_epoch",
            "wire_dialect",
            "source_receipt_ref",
            "rights_receipt_ref",
        ):
            _pit_book_text(getattr(self, name), name)
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "state profile has the wrong exact type",
            )
        if type(self.levels) is not tuple or any(
            type(value) is not PITBookStateLevelV2 for value in self.levels
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "state levels must be exact PITBookStateLevelV2 values",
            )
        if self.levels != tuple(sorted(self.levels, key=_pit_state_level_sort_key)):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
                "state levels are not in canonical order",
            )
        keys = tuple((value.canonical_side, value.price) for value in self.levels)
        if len(keys) != len(set(keys)):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "state contains duplicate canonical side/price levels",
            )
        _pit_validate_state_book(self.profile_id, self.levels)
        for name in (
            "last_provider_sequence_start_or_none",
            "last_provider_sequence_end_or_none",
        ):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE,
                    f"{name} must be exact nonnegative integer or absent",
                )
        if (
            self.last_provider_sequence_start_or_none is None
        ) != (self.last_provider_sequence_end_or_none is None):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE,
                "state provider sequence range must be wholly present or wholly absent",
            )
        if (
            self.last_provider_sequence_start_or_none is not None
            and self.last_provider_sequence_start_or_none
            > self.last_provider_sequence_end_or_none
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SEQUENCE_GAP,
                "state provider sequence range is reversed",
            )
        if self.provider_subscription_id_or_none is not None:
            _pit_book_text(
                self.provider_subscription_id_or_none,
                "provider_subscription_id_or_none",
            )
        if self.profile_id is Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT and (
            self.last_provider_sequence_start_or_none is not None
            or self.provider_subscription_id_or_none is not None
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE,
                "Retail state cannot claim provider sequence/subscription identity",
            )
        if (
            self.profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT
            and self.provider_subscription_id_or_none is not None
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE,
                "Gemini state does not expose provider subscription identity",
            )
        if (
            self.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT
            and self.last_provider_sequence_start_or_none is not None
            and self.provider_subscription_id_or_none is None
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE,
                "Kalshi sequenced state requires exact provider subscription identity",
            )
        if type(self.retained_provider_event_content) is not tuple or any(
            type(value) is not tuple
            or len(value) != 2
            or any(type(item) is not str or not item for item in value)
            for value in self.retained_provider_event_content
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "retained provider event content must be exact identity/JSON pairs",
            )
        retained_ids = tuple(value[0] for value in self.retained_provider_event_content)
        if len(retained_ids) != len(set(retained_ids)):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "retained provider identities must be unique",
            )
        if type(self.last_completed_event_ordinal) is not int or self.last_completed_event_ordinal < 0:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                "last completed ordinal must be an exact nonnegative integer",
            )
        if type(self.state_vector) is not PITStateVectorV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "state vector has the wrong exact type",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "book state must carry exact NO_EFFECTS_V1",
            )


@dataclass(frozen=True, slots=True)
class PITBookTransitionResultV2:
    transition_id: str
    event_record_ref: str
    pre_state_ref_or_none: str | None
    post_state: PITOrderBookStateV2
    event_disposition: PITEventDispositionV1
    continuity_result: PITContinuityStateV3
    integrity_result: PITIntegrityStateV1
    failure_reason_or_none: PITReasonCodeV1 | None
    recovery_required: bool
    provider_identity: str
    candidate_content_json: str
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        for name in (
            "transition_id",
            "event_record_ref",
            "provider_identity",
            "candidate_content_json",
        ):
            _pit_book_text(getattr(self, name), name)
        if self.pre_state_ref_or_none is not None:
            _pit_book_text(self.pre_state_ref_or_none, "pre_state_ref_or_none")
        if type(self.post_state) is not PITOrderBookStateV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "transition post state has the wrong exact type",
            )
        for name, enum_type in (
            ("event_disposition", PITEventDispositionV1),
            ("continuity_result", PITContinuityStateV3),
            ("integrity_result", PITIntegrityStateV1),
        ):
            if type(getattr(self, name)) is not enum_type:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} has the wrong exact type",
                )
        if self.failure_reason_or_none is not None and type(
            self.failure_reason_or_none
        ) is not PITReasonCodeV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "transition failure reason has the wrong exact type",
            )
        if type(self.recovery_required) is not bool:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "recovery_required must be exact Boolean",
            )
        if self.event_disposition is PITEventDispositionV1.COMMITTED:
            if self.failure_reason_or_none is not None or self.recovery_required:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                    "committed transition cannot carry failure/recovery state",
                )
        elif self.event_disposition is not PITEventDispositionV1.DUPLICATE_IGNORED and (
            self.failure_reason_or_none is None
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "rejected/quarantined transition requires a specific reason",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "transition must carry exact NO_EFFECTS_V1",
            )


def _pit_public_level(value: object) -> PITBookStateLevelV2:
    return PITBookStateLevelV2(
        source_side=value.source_side,
        canonical_side=value.canonical_side,
        price_text=value.price_text,
        price=value.price,
        quantity_text=value.quantity_text,
        quantity=value.quantity,
        price_scale=value.price_scale,
        quantity_scale=value.quantity_scale,
        price_increment=value.price_increment,
        price_origin=value.price_origin,
        quantity_increment=value.quantity_increment_or_none,
    )


def _pit_provider_identity(candidate: PITCanonicalEventCandidateV2) -> str:
    if candidate.event_kind is PITEventKindV2.TRADE:
        if candidate.profile_id in {
            Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT,
            Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT,
        }:
            if candidate.provider_trade_id_or_none is None:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    "trade event lacks its exact provider trade identity",
                )
            return (
                f"{candidate.profile_id.value}-TRADE::{candidate.instrument_id}::"
                f"{candidate.provider_trade_id_or_none}"
            )
        return f"PROVIDER-TRADE-IDENTITY-ABSENT::{candidate.event_record_id}"
    if candidate.profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT:
        if (
            candidate.provider_sequence_start_or_none is None
            or candidate.provider_sequence_end_or_none is None
        ):
            return f"GEMINI-NONSEQUENCED::{candidate.event_record_id}"
        return (
            f"GEMINI::{candidate.instrument_id}::{candidate.connection_epoch}::"
            f"{candidate.provider_sequence_start_or_none}::"
            f"{candidate.provider_sequence_end_or_none}"
        )
    if candidate.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT:
        if (
            candidate.provider_subscription_id_or_none is None
            or candidate.provider_sequence_end_or_none is None
        ):
            return f"KALSHI-NONSEQUENCED::{candidate.event_record_id}"
        return (
            f"KALSHI::{candidate.connection_epoch}::"
            f"{candidate.provider_subscription_id_or_none}::"
            f"{candidate.provider_sequence_end_or_none}"
        )
    return f"PROVIDER-IDENTITY-ABSENT::{candidate.event_record_id}"


def _pit_polymarket_parity_matches(
    prior_state: PITOrderBookStateV2,
    candidate_levels: tuple[PITBookStateLevelV2, ...],
    candidate_depth: PITDepthClassV2,
) -> bool:
    if (
        prior_state.state_vector.depth_class
        is PITDepthClassV2.PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME
    ):
        published_levels = prior_state.levels
        complete_levels = candidate_levels
    elif candidate_depth is (
        PITDepthClassV2.PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME
    ):
        published_levels = candidate_levels
        complete_levels = prior_state.levels
    else:
        return False
    for side, reverse in (("BID", True), ("ASK", False)):
        published_side = tuple(
            sorted(
                (
                    (level.price, level.quantity)
                    for level in published_levels
                    if level.canonical_side == side
                ),
                reverse=reverse,
            )
        )
        complete_side = tuple(
            sorted(
                (
                    (level.price, level.quantity)
                    for level in complete_levels
                    if level.canonical_side == side
                ),
                reverse=reverse,
            )
        )
        if (not published_side and complete_side) or published_side != complete_side[
            : len(published_side)
        ]:
            return False
    return True


def _pit_apply_scalar_event(
    prior_state: PITOrderBookStateV2 | None,
    candidate: PITCanonicalEventCandidateV2,
    *,
    candidate_event_ordinal: int,
    provider_identity: str,
    candidate_content_json: str,
    transport_state: PITTransportStateV1,
    lifecycle_state: str,
) -> PITBookTransitionResultV2:
    retained_by_id = (
        dict(prior_state.retained_provider_event_content)
        if prior_state is not None
        else {}
    )
    retained_by_id[provider_identity] = candidate_content_json
    same_epoch = (
        prior_state is not None
        and prior_state.connection_epoch == candidate.connection_epoch
    )
    if prior_state is None:
        levels: tuple[PITBookStateLevelV2, ...] = ()
        last_start = None
        last_end = None
        subscription_id = None
        depth = PITDepthClassV2.BBO_ONLY
        anchor = PITAnchorStateV1.ANCHOR_REQUIRED
        continuity = (
            PITContinuityStateV3.SEQUENCE_UNAVAILABLE
            if candidate.profile_id
            is Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT
            else PITContinuityStateV3.RECOVERY_IN_PROGRESS
        )
        integrity = PITIntegrityStateV1.UNVALIDATED
    elif same_epoch:
        levels = prior_state.levels
        last_start = prior_state.last_provider_sequence_start_or_none
        last_end = prior_state.last_provider_sequence_end_or_none
        subscription_id = prior_state.provider_subscription_id_or_none
        depth = prior_state.state_vector.depth_class
        anchor = prior_state.state_vector.anchor_state
        continuity = prior_state.state_vector.continuity_state
        integrity = prior_state.state_vector.integrity_state
    else:
        levels = prior_state.levels
        last_start = None
        last_end = None
        subscription_id = None
        depth = prior_state.state_vector.depth_class
        anchor = PITAnchorStateV1.REANCHOR_REQUIRED
        continuity = PITContinuityStateV3.RECOVERY_IN_PROGRESS
        integrity = prior_state.state_vector.integrity_state
    state_vector = _pit_state_vector(
        transport=transport_state,
        anchor=anchor,
        continuity=continuity,
        integrity=integrity,
        depth=depth,
        lifecycle_state=lifecycle_state,
    )
    post_state = PITOrderBookStateV2(
        state_id=f"PIT-STATE::{candidate.event_record_id}::{candidate_event_ordinal}",
        profile_id=candidate.profile_id,
        market_id=candidate.market_id,
        instrument_id=candidate.instrument_id,
        capture_session_id=candidate.capture_session_id,
        connection_epoch=candidate.connection_epoch,
        wire_dialect=candidate.wire_dialect,
        levels=levels,
        last_provider_sequence_start_or_none=last_start,
        last_provider_sequence_end_or_none=last_end,
        provider_subscription_id_or_none=subscription_id,
        retained_provider_event_content=tuple(retained_by_id.items()),
        last_completed_event_ordinal=candidate_event_ordinal,
        state_vector=state_vector,
        source_receipt_ref=candidate.source_receipt_ref,
        rights_receipt_ref=candidate.rights_receipt_ref,
    )
    return PITBookTransitionResultV2(
        transition_id=f"PIT-TRANSITION::{candidate.event_record_id}",
        event_record_ref=candidate.event_record_id,
        pre_state_ref_or_none=(prior_state.state_id if prior_state else None),
        post_state=post_state,
        event_disposition=PITEventDispositionV1.COMMITTED,
        continuity_result=continuity,
        integrity_result=integrity,
        failure_reason_or_none=None,
        recovery_required=False,
        provider_identity=provider_identity,
        candidate_content_json=candidate_content_json,
    )


def _pit_state_vector(
    *,
    transport: PITTransportStateV1,
    anchor: PITAnchorStateV1,
    continuity: PITContinuityStateV3,
    integrity: PITIntegrityStateV1,
    depth: PITDepthClassV2,
    lifecycle_state: str,
) -> PITStateVectorV1:
    availability = _derive_pit_availability_v2(
        transport_state=transport,
        anchor_state=anchor,
        continuity_state=continuity,
        integrity_state=integrity,
        depth_class=depth,
        lifecycle_state=lifecycle_state,
    )
    return PITStateVectorV1(
        transport_state=transport,
        anchor_state=anchor,
        continuity_state=continuity,
        integrity_state=integrity,
        availability_state=availability,
        event_disposition=PITEventDispositionV1.COMMITTED,
        depth_class=depth,
        lifecycle_state=lifecycle_state,
    )


def _pit_validate_state_book(
    profile_id: Stage1VenueProfileIdV1,
    levels: tuple[PITBookStateLevelV2, ...],
) -> None:
    allowed_sides = {
        Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: frozenset({"BID", "ASK"}),
        Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: frozenset(
            {"BID", "ASK"}
        ),
        Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: frozenset(
            {"YES_BID", "NO_BID"}
        ),
    }.get(profile_id)
    if allowed_sides is None:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "book state profile is outside selected scope",
        )
    if any(level.canonical_side not in allowed_sides for level in levels):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "book state side is invalid for the selected profile",
        )
    if any(
        level.price < 0
        or level.price > 1
        or (level.price.is_zero() and level.price.is_signed())
        for level in levels
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_TICK_GRID_INVALID,
            "prediction-market book price is outside the unit payout range",
        )
    bids = [value.price for value in levels if value.canonical_side == "BID"]
    asks = [value.price for value in levels if value.canonical_side == "ASK"]
    if bids and asks and max(bids) > min(asks):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_BOOK_CROSSED_INVALID,
            "resulting book is crossed",
        )
    yes_bids = [
        value.price for value in levels if value.canonical_side == "YES_BID"
    ]
    no_bids = [
        value.price for value in levels if value.canonical_side == "NO_BID"
    ]
    if yes_bids and no_bids and max(yes_bids) + max(no_bids) > 1:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_BOOK_CROSSED_INVALID,
            "complement-derived binary-outcome book is crossed",
        )


def _pit_unavailable_state(
    prior_state: PITOrderBookStateV2 | None,
    candidate: PITCanonicalEventCandidateV2,
    *,
    continuity: PITContinuityStateV3,
    integrity: PITIntegrityStateV1,
    lifecycle_state: str,
) -> PITOrderBookStateV2:
    if prior_state is None:
        levels: tuple[PITBookStateLevelV2, ...] = ()
        last_start = None
        last_end = None
        subscription_id = candidate.provider_subscription_id_or_none
        retained: tuple[tuple[str, str], ...] = ()
        last_ordinal = 0
        source_ref = candidate.source_receipt_ref
        rights_ref = candidate.rights_receipt_ref
        depth = candidate.depth_class
    else:
        levels = prior_state.levels
        last_start = prior_state.last_provider_sequence_start_or_none
        last_end = prior_state.last_provider_sequence_end_or_none
        subscription_id = prior_state.provider_subscription_id_or_none
        retained = prior_state.retained_provider_event_content
        last_ordinal = prior_state.last_completed_event_ordinal
        source_ref = prior_state.source_receipt_ref
        rights_ref = prior_state.rights_receipt_ref
        depth = prior_state.state_vector.depth_class
    state_vector = _pit_state_vector(
        transport=PITTransportStateV1.CONNECTED_HEALTHY,
        anchor=PITAnchorStateV1.REANCHOR_REQUIRED,
        continuity=continuity,
        integrity=integrity,
        depth=depth,
        lifecycle_state=lifecycle_state,
    )
    return PITOrderBookStateV2(
        state_id=f"PIT-STATE-UNAVAILABLE::{candidate.event_record_id}",
        profile_id=candidate.profile_id,
        market_id=candidate.market_id,
        instrument_id=candidate.instrument_id,
        capture_session_id=candidate.capture_session_id,
        connection_epoch=candidate.connection_epoch,
        wire_dialect=candidate.wire_dialect,
        levels=levels,
        last_provider_sequence_start_or_none=last_start,
        last_provider_sequence_end_or_none=last_end,
        provider_subscription_id_or_none=subscription_id,
        retained_provider_event_content=retained,
        last_completed_event_ordinal=last_ordinal,
        state_vector=state_vector,
        source_receipt_ref=source_ref,
        rights_receipt_ref=rights_ref,
    )


def _pit_transition_failure(
    prior_state: PITOrderBookStateV2 | None,
    candidate: PITCanonicalEventCandidateV2,
    *,
    disposition: PITEventDispositionV1,
    continuity: PITContinuityStateV3,
    integrity: PITIntegrityStateV1,
    reason: PITReasonCodeV1,
    candidate_content_json: str,
    lifecycle_state: str,
) -> PITBookTransitionResultV2:
    return PITBookTransitionResultV2(
        transition_id=f"PIT-TRANSITION::{candidate.event_record_id}",
        event_record_ref=candidate.event_record_id,
        pre_state_ref_or_none=(prior_state.state_id if prior_state else None),
        post_state=_pit_unavailable_state(
            prior_state,
            candidate,
            continuity=continuity,
            integrity=integrity,
            lifecycle_state=lifecycle_state,
        ),
        event_disposition=disposition,
        continuity_result=continuity,
        integrity_result=integrity,
        failure_reason_or_none=reason,
        recovery_required=True,
        provider_identity=_pit_provider_identity(candidate),
        candidate_content_json=candidate_content_json,
    )


def _pit_assert_prior_identity(
    prior_state: PITOrderBookStateV2,
    candidate: PITCanonicalEventCandidateV2,
) -> None:
    if (
        prior_state.profile_id is not candidate.profile_id
        or prior_state.market_id != candidate.market_id
        or prior_state.instrument_id != candidate.instrument_id
        or prior_state.capture_session_id != candidate.capture_session_id
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "candidate and prior state partition identities differ",
        )


def _pit_apply_absolute_updates(
    prior_levels: tuple[PITBookStateLevelV2, ...],
    payload: _PITBookAbsoluteUpdatePayloadV2,
) -> tuple[PITBookStateLevelV2, ...]:
    by_key = {
        (value.canonical_side, value.price): value for value in prior_levels
    }
    for update in payload.updates:
        key = (update.canonical_side, update.price)
        if update.absolute_quantity == 0:
            by_key.pop(key, None)
            continue
        by_key[key] = PITBookStateLevelV2(
            source_side=update.source_side,
            canonical_side=update.canonical_side,
            price_text=update.price_text,
            price=update.price,
            quantity_text=update.absolute_quantity_text,
            quantity=update.absolute_quantity,
            price_scale=update.price_scale,
            quantity_scale=update.quantity_scale,
            price_increment=update.price_increment,
            price_origin=update.price_origin,
            quantity_increment=update.quantity_increment_or_none,
        )
    return tuple(sorted(by_key.values(), key=_pit_state_level_sort_key))


def _pit_apply_signed_deltas(
    prior_levels: tuple[PITBookStateLevelV2, ...],
    payload: _PITBookDeltaPayloadV2,
) -> tuple[PITBookStateLevelV2, ...]:
    by_key = {
        (value.canonical_side, value.price): value for value in prior_levels
    }
    for delta in payload.deltas:
        key = (delta.canonical_side, delta.price)
        previous = by_key.get(key)
        previous_quantity = previous.quantity if previous is not None else Decimal(0)
        if (
            previous is not None
            and previous.quantity_increment is not None
            and delta.quantity_increment_or_none is not None
            and previous.quantity_increment != delta.quantity_increment_or_none
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
                "signed delta quantity increment differs from anchored state",
            )
        resulting = previous_quantity + delta.quantity_delta
        if resulting < 0:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
                "signed delta produces a negative state quantity",
            )
        if resulting == 0:
            by_key.pop(key, None)
            continue
        quantity_text = str(resulting)
        quantity_scale = max(
            delta.quantity_scale,
            previous.quantity_scale if previous is not None else 0,
        )
        if resulting.as_tuple().exponent < 0:
            quantity_scale = -resulting.as_tuple().exponent
        else:
            quantity_scale = 0
        by_key[key] = PITBookStateLevelV2(
            source_side=delta.source_side,
            canonical_side=delta.canonical_side,
            price_text=delta.price_text,
            price=delta.price,
            quantity_text=quantity_text,
            quantity=resulting,
            price_scale=delta.price_scale,
            quantity_scale=quantity_scale,
            price_increment=delta.price_increment,
            price_origin=delta.price_origin,
            quantity_increment=(
                delta.quantity_increment_or_none
                if delta.quantity_increment_or_none is not None
                else (
                    previous.quantity_increment if previous is not None else None
                )
            ),
        )
    return tuple(sorted(by_key.values(), key=_pit_state_level_sort_key))


def apply_pit_event_v2(
    prior_state: PITOrderBookStateV2 | None,
    candidate: PITCanonicalEventCandidateV2,
    *,
    candidate_event_ordinal: int,
    lifecycle_state: str = "ADMISSIBLE",
    transport_state: PITTransportStateV1 = PITTransportStateV1.CONNECTED_HEALTHY,
) -> PITBookTransitionResultV2:
    """Apply one exact selected-profile event without mutating its prior state."""

    if prior_state is not None and type(prior_state) is not PITOrderBookStateV2:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "prior_state must be exact PITOrderBookStateV2 or absent",
        )
    if type(candidate) is not PITCanonicalEventCandidateV2:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "candidate must be exact PITCanonicalEventCandidateV2",
        )
    if type(candidate_event_ordinal) is not int or candidate_event_ordinal < 1:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
            "candidate ordinal must be an exact positive integer",
        )
    _pit_book_text(lifecycle_state, "lifecycle_state")
    if type(transport_state) is not PITTransportStateV1:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "transport state has the wrong exact type",
        )
    expected_ordinal = (
        1 if prior_state is None else prior_state.last_completed_event_ordinal + 1
    )
    if candidate_event_ordinal != expected_ordinal:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
            "candidate ordinal is not the exact next completed ordinal",
        )
    if prior_state is not None:
        _pit_assert_prior_identity(prior_state, candidate)
    transition_policy = policy.PIT_BOOK_TRANSITION_POLICIES_V2.get(
        candidate.profile_id
    )
    if transition_policy is None:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "no transition policy exists outside selected profiles",
        )
    provider_identity = _pit_provider_identity(candidate)
    candidate_content_json = deterministic_json(candidate.payload)
    retained_by_id = (
        dict(prior_state.retained_provider_event_content)
        if prior_state is not None
        else {}
    )
    if provider_identity in retained_by_id:
        if retained_by_id[provider_identity] == candidate_content_json:
            return PITBookTransitionResultV2(
                transition_id=f"PIT-TRANSITION::{candidate.event_record_id}",
                event_record_ref=candidate.event_record_id,
                pre_state_ref_or_none=prior_state.state_id,
                post_state=prior_state,
                event_disposition=PITEventDispositionV1.DUPLICATE_IGNORED,
                continuity_result=prior_state.state_vector.continuity_state,
                integrity_result=prior_state.state_vector.integrity_state,
                failure_reason_or_none=None,
                recovery_required=False,
                provider_identity=provider_identity,
                candidate_content_json=candidate_content_json,
            )
        return _pit_transition_failure(
            prior_state,
            candidate,
            disposition=PITEventDispositionV1.QUARANTINED,
            continuity=PITContinuityStateV3.RECOVERY_IN_PROGRESS,
            integrity=PITIntegrityStateV1.CORRUPT,
            reason=PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
            candidate_content_json=candidate_content_json,
            lifecycle_state=lifecycle_state,
        )

    if candidate.event_kind not in {
        PITEventKindV2.BOOK_SNAPSHOT,
        PITEventKindV2.BOOK_DELTA,
        PITEventKindV2.BOOK_REPLACEMENT,
    }:
        return _pit_apply_scalar_event(
            prior_state,
            candidate,
            candidate_event_ordinal=candidate_event_ordinal,
            provider_identity=provider_identity,
            candidate_content_json=candidate_content_json,
            transport_state=transport_state,
            lifecycle_state=lifecycle_state,
        )

    new_levels: tuple[PITBookStateLevelV2, ...]
    sequence_start = candidate.provider_sequence_start_or_none
    sequence_end = candidate.provider_sequence_end_or_none
    subscription_id = candidate.provider_subscription_id_or_none
    is_anchor = candidate.event_kind is PITEventKindV2.BOOK_SNAPSHOT
    is_current_replacement = (
        candidate.event_kind is PITEventKindV2.BOOK_REPLACEMENT
    )
    if prior_state is None and not (is_anchor or is_current_replacement):
        return _pit_transition_failure(
            prior_state,
            candidate,
            disposition=PITEventDispositionV1.REJECTED,
            continuity=PITContinuityStateV3.RECOVERY_IN_PROGRESS,
            integrity=PITIntegrityStateV1.UNVALIDATED,
            reason=PITReasonCodeV1.PIT_ANCHOR_REQUIRED,
            candidate_content_json=candidate_content_json,
            lifecycle_state=lifecycle_state,
        )

    if (
        is_anchor
        and prior_state is not None
        and prior_state.connection_epoch == candidate.connection_epoch
        and candidate.profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT
        and prior_state.state_vector.anchor_state
        is not PITAnchorStateV1.ANCHOR_REQUIRED
    ):
        return _pit_transition_failure(
            prior_state,
            candidate,
            disposition=PITEventDispositionV1.REJECTED,
            continuity=PITContinuityStateV3.RECOVERY_IN_PROGRESS,
            integrity=PITIntegrityStateV1.UNVALIDATED,
            reason=PITReasonCodeV1.PIT_ANCHOR_REQUIRED,
            candidate_content_json=candidate_content_json,
            lifecycle_state=lifecycle_state,
        )
    if (
        is_anchor
        and prior_state is not None
        and prior_state.connection_epoch == candidate.connection_epoch
        and candidate.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT
        and (
            prior_state.state_vector.anchor_state
            is PITAnchorStateV1.ANCHOR_ACCEPTED
            or (
                prior_state.state_vector.anchor_state
                is PITAnchorStateV1.REANCHOR_REQUIRED
                and candidate.provider_subscription_id_or_none
                != prior_state.provider_subscription_id_or_none
            )
        )
    ):
        return _pit_transition_failure(
            prior_state,
            candidate,
            disposition=PITEventDispositionV1.REJECTED,
            continuity=PITContinuityStateV3.RECOVERY_IN_PROGRESS,
            integrity=PITIntegrityStateV1.UNVALIDATED,
            reason=PITReasonCodeV1.PIT_ANCHOR_REQUIRED,
            candidate_content_json=candidate_content_json,
            lifecycle_state=lifecycle_state,
        )

    if is_anchor:
        if type(candidate.payload) is not _PITBookSnapshotPayloadV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "anchor candidate requires exact snapshot payload",
            )
        new_levels = tuple(
            sorted(
                (_pit_public_level(value) for value in candidate.payload.levels),
                key=_pit_state_level_sort_key,
            )
        )
        continuity = PITContinuityStateV3.CONTIGUOUS
    elif is_current_replacement:
        if (
            candidate.profile_id
            is not Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT
            or type(candidate.payload) is not _PITBookReplacementPayloadV2
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "current-state replacement is admitted only for Retail payload",
            )
        new_levels = tuple(
            sorted(
                (_pit_public_level(value) for value in candidate.payload.levels),
                key=_pit_state_level_sort_key,
            )
        )
        if (
            prior_state is not None
            and prior_state.connection_epoch == candidate.connection_epoch
            and prior_state.state_vector.anchor_state
            is PITAnchorStateV1.REANCHOR_REQUIRED
        ):
            return _pit_transition_failure(
                prior_state,
                candidate,
                disposition=PITEventDispositionV1.REJECTED,
                continuity=PITContinuityStateV3.RECOVERY_IN_PROGRESS,
                integrity=PITIntegrityStateV1.UNVALIDATED,
                reason=PITReasonCodeV1.PIT_ANCHOR_REQUIRED,
                candidate_content_json=candidate_content_json,
                lifecycle_state=lifecycle_state,
            )
        if (
            prior_state is not None
            and prior_state.connection_epoch == candidate.connection_epoch
            and prior_state.state_vector.depth_class
            is not candidate.depth_class
            and {
                prior_state.state_vector.depth_class,
                candidate.depth_class,
            }
            == {
                PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT,
                PITDepthClassV2.PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME,
            }
            and not _pit_polymarket_parity_matches(
                prior_state,
                new_levels,
                candidate.depth_class,
            )
        ):
            return _pit_transition_failure(
                prior_state,
                candidate,
                disposition=PITEventDispositionV1.REJECTED,
                continuity=PITContinuityStateV3.SEQUENCE_UNAVAILABLE,
                integrity=PITIntegrityStateV1.CURRENT_STATE_PARITY_FAILED,
                reason=PITReasonCodeV1.PIT_CURRENT_STATE_PARITY_FAILED,
                candidate_content_json=candidate_content_json,
                lifecycle_state=lifecycle_state,
            )
        sequence_start = None
        sequence_end = None
        subscription_id = None
        continuity = PITContinuityStateV3.SEQUENCE_UNAVAILABLE
    else:
        if prior_state is None:
            raise AssertionError("prior state checked above")
        if (
            prior_state.state_vector.anchor_state
            is not PITAnchorStateV1.ANCHOR_ACCEPTED
            or prior_state.state_vector.continuity_state
            is not PITContinuityStateV3.CONTIGUOUS
            or prior_state.state_vector.integrity_state
            is not PITIntegrityStateV1.VALID
        ):
            return _pit_transition_failure(
                prior_state,
                candidate,
                disposition=PITEventDispositionV1.REJECTED,
                continuity=PITContinuityStateV3.RECOVERY_IN_PROGRESS,
                integrity=PITIntegrityStateV1.UNVALIDATED,
                reason=PITReasonCodeV1.PIT_ANCHOR_REQUIRED,
                candidate_content_json=candidate_content_json,
                lifecycle_state=lifecycle_state,
            )
        if prior_state.connection_epoch != candidate.connection_epoch:
            return _pit_transition_failure(
                prior_state,
                candidate,
                disposition=PITEventDispositionV1.REJECTED,
                continuity=PITContinuityStateV3.RECOVERY_IN_PROGRESS,
                integrity=PITIntegrityStateV1.UNVALIDATED,
                reason=PITReasonCodeV1.PIT_ANCHOR_REQUIRED,
                candidate_content_json=candidate_content_json,
                lifecycle_state=lifecycle_state,
            )
        last_sequence = prior_state.last_provider_sequence_end_or_none
        if transition_policy.provider_sequence_required:
            if last_sequence is None or sequence_start is None or sequence_end is None:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE,
                    "sequenced transition lacks an exact prior/current sequence",
                )
            if sequence_end <= last_sequence:
                return _pit_transition_failure(
                    prior_state,
                    candidate,
                    disposition=PITEventDispositionV1.QUARANTINED,
                    continuity=PITContinuityStateV3.RECOVERY_IN_PROGRESS,
                    integrity=PITIntegrityStateV1.CORRUPT,
                    reason=PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                    candidate_content_json=candidate_content_json,
                    lifecycle_state=lifecycle_state,
                )
            expected = last_sequence + 1
            if candidate.profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT:
                applies = sequence_start <= expected <= sequence_end
            else:
                applies = sequence_start == expected == sequence_end
                if subscription_id != prior_state.provider_subscription_id_or_none:
                    applies = False
            if not applies:
                return _pit_transition_failure(
                    prior_state,
                    candidate,
                    disposition=PITEventDispositionV1.REJECTED,
                    continuity=PITContinuityStateV3.GAP_DETECTED,
                    integrity=PITIntegrityStateV1.VALID,
                    reason=PITReasonCodeV1.PIT_SEQUENCE_GAP,
                    candidate_content_json=candidate_content_json,
                    lifecycle_state=lifecycle_state,
                )
        if candidate.profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT:
            if type(candidate.payload) is not _PITBookAbsoluteUpdatePayloadV2:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    "Gemini delta requires absolute level-update payload",
                )
            new_levels = _pit_apply_absolute_updates(
                prior_state.levels, candidate.payload
            )
        elif candidate.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT:
            if type(candidate.payload) is not _PITBookDeltaPayloadV2:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    "Kalshi delta requires signed level-delta payload",
                )
            new_levels = _pit_apply_signed_deltas(
                prior_state.levels, candidate.payload
            )
        else:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "Retail accepts replacements, not synthesized deltas",
            )
        continuity = PITContinuityStateV3.CONTIGUOUS

    _pit_validate_state_book(candidate.profile_id, new_levels)
    retained = tuple(
        (*retained_by_id.items(), (provider_identity, candidate_content_json))
    )
    state_vector = _pit_state_vector(
        transport=transport_state,
        anchor=PITAnchorStateV1.ANCHOR_ACCEPTED,
        continuity=continuity,
        integrity=PITIntegrityStateV1.VALID,
        depth=candidate.depth_class,
        lifecycle_state=lifecycle_state,
    )
    post_state = PITOrderBookStateV2(
        state_id=f"PIT-STATE::{candidate.event_record_id}::{candidate_event_ordinal}",
        profile_id=candidate.profile_id,
        market_id=candidate.market_id,
        instrument_id=candidate.instrument_id,
        capture_session_id=candidate.capture_session_id,
        connection_epoch=candidate.connection_epoch,
        wire_dialect=candidate.wire_dialect,
        levels=new_levels,
        last_provider_sequence_start_or_none=sequence_start,
        last_provider_sequence_end_or_none=sequence_end,
        provider_subscription_id_or_none=subscription_id,
        retained_provider_event_content=retained,
        last_completed_event_ordinal=candidate_event_ordinal,
        state_vector=state_vector,
        source_receipt_ref=candidate.source_receipt_ref,
        rights_receipt_ref=candidate.rights_receipt_ref,
    )
    return PITBookTransitionResultV2(
        transition_id=f"PIT-TRANSITION::{candidate.event_record_id}",
        event_record_ref=candidate.event_record_id,
        pre_state_ref_or_none=(prior_state.state_id if prior_state else None),
        post_state=post_state,
        event_disposition=PITEventDispositionV1.COMMITTED,
        continuity_result=continuity,
        integrity_result=PITIntegrityStateV1.VALID,
        failure_reason_or_none=None,
        recovery_required=False,
        provider_identity=provider_identity,
        candidate_content_json=candidate_content_json,
    )


def build_event_state_snapshots(
    input_locks: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for sequence, lock in enumerate(input_locks, start=1):
        scope_value = _scope_value(lock)
        scope_ref = _scope_ref_from_value(scope_value)
        states = _event_states(scope_value)
        records.append(
            {
                **policy.common_record_fields("EVENT_STATE_SNAPSHOT_RECORD", scope_value),
                **policy.scope_field(scope_ref),
                "snapshot_id": event_state_snapshot_id(scope_value),
                "snapshot_input_lock_ref": str(lock["input_lock_id"]),
                "snapshot_class": "SYNTHETIC_FIXTURE_EVENT_STATE_SNAPSHOT",
                "qtt_internal_snapshot_class": "QTT_INTERNAL_EVENT_LIFECYCLE_METADATA_SNAPSHOT",
                "deterministic_sequence_id": f"PR133_EVENT_STATE_SEQUENCE_{sequence:04d}",
                "synthetic_event_state_refs": [
                    str(state["synthetic_event_state_id"]) for state in states
                ],
                "synthetic_event_state_id": f"PR133_{scope_value}_EVENT_STATE_AGGREGATE_V1",
                "event_states": states,
                "canonical_event_state_rank": 0,
                "canonical_sort_key": f"PR133_{scope_value}_EVENT_STATE_AGGREGATE_SORT_KEY",
                "qtt_internal_event_status_class": "QTT_INTERNAL_STATUS_METADATA_MIXED",
                "qtt_internal_lifecycle_state_class": "UNKNOWN_SOURCE_REQUIRED",
                "qtt_internal_settlement_state_class": "QTT_INTERNAL_SETTLEMENT_METADATA_ONLY",
                "official_venue_field_value_source_state": str(
                    lock["source_dependency_state"]
                ),
                "fixture_event_state_snapshot_created": True,
                "event_state_snapshot_is_trading_signal": False,
                "event_state_snapshot_is_feature_vector": False,
                "event_state_snapshot_is_quantum_feature_vector": False,
                "event_state_snapshot_is_atomicrows_row": False,
                "event_state_snapshot_is_order_authority": False,
                "event_state_snapshot_is_runtime_resolver_snapshot": False,
                "no_live_fetch": True,
                "no_network_io": True,
                "no_order_authority": True,
                "no_profit_evidence": True,
                "no_quantum_execution": True,
            }
        )
    return records


def build_snapshot_builder_bindings(
    input_locks: list[Mapping[str, object]],
    orderbook_snapshots: list[Mapping[str, object]],
    event_state_snapshots: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    inputs_by_scope = {_scope_value(record): str(record["input_lock_id"]) for record in input_locks}
    orderbook_by_scope = {
        _scope_value(record): str(record["snapshot_id"]) for record in orderbook_snapshots
    }
    event_by_scope = {
        _scope_value(record): str(record["snapshot_id"]) for record in event_state_snapshots
    }
    records: list[dict[str, object]] = []
    for scope_ref in policy.stage1_scope_refs():
        scope_value = scope_ref.value
        records.append(
            {
                **policy.common_record_fields(
                    "ORDERBOOK_EVENT_STATE_SNAPSHOT_BUILDER_BINDING",
                    scope_value,
                ),
                **policy.scope_field(scope_ref),
                "binding_id": binding_id(scope_value),
                "builder_name": f"PR133_{scope_value}_FIXTURE_SNAPSHOT_BUILDER",
                "builder_version": "v1",
                "builder_scope": "FIXTURE_BACKED_CONTRACT_ONLY",
                "input_lock_refs": [inputs_by_scope[scope_value]],
                "orderbook_snapshot_refs": [orderbook_by_scope[scope_value]],
                "event_state_snapshot_refs": [event_by_scope[scope_value]],
                "market_data_ingest_handoff_ref": "PR132_MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF_V1",
                "credential_readiness_handoff_ref": "PR131_CREDENTIAL_READINESS_DOWNSTREAM_HANDOFF_V1",
                "source_dependency_refs": [
                    f"PR132_{scope_value}_ORDERBOOK_INPUT_METADATA_ENVELOPE_FOR_PR115_ONLY_SOURCE_DEPENDENCY_V1"
                ],
                "connector_semantic_dependency_refs": [
                    f"PR124_CONNECTOR_SEMANTIC_BINDING_REF_METADATA_ONLY_{scope_value}"
                ],
                "orderbook_canonical_sort_rules_ref": "PR133_ORDERBOOK_CANONICAL_SORT_RULES_POLICY",
                "event_state_canonical_sort_rules_ref": "PR133_EVENT_STATE_CANONICAL_SORT_RULES_POLICY",
                "allowed_use": "FIXTURE_BACKED_ORDERBOOK_EVENT_STATE_SNAPSHOT_CONTRACT_ONLY",
                "disallowed_use": list(policy.DISALLOWED_USE),
                "future_live_use_requires_owner_approval": True,
                "future_live_use_requires_accepted_source_packet": True,
                "future_live_use_requires_fresh_revalidation_state": True,
                "future_live_use_requires_connector_semantic_binding": True,
                "future_live_use_requires_credential_provider_receipt_if_credentials_needed": True,
                "future_runtime_resolver_use_requires_pr134_authorization": True,
                "future_historical_dataset_use_requires_pr135_authorization": True,
                "future_atomicrows_bridge_requires_post_pr135_owner_authorization": True,
                "future_atomicrows_bundle_sha_requires_explicit_owner_authorization": True,
                "future_quantum_use_requires_pr116_pr117_data_chain": True,
                "future_quantum_use_requires_replay_paper_validation": True,
                "future_quantum_use_requires_owner_approval": True,
            }
        )
    return records
