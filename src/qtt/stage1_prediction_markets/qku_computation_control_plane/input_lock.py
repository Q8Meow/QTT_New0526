"""Immutable ST12-F parent input lock built only from canonical owner snapshots."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from decimal import Decimal
import math
import re
from types import MappingProxyType
from typing import Mapping

from .context import parse_utc
from .errors import ContractValidationError, ReasonCode
from .parameter_policy import (
    ST12FParameterRegistryV1,
    initialize_st12f_parameter_registry_v1,
)
from .serialization import deterministic_json


INPUT_LOCK_SCHEMA_VERSION_V1 = "QTT_ST12F_IMMUTABLE_REPLAY_PAPER_INPUT_LOCK_V1_4"
INPUT_LOCK_CONTRACT_VERSION_V1 = "1.4"
ST12F_TEMPLATE_IDS_V1 = tuple(f"MATH-{number:02d}" for number in range(1, 53))
ST12F_REPLAY_RESULT_CONTRACT_IDS_V1 = tuple(
    f"ST12F-REPLAY-CONTRACT::{template_id}" for template_id in ST12F_TEMPLATE_IDS_V1
)
ST12F_PAPER_RESULT_CONTRACT_IDS_V1 = tuple(
    f"ST12F-PAPER-CONTRACT::{template_id}" for template_id in ST12F_TEMPLATE_IDS_V1
)
ST12F_PARAMETER_VALUE_REF_COUNT_V1 = 3096
_IDENTITY_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def _text(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{name} must be bounded canonical text",
        )
    return value


def _identity_tuple(value: object, name: str, *, count: int | None = None) -> tuple[str, ...]:
    if (
        not isinstance(value, tuple)
        or any(not isinstance(item, str) or not item or item != item.strip() for item in value)
        or len(value) != len(set(value))
        or (count is not None and len(value) != count)
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{name} must be an ordered unique identity tuple",
        )
    return value


def _freeze_json(value: object, name: str) -> object:
    if value is None or type(value) in {bool, int, str} or isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractValidationError(
                ReasonCode.NONFINITE_NUMERIC_INPUT,
                f"{name} contains a nonfinite float",
            )
        return value
    if isinstance(value, tuple | list):
        return tuple(_freeze_json(item, name) for item in value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) or not key for key in value):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                f"{name} contains a non-text mapping key",
            )
        return MappingProxyType(
            {
                key: _freeze_json(item, f"{name}.{key}")
                for key, item in sorted(value.items())
            }
        )
    raise ContractValidationError(
        ReasonCode.CONTRACT_OR_TYPE_INVALID,
        f"{name} contains unsupported {type(value).__name__}",
    )


def _mapping(value: object, name: str, *, nonempty: bool = True) -> Mapping[str, object]:
    frozen = _freeze_json(value, name)
    if not isinstance(frozen, Mapping) or (nonempty and not frozen):
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT,
            f"{name} must be a nonempty immutable mapping",
        )
    return frozen


def validated_st12f_identity_token_v1(value: object) -> str:
    text = _text(value, "identity token")
    if _IDENTITY_TOKEN.fullmatch(text) is None:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "identity token is outside the bounded canonical grammar",
        )
    return text


def canonical_st12f_parameter_value_refs_v1(
    registry: ST12FParameterRegistryV1 | None = None,
) -> tuple[str, ...]:
    ready = initialize_st12f_parameter_registry_v1() if registry is None else registry
    if type(ready) is not ST12FParameterRegistryV1:
        raise ContractValidationError(
            ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
            "parameter registry must be the exact READY registry",
        )
    refs = tuple(row.parameter_id for row in ready.parameter_policies)
    _identity_tuple(refs, "parameter_value_refs", count=ST12F_PARAMETER_VALUE_REF_COUNT_V1)
    return refs


@dataclass(frozen=True, slots=True)
class CanonicalReplayPaperInputSnapshotV1:
    """Injected canonical-owner state; never accepted from an OP13 request body."""

    decision_time: datetime
    point_in_time_cutoff: datetime
    market_scope: tuple[str, ...]
    venue_scope: tuple[str, ...]
    instrument_scope: tuple[str, ...]
    formula_specification_versions: Mapping[str, object]
    implementation_versions: Mapping[str, object]
    parameter_policy_version: str
    parameter_value_refs: tuple[str, ...]
    source_epochs: Mapping[str, object]
    data_semantics_version: str
    venue_semantics_version: str
    accounting_definition: Mapping[str, object]
    fee_assumptions: Mapping[str, object]
    spread_assumptions: Mapping[str, object]
    slippage_assumptions: Mapping[str, object]
    fill_and_queue_assumptions: Mapping[str, object]
    latency_and_staleness_assumptions: Mapping[str, object]
    capacity_and_crowding_assumptions: Mapping[str, object]
    portfolio_and_cash_context: Mapping[str, object]
    random_seed_policy: Mapping[str, object]
    resampling_policy: Mapping[str, object]
    scenario_set_id: str
    causation_id: str
    correlation_id: str
    created_by: str
    created_at: datetime

    def __post_init__(self) -> None:
        decision = parse_utc(self.decision_time, field_name="decision_time")
        cutoff = parse_utc(self.point_in_time_cutoff, field_name="point_in_time_cutoff")
        created = parse_utc(self.created_at, field_name="created_at")
        if cutoff > decision or created < decision:
            raise ContractValidationError(
                ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID,
                "input snapshot times violate point-in-time custody",
            )
        object.__setattr__(self, "decision_time", decision)
        object.__setattr__(self, "point_in_time_cutoff", cutoff)
        object.__setattr__(self, "created_at", created)
        for name in ("market_scope", "venue_scope", "instrument_scope"):
            _identity_tuple(getattr(self, name), name)
            if not getattr(self, name):
                raise ContractValidationError(
                    ReasonCode.INPUT_SCOPE_MISMATCH,
                    f"{name} cannot be empty",
                )
        for name in (
            "formula_specification_versions",
            "implementation_versions",
            "source_epochs",
            "accounting_definition",
            "fee_assumptions",
            "spread_assumptions",
            "slippage_assumptions",
            "fill_and_queue_assumptions",
            "latency_and_staleness_assumptions",
            "capacity_and_crowding_assumptions",
            "portfolio_and_cash_context",
            "random_seed_policy",
            "resampling_policy",
        ):
            object.__setattr__(self, name, _mapping(getattr(self, name), name))
        if set(self.formula_specification_versions) != set(ST12F_TEMPLATE_IDS_V1):
            raise ContractValidationError(
                ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,
                "formula version pins must cover the exact 52-template roster",
            )
        if set(self.implementation_versions) != set(ST12F_TEMPLATE_IDS_V1):
            raise ContractValidationError(
                ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,
                "implementation version pins must cover the exact 52-template roster",
            )
        _identity_tuple(
            self.parameter_value_refs,
            "parameter_value_refs",
            count=ST12F_PARAMETER_VALUE_REF_COUNT_V1,
        )
        if any(not value.startswith("ST10-PARAM::") for value in self.parameter_value_refs):
            raise ContractValidationError(
                ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                "parameter references must remain canonical identities only",
            )
        for name in (
            "parameter_policy_version",
            "data_semantics_version",
            "venue_semantics_version",
            "scenario_set_id",
            "causation_id",
            "correlation_id",
            "created_by",
        ):
            _text(getattr(self, name), name)
        if self.causation_id == self.correlation_id:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "causation and correlation identities must remain distinct",
            )
        if not isinstance(self.resampling_policy.get("trial_family_id"), str):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "resampling_policy must contain trial_family_id",
            )
        if not isinstance(
            self.portfolio_and_cash_context.get("permanent_no_trade_baseline_ref"),
            str,
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "portfolio context must contain the permanent NO_TRADE baseline",
            )


@dataclass(frozen=True, slots=True)
class ImmutableReplayPaperInputLockV1:
    input_lock_id: str
    schema_version: str
    contract_version: str
    decision_time: datetime
    point_in_time_cutoff: datetime
    market_scope: tuple[str, ...]
    venue_scope: tuple[str, ...]
    instrument_scope: tuple[str, ...]
    cohort_template_ids: tuple[str, ...]
    expected_replay_result_contract_ids: tuple[str, ...]
    expected_paper_result_contract_ids: tuple[str, ...]
    formula_specification_versions: Mapping[str, object]
    implementation_versions: Mapping[str, object]
    parameter_policy_version: str
    parameter_value_refs: tuple[str, ...]
    source_epochs: Mapping[str, object]
    data_semantics_version: str
    venue_semantics_version: str
    accounting_definition: Mapping[str, object]
    fee_assumptions: Mapping[str, object]
    spread_assumptions: Mapping[str, object]
    slippage_assumptions: Mapping[str, object]
    fill_and_queue_assumptions: Mapping[str, object]
    latency_and_staleness_assumptions: Mapping[str, object]
    capacity_and_crowding_assumptions: Mapping[str, object]
    portfolio_and_cash_context: Mapping[str, object]
    random_seed_policy: Mapping[str, object]
    resampling_policy: Mapping[str, object]
    scenario_set_id: str
    causation_id: str
    correlation_id: str
    created_by: str
    created_at: datetime

    def __post_init__(self) -> None:
        if len(fields(self)) != 33:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "immutable input lock must contain exactly 33 top-level fields",
            )
        if self.schema_version != INPUT_LOCK_SCHEMA_VERSION_V1 or self.contract_version != INPUT_LOCK_CONTRACT_VERSION_V1:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "immutable input lock schema or contract version differs",
            )
        token = self.input_lock_id.removeprefix("ST12F-LOCK::")
        if self.input_lock_id != f"ST12F-LOCK::{validated_st12f_identity_token_v1(token)}":
            raise ContractValidationError(
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                "input_lock_id is not the deterministic natural identity",
            )
        snapshot = CanonicalReplayPaperInputSnapshotV1(
            **{
                name: getattr(self, name)
                for name in (
                    "decision_time",
                    "point_in_time_cutoff",
                    "market_scope",
                    "venue_scope",
                    "instrument_scope",
                    "formula_specification_versions",
                    "implementation_versions",
                    "parameter_policy_version",
                    "parameter_value_refs",
                    "source_epochs",
                    "data_semantics_version",
                    "venue_semantics_version",
                    "accounting_definition",
                    "fee_assumptions",
                    "spread_assumptions",
                    "slippage_assumptions",
                    "fill_and_queue_assumptions",
                    "latency_and_staleness_assumptions",
                    "capacity_and_crowding_assumptions",
                    "portfolio_and_cash_context",
                    "random_seed_policy",
                    "resampling_policy",
                    "scenario_set_id",
                    "causation_id",
                    "correlation_id",
                    "created_by",
                    "created_at",
                )
            }
        )
        for name in (
            "decision_time",
            "point_in_time_cutoff",
            "formula_specification_versions",
            "implementation_versions",
            "source_epochs",
            "accounting_definition",
            "fee_assumptions",
            "spread_assumptions",
            "slippage_assumptions",
            "fill_and_queue_assumptions",
            "latency_and_staleness_assumptions",
            "capacity_and_crowding_assumptions",
            "portfolio_and_cash_context",
            "random_seed_policy",
            "resampling_policy",
            "created_at",
        ):
            object.__setattr__(self, name, getattr(snapshot, name))
        if self.cohort_template_ids != ST12F_TEMPLATE_IDS_V1:
            raise ContractValidationError(
                ReasonCode.ST12F_TEMPLATE_ROSTER_MISMATCH,
                "input lock template roster must be the exact ordered 52 identities",
            )
        if (
            self.expected_replay_result_contract_ids != ST12F_REPLAY_RESULT_CONTRACT_IDS_V1
            or self.expected_paper_result_contract_ids != ST12F_PAPER_RESULT_CONTRACT_IDS_V1
            or set(self.expected_replay_result_contract_ids)
            & set(self.expected_paper_result_contract_ids)
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN,
                "REPLAY and PAPER must define disjoint exact 52-slot rosters",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "ImmutableReplayPaperInputLockV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "input-lock payload field roster differs",
            )
        return cls(**dict(value))

    def canonical_json(self) -> str:
        return deterministic_json(self)


def build_immutable_replay_paper_input_lock_v1(
    *,
    identity_token: str,
    asserted_input_lock_id: str,
    canonical_snapshot: CanonicalReplayPaperInputSnapshotV1,
) -> ImmutableReplayPaperInputLockV1:
    token = validated_st12f_identity_token_v1(identity_token)
    expected_lock_id = f"ST12F-LOCK::{token}"
    if asserted_input_lock_id != expected_lock_id:
        raise ContractValidationError(
            ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
            "caller lock text is only an equality assertion",
        )
    if type(canonical_snapshot) is not CanonicalReplayPaperInputSnapshotV1:
        raise ContractValidationError(
            ReasonCode.INPUT_OWNER_MISMATCH,
            "input lock content must come from the exact canonical snapshot owner",
        )
    values = {
        field.name: getattr(canonical_snapshot, field.name)
        for field in fields(canonical_snapshot)
    }
    return ImmutableReplayPaperInputLockV1(
        input_lock_id=expected_lock_id,
        schema_version=INPUT_LOCK_SCHEMA_VERSION_V1,
        contract_version=INPUT_LOCK_CONTRACT_VERSION_V1,
        cohort_template_ids=ST12F_TEMPLATE_IDS_V1,
        expected_replay_result_contract_ids=ST12F_REPLAY_RESULT_CONTRACT_IDS_V1,
        expected_paper_result_contract_ids=ST12F_PAPER_RESULT_CONTRACT_IDS_V1,
        **values,
    )


if (
    len(ST12F_TEMPLATE_IDS_V1) != 52
    or len(ST12F_REPLAY_RESULT_CONTRACT_IDS_V1) != 52
    or len(ST12F_PAPER_RESULT_CONTRACT_IDS_V1) != 52
    or len(set((*ST12F_REPLAY_RESULT_CONTRACT_IDS_V1, *ST12F_PAPER_RESULT_CONTRACT_IDS_V1))) != 104
    or len(fields(ImmutableReplayPaperInputLockV1)) != 33
):
    raise ContractValidationError(
        ReasonCode.SCHEMA_MISMATCH,
        "ST12-F immutable lock denominators are not exact",
    )
