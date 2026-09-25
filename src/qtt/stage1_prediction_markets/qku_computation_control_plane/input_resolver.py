"""Strict formula-input and runtime-parameter owner-packet resolution."""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
import math
import os
import threading
import time
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .bindings import (
    CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
    FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
    FormulaInputAdmissionClassV1,
    FormulaInputAuthorityBindingV1,
    ST12DMath39RawInputBindingV1,
)
from .context import (
    exact_decimal,
    finite_float,
)
from .errors import (
    FreshnessError,
    InputAuthorityError,
    NumericDomainError,
    PointInTimeError,
    ReasonCode,
)
from .freshness import (
    FreshnessPolicyV1,
    FreshnessReceiptV1,
    FreshnessResolverV1,
)
from .point_in_time import (
    PITDataContractErrorV1,
    PITDepthClassV2,
    PITInputAvailabilityV2,
    PITReasonCodeV1,
    PointInTimeClocksV1,
    PointInTimeFieldClassV1,
    PointInTimePolicyV1,
    PointInTimeReceiptV1,
    classify_point_in_time_semantics,
)
from .stage1_launch_graph import Stage1VenueProfileIdV1
from .models import (
    ComputationExecutionContextV1,
    ComputationScopeV1,
    ImplementationVersionPinV1,
    NO_EFFECTS_V1,
    OwnerActionConfirmationReceiptV1,
    ReadOnlyKillSubmitStateV1,
    ST12FEvidenceReferenceV1,
    ST12FEvidenceStateV1,
)
from .specification import FROZEN_FORMULA_REQUIREMENTS


_PROBABILITY_ACCEPTANCE_PARENTS_V1 = MappingProxyType({
    "SOURCE_RIGHTS": (), "ENVIRONMENT": (),
    "MODEL_BUILD": ("SOURCE_RIGHTS", "ENVIRONMENT"),
    "MODEL_REVIEW": ("MODEL_BUILD",),
    "USE_POLICY": ("SOURCE_RIGHTS", "ENVIRONMENT", "MODEL_REVIEW"),
    "CATALOG": ("SOURCE_RIGHTS",),
    "COMPUTATION": ("ENVIRONMENT", "MODEL_BUILD", "USE_POLICY", "CATALOG"),
})


def _probability_receipt_subjects_v1(role, scope, catalog_ref, result_ref):
    from .models import _probability_require_v1 as need
    subjects = {
        "SOURCE_RIGHTS": (scope.input_lock_ref, scope.reference_cohort_ref, catalog_ref),
        "ENVIRONMENT": (scope.environment_ref,),
        "MODEL_BUILD": (scope.model_artifact_ref, scope.cell_manifest_ref),
        "MODEL_REVIEW": (scope.model_artifact_ref,),
        "USE_POLICY": (scope.policy_ref, scope.family_ref), "CATALOG": (catalog_ref,),
    }
    if role in subjects:
        return subjects[role]
    need(role == "COMPUTATION" and result_ref is not None, "PROBABILITY_RECEIPT_ROLE")
    return (result_ref,)


def _probability_selected_record_v1(snapshot, ref, scope, kind):
    from .models import _probability_require_v1 as need
    from .persistence import ProbabilityProducerReadSnapshotV1
    from .receipts import _validate_probability_control_spine_v1
    need(type(snapshot) is ProbabilityProducerReadSnapshotV1 and snapshot.scope == scope,
         "PROBABILITY_COMMITTED_SNAPSHOT")
    record = snapshot.records_by_ref.get(ref)
    need(record is not None, "PROBABILITY_REQUIRED_RECORD_MISSING")
    _validate_probability_control_spine_v1(record)
    need(record.record_id == ref and record.typed_payload.scope == scope and
         record.typed_payload.control_kind == kind, "PROBABILITY_SELECTED_RECORD")
    return record


def _probability_current_record_v1(record, snapshot, evaluated_ns):
    from .models import _probability_require_v1 as need
    payload = record.typed_payload
    need(payload.available_ns <= snapshot.read_completed_ns <= evaluated_ns,
         "PROBABILITY_RECORD_NOT_OBSERVED")
    if payload.valid_until_ns is not None:
        need(evaluated_ns < payload.valid_until_ns, "PROBABILITY_RECORD_EXPIRED")


def _probability_record_issuer_request_v1(record):
    from .protocols import ProbabilityIssuerReadRequestV1
    from .models import _probability_require_v1 as need
    p, b = record.typed_payload, record.typed_payload.body
    if p.control_kind == "ACCEPTANCE_RECEIPT":
        role, subjects, issuer = b["role"], b["subject_refs"], b["issuer_ref"]
    elif p.control_kind == "PREDICTION_RESULT":
        role, subjects, issuer = "COMPUTATION", (record.record_id,), b["producer_ref"]
    else:
        need(p.control_kind == "PREDICTION_REVIEW", "PROBABILITY_ISSUER_RECORD_KIND")
        role, subjects, issuer = "MODEL_REVIEW", (p.scope.model_artifact_ref, b["result_ref"]), b["reviewer_ref"]
    return ProbabilityIssuerReadRequestV1(role, p.scope, subjects, issuer)


def _probability_join_issuer_v1(record, *, issuer_requests, issuer_snapshot, issuer_admissions, evaluated_ns):
    """Pure full-request join; the caller owns and authenticates the issued view."""
    from .models import _probability_require_v1 as need
    from .protocols import ProbabilityIssuerAdmissionV1, ProbabilityIssuerSnapshotV1
    request = _probability_record_issuer_request_v1(record)
    need(type(issuer_requests) is tuple and type(issuer_admissions) is tuple and
         type(issuer_snapshot) is ProbabilityIssuerSnapshotV1 and
         len(issuer_requests) == len(issuer_admissions) == len(issuer_snapshot.entries),
         "PROBABILITY_ISSUER_JOIN_ROSTER")
    indexes = tuple(i for i, candidate in enumerate(issuer_requests) if candidate == request)
    need(len(indexes) == 1, "PROBABILITY_FULL_ISSUER_REQUEST_REQUIRED")
    index = indexes[0]
    context, grant, _ = issuer_snapshot.entries[index]
    admission = issuer_admissions[index]
    need(type(admission) is ProbabilityIssuerAdmissionV1 and
         (admission.role, admission.issuer_ref) == (request.role, request.issuer_ref) and
         grant.role == request.role and grant.scope == request.scope and grant.subject_refs == request.subject_refs and
         context.principal_ref == grant.principal_ref == request.issuer_ref and
         evaluated_ns < admission.valid_until_ns <= min(context.valid_until_ns, grant.valid_until_ns,
                                                       issuer_snapshot.valid_until_ns),
         "PROBABILITY_ISSUER_ORIGIN_JOIN")
    required = record.typed_payload.body.get("issuer_admission_refs", ())
    need(set(required) <= set(admission.authority_dependency_refs), "PROBABILITY_ORIGINAL_ISSUER_CLOSURE")
    return admission, context


def _join_probability_acceptance_v1(
    scope, binding_ref, *, committed_snapshot, issuer_requests, issuer_snapshot,
    issuer_admissions, evaluated_ns: int, require_result: bool,
):
    """Join the bounded original ancestry without issuing or renewing acceptance."""
    from .models import _probability_require_v1 as need, _probability_ns_v1
    from .serialization import _bounded_probability_json_v1
    need(type(require_result) is bool, "PROBABILITY_RESULT_REQUIREMENT")
    _probability_ns_v1(evaluated_ns)
    snapshot = committed_snapshot
    binding = _probability_selected_record_v1(snapshot, binding_ref, scope, "INPUT_BINDING")
    root = binding.typed_payload
    descriptors = root.body["objects"]
    expected_roles = ("MODEL", "CATALOG", "RESULT", "POLICY") if require_result else ("MODEL", "CATALOG", "POLICY")
    need(tuple(row["role"] for row in descriptors) == expected_roles, "PROBABILITY_BINDING_RESULT_LAYOUT")
    objects = {row["role"]: row["object_ref"] for row in descriptors}
    manifest = _probability_selected_record_v1(snapshot, root.body["acceptance_manifest_ref"], scope, "ACCEPTANCE_MANIFEST")
    mp = manifest.typed_payload
    need(mp.body["binding_ref"] == binding_ref and
         (mp.effective_ns, mp.recorded_ns, mp.available_ns) == (root.effective_ns, root.recorded_ns, root.available_ns),
         "PROBABILITY_MANIFEST_BINDING")
    roles = tuple(_PROBABILITY_ACCEPTANCE_PARENTS_V1)[:7 if require_result else 6]
    receipt_refs = mp.body["receipt_refs"]
    need(len(receipt_refs) == len(roles) and len(set((binding_ref, manifest.record_id, *receipt_refs))) == len(roles) + 2,
         "PROBABILITY_MANIFEST_ALIASES")
    selected = dict(zip(roles, receipt_refs, strict=True))
    records, domains, dependencies, expiries = [binding, manifest], {}, [], [issuer_snapshot.valid_until_ns]
    origins = []
    for role, ref in zip(roles, receipt_refs, strict=True):
        record = _probability_selected_record_v1(snapshot, ref, scope, "ACCEPTANCE_RECEIPT")
        p, body = record.typed_payload, record.typed_payload.body
        need(body["role"] == role and "prediction_basis_kind" not in body["claims"], "PROBABILITY_LEGACY_ROLE")
        need(body["subject_refs"] == _probability_receipt_subjects_v1(role, scope, objects["CATALOG"], objects.get("RESULT")),
             "PROBABILITY_RECEIPT_SUBJECT")
        parents = tuple(selected[parent] for parent in _PROBABILITY_ACCEPTANCE_PARENTS_V1[role])
        need(body["depends_on"] == parents and set(parents) <= set(p.dependency_refs), "PROBABILITY_ACCEPTANCE_DAG")
        need(all(snapshot.records_by_ref[parent].typed_payload.available_ns <= body["observed_ns"] for parent in parents),
             "PROBABILITY_PARENT_NOT_OBSERVED")
        need(body["observed_ns"] <= p.recorded_ns <= p.available_ns <= root.available_ns <=
             snapshot.read_completed_ns <= evaluated_ns < p.valid_until_ns, "PROBABILITY_ACCEPTANCE_NOT_CURRENT")
        if role == "COMPUTATION":
            need(body["binding_ref"] == binding_ref, "PROBABILITY_COMPUTATION_BINDING")
        else:
            origins.append(body["binding_ref"])
        admission, context = _probability_join_issuer_v1(
            record, issuer_requests=issuer_requests, issuer_snapshot=issuer_snapshot,
            issuer_admissions=issuer_admissions, evaluated_ns=evaluated_ns,
        )
        domains[role] = context.control_domain_ref
        dependencies.extend(admission.authority_dependency_refs)
        expiries.extend((p.valid_until_ns, admission.valid_until_ns))
        records.append(record)
    need(domains["MODEL_REVIEW"] not in (domains["MODEL_BUILD"], domains.get("COMPUTATION")),
         "PROBABILITY_CONTROLLING_DOMAIN_SELF_REVIEW")
    need(not records[5].typed_payload.body["claims"]["blocker_codes"], "PROBABILITY_ORIGINAL_REVIEW_BLOCKED")
    need(len(set(origins)) == 1, "PROBABILITY_MIXED_ORIGIN")
    if origins[0] != binding_ref:
        need(require_result, "PROBABILITY_ORIGIN_REQUIRES_RESULT")
        origin = _probability_selected_record_v1(snapshot, origins[0], scope, "INPUT_BINDING")
        op = origin.typed_payload
        origin_manifest = _probability_selected_record_v1(snapshot, op.body["acceptance_manifest_ref"], scope, "ACCEPTANCE_MANIFEST")
        om = origin_manifest.typed_payload
        need(op.body["owner_epoch"] == root.body["owner_epoch"] and
             _bounded_probability_json_v1(op.body["objects"], max_bytes=1048576) ==
             _bounded_probability_json_v1(tuple(row for row in descriptors if row["role"] != "RESULT"), max_bytes=1048576),
             "PROBABILITY_ORIGIN_OBJECTS_CHANGED")
        need(om.body["binding_ref"] == origin.record_id and om.body["receipt_refs"] == receipt_refs[:6] and
             (om.effective_ns, om.recorded_ns, om.available_ns) == (op.effective_ns, op.recorded_ns, op.available_ns),
             "PROBABILITY_ORIGIN_MANIFEST_CHANGED")
        need(all(record.typed_payload.available_ns <= op.available_ns for record in records[2:8]) and
             op.available_ns <= root.effective_ns and
             op.available_ns <= records[8].typed_payload.body["claims"]["started_ns"], "PROBABILITY_ORIGIN_CHRONOLOGY")
        records.extend((origin, origin_manifest))
    for record in records:
        _probability_current_record_v1(record, snapshot, evaluated_ns)
        dependencies.extend((record.record_id, *record.typed_payload.dependency_refs))
        if record.typed_payload.valid_until_ns is not None:
            expiries.append(record.typed_payload.valid_until_ns)
    dependencies = tuple(dict.fromkeys(dependencies))
    invalidated = set(issuer_snapshot.invalidated_refs)
    for record in snapshot.revocation_records:
        invalidated.update(record.typed_payload.body["invalidated_dependency_refs"])
    need(not invalidated.intersection(dependencies), "PROBABILITY_ACCEPTANCE_INVALIDATED")
    return tuple(records), dependencies, min(expiries)


@dataclass(frozen=True, slots=True)
class ProbabilityOutcomeJoinV1:
    context_identity: tuple[object, ...]
    query_key: tuple[str, tuple[str, ...]]
    validity_probability: Decimal
    validity_evidence_ref: str
    fill_conditioning_evidence_ref: str
    dependency_refs: tuple[str, ...]
    available_ns: int
    valid_until_ns: int

    def __post_init__(self) -> None:
        from .models import _probability_require_v1, _probability_text_v1, _probability_refs_v1, _probability_ns_v1
        from .serialization import _probability_binary64_v1
        need = _probability_require_v1
        need(type(self.context_identity) is tuple and bool(self.context_identity), "PROBABILITY_OUTCOME_CONTEXT")
        need(type(self.query_key) is tuple and len(self.query_key) == 2 and type(self.query_key[1]) is tuple,
             "PROBABILITY_OUTCOME_QUERY")
        _probability_text_v1(self.query_key[0])
        for feature in self.query_key[1]:
            _probability_binary64_v1(feature)
        need(type(self.validity_probability) is Decimal and self.validity_probability.is_finite()
             and 0 <= self.validity_probability <= 1, "PROBABILITY_VALIDITY")
        _probability_text_v1(self.validity_evidence_ref)
        _probability_text_v1(self.fill_conditioning_evidence_ref)
        _probability_refs_v1(self.dependency_refs, nonempty=True)
        need({self.validity_evidence_ref, self.fill_conditioning_evidence_ref}.issubset(self.dependency_refs),
             "PROBABILITY_OUTCOME_DEPENDENCIES")
        _probability_ns_v1(self.available_ns); _probability_ns_v1(self.valid_until_ns)
        need(self.available_ns < self.valid_until_ns, "PROBABILITY_OUTCOME_LIFETIME")


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType(
            {str(key): _freeze(item) for key, item in value.items()}
        )
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    return value


def thaw_input(value: object) -> object:
    """Return a private mutable call value without changing authoritative state."""

    if isinstance(value, Mapping):
        return {str(key): thaw_input(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_input(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class OwnerValuePacketV1:
    packet_id: str
    owner_id: str
    packet_type: str
    schema_id: str
    schema_version: str
    context_id: str
    scope: ComputationScopeV1
    source_epoch_id: str
    input_version: str
    clocks: PointInTimeClocksV1
    ttl: timedelta
    values: Mapping[str, object]
    authorized_binding_ids: tuple[str, ...]
    producer_receipt_id: str
    producer_receipt_type: str
    source_state_and_claim_lineage: str
    provider_sequence: int | str | None = None
    revision: int | str | None = None
    prior_revision_available_time: object | None = None
    source_conflict: bool = False

    def __post_init__(self) -> None:
        required = (
            self.packet_id,
            self.owner_id,
            self.packet_type,
            self.schema_id,
            self.schema_version,
            self.context_id,
            self.source_epoch_id,
            self.input_version,
            self.producer_receipt_id,
            self.producer_receipt_type,
            self.source_state_and_claim_lineage,
        )
        if any(not isinstance(value, str) or not value for value in required):
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "owner packet identity and lineage fields are required",
            )
        if type(self.scope) is not ComputationScopeV1:
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "owner packet requires an exact ComputationScopeV1",
            )
        if self.input_version != self.input_version.strip():
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "owner packet input_version must be canonical text",
            )
        if not isinstance(self.clocks, PointInTimeClocksV1):
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "owner packet requires typed six-clock point-in-time state",
            )
        if not isinstance(self.ttl, timedelta) or self.ttl <= timedelta(0):
            raise InputAuthorityError(
                ReasonCode.FRESHNESS_VIOLATION,
                "owner packet TTL must be positive",
            )
        if (
            not isinstance(self.values, Mapping)
            or not self.values
            or not isinstance(self.authorized_binding_ids, tuple)
            or not self.authorized_binding_ids
            or len(self.authorized_binding_ids)
            != len(set(self.authorized_binding_ids))
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "owner packet needs values and exact unique binding identities",
            )
        if type(self.source_conflict) is not bool:
            raise InputAuthorityError(
                ReasonCode.SOURCE_CONFLICT,
                "source conflict state must be an exact boolean",
            )
        object.__setattr__(self, "values", _freeze(dict(self.values)))


@dataclass(frozen=True, slots=True)
class ResolvedFormulaInputV1:
    binding_id: str
    math_spec_id: str
    input_name: str
    value: object
    owner_id: str
    packet_id: str
    field_path: str
    point_in_time_receipt: PointInTimeReceiptV1
    freshness_receipt: FreshnessReceiptV1
    producer_receipt_id: str


@dataclass(frozen=True, slots=True)
class FormulaInputResolutionV1:
    math_spec_id: str
    execution_context: ComputationExecutionContextV1
    inputs: tuple[ResolvedFormulaInputV1, ...]
    authoritative_values: Mapping[str, object]
    packet_refs: tuple[str, ...]
    receipt_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not self.math_spec_id
            or not isinstance(
                self.execution_context, ComputationExecutionContextV1
            )
            or not self.inputs
            or len({row.input_name for row in self.inputs}) != len(self.inputs)
            or tuple(self.authoritative_values)
            != tuple(row.input_name for row in self.inputs)
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                "resolved formula inputs are incomplete or out of declared order",
            )

    @property
    def context_id(self) -> str:
        return self.execution_context.context_id


class Math39BookEventKindV1(StrEnum):
    DISPLAYED_BEFORE_ORDER = "DISPLAYED_BEFORE_ORDER"
    PRIOR_ADDITION = "PRIOR_ADDITION"
    PRIOR_CANCELLATION = "PRIOR_CANCELLATION"
    TRADE_AHEAD = "TRADE_AHEAD"


def _math39_utc(value: object, name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
        or value.utcoffset().total_seconds() != 0
    ):
        raise InputAuthorityError(
            ReasonCode.POINT_IN_TIME_VIOLATION,
            f"MATH-39 {name} must be an aware UTC timestamp",
        )
    return value


def _math39_decimal(value: object, name: str, *, nonnegative: bool) -> Decimal:
    if (
        not isinstance(value, Decimal)
        or isinstance(value, bool)
        or not value.is_finite()
        or nonnegative
        and value < 0
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_VALUE_CONFLICT,
            f"MATH-39 {name} must be an exact finite"
            + (" nonnegative" if nonnegative else "")
            + " Decimal",
        )
    return value


@dataclass(frozen=True, slots=True)
class Math39OrderAcknowledgementV1:
    order_id: str
    venue_id: str
    instrument_id: str
    side: str
    price: Decimal
    acknowledged_at: datetime
    available_at: datetime
    matching_priority: str
    venue_evidence_ref: str
    unit: str
    basis: str
    producer_receipt_ref: str

    def __post_init__(self) -> None:
        for name in (
            "order_id",
            "venue_id",
            "instrument_id",
            "side",
            "matching_priority",
            "venue_evidence_ref",
            "unit",
            "basis",
            "producer_receipt_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or value != value.strip():
                raise InputAuthorityError(
                    ReasonCode.INPUT_PACKET_MISMATCH,
                    f"MATH-39 acknowledgement {name} must be canonical text",
                )
        _math39_decimal(self.price, "acknowledgement price", nonnegative=True)
        acknowledged = _math39_utc(self.acknowledged_at, "acknowledged_at")
        available = _math39_utc(self.available_at, "ack available_at")
        if acknowledged > available:
            raise InputAuthorityError(
                ReasonCode.POINT_IN_TIME_VIOLATION,
                "MATH-39 acknowledgement cannot be available before its event time",
            )
        if self.matching_priority != "PRICE_TIME_FIFO":
            raise InputAuthorityError(
                ReasonCode.MATCHING_PRIORITY_UNKNOWN,
                "MATH-39 acknowledgement lacks exact matching-priority evidence",
            )
        if self.unit != "units" or self.basis != "ACKNOWLEDGED_INSERTION_POINT":
            raise InputAuthorityError(
                ReasonCode.UNIT_BASIS_OR_PRECISION_INVALID,
                "MATH-39 acknowledgement lacks exact unit/basis evidence",
            )


@dataclass(frozen=True, slots=True)
class Math39SequencedBookEventV1:
    event_id: str
    sequence: int
    event_kind: Math39BookEventKindV1
    venue_id: str
    instrument_id: str
    side: str
    price: Decimal
    quantity: Decimal
    event_time: datetime
    available_at: datetime
    priority_order_id: str
    venue_evidence_ref: str
    unit: str
    basis: str
    producer_receipt_ref: str
    ahead_of_order: bool = True

    def __post_init__(self) -> None:
        for name in (
            "event_id",
            "venue_id",
            "instrument_id",
            "side",
            "priority_order_id",
            "venue_evidence_ref",
            "unit",
            "basis",
            "producer_receipt_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or value != value.strip():
                raise InputAuthorityError(
                    ReasonCode.INPUT_PACKET_MISMATCH,
                    f"MATH-39 book event {name} must be canonical text",
                )
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int):
            raise InputAuthorityError(
                ReasonCode.SEQUENCE_GAP,
                "MATH-39 sequence must be an exact integer",
            )
        if type(self.event_kind) is not Math39BookEventKindV1:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "MATH-39 event kind must be the exact finite enum",
            )
        _math39_decimal(self.price, "event price", nonnegative=True)
        _math39_decimal(self.quantity, "event quantity", nonnegative=True)
        event_time = _math39_utc(self.event_time, "event_time")
        available = _math39_utc(self.available_at, "event available_at")
        if event_time > available:
            raise InputAuthorityError(
                ReasonCode.POINT_IN_TIME_VIOLATION,
                "MATH-39 event cannot be available before occurrence",
            )
        if (
            self.unit != "units"
            or self.basis != "ACKNOWLEDGED_INSERTION_POINT"
            or self.ahead_of_order is not True
        ):
            raise InputAuthorityError(
                ReasonCode.UNIT_BASIS_OR_PRECISION_INVALID,
                "MATH-39 events require exact ahead-of-order unit/basis custody",
            )


@dataclass(frozen=True, slots=True)
class ResolvedRuntimeParameterValueV1:
    binding_id: str
    parameter_id: str
    parameter_symbol: str
    value: object
    unit_or_basis: str
    owner_id: str
    packet_id: str
    field_path: str
    point_in_time_receipt: PointInTimeReceiptV1
    freshness_receipt: FreshnessReceiptV1
    producer_receipt_id: str

    def __post_init__(self) -> None:
        if (
            self.binding_id != f"RPVOB::{self.parameter_id}"
            or not self.parameter_symbol
            or not self.unit_or_basis
            or not self.owner_id
            or not self.packet_id
            or not self.field_path
            or not self.producer_receipt_id
        ):
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                "resolved runtime parameter identity or lineage is incomplete",
            )


@dataclass(frozen=True, slots=True)
class RuntimeParameterValueResolutionV1:
    parameter_id: str
    execution_context: ComputationExecutionContextV1
    resolved: ResolvedRuntimeParameterValueV1
    receipt_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not self.parameter_id
            or not isinstance(
                self.execution_context, ComputationExecutionContextV1
            )
            or self.resolved.parameter_id != self.parameter_id
            or self.receipt_refs
            != (
                self.resolved.producer_receipt_id,
                self.resolved.point_in_time_receipt.receipt_id,
                self.resolved.freshness_receipt.receipt_id,
            )
        ):
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                "runtime parameter resolution receipt is inconsistent",
            )

    @property
    def context_id(self) -> str:
        return self.execution_context.context_id


class CanonicalOwnerPacketRegistryV1:
    """Immutable local view of canonical owners; requests cannot add/select owners."""

    def __init__(self, packets: tuple[OwnerValuePacketV1, ...] = (), *, _probability_guard_bindings: tuple = ()) -> None:
        if (
            not isinstance(packets, tuple)
            or any(not isinstance(packet, OwnerValuePacketV1) for packet in packets)
            or len({packet.packet_id for packet in packets}) != len(packets)
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "owner packet registry requires unique typed immutable packets",
            )
        by_binding: dict[tuple[object, ...], list[OwnerValuePacketV1]] = {}
        by_context_binding: dict[
            tuple[str, str], list[OwnerValuePacketV1]
        ] = {}
        for packet in packets:
            for binding_id in packet.authorized_binding_ids:
                by_binding.setdefault(
                    self._packet_binding_key(packet, binding_id), []
                ).append(packet)
                by_context_binding.setdefault(
                    (packet.context_id, binding_id), []
                ).append(packet)
        if any(len(rows) != 1 for rows in by_binding.values()):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                "canonical registry has conflicting packets for one exact scope/version binding",
            )
        self._packets = packets
        self._by_id = MappingProxyType(
            {packet.packet_id: packet for packet in packets}
        )
        self._by_binding = MappingProxyType(
            {key: rows[0] for key, rows in by_binding.items()}
        )
        self._by_context_binding = MappingProxyType(
            {key: tuple(rows) for key, rows in by_context_binding.items()}
        )
        if type(_probability_guard_bindings) is not tuple:
            raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH, "probability guard bindings must be an owned tuple")
        guards = {}
        for row in _probability_guard_bindings:
            if type(row) is not tuple or len(row) != 3:
                raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH, "probability guard binding shape")
            packet, admission, resolver = row
            if (type(packet) is not OwnerValuePacketV1 or self._by_id.get(packet.packet_id) is not packet or
                    packet.packet_id in guards or not packet.packet_id.startswith("V35::")):
                raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH, "probability guard packet membership")
            fence = getattr(resolver, "_probability_source_fence_v1", None)
            entry = None if fence is None else fence._registrations.get(id(admission))
            if (entry is None or entry["object"] is not admission or fence.issuer_resolver is not resolver or
                    not any(packet is original for original in entry["metadata"].get("packets", ()))):
                raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH, "probability packet was not originally issued")
            guards[packet.packet_id] = row
        if any(packet.packet_id.startswith("V35::") and packet.packet_id not in guards for packet in packets):
            raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH, "reserved probability packet lacks its original guard")
        self._probability_guard_bindings = _probability_guard_bindings
        self._probability_guards_by_id_v1 = MappingProxyType(guards)

    @staticmethod
    def _packet_binding_key(
        packet: OwnerValuePacketV1,
        binding_id: str,
    ) -> tuple[object, ...]:
        return (
            packet.context_id,
            packet.clocks.as_of_time,
            packet.source_epoch_id,
            packet.input_version,
            packet.scope.identity_tuple,
            binding_id,
        )

    @staticmethod
    def _context_binding_key(
        context: ComputationExecutionContextV1,
        binding_id: str,
    ) -> tuple[object, ...]:
        return (
            context.context_id,
            context.as_of,
            context.source_epoch_id,
            context.input_version,
            context.scope.identity_tuple,
            binding_id,
        )

    @property
    def packets(self) -> tuple[OwnerValuePacketV1, ...]:
        return self._packets

    def packet_for(
        self,
        *,
        context: ComputationExecutionContextV1,
        binding_id: str,
    ) -> OwnerValuePacketV1:
        if not isinstance(context, ComputationExecutionContextV1):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "packet lookup requires ComputationExecutionContextV1",
            )
        try:
            packet = self._by_binding[
                self._context_binding_key(context, binding_id)
            ]
        except KeyError as exc:
            candidates = self._by_context_binding.get(
                (context.context_id, binding_id), ()
            )
            if any(
                packet.scope == context.scope
                and packet.input_version == context.input_version
                and packet.source_epoch_id == context.source_epoch_id
                for packet in candidates
            ):
                raise PointInTimeError(
                    ReasonCode.POINT_IN_TIME_VIOLATION,
                    f"{binding_id} packet as_of differs from the execution context",
                ) from exc
            if any(
                packet.scope == context.scope
                and packet.input_version == context.input_version
                and packet.clocks.as_of_time == context.as_of
                for packet in candidates
            ):
                raise FreshnessError(
                    ReasonCode.SOURCE_EPOCH_STALE,
                    f"{binding_id} packet source epoch differs from the execution context",
                ) from exc
            if candidates:
                raise InputAuthorityError(
                    ReasonCode.INPUT_SCOPE_MISMATCH,
                    f"{binding_id} packet scope or input version differs",
                ) from exc
            raise InputAuthorityError(
                ReasonCode.INPUT_OWNER_MISSING,
                f"canonical owner packet is absent for {binding_id}",
            ) from exc
        self._check_probability_packet_refs_v1((packet.packet_id,), context=context)
        return packet

    def _check_probability_packet_refs_v1(self, packet_refs: tuple[str, ...], *, context: ComputationExecutionContextV1) -> None:
        from .latency_policy import utc_event_time_ns
        from .errors import ComputationControlPlaneError
        if type(context) is not ComputationExecutionContextV1:
            raise InputAuthorityError(ReasonCode.INPUT_SCOPE_MISMATCH, "probability consumption needs the full execution context")
        if type(packet_refs) is not tuple or any(type(ref) is not str or not ref for ref in packet_refs):
            raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH, "consumed packet references are malformed")
        for ref in dict.fromkeys(packet_refs):
            packet = self._by_id.get(ref)
            if packet is None:
                raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH, "consumed packet is absent from this registry")
            guard = self._probability_guards_by_id_v1.get(ref)
            if guard is None:
                if ref.startswith("V35::"):
                    raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH, "reserved probability packet is unguarded")
                continue
            original, admission, resolver = guard
            if original is not packet:
                raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH, "consumed probability packet was substituted")
            request = admission.request
            if request.execution_context.execution_identity_tuple != context.execution_identity_tuple:
                raise InputAuthorityError(ReasonCode.INPUT_SCOPE_MISMATCH, "probability packet execution context changed")
            if (request.query_key not in request.prepared_prediction.request_keys or
                    len(packet.authorized_binding_ids) != 1 or packet.authorized_binding_ids[0] not in request.binding_ids):
                raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH, "probability packet query or binding changed")
            now = utc_event_time_ns()
            if type(now) is not int:
                raise FreshnessError(ReasonCode.FRESHNESS_VIOLATION, "probability UTC clock is not an exact integer")
            try:
                result = resolver._check_probability_native_use_v1(admission, evaluated_ns=now)
            except ComputationControlPlaneError as error:
                if error.reason_code in (ReasonCode.OWNER_DATA_STALE, ReasonCode.FRESHNESS_VIOLATION) or now >= admission.valid_until_ns:
                    raise FreshnessError(ReasonCode.FRESHNESS_VIOLATION, "probability input expired or clock regressed") from error
                raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH, "probability input authority is no longer current") from error
            if result is not None:
                raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH, "probability currentness check did not succeed")

    def packet_by_id(self, packet_id: str) -> OwnerValuePacketV1:
        try:
            return self._by_id[packet_id]
        except KeyError as exc:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                f"owner packet identity is absent: {packet_id}",
            ) from exc

    def with_internal_computation_receipt(
        self, packet: OwnerValuePacketV1
    ) -> CanonicalOwnerPacketRegistryV1:
        if (
            packet.owner_id != "QKUComputationControlPlaneV1.MATH-01"
            or packet.packet_type != "ComputationExecutionReceiptV1::MATH-01"
            or packet.schema_id
            != "ComputationExecutionReceiptV1::MATH-01::SCHEMA"
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_OWNER_MISMATCH,
                "only the exact registered MATH-01 dependency receipt may be added",
            )
        return CanonicalOwnerPacketRegistryV1((*self._packets, packet),
                                             _probability_guard_bindings=self._probability_guard_bindings)


def _extract(values: Mapping[str, object], field_path: str) -> object:
    if field_path in values:
        return values[field_path]
    current: object = values
    for token in field_path.split("."):
        if not isinstance(current, Mapping) or token not in current:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                f"owner packet lacks exact field path {field_path}",
            )
        current = current[token]
    return current


def _parse_typed(value: object, binding: FormulaInputAuthorityBindingV1) -> object:
    token = binding.input_type.casefold()
    try:
        if token == "decimal string" or "decimal string" in token and not (
            "list" in token or "vector" in token
        ):
            return exact_decimal(value, field_name=binding.input_name)  # type: ignore[arg-type]
        if token in {"float64", "float"}:
            return finite_float(value, field_name=binding.input_name)  # type: ignore[arg-type]
    except NumericDomainError as exc:
        raise InputAuthorityError(
            ReasonCode.INPUT_VALUE_CONFLICT,
            f"{binding.input_name} failed canonical numeric extraction",
        ) from exc
    if token in {"int", "integer"}:
        if isinstance(value, bool) or not isinstance(value, int):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be an exact integer",
            )
        return value
    if token in {"bool", "boolean"}:
        if type(value) is not bool:
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be an exact boolean",
            )
        return value
    if token in {"enum", "str", "string"}:
        if not isinstance(value, str) or not value:
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be nonempty exact text",
            )
        return value
    if token in {"decimal string list", "list[decimal string]"}:
        if not isinstance(value, list | tuple):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be a Decimal-string list",
            )
        try:
            return tuple(
                exact_decimal(item, field_name=binding.input_name)  # type: ignore[arg-type]
                for item in value
            )
        except NumericDomainError as exc:
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} contains a noncanonical Decimal",
            ) from exc
    if token == "list[float64]":
        if not isinstance(value, list | tuple):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be a float64 list",
            )
        try:
            return tuple(
                finite_float(item, field_name=binding.input_name)  # type: ignore[arg-type]
                for item in value
            )
        except NumericDomainError as exc:
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} contains a nonfinite float64",
            ) from exc
    if token == "list[list[float64]]":
        if not isinstance(value, list | tuple) or any(
            not isinstance(row, list | tuple) for row in value
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be a nested float64 list",
            )
        try:
            return tuple(
                tuple(
                    finite_float(item, field_name=binding.input_name)  # type: ignore[arg-type]
                    for item in row
                )
                for row in value
            )
        except NumericDomainError as exc:
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} contains a nonfinite float64",
            ) from exc
    if token == "list[int]":
        if (
            not isinstance(value, list | tuple)
            or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be an exact integer list",
            )
        return tuple(value)
    if token in {"list[str]", "ordered unique string list"}:
        if (
            not isinstance(value, list | tuple)
            or any(not isinstance(item, str) or not item for item in value)
            or (
                token == "ordered unique string list"
                and len(set(value)) != len(value)
            )
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be a valid ordered text list",
            )
        return tuple(value)
    if token == "list[record]":
        if (
            not isinstance(value, list | tuple)
            or any(not isinstance(item, Mapping) for item in value)
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be a record list",
            )
        return tuple(_freeze(dict(item)) for item in value)
    if token in {
        "mapping",
        "qtt_cqm_grammar_v1 record",
        "qtt_dqm_grammar_v1 record",
    }:
        if not isinstance(value, Mapping):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be a typed mapping",
            )
        return _freeze(dict(value))
    if token == "ordered list[nonnegative or inf]":
        if not isinstance(value, list | tuple):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be an ordered threshold list",
            )
        normalized: list[float | str] = []
        for item in value:
            if isinstance(item, str) and item.upper() == "INF":
                normalized.append("INF")
                continue
            try:
                number = finite_float(item, field_name=binding.input_name)  # type: ignore[arg-type]
            except NumericDomainError as exc:
                raise InputAuthorityError(
                    ReasonCode.INPUT_VALUE_CONFLICT,
                    f"{binding.input_name} contains an invalid threshold",
                ) from exc
            if number < 0:
                raise InputAuthorityError(
                    ReasonCode.INPUT_VALUE_CONFLICT,
                    f"{binding.input_name} thresholds must be nonnegative",
                )
            normalized.append(number)
        ordered_values = tuple(
            math.inf if item == "INF" else item for item in normalized
        )
        if any(
            left > right
            for left, right in zip(
                ordered_values, ordered_values[1:], strict=False
            )
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} thresholds must be ordered",
            )
        return tuple(normalized)
    return _freeze(value)


def _canonical_equal(left: object, right: object) -> bool:
    if isinstance(left, Decimal):
        try:
            return left == exact_decimal(right, field_name="caller_assertion")  # type: ignore[arg-type]
        except ValueError:
            return False
    if isinstance(left, float):
        if math.isinf(left):
            return (
                isinstance(right, float)
                and not isinstance(right, bool)
                and left == right
            )
        try:
            candidate = finite_float(right, field_name="caller_assertion")  # type: ignore[arg-type]
        except ValueError:
            return False
        return math.isclose(left, candidate, rel_tol=0.0, abs_tol=0.0)
    if isinstance(left, Mapping):
        if not isinstance(right, Mapping) or tuple(left) != tuple(right):
            return False
        return all(_canonical_equal(left[key], right[key]) for key in left)
    if isinstance(left, tuple):
        if not isinstance(right, list | tuple) or len(left) != len(right):
            return False
        return all(_canonical_equal(a, b) for a, b in zip(left, right, strict=True))
    return type(left) is type(right) and left == right


def _sequence_revision_requirements(text: str) -> tuple[bool, bool]:
    token = text.casefold()
    if "not applicable" in token:
        return False, False
    sequence = (
        "sequence required" in token
        or "provider-native sequence" in token
        or "sequence/revision required" in token
    )
    revision = (
        "revision required" in token
        or "sequence/revision required" in token
    )
    return sequence, revision


def _parse_runtime_parameter_value(
    value: object,
    *,
    parameter_id: str,
    parameter_symbol: str,
    extraction: str,
) -> object:
    if "parse as DECIMAL_STRING" in extraction:
        try:
            return exact_decimal(value, field_name=parameter_symbol)  # type: ignore[arg-type]
        except ValueError as exc:
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                f"{parameter_id} requires an exact finite Decimal string",
            ) from exc
    if "parse as INTEGER" in extraction:
        if isinstance(value, bool) or not isinstance(value, int):
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                f"{parameter_id} requires an exact integer",
            )
        return value
    if "parse as BOOLEAN" in extraction:
        if type(value) is not bool:
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                f"{parameter_id} requires an exact boolean",
            )
        return value
    if "parse as CANONICAL_ENUM_OR_RULE" in extraction:
        if not isinstance(value, str) or not value:
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                f"{parameter_id} requires a nonempty canonical token",
            )
        return value
    if "parse as TYPED_STRUCT_OR_COLLECTION" in extraction:
        if not isinstance(value, Mapping | list | tuple) or not value:
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                f"{parameter_id} requires a nonempty typed structure",
            )
        return _freeze(value)
    raise InputAuthorityError(
        ReasonCode.PARAMETER_BINDING_MISMATCH,
        f"{parameter_id} has an unsupported frozen extraction contract",
    )


def _require_execution_context(
    context: object,
) -> ComputationExecutionContextV1:
    if not isinstance(context, ComputationExecutionContextV1):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCOPE_MISMATCH,
            "value resolution requires ComputationExecutionContextV1",
        )
    return context


def _admit_formula_input_binding(
    binding: FormulaInputAuthorityBindingV1,
    packet: OwnerValuePacketV1,
) -> None:
    if (
        binding.admission_class
        is FormulaInputAdmissionClassV1.ACCEPTED_OWNER_PACKET_REQUIRED_BEFORE_CONTEXTUAL_COMPUTABILITY
    ):
        return
    if (
        binding.admission_class
        is FormulaInputAdmissionClassV1.EXACT_REGISTERED_UPSTREAM_RECEIPT_REQUIRED_BEFORE_CONTEXTUAL_COMPUTABILITY
        and packet.producer_receipt_id
        and packet.producer_receipt_type
    ):
        return
    raise InputAuthorityError(
        ReasonCode.INPUT_PACKET_MISMATCH,
        f"{binding.binding_id} lacks its exact typed admission precondition",
    )


def _validate_formula_input_context(
    context: ComputationExecutionContextV1,
) -> ComputationExecutionContextV1:
    context = _require_execution_context(context)
    FreshnessResolverV1.assert_context_current(context)
    return context


def _resolve_formula_input_binding(
    math_spec_id: str,
    *,
    binding: FormulaInputAuthorityBindingV1,
    context: ComputationExecutionContextV1,
    owner_registry: CanonicalOwnerPacketRegistryV1,
    caller_assertions: Mapping[str, object],
) -> ResolvedFormulaInputV1:
    """Apply the sole owner/schema/scope/PIT/freshness/value admission body."""

    packet = owner_registry.packet_for(
        context=context,
        binding_id=binding.binding_id,
    )
    _admit_formula_input_binding(binding, packet)
    if packet.owner_id != binding.accepted_upstream_owner_id:
        raise InputAuthorityError(
            ReasonCode.INPUT_OWNER_MISMATCH,
            f"{binding.binding_id} packet owner is not canonical",
        )
    if packet.packet_type != binding.accepted_packet_or_snapshot_type:
        raise InputAuthorityError(
            ReasonCode.INPUT_PACKET_MISMATCH,
            f"{binding.binding_id} packet type is not accepted",
        )
    if (
        packet.schema_id != binding.schema_id
        or packet.schema_version != binding.schema_version
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCHEMA_MISMATCH,
            f"{binding.binding_id} schema identity/version differs",
        )
    if (
        packet.context_id != context.context_id
        or packet.scope != context.scope
        or packet.input_version != context.input_version
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCOPE_MISMATCH,
            f"{binding.binding_id} packet execution scope differs",
        )
    if packet.producer_receipt_type != binding.producer_receipt_type:
        raise InputAuthorityError(
            ReasonCode.INPUT_PACKET_MISMATCH,
            f"{binding.binding_id} producer receipt type differs",
        )
    if packet.source_conflict:
        raise InputAuthorityError(
            ReasonCode.SOURCE_CONFLICT,
            f"{binding.binding_id} owner packet has an unresolved conflict",
        )
    if (
        packet.source_state_and_claim_lineage
        != binding.source_state_and_claim_lineage
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_PACKET_MISMATCH,
            f"{binding.binding_id} source/state/claim lineage differs",
        )
    raw_value = _extract(packet.values, binding.exact_field_path)
    value = _parse_typed(raw_value, binding)
    if binding.input_name in caller_assertions:
        assertion = _parse_typed(
            caller_assertions[binding.input_name], binding
        )
        if not _canonical_equal(value, assertion):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"caller comparison assertion differs for {binding.binding_id}",
            )
    semantics = str(
        next(
            row["point_in_time_semantics"]
            for row in FROZEN_FORMULA_REQUIREMENTS[math_spec_id].raw[
                "typed_inputs"
            ]
            if row["name"] == binding.input_name
        )
    )
    pit = PointInTimePolicyV1.validate(
        receipt_id=f"PIT::{packet.packet_id}::{binding.binding_id}",
        field_class=classify_point_in_time_semantics(semantics),
        clocks=packet.clocks,
        context=context,
        prior_revision_available_time=packet.prior_revision_available_time,
    )
    require_sequence, require_revision = _sequence_revision_requirements(
        binding.provider_native_sequence_or_revision
    )
    freshness = FreshnessResolverV1.validate(
        receipt_id=f"FRESHNESS::{packet.packet_id}::{binding.binding_id}",
        clocks=packet.clocks,
        context=context,
        packet_source_epoch_id=packet.source_epoch_id,
        policy=FreshnessPolicyV1(
            ttl=packet.ttl,
            require_provider_sequence=require_sequence,
            require_revision=require_revision,
        ),
        provider_sequence=packet.provider_sequence,
        revision=packet.revision,
    )
    return ResolvedFormulaInputV1(
        binding_id=binding.binding_id,
        math_spec_id=math_spec_id,
        input_name=binding.input_name,
        value=value,
        owner_id=packet.owner_id,
        packet_id=packet.packet_id,
        field_path=binding.exact_field_path,
        point_in_time_receipt=pit,
        freshness_receipt=freshness,
        producer_receipt_id=packet.producer_receipt_id,
    )


def _admit_runtime_parameter_binding(binding: object) -> None:
    raw = getattr(binding, "raw", None)
    exact_fields = (
        getattr(binding, "accepted_upstream_owner_id", None),
        getattr(binding, "accepted_packet_or_snapshot_type", None),
        getattr(binding, "schema_id", None),
        getattr(binding, "schema_version", None),
        getattr(binding, "producer_receipt_type", None),
        raw.get("source_state_and_claim_lineage") if isinstance(raw, Mapping) else None,
    )
    if (
        getattr(binding, "value_state", None) != "RUNTIME_BINDING_REQUIRED"
        or not isinstance(raw, Mapping)
        or raw.get("current_computation_admission")
        != "BLOCKED_PENDING_ACCEPTED_UPSTREAM_VALUE_PACKET"
        or any(
            not isinstance(value, str)
            or not value
            or value != value.strip()
            for value in exact_fields
        )
    ):
        raise InputAuthorityError(
            ReasonCode.PARAMETER_BINDING_MISMATCH,
            "runtime parameter owner admission metadata is incomplete or altered",
        )


def _resolve_math39_raw_packet(
    binding: ST12DMath39RawInputBindingV1,
    *,
    context: ComputationExecutionContextV1,
    owner_registry: CanonicalOwnerPacketRegistryV1,
) -> tuple[OwnerValuePacketV1, PointInTimeReceiptV1, FreshnessReceiptV1]:
    packet = owner_registry.packet_for(context=context, binding_id=binding.binding_id)
    if packet.owner_id != binding.accepted_upstream_owner_id:
        raise InputAuthorityError(
            ReasonCode.INPUT_OWNER_MISMATCH,
            f"{binding.binding_id} packet owner is not canonical",
        )
    if (
        packet.packet_type != binding.accepted_packet_or_snapshot_type
        or packet.schema_id != binding.schema_id
        or packet.schema_version != binding.schema_version
        or packet.producer_receipt_type != binding.producer_receipt_type
        or packet.source_state_and_claim_lineage
        != binding.source_state_and_claim_lineage
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_PACKET_MISMATCH,
            f"{binding.binding_id} packet/schema/lineage identity differs",
        )
    if packet.source_conflict:
        raise InputAuthorityError(
            ReasonCode.SOURCE_CONFLICT,
            f"{binding.binding_id} has unresolved source conflict",
        )
    pit = PointInTimePolicyV1.validate(
        receipt_id=f"PIT::{packet.packet_id}::{binding.binding_id}",
        field_class=PointInTimeFieldClassV1.OBSERVATION,
        clocks=packet.clocks,
        context=context,
        prior_revision_available_time=packet.prior_revision_available_time,
    )
    is_events = binding.input_name == "sequenced_book_events"
    freshness = FreshnessResolverV1.validate(
        receipt_id=f"FRESHNESS::{packet.packet_id}::{binding.binding_id}",
        clocks=packet.clocks,
        context=context,
        packet_source_epoch_id=packet.source_epoch_id,
        policy=FreshnessPolicyV1(
            ttl=packet.ttl,
            require_provider_sequence=is_events,
            require_revision=not is_events,
        ),
        provider_sequence=packet.provider_sequence,
        revision=packet.revision,
    )
    return packet, pit, freshness


def resolve_math39_formula_inputs(
    *,
    context: ComputationExecutionContextV1,
    owner_registry: CanonicalOwnerPacketRegistryV1,
    caller_assertions: Mapping[str, object] | None = None,
) -> FormulaInputResolutionV1:
    """Resolve two raw owner packets into the four immutable Decimal terms."""

    context = _validate_formula_input_context(context)
    bindings = CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-39"]
    if (
        len(bindings) != 2
        or any(type(row) is not ST12DMath39RawInputBindingV1 for row in bindings)
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCHEMA_MISMATCH,
            "MATH-39 requires exactly two additive raw bindings",
        )
    packet_rows = {
        binding.input_name: _resolve_math39_raw_packet(
            binding,
            context=context,
            owner_registry=owner_registry,
        )
        for binding in bindings
        if isinstance(binding, ST12DMath39RawInputBindingV1)
    }
    events_packet, events_pit, events_freshness = packet_rows[
        "sequenced_book_events"
    ]
    ack_packet, ack_pit, ack_freshness = packet_rows["order_ack"]
    events = _extract(events_packet.values, "book.sequenced_book_events")
    acknowledgement = _extract(ack_packet.values, "execution.order_ack")
    if (
        not isinstance(events, tuple)
        or not events
        or any(type(row) is not Math39SequencedBookEventV1 for row in events)
        or type(acknowledgement) is not Math39OrderAcknowledgementV1
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCHEMA_MISMATCH,
            "MATH-39 raw packets require exact immutable typed event/ack records",
        )
    ack = acknowledgement
    if (
        ack.venue_id != context.scope.venue_scope_id
        or ack.instrument_id != context.scope.instrument_or_contract_scope_id
        or ack.producer_receipt_ref != ack_packet.producer_receipt_id
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCOPE_MISMATCH,
            "MATH-39 acknowledgement identity scope differs",
        )
    if ack.acknowledged_at > context.as_of or ack.available_at > context.as_of:
        raise InputAuthorityError(
            ReasonCode.POINT_IN_TIME_VIOLATION,
            "MATH-39 acknowledgement is not available at the context as-of",
        )
    sequences = tuple(row.sequence for row in events)
    if sequences != tuple(range(sequences[0], sequences[0] + len(sequences))):
        raise InputAuthorityError(
            ReasonCode.SEQUENCE_GAP,
            "MATH-39 event stream contains a sequence gap or reorder",
        )
    if sum(
        row.event_kind is Math39BookEventKindV1.DISPLAYED_BEFORE_ORDER
        for row in events
    ) != 1:
        raise InputAuthorityError(
            ReasonCode.INPUT_VALUE_CONFLICT,
            "MATH-39 requires exactly one displayed insertion-point quantity",
        )
    for row in events:
        if (
            row.venue_id != ack.venue_id
            or row.instrument_id != ack.instrument_id
            or row.side != ack.side
            or row.price != ack.price
            or row.priority_order_id != ack.order_id
            or row.venue_evidence_ref != ack.venue_evidence_ref
            or row.producer_receipt_ref != events_packet.producer_receipt_id
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "MATH-39 event identity or venue-evidence custody differs",
            )
        if (
            row.event_time > context.as_of
            or row.available_at > context.as_of
            or row.event_kind is Math39BookEventKindV1.DISPLAYED_BEFORE_ORDER
            and row.event_time > ack.acknowledged_at
            or row.event_kind is not Math39BookEventKindV1.DISPLAYED_BEFORE_ORDER
            and row.event_time < ack.acknowledged_at
        ):
            raise InputAuthorityError(
                ReasonCode.POINT_IN_TIME_VIOLATION,
                "MATH-39 event temporal custody differs from acknowledgement",
            )
    by_kind = {
        kind: sum(
            (row.quantity for row in events if row.event_kind is kind),
            start=Decimal(0),
        )
        for kind in Math39BookEventKindV1
    }
    values = MappingProxyType(
        {
            "displayed_quantity_before_order": by_kind[
                Math39BookEventKindV1.DISPLAYED_BEFORE_ORDER
            ],
            "net_prior_additions": by_kind[Math39BookEventKindV1.PRIOR_ADDITION],
            "observed_prior_cancellations": by_kind[
                Math39BookEventKindV1.PRIOR_CANCELLATION
            ],
            "observed_trades_ahead": by_kind[Math39BookEventKindV1.TRADE_AHEAD],
        }
    )
    assertions = caller_assertions or MappingProxyType({})
    if set(assertions) - set(values):
        raise InputAuthorityError(
            ReasonCode.INPUT_VALUE_CONFLICT,
            "MATH-39 caller assertions contain undeclared derived terms",
        )
    if any(
        name in assertions and not _canonical_equal(value, assertions[name])
        for name, value in values.items()
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_VALUE_CONFLICT,
            "MATH-39 caller assertion differs from raw owner reconstruction",
        )
    resolved = tuple(
        ResolvedFormulaInputV1(
            binding_id=f"DERIVED::MATH-39::{name}",
            math_spec_id="MATH-39",
            input_name=name,
            value=value,
            owner_id="QKUComputationControlPlaneV1",
            packet_id=events_packet.packet_id,
            field_path=f"derived.{name}",
            point_in_time_receipt=events_pit,
            freshness_receipt=events_freshness,
            producer_receipt_id=events_packet.producer_receipt_id,
        )
        for name, value in values.items()
    )
    receipt_refs = tuple(
        dict.fromkeys(
            (
                events_packet.producer_receipt_id,
                events_pit.receipt_id,
                events_freshness.receipt_id,
                ack_packet.producer_receipt_id,
                ack_pit.receipt_id,
                ack_freshness.receipt_id,
                *(row.producer_receipt_ref for row in events),
                ack.producer_receipt_ref,
            )
        )
    )
    return FormulaInputResolutionV1(
        math_spec_id="MATH-39",
        execution_context=context,
        inputs=resolved,
        authoritative_values=values,
        packet_refs=(events_packet.packet_id, ack_packet.packet_id),
        receipt_refs=receipt_refs,
    )


class FormulaInputResolverV1:
    """Resolve every value from the package-named owner, never from the request."""

    @staticmethod
    def resolve(
        math_spec_id: str,
        *,
        context: ComputationExecutionContextV1,
        owner_registry: CanonicalOwnerPacketRegistryV1,
        caller_assertions: Mapping[str, object] | None = None,
    ) -> FormulaInputResolutionV1:
        if math_spec_id == "MATH-39":
            return resolve_math39_formula_inputs(
                context=context,
                owner_registry=owner_registry,
                caller_assertions=caller_assertions,
            )
        context = _validate_formula_input_context(context)
        try:
            bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_spec_id]
        except KeyError as exc:
            raise InputAuthorityError(
                ReasonCode.UNKNOWN_IMPLEMENTATION,
                f"unknown frozen formula input contract: {math_spec_id}",
            ) from exc
        assertions = caller_assertions or MappingProxyType({})
        unknown = set(assertions) - {binding.input_name for binding in bindings}
        if unknown:
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"caller assertions contain undeclared inputs: {sorted(unknown)}",
            )
        resolved: list[ResolvedFormulaInputV1] = []
        for binding in bindings:
            resolved.append(
                _resolve_formula_input_binding(
                    math_spec_id,
                    binding=binding,
                    context=context,
                    owner_registry=owner_registry,
                    caller_assertions=assertions,
                )
            )
        result = FormulaInputResolutionV1(
            math_spec_id=math_spec_id,
            execution_context=context,
            inputs=tuple(resolved),
            authoritative_values=MappingProxyType(
                {row.input_name: row.value for row in resolved}
            ),
            packet_refs=tuple(dict.fromkeys(row.packet_id for row in resolved)),
            receipt_refs=tuple(
                item
                for row in resolved
                for item in (
                    row.producer_receipt_id,
                    row.point_in_time_receipt.receipt_id,
                    row.freshness_receipt.receipt_id,
                )
            ),
        )
        owner_registry._check_probability_packet_refs_v1(result.packet_refs, context=context)
        return result


class RuntimeParameterValueResolverV1:
    """Resolve one runtime parameter only from its exact frozen owner packet."""

    @staticmethod
    def resolve(
        parameter_id: str,
        *,
        context: ComputationExecutionContextV1,
        owner_registry: CanonicalOwnerPacketRegistryV1,
        caller_assertion: object | None = None,
    ) -> RuntimeParameterValueResolutionV1:
        context = _require_execution_context(context)
        FreshnessResolverV1.assert_context_current(context)
        from .parameter_policy import (
            CUMULATIVE_PARAMETER_POLICIES,
            RUNTIME_PARAMETER_OWNER_BINDINGS,
        )

        try:
            binding = RUNTIME_PARAMETER_OWNER_BINDINGS[parameter_id]
            policy = CUMULATIVE_PARAMETER_POLICIES[parameter_id]
        except KeyError as exc:
            raise InputAuthorityError(
                ReasonCode.PARAMETER_OWNER_MISSING,
                f"no runtime owner interface exists for {parameter_id}",
            ) from exc
        _admit_runtime_parameter_binding(binding)
        packet = owner_registry.packet_for(
            context=context,
            binding_id=binding.binding_id,
        )
        if packet.owner_id != binding.accepted_upstream_owner_id:
            raise InputAuthorityError(
                ReasonCode.INPUT_OWNER_MISMATCH,
                f"{parameter_id} packet owner is not canonical",
            )
        if packet.packet_type != binding.accepted_packet_or_snapshot_type:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                f"{parameter_id} packet type is not accepted",
            )
        if (
            packet.schema_id != binding.schema_id
            or packet.schema_version != binding.schema_version
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCHEMA_MISMATCH,
                f"{parameter_id} schema identity/version differs",
            )
        if (
            packet.context_id != context.context_id
            or packet.scope != context.scope
            or packet.input_version != context.input_version
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                f"{parameter_id} packet execution scope differs",
            )
        if packet.producer_receipt_type != binding.producer_receipt_type:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                f"{parameter_id} producer receipt type differs",
            )
        if packet.source_conflict:
            raise InputAuthorityError(
                ReasonCode.SOURCE_CONFLICT,
                f"{parameter_id} owner packet has an unresolved conflict",
            )
        if (
            packet.source_state_and_claim_lineage
            != str(binding.raw["source_state_and_claim_lineage"])
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                f"{parameter_id} source/state/claim lineage differs",
            )
        value = _parse_runtime_parameter_value(
            _extract(packet.values, binding.exact_field_path),
            parameter_id=parameter_id,
            parameter_symbol=binding.parameter_symbol,
            extraction=str(binding.raw["canonical_typed_value_extraction"]),
        )
        if caller_assertion is not None:
            assertion = _parse_runtime_parameter_value(
                caller_assertion,
                parameter_id=parameter_id,
                parameter_symbol=binding.parameter_symbol,
                extraction=str(binding.raw["canonical_typed_value_extraction"]),
            )
            if not _canonical_equal(value, assertion):
                raise InputAuthorityError(
                    ReasonCode.INPUT_VALUE_CONFLICT,
                    f"caller comparison assertion differs for {parameter_id}",
                )
        pit = PointInTimePolicyV1.validate(
            receipt_id=f"PIT::{packet.packet_id}::{binding.binding_id}",
            field_class=PointInTimeFieldClassV1.OBSERVATION,
            clocks=packet.clocks,
            context=context,
            prior_revision_available_time=packet.prior_revision_available_time,
        )
        require_sequence, require_revision = _sequence_revision_requirements(
            str(binding.raw["provider_native_sequence_or_revision"])
        )
        freshness = FreshnessResolverV1.validate(
            receipt_id=f"FRESHNESS::{packet.packet_id}::{binding.binding_id}",
            clocks=packet.clocks,
            context=context,
            packet_source_epoch_id=packet.source_epoch_id,
            policy=FreshnessPolicyV1(
                ttl=packet.ttl,
                require_provider_sequence=require_sequence,
                require_revision=require_revision,
            ),
            provider_sequence=packet.provider_sequence,
            revision=packet.revision,
        )
        resolved = ResolvedRuntimeParameterValueV1(
            binding_id=binding.binding_id,
            parameter_id=parameter_id,
            parameter_symbol=binding.parameter_symbol,
            value=value,
            unit_or_basis=str(policy.crosswalk["unit_or_basis"]),
            owner_id=packet.owner_id,
            packet_id=packet.packet_id,
            field_path=binding.exact_field_path,
            point_in_time_receipt=pit,
            freshness_receipt=freshness,
            producer_receipt_id=packet.producer_receipt_id,
        )
        return RuntimeParameterValueResolutionV1(
            parameter_id=parameter_id,
            execution_context=context,
            resolved=resolved,
            receipt_refs=(
                packet.producer_receipt_id,
                pit.receipt_id,
                freshness.receipt_id,
            ),
        )


ST12D_SAFETY_BINDING_ID = "ST12D::SAFETY::KILL_SUBMIT"
ST12D_OWNER_ACTION_BINDING_ID = "ST12D::OWNER_ACTION::CONFIRMATION"


def _exact_d_owner_payload(
    *,
    registry: CanonicalOwnerPacketRegistryV1,
    context: ComputationExecutionContextV1,
    binding_id: str,
    owner_id: str,
    packet_type: str,
    schema_id: str,
    field_path: str,
    payload_type: type[object],
) -> object:
    packet = registry.packet_for(context=context, binding_id=binding_id)
    if (
        packet.owner_id != owner_id
        or packet.packet_type != packet_type
        or packet.schema_id != schema_id
        or packet.schema_version != "1.0.0"
        or packet.source_conflict
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_PACKET_MISMATCH,
            f"{binding_id} canonical owner packet identity differs",
        )
    pit = PointInTimePolicyV1.validate(
        receipt_id=f"PIT::{packet.packet_id}::{binding_id}",
        field_class=PointInTimeFieldClassV1.OBSERVATION,
        clocks=packet.clocks,
        context=context,
        prior_revision_available_time=packet.prior_revision_available_time,
    )
    FreshnessResolverV1.validate(
        receipt_id=f"FRESHNESS::{packet.packet_id}::{binding_id}",
        clocks=packet.clocks,
        context=context,
        packet_source_epoch_id=packet.source_epoch_id,
        policy=FreshnessPolicyV1(ttl=packet.ttl),
        provider_sequence=packet.provider_sequence,
        revision=packet.revision,
    )
    payload = _extract(packet.values, field_path)
    if type(payload) is not payload_type:
        raise InputAuthorityError(
            ReasonCode.INPUT_SCHEMA_MISMATCH,
            f"{binding_id} payload is not {payload_type.__name__}",
        )
    if not pit.receipt_id:
        raise InputAuthorityError(
            ReasonCode.POINT_IN_TIME_VIOLATION,
            f"{binding_id} produced no point-in-time receipt",
        )
    return payload


class CurrentSafetyStateAdapterV1:
    """Exact read-only adapter for the existing safety owner interface."""

    def __init__(self, registry: CanonicalOwnerPacketRegistryV1) -> None:
        if not isinstance(registry, CanonicalOwnerPacketRegistryV1):
            raise InputAuthorityError(
                ReasonCode.INPUT_OWNER_MISSING,
                "current safety adapter requires the canonical packet registry",
            )
        self._registry = registry

    def read_kill_submit_state(
        self, context: ComputationExecutionContextV1
    ) -> ReadOnlyKillSubmitStateV1:
        payload = _exact_d_owner_payload(
            registry=self._registry,
            context=context,
            binding_id=ST12D_SAFETY_BINDING_ID,
            owner_id="SafetyStateProjectionProtocolV1",
            packet_type="ReadOnlyKillSubmitStateV1",
            schema_id="ReadOnlyKillSubmitStateV1::SCHEMA",
            field_path="safety.kill_submit_state",
            payload_type=ReadOnlyKillSubmitStateV1,
        )
        assert isinstance(payload, ReadOnlyKillSubmitStateV1)
        if payload.scope_ref != context.context_id:
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "safety state scope differs from the exact execution context",
            )
        return payload


class CurrentPreFEvidenceAdapterV1:
    """Truthful current evidence adapter: future F states remain interface-only."""

    @staticmethod
    def read_evidence_reference(
        context: ComputationExecutionContextV1,
        *,
        causation_id: str,
        correlation_id: str,
    ) -> ST12FEvidenceReferenceV1:
        from .mode_snapshot_policy import pre_f_unavailable_reference

        return pre_f_unavailable_reference(
            observed_at=context.as_of,
            valid_until=context.as_of + context.maximum_age,
            causation_id=causation_id,
            correlation_id=correlation_id,
        )


class CurrentOwnerActionConfirmationAdapterV1:
    """Exact read-only adapter for current owner-action confirmation receipts."""

    def __init__(self, registry: CanonicalOwnerPacketRegistryV1) -> None:
        if not isinstance(registry, CanonicalOwnerPacketRegistryV1):
            raise InputAuthorityError(
                ReasonCode.INPUT_OWNER_MISSING,
                "owner-action adapter requires the canonical packet registry",
            )
        self._registry = registry

    def read_owner_action_confirmation(
        self, context: ComputationExecutionContextV1
    ) -> OwnerActionConfirmationReceiptV1:
        payload = _exact_d_owner_payload(
            registry=self._registry,
            context=context,
            binding_id=ST12D_OWNER_ACTION_BINDING_ID,
            owner_id="OwnerActionSemanticProtocolV1",
            packet_type="OwnerActionConfirmationReceiptV1",
            schema_id="OwnerActionConfirmationReceiptV1::SCHEMA",
            field_path="owner_action.confirmation",
            payload_type=OwnerActionConfirmationReceiptV1,
        )
        assert isinstance(payload, OwnerActionConfirmationReceiptV1)
        return payload


class CurrentModeSnapshotInputResolverV1:
    """Gate-first D resolver; all repository projections are injected preloaded."""

    def __init__(
        self,
        *,
        repo_root: str | Path,
        owner_registry: CanonicalOwnerPacketRegistryV1,
        canonical_f_evidence_owner: object | None = None,
    ) -> None:
        if canonical_f_evidence_owner is not None and not callable(
            getattr(canonical_f_evidence_owner, "read_evidence_reference", None)
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_OWNER_MISMATCH,
                "F evidence owner must expose the exact read-only reference method",
            )
        self._repo_root = Path(repo_root).resolve()
        self._owner_registry = owner_registry
        self._safety = CurrentSafetyStateAdapterV1(owner_registry)
        self._evidence = (
            CurrentPreFEvidenceAdapterV1()
            if canonical_f_evidence_owner is None
            else canonical_f_evidence_owner
        )
        self._owner_action = CurrentOwnerActionConfirmationAdapterV1(owner_registry)

    @property
    def owner_registry(self) -> CanonicalOwnerPacketRegistryV1:
        return self._owner_registry

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    @property
    def canonical_f_evidence_owner(self) -> object:
        """Return the immutable injected owner; requests cannot replace it."""

        return self._evidence

    @staticmethod
    def _admitted_context(
        request: object,
        capability_decision: object,
    ) -> tuple[object, ComputationExecutionContextV1, str, str]:
        from .agent_policy import AgentCapabilityDecisionV1

        context = getattr(request, "context", None)
        if (
            type(capability_decision) is not AgentCapabilityDecisionV1
            or not isinstance(context, ComputationExecutionContextV1)
            or getattr(request, "request_id", None) != capability_decision.request_id
            or getattr(request, "principal_id", None)
            != capability_decision.principal_id
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "current D resolution requires the exact admitted E identity/context",
            )
        if len(capability_decision.st12c_causation_correlation_refs) < 2:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "admitted E decision lacks causation/correlation lineage",
            )
        causation_id, correlation_id = (
            capability_decision.st12c_causation_correlation_refs[:2]
        )
        return capability_decision, context, causation_id, correlation_id

    @staticmethod
    def _typed_f_reference_query(
        request: object,
        decision: object,
        context: ComputationExecutionContextV1,
        *,
        causation_id: str,
        correlation_id: str,
        safety_receipt_ref: str,
    ) -> object | None:
        from .evidence import FToDEvidenceReferenceQueryV1

        requested_evidence_id = getattr(request, "evidence_id", None)
        expected_input_lock_id = getattr(request, "input_lock_id", None)
        requested_component = getattr(request, "component_id", None)
        expected_epochs = getattr(request, "source_epoch_refs", None)
        evidence_refs = tuple(getattr(decision, "evidence_refs", ()))
        scope_refs = tuple(getattr(decision, "scope_refs", ()))
        request_refs = tuple(getattr(request, "source_candidate_refs", ()))
        tagged_refs = tuple(dict.fromkeys((*request_refs, *evidence_refs)))

        if not isinstance(requested_evidence_id, str) or not requested_evidence_id:
            matches = tuple(
                ref.split("=", 1)[1]
                for ref in tagged_refs
                if ref.startswith("ST12F_EVIDENCE_ID=") and "=" in ref
            )
            requested_evidence_id = matches[0] if len(matches) == 1 else None
        if not isinstance(expected_input_lock_id, str) or not expected_input_lock_id:
            matches = tuple(
                ref.split("=", 1)[1]
                for ref in tagged_refs
                if ref.startswith("ST12F_INPUT_LOCK_ID=") and "=" in ref
            )
            expected_input_lock_id = matches[0] if len(matches) == 1 else None
        if not isinstance(requested_component, str) or not requested_component:
            tagged_matches = tuple(
                ref.split("=", 1)[1]
                for ref in tagged_refs
                if ref.startswith("ST12F_COMPONENT_OR_TEMPLATE_REF=")
                and "=" in ref
            )
            scope_matches = tuple(ref for ref in scope_refs if ref.startswith("MATH-"))
            requested_component = (
                tagged_matches[0]
                if len(tagged_matches) == 1
                else scope_matches[0]
                if len(scope_matches) == 1
                else None
            )
        if not isinstance(expected_epochs, tuple) or not expected_epochs:
            expected_epochs = tuple(
                ref.split("ST12F_SOURCE_EPOCH=", 1)[1]
                for ref in tagged_refs
                if ref.startswith("ST12F_SOURCE_EPOCH=")
            )
        if (
            not isinstance(requested_evidence_id, str)
            or not requested_evidence_id
            or not isinstance(expected_input_lock_id, str)
            or not expected_input_lock_id
            or not isinstance(requested_component, str)
            or not requested_component
            or not isinstance(expected_epochs, tuple)
            or not expected_epochs
        ):
            return None
        return FToDEvidenceReferenceQueryV1(
            query_id=f"ST12D-F-QUERY::{getattr(decision, 'request_id')}",
            requested_evidence_id=requested_evidence_id,
            requested_component_or_template_ref=requested_component,
            expected_input_lock_id=expected_input_lock_id,
            expected_source_epoch_refs=expected_epochs,
            evaluated_at=context.as_of,
            request_read_lineage_refs=tuple(
                dict.fromkeys(
                    (
                        getattr(decision, "agent_orch_receipt_ref"),
                        safety_receipt_ref,
                        causation_id,
                        correlation_id,
                    )
                )
            ),
        )

    @staticmethod
    def _validate_f_reference_for_d(
        *,
        context: ComputationExecutionContextV1,
        query: object | None,
        reference: ST12FEvidenceReferenceV1,
        causation_id: str,
        correlation_id: str,
    ) -> ST12FEvidenceReferenceV1:
        if reference.evidence_state is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE:
            return reference
        valid = (
            query is not None
            and reference.reference_id != "EXPLICIT_ABSENCE"
            and reference.evidence_id == getattr(query, "requested_evidence_id", None)
            and reference.component_or_template_ref
            == getattr(query, "requested_component_or_template_ref", None)
            and reference.input_lock_id
            == getattr(query, "expected_input_lock_id", None)
            and reference.source_epoch_refs
            == getattr(query, "expected_source_epoch_refs", None)
            and reference.lane == "REPLAY_PAPER"
            and reference.terminal_state == "CLOSED_INDEPENDENTLY_VALIDATED"
            and reference.evidence_ref.startswith("ST12F-RECEIPT::")
            and reference.contract_version == "1.4"
            and reference.no_effect_flags == NO_EFFECTS_V1
            and reference.observed_at
            <= getattr(query, "evaluated_at", context.as_of)
            <= reference.valid_until
        )
        if valid:
            return reference
        from .mode_snapshot_policy import pre_f_unavailable_reference

        return pre_f_unavailable_reference(
            observed_at=context.as_of,
            valid_until=context.as_of,
            causation_id=causation_id,
            correlation_id=correlation_id,
        )

    def resolve_mode_snapshot_preconstruction_gate(
        self,
        request: object,
        capability_decision: object,
    ) -> object:
        from .mode_snapshot_policy import ModeSnapshotPreconstructionGateV1

        decision, context, causation_id, correlation_id = self._admitted_context(
            request,
            capability_decision,
        )
        safety = self._safety.read_kill_submit_state(context)
        safety_packet = self._owner_registry.packet_for(
            context=context,
            binding_id=ST12D_SAFETY_BINDING_ID,
        )
        if getattr(self._evidence, "supports_typed_reference_query", False):
            query = self._typed_f_reference_query(
                request,
                decision,
                context,
                causation_id=causation_id,
                correlation_id=correlation_id,
                safety_receipt_ref=safety_packet.producer_receipt_id,
            )
            evidence = self._evidence.read_evidence_reference(
                context,
                causation_id=causation_id,
                correlation_id=correlation_id,
                query=query,
            )
            evidence = self._validate_f_reference_for_d(
                context=context,
                query=query,
                reference=evidence,
                causation_id=causation_id,
                correlation_id=correlation_id,
            )
        else:
            evidence = self._evidence.read_evidence_reference(
                context,
                causation_id=causation_id,
                correlation_id=correlation_id,
            )
        evidence_receipt_refs = (
            (
                f"ST12F-RECEIPT::{evidence.reference_id}::D_EVIDENCE_REFERENCE",
            )
            if evidence.evidence_state
            is ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
            else ()
        )
        return ModeSnapshotPreconstructionGateV1(
            request_id=decision.request_id,
            principal_id=decision.principal_id,
            task_id=decision.task_id,
            current_agent_id=decision.current_agent_id,
            capability_decision_ref=decision.decision_id,
            context_ref=context.context_id,
            current_mode=context.scope.mode_context_id,
            requested_mode="HOTPATH_CANDIDATE_ONLY",
            candidate_version=context.input_version,
            evaluated_at=context.as_of,
            expires_at=min(
                context.as_of + context.maximum_age,
                safety.valid_until,
                evidence.valid_until,
            ),
            causation_id=causation_id,
            correlation_id=correlation_id,
            receipt_lineage_refs=tuple(
                dict.fromkeys(
                    (
                        decision.agent_orch_receipt_ref,
                        safety_packet.producer_receipt_id,
                        *evidence_receipt_refs,
                    )
                )
            ),
            source_epoch_refs=tuple(
                dict.fromkeys(
                    (
                        safety_packet.source_epoch_id,
                        *evidence.source_epoch_refs,
                    )
                )
            ),
            evidence_reference=evidence,
            kill_submit_state=safety,
        )

    def enrich_mode_snapshot_candidate(
        self,
        request: object,
        capability_decision: object,
        preconstruction_gate: object,
        owner_projections: object,
    ) -> object:
        from .implementation_registry import ST12D_MATH_IMPLEMENTATION_REGISTRY
        from .mode_snapshot_policy import (
            ModeSnapshotCandidateInputsV1,
            ModeSnapshotPreconstructionGateV1,
        )
        from .parameter_policy import (
            ST12D_PARAMETER_POLICY_SET_VERSION,
            resolve_st12d_snapshot_parameter_values,
        )
        from .protocols import PreloadedOwnerProjectionBundleV1
        from .stack_resolver import preflight_snapshot_computation_bundle
        from .models import SnapshotParameterResolutionStateV1

        decision, context, causation_id, correlation_id = self._admitted_context(
            request,
            capability_decision,
        )
        if (
            type(preconstruction_gate) is not ModeSnapshotPreconstructionGateV1
            or type(owner_projections) is not PreloadedOwnerProjectionBundleV1
            or preconstruction_gate.request_id != decision.request_id
            or preconstruction_gate.context_ref != context.context_id
            or preconstruction_gate.causation_id != causation_id
            or preconstruction_gate.correlation_id != correlation_id
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "D enrichment requires the admitted gate and one preloaded owner bundle",
            )
        owner_action = self._owner_action.read_owner_action_confirmation(context)
        owner_action_packet = self._owner_registry.packet_for(
            context=context,
            binding_id=ST12D_OWNER_ACTION_BINDING_ID,
        )
        resolved_parameter_values = resolve_st12d_snapshot_parameter_values(
            context=context,
            owner_registry=self._owner_registry,
        )
        unavailable = tuple(
            row
            for row in resolved_parameter_values
            if row.resolution_state
            is SnapshotParameterResolutionStateV1.REQUIRED_OWNER_VALUE_UNAVAILABLE
        )
        if unavailable:
            raise InputAuthorityError(
                unavailable[0].diagnostic_reason_codes[0],
                "D candidate construction is blocked by unresolved snapshot parameter values: "
                + ", ".join(row.parameter_id for row in unavailable),
            )
        parameter_value_refs = tuple(
            row.resolved_value_ref for row in resolved_parameter_values
        )
        parameter_policy_snapshot_ref = (
            f"ComputationParameterPolicyV1::{ST12D_PARAMETER_POLICY_SET_VERSION}"
        )
        formula_input_resolutions = tuple(
            FormulaInputResolverV1.resolve(
                math_id,
                context=context,
                owner_registry=self._owner_registry,
            )
            for math_id in ST12D_MATH_IMPLEMENTATION_REGISTRY
        )
        consumed_formula_epochs = tuple(
            self._owner_registry.packet_by_id(packet_id).source_epoch_id
            for resolution in formula_input_resolutions
            for packet_id in resolution.packet_refs
        )
        source_epoch_refs = tuple(
            dict.fromkeys(
                (
                    *consumed_formula_epochs,
                    *(
                        epoch
                        for row in resolved_parameter_values
                        for epoch in row.source_epoch_refs
                    ),
                    *preconstruction_gate.source_epoch_refs,
                    owner_action_packet.source_epoch_id,
                    *owner_projections.source_epoch_refs,
                )
            )
        )
        bundle = preflight_snapshot_computation_bundle(
            context=context,
            owner_registry=self._owner_registry,
            parameter_policy_snapshot_ref=parameter_policy_snapshot_ref,
            parameter_value_refs=parameter_value_refs,
            resolved_parameter_values=resolved_parameter_values,
            source_epoch_refs=source_epoch_refs,
            formula_input_resolutions=formula_input_resolutions,
        )
        implementation_pins = tuple(
            ImplementationVersionPinV1(
                math_spec_id=math_id,
                implementation_id=(
                    ST12D_MATH_IMPLEMENTATION_REGISTRY[
                        math_id
                    ].contract.implementation_id
                ),
            )
            for math_id in ST12D_MATH_IMPLEMENTATION_REGISTRY
        )
        if context.implementation_versions != implementation_pins:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "D execution context implementation pins differ from the selected bundle",
            )
        receipt_lineage_refs = tuple(
            dict.fromkeys(
                (
                    decision.agent_orch_receipt_ref,
                    *preconstruction_gate.receipt_lineage_refs,
                    owner_action.receipt_ref,
                    owner_action_packet.producer_receipt_id,
                    *(
                        ref
                        for resolution in formula_input_resolutions
                        for ref in resolution.receipt_refs
                    ),
                    *(
                        ref
                        for row in resolved_parameter_values
                        for ref in (
                            *row.producer_receipt_refs,
                            *row.point_in_time_receipt_refs,
                            *row.freshness_receipt_refs,
                        )
                    ),
                    *(
                        (
                            owner_action.predecessor_transition_receipt_ref_or_explicit_absence,
                        )
                        if owner_action.predecessor_transition_receipt_proposal_or_explicit_absence
                        is not None
                        else ()
                    ),
                    *owner_projections.receipt_refs,
                )
            )
        )
        expires_at = min(
            context.as_of + context.maximum_age,
            preconstruction_gate.kill_submit_state.valid_until,
            owner_action.valid_until,
        )
        return ModeSnapshotCandidateInputsV1(
            request_id=decision.request_id,
            principal_id=decision.principal_id,
            task_id=decision.task_id,
            current_agent_id=decision.current_agent_id,
            capability_decision_ref=decision.decision_id,
            computation_bundle_ref=bundle.bundle_ref,
            context_ref=context.context_id,
            formula_spec_refs=tuple(ST12D_MATH_IMPLEMENTATION_REGISTRY),
            implementation_version_pins=implementation_pins,
            binding_profile_ref=(
                f"ComputationBindingProfileV1::{context.binding_profile_version}"
            ),
            parameter_policy_snapshot_ref=parameter_policy_snapshot_ref,
            parameter_value_refs=parameter_value_refs,
            resolved_parameter_values=resolved_parameter_values,
            source_epoch_refs=source_epoch_refs,
            receipt_lineage_refs=receipt_lineage_refs,
            readiness_state_ref=(
                f"READINESS1::{owner_projections.readiness.source_version}"
            ),
            pretrade_state_ref=(
                f"PRETRADE1::{owner_projections.pretrade.source_version}"
            ),
            owner_action_policy_ref=owner_action.owner_action_policy_ref,
            current_mode=context.scope.mode_context_id,
            requested_mode="HOTPATH_CANDIDATE_ONLY",
            expected_owner_state_ref=(
                f"SVC1::{owner_projections.svc.source_version}"
            ),
            candidate_version=context.input_version,
            created_at=context.as_of,
            evaluated_at=context.as_of,
            expires_at=expires_at,
            causation_id=causation_id,
            correlation_id=correlation_id,
            evidence_reference=preconstruction_gate.evidence_reference,
            kill_submit_state=preconstruction_gate.kill_submit_state,
            computation_bundle_closure=bundle,
            owner_action_confirmation=owner_action,
        )


PIT_PUBLIC_INPUT_OWNER_IDS_V1 = frozenset(
    {
        "SelectedVenuePublicMarketDataOwnerV1",
        "KalshiAcceptedOrderBookStateOwnerV1",
        "KalshiMarketMetadataOwnerV1",
    }
)
PIT_PUBLIC_ORIGIN_CLASSES_V1 = frozenset(
    {
        "ACCEPTED_POINT_IN_TIME_SNAPSHOT",
        "ACCEPTED_VERSIONED_MARKET_METADATA",
    }
)
PIT_RAW_INPUT_PACKET_TYPES_V1 = frozenset({"SequencedBookEventsPacketV1"})


def _pit_input_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


def _pit_input_text_tuple(
    value: object,
    name: str,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple or (not allow_empty and not value):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be an exact tuple",
        )
    result = tuple(_pit_input_text(item, name) for item in value)
    if len(result) != len(set(result)):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
            f"{name} contains duplicate identities",
        )
    return result


@dataclass(frozen=True, slots=True)
class PITFormulaInputAuthorityPartitionV1:
    all_binding_ids: frozenset[str]
    pit_applicable_binding_ids: frozenset[str]
    non_pit_binding_ids: frozenset[str]
    canonical_binding_order: tuple[str, ...]
    pit_applicable_binding_order: tuple[str, ...]
    non_pit_binding_order: tuple[str, ...]
    all_row_count: int
    pit_row_count: int
    non_pit_row_count: int
    intersection_empty: bool
    union_complete: bool
    duplicate_binding_identity_count: int
    duplicate_object_inclusion_count: int
    unclassified_row_type_count: int

    def __post_init__(self) -> None:
        for name in (
            "all_binding_ids",
            "pit_applicable_binding_ids",
            "non_pit_binding_ids",
        ):
            value = getattr(self, name)
            if type(value) is not frozenset or any(
                type(item) is not str or not item for item in value
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact text frozenset",
                )
        for name, expected_set in (
            ("canonical_binding_order", self.all_binding_ids),
            ("pit_applicable_binding_order", self.pit_applicable_binding_ids),
            ("non_pit_binding_order", self.non_pit_binding_ids),
        ):
            ordered = _pit_input_text_tuple(
                getattr(self, name), name, allow_empty=True
            )
            if frozenset(ordered) != expected_set:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                    f"{name} does not equal its binding-ID set",
                )
        for name in (
            "all_row_count",
            "pit_row_count",
            "non_pit_row_count",
            "duplicate_binding_identity_count",
            "duplicate_object_inclusion_count",
            "unclassified_row_type_count",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be a nonnegative exact integer",
                )
        if type(self.intersection_empty) is not bool or type(
            self.union_complete
        ) is not bool:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "partition laws must be exact booleans",
            )
        if (
            self.all_row_count != len(self.canonical_binding_order)
            or self.pit_row_count != len(self.pit_applicable_binding_order)
            or self.non_pit_row_count != len(self.non_pit_binding_order)
            or self.pit_row_count + self.non_pit_row_count != self.all_row_count
            or not self.intersection_empty
            or not self.union_complete
            or self.duplicate_binding_identity_count
            or self.duplicate_object_inclusion_count
            or self.unclassified_row_type_count
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "formula-input authority partition is not exact and total",
            )


def _pit_formula_rows_once() -> tuple[object, ...]:
    rows: list[object] = []
    for math_id, values in CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID.items():
        _pit_input_text(math_id, "math_id")
        if type(values) is not tuple:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "formula-input authority registry values must be exact tuples",
            )
        rows.extend(values)
    return tuple(rows)


def _pit_binding_id(row: object) -> str:
    if type(row) not in {
        FormulaInputAuthorityBindingV1,
        ST12DMath39RawInputBindingV1,
    }:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"unclassified formula-input authority row type: {type(row).__name__}",
        )
    return _pit_input_text(row.binding_id, "binding_id")


def _pit_row_is_applicable(row: object) -> bool:
    if type(row) is FormulaInputAuthorityBindingV1:
        return (
            row.accepted_upstream_owner_id in PIT_PUBLIC_INPUT_OWNER_IDS_V1
            and row.allowed_origin_class in PIT_PUBLIC_ORIGIN_CLASSES_V1
        )
    if type(row) is ST12DMath39RawInputBindingV1:
        return (
            row.accepted_upstream_owner_id
            == "SelectedVenuePublicMarketDataOwnerV1"
            and row.accepted_packet_or_snapshot_type in PIT_RAW_INPUT_PACKET_TYPES_V1
            and row.binding_id == "FIVAB::sequenced_book_events::MATH-39"
            and row.input_name == "sequenced_book_events"
        )
    _pit_binding_id(row)
    raise AssertionError("unreachable unclassified formula-input row")


def partition_pit_formula_input_authority_v1() -> PITFormulaInputAuthorityPartitionV1:
    """Partition the current registry once, preserving exact canonical order."""

    rows = _pit_formula_rows_once()
    all_ids: list[str] = []
    pit_ids: list[str] = []
    non_pit_ids: list[str] = []
    object_ids: list[int] = []
    unclassified = 0
    for row in rows:
        if type(row) not in {
            FormulaInputAuthorityBindingV1,
            ST12DMath39RawInputBindingV1,
        }:
            unclassified += 1
            continue
        binding_id = _pit_binding_id(row)
        all_ids.append(binding_id)
        object_ids.append(id(row))
        (pit_ids if _pit_row_is_applicable(row) else non_pit_ids).append(binding_id)
    duplicate_binding_count = len(all_ids) - len(set(all_ids))
    duplicate_object_count = len(object_ids) - len(set(object_ids))
    all_set = frozenset(all_ids)
    pit_set = frozenset(pit_ids)
    non_pit_set = frozenset(non_pit_ids)
    return PITFormulaInputAuthorityPartitionV1(
        all_binding_ids=all_set,
        pit_applicable_binding_ids=pit_set,
        non_pit_binding_ids=non_pit_set,
        canonical_binding_order=tuple(all_ids),
        pit_applicable_binding_order=tuple(pit_ids),
        non_pit_binding_order=tuple(non_pit_ids),
        all_row_count=len(rows),
        pit_row_count=len(pit_ids),
        non_pit_row_count=len(non_pit_ids),
        intersection_empty=pit_set.isdisjoint(non_pit_set),
        union_complete=pit_set | non_pit_set == all_set,
        duplicate_binding_identity_count=duplicate_binding_count,
        duplicate_object_inclusion_count=duplicate_object_count,
        unclassified_row_type_count=unclassified,
    )


@dataclass(frozen=True, slots=True)
class PITInputCapabilityV2:
    capability_id: str
    profile_id: Stage1VenueProfileIdV1
    binding_id: str
    math_spec_id: str
    input_name: str
    accepted_packet_or_snapshot_type: str
    source_field_path: str
    declared_input_type: str
    declared_shape_or_none: str | None
    unit_or_basis: str
    transform: str
    required_clock_fields: tuple[str, ...]
    required_depth_class_or_none: PITDepthClassV2 | None
    provider_sequence_required: bool
    provider_publication_time_required: bool
    required_state: str
    source_contract_ref: str
    rights_receipt_ref: str
    availability: PITInputAvailabilityV2
    unavailable_reason_or_none: PITReasonCodeV1 | None
    event_or_snapshot_ref_or_none: str | None
    freshness_receipt_ref_or_none: str | None
    context_id: str
    source_epoch_id: str
    input_version: str

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "profile_id must be an exact Stage1VenueProfileIdV1",
            )
        for name in (
            "capability_id",
            "binding_id",
            "math_spec_id",
            "input_name",
            "accepted_packet_or_snapshot_type",
            "source_field_path",
            "declared_input_type",
            "unit_or_basis",
            "transform",
            "required_state",
            "source_contract_ref",
            "rights_receipt_ref",
            "context_id",
            "source_epoch_id",
            "input_version",
        ):
            _pit_input_text(getattr(self, name), name)
        if self.declared_shape_or_none is not None:
            _pit_input_text(self.declared_shape_or_none, "declared_shape_or_none")
        _pit_input_text_tuple(
            self.required_clock_fields,
            "required_clock_fields",
            allow_empty=False,
        )
        if self.required_depth_class_or_none is not None and type(
            self.required_depth_class_or_none
        ) is not PITDepthClassV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TOP_LEVEL_DEPTH_ONLY,
                "required depth class has the wrong exact type",
            )
        for name in (
            "provider_sequence_required",
            "provider_publication_time_required",
        ):
            if type(getattr(self, name)) is not bool:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact boolean",
                )
        if type(self.availability) is not PITInputAvailabilityV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "availability has the wrong exact type",
            )
        if self.unavailable_reason_or_none is not None and type(
            self.unavailable_reason_or_none
        ) is not PITReasonCodeV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "unavailable reason has the wrong exact type",
            )
        for name in (
            "event_or_snapshot_ref_or_none",
            "freshness_receipt_ref_or_none",
        ):
            value = getattr(self, name)
            if value is not None:
                _pit_input_text(value, name)
        if self.availability is PITInputAvailabilityV2.AVAILABLE:
            if (
                self.unavailable_reason_or_none is not None
                or self.event_or_snapshot_ref_or_none is None
                or self.freshness_receipt_ref_or_none is None
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                    "available capability requires exact event and freshness lineage",
                )
        elif (
            self.unavailable_reason_or_none is None
            or self.event_or_snapshot_ref_or_none is not None
            or self.freshness_receipt_ref_or_none is not None
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "unavailable capability requires a reason and no admitted lineage",
            )

    @property
    def key(self) -> tuple[Stage1VenueProfileIdV1, str]:
        return (self.profile_id, self.binding_id)


@dataclass(frozen=True, slots=True)
class PITFormulaInputPacketV2:
    packet_id: str
    profile_id: Stage1VenueProfileIdV1
    binding_id: str
    context_id: str
    source_epoch_id: str
    input_version: str
    declared_input_type: str
    declared_shape_or_none: str | None
    unit_or_basis: str
    source_field_path: str
    value: object
    event_or_snapshot_ref: str
    freshness_receipt_ref: str

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "packet profile has the wrong exact type",
            )
        for name in (
            "packet_id",
            "binding_id",
            "context_id",
            "source_epoch_id",
            "input_version",
            "declared_input_type",
            "unit_or_basis",
            "source_field_path",
            "event_or_snapshot_ref",
            "freshness_receipt_ref",
        ):
            _pit_input_text(getattr(self, name), name)
        if self.declared_shape_or_none is not None:
            _pit_input_text(self.declared_shape_or_none, "declared_shape_or_none")
        object.__setattr__(self, "value", _freeze(self.value))

    @property
    def key(self) -> tuple[Stage1VenueProfileIdV1, str]:
        return (self.profile_id, self.binding_id)


@dataclass(frozen=True, slots=True)
class PITResolvedFormulaInputV2:
    profile_id: Stage1VenueProfileIdV1
    binding_id: str
    math_spec_id: str
    input_name: str
    value: object
    declared_input_type: str
    declared_shape_or_none: str | None
    unit_or_basis: str
    source_field_path: str
    context_id: str
    source_epoch_id: str
    input_version: str
    packet_ref: str
    event_or_snapshot_ref: str
    freshness_receipt_ref: str

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "resolved profile has the wrong exact type",
            )
        for name in (
            "binding_id",
            "math_spec_id",
            "input_name",
            "declared_input_type",
            "unit_or_basis",
            "source_field_path",
            "context_id",
            "source_epoch_id",
            "input_version",
            "packet_ref",
            "event_or_snapshot_ref",
            "freshness_receipt_ref",
        ):
            _pit_input_text(getattr(self, name), name)
        if self.declared_shape_or_none is not None:
            _pit_input_text(self.declared_shape_or_none, "declared_shape_or_none")
        object.__setattr__(self, "value", _freeze(self.value))


@dataclass(frozen=True, slots=True)
class PITFormulaInputResolutionV2:
    resolution_id: str
    context_id: str
    source_epoch_id: str
    input_version: str
    resolved_inputs: tuple[PITResolvedFormulaInputV2, ...]
    unavailable_capabilities: tuple[PITInputCapabilityV2, ...]
    required_keys: frozenset[tuple[Stage1VenueProfileIdV1, str]]
    exact_key_set_equal: bool

    def __post_init__(self) -> None:
        for name in (
            "resolution_id",
            "context_id",
            "source_epoch_id",
            "input_version",
        ):
            _pit_input_text(getattr(self, name), name)
        if type(self.resolved_inputs) is not tuple or any(
            type(value) is not PITResolvedFormulaInputV2
            for value in self.resolved_inputs
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "resolved_inputs must be exact PITResolvedFormulaInputV2 values",
            )
        if type(self.unavailable_capabilities) is not tuple or any(
            type(value) is not PITInputCapabilityV2
            for value in self.unavailable_capabilities
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "unavailable_capabilities must contain exact capabilities",
            )
        if type(self.required_keys) is not frozenset or any(
            type(key) is not tuple
            or len(key) != 2
            or type(key[0]) is not Stage1VenueProfileIdV1
            or type(key[1]) is not str
            for key in self.required_keys
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "required_keys has an invalid exact key",
            )
        if type(self.exact_key_set_equal) is not bool or not self.exact_key_set_equal:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "formula-input resolution key set is not exact",
            )


def _pit_resolution_binding_metadata(binding_id: str) -> dict[str, object]:
    matches = tuple(
        row
        for row in _pit_formula_rows_once()
        if type(row)
        in {FormulaInputAuthorityBindingV1, ST12DMath39RawInputBindingV1}
        and row.binding_id == binding_id
        and _pit_row_is_applicable(row)
    )
    if len(matches) != 1:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
            "capability binding identity does not resolve exactly once",
        )
    row = matches[0]
    if type(row) is FormulaInputAuthorityBindingV1:
        shape_by_exact_type = {
            "Decimal string": "SCALAR",
            "boolean": "SCALAR",
            "enum": "SCALAR",
            "int": "SCALAR",
            "list[Decimal string]": "SEQUENCE",
            "list[record]": "SEQUENCE",
        }
        try:
            shape = shape_by_exact_type[row.input_type]
        except KeyError as exc:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "formula binding has an unclassified exact input type",
            ) from exc
        return {
            "math_spec_id": row.math_spec_id,
            "input_name": row.input_name,
            "packet_type": row.accepted_packet_or_snapshot_type,
            "source_path": row.exact_field_path,
            "input_type": row.input_type,
            "shape": shape,
            "unit": row.unit_or_basis,
            "transform": row.canonical_typed_value_extraction,
            "required_clock_fields": tuple(row.required_clock_fields),
        }
    if type(row) is ST12DMath39RawInputBindingV1:
        return {
            "math_spec_id": "MATH-39",
            "input_name": row.input_name,
            "packet_type": row.accepted_packet_or_snapshot_type,
            "source_path": row.exact_field_path,
            "input_type": "SequencedBookEventsPacketV1",
            "shape": "SEQUENCE",
            "unit": row.unit_or_basis,
            "transform": row.point_in_time_rule,
            "required_clock_fields": (
                "qtt_received_at_utc",
                "qtt_parse_completed_at_utc",
                "durable_commit_completed_at_utc",
                "strategy_available_at_utc",
            ),
        }
    raise AssertionError("unreachable exact formula binding type")


def _pit_validate_resolution_capability_metadata(
    capability: PITInputCapabilityV2,
) -> None:
    expected = _pit_resolution_binding_metadata(capability.binding_id)
    actual = {
        "math_spec_id": capability.math_spec_id,
        "input_name": capability.input_name,
        "packet_type": capability.accepted_packet_or_snapshot_type,
        "source_path": capability.source_field_path,
        "input_type": capability.declared_input_type,
        "shape": capability.declared_shape_or_none,
        "unit": capability.unit_or_basis,
        "transform": capability.transform,
        "required_clock_fields": capability.required_clock_fields,
    }
    if actual != expected:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
            "capability metadata differs from the canonical formula-input binding",
        )


def _pit_packet_value_matches_type(value: object, declared_type: str) -> bool:
    if declared_type == "boolean":
        return type(value) is bool
    if declared_type == "int":
        return type(value) is int
    if declared_type == "Decimal string":
        if type(value) is not str:
            return False
        try:
            exact_decimal(value, field_name="PIT formula input")
        except NumericDomainError:
            return False
        return True
    if declared_type == "list[Decimal string]":
        if type(value) is not tuple or not value:
            return False
        try:
            for item in value:
                if type(item) is not str:
                    return False
                exact_decimal(item, field_name="PIT formula input list")
        except NumericDomainError:
            return False
        return True
    if declared_type == "enum":
        return type(value) is str and bool(value)
    if declared_type in {"list[record]", "SequencedBookEventsPacketV1"}:
        return (
            type(value) is tuple
            and bool(value)
            and all(isinstance(item, Mapping) for item in value)
        )
    return False


def resolve_pit_formula_inputs_v2(
    capabilities: tuple[PITInputCapabilityV2, ...],
    packets: tuple[PITFormulaInputPacketV2, ...],
    *,
    resolution_id: str,
    context_id: str,
    source_epoch_id: str,
    input_version: str,
) -> PITFormulaInputResolutionV2:
    """Resolve available capabilities without synthesizing missing truth."""

    _pit_input_text(resolution_id, "resolution_id")
    for name, value in (
        ("context_id", context_id),
        ("source_epoch_id", source_epoch_id),
        ("input_version", input_version),
    ):
        _pit_input_text(value, name)
    if type(capabilities) is not tuple or any(
        type(value) is not PITInputCapabilityV2 for value in capabilities
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "capabilities must be an exact PITInputCapabilityV2 tuple",
        )
    if type(packets) is not tuple or any(
        type(value) is not PITFormulaInputPacketV2 for value in packets
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "packets must be an exact PITFormulaInputPacketV2 tuple",
        )
    capability_by_key: dict[
        tuple[Stage1VenueProfileIdV1, str], PITInputCapabilityV2
    ] = {}
    for capability in capabilities:
        _pit_validate_resolution_capability_metadata(capability)
        if capability.key in capability_by_key:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "duplicate PIT capability key",
            )
        capability_by_key[capability.key] = capability
    packet_by_key: dict[
        tuple[Stage1VenueProfileIdV1, str], PITFormulaInputPacketV2
    ] = {}
    for packet in packets:
        if packet.key in packet_by_key:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "duplicate PIT formula-input packet key",
            )
        packet_by_key[packet.key] = packet
    available_keys = {
        key
        for key, capability in capability_by_key.items()
        if capability.availability is PITInputAvailabilityV2.AVAILABLE
    }
    if set(packet_by_key) != available_keys:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
            "packet keys must equal available capability keys exactly",
        )
    resolved: list[PITResolvedFormulaInputV2] = []
    unavailable: list[PITInputCapabilityV2] = []
    for capability in capabilities:
        if (
            capability.context_id != context_id
            or capability.source_epoch_id != source_epoch_id
            or capability.input_version != input_version
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "capability context/source epoch/input version mismatch",
            )
        if capability.availability is not PITInputAvailabilityV2.AVAILABLE:
            unavailable.append(capability)
            continue
        packet = packet_by_key[capability.key]
        equality_pairs = (
            (packet.context_id, capability.context_id),
            (packet.source_epoch_id, capability.source_epoch_id),
            (packet.input_version, capability.input_version),
            (packet.declared_input_type, capability.declared_input_type),
            (packet.declared_shape_or_none, capability.declared_shape_or_none),
            (packet.unit_or_basis, capability.unit_or_basis),
            (packet.source_field_path, capability.source_field_path),
            (packet.event_or_snapshot_ref, capability.event_or_snapshot_ref_or_none),
            (packet.freshness_receipt_ref, capability.freshness_receipt_ref_or_none),
        )
        if any(left != right for left, right in equality_pairs):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "packet metadata does not exactly equal the capability binding",
            )
        if not _pit_packet_value_matches_type(
            packet.value, capability.declared_input_type
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
                "packet value does not match the exact declared input type",
            )
        resolved.append(
            PITResolvedFormulaInputV2(
                profile_id=capability.profile_id,
                binding_id=capability.binding_id,
                math_spec_id=capability.math_spec_id,
                input_name=capability.input_name,
                value=packet.value,
                declared_input_type=capability.declared_input_type,
                declared_shape_or_none=capability.declared_shape_or_none,
                unit_or_basis=capability.unit_or_basis,
                source_field_path=capability.source_field_path,
                context_id=context_id,
                source_epoch_id=source_epoch_id,
                input_version=input_version,
                packet_ref=packet.packet_id,
                event_or_snapshot_ref=packet.event_or_snapshot_ref,
                freshness_receipt_ref=packet.freshness_receipt_ref,
            )
        )
    required_keys = frozenset(capability_by_key)
    actual_keys = {
        (value.profile_id, value.binding_id) for value in resolved
    } | {value.key for value in unavailable}
    return PITFormulaInputResolutionV2(
        resolution_id=resolution_id,
        context_id=context_id,
        source_epoch_id=source_epoch_id,
        input_version=input_version,
        resolved_inputs=tuple(resolved),
        unavailable_capabilities=tuple(unavailable),
        required_keys=required_keys,
        exact_key_set_equal=actual_keys == set(required_keys),
    )


# F14 pending references are separate from the closed formula input registry.
from _thread import RLock
from .context import _f14_freeze_v1, _f14_plain_v1
from .source_policy import RetailPrivateSourceRegistryV1, _f14_ingress_require_v1


class PrivateObservationPublisherV1:
    def __init__(self, *, source_registry):
        _f14_ingress_require_v1(type(source_registry) is RetailPrivateSourceRegistryV1,
            'F14_INGRESS_SOURCE')
        self.source_registry = source_registry
        self._lock = RLock()
        self._slots = {}
        self._requests = {}

    def _capture_v1(self, observed):
        entry = self.source_registry._captures.get(id(observed))
        _f14_ingress_require_v1(entry is not None and entry[0] is observed and entry[3] is True,
            'F14_INGRESS_CAPTURE_ASSOCIATION')
        return entry

    def publish_private_reference_v1(self, observed, raw_record_ref, capture_commit_ref):
        with self.source_registry._lock:
            entry = self._capture_v1(observed)
            request, attempt = entry[2], entry[4]
            with self.source_registry.fenced(request.grant, request.operation):
                _f14_ingress_require_v1(raw_record_ref == attempt + ':raw'
                    and capture_commit_ref == attempt + ':capture', 'F14_INGRESS_PUBLICATION_BINDING')
                key = (observed.session_binding.source_snapshot_ref, attempt)
                with self._lock:
                    existing = self._slots.get(key)
                    if existing is not None:
                        _f14_ingress_require_v1(existing['observed'] is observed
                            and existing['raw_record_ref'] == raw_record_ref
                            and existing['capture_commit_ref'] == capture_commit_ref
                            and existing['state'] in ('PENDING', 'RESOLVED')
                            and existing['published_clock'] is not None,
                            'F14_INGRESS_PUBLICATION_OUTCOME_UNKNOWN')
                        return existing['published_clock']
                    slot = dict(observed=observed, raw_record_ref=raw_record_ref,
                        capture_commit_ref=capture_commit_ref, state='OUTCOME_UNKNOWN',
                        published_clock=None, resolution=None, result=None)
                    self._slots[key] = slot
                    slot['state'] = 'PENDING'
                    try:
                        published = self.source_registry._observe_v1(request.grant)
                    except Exception:
                        slot['state'] = 'OUTCOME_UNKNOWN'
                        raise
                    slot['published_clock'] = published
                    return published

    def _bind_resolution_v1(self, observed, snapshot, observation, decision_time, recorded_cutoff):
        entry = self._capture_v1(observed)
        key = (observed.session_binding.source_snapshot_ref, entry[4])
        with self._lock:
            slot = self._slots.get(key)
            _f14_ingress_require_v1(slot is not None and slot['state'] == 'PENDING',
                'F14_INGRESS_PUBLICATION_OUTCOME_UNKNOWN')
            slot['resolution'] = (snapshot, observation, observed.session_binding, decision_time, recorded_cutoff)

    def resolve_committed_private_observation_v1(self, snapshot, observation, source_binding,
            decision_time, recorded_cutoff):
        from .persistence import PrivateEvidenceReadSnapshotV1
        _f14_ingress_require_v1(type(snapshot) is PrivateEvidenceReadSnapshotV1,
            'F14_INGRESS_COMMITTED_SNAPSHOT')
        with self.source_registry._lock:
            with self._lock:
                matches = [slot for slot in self._slots.values() if slot['resolution'] is not None
                    and slot['resolution'][0] is snapshot and slot['resolution'][1] is observation
                    and slot['resolution'][2] is source_binding
                    and slot['resolution'][3:] == (decision_time, recorded_cutoff)]
                _f14_ingress_require_v1(len(matches) == 1, 'F14_INGRESS_COMMITTED_SNAPSHOT')
                slot = matches[0]
                entry = self._capture_v1(slot['observed'])
                self.source_registry._validate_grant_v1(entry[2].grant, entry[2].operation)
                _f14_ingress_require_v1(slot['state'] in ('PENDING', 'RESOLVED')
                    and observation.get('state') == 'PRIVATE_EVIDENCE_CHAIN_CONFORMANCE_ONLY'
                    and all(value is False for value in observation.values() if type(value) is bool),
                    'F14_INGRESS_PUBLICATION_OUTCOME_UNKNOWN')
                if slot['state'] == 'PENDING':
                    slot['result'] = _f14_freeze_v1(_f14_plain_v1(observation))
                    slot['state'] = 'RESOLVED'
                return _f14_freeze_v1(_f14_plain_v1(slot['result']))


# Detached value algorithms share the original native arithmetic owners.
import copy as _probability_copy_v1
from dataclasses import asdict as _probability_asdict_v1
from fractions import Fraction as _ProbabilityFractionV1
from .models import (
    ProbabilityProducerScopeV1, _ProbabilityMaturityClusterV1, _ProbabilityWindowRequestV1,
    _ProbabilityAdmissionModelV1, _ProbabilityAdmissionCatalogV1, _ProbabilityAdmissionResultV1,
    _ProbabilityAdmissionSnapshotV1, _ProbabilityAdmissionLimitsV1, _ProbabilityBinaryDriftFamilyV1,
    _probability_require_v1, _probability_projection_text_v1, _probability_projection_integer_v1,
    _probability_projection_names_v1,
)
from .model_risk import _derive_probability_window_v1
from .serialization import _native_strict_json as _probability_json_data_v1, _bounded_probability_json_v1
from .implementation_registry import (
    _probability_validate_model_v1, _probability_functional_scalar_v1,
    _probability_bootstrap_bank_v1, _derive_probability_drift_result_v1,
    _probability_cluster_functional_bank_v1, _fit_probability_calibration_diagnostic_v1,
    _probability_model_predict_v1, _compile_probability_binary_drift_family_v1,
    _ProbabilityNumericalFailureV1, compute_math_08_brier_score, compute_math_09_log_loss,
)

_PROBABILITY_ADMISSION_INTENT_FIELDS_V1 = frozenset((
    'request_id', 'receipt_id', 'scope', 'expected_head_ref', 'expected_sequence',
    'expected_high_watermark', 'selection_cutoff_ns', 'result_ref',
))
_PROBABILITY_ORIGINAL_FAILURE_REASONS_V1 = frozenset(
    'NOT_EXECUTED_ORIGINAL_' + partition + '_' + reason
    for partition in ('R', 'W') for reason in (
        'FUNCTIONAL_UNDERFLOW', 'FUNCTIONAL_OVERFLOW', 'CLASS_ABSENT', 'RANK_DEFICIENT',
        'COMPLETE_SEPARATION', 'QUASI_SEPARATION', 'FIT_NUMERIC_FAILURE',
        'FIT_NOT_CONVERGED', 'FIT_OUTPUT_INVALID', 'FIT_EXPORT_PARITY',
    )
)


def _probability_admission_failure_v1(detail):
    from .errors import ContractValidationError
    return ContractValidationError(ReasonCode.SCHEMA_MISMATCH, detail)


def _probability_canonical_data_v1(value):
    return _bounded_probability_json_v1(value, max_bytes=1048576)


@contextmanager
def _probability_owned_context_v1(manager):
    """Retain body failure even when an injected owner's exit suppresses it."""
    body_error = exit_error = None
    completed = False
    try:
        with manager as value:
            try:
                yield value
                completed = True
            except BaseException as error:
                body_error = error
                raise
    except BaseException as error:
        exit_error = error
    errors = []
    for error in (body_error, exit_error):
        if error is not None and not any(error is prior for prior in errors):
            errors.append(error)
    if len(errors) == 1:
        raise errors[0]
    if errors:
        raise BaseExceptionGroup("probability owned body and exit failures", errors)
    _probability_require_v1(completed, "PROBABILITY_CONTEXT_BODY_INCOMPLETE")


class _ProbabilityDependencyFenceV1:
    """Bounded process-local custody over an already accepted source cut.

    Trusted composition supplies the authentic stream/baseline/checkpoint and
    explicit capacity. Construction does not authenticate those inputs or
    qualify cross-process delivery. Public computation requests cannot bind it.
    """

    def __init__(self, *, persistence, issuer_resolver, scope, issuer_snapshot,
                 source_issuer_ref, stream_ref, baseline_ref, baseline_ordinal,
                 baseline_invalidated_refs, cut, max_prepared, max_pending, max_records,
                 initial_latch, input_artifacts=None, artifact_writer=None, construction_inputs=None):
        from .agent_policy import AgentCapabilityResolverV1
        from .models import _ProbabilityRevocationCutV1
        from .persistence import PersistenceAdapterV1
        need = _probability_require_v1
        need(isinstance(persistence, PersistenceAdapterV1) and type(issuer_resolver) is AgentCapabilityResolverV1 and
             type(scope) is ProbabilityProducerScopeV1 and type(cut) is _ProbabilityRevocationCutV1,
             "PROBABILITY_FENCE_OWNERS")
        for bound in (max_prepared, max_pending, max_records):
            _probability_projection_integer_v1(bound, "PROBABILITY_FENCE_CAPACITY", 1)
        for ref in (source_issuer_ref, stream_ref, baseline_ref):
            _probability_projection_text_v1(ref, "PROBABILITY_STREAM_IDENTITY")
        _probability_projection_integer_v1(baseline_ordinal, "PROBABILITY_BASELINE_ORDINAL")
        _probability_projection_names_v1(baseline_invalidated_refs, "PROBABILITY_BASELINE_INVALIDATIONS", empty=True)
        view = issuer_resolver._probability_last_issuer_view_v1
        need(type(view) is dict and view["snapshot"] is issuer_snapshot and
             view["reader"] is issuer_resolver.probability_issuer_reader and
             view["policy"] is issuer_resolver.policy_store.snapshot and
             any(request.role == "SOURCE_RIGHTS" and request.scope == scope and
                 request.issuer_ref == source_issuer_ref and index in view["admissions"] and
                 cut.valid_until_ns <= view["admissions"][index].valid_until_ns
                 for index, request in enumerate(view["requests"])),
             "PROBABILITY_ORIGINAL_SOURCE_ISSUER_VIEW")
        need(getattr(issuer_resolver, "_probability_source_fence_v1", None) is None and
             getattr(persistence, "_probability_preappend_guard_v1", None) is None, "PROBABILITY_FENCE_ALREADY_BOUND")
        need(cut.stream_ordinal >= baseline_ordinal and set(baseline_invalidated_refs) <= set(cut.invalidated_refs),
             "PROBABILITY_BASELINE_CLOSURE")
        self.persistence, self.issuer_resolver, self.scope = persistence, issuer_resolver, scope
        self.reader, self.policy = view["reader"], view["policy"]
        self._source_view_v1 = view
        self.process_ref, self.policy_epoch = issuer_snapshot.process_ref, issuer_snapshot.policy_epoch
        self.source_issuer_ref, self.stream_ref, self.baseline_ref = source_issuer_ref, stream_ref, baseline_ref
        self.baseline_ordinal, self.baseline_invalidated_refs = baseline_ordinal, baseline_invalidated_refs
        self.cut, self.generation = cut, scope.generation
        self._scope_fields_v1 = tuple(getattr(scope, name) for name in scope.__dataclass_fields__)
        self._cut_fields_v1 = tuple(getattr(cut, name) for name in cut.__dataclass_fields__)
        self.max_prepared, self.max_pending, self.max_records = max_prepared, max_pending, max_records
        self._process_id = os.getpid()
        self._lock = threading.RLock()
        self._last_ns = cut.checked_ns
        self._pending_notices = {}
        self._overflow = False
        self._source_synchronized_v1 = True
        self._uncertain = {}
        self._reserved_result_refs_v1 = {}
        self._registrations = {}
        self._active_append = None
        self._model_admission_v1 = None
        # Original source projections belong to trusted composition. No public
        # request, locator, provider discovery or synthetic fallback selects them.
        self._construction_inputs_v1 = construction_inputs
        need(type(initial_latch) is bool, "PROBABILITY_ACCEPTED_GENESIS_LATCH")
        self._initial_latch_v1 = initial_latch
        if input_artifacts is not None:
            need(type(input_artifacts) in (dict, MappingProxyType) and 3 <= len(input_artifacts) <= 4,
                 "PROBABILITY_INPUT_ARTIFACT_HANDLES")
            for ref in input_artifacts:
                _probability_projection_text_v1(ref, "PROBABILITY_INPUT_ARTIFACT_ID")
            input_artifacts = MappingProxyType(dict(input_artifacts))
        self._input_artifacts_v1 = input_artifacts
        self._artifact_writer_v1 = artifact_writer
        self._check_v1(original_cut=cut, dependency_refs=(), evaluated_ns=time.time_ns())
        issuer_resolver._probability_source_fence_v1 = self
        persistence._probability_preappend_guard_v1 = self._append_guard_v1

    @contextmanager
    def _owned_v1(self):
        _probability_require_v1(os.getpid() == self._process_id and self._lock.acquire(blocking=False),
                                "PROBABILITY_DEPENDENCY_FENCE_BUSY")
        try:
            yield
        finally:
            self._lock.release()

    def _check_v1(self, *, original_cut, dependency_refs, evaluated_ns, deadline_ns=None, allow_uncertain=False):
        from .agent_policy import _probability_issuer_pin_v1
        from .models import _probability_ns_v1
        need = _probability_require_v1
        _probability_ns_v1(evaluated_ns)
        need(tuple(getattr(self.scope, name) for name in self.scope.__dataclass_fields__) == self._scope_fields_v1 and
             tuple(getattr(self.cut, name) for name in self.cut.__dataclass_fields__) == self._cut_fields_v1,
             "PROBABILITY_ORIGINAL_SOURCE_FIELDS_CHANGED")
        need(os.getpid() == self._process_id and self.reader is self.issuer_resolver.probability_issuer_reader and
             self.policy is self.issuer_resolver.policy_store.snapshot and original_cut is self.cut,
             "PROBABILITY_SOURCE_CUT_REPLACED")
        source_view = self._source_view_v1
        need(_probability_issuer_pin_v1(source_view["requests"], source_view["snapshot"]) == source_view["pin"] and
             source_view["reader"] is self.reader and source_view["policy"] is self.policy and
             evaluated_ns < source_view["snapshot"].valid_until_ns,
             "PROBABILITY_ORIGINAL_SOURCE_ISSUER_CHANGED")
        if evaluated_ns < self._last_ns or not self.cut.checked_ns <= evaluated_ns < self.cut.valid_until_ns:
            raise FreshnessError(ReasonCode.FRESHNESS_VIOLATION, "PROBABILITY_SOURCE_CUT_EXPIRED_OR_CLOCK_REGRESSED")
        need(self._source_synchronized_v1 and not self._pending_notices and not self._overflow and (allow_uncertain or not self._uncertain),
             "PROBABILITY_SOURCE_DELIVERY_OR_COMMIT_PENDING")
        need(not set(dependency_refs).intersection(self.cut.invalidated_refs), "PROBABILITY_SOURCE_DEPENDENCY_INVALIDATED")
        if deadline_ns is not None:
            _probability_projection_integer_v1(deadline_ns, "PROBABILITY_MONOTONIC_DEADLINE", 1)
            need(time.monotonic_ns() < deadline_ns, "PROBABILITY_PREPARATION_DEADLINE")
        self._last_ns = evaluated_ns

    def _check_snapshot_v1(self, snapshot, *, issuer_snapshot, original_cut, dependency_refs, deadline_ns):
        need = _probability_require_v1
        self._check_v1(original_cut=original_cut, dependency_refs=dependency_refs,
                       evaluated_ns=time.time_ns(), deadline_ns=deadline_ns)
        need(snapshot.scope == self.scope and len(snapshot.revocation_records) <= self.max_records and
             (issuer_snapshot.policy_epoch, issuer_snapshot.process_ref) == (self.policy_epoch, self.process_ref),
             "PROBABILITY_APPLIED_SOURCE_EPOCH")
        invalidated = list(self.baseline_invalidated_refs)
        ordinal, head = self.baseline_ordinal, None
        for record in snapshot.revocation_records:
            p, b = record.typed_payload, record.typed_payload.body
            need((b["issuer_ref"], b["stream_ref"], b["baseline_ref"], b["stream_ordinal"]) ==
                 (self.source_issuer_ref, self.stream_ref, self.baseline_ref, ordinal + 1), "PROBABILITY_SOURCE_STREAM_GAP")
            need(p.available_ns <= self.cut.checked_ns <= snapshot.read_completed_ns, "PROBABILITY_SOURCE_CHECKPOINT_PRECEDES_APPLICATION")
            ordinal, head = b["stream_ordinal"], record.record_id
            invalidated.extend(b["invalidated_dependency_refs"])
        need((ordinal, head) == (self.cut.stream_ordinal, self.cut.head_ref) and
             tuple(sorted(set(invalidated))) == self.cut.invalidated_refs and
             set(self.cut.invalidated_refs) <= set(issuer_snapshot.invalidated_refs), "PROBABILITY_SOURCE_CUT_NOT_COMPLETE")

    def _register_v1(self, value, *, kind, view, dependency_refs, valid_until_ns, metadata, value_node_limit):
        from .agent_policy import _probability_issuer_pin_v1
        need = _probability_require_v1
        with self._owned_v1():
            self._check_v1(original_cut=self.cut, dependency_refs=dependency_refs, evaluated_ns=time.time_ns())
            need((view is self.issuer_resolver._probability_last_issuer_view_v1 or
                  any(entry["view"] is view and entry["kind"] == "PREDICTION" for entry in self._registrations.values())) and
                 view["reader"] is self.reader and view["policy"] is self.policy and
                 len(self._registrations) < self.max_prepared and id(value) not in self._registrations,
                 "PROBABILITY_ORIGINAL_REGISTRATION_CAPACITY")
            need(time.time_ns() < valid_until_ns <= self.cut.valid_until_ns, "PROBABILITY_PREPARED_LIFETIME")
            need(_probability_issuer_pin_v1(view["requests"], view["snapshot"]) == view["pin"] and
                 valid_until_ns <= view["snapshot"].valid_until_ns,
                 "PROBABILITY_ORIGINAL_REGISTERED_ISSUER_CHANGED")
            fields = tuple(getattr(value, name) for name in value.__dataclass_fields__)
            entry = {"object": value, "fields": fields, "kind": kind, "cut": self.cut, "view": view,
                     "dependencies": dependency_refs, "expiry": valid_until_ns, "metadata": metadata,
                     "reader": self.reader, "policy": self.policy, "last_ns": self._last_ns,
                     "value_node_limit": value_node_limit,
                     "value_pin": _probability_construction_pin_v1(value, max_nodes=value_node_limit)}
            self._registrations[id(value)] = entry
            return entry

    def _registered_v1(self, value, *, kind, evaluated_ns):
        from .agent_policy import _probability_issuer_pin_v1
        need = _probability_require_v1
        entry = self._registrations.get(id(value))
        need(entry is not None and entry["object"] is value and entry["kind"] == kind and
             tuple(getattr(value, name) for name in value.__dataclass_fields__) == entry["fields"] and
             _probability_construction_pin_v1(value, max_nodes=entry["value_node_limit"]) == entry["value_pin"],
             "PROBABILITY_ORIGINAL_OBJECT_REQUIRED")
        self._check_v1(original_cut=entry["cut"], dependency_refs=entry["dependencies"], evaluated_ns=evaluated_ns)
        need(entry["last_ns"] <= evaluated_ns < entry["expiry"] and
             entry["reader"] is self.reader and entry["policy"] is self.policy,
             "PROBABILITY_REGISTERED_OBJECT_STALE")
        view = entry["view"]
        need(_probability_issuer_pin_v1(view["requests"], view["snapshot"]) == view["pin"] and
             evaluated_ns < view["snapshot"].valid_until_ns,
             "PROBABILITY_ORIGINAL_REGISTERED_ISSUER_CHANGED")
        entry["last_ns"] = evaluated_ns
        return entry

    def _release_v1(self, value):
        with self._owned_v1():
            entry = self._registrations.get(id(value))
            _probability_require_v1(entry is not None and entry["object"] is value and not self._active_append and
                                    not self._uncertain, "PROBABILITY_RELEASE_OWNERSHIP")
            del self._registrations[id(value)]

    def _retain_notice_v1(self, notice):
        from .models import _ProbabilityRevocationNoticeV1
        need = _probability_require_v1
        with self._owned_v1():
            need(type(notice) is _ProbabilityRevocationNoticeV1 and
                 (notice.scope, notice.issuer_ref, notice.stream_ref) == (self.scope, self.source_issuer_ref, self.stream_ref),
                 "PROBABILITY_NOTICE_SCOPE")
            need(self._active_append is None, "PROBABILITY_DEPENDENCY_FENCE_BUSY")
            prior = self._pending_notices.get(notice.notice_id)
            if prior is not None:
                need(prior is notice or prior == notice, "PROBABILITY_NOTICE_IDEMPOTENCY_CONFLICT")
                return
            if len(self._pending_notices) >= self.max_pending:
                self._overflow = True
                need(False, "PROBABILITY_PENDING_NOTICE_CAPACITY")
            # A pending delivery blocks use immediately, before durable acknowledgement.
            self._pending_notices[notice.notice_id] = notice

    def _append_guard_v1(self, transaction, record):
        from .receipts import _probability_control_projection_v1
        need = _probability_require_v1
        issued = self._active_append
        need(issued is not None and transaction is issued["transaction"] and
             transaction is self.persistence._active_transaction and transaction.is_active,
             "PROBABILITY_ISSUED_APPEND_CONTEXT_REQUIRED")
        if issued.get("delivery") is not None:
            self._check_delivery_v1(issued)
        else:
            self._check_v1(original_cut=issued["cut"], dependency_refs=issued["dependencies"],
                           evaluated_ns=time.time_ns(), deadline_ns=issued["deadline"])
        need(time.time_ns() < issued["expiry"] and any(record is row for row in issued["records"]),
             "PROBABILITY_ORIGINAL_APPEND_RECORD")
        need(_bounded_probability_json_v1(_probability_control_projection_v1(record), max_bytes=1048576) ==
             issued["canonical"][record.record_id], "PROBABILITY_APPEND_RECORD_CHANGED")


    def _check_delivery_v1(self, issued):
        view = issued["entry"]["view"]
        now = time.time_ns()
        need = _probability_require_v1
        notice = issued["delivery"]
        need(self._pending_notices.get(notice.notice_id) is notice and os.getpid() == self._process_id and
             view["reader"] is self.reader is self.issuer_resolver.probability_issuer_reader and
             view["policy"] is self.policy is self.issuer_resolver.policy_store.snapshot,
             "PROBABILITY_REVOCATION_ORIGINAL_DELIVERY")
        need(self._last_ns <= now < issued["expiry"] and time.monotonic_ns() < issued["deadline"],
             "PROBABILITY_REVOCATION_DELIVERY_EXPIRED")
        self._last_ns = now

    def _rebind_cut_v1(self, *, cut, committed_snapshot, issuer_snapshot):
        """Accept a new original source checkpoint only after full applied-history equality."""
        from .models import _ProbabilityRevocationCutV1
        need = _probability_require_v1
        with self._owned_v1():
            view = self.issuer_resolver._probability_last_issuer_view_v1
            need(type(cut) is _ProbabilityRevocationCutV1 and view is not None and view["snapshot"] is issuer_snapshot and
                 view["reader"] is self.reader and view["policy"] is self.policy and
                 self._active_append is None and not self._uncertain and not self._pending_notices and not self._overflow,
                 "PROBABILITY_SOURCE_REBIND_OWNERSHIP")
            need(any(request.role == "SOURCE_RIGHTS" and request.scope == self.scope and
                     request.issuer_ref == self.source_issuer_ref and index in view["admissions"] and
                     cut.valid_until_ns <= view["admissions"][index].valid_until_ns
                     for index, request in enumerate(view["requests"])), "PROBABILITY_SOURCE_REBIND_ISSUANCE")
            need(cut.checked_ns >= self._last_ns and set(self.cut.invalidated_refs) <= set(cut.invalidated_refs) and
                 cut is not self.cut, "PROBABILITY_SOURCE_REBIND_MONOTONICITY")
            previous, previous_fields, previous_view = self.cut, self._cut_fields_v1, self._source_view_v1
            self.cut = cut
            self._cut_fields_v1 = tuple(getattr(cut, name) for name in cut.__dataclass_fields__)
            self._source_view_v1 = view
            self._source_synchronized_v1 = True
            try:
                self._check_snapshot_v1(committed_snapshot, issuer_snapshot=issuer_snapshot, original_cut=cut,
                    dependency_refs=(), deadline_ns=None)
            except BaseException:
                self.cut, self._cut_fields_v1 = previous, previous_fields
                self._source_view_v1 = previous_view
                self._source_synchronized_v1 = False
                raise


def _reconstruct_probability_state_v1(*, initial, snapshot, max_catalog_rows):
    """Reconstruct only this scoped native publication chain from accepted genesis."""
    from .receipts import _validate_probability_control_spine_v1
    state = _probability_copy_v1.deepcopy(initial)
    requests, receipts = set(), set()
    for record in snapshot.publication_records:
        _validate_probability_control_spine_v1(record)
        p, b = record.typed_payload, record.typed_payload.body
        _probability_require_v1(p.scope == snapshot.scope and record.record_id not in receipts and b["request_id"] not in requests,
                                "PROBABILITY_PUBLICATION_CHAIN_IDENTITY")
        rows = tuple(_ProbabilityMaturityClusterV1(**dict(row)) for row in b["selected_rows"])
        request = _ProbabilityWindowRequestV1(b["request_id"], record.record_id, p.scope, b["expected_head_ref"],
            b["expected_sequence"], b["expected_high_watermark"], b["kind"], b["cutoff_ns"], b["catalog_ref"], rows,
            b["family_result"], p.dependency_refs, b["reason"])
        derived = _derive_probability_window_v1(state, request, window_size=200, max_catalog_rows=max_catalog_rows)
        _probability_require_v1(derived["record"] is not None and record.sequence == derived["state"]["sequence"] and
            _probability_canonical_data_v1(derived["record"]["after"]) == _probability_canonical_data_v1(b["after"]),
            "PROBABILITY_PUBLICATION_RECONSTRUCTION_MISMATCH")
        state = derived["state"]
        requests.add(b["request_id"]); receipts.add(record.record_id)
    return state


def _probability_check_receipt_projection_v1(ancestry, snapshot, limits):
    expected = _probability_receipt_expected_claims_v1(snapshot, limits)
    records = {record.typed_payload.body["role"]: record for record in ancestry if
               record.typed_payload.control_kind == "ACCEPTANCE_RECEIPT"}
    need = _probability_require_v1
    need(set(records) == set(expected), "PROBABILITY_EXPECTED_CLAIM_ROSTER")
    for role, claims in expected.items():
        record = records[role]
        actual = dict(record.typed_payload.body["claims"])
        if role in ("MODEL_BUILD", "COMPUTATION"):
            start, end = actual.pop("started_ns"), actual.pop("completed_ns")
            need(start <= end <= claims["artifact_available_ns"] and end <= record.typed_payload.body["observed_ns"],
                 "PROBABILITY_ACTUAL_RUN_CHRONOLOGY")
            if role == "MODEL_BUILD":
                floor = max(snapshot.model.reference_cutoff_ns, records["SOURCE_RIGHTS"].typed_payload.available_ns,
                            records["ENVIRONMENT"].typed_payload.available_ns)
            else:
                floor = max(snapshot.result.selection_cutoff_ns, snapshot.model.available_ns,
                            *(records[parent].typed_payload.available_ns for parent in _PROBABILITY_ACCEPTANCE_PARENTS_V1[role]))
                if len(ancestry) == 11:
                    floor = max(floor, ancestry[-2].typed_payload.available_ns)
            need(floor <= start, "PROBABILITY_ACTUAL_RUN_PRECEDES_INPUT")
        need(_probability_canonical_data_v1(actual) == _probability_canonical_data_v1(claims),
             "PROBABILITY_ACCEPTED_CLAIM_PROJECTION")
    need(snapshot.catalog.complete_through_ns <= records["CATALOG"].typed_payload.body["observed_ns"] and
         snapshot.model.available_ns <= records["MODEL_REVIEW"].typed_payload.body["observed_ns"],
         "PROBABILITY_REVIEW_OR_CATALOG_CHRONOLOGY")


def _resolve_probability_admission_snapshot_v1(*, read_request, intent, persistence, issuer_resolver, budget):
    """Detach exact committed inputs and their accepted original issuer ancestry."""
    from .agent_policy import AgentCapabilityResolverV1
    from .errors import OwnerAdapterError
    from .models import _ProbabilityMaterializationReadBudgetV1
    from .model_risk import _probability_genesis_v1
    from .persistence import (ProbabilityProducerReadRequestV1, _probability_combined_read_budget_v1,
                              _probability_charge_read_v1)
    from .receipts import _probability_control_projection_v1
    from .serialization import _decode_probability_input_object_v1
    need = _probability_require_v1
    need(type(read_request) is ProbabilityProducerReadRequestV1 and read_request.purpose in
         ("CONSTRUCT_CANDIDATE", "MATERIALIZE_CURRENT") and type(issuer_resolver) is AgentCapabilityResolverV1 and
         type(budget) is _ProbabilityMaterializationReadBudgetV1, "PROBABILITY_MATERIALIZATION_REQUEST")
    fence = issuer_resolver._probability_source_fence_v1
    need(type(fence) is _ProbabilityDependencyFenceV1 and fence.persistence is persistence and fence.scope == read_request.scope,
         "PROBABILITY_MATERIALIZATION_FENCE")
    artifacts = fence._input_artifacts_v1
    if artifacts is None:
        raise OwnerAdapterError(ReasonCode.OWNER_DATA_MISSING, "PROBABILITY_ORIGINAL_INPUT_ARTIFACTS_UNAVAILABLE")
    scope, original_cut = read_request.scope, fence.cut
    deadline = read_request.limits.deadline_monotonic_ns
    fence._check_v1(original_cut=original_cut, dependency_refs=(), evaluated_ns=time.time_ns(), deadline_ns=deadline)
    with _probability_combined_read_budget_v1(persistence, scope=scope, max_total_bytes=budget.max_total_bytes):
        with _probability_owned_context_v1(persistence.load_committed_probability_producer_state_v1(read_request)) as discovery:
            discovered = {ref: _bounded_probability_json_v1(_probability_control_projection_v1(record),
                          max_bytes=read_request.limits.max_frame_bytes) for ref, record in discovery.records_by_ref.items()}
            issuer_requests = tuple(dict.fromkeys(_probability_record_issuer_request_v1(record)
                for record in discovery.records_by_ref.values() if record.typed_payload.control_kind == "ACCEPTANCE_RECEIPT"))
        with issuer_resolver._resolve_probability_issuer_context_v1(issuer_requests, evaluated_ns=time.time_ns()) as issuer_snapshot:
            with _probability_owned_context_v1(persistence.load_committed_probability_producer_state_v1(read_request)) as committed:
                need(set(discovered) == set(committed.records_by_ref), "PROBABILITY_DISCOVERY_IDENTITIES_CHANGED")
                for ref, canonical in discovered.items():
                    need(_bounded_probability_json_v1(_probability_control_projection_v1(committed.records_by_ref[ref]),
                         max_bytes=read_request.limits.max_frame_bytes) == canonical, "PROBABILITY_DISCOVERY_BYTES_CHANGED")
                admissions = tuple(issuer_resolver._admit_probability_issuer_v1(request, trusted_snapshot=issuer_snapshot)
                                   for request in issuer_requests)
                root = _probability_selected_record_v1(committed, read_request.binding_ref, scope, "INPUT_BINDING")
                descriptors = root.typed_payload.body["objects"]
                require_result = len(descriptors) == 4
                ancestry, dependencies, expiry = _join_probability_acceptance_v1(scope, root.record_id,
                    committed_snapshot=committed, issuer_requests=issuer_requests, issuer_snapshot=issuer_snapshot,
                    issuer_admissions=admissions, evaluated_ns=time.time_ns(), require_result=require_result)
                need(root.typed_payload.body["owner_epoch"] == fence.policy_epoch and
                     len(committed.publication_records) <= budget.max_history_records, "PROBABILITY_MATERIALIZATION_EPOCH_OR_HISTORY")
                fence._check_snapshot_v1(committed, issuer_snapshot=issuer_snapshot, original_cut=original_cut,
                                         dependency_refs=dependencies, deadline_ns=deadline)
        view = issuer_resolver._probability_last_issuer_view_v1
        del discovery, discovered
        need(sum(row["frame_count"] for row in descriptors) <= budget.max_frames, "PROBABILITY_INPUT_FRAME_BUDGET")
        decoded, environment = {}, None
        for member in descriptors:
            fence._check_v1(original_cut=original_cut, dependency_refs=dependencies, evaluated_ns=time.time_ns(), deadline_ns=deadline)
            frames = artifacts.get(member["object_ref"])
            if frames is None:
                raise OwnerAdapterError(ReasonCode.OWNER_DATA_MISSING, "PROBABILITY_INPUT_ARTIFACT_MISSING")
            need(type(frames) is tuple and len(frames) == member["frame_count"] and all(type(frame) is bytes for frame in frames) and
                 sum(map(len, frames)) == member["byte_count"], "PROBABILITY_INPUT_ARTIFACT_DENOMINATOR")
            _probability_charge_read_v1(persistence, scope, member["byte_count"])
            value, env = _decode_probability_input_object_v1(member["role"], frames, budget)
            decoded[member["role"]] = value
            if member["role"] == "POLICY":
                environment = env
            need(artifacts is fence._input_artifacts_v1 and frames is artifacts[member["object_ref"]],
                 "PROBABILITY_INPUT_ARTIFACT_OWNER_CHANGED")
        model, catalog, limits = decoded["MODEL"], decoded["CATALOG"], decoded["POLICY"]
        result = decoded.get("RESULT")
        refs = {row["role"]: row["object_ref"] for row in descriptors}
        need(model.scope == catalog.scope == scope and (result is None or result.scope == scope) and
             refs["MODEL"] == scope.model_artifact_ref and refs["POLICY"] == scope.policy_ref and
             refs["CATALOG"] == catalog.catalog_ref and (result is None or refs["RESULT"] == result.result_ref == intent["result_ref"]),
             "PROBABILITY_MATERIALIZED_OBJECT_IDENTITY")
        need(catalog.owner_epoch == fence.policy_epoch and (result is None or result.owner_epoch == fence.policy_epoch) and
             model.available_ns <= root.typed_payload.available_ns and
             (result is None or result.available_ns <= root.typed_payload.available_ns), "PROBABILITY_MATERIALIZED_OBJECT_CUT")
        expiry = min(expiry, model.valid_until_ns, original_cut.valid_until_ns)
        dependencies = tuple(dict.fromkeys((*dependencies, *refs.values(), *model.dependency_refs, *catalog.dependency_refs,
            *((*result.dependency_refs, result.reference_plan_ref, result.current_plan_ref) if result is not None else ()),
            *((model.precision_protocol_ref,) if model.precision_protocol_ref is not None else ()),
            fence.baseline_ref, original_cut.checkpoint_ref)))
        snapshot = _ProbabilityAdmissionSnapshotV1(root.record_id, fence.policy_epoch, committed.read_completed_ns, model,
            catalog, result, environment, original_cut.invalidated_refs, dependencies, expiry)
        _probability_check_receipt_projection_v1(ancestry, snapshot, limits)
        initial = _probability_genesis_v1(scope, reference_clusters=tuple(row.cluster_id for row in model.reference_clusters),
            reference_rows=tuple(ref for row in model.reference_clusters for ref in row.row_ids),
            reference_cutoff_ns=model.reference_cutoff_ns, initial_latch=fence._initial_latch_v1)
        state = _reconstruct_probability_state_v1(initial=initial, snapshot=committed, max_catalog_rows=limits.max_catalog_rows)
        if read_request.purpose == "CONSTRUCT_CANDIDATE":
            _prepare_probability_window_v1(snapshot, intent, state, current_owner_epoch=fence.policy_epoch,
                                           publication_ns=time.time_ns(), limits=limits)
        else:
            _validate_probability_admission_v1(snapshot, intent, state, current_owner_epoch=fence.policy_epoch,
                                               publication_ns=time.time_ns(), limits=limits)
        fence._check_v1(original_cut=original_cut, dependency_refs=dependencies, evaluated_ns=time.time_ns(), deadline_ns=deadline)
        need(time.time_ns() < expiry, "PROBABILITY_MATERIALIZATION_EXPIRED")
        output = {"snapshot": snapshot, "limits": limits, "state": state, "committed_snapshot": committed,
                  "read_request": read_request, "ancestry": ancestry, "source_cut": original_cut,
                  "disposition": "MATERIALIZED_COMMITTED_PROBABILITY_INPUTS", "acceptance_receipt_refs": dependencies,
                  "accepted_source_authenticated": False, "actual_model_fits": 0,
                  "model_use_authorized": False, "current_use_eligible": False}
    fence._check_v1(original_cut=original_cut, dependency_refs=dependencies, evaluated_ns=time.time_ns(), deadline_ns=deadline)
    need(time.time_ns() < expiry, "PROBABILITY_MATERIALIZATION_EXPIRED_AT_RETURN")
    fence._model_admission_v1 = model
    fence._register_v1(snapshot, kind="MATERIALIZATION", view=view, dependency_refs=dependencies,
        valid_until_ns=expiry, value_node_limit=budget.max_total_bytes,
        metadata={"materialization": output, "intent": _probability_canonical_data_v1(intent),
                  "state": _probability_canonical_data_v1(state)})
    return output


def _resolve_committed_prediction_v1(
    *, scope, read_request, expected_model, prediction_input_lock_id, feature_names, requests,
    persistence, issuer_resolver, expected_protocol_bindings, artifact_reader,
    existing_conditions, limits,
):
    from .agent_policy import AgentCapabilityResolverV1
    from .errors import OwnerAdapterError
    from .evidence import ComputationEvidenceServiceV1
    from .models import (ProbabilityPredictionReadRequestV1, ProbabilityPredictionReadLimitsV1,
                         ProbabilityPredictionArtifactReadV1, PreparedProbabilityPredictionV1)
    from .persistence import _probability_combined_read_budget_v1, _probability_charge_read_v1
    from .receipts import _probability_control_projection_v1
    from .serialization import _decode_prediction_artifact_v1
    from .implementation_registry import _probability_read_locked_prediction_bank_v1

    need = _probability_require_v1
    need(type(issuer_resolver) is AgentCapabilityResolverV1 and
         type(read_request) is ProbabilityPredictionReadRequestV1 and read_request.scope == scope and
         read_request.purpose == "ADMIT_COMMITTED_PREDICTION" and
         type(limits) is ProbabilityPredictionReadLimitsV1 and read_request.limits is limits.metadata_limits,
         "PROBABILITY_PREDICTION_READ_BINDING")
    if artifact_reader is None or not callable(getattr(artifact_reader, "open_prediction_artifact_v1", None)):
        raise OwnerAdapterError(ReasonCode.OWNER_DATA_MISSING, "PROBABILITY_ARTIFACT_READER_UNAVAILABLE")
    fence = issuer_resolver._probability_source_fence_v1
    need(type(fence) is _ProbabilityDependencyFenceV1 and fence.persistence is persistence and fence.scope == scope,
         "PROBABILITY_PREDICTION_FENCE_REQUIRED")
    admitted_model = fence._model_admission_v1
    need(type(admitted_model) is _ProbabilityAdmissionModelV1 and admitted_model.scope == scope,
         "PROBABILITY_ACCEPTED_MODEL_REQUIRED")
    model_text = _bounded_probability_json_v1(expected_model, max_bytes=limits.metadata_limits.max_frame_bytes)
    need(model_text == admitted_model.export_text and feature_names == admitted_model.feature_names,
         "PROBABILITY_EXPECTED_ORIGINAL_MODEL")
    original_cut = fence.cut
    deadline = limits.metadata_limits.deadline_monotonic_ns
    fence._check_v1(original_cut=original_cut, dependency_refs=admitted_model.dependency_refs,
                    evaluated_ns=time.time_ns(), deadline_ns=deadline)
    need(type(requests) is tuple and bool(requests) and type(feature_names) is tuple and bool(feature_names),
         "PROBABILITY_REQUEST_ROSTER")
    request_keys = []
    for row in requests:
        need(type(row) is tuple and len(row) == 2 and type(row[1]) is tuple and len(row[1]) == len(feature_names) and
             all(type(value) is float and math.isfinite(value) for value in row[1]), "PROBABILITY_REQUEST_FEATURES")
        _probability_projection_text_v1(row[0], "PROBABILITY_QUERY_ID")
        request_keys.append((row[0], tuple(value.hex() for value in row[1])))
    _probability_projection_names_v1(tuple(row[0] for row in requests), "PROBABILITY_QUERY_ROSTER")
    with _probability_combined_read_budget_v1(persistence, scope=scope, max_total_bytes=limits.max_total_bytes):
        with _probability_owned_context_v1(persistence.load_committed_probability_producer_state_v1(read_request)) as discovery:
            discovered = {ref: _bounded_probability_json_v1(_probability_control_projection_v1(record),
                          max_bytes=limits.metadata_limits.max_frame_bytes) for ref, record in discovery.records_by_ref.items()}
            issuer_requests = tuple(dict.fromkeys(_probability_record_issuer_request_v1(record)
                for record in discovery.records_by_ref.values() if record.typed_payload.control_kind in
                ("ACCEPTANCE_RECEIPT", "PREDICTION_RESULT", "PREDICTION_REVIEW")))
        with issuer_resolver._resolve_probability_issuer_context_v1(issuer_requests, evaluated_ns=time.time_ns()) as issuer_snapshot:
            with _probability_owned_context_v1(persistence.load_committed_probability_producer_state_v1(read_request)) as snapshot:
                need(set(snapshot.records_by_ref) == set(discovered), "PROBABILITY_DISCOVERY_IDENTITIES_CHANGED")
                for ref, canonical in discovered.items():
                    need(_bounded_probability_json_v1(_probability_control_projection_v1(snapshot.records_by_ref[ref]),
                         max_bytes=limits.metadata_limits.max_frame_bytes) == canonical, "PROBABILITY_DISCOVERY_BYTES_CHANGED")
                issuer_admissions = tuple(issuer_resolver._admit_probability_issuer_v1(request, trusted_snapshot=issuer_snapshot)
                                          for request in issuer_requests)
                result = _probability_selected_record_v1(snapshot, read_request.result_ref, scope, "PREDICTION_RESULT")
                review = _probability_selected_record_v1(snapshot, read_request.review_ref, scope, "PREDICTION_REVIEW")
                rp, rb = result.typed_payload, result.typed_payload.body
                roots = tuple(record for ref in rp.dependency_refs if (record := snapshot.records_by_ref.get(ref)) is not None
                              and record.typed_payload.control_kind == "INPUT_BINDING")
                need(len(roots) == 1, "PROBABILITY_RESULT_UNIQUE_INPUT_BINDING")
                evaluated = time.time_ns()
                ancestry, dependencies, expiry = _join_probability_acceptance_v1(scope, roots[0].record_id,
                    committed_snapshot=snapshot, issuer_requests=issuer_requests, issuer_snapshot=issuer_snapshot,
                    issuer_admissions=issuer_admissions, evaluated_ns=evaluated, require_result=False)
                need(set(record.record_id for record in ancestry) <= set(rp.dependency_refs) and
                     max(admitted_model.available_ns, roots[0].typed_payload.available_ns) <= rb["input_available_ns"] and
                     rb["prediction_input_lock_id"] == prediction_input_lock_id, "PROBABILITY_RESULT_INPUT_ANCESTRY")
                for record in snapshot.records_by_ref.values():
                    p = record.typed_payload
                    if p.control_kind not in ("ACCEPTANCE_RECEIPT", "PREDICTION_RESULT", "PREDICTION_REVIEW"):
                        continue
                    admission, context = _probability_join_issuer_v1(record, issuer_requests=issuer_requests,
                        issuer_snapshot=issuer_snapshot, issuer_admissions=issuer_admissions, evaluated_ns=evaluated)
                    dependencies = tuple(dict.fromkeys((*dependencies, record.record_id, *p.dependency_refs,
                                                        *admission.authority_dependency_refs)))
                    expiry = min(expiry, admission.valid_until_ns, p.valid_until_ns)
                    if p.control_kind in ("PREDICTION_RESULT", "PREDICTION_REVIEW"):
                        field = "producer_control_domain_ref" if p.control_kind == "PREDICTION_RESULT" else "reviewer_control_domain_ref"
                        need(p.body[field] == context.control_domain_ref, "PROBABILITY_DECLARED_CONTROL_DOMAIN")
                    if p.control_kind == "ACCEPTANCE_RECEIPT" and "prediction_basis_kind" in p.body["claims"]:
                        claim = p.body["claims"]
                        need(claim["effective_cutoff_ns"] == read_request.effective_cutoff_ns and
                             claim["recorded_cutoff_ns"] == read_request.recorded_cutoff_ns, "PROBABILITY_EXACT_REVIEW_CONTEXT_CUT")
                conditions, review_dependencies, review_expiry = ComputationEvidenceServiceV1._resolve_probability_prediction_review_v1(
                    scope, result, review, basis_request=None, committed_snapshot=snapshot, issuer_admissions=issuer_admissions,
                    expected_protocol_bindings=expected_protocol_bindings, existing_conditions=existing_conditions, evaluated_ns=evaluated)
                dependencies = tuple(dict.fromkeys((*dependencies, *review_dependencies, *admitted_model.dependency_refs,
                    *(getattr(scope, name) for name in scope.__dataclass_fields__ if name != "generation"),
                    fence.baseline_ref, original_cut.checkpoint_ref, rb["artifact_ref"], rb["plan_id"], prediction_input_lock_id)))
                expiry = min(expiry, review_expiry, admitted_model.valid_until_ns, original_cut.valid_until_ns)
                fence._check_snapshot_v1(snapshot, issuer_snapshot=issuer_snapshot, original_cut=original_cut,
                                         dependency_refs=dependencies, deadline_ns=deadline)
        del discovery, discovered
        view = issuer_resolver._probability_last_issuer_view_v1
        fence._check_v1(original_cut=original_cut, dependency_refs=dependencies, evaluated_ns=time.time_ns(), deadline_ns=deadline)
        need(time.time_ns() < expiry, "PROBABILITY_PREDICTION_METADATA_EXPIRED")
        need(rb["artifact_byte_count"] <= limits.max_artifact_bytes and rb["artifact_frame_count"] <= limits.max_frames,
             "PROBABILITY_ARTIFACT_DECLARED_BUDGET")
        _probability_charge_read_v1(persistence, scope, rb["artifact_byte_count"])
        with _probability_owned_context_v1(artifact_reader.open_prediction_artifact_v1(
                artifact_ref=rb["artifact_ref"], scope=scope, max_bytes=rb["artifact_byte_count"],
                max_frames=rb["artifact_frame_count"])) as artifact:
            need(type(artifact) is ProbabilityPredictionArtifactReadV1, "PROBABILITY_ARTIFACT_READ_TYPE")
            artifact.__post_init__()
            need((artifact.artifact_ref, artifact.scope, artifact.byte_count, artifact.frame_count) ==
                 (rb["artifact_ref"], scope, rb["artifact_byte_count"], rb["artifact_frame_count"]), "PROBABILITY_ARTIFACT_IDENTITY")
            need(rp.available_ns <= artifact.observed_ns <= time.time_ns() < artifact.valid_until_ns,
                 "PROBABILITY_ARTIFACT_OBSERVATION")
            artifact_fields = tuple(getattr(artifact, name) for name in artifact.__dataclass_fields__)
            raw = artifact.immutable_bytes
            dependencies = tuple(dict.fromkeys((*dependencies, *artifact.dependency_refs)))
            expiry = min(expiry, artifact.valid_until_ns)
        need(tuple(getattr(artifact, name) for name in artifact.__dataclass_fields__) == artifact_fields and
             artifact.immutable_bytes is raw, "PROBABILITY_ARTIFACT_CHANGED_ON_EXIT")
        fence._check_v1(original_cut=original_cut, dependency_refs=dependencies, evaluated_ns=time.time_ns(), deadline_ns=deadline)
        need(time.time_ns() < expiry, "PROBABILITY_ARTIFACT_EXPIRED_ON_EXIT")
        bank, decoded_frame_count = _decode_prediction_artifact_v1(raw, max_bytes=limits.max_artifact_bytes, max_frames=limits.max_frames)
        need(decoded_frame_count == artifact.frame_count, "PROBABILITY_ARTIFACT_DECODED_FRAME_COUNT")
        need(type(bank) is dict and bank.get("plan_id") == rb["plan_id"] and
             _bounded_probability_json_v1(bank.get("original_model"), max_bytes=limits.metadata_limits.max_frame_bytes) == model_text,
             "PROBABILITY_ARTIFACT_ORIGINAL_MODEL")
        numerical = _probability_read_locked_prediction_bank_v1(bank, input_lock_id=scope.input_lock_ref,
            prediction_input_lock_id=prediction_input_lock_id, feature_names=feature_names, requests=requests)
        blockers = list(review.typed_payload.body["blocker_codes"])
        if numerical["values"] is None:
            blockers.append(ReasonCode.ST12F_MODEL_RISK_VETO)
        for condition in conditions:
            if condition.active and condition.condition_id in ("MISSING_OR_STALE_REQUIRED_EVIDENCE", "INDEPENDENT_REVIEW_NOT_CLOSED"):
                blockers.extend((*condition.reason_codes, ReasonCode.ST12F_MODEL_RISK_VETO))
        blockers = tuple(dict.fromkeys(blockers))
        prepared = PreparedProbabilityPredictionV1("ABSTAIN" if blockers else "SCORE_RESEARCH_ONLY",
            result.record_id, review.record_id, scope.input_lock_ref, prediction_input_lock_id, feature_names,
            tuple(request_keys), None if blockers else numerical["values"], dependencies, snapshot.read_completed_ns,
            expiry, scope.generation, blockers)
        fence._check_v1(original_cut=original_cut, dependency_refs=dependencies, evaluated_ns=time.time_ns(), deadline_ns=deadline)
        need(time.time_ns() < expiry, "PROBABILITY_PREPARED_EXPIRED_AT_RETURN")
    entry = fence._register_v1(prepared, kind="PREDICTION", view=view, dependency_refs=dependencies,
        valid_until_ns=expiry, value_node_limit=limits.max_total_bytes,
        metadata={"scope": scope, "cutoffs": (read_request.effective_cutoff_ns, read_request.recorded_cutoff_ns),
                                        "conditions": conditions, "result": result, "review": review,
                                        "read_snapshot": snapshot, "model": admitted_model})
    try:
        fence._registered_v1(prepared, kind="PREDICTION", evaluated_ns=time.time_ns())
    except BaseException:
        if fence._registrations.get(id(prepared)) is entry:
            del fence._registrations[id(prepared)]
        raise
    return prepared


def _probability_receipt_dependency_binding_v1(snapshot, now):
    """Private detached value construction; accepted source custody is enforced by the calling resolver."""
    _probability_require_v1(type(snapshot) is _ProbabilityAdmissionSnapshotV1, 'ADMISSION_TYPE')
    _probability_projection_integer_v1(now, 'RECEIPT_BINDING_TIME', None)
    refs = _probability_projection_names_v1(snapshot.receipt_dependency_refs, 'RECEIPT_BINDING_REFS', empty=True)
    expiry = snapshot.receipt_valid_until_ns
    if not refs:
        _probability_require_v1(expiry is None, 'RECEIPT_BINDING_PAIR')
        return ()
    _probability_projection_integer_v1(expiry, 'RECEIPT_BINDING_TIME', None)
    _probability_require_v1(snapshot.read_ns < expiry and now < expiry, 'RECEIPT_BINDING_EXPIRED')
    _probability_require_v1(not set(refs).intersection(snapshot.invalidated_refs), 'DEPENDENCY_INVALIDATED')
    return refs

def _prepare_probability_window_v1(snapshot: _ProbabilityAdmissionSnapshotV1, intent: dict, state: dict, *, current_owner_epoch: int, publication_ns: int, limits: _ProbabilityAdmissionLimitsV1) -> tuple[dict, ProbabilityProducerScopeV1, _ProbabilityAdmissionModelV1, _ProbabilityAdmissionCatalogV1, _ProbabilityAdmissionResultV1 | None, int, tuple[str, ...], dict]:
    """Private detached value construction; accepted source custody is enforced by the calling resolver."""

    def encoded(text: str) -> bytes:
        try:
            return text.encode('utf-8', errors='strict')
        except UnicodeError as exc:
            raise _probability_admission_failure_v1('ADMISSION_UTF8') from exc
    _probability_require_v1(type(snapshot) is _ProbabilityAdmissionSnapshotV1 and type(limits) is _ProbabilityAdmissionLimitsV1, 'ADMISSION_TYPE')
    for field in limits.__dataclass_fields__:
        _probability_projection_integer_v1(getattr(limits, field), 'ADMISSION_BUDGET', 1)
    _probability_require_v1(limits.max_model_bytes <= 1048576 and limits.max_record_bytes <= 1048576, 'REFERENCE_PARSER_BUDGET')
    _probability_require_v1(type(intent) is dict and set(intent) == _PROBABILITY_ADMISSION_INTENT_FIELDS_V1, 'INTENT_FIELDS')
    intent = _probability_copy_v1.deepcopy(intent)
    for field in ('request_id', 'receipt_id'):
        _probability_projection_text_v1(intent[field], 'INTENT_ID')
    if intent['result_ref'] is not None:
        _probability_projection_text_v1(intent['result_ref'], 'RESULT_REF')
    _probability_require_v1(type(intent['scope']) is dict and set(intent['scope']) == set(ProbabilityProducerScopeV1.__dataclass_fields__), 'INTENT_SCOPE')
    scope = ProbabilityProducerScopeV1(**intent['scope'])
    if intent['expected_head_ref'] is not None:
        _probability_projection_text_v1(intent['expected_head_ref'], 'HEAD_REF')
    for field in ('expected_sequence', 'expected_high_watermark'):
        _probability_projection_integer_v1(intent[field], 'INTENT_PARENT')
    cutoff = _probability_projection_integer_v1(intent['selection_cutoff_ns'], 'SELECTION_CUTOFF', None)
    for value in (snapshot.owner_epoch, current_owner_epoch):
        _probability_projection_integer_v1(value, 'OWNER_EPOCH')
    _probability_require_v1(snapshot.owner_epoch == current_owner_epoch, 'OWNER_EPOCH_CHANGED')
    _probability_projection_text_v1(snapshot.snapshot_ref, 'SNAPSHOT_REF')
    _probability_projection_integer_v1(snapshot.read_ns, 'READ_TIME', None)
    _probability_projection_integer_v1(publication_ns, 'PUBLICATION_TIME', None)
    _probability_require_v1(cutoff <= snapshot.read_ns <= publication_ns, 'ADMISSION_CLOCK')
    _probability_projection_names_v1(snapshot.invalidated_refs, 'INVALIDATIONS', empty=True)
    receipt_refs = _probability_receipt_dependency_binding_v1(snapshot, publication_ns)
    model, catalog, result = (snapshot.model, snapshot.catalog, snapshot.result)
    _probability_require_v1(type(model) is _ProbabilityAdmissionModelV1 and type(catalog) is _ProbabilityAdmissionCatalogV1, 'DEPENDENCY_TYPES')
    _probability_require_v1(type(model.scope) is ProbabilityProducerScopeV1 and type(catalog.scope) is ProbabilityProducerScopeV1 and (model.scope == catalog.scope == scope), 'DEPENDENCY_SCOPE')
    _probability_projection_names_v1(model.feature_names, 'FEATURE_NAMES')
    _probability_projection_names_v1(model.targets, 'TARGET_NAMES')
    _probability_require_v1(type(model.target_domains) is tuple and all((type(row) is tuple and len(row) == 2 and (type(row[0]) is str) and (type(row[1]) is str) and (row[1] in ('REAL', 'NONNEGATIVE', 'UNIT_INTERVAL')) for row in model.target_domains)) and (tuple((row[0] for row in model.target_domains)) == model.targets), 'TARGET_DOMAIN_ROSTER')
    _probability_require_v1(len(model.targets) <= limits.max_targets, 'TARGET_BUDGET')
    _probability_require_v1(type(model.replicate_count) is int and model.replicate_count in (1000, 5000), 'FROZEN_REPLICATE_COUNT')
    if model.replicate_count == 5000:
        _probability_projection_text_v1(model.precision_protocol_ref, 'PRECISION_PROTOCOL_REQUIRED')
    else:
        _probability_require_v1(model.precision_protocol_ref is None, 'UNEXPECTED_PRECISION_PROTOCOL')
    _probability_projection_names_v1(model.dependency_refs, 'MODEL_DEPENDENCIES')
    for value in (model.reference_cutoff_ns, model.available_ns, model.valid_until_ns):
        _probability_projection_integer_v1(value, 'MODEL_CLOCK', None)
    _probability_require_v1(model.reference_cutoff_ns <= cutoff and model.reference_cutoff_ns <= model.available_ns <= snapshot.read_ns and (publication_ns < model.valid_until_ns), 'MODEL_NOT_CURRENT')
    _probability_require_v1(type(model.export_text) is str, 'MODEL_TEXT')
    artifact = _probability_json_data_v1(encoded(model.export_text), limits.max_model_bytes)
    _probability_validate_model_v1(artifact)
    _probability_require_v1(tuple(artifact['feature_names']) == model.feature_names, 'MODEL_FEATURE_BINDING')
    _probability_projection_text_v1(model.model_kind, 'MODEL_KIND')
    _probability_require_v1(artifact['kind'] == model.model_kind, 'MODEL_TASK_KIND')
    _probability_require_v1(type(snapshot.expected_environment) is tuple and all((type(row) is tuple and len(row) == 2 for row in snapshot.expected_environment)), 'ENVIRONMENT_FIELDS')
    for key, value in snapshot.expected_environment:
        _probability_projection_text_v1(key, 'ENVIRONMENT_KEY')
        _probability_projection_text_v1(value, 'ENVIRONMENT_VALUE')
    _probability_require_v1(len(dict(snapshot.expected_environment)) == len(snapshot.expected_environment) and set(dict(snapshot.expected_environment)) == {'python', 'numpy', 'scipy', 'scikit-learn'} and (artifact['environment'] == dict(snapshot.expected_environment)), 'ENVIRONMENT_MISMATCH')
    _probability_require_v1(type(model.reference_clusters) is tuple and bool(model.reference_clusters) and all((type(row) is _ProbabilityMaturityClusterV1 for row in model.reference_clusters)), 'REFERENCE_COHORT')
    reference_ids = tuple((row.cluster_id for row in model.reference_clusters))
    reference_rows = tuple((rid for row in model.reference_clusters for rid in row.row_ids))
    _probability_projection_names_v1(reference_ids, 'REFERENCE_CLUSTER_IDS')
    _probability_projection_names_v1(reference_rows, 'REFERENCE_ROW_IDS')
    _probability_require_v1(len(reference_rows) <= limits.max_reference_rows, 'REFERENCE_ROW_BUDGET')
    _probability_require_v1(all((row.available_ns <= row.maturity_ns <= model.reference_cutoff_ns for row in model.reference_clusters)), 'REFERENCE_FUTURE_ROW')
    _probability_require_v1(set(reference_rows) == set(artifact['fit_ids']) | set(artifact['calibration_ids']), 'REFERENCE_TRAIN_CALIBRATION_JOIN')
    expected_state = {'scope', 'head_ref', 'sequence', 'high_watermark', 'last_maturity_ns', 'last_cutoff_ns', 'bad_streak', 'green_streak', 'latched', 'used_clusters', 'used_rows'}
    _probability_require_v1(type(state) is dict and set(state) == expected_state, 'STATE_FIELDS')
    _probability_require_v1(type(state['scope']) is dict and set(state['scope']) == set(ProbabilityProducerScopeV1.__dataclass_fields__), 'STATE_SCOPE')
    _probability_require_v1(ProbabilityProducerScopeV1(**state['scope']) == scope, 'STATE_SCOPE')
    if state['head_ref'] is not None:
        _probability_projection_text_v1(state['head_ref'], 'STATE_HEAD')
    for field in ('sequence', 'high_watermark', 'bad_streak', 'green_streak'):
        _probability_projection_integer_v1(state[field], 'STATE_INTEGER')
    _probability_require_v1((state['head_ref'] is None) == (state['sequence'] == 0), 'STATE_HEAD_SEQUENCE')
    _probability_require_v1(state['bad_streak'] <= 2 and state['green_streak'] <= 2 and (not (state['bad_streak'] and state['green_streak'])), 'STATE_STREAK')
    for field in ('last_maturity_ns', 'last_cutoff_ns'):
        _probability_projection_integer_v1(state[field], 'STATE_CLOCK', None)
    _probability_require_v1(type(state['latched']) is bool and type(state['used_clusters']) is list and (type(state['used_rows']) is list), 'STATE_TYPES')
    _probability_require_v1(state['bad_streak'] < 2 or state['latched'], 'STATE_LATCH')
    _probability_projection_names_v1(tuple(state['used_clusters']), 'STATE_CLUSTERS', empty=True)
    _probability_projection_names_v1(tuple(state['used_rows']), 'STATE_ROWS', empty=True)
    _probability_require_v1(set(reference_ids) <= set(state['used_clusters']) and set(reference_rows) <= set(state['used_rows']), 'REFERENCE_EXCLUSION_MISSING')
    _probability_require_v1((intent['expected_head_ref'], intent['expected_sequence'], intent['expected_high_watermark']) == (state['head_ref'], state['sequence'], state['high_watermark']), 'STALE_PARENT')
    _probability_require_v1(cutoff >= state['last_cutoff_ns'], 'CUTOFF_REGRESSION')
    _probability_projection_text_v1(catalog.catalog_ref, 'CATALOG_REF')
    _probability_projection_names_v1(catalog.dependency_refs, 'CATALOG_DEPENDENCIES')
    _probability_projection_integer_v1(catalog.owner_epoch, 'CATALOG_EPOCH')
    _probability_projection_integer_v1(catalog.after_ordinal, 'CATALOG_CURSOR')
    _probability_projection_integer_v1(catalog.complete_through_ns, 'CATALOG_COMPLETENESS_TIME', None)
    _probability_require_v1(catalog.owner_epoch == snapshot.owner_epoch, 'CATALOG_EPOCH_CHANGED')
    _probability_require_v1(catalog.after_ordinal == state['high_watermark'], 'CATALOG_CURSOR_MISMATCH')
    _probability_require_v1(cutoff <= catalog.complete_through_ns <= snapshot.read_ns, 'CATALOG_NOT_COMPLETE_AT_CUTOFF')
    _probability_require_v1(type(catalog.rows) is tuple and all((type(r) is _ProbabilityMaturityClusterV1 for r in catalog.rows)), 'CATALOG_TYPE')
    _probability_require_v1(all((r.available_ns <= snapshot.read_ns for r in catalog.rows)), 'CATALOG_ROW_NOT_OBSERVED')
    _probability_require_v1(sum((len(r.row_ids) for r in catalog.rows)) <= limits.max_catalog_rows, 'CATALOG_RESOURCE_LIMIT')
    scope_refs = tuple((getattr(scope, k) for k in scope.__dataclass_fields__ if k not in ('profile_id', 'generation')))
    refs = (snapshot.snapshot_ref, *scope_refs, *model.dependency_refs, catalog.catalog_ref, *catalog.dependency_refs, *receipt_refs)
    if model.precision_protocol_ref is not None:
        refs += (model.precision_protocol_ref,)
    _probability_require_v1(not set(refs) & set(snapshot.invalidated_refs), 'DEPENDENCY_INVALIDATED')
    effective_state = _probability_copy_v1.deepcopy(state)
    effective_state['used_rows'] = list(dict.fromkeys((*state['used_rows'], *artifact['final_ids'])))
    selection_request = _ProbabilityWindowRequestV1(intent['request_id'], intent['receipt_id'], scope, state['head_ref'], state['sequence'], state['high_watermark'], 'WINDOW', cutoff, catalog.catalog_ref, catalog.rows, 'UNAVAILABLE', tuple(dict.fromkeys(refs)), 'SELECTION_ONLY_NOT_A_PUBLISHED_RESULT')
    selected = _derive_probability_window_v1(effective_state, selection_request, window_size=200, max_catalog_rows=limits.max_catalog_rows)
    return (intent, scope, model, catalog, result, cutoff, refs, selected)

def _validate_probability_admission_v1(snapshot: _ProbabilityAdmissionSnapshotV1, intent: dict, state: dict, *, current_owner_epoch: int, publication_ns: int, limits: _ProbabilityAdmissionLimitsV1) -> dict:
    """Private detached value construction; accepted source custody is enforced by the calling resolver."""
    intent, scope, model, catalog, result, cutoff, refs, selected = _prepare_probability_window_v1(snapshot, intent, state, current_owner_epoch=current_owner_epoch, publication_ns=publication_ns, limits=limits)

    def encoded(text: str) -> bytes:
        try:
            return text.encode('utf-8', errors='strict')
        except UnicodeError as exc:
            raise _probability_admission_failure_v1('ADMISSION_UTF8') from exc
    domains = dict(model.target_domains)

    def functional_value(name: str, text: str) -> _ProbabilityFractionV1:
        value = _probability_functional_scalar_v1(text)
        domain = domains[name]
        _probability_require_v1(domain == 'REAL' or (domain == 'NONNEGATIVE' and value >= 0) or (domain == 'UNIT_INTERVAL' and 0 <= value <= 1), 'TARGET_VALUE_DOMAIN')
        return value
    if selected['record'] is None:
        _probability_require_v1(result is None and intent['result_ref'] is None, 'RESULT_WITHOUT_COMPLETE_WINDOW')
        return {'disposition': 'NOT_READY_NO_TRANSITION', 'request': None, 'selection_cutoff_ns': cutoff, 'observed_ns': snapshot.read_ns, 'model_use_authorized': False}
    _probability_require_v1(type(result) is _ProbabilityAdmissionResultV1 and result.result_ref == intent['result_ref'], 'RESULT_ABSENT_OR_MISMATCH')
    _probability_projection_text_v1(result.result_ref, 'RESULT_REF')
    _probability_require_v1(type(result.scope) is ProbabilityProducerScopeV1 and result.scope == scope, 'RESULT_SCOPE')
    _probability_projection_integer_v1(result.owner_epoch, 'RESULT_EPOCH')
    _probability_projection_integer_v1(result.selection_cutoff_ns, 'RESULT_CUTOFF', None)
    _probability_projection_integer_v1(result.available_ns, 'RESULT_TIME', None)
    _probability_require_v1(result.owner_epoch == snapshot.owner_epoch and result.catalog_ref == catalog.catalog_ref and (result.selection_cutoff_ns == cutoff), 'RESULT_CATALOG_JOIN')
    _probability_require_v1(max(cutoff, model.available_ns) <= result.available_ns <= snapshot.read_ns, 'RESULT_NOT_VISIBLE')
    _probability_projection_names_v1(result.cluster_ids, 'RESULT_CLUSTERS')
    _probability_projection_names_v1(result.original_row_ids, 'RESULT_SOURCE_ROWS')
    chosen = selected['record']['selected_rows']
    _probability_require_v1(result.cluster_ids == tuple((row['cluster_id'] for row in chosen)) and result.original_row_ids == tuple((rid for row in chosen for rid in row['row_ids'])), 'RESULT_WINDOW_LINEAGE')
    _probability_projection_names_v1(result.targets, 'RESULT_TARGETS')
    _probability_require_v1(result.targets == model.targets, 'RESULT_TARGET_ORDER')
    _probability_require_v1(type(result.replicate_count) is int and result.replicate_count == model.replicate_count, 'RESULT_REPLICATE_COUNT')
    _probability_projection_text_v1(result.reference_plan_ref, 'PLAN_REF')
    _probability_projection_text_v1(result.current_plan_ref, 'PLAN_REF')
    _probability_require_v1(result.reference_plan_ref != result.current_plan_ref and type(result.partition_codes) is tuple and all((type(v) is int for v in result.partition_codes)) and (result.partition_codes == (3, 4)), 'PARTITION_IDENTITY')
    _probability_projection_names_v1(result.dependency_refs, 'RESULT_DEPENDENCIES')
    refs += (result.result_ref, result.reference_plan_ref, result.current_plan_ref, *result.dependency_refs)
    _probability_require_v1(not set(refs) & set(snapshot.invalidated_refs), 'DEPENDENCY_INVALIDATED')
    original_unavailable = type(result.reference_values) is tuple and type(result.current_values) is tuple and (result.reference_values == result.current_values == ())
    if not original_unavailable:
        for rows in (result.reference_values, result.current_values):
            _probability_require_v1(type(rows) is tuple and all((type(row) is tuple and len(row) == 2 for row in rows)) and (tuple((row[0] for row in rows)) == model.targets), 'FUNCTIONAL_TARGET_ORDER')
            for name, value in rows:
                functional_value(name, value)
    raw_banks = (result.reference_records, result.current_records)
    for bank in raw_banks:
        _probability_require_v1(type(bank) is tuple and len(bank) == model.replicate_count and all((type(row) is str for row in bank)), 'BANK_DENOMINATOR')
    _probability_require_v1(sum((len(encoded(row)) for bank in raw_banks for row in bank)) <= limits.max_total_bank_bytes, 'BANK_BYTE_BUDGET')
    banks = []
    original_reasons = set()
    for bank in raw_banks:
        parsed = [_probability_json_data_v1(encoded(row), limits.max_record_bytes) for row in bank]
        banks.append(_probability_bootstrap_bank_v1(parsed, model.replicate_count, list(model.targets)))
        for row in parsed:
            if original_unavailable:
                _probability_require_v1(row['status'] == 'INVALID' and row['values'] is None and (row['reason'] in _PROBABILITY_ORIGINAL_FAILURE_REASONS_V1), 'ORIGINAL_UNAVAILABLE_BANK')
                original_reasons.add(row['reason'])
            else:
                _probability_require_v1(row['reason'] not in _PROBABILITY_ORIGINAL_FAILURE_REASONS_V1, 'ORIGINAL_FAILURE_WITH_VALUES')
            if row['status'] == 'VALID':
                for name in model.targets:
                    functional_value(name, row['values'][name])
    failures = tuple(((code, bank['failed_replicates']) for code, bank in zip((3, 4), banks, strict=True) if bank['state'] != 'COMPLETE'))
    if original_unavailable:
        _probability_require_v1(len(original_reasons) == 1, 'ORIGINAL_FAILURE_REASON_CONFLICT')
        family, reason = ('UNAVAILABLE', next(iter(original_reasons)))
        summary = None
    elif failures:
        family, reason = ('UNAVAILABLE', 'REQUIRED_BOOTSTRAP_REPLICATE_INVALID')
        summary = None
    else:
        reference = dict(result.reference_values)
        current = dict(result.current_values)
        summary = _derive_probability_drift_result_v1(reference, current, *banks)
        family = 'MATERIAL_BREACH' if summary['state'] == 'MATERIAL_BREACH' else 'FAMILY_NONREJECTION'
        reason = None
    admitted = _ProbabilityWindowRequestV1(intent['request_id'], intent['receipt_id'], scope, state['head_ref'], state['sequence'], state['high_watermark'], 'WINDOW', cutoff, catalog.catalog_ref, catalog.rows, family, tuple(dict.fromkeys(refs)), reason)
    return {'disposition': 'VALIDATED_PROBABILITY_WINDOW_INPUT', 'request': admitted, 'summary': summary, 'invalid_replicates': failures, 'selection_cutoff_ns': cutoff, 'observed_ns': snapshot.read_ns, 'publication_ns': publication_ns, 'owner_epoch': snapshot.owner_epoch, 'model_use_authorized': False}

def _probability_receipt_expected_claims_v1(snapshot, limits):
    """Private detached value construction; accepted source custody is enforced by the calling resolver."""
    m, c, r = (snapshot.model, snapshot.catalog, snapshot.result)
    claims = {'SOURCE_RIGHTS': {'input_lock_ref': m.scope.input_lock_ref, 'reference_cohort_ref': m.scope.reference_cohort_ref, 'catalog_ref': c.catalog_ref, 'input_class': 'SCOPED_DATA_RIGHTS_AND_SOURCE_SEMANTICS_NOT_DOCUMENTATION_ONLY'}, 'ENVIRONMENT': {'environment_ref': m.scope.environment_ref, 'versions': [list(pair) for pair in snapshot.expected_environment], 'check_class': 'TARGET_ENVIRONMENT_WITH_BOUNDED_SYNTHETIC_ADAPTER_PARITY'}, 'MODEL_BUILD': {'model_artifact_ref': m.scope.model_artifact_ref, 'feature_names': list(m.feature_names), 'model_kind': m.model_kind, 'reference_cohort_ref': m.scope.reference_cohort_ref, 'reference_cutoff_ns': m.reference_cutoff_ns, 'artifact_available_ns': m.available_ns, 'build_class': 'FROZEN_BASE_PIPELINE_AND_SELECTED_CALIBRATOR', 'export_parity_kind': 'ACTUAL_SUBJECT_PIPELINE_ROUNDTRIP'}, 'MODEL_REVIEW': {'model_artifact_ref': m.scope.model_artifact_ref, 'review_class': 'CONCEPTUAL_AND_IMPLEMENTATION_REVIEW', 'scope_of_conclusion': 'BOUNDED_OFFLINE_DIAGNOSTICS_ONLY', 'blocker_codes': []}, 'USE_POLICY': {'policy_ref': m.scope.policy_ref, 'family_ref': m.scope.family_ref, 'targets': list(m.targets), 'target_domains': [list(p) for p in m.target_domains], 'replicate_count': m.replicate_count, 'precision_protocol_ref': m.precision_protocol_ref, 'limits': _probability_asdict_v1(limits), 'purpose': 'OFFLINE_PRODUCER_DIAGNOSTICS', 'permitted_model_use_modes': []}, 'CATALOG': {'catalog_ref': c.catalog_ref, 'owner_epoch': c.owner_epoch, 'after_ordinal': c.after_ordinal, 'complete_through_ns': c.complete_through_ns, 'row_count': len(c.rows), 'membership_class': 'IMMUTABLE_ORIGINAL_OBSERVATION_MEMBERSHIP'}}
    if r is not None:
        claims['COMPUTATION'] = {'result_ref': r.result_ref, 'catalog_ref': r.catalog_ref, 'owner_epoch': r.owner_epoch, 'selection_cutoff_ns': r.selection_cutoff_ns, 'artifact_available_ns': r.available_ns, 'reference_plan_ref': r.reference_plan_ref, 'current_plan_ref': r.current_plan_ref, 'partition_codes': list(r.partition_codes), 'targets': list(r.targets), 'replicate_count': r.replicate_count, 'reference_record_count': len(r.reference_records), 'current_record_count': len(r.current_records), 'run_kind': 'DRIFT_FUNCTIONAL_RESAMPLING_V36', 'completion_class': 'COMPLETE_ORDERED_RECORDS_INCLUDING_INVALID'}
    return claims

def _assemble_probability_drift_candidate_v1(snapshot, intent, model, catalog, cutoff, refs, chosen, banks, plan_refs, construction_refs, *, started_ns, completed_ns, limits, model_fits=0, original_failure=None):
    """Private detached value construction; accepted source custody is enforced by the calling resolver."""
    encoded_banks = tuple((tuple((_probability_canonical_data_v1(row) for row in bank['records'])) for bank in banks))
    _probability_require_v1(all((len(row.encode('utf-8')) <= limits.max_record_bytes for bank in encoded_banks for row in bank)), 'CONSTRUCTION_FRAME_BUDGET')
    _probability_require_v1(sum((len(row.encode('utf-8')) for bank in encoded_banks for row in bank)) <= limits.max_total_bank_bytes, 'BANK_BYTE_BUDGET')
    _probability_require_v1(completed_ns < model.valid_until_ns, 'MODEL_NOT_CURRENT')
    _probability_receipt_dependency_binding_v1(snapshot, completed_ns)
    result = _ProbabilityAdmissionResultV1(intent['result_ref'], model.scope, snapshot.owner_epoch, catalog.catalog_ref, cutoff, completed_ns, tuple((row.cluster_id for row in chosen)), tuple((rid for row in chosen for rid in row.row_ids)), model.targets, plan_refs[0], plan_refs[1], (3, 4), model.replicate_count, tuple(banks[0]['original'].items()), tuple(banks[1]['original'].items()), encoded_banks[0], encoded_banks[1], tuple(dict.fromkeys((*refs, *construction_refs))))
    invalid = tuple(((code, tuple((row['replicate'] for row in bank['records'] if row['status'] == 'INVALID'))) for code, bank in zip((3, 4), banks, strict=True)))
    return {'disposition': 'UNACCEPTED_DRIFT_CANDIDATE', 'result': result, 'started_ns': started_ns, 'completed_ns': completed_ns, 'invalid_replicates': invalid, 'model_fits': model_fits, 'accepted': False, 'source_authentication': False, 'model_use_authorized': False, 'random_plan_authenticated': False, 'original_failure': original_failure}

def _construct_probability_drift_candidate_v1(snapshot: _ProbabilityAdmissionSnapshotV1, intent: dict, state: dict, *, current_owner_epoch: int, started_ns: int, completed_ns: int, reference_primitives: tuple, current_primitives: tuple, reference_plan: tuple, current_plan: tuple, plan_refs: tuple[str, str], construction_refs: tuple[str, ...], limits: _ProbabilityAdmissionLimitsV1, max_plan_cells: int, max_primitive_cells: int) -> dict:
    """Private detached value construction; accepted source custody is enforced by the calling resolver."""
    _probability_projection_integer_v1(started_ns, 'CONSTRUCTION_CLOCK', None)
    _probability_projection_integer_v1(completed_ns, 'CONSTRUCTION_CLOCK', None)
    _probability_require_v1(started_ns <= completed_ns, 'CONSTRUCTION_CLOCK')
    _probability_projection_integer_v1(max_plan_cells, 'CONSTRUCTION_BUDGET', 1)
    _probability_projection_integer_v1(max_primitive_cells, 'CONSTRUCTION_BUDGET', 1)
    _probability_require_v1(type(snapshot) is _ProbabilityAdmissionSnapshotV1 and snapshot.result is None, 'CONSTRUCTION_ALREADY_HAS_RESULT')
    intent, scope, model, catalog, _, cutoff, refs, selected = _prepare_probability_window_v1(snapshot, intent, state, current_owner_epoch=current_owner_epoch, publication_ns=started_ns, limits=limits)
    if selected['record'] is None:
        _probability_require_v1(intent['result_ref'] is None and (reference_primitives, current_primitives, reference_plan, current_plan, plan_refs, construction_refs) == ((), (), (), (), (), ()), 'CONSTRUCTION_NOT_READY_HAS_WORK')
        return {'disposition': 'NOT_READY_NO_TRANSITION', 'result': None, 'model_fits': 0, 'accepted': False, 'source_authentication': False}
    _probability_projection_text_v1(intent['result_ref'], 'CONSTRUCTION_RESULT_ID')
    _probability_projection_names_v1(plan_refs, 'CONSTRUCTION_PLAN_REFS')
    _probability_require_v1(len(plan_refs) == 2, 'CONSTRUCTION_PLAN_REFS')
    _probability_projection_names_v1(construction_refs, 'CONSTRUCTION_DEPENDENCIES')
    _probability_require_v1(not set((*plan_refs, *construction_refs, intent['result_ref'])) & set(snapshot.invalidated_refs), 'DEPENDENCY_INVALIDATED')
    _probability_require_v1(type(reference_plan) is tuple and type(current_plan) is tuple and (len(reference_plan) == len(current_plan) == model.replicate_count), 'CONSTRUCTION_PLAN_DENOMINATOR')
    chosen = tuple((_ProbabilityMaturityClusterV1(**{**row, 'row_ids': tuple(row['row_ids'])}) for row in selected['record']['selected_rows']))
    _probability_require_v1(model.replicate_count * (len(model.reference_clusters) + len(chosen)) <= max_plan_cells, 'CONSTRUCTION_PLAN_BUDGET')
    nrows = sum((len(r.row_ids) for r in (*model.reference_clusters, *chosen)))
    _probability_require_v1(nrows * len(model.targets) <= max_primitive_cells, 'CONSTRUCTION_PRIMITIVE_BUDGET')
    domains = dict(model.target_domains)

    def values_for(supplied, expected):
        _probability_require_v1(type(supplied) is tuple and len(supplied) == len(expected), 'CONSTRUCTION_CLUSTER_ROSTER')
        result = []
        for cluster, source in zip(supplied, expected, strict=True):
            _probability_require_v1(type(cluster) is tuple and len(cluster) == 2 and (type(cluster[0]) is str) and (cluster[0] == source.cluster_id) and (type(cluster[1]) is tuple) and (len(cluster[1]) == len(source.row_ids)), 'CONSTRUCTION_CLUSTER_ROSTER')
            rows = []
            for row, rid in zip(cluster[1], source.row_ids, strict=True):
                _probability_require_v1(type(row) is tuple and len(row) == 2 and (type(row[0]) is str) and (row[0] == rid) and (type(row[1]) is tuple) and (len(row[1]) == len(model.targets)), 'CONSTRUCTION_ROW_LINEAGE')
                for target, value in zip(model.targets, row[1], strict=True):
                    _probability_require_v1(type(value) is float and math.isfinite(value), 'CONSTRUCTION_PRIMITIVE_TYPE')
                    domain = domains[target]
                    _probability_require_v1(domain == 'REAL' or (domain == 'NONNEGATIVE' and value >= 0) or (domain == 'UNIT_INTERVAL' and 0 <= value <= 1), 'CONSTRUCTION_PRIMITIVE_DOMAIN')
                rows.append(row[1])
            result.append(tuple(rows))
        return tuple(result)
    R = values_for(reference_primitives, model.reference_clusters)
    W = values_for(current_primitives, chosen)
    banks = (_probability_cluster_functional_bank_v1(R, model.targets, reference_plan, max_rows=limits.max_reference_rows, max_targets=limits.max_targets, max_plan_cells=max_plan_cells), _probability_cluster_functional_bank_v1(W, model.targets, current_plan, max_rows=limits.max_catalog_rows, max_targets=limits.max_targets, max_plan_cells=max_plan_cells))
    return _assemble_probability_drift_candidate_v1(snapshot, intent, model, catalog, cutoff, refs, chosen, banks, plan_refs, construction_refs, started_ns=started_ns, completed_ns=completed_ns, limits=limits)

def _construct_probability_full_family_candidate_v1(snapshot: _ProbabilityAdmissionSnapshotV1, intent: dict, state: dict, *, current_owner_epoch: int, started_ns: int, completed_ns: int, family: _ProbabilityBinaryDriftFamilyV1, reference_rows: tuple, current_rows: tuple, reference_plan: tuple, current_plan: tuple, plan_refs: tuple[str, str], construction_refs: tuple[str, ...], limits: _ProbabilityAdmissionLimitsV1, max_plan_cells: int, max_primitive_cells: int, max_diagnostic_rows: int, max_diagnostic_fits: int) -> dict:
    """Private detached value construction; accepted source custody is enforced by the calling resolver."""
    _probability_projection_integer_v1(started_ns, 'CONSTRUCTION_CLOCK', None)
    _probability_projection_integer_v1(completed_ns, 'CONSTRUCTION_CLOCK', None)
    _probability_require_v1(started_ns <= completed_ns, 'CONSTRUCTION_CLOCK')
    for bound in (max_plan_cells, max_primitive_cells, max_diagnostic_rows):
        _probability_projection_integer_v1(bound, 'CONSTRUCTION_BUDGET', 1)
    _probability_projection_integer_v1(max_diagnostic_fits, 'CONSTRUCTION_BUDGET')
    _probability_require_v1(type(snapshot) is _ProbabilityAdmissionSnapshotV1 and snapshot.result is None, 'CONSTRUCTION_ALREADY_HAS_RESULT')
    intent, scope, model, catalog, _, cutoff, refs, selected = _prepare_probability_window_v1(snapshot, intent, state, current_owner_epoch=current_owner_epoch, publication_ns=started_ns, limits=limits)
    _probability_require_v1(type(family) is _ProbabilityBinaryDriftFamilyV1, 'FULL_FAMILY_SCHEMA')
    layout = _compile_probability_binary_drift_family_v1(family)
    _probability_require_v1(family.family_ref == scope.family_ref and family.feature_names == model.feature_names and (model.target_domains == layout) and (model.targets == tuple((n for n, _ in layout))), 'FULL_FAMILY_BINDING')
    _probability_require_v1(model.model_kind == 'CALIBRATED_LOGISTIC', 'FULL_FAMILY_BINARY_APPLICABILITY')
    if selected['record'] is None:
        _probability_require_v1(intent['result_ref'] is None and (reference_rows, current_rows, reference_plan, current_plan, plan_refs, construction_refs) == ((), (), (), (), (), ()), 'CONSTRUCTION_NOT_READY_HAS_WORK')
        return {'disposition': 'NOT_READY_NO_TRANSITION', 'result': None, 'model_fits': 0, 'accepted': False, 'source_authentication': False}
    _probability_projection_text_v1(intent['result_ref'], 'CONSTRUCTION_RESULT_ID')
    _probability_projection_names_v1(plan_refs, 'CONSTRUCTION_PLAN_REFS')
    _probability_projection_names_v1(construction_refs, 'CONSTRUCTION_DEPENDENCIES')
    _probability_require_v1(len(plan_refs) == 2, 'CONSTRUCTION_PLAN_REFS')
    _probability_require_v1(not set((*plan_refs, *construction_refs, intent['result_ref'])) & set(snapshot.invalidated_refs), 'DEPENDENCY_INVALIDATED')
    chosen = tuple((_ProbabilityMaturityClusterV1(**{**row, 'row_ids': tuple(row['row_ids'])}) for row in selected['record']['selected_rows']))
    expected = (model.reference_clusters, chosen)
    plans = (reference_plan, current_plan)
    B = model.replicate_count
    _probability_require_v1(all((type(plan) is tuple and len(plan) == B for plan in plans)), 'CONSTRUCTION_PLAN_DENOMINATOR')
    _probability_require_v1(B * sum(map(len, expected)) <= max_plan_cells, 'CONSTRUCTION_PLAN_BUDGET')
    _probability_require_v1(sum((len(c.row_ids) for partition in expected for c in partition)) * len(layout) <= max_primitive_cells, 'CONSTRUCTION_PRIMITIVE_BUDGET')
    _probability_require_v1(not family.calibration_material or 2 * (B + 1) <= max_diagnostic_fits, 'DIAGNOSTIC_FIT_BUDGET')
    for plan, partition in zip(plans, expected, strict=True):
        for indices in plan:
            _probability_require_v1(type(indices) is tuple and len(indices) == len(partition) and all((type(i) is int and 0 <= i < len(partition) for i in indices)), 'FUNCTIONAL_INDEX')
            if family.calibration_material:
                _probability_require_v1(sum((len(partition[i].row_ids) for i in indices)) <= min(max_diagnostic_rows, 10000), 'DIAGNOSTIC_ROW_BUDGET')
        if family.calibration_material:
            _probability_require_v1(2 <= sum((len(c.row_ids) for c in partition)) <= min(max_diagnostic_rows, 10000), 'DIAGNOSTIC_ROW_BUDGET')
    all_raw = (reference_rows, current_rows)
    for supplied, partition in zip(all_raw, expected, strict=True):
        _probability_require_v1(type(supplied) is tuple and len(supplied) == len(partition), 'CONSTRUCTION_CLUSTER_ROSTER')
        for cluster, source in zip(supplied, partition, strict=True):
            _probability_require_v1(type(cluster) is tuple and len(cluster) == 2 and (type(cluster[0]) is str) and (cluster[0] == source.cluster_id) and (type(cluster[1]) is tuple) and (len(cluster[1]) == len(source.row_ids)), 'CONSTRUCTION_CLUSTER_ROSTER')
            for row, rid in zip(cluster[1], source.row_ids, strict=True):
                _probability_require_v1(type(row) is tuple and len(row) == 6 and (type(row[0]) is str) and (row[0] == rid), 'CONSTRUCTION_ROW_LINEAGE')
                _, x, y, missing, ood, composition = row
                _probability_require_v1(type(x) is tuple and len(x) == len(family.feature_names) and all((type(v) is float and math.isfinite(v) for v in x)), 'FULL_FAMILY_FEATURE_VALUES')
                _probability_require_v1(type(y) is int and y in (0, 1), 'DIAGNOSTIC_LABEL')
                _probability_require_v1(type(missing) is tuple and len(missing) == len(family.missingness_names) and (type(composition) is tuple) and (len(composition) == len(family.composition_names)) and all((type(v) is int and v in (0, 1) for v in (*missing, ood, *composition))), 'FULL_FAMILY_INDICATORS')
    artifact = _probability_json_data_v1(model.export_text.encode(), limits.max_model_bytes)
    means, scales, _, _ = _probability_validate_model_v1(artifact)
    additive_targets = model.targets[:-2] if family.calibration_material else model.targets
    additive_banks, diagnostic_originals, cached_diagnostics = ([], [], [])
    fit_calls = 0
    original_failure = None

    def fit(rows):
        nonlocal fit_calls
        outcome = _fit_probability_calibration_diagnostic_v1(tuple((q for q, _ in rows)), tuple((y for _, y in rows)), max_rows=max_diagnostic_rows)
        fit_calls += outcome['fit_calls']
        return outcome
    for partition_name, raw, indices, limit in zip(('R', 'W'), all_raw, plans, (limits.max_reference_rows, limits.max_catalog_rows), strict=True):
        primitives, diagnostics = ([], [])
        for _, rows in raw:
            cp, cd = ([], [])
            for _, x, y, missing, ood, composition in rows:
                z = tuple(((v - m) / s for v, m, s in zip(x, means, scales, strict=True)))
                _probability_require_v1(all((math.isfinite(v) and math.isfinite(v * v) for v in z)), 'FULL_FAMILY_TRANSFORM_NONFINITE')
                q = _probability_model_predict_v1(artifact, list(x), feature_names=list(family.feature_names))
                epsilon = math.ulp(1.0)
                clipped = min(1.0 - epsilon, max(epsilon, q))
                brier = compute_math_08_brier_score(q, y)
                loss = compute_math_09_log_loss(q, y, clip_epsilon=epsilon)
                cp.append(tuple((v for t in z for v in (t, t * t))) + tuple((float(v) for v in missing)) + (float(y), brier, loss, float(ood)) + tuple((float(v) for v in composition)))
                cd.append((q, y))
            primitives.append(tuple(cp))
            diagnostics.append(tuple(cd))
        try:
            bank = _probability_cluster_functional_bank_v1(tuple(primitives), additive_targets, indices, max_rows=limit, max_targets=limits.max_targets, max_plan_cells=max_plan_cells)
        except _ProbabilityNumericalFailureV1 as exc:
            if exc.detail not in ('FUNCTIONAL_UNDERFLOW', 'FUNCTIONAL_OVERFLOW'):
                raise
            original_failure = 'NOT_EXECUTED_ORIGINAL_' + partition_name + '_' + exc.detail
            break
        additive_banks.append(bank)
        cached_diagnostics.append(tuple(diagnostics))
        if family.calibration_material:
            original = fit(tuple((row for cluster in diagnostics for row in cluster)))
            if original['status'] == 'INVALID':
                original_failure = 'NOT_EXECUTED_ORIGINAL_' + partition_name + '_' + original['reason']
                break
            diagnostic_originals.append(original['values'])
    if original_failure is not None:
        _probability_require_v1(original_failure in _PROBABILITY_ORIGINAL_FAILURE_REASONS_V1, 'ORIGINAL_FAILURE_REASON')
        banks = tuple(({'original': {}, 'records': [{'replicate': r, 'status': 'INVALID', 'values': None, 'reason': original_failure} for r in range(B)]} for _ in range(2)))
    else:
        banks = []
        for partition_index, (bank, indices) in enumerate(zip(additive_banks, plans, strict=True)):
            original = dict(bank['original'])
            if family.calibration_material:
                original.update(zip(model.targets[-2:], diagnostic_originals[partition_index], strict=True))
            records = []
            for r, (additive, draw) in enumerate(zip(bank['records'], indices, strict=True)):
                if additive['status'] == 'INVALID':
                    records.append(dict(additive))
                    continue
                values = dict(additive['values'])
                if family.calibration_material:
                    occurrence_rows = tuple((row for i in draw for row in cached_diagnostics[partition_index][i]))
                    diagnostic = fit(occurrence_rows)
                    if diagnostic['status'] == 'INVALID':
                        records.append({'replicate': r, 'status': 'INVALID', 'values': None, 'reason': diagnostic['reason']})
                        continue
                    values.update(zip(model.targets[-2:], diagnostic['values'], strict=True))
                records.append({'replicate': r, 'status': 'VALID', 'values': values, 'reason': None})
            banks.append({'original': original, 'records': records})
        banks = tuple(banks)
    return _assemble_probability_drift_candidate_v1(snapshot, intent, model, catalog, cutoff, refs, chosen, banks, plan_refs, construction_refs, started_ns=started_ns, completed_ns=completed_ns, limits=limits, model_fits=fit_calls, original_failure=original_failure)


def _probability_context_projection_v1(context):
    """Preserve the full native context without floating-point epoch conversion."""
    from datetime import timezone
    from .models import _probability_require_v1 as need
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    def project(value):
        if type(value) is datetime:
            need(value.tzinfo is timezone.utc, "PROBABILITY_CONTEXT_UTC")
            delta = value - epoch
            return ((delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds) * 1000
        if type(value) is timedelta:
            return (value.days * 86400 + value.seconds) * 1000000 + value.microseconds
        if type(value) is tuple:
            return tuple(project(cell) for cell in value)
        need(value is None or type(value) in (str, int, bool), "PROBABILITY_CONTEXT_CELL")
        return value
    return project(context.execution_identity_tuple)


def _build_probability_owner_registry_v1(
    *, base_registry: CanonicalOwnerPacketRegistryV1, request: ProbabilityNativeUseRequestV1,
    capability_resolver: AgentCapabilityResolverV1, clock_facts: tuple[int, int, int, int, int],
    existing_conditions: tuple[NoTradeConditionOutcomeV1, ...], limits: ProbabilityPredictionReadLimitsV1,
    evaluated_ns: int, deadline_ns: int,
) -> tuple[CanonicalOwnerPacketRegistryV1, tuple[NoTradeConditionOutcomeV1, ...]]:
    """Conditional nearline projection; only original issued inputs can reach the registry."""
    from datetime import timezone
    from decimal import localcontext, DecimalException
    from .agent_policy import AgentCapabilityResolverV1
    from .context import canonical_probability_decimal, decimal_context_v1
    from .evidence import ComputationEvidenceServiceV1
    from .models import ProbabilityPredictionReadLimitsV1, _probability_require_v1 as need, _probability_ns_v1
    from .model_risk import (ProbabilityNativeUseRequestV1, NoTradeConditionOutcomeV1,
                             NO_TRADE_CONDITION_IDS_V1, _bind_probability_condition_evidence_v1)
    from .serialization import _bounded_probability_json_v1, _iter_prediction_artifact_frames_v1
    need(type(base_registry) is CanonicalOwnerPacketRegistryV1 and
         type(request) is ProbabilityNativeUseRequestV1 and type(capability_resolver) is AgentCapabilityResolverV1 and
         type(limits) is ProbabilityPredictionReadLimitsV1, "PROBABILITY_FACTORY_TYPES")
    request.__post_init__()
    fence = capability_resolver._probability_source_fence_v1
    need(type(fence) is _ProbabilityDependencyFenceV1, "PROBABILITY_FACTORY_SOURCE")
    prepared = request.prepared_prediction
    entry = fence._registered_v1(prepared, kind="PREDICTION", evaluated_ns=evaluated_ns)
    need(prepared.state == "SCORE_RESEARCH_ONLY" and prepared.values is not None and
         prepared.model_use_authorized is False and prepared.source_authentication is False and
         prepared.native_packet_created is False, "PROBABILITY_FACTORY_PREPARED")
    matches = tuple(i for i, key in enumerate(prepared.request_keys) if key == request.query_key)
    need(len(matches) == 1, "PROBABILITY_FACTORY_QUERY")
    q = prepared.values[matches[0]][1]
    need(type(q) is float and math.isfinite(q) and 0 <= q <= 1, "PROBABILITY_FACTORY_POINT")
    context = request.execution_context
    projection = _probability_context_projection_v1(context)
    as_of_ns = projection[1]
    need(type(clock_facts) is tuple and len(clock_facts) == 5, "PROBABILITY_FACTORY_CLOCKS")
    for instant in (*clock_facts, evaluated_ns):
        _probability_ns_v1(instant)
    observed, effective, available, received, processed = clock_facts
    need(observed <= available <= received <= processed <= as_of_ns <= evaluated_ns,
         "PROBABILITY_FACTORY_CLOCK_ORDER")
    need(type(existing_conditions) is tuple and tuple(row.condition_id for row in existing_conditions) ==
         NO_TRADE_CONDITION_IDS_V1 and all(type(row) is NoTradeConditionOutcomeV1 for row in existing_conditions),
         "PROBABILITY_FACTORY_CONDITIONS")
    need(limits.metadata_limits.deadline_monotonic_ns >= deadline_ns and time.monotonic_ns() < deadline_ns,
         "PROBABILITY_FACTORY_DEADLINE")
    need(len(request.binding_ids) <= limits.metadata_limits.max_records, "PROBABILITY_FACTORY_PACKET_CAPACITY")
    with _probability_owned_context_v1(capability_resolver._resolve_probability_native_use_v1(
            request, evaluated_ns=evaluated_ns, deadline_ns=deadline_ns)) as admission:
        values = {request.binding_ids[0]: q}
        if request.outcome_join is not None:
            outcome = request.outcome_join
            try:
                with localcontext(decimal_context_v1()):
                    q_decimal = canonical_probability_decimal(q, field_name="probability point")
                    p_win = outcome.validity_probability * q_decimal
                    p_void = Decimal(1) - outcome.validity_probability
                    need(p_win.is_finite() and p_void.is_finite() and 0 <= p_win <= 1 and 0 <= p_void <= 1 and
                         p_win + p_void <= 1, "PROBABILITY_OUTCOME_PROJECTION")
                    values[request.binding_ids[2]] = str(p_win)
                    values[request.binding_ids[3]] = str(p_void)
            except DecimalException as error:
                raise NumericDomainError(ReasonCode.INVALID_NUMERIC_INPUT, "probability outcome arithmetic") from error
    now = time.time_ns()
    capability_resolver._check_probability_native_use_v1(admission, evaluated_ns=now)
    # The reader's final currentness observation advances the original fence.
    # Each subsequent observation needs its own current clock value; reusing
    # the pre-reader timestamp would falsely report a clock regression.
    use = fence._registered_v1(admission, kind="NATIVE_USE", evaluated_ns=time.time_ns())
    need("packets" not in use["metadata"], "PROBABILITY_USE_ALREADY_PROJECTED")
    values[request.binding_ids[1]] = ComputationEvidenceServiceV1._probability_calibration_token_v1(
        review=entry["metadata"]["review"], admission=admission,
        capability_resolver=capability_resolver, evaluated_ns=time.time_ns())
    now = time.time_ns()
    minimum_availability = max(prepared.observed_ns, admission.available_ns,
        entry["metadata"]["result"].typed_payload.available_ns,
        entry["metadata"]["review"].typed_payload.available_ns,
        prepared.observed_ns if request.outcome_join is None else request.outcome_join.available_ns)
    need(minimum_availability <= available and processed <= now and admission.valid_until_ns - now >= 1000,
         "PROBABILITY_FACTORY_AVAILABILITY_OR_EXPIRY")
    expiry_us = admission.valid_until_ns // 1000
    ttl_us = expiry_us - observed // 1000
    need(ttl_us > 0, "PROBABILITY_FACTORY_TTL")
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    try:
        clocks = PointInTimeClocksV1(
            observed_time=epoch + timedelta(microseconds=observed // 1000),
            effective_time=epoch + timedelta(microseconds=effective // 1000),
            available_time=epoch + timedelta(microseconds=-((-available) // 1000)),
            received_time=epoch + timedelta(microseconds=-((-received) // 1000)),
            processed_time=epoch + timedelta(microseconds=-((-processed) // 1000)), as_of_time=context.as_of)
        ttl = timedelta(microseconds=ttl_us)
    except (ValueError, OverflowError) as error:
        raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, "probability clock range") from error
    selected = tuple(binding for rows in FORMULA_INPUT_AUTHORITY_BY_MATH_ID.values() for binding in rows
                     if binding.binding_id in request.binding_ids)
    need(len(selected) == len(request.binding_ids), "PROBABILITY_FACTORY_BINDING_ROSTER")
    by_id = {binding.binding_id: binding for binding in selected}
    specifications = []
    used_bytes = used_frames = 0
    refs = tuple(dict.fromkeys((*admission.dependency_refs, prepared.result_ref, prepared.review_ref)))
    need(len(refs) + len(request.binding_ids) <= limits.metadata_limits.max_records, "PROBABILITY_FACTORY_REFERENCE_CAPACITY")
    for binding_id in request.binding_ids:
        binding = by_id[binding_id]
        semantics = next(row["point_in_time_semantics"] for row in FROZEN_FORMULA_REQUIREMENTS[binding.math_spec_id].raw["typed_inputs"]
                         if row["name"] == binding.input_name)
        field_class = classify_point_in_time_semantics(semantics)
        need(effective <= as_of_ns or field_class not in (PointInTimeFieldClassV1.EVENT_OUTCOME, PointInTimeFieldClassV1.SETTLEMENT),
             "PROBABILITY_FACTORY_EFFECTIVE_TIME")
        need(not any(_sequence_revision_requirements(binding.provider_native_sequence_or_revision)),
             "PROBABILITY_FACTORY_REQUIRED_SEQUENCE_UNAVAILABLE")
        identity = "V35::" + _bounded_probability_json_v1((prepared.result_ref, prepared.review_ref,
            admission.accepted_use_decision_ref, binding_id, request.query_key, projection),
            max_bytes=limits.metadata_limits.max_frame_bytes)
        leaf = values[binding_id]
        nested = leaf
        for part in reversed(binding.exact_field_path.split(".")):
            nested = {part: nested}
        producer = prepared.review_ref if binding_id == request.binding_ids[1] else prepared.result_ref
        # Reserve the exact bounded transport for every packet before constructing any packet.
        data = dict(packet_id=identity, owner_id=binding.accepted_upstream_owner_id,
            packet_type=binding.accepted_packet_or_snapshot_type, schema_id=binding.schema_id,
            schema_version=binding.schema_version, context_id=context.context_id, scope=tuple(context.scope.identity_tuple),
            source_epoch_id=context.source_epoch_id, input_version=context.input_version,
            clocks=(*clock_facts, as_of_ns), ttl_us=ttl_us, values=nested, authorized_binding_ids=(binding_id,),
            producer_receipt_id=producer, producer_receipt_type=binding.producer_receipt_type,
            source_state_and_claim_lineage=binding.source_state_and_claim_lineage,
            provider_sequence=None, revision=None, prior_revision_available_time=None, source_conflict=False)
        for frame in _iter_prediction_artifact_frames_v1(data, max_bytes=limits.max_total_bytes - used_bytes,
                                                       max_frames=limits.max_frames - used_frames):
            need(len(frame) <= limits.metadata_limits.max_frame_bytes, "PROBABILITY_FACTORY_METADATA_BOUND")
            used_bytes += len(frame)
            used_frames += 1
        specifications.append((binding, identity, nested, producer))
    packets = tuple(OwnerValuePacketV1(packet_id=identity, owner_id=binding.accepted_upstream_owner_id,
        packet_type=binding.accepted_packet_or_snapshot_type, schema_id=binding.schema_id, schema_version=binding.schema_version,
        context_id=context.context_id, scope=context.scope, source_epoch_id=context.source_epoch_id,
        input_version=context.input_version, clocks=clocks, ttl=ttl, values=nested,
        authorized_binding_ids=(binding.binding_id,), producer_receipt_id=producer,
        producer_receipt_type=binding.producer_receipt_type, source_state_and_claim_lineage=binding.source_state_and_claim_lineage)
        for binding, identity, nested, producer in specifications)
    use["metadata"]["packets"] = packets
    try:
        registry = CanonicalOwnerPacketRegistryV1((*base_registry.packets, *packets),
            _probability_guard_bindings=(*base_registry._probability_guard_bindings,
                                        *((packet, admission, capability_resolver) for packet in packets)))
        for binding, _, _, _ in specifications:
            _resolve_formula_input_binding(binding.math_spec_id, binding=binding, context=context,
                                           owner_registry=registry, caller_assertions=MappingProxyType({}))
        retained = tuple(NoTradeConditionOutcomeV1(old.condition_id, old.active or original.active,
            tuple(dict.fromkeys((*old.evidence_receipt_refs, *original.evidence_receipt_refs))),
            tuple(dict.fromkeys((*old.reason_codes, *original.reason_codes))))
            for old, original in zip(existing_conditions, entry["metadata"]["conditions"], strict=True))
        model = entry["metadata"]["model"]
        conditions = _bind_probability_condition_evidence_v1(scope=request.producer_scope,
            read_snapshot=entry["metadata"]["read_snapshot"], evaluated_ns=time.time_ns(),
            model_available_ns=model.available_ns, model_valid_until_ns=model.valid_until_ns,
            receipt_dependency_refs=admission.dependency_refs, receipt_valid_until_ns=admission.valid_until_ns,
            conditions=retained)
        result = (registry, conditions)
        fence._check_v1(original_cut=use["cut"], dependency_refs=use["dependencies"],
                        evaluated_ns=time.time_ns(), deadline_ns=deadline_ns)
        registry._check_probability_packet_refs_v1(tuple(packet.packet_id for packet in packets), context=context)
        return result
    except BaseException:
        use["metadata"].pop("packets", None)
        raise


def _commit_probability_issued_record_v1(*, fence, record, entry, read_request, readback_request):
    """One owned transaction and one exact readback; ambiguous outcomes remain retained."""
    from .receipts import _probability_control_projection_v1
    from .errors import PersistenceContractError
    from .persistence import _probability_read_roots_v1, _probability_read_check_v1
    need = _probability_require_v1
    canonical = _bounded_probability_json_v1(_probability_control_projection_v1(record),
                                            max_bytes=read_request.limits.max_frame_bytes)
    need(entry is fence._registrations.get(id(entry["object"])) and entry["object"] is record and entry["kind"] == "APPEND",
         "PROBABILITY_ORIGINAL_APPEND_ISSUANCE")
    need(read_request.scope == readback_request.scope == fence.scope, "PROBABILITY_COMMIT_SCOPE")
    _probability_read_check_v1(read_request)
    _probability_read_check_v1(readback_request)
    if record.typed_payload.control_kind in ("PREDICTION_RESULT", "PREDICTION_REVIEW"):
        need(record.record_id in _probability_read_roots_v1(readback_request),
             "PROBABILITY_COMMIT_READBACK_ROOT")
    deadline = min(read_request.limits.deadline_monotonic_ns, readback_request.limits.deadline_monotonic_ns)
    issued = {"records": (record,), "canonical": {record.record_id: canonical}, "transaction": None,
              "cut": entry["cut"], "dependencies": entry["dependencies"], "expiry": entry["expiry"],
              "deadline": deadline, "readback_request": readback_request, "entry": entry,
              "status": "PREPARED"}
    with fence._owned_v1():
        need(fence._active_append is None and record.record_id not in fence._uncertain,
             "PROBABILITY_PUBLICATION_BUSY_OR_UNKNOWN")
        fence._registered_v1(record, kind="APPEND", evaluated_ns=time.time_ns())
        fence._active_append = issued
        transaction = None
        attempted = False
        repeated = None
        rollback_attempted = False
        try:
            transaction = fence.persistence.begin_transaction()
            issued["transaction"] = transaction
            current = fence.persistence._probability_append_snapshot_v1(transaction, read_request)
            fence._check_snapshot_v1(current, issuer_snapshot=entry["view"]["snapshot"], original_cut=entry["cut"],
                                     dependency_refs=entry["dependencies"], deadline_ns=deadline)
            expected = entry["metadata"]["committed_snapshot"]
            for reference, old in expected.records_by_ref.items():
                row = current.records_by_ref.get(reference)
                need(row is not None and _bounded_probability_json_v1(_probability_control_projection_v1(row),
                     max_bytes=read_request.limits.max_frame_bytes) ==
                     _bounded_probability_json_v1(_probability_control_projection_v1(old),
                     max_bytes=read_request.limits.max_frame_bytes), "PROBABILITY_COMMIT_ANCESTRY_CHANGED")
            if record.typed_payload.control_kind == "PUBLICATION":
                body = record.typed_payload.body
                matches = tuple(row for row in current.publication_records if
                    row.record_id == record.record_id or row.typed_payload.body["request_id"] == body["request_id"])
                if matches:
                    need(len(matches) == 1 and matches[0].record_id == record.record_id and
                         matches[0].typed_payload.scope == record.typed_payload.scope and
                         matches[0].typed_payload.dependency_refs == record.typed_payload.dependency_refs and
                         _bounded_probability_json_v1(matches[0].typed_payload.body,
                             max_bytes=read_request.limits.max_frame_bytes) ==
                         _bounded_probability_json_v1(body, max_bytes=read_request.limits.max_frame_bytes),
                         "PROBABILITY_EXACT_REPEAT_CONFLICT")
                    repeated = matches[0]
                    issued["records"] = (repeated,)
                    issued["canonical"] = {repeated.record_id: _bounded_probability_json_v1(
                        _probability_control_projection_v1(repeated), max_bytes=read_request.limits.max_frame_bytes)}
                    # This owned transaction made no writes. Its cleanup must
                    # succeed before the separate committed read is exposed.
                    issued["status"] = "EXACT_REPEAT_READBACK_PENDING"
                    fence._uncertain[record.record_id] = issued
                    rollback_attempted = True
                    transaction.rollback()
                head = current.publication_records[-1] if current.publication_records else None
                need(repeated is not None or (None if head is None else head.record_id, len(current.publication_records),
                      0 if head is None else head.typed_payload.body["after"]["high_watermark"]) ==
                     (body["expected_head_ref"], body["expected_sequence"], body["expected_high_watermark"]),
                     "PROBABILITY_STALE_PUBLICATION_PARENT")
            if repeated is None:
                fence.persistence.insert_receipt_record(transaction, record)
                fence._append_guard_v1(transaction, record)
                # Retain the identity BEFORE crossing the native commit boundary.
                fence._uncertain[record.record_id] = issued
                issued["status"] = "COMMIT_ATTEMPTED"
                attempted = True
                fence.persistence._probability_commit_attempt_v1 = transaction
                transaction.commit()
                issued["status"] = "COMMIT_RETURNED"
        except BaseException as body_error:
            if not attempted and not rollback_attempted and transaction is not None and transaction.is_active:
                try:
                    rollback_attempted = True
                    transaction.rollback()
                except BaseException as cleanup_error:
                    fence._uncertain[record.record_id] = issued
                    raise BaseExceptionGroup("probability receipt body and rollback failures", [body_error, cleanup_error])
            raise
        finally:
            fence._active_append = None
            fence.persistence._probability_commit_attempt_v1 = None
    # Read ownership ends before any currentness or caller exposure.
    committed = _reconcile_probability_record_v1(fence=fence,
        record=record if repeated is None else repeated, read_request=readback_request)
    fence._check_snapshot_v1(issued["committed_snapshot"], issuer_snapshot=entry["view"]["snapshot"],
        original_cut=entry["cut"], dependency_refs=entry["dependencies"], deadline_ns=deadline)
    need(time.time_ns() < entry["expiry"], "PROBABILITY_COMMITTED_BUT_NO_LONGER_CURRENT")
    return committed


def _reconcile_probability_record_v1(*, fence, record, read_request):
    """Historical reconciliation never renews an expired/revoked issuance or retries a write."""
    from .receipts import _probability_control_projection_v1
    from .persistence import _probability_read_check_v1
    from dataclasses import replace
    need = _probability_require_v1
    issued = fence._uncertain.get(record.record_id)
    need(issued is not None and issued["records"] == (record,) and issued["records"][0] is record and
         read_request is issued["readback_request"], "PROBABILITY_RECONCILIATION_OWNERSHIP")
    now = _probability_read_check_v1(read_request)
    observed_request = replace(read_request, effective_cutoff_ns=now, recorded_cutoff_ns=now)
    issued["observed_readback_request"] = observed_request
    with _probability_owned_context_v1(fence.persistence.load_committed_probability_producer_state_v1(observed_request)) as snapshot:
        committed = snapshot.records_by_ref.get(record.record_id)
        need(committed is not None, "PROBABILITY_COMMIT_STILL_UNCONFIRMED")
        need(_bounded_probability_json_v1(_probability_control_projection_v1(committed),
             max_bytes=read_request.limits.max_frame_bytes) == issued["canonical"][record.record_id],
             "PROBABILITY_COMMITTED_IDENTITY_CONFLICT")
    issued["status"] = "CONFIRMED_COMMITTED"
    issued["committed_snapshot"] = snapshot
    issued["entry"]["metadata"]["historical_commit"] = snapshot
    if fence._uncertain.get(record.record_id) is issued:
        del fence._uncertain[record.record_id]
    return committed


def _publish_probability_window_v1(*, materialization, intent, issuer_resolver, spine_metadata, readback_request):
    """Publish the pure admitted transition under its original cut and compare-and-append."""
    from .receipts import ProbabilityProducerControlReceiptV1, _probability_control_record_v1
    from .model_risk import _derive_probability_window_v1
    need = _probability_require_v1
    fence = issuer_resolver._probability_source_fence_v1
    need(type(fence) is _ProbabilityDependencyFenceV1 and type(materialization) is dict, "PROBABILITY_PUBLICATION_SOURCE")
    snapshot = materialization["snapshot"]
    entry = fence._registered_v1(snapshot, kind="MATERIALIZATION", evaluated_ns=time.time_ns())
    need(entry["metadata"]["materialization"] is materialization and
         entry["metadata"]["intent"] == _probability_canonical_data_v1(intent) and
         entry["metadata"]["state"] == _probability_canonical_data_v1(materialization["state"]),
         "PROBABILITY_ORIGINAL_MATERIALIZATION")
    now = time.time_ns()
    admitted = _validate_probability_admission_v1(snapshot, intent, materialization["state"],
        current_owner_epoch=fence.policy_epoch, publication_ns=now, limits=materialization["limits"])
    if admitted["request"] is None:
        return admitted
    request = admitted["request"]
    transition = _derive_probability_window_v1(materialization["state"], request, window_size=200,
                                               max_catalog_rows=materialization["limits"].max_catalog_rows)
    pure = transition["record"]
    body = {"request_id": request.request_id, "expected_head_ref": request.expected_head_ref,
            "expected_sequence": request.expected_sequence, "expected_high_watermark": request.expected_high_watermark,
            "kind": request.kind, "cutoff_ns": request.cutoff_ns, "catalog_ref": request.catalog_ref,
            "result_ref": intent["result_ref"], "selected_rows": tuple(pure["selected_rows"]),
            "family_result": request.family_result, "reason": request.reason, "after": pure["after"]}
    payload = ProbabilityProducerControlReceiptV1(schema_version="PROBABILITY_PRODUCER_CONTROL_V1",
        control_kind="PUBLICATION", scope=fence.scope, effective_ns=request.cutoff_ns, recorded_ns=now, available_ns=now,
        valid_until_ns=entry["expiry"], dependency_refs=request.evidence_refs, body=body)
    record = _probability_control_record_v1(record_id=request.receipt_id, payload=payload, **spine_metadata)
    issued = fence._register_v1(record, kind="APPEND", view=entry["view"], dependency_refs=request.evidence_refs,
        valid_until_ns=entry["expiry"], value_node_limit=materialization["read_request"].limits.max_total_bytes,
        metadata={"committed_snapshot": materialization["committed_snapshot"],
                                               "intent": entry["metadata"]["intent"], "transition": transition})
    return _commit_probability_issued_record_v1(fence=fence, record=record, entry=issued,
        read_request=materialization["read_request"], readback_request=readback_request)


def _probability_construction_pin_v1(value, *, max_nodes):
    """Bounded identity/value pin of the trusted immutable source projection.

    This is local lifetime custody, not serialization or source authentication.
    """
    from dataclasses import fields, is_dataclass
    from enum import Enum
    from .models import _probability_datetime_ns_v1
    need = _probability_require_v1
    _probability_projection_integer_v1(max_nodes, "PROBABILITY_SOURCE_PIN_BUDGET", 1)
    remaining, active, seen_objects = max_nodes, set(), set()
    def walk(item, depth=0):
        nonlocal remaining
        remaining -= 1
        need(remaining >= 0 and depth <= 16, "PROBABILITY_SOURCE_PIN_BUDGET")
        if item is None or type(item) is bool:
            return (type(item), item)
        if type(item) is int:
            need(item.bit_length() <= 512, "PROBABILITY_SOURCE_INTEGER")
            return (int, item)
        if type(item) is float:
            need(math.isfinite(item), "PROBABILITY_SOURCE_BINARY64")
            return (float, item.hex())
        if type(item) is str:
            need(len(item) <= remaining, "PROBABILITY_SOURCE_TEXT_BUDGET")
            for character in item:
                code = ord(character)
                need(not 0xD800 <= code <= 0xDFFF, "PROBABILITY_SOURCE_UTF8")
                remaining -= 1 if code < 128 else 2 if code < 2048 else 3 if code < 65536 else 4
                need(remaining >= 0, "PROBABILITY_SOURCE_TEXT_BUDGET")
            return (str, item)
        if type(item) is Decimal:
            need(item.is_finite(), "PROBABILITY_SOURCE_DECIMAL")
            parts = item.as_tuple()
            need(len(parts.digits) <= remaining, "PROBABILITY_SOURCE_DECIMAL_BUDGET")
            remaining -= len(parts.digits)
            return (Decimal, parts)
        if type(item) is datetime:
            return (datetime, _probability_datetime_ns_v1(item))
        if type(item) is timedelta:
            # The original native execution context carries maximum_age as an
            # exact duration. Pin its normalized integer parts without a float.
            return (timedelta, item.days, item.seconds, item.microseconds)
        if isinstance(item, Enum):
            return (type(item), item.name, walk(item.value, depth + 1))
        need(id(item) not in active, "PROBABILITY_SOURCE_CYCLE")
        if (type(item) is MappingProxyType or is_dataclass(item)) and id(item) in seen_objects:
            return ("ORIGINAL_REFERENCE", type(item), id(item))
        active.add(id(item))
        try:
            if type(item) is tuple:
                need(len(item) <= remaining, "PROBABILITY_SOURCE_PIN_BUDGET")
                return (tuple, tuple(walk(child, depth + 1) for child in item))
            if type(item) is MappingProxyType:
                need(len(item) <= remaining and all(type(key) is str for key in item), "PROBABILITY_SOURCE_MAP")
                pinned = (MappingProxyType, id(item), tuple((walk(key, depth + 1), walk(child, depth + 1))
                    for key, child in item.items()))
                seen_objects.add(id(item))
                return pinned
            need(is_dataclass(item) and not isinstance(item, type) and item.__dataclass_params__.frozen,
                 "PROBABILITY_SOURCE_IMMUTABLE_VALUES_REQUIRED")
            pinned = (type(item), id(item), tuple((field.name, walk(getattr(item, field.name), depth + 1))
                for field in fields(item)))
            seen_objects.add(id(item))
            return pinned
        finally:
            active.remove(id(item))
    return walk(value)


def _probability_bind_pit_rows_v1(source, rows, dependencies, read_ns):
    """Join final native PIT objects, never candidates or provider payloads."""
    from ..market_data_ingest.adapter import PITCanonicalEventV2, PITReadRequestV1
    from ..market_data_ingest.binding import SelectedPITPublicDataContractV2
    from ..market_data_ingest.source_dependency import PIT_SOURCE_DEPENDENCIES_V2
    from .point_in_time import PITEventDispositionV1, PITClockSetV3
    from .models import _probability_datetime_ns_v1
    need = _probability_require_v1
    bindings = source["pit_rows"]
    need(type(bindings) is tuple and len(bindings) == len(rows), "PROBABILITY_PIT_ROW_COVERAGE")
    for original, binding in zip(rows, bindings, strict=True):
        need(type(binding) is tuple and len(binding) == 4 and binding[0] == original[0], "PROBABILITY_PIT_ROW_ORDER")
        _, contract, request, event = binding
        feature = original[1]
        need(type(contract) is SelectedPITPublicDataContractV2 and type(request) is PITReadRequestV1 and
             type(event) is PITCanonicalEventV2 and type(event.clocks) is PITClockSetV3,
             "PROBABILITY_ACCEPTED_PIT_TYPES")
        contract.__post_init__(); request.__post_init__(); event.__post_init__(); event.clocks.__post_init__()
        need(contract.profile_id == request.profile_id == event.profile_id and event.profile_id.value == feature.profile_id and
             event.event_disposition is PITEventDispositionV1.COMMITTED and event.failure_reason_or_none is None and
             event.event_kind == request.event_kind and event.event_kind in contract.admitted_event_kinds and
             request.access_class in contract.allowed_access_classes and request.read_action in contract.allowed_methods and
             request.path_or_channel in (*contract.allowed_paths, *contract.allowed_channels) and
             event.source_currentization_version == request.source_contract_version == contract.source_contract_version,
             "PROBABILITY_PIT_CONTRACT_OR_CAPABILITY")
        selected = tuple(row for row in PIT_SOURCE_DEPENDENCIES_V2 if row.dependency_id == request.source_dependency_ref)
        need(len(selected) == 1 and all(getattr(request, name) == getattr(selected[0], name) for name in
             ("profile_id", "event_kind", "access_class", "read_action", "host", "path_or_channel", "credential_alias_required")),
             "PROBABILITY_PIT_EXACT_ACCESS")
        need((event.event_record_id, event.market_id, event.instrument_id, event.post_state_ref,
              event.rights_receipt_ref, event.source_receipt_ref, event.committed_event_ordinal,
              event.provider_sequence_end_or_none) ==
             (feature.canonical_event_id, feature.market_id, feature.contract_id, feature.source_snapshot_ref,
              feature.source_rights_receipt_ref, contract.source_currentization_receipt_ref,
              feature.durable_commit_sequence, feature.source_sequence_or_none) and
             event.rights_receipt_ref == contract.rights_receipt_ref, "PROBABILITY_PIT_FEATURE_SOURCE_JOIN")
        clocks = event.clocks
        need((feature.received_at_utc, feature.processed_at_utc, feature.available_to_strategy_at_utc) ==
             (clocks.qtt_received_at_utc, clocks.qtt_parse_completed_at_utc, clocks.strategy_available_at_utc) and
             clocks.qtt_received_monotonic_ns <= clocks.qtt_parse_completed_monotonic_ns <=
             clocks.durable_commit_completed_monotonic_ns <= clocks.strategy_available_monotonic_ns and
             _probability_datetime_ns_v1(clocks.durable_commit_completed_at_utc) <=
             _probability_datetime_ns_v1(clocks.strategy_available_at_utc) <= read_ns,
             "PROBABILITY_PIT_COMMIT_AND_AVAILABILITY")
        need({event.commit_completion_ref, event.source_receipt_ref, event.rights_receipt_ref,
              clocks.clock_quality_receipt_ref, contract.scope_receipt_ref} <= dependencies,
             "PROBABILITY_PIT_UNACCEPTED_DEPENDENCY")


def _resolve_probability_construction_inputs_v1(*, read_request, intent, persistence, issuer_resolver, budget):
    """Resolve the sole pre-result read and bind original feature/label source projections."""
    from .errors import OwnerAdapterError
    from .models import ProbabilityModelCellManifestV2, SelectedFeatureVectorV2, SelectedLabelRecordV2, _probability_datetime_ns_v1
    need = _probability_require_v1
    need(read_request.purpose == "CONSTRUCT_CANDIDATE", "PROBABILITY_CONSTRUCTION_READ_PURPOSE")
    fence = issuer_resolver._probability_source_fence_v1
    if type(fence) is not _ProbabilityDependencyFenceV1 or fence._construction_inputs_v1 is None:
        raise OwnerAdapterError(ReasonCode.OWNER_DATA_MISSING, "PROBABILITY_ACCEPTED_FEATURE_LABEL_BINDING_UNAVAILABLE")
    source = fence._construction_inputs_v1
    need(type(source) is MappingProxyType, "PROBABILITY_CONSTRUCTION_OWNED_SOURCE")
    required = {"manifest", "feature_rows", "input_lock_ref", "binding_ref", "pit_rows"}
    routes = set(source) - required
    need(required <= set(source) and routes and routes <= {
         "prediction_parameters", "continuous_parameters", "drift_parameters", "drift_indicators"}
         and not {"prediction_parameters", "continuous_parameters"} <= routes
         and ("drift_parameters" in routes) == ("drift_indicators" in routes), "PROBABILITY_CONSTRUCTION_SOURCE_FIELDS")
    materialized = _resolve_probability_admission_snapshot_v1(read_request=read_request, intent=intent,
        persistence=persistence, issuer_resolver=issuer_resolver, budget=budget)
    snapshot = materialized["snapshot"]
    entry = fence._registered_v1(snapshot, kind="MATERIALIZATION", evaluated_ns=time.time_ns())
    manifest = source["manifest"]
    need(type(manifest) is ProbabilityModelCellManifestV2 and
         (manifest.cell_manifest_id, manifest.profile_id, manifest.ordered_feature_names) ==
         (fence.scope.cell_manifest_ref, fence.scope.profile_id, snapshot.model.feature_names), "PROBABILITY_SOURCE_CELL_MANIFEST")
    manifest.__post_init__()
    need(time.time_ns() < _probability_datetime_ns_v1(manifest.valid_until_utc), "PROBABILITY_SOURCE_CELL_EXPIRED")
    rows = source["feature_rows"]
    need(type(rows) is tuple and len(rows) <= materialized["limits"].max_catalog_rows, "PROBABILITY_SOURCE_ROW_BUDGET")
    dependencies = set(entry["dependencies"])
    source_pin = _probability_construction_pin_v1(source, max_nodes=budget.max_total_bytes)
    need(set(manifest.source_capability_refs) <= dependencies, "PROBABILITY_SOURCE_CAPABILITIES")
    seen = set()
    for row in rows:
        need(type(row) is tuple and len(row) == 3, "PROBABILITY_SOURCE_ROW_SHAPE")
        row_id, feature, label = row
        _probability_projection_text_v1(row_id, "PROBABILITY_SOURCE_ROW_ID")
        need(row_id not in seen and type(feature) is SelectedFeatureVectorV2 and type(label) is SelectedLabelRecordV2,
             "PROBABILITY_SOURCE_ROW_IDENTITY")
        seen.add(row_id)
        feature.__post_init__(); label.__post_init__()
        need((feature.cell_manifest_id, feature.profile_id, feature.venue_scope_id, feature.feature_pack_id,
              feature.task_id, feature.lead_time_bucket_or_horizon, feature.ordered_feature_names, feature.feature_units) ==
             (manifest.cell_manifest_id, manifest.profile_id, manifest.scope_id, manifest.feature_pack_id,
              manifest.task_id, manifest.horizon_or_lead_bucket, manifest.ordered_feature_names, manifest.feature_units),
             "PROBABILITY_SOURCE_FEATURE_MANIFEST_JOIN")
        need(not any(feature.feature_missing_bitmap) and
             label.label_contract_id == manifest.label_contract_id and
             feature.dependence_cluster_id == label.dependence_cluster_id and
             feature.contract_id == label.contract_or_decision_id, "PROBABILITY_SOURCE_TARGET_JOIN")
        refs = (feature.source_snapshot_ref, feature.source_rights_receipt_ref, feature.pit_receipt_ref,
                feature.freshness_receipt_ref, feature.book_continuity_receipt_ref, feature.capability_receipt_ref,
                feature.contract_semantics_ref, label.authority_receipt_ref,
                *((label.accounting_receipt_ref,) if label.accounting_receipt_ref is not None else ()))
        need(set(refs) <= dependencies, "PROBABILITY_SOURCE_UNACCEPTED_DEPENDENCY")
        need(_probability_datetime_ns_v1(feature.available_to_strategy_at_utc) <= snapshot.read_ns and
             _probability_datetime_ns_v1(label.decision_available_at_utc) <= snapshot.read_ns, "PROBABILITY_SOURCE_FUTURE_INPUT")
        if manifest.task_id == "PM-SETTLEMENT-YES-V2":
            need(label.target_kind == "BINARY" and label.target_evidence_class == "REALIZED",
                 "PROBABILITY_SETTLEMENT_TARGET_AUTHORITY")
        elif manifest.task_id in ("PM-TLD-CASH-V2", "PM-PORR-CASH-V2"):
            need(label.target_kind == "CONTINUOUS" and label.accounting_receipt_ref is not None,
                 "PROBABILITY_ECONOMIC_TARGET_AUTHORITY")
        elif manifest.task_id == "PM-QAML-MARKOUT-V2":
            need(label.target_kind == "CONTINUOUS", "PROBABILITY_MARKOUT_TARGET_AUTHORITY")
        elif manifest.task_id in ("PM-TLD-POSITIVE-CASH-V2", "PM-PORR-POSITIVE-CASH-V2"):
            need(label.target_kind == "BINARY" and label.accounting_receipt_ref is not None,
                 "PROBABILITY_ECONOMIC_TARGET_AUTHORITY")
        elif manifest.task_id == "PM-QAML-FILL-V2":
            need(label.target_kind == "BINARY" and label.target_evidence_class == "REALIZED",
                 "PROBABILITY_FILL_TARGET_AUTHORITY")
    _probability_bind_pit_rows_v1(source, rows, dependencies, snapshot.read_ns)
    if "drift_parameters" in source:
        need(type(source["drift_parameters"]) is MappingProxyType and
             type(source["drift_parameters"].get("family")) is _ProbabilityBinaryDriftFamilyV1,
             "PROBABILITY_DRIFT_PARAMETER_TYPES")
        indicators = source["drift_indicators"]
        family = source["drift_parameters"]["family"]
        need(type(indicators) is tuple and len(indicators) == len(rows), "PROBABILITY_DRIFT_INDICATOR_COVERAGE")
        for original, indicator in zip(rows, indicators, strict=True):
            need(type(indicator) is tuple and len(indicator) == 5 and indicator[0] == original[0],
                 "PROBABILITY_DRIFT_INDICATOR_ROW")
            _, missing, ood, composition, refs = indicator
            need(type(missing) is tuple and len(missing) == len(family.missingness_names) and
                 type(composition) is tuple and len(composition) == len(family.composition_names) and
                 all(type(value) is int and value in (0, 1) for value in (*missing, ood, *composition)),
                 "PROBABILITY_DRIFT_INDICATOR_VALUES")
            _probability_projection_names_v1(refs, "PROBABILITY_DRIFT_INDICATOR_EVIDENCE")
            need(set(refs) <= dependencies, "PROBABILITY_DRIFT_INDICATOR_UNACCEPTED_DEPENDENCY")
    # The source owner retains PIT nanoseconds, task-specific semantics and
    # deterministic OOD/continuity outcomes as original committed dependencies.
    # This projection cannot manufacture those receipts from a vector's type.
    need(source["input_lock_ref"] == fence.scope.input_lock_ref and source["binding_ref"] == snapshot.snapshot_ref and
         source is fence._construction_inputs_v1, "PROBABILITY_SOURCE_ORIGINAL_LOCK")
    entry["metadata"]["construction_source"] = source
    entry["metadata"]["source_row_ids"] = tuple(row[0] for row in rows)
    need(_probability_construction_pin_v1(source, max_nodes=budget.max_total_bytes) == source_pin,
         "PROBABILITY_CONSTRUCTION_SOURCE_CHANGED_DURING_ADMISSION")
    entry["metadata"]["construction_pin"] = source_pin
    entry["metadata"]["construction_pin_limit"] = budget.max_total_bytes
    result = (materialized, source)
    fence._check_v1(original_cut=entry["cut"], dependency_refs=entry["dependencies"], evaluated_ns=time.time_ns(),
                    deadline_ns=read_request.limits.deadline_monotonic_ns)
    return result


def _probability_bind_prediction_partitions_v1(source, snapshot, parameters, *, target_kind):
    from .models import _probability_datetime_ns_v1
    need = _probability_require_v1
    need(target_kind in ("BINARY", "CONTINUOUS"), "PROBABILITY_TARGET_KIND")
    target_type = int if target_kind == "BINARY" else Decimal
    for key in ("fit_clusters", "calibration_clusters"):
        need(type(parameters[key]) is tuple and all(type(cluster) is tuple and len(cluster) == 6
             and type(cluster[5]) is tuple for cluster in parameters[key]), "PROBABILITY_CLUSTER_SOURCE")
    original_rows = {row_id: (feature, label) for row_id, feature, label in source["feature_rows"]}
    reference = {cluster.cluster_id: cluster for cluster in snapshot.model.reference_clusters}
    need(tuple(cluster[0] for cluster in (*parameters["fit_clusters"], *parameters["calibration_clusters"])) ==
         tuple(reference), "PROBABILITY_PREDICTION_REFERENCE_COHORT")
    final_clusters = parameters["final_cluster_ids"]
    need(type(final_clusters) is tuple and
         tuple(dict.fromkeys(feature.dependence_cluster_id for _, feature, _ in source["feature_rows"]
             if feature.dependence_cluster_id in final_clusters)) == final_clusters and
         tuple(row_id for row_id, feature, _ in source["feature_rows"]
             if feature.dependence_cluster_id in final_clusters) == parameters["final_row_ids"],
         "PROBABILITY_ORIGINAL_FINAL_COHORT")
    for key, cutoff_key in (("fit_clusters", "fit_cutoff_ns"), ("calibration_clusters", "calibration_cutoff_ns")):
        for cluster in parameters[key]:
            need(type(cluster) is tuple and len(cluster) == 6 and type(cluster[5]) is tuple, "PROBABILITY_CLUSTER_SOURCE")
            parent = reference[cluster[0]]
            need((cluster[1], cluster[2], tuple(row[0] for row in cluster[5])) ==
                 (parent.available_ns, parent.maturity_ns, parent.row_ids), "PROBABILITY_ORIGINAL_CLUSTER_METADATA")
            for row_id, feature_values, target in cluster[5]:
                need(row_id in original_rows, "PROBABILITY_UNKNOWN_ORIGINAL_ROW")
                feature, label = original_rows[row_id]
                need(label.censor_state == "MATURED" and label.target_kind == target_kind and
                     cluster[0] == feature.dependence_cluster_id and
                     type(feature_values) is tuple and all(type(value) is float for value in feature_values) and
                     tuple(value.hex() for value in feature_values) == tuple(value.hex() for value in feature.ordered_feature_values) and
                     type(target) is target_type and target == label.target_value and
                     max(_probability_datetime_ns_v1(label.label_matured_at_utc),
                         _probability_datetime_ns_v1(label.label_became_knowable_at_utc)) <= cluster[2] <= parameters[cutoff_key] and
                     _probability_datetime_ns_v1(feature.available_to_strategy_at_utc) <= cluster[1],
                     "PROBABILITY_ORIGINAL_FEATURE_LABEL_PROJECTION")


def _construct_probability_prediction_result_v1(*, construction, issuer_resolver, write_request,
                                               producer_request, spine_metadata, readback_request):
    """Fit once outside reads, finalize once, then append the issued result once."""
    from .errors import OwnerAdapterError
    from .models import ProbabilityPredictionArtifactWriteRequestV1, ProbabilityPredictionReadRequestV1, _probability_datetime_ns_v1
    from .agent_policy import _probability_issuer_pin_v1
    from .protocols import ProbabilityIssuerReadRequestV1
    from .implementation_registry import (_probability_construct_prediction_bank_v1,
        _probability_read_locked_prediction_bank_v1, _probability_numerical_work_v1)
    from .persistence import _finalize_prediction_artifact_v1
    from .persistence import _probability_read_check_v1
    from .receipts import ProbabilityProducerControlReceiptV1, _probability_control_record_v1
    need = _probability_require_v1
    fence = issuer_resolver._probability_source_fence_v1
    if type(fence) is not _ProbabilityDependencyFenceV1 or fence._artifact_writer_v1 is None:
        raise OwnerAdapterError(ReasonCode.OWNER_DATA_MISSING, "PROBABILITY_ARTIFACT_WRITER_UNAVAILABLE")
    need(type(construction) is tuple and len(construction) == 2 and
         type(write_request) is ProbabilityPredictionArtifactWriteRequestV1 and
         type(producer_request) is ProbabilityIssuerReadRequestV1, "PROBABILITY_PREDICTION_CONSTRUCTION_TYPES")
    write_request.__post_init__()
    producer_request.__post_init__()
    need(type(readback_request) is ProbabilityPredictionReadRequestV1 and
         (readback_request.scope, readback_request.result_ref, readback_request.review_ref) ==
         (fence.scope, write_request.result_ref, None), "PROBABILITY_PREDICTION_READBACK_REQUEST")
    _probability_read_check_v1(readback_request)
    materialized, source = construction
    snapshot = materialized["snapshot"]
    entry = fence._registered_v1(snapshot, kind="MATERIALIZATION", evaluated_ns=time.time_ns())
    need(entry["metadata"].get("construction_source") is source and source is fence._construction_inputs_v1 and
         entry["metadata"]["materialization"] is materialized and snapshot.result is None,
         "PROBABILITY_ORIGINAL_PREDICTION_INPUTS")
    need(_probability_construction_pin_v1(source, max_nodes=entry["metadata"]["construction_pin_limit"]) ==
         entry["metadata"]["construction_pin"], "PROBABILITY_CONSTRUCTION_SOURCE_CHANGED")
    write_pin = _probability_construction_pin_v1(write_request, max_nodes=entry["value_node_limit"])
    readback_pin = _probability_construction_pin_v1(readback_request, max_nodes=entry["value_node_limit"])
    need(source["manifest"].task_id in ("PM-SETTLEMENT-YES-V2", "PM-QAML-FILL-V2",
         "PM-TLD-POSITIVE-CASH-V2", "PM-PORR-POSITIVE-CASH-V2"), "PROBABILITY_BINARY_PREDICTION_TASK")
    need((write_request.scope, producer_request.scope, producer_request.role, producer_request.subject_refs) ==
         (fence.scope, fence.scope, "COMPUTATION", (write_request.result_ref,)), "PROBABILITY_PREDICTION_PRODUCER_JOIN")
    need(set(entry["dependencies"]) <= set(write_request.dependency_refs) and
         write_request.valid_until_ns <= entry["expiry"], "PROBABILITY_PREDICTION_WRITE_LIFETIME")
    # Resolve the original COMPUTATION principal before any numerical operation,
    # close that view, and retain its actual controlling domain and finite grant.
    requests = (*entry["view"]["requests"], producer_request)
    with issuer_resolver._resolve_probability_issuer_context_v1(requests, evaluated_ns=time.time_ns()) as issuer_snapshot:
        admissions = tuple(issuer_resolver._admit_probability_issuer_v1(request, trusted_snapshot=issuer_snapshot)
                           for request in requests)
    view = issuer_resolver._probability_last_issuer_view_v1
    producer_index = len(requests) - 1
    producer_context = issuer_snapshot.entries[producer_index][0]
    producer_admission = admissions[producer_index]
    expiry = min(entry["expiry"], producer_admission.valid_until_ns, write_request.valid_until_ns)
    need(set(producer_admission.authority_dependency_refs) <= set(write_request.dependency_refs) and
         write_request.valid_until_ns <= expiry, "PROBABILITY_COMPUTATION_WRITE_DEPENDENCIES")
    parameters = source["prediction_parameters"]
    need(type(parameters) is MappingProxyType and set(parameters) == {
        "fit_clusters", "calibration_clusters", "final_cluster_ids", "final_row_ids", "final_start_ns",
        "feature_names", "requests", "input_lock_id", "prediction_input_lock_id", "plan_id", "master_seed",
        "replicate_count", "method", "block_length", "fit_cutoff_ns", "calibration_cutoff_ns", "embargo_ns",
        "max_plan_cells", "max_expanded_rows", "max_prediction_cells", "max_feature_cells", "max_fit_calls"},
        "PROBABILITY_PREDICTION_ACCEPTED_POLICY")
    need(entry["metadata"]["intent"] == _probability_canonical_data_v1({
        **_probability_json_data_v1(entry["metadata"]["intent"].encode("utf-8"), materialized["limits"].max_record_bytes),
        "result_ref": write_request.result_ref}), "PROBABILITY_ORIGINAL_RESULT_ID")
    need(parameters["input_lock_id"] == fence.scope.input_lock_ref and
         parameters["feature_names"] == snapshot.model.feature_names and
         parameters["replicate_count"] == snapshot.model.replicate_count,
         "PROBABILITY_PREDICTION_POLICY_JOIN")
    _probability_bind_prediction_partitions_v1(source, snapshot, parameters, target_kind="BINARY")
    started = time.time_ns()
    fence._check_v1(original_cut=entry["cut"], dependency_refs=write_request.dependency_refs,
                    evaluated_ns=started, deadline_ns=write_request.deadline_monotonic_ns)
    need(snapshot.read_ns <= started and len(fence._registrations) + 1 <= fence.max_prepared and
         write_request.result_ref not in fence._uncertain, "PROBABILITY_RESULT_PREALLOCATION")
    need(write_request.result_ref not in fence._reserved_result_refs_v1 and
         len(fence._reserved_result_refs_v1) < fence.max_prepared, "PROBABILITY_RESULT_ALREADY_ATTEMPTED_OR_CAPACITY")
    fence._reserved_result_refs_v1[write_request.result_ref] = write_request
    work = {"base_fit_calls": 0, "calibration_fit_calls": 0, "calibration_verification_calls": 0}
    with _probability_numerical_work_v1(deadline_ns=write_request.deadline_monotonic_ns, valid_until_ns=expiry):
        bank = _probability_construct_prediction_bank_v1(**parameters, work=work)
        _probability_read_locked_prediction_bank_v1(bank, input_lock_id=parameters["input_lock_id"],
            prediction_input_lock_id=parameters["prediction_input_lock_id"], feature_names=parameters["feature_names"],
            requests=parameters["requests"])
    completed = time.time_ns()
    need(_probability_construction_pin_v1(source, max_nodes=entry["metadata"]["construction_pin_limit"]) ==
         entry["metadata"]["construction_pin"], "PROBABILITY_CONSTRUCTION_SOURCE_CHANGED")
    need(_bounded_probability_json_v1(bank["original_model"], max_bytes=materialized["limits"].max_record_bytes) ==
         snapshot.model.export_text, "PROBABILITY_ORIGINAL_ACCEPTED_MODEL_EXPORT")
    fence._check_v1(original_cut=entry["cut"], dependency_refs=write_request.dependency_refs,
                    evaluated_ns=completed, deadline_ns=write_request.deadline_monotonic_ns)
    # Retain the same bank/request/writer before a possibly irreversible seal.
    orphan = {"bank": bank, "write_request": write_request, "writer": fence._artifact_writer_v1,
              "status": "ARTIFACT_FINALIZATION_PENDING", "work": dict(work)}
    entry["metadata"]["prediction_attempt"] = orphan
    def check_artifact_source():
        need(_probability_construction_pin_v1(write_request, max_nodes=entry["value_node_limit"]) == write_pin and
             _probability_construction_pin_v1(readback_request, max_nodes=entry["value_node_limit"]) == readback_pin and
             _probability_issuer_pin_v1(view["requests"], view["snapshot"]) == view["pin"] and
             source is fence._construction_inputs_v1, "PROBABILITY_PREDICTION_ORIGINAL_INVOCATION_CHANGED")
        fence._check_v1(original_cut=entry["cut"], dependency_refs=write_request.dependency_refs,
                        evaluated_ns=time.time_ns(), deadline_ns=write_request.deadline_monotonic_ns)
        need(time.time_ns() < expiry, "PROBABILITY_FINALIZATION_ISSUER_EXPIRED")

    try:
        seal = _finalize_prediction_artifact_v1(bank=bank, request=write_request,
            artifact_writer=fence._artifact_writer_v1, check_current=check_artifact_source)
    except BaseException:
        orphan["status"] = "ARTIFACT_FINALIZATION_UNCONFIRMED"
        fence._uncertain[write_request.result_ref] = orphan
        raise
    orphan.update(status="ARTIFACT_FINALIZED_RECEIPT_UNCOMMITTED", seal=seal)
    try:
        now = time.time_ns()
        fence._check_v1(original_cut=entry["cut"], dependency_refs=write_request.dependency_refs,
                        evaluated_ns=now, deadline_ns=write_request.deadline_monotonic_ns)
        expiry = min(expiry, seal.valid_until_ns)
        need(now < expiry, "PROBABILITY_FINALIZED_ARTIFACT_EXPIRED")
        body = dict(artifact_ref=seal.artifact_ref, artifact_byte_count=seal.byte_count, artifact_frame_count=seal.frame_count,
            input_lock_id=fence.scope.input_lock_ref, prediction_input_lock_id=parameters["prediction_input_lock_id"],
            plan_id=parameters["plan_id"], producer_ref=producer_request.issuer_ref,
            producer_control_domain_ref=producer_context.control_domain_ref, started_ns=started, completed_ns=completed,
            input_available_ns=snapshot.read_ns)
        payload = ProbabilityProducerControlReceiptV1(schema_version="PROBABILITY_PRODUCER_CONTROL_V1", control_kind="PREDICTION_RESULT",
            scope=fence.scope, effective_ns=completed, recorded_ns=now, available_ns=max(now, seal.observed_ns),
            dependency_refs=write_request.dependency_refs, valid_until_ns=expiry, body=body)
        record = _probability_control_record_v1(record_id=write_request.result_ref, payload=payload, **spine_metadata)
        issued = fence._register_v1(record, kind="APPEND", view=view, dependency_refs=write_request.dependency_refs,
            valid_until_ns=expiry, value_node_limit=materialized["read_request"].limits.max_total_bytes,
            metadata={"committed_snapshot": materialized["committed_snapshot"], "artifact": orphan,
                                           "producer_admission": producer_admission})
        committed = _commit_probability_issued_record_v1(fence=fence, record=record, entry=issued,
            read_request=materialized["read_request"], readback_request=readback_request)

        orphan["status"] = "ARTIFACT_AND_RECEIPT_CONFIRMED_COMMITTED"
        return committed
    except BaseException:
        # A valid seal survives every subsequent failure. Hold the original
        # orphan/attempt; no automatic abort, deletion, refit or reseal.
        fence._uncertain.setdefault(write_request.result_ref, orphan)
        raise


def _construct_probability_continuous_result_v1(*, construction, issuer_resolver, producer_request, deadline_ns):
    """Complete Huber refits and the separate original conformal diagnostic.

    Its original registered outputs remain unaccepted research results. The
    separate computation/review owners must adjudicate subsequent evidence use.
    """
    from .implementation_registry import (_probability_construct_continuous_bank_v1,
        _probability_read_continuous_bank_v1, _probability_numerical_work_v1)
    from .errors import OwnerAdapterError
    from .models import ContinuousScoreResultV2
    from .protocols import ProbabilityIssuerReadRequestV1
    need = _probability_require_v1
    fence = issuer_resolver._probability_source_fence_v1
    need(type(fence) is _ProbabilityDependencyFenceV1 and type(construction) is tuple and len(construction) == 2,
         "PROBABILITY_CONTINUOUS_ORIGINAL_CONSTRUCTION")
    materialized, source = construction
    snapshot = materialized["snapshot"]
    entry = fence._registered_v1(snapshot, kind="MATERIALIZATION", evaluated_ns=time.time_ns())
    need(entry["metadata"]["materialization"] is materialized and
         entry["metadata"].get("construction_source") is source and source is fence._construction_inputs_v1 and
         _probability_construction_pin_v1(source, max_nodes=entry["metadata"]["construction_pin_limit"]) ==
         entry["metadata"]["construction_pin"], "PROBABILITY_CONTINUOUS_SOURCE_CHANGED")
    manifest = source["manifest"]
    need(snapshot.result is None and snapshot.model.model_kind == "HUBER" and manifest.task_id in
         ("PM-QAML-MARKOUT-V2", "PM-TLD-CASH-V2", "PM-PORR-CASH-V2"), "PROBABILITY_CONTINUOUS_TASK")
    intent = _probability_json_data_v1(entry["metadata"]["intent"].encode("utf-8"), materialized["limits"].max_record_bytes)
    result_ref = intent["result_ref"]
    _probability_projection_text_v1(result_ref, "PROBABILITY_CONTINUOUS_RESULT_REF")
    need(type(producer_request) is ProbabilityIssuerReadRequestV1 and
         (producer_request.scope, producer_request.role, producer_request.subject_refs) ==
         (fence.scope, "COMPUTATION", (result_ref,)), "PROBABILITY_CONTINUOUS_COMPUTATION_SCOPE")
    parameters = source["continuous_parameters"]
    numerical_names = {"fit_clusters", "calibration_clusters", "final_row_ids", "final_cluster_ids", "final_start_ns",
        "feature_names", "requests", "fit_cutoff_ns", "calibration_cutoff_ns", "embargo_ns", "max_rows", "max_feature_cells",
        "unit", "input_lock_id", "prediction_input_lock_id", "plan_id", "master_seed", "replicate_count",
        "method", "block_length", "max_plan_cells", "max_expanded_rows", "max_prediction_cells", "max_fit_calls",
        "resource_envelope", "allocation_calculation", "work_roster"}
    need(type(parameters) is MappingProxyType and set(parameters) == numerical_names |
          {"uncertainty_packet_ref", "evidence_level", "use_limit_ref"},
          "PROBABILITY_CONTINUOUS_ACCEPTED_PARAMETERS")
    _probability_projection_integer_v1(parameters["max_fit_calls"], "PROBABILITY_CONTINUOUS_FIT_BUDGET", 1)
    _probability_projection_integer_v1(parameters["master_seed"], "PROBABILITY_CONTINUOUS_ORIGINAL_SEED", 0)
    _probability_projection_integer_v1(deadline_ns, "PROBABILITY_CONTINUOUS_DEADLINE", 1)
    for name in ("unit", "uncertainty_packet_ref", "evidence_level", "use_limit_ref"):
        _probability_projection_text_v1(parameters[name], "PROBABILITY_CONTINUOUS_BASIS")
    need(parameters["feature_names"] == snapshot.model.feature_names and
          type(parameters["replicate_count"]) is int and parameters["replicate_count"] == snapshot.model.replicate_count and
          parameters["input_lock_id"] == fence.scope.input_lock_ref and
          parameters["use_limit_ref"] in entry["dependencies"] and
         all(label.target_unit == parameters["unit"] for _, _, label in source["feature_rows"]),
         "PROBABILITY_CONTINUOUS_UNIT_AND_POLICY")
    _probability_bind_prediction_partitions_v1(source, snapshot, parameters, target_kind="CONTINUOUS")
    need(type(parameters["requests"]) is tuple and parameters["requests"] and
         len(fence._registrations) + len(parameters["requests"]) <= fence.max_prepared and
         result_ref not in fence._reserved_result_refs_v1 and len(fence._reserved_result_refs_v1) < fence.max_prepared,
         "PROBABILITY_CONTINUOUS_RESULT_CAPACITY")
    requests = (*entry["view"]["requests"], producer_request)
    with issuer_resolver._resolve_probability_issuer_context_v1(requests, evaluated_ns=time.time_ns()) as issued:
        admissions = tuple(issuer_resolver._admit_probability_issuer_v1(request, trusted_snapshot=issued) for request in requests)
    view = issuer_resolver._probability_last_issuer_view_v1
    expiry = min(entry["expiry"], *(admission.valid_until_ns for admission in admissions))
    dependencies = tuple(dict.fromkeys((*entry["dependencies"],
        *(ref for admission in admissions for ref in admission.authority_dependency_refs))))
    started = time.time_ns()
    fence._check_v1(original_cut=entry["cut"], dependency_refs=dependencies, evaluated_ns=started, deadline_ns=deadline_ns)
    fence._reserved_result_refs_v1[result_ref] = producer_request
    work = {"base_fit_calls": 0, "calibration_fit_calls": 0, "calibration_verification_calls": 0}
    numerical_attempt = {}
    attempt = {"state": "NUMERICAL_PENDING", "result_ref": result_ref, "work": work,
               "numerical_attempt": numerical_attempt, "producer_request": producer_request}
    entry["metadata"]["continuous_attempt"] = attempt
    try:
        with _probability_numerical_work_v1(deadline_ns=deadline_ns, valid_until_ns=expiry):
            bank, diagnostic = _probability_construct_continuous_bank_v1(
                **{name: parameters[name] for name in numerical_names},
                max_model_bytes=materialized["limits"].max_model_bytes,
                max_record_bytes=materialized["limits"].max_record_bytes,
                max_total_bank_bytes=materialized["limits"].max_total_bank_bytes,
                deadline_ns=min(deadline_ns, materialized["read_request"].limits.deadline_monotonic_ns),
                work=work, attempt=numerical_attempt)
            attempt.update(state=bank.state, bank=bank, diagnostic=diagnostic)
            bootstrap_bounds = _probability_read_continuous_bank_v1(bank,
                input_lock_id=parameters["input_lock_id"], prediction_input_lock_id=parameters["prediction_input_lock_id"],
                feature_names=parameters["feature_names"], requests=parameters["requests"], unit=parameters["unit"],
                max_record_bytes=materialized["limits"].max_record_bytes)
            if bootstrap_bounds is None:
                raise OwnerAdapterError(ReasonCode.OWNER_DATA_MISSING, "PROBABILITY_CONTINUOUS_UNCERTAINTY_UNAVAILABLE")
        completed = time.time_ns()
        need(started <= completed < expiry and diagnostic["fit_calls"] == 1 and diagnostic["calibrator_fit_calls"] == 0 and
              work == dict(bank.actual_fit_calls) == {"base_fit_calls": parameters["replicate_count"] + 1,
                  "calibration_fit_calls": 0, "calibration_verification_calls": 0} and
              (bank.plan_id, bank.master_seed, bank.replicate_count, bank.method, bank.block_length) ==
              tuple(parameters[name] for name in ("plan_id", "master_seed", "replicate_count", "method", "block_length")) and
              bank.original_predictions == diagnostic["original_predictions"] and
             _bounded_probability_json_v1(diagnostic["model"], max_bytes=materialized["limits"].max_model_bytes) ==
             snapshot.model.export_text, "PROBABILITY_CONTINUOUS_MODEL_AND_WORK_BINDING")
        need(source is fence._construction_inputs_v1 and entry["metadata"]["construction_source"] is source and
             _probability_construction_pin_v1(source, max_nodes=entry["metadata"]["construction_pin_limit"]) ==
             entry["metadata"]["construction_pin"], "PROBABILITY_CONTINUOUS_SOURCE_CHANGED")
        results = tuple(ContinuousScoreResultV2(request_id, manifest.task_id, fence.scope.model_artifact_ref,
            Decimal(point), Decimal(lower), Decimal(upper), parameters["unit"], parameters["uncertainty_packet_ref"],
            parameters["evidence_level"], parameters["use_limit_ref"], "SCORE_RESEARCH_ONLY")
            for request_id, point, lower, upper in diagnostic["decimal34_values"])
        registered = []
        try:
            for result in results:
                registered.append(fence._register_v1(result, kind="CANDIDATE", view=view,
                    dependency_refs=dependencies, valid_until_ns=expiry,
                    value_node_limit=materialized["read_request"].limits.max_total_bytes,
                    metadata={"construction": construction, "result_ref": result_ref, "diagnostic": diagnostic,
                              "continuous_refit_bank": bank, "descriptive_bootstrap_bounds": bootstrap_bounds,
                              "started_ns": started, "completed_ns": completed, "issuer": admissions[-1]}))
            for result in results:
                fence._registered_v1(result, kind="CANDIDATE", evaluated_ns=time.time_ns())
            fence._check_v1(original_cut=entry["cut"], dependency_refs=dependencies,
                            evaluated_ns=time.time_ns(), deadline_ns=deadline_ns)
        except BaseException:
            for registered_entry in registered:
                if fence._registrations.get(id(registered_entry["object"])) is registered_entry:
                    del fence._registrations[id(registered_entry["object"])]
            raise
        attempt.update(state="RESEARCH_RESULT_REGISTERED", completed_ns=completed)
    except BaseException as exc:
        attempt.update(state="UNAVAILABLE_RETAINED_ATTEMPT", failure=exc)
        raise
    # ContinuousScoreResultV2 keeps its original conformal bounds and units.
    # Descriptive bootstrap bounds remain a separately named research projection;
    # neither is economic acceptance or a [0,1] probability packet.
    return {"results": results, "diagnostic": diagnostic, "refit_bank": bank,
            "descriptive_bootstrap_bounds": bootstrap_bounds, "result_ref": result_ref,
            "started_ns": started, "completed_ns": completed, "accepted": False,
            "source_authentication": False, "model_use_authorized": False}


def _apply_probability_revocation_v1(*, fence, notice, record_ref, source_request, read_request, readback_request, spine_metadata):
    """Apply an already delivered source notice; only exact committed readback acknowledges it."""
    from .receipts import ProbabilityProducerControlReceiptV1, _probability_control_record_v1, _probability_control_projection_v1
    from .protocols import ProbabilityIssuerReadRequestV1
    need = _probability_require_v1
    fence._retain_notice_v1(notice)
    need(type(source_request) is ProbabilityIssuerReadRequestV1 and source_request.role == "SOURCE_RIGHTS" and
         source_request.issuer_ref == notice.issuer_ref and source_request.scope == fence.scope and
         read_request.purpose == readback_request.purpose == "READ_CURRENT_STATE", "PROBABILITY_REVOCATION_ISSUER")
    with fence.issuer_resolver._resolve_probability_issuer_context_v1((source_request,), evaluated_ns=time.time_ns()) as source_snapshot:
        admission = fence.issuer_resolver._admit_probability_issuer_v1(source_request, trusted_snapshot=source_snapshot)
    view = fence.issuer_resolver._probability_last_issuer_view_v1
    with _probability_owned_context_v1(fence.persistence.load_committed_probability_producer_state_v1(read_request)) as snapshot:
        prior = snapshot.records_by_ref.get(record_ref)
        if prior is not None:
            body = prior.typed_payload.body
            need(prior.typed_payload.control_kind == "REVOCATION_APPLICATION" and
                 (body["notice_id"], body["issuer_ref"], body["stream_ref"], body["stream_ordinal"], body["observed_ns"],
                  body["invalidated_dependency_refs"], prior.typed_payload.effective_ns) ==
                 (notice.notice_id, notice.issuer_ref, notice.stream_ref, notice.stream_ordinal, notice.observed_ns,
                  notice.dependency_refs, notice.effective_ns), "PROBABILITY_REVOCATION_REPEAT_CONFLICT")
    if prior is not None:
        fence._pending_notices.pop(notice.notice_id)
        fence._source_synchronized_v1 = False
        return prior
    ordinal = snapshot.revocation_records[-1].sequence if snapshot.revocation_records else fence.baseline_ordinal
    need(notice.stream_ordinal == ordinal + 1 and len(snapshot.revocation_records) < fence.max_records,
         "PROBABILITY_REVOCATION_GAP_OR_CAPACITY")
    now = time.time_ns()
    dependencies = tuple(dict.fromkeys((notice.notice_id, notice.issuer_ref, fence.baseline_ref,
                                      *admission.authority_dependency_refs)))
    body = dict(notice_id=notice.notice_id, issuer_ref=notice.issuer_ref, stream_ref=notice.stream_ref,
                stream_ordinal=notice.stream_ordinal, observed_ns=notice.observed_ns, baseline_ref=fence.baseline_ref,
                invalidated_dependency_refs=notice.dependency_refs)
    payload = ProbabilityProducerControlReceiptV1(schema_version="PROBABILITY_PRODUCER_CONTROL_V1", control_kind="REVOCATION_APPLICATION",
        scope=fence.scope, effective_ns=notice.effective_ns, recorded_ns=now, available_ns=now,
        dependency_refs=dependencies, valid_until_ns=None, body=body)
    record = _probability_control_record_v1(record_id=record_ref, payload=payload, **spine_metadata)
    canonical = _bounded_probability_json_v1(_probability_control_projection_v1(record), max_bytes=read_request.limits.max_frame_bytes)
    entry = {"object": record, "fields": tuple(getattr(record, name) for name in record.__dataclass_fields__),
        "kind": "APPEND", "cut": fence.cut, "view": view, "dependencies": dependencies,
        "expiry": admission.valid_until_ns, "metadata": {"committed_snapshot": snapshot},
        "reader": fence.reader, "policy": fence.policy, "last_ns": now}
    issued = dict(records=(record,), canonical={record_ref: canonical}, transaction=None, cut=fence.cut,
        dependencies=dependencies, expiry=admission.valid_until_ns, deadline=read_request.limits.deadline_monotonic_ns,
        readback_request=readback_request, entry=entry, status="PREPARED", delivery=notice)
    transaction = None
    attempted = False
    with fence._owned_v1():
        need(fence._active_append is None and not fence._uncertain and len(fence._registrations) < fence.max_prepared,
             "PROBABILITY_REVOCATION_BUSY_OR_CAPACITY")
        fence._check_delivery_v1(issued)
        fence._registrations[id(record)] = entry
        fence._active_append = issued
        try:
            transaction = fence.persistence.begin_transaction()
            issued["transaction"] = transaction
            current = fence.persistence._probability_append_snapshot_v1(transaction, read_request)
            need(tuple(row.record_id for row in current.revocation_records) == tuple(row.record_id for row in snapshot.revocation_records),
                 "PROBABILITY_REVOCATION_HEAD_CHANGED")
            fence.persistence.insert_receipt_record(transaction, record)
            fence._append_guard_v1(transaction, record)
            fence._uncertain[record_ref] = issued
            attempted = True
            fence.persistence._probability_commit_attempt_v1 = transaction
            transaction.commit()
            issued["status"] = "COMMIT_RETURNED"
        except BaseException as error:
            if not attempted and transaction is not None and transaction.is_active:
                try:
                    transaction.rollback()
                except BaseException as cleanup:
                    fence._uncertain[record_ref] = issued
                    raise BaseExceptionGroup("revocation append and rollback", [error, cleanup])
            raise
        finally:
            fence._active_append = None
            fence.persistence._probability_commit_attempt_v1 = None
    committed = _reconcile_probability_record_v1(fence=fence, record=record, read_request=readback_request)
    fence._pending_notices.pop(notice.notice_id)
    fence._source_synchronized_v1 = False
    return committed


def _run_probability_drift_construction_v1(*, construction, issuer_resolver, intent,
        producer_request, deadline_ns):
    """Original admitted inputs -> actual bounded work -> retained unaccepted result.

    COMPUTATION acceptance and a result-bearing successor binding remain the
    separately invoked existing scoped issuer's operation.
    """
    from dataclasses import replace
    from .implementation_registry import _probability_metric_plans_v1, _probability_numerical_work_v1
    from .models import _probability_datetime_ns_v1
    from .protocols import ProbabilityIssuerReadRequestV1
    need = _probability_require_v1
    fence = issuer_resolver._probability_source_fence_v1
    need(type(fence) is _ProbabilityDependencyFenceV1 and type(construction) is tuple and len(construction) == 2,
         "PROBABILITY_ORIGINAL_DRIFT_CONSTRUCTION")
    materialized, source = construction
    snapshot = materialized['snapshot']
    entry = fence._registered_v1(snapshot, kind='MATERIALIZATION', evaluated_ns=time.time_ns())
    need(entry['metadata']['materialization'] is materialized and entry['metadata'].get('construction_source') is source
         and source is fence._construction_inputs_v1 and snapshot.result is None
         and entry['metadata']['intent'] == _probability_canonical_data_v1(intent), 'PROBABILITY_DRIFT_SOURCE_BINDING')
    need(_probability_construction_pin_v1(source, max_nodes=entry['metadata']['construction_pin_limit']) ==
         entry['metadata']['construction_pin'], 'PROBABILITY_CONSTRUCTION_SOURCE_CHANGED')
    prepared_window = _prepare_probability_window_v1(snapshot, intent, materialized['state'],
        current_owner_epoch=fence.policy_epoch, publication_ns=time.time_ns(), limits=materialized['limits'])
    if prepared_window[-1]['record'] is None:
        need(intent['result_ref'] is None, 'CONSTRUCTION_NOT_READY_HAS_WORK')
        result = {'disposition': 'NOT_READY_NO_TRANSITION', 'result': None, 'model_fits': 0,
                  'accepted': False, 'source_authentication': False, 'model_use_authorized': False}
        fence._check_v1(original_cut=entry['cut'], dependency_refs=entry['dependencies'],
                        evaluated_ns=time.time_ns(), deadline_ns=deadline_ns)
        return result
    need(type(producer_request) is ProbabilityIssuerReadRequestV1 and
         (producer_request.scope, producer_request.role, producer_request.subject_refs) ==
         (fence.scope, 'COMPUTATION', (intent['result_ref'],)), 'PROBABILITY_DRIFT_COMPUTATION_SCOPE')
    parameters = source['drift_parameters']
    need(type(parameters) is MappingProxyType and set(parameters) == {
        'family', 'reference_rows', 'current_rows', 'master_seed', 'method', 'block_length',
        'plan_refs', 'construction_refs', 'max_plan_cells', 'max_primitive_cells',
        'max_diagnostic_rows', 'max_diagnostic_fits'}, 'PROBABILITY_DRIFT_ACCEPTED_PARAMETERS')
    original = {row_id: (feature, label) for row_id, feature, label in source['feature_rows']}
    indicators = {row[0]: row[1:4] for row in source['drift_indicators']}
    for partition in ('reference_rows', 'current_rows'):
        need(type(parameters[partition]) is tuple, 'PROBABILITY_DRIFT_ROW_TYPE')
        for cluster_id, rows in parameters[partition]:
            need(type(rows) is tuple, 'PROBABILITY_DRIFT_ROW_TYPE')
            for row_id, values, target, missing, ood, composition in rows:
                need(row_id in original, 'PROBABILITY_DRIFT_UNKNOWN_SOURCE_ROW')
                feature, label = original[row_id]
                need((missing, ood, composition) == indicators[row_id] and
                     type(missing) is tuple and type(composition) is tuple and
                     all(type(value) is int and value in (0, 1) for value in (*missing, ood, *composition)),
                     'PROBABILITY_DRIFT_ORIGINAL_INDICATORS')
                need(feature.dependence_cluster_id == cluster_id and type(values) is tuple
                     and all(type(value) is float for value in values)
                     and tuple(value.hex() for value in values) == tuple(value.hex() for value in feature.ordered_feature_values)
                     and label.censor_state == 'MATURED' and label.target_kind == 'BINARY'
                     and type(target) is int and target == label.target_value
                     and max(_probability_datetime_ns_v1(label.label_matured_at_utc),
                             _probability_datetime_ns_v1(label.label_became_knowable_at_utc)) <= snapshot.read_ns,
                     'PROBABILITY_DRIFT_ORIGINAL_FEATURE_LABEL')
    requests = (*entry['view']['requests'], producer_request)
    with issuer_resolver._resolve_probability_issuer_context_v1(requests, evaluated_ns=time.time_ns()) as issued:
        admissions = tuple(issuer_resolver._admit_probability_issuer_v1(request, trusted_snapshot=issued) for request in requests)
    view = issuer_resolver._probability_last_issuer_view_v1
    expiry = min(entry['expiry'], *(admission.valid_until_ns for admission in admissions))
    refs = tuple(dict.fromkeys((*parameters['construction_refs'],
        *(ref for admission in admissions for ref in admission.authority_dependency_refs))))
    started = time.time_ns()
    fence._check_v1(original_cut=entry['cut'], dependency_refs=refs, evaluated_ns=started, deadline_ns=deadline_ns)
    result_ref = intent['result_ref']
    need(result_ref not in fence._reserved_result_refs_v1 and len(fence._reserved_result_refs_v1) < fence.max_prepared,
         'PROBABILITY_RESULT_ALREADY_ATTEMPTED_OR_CAPACITY')
    fence._reserved_result_refs_v1[result_ref] = producer_request
    with _probability_numerical_work_v1(deadline_ns=deadline_ns, valid_until_ns=expiry):
        plans = _probability_metric_plans_v1(master_seed=parameters['master_seed'], replicate_count=snapshot.model.replicate_count,
            reference_clusters=len(parameters['reference_rows']), current_clusters=len(parameters['current_rows']),
            method=parameters['method'], block_length=parameters['block_length'], max_plan_cells=parameters['max_plan_cells'])
        output = _construct_probability_full_family_candidate_v1(snapshot, intent, materialized['state'],
            current_owner_epoch=fence.policy_epoch, started_ns=started, completed_ns=started,
            family=parameters['family'], reference_rows=parameters['reference_rows'], current_rows=parameters['current_rows'],
            reference_plan=plans[0], current_plan=plans[1], plan_refs=parameters['plan_refs'], construction_refs=refs,
            limits=materialized['limits'], max_plan_cells=parameters['max_plan_cells'],
            max_primitive_cells=parameters['max_primitive_cells'], max_diagnostic_rows=parameters['max_diagnostic_rows'],
            max_diagnostic_fits=parameters['max_diagnostic_fits'])
    completed = time.time_ns()
    need(started <= completed < expiry, 'PROBABILITY_DRIFT_COMPLETION_CLOCK')
    _probability_receipt_dependency_binding_v1(snapshot, completed)
    if output['result'] is not None:
        result = replace(output['result'], available_ns=completed)
        output = {**output, 'result': result, 'completed_ns': completed, 'plans': plans}
        fence._register_v1(result, kind='CANDIDATE', view=view, dependency_refs=result.dependency_refs,
            valid_until_ns=expiry, value_node_limit=materialized['read_request'].limits.max_total_bytes,
            metadata={'construction': construction, 'output': output, 'issuer': admissions[-1]})
    fence._check_v1(original_cut=entry['cut'], dependency_refs=refs, evaluated_ns=time.time_ns(), deadline_ns=deadline_ns)
    return output
