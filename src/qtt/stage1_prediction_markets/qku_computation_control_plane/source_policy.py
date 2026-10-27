"""Exact source-state metadata, currentization overlays, and fail-closed policy."""

from __future__ import annotations

import ast
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from enum import StrEnum
import json
import os
import threading
import time
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Mapping

from .errors import ReasonCode, SourcePolicyError
from .context import (
    _native_ident, _native_require, _native_retail_decimal_string_v1,
    _public_counter_v1, _public_nanoseconds_v1, _public_refs_v1,
    _native_utc_nanoseconds,
)
from .models import NO_EFFECTS_V1, NoEffectFlagsV1
from .point_in_time import (
    PITDataContractErrorV1,
    PITReasonCodeV1,
    PointInTimeClocksV1,
    PointInTimeFieldClassV1,
    PointInTimePolicyV1,
)
from .stage1_launch_graph import Stage1VenueProfileIdV1
from .source_rights import reject_secret_material

if TYPE_CHECKING:
    from .persistence import PersistenceAdapterV1


def _public_interval_v1(row, *, known_name="known_at_ns"):
    for name in (known_name, "effective_from_ns", "expires_at_ns"):
        _public_nanoseconds_v1(getattr(row, name))
    end = row.effective_until_ns_or_none
    if end is not None:
        _public_nanoseconds_v1(end)
        _native_require(row.effective_from_ns < end, "public effective interval is empty")
    _native_require(getattr(row, known_name) < row.expires_at_ns, "public source expired before availability")
    _public_counter_v1(row.generation, allow_zero=True)


@dataclass(frozen=True, slots=True)
class PublicDataSourceBindingV1:
    """Data-only candidate. Receipt admission and a current permit remain separate."""

    binding_id: str
    profile_id: Stage1VenueProfileIdV1
    legal_product_ref: str
    source_ids: tuple[str, ...]
    source_contract_versions: tuple[str, ...]
    source_receipt_refs: tuple[str, ...]
    rights_receipt_refs: tuple[str, ...]
    original_evidence_refs: tuple[str, ...]
    review_scope_ref: str
    allowed_operation_ids: tuple[str, ...]
    field_bindings: tuple[tuple[str, str, str, str, str, str], ...]
    known_at_ns: int
    effective_from_ns: int
    effective_until_ns_or_none: int | None
    expires_at_ns: int
    generation: int
    permitted_consumer_ids: tuple[str, ...]

    def __post_init__(self):
        from .receipts import _PUBLIC_OPERATIONS_V1, _PUBLIC_CONSUMERS_V1, _public_profile_v1
        from ..market_data_ingest.binding import PUBLIC_FIELD_TRANSFORMS_V1

        _public_profile_v1(self.profile_id)
        for name in ("binding_id", "legal_product_ref", "review_scope_ref"):
            _native_ident(getattr(self, name))
        for name in ("source_ids", "source_contract_versions", "source_receipt_refs",
                     "rights_receipt_refs", "original_evidence_refs", "allowed_operation_ids",
                     "permitted_consumer_ids"):
            _public_refs_v1(getattr(self, name))
        _native_require(len(self.source_ids) == len(self.source_contract_versions)
                        == len(self.source_receipt_refs) == len(self.rights_receipt_refs),
                        "unbound source/contract/receipt vector")
        _native_require(set(self.allowed_operation_ids) <= _PUBLIC_OPERATIONS_V1[self.profile_id]
                        and set(self.permitted_consumer_ids) <= _PUBLIC_CONSUMERS_V1,
                        "unsupported public source purpose")
        _native_require(type(self.field_bindings) is tuple and 0 < len(self.field_bindings) <= 4096,
                        "missing or unbounded field bindings")
        names = set()
        for row in self.field_bindings:
            _native_require(type(row) is tuple and len(row) == 6, "invalid material field binding")
            name, wire, unit, original, pointer, transform = row
            for value in row:
                _native_ident(value)
            _native_require(name not in names and wire in {
                "STRING", "INTEGER", "DECIMAL_NUMBER", "DECIMAL_TEXT", "BOOLEAN", "OBJECT", "ARRAY"}
                and original in self.original_evidence_refs and pointer.startswith("/")
                and transform in PUBLIC_FIELD_TRANSFORMS_V1,
                "ambiguous or unbound material field")
            names.add(name)
        _public_interval_v1(self)


@dataclass(frozen=True, slots=True)
class SelectedAccountApplicabilityV1:
    profile_id: Stage1VenueProfileIdV1
    account_scope_ref: str
    product_scope_ref: str
    effective_from_ns: int
    effective_until_ns: int
    available_at_ns: int
    source_receipt_refs: tuple[str, ...]
    qualification_ref: str
    generation: int
    fee_profile_id_or_none: str | None
    balance_increment_text_or_none: str | None
    maker_tier_or_none: int | None
    taker_tier_or_none: int | None
    promotion_eligibility_or_none: bool | None
    limitations: tuple[str, ...]

    def __post_init__(self):
        from .receipts import _public_profile_v1

        _public_profile_v1(self.profile_id)
        for name in ("account_scope_ref", "product_scope_ref", "qualification_ref"):
            _native_ident(getattr(self, name))
        for name in ("effective_from_ns", "effective_until_ns", "available_at_ns"):
            _public_nanoseconds_v1(getattr(self, name))
        _native_require(self.effective_from_ns < self.effective_until_ns
                        and self.available_at_ns < self.effective_until_ns,
                        "invalid account applicability interval")
        _public_refs_v1(self.source_receipt_refs)
        _public_refs_v1(self.limitations, allow_empty=True)
        _public_counter_v1(self.generation, allow_zero=True)
        if self.fee_profile_id_or_none is not None:
            _native_ident(self.fee_profile_id_or_none)
        if self.balance_increment_text_or_none is not None:
            _native_require(Fraction(_native_retail_decimal_string_v1(self.balance_increment_text_or_none)) > 0,
                            "account balance increment must be positive")
        for value, maximum in ((self.maker_tier_or_none, 4), (self.taker_tier_or_none, 6)):
            if value is not None:
                _native_require(type(value) is int and 1 <= value <= maximum, "invalid independent account tier")
        if self.promotion_eligibility_or_none is not None:
            _native_require(type(self.promotion_eligibility_or_none) is bool, "invalid promotion fact")
        if any(value is None for value in (self.fee_profile_id_or_none, self.balance_increment_text_or_none,
                                          self.maker_tier_or_none, self.taker_tier_or_none,
                                          self.promotion_eligibility_or_none)):
            _native_require(bool(self.limitations), "missing account facts require unavailable reasons")


def _project_public_account_applicability_facts_v1(*, source_binding, facts, field_bindings, original_ref):
    """Project accepted account facts; the outer packet retains legal product."""
    required = {"account_scope_ref", "product_scope_ref", "effective_from_ns", "effective_until_ns", "generation",
        "fee_profile_id_or_none", "balance_increment_text_or_none", "maker_tier_or_none", "taker_tier_or_none",
        "promotion_eligibility_or_none", "limitations"}
    _native_require(type(facts) in (dict, MappingProxyType) and set(facts) == required,
                    "accepted account applicability has missing or extra fields")
    _native_require(tuple(row for row in field_bindings if row == (
        "account_applicability", "OBJECT", "EVIDENCE_USE_ACCOUNT_APPLICABILITY", original_ref,
        "/account_applicability", "EXACT_IDENTITY")), "account applicability lacks its exact source field")
    _native_require(type(facts["limitations"]) in (tuple,list), "account limitations must be an exact vector")
    for name in ("effective_from_ns", "effective_until_ns"):
        _public_nanoseconds_v1(facts[name])
    _native_require(facts["effective_from_ns"] < facts["effective_until_ns"], "accepted account interval is empty")
    if source_binding.profile_id is not Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT:
        _native_require(facts["maker_tier_or_none"] is None and facts["taker_tier_or_none"] is None,
                        "Retail tiers cannot classify another selected profile")
    if source_binding.profile_id is not Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT:
        _native_require(facts["promotion_eligibility_or_none"] is None,
                        "Gemini promotion cannot classify another selected profile")
    ends = [facts["effective_until_ns"], source_binding.expires_at_ns]
    if source_binding.effective_until_ns_or_none is not None:
        ends.append(source_binding.effective_until_ns_or_none)
    return SelectedAccountApplicabilityV1(source_binding.profile_id, facts["account_scope_ref"], facts["product_scope_ref"],
        max(facts["effective_from_ns"],source_binding.effective_from_ns), min(ends), source_binding.known_at_ns,
        source_binding.source_receipt_refs, original_ref, facts["generation"], facts["fee_profile_id_or_none"],
        facts["balance_increment_text_or_none"], facts["maker_tier_or_none"], facts["taker_tier_or_none"],
        facts["promotion_eligibility_or_none"], tuple(facts["limitations"]))


def compile_accepted_public_account_applicability_v1(*, source_binding, acceptance_results: tuple,
                                                    originals: tuple, review_facts):
    """Data-only account projection through the existing acceptance owner."""
    from ..market_data_ingest.source_dependency import project_accepted_public_field_bindings_v1

    projection = project_accepted_public_field_bindings_v1(source_binding=source_binding,
        acceptance_results=acceptance_results, originals=originals, review_facts=review_facts)
    rows = []
    for bundle in projection[2]:
        packet = bundle["accepted_packet"]
        facts = packet["extracted_fact_payload"].get("account_applicability")
        if facts is not None:
            rows.append(_project_public_account_applicability_facts_v1(source_binding=source_binding, facts=facts,
                field_bindings=source_binding.field_bindings, original_ref=packet["accepted_source_evidence_packet_id"]))
    if len(rows) != 1:
        raise SourcePolicyError(ReasonCode.OWNER_DATA_MISSING, "accepted account applicability missing or conflicting")
    return rows[0]


def _public_accepted_account_state_v1(*, inputs, applicability, native_only, known_as_of_ns, effective_at_ns=None):
    """Retain qualification custody and its conflict-free effective interval."""
    _public_nanoseconds_v1(known_as_of_ns)
    effective_at_ns = known_as_of_ns if effective_at_ns is None else _public_nanoseconds_v1(effective_at_ns)
    matched, refs = [], []
    start, end = applicability.effective_from_ns, applicability.effective_until_ns
    for projection in inputs.get("qualified_source_bindings", ()):
        _native_require(type(projection) is tuple and len(projection) == 5, "malformed retained account source proof")
        source = projection[0]
        if not any(source is row for row in inputs["source_bindings"]) or native_only and projection[4] is not True:
            continue
        for bundle in projection[2]:
            packet = bundle["accepted_packet"]
            facts = packet["extracted_fact_payload"].get("account_applicability")
            if facts is None:
                continue
            candidate = _project_public_account_applicability_facts_v1(source_binding=source, facts=facts,
                field_bindings=source.field_bindings, original_ref=packet["accepted_source_evidence_packet_id"])
            if candidate.available_at_ns > known_as_of_ns:
                continue
            if (candidate.profile_id, candidate.account_scope_ref, candidate.product_scope_ref) != (
                    applicability.profile_id, applicability.account_scope_ref, applicability.product_scope_ref):
                continue
            if candidate != applicability:
                _native_require(not candidate.effective_from_ns <= effective_at_ns < candidate.effective_until_ns,
                                "conflicting current accepted account qualification")
                if candidate.effective_from_ns > effective_at_ns and candidate.effective_from_ns < end:
                    end = candidate.effective_from_ns
                    refs.append(candidate.qualification_ref)
                elif candidate.effective_until_ns <= effective_at_ns and candidate.effective_until_ns > start:
                    start = candidate.effective_until_ns
                    refs.append(candidate.qualification_ref)
            elif (candidate.available_at_ns <= known_as_of_ns < candidate.effective_until_ns
                    and candidate.effective_from_ns <= effective_at_ns < candidate.effective_until_ns):
                matched.append(source)
                refs.append(candidate.qualification_ref)
    return tuple(matched), start, end, tuple(dict.fromkeys(refs))


def _public_accepted_account_sources_v1(**kwargs):
    """Keep the accepted legal-product/class relation in the retained proof."""
    return _public_accepted_account_state_v1(**kwargs)[0]


@dataclass(frozen=True, slots=True)
class PublicRequestRateBindingV1:
    binding_id: str
    profile_id: Stage1VenueProfileIdV1
    operation_classes: tuple[str, ...]
    counter_scope: str
    source_refs: tuple[str, ...]
    effective_from_ns: int
    expires_at_ns: int
    allocation_ref: str
    maximum_requests_per_window: int
    window_ns: int
    minimum_request_interval_ns: int
    token_capacity_or_none: str | None
    token_refill_per_second_or_none: str | None
    token_costs: tuple[tuple[str, str], ...]
    generation: int
    limitations: tuple[str, ...]

    def __post_init__(self):
        from .receipts import _PUBLIC_OPERATIONS_V1, _public_profile_v1

        _public_profile_v1(self.profile_id)
        for name in ("binding_id", "counter_scope", "allocation_ref"):
            _native_ident(getattr(self, name))
        _public_refs_v1(self.operation_classes)
        _native_require(set(self.operation_classes) <= _PUBLIC_OPERATIONS_V1[self.profile_id],
                        "rate allocation includes an unsupported operation")
        _public_refs_v1(self.source_refs)
        _public_refs_v1(self.limitations, allow_empty=True)
        for name in ("maximum_requests_per_window", "window_ns", "minimum_request_interval_ns"):
            _public_counter_v1(getattr(self, name))
        for name in ("effective_from_ns", "expires_at_ns"):
            _public_nanoseconds_v1(getattr(self, name))
        _native_require(self.effective_from_ns < self.expires_at_ns, "expired rate allocation")
        _public_counter_v1(self.generation, allow_zero=True)
        _native_require((self.token_capacity_or_none is None) == (self.token_refill_per_second_or_none is None),
                        "incomplete token allocation")
        for value in (self.token_capacity_or_none, self.token_refill_per_second_or_none):
            if value is not None:
                _native_require(Fraction(_native_retail_decimal_string_v1(value)) > 0, "nonpositive token allocation")
        _native_require(type(self.token_costs) is tuple, "invalid token cost vector")
        names = set()
        for row in self.token_costs:
            _native_require(type(row) is tuple and len(row) == 2, "invalid endpoint token cost")
            name, value = row
            _native_require(name in self.operation_classes and name not in names
                            and Fraction(_native_retail_decimal_string_v1(value)) > 0, "invalid endpoint cost")
            names.add(name)
        _native_require((not self.token_costs) if self.token_capacity_or_none is None
                        else names == set(self.operation_classes), "endpoint costs do not cover the allocation")


@dataclass(frozen=True, slots=True)
class PublicFeeEpochV1:
    epoch_id: str
    profile_id: Stage1VenueProfileIdV1
    product_class: str
    market_scope: tuple[str, ...]
    account_scope_ref_or_none: str | None
    liquidity_role: str
    formula_family: str
    coefficients: tuple[tuple[str, str], ...]
    rounding_rule: str
    effective_from_ns: int
    effective_until_ns_or_none: int | None
    known_at_ns: int
    expires_at_ns: int
    source_observation_refs: tuple[str, ...]
    account_applicability_ref_or_none: str | None
    supersedes_epoch_ref_or_none: str | None
    generation: int
    limitations: tuple[str, ...]

    def __post_init__(self):
        from .receipts import _public_profile_v1

        _public_profile_v1(self.profile_id)
        _native_ident(self.epoch_id)
        _native_ident(self.product_class)
        _public_refs_v1(self.market_scope)
        _public_refs_v1(self.source_observation_refs)
        _public_refs_v1(self.limitations, allow_empty=True)
        for name in ("account_scope_ref_or_none", "account_applicability_ref_or_none", "supersedes_epoch_ref_or_none"):
            if getattr(self, name) is not None:
                _native_ident(getattr(self, name))
        _native_require(self.supersedes_epoch_ref_or_none != self.epoch_id, "self-superseding fee epoch")
        _native_require(type(self.liquidity_role) is str and self.liquidity_role in {"MAKER", "TAKER"},
                        "invalid fee liquidity role")
        fields = {"QUADRATIC": {"rate", "multiplier"}, "RETAIL_COMBO": {"quadratic_rate", "quartic_rate"},
                  "GEMINI_LEGACY_MIN_SIDE": {"rate"}, "EXPLICIT_ZERO": set()}
        _native_require(type(self.formula_family) is str and self.formula_family in fields,
                        "unsupported source fee family")
        _native_require(type(self.coefficients) is tuple, "invalid fee coefficients")
        names = set()
        for row in self.coefficients:
            _native_require(type(row) is tuple and len(row) == 2, "invalid fee coefficient")
            name, value = row
            _native_require(name not in names and name in fields[self.formula_family]
                            and Fraction(_native_retail_decimal_string_v1(value)) > 0,
                            "unsupported or nonpositive fee coefficient; zero requires an explicit zero rule")
            names.add(name)
        _native_require(names == fields[self.formula_family], "missing fee coefficient")
        _native_require(type(self.rounding_rule) is str and self.rounding_rule in {
            "HALF_EVEN_CENT", "CEILING_CENT", "KALSHI_ACCOUNT_GRID", "UNAVAILABLE", "EXACT_ZERO"},
            "unknown fee rounding rule")
        if self.formula_family == "EXPLICIT_ZERO":
            _native_require(self.rounding_rule == "EXACT_ZERO", "zero fee requires an affirmative zero rule")
        if self.formula_family == "RETAIL_COMBO":
            _native_require(self.profile_id is Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT
                            and self.liquidity_role == "TAKER", "combo rule profile/role mismatch")
        if self.formula_family == "GEMINI_LEGACY_MIN_SIDE":
            _native_require(self.profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT,
                            "legacy Gemini fee profile mismatch")
        _public_interval_v1(self)


def _project_public_fee_rule_facts_v1(*, source_binding, facts, field_bindings, original_ref):
    """Project source-accepted, closed fee templates; no account or use grant."""
    required = {"rule_id", "product_class", "market_scope", "account_scope_ref_or_none", "liquidity_role",
        "formula_family", "coefficients", "rounding_rule", "effective_from_ns", "effective_until_ns_or_none",
        "account_applicability_ref_or_none", "supersedes_rule_ref_or_none", "generation", "limitations",
        "native_fee_type_or_none"}
    _native_require(type(facts) in (list, tuple) and 0 < len(facts) <= 4096, "accepted fee rules unavailable")
    projected, identities = [], set()
    for index, row in enumerate(facts):
        _native_require(type(row) in (dict, MappingProxyType) and set(row) == required,
                        "accepted fee rule has missing or extra fields")
        rule_id = _native_ident(row["rule_id"])
        _native_require(rule_id not in identities, "duplicate accepted fee rule identity")
        identities.add(rule_id)
        matching = tuple(item for item in field_bindings if item == (
            "fee_rules." + rule_id, "OBJECT", "EVIDENCE_USE_FEE_RULE", original_ref,
            "/fee_rules/" + str(index), "EXACT_IDENTITY"))
        _native_require(len(matching) == 1, "fee rule lacks exact accepted source-field binding")
        for name in ("market_scope", "coefficients", "limitations"):
            _native_require(type(row[name]) in (list, tuple), "fee rule vector is not a closed array")
        _native_require(all(type(item) in (list, tuple) and len(item) == 2 for item in row["coefficients"]),
                        "fee coefficient is not a named exact scalar")
        native_type = row["native_fee_type_or_none"]
        if source_binding.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT:
            _native_ident(native_type)
        else:
            _native_require(native_type is None, "non-Kalshi rule cannot borrow a Kalshi native fee type")
        epoch = PublicFeeEpochV1(rule_id, source_binding.profile_id, row["product_class"], tuple(row["market_scope"]),
            row["account_scope_ref_or_none"], row["liquidity_role"], row["formula_family"],
            tuple(tuple(item) for item in row["coefficients"]), row["rounding_rule"],
            row["effective_from_ns"], row["effective_until_ns_or_none"], source_binding.known_at_ns,
            source_binding.expires_at_ns, (original_ref,), row["account_applicability_ref_or_none"],
            row["supersedes_rule_ref_or_none"], row["generation"], tuple(row["limitations"]))
        projected.append((native_type, epoch))
    return tuple(projected)


def compile_accepted_public_fee_rules_v1(*, source_binding, acceptance_results: tuple,
                                       originals: tuple, review_facts):
    """Retain the existing acceptance owner's exact knowledge/source linkage.

    Returned templates still need market, native observation and account joins;
    neither an accepted document nor this data-only projection issues packets.
    """
    from ..market_data_ingest.source_dependency import project_accepted_public_field_bindings_v1

    projection = project_accepted_public_field_bindings_v1(source_binding=source_binding,
        acceptance_results=acceptance_results, originals=originals, review_facts=review_facts)
    result = []
    for bundle in projection[2]:
        packet = bundle["accepted_packet"]
        facts = packet["extracted_fact_payload"].get("fee_rules")
        if facts is not None:
            result.extend(_project_public_fee_rule_facts_v1(source_binding=source_binding, facts=facts,
                field_bindings=source_binding.field_bindings,
                original_ref=packet["accepted_source_evidence_packet_id"]))
    if not result:
        raise SourcePolicyError(ReasonCode.OWNER_DATA_MISSING, "accepted fee family/product mapping unavailable")
    _native_require(len(result) <= 4096 and len({epoch.epoch_id for _, epoch in result}) == len(result),
                    "accepted fee rules conflict across source packets")
    return tuple(result)


def _resolve_public_publication_fee_epochs_v1(*, publication, instrument_id: str,
                                             known_as_of_ns: int, applicability, fills: tuple):
    """Join sealed source history to accepted fee templates for proposed fills."""
    from dataclasses import replace
    from ..orderbook_event_state_snapshot.handoff import (
        _require_public_publication_handle_v1, _public_reference_translations_v1,
        _public_committed_observation_plans_v1,
    )
    from ...pretrade.pr169_pretrade1_resolvers import PublicConditionalFillV1
    from .receipts import _public_identity_v1

    entry = _require_public_publication_handle_v1(publication=publication)
    _public_nanoseconds_v1(known_as_of_ns)
    use_expiry = _PUBLIC_RESPONSE_FENCES_V1[id(entry[14])][5]
    _native_require(entry[8] <= known_as_of_ns < use_expiry,
                    "fee decision predates issuance or exceeds source-use expiry")
    metadata_rows = tuple(row for row in entry[4] if row.instrument_id == instrument_id)
    _native_require(len(metadata_rows) == 1, "fee market metadata selection is ambiguous")
    metadata = metadata_rows[0]
    _native_require(metadata.known_at_ns <= known_as_of_ns < metadata.expires_at_ns,
                    "fee metadata is unavailable at the decision")
    _native_require(type(fills) is tuple and 0 < len(fills) <= 4096
        and all(type(fill) is PublicConditionalFillV1 for fill in fills), "proposed fee fills unavailable")
    _native_require(type(applicability) is SelectedAccountApplicabilityV1
        and entry[1]._inputs["account_applicability_or_none"] is applicability,
        "fee account dependency has no admitted original identity")
    applicability.__post_init__()
    _native_require(applicability.profile_id is metadata.profile_id
        and applicability.account_scope_ref == entry[1]._scope.account_scope_ref_or_none
        and applicability.qualification_ref == entry[1]._binding._capture.account_applicability_ref_or_none
        and applicability.available_at_ns <= known_as_of_ns < applicability.effective_until_ns,
        "fee account dependency is unavailable or outside the publication scope")
    account_sources, _, account_available_until, current_account_refs = _public_accepted_account_state_v1(inputs=entry[1]._inputs,
        applicability=applicability, native_only=entry[12], known_as_of_ns=known_as_of_ns)
    if entry[12]:
        if len(account_sources) != 1 or not any(account_sources[0] is row for row in entry[5]):
            raise SourcePolicyError(ReasonCode.OWNER_DATA_MISSING, "native account fee qualification custody unavailable")
    qualified = entry[1]._inputs.get("qualified_source_bindings", ())
    templates = []
    for projection in qualified:
        _native_require(type(projection) is tuple and len(projection) == 5,
                        "fee source has no admitted original qualification")
        source = projection[0]
        if not any(source is admitted for admitted in entry[5]) or source.profile_id is not metadata.profile_id:
            continue
        for bundle in projection[2]:
            packet = bundle["accepted_packet"]
            facts = packet["extracted_fact_payload"].get("fee_rules")
            if facts is not None:
                templates.extend(_project_public_fee_rule_facts_v1(source_binding=source, facts=facts,
                    field_bindings=source.field_bindings, original_ref=packet["accepted_source_evidence_packet_id"]))
    if not templates:
        raise SourcePolicyError(ReasonCode.OWNER_DATA_MISSING, "publication lacks accepted fee family/product mapping")
    _native_require(len(templates) <= 4096 and len({row.epoch_id for _, row in templates}) == len(templates),
                    "publication fee mappings conflict")
    histories = {"K_SERIES_FEES": [], "K_EVENT_FEES": []}
    history_refs = []
    if metadata.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT:
        _native_require(metadata.series_id_or_none is not None and metadata.event_id_or_none is not None,
                        "Kalshi fee parent identity unavailable")
        selected = {name: [] for name in histories}
        for translated in _public_reference_translations_v1(publication=publication):
            op = translated.stream_disposition.get("operation_id")
            if op in selected and instrument_id in translated.stream_disposition["instrument_ids"]:
                selected[op].append(translated)
        _native_require(selected["K_SERIES_FEES"] and selected["K_EVENT_FEES"],
                        "complete Series/Event fee history unavailable")
        for op, translations in selected.items():
            cursor, seen_cursors, identities, instants = None, set(), set(), set()
            for index, translated in enumerate(translations):
                plan = _public_committed_observation_plans_v1(publication=publication).get(translated.observation_ref)
                _native_require(plan is not None and plan[0].operation_id == op,
                                "fee history lost its original request plan")
                request = plan[0]
                values = translated.normalized_frame.parsed_source_scalar_tree_or_none
                if op == "K_SERIES_FEES":
                    _native_require(request.request_options["show_historical"] is True
                        and request.request_options["series_ticker"] == metadata.series_id_or_none,
                        "Series fee history omitted historical changes")
                    # Every Series response is a complete history snapshot.
                    # Repeated rows in a later fetch are not duplicate pages.
                    identities, instants = set(), set()
                    histories[op] = []
                else:
                    if request.pagination_cursor_or_none is None:
                        _native_require(index == 0 or cursor == "",
                                        "Event fee history pagination is incomplete or reordered")
                        cursor, seen_cursors, identities, instants = None, set(), set(), set()
                        histories[op] = []
                    _native_require(request.request_options["event_ticker"] == metadata.event_id_or_none
                        and request.pagination_cursor_or_none == cursor,
                        "Event fee history pagination is incomplete or reordered")
                    cursor = values["cursor"]
                    _native_require(not cursor or cursor not in seen_cursors, "Event fee history cursor repeats")
                    seen_cursors.add(cursor)
                history_refs.append(translated.observation_ref)
                for change in values["fee_changes"]:
                    instant = int(change["scheduled_at"]["utc_ns_text"])
                    _native_require(change["id"] not in identities and instant not in instants
                        and change["series_ticker"] == metadata.series_id_or_none
                        and (op != "K_EVENT_FEES" or change["event_ticker"] == metadata.event_id_or_none),
                        "duplicate/conflicting fee history or parent identity")
                    identities.add(change["id"])
                    instants.add(instant)
                    histories[op].append((instant, change))
            _native_require(op != "K_EVENT_FEES" or cursor == "", "Event fee history has an unread page")
            histories[op].sort(key=lambda row: row[0])
        _native_require(histories["K_SERIES_FEES"], "Series fee history lacks a baseline")
    all_epochs = {epoch.epoch_id: epoch for _, epoch in templates}
    native_types = {epoch.epoch_id: name for name, epoch in templates}
    emitted, previous_fill = {}, known_as_of_ns
    for fill in fills:
        fill.__post_init__()
        _native_require(fill.fill_at_ns >= previous_fill, "fee fills are reordered or precede the decision")
        _, account_start, account_end, account_refs = _public_accepted_account_state_v1(
            inputs=entry[1]._inputs, applicability=applicability,
            native_only=entry[12], known_as_of_ns=known_as_of_ns, effective_at_ns=fill.fill_at_ns)
        previous_fill = fill.fill_at_ns
        native_type, multiplier, start, end = None, None, 0, None
        if metadata.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT:
            series = [row for row in histories["K_SERIES_FEES"] if row[0] <= fill.fill_at_ns]
            event = [row for row in histories["K_EVENT_FEES"] if row[0] <= fill.fill_at_ns]
            _native_require(series, "Series fee baseline unavailable at the fill")
            chosen = event[-1] if event and not event[-1][1]["override_cleared"] else series[-1]
            native_type, multiplier = chosen[1]["fee_type"], chosen[1]["fee_multiplier"]
            start = max(series[-1][0], event[-1][0] if event else 0)
            future = [instant for history in histories.values() for instant, _ in history if instant > fill.fill_at_ns]
            end = min(future) if future else None
        eligible_by_id = {epoch.epoch_id: epoch for name, epoch in templates if name == native_type}
        # Preserve predecessor evidence across native-type transitions. The one
        # fee selector validates scope, generation and known/effective axes.
        for epoch in tuple(eligible_by_id.values()):
            visited = {epoch.epoch_id}
            while epoch.supersedes_epoch_ref_or_none is not None:
                predecessor = all_epochs.get(epoch.supersedes_epoch_ref_or_none)
                _native_require(predecessor is not None and predecessor.epoch_id not in visited,
                                "fee supersession lacks its original predecessor closure")
                visited.add(predecessor.epoch_id)
                eligible_by_id[predecessor.epoch_id] = predecessor
                epoch = predecessor
        eligible = tuple(eligible_by_id.values())
        selected = resolve_public_fee_epoch_v1(epochs=eligible, profile_id=metadata.profile_id,
            market_scope=(instrument_id,), applicability=applicability, known_as_of_ns=known_as_of_ns,
            effective_at_ns=fill.fill_at_ns, liquidity_role=fill.liquidity_role)
        _native_require(selected.product_class == metadata.product_class, "fee rule product differs from admitted metadata")
        _native_require(native_types[selected.epoch_id] == native_type,
                        "accepted fee family does not match the effective native fee type")
        coefficients = selected.coefficients
        if native_type is not None:
            _native_require(selected.formula_family in {"QUADRATIC", "EXPLICIT_ZERO"}, "unsupported native fee family")
            if selected.formula_family == "QUADRATIC":
                _native_require(multiplier is not None and Fraction(multiplier) > 0,
                                "zero/unknown multiplier is not an affirmative zero-fee rule")
                coefficients = tuple((name, multiplier if name == "multiplier" else value) for name, value in coefficients)
            start = max(start, selected.effective_from_ns)
        else:
            start = selected.effective_from_ns
        start = max(start, metadata.effective_from_ns, account_start)
        ends = [value for value in (end, selected.effective_until_ns_or_none, metadata.effective_until_ns_or_none,
                                   account_end, selected.expires_at_ns, metadata.expires_at_ns,
                                   use_expiry) if value is not None]
        for successor in all_epochs.values():
            if not (successor.known_at_ns <= known_as_of_ns < successor.expires_at_ns
                    and successor.effective_from_ns > fill.fill_at_ns
                    and (successor.profile_id, successor.product_class, successor.market_scope, successor.liquidity_role,
                         successor.account_scope_ref_or_none, successor.account_applicability_ref_or_none)
                    == (selected.profile_id, selected.product_class, selected.market_scope, selected.liquidity_role,
                        selected.account_scope_ref_or_none, selected.account_applicability_ref_or_none)):
                continue
            cursor, visited = successor, set()
            while cursor.supersedes_epoch_ref_or_none is not None:
                predecessor = all_epochs.get(cursor.supersedes_epoch_ref_or_none)
                _native_require(predecessor is not None and predecessor.epoch_id not in visited
                    and predecessor.generation < cursor.generation and predecessor.known_at_ns <= cursor.known_at_ns
                    and (predecessor.profile_id, predecessor.product_class, predecessor.market_scope, predecessor.liquidity_role,
                         predecessor.account_scope_ref_or_none, predecessor.account_applicability_ref_or_none)
                    == (cursor.profile_id, cursor.product_class, cursor.market_scope, cursor.liquidity_role,
                        cursor.account_scope_ref_or_none, cursor.account_applicability_ref_or_none),
                    "future fee supersession has an invalid predecessor")
                visited.add(predecessor.epoch_id)
                if predecessor.epoch_id == selected.epoch_id:
                    ends.append(successor.effective_from_ns)
                    break
                cursor = predecessor
        end = min(ends) if ends else None
        expiry = min(selected.expires_at_ns, metadata.expires_at_ns, account_available_until, use_expiry)
        action = entry[1]._binding._event.typed_payload
        identity = _public_identity_v1("PUBLIC_FEE_EPOCH_V1", selected.epoch_id, action.process_ref, action.sequence,
            entry[10], entry[11], entry[7].typed_payload.partition_ordinal, start,
            "OPEN" if end is None else end, known_as_of_ns, expiry, *sorted(row.instrument_id for row in entry[4]))
        result = replace(selected, epoch_id=identity, coefficients=coefficients, effective_from_ns=start,
            effective_until_ns_or_none=end, known_at_ns=max(selected.known_at_ns, metadata.known_at_ns, entry[8]),
            expires_at_ns=expiry,
            source_observation_refs=tuple(dict.fromkeys((*selected.source_observation_refs, *history_refs,
                *current_account_refs, *account_refs))),
            supersedes_epoch_ref_or_none=None)
        _native_require(result.effective_from_ns <= fill.fill_at_ns
            and (result.effective_until_ns_or_none is None or fill.fill_at_ns < result.effective_until_ns_or_none),
            "selected fee/metadata interval does not cover proposed fill")
        prior = emitted.setdefault(identity, result)
        _native_require(prior == result, "derived fee epoch identity conflicts")
    return tuple(emitted.values())


def resolve_public_contractual_settlement_v1(*, metadata, translations: tuple,
                                            known_as_of_ns: int, effective_at_ns: int,
                                            position_outcome: str):
    """Select a data-only contractual value; publication custody is separate.

    Neither accepted resolution nor this value establishes account cash posting.
    Scalar, void and resettlement formulas need their separately accepted mapping.
    """
    from ..market_data_ingest.binding import PublicMetadataSnapshotV1
    from ..market_data_ingest.adapter import PublicCanonicalTranslationV1
    from .context import _native_retail_finite_decimal_text_v1

    _native_require(type(metadata) is PublicMetadataSnapshotV1, "contractual settlement metadata unavailable")
    metadata.__post_init__()
    _public_nanoseconds_v1(known_as_of_ns)
    _public_nanoseconds_v1(effective_at_ns)
    _native_require(type(position_outcome) is str and position_outcome in {"YES", "NO"},
                    "contractual position outcome is not bound")
    _native_require(metadata.known_at_ns <= known_as_of_ns < metadata.expires_at_ns
        and metadata.effective_from_ns <= effective_at_ns
        and (metadata.effective_until_ns_or_none is None or effective_at_ns < metadata.effective_until_ns_or_none),
        "contractual settlement metadata unavailable at known/effective time")
    resolution = metadata.resolution
    required = {"state", "outcome", "final", "revision", "effective_at_ns", "known_at_ns", "observation_ref"}
    if (metadata.product_class != "BINARY" or metadata.payout_basis_or_none != "USD_PER_CONTRACT"
            or metadata.lifecycle["state"] not in {"RESOLVED", "SETTLED"}
            or metadata.payout_amount_or_none is None or not required <= set(resolution)
            or resolution["state"] not in {"RESOLVED", "SETTLED"} or resolution["final"] is not True
            or resolution["outcome"] not in {"YES", "NO"} or resolution.get("unavailable_reason") is not None):
        raise SourcePolicyError(ReasonCode.OWNER_DATA_MISSING,
            "accepted binary payout/outcome/finality unavailable; scalar or void mapping cannot be inferred")
    _native_ident(resolution["revision"])
    _native_ident(resolution["observation_ref"])
    _native_require(resolution["known_at_ns"] <= metadata.known_at_ns <= known_as_of_ns
        and resolution["effective_at_ns"] <= effective_at_ns, "later resolution cannot enter an earlier decision")
    lineage = {row[2]: row for row in metadata.field_lineage}
    source_fields = {"state", "outcome", "final", "revision", "effective_at_ns"}
    material = {"product_class", "payout_amount", "payout_basis", *("resolution." + key for key in source_fields)}
    _native_require(material <= set(lineage)
        and all(sum(row[2] == name for row in metadata.field_lineage) == 1 for name in material)
        and all(lineage["resolution." + key][0] == resolution["observation_ref"] for key in source_fields),
        "contractual settlement lacks exact accepted material-field lineage")
    _native_require(type(translations) is tuple and len(translations) <= 4096,
                    "invalid bounded settlement observation history")
    latest_book = None
    unresolved_preliminary = False
    observed_refs = []
    seen_observations, previous_order, clock_scope = set(), None, None
    for translation in translations:
        _native_require(type(translation) is PublicCanonicalTranslationV1, "untyped settlement observation")
        translation.__post_init__()
        disposition = translation.stream_disposition
        if disposition.get("instrument_id") != metadata.instrument_id:
            continue
        _native_require(translation.normalized_frame.profile_id is metadata.profile_id,
                        "cross-profile settlement observation")
        frame = translation.normalized_frame
        received = int(translation.exact_clock_companion["received"]["utc_ns_text"])
        _native_require(received <= known_as_of_ns, "later public observation cannot enter an earlier settlement")
        current_scope = (frame.capture_session_id, frame.process_epoch_id, frame.monotonic_clock_id)
        order = (received, frame.qtt_received_monotonic_ns)
        _native_require(translation.observation_ref not in seen_observations
            and (clock_scope is None or current_scope == clock_scope)
            and (previous_order is None or order[0] >= previous_order[0] and order[1] > previous_order[1]),
            "settlement history is reordered, duplicated or has ambiguous receive clocks")
        seen_observations.add(translation.observation_ref)
        previous_order, clock_scope = order, current_scope
        if disposition.get("event_kind") == "LIFECYCLE":
            _native_require(translation.observation_ref == resolution["observation_ref"]
                or received < resolution["known_at_ns"], "public lifecycle invalidates the accepted resolution")
            observed_refs.append(translation.observation_ref)
        if (metadata.profile_id is Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT
                and disposition.get("event_kind") == "BOOK_REPLACEMENT"):
            latest_book = translation
            flag = frame.parsed_source_scalar_tree_or_none.get("settlement_preliminary_or_none")
            unresolved_preliminary = unresolved_preliminary or (
                received >= resolution["known_at_ns"] and flag is not False)
    if latest_book is not None:
        # A later false cannot revive a resolution invalidated by a preliminary
        # observation. Only a strictly later accepted finality revision can.
        if unresolved_preliminary:
            raise SourcePolicyError(ReasonCode.OWNER_DATA_MISSING,
                "Retail settlement is preliminary or its preliminary status is unavailable")
        observed_refs.append(latest_book.observation_ref)
    payout = Fraction(metadata.payout_amount_or_none)
    yes_value = payout if resolution["outcome"] == "YES" else Fraction(0)
    if "value" in resolution:
        _native_require(Fraction(_native_retail_decimal_string_v1(resolution["value"])) == yes_value,
                        "accepted settlement value differs from the binary payout/outcome")
    value = yes_value if position_outcome == "YES" else payout - yes_value
    return MappingProxyType(dict(value_per_contract=_native_retail_finite_decimal_text_v1(value),
        position_outcome=position_outcome, resolved_outcome=resolution["outcome"],
        metadata_ref=metadata.metadata_id, resolution_ref=resolution["observation_ref"],
        resolution_revision=resolution["revision"], original_observation_refs=tuple(dict.fromkeys(observed_refs)),
        known_at_ns=metadata.known_at_ns, effective_at_ns=resolution["effective_at_ns"],
        accounting_class="PUBLIC_CONTRACTUAL_SETTLEMENT_NOT_ACCOUNT_CASH", no_order_authority=True))


def resolve_public_fee_epoch_v1(*, epochs: tuple[PublicFeeEpochV1, ...],
                              profile_id: Stage1VenueProfileIdV1, market_scope: tuple[str, ...],
                              applicability: SelectedAccountApplicabilityV1 | None,
                              known_as_of_ns: int, effective_at_ns: int, liquidity_role: str) -> PublicFeeEpochV1:
    """Select accepted source facts without retrieval-order or absent-as-zero inference."""
    from .receipts import _public_profile_v1

    _public_profile_v1(profile_id)
    _public_refs_v1(market_scope)
    _public_nanoseconds_v1(known_as_of_ns)
    _public_nanoseconds_v1(effective_at_ns)
    _native_require(type(epochs) is tuple and len(epochs) <= 4096
                    and type(liquidity_role) is str and liquidity_role in {"MAKER", "TAKER"},
                    "invalid fee selection inputs")
    if applicability is not None:
        _native_require(type(applicability) is SelectedAccountApplicabilityV1, "invalid account applicability")
        applicability.__post_init__()
        _native_require(applicability.profile_id is profile_id and applicability.available_at_ns <= known_as_of_ns
                        and applicability.effective_from_ns <= effective_at_ns < applicability.effective_until_ns
                        and known_as_of_ns < applicability.effective_until_ns, "account applicability unavailable")
    else:
        raise SourcePolicyError(ReasonCode.OWNER_DATA_MISSING, "exact fee selection requires account/product applicability")
    selected = []
    identities = set()
    for epoch in epochs:
        _native_require(type(epoch) is PublicFeeEpochV1, "invalid fee epoch type")
        epoch.__post_init__()
        _native_require(epoch.epoch_id not in identities, "duplicate fee epoch identity")
        identities.add(epoch.epoch_id)
        if not (epoch.profile_id is profile_id and epoch.market_scope == market_scope
                and epoch.product_class == applicability.product_scope_ref
                and epoch.account_scope_ref_or_none in (None, applicability.account_scope_ref)
                and epoch.account_applicability_ref_or_none in (None, applicability.qualification_ref)
                and epoch.liquidity_role == liquidity_role and epoch.known_at_ns <= known_as_of_ns < epoch.expires_at_ns
                and epoch.effective_from_ns <= effective_at_ns
                and (epoch.effective_until_ns_or_none is None or effective_at_ns < epoch.effective_until_ns_or_none)):
            continue
        if epoch.account_scope_ref_or_none is not None or epoch.account_applicability_ref_or_none is not None:
            _native_require(applicability is not None
                            and epoch.account_scope_ref_or_none == applicability.account_scope_ref
                            and epoch.account_applicability_ref_or_none == applicability.qualification_ref
                            and epoch.product_class == applicability.product_scope_ref,
                            "fee epoch has no matching account/product qualification")
        selected.append(epoch)
    by_id = {row.epoch_id: row for row in epochs}
    superseded = set()
    for selected_epoch in selected:
        epoch = selected_epoch
        while epoch.supersedes_epoch_ref_or_none is not None:
            predecessor = by_id.get(epoch.supersedes_epoch_ref_or_none)
            _native_require(predecessor is not None and predecessor.profile_id is epoch.profile_id
                and predecessor.market_scope == epoch.market_scope and predecessor.product_class == epoch.product_class
                and predecessor.liquidity_role == epoch.liquidity_role
                and predecessor.account_scope_ref_or_none == epoch.account_scope_ref_or_none
                and predecessor.account_applicability_ref_or_none == epoch.account_applicability_ref_or_none
                and predecessor.generation < epoch.generation and predecessor.known_at_ns <= epoch.known_at_ns,
                "fee supersession differs from the same scoped predecessor")
            superseded.add(predecessor.epoch_id)
            epoch = predecessor
    selected = [row for row in selected if row.epoch_id not in superseded]
    if len(selected) != 1:
        raise SourcePolicyError(ReasonCode.INVALID_CONTRACT, "fee epoch missing or conflicting at selected known/effective axes")
    _native_require(selected[0].rounding_rule != "UNAVAILABLE", "exact fee rounding unavailable")
    result = selected[0]
    if profile_id is Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT and liquidity_role == "MAKER":
        _native_require(applicability.maker_tier_or_none is not None, "independent maker tier unavailable")
        rate = ("0", "0.0035", "0.0070", "0.0104")[applicability.maker_tier_or_none - 1]
        _native_require((result.formula_family == "EXPLICIT_ZERO" and rate == "0") or (
            result.formula_family == "QUADRATIC" and {key: Fraction(value) for key,value in result.coefficients}
            == {"rate": Fraction(rate), "multiplier": Fraction(1)}),
            "Retail maker fee rule differs from the independently qualified tier")
    if profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT and liquidity_role == "MAKER" and result.formula_family == "EXPLICIT_ZERO":
        _native_require(applicability.promotion_eligibility_or_none is True,
                        "Gemini maker waiver eligibility unavailable")
    return result


# These closed rules describe evidence use. Their presence here establishes no
# source fact: the compiler requires the accepted extraction and its originals.
_PUBLIC_COMMON_SEMANTICS_V1 = MappingProxyType({
    "settlement_semantics.public_value": "CONTRACTUAL_VALUE_REQUIRES_ACCEPTED_PAYOUT_OUTCOME_AND_FINALITY",
    "settlement_semantics.account_cash": "PUBLIC_RESOLUTION_NEVER_RELEASES_ACCOUNT_CASH",
    "emergency_profile.unknown_custody_policy": "SAFE_HOLD_RETAIN_OBLIGATIONS_UNTIL_PRIVATE_RECONCILIATION",
    "emergency_profile.rearm_requirements": "CURRENT_SCOPE_AND_PRIVATE_ORDER_FILL_CASH_POSITION_RECONCILIATION",
})
_PUBLIC_VENUE_SEMANTICS_V1 = MappingProxyType({
    Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: MappingProxyType({
        "order_semantics.side_orientation": "YES_BOOK_BID_BUYS_YES_ASK_SELLS_YES",
        "order_semantics.time_in_force": "EXPLICIT_FOK_GTC_IOC_NO_GTT_WIRE_ENUM",
        "order_semantics.expiration": "IOC_NO_EXPIRY_GTC_EXPIRY_UNIX_SECONDS",
        "order_semantics.reduce_only": "REDUCE_ONLY_REQUIRES_IOC",
        "order_semantics.explicit_controls": "QTT_EXPLICIT_STP_BOOLEANS_CLIENT_SUBACCOUNT_AND_METADATA_SHARD",
        "quantity_price_semantics.count": "EXACT_DECIMAL_TEXT_ACCEPTED_QUANTITY_GRID",
        "quantity_price_semantics.price": "EXACT_ACCEPTED_BANDS_NO_SNAP_NO_OUTCOME_REINTERPRETATION",
        "quantity_price_semantics.amend_count": "FILLED_PLUS_DESIRED_REMAINING",
        "quantity_price_semantics.reduction": "EXCLUSIVE_POSITIVE_REDUCE_BY_OR_NONNEGATIVE_REDUCE_TO_BOUNDED_BY_REMAINING",
        "queue_semantics.decrease_or_expiry": "PRESERVES_PRIORITY",
        "queue_semantics.increase_or_price": "LOSES_PRIORITY",
        "maintenance_semantics.trading_pause": "NO_CREATE_OR_AMEND_CANCEL_ALLOWED",
        "maintenance_semantics.exchange_pause": "NO_CREATE_AMEND_OR_CANCEL",
        "maintenance_semantics.resting_orders": "PERSIST_UNLESS_ACCEPTED_CANCEL_ON_PAUSE",
        "emergency_profile.single_cancel": "EXACT_ORDER_SCOPE_REQUIRES_PRIVATE_TERMINAL_EVIDENCE",
        "emergency_profile.batch_cancel": "EXACT_ENUMERATED_ORDER_SCOPE_NO_ATOMICITY_INFERENCE",
        "emergency_profile.group_cancel": "EXACT_ORDER_GROUP_SCOPE_REQUIRES_PRIVATE_TERMINAL_EVIDENCE",
        "emergency_profile.pause_new_order_behavior": "TRADING_OR_EXCHANGE_PAUSE_BLOCKS_CREATE_AND_AMEND",
        "emergency_profile.pause_cancel_behavior": "TRADING_PAUSE_ALLOWS_CANCEL_EXCHANGE_PAUSE_BLOCKS_CANCEL",
        "emergency_profile.terminal_evidence_sources": "PRIVATE_ORDER_FILL_AND_OPEN_ORDER_RECONCILIATION",
        "emergency_profile.reduction_mechanism": "EXCLUSIVE_REDUCE_BY_OR_REDUCE_TO_WITH_KNOWN_REMAINING",
        "emergency_profile.scope_blast_radius": "ORDER_BATCH_AND_GROUP_SCOPES_ARE_DISTINCT",
    }),
    Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: MappingProxyType({
        "order_semantics.intent": "EXACTLY_ONE_INTENT_REPRESENTATION",
        "order_semantics.time_in_force": "DISTINCT_DAY_GTC_GTD_IOC_FOK_GTD_REQUIRES_EXPIRY",
        "order_semantics.explicit_controls": "QTT_EXPLICIT_AUTOMATIC_MANUAL_MAKER_ONLY_AND_SYNCHRONOUS_FLAGS",
        "order_semantics.maker_only": "PARTICIPATE_DONT_INITIATE_REFUSES_MARKETABLE_LIQUIDITY",
        "order_semantics.cancel_response": "ID_OR_EMPTY_CANCEL_RESPONSE_IS_NOT_TERMINAL_PROOF",
        "quantity_price_semantics.count": "EXACT_JSON_NUMBER_NO_SILENT_SNAPPING",
        "quantity_price_semantics.price": "YES_ORIENTED_EXACT_MONEY_NO_SILENT_SNAPPING",
        "queue_semantics.modification": "UNKNOWN_REQUIRES_ACCEPTED_BINDING",
        "maintenance_semantics.order_processing_stopgap": "FIVE_SECOND_ORDER_LATENCY_REJECTION_NOT_RATE_LIMIT_RESET",
        "emergency_profile.single_cancel": "EXACT_ORDER_SCOPE_REQUIRES_PRIVATE_TERMINAL_EVIDENCE",
        "emergency_profile.all_cancel": "EXPLICIT_ALL_SCOPE_REQUIRES_PRIVATE_RECONCILIATION",
        "emergency_profile.group_cancel": "EXACT_MARKET_SCOPE_REQUIRES_PRIVATE_TERMINAL_EVIDENCE",
        "emergency_profile.terminal_evidence_sources": "PRIVATE_ORDER_FILL_AND_OPEN_ORDER_RECONCILIATION",
        "emergency_profile.scope_blast_radius": "ORDER_MARKET_AND_ALL_SCOPES_ARE_DISTINCT",
    }),
    Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: MappingProxyType({
        "order_semantics.side_outcome_type": "WS_BUY_SELL_YES_NO_LIMIT_MARKET_DISTINCT_FROM_REST",
        "order_semantics.time_in_force": "DISTINCT_GTC_IOC_FOK_MOC",
        "order_semantics.stop_limit": "FRESH_LAST_TRADE_BUY_LAST_LE_STOP_LE_LIMIT_SELL_LIMIT_LE_STOP_LE_LAST",
        "order_semantics.stop_market": "PRIVATE_EVENT_ENUM_DOES_NOT_ESTABLISH_STOP_MARKET_SUBMISSION",
        "order_semantics.terminality": "NEW_MAY_LATER_CANCEL_FILLED_IOC_MAY_END_CANCELED_QUANTITIES_CONTROL_OBLIGATIONS",
        "quantity_price_semantics.price": "ACCEPTED_PRICE_MINIMUM_ORIGIN_AND_INCREMENT_NO_SNAP",
        "quantity_price_semantics.quantity": "DISTINCT_MINIMUM_INCREMENT_AND_UNAVAILABLE_UNPROVEN_ORIGIN",
        "quantity_price_semantics.executed": "PER_FILL_EXECUTED_DISTINCT_FROM_TERMINAL_CUMULATIVE_EXECUTED",
        "emergency_profile.single_cancel": "EXACT_ORDER_SCOPE_REQUIRES_PRIVATE_TERMINAL_EVIDENCE",
        "emergency_profile.all_cancel": "EXPLICIT_ACCOUNT_ALL_SCOPE_REQUIRES_PRIVATE_RECONCILIATION",
        "emergency_profile.session_cancel": "EXACT_SESSION_SCOPE_REQUIRES_PRIVATE_TERMINAL_EVIDENCE",
        "emergency_profile.terminal_evidence_sources": "PRIVATE_ORDER_FILL_AND_OPEN_ORDER_RECONCILIATION",
        "emergency_profile.scope_blast_radius": "ORDER_SESSION_AND_ACCOUNT_ALL_SCOPES_ARE_DISTINCT",
    }),
})
_PUBLIC_EMERGENCY_FIELDS_V1 = (
    "single_cancel", "batch_cancel", "all_cancel", "group_cancel", "session_cancel",
    "pause_new_order_behavior", "pause_cancel_behavior", "disconnect_order_behavior",
    "terminal_evidence_sources", "reduction_mechanism", "scope_blast_radius",
    "unknown_custody_policy", "rearm_requirements",
)
_PUBLIC_UNOBSERVED_SEMANTICS_V1 = (
    "queue_semantics.native_queue_position", "queue_semantics.batch_atomicity",
    "queue_semantics.taker_delay", "maintenance_semantics.account_capacity",
    "settlement_semantics.cash_posting",
)


def _public_semantic_rules_v1(profile_id):
    from .receipts import _public_profile_v1

    _public_profile_v1(profile_id)
    return dict(_PUBLIC_COMMON_SEMANTICS_V1, **_PUBLIC_VENUE_SEMANTICS_V1[profile_id])


def _validate_public_semantic_facts_v1(*, profile_id, facts, field_bindings, original_ref):
    """Validate a closed accepted extraction; no source acceptance is issued."""
    rules = _public_semantic_rules_v1(profile_id)
    _native_require(type(facts) in (dict, MappingProxyType) and len(facts) <= len(rules),
                    "invalid accepted venue semantics")
    for name, value in facts.items():
        _native_require(type(name) is str and name in rules and type(value) in (dict, MappingProxyType)
            and set(value) == {"disposition", "rule_id"}, "unselected venue semantic field")
        _native_require(value["disposition"] in {"SOURCE_BOUND_SUPPORTED", "SOURCE_BOUND_UNSUPPORTED", "NOT_APPLICABLE_WITH_PROOF"}
            and type(value["disposition"]) is str and type(value["rule_id"]) is str and value["rule_id"] == rules[name],
            "unsupported native semantic rule")
        matches = tuple(row for row in field_bindings if row[0] == "venue_semantics." + name and row[3] == original_ref)
        _native_require(len(matches) == 1 and matches[0][1] == "OBJECT" and matches[0][2] == "EVIDENCE_USE_SEMANTICS"
            and matches[0][5] == "EXACT_IDENTITY", "venue semantic fact lacks exact accepted field lineage")


@dataclass(frozen=True, slots=True)
class PublicVenueSemanticFactV1:
    disposition: str
    rule_id_or_none: str | None
    field_lineage: tuple[tuple[str, str, str, str], ...]
    unavailable_reason_or_none: str | None

    def __post_init__(self):
        from ..market_data_ingest.binding import _public_field_lineage_v1

        _native_require(type(self.disposition) is str and self.disposition in {
            "SOURCE_BOUND_SUPPORTED", "SOURCE_BOUND_UNSUPPORTED", "UNAVAILABLE_MISSING_BINDING", "NOT_APPLICABLE_WITH_PROOF"},
            "invalid semantic capability disposition")
        if self.disposition == "UNAVAILABLE_MISSING_BINDING":
            _native_require(self.rule_id_or_none is None and self.field_lineage == (),
                            "unavailable semantic capability cannot claim a rule")
            _native_ident(self.unavailable_reason_or_none)
        else:
            _native_ident(self.rule_id_or_none)
            _public_field_lineage_v1(self.field_lineage)
            _native_require(self.unavailable_reason_or_none is None, "bound semantic capability has an unavailable reason")


@dataclass(frozen=True, slots=True)
class PublicVenueSemanticSectionV1:
    section: str
    fields: tuple[tuple[str, PublicVenueSemanticFactV1], ...]

    def __post_init__(self):
        _native_require(type(self.section) is str and self.section in {
            "order_semantics", "quantity_price_semantics", "queue_semantics", "maintenance_semantics", "settlement_semantics"},
            "unselected semantic section")
        _native_require(type(self.fields) is tuple and 0 < len(self.fields) <= 64, "invalid semantic section fields")
        names = set()
        for row in self.fields:
            _native_require(type(row) is tuple and len(row) == 2 and type(row[1]) is PublicVenueSemanticFactV1,
                            "invalid typed semantic fact")
            _native_ident(row[0])
            _native_require(row[0] not in names, "duplicate semantic field")
            names.add(row[0])
            row[1].__post_init__()


@dataclass(frozen=True, slots=True)
class PublicEmergencySemanticProfileV1:
    single_cancel: PublicVenueSemanticFactV1
    batch_cancel: PublicVenueSemanticFactV1
    all_cancel: PublicVenueSemanticFactV1
    group_cancel: PublicVenueSemanticFactV1
    session_cancel: PublicVenueSemanticFactV1
    pause_new_order_behavior: PublicVenueSemanticFactV1
    pause_cancel_behavior: PublicVenueSemanticFactV1
    disconnect_order_behavior: PublicVenueSemanticFactV1
    terminal_evidence_sources: PublicVenueSemanticFactV1
    reduction_mechanism: PublicVenueSemanticFactV1
    scope_blast_radius: PublicVenueSemanticFactV1
    unknown_custody_policy: PublicVenueSemanticFactV1
    rearm_requirements: PublicVenueSemanticFactV1
    source_refs: tuple[str, ...]
    native_version: str
    known_at_ns: int
    effective_from_ns: int
    expires_at_ns: int
    generation: int

    def __post_init__(self):
        _public_refs_v1(self.source_refs)
        _native_ident(self.native_version)
        for name in _PUBLIC_EMERGENCY_FIELDS_V1:
            fact = getattr(self, name)
            _native_require(type(fact) is PublicVenueSemanticFactV1, "emergency capability must have a typed disposition")
            fact.__post_init__()
        for name in ("known_at_ns", "effective_from_ns", "expires_at_ns"):
            _public_nanoseconds_v1(getattr(self, name))
        _native_require(max(self.known_at_ns, self.effective_from_ns) < self.expires_at_ns, "expired emergency semantics")
        _public_counter_v1(self.generation, allow_zero=True)


@dataclass(frozen=True, slots=True)
class SelectedVenueRealityBindingV1:
    binding_id: str
    profile_id: Stage1VenueProfileIdV1
    source_epoch_id: str
    native_version: str
    instrument_scope: tuple[str, ...]
    account_scope_ref_or_none: str | None
    source_refs: tuple[str, ...]
    known_at_ns: int
    effective_from_ns: int
    expires_at_ns: int
    generation: int
    order_semantics: PublicVenueSemanticSectionV1
    quantity_price_semantics: PublicVenueSemanticSectionV1
    fee_binding_refs: tuple[str, ...]
    rate_binding_ref_or_none: str | None
    queue_semantics: PublicVenueSemanticSectionV1
    maintenance_semantics: PublicVenueSemanticSectionV1
    settlement_semantics: PublicVenueSemanticSectionV1
    emergency_profile: PublicEmergencySemanticProfileV1
    unavailable_capabilities: tuple[str, ...]
    no_order_authority: bool

    def __post_init__(self):
        rules = _public_semantic_rules_v1(self.profile_id)
        for name in ("binding_id", "source_epoch_id", "native_version"):
            _native_ident(getattr(self, name))
        for name in ("account_scope_ref_or_none", "rate_binding_ref_or_none"):
            if getattr(self, name) is not None:
                _native_ident(getattr(self, name))
        for name in ("instrument_scope", "source_refs", "fee_binding_refs", "unavailable_capabilities"):
            _public_refs_v1(getattr(self, name), allow_empty=name in {"fee_binding_refs", "unavailable_capabilities"})
        for name in ("known_at_ns", "effective_from_ns", "expires_at_ns"):
            _public_nanoseconds_v1(getattr(self, name))
        _native_require(max(self.known_at_ns, self.effective_from_ns) < self.expires_at_ns
            and self.no_order_authority is True, "reality binding expired or claims order authority")
        _public_counter_v1(self.generation, allow_zero=True)
        expected = set(rules) | set(_PUBLIC_UNOBSERVED_SEMANTICS_V1) | {
            "emergency_profile." + name for name in _PUBLIC_EMERGENCY_FIELDS_V1}
        actual = {}
        for name in ("order_semantics", "quantity_price_semantics", "queue_semantics", "maintenance_semantics", "settlement_semantics"):
            section = getattr(self, name)
            _native_require(type(section) is PublicVenueSemanticSectionV1 and section.section == name,
                            "wrong typed venue semantic section")
            section.__post_init__()
            actual.update((name + "." + key, value) for key, value in section.fields)
        emergency = self.emergency_profile
        _native_require(type(emergency) is PublicEmergencySemanticProfileV1, "untyped emergency semantics")
        emergency.__post_init__()
        _native_require(all(getattr(emergency, name) == getattr(self, name) for name in (
            "source_refs", "native_version", "known_at_ns", "effective_from_ns", "expires_at_ns", "generation")),
            "emergency source/version/time/generation mismatch")
        actual.update(("emergency_profile." + name, getattr(emergency, name)) for name in _PUBLIC_EMERGENCY_FIELDS_V1)
        _native_require(set(actual) == expected, "venue reality field set is not closed")
        unavailable = set()
        for name, fact in actual.items():
            if fact.disposition == "UNAVAILABLE_MISSING_BINDING":
                unavailable.add(name)
            else:
                _native_require(name in rules and fact.rule_id_or_none == rules[name]
                    and all(row[0] in self.source_refs and row[2] == "venue_semantics." + name for row in fact.field_lineage),
                    "venue semantic rule or lineage differs from the selected profile")
                if fact.rule_id_or_none == "UNKNOWN_REQUIRES_ACCEPTED_BINDING":
                    unavailable.add(name)
        if not self.fee_binding_refs:
            unavailable.add("fee_binding_refs")
        if self.rate_binding_ref_or_none is None:
            unavailable.add("rate_binding_ref_or_none")
        _native_require(set(self.unavailable_capabilities) == unavailable, "venue unavailable capabilities differ from facts")


def compile_selected_venue_reality_binding_v1(*, source_binding, acceptance_results, originals, review_facts,
                                            source_epoch_id, metadata, applicability, fee_epochs, rate_binding,
                                            known_as_of_ns):
    """Compile evidence-use semantics through the existing accepted source owner.

    Synthetic acceptance remains synthetic. Native use additionally requires the
    current source-use/publication custody and never follows from this record.
    """
    from ..market_data_ingest.binding import PublicMetadataSnapshotV1
    from ..market_data_ingest.source_dependency import project_accepted_public_field_bindings_v1
    from .receipts import _public_identity_v1

    projection = project_accepted_public_field_bindings_v1(source_binding=source_binding,
        acceptance_results=acceptance_results, originals=originals, review_facts=review_facts)
    _native_ident(source_epoch_id)
    _public_nanoseconds_v1(known_as_of_ns)
    _native_require(source_binding.known_at_ns <= known_as_of_ns < source_binding.expires_at_ns
        and source_binding.effective_from_ns <= known_as_of_ns
        and (source_binding.effective_until_ns_or_none is None or known_as_of_ns < source_binding.effective_until_ns_or_none),
        "venue semantics source is not current")
    _native_require(type(metadata) is tuple and 0 < len(metadata) <= 4096
        and all(type(row) is PublicMetadataSnapshotV1 for row in metadata), "venue semantics metadata unavailable")
    for row in metadata:
        row.__post_init__()
        _native_require(row.profile_id is source_binding.profile_id and row.known_at_ns <= known_as_of_ns < row.expires_at_ns
            and row.effective_from_ns <= known_as_of_ns
            and (row.effective_until_ns_or_none is None or known_as_of_ns < row.effective_until_ns_or_none),
            "venue semantics metadata scope/interval differs")
    instruments = tuple(sorted(row.instrument_id for row in metadata))
    _public_refs_v1(instruments)
    ends = [source_binding.expires_at_ns, *(row.expires_at_ns for row in metadata)]
    ends.extend(row.effective_until_ns_or_none for row in (source_binding, *metadata) if row.effective_until_ns_or_none is not None)
    known = max(source_binding.known_at_ns, *(row.known_at_ns for row in metadata))
    effective = max(source_binding.effective_from_ns, *(row.effective_from_ns for row in metadata))
    if applicability is not None:
        _native_require(type(applicability) is SelectedAccountApplicabilityV1, "untyped venue account applicability")
        applicability.__post_init__()
        _native_require(applicability.profile_id is source_binding.profile_id
            and applicability.available_at_ns <= known_as_of_ns
            and applicability.effective_from_ns <= known_as_of_ns < applicability.effective_until_ns,
            "venue account applicability is not current")
        known, effective = max(known, applicability.available_at_ns), max(effective, applicability.effective_from_ns)
        ends.append(applicability.effective_until_ns)
    _native_require(type(fee_epochs) is tuple and len(fee_epochs) <= 4096, "invalid venue fee bindings")
    for epoch in fee_epochs:
        _native_require(type(epoch) is PublicFeeEpochV1, "untyped venue fee binding")
        epoch.__post_init__()
        _native_require(epoch.profile_id is source_binding.profile_id and set(epoch.market_scope) <= set(instruments)
            and epoch.known_at_ns <= known_as_of_ns < epoch.expires_at_ns, "venue fee scope/knowledge differs")
        ends.append(epoch.expires_at_ns)
        known = max(known, epoch.known_at_ns)
    if rate_binding is not None:
        _native_require(type(rate_binding) is PublicRequestRateBindingV1, "untyped venue rate binding")
        rate_binding.__post_init__()
        _native_require(rate_binding.profile_id is source_binding.profile_id
            and rate_binding.effective_from_ns <= known_as_of_ns < rate_binding.expires_at_ns
            and set(rate_binding.source_refs) <= set(source_binding.original_evidence_refs), "venue rate scope/source differs")
        effective = max(effective, rate_binding.effective_from_ns)
        ends.append(rate_binding.expires_at_ns)
    rules = _public_semantic_rules_v1(source_binding.profile_id)
    selected = {}
    for bundle in projection[2]:
        packet = bundle["accepted_packet"]
        original_ref = packet["accepted_source_evidence_packet_id"]
        facts = packet["extracted_fact_payload"].get("venue_semantics", {})
        _validate_public_semantic_facts_v1(profile_id=source_binding.profile_id, facts=facts,
            field_bindings=source_binding.field_bindings, original_ref=original_ref)
        for name, fact in facts.items():
            _native_require(name not in selected, "conflicting accepted venue semantic facts")
            lineage = tuple((original, pointer, field_name, transform) for field_name, wire, unit, original, pointer, transform
                in source_binding.field_bindings if field_name == "venue_semantics." + name and original == original_ref)
            selected[name] = PublicVenueSemanticFactV1(fact["disposition"], fact["rule_id"], lineage, None)
    expected = set(rules) | set(_PUBLIC_UNOBSERVED_SEMANTICS_V1) | {
        "emergency_profile." + name for name in _PUBLIC_EMERGENCY_FIELDS_V1}
    for name in sorted(expected - set(selected)):
        selected[name] = PublicVenueSemanticFactV1("UNAVAILABLE_MISSING_BINDING", None, (), "OWNER_DATA_MISSING::" + name)
    unavailable = {name for name, fact in selected.items() if fact.disposition == "UNAVAILABLE_MISSING_BINDING"
        or fact.rule_id_or_none == "UNKNOWN_REQUIRES_ACCEPTED_BINDING"}
    if not fee_epochs:
        unavailable.add("fee_binding_refs")
    if rate_binding is None:
        unavailable.add("rate_binding_ref_or_none")
    version = _public_identity_v1("PUBLIC_NATIVE_SOURCE_VERSIONS_V1", *source_binding.source_contract_versions)
    generation = max(source_binding.generation, *(row.generation for row in metadata),
        *(row.generation for row in fee_epochs), *(() if applicability is None else (applicability.generation,)),
        *(() if rate_binding is None else (rate_binding.generation,)))
    common = dict(source_refs=source_binding.original_evidence_refs, native_version=version,
        known_at_ns=known, effective_from_ns=effective, expires_at_ns=min(ends), generation=generation)
    sections = {section: PublicVenueSemanticSectionV1(section, tuple(sorted(
        (name.split(".", 1)[1], fact) for name, fact in selected.items() if name.startswith(section + "."))))
        for section in ("order_semantics", "quantity_price_semantics", "queue_semantics", "maintenance_semantics", "settlement_semantics")}
    identity = _public_identity_v1("SELECTED_VENUE_REALITY_V1", source_binding.profile_id.value, source_epoch_id,
        source_binding.binding_id, version, generation, known, effective, min(ends), *instruments)
    return SelectedVenueRealityBindingV1(binding_id=identity, profile_id=source_binding.profile_id,
        source_epoch_id=source_epoch_id, instrument_scope=instruments,
        account_scope_ref_or_none=None if applicability is None else applicability.account_scope_ref,
        fee_binding_refs=tuple(epoch.epoch_id for epoch in fee_epochs),
        rate_binding_ref_or_none=None if rate_binding is None else rate_binding.binding_id,
        emergency_profile=PublicEmergencySemanticProfileV1(**{name: selected["emergency_profile." + name]
            for name in _PUBLIC_EMERGENCY_FIELDS_V1}, **common),
        unavailable_capabilities=tuple(sorted(unavailable)), no_order_authority=True, **sections, **common)


@dataclass(frozen=True, slots=True)
class RecordedSourceUseStatusV1:
    """Current recorded assertions only; neither authenticated nor admitted."""

    stream_id: str
    current_head_record_ref: str | None
    current_sequence: int | None
    subject_kind: str | None
    recorded_at_utc: datetime | None
    evaluated_at_utc: datetime
    state: str
    admission_eligible: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        from .receipts import (
            _source_use_stream_id_v1, _source_use_record_ref_v1, _source_use_require_v1, _source_use_utc_v1,
        )

        _source_use_stream_id_v1(self.stream_id)
        _source_use_utc_v1(self.evaluated_at_utc)
        _source_use_require_v1(type(self.state) is str and self.state in {
            "MISSING", "RECORDED_UNVERIFIED", "WITHDRAWAL_RECORDED_UNVERIFIED",
            "CLAIMED_NOT_YET_EFFECTIVE_UNVERIFIED", "CLAIMED_EXPIRED_UNVERIFIED",
        })
        if self.state == "MISSING":
            _source_use_require_v1(all(value is None for value in (
                self.current_head_record_ref, self.current_sequence, self.subject_kind, self.recorded_at_utc,
            )))
        else:
            _source_use_record_ref_v1(self.current_head_record_ref)
            _source_use_require_v1(type(self.current_sequence) is int and 1 <= self.current_sequence <= 2**63 - 1
                                   and self.current_head_record_ref == f"SOURCE_USE::{self.stream_id}::{self.current_sequence:020d}"
                                   and type(self.subject_kind) is str and self.subject_kind in {"OWNER_DECLARATION", "SOURCE_REVIEW"})
            _source_use_require_v1(_source_use_utc_v1(self.recorded_at_utc) <= self.evaluated_at_utc)


def read_recorded_source_use_status_v1(
    *, adapter: PersistenceAdapterV1, stream_id: str, evaluated_at_utc: datetime,
) -> RecordedSourceUseStatusV1:
    from .errors import PersistenceContractError, PointInTimeError
    from .persistence import PersistenceAdapterV1
    from .receipts import _source_use_from_storage_v1, _source_use_stream_id_v1, _source_use_utc_v1, _source_use_require_v1

    _source_use_stream_id_v1(stream_id)
    evaluated_at_utc = _source_use_utc_v1(evaluated_at_utc)
    _source_use_require_v1(isinstance(adapter, PersistenceAdapterV1))
    head = adapter.load_committed_source_use_head_v1(stream_id)
    if head is None:
        return RecordedSourceUseStatusV1(stream_id, None, None, None, None, evaluated_at_utc, "MISSING")
    head = _source_use_from_storage_v1(head, record_id=getattr(head, "record_id", None))
    payload = head.typed_payload
    if payload.stream_id != stream_id:
        raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "source-use stored head mismatch")
    if head.recorded_at > evaluated_at_utc:
        raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, "source-use head is recorded after evaluation")
    if payload.action == "WITHDRAW":
        state = "WITHDRAWAL_RECORDED_UNVERIFIED"
    elif payload.content.claimed_effective_at_utc is not None and evaluated_at_utc < payload.content.claimed_effective_at_utc:
        state = "CLAIMED_NOT_YET_EFFECTIVE_UNVERIFIED"
    elif payload.content.claimed_expires_at_utc is not None and evaluated_at_utc >= payload.content.claimed_expires_at_utc:
        state = "CLAIMED_EXPIRED_UNVERIFIED"
    else:
        state = "RECORDED_UNVERIFIED"
    return RecordedSourceUseStatusV1(stream_id, head.record_id, head.sequence, payload.subject_kind,
                                    head.recorded_at, evaluated_at_utc, state)


_PUBLIC_BINDINGS_V1 = {}
_PUBLIC_CREDENTIALS_V1 = {}


class PublicCredentialBindingV1:
    """Opaque parsed-key custody, issued only inside an admitted capture effect."""

    __slots__ = ("_binding", "_row", "_key", "_expiry", "_generation", "_resources", "_process_id", "_native_qualified")

    def __init__(self):
        raise TypeError("public credential requires the protected capture effect")

    def __repr__(self):
        return "<PublicCredentialBindingV1 opaque>"

    def __reduce__(self):
        raise TypeError("public credentials cannot be serialized")

    def __copy__(self):
        raise TypeError("public credentials cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("public credentials cannot be copied")


class PublicSourceUseBindingV1:
    """Private process-bound issuance, separate from data-only scope records."""

    __slots__ = ("_authority", "_root", "_generation", "_event", "_capture", "_control_records",
                 "_native_qualified", "_process_id", "_thread_id", "_deadline", "_failed", "_owner",
                 "_source_inputs", "_publication_lock", "_resources", "_started", "_input_view")

    def __init__(self):
        raise TypeError("public source-use binding requires authenticated owner issuance")

    def __reduce__(self):
        raise TypeError("public permission cannot be serialized")

    def __copy__(self):
        raise TypeError("public permission cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("public permission cannot be copied")


def _public_binding_facts_v1(binding):
    import os
    import threading
    import time
    from .receipts import _public_identity_v1

    _native_require(type(binding) is PublicSourceUseBindingV1 and _PUBLIC_BINDINGS_V1.get(id(binding)) is binding
                    and binding._process_id == os.getpid() and binding._thread_id == threading.get_ident()
                    and not binding._failed and time.monotonic_ns() < binding._deadline,
                    "public permission has no current process/thread custody")
    if binding._authority is not None:
        with binding._authority._lock:
            binding._authority._check_public_binding_v1(binding)
    request = binding._capture
    _native_require(time.time_ns() < request.operating_expires_at_ns
                    and time.time_ns() < request.scope.retention_expires_at_ns,
                    "public operating/retention permission expired")
    return MappingProxyType(dict(scope=request.scope,
        scope_ref=_public_identity_v1("PUBLIC_SCOPE_V1", request.request_id, binding._generation),
        scope_generation=binding._generation, storage_root_ref=request.scope.storage_root_ref,
        retention_expires_at_ns=request.scope.retention_expires_at_ns, budget=request.scope.budget,
        native_qualified=binding._native_qualified, capture_session_id=request.capture_session_id,
        action_ref=binding._event.record_id, control_records=binding._control_records,
        source_inputs=binding._source_inputs))


def _create_synthetic_public_binding_v1(*, capture, control_records: tuple, source_inputs: Mapping):
    """Explicit synthetic fixture issuer; its binding cannot open a native store or registry."""
    import os
    import threading
    from .receipts import PublicCaptureRequestV1, PublicDataSourceUseActionV1, _public_validate_spine_v1

    _native_require(type(capture) is PublicCaptureRequestV1 and type(control_records) is tuple and control_records,
                    "synthetic public binding requires exact fixture records")
    capture.__post_init__()
    for row in control_records:
        _public_validate_spine_v1(row)
    event = control_records[-1]
    _native_require(type(event.typed_payload) is PublicDataSourceUseActionV1
                    and event.typed_payload.action == "OBSERVE_ONCE" and event.typed_payload.capture == capture,
                    "synthetic capture fixture has no matching final action")
    _native_require(type(source_inputs) in (dict, MappingProxyType), "invalid synthetic source inputs")
    result = object.__new__(PublicSourceUseBindingV1)
    result._authority = result._root = None
    result._generation, result._event, result._capture = event.typed_payload.generation_after, event, capture
    result._control_records, result._native_qualified = control_records, False
    result._process_id, result._thread_id = os.getpid(), threading.get_ident()
    result._deadline, result._failed, result._owner = capture.scope.budget.deadline_monotonic_ns, False, None
    result._source_inputs, result._publication_lock = MappingProxyType(dict(source_inputs)), threading.RLock()
    result._resources, result._started = None, False
    result._input_view = None
    _PUBLIC_BINDINGS_V1[id(result)] = result
    _public_binding_facts_v1(result)
    return result


_PUBLIC_RESPONSE_FENCES_V1 = {}


class _PublicResponseFenceV1:
    def __init__(self):
        raise TypeError("public response fence requires original source custody")

    def __reduce__(self):
        raise TypeError("public response fence is process-local")


def _prepare_public_response_fence_v1(*, binding, sources, metadata, applicability=None, not_after_ns=None):
    """Perform source/root checks before entering the short resident fence."""
    from ..market_data_ingest.binding import PublicMetadataSnapshotV1
    from .sqlite_reference import _public_root_facts_v1, _SYNTHETIC_PUBLIC_ROOTS_V1
    from ...service.owner_source_use_windows import _ROOTS, _PUBLIC_STORAGE_ROOTS_V1
    from .persistence import PersistenceAvailabilityV1

    facts = _public_binding_facts_v1(binding)
    inputs, owner = binding._source_inputs, binding._owner
    _native_require(owner is not None and owner._inputs is inputs
                    and type(sources) is tuple and sources and type(metadata) is tuple and metadata,
                    "response fence requires its selected source and metadata closure")
    before, wall, after = time.monotonic_ns(), time.time_ns(), time.monotonic_ns()
    _native_require(0 <= before <= after <= 2**63-1 and type(wall) is int
                    and after-before <= facts["budget"].maximum_wall_uncertainty_ns, "response fence clock quality unavailable")
    root = inputs["storage_root"]
    root_facts = _public_root_facts_v1(root)
    expiries = [binding._capture.operating_expires_at_ns, facts["retention_expires_at_ns"], root_facts["expires_at_ns"]]
    if not_after_ns is not None:
        _public_nanoseconds_v1(not_after_ns)
        expiries.append(not_after_ns)
    selected = []
    for rows, key, cls in ((sources, "source_bindings", PublicDataSourceBindingV1),
                           (metadata, "metadata", PublicMetadataSnapshotV1)):
        for row in rows:
            admitted = owner._active_metadata if key == "metadata" else inputs[key]
            _native_require(type(row) is cls and any(item is row for item in admitted),
                            "response dependency has no admitted source-owner identity")
            row.__post_init__()
            _native_require(row.known_at_ns <= wall < row.expires_at_ns and row.effective_from_ns <= wall
                            and (row.effective_until_ns_or_none is None or wall < row.effective_until_ns_or_none),
                            "selected response dependency is expired or ineffective")
            expiries.append(row.expires_at_ns)
            if row.effective_until_ns_or_none is not None:
                expiries.append(row.effective_until_ns_or_none)
            selected.append((row, row.generation))
    if applicability is not None:
        _native_require(type(applicability) is SelectedAccountApplicabilityV1
                        and inputs["account_applicability_or_none"] is applicability,
                        "response account dependency has no admitted identity")
        applicability.__post_init__()
        _native_require(applicability.available_at_ns <= wall
                        and applicability.effective_from_ns <= wall < applicability.effective_until_ns,
                        "response account dependency is unavailable")
        expiries.append(applicability.effective_until_ns)
        selected.append((applicability, applicability.generation))
    authority = binding._authority
    native = None
    if authority is not None:
        resources = binding._resources
        expiries.extend((resources["expires_at_ns"], _native_utc_nanoseconds(authority._expires.isoformat()),
            _native_utc_nanoseconds(authority._review.typed_payload.expires_at_utc.isoformat()),
            _native_utc_nanoseconds(authority._use.typed_payload.expires_at_utc.isoformat())))
        native = (authority._head, authority._review, authority._use, authority._selected_scope,
                  authority._adapter._original_control_scope, resources, resources["configuration"],
                  resources["configuration_generation"], _ROOTS, _PUBLIC_STORAGE_ROOTS_V1,
                  PersistenceAvailabilityV1.AVAILABLE_OWNER_CONTROL_EPHEMERAL)
    _native_require(wall < min(expiries) and after < binding._deadline, "response permission expired")
    fence = object.__new__(_PublicResponseFenceV1)
    _PUBLIC_RESPONSE_FENCES_V1[id(fence)] = (fence, binding, owner, inputs, binding._generation, min(expiries),
        binding._deadline, (tuple(selected), owner._active_metadata), native, wall, after, _SYNTHETIC_PUBLIC_ROOTS_V1, root,
        facts["budget"].maximum_wall_uncertainty_ns)
    return fence


def _check_public_response_fence_v1(fence):
    """Resident identities and exact clocks only; no imports, I/O or refresh."""
    row = _PUBLIC_RESPONSE_FENCES_V1.get(id(fence))
    _native_require(type(fence) is _PublicResponseFenceV1 and row is not None and row[0] is fence,
                    "response fence has no original issuance")
    _, binding, owner, inputs, generation, expiry, deadline, selected, native, last_wall, last_mono, roots, root, uncertainty = row
    before, wall, after = time.monotonic_ns(), time.time_ns(), time.monotonic_ns()
    _native_require(type(before) is type(wall) is type(after) is int
                    and 0 <= last_mono <= before <= after < deadline and last_wall <= wall < expiry
                    and owner._last_wall <= wall and owner._last_mono <= before
                    and after-before <= uncertainty and _PUBLIC_BINDINGS_V1.get(id(binding)) is binding
                    and binding._owner is owner and binding._source_inputs is inputs and owner._inputs is inputs
                    and binding._generation == generation
                    and not binding._failed and binding._process_id == os.getpid()
                    and binding._thread_id == threading.get_ident(),
                    "response dependency generation, custody or exclusive deadline changed")
    _native_require(owner._active_metadata is selected[1], "response metadata version changed")
    for item, expected in selected[0]:
        _native_require(item.generation == expected, "response dependency generation changed")
    authority = binding._authority
    if native is None:
        _native_require(authority is None and not binding._native_qualified and roots.get(id(root)) is root,
                        "synthetic response origin changed")
    else:
        head, review, use, scope, control_scope, resources, configuration, configuration_generation, native_roots, storage_roots, available = native
        _native_require(authority is not None and not authority._stopped
                        and authority._bindings.get(id(binding)) is binding and authority._active_permit is binding
                        and authority._head is head is binding._event and authority._review is review and authority._use is use
                        and authority._selected_scope is scope and head.typed_payload.capture is binding._capture
                        and binding._native_qualified is True
                        and authority._public_input_view is binding._input_view and binding._input_view is not None
                        and binding._source_inputs["qualified_source_bindings"] is binding._input_view[5]
                        and all(binding._source_inputs[name] is value for name,value in binding._input_view[4].items())
                        and authority._adapter._control_scope is control_scope is authority._adapter._original_control_scope
                        and authority._adapter.availability is available and binding._resources is resources
                        and binding._root is authority._root and native_roots.get(id(binding._root)) is binding._root
                        and not binding._root.closed and binding._root.public_configuration is configuration
                        and configuration[0] == configuration_generation and storage_roots.get(id(root)) is root
                        and resources["storage_root"] is root and root.owner is binding._root,
                        "native response authority/root changed")
    owner._last_wall, owner._last_mono = wall, after
    _PUBLIC_RESPONSE_FENCES_V1[id(fence)] = (*row[:9], wall, after, *row[11:])
    return wall, after


@contextmanager
def _public_response_fence_v1(fence):
    row = _PUBLIC_RESPONSE_FENCES_V1.get(id(fence))
    _native_require(type(fence) is _PublicResponseFenceV1 and row is not None and row[0] is fence,
                    "unissued public response fence")
    binding, owner = row[1], row[2]
    authority_lock = binding._authority._lock if binding._authority is not None else binding._publication_lock
    # S -> O -> A -> P. Callers only install/return an already assembled immutable
    # result here; source lookup, serialization and external effects precede it.
    with owner._lock, owner._observation_lock, authority_lock, binding._publication_lock:
        _check_public_response_fence_v1(fence)
        yield
        _check_public_response_fence_v1(fence)


def _resolve_public_operational_inputs_v1(*, binding, evaluated_at_ns: int):
    """Join the original binding's immutable inputs before capture/publication."""
    from .sqlite_reference import _public_root_facts_v1

    facts = _public_binding_facts_v1(binding)
    inputs = facts["source_inputs"]
    # Preserve the typed missing-input result before touching a root.
    if "storage_root" not in inputs:
        raise SourcePolicyError(ReasonCode.OWNER_DATA_MISSING, "public source-owner storage input unavailable")
    root = _public_root_facts_v1(inputs["storage_root"])
    return _validate_public_operational_input_view_v1(inputs=inputs, capture=binding._capture,
        root=root, native_qualified=facts["native_qualified"], evaluated_at_ns=evaluated_at_ns)


def _validate_public_operational_input_view_v1(*, inputs, capture, root, native_qualified, evaluated_at_ns):
    """Pure shared join of previously observed root facts and typed owner views."""
    from ..market_data_ingest.adapter import PublicDataReadRequestV1, compile_public_read_request_v1
    from ..market_data_ingest.binding import PublicMetadataSnapshotV1, SelectedPITPublicDataContractV2
    from .receipts import PublicCaptureRequestV1

    _native_require(type(capture) is PublicCaptureRequestV1 and type(inputs) in (dict, MappingProxyType)
                    and type(native_qualified) is bool, "invalid public operational input view")
    capture.__post_init__()
    _public_nanoseconds_v1(evaluated_at_ns)
    scope = capture.scope
    required = {"requests", "contracts", "metadata", "source_bindings", "rate_bindings",
                "exclusive_allocation_refs", "storage_root", "process_epoch_id", "monotonic_clock_id",
                "wall_clock_source_id", "clock_quality_ref", "wall_uncertainty_ns", "account_applicability_or_none"}
    missing = sorted(required - set(inputs))
    if missing:
        raise SourcePolicyError(ReasonCode.OWNER_DATA_MISSING,
                                "public source-owner operational inputs unavailable: " + ", ".join(missing))
    for name in ("requests", "contracts", "metadata", "source_bindings", "rate_bindings"):
        _native_require(type(inputs[name]) is tuple and len(inputs[name]) <= 4096,
                        "invalid bounded public source-owner input: " + name)
    _native_require(inputs["requests"] and len(inputs["requests"]) <= scope.budget.max_requests,
                    "finite request selection is absent or exceeds the original budget")
    for name in ("process_epoch_id", "monotonic_clock_id", "wall_clock_source_id", "clock_quality_ref"):
        _native_ident(inputs[name])
    _public_nanoseconds_v1(inputs["wall_uncertainty_ns"])
    _native_require(inputs["wall_uncertainty_ns"] <= scope.budget.maximum_wall_uncertainty_ns,
                    "source clock quality exceeds the admitted uncertainty")
    _native_require(root["root_ref"] == scope.storage_root_ref
                    and root["native_qualified"] is native_qualified, "source storage origin/scope differs")
    _public_refs_v1(inputs["exclusive_allocation_refs"])
    sources, metadata, contracts = {}, {}, {}
    for row in inputs["source_bindings"]:
        _native_require(type(row) is PublicDataSourceBindingV1, "untyped public source binding")
        row.__post_init__()
        _native_require(row.binding_id not in sources and row.profile_id is scope.profile_id
                        and set(row.source_ids) <= set(scope.source_ids)
                        and set(row.allowed_operation_ids) <= set(scope.native_operation_ids)
                        and set(row.permitted_consumer_ids) <= set(scope.permitted_consumer_ids)
                        and scope.source_contract_version in row.source_contract_versions
                        and row.known_at_ns <= evaluated_at_ns < row.expires_at_ns
                        and row.effective_from_ns <= evaluated_at_ns
                        and (row.effective_until_ns_or_none is None or evaluated_at_ns < row.effective_until_ns_or_none),
                        "public source binding is conflicting, stale or outside the admitted scope")
        sources[row.binding_id] = row
    _native_require(set(sources) == set(capture.source_binding_refs), "capture source references do not resolve exactly")
    if native_qualified:
        # The authenticated source owner already issued these exact receipts.
        pairs = inputs.get("source_pairs")
        _native_require(type(pairs) is tuple and pairs, "native source/right custody unavailable")
        qualified = inputs.get("qualified_source_bindings")
        _native_require(type(qualified) is tuple and len(qualified) == len(sources),
                        "native accepted material source qualification unavailable")
        for row in sources.values():
            matched = tuple(item for item in qualified if type(item) is tuple and len(item) == 5 and item[0] is row)
            _native_require(len(matched) == 1 and matched[0][4] is True,
                            "native material source facts are unqualified or synthetic")
            expected = tuple((item.source_id, item.source_contract_version, item.receipt_id,
                              rights.receipt_id) for item, rights in pairs)
            selected = tuple(zip(row.source_ids, row.source_contract_versions, row.source_receipt_refs, row.rights_receipt_refs))
            _native_require(set(selected) <= set(expected), "source candidate is not joined to the accepted source/right receipts")
        # Source/right acceptance is not quota or exclusive shared-counter
        # custody. No native allocation issuer is available through this owner;
        # caller-authored rate rows and matching reference strings cannot replace
        # it. Keep synthetic quota arithmetic usable without granting transport.
        raise SourcePolicyError(ReasonCode.OWNER_DATA_MISSING,
                                "verified native provider quota and exclusive allocation custody unavailable")
    for row in inputs["metadata"]:
        _native_require(type(row) is PublicMetadataSnapshotV1, "untyped public metadata")
        row.__post_init__()
        _native_require(row.metadata_id not in metadata and row.profile_id is scope.profile_id
                        and row.instrument_id in capture.requested_instrument_ids
                        and row.known_at_ns <= evaluated_at_ns < row.expires_at_ns
                        and row.effective_from_ns <= evaluated_at_ns
                        and (row.effective_until_ns_or_none is None or evaluated_at_ns < row.effective_until_ns_or_none),
                        "public metadata is conflicting, stale or outside selected instruments")
        metadata[row.metadata_id] = row
    for row in inputs["contracts"]:
        _native_require(type(row) is SelectedPITPublicDataContractV2, "untyped public canonical contract")
        row.__post_init__()
        _native_require(row.contract_id not in contracts and row.profile_id is scope.profile_id,
                        "conflicting/cross-profile public canonical contract")
        contracts[row.contract_id] = row
    applicability = inputs["account_applicability_or_none"]
    if applicability is not None:
        _native_require(type(applicability) is SelectedAccountApplicabilityV1, "untyped account applicability")
        applicability.__post_init__()
        _native_require(applicability.profile_id is scope.profile_id
                        and applicability.account_scope_ref == scope.account_scope_ref_or_none
                        and applicability.qualification_ref == capture.account_applicability_ref_or_none
                        and applicability.available_at_ns <= evaluated_at_ns
                        and applicability.effective_from_ns <= evaluated_at_ns < applicability.effective_until_ns,
                        "public account applicability unavailable or mismatched")
    rates = inputs["rate_bindings"]
    rate_ids = set()
    for rate in rates:
        _native_require(type(rate) is PublicRequestRateBindingV1, "untyped public request allocation")
        rate.__post_init__()
        _native_require(rate.binding_id not in rate_ids and rate.profile_id is scope.profile_id
                        and rate.allocation_ref in inputs["exclusive_allocation_refs"]
                        and rate.effective_from_ns <= evaluated_at_ns < rate.expires_at_ns,
                        "public allocation is conflicting, shared without custody or expired")
        rate_ids.add(rate.binding_id)
    plan, request_ids = [], set()
    for request in inputs["requests"]:
        _native_require(type(request) is PublicDataReadRequestV1, "untyped public read request")
        request.__post_init__()
        _native_require(request.request_id not in request_ids and request.profile_id is scope.profile_id
                        and request.capture_request_ref == capture.request_id
                        and request.operation_id in capture.requested_operation_ids
                        and set(request.instrument_ids) <= set(capture.requested_instrument_ids)
                        and request.source_binding_ref in sources
                        and set(request.metadata_refs) <= set(metadata), "public request is unbound or outside capture")
        request_ids.add(request.request_id)
        source = sources[request.source_binding_ref]
        selected_metadata = tuple(metadata[ref] for ref in request.metadata_refs)
        admitted_contract_receipts = set(zip(source.source_contract_versions,
            source.source_receipt_refs, source.rights_receipt_refs))
        selected_contracts = [row for row in contracts.values()
            if row.source_contract_version == request.native_contract_version
            and (row.source_contract_version, row.source_currentization_receipt_ref,
                 row.rights_receipt_ref) in admitted_contract_receipts]
        _native_require(len(selected_contracts) == 1, "public request has no unique admitted canonical contract")
        matching_rates = [row for row in rates if request.operation_id in row.operation_classes]
        _native_require(len(matching_rates) == 1, "public operation has no unique active request allocation")
        accepted_refs = set(source.source_ids + source.source_receipt_refs + source.original_evidence_refs)
        _native_require(set(matching_rates[0].source_refs) <= accepted_refs,
                        "public request allocation is not joined to admitted source evidence")
        if request.operation_id in {"K_WS", "P_WS"}:
            # Legacy same-product capture scope does not qualify fee facts.
            # A distinct economic class requires its accepted source relation;
            # credential product scope remains the configured legal product.
            _native_require(applicability is not None and (applicability.product_scope_ref == source.legal_product_ref
                or any(row is source for row in _public_accepted_account_sources_v1(inputs=inputs,
                    applicability=applicability, native_only=native_qualified, known_as_of_ns=evaluated_at_ns))),
                            "authenticated public stream account/product qualification unavailable")
        descriptor = compile_public_read_request_v1(request=request, source_binding=source, metadata=selected_metadata)
        _native_require(descriptor["receive_scope_class"] in scope.receive_scope_classes,
                        "compiled receive scope was not explicitly admitted")
        if descriptor["receive_scope_class"] == "GLOBAL_PUBLIC_LIFECYCLE":
            _native_require(set(request.instrument_ids) == set(capture.requested_instrument_ids)
                and {row.instrument_id for row in selected_metadata} == set(capture.requested_instrument_ids),
                "global lifecycle request must cover every capture-selected instrument")
        plan.append((request, source, selected_metadata, selected_contracts[0], descriptor))
    _native_require(set(row[0].operation_id for row in plan) == set(capture.requested_operation_ids),
                    "finite request plan does not cover the exact captured operation set")
    return tuple(plan)


def _require_public_credential_v1(*, credential, descriptor):
    import os
    import time

    _native_require(type(credential) is PublicCredentialBindingV1
                    and _PUBLIC_CREDENTIALS_V1.get(id(credential._binding)) is credential
                    and credential._process_id == os.getpid(), "public credential has no original issuance custody")
    binding, row = credential._binding, credential._row
    facts = _public_binding_facts_v1(binding)
    _native_require(binding._owner is not None and binding._resources is credential._resources
                    and facts["native_qualified"] is credential._native_qualified,
                    "public credential permission origin/resources changed")
    _, wall, _ = binding._owner._guard_v1()
    plan = _resolve_public_operational_inputs_v1(binding=binding, evaluated_at_ns=wall)
    matches = [item for item in plan if item[4] == descriptor and item[0].operation_id in {"K_WS", "P_WS"}]
    _native_require(len(matches) == 1 and descriptor["method"] == "WEBSOCKET"
                    and descriptor["path"] in row["allowed_handshake_paths"] and not descriptor["query"]
                    and row["alias_ref"] == facts["scope"].credential_alias_ref_or_none
                    and row["profile_id"] == facts["scope"].profile_id.value
                    and row["account_scope_ref"] == facts["scope"].account_scope_ref_or_none
                    and row["product_scope_ref"] == matches[0][1].legal_product_ref
                    and row["generation"] == credential._generation
                    and row["valid_from_ns"] <= wall < credential._expiry <= row["expires_at_ns"],
                    "public credential path/account/product/generation unavailable")
    if credential._native_qualified:
        from ...service.owner_source_use_windows import _check_public_credential_file_v1

        _check_public_credential_file_v1(binding=binding, credential_row=row)
    _native_require(time.time_ns() < credential._expiry, "public credential expired before signing/connect")
    return wall


def _load_public_credential_v1(*, binding, descriptor):
    import os
    from ...service.owner_source_use_windows import _read_public_credential_key_v1

    facts = _public_binding_facts_v1(binding)
    _native_require(binding._owner is not None, "public credential has no receiving owner")
    _, wall, _ = binding._owner._guard_v1()
    plan = _resolve_public_operational_inputs_v1(binding=binding, evaluated_at_ns=wall)
    _native_require(len([item for item in plan if item[4] == descriptor
                    and item[0].operation_id in {"K_WS", "P_WS"}]) == 1,
                    "public credential requested for an unauthenticated or unbound route")
    existing = _PUBLIC_CREDENTIALS_V1.get(id(binding))
    if existing is not None:
        _require_public_credential_v1(credential=existing, descriptor=descriptor)
        return existing
    row, key = _read_public_credential_key_v1(binding=binding)
    _native_require(type(row) is MappingProxyType and set(row) == {"alias_ref", "profile_id", "account_scope_ref",
        "product_scope_ref", "key_identifier", "algorithm", "relative_key_file", "valid_from_ns", "expires_at_ns",
        "generation", "allowed_handshake_paths"}, "protected credential metadata closure differs")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

    permitted = {
        Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: {
            "KALSHI_ED25519": Ed25519PrivateKey, "KALSHI_RSA_PSS": RSAPrivateKey},
        Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: {"RETAIL_ED25519": Ed25519PrivateKey},
    }
    expected = permitted.get(facts["scope"].profile_id, {}).get(row["algorithm"])
    _native_require(expected is not None and isinstance(key, expected), "parsed credential does not match the enrolled algorithm")
    for name in ("alias_ref", "profile_id", "account_scope_ref", "product_scope_ref", "key_identifier", "relative_key_file"):
        _native_ident(row[name])
    for name in ("valid_from_ns", "expires_at_ns"):
        _public_nanoseconds_v1(row[name])
    _public_counter_v1(row["generation"], allow_zero=True)
    _native_require(type(row["allowed_handshake_paths"]) is tuple and row["allowed_handshake_paths"] == (descriptor["path"],),
                    "public credential has a broadened signing path")
    result = object.__new__(PublicCredentialBindingV1)
    result._binding, result._row, result._key, result._resources = binding, row, key, binding._resources
    result._expiry = min(row["expires_at_ns"], binding._capture.operating_expires_at_ns)
    result._generation, result._process_id, result._native_qualified = row["generation"], os.getpid(), facts["native_qualified"]
    _PUBLIC_CREDENTIALS_V1[id(binding)] = result
    try:
        _require_public_credential_v1(credential=result, descriptor=descriptor)
    except BaseException:
        _PUBLIC_CREDENTIALS_V1.pop(id(binding), None)
        raise
    return result


def _public_handshake_headers_v1(*, binding, descriptor):
    import base64

    facts = _public_binding_facts_v1(binding)
    if facts["scope"].profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT:
        _native_require(descriptor["host"] == "ws.gemini.com" and descriptor["method"] == "WEBSOCKET",
                        "unbound unauthenticated public stream")
        return {}
    credential = _load_public_credential_v1(binding=binding, descriptor=descriptor)
    wall = _require_public_credential_v1(credential=credential, descriptor=descriptor)
    row = credential._row
    timestamp = str(wall // 1_000_000)
    message = (timestamp + "GET" + descriptor["path"]).encode("utf-8")
    if row["algorithm"] == "KALSHI_RSA_PSS":
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        # Owner-accepted K-AUTH clarification: direct message signing, SHA-256,
        # MGF1/SHA-256 and exactly the 32-byte SHA-256 digest-length salt.
        signed = credential._key.sign(message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    else:
        signed = credential._key.sign(message)
    signature = base64.b64encode(signed).decode("ascii")
    _require_public_credential_v1(credential=credential, descriptor=descriptor)
    if row["algorithm"] == "RETAIL_ED25519":
        return {"X-PM-Access-Key": row["key_identifier"], "X-PM-Timestamp": timestamp, "X-PM-Signature": signature}
    return {"KALSHI-ACCESS-KEY": row["key_identifier"], "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "KALSHI-ACCESS-SIGNATURE": signature}


def _release_public_credential_v1(*, binding):
    credential = _PUBLIC_CREDENTIALS_V1.get(id(binding))
    if credential is not None and credential._binding is binding:
        credential._key = None
        _PUBLIC_CREDENTIALS_V1.pop(id(binding), None)


class _VerifiedSourceUseActionV1:
    """One original verification; neither a value constructor nor serializable."""

    __slots__ = ("_authority", "_root", "_pending", "_proof", "_attempted")

    def __init__(self):
        raise TypeError("source-use verification is owned by the original authority")

    def __reduce__(self):
        raise TypeError("source-use verification cannot be serialized")


class KalshiSourceUseBindingV1:
    """Private, registered process binding. Public receipts alone are not authority."""

    __slots__ = ("_authority", "_root", "_generation", "_declaration_ref", "_review_ref",
                 "_review_event_ref", "_use_event_ref", "_permit", "_source", "_rights")

    def __init__(self):
        raise TypeError("source-use bindings are issued by their original authority")

    def __reduce__(self):
        raise TypeError("source-use bindings cannot be serialized")


class _SourceUseObservationPermitV1:
    __slots__ = ("_event", "_request", "_deadline", "_owner", "_route", "_published", "_failed", "_started")

    def __init__(self):
        raise TypeError("observation permission requires its separately verified action")

    def __reduce__(self):
        raise TypeError("observation permission cannot be serialized")


@dataclass(frozen=True, slots=True)
class _PendingSourceUseActionV1:
    request_ref: str
    proposal: object
    expected: tuple
    original_heads: tuple
    original: object
    expires_at_utc: datetime
    deadline_monotonic_ns: int
    authentication: object
    preview: str
    public_resources: object = None
    public_inputs: object = None


def _create_source_use_authority_v1(root):
    from uuid import uuid4
    from ...service.owner_source_use_windows import _require_native_root_v1
    from .persistence import InMemoryPersistenceAdapterV1, OwnerControlMemoryAdapterV1, PersistenceAvailabilityV1
    from .receipts import _source_use_require_v1
    from .transaction import TrancheCUnitOfWorkV1, TransactionRetryPolicyV1

    _require_native_root_v1(root)
    _source_use_require_v1(root.enrollment.root_state == "ACTIVE")
    authority = object.__new__(SourceUseAuthorityV1)
    authority._root = root
    authority._lock = RLock()
    authority._process_ref = uuid4().hex
    authority._clock_ref = uuid4().hex
    authority._issuer = object()
    authority._stopped = False
    authority._pending = None
    authority._completion_pending = None
    authority._valid_completion = None
    authority._selected_scope = None
    authority._public_configuration = None
    authority._public_input_view = None
    authority._head = authority._review = authority._use = None
    authority._last_use_event = None
    authority._bindings = {}
    authority._active_permit = None
    authority._last_operating_permit = None
    authority._counter = root.enrollment.initial_counter
    authority._last_clock = None
    authority._last_disposition = "DENIED_NO_ACTION"
    now, mono = authority._clock_v1()
    authority._deadline = mono + 900_000_000_000
    _source_use_require_v1(authority._deadline <= 2**63 - 1)
    authority._expires = now + timedelta(seconds=900)
    adapter = object.__new__(OwnerControlMemoryAdapterV1)
    InMemoryPersistenceAdapterV1.__init__(adapter)
    adapter._availability = PersistenceAvailabilityV1.AVAILABLE_OWNER_CONTROL_EPHEMERAL
    adapter._control_scope = (root, authority._issuer, authority._process_ref)
    adapter._original_control_scope = adapter._control_scope
    adapter._registered_batches = {}
    adapter._pending_batch = None
    adapter._public_control_mode = False
    authority._adapter = adapter
    authority._uow = TrancheCUnitOfWorkV1(adapter, TransactionRetryPolicyV1(1))
    return authority


class SourceUseAuthorityV1:
    """Sole ephemeral issuer. Lock order is S → O → A → P, never reversed.

    Device calls and cryptographic completion execute outside A. Storage only
    examines previously registered immutable batches and never calls back here.
    """

    def __init__(self):
        raise TypeError("source-use authority requires original native bootstrap")

    def __reduce__(self):
        raise TypeError("process source-use authority cannot be serialized")

    def _clock_v1(self):
        from .receipts import _source_use_require_v1

        before, wall, after = time.monotonic_ns(), time.time_ns(), time.monotonic_ns()
        _kalshi_observation_time(all(type(value) is int and 0 <= value <= 2**63 - 1 for value in (before, wall, after))
                                 and before <= after)
        if self._last_clock is not None and (wall < self._last_clock[0] or before < self._last_clock[1]):
            self.stop_v1()
            _kalshi_observation_time(False)
        self._last_clock = (wall, after)
        return KalshiFeeObservationOwnerV1._wall_datetime_v1(wall), after

    def _live_v1(self):
        from .receipts import _source_use_require_v1

        _source_use_require_v1(not self._stopped and self._adapter._scope_valid_v1())
        now, mono = self._clock_v1()
        if mono >= self._deadline or now >= self._expires:
            self.stop_v1()
            _kalshi_observation_time(False)
        return now, mono

    def stop_v1(self):
        # Preallocated latch, no append/signature, no record or permit allocation.
        with self._lock:
            self._stopped = True
            self._pending = None
            self._valid_completion = None
            self._use = None
            self._active_permit = None
            self._bindings.clear()
            self._public_input_view = None
            self._last_disposition = "STOPPED"

    def cancel_pending_v1(self):
        with self._lock:
            self._pending = None
            self._valid_completion = None
            self._last_disposition = "CANCELLED"

    def _heads_v1(self):
        from .receipts import _source_use_require_v1

        adapter = self._adapter
        with adapter._lock:
            head = adapter.load_committed_source_action_head_v1(self._process_ref)
            _source_use_require_v1(head == self._head)
            originals = []
            for ref in (() if head is None else (head.typed_payload.declaration_ref, head.typed_payload.review_ref)):
                if ref is None:
                    originals.append(None)
                else:
                    row = adapter.load_committed_source_use_record_v1(ref)
                    _source_use_require_v1(row is not None
                        and adapter.load_committed_source_use_head_v1(row.typed_payload.stream_id) == row)
                    originals.append(row)
            return head, tuple(originals) if head is not None else (None, None)

    def _public_source_pairs_v1(self, *, evaluated_at_utc):
        from .receipts import _public_identity_v1

        scope = self._selected_scope
        facts = self._review.typed_payload.review_facts
        pairs = []
        for source_id in scope.source_ids:
            # An anonymous public scope is a source-use identity, never evidence
            # of an account, balance, membership or trading entitlement.
            account = scope.account_scope_ref_or_none or _public_identity_v1(
                "PUBLIC_UNAUTHENTICATED_SCOPE_V1", scope.profile_id.value, source_id)
            source = PITSourceCurrentizationReceiptV1(
                _public_identity_v1("PUBLIC_SOURCE_REVIEW_V1", self._review.record_id, source_id),
                scope.profile_id, source_id, scope.source_contract_version, facts.factual_checked_at_utc,
                facts.source_effective_at_utc, facts.source_expires_at_utc, self._root.enrollment.owner_ref,
                facts.recheck_triggers, False, True)
            rights = PITRightsAdmissionReceiptV1(
                _public_identity_v1("PUBLIC_SOURCE_RIGHTS_V1", self._use.record_id, source_id),
                scope.profile_id, account, source_id, facts.agreement_id, facts.agreement_version,
                scope.internal_use_class, "ADMITTED_INTERNAL_USE", self._use.recorded_at,
                self._use.typed_payload.expires_at_utc, facts.recheck_triggers, False,
                scope.permitted_retention_class, scope.prohibited_redistribution_class)
            validate_pit_source_rights_admission_v1(source, rights, admission_id=self._use.record_id,
                profile_id=scope.profile_id, account_scope=account, internal_use_class=scope.internal_use_class,
                permitted_retention_class=scope.permitted_retention_class, evaluated_at_utc=evaluated_at_utc)
            pairs.append((source, rights))
        return tuple(pairs)

    def _bind_public_operational_inputs_v1(self, *, capture, inputs, accepted_source_evidence=()):
        """Retain accepted owner views; this private join grants no capture effect."""
        from ...service.owner_source_use_windows import _public_scope_resources_v1
        from .sqlite_reference import _public_root_facts_v1
        from .receipts import PublicCaptureRequestV1, _source_use_require_v1
        from ..market_data_ingest.source_dependency import project_accepted_public_field_bindings_v1

        _native_require(type(capture) is PublicCaptureRequestV1 and type(inputs) in (dict, MappingProxyType),
                        "public input retention requires an exact capture and mapping")
        capture.__post_init__()
        required = {"requests", "contracts", "metadata", "source_bindings", "rate_bindings",
            "exclusive_allocation_refs", "wall_clock_source_id", "clock_quality_ref", "wall_uncertainty_ns",
            "account_applicability_or_none", "source_epoch_id", "input_version"}
        _native_require(set(inputs) == required, "public retained inputs have missing or extra fields")
        retained = MappingProxyType(dict(inputs))
        for name in ("source_epoch_id", "input_version"):
            _native_ident(retained[name])
        # Protection/file inspection is outside the short authority lock.
        resources = _public_scope_resources_v1(self._root, capture.scope)
        root = _public_root_facts_v1(resources["storage_root"])
        _native_require(type(accepted_source_evidence) is tuple and len(accepted_source_evidence) <= 4096,
                        "invalid accepted source evidence selection")
        with self._lock:
            _source_use_require_v1(self._review is not None and self._use is not None)
            selected_review, selected_use = self._review, self._use
        qualified = []
        for row in accepted_source_evidence:
            _native_require(type(row) is tuple and len(row) == 3, "invalid accepted source evidence row")
            matches = tuple(item for item in retained["source_bindings"] if item.binding_id == row[0])
            _native_require(len(matches) == 1 and not any(item[0] is matches[0] for item in qualified),
                            "accepted source evidence has no unique selected binding")
            qualified.append(project_accepted_public_field_bindings_v1(source_binding=matches[0],
                acceptance_results=row[1], originals=row[2], review_facts=selected_review.typed_payload.review_facts))
        qualified = tuple(qualified)
        with self._lock:
            now, _mono = self._live_v1()
            _source_use_require_v1(self._review is not None and self._use is not None
                and self._head == self._use and self._pending is None and self._completion_pending is None
                and self._active_permit is None and capture.scope == self._selected_scope
                and capture.scope.scope_generation == self._head.typed_payload.generation_after
                and self._review is selected_review and self._use is selected_use)
            pairs = self._public_source_pairs_v1(evaluated_at_utc=now)
            merged = MappingProxyType(dict(retained, source_pairs=pairs, qualified_source_bindings=qualified,
                storage_root=resources["storage_root"], process_epoch_id=self._process_ref,
                monotonic_clock_id=self._clock_ref))
            _validate_public_operational_input_view_v1(inputs=merged, capture=capture, root=root,
                native_qualified=resources["native_qualified"], evaluated_at_ns=self._last_clock[0])
            self._public_input_view = (self._root, self._review, self._use, capture, retained, qualified)

    def _public_retained_inputs_v1(self, *, capture):
        from .receipts import _source_use_require_v1

        view = self._public_input_view
        if view is None:
            return None
        _source_use_require_v1(view[0] is self._root and view[1] is self._review and view[2] is self._use
            and view[3] == capture and capture.scope == self._selected_scope
            and capture.scope.scope_generation == self._head.typed_payload.generation_after)
        return view

    def prepare_action_v1(self, raw_proposal: bytes):
        from dataclasses import replace
        from uuid import uuid4
        from ...service.owner_source_use import _source_use_proposal_v1, _begin_source_use_authentication_v1
        from .receipts import (_source_use_require_v1, SourceUseControlRecordV1,
                              PublicSourceUseOriginalV1, PublicDataSourceUseScopeV1)
        from .serialization import deterministic_json

        proposal = _source_use_proposal_v1(raw_proposal)
        action, scope = proposal["action"], proposal["scope"]
        public = type(scope) is PublicDataSourceUseScopeV1
        resources = None
        public_inputs = None
        if public and action == "OBSERVE_ONCE":
            # Protected metadata checks happen before A; no key or SQLite read.
            from ...service.owner_source_use_windows import _public_scope_resources_v1

            resources = _public_scope_resources_v1(self._root, scope)

        def original_record(stream, kind, sequence, operation, predecessor, selected_scope, content, reason, input_class):
            if public:
                return PublicSourceUseOriginalV1("PUBLIC_SOURCE_ORIGINAL_V1", stream, sequence, kind,
                    operation, predecessor, selected_scope, content, reason, input_class)
            return SourceUseControlRecordV1(stream, kind, sequence, operation, predecessor,
                                             selected_scope, content, reason, input_class)

        with self._lock:
            now, mono = self._live_v1()
            _source_use_require_v1(self._pending is None and self._completion_pending is None
                                   and (self._selected_scope is None or scope == self._selected_scope))
            if self._head is None:
                _source_use_require_v1(not self._adapter._tables["receipt_records"])
                self._adapter._public_control_mode = public
            else:
                _source_use_require_v1(self._adapter._public_control_mode is public)
            head, originals = self._heads_v1()
            expected = (None if head is None else head.record_id,
                        *(None if row is None else row.record_id for row in originals))
            for name, ref in (("expected_declaration_ref", expected[1]), ("expected_review_ref", expected[2])):
                if name in proposal:
                    _source_use_require_v1(proposal[name] == ref)
            positive = action in {"REVIEW_ACCEPT", "USE_ADMIT", "OBSERVE_ONCE"}
            if positive:
                rows = self._adapter._tables["receipt_records"]
                _source_use_require_v1(len(rows) + 2 <= 256
                    and sum(len(deterministic_json(row).encode("utf-8")) for row in rows.values()) + 2 * 65536 <= 16 * 1024 * 1024)
            _source_use_require_v1(head is not None or action == "REVIEW_ACCEPT")
            if action == "OBSERVE_ONCE":
                _source_use_require_v1(self._use is not None and self._active_permit is None)
                if public:
                    public_inputs = self._public_retained_inputs_v1(capture=proposal["capture"])
                    _source_use_require_v1(public_inputs is not None or not resources["native_qualified"])
            if action == "USE_ADMIT":
                _source_use_require_v1(self._review is not None)
            original = None
            if action != "OBSERVE_ONCE":
                review_action = action in {"REVIEW_ACCEPT", "INVALIDATE_REVIEW"}
                old = originals[1 if review_action else 0]
                kind = "SOURCE_REVIEW" if review_action else "OWNER_DECLARATION"
                if positive:
                    content = proposal["original"]
                    if old is None or old.typed_payload.content != content:
                        fresh = old is None or old.typed_payload.action == "WITHDRAW"
                        stream = ("review_" if review_action else "declaration_") + uuid4().hex if fresh else old.typed_payload.stream_id
                        original = original_record(stream, kind, 1 if fresh else old.sequence + 1,
                            "RECORD" if fresh else "SUPERSEDE", None if fresh else old.record_id, scope, content,
                            None if fresh else ("OWNER_CONFIRMED_REVIEW_REPLACEMENT" if review_action else "OWNER_CONFIRMED_DECLARATION_REPLACEMENT"),
                            "UNVERIFIED_SUBMISSION")
                else:
                    _source_use_require_v1(old is not None)
                    if old.typed_payload.action != "WITHDRAW":
                        original = original_record(old.typed_payload.stream_id, kind, old.sequence + 1,
                            "WITHDRAW", old.record_id, scope, None, proposal["reason"], old.typed_payload.input_class)
            expiry = now
            if positive:
                if public and action == "OBSERVE_ONCE":
                    capture = proposal["capture"]
                    seconds, nanos = divmod(capture.operating_expires_at_ns, 1_000_000_000)
                    # The enclosing legacy-compatible action clock rounds up;
                    # the private permit still enforces the exact exclusive ns.
                    requested = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(
                        seconds=seconds, microseconds=(nanos + 999) // 1000)
                    _source_use_require_v1(self._last_clock[0] < capture.operating_expires_at_ns
                        and scope.scope_generation == head.typed_payload.generation_after
                        and mono < scope.budget.deadline_monotonic_ns
                        and capture.operating_expires_at_ns <= resources["expires_at_ns"])
                else:
                    requested = proposal["observation"].expires_at_utc if action == "OBSERVE_ONCE" else proposal["requested_expires_at_utc"]
                _source_use_require_v1(requested <= self._expires)
                expiry = min(requested, self._expires)
                if action == "REVIEW_ACCEPT":
                    facts = proposal["review_facts"]
                    _source_use_require_v1(facts.factual_checked_at_utc <= now)
                    _source_use_require_v1(requested <= facts.source_expires_at_utc)
                    expiry = min(expiry, facts.source_expires_at_utc)
                else:
                    _source_use_require_v1(self._review is not None)
                    _source_use_require_v1(requested <= self._review.typed_payload.expires_at_utc)
                    expiry = min(expiry, self._review.typed_payload.expires_at_utc)
                    declaration = original if original is not None else (None if originals[0] is None else originals[0].typed_payload)
                    _source_use_require_v1(declaration is not None and declaration.content is not None
                                           and declaration.content.claimed_effective_at_utc is not None
                                           and declaration.content.claimed_effective_at_utc <= now
                                           and declaration.content.claimed_expires_at_utc is not None)
                    expiry = min(expiry, declaration.content.claimed_expires_at_utc)
                    _source_use_require_v1(requested <= declaration.content.claimed_expires_at_utc)
                    if action == "OBSERVE_ONCE":
                        expiry = min(expiry, self._use.typed_payload.expires_at_utc)
                        _source_use_require_v1(requested <= expiry)
                _source_use_require_v1(now < expiry)
            request = uuid4().hex
            preview = deterministic_json({"request_ref": request, "proposal": dict(proposal),
                "expected_event_ref": expected[0], "expected_declaration_ref": expected[1],
                "expected_review_ref": expected[2], "selected_original": original,
                "current_originals": originals, "accepted_expires_at_utc": expiry,
                "owner_ref": self._root.enrollment.owner_ref, "key_ref": self._root.enrollment.enrollment_ref,
                "process_ref": self._process_ref, "generation": 0 if head is None else head.typed_payload.generation_after})
            pending = _PendingSourceUseActionV1(request, proposal, expected, originals, original, expiry,
                min(mono + 120_000_000_000, self._deadline), None, preview, resources, public_inputs)
            self._pending = pending
        try:
            authentication = _begin_source_use_authentication_v1(self._root.enrollment, operation="GET")
            with self._lock:
                self._live_v1()
                _source_use_require_v1(self._pending is pending)
                self._pending = replace(pending, authentication=authentication)
                return request, preview
        except BaseException:
            with self._lock:
                if self._pending is pending:
                    self._pending = None
            raise

    def _spine_v1(self, payload, now, request):
        from .receipts import (EconomicReceiptEventSpineV1, EconomicRecordTypeV1, SourceUseControlRecordV1,
                              PublicSourceUseOriginalV1, PublicDataSourceUseActionV1, _public_identity_v1)

        if type(payload) in (PublicSourceUseOriginalV1, PublicDataSourceUseActionV1):
            original = type(payload) is PublicSourceUseOriginalV1
            prefix = "PUBLIC_SOURCE_ORIGINAL_V1" if original else "PUBLIC_SOURCE_ACTION_V1"
            stream = payload.stream_id if original else payload.process_ref
            return EconomicReceiptEventSpineV1(
                record_id=_public_identity_v1(prefix, stream, payload.sequence),
                record_type=EconomicRecordTypeV1.PUBLIC_SOURCE_USE_CONTROL, schema_version=payload.schema_version,
                semantic_owner="QTT_PUBLIC_DATA_SOURCE_USE", implementation_owner="QTT_PUBLIC_DATA_SOURCE_USE",
                context_ref=self._process_ref, effective_at=now, recorded_at=now,
                causation_id="ACTION::" + request, correlation_id="PROCESS::" + self._process_ref,
                traceparent="TRACE::" + request, tracestate="LOCAL_OWNER_CONTROL", sequence=payload.sequence,
                aggregate_id=_public_identity_v1(prefix, stream), aggregate_version=payload.sequence,
                authority_class="PUBLIC_DATA_CANDIDATE_NO_OPERATING_AUTHORITY", typed_payload=payload)

        original = type(payload) is SourceUseControlRecordV1
        aggregate = ("SOURCE_USE::" + payload.stream_id) if original else ("SOURCE_ACTION::" + self._process_ref)
        owner = "QTT_SOURCE_USE_CUSTODY" if original else "QTT_SOURCE_USE_POLICY"
        return EconomicReceiptEventSpineV1(
            record_id=f"{aggregate}::{payload.sequence:020d}",
            record_type=EconomicRecordTypeV1.SOURCE_USE_CONTROL if original else EconomicRecordTypeV1.SOURCE_USE_ATTRIBUTED_ACTION,
            schema_version="SOURCE_USE_CONTROL_V1" if original else "SOURCE_USE_ATTRIBUTED_ACTION_V1",
            semantic_owner=owner, implementation_owner=owner, context_ref=self._process_ref,
            effective_at=now, recorded_at=now, causation_id="ACTION::" + request,
            correlation_id="PROCESS::" + self._process_ref, traceparent="TRACE::" + request,
            tracestate="LOCAL_OWNER_CONTROL", sequence=payload.sequence, aggregate_id=aggregate,
            aggregate_version=payload.sequence,
            authority_class="RECORDED_NOT_AUTHENTICATED_NOT_ADMITTED" if original else "PROCESS_SCOPED_SOURCE_USE_EVENT",
            typed_payload=payload)

    def complete_action_v1(self, pending_ref, raw_response):
        from dataclasses import replace
        from ...service.owner_source_use import _verify_source_use_response_v1
        from ...service.owner_source_use_windows import _require_completed_operation_v1
        from .receipts import _source_use_require_v1, SourceUseAttributedActionV1

        with self._lock:
            pending = self._pending
            self._pending = None  # First completion attempt consumes, including malformed input.
            _source_use_require_v1(type(pending_ref) is str and type(pending) is _PendingSourceUseActionV1
                                   and pending.request_ref == pending_ref and pending.authentication is not None)
            now, mono = self._live_v1()
            _source_use_require_v1(mono < pending.deadline_monotonic_ns)
            _source_use_require_v1(self._completion_pending is None)
            self._completion_pending = self._valid_completion = pending
        committed = [False]
        try:
            _require_completed_operation_v1(self._root, pending_ref, raw_response)
            proof = _verify_source_use_response_v1(pending.authentication, raw_response, verified_at_utc=now)
            return self._commit_verified_action_v1(pending, proof, committed)
        except BaseException:
            if pending.proposal["action"] in {"WITHDRAW_USE", "INVALIDATE_REVIEW"}:
                with self._lock:
                    self.stop_v1()
                    self._last_disposition = ("STOPPED_WITHDRAWAL_COMMITTED" if committed[0] else
                        "STOPPED_WITHDRAWAL_COMMIT_UNESTABLISHED" if self._adapter._source_use_integrity_failed_v1 else
                        "STOPPED_WITHDRAWAL_NOT_COMMITTED")
            raise
        finally:
            with self._lock:
                if self._completion_pending is pending:
                    self._completion_pending = self._valid_completion = None

    def _commit_verified_action_v1(self, pending, proof, committed):
        from dataclasses import replace
        from .receipts import (_source_use_require_v1, SourceUseAttributedActionV1,
                              PublicDataSourceUseScopeV1, PublicDataSourceUseActionV1)

        pending_ref = pending.request_ref
        public = type(pending.proposal["scope"]) is PublicDataSourceUseScopeV1
        with self._lock:
            # Cryptographic success consumes the observed counter even when a
            # later protected-resource recheck fails outside this lock.
            if (self._counter != 0 or proof.counter != 0) and proof.counter <= self._counter:
                self.stop_v1()
                _source_use_require_v1(False)
            self._counter = proof.counter
            _source_use_require_v1(self._valid_completion is pending)
        public_root = None
        if public and pending.proposal["action"] == "OBSERVE_ONCE":
            from ...service.owner_source_use_windows import _public_scope_resources_v1
            from .sqlite_reference import _public_root_facts_v1

            # Reobserve outside A after authentication, before control commit.
            refreshed = _public_scope_resources_v1(self._root, pending.proposal["scope"])
            _source_use_require_v1(refreshed == pending.public_resources)
            _source_use_require_v1(pending.public_inputs is not None or not refreshed["native_qualified"])
            if pending.public_inputs is not None:
                public_root = _public_root_facts_v1(refreshed["storage_root"])
        with self._lock:
            _source_use_require_v1(self._valid_completion is pending)
            now, mono = self._live_v1()
            proof = replace(proof, verified_at_utc=now)
            _source_use_require_v1(mono < pending.deadline_monotonic_ns)
            head, originals_before = self._heads_v1()
            _source_use_require_v1(originals_before == pending.original_heads
                                   and (None if head is None else head.record_id) == pending.expected[0])
            proposal, action = pending.proposal, pending.proposal["action"]
            if public and action == "OBSERVE_ONCE":
                _source_use_require_v1(self._public_retained_inputs_v1(capture=proposal["capture"]) is pending.public_inputs)
                if pending.public_inputs is not None:
                    current_inputs = MappingProxyType(dict(pending.public_inputs[4],
                        source_pairs=self._public_source_pairs_v1(evaluated_at_utc=now),
                        qualified_source_bindings=pending.public_inputs[5],
                        storage_root=refreshed["storage_root"], process_epoch_id=self._process_ref,
                        monotonic_clock_id=self._clock_ref))
                    _validate_public_operational_input_view_v1(inputs=current_inputs, capture=proposal["capture"],
                        root=public_root, native_qualified=refreshed["native_qualified"], evaluated_at_ns=self._last_clock[0])
            _source_use_require_v1((head is None and self._selected_scope is None)
                or (head is not None and self._selected_scope == head.typed_payload.scope == proposal["scope"]))
            negative = action in {"WITHDRAW_USE", "INVALIDATE_REVIEW"}
            _source_use_require_v1(negative or now < pending.expires_at_utc)
            originals = () if pending.original is None else (self._spine_v1(pending.original, now, pending_ref),)
            resulting = list(pending.expected[1:])
            for row in originals:
                resulting[1 if row.typed_payload.subject_kind == "SOURCE_REVIEW" else 0] = row.record_id
            generation = 0 if head is None else head.typed_payload.generation_after
            arguments = (
                self._process_ref, 1 if head is None else head.sequence + 1, pending.expected[0], action,
                proposal["scope"], self._root.enrollment.owner_ref, self._root.enrollment.enrollment_ref,
                pending_ref, proof, generation, generation + (action != "OBSERVE_ONCE"),
                pending.expected[1], pending.expected[2], *resulting,
                None if action == "REVIEW_ACCEPT" or self._review is None else self._review.record_id,
                None if action in {"REVIEW_ACCEPT", "USE_ADMIT"} or self._use is None else self._use.record_id,
                tuple(row.record_id for row in originals), proposal.get("review_facts"),
                now, now if negative else pending.expires_at_utc,
                proposal.get("capture" if public else "observation"), proposal.get("reason"))
            payload = (PublicDataSourceUseActionV1("PUBLIC_SOURCE_USE_ACTION_V1", *arguments)
                       if public else SourceUseAttributedActionV1(*arguments))
            event = self._spine_v1(payload, now, pending_ref)
            verified = object.__new__(_VerifiedSourceUseActionV1)
            verified._authority, verified._root = self, self._root
            verified._pending, verified._proof, verified._attempted = pending, proof, False
            self._adapter._registered_batches[event.record_id] = MappingProxyType({
                "verified": verified, "scope": self._adapter._control_scope,
                "event": event, "originals": originals, "expected": pending.expected})
            try:
                result = self._uow.commit_source_use_action_v1(originals=originals, event=event,
                    expected_event_ref=pending.expected[0], expected_declaration_ref=pending.expected[1],
                    expected_review_ref=pending.expected[2], verified_action=verified)
                _source_use_require_v1(result.disposition == "APPENDED")
                committed[0] = True
                self._head = result.current_event
                self._selected_scope = proposal["scope"]
                if action != "OBSERVE_ONCE":
                    self._public_input_view = None
                    self._bindings.clear()
                    self._active_permit = None
                    self._use = None
                if action == "REVIEW_ACCEPT":
                    self._review = event
                elif action == "INVALIDATE_REVIEW":
                    self._review = None
                elif action == "USE_ADMIT":
                    self._use = event
                    self._last_use_event = event
                    if not public:
                        self._issue_binding_v1(None, mono)
                elif action == "OBSERVE_ONCE":
                    _source_use_require_v1(self._active_permit is None)
                    if public:
                        self._issue_public_binding_v1(self._head, mono, pending.public_resources, public_root)
                    else:
                        self._issue_binding_v1(event, mono)
                self._last_disposition = "APPENDED"
                return result
            except BaseException:
                self.stop_v1()
                raise

    def _issue_binding_v1(self, permit_event, mono):
        from .receipts import _source_use_require_v1

        _source_use_require_v1(self._review is not None and self._use is not None)
        scope, facts = self._selected_scope, self._review.typed_payload.review_facts
        source = PITSourceCurrentizationReceiptV1(
            "SOURCE_REVIEW::" + self._review.record_id, scope.profile_id, scope.source_id,
            scope.source_contract_version, facts.factual_checked_at_utc, facts.source_effective_at_utc,
            facts.source_expires_at_utc, self._root.enrollment.owner_ref, facts.recheck_triggers, False, True)
        rights = PITRightsAdmissionReceiptV1(
            "SOURCE_USE::" + self._use.record_id, scope.profile_id, scope.account_scope_ref, scope.source_id,
            facts.agreement_id, facts.agreement_version, scope.internal_use_class, "ADMITTED_INTERNAL_USE",
            self._use.recorded_at, self._use.typed_payload.expires_at_utc, facts.recheck_triggers, False,
            scope.permitted_retention_class, scope.prohibited_redistribution_class)
        validate_pit_source_rights_admission_v1(source, rights, admission_id=self._use.record_id,
            profile_id=scope.profile_id, account_scope=scope.account_scope_ref,
            internal_use_class=scope.internal_use_class, permitted_retention_class=scope.permitted_retention_class,
            evaluated_at_utc=self._head.recorded_at)
        binding = object.__new__(KalshiSourceUseBindingV1)
        binding._authority, binding._root = self, self._root
        binding._generation = self._head.typed_payload.generation_after
        binding._declaration_ref, binding._review_ref = self._head.typed_payload.declaration_ref, self._head.typed_payload.review_ref
        binding._review_event_ref, binding._use_event_ref = self._review.record_id, self._use.record_id
        binding._source, binding._rights, binding._permit = source, rights, None
        if permit_event is not None:
            permit = object.__new__(_SourceUseObservationPermitV1)
            permit._event, permit._request = permit_event, permit_event.typed_payload.observation
            remaining = permit._request.expires_at_utc - permit_event.recorded_at
            remaining_ns = (remaining.days * 86400 + remaining.seconds) * 1_000_000_000 + remaining.microseconds * 1000
            permit._deadline = min(self._deadline, mono + permit._request.maximum_duration_ns, mono + remaining_ns)
            _source_use_require_v1(mono < permit._deadline <= 2**63 - 1)
            permit._owner = permit._route = None
            permit._published = permit._failed = False
            permit._started = 0
            binding._permit = permit
            self._active_permit = permit
            self._last_operating_permit = permit
        self._bindings[id(binding)] = binding
        return binding

    def _issue_public_binding_v1(self, event, mono, resources, root_facts):
        import os
        import threading
        from .context import _native_utc_nanoseconds
        from .receipts import PublicDataSourceUseActionV1, _source_use_require_v1, _public_identity_v1

        _source_use_require_v1(type(event.typed_payload) is PublicDataSourceUseActionV1
            and event is self._head and event.typed_payload.action == "OBSERVE_ONCE"
            and self._review is not None and self._use is not None and resources is not None)
        capture, scope = event.typed_payload.capture, self._selected_scope
        now, mono = self._live_v1()
        pairs = self._public_source_pairs_v1(evaluated_at_utc=now)
        remaining = capture.operating_expires_at_ns - self._last_clock[0]
        deadline = min(self._deadline, scope.budget.deadline_monotonic_ns,
                       mono + scope.budget.duration_ns, mono + remaining)
        _source_use_require_v1(remaining > 0 and mono < deadline <= 2**63 - 1
            and scope.scope_generation == event.typed_payload.generation_after
            and capture.operating_expires_at_ns <= min(resources["expires_at_ns"],
                _native_utc_nanoseconds(self._use.typed_payload.expires_at_utc.isoformat()),
                _native_utc_nanoseconds(self._review.typed_payload.expires_at_utc.isoformat())))
        binding = object.__new__(PublicSourceUseBindingV1)
        binding._authority, binding._root, binding._resources = self, self._root, resources
        binding._generation, binding._event, binding._capture = scope.scope_generation, event, capture
        binding._process_id, binding._thread_id = os.getpid(), threading.get_ident()
        binding._deadline, binding._failed, binding._owner, binding._started = deadline, False, None, False
        binding._native_qualified = resources["native_qualified"]
        binding._publication_lock = threading.RLock()
        binding._control_records = tuple(self._adapter._tables["receipt_records"].values())
        retained = self._public_retained_inputs_v1(capture=capture)
        binding._input_view = retained
        _source_use_require_v1(retained is not None or not resources["native_qualified"])
        binding._source_inputs = MappingProxyType(dict({} if retained is None else retained[4], source_pairs=pairs,
            qualified_source_bindings=() if retained is None else retained[5],
            storage_root=resources["storage_root"], process_epoch_id=self._process_ref,
            monotonic_clock_id=self._clock_ref))
        if retained is not None:
            _validate_public_operational_input_view_v1(inputs=binding._source_inputs, capture=capture,
                root=root_facts, native_qualified=resources["native_qualified"], evaluated_at_ns=self._last_clock[0])
        self._public_configuration = resources["configuration"]
        self._bindings[id(binding)] = binding
        _PUBLIC_BINDINGS_V1[id(binding)] = binding
        self._active_permit = self._last_operating_permit = binding
        self._check_public_binding_v1(binding)
        return binding

    def _check_public_binding_v1(self, binding):
        import os
        import threading
        from .receipts import _source_use_require_v1
        from ...service.owner_source_use_windows import _public_resources_resident_v1

        now, mono = self._live_v1()
        _source_use_require_v1(type(binding) is PublicSourceUseBindingV1
            and self._bindings.get(id(binding)) is binding and _PUBLIC_BINDINGS_V1.get(id(binding)) is binding
            and binding._authority is self and binding._root is self._root
            and binding._process_id == os.getpid() and binding._thread_id == threading.get_ident()
            and binding is self._active_permit and not binding._failed
            and self._review is not None and self._use is not None and self._head is binding._event
            and self._head.typed_payload.scope == self._selected_scope == binding._capture.scope
            and self._head.typed_payload.generation_after == binding._generation
            and self._head.typed_payload.review_event_ref == self._review.record_id
            and self._head.typed_payload.use_event_ref == self._use.record_id
            and now < self._review.typed_payload.expires_at_utc and now < self._use.typed_payload.expires_at_utc
            and self._last_clock[0] < min(binding._capture.operating_expires_at_ns,
                binding._capture.scope.retention_expires_at_ns)
            and mono < binding._deadline and self._public_configuration is binding._resources["configuration"])
        _public_resources_resident_v1(self._root, binding._resources, self._last_clock[0])
        if binding._native_qualified:
            _source_use_require_v1(self._public_input_view is binding._input_view and binding._input_view is not None
                and binding._source_inputs["qualified_source_bindings"] is binding._input_view[5]
                and all(binding._source_inputs[name] is value for name,value in binding._input_view[4].items()))
        for source, rights in binding._source_inputs["source_pairs"]:
            validate_pit_source_rights_admission_v1(source, rights, admission_id=self._use.record_id,
                profile_id=self._selected_scope.profile_id, account_scope=rights.account_scope,
                internal_use_class=self._selected_scope.internal_use_class,
                permitted_retention_class=self._selected_scope.permitted_retention_class, evaluated_at_utc=now)
        return now, mono

    def _check_binding_v1(self, binding, owner=None, *, inputs=None, allow_published=False):
        from .receipts import _source_use_require_v1

        now, mono = self._live_v1()
        _source_use_require_v1(type(binding) is KalshiSourceUseBindingV1
                               and self._bindings.get(id(binding)) is binding
                               and binding._authority is self and binding._root is self._root)
        head, originals = self._heads_v1()
        _source_use_require_v1(head is not None and self._review is not None and self._use is not None
                               and head.typed_payload.generation_after == binding._generation
                               and (head.typed_payload.declaration_ref, head.typed_payload.review_ref)
                               == (binding._declaration_ref, binding._review_ref)
                               and self._review.record_id == binding._review_event_ref
                               and self._use.record_id == binding._use_event_ref
                               and self._review.typed_payload.review_ref == binding._review_ref
                               and all(row is not None and row.typed_payload.content is not None for row in originals))
        scope = self._selected_scope
        _source_use_require_v1(head.typed_payload.scope == scope
                               and binding._rights.prohibited_redistribution_class == scope.prohibited_redistribution_class)
        _kalshi_observation_time(now < self._review.typed_payload.expires_at_utc
                                 and now < self._use.typed_payload.expires_at_utc)
        validate_pit_source_rights_admission_v1(binding._source, binding._rights, admission_id=self._use.record_id,
            profile_id=scope.profile_id, account_scope=scope.account_scope_ref,
            internal_use_class=scope.internal_use_class, permitted_retention_class=scope.permitted_retention_class,
            evaluated_at_utc=now)
        permit = binding._permit
        if owner is not None or inputs is not None:
            _source_use_require_v1(type(permit) is _SourceUseObservationPermitV1
                                   and (permit is self._active_permit or (allow_published and permit._published)) and not permit._failed
                                   and (allow_published or not permit._published))
            _kalshi_observation_time(now < permit._event.typed_payload.expires_at_utc
                                     and now < permit._request.expires_at_utc and mono < permit._deadline)
            if owner is not None:
                _source_use_require_v1(permit._owner is owner)
            if inputs is not None:
                _source_use_require_v1(type(inputs) is tuple and inputs == (permit._request.fills,
                    permit._request.balance_increment, permit._request.prior_rounding_overpayment))
        return now, mono

    def _claim_owner_v1(self, binding, owner, supplied):
        from .receipts import _source_use_require_v1

        with self._lock:
            self._check_binding_v1(binding, inputs=(binding._permit._request.fills,
                binding._permit._request.balance_increment, binding._permit._request.prior_rounding_overpayment))
            permit = binding._permit
            _source_use_require_v1(permit._owner is None)
            permit._owner = owner  # Failure after this line consumes this owner claim.
            expected = (binding._source, binding._rights, self._selected_scope.account_scope_ref,
                self._selected_scope.internal_use_class, self._selected_scope.permitted_retention_class,
                permit._request.market_ticker, self._process_ref, self._clock_ref, permit._event.record_id,
                permit._event.typed_payload.expires_at_utc, permit._deadline)
            _source_use_require_v1(supplied[0] is binding._source and supplied[1] is binding._rights and supplied == expected)


class AtomicFactTerminalStateV1(StrEnum):
    PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE = (
        "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
    )


class ClaimBindingTerminalStateV1(StrEnum):
    COMPLETE_TERMINAL_EXACT_CLAIM_BINDING = (
        "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING"
    )


class PrimarySourceCompletenessV1(StrEnum):
    COMPLETE_PRIMARY_SOURCE = "COMPLETE_PRIMARY_SOURCE"


@dataclass(frozen=True, slots=True)
class AtomicSourceFactV1:
    atomic_fact_id: str
    fact: str
    result: AtomicFactTerminalStateV1

    def __post_init__(self) -> None:
        if (
            not isinstance(self.atomic_fact_id, str)
            or not self.atomic_fact_id
            or not isinstance(self.fact, str)
            or not self.fact
            or not isinstance(self.result, AtomicFactTerminalStateV1)
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "atomic source facts require the exact typed terminal result",
            )


@dataclass(frozen=True, slots=True)
class SourceStateV1:
    source_state_id: str
    source_audit_row_id: str
    stable_source_identity: str
    subject_id: str
    publisher: str
    source_title: str
    source_url: str
    epoch: str
    effective_from: str | None
    effective_to_or_open: str
    source_currentization_owner: str
    source_precedence: str
    availability_state: str
    conflict_resolution_state: str
    future_fact_exclusion_state: str
    rights_and_use_state: str
    permitted_use_class: str
    source_class: str
    ttl: str
    exact_claims: tuple[str, ...]
    atomic_facts: tuple[AtomicSourceFactV1, ...]
    implementation_binding: tuple[str, ...]
    failure_reason_code: str
    recheck_triggers: tuple[str, ...]
    research_completeness_state: ClaimBindingTerminalStateV1
    primary_source_completeness_state: PrimarySourceCompletenessV1
    provider_connection_or_effect_authorized: bool
    runtime_online_research_allowed: bool
    codex_online_research_allowed: bool
    original_row_json: str

    def __post_init__(self) -> None:
        required_names = (
            "source_state_id",
            "source_audit_row_id",
            "stable_source_identity",
            "subject_id",
            "publisher",
            "source_title",
            "source_url",
            "epoch",
            "effective_to_or_open",
            "source_currentization_owner",
            "source_precedence",
            "availability_state",
            "conflict_resolution_state",
            "future_fact_exclusion_state",
            "rights_and_use_state",
            "permitted_use_class",
            "source_class",
            "ttl",
            "failure_reason_code",
            "original_row_json",
        )
        if any(
            not isinstance(getattr(self, name), str)
            or not getattr(self, name)
            for name in required_names
        ) or not self.atomic_facts:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                f"incomplete source state: {self.source_state_id}",
            )
        if self.effective_from is not None and (
            not isinstance(self.effective_from, str) or not self.effective_from
        ):
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT,
                "effective_from must be nonempty text when declared",
            )
        for name in (
            "provider_connection_or_effect_authorized",
            "runtime_online_research_allowed",
            "codex_online_research_allowed",
        ):
            if type(getattr(self, name)) is not bool:
                raise SourcePolicyError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a boolean",
                )
        if not isinstance(self.atomic_facts, tuple) or any(
            not isinstance(fact, AtomicSourceFactV1)
            for fact in self.atomic_facts
        ):
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT,
                "atomic source facts must be typed immutable rows",
            )
        for name in (
            "exact_claims",
            "implementation_binding",
            "recheck_triggers",
        ):
            values = getattr(self, name)
            if not isinstance(values, tuple) or any(
                not isinstance(value, str) or not value for value in values
            ):
                raise SourcePolicyError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be an immutable string tuple",
                )
            if len(values) != len(set(values)):
                raise SourcePolicyError(
                    ReasonCode.SOURCE_CONFLICT,
                    f"{name} contains duplicate source metadata",
                )
        if (
            self.provider_connection_or_effect_authorized
            or self.runtime_online_research_allowed
            or self.codex_online_research_allowed
        ):
            raise SourcePolicyError(
                ReasonCode.CAPABILITY_DENIED,
                f"source state exercises unauthorized effects: {self.source_state_id}",
            )
        if (
            not isinstance(
                self.research_completeness_state,
                ClaimBindingTerminalStateV1,
            )
            or not isinstance(
                self.primary_source_completeness_state,
                PrimarySourceCompletenessV1,
            )
            or self.conflict_resolution_state
            != "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE"
            or self.future_fact_exclusion_state
            != "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED"
            or self.rights_and_use_state
            != (
                "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_"
                "OR_REPUBLICATION_RIGHT_INFERRED"
            )
            or self.permitted_use_class
            != (
                "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_"
                "TEST_METADATA_ONLY"
            )
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_CONFLICT,
                f"source row is not terminally bound: {self.source_state_id}",
            )
        try:
            original_row = json.loads(self.original_row_json)
        except json.JSONDecodeError as exc:
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT,
                "source original-row metadata is not valid JSON",
            ) from exc
        if not isinstance(original_row, dict):
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT,
                "source original-row metadata must be an object",
            )
        if len({fact.atomic_fact_id for fact in self.atomic_facts}) != len(
            self.atomic_facts
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_CONFLICT,
                f"duplicate atomic fact id in {self.source_state_id}",
            )
        if any(
            fact.result
            is not AtomicFactTerminalStateV1.PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE
            for fact in self.atomic_facts
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_CONFLICT,
                f"non-passing atomic fact in {self.source_state_id}",
            )


@dataclass(frozen=True, slots=True)
class SourceCurrentizationOverlayV1:
    currentization_id: str
    subject: str
    source_class: str
    source_url: str
    retrieved_at_utc: str
    implementation_rule: str
    exact_facts_json: str
    supersedes_package_addendum_fields: tuple[str, ...]
    runtime_effect_authorized: bool
    original_row_json: str

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str) or not value
            for value in (
                self.currentization_id,
                self.subject,
                self.implementation_rule,
            )
        ):
            raise SourcePolicyError(
                ReasonCode.INCOMPLETE_CONTRACT, "source overlay is incomplete"
            )
        for name in (
            "source_class",
            "source_url",
            "retrieved_at_utc",
            "exact_facts_json",
            "original_row_json",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ):
                raise SourcePolicyError(
                    ReasonCode.INVALID_CONTRACT,
                    f"overlay {name} must be nonempty text",
                )
        if type(self.runtime_effect_authorized) is not bool:
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT,
                "overlay runtime authority must be a boolean",
            )
        if not isinstance(self.supersedes_package_addendum_fields, tuple) or any(
            not isinstance(value, str) or not value
            for value in self.supersedes_package_addendum_fields
        ):
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT,
                "overlay supersession fields must be an immutable string tuple",
            )
        try:
            exact_facts = json.loads(self.exact_facts_json)
        except json.JSONDecodeError as exc:
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT,
                "overlay exact facts are not valid JSON",
            ) from exc
        if not isinstance(exact_facts, dict) or not exact_facts:
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT,
                "overlay exact facts must be a nonempty object",
            )
        try:
            original_row = json.loads(self.original_row_json)
        except json.JSONDecodeError as exc:
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT,
                "overlay original-row metadata is not valid JSON",
            ) from exc
        if not isinstance(original_row, dict):
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT,
                "overlay original-row metadata must be an object",
            )
        if self.runtime_effect_authorized:
            raise SourcePolicyError(
                ReasonCode.CAPABILITY_DENIED,
                "source overlays cannot authorize runtime effects",
            )


class TradeLifecycleClass(StrEnum):
    PENDING = "PENDING"
    TERMINAL_SUCCESS = "TERMINAL_SUCCESS"
    TERMINAL_FAILURE = "TERMINAL_FAILURE"


@dataclass(frozen=True, slots=True)
class EndpointWindowLimitV1:
    method_and_path: str
    burst_requests: int
    burst_window_seconds: int
    sustained_requests: int
    sustained_window_seconds: int
    scope: str = "CLOUDFLARE_IP"

    def __post_init__(self) -> None:
        if (
            not isinstance(self.method_and_path, str)
            or not self.method_and_path
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
                for value in (
                    self.burst_requests,
                    self.burst_window_seconds,
                    self.sustained_requests,
                    self.sustained_window_seconds,
                )
            )
            or self.scope != "CLOUDFLARE_IP"
        ):
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT, "invalid endpoint-window limit"
            )


@dataclass(frozen=True, slots=True)
class SignerTokenBucketV1:
    operation_class: str
    rate_tokens_per_second: int
    burst_tokens: int
    warning_header: str
    warning_mode_begins: str
    warning_mode_duration: str
    scope: str = "SIGNER"

    def __post_init__(self) -> None:
        if (
            not isinstance(self.operation_class, str)
            or not self.operation_class
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
                for value in (
                    self.rate_tokens_per_second,
                    self.burst_tokens,
                )
            )
            or self.warning_header != "Poly-RateLimit-Warning: true"
            or self.warning_mode_begins != "2026-07-24"
            or self.warning_mode_duration
            != "two weeks; live enforcement date to be announced"
            or self.scope != "SIGNER"
        ):
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT,
                "invalid signer-scoped token-bucket currentization",
            )


@dataclass(frozen=True, slots=True)
class FAKFOKResponseContractV1:
    effective_at_utc: str
    successful_response_field: str = "tradeIDs"
    custom_rest_followup: str = (
        "poll existing trades by tradeID until hash is available or status is FAILED"
    )
    inline_transaction_hashes_expected: bool = False
    accepted_order_resubmission_allowed: bool = False
    runtime_execution_allowed: bool = False

    def __post_init__(self) -> None:
        if (
            self.effective_at_utc != "2026-07-24T04:00:00Z"
            or self.successful_response_field != "tradeIDs"
            or self.custom_rest_followup
            != (
                "poll existing trades by tradeID until hash is available "
                "or status is FAILED"
            )
            or any(
                type(value) is not bool
                for value in (
                    self.inline_transaction_hashes_expected,
                    self.accepted_order_resubmission_allowed,
                    self.runtime_execution_allowed,
                )
            )
            or self.inline_transaction_hashes_expected
            or self.accepted_order_resubmission_allowed
            or self.runtime_execution_allowed
        ):
            raise SourcePolicyError(
                ReasonCode.CAPABILITY_DENIED,
                "FAK/FOK contract violates the current no-execution binding",
            )

    def successful_field_at(self, as_of: datetime) -> str:
        if not isinstance(as_of, datetime) or as_of.tzinfo is None:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "FAK/FOK response evaluation requires an aware timestamp",
            )
        effective = datetime.fromisoformat(
            self.effective_at_utc.replace("Z", "+00:00")
        ).astimezone(UTC)
        if as_of.astimezone(UTC) < effective:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_STALE,
                "tradeIDs binding is not effective at the requested instant",
            )
        return self.successful_response_field


@dataclass(frozen=True, slots=True)
class SourceRevalidationPolicyViewV1:
    owner_id: str
    source_path: str
    live_critical_interval: str
    low_risk_interval: str
    event_triggered_latency_class: str
    live_critical_field_classes: tuple[str, ...]
    low_risk_field_classes: tuple[str, ...]
    platform_scopes: tuple[str, ...]
    network_retrieval_allowed: bool = False
    source_truth_acceptance_allowed: bool = False

    def __post_init__(self) -> None:
        required = (
            self.owner_id,
            self.source_path,
            self.live_critical_interval,
            self.low_risk_interval,
            self.event_triggered_latency_class,
        )
        if any(not isinstance(value, str) or not value for value in required):
            raise SourcePolicyError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "source scheduler lineage is incomplete",
            )
        for name in (
            "live_critical_field_classes",
            "low_risk_field_classes",
            "platform_scopes",
        ):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or any(not isinstance(value, str) or not value for value in values)
                or len(set(values)) != len(values)
            ):
                raise SourcePolicyError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    f"source scheduler {name} is malformed",
                )
        if set(self.live_critical_field_classes) & set(
            self.low_risk_field_classes
        ):
            raise SourcePolicyError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "source scheduler field classes overlap",
            )
        if (
            type(self.network_retrieval_allowed) is not bool
            or type(self.source_truth_acceptance_allowed) is not bool
            or self.network_retrieval_allowed
            or self.source_truth_acceptance_allowed
        ):
            raise SourcePolicyError(
                ReasonCode.CAPABILITY_DENIED,
                "source scheduler view cannot retrieve or accept source truth",
            )
        from .serialization import validate_relative_path

        validate_relative_path(self.source_path)


class SourceRevalidationSchedulerAdapterV1:
    """Explicit immutable policy view; it never invokes scheduler execution."""

    @staticmethod
    def load_view() -> SourceRevalidationPolicyViewV1:
        from src.qtt.source_evidence.revalidation.scheduler import (
            EVENT_TRIGGERED_REVALIDATION_LATENCY_CLASS,
            LIVE_CRITICAL_REVALIDATION_INTERVAL,
            LIVE_CRITICAL_SOURCE_FIELD_CLASSES,
            LOW_RISK_REVALIDATION_INTERVAL,
            LOW_RISK_SOURCE_FIELD_CLASSES,
            STAGE1_PLATFORM_SCOPES,
        )

        return SourceRevalidationPolicyViewV1(
            owner_id="SOURCE_REVALIDATION_SCHEDULER",
            source_path="src/qtt/source_evidence/revalidation/scheduler.py",
            live_critical_interval=LIVE_CRITICAL_REVALIDATION_INTERVAL,
            low_risk_interval=LOW_RISK_REVALIDATION_INTERVAL,
            event_triggered_latency_class=(
                EVENT_TRIGGERED_REVALIDATION_LATENCY_CLASS
            ),
            live_critical_field_classes=tuple(
                LIVE_CRITICAL_SOURCE_FIELD_CLASSES
            ),
            low_risk_field_classes=tuple(LOW_RISK_SOURCE_FIELD_CLASSES),
            platform_scopes=tuple(STAGE1_PLATFORM_SCOPES),
        )


_CERTIFIED_SOURCE_ROWS_JSON = r'''
[
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::01::epoch2::01",
        "fact": "GET /historical/cutoff is the dynamic routing authority for markets/candlesticks, trades/fills, completed orders, and archived settled positions.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::01::epoch2::02",
        "fact": "Records older than the applicable cutoff must use historical endpoints; the target live window is approximately three months and advances.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::01::epoch2::03",
        "fact": "Historical public trades are a trade tape and do not establish historical L2, order identity, or native queue priority.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::01::epoch2::04",
        "fact": "GET /historical/positions serves user-scoped settled positions older than market_positions_last_updated_ts; positions move per whole event, while unsettled positions remain on the live endpoint.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Kalshi",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::01",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::01",
    "source_title": "Kalshi — Historical Data",
    "source_url": "https://docs.kalshi.com/getting_started/historical_data",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface KALSHI_LIVE_AND_HISTORICAL_REST_ROUTING to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-KALSHI-HISTORICAL-DATA",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::01",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::01",
  "stable_source_identity": "VENUE::ST10-SOURCE_01::KALSHI_HISTORICAL_DATA",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "GET /historical/cutoff is the dynamic routing authority for markets/candlesticks, trades/fills, completed orders, and archived settled positions.",
      "Records older than the applicable cutoff must use historical endpoints; the target live window is approximately three months and advances.",
      "Historical public trades are a trade tape and do not establish historical L2, order identity, or native queue priority.",
      "GET /historical/positions serves user-scoped settled positions older than market_positions_last_updated_ts; positions move per whole event, while unsettled positions remain on the live endpoint."
    ],
    "failure_reason_code": "ST12_SOURCE_01_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface KALSHI_LIVE_AND_HISTORICAL_REST_ROUTING to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P1D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-KALSHI-HISTORICAL-DATA"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::02::epoch2::01",
        "fact": "GET /markets/{ticker}/orderbook is public and returns current aggregated YES and NO bid ladders.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::02::epoch2::02",
        "fact": "Prices and quantities are fixed-point decimal strings; complementary asks are reconstructed from opposite-outcome bids.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::02::epoch2::03",
        "fact": "The current aggregate book does not establish historical L2 or native order identity.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Kalshi",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::02",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::02",
    "source_title": "Kalshi — Orderbook Responses",
    "source_url": "https://docs.kalshi.com/getting_started/orderbook_responses",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface KALSHI_CURRENT_PUBLIC_REST_AGGREGATE_ORDERBOOK to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-KALSHI-ORDERBOOK",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::02",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::02",
  "stable_source_identity": "VENUE::ST10-SOURCE_02::KALSHI_ORDERBOOK_RESPONSES",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "GET /markets/{ticker}/orderbook is public and returns current aggregated YES and NO bid ladders.",
      "Prices and quantities are fixed-point decimal strings; complementary asks are reconstructed from opposite-outcome bids.",
      "The current aggregate book does not establish historical L2 or native order identity."
    ],
    "failure_reason_code": "ST12_SOURCE_02_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface KALSHI_CURRENT_PUBLIC_REST_AGGREGATE_ORDERBOOK to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P7D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-KALSHI-ORDERBOOK"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::03::epoch2::01",
        "fact": "The channel requires authentication, emits an orderbook_snapshot first, then incremental orderbook_delta messages.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::03::epoch2::02",
        "fact": "Messages carry subscription and sequence fields plus timestamps on deltas.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::03::epoch2::03",
        "fact": "The stream is aggregated by price level and does not expose full native order identity.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::03::epoch2::04",
        "fact": "Subaccount-restricted session and private-channel scoping is versioned through the July 23 changelog and must be joined as a separate effective source binding rather than inferred from this channel page.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Kalshi",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::03",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::03",
    "source_title": "Kalshi — WebSocket Orderbook Updates",
    "source_url": "https://docs.kalshi.com/websockets/orderbook-updates",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface KALSHI_AUTHENTICATED_WSS_AGGREGATE_L2 to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-KALSHI-WSS-ORDERBOOK",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::03",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::03",
  "stable_source_identity": "VENUE::ST10-SOURCE_03::KALSHI_WEBSOCKET_ORDERBOOK_UPDATES",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "The channel requires authentication, emits an orderbook_snapshot first, then incremental orderbook_delta messages.",
      "Messages carry subscription and sequence fields plus timestamps on deltas.",
      "The stream is aggregated by price level and does not expose full native order identity.",
      "Subaccount-restricted session and private-channel scoping is versioned through the July 23 changelog and must be joined as a separate effective source binding rather than inferred from this channel page."
    ],
    "failure_reason_code": "ST12_SOURCE_03_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface KALSHI_AUTHENTICATED_WSS_AGGREGATE_L2 to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P7D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-KALSHI-WSS-ORDERBOOK"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::04::epoch2::01",
        "fact": "Direct member balance precision is 0.0001 USD; non-direct member balance precision is 0.01 USD.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::04::epoch2::02",
        "fact": "Trade fee is rounded up to the nearest 0.0001 USD; balance change is floored to target precision.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::04::epoch2::03",
        "fact": "A per-order accumulator issues whole-cent rebates when accumulated rounding overpayment exceeds 0.01 USD.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Kalshi",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::04",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::04",
    "source_title": "Kalshi — Fee Rounding",
    "source_url": "https://docs.kalshi.com/getting_started/fee_rounding",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface KALSHI_BALANCE_AND_FEE_ROUNDING to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-KALSHI-FEE-ROUNDING",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::04",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::04",
  "stable_source_identity": "VENUE::ST10-SOURCE_04::KALSHI_FEE_ROUNDING",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "Direct member balance precision is 0.0001 USD; non-direct member balance precision is 0.01 USD.",
      "Trade fee is rounded up to the nearest 0.0001 USD; balance change is floored to target precision.",
      "A per-order accumulator issues whole-cent rebates when accumulated rounding overpayment exceeds 0.01 USD."
    ],
    "failure_reason_code": "ST12_SOURCE_04_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface KALSHI_BALANCE_AND_FEE_ROUNDING to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P1D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-KALSHI-FEE-ROUNDING"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::05::epoch2::01",
        "fact": "Series fee changes are retrieved from the official exchange endpoint and must be bound by series and effective time.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::05::epoch2::02",
        "fact": "Historical replay uses the fee regime effective at simulated time rather than the current regime by default.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Kalshi",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::05",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::05",
    "source_title": "Kalshi — Series Fee Changes",
    "source_url": "https://docs.kalshi.com/api-reference/exchange/get-series-fee-changes",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface KALSHI_SERIES_EFFECTIVE_FEE_EPOCHS to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-KALSHI-FEE-EPOCHS",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::05",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::05",
  "stable_source_identity": "VENUE::ST10-SOURCE_05::KALSHI_SERIES_FEE_CHANGES",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "Series fee changes are retrieved from the official exchange endpoint and must be bound by series and effective time.",
      "Historical replay uses the fee regime effective at simulated time rather than the current regime by default."
    ],
    "failure_reason_code": "ST12_SOURCE_05_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface KALSHI_SERIES_EFFECTIVE_FEE_EPOCHS to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P1D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-KALSHI-FEE-EPOCHS"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::06::epoch2::01",
        "fact": "The July 9, 2026 changelog removes deprecated response_price_units, fractional_trading_enabled, and resting_orders_count fields; fixed-point and price-range replacements remain canonical.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::06::epoch2::02",
        "fact": "As of July 22, 2026, GET /incentive_programs excludes incentive programs whose market belongs to a hidden event.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::06::epoch2::03",
        "fact": "As of July 23, 2026, attempts to create an order group after the 25,000-group limit are rejected; existing groups above the limit are cancelled before the change window.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::06::epoch2::04",
        "fact": "As of July 23, 2026, GET /historical/positions and market_positions_last_updated_ts are active for event-whole archived settled positions.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::06::epoch2::05",
        "fact": "As of July 23, 2026, subaccount-restricted API keys may open WebSocket sessions; private channels are scoped to the locked subaccount while orderbook_delta still delivers the full book with sibling own-order annotations withheld.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::06::epoch2::06",
        "fact": "As of July 23, 2026, a subaccount-restricted key may use an RfqMode FIX session for Quote, QuoteConfirm, and QuoteCancel on its subaccount; RFQ creation and AcceptQuote remain unavailable.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::06::epoch2::07",
        "fact": "As of July 23, 2026, authenticated WebSocket clients may subscribe to the pyth_value channel for deduplicated Pyth prices by underlying ticker.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::06::epoch2::08",
        "fact": "Seven additional price_level_structure labels are declared on July 23, but price_ranges remains the per-market source of truth and consumers must not hardcode behavior from the label.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::06::epoch2::09",
        "fact": "Pilot adoption of the new price structures during the week of July 27 and broader rollout during the week of August 3 remain future effective relative to this July 23 audit and are excluded until revalidated.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_WITH_LATER_ROLLOUT_EPOCHS_EXCLUDED",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": "2026-07-23",
    "effective_time_precision": "PER_CHANGELOG_ENTRY_DATE; NO SINGLE GLOBAL EFFECTIVE INSTANT",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_epoch_exclusion": "JULY_27_2026_AND_AUGUST_3_2026_PRICE_STRUCTURE_ROLLOUTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Kalshi",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::06",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::06",
    "source_title": "Kalshi — API changelog through July 23, 2026",
    "source_url": "https://docs.kalshi.com/changelog",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface KALSHI_SCHEMA_AND_ENDPOINT_EPOCHS to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-KALSHI-CHANGELOG",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::06",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::06",
  "stable_source_identity": "VENUE::ST10-SOURCE_06::KALSHI_API_CHANGELOG_THROUGH_JULY_23_2026",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "EFFECTIVE_EPOCH_GUARD_RECONFIRMED",
    "implementation_binding_addition": "Future-dated rollout entries remain inactive until their effective date and a fresh source-owner recheck; never activate early.",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "The July 9, 2026 changelog removes deprecated response_price_units, fractional_trading_enabled, and resting_orders_count fields; fixed-point and price-range replacements remain canonical.",
      "As of July 22, 2026, GET /incentive_programs excludes incentive programs whose market belongs to a hidden event.",
      "As of July 23, 2026, attempts to create an order group after the 25,000-group limit are rejected; existing groups above the limit are cancelled before the change window.",
      "As of July 23, 2026, GET /historical/positions and market_positions_last_updated_ts are active for event-whole archived settled positions.",
      "As of July 23, 2026, subaccount-restricted API keys may open WebSocket sessions; private channels are scoped to the locked subaccount while orderbook_delta still delivers the full book with sibling own-order annotations withheld.",
      "As of July 23, 2026, a subaccount-restricted key may use an RfqMode FIX session for Quote, QuoteConfirm, and QuoteCancel on its subaccount; RFQ creation and AcceptQuote remain unavailable.",
      "As of July 23, 2026, authenticated WebSocket clients may subscribe to the pyth_value channel for deduplicated Pyth prices by underlying ticker.",
      "Seven additional price_level_structure labels are declared on July 23, but price_ranges remains the per-market source of truth and consumers must not hardcode behavior from the label.",
      "Pilot adoption of the new price structures during the week of July 27 and broader rollout during the week of August 3 remain future effective relative to this July 23 audit and are excluded until revalidated."
    ],
    "failure_reason_code": "ST12_SOURCE_06_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface KALSHI_SCHEMA_AND_ENDPOINT_EPOCHS to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P1D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-KALSHI-CHANGELOG"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::07::epoch2::01",
        "fact": "The current token book exposes bids, asks, timestamp, hash, tick size, minimum order size, negative-risk state, and last-trade price.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::07::epoch2::02",
        "fact": "A current book does not establish historical order-event identity or queue priority.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Polymarket Global",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::07",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::07",
    "source_title": "Polymarket Global — Get Order Book",
    "source_url": "https://docs.polymarket.com/api-reference/market-data/get-order-book",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface POLYMARKET_GLOBAL_CURRENT_TOKEN_ORDERBOOK to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-POLYGLOBAL-ORDERBOOK",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::07",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::07",
  "stable_source_identity": "VENUE::ST10-SOURCE_07::POLYMARKET_GLOBAL_GET_ORDER_BOOK",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "The current token book exposes bids, asks, timestamp, hash, tick size, minimum order size, negative-risk state, and last-trade price.",
      "A current book does not establish historical order-event identity or queue priority."
    ],
    "failure_reason_code": "ST12_SOURCE_07_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface POLYMARKET_GLOBAL_CURRENT_TOKEN_ORDERBOOK to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P7D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-POLYGLOBAL-ORDERBOOK"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::08::epoch2::01",
        "fact": "The endpoint returns token time/price points under interval/fidelity controls.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::08::epoch2::02",
        "fact": "Price history contains neither historical L2 depth nor native order identity or queue priority.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Polymarket Global",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::08",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::08",
    "source_title": "Polymarket Global — Get Prices History",
    "source_url": "https://docs.polymarket.com/api-reference/markets/get-prices-history",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface POLYMARKET_GLOBAL_TOKEN_TIME_PRICE_HISTORY to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-POLYGLOBAL-PRICE-HISTORY",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::08",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::08",
  "stable_source_identity": "VENUE::ST10-SOURCE_08::POLYMARKET_GLOBAL_GET_PRICES_HISTORY",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "The endpoint returns token time/price points under interval/fidelity controls.",
      "Price history contains neither historical L2 depth nor native order identity or queue priority."
    ],
    "failure_reason_code": "ST12_SOURCE_08_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface POLYMARKET_GLOBAL_TOKEN_TIME_PRICE_HISTORY to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P7D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-POLYGLOBAL-PRICE-HISTORY"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::09::epoch2::01",
        "fact": "The public market channel exposes book, price_change, tick_size_change, last_trade_price and optional BBO/lifecycle events.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::09::epoch2::02",
        "fact": "Events include timestamps and hashes, but the documentation does not establish a market-wide sequence-number gap contract.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::09::epoch2::03",
        "fact": "The surface supports current aggregate L2 and bounded fill proxies, not exact native queue-ahead proof.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Polymarket Global",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::09",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::09",
    "source_title": "Polymarket Global — WebSocket Market Channel",
    "source_url": "https://docs.polymarket.com/market-data/websocket/market-channel",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface POLYMARKET_GLOBAL_PUBLIC_CLOB_MARKET_WEBSOCKET to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-POLYGLOBAL-WSS-MARKET",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::09",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::09",
  "stable_source_identity": "VENUE::ST10-SOURCE_09::POLYMARKET_GLOBAL_WEBSOCKET_MARKET_CHANNEL",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "DOCUMENTATION_ROUTE_AND_EVENT_SURFACE_CURRENTIZATION",
    "documented_event_types": [
      "book",
      "price_change",
      "last_trade_price",
      "tick_size_change"
    ],
    "implementation_binding_addition": "Do not invent a market-wide sequence-gap protocol. Preserve event timestamps and provider fields; stale/reconnect policy must be an explicit QTT connector contract.",
    "market_wide_sequence_gap_contract_documented": false,
    "material_to_step11_certification": false,
    "optional_lifecycle_events_are_schema_version_dependent": true,
    "resolved_current_url": "https://docs.polymarket.com/market-data/realtime-data#market-stream",
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "The public market channel exposes book, price_change, tick_size_change, last_trade_price and optional BBO/lifecycle events.",
      "Events include timestamps and hashes, but the documentation does not establish a market-wide sequence-number gap contract.",
      "The surface supports current aggregate L2 and bounded fill proxies, not exact native queue-ahead proof."
    ],
    "failure_reason_code": "ST12_SOURCE_09_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface POLYMARKET_GLOBAL_PUBLIC_CLOB_MARKET_WEBSOCKET to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P7D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-POLYGLOBAL-WSS-MARKET"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::10::epoch2::01",
        "fact": "Fee basis is C * feeRate * p * (1-p), with fee charged on taker transactions and makers never charged.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::10::epoch2::02",
        "fact": "The current Sports category schedule shown on the direct official page is taker fee rate 0.05 and maker rebate percentage 15%.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::10::epoch2::03",
        "fact": "Exact per-market configuration returned by getClobMarketInfo is stronger than the category schedule and must be bound by market and effective time.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::10::epoch2::04",
        "fact": "Fee precision is five decimal places unless an exact market binding states otherwise.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "conflicting_cached_claim": "SPORTS_TAKER_0.03_AND_MAKER_REBATE_25_PERCENT",
    "controlling_direct_official_claim": "SPORTS_TAKER_0.05_AND_MAKER_REBATE_15_PERCENT_WITH_PER_MARKET_CONFIGURATION_STRONGER",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "CURRENT_OBSERVATION_NO_PUBLISHED_EFFECTIVE_INSTANT",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Polymarket Global",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "search_cache_conflict_detected": true,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::10",
    "source_conflict_resolution": "DIRECT_CURRENT_OFFICIAL_PAGE_OUTRANKS_SEARCH_CACHE",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::10",
    "source_title": "Polymarket Global — Fees (current direct documentation)",
    "source_url": "https://docs.polymarket.com/trading/fees",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface POLYMARKET_GLOBAL_MARKET_SPECIFIC_FEES to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-POLYGLOBAL-FEES",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::10",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::10",
  "stable_source_identity": "VENUE::ST10-SOURCE_10::POLYMARKET_GLOBAL_FEES_CURRENT_DIRECT_DOCUMENTATION",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "current_category_matrix": {
      "CRYPTO": {
        "fee_rate": "0.07",
        "maker_rebate_share": "0.20"
      },
      "CULTURE": {
        "fee_rate": "0.05",
        "maker_rebate_share": "0.25"
      },
      "ECONOMICS": {
        "fee_rate": "0.05",
        "maker_rebate_share": "0.25"
      },
      "FINANCE": {
        "fee_rate": "0.04",
        "maker_rebate_share": "0.25"
      },
      "GEOPOLITICS": {
        "fee_rate": "0.00",
        "maker_rebate_share": "0.00"
      },
      "MENTIONS": {
        "fee_rate": "0.04",
        "maker_rebate_share": "0.25"
      },
      "OTHER_OR_GENERAL": {
        "fee_rate": "0.05",
        "maker_rebate_share": "0.25"
      },
      "POLITICS": {
        "fee_rate": "0.04",
        "maker_rebate_share": "0.25"
      },
      "SPORTS": {
        "fee_rate": "0.05",
        "maker_rebate_share": "0.15"
      },
      "TECH": {
        "fee_rate": "0.04",
        "maker_rebate_share": "0.25"
      },
      "WEATHER": {
        "fee_rate": "0.05",
        "maker_rebate_share": "0.25"
      }
    },
    "delta_class": "MATERIAL_CURRENT_DIRECT_PAGE_RECONCILIATION",
    "direct_page_precedence": "CURRENT_DIRECT_OFFICIAL_PAGE_OVER_STALE_SEARCH_OR_CACHE_REPRESENTATION",
    "fee_formula": "fee = contracts * fee_rate * price * (1-price)",
    "fee_precision": "ROUND_TO_5_DECIMAL_PLACES_MINIMUM_NONZERO_0.00001_OTHERWISE_ZERO",
    "maker_fee_rate": "0",
    "material_to_step11_certification": false,
    "revalidated_at_utc": "2026-07-24T02:49:43Z",
    "revalidation_basis": "STEP12_DIRECT_OFFICIAL_PAGE_RECHECK"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "Fees are determined per market at match time; market metadata is primary at runtime.",
      "fee = contracts * fee_rate * price * (1-price).",
      "Makers are not charged a fee; only takers pay the fee.",
      "Current category matrix is exact as recorded in the Step 12 addendum, including Sports 0.05 and 15 percent maker-rebate share.",
      "Fees are rounded to five decimals; the smallest nonzero fee is 0.00001."
    ],
    "failure_reason_code": "ST12_SOURCE_10_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface POLYMARKET_GLOBAL_MARKET_SPECIFIC_FEES to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P1D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-POLYGLOBAL-FEES"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::11::epoch2::01",
        "fact": "DELETE /orders is limited to 2,000 requests per 10 seconds and 15,000 requests per 10 minutes on the current direct official page.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::11::epoch2::02",
        "fact": "Request rate and per-request cardinality are different controls and must not be conflated.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::11::epoch2::03",
        "fact": "Rate-limit behavior is endpoint- and epoch-specific; a later typed source refresh may supersede these values.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "CURRENT_OBSERVATION_NO_PUBLISHED_EFFECTIVE_INSTANT",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Polymarket Global",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::11",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::11",
    "source_title": "Polymarket Global — Current rate limits",
    "source_url": "https://docs.polymarket.com/api-reference/rate-limits",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface POLYMARKET_GLOBAL_REQUEST_BUDGETS to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-POLYGLOBAL-RATE-LIMITS",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::11",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::11",
  "stable_source_identity": "VENUE::ST10-SOURCE_11::POLYMARKET_GLOBAL_CURRENT_RATE_LIMITS",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "CURRENT_RATE_LIMIT_BINDING_RECONFIRMED",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "selected_documented_limits": {
      "DELETE_/orders": "2000 requests per 10 seconds and 15000 requests per 10 minutes",
      "binding_rule": "Use exact endpoint-specific current limit; no global extrapolation."
    },
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "DELETE /orders is limited to 2,000 requests per 10 seconds and 15,000 requests per 10 minutes on the current direct official page.",
      "Request rate and per-request cardinality are different controls and must not be conflated.",
      "Rate-limit behavior is endpoint- and epoch-specific; a later typed source refresh may supersede these values."
    ],
    "failure_reason_code": "ST12_SOURCE_11_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface POLYMARKET_GLOBAL_REQUEST_BUDGETS to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P1D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-POLYGLOBAL-RATE-LIMITS"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::12::epoch2::01",
        "fact": "The current direct official page states an effective time of 12:00 AM Eastern Time on July 1, 2026.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::12::epoch2::02",
        "fact": "The taker fee theta is 0.06 and the maker rebate theta is -0.0125 under the published formulas.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::12::epoch2::03",
        "fact": "Fees and rebates are rounded to the nearest USD 0.01 using half-even rounding.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::12::epoch2::04",
        "fact": "Historical replay must bind the fee epoch effective at simulated time rather than applying the latest epoch retroactively.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "conflicting_cached_claim": "APRIL_3_2026_THETA_0.05",
    "controlling_direct_official_claim": "JULY_1_2026_THETA_0.06_AND_MAKER_REBATE_THETA_MINUS_0.0125",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": "2026-07-01T04:00:00Z",
    "effective_time_precision": "EXACT_12AM_AMERICA_NEW_YORK_CONVERTED_TO_UTC",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Polymarket US",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "search_cache_conflict_detected": true,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::12",
    "source_conflict_resolution": "DIRECT_CURRENT_OFFICIAL_PAGE_OUTRANKS_SEARCH_CACHE",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::12",
    "source_title": "Polymarket US — Fee Schedule effective July 1, 2026",
    "source_url": "https://docs.polymarket.us/fees",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface POLYMARKET_US_EXCHANGE_WIDE_FEE_EPOCH to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-POLYUS-FEES-2026-07-01",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::12",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::12",
  "stable_source_identity": "VENUE::ST10-SOURCE_12::POLYMARKET_US_FEE_SCHEDULE_EFFECTIVE_JULY_1_2026",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "current_fee_schedule": {
      "effective_from": "2026-07-01T00:00:00-04:00",
      "formula": "amount = theta * contracts * price * (1-price)",
      "maker_rebate_theta": "-0.0125",
      "rounding": "BANKERS_ROUNDING_TO_CENTS_AT_EXCHANGE_FEE_BOUNDARY",
      "taker_theta": "0.06",
      "taker_volume_rebate_tiers": [
        {
          "prior_calendar_month_notional_max": "999999.99",
          "prior_calendar_month_notional_min": "250000",
          "rebate_share": "0.10"
        },
        {
          "prior_calendar_month_notional_max": "9999999.99",
          "prior_calendar_month_notional_min": "1000000",
          "rebate_share": "0.25"
        },
        {
          "prior_calendar_month_notional_max": null,
          "prior_calendar_month_notional_min": "10000000",
          "rebate_share": "0.50"
        }
      ]
    },
    "delta_class": "MATERIAL_CURRENT_EFFECTIVE_EPOCH_RECONFIRMED",
    "material_to_step11_certification": false,
    "revalidated_at_utc": "2026-07-24T02:49:43Z",
    "revalidation_basis": "STEP12_DIRECT_OFFICIAL_PAGE_RECHECK",
    "venue_scope": "POLYMARKET_US_ONLY_NOT_POLYMARKET_GLOBAL"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "Exchange-wide fee schedule is effective from 12 AM ET on July 1, 2026.",
      "Fee or rebate amount equals theta times contracts times price times one minus price.",
      "Taker theta is 0.06 and maker rebate theta is -0.0125.",
      "Taker volume rebates use prior-calendar-month notional tiers of 10, 25, and 50 percent.",
      "Polymarket US semantics are not generalized to Polymarket Global."
    ],
    "failure_reason_code": "ST12_SOURCE_12_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface POLYMARKET_US_EXCHANGE_WIDE_FEE_EPOCH to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P1D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-POLYUS-FEES-2026-07-01"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::13::epoch2::01",
        "fact": "The July 9, 2026 official changelog announces weekly Thursday maintenance from 2:00 AM to 6:00 AM Eastern Time.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::13::epoch2::02",
        "fact": "This newer changelog epoch supersedes the older FAQ interval of 6:00 AM to 8:00 AM Eastern Time for current implementation.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::13::epoch2::03",
        "fact": "Maintenance behavior remains an operational availability binding and does not create provider connection or order authority.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "DATE_ONLY; NO EXACT INSTANT STATED",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Polymarket US",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::13",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::13",
    "source_title": "Polymarket US — Changelog maintenance epoch effective July 9, 2026",
    "source_url": "https://docs.polymarket.us/changelog",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface POLYMARKET_US_WEEKLY_MAINTENANCE to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-POLYUS-MAINTENANCE-2026-07-09",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::13",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::13",
  "stable_source_identity": "VENUE::ST10-SOURCE_13::POLYMARKET_US_CHANGELOG_MAINTENANCE_EPOCH_EFFECTIVE_JULY_9_2026",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "CURRENT_CHANGELOG_RECONCILIATION",
    "fee_schedule_precedence": "ST10-SOURCE::12",
    "latest_observed_nonfee_metadata_release": "2026-07-20",
    "maintenance_epoch_observed": "2026-07-09",
    "material_to_step11_certification": false,
    "retention_epoch_observed": "2026-07-16",
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "The July 9, 2026 official changelog announces weekly Thursday maintenance from 2:00 AM to 6:00 AM Eastern Time.",
      "This newer changelog epoch supersedes the older FAQ interval of 6:00 AM to 8:00 AM Eastern Time for current implementation.",
      "Maintenance behavior remains an operational availability binding and does not create provider connection or order authority."
    ],
    "failure_reason_code": "ST12_SOURCE_13_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface POLYMARKET_US_WEEKLY_MAINTENANCE to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P1D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-POLYUS-MAINTENANCE-2026-07-09"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::14::epoch2::01",
        "fact": "Long-lived HTTP market-data messages are complete snapshot-style updates unless a specific interface states delta semantics.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::14::epoch2::02",
        "fact": "REST/L2 order books are aggregated by price level; individual order IDs are not visible.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::14::epoch2::03",
        "fact": "Price and quantity scaling must use exact integer-to-decimal conversion.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Polymarket US",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::14",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::14",
    "source_title": "Polymarket US — Market Data",
    "source_url": "https://docs.polymarket.us/trader-guide/market-data",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface POLYMARKET_US_AGGREGATE_HTTP_STREAM_MARKET_DATA to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-POLYUS-MARKET-DATA",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::14",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::14",
  "stable_source_identity": "VENUE::ST10-SOURCE_14::POLYMARKET_US_MARKET_DATA",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "Long-lived HTTP market-data messages are complete snapshot-style updates unless a specific interface states delta semantics.",
      "REST/L2 order books are aggregated by price level; individual order IDs are not visible.",
      "Price and quantity scaling must use exact integer-to-decimal conversion."
    ],
    "failure_reason_code": "ST12_SOURCE_14_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface POLYMARKET_US_AGGREGATE_HTTP_STREAM_MARKET_DATA to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P7D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-POLYUS-MARKET-DATA"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::15::epoch2::01",
        "fact": "The historical time-and-sales report contains timestamp, symbol, execution price, and quantity.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::15::epoch2::02",
        "fact": "It does not include side, aggressor flag, buyer, or seller information.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::15::epoch2::03",
        "fact": "The tape does not establish historical L2 or queue priority.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Polymarket US",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::15",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::15",
    "source_title": "Polymarket US — Time and Sales Report",
    "source_url": "https://docs.polymarket.us/faqs/execution-tape",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface POLYMARKET_US_PUBLIC_HISTORICAL_EXECUTION_TAPE to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-POLYUS-TIME-SALES",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::15",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::15",
  "stable_source_identity": "VENUE::ST10-SOURCE_15::POLYMARKET_US_TIME_AND_SALES_REPORT",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "The historical time-and-sales report contains timestamp, symbol, execution price, and quantity.",
      "It does not include side, aggressor flag, buyer, or seller information.",
      "The tape does not establish historical L2 or queue priority."
    ],
    "failure_reason_code": "ST12_SOURCE_15_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface POLYMARKET_US_PUBLIC_HISTORICAL_EXECUTION_TAPE to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P7D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-POLYUS-TIME-SALES"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::16::epoch2::01",
        "fact": "The endpoint returns aggregate trade statistics and bar summaries including first, last, high, low, trade count, volume, and notional over a requested period.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::16::epoch2::02",
        "fact": "It does not establish individual execution records, side or aggressor, buyer or seller identity, order identity, historical L2, or queue priority.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::16::epoch2::03",
        "fact": "This aggregate report surface is distinct from downloadable Time & Sales, live aggregate market data, and conditional institutional FIX MBO.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Polymarket US",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::16",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::16",
    "source_title": "Polymarket US — Get Trade Stats",
    "source_url": "https://docs.polymarket.us/api-reference/report/get-trade-stats",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface POLYMARKET_US_AGGREGATE_TRADE_STATISTICS to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-POLYUS-TRADE-STATS",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::16",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::16",
  "stable_source_identity": "VENUE::ST10-SOURCE_16::POLYMARKET_US_GET_TRADE_STATS",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "The endpoint returns aggregate trade statistics and bar summaries including first, last, high, low, trade count, volume, and notional over a requested period.",
      "It does not establish individual execution records, side or aggressor, buyer or seller identity, order identity, historical L2, or queue priority.",
      "This aggregate report surface is distinct from downloadable Time & Sales, live aggregate market data, and conditional institutional FIX MBO."
    ],
    "failure_reason_code": "ST12_SOURCE_16_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface POLYMARKET_US_AGGREGATE_TRADE_STATISTICS to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P7D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-POLYUS-TRADE-STATS"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::17::epoch2::01",
        "fact": "During the Thursday, July 16, 2026 maintenance window, orders older than 90 days, market data older than 45 days, and executions beyond the retained window were pruned.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::17::epoch2::02",
        "fact": "Going-forward retention is orders 90 days, market data 45 days, and executions 7 days; trades and positions remain unchanged.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::17::epoch2::03",
        "fact": "The source does not state one exact activation instant inside the 2:00 AM–6:00 AM Eastern maintenance window; replay spanning that window requires observed completion evidence and otherwise fails closed.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::17::epoch2::04",
        "fact": "Retention limits are access-window facts and do not imply historical L2, queue identity, or indefinite replay availability.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AFTER_JULY16_MAINTENANCE_WITH_WINDOW_BOUNDARY",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Polymarket US",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::17",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::17",
    "source_title": "Polymarket US — Changelog retention epochs through July 16, 2026",
    "source_url": "https://docs.polymarket.us/changelog",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface POLYMARKET_US_INSTITUTIONAL_RETENTION to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-POLYUS-RETENTION",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::17",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::17",
  "stable_source_identity": "VENUE::ST10-SOURCE_17::POLYMARKET_US_CHANGELOG_RETENTION_EPOCHS_THROUGH_JULY_16_2026",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "current_non_target_metadata_update": {
      "client_version": "0.0.71",
      "optional_sports_instrument_fields": [
        "home_team_name",
        "away_team_name",
        "tournament_name"
      ],
      "published": "2026-07-20"
    },
    "delta_class": "NON_TARGET_CHANGELOG_METADATA_ADDITION",
    "material_to_step11_certification": false,
    "retention_epoch_binding_changed": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "During the Thursday, July 16, 2026 maintenance window, orders older than 90 days, market data older than 45 days, and executions beyond the retained window were pruned.",
      "Going-forward retention is orders 90 days, market data 45 days, and executions 7 days; trades and positions remain unchanged.",
      "The source does not state one exact activation instant inside the 2:00 AM–6:00 AM Eastern maintenance window; replay spanning that window requires observed completion evidence and otherwise fails closed.",
      "Retention limits are access-window facts and do not imply historical L2, queue identity, or indefinite replay availability."
    ],
    "failure_reason_code": "ST12_SOURCE_17_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface POLYMARKET_US_INSTITUTIONAL_RETENTION to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P1D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-POLYUS-RETENTION"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::18::epoch2::01",
        "fact": "A separate FIX market-data gateway can expose Market-by-Order, with individual orders, timestamps and OrderID.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::18::epoch2::02",
        "fact": "MarketDepth supports full book or up to 25 price levels.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::18::epoch2::03",
        "fact": "This surface is participant/session scoped, separate from aggregate REST/HTTP data, and is not enabled by Step 9.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CONDITIONAL_NOT_DEFAULT_NOT_ENABLED_BY_STEP9",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Polymarket US",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::18",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::18",
    "source_title": "Polymarket US — FIX Market Data Subscription",
    "source_url": "https://docs.polymarket.us/institutional/fix-api/fix-market-data-subscription",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface POLYMARKET_US_SEPARATE_FIX_MARKET_DATA_GATEWAY to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-POLYUS-FIX-MBO",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::18",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::18",
  "stable_source_identity": "VENUE::ST10-SOURCE_18::POLYMARKET_US_FIX_MARKET_DATA_SUBSCRIPTION",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "A separate FIX market-data gateway can expose Market-by-Order, with individual orders, timestamps and OrderID.",
      "MarketDepth supports full book or up to 25 price levels.",
      "This surface is participant/session scoped, separate from aggregate REST/HTTP data, and is not enabled by Step 9."
    ],
    "failure_reason_code": "ST12_SOURCE_18_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface POLYMARKET_US_SEPARATE_FIX_MARKET_DATA_GATEWAY to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P7D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-POLYUS-FIX-MBO"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::19::epoch2::01",
        "fact": "Web API top-of-book data and OHLC historical bars can be requested for Event Contracts.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::19::epoch2::02",
        "fact": "Historical bars are available only while the instrument is trading and are unavailable after expiration.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::19::epoch2::03",
        "fact": "OHLC bars do not establish historical trade-tape identity, L2, or queue evidence.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "IBKR",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::19",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::19",
    "source_title": "IBKR — Event Contracts in the Web API",
    "source_url": "https://www.interactivebrokers.com/campus/ibkr-api-page/event-contracts/",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface IBKR_WEB_API_EVENT_CONTRACTS to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-IBKR-WEB-EVENT-CONTRACTS",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::19",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::19",
  "stable_source_identity": "VENUE::ST10-SOURCE_19::IBKR_EVENT_CONTRACTS_IN_THE_WEB_API",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "Web API top-of-book data and OHLC historical bars can be requested for Event Contracts.",
      "Historical bars are available only while the instrument is trading and are unavailable after expiration.",
      "OHLC bars do not establish historical trade-tape identity, L2, or queue evidence."
    ],
    "failure_reason_code": "ST12_SOURCE_19_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface IBKR_WEB_API_EVENT_CONTRACTS to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P7D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-IBKR-WEB-EVENT-CONTRACTS"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::20::epoch2::01",
        "fact": "ForecastEx TWS event data has no historical Trades and no real-time Last because bid/ask do not map conventionally to buy/sell.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::20::epoch2::02",
        "fact": "ForecastEx orders are BUY-only, limit-only, with DAY/GTC/IOC time in force.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::20::epoch2::03",
        "fact": "A position is reduced or closed by buying the opposing contract.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "IBKR",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::20",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::20",
    "source_title": "IBKR — TWS API Event Trading",
    "source_url": "https://www.interactivebrokers.com/campus/ibkr-api-page/event-trading/",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface IBKR_TWS_API_FORECASTEX to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-IBKR-TWS-EVENT-CONTRACTS",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::20",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::20",
  "stable_source_identity": "VENUE::ST10-SOURCE_20::IBKR_TWS_API_EVENT_TRADING",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "ForecastEx TWS event data has no historical Trades and no real-time Last because bid/ask do not map conventionally to buy/sell.",
      "ForecastEx orders are BUY-only, limit-only, with DAY/GTC/IOC time in force.",
      "A position is reduced or closed by buying the opposing contract."
    ],
    "failure_reason_code": "ST12_SOURCE_20_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface IBKR_TWS_API_FORECASTEX to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "DIRECT_OFFICIAL_PROVIDER_DOCUMENTATION",
    "ttl": "P7D"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-IBKR-TWS-EVENT-CONTRACTS"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::21::epoch2::01",
        "fact": "BH uses the largest ordered index i satisfying p_(i) <= i*q/m.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::21::epoch2::02",
        "fact": "BH is distinct from the dependency-robust BY harmonic correction.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Benjamini and Hochberg",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::21",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::21",
    "source_title": "Benjamini and Hochberg — False Discovery Rate",
    "source_url": "https://doi.org/10.1111/j.2517-6161.1995.tb02031.x",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface MULTIPLE_TESTING_INDEPENDENT_OR_POSITIVE_DEPENDENCE to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-BH-FDR",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::21",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::21",
  "stable_source_identity": "METHOD::ST10-SOURCE_21::BENJAMINI_AND_HOCHBERG_FALSE_DISCOVERY_RATE",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "BH uses the largest ordered index i satisfying p_(i) <= i*q/m.",
      "BH is distinct from the dependency-robust BY harmonic correction."
    ],
    "failure_reason_code": "ST12_SOURCE_21_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface MULTIPLE_TESTING_INDEPENDENT_OR_POSITIVE_DEPENDENCE to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "PRIMARY_METHOD_OR_PUBLISHER_SOURCE",
    "ttl": "METHOD_VERSION_OR_MATERIAL_CHANGE_TRIGGERED"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-BH-FDR"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::22::epoch2::01",
        "fact": "BY uses c(m)=sum_{j=1}^m 1/j and the largest ordered index i satisfying p_(i) <= i*q/(m*c(m)).",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::22::epoch2::02",
        "fact": "This correction is distinct from BH and requires its own source and oracle.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Benjamini and Yekutieli",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::22",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::22",
    "source_title": "Benjamini and Yekutieli — FDR Under Dependency",
    "source_url": "https://doi.org/10.1214/aos/1013699998",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface MULTIPLE_TESTING_ARBITRARY_DEPENDENCY to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-BY-FDR",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::22",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::22",
  "stable_source_identity": "METHOD::ST10-SOURCE_22::BENJAMINI_AND_YEKUTIELI_FDR_UNDER_DEPENDENCY",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "BY uses c(m)=sum_{j=1}^m 1/j and the largest ordered index i satisfying p_(i) <= i*q/(m*c(m)).",
      "This correction is distinct from BH and requires its own source and oracle."
    ],
    "failure_reason_code": "ST12_SOURCE_22_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface MULTIPLE_TESTING_ARBITRARY_DEPENDENCY to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "PRIMARY_METHOD_OR_PUBLISHER_SOURCE",
    "ttl": "METHOD_VERSION_OR_MATERIAL_CHANGE_TRIGGERED"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-BY-FDR"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::23::epoch2::01",
        "fact": "The Wilson score interval supplies a bounded binomial-proportion confidence interval and avoids the unstable Wald form near boundaries.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Wilson",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::23",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::23",
    "source_title": "Wilson — Score Interval",
    "source_url": "https://doi.org/10.1080/01621459.1927.10502953",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface BINOMIAL_PROPORTION_INTERVAL to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-WILSON-INTERVAL",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::23",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::23",
  "stable_source_identity": "METHOD::ST10-SOURCE_23::WILSON_SCORE_INTERVAL",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "The Wilson score interval supplies a bounded binomial-proportion confidence interval and avoids the unstable Wald form near boundaries."
    ],
    "failure_reason_code": "ST12_SOURCE_23_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface BINOMIAL_PROPORTION_INTERVAL to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "PRIMARY_METHOD_OR_PUBLISHER_SOURCE",
    "ttl": "METHOD_VERSION_OR_MATERIAL_CHANGE_TRIGGERED"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-WILSON-INTERVAL"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::24::epoch2::01",
        "fact": "The stationary bootstrap uses random-length blocks to preserve weak temporal dependence.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::24::epoch2::02",
        "fact": "The block termination probability has no universal Step 9 numeric default and requires declared calibration.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Politis and Romano",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::24",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::24",
    "source_title": "Politis and Romano — Stationary Bootstrap",
    "source_url": "https://doi.org/10.1080/01621459.1994.10476870",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface WEAKLY_DEPENDENT_STATIONARY_RESAMPLING to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-STATIONARY-BOOTSTRAP",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::24",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::24",
  "stable_source_identity": "METHOD::ST10-SOURCE_24::POLITIS_AND_ROMANO_STATIONARY_BOOTSTRAP",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "The stationary bootstrap uses random-length blocks to preserve weak temporal dependence.",
      "The block termination probability has no universal Step 9 numeric default and requires declared calibration."
    ],
    "failure_reason_code": "ST12_SOURCE_24_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface WEAKLY_DEPENDENT_STATIONARY_RESAMPLING to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "PRIMARY_METHOD_OR_PUBLISHER_SOURCE",
    "ttl": "METHOD_VERSION_OR_MATERIAL_CHANGE_TRIGGERED"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-STATIONARY-BOOTSTRAP"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::25::epoch2::01",
        "fact": "The Reality Check evaluates whether the best model found in a specification search has predictive superiority over a benchmark while accounting for data reuse.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "White",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::25",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::25",
    "source_title": "White — Reality Check for Data Snooping",
    "source_url": "https://doi.org/10.1111/1468-0262.00152",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface DATA_SNOOPING_MULTIPLE_MODEL_COMPARISON to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-WHITE-REALITY-CHECK",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::25",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::25",
  "stable_source_identity": "METHOD::ST10-SOURCE_25::WHITE_REALITY_CHECK_FOR_DATA_SNOOPING",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "The Reality Check evaluates whether the best model found in a specification search has predictive superiority over a benchmark while accounting for data reuse."
    ],
    "failure_reason_code": "ST12_SOURCE_25_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface DATA_SNOOPING_MULTIPLE_MODEL_COMPARISON to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "PRIMARY_METHOD_OR_PUBLISHER_SOURCE",
    "ttl": "METHOD_VERSION_OR_MATERIAL_CHANGE_TRIGGERED"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-WHITE-REALITY-CHECK"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::26::epoch2::01",
        "fact": "SPA improves power and reduces sensitivity to poor alternatives relative to the Reality Check.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::26::epoch2::02",
        "fact": "SPA is a significance test, not a strategy-selection or promotion authority.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Hansen",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::26",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::26",
    "source_title": "Hansen — Test for Superior Predictive Ability",
    "source_url": "https://doi.org/10.1198/073500105000000063",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface SUPERIOR_PREDICTIVE_ABILITY_TEST to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-HANSEN-SPA",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::26",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::26",
  "stable_source_identity": "METHOD::ST10-SOURCE_26::HANSEN_TEST_FOR_SUPERIOR_PREDICTIVE_ABILITY",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "SPA improves power and reduces sensitivity to poor alternatives relative to the Reality Check.",
      "SPA is a significance test, not a strategy-selection or promotion authority."
    ],
    "failure_reason_code": "ST12_SOURCE_26_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface SUPERIOR_PREDICTIVE_ABILITY_TEST to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "PRIMARY_METHOD_OR_PUBLISHER_SOURCE",
    "ttl": "METHOD_VERSION_OR_MATERIAL_CHANGE_TRIGGERED"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-HANSEN-SPA"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::27::epoch2::01",
        "fact": "CSCV estimates probability of backtest overfitting by enumerating symmetric train/test subset combinations and evaluating the out-of-sample relative rank of the in-sample winner.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Bailey et al.",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::27",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::27",
    "source_title": "Bailey et al. — Probability of Backtest Overfitting",
    "source_url": "https://doi.org/10.21314/JCF.2016.322",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface BACKTEST_OVERFITTING_CSCV to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-PBO-CSCV",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::27",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::27",
  "stable_source_identity": "METHOD::ST10-SOURCE_27::BAILEY_ET_AL_PROBABILITY_OF_BACKTEST_OVERFITTING",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "CSCV estimates probability of backtest overfitting by enumerating symmetric train/test subset combinations and evaluating the out-of-sample relative rank of the in-sample winner."
    ],
    "failure_reason_code": "ST12_SOURCE_27_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface BACKTEST_OVERFITTING_CSCV to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "PRIMARY_METHOD_OR_PUBLISHER_SOURCE",
    "ttl": "METHOD_VERSION_OR_MATERIAL_CHANGE_TRIGGERED"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-PBO-CSCV"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::28::epoch2::01",
        "fact": "DSR adjusts a Sharpe-ratio claim for selection bias, multiple trials and non-normal returns.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::28::epoch2::02",
        "fact": "Trial count and cross-trial dispersion must be explicit; no hidden candidate inventory is allowed.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "Bailey and Lopez de Prado",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::28",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::28",
    "source_title": "Bailey and Lopez de Prado — Deflated Sharpe Ratio",
    "source_url": "https://doi.org/10.3905/jpm.2014.40.5.094",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind interface SELECTION_ADJUSTED_SHARPE_INFERENCE to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-DSR",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::28",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::28",
  "stable_source_identity": "METHOD::ST10-SOURCE_28::BAILEY_AND_LOPEZ_DE_PRADO_DEFLATED_SHARPE_RATIO",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "DSR adjusts a Sharpe-ratio claim for selection bias, multiple trials and non-normal returns.",
      "Trial count and cross-trial dispersion must be explicit; no hidden candidate inventory is allowed."
    ],
    "failure_reason_code": "ST12_SOURCE_28_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind interface SELECTION_ADJUSTED_SHARPE_INFERENCE to the exact owner-currentized facts and effective state; future refresh belongs to SourceCurrentizationOwner and never Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "PRIMARY_METHOD_OR_PUBLISHER_SOURCE",
    "ttl": "METHOD_VERSION_OR_MATERIAL_CHANGE_TRIGGERED"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-DSR"
},
{
  "certified_step11_identity_state": "VERIFIED_EXACT_V1_2R10",
  "certified_step11_row": {
    "active_runtime_authority": false,
    "all_atomic_facts_pass": true,
    "atomic_fact_results": [
      {
        "atomic_fact_id": "ST10-SOURCE::29::epoch2::01",
        "fact": "The Probabilistic Sharpe Ratio evaluates the probability that an estimated Sharpe ratio exceeds a stated benchmark under non-normal returns.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::29::epoch2::02",
        "fact": "Its implementation requires sample length, benchmark Sharpe, observed Sharpe, skewness and kurtosis assumptions on one declared return-frequency basis.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      },
      {
        "atomic_fact_id": "ST10-SOURCE::29::epoch2::03",
        "fact": "Minimum track-record length and statistical PSR passage are evidence measures only and create no live promotion or order authority.",
        "result": "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
      }
    ],
    "availability_state": "CURRENT_AVAILABLE",
    "codex_browsing_forbidden": true,
    "codex_online_research_required": false,
    "conflict_resolution_state": "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE",
    "conflict_result": "PASS_TERMINAL_CONFLICT_RESOLUTION_PRESERVED_OR_CURRENTIZED",
    "currentization_cutoff_owner_local_date": "2026-07-23",
    "effective_from": null,
    "effective_time_precision": "SOURCE_DECLARED_OR_EXPLICITLY_UNKNOWN",
    "effective_to_or_open": "OPEN_UNTIL_SUPERSEDED",
    "epoch": "epoch2",
    "epoch2_revalidation_state": "PASS_TERMINAL_OWNER_SIDE_SOURCE_EPOCH_COMPLETE_BEFORE_FINAL_R10_FREEZE",
    "future_fact_exclusion_state": "FUTURE_EFFECTIVE_FACTS_EXCLUDED_UNTIL_EFFECTIVE_AND_REVALIDATED",
    "historical_epoch_preservation": "PRESERVE_PRIOR_EFFECTIVE_EPOCHS_DO_NOT_OVERWRITE_HISTORY",
    "owner_local_date": "2026-07-23",
    "owner_local_timestamp": "2026-07-23T04:47:18-04:00",
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "publisher": "The Journal of Risk / Risk.net",
    "redirect_checked": true,
    "research_completeness_state": "COMPLETE_PRIMARY_SOURCE",
    "result_state": "PASS_PRIMARY_SOURCE_AUDIT_NO_RUNTIME_CLAIM",
    "retrieved_at_utc": "2026-07-23T08:47:18Z",
    "revalidated_at_utc": "2026-07-23T08:47:18Z",
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "runtime_online_research_allowed": false,
    "source_audit_row_id": "ST11-SOURCE::EPOCH2::29",
    "source_currentization_owner": "Step11GPTSourceResearchOwnerV1",
    "source_precedence": "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION",
    "source_state_id": "ST10-SOURCE::29",
    "source_title": "Bailey and Lopez de Prado — The Sharpe Ratio Efficient Frontier",
    "source_url": "https://www.risk.net/journal-risk/2223785/sharpe-ratio-efficient-frontier",
    "step12_binding_fields": {
      "canonical_owner": "SourceCurrentizationOwner",
      "future_revalidation_owner": "SOURCE_CURRENTIZATION_OWNER",
      "implementation_requirement": "Bind PROBABILISTIC_SHARPE_RATIO to The Sharpe Ratio Efficient Frontier; keep strategy-approval decision logic as a distinct identity and source lineage; no Codex browsing.",
      "next_recheck_trigger": "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    },
    "subject_id": "ST9-SRC-PSR-SHARPE-RATIO-EFFICIENT-FRONTIER",
    "unresolved_research": false,
    "verification_method": "DIRECT_CURRENT_PRIMARY_PROVIDER_OR_PUBLISHER_PAGE_REOPENED_OWNER_SIDE_BEFORE_FINAL_R10_FREEZE; POST_CAMPAIGN_NO_CHANGE_RECHECK_RECORDED_ONLY_IN_EXTERNAL_PUBLICATION_RECEIPT"
  },
  "codex_online_research_allowed": false,
  "currentized_at_utc": "2026-07-23T20:07:31Z",
  "currentized_owner_local_timestamp": "2026-07-23T16:07:31-04:00",
  "provider_connection_or_effect_authorized": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
  "runtime_online_research_allowed": false,
  "source_audit_row_id": "ST11-SOURCE::EPOCH2::29",
  "source_currentization_owner": "SourceCurrentizationOwnerV1",
  "source_state_id": "ST10-SOURCE::29",
  "stable_source_identity": "METHOD::ST10-SOURCE_29::BAILEY_AND_LOPEZ_DE_PRADO_THE_SHARPE_RATIO_EFFICIENT_FRONTIER",
  "step12_currentization_addendum": {
    "certified_step11_row_modified": false,
    "delta_class": "NO_MATERIAL_CHANGE_RECONFIRMED_OR_STABLE_METHOD_SOURCE",
    "material_to_step11_certification": false,
    "revalidation_basis": "INHERITED_EXACT_STEP11R10_SOURCE_EPOCH_NO_NEW_DIRECT_STEP12_RECHECK_CLAIM",
    "step12_packaged_at_utc": "2026-07-24T02:49:43Z"
  },
  "step12_implementation_specification": {
    "exact_claims": [
      "The Probabilistic Sharpe Ratio evaluates the probability that an estimated Sharpe ratio exceeds a stated benchmark under non-normal returns.",
      "Its implementation requires sample length, benchmark Sharpe, observed Sharpe, skewness and kurtosis assumptions on one declared return-frequency basis.",
      "Minimum track-record length and statistical PSR passage are evidence measures only and create no live promotion or order authority."
    ],
    "failure_reason_code": "ST12_SOURCE_29_MISSING_STALE_CONFLICT_UNSUPPORTED_OR_RIGHTS_BLOCKED",
    "implementation_binding": [
      "Bind PROBABILISTIC_SHARPE_RATIO to The Sharpe Ratio Efficient Frontier; keep strategy-approval decision logic as a distinct identity and source lineage; no Codex browsing.",
      "Compile the exact certified atomic facts into typed schemas, fixtures and fail-closed parser or method contracts; never infer unlisted provider fields or authority."
    ],
    "permitted_use_class": "IMPLEMENTATION_REFERENCE_CONFIGURATION_BINDING_AND_BOUNDED_TEST_METADATA_ONLY",
    "precision_and_rounding_policy": "EXACT_SOURCE_DECLARED_SEMANTICS; DECIMAL_FOR_FINANCIAL_VALUES; NO_HIDDEN_ROUNDING_OR_FLOAT_COERCION",
    "recheck_triggers": [
      "TYPED_SOURCE_REFRESH_GATE_BEFORE_EMPIRICAL_OR_PROVIDER_EFFECT_USE_OR_ON_DETECTED_CHANGE"
    ],
    "rights_and_use_state": "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY_NO_DATA_LICENSE_OR_REPUBLICATION_RIGHT_INFERRED",
    "source_class": "PRIMARY_METHOD_OR_PUBLISHER_SOURCE",
    "ttl": "METHOD_VERSION_OR_MATERIAL_CHANGE_TRIGGERED"
  },
  "step12_packaged_at_utc": "2026-07-24T02:49:43Z",
  "step12_packaged_owner_local_timestamp": "2026-07-23T22:49:43-04:00",
  "step12_source_epoch_basis": "EXACT_STEP11R10_REVALIDATION_INHERITED_UNLESS_STEP12_DIRECT_RECHECK_EXPLICITLY_RECORDED",
  "subject_id": "ST9-SRC-PSR-SHARPE-RATIO-EFFICIENT-FRONTIER"
}
]
'''

_CURRENTIZATION_OVERLAY_ROWS_JSON = r'''
[
  {
    "certified_rule_011_state": "CONFIRMED_CURRENT",
    "currentization_id": "ST12A-CURR-SOURCE-001",
    "exact_facts": {
      "DELETE /cancel-all": {
        "burst": "250 requests/10 seconds",
        "sustained": "6000 requests/10 minutes"
      },
      "DELETE /cancel-market-orders": {
        "burst": "1500 requests/10 seconds",
        "sustained": "21000 requests/10 minutes"
      },
      "DELETE /order": {
        "burst": "5000 requests/10 seconds",
        "sustained": "120000 requests/10 minutes"
      },
      "DELETE /orders": {
        "burst": "2000 requests/10 seconds",
        "sustained": "15000 requests/10 minutes"
      },
      "POST /order": {
        "burst": "5000 requests/10 seconds",
        "sustained": "120000 requests/10 minutes"
      },
      "POST /orders": {
        "burst": "2000 requests/10 seconds",
        "sustained": "21000 requests/10 minutes"
      }
    },
    "implementation_rule": "STORE_BURST_AND_SUSTAINED_AS_DISTINCT_ENDPOINT_AND_WINDOW_KEYS_NO_PER_SECOND_CONFLATION",
    "retrieved_at_utc": "2026-07-24T21:55:20Z",
    "runtime_effect_authorized": false,
    "source_class": "DIRECT_OFFICIAL_DOCUMENTATION",
    "source_url": "https://docs.polymarket.com/api-reference/rate-limits",
    "subject": "Polymarket Cloudflare IP endpoint limits",
    "supersedes_package_addendum_fields": [
      "polymarket_rate_limit_matrix"
    ]
  },
  {
    "currentization_id": "ST12A-CURR-SOURCE-002",
    "exact_facts": {
      "separate_from_cloudflare_ip_limits": true,
      "standard_cancel_burst_tokens": 120,
      "standard_cancel_rate_tokens_per_second": 80,
      "standard_order_burst_tokens": 60,
      "standard_order_rate_tokens_per_second": 40,
      "warning_header": "Poly-RateLimit-Warning: true",
      "warning_mode_begins": "2026-07-24",
      "warning_mode_duration": "two weeks; live enforcement date to be announced"
    },
    "implementation_rule": "MODEL_AS_SEPARATE_SIGNER_SCOPED_BUCKET_POLICY_AND_WARNING_RECEIPT; DO_NOT_MERGE_WITH_IP_RATE_MATRIX",
    "retrieved_at_utc": "2026-07-24T21:55:20Z",
    "runtime_effect_authorized": false,
    "source_class": "DIRECT_OFFICIAL_DOCUMENTATION",
    "source_url": "https://docs.polymarket.com/api-reference/trading-rate-limits",
    "subject": "Polymarket per-signer CLOB token buckets"
  },
  {
    "currentization_id": "ST12A-CURR-SOURCE-003",
    "exact_facts": {
      "accepted_order_resubmission_allowed": false,
      "custom_REST_followup": "poll existing trades by tradeID until hash is available or status is FAILED",
      "effective_at_utc": "2026-07-24T04:00:00Z",
      "inline_transactionHashes_expected": false,
      "successful_FAK_FOK_response_uses": "tradeIDs"
    },
    "implementation_rule": "BIND_RESPONSE_CONTRACT_ONLY; NO_CONNECTOR_OR_ORDER_EXECUTION_IN_TRANCHE_A",
    "retrieved_at_utc": "2026-07-24T21:55:20Z",
    "runtime_effect_authorized": false,
    "source_class": "DIRECT_OFFICIAL_CHANGELOG",
    "source_url": "https://docs.polymarket.com/changelog/predictions",
    "subject": "Polymarket FAK/FOK successful response transition"
  },
  {
    "currentization_id": "ST12A-CURR-SOURCE-004",
    "exact_facts": {
      "order_statuses": [
        "live",
        "matched",
        "delayed",
        "unmatched"
      ],
      "trade_pending_statuses": [
        "MATCHED",
        "MINED",
        "RETRYING"
      ],
      "trade_terminal_failure_statuses": [
        "FAILED"
      ],
      "trade_terminal_success_statuses": [
        "CONFIRMED"
      ]
    },
    "implementation_rule": "INCLUDE_RETRYING_AS_NONTERMINAL_PENDING_STATE; FAIL_CLOSED_ON_UNKNOWN_STATUS",
    "retrieved_at_utc": "2026-07-24T21:55:20Z",
    "runtime_effect_authorized": false,
    "source_class": "DIRECT_OFFICIAL_DOCUMENTATION",
    "source_url": "https://docs.polymarket.com/concepts/order-lifecycle",
    "subject": "Polymarket order and trade lifecycle",
    "supersedes_package_addendum_fields": [
      "polymarket_order_transition.poll_status_matrix"
    ]
  },
  {
    "currentization_id": "ST12A-CURR-DEPENDENCY-001",
    "exact_facts": {
      "explicit_context_required": true,
      "nonfinite_and_float_operation_policy": "explicit traps/validation; do not silently accept NaN, infinity or binary-float contamination",
      "precision": 34,
      "python_line": "3.14",
      "rounding": "ROUND_HALF_EVEN"
    },
    "implementation_rule": "STANDARD_LIBRARY_ONLY_REQUIRED_IMPORT",
    "retrieved_at_utc": "2026-07-24T21:55:20Z",
    "runtime_effect_authorized": false,
    "source_class": "OFFICIAL_LANGUAGE_DOCUMENTATION",
    "source_url": "https://docs.python.org/3.14/library/decimal.html",
    "subject": "Python Decimal arithmetic baseline"
  },
  {
    "currentization_id": "ST12A-CURR-DEPENDENCY-002",
    "exact_facts": {
      "observed_version": "0.7.0",
      "official_IBM_support": false,
      "project_archived": true
    },
    "implementation_rule": "NO_MANDATORY_IMPORT_NO_INSTALL_NO_MIGRATION; OPTIONAL_ADAPTER_METADATA_ONLY",
    "retrieved_at_utc": "2026-07-24T21:55:20Z",
    "runtime_effect_authorized": false,
    "source_class": "PRIMARY_PACKAGE_INDEX_RECORD",
    "source_url": "https://pypi.org/project/qiskit-optimization/",
    "subject": "Qiskit Optimization compatibility observation"
  },
  {
    "currentization_id": "ST12A-CURR-DEPENDENCY-003",
    "exact_facts": {
      "observed_version": "9.4.0",
      "python_requires": ">=3.10",
      "released": "2026-06-18"
    },
    "implementation_rule": "NO_MANDATORY_IMPORT_NO_INSTALL_NO_BACKEND_OR_PROVIDER_EFFECT; OPTIONAL_ADAPTER_METADATA_ONLY",
    "retrieved_at_utc": "2026-07-24T21:55:20Z",
    "runtime_effect_authorized": false,
    "source_class": "PRIMARY_PACKAGE_INDEX_RECORD",
    "source_url": "https://pypi.org/project/dwave-ocean-sdk/9.4.0/",
    "subject": "D-Wave Ocean SDK compatibility observation"
  }
]
'''


def _source_record(row: object) -> SourceStateV1:
    if not isinstance(row, dict):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING, "source-state row must be an object"
        )
    certified = row["certified_step11_row"]
    specification = row["step12_implementation_specification"]
    if not isinstance(certified, dict) or not isinstance(specification, dict):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            "source state lacks certified or implementation metadata",
        )
    for field_name in (
        "provider_connection_or_effect_authorized",
        "runtime_online_research_allowed",
        "codex_online_research_allowed",
    ):
        if type(row[field_name]) is not bool:
            raise SourcePolicyError(
                ReasonCode.INVALID_CONTRACT,
                f"{field_name} must be a boolean",
            )
    atomic_rows = certified["atomic_fact_results"]
    if not isinstance(atomic_rows, list) or any(
        not isinstance(item, dict) for item in atomic_rows
    ):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            "atomic fact materialization must be a list of objects",
        )
    facts = tuple(
        AtomicSourceFactV1(
            atomic_fact_id=str(item["atomic_fact_id"]),
            fact=str(item["fact"]),
            result=AtomicFactTerminalStateV1(str(item["result"])),
        )
        for item in atomic_rows
    )
    return SourceStateV1(
        source_state_id=str(row["source_state_id"]),
        source_audit_row_id=str(row["source_audit_row_id"]),
        stable_source_identity=str(row["stable_source_identity"]),
        subject_id=str(row["subject_id"]),
        publisher=str(certified["publisher"]),
        source_title=str(certified["source_title"]),
        source_url=str(certified["source_url"]),
        epoch=str(certified["epoch"]),
        effective_from=(
            None
            if certified["effective_from"] is None
            else str(certified["effective_from"])
        ),
        effective_to_or_open=str(certified["effective_to_or_open"]),
        source_currentization_owner=str(row["source_currentization_owner"]),
        source_precedence=str(certified["source_precedence"]),
        availability_state=str(certified["availability_state"]),
        conflict_resolution_state=str(certified["conflict_resolution_state"]),
        future_fact_exclusion_state=str(certified["future_fact_exclusion_state"]),
        rights_and_use_state=str(specification["rights_and_use_state"]),
        permitted_use_class=str(specification["permitted_use_class"]),
        source_class=str(specification["source_class"]),
        ttl=str(specification["ttl"]),
        exact_claims=tuple(str(value) for value in specification["exact_claims"]),
        atomic_facts=facts,
        implementation_binding=tuple(
            str(value) for value in specification["implementation_binding"]
        ),
        failure_reason_code=str(specification["failure_reason_code"]),
        recheck_triggers=tuple(
            str(value) for value in specification["recheck_triggers"]
        ),
        research_completeness_state=ClaimBindingTerminalStateV1(
            str(row["research_completeness_state"])
        ),
        primary_source_completeness_state=PrimarySourceCompletenessV1(
            str(certified["research_completeness_state"])
        ),
        provider_connection_or_effect_authorized=row[
            "provider_connection_or_effect_authorized"
        ],
        runtime_online_research_allowed=row["runtime_online_research_allowed"],
        codex_online_research_allowed=row["codex_online_research_allowed"],
        original_row_json=json.dumps(
            row,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
    )


def _overlay_record(row: object) -> SourceCurrentizationOverlayV1:
    if not isinstance(row, dict):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING, "overlay row must be an object"
        )
    if type(row["runtime_effect_authorized"]) is not bool:
        raise SourcePolicyError(
            ReasonCode.INVALID_CONTRACT,
            "overlay runtime authority must be a boolean",
        )
    return SourceCurrentizationOverlayV1(
        currentization_id=str(row["currentization_id"]),
        subject=str(row["subject"]),
        source_class=str(row["source_class"]),
        source_url=str(row["source_url"]),
        retrieved_at_utc=str(row["retrieved_at_utc"]),
        implementation_rule=str(row["implementation_rule"]),
        exact_facts_json=json.dumps(
            row["exact_facts"],
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        supersedes_package_addendum_fields=tuple(
            str(value) for value in row.get("supersedes_package_addendum_fields", ())
        ),
        runtime_effect_authorized=row["runtime_effect_authorized"],
        original_row_json=json.dumps(
            row,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
    )


def _load_source_states() -> tuple[SourceStateV1, ...]:
    raw = json.loads(_CERTIFIED_SOURCE_ROWS_JSON)
    if not isinstance(raw, list):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING, "source-state materialization is invalid"
        )
    rows = tuple(_source_record(row) for row in raw)
    expected_ids = tuple(f"ST10-SOURCE::{index:02d}" for index in range(1, 30))
    if (
        len(rows) != 29
        or len({row.source_state_id for row in rows}) != 29
        or tuple(row.source_state_id for row in rows) != expected_ids
    ):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            f"expected 29 unique source states, found {len(rows)}",
        )
    return rows


def _load_overlays() -> tuple[SourceCurrentizationOverlayV1, ...]:
    raw = json.loads(_CURRENTIZATION_OVERLAY_ROWS_JSON)
    if not isinstance(raw, list):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING, "source overlay materialization is invalid"
        )
    rows = tuple(_overlay_record(row) for row in raw)
    expected_ids = (
        "ST12A-CURR-SOURCE-001",
        "ST12A-CURR-SOURCE-002",
        "ST12A-CURR-SOURCE-003",
        "ST12A-CURR-SOURCE-004",
        "ST12A-CURR-DEPENDENCY-001",
        "ST12A-CURR-DEPENDENCY-002",
        "ST12A-CURR-DEPENDENCY-003",
    )
    if (
        len(rows) != 7
        or len({row.currentization_id for row in rows}) != 7
        or tuple(row.currentization_id for row in rows) != expected_ids
    ):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            f"expected 7 unique source overlays, found {len(rows)}",
        )
    return rows


CERTIFIED_SOURCE_STATES = _load_source_states()
SOURCE_CURRENTIZATION_OVERLAYS = _load_overlays()
SOURCE_STATE_BY_ID: Mapping[str, SourceStateV1] = MappingProxyType(
    {row.source_state_id: row for row in CERTIFIED_SOURCE_STATES}
)
SOURCE_OVERLAY_BY_ID: Mapping[str, SourceCurrentizationOverlayV1] = MappingProxyType(
    {row.currentization_id: row for row in SOURCE_CURRENTIZATION_OVERLAYS}
)


POLYMARKET_ENDPOINT_LIMITS = (
    EndpointWindowLimitV1("DELETE /cancel-all", 250, 10, 6000, 600),
    EndpointWindowLimitV1("DELETE /cancel-market-orders", 1500, 10, 21000, 600),
    EndpointWindowLimitV1("DELETE /order", 5000, 10, 120000, 600),
    EndpointWindowLimitV1("DELETE /orders", 2000, 10, 15000, 600),
    EndpointWindowLimitV1("POST /order", 5000, 10, 120000, 600),
    EndpointWindowLimitV1("POST /orders", 2000, 10, 21000, 600),
)

POLYMARKET_SIGNER_BUCKETS = (
    SignerTokenBucketV1(
        "STANDARD_CANCEL",
        80,
        120,
        "Poly-RateLimit-Warning: true",
        "2026-07-24",
        "two weeks; live enforcement date to be announced",
    ),
    SignerTokenBucketV1(
        "STANDARD_ORDER",
        40,
        60,
        "Poly-RateLimit-Warning: true",
        "2026-07-24",
        "two weeks; live enforcement date to be announced",
    ),
)

FAK_FOK_RESPONSE_CONTRACT = FAKFOKResponseContractV1(
    effective_at_utc="2026-07-24T04:00:00Z"
)

ORDER_LIFECYCLE_STATES = frozenset({"live", "matched", "delayed", "unmatched"})
TRADE_PENDING_STATES = frozenset({"MATCHED", "MINED", "RETRYING"})
TRADE_TERMINAL_SUCCESS_STATES = frozenset({"CONFIRMED"})
TRADE_TERMINAL_FAILURE_STATES = frozenset({"FAILED"})


def classify_trade_lifecycle(state: str) -> TradeLifecycleClass:
    if state in TRADE_PENDING_STATES:
        return TradeLifecycleClass.PENDING
    if state in TRADE_TERMINAL_SUCCESS_STATES:
        return TradeLifecycleClass.TERMINAL_SUCCESS
    if state in TRADE_TERMINAL_FAILURE_STATES:
        return TradeLifecycleClass.TERMINAL_FAILURE
    raise SourcePolicyError(
        ReasonCode.UNKNOWN_LIFECYCLE_STATE,
        f"unknown trade lifecycle state: {state!r}",
    )


def get_source_state(source_state_id: str) -> SourceStateV1:
    if not isinstance(source_state_id, str) or not source_state_id:
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            "source-state identity must be nonempty text",
        )
    try:
        return SOURCE_STATE_BY_ID[source_state_id]
    except KeyError as exc:
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            f"unknown source state: {source_state_id}",
        ) from exc


def validate_effective_epoch(
    source_state_id: str,
    *,
    as_of: datetime,
) -> SourceStateV1:
    source = get_source_state(source_state_id)
    if not isinstance(as_of, datetime) or as_of.tzinfo is None:
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING, "as_of must be timezone-aware"
        )
    if source.effective_from:
        effective = datetime.fromisoformat(
            source.effective_from.replace("Z", "+00:00")
        ).astimezone(UTC)
        if as_of.astimezone(UTC) < effective:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_STALE,
                f"{source_state_id} is not effective at the requested time",
            )
    if (
        source.research_completeness_state
        is not ClaimBindingTerminalStateV1.COMPLETE_TERMINAL_EXACT_CLAIM_BINDING
        or source.primary_source_completeness_state
        is not PrimarySourceCompletenessV1.COMPLETE_PRIMARY_SOURCE
    ):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_STALE,
            f"{source_state_id} is not terminally currentized",
        )
    return source


def assert_source_precedence(states: tuple[SourceStateV1, ...]) -> None:
    if not states:
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING, "source set must be nonempty"
        )
    identities = [state.stable_source_identity for state in states]
    if len(identities) != len(set(identities)):
        raise SourcePolicyError(
            ReasonCode.SOURCE_CONFLICT, "duplicate stable source identity"
        )
    if any(
        state.conflict_resolution_state
        != "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE"
        for state in states
    ):
        raise SourcePolicyError(
            ReasonCode.SOURCE_CONFLICT,
            "source conflict resolution is not terminal",
        )


@dataclass(frozen=True, slots=True)
class ST12FSourceDecisionViewV1:
    decision_id: str
    stable_source_identity: str
    decision_class: str
    terminal_state: str
    runtime_provider_access_authorized: bool = False
    repository_dependency_change_authorized: bool = False

    def __post_init__(self) -> None:
        if (
            not self.decision_id
            or not self.stable_source_identity
            or self.decision_class not in {"CERTIFIED_STEP12_CURRENTIZATION", "ST12F_CURRENT_MAIN_OVERLAY"}
            or self.terminal_state != "COMPLETE_TERMINAL_SOURCE_DECISION"
            or self.runtime_provider_access_authorized
            or self.repository_dependency_change_authorized
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_CONFLICT,
                "ST12-F source decision is not terminal and no-effect",
            )


@dataclass(frozen=True, slots=True)
class ST12FSourceConflictResolutionV1:
    conflict_id: str
    subject: str
    resolution: str
    controlling_current_direct_value: str
    terminal_state: str = "COMPLETE_TERMINAL_CONFLICT_RESOLUTION"
    codex_resolution_allowed: bool = False

    def __post_init__(self) -> None:
        if (
            not self.conflict_id
            or not self.subject
            or not self.resolution
            or not self.controlling_current_direct_value
            or self.terminal_state != "COMPLETE_TERMINAL_CONFLICT_RESOLUTION"
            or self.codex_resolution_allowed
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_CONFLICT,
                "source conflict must preserve exact terminal owner resolution",
            )


_ST12F_SOURCE_OVERLAY_ROWS_V1 = (
    ("ST12F-CURR::POLYMARKET-GLOBAL-FEES", "VENUE::POLYMARKET_GLOBAL::CURRENT_DYNAMIC_MARKET_FEE_RECEIPT"),
    ("ST12F-CURR::POLYMARKET-US-FEES", "VENUE::POLYMARKET_US::CURRENT_SEPARATE_JURISDICTIONAL_FEE_EPOCH"),
    ("ST12F-CURR::POLYMARKET-FEE-RATE-ENDPOINT", "VENUE::POLYMARKET_GLOBAL::TOKEN_FEE_RATE_ENDPOINT"),
    ("ST12F-CURR::POLYMARKET-RATE-LIMITS", "VENUE::POLYMARKET_GLOBAL::ENDPOINT_KEYED_RATE_LIMITS"),
    ("ST12F-CURR::POLYMARKET-BUILDER-FEES", "VENUE::POLYMARKET_GLOBAL::BUILDER_FEE_PROFILE"),
    ("ST12F-CURR::POLYMARKET-PYTHON-SDK", "LIBRARY::POLYMARKET_PYTHON_SDK::PUBLIC_RELEASE_SURFACE"),
)
ST12F_SOURCE_DECISIONS_V1 = tuple(
    ST12FSourceDecisionViewV1(
        decision_id=state.source_state_id,
        stable_source_identity=state.stable_source_identity,
        decision_class="CERTIFIED_STEP12_CURRENTIZATION",
        terminal_state="COMPLETE_TERMINAL_SOURCE_DECISION",
    )
    for state in CERTIFIED_SOURCE_STATES
) + tuple(
    ST12FSourceDecisionViewV1(
        decision_id=decision_id,
        stable_source_identity=identity,
        decision_class="ST12F_CURRENT_MAIN_OVERLAY",
        terminal_state="COMPLETE_TERMINAL_SOURCE_DECISION",
    )
    for decision_id, identity in _ST12F_SOURCE_OVERLAY_ROWS_V1
)
ST12F_SOURCE_DECISION_BY_ID_V1: Mapping[str, ST12FSourceDecisionViewV1] = MappingProxyType(
    {row.decision_id: row for row in ST12F_SOURCE_DECISIONS_V1}
)

_ST12F_SOURCE_CONFLICT_ROWS_V1 = (
    ("ST12-R2-CONFLICT-001", "Polymarket Global Sports fee and rebate", "CURRENT_DIRECT_OFFICIAL_PAGE_WINS", "SPORTS_FEE_0.05_REBATE_15PCT"),
    ("ST12-R2-CONFLICT-002", "OTLP document versus protocol schema release", "SEPARATE_DOCUMENT_AND_PROTOCOL_PACKAGE_FIELDS_CURRENT_DIRECT_SOURCES_WIN", "OTLP_DOC_1.11_PROTO_1.10"),
    ("ST12-R2-CONFLICT-003", "Polymarket US versus Global fee semantics", "NO_CROSS_VENUE_GENERALIZATION", "SEPARATE_VENUE_SCOPED_RULES"),
    ("ST12-R2-CONFLICT-004", "pandas current release observation", "CURRENT_RELEASE_OBSERVED_WITHOUT_REPOSITORY_PIN_OR_INSTALL_AUTHORITY", "3.0.5_CURRENT_EXTERNAL_OBSERVATION_3.0.4_YANKED_REPOSITORY_PIN_UNCHANGED"),
    ("ST12-R2-CONFLICT-005", "Qiskit Optimization 0.7.0", "ISOLATED_NONLIVE_COMPATIBILITY_ADAPTER_WITH_MIGRATION_RISK", "NO_LONGER_OFFICIALLY_SUPPORTED_BY_IBM"),
    ("ST12-R2-CONFLICT-006", "Qiskit core current release", "CURRENT_EXTERNAL_RELEASE_OBSERVATION_ONLY", "2.5.1_RELEASED_2026_07_23_NO_REPOSITORY_PIN_CHANGE"),
    ("ST12-R2-CONFLICT-008", "Polymarket unified Python SDK stable release versus beta or legacy-only client representation", "CURRENT_DIRECT_STABLE_RELEASE_AND_EXACT_COMPATIBILITY_ROLE_WIN_NO_AUTO_MIGRATION", "polymarket-client_0.1.0_PRIMARY_OBSERVATION; py-clob-client-v2_1.1.0_COMPATIBILITY_ADAPTER"),
)
ST12F_SOURCE_CONFLICT_RESOLUTIONS_V1 = tuple(
    ST12FSourceConflictResolutionV1(*row) for row in _ST12F_SOURCE_CONFLICT_ROWS_V1
)

if (
    len(ST12F_SOURCE_DECISIONS_V1) != 35
    or len(ST12F_SOURCE_DECISION_BY_ID_V1) != 35
    or len(ST12F_SOURCE_CONFLICT_RESOLUTIONS_V1) != 7
):
    raise SourcePolicyError(
        ReasonCode.SOURCE_CONFLICT,
        "ST12-F source closure must remain exact 35 decisions and seven conflicts",
    )


def _st12h_source_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            f"{field_name} must be canonical nonempty text",
        )
    return value


@dataclass(frozen=True, slots=True)
class ST12HSourceBindingV1:
    source_id: str
    source_name: str
    source_class: str
    authority_class: str
    source_locator: str
    publication_or_version: str
    observed_at: date
    currentness_state: str
    rights_state: str
    recheck_trigger: str
    codex_research_required: bool

    def __post_init__(self) -> None:
        for field_name in (
            "source_id",
            "source_name",
            "source_class",
            "authority_class",
            "source_locator",
            "publication_or_version",
            "currentness_state",
            "rights_state",
            "recheck_trigger",
        ):
            _st12h_source_text(getattr(self, field_name), field_name=field_name)
        if type(self.observed_at) is not date:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "observed_at must be an exact date",
            )
        if self.codex_research_required is not False:
            raise SourcePolicyError(
                ReasonCode.CAPABILITY_DENIED,
                "ST12-H does not authorize Codex research",
            )


@dataclass(frozen=True, slots=True)
class ST12HSourceCurrentizationRuleV1:
    rule_id: str
    source_id: str
    mutable_fact_class: str
    recheck_action: str
    stale_behavior: str
    conflict_behavior: str
    online_research_allowed_to_codex: bool

    def __post_init__(self) -> None:
        for field_name in (
            "rule_id",
            "source_id",
            "mutable_fact_class",
            "recheck_action",
            "stale_behavior",
            "conflict_behavior",
        ):
            _st12h_source_text(getattr(self, field_name), field_name=field_name)
        if self.online_research_allowed_to_codex is not False:
            raise SourcePolicyError(
                ReasonCode.CAPABILITY_DENIED,
                "ST12-H source currentization is owner-supplied and offline",
            )


_ST12H_SOURCE_ROWS = (
    (
        "ST12H-V8-SRC::01",
        "QTT Master Plan v10.0.4",
        "OWNER_SUPPLIED_CONTROLLING_DOCUMENT",
        "OWNER_ARCHITECTURE_AUTHORITY",
        "uploaded:QTT_MasterPlan_Current_v10_0_4.md",
        "10.0.4",
        "STABLE_ARCHITECTURE_CONTROLLING_CURRENT_REPOSITORY_OUTRANKS_DATED_PROGRESS",
        "OWNER_SUPPLIED_INTERNAL_USE",
        "PERMANENT_ARCHITECTURE_CHANGE_ONLY",
    ),
    (
        "ST12H-V8-SRC::02",
        "QTT Current Canonical Implementation Roadmap v10.0",
        "OWNER_SUPPLIED_STABLE_ROADMAP_CANDIDATE",
        "OWNER_STABLE_ROADMAP_LAW_AUTHORITY",
        "uploaded:QTT_Current_Canonical_Implementation_Roadmap_v10_0.md",
        "10.0",
        "STABLE_LAWS_ACCEPTED_DATED_FRONTIER_SUPERSEDED",
        "OWNER_SUPPLIED_INTERNAL_USE",
        "PERMANENT_ROADMAP_CHANGE_ONLY",
    ),
    (
        "ST12H-V8-SRC::03",
        "Certified Step-12 owner package H payload",
        "CERTIFIED_HISTORICAL_BASELINE",
        "HISTORICAL_PROVENANCE_ONLY",
        "uploaded:QTT_FINAL_Step12_Complete_Owner_Package_v1_2R4_CURRENTIZED_REPAIRED_COMPLETE_CERTIFIED.zip",
        "v1.2R4",
        "DENOMINATORS_AND_REQUIREMENT_INVENTORY_ACCEPTED_PATH_ACTIONS_REQUIRE_CURRENT_MAIN_RECONCILIATION",
        "OWNER_SUPPLIED_INTERNAL_USE",
        "CURRENT_MAIN_OWNER_OR_PATH_CHANGE",
    ),
    (
        "ST12H-V8-SRC::04",
        "Post-ST12-G complete handoff",
        "OWNER_SUPPLIED_MUTABLE_STATE_HANDOFF",
        "OWNER_GATE_STATE_PROVENANCE",
        "uploaded:QTT_Post_ST12G_NewChat_Complete_Handoff_v1_0.md",
        "1.0",
        "STARTING_STATE_REVERIFIED_REMOTE_LOCAL_FACTS_REQUIRE_PHASE0",
        "OWNER_SUPPLIED_INTERNAL_USE",
        "BEFORE_EVERY_OWNER_OR_CODEX_GATE",
    ),
    (
        "ST12H-V8-SRC::05",
        "Current GitHub main owner topology",
        "CURRENT_REPOSITORY_IMPLEMENTATION",
        "CURRENT_REPOSITORY_IMPLEMENTATION_AUTHORITY",
        "https://github.com/Q8Meow/QTT_New0526/tree/main",
        "CURRENT_GIT_TRACKED_OWNER_RECHECK_REQUIRED",
        "REMOTE_CURRENT_AT_OWNER_PACKAGE_FREEZE",
        "PUBLIC_REPOSITORY_REFERENCE",
        "CODEX_PHASE0_PREPUSH_PREMERGE",
    ),
    (
        "ST12H-V8-SRC::06",
        "Current QTT validation workflow",
        "CURRENT_REPOSITORY_IMPLEMENTATION",
        "CURRENT_REPOSITORY_IMPLEMENTATION_AUTHORITY",
        "https://github.com/Q8Meow/QTT_New0526/blob/main/.github/workflows/qtt_validation.yml",
        "CURRENT_WORKFLOW_CONTENT_RECHECK_REQUIRED",
        "CURRENT_REQUIRES_H_ENVIRONMENT_PIN_CURRENTIZATION",
        "PUBLIC_REPOSITORY_REFERENCE",
        "WORKFLOW_CHANGE_OR_PREMERGE",
    ),
    (
        "ST12H-V8-SRC::07",
        "CPython 3.14.6 release",
        "OFFICIAL_PRIMARY_DEPENDENCY_SOURCE",
        "OFFICIAL_PRIMARY_VERSION_AUTHORITY",
        "https://www.python.org/downloads/release/python-3146/",
        "3.14.6",
        "PINNED_CLEAN_CI_AUTHORITATIVE",
        "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY",
        "WORKFLOW_RUNTIME_PIN_CHANGE",
    ),
    (
        "ST12H-V8-SRC::08",
        "pytest 9.1.1 release",
        "OFFICIAL_PRIMARY_DEPENDENCY_SOURCE",
        "OFFICIAL_PRIMARY_VERSION_AUTHORITY",
        "https://pypi.org/project/pytest/9.1.1/",
        "9.1.1",
        "PINNED_CLEAN_CI_AUTHORITATIVE",
        "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY",
        "WORKFLOW_DEPENDENCY_PIN_CHANGE",
    ),
    (
        "ST12H-V8-SRC::09",
        "Current ReasonCode, NoEffectFlags and validation owners",
        "CURRENT_REPOSITORY_IMPLEMENTATION",
        "CURRENT_REPOSITORY_IMPLEMENTATION_AUTHORITY",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/{errors.py,models.py,validation.py}",
        "CURRENT_GIT_TRACKED_OWNER_RECHECK_REQUIRED",
        "CURRENT_EXACT_CODE_OWNER",
        "PUBLIC_REPOSITORY_REFERENCE",
        "REASON_CODE_MODEL_OR_VALIDATION_OWNER_CHANGE",
    ),
)

ST12H_SOURCE_BINDINGS = tuple(
    ST12HSourceBindingV1(
        source_id=source_id,
        source_name=source_name,
        source_class=source_class,
        authority_class=authority_class,
        source_locator=source_locator,
        publication_or_version=publication_or_version,
        observed_at=date(2026, 8, 15),
        currentness_state=currentness_state,
        rights_state=rights_state,
        recheck_trigger=recheck_trigger,
        codex_research_required=False,
    )
    for (
        source_id,
        source_name,
        source_class,
        authority_class,
        source_locator,
        publication_or_version,
        currentness_state,
        rights_state,
        recheck_trigger,
    ) in _ST12H_SOURCE_ROWS
)

_ST12H_MUTABLE_FACT_CLASSES = (
    "PERMANENT_ARCHITECTURE",
    "PERMANENT_ROADMAP_LAWS",
    "CURRENT_MAIN_OWNER_OR_PATH",
    "OWNER_OR_CODEX_GATE_STATE",
    "REMOTE_CURRENT_MAIN",
    "VALIDATION_WORKFLOW",
    "WORKFLOW_RUNTIME_PIN",
    "WORKFLOW_DEPENDENCY_PIN",
    "REASON_CODE_MODEL_OR_VALIDATION_OWNER",
)

ST12H_SOURCE_CURRENTIZATION_RULES = tuple(
    ST12HSourceCurrentizationRuleV1(
        rule_id=f"ST12H-SOURCE-CURRENTIZATION::{index:02d}",
        source_id=binding.source_id,
        mutable_fact_class=mutable_fact_class,
        recheck_action=binding.recheck_trigger,
        stale_behavior="REJECT_STALE_MUTABLE_FACT",
        conflict_behavior="REJECT_SOURCE_CONFLICT",
        online_research_allowed_to_codex=False,
    )
    for index, (binding, mutable_fact_class) in enumerate(
        zip(ST12H_SOURCE_BINDINGS, _ST12H_MUTABLE_FACT_CLASSES, strict=True),
        start=1,
    )
)

_ST12H_RIGHTS_STATES = frozenset(
    {
        "OWNER_SUPPLIED_INTERNAL_USE",
        "PUBLIC_REPOSITORY_REFERENCE",
        "OFFICIAL_PUBLIC_DOCUMENTATION_REFERENCE_ONLY",
    }
)


@dataclass(frozen=True, slots=True)
class _ST12HSourceCurrentnessReceiptV1:
    source_id: str
    evaluated_at: date
    valid_until: date | None
    stability_class: str
    evidence_refs: tuple[str, ...]
    terminal_state: str


def _st12h_repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


_ST12H_MUTABLE_SOURCE_IDS = frozenset(
    {
        "ST12H-V8-SRC::04",
        "ST12H-V8-SRC::05",
        "ST12H-V8-SRC::06",
        "ST12H-V8-SRC::09",
    }
)
_ST12H_STABLE_SOURCE_IDS = frozenset(
    {"ST12H-V8-SRC::01", "ST12H-V8-SRC::02", "ST12H-V8-SRC::07", "ST12H-V8-SRC::08"}
)
_ST12H_SOURCE_DISPOSITION_BY_ID: Mapping[str, str] = MappingProxyType(
    {
        "ST12H-V8-SRC::01": "CURRENT_BY_STABLE_VERSION",
        "ST12H-V8-SRC::02": "CURRENT_BY_STABLE_VERSION",
        "ST12H-V8-SRC::03": "PROVENANCE_ONLY_PINNED",
        "ST12H-V8-SRC::04": "SUPERSEDED_BY_CURRENT_REPOSITORY_CUSTODY",
        "ST12H-V8-SRC::05": "CURRENT_BY_TRACKED_REPOSITORY_RECHECK",
        "ST12H-V8-SRC::06": "CURRENT_BY_TRACKED_REPOSITORY_RECHECK",
        "ST12H-V8-SRC::07": "CURRENT_BY_STABLE_VERSION",
        "ST12H-V8-SRC::08": "CURRENT_BY_STABLE_VERSION",
        "ST12H-V8-SRC::09": "CURRENT_BY_TRACKED_REPOSITORY_RECHECK",
    }
)


def _st12h_source_evidence_ref(binding: ST12HSourceBindingV1) -> str:
    return f"ST12H-SOURCE-EVIDENCE::{binding.source_id}"


def _st12h_parse_tracked_python_owner(repo_root: Path, path: str) -> ast.Module:
    try:
        source = (repo_root / path).read_text(encoding="utf-8")
        return ast.parse(source, filename=path)
    except (OSError, SyntaxError) as exc:
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            f"tracked source owner is unavailable or invalid: {path}",
        ) from exc


def _st12h_module_symbol_kinds(tree: ast.Module) -> Mapping[str, str]:
    symbols: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols[node.name] = "FUNCTION"
        elif isinstance(node, ast.ClassDef):
            symbols[node.name] = "CLASS"
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                if isinstance(target, ast.Name):
                    symbols[target.id] = "VALUE"
    return MappingProxyType(symbols)


def _st12h_validate_repository_topology(repo_root: Path) -> tuple[str, ...]:
    validation_path = (
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py"
    )
    runner_path = "tools/run_validation_gates.py"
    validation_tree = _st12h_parse_tracked_python_owner(repo_root, validation_path)
    runner_tree = _st12h_parse_tracked_python_owner(repo_root, runner_path)
    validation_symbols = _st12h_module_symbol_kinds(validation_tree)
    runner_symbols = _st12h_module_symbol_kinds(runner_tree)
    imported_scope_owner = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "tools.validation_scope_registry"
        and any(alias.name == "build_st12h_validation_commands" for alias in node.names)
        for node in runner_tree.body
    )
    if (
        validation_symbols.get("ST12H_CONTROL_CASES") != "VALUE"
        or validation_symbols.get("ST12H_EXECUTABLE_CONTROL_ADAPTERS") != "VALUE"
        or validation_symbols.get("validate_st12h_control_case_v1") != "FUNCTION"
        or runner_symbols.get("_execution_command_with_qku_root_importlib") != "FUNCTION"
        or not imported_scope_owner
    ):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_STALE,
            "current tracked repository owner topology recheck failed",
        )
    return (validation_path, runner_path)


def _st12h_workflow_contract_state(workflow_path: Path) -> Mapping[str, object]:
    try:
        text = workflow_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            "current validation workflow is unavailable",
        ) from exc
    if len(text.encode("utf-8")) > 256 * 1024:
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_STALE,
            "current validation workflow exceeds the bounded contract parser limit",
        )
    setup_actions: list[str] = []
    python_versions: list[str] = []
    pytest_installs: list[str] = []
    phases: list[str] = []
    aggregate_needs: list[str] = []
    in_validation_job = False
    in_needs = False
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent == 2 and stripped.endswith(":"):
            in_validation_job = stripped == "validation:"
            in_needs = False
        elif in_validation_job and indent == 4 and stripped == "needs:":
            in_needs = True
        elif in_validation_job and indent <= 4 and stripped and stripped != "needs:":
            in_needs = False
        if stripped.startswith("uses: actions/setup-python@"):
            setup_actions.append(stripped.removeprefix("uses: "))
        elif stripped.startswith("python-version:"):
            python_versions.append(
                stripped.partition(":")[2].strip().strip("'\"")
            )
        elif stripped == "python -m pip install pytest==9.1.1":
            pytest_installs.append(stripped)
        elif stripped.startswith("- phase:"):
            phases.append(stripped.partition(":")[2].strip())
        elif in_validation_job and in_needs and stripped.startswith("- "):
            aggregate_needs.append(stripped.removeprefix("- ").strip())
    return MappingProxyType(
        {
            "setup_actions": tuple(setup_actions),
            "python_versions": tuple(python_versions),
            "pytest_installs": tuple(pytest_installs),
            "phases": tuple(phases),
            "aggregate_needs": tuple(aggregate_needs),
        }
    )


def _st12h_validate_workflow_contract(repo_root: Path) -> tuple[str, ...]:
    workflow_path = ".github/workflows/qtt_validation.yml"
    state = _st12h_workflow_contract_state(repo_root / workflow_path)
    if (
        state["setup_actions"] != ("actions/setup-python@v5", "actions/setup-python@v5")
        or state["python_versions"] != ("3.14.6", "3.14.6")
        or state["pytest_installs"] != ("python -m pip install pytest==9.1.1",)
        or len(state["phases"]) != 13
        or state["aggregate_needs"] != ("validation_shards",)
    ):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_STALE,
            "current validation workflow differs from the exact H workflow contract",
        )
    return (workflow_path,)


def _st12h_validate_reason_model_and_validation_owners(
    repo_root: Path,
) -> tuple[str, ...]:
    paths = (
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/errors.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py",
    )
    errors_tree, models_tree, validation_tree = tuple(
        _st12h_parse_tracked_python_owner(repo_root, path) for path in paths
    )
    reason_class = next(
        (node for node in errors_tree.body if isinstance(node, ast.ClassDef) and node.name == "ReasonCode"),
        None,
    )
    reason_values: dict[str, object] = {}
    if reason_class is not None:
        for node in reason_class.body:
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Constant)
            ):
                reason_values[node.targets[0].id] = node.value.value
    no_effect_class = next(
        (node for node in models_tree.body if isinstance(node, ast.ClassDef) and node.name == "NoEffectFlagsV1"),
        None,
    )
    no_effect_fields = {
        node.target.id: node.value.value
        for node in (() if no_effect_class is None else no_effect_class.body)
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and isinstance(node.value, ast.Constant)
    }
    required_no_effect_fields = {
        "provider_connection_allowed",
        "private_state_read_allowed",
        "replay_or_paper_execution_allowed",
        "llm_inference_allowed",
        "qpu_execution_allowed",
        "mode_or_allow_activation_allowed",
        "order_release_allowed",
        "capital_mutation_allowed",
    }
    validation_symbols = _st12h_module_symbol_kinds(validation_tree)
    if (
        reason_values.get("KILL_OR_SUBMIT_DISABLED")
        != "ST12D_KILL_OR_SUBMIT_DISABLED"
        or reason_values.get("CONTEXT_SCOPE_MISMATCH")
        != "ST12E_CONTEXT_SCOPE_MISMATCH"
        or set(no_effect_fields) != required_no_effect_fields
        or any(value is not False for value in no_effect_fields.values())
        or validation_symbols.get("validate_st12h_control_case_v1") != "FUNCTION"
        or validation_symbols.get("validate_st12h_parameter_consumption_v1") != "FUNCTION"
    ):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_STALE,
            "current reason, no-effect, or validation owner recheck failed",
        )
    return paths


def _st12h_mutable_source_recheck(
    binding: ST12HSourceBindingV1,
    *,
    repo_root: Path,
) -> tuple[str, ...]:
    if binding.source_id in {"ST12H-V8-SRC::04", "ST12H-V8-SRC::05"}:
        return (*_st12h_validate_repository_topology(repo_root), _st12h_source_evidence_ref(binding))
    if binding.source_id == "ST12H-V8-SRC::06":
        return (*_st12h_validate_workflow_contract(repo_root), _st12h_source_evidence_ref(binding))
    if binding.source_id == "ST12H-V8-SRC::09":
        return (
            *_st12h_validate_reason_model_and_validation_owners(repo_root),
            _st12h_source_evidence_ref(binding),
        )
    raise SourcePolicyError(
        ReasonCode.SOURCE_CONFLICT,
        f"mutable source has no exact tracked recheck owner: {binding.source_id}",
    )


def _observe_st12h_source_binding_v1(
    binding: ST12HSourceBindingV1,
    *,
    evaluated_at: date,
    repo_root: Path | None = None,
) -> _ST12HSourceCurrentnessReceiptV1:
    if not isinstance(binding, ST12HSourceBindingV1) or type(evaluated_at) is not date:
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            "ST12-H source validation requires an exact binding and date",
        )
    if not binding.source_locator:
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            "ST12-H source locator is missing",
        )
    if binding.rights_state not in _ST12H_RIGHTS_STATES:
        raise SourcePolicyError(
            ReasonCode.SOURCE_RIGHTS_BLOCKED,
            "ST12-H source rights are unknown",
        )
    if binding.observed_at > evaluated_at:
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_STALE,
            "ST12-H source observation is in the future",
        )
    disposition = _ST12H_SOURCE_DISPOSITION_BY_ID.get(binding.source_id)
    if disposition is None:
        raise SourcePolicyError(
            ReasonCode.SOURCE_CONFLICT,
            "ST12-H source has no exact currentness disposition",
        )
    if binding.source_id == "ST12H-V8-SRC::03":
        if (
            binding.source_class != "CERTIFIED_HISTORICAL_BASELINE"
            or binding.authority_class != "HISTORICAL_PROVENANCE_ONLY"
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_CONFLICT,
                "historical ST12-H provenance cannot become current implementation truth",
            )
        evidence_refs = (
            binding.source_locator,
            binding.publication_or_version,
            _st12h_source_evidence_ref(binding),
        )
        stability_class = "PINNED_PROVENANCE"
        valid_until = None
    elif binding.source_id in _ST12H_STABLE_SOURCE_IDS:
        if not binding.publication_or_version:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "stable source requires an exact version",
            )
        evidence_refs = (
            binding.source_locator,
            binding.publication_or_version,
            _st12h_source_evidence_ref(binding),
        )
        stability_class = "STABLE_VERSION"
        valid_until = None
    elif binding.source_id in _ST12H_MUTABLE_SOURCE_IDS:
        evidence_refs = _st12h_mutable_source_recheck(
            binding,
            repo_root=repo_root or _st12h_repository_root(),
        )
        stability_class = "MUTABLE_RECHECK"
        valid_until = evaluated_at
    else:
        raise SourcePolicyError(
            ReasonCode.SOURCE_CONFLICT,
            "ST12-H source currentness class is not exact",
        )
    return _ST12HSourceCurrentnessReceiptV1(
        source_id=binding.source_id,
        evaluated_at=evaluated_at,
        valid_until=valid_until,
        stability_class=stability_class,
        evidence_refs=evidence_refs,
        terminal_state=disposition,
    )


def validate_st12h_source_binding_v1(
    binding: ST12HSourceBindingV1,
    *,
    evaluated_at: date,
) -> None:
    _observe_st12h_source_binding_v1(binding, evaluated_at=evaluated_at)


def _validate_st12h_source_currentness_receipt_v1(
    receipt: _ST12HSourceCurrentnessReceiptV1,
    *,
    evaluated_at: date,
) -> None:
    if (
        type(receipt) is not _ST12HSourceCurrentnessReceiptV1
        or type(evaluated_at) is not date
    ):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            "source currentness requires one exact observed receipt and date",
        )
    expected_disposition = _ST12H_SOURCE_DISPOSITION_BY_ID.get(receipt.source_id)
    if receipt.terminal_state != expected_disposition:
        raise SourcePolicyError(
            ReasonCode.SOURCE_CONFLICT,
            "source currentness receipt has an unknown terminal state",
        )
    if receipt.stability_class == "MUTABLE_RECHECK":
        if (
            receipt.source_id not in _ST12H_MUTABLE_SOURCE_IDS
            or receipt.valid_until != receipt.evaluated_at
            or not receipt.evidence_refs
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_STALE,
                "mutable source currentness requires a same-evaluation offline recheck receipt",
            )
    elif receipt.stability_class == "STABLE_VERSION":
        if (
            receipt.source_id not in _ST12H_STABLE_SOURCE_IDS
            or receipt.valid_until is not None
            or not receipt.evidence_refs
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_CONFLICT,
                "stable source currentness requires its exact version-basis receipt",
            )
    elif receipt.stability_class == "PINNED_PROVENANCE":
        if (
            receipt.source_id != "ST12H-V8-SRC::03"
            or receipt.terminal_state != "PROVENANCE_ONLY_PINNED"
            or receipt.valid_until is not None
            or not receipt.evidence_refs
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_CONFLICT,
                "pinned provenance requires an exact non-current receipt",
            )
    else:
        raise SourcePolicyError(
            ReasonCode.SOURCE_CONFLICT,
            "source currentness receipt has an unknown stability class",
        )
    if receipt.valid_until is not None and evaluated_at > receipt.valid_until:
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_STALE,
            f"source currentness receipt expired: {receipt.source_id}",
        )


if (
    len(ST12H_SOURCE_BINDINGS) != 9
    or len(ST12H_SOURCE_CURRENTIZATION_RULES) != 9
    or tuple(row.source_id for row in ST12H_SOURCE_BINDINGS)
    != tuple(f"ST12H-V8-SRC::{index:02d}" for index in range(1, 10))
):
    raise SourcePolicyError(
        ReasonCode.SOURCE_CONFLICT,
        "ST12-H source closure must remain exact and ordered",
    )


# Unadmitted native Series candidates; no source or account acceptance is implied.
@dataclass(frozen=True, slots=True)
class KalshiQuadraticSeriesFeeCandidateV1:
    """Unadmitted Series fee fields; not current source or account evidence."""

    series_ticker: str
    fee_multiplier: Decimal

    def __post_init__(self) -> None:
        _native_ident(self.series_ticker)
        _native_bounded_decimal(self.fee_multiplier)
        _native_require(self.fee_multiplier >= 0, "NONNEGATIVE")


def _kalshi_scheduled_utc_v1(value: datetime) -> datetime:
    _native_require(type(value) is datetime and value.tzinfo is UTC, "SCHEDULED_UTC")
    return value


def _kalshi_scheduled_clocks_v1(clocks: PointInTimeClocksV1) -> PointInTimeClocksV1:
    _native_require(type(clocks) is PointInTimeClocksV1, "SCHEDULED_CLOCKS")
    try:
        values = {name: getattr(clocks, name) for name in PointInTimePolicyV1.CHECKED_CLOCKS}
    except AttributeError as error:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "SCHEDULED_CLOCK_FIELDS") from error
    return PointInTimeClocksV1(**{name: _kalshi_scheduled_utc_v1(value) for name, value in values.items()})


@dataclass(frozen=True, slots=True)
class KalshiScheduledFeeStateV1:
    """One unadmitted hypothetical interval; never source or account evidence."""

    state_ref: str
    scope_kind: str
    series_ticker: str
    event_ticker: str | None
    clocks: PointInTimeClocksV1
    effective_until_utc: datetime
    fee_type: str | None
    fee_multiplier: Decimal | None

    def __post_init__(self) -> None:
        _native_ident(self.state_ref)
        _native_ident(self.series_ticker)
        _native_require(type(self.scope_kind) is str and self.scope_kind in ("SERIES", "EVENT"), "SCHEDULED_ROLE")
        if self.scope_kind == "SERIES":
            _native_require(self.event_ticker is None, "SCHEDULED_SERIES_SCOPE")
        else:
            _native_ident(self.event_ticker)
        if not (self.scope_kind == "EVENT" and self.fee_type is None and self.fee_multiplier is None):
            _native_require(type(self.fee_type) is str and self.fee_type == "quadratic", "SCHEDULED_FEE_PAIR")
            _native_require(self.fee_multiplier is not None, "SCHEDULED_FEE_PAIR")
            KalshiQuadraticSeriesFeeCandidateV1(self.series_ticker, self.fee_multiplier)
        clocks = _kalshi_scheduled_clocks_v1(self.clocks)
        end = _kalshi_scheduled_utc_v1(self.effective_until_utc)
        if clocks.effective_time >= end:
            raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, "SCHEDULED_INTERVAL_ORDER")
        object.__setattr__(self, "clocks", clocks)


def _kalshi_scheduled_context_v1(context: ComputationContextKeyV1) -> ComputationContextKeyV1:
    _native_require(type(context) is ComputationContextKeyV1, "SCHEDULED_CONTEXT")
    try:
        context_id, as_of, observed_at, epoch, version, age = (
            context.context_id, context.as_of, context.observed_at,
            context.source_epoch_id, context.input_version, context.maximum_age,
        )
    except AttributeError as error:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "SCHEDULED_CONTEXT_FIELDS") from error
    _native_ident(context_id)
    _native_ident(epoch)
    _native_ident(version)
    _kalshi_scheduled_utc_v1(as_of)
    _kalshi_scheduled_utc_v1(observed_at)
    _native_require(type(age) is timedelta and age > timedelta(0), "SCHEDULED_MAXIMUM_AGE")
    local = ComputationContextKeyV1(context_id, as_of, observed_at, epoch, version, age)
    local.assert_fresh()
    return local


def _kalshi_scheduled_state_snapshot_v1(row: KalshiScheduledFeeStateV1) -> KalshiScheduledFeeStateV1:
    _native_require(type(row) is KalshiScheduledFeeStateV1, "SCHEDULED_STATE")
    try:
        values = (row.state_ref, row.scope_kind, row.series_ticker, row.event_ticker,
                  row.clocks, row.effective_until_utc, row.fee_type, row.fee_multiplier)
    except AttributeError as error:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "SCHEDULED_STATE_FIELDS") from error
    return KalshiScheduledFeeStateV1(*values)


def resolve_kalshi_scheduled_fee_scenario_v1(
    *, context: ComputationContextKeyV1, expected_series_ticker: str,
    expected_event_ticker: str, states: tuple[KalshiScheduledFeeStateV1, ...],
    fill_times: tuple[datetime, ...],
) -> tuple[Decimal, ...]:
    """Resolve explicit known hypothetical states; grant no source/account admission.

    Both streams must cover each nondecreasing future fill. Local sorted intervals
    and monotone cursors bound the work to O(S log S + F), with O(S + F) memory.
    """
    _native_require(type(states) is tuple and 2 <= len(states) <= 4096, "SCHEDULED_STATES")
    _native_require(type(fill_times) is tuple and 1 <= len(fill_times) <= 4096, "SCHEDULED_FILL_TIMES")
    local_context = _kalshi_scheduled_context_v1(context)
    _native_ident(expected_series_ticker)
    _native_ident(expected_event_ticker)
    rows = tuple(_kalshi_scheduled_state_snapshot_v1(row) for row in states)
    _native_require(len({row.state_ref for row in rows}) == len(rows), "SCHEDULED_DUPLICATE_REF")
    for row in rows:
        if row.series_ticker != expected_series_ticker or (
            row.scope_kind == "EVENT" and row.event_ticker != expected_event_ticker
        ):
            raise ContractValidationError(ReasonCode.INPUT_SCOPE_MISMATCH, "SCHEDULED_SCOPE")
    for row in rows:
        PointInTimePolicyV1.validate(
            receipt_id=row.state_ref, field_class=PointInTimeFieldClassV1.SCHEDULED_EFFECTIVE_FACT,
            clocks=row.clocks, context=local_context,
        )
        if local_context.as_of - row.clocks.observed_time > local_context.maximum_age:
            raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, "SCHEDULED_ROW_AGE")
    streams = tuple(tuple(sorted(
        (row for row in rows if row.scope_kind == role),
        key=lambda row: (row.clocks.effective_time, row.effective_until_utc, row.state_ref),
    )) for role in ("SERIES", "EVENT"))
    for stream in streams:
        for previous, current in zip(stream, stream[1:]):
            if previous.effective_until_utc > current.clocks.effective_time:
                raise SourcePolicyError(ReasonCode.SOURCE_CONFLICT, "SCHEDULED_INTERVAL_CONFLICT")
    previous_time = local_context.as_of
    for moment in fill_times:
        _kalshi_scheduled_utc_v1(moment)
        if moment < previous_time:
            raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, "SCHEDULED_FILL_ORDER_OR_PAST")
        previous_time = moment
    cursors = [0, 0]
    selected = []
    for moment in fill_times:
        covering = []
        for index, stream in enumerate(streams):
            while cursors[index] < len(stream) and stream[cursors[index]].effective_until_utc <= moment:
                cursors[index] += 1
            if cursors[index] == len(stream) or stream[cursors[index]].clocks.effective_time > moment:
                raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "SCHEDULED_COVERAGE")
            covering.append(stream[cursors[index]])
        series, event = covering
        selected.append(series.fee_multiplier if event.fee_multiplier is None else event.fee_multiplier)
    return tuple(selected)


def decode_kalshi_quadratic_series_fee_candidate_v1(
    *, raw_response: bytes, expected_series_ticker: str,
) -> KalshiQuadraticSeriesFeeCandidateV1:
    """Project bounded caller bytes into unadmitted quadratic Series fee fields."""
    _native_ident(expected_series_ticker)
    decoded = _native_strict_json(raw_response)
    reject_secret_material("series_fee_response", decoded)
    if type(decoded) is not dict:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "Kalshi series fee response shape is invalid")
    if "series" not in decoded:
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "Kalshi series fee fields are missing")
    series = decoded["series"]
    if type(series) is not dict:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "Kalshi series fee response shape is invalid")
    if not {"ticker", "fee_type", "fee_multiplier"} <= series.keys():
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "Kalshi series fee fields are missing")
    ticker = _native_ident(series["ticker"])
    if ticker != expected_series_ticker:
        raise ContractValidationError(ReasonCode.INPUT_SCOPE_MISMATCH, "Kalshi series ticker does not match expected scope")
    if type(series["fee_type"]) is not str or series["fee_type"] != "quadratic":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "Kalshi fee family is outside the selected quadratic scope")
    multiplier = series["fee_multiplier"]
    if type(multiplier) not in (int, Decimal):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "Kalshi fee multiplier must be a JSON number")
    return KalshiQuadraticSeriesFeeCandidateV1(
        series_ticker=ticker,
        fee_multiplier=Decimal(multiplier) if type(multiplier) is int else multiplier,
    )


def decode_kalshi_market_linked_series_fee_candidate_v1(
    *, raw_market_response: bytes, raw_event_response: bytes,
    raw_series_response: bytes, expected_market_ticker: str,
) -> KalshiQuadraticSeriesFeeCandidateV1:
    """Join supplied identities for an unadmitted, hypothetical Series-base scenario."""
    _native_ident(expected_market_ticker)

    def identity_pair(raw, root, names, secret_field):
        decoded = _native_strict_json(raw)
        reject_secret_material(secret_field, decoded)
        if type(decoded) is not dict:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT, "Kalshi linked identity response shape is invalid",
            )
        if root not in decoded:
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT, "Kalshi linked identity fields are missing",
            )
        identity = decoded[root]
        if type(identity) is not dict:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT, "Kalshi linked identity response shape is invalid",
            )
        if not set(names) <= identity.keys():
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT, "Kalshi linked identity fields are missing",
            )
        return _native_ident(identity[names[0]]), _native_ident(identity[names[1]])

    market_ticker, market_event = identity_pair(
        raw_market_response, "market", ("ticker", "event_ticker"), "market_identity_response",
    )
    if market_ticker != expected_market_ticker:
        raise ContractValidationError(
            ReasonCode.INPUT_SCOPE_MISMATCH, "Kalshi market ticker does not match expected scope",
        )
    event_ticker, event_series = identity_pair(
        raw_event_response, "event", ("event_ticker", "series_ticker"), "event_identity_response",
    )
    if event_ticker != market_event:
        raise ContractValidationError(
            ReasonCode.INPUT_SCOPE_MISMATCH, "Kalshi event ticker does not match market linkage",
        )
    return decode_kalshi_quadratic_series_fee_candidate_v1(
        raw_response=raw_series_response, expected_series_ticker=event_series,
    )


# A dormant, process-local observation capability. Bootstrap admission remains
# external; neither these records nor synthetic receiver tests confer authority.
_KALSHI_OBSERVATION_BODY_LIMIT = 65_536


def _kalshi_observation_require(ok, token, reason=ReasonCode.INVALID_CONTRACT):
    if not ok:
        raise ContractValidationError(reason, token)


def _kalshi_observation_time(ok):
    if not ok:
        raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, "KALSHI_OBSERVATION_TIME")


def _kalshi_observation_counter(value):
    _kalshi_observation_time(type(value) is int and 0 <= value <= 2**63 - 1)
    return value


def _kalshi_observation_target(role, ticker):
    from urllib.parse import quote

    _native_ident(ticker)
    _kalshi_observation_require(
        type(role) is str and role in ("MARKET", "EVENT", "SERIES")
        and ticker not in (".", "..")
        and not (role in ("EVENT", "SERIES") and ticker == "fee_changes"),
        "KALSHI_OBSERVATION_FIELDS",
    )
    routes = {"MARKET": "markets", "EVENT": "events", "SERIES": "series"}
    return ("/trade-api/v2/" + routes[role] + "/"
            + quote(ticker, safe='', encoding='utf-8', errors='strict')
            + ("?exclude_markets=true" if role == "EVENT" else ""))


@dataclass(frozen=True, slots=True)
class KalshiFeeHttpObservationV1:
    """Original entity bytes and nominal local times; not a native receipt."""

    role: str
    request_target: str
    raw_body: bytes
    request_wall_ns: int
    request_monotonic_ns: int
    received_wall_ns: int
    received_monotonic_ns: int

    def __post_init__(self):
        _kalshi_observation_require(
            type(self.role) is str and self.role in ("MARKET", "EVENT", "SERIES")
            and type(self.request_target) is str,
            "KALSHI_OBSERVATION_FIELDS",
        )
        _kalshi_observation_require(
            type(self.raw_body) is bytes and 1 <= len(self.raw_body) <= _KALSHI_OBSERVATION_BODY_LIMIT,
            "KALSHI_OBSERVATION_HTTP",
        )
        for value in (self.request_wall_ns, self.request_monotonic_ns,
                      self.received_wall_ns, self.received_monotonic_ns):
            _kalshi_observation_counter(value)
        _kalshi_observation_time(self.request_wall_ns <= self.received_wall_ns
                                 and self.request_monotonic_ns <= self.received_monotonic_ns)


@dataclass(frozen=True, slots=True)
class KalshiObservedFeeCohortV1:
    """An observed hypothetical fee scenario, without effective-fee authority."""

    observations: tuple[KalshiFeeHttpObservationV1, ...]
    market_ticker: str
    event_ticker: str
    series_ticker: str
    fee_basis: str
    fee_multiplier: Decimal
    available_wall_ns: int
    available_monotonic_ns: int
    process_epoch_id: str
    monotonic_clock_id: str

    def __post_init__(self):
        for value in (self.market_ticker, self.event_ticker, self.series_ticker,
                      self.process_epoch_id, self.monotonic_clock_id):
            _native_ident(value)
        _kalshi_observation_require(
            type(self.observations) is tuple and len(self.observations) == 3
            and all(type(row) is KalshiFeeHttpObservationV1 for row in self.observations)
            and type(self.fee_basis) is str
            and self.fee_basis in ("OBSERVED_SERIES_BASE", "OBSERVED_EVENT_OVERRIDE"),
            "KALSHI_OBSERVATION_FIELDS",
        )
        KalshiQuadraticSeriesFeeCandidateV1(self.series_ticker, self.fee_multiplier)
        previous_wall = previous_mono = 0
        for row, role, ticker in zip(self.observations, ("MARKET", "EVENT", "SERIES"),
                                    (self.market_ticker, self.event_ticker, self.series_ticker), strict=True):
            _kalshi_observation_require(
                row.role == role and row.request_target == _kalshi_observation_target(role, ticker),
                "KALSHI_OBSERVATION_ASSOCIATION",
            )
            _kalshi_observation_time(previous_wall <= row.request_wall_ns
                                     and previous_mono <= row.request_monotonic_ns)
            previous_wall, previous_mono = row.received_wall_ns, row.received_monotonic_ns
        _kalshi_observation_counter(self.available_wall_ns)
        _kalshi_observation_counter(self.available_monotonic_ns)
        _kalshi_observation_time(previous_wall <= self.available_wall_ns
                                 and previous_mono <= self.available_monotonic_ns)


@dataclass(frozen=True, slots=True)
class _KalshiObservationConfigV1:
    owner: object
    source_receipt: PITSourceCurrentizationReceiptV1
    rights_receipt: PITRightsAdmissionReceiptV1
    account_scope: str
    internal_use_class: str
    permitted_retention_class: str
    expected_market_ticker: str
    process_epoch_id: str
    monotonic_clock_id: str
    operating_authorization_ref: str
    effective_expiry_wall_ns: int
    deadline_monotonic_ns: int
    source_use_binding: object = None


@dataclass(frozen=True, slots=True)
class _KalshiPreparedReadV1:
    owner: object
    originating_thread: object
    role: str
    ticker: str
    target: str
    headers: Mapping
    tls_context: object
    timeout_seconds: float
    maximum_raw_bytes: int


class KalshiFeeObservationOwnerV1:
    """One explicitly authorized capture and same-process scenario consumption.

    No factory or runtime registration activates this capability. The operating
    window fences publication, not the total duration of blocking network I/O.
    """

    def __init__(self, *, source_receipt: PITSourceCurrentizationReceiptV1,
                 rights_receipt: PITRightsAdmissionReceiptV1, account_scope: str,
                 internal_use_class: str, permitted_retention_class: str,
                 expected_market_ticker: str, process_epoch_id: str,
                 monotonic_clock_id: str, operating_authorization_ref: str,
                 authorization_expires_at_utc: datetime, deadline_monotonic_ns: int,
                 source_use_binding=None) -> None:
        _kalshi_observation_require(type(self) is KalshiFeeObservationOwnerV1
            and not hasattr(self, "_lock"), "KALSHI_OBSERVATION_STATE")
        self._lock = RLock()
        self._state = "NEW"
        self._last_clock = None
        self._pending = None
        self._issued_cohort = None
        self._attempts = 0
        self._expected_read = ("MARKET", expected_market_ticker)
        self._session_origin = None
        self._publication_route = None
        self._publication_cleanup = False
        try:
            if source_use_binding is not None:
                _kalshi_observation_require(type(source_use_binding) is KalshiSourceUseBindingV1,
                                            "KALSHI_OBSERVATION_ASSOCIATION")
                with self._lock:
                    source_use_binding._authority._claim_owner_v1(source_use_binding, self, (
                        source_receipt, rights_receipt, account_scope, internal_use_class, permitted_retention_class,
                        expected_market_ticker, process_epoch_id, monotonic_clock_id, operating_authorization_ref,
                        authorization_expires_at_utc, deadline_monotonic_ns))
            _kalshi_observation_require(type(source_receipt) is PITSourceCurrentizationReceiptV1
                and type(rights_receipt) is PITRightsAdmissionReceiptV1,
                "KALSHI_OBSERVATION_SCOPE")
            profile = Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT
            _kalshi_observation_require(
                source_receipt.profile_id is profile and rights_receipt.profile_id is profile
                and source_receipt.source_id == rights_receipt.source_id == "KALSHI_PUBLIC_MARKET_EVENT_SERIES"
                and source_receipt.source_contract_version == "KALSHI_PUBLIC_FEE_OBSERVATION_V1"
                and type(internal_use_class) is str
                and internal_use_class == rights_receipt.internal_use_class == "OBSERVED_FEE_SCENARIO_INTERNAL"
                and type(permitted_retention_class) is str
                and permitted_retention_class == rights_receipt.permitted_retention_class == "PROCESS_MEMORY_ONLY",
                "KALSHI_OBSERVATION_SCOPE",
            )
            for value in (expected_market_ticker, process_epoch_id, monotonic_clock_id,
                          operating_authorization_ref):
                _native_ident(value)
            _kalshi_observation_target("MARKET", expected_market_ticker)
            _kalshi_observation_time(type(authorization_expires_at_utc) is datetime
                and authorization_expires_at_utc.tzinfo is not None
                and authorization_expires_at_utc.utcoffset() == timedelta(0))
            _kalshi_observation_counter(deadline_monotonic_ns)
            wall, mono = self._observe_clock_v1()
            _kalshi_observation_time(mono < deadline_monotonic_ns <= mono + 60_000_000_000)
            admission = validate_pit_source_rights_admission_v1(
                source_receipt, rights_receipt, admission_id=operating_authorization_ref,
                profile_id=profile, account_scope=account_scope, internal_use_class=internal_use_class,
                permitted_retention_class=permitted_retention_class,
                evaluated_at_utc=self._wall_datetime_v1(wall))
            # Logical PIT admits factual age exactly 24h, but the observation
            # deadline is exclusive: at that endpoint no observation window remains.
            expiry = min(authorization_expires_at_utc, admission.valid_until_utc)
            expiry_ns = _native_utc_nanoseconds(expiry.isoformat())
            _kalshi_observation_time(wall < expiry_ns)
            self._config = _KalshiObservationConfigV1(
                self, source_receipt, rights_receipt, account_scope, internal_use_class,
                permitted_retention_class, expected_market_ticker, process_epoch_id,
                monotonic_clock_id, operating_authorization_ref, expiry_ns, deadline_monotonic_ns, source_use_binding)
        except BaseException:
            # A genuine first claim is consumed even when later constructor
            # validation fails. Never invalidate another owner's permit.
            if type(source_use_binding) is KalshiSourceUseBindingV1:
                authority = source_use_binding._authority
                with self._lock, authority._lock:
                    permit = source_use_binding._permit
                    if type(permit) is _SourceUseObservationPermitV1 and permit._owner is self:
                        permit._failed = True
                        if authority._active_permit is permit:
                            authority._active_permit = None
            self._invalidate_v1()
            raise

    @contextmanager
    def _authority_guard_v1(self):
        binding = self._config.source_use_binding
        _kalshi_observation_require(type(binding) is KalshiSourceUseBindingV1, "KALSHI_OBSERVATION_SOURCE_USE_REQUIRED")
        with binding._authority._lock:
            binding._authority._check_binding_v1(binding, self)
            yield

    def _bind_session_v1(self, session):
        with self._lock:
            _kalshi_observation_require(self._session_origin is None and self._state == "NEW", "KALSHI_OBSERVATION_STATE")
            if self._config.source_use_binding is not None:
                with self._authority_guard_v1():
                    permit = self._config.source_use_binding._permit
                    _kalshi_observation_require(permit._route is None, "KALSHI_OBSERVATION_STATE")
                    permit._route = "SESSION"
            self._session_origin = session

    def _check_inputs_v1(self, fills, balance_increment, prior_rounding_overpayment):
        with self._lock, self._authority_guard_v1():
            binding = self._config.source_use_binding
            binding._authority._check_binding_v1(binding, self,
                inputs=(fills, balance_increment, prior_rounding_overpayment))

    @contextmanager
    def _publication_fence_v1(self, *, cohort, expected_market_ticker, as_of_monotonic_ns,
                              fills, balance_increment, prior_rounding_overpayment, route):
        with self._lock, self._authority_guard_v1():
            binding = self._config.source_use_binding
            authority, permit, config = binding._authority, binding._permit, self._config
            inputs = (fills, balance_increment, prior_rounding_overpayment)
            authority._check_binding_v1(binding, self, inputs=inputs)
            self.resolve_scenario_multiplier(cohort=cohort, expected_market_ticker=expected_market_ticker,
                                             as_of_monotonic_ns=as_of_monotonic_ns)
            _kalshi_observation_require(self._publication_route is None
                and route in ("DIRECT", "SESSION_INTERNAL", "SESSION_FINAL"), "KALSHI_OBSERVATION_PUBLICATION")
            if route == "DIRECT":
                _kalshi_observation_require(self._session_origin is None and permit._route in (None, "DIRECT"),
                                            "KALSHI_OBSERVATION_PUBLICATION")
            else:
                session = self._session_origin
                _kalshi_observation_require(session is not None and permit._route == "SESSION"
                    and session._KalshiFeeScenarioSessionV1__origin is session
                    and session._KalshiFeeScenarioSessionV1__owner is self
                    and session._KalshiFeeScenarioSessionV1__state == "RUNNING", "KALSHI_OBSERVATION_PUBLICATION")
            self._publication_route = route
            self._publication_cleanup = False
            try:
                yield  # No guard object or arbitrary callback escapes this region.
                authority._check_binding_v1(binding, self, inputs=inputs)
                now = self._observe_clock_v1()
                _kalshi_observation_require(self._config is config and config.source_use_binding is binding
                    and permit._owner is self and self._publication_route == route,
                    "KALSHI_OBSERVATION_ASSOCIATION")
                _kalshi_observation_time(cohort.available_monotonic_ns <= as_of_monotonic_ns <= now[1]
                    and now[0] < config.effective_expiry_wall_ns and now[1] < config.deadline_monotonic_ns)
                if route == "SESSION_FINAL":
                    _kalshi_observation_require(self._publication_cleanup and self._state == "REVOKED"
                        and self._issued_cohort is None and self._pending is None
                        and self._session_origin is session and session._KalshiFeeScenarioSessionV1__owner is self
                        and session._KalshiFeeScenarioSessionV1__state == "CONSUMED", "KALSHI_OBSERVATION_PUBLICATION")
                else:
                    _kalshi_observation_require(self._state == "READY" and self._issued_cohort is cohort
                        and not self._publication_cleanup, "KALSHI_OBSERVATION_PUBLICATION")
                if route != "SESSION_INTERNAL":
                    permit._route = "DIRECT" if route == "DIRECT" else "SESSION"
                    permit._published = True
                    authority._active_permit = None
            except BaseException:
                permit._failed = True
                self._invalidate_v1()
                raise
            finally:
                self._publication_route = None
                self._publication_cleanup = False

    @staticmethod
    def _wall_datetime_v1(wall):
        seconds, nanos = divmod(wall, 1_000_000_000)
        return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds, microseconds=nanos // 1000)

    def _invalidate_v1(self):
        if self._state != "REVOKED":
            self._state = "FAILED"
        self._pending = None
        self._issued_cohort = None

    def _require_instance_v1(self):
        config = getattr(self, "_config", None)
        _kalshi_observation_require(type(self) is KalshiFeeObservationOwnerV1
            and type(config) is _KalshiObservationConfigV1 and config.owner is self,
            "KALSHI_OBSERVATION_ASSOCIATION")

    def _observe_clock_v1(self):
        with self._lock:
            try:
                before = _kalshi_observation_counter(time.monotonic_ns())
                wall = _kalshi_observation_counter(time.time_ns())
                after = _kalshi_observation_counter(time.monotonic_ns())
                _kalshi_observation_time(before <= after)
                if self._last_clock is not None:
                    _kalshi_observation_time(self._last_clock[0] <= wall and self._last_clock[1] <= before)
                self._last_clock = (wall, after)
                return self._last_clock
            except BaseException:
                self._invalidate_v1()
                raise

    def _check_operating_v1(self, clock):
        config = self._config
        _kalshi_observation_require(self._state in ("NEW", "CAPTURING", "READY"),
                                    "KALSHI_OBSERVATION_STATE")
        try:
            if config.source_use_binding is not None:
                with config.source_use_binding._authority._lock:
                    config.source_use_binding._authority._check_binding_v1(config.source_use_binding, self)
            validate_pit_source_rights_admission_v1(
                config.source_receipt, config.rights_receipt,
                admission_id=config.operating_authorization_ref,
                profile_id=Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT,
                account_scope=config.account_scope, internal_use_class=config.internal_use_class,
                permitted_retention_class=config.permitted_retention_class,
                evaluated_at_utc=self._wall_datetime_v1(clock[0]))
            _kalshi_observation_time(clock[0] < config.effective_expiry_wall_ns
                                     and clock[1] < config.deadline_monotonic_ns)
        except BaseException:
            self._invalidate_v1()
            raise

    def _require_pending_v1(self, prepared, *, charged):
        from threading import current_thread

        _kalshi_observation_require(self._state == "CAPTURING", "KALSHI_OBSERVATION_STATE")
        _kalshi_observation_require(
            type(prepared) is _KalshiPreparedReadV1 and prepared.owner is self
            and prepared.originating_thread is current_thread()
            and self._pending is not None and self._pending[0] is prepared
            and (self._pending[1] is not None) is charged,
            "KALSHI_OBSERVATION_ASSOCIATION")

    def _prepare_read_v1(self, role, ticker):
        import ssl
        from threading import current_thread

        with self._lock, self._authority_guard_v1():
            _kalshi_observation_require(self._state == "CAPTURING" and self._pending is None
                and self._attempts < 3 and (role, ticker) == self._expected_read
                and role == ("MARKET", "EVENT", "SERIES")[self._attempts],
                "KALSHI_OBSERVATION_STATE")
            target = _kalshi_observation_target(role, ticker)
            clock = self._observe_clock_v1()
            self._check_operating_v1(clock)
        try:
            tls_context = ssl.create_default_context()
        except (OSError, ValueError) as error:
            self._raise_transport_v1(error)
        with self._lock, self._authority_guard_v1():
            _kalshi_observation_require(self._state == "CAPTURING" and self._pending is None
                and self._attempts < 3 and (role, ticker) == self._expected_read,
                "KALSHI_OBSERVATION_STATE")
            _kalshi_observation_require(tls_context.check_hostname is True
                and tls_context.verify_mode == ssl.CERT_REQUIRED, "KALSHI_OBSERVATION_TRANSPORT")
            clock = self._observe_clock_v1()
            self._check_operating_v1(clock)
            prepared = _KalshiPreparedReadV1(
                self, current_thread(), role, ticker, target,
                MappingProxyType({"Accept": "application/json", "Accept-Encoding": "identity", "Connection": "close"}),
                tls_context, min(20.0, (self._config.deadline_monotonic_ns - clock[1]) / 1_000_000_000),
                _KALSHI_OBSERVATION_BODY_LIMIT)
            self._pending = (prepared, None, None, False)
            return prepared

    def _recheck_and_charge_v1(self, prepared):
        with self._lock, self._authority_guard_v1():
            self._require_pending_v1(prepared, charged=False)
            clock = self._observe_clock_v1()
            self._check_operating_v1(clock)
            _kalshi_observation_require(self._attempts < 3, "KALSHI_OBSERVATION_STATE")
            self._attempts += 1
            self._config.source_use_binding._permit._started += 1
            self._pending = (prepared, clock, None, False)

    def _validate_response_headers_v1(self, prepared, response):
        with self._lock:
            self._require_pending_v1(prepared, charged=True)
            _kalshi_observation_require(type(response.status) is int and response.status == 200,
                                        "KALSHI_OBSERVATION_HTTP")
            headers = response.getheaders()
            _kalshi_observation_require(type(headers) in (list, tuple) and len(headers) <= 100,
                                        "KALSHI_OBSERVATION_HTTP")
            retained = {}
            size = 0
            for pair in headers:
                _kalshi_observation_require(type(pair) in (list, tuple) and len(pair) == 2
                    and all(type(value) is str for value in pair), "KALSHI_OBSERVATION_HTTP")
                name, value = pair
                try:
                    size += len(name.encode("latin-1", "strict")) + len(value.encode("latin-1", "strict"))
                except UnicodeError:
                    raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_OBSERVATION_HTTP") from None
                _kalshi_observation_require(size <= 65_536, "KALSHI_OBSERVATION_HTTP")
                name = name.lower()
                if name in ("content-type", "content-length", "content-encoding", "transfer-encoding"):
                    _kalshi_observation_require(name not in retained, "KALSHI_OBSERVATION_HTTP")
                    retained[name] = value
            content_type = retained.get("content-type", "").lower().split(";")
            valid_type = content_type[0].strip() == "application/json" and len(content_type) <= 2
            if len(content_type) == 2:
                parameter = content_type[1].strip().split("=")
                valid_type = valid_type and len(parameter) == 2 and parameter[0].strip() == "charset" and parameter[1].strip() in ('utf-8', '"utf-8"')
            _kalshi_observation_require(valid_type, "KALSHI_OBSERVATION_HTTP")
            _kalshi_observation_require(retained.get("content-encoding", "identity").lower() == "identity"
                and retained.get("transfer-encoding", "chunked").lower() == "chunked"
                and not {"transfer-encoding", "content-length"} <= retained.keys(),
                "KALSHI_OBSERVATION_HTTP")
            length = None
            if "content-length" in retained:
                text = retained["content-length"]
                _kalshi_observation_require(bool(text) and all("0" <= c <= "9" for c in text),
                                            "KALSHI_OBSERVATION_HTTP")
                digits = text.lstrip("0")
                _kalshi_observation_require(0 < len(digits) <= 5, "KALSHI_OBSERVATION_HTTP")
                length = int(digits)
                _kalshi_observation_require(1 <= length <= prepared.maximum_raw_bytes, "KALSHI_OBSERVATION_HTTP")
            self._pending = (prepared, self._pending[1], length, True)

    def _validate_response_body_v1(self, prepared, response, raw):
        with self._lock:
            self._require_pending_v1(prepared, charged=True)
            self._check_operating_v1(self._last_clock)
            _kalshi_observation_require(self._pending[3] and type(raw) is bytes
                and 1 <= len(raw) <= prepared.maximum_raw_bytes
                and (self._pending[2] is None or len(raw) == self._pending[2]),
                "KALSHI_OBSERVATION_HTTP")

    def _retain_received_v1(self, prepared, raw, received):
        with self._lock, self._authority_guard_v1():
            self._require_pending_v1(prepared, charged=True)
            _kalshi_observation_require(received is self._last_clock, "KALSHI_OBSERVATION_ASSOCIATION")
            self._check_operating_v1(received)
            request = self._pending[1]
            observation = KalshiFeeHttpObservationV1(prepared.role, prepared.target, raw,
                request[0], request[1], received[0], received[1])
            self._pending = None
            return observation

    def _raise_transport_v1(self, error):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_OBSERVATION_TRANSPORT") from None

    def _read_rest_once_v1(self, role, ticker):
        prepared = self._prepare_read_v1(role, ticker)
        import http.client
        connection = http.client.HTTPSConnection("external-api.kalshi.com", 443, timeout=prepared.timeout_seconds, context=prepared.tls_context)
        try:
            self._recheck_and_charge_v1(prepared)
            connection.request("GET", prepared.target, body=None, headers=prepared.headers)
            response = connection.getresponse()
            self._validate_response_headers_v1(prepared, response)
            raw = response.read(prepared.maximum_raw_bytes + 1)
            received = self._observe_clock_v1()
            self._validate_response_body_v1(prepared, response, raw)
            return self._retain_received_v1(prepared, raw, received)
        except (OSError, http.client.HTTPException) as error:
            self._raise_transport_v1(error)
        finally:
            try:
                connection.close()
            except OSError as error:
                self._raise_transport_v1(error)

    @staticmethod
    def _routing_fields_v1(raw, role, ticker):
        decoded = _native_strict_json(raw)
        reject_secret_material("kalshi_observation", decoded)
        root, identity, link = ("market", "ticker", "event_ticker") if role == "MARKET" else ("event", "event_ticker", "series_ticker")
        _kalshi_observation_require(type(decoded) is dict, "KALSHI_OBSERVATION_FIELDS")
        _kalshi_observation_require(root in decoded, "KALSHI_OBSERVATION_FIELDS", ReasonCode.INCOMPLETE_CONTRACT)
        fields = decoded[root]
        _kalshi_observation_require(type(fields) is dict, "KALSHI_OBSERVATION_FIELDS")
        _kalshi_observation_require({identity, link} <= fields.keys(), "KALSHI_OBSERVATION_FIELDS", ReasonCode.INCOMPLETE_CONTRACT)
        observed, next_ticker = _native_ident(fields[identity]), _native_ident(fields[link])
        _kalshi_observation_require(observed == ticker, "KALSHI_OBSERVATION_FIELDS", ReasonCode.INPUT_SCOPE_MISMATCH)
        if "exchange_index" in fields:
            _kalshi_observation_require(type(fields["exchange_index"]) is int and fields["exchange_index"] == 0,
                                        "KALSHI_OBSERVATION_MODIFIER")
        return fields, next_ticker

    def capture(self) -> KalshiObservedFeeCohortV1:
        self._require_instance_v1()
        with self._lock:
            _kalshi_observation_require(self._state == "NEW", "KALSHI_OBSERVATION_STATE")
            self._state = "CAPTURING"
        try:
            config = self._config
            market = self._read_rest_once_v1("MARKET", config.expected_market_ticker)
            market_fields, event_ticker = self._routing_fields_v1(market.raw_body, "MARKET", config.expected_market_ticker)
            with self._lock:
                self._expected_read = ("EVENT", event_ticker)
            event = self._read_rest_once_v1("EVENT", event_ticker)
            event_fields, series_ticker = self._routing_fields_v1(event.raw_body, "EVENT", event_ticker)
            with self._lock:
                self._expected_read = ("SERIES", series_ticker)
            series = self._read_rest_once_v1("SERIES", series_ticker)
            candidate = decode_kalshi_market_linked_series_fee_candidate_v1(
                raw_market_response=market.raw_body, raw_event_response=event.raw_body,
                raw_series_response=series.raw_body, expected_market_ticker=config.expected_market_ticker)
            _kalshi_observation_require({"fee_type_override", "fee_multiplier_override"} <= event_fields.keys(),
                "KALSHI_OBSERVATION_FIELDS", ReasonCode.INCOMPLETE_CONTRACT)
            _kalshi_observation_require(market_fields.get("fee_waiver_expiration_time") is None,
                                        "KALSHI_OBSERVATION_MODIFIER")
            family, multiplier = event_fields["fee_type_override"], event_fields["fee_multiplier_override"]
            if family is None and multiplier is None:
                basis, multiplier = "OBSERVED_SERIES_BASE", candidate.fee_multiplier
            else:
                _kalshi_observation_require(type(family) is str and family == "quadratic"
                    and type(multiplier) in (int, Decimal), "KALSHI_OBSERVATION_MODIFIER")
                multiplier = KalshiQuadraticSeriesFeeCandidateV1(series_ticker,
                    Decimal(multiplier) if type(multiplier) is int else multiplier).fee_multiplier
                basis = "OBSERVED_EVENT_OVERRIDE"
            with self._lock, self._authority_guard_v1():
                _kalshi_observation_require(self._state == "CAPTURING" and self._pending is None
                    and self._attempts == 3, "KALSHI_OBSERVATION_STATE")
                available = self._observe_clock_v1()
                self._check_operating_v1(available)
                cohort = KalshiObservedFeeCohortV1((market, event, series), config.expected_market_ticker,
                    event_ticker, series_ticker, basis, multiplier, available[0], available[1],
                    config.process_epoch_id, config.monotonic_clock_id)
                self._issued_cohort = cohort
                self._state = "READY"
                return cohort
        except BaseException as error:
            with self._lock:
                self._invalidate_v1()
            if isinstance(error, OSError):
                self._raise_transport_v1(error)
            raise

    def resolve_scenario_multiplier(self, *, cohort: KalshiObservedFeeCohortV1,
                                    expected_market_ticker: str, as_of_monotonic_ns: int) -> Decimal:
        self._require_instance_v1()
        with self._lock:
            _kalshi_observation_require(self._state == "READY", "KALSHI_OBSERVATION_STATE")
            config = self._config
            _kalshi_observation_require(type(cohort) is KalshiObservedFeeCohortV1
                and self._issued_cohort is cohort and cohort.process_epoch_id == config.process_epoch_id
                and cohort.monotonic_clock_id == config.monotonic_clock_id, "KALSHI_OBSERVATION_ASSOCIATION")
            _native_ident(expected_market_ticker)
            _kalshi_observation_require(expected_market_ticker == cohort.market_ticker == config.expected_market_ticker,
                                        "KALSHI_OBSERVATION_FIELDS", ReasonCode.INPUT_SCOPE_MISMATCH)
            now = self._observe_clock_v1()
            self._check_operating_v1(now)
            _kalshi_observation_counter(as_of_monotonic_ns)
            _kalshi_observation_time(cohort.available_monotonic_ns <= as_of_monotonic_ns <= now[1])
            return cohort.fee_multiplier

    def revoke(self) -> None:
        self._require_instance_v1()
        with self._lock:
            if self._publication_route == "SESSION_FINAL" and self._state == "READY":
                self._publication_cleanup = True
            else:
                binding = self._config.source_use_binding
                if binding is not None:
                    with binding._authority._lock:
                        permit = binding._permit
                        if permit is not None and permit._owner is self and not permit._published:
                            permit._failed = True
                            if binding._authority._active_permit is permit:
                                binding._authority._active_permit = None
            self._state = "REVOKED"
            self._pending = None
            self._issued_cohort = None


def _pit_source_text(value: object, name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


def _pit_source_utc(value: object, name: str) -> datetime:
    if (
        type(value) is not datetime
        or value.tzinfo is None
        or value.utcoffset() is None
        or value.utcoffset().total_seconds() != 0
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
            f"{name} must be an aware UTC datetime",
        )
    return value.astimezone(UTC)


def _pit_source_text_tuple(value: object, name: str) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(item) is not str for item in value):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be an exact text tuple",
        )
    result = tuple(_pit_source_text(item, name) for item in value)
    if len(result) != len(set(result)):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must contain unique values",
        )
    return result


@dataclass(frozen=True, slots=True)
class PITSourceCurrentizationReceiptV1:
    receipt_id: str
    profile_id: Stage1VenueProfileIdV1
    source_id: str
    source_contract_version: str
    checked_at_utc: datetime
    effective_at_utc: datetime
    expires_at_utc: datetime
    currentization_owner_id: str
    recheck_triggers: tuple[str, ...]
    invalidating_change_detected: bool
    admitted_current: bool
    no_effects: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "source_id",
            "source_contract_version",
            "currentization_owner_id",
        ):
            _pit_source_text(getattr(self, name), name)
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "profile_id must be an exact Stage1VenueProfileIdV1",
            )
        for name in ("checked_at_utc", "effective_at_utc", "expires_at_utc"):
            object.__setattr__(self, name, _pit_source_utc(getattr(self, name), name))
        if not _pit_source_text_tuple(self.recheck_triggers, "recheck_triggers"):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
                "source currentization requires at least one recheck trigger",
            )
        if (
            type(self.invalidating_change_detected) is not bool
            or type(self.admitted_current) is not bool
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
                "currentization states must be exact booleans",
            )
        if self.effective_at_utc > self.checked_at_utc:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
                "source receipt cannot be checked before it is effective",
            )
        if self.expires_at_utc <= self.checked_at_utc:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
                "source receipt must be unexpired when checked",
            )
        if self.invalidating_change_detected or not self.admitted_current:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
                "source receipt is stale or invalidated",
            )
        if type(self.no_effects) is not NoEffectFlagsV1 or self.no_effects != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "source currentization must have exactly zero effects",
            )


@dataclass(frozen=True, slots=True)
class PITRightsAdmissionReceiptV1:
    receipt_id: str
    profile_id: Stage1VenueProfileIdV1
    account_scope: str
    source_id: str
    agreement_id: str
    agreement_version: str
    internal_use_class: str
    owner_decision: str
    checked_at_utc: datetime
    expires_at_utc: datetime
    recheck_triggers: tuple[str, ...]
    revoked: bool
    permitted_retention_class: str
    prohibited_redistribution_class: str
    no_effects: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "profile_id must be an exact Stage1VenueProfileIdV1",
            )
        for name in (
            "receipt_id",
            "account_scope",
            "source_id",
            "agreement_id",
            "agreement_version",
            "internal_use_class",
            "owner_decision",
            "permitted_retention_class",
            "prohibited_redistribution_class",
        ):
            _pit_source_text(getattr(self, name), name)
        object.__setattr__(
            self, "checked_at_utc", _pit_source_utc(self.checked_at_utc, "checked_at_utc")
        )
        object.__setattr__(
            self, "expires_at_utc", _pit_source_utc(self.expires_at_utc, "expires_at_utc")
        )
        if not _pit_source_text_tuple(self.recheck_triggers, "recheck_triggers"):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
                "rights admission requires at least one recheck trigger",
            )
        if type(self.revoked) is not bool:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
                "revoked must be an exact boolean",
            )
        if (
            self.owner_decision != "ADMITTED_INTERNAL_USE"
            or self.revoked
            or self.expires_at_utc <= self.checked_at_utc
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
                "rights receipt is not an active owner admission",
            )
        if type(self.no_effects) is not NoEffectFlagsV1 or self.no_effects != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "rights admission must have exactly zero effects",
            )


@dataclass(frozen=True, slots=True)
class PITSourceRightsAdmissionV1:
    admission_id: str
    profile_id: Stage1VenueProfileIdV1
    source_receipt_ref: str
    rights_receipt_ref: str
    source_contract_version: str
    agreement_version: str
    account_scope: str
    internal_use_class: str
    permitted_retention_class: str
    admitted_at_utc: datetime
    valid_until_utc: datetime
    admitted: bool
    no_effects: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "profile_id must be an exact Stage1VenueProfileIdV1",
            )
        for name in (
            "admission_id",
            "source_receipt_ref",
            "rights_receipt_ref",
            "source_contract_version",
            "agreement_version",
            "account_scope",
            "internal_use_class",
            "permitted_retention_class",
        ):
            _pit_source_text(getattr(self, name), name)
        object.__setattr__(
            self, "admitted_at_utc", _pit_source_utc(self.admitted_at_utc, "admitted_at_utc")
        )
        object.__setattr__(
            self, "valid_until_utc", _pit_source_utc(self.valid_until_utc, "valid_until_utc")
        )
        if type(self.admitted) is not bool or not self.admitted:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
                "source/rights admission must be admitted",
            )
        if self.valid_until_utc < self.admitted_at_utc:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
                "source/rights admission validity interval is reversed",
            )
        if type(self.no_effects) is not NoEffectFlagsV1 or self.no_effects != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "source/rights admission must have exactly zero effects",
            )


def validate_pit_source_rights_admission_v1(
    source_receipt: PITSourceCurrentizationReceiptV1,
    rights_receipt: PITRightsAdmissionReceiptV1,
    *,
    admission_id: str,
    profile_id: Stage1VenueProfileIdV1,
    account_scope: str,
    internal_use_class: str,
    permitted_retention_class: str,
    evaluated_at_utc: datetime,
) -> PITSourceRightsAdmissionV1:
    """Bind exact current source and rights receipts without runtime inference."""

    if type(source_receipt) is not PITSourceCurrentizationReceiptV1:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
            "source_receipt must be exact PITSourceCurrentizationReceiptV1",
        )
    if type(rights_receipt) is not PITRightsAdmissionReceiptV1:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
            "rights_receipt must be exact PITRightsAdmissionReceiptV1",
        )
    evaluated = _pit_source_utc(evaluated_at_utc, "evaluated_at_utc")
    if (
        type(profile_id) is not Stage1VenueProfileIdV1
        or source_receipt.profile_id is not profile_id
        or rights_receipt.profile_id is not profile_id
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "source, rights, and requested profile must match exactly",
        )
    if source_receipt.source_id != rights_receipt.source_id:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
            "rights receipt does not bind the current source",
        )
    for requested, observed, name in (
        (account_scope, rights_receipt.account_scope, "account_scope"),
        (internal_use_class, rights_receipt.internal_use_class, "internal_use_class"),
        (
            permitted_retention_class,
            rights_receipt.permitted_retention_class,
            "permitted_retention_class",
        ),
    ):
        _pit_source_text(requested, name)
        if requested != observed:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
                f"{name} does not equal the owner rights receipt",
            )
    if (
        evaluated < source_receipt.effective_at_utc
        or evaluated < source_receipt.checked_at_utc
        or evaluated - source_receipt.checked_at_utc > timedelta(hours=24)
        or evaluated >= source_receipt.expires_at_utc
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
            "source currentization is not valid at the evaluation time",
        )
    if (
        evaluated < rights_receipt.checked_at_utc
        or evaluated >= rights_receipt.expires_at_utc
        or rights_receipt.revoked
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
            "rights admission is not valid at the evaluation time",
        )
    valid_until = min(
        source_receipt.expires_at_utc,
        source_receipt.checked_at_utc + timedelta(hours=24),
        rights_receipt.expires_at_utc,
    )
    return PITSourceRightsAdmissionV1(
        admission_id=admission_id,
        profile_id=profile_id,
        source_receipt_ref=source_receipt.receipt_id,
        rights_receipt_ref=rights_receipt.receipt_id,
        source_contract_version=source_receipt.source_contract_version,
        agreement_version=rights_receipt.agreement_version,
        account_scope=account_scope,
        internal_use_class=internal_use_class,
        permitted_retention_class=permitted_retention_class,
        admitted_at_utc=evaluated,
        valid_until_utc=valid_until,
        admitted=True,
    )


# Internal F14 source capabilities. Bootstrap supplies accepted operational
# inputs; these types do not measure clock quality or authorize a real account.
from contextlib import contextmanager
from _thread import RLock
import time
from .context import _f14_freeze_v1, _f14_plain_v1, _native_utc_nanoseconds
from .context import ComputationContextKeyV1, _native_ident, _native_bounded_decimal, _native_require
from .errors import ContractValidationError, PointInTimeError
from .serialization import (_F14_SCOPE, _F14_SCOPE_FIELDS, _F14_ID, _F14_OPERATIONS, _F14_MAX_INT,
    _f14_validate_v1, _f14_native_time_v1)
from .serialization import _native_strict_json


def _f14_ingress_require_v1(ok, token):
    if not ok:
        if any(word in token for word in ('CLOCK', 'DEADLINE', 'TIME_ORDER')):
            raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, token)
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, token)


def _f14_counter_v1(value, minimum=0, maximum=_F14_MAX_INT):
    _f14_ingress_require_v1(type(value) is int and minimum <= value <= maximum,
        'F14_INGRESS_COUNTER')
    return value


def _f14_wall_text_v1(nanoseconds):
    _f14_ingress_require_v1(type(nanoseconds) is int, 'F14_INGRESS_CLOCK')
    seconds, fraction = divmod(nanoseconds, 1_000_000_000)
    stamp = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds)
    return (f'{stamp.year:04d}-{stamp.month:02d}-{stamp.day:02d}T'
        f'{stamp.hour:02d}:{stamp.minute:02d}:{stamp.second:02d}.{fraction:09d}Z')


@dataclass(frozen=True, slots=True)
class RetailPrivateSessionBindingV1:
    scope: Mapping[str, str]
    source_snapshot_ref: str
    credential_binding_ref: str
    session_ref: str
    revocation_epoch: int
    source_receipt: PITSourceCurrentizationReceiptV1
    rights_receipt: PITRightsAdmissionReceiptV1
    valid_from_utc: datetime
    valid_until_utc: datetime
    permitted_route_ops: tuple[str, ...]

    def __post_init__(self):
        _f14_ingress_require_v1(isinstance(self.scope, Mapping), 'F14_INGRESS_SCOPE')
        scope = dict(self.scope)
        _f14_validate_v1(_F14_SCOPE, scope)
        _f14_ingress_require_v1(scope['profile'] == 'POLYMARKET_US_RETAIL_DIRECT', 'F14_INGRESS_SCOPE')
        for value in (self.source_snapshot_ref, self.credential_binding_ref, self.session_ref):
            _f14_validate_v1(_F14_ID, value)
        _f14_counter_v1(self.revocation_epoch)
        _f14_ingress_require_v1(type(self.source_receipt) is PITSourceCurrentizationReceiptV1
            and type(self.rights_receipt) is PITRightsAdmissionReceiptV1, 'F14_INGRESS_SOURCE')
        for name in ('valid_from_utc', 'valid_until_utc'):
            _f14_ingress_require_v1(type(getattr(self, name)) is datetime, 'F14_INGRESS_CLOCK')
            object.__setattr__(self, name, _pit_source_utc(getattr(self, name), name))
        start = max(self.source_receipt.effective_at_utc, self.source_receipt.checked_at_utc,
            self.rights_receipt.checked_at_utc)
        end = min(self.source_receipt.expires_at_utc, self.rights_receipt.expires_at_utc,
            self.source_receipt.checked_at_utc + timedelta(hours=24))
        _f14_ingress_require_v1(start == self.valid_from_utc < self.valid_until_utc == end,
            'F14_INGRESS_SOURCE_INTERVAL')
        _f14_ingress_require_v1(self.source_receipt.source_id == self.rights_receipt.source_id
            == scope['source_binding_ref'], 'F14_INGRESS_SOURCE')
        ops = self.permitted_route_ops
        _f14_ingress_require_v1(type(ops) is tuple and bool(ops)
            and all(type(op) is str and op in _F14_OPERATIONS for op in ops)
            and len(ops) == len(set(ops)), 'F14_INGRESS_ROUTE')
        object.__setattr__(self, 'scope', _f14_freeze_v1(scope))


@dataclass(frozen=True, slots=True)
class RetailPrivateRuntimeGrantV1:
    grant_id: str
    session_binding: RetailPrivateSessionBindingV1
    issued_at_utc: datetime
    expires_at_utc: datetime
    process_epoch_id: str
    monotonic_clock_id: str
    wall_clock_source_id: str
    clock_quality_receipt_ref: str
    wall_clock_uncertainty_ns: int
    transport_attempts_remaining: int
    deadline_monotonic_ns: int
    maximum_application_messages: int

    def __post_init__(self):
        _f14_ingress_require_v1(type(self.session_binding) is RetailPrivateSessionBindingV1,
            'F14_INGRESS_SESSION')
        for value in (self.grant_id, self.process_epoch_id, self.monotonic_clock_id,
                self.wall_clock_source_id, self.clock_quality_receipt_ref):
            _f14_validate_v1(_F14_ID, value)
        _f14_counter_v1(self.wall_clock_uncertainty_ns)
        for value in (self.transport_attempts_remaining, self.deadline_monotonic_ns,
                self.maximum_application_messages):
            _f14_counter_v1(value, 1)
        for name in ('issued_at_utc', 'expires_at_utc'):
            _f14_ingress_require_v1(type(getattr(self, name)) is datetime, 'F14_INGRESS_CLOCK')
            object.__setattr__(self, name, _pit_source_utc(getattr(self, name), name))
        _f14_ingress_require_v1(self.session_binding.valid_from_utc <= self.issued_at_utc
            < self.expires_at_utc <= self.session_binding.valid_until_utc, 'F14_INGRESS_SOURCE_INTERVAL')


class RetailPrivateSourceRegistryV1:
    """Empty, process-local projection over independently admitted source inputs."""

    def __init__(self, *, process_epoch_id: str, monotonic_clock_id: str):
        for value in (process_epoch_id, monotonic_clock_id):
            _f14_validate_v1(_F14_ID, value)
        self.process_epoch_id = process_epoch_id
        self.monotonic_clock_id = monotonic_clock_id
        self._lock = RLock()
        self._sessions = {}
        self._generations = {}
        self._grants = {}
        self._remaining = {}
        self._credentials = {}
        self._receivers = {}
        self._captures = {}
        self._clock_facts = {}
        self._last_clock = None

    def _validate_session_v1(self, session, wall_ns):
        _f14_ingress_require_v1(type(session) is RetailPrivateSessionBindingV1
            and self._sessions.get(session.source_snapshot_ref) is session,
            'F14_INGRESS_SESSION')
        key = tuple(session.scope[name] for name in _F14_SCOPE_FIELDS)
        _f14_ingress_require_v1(self._generations.get(key) == session.revocation_epoch,
            'F14_INGRESS_REVOKED')
        instant = _f14_wall_text_v1(wall_ns)
        _f14_ingress_require_v1(_native_utc_nanoseconds(session.valid_from_utc.isoformat())
            <= wall_ns < _native_utc_nanoseconds(session.valid_until_utc.isoformat()),
            'F14_INGRESS_SOURCE_EXPIRED')
        validate_pit_source_rights_admission_v1(session.source_receipt, session.rights_receipt,
            admission_id=session.source_snapshot_ref,
            profile_id=Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT,
            account_scope=session.scope['ledger_account_ref'],
            internal_use_class=session.rights_receipt.internal_use_class,
            permitted_retention_class=session.rights_receipt.permitted_retention_class,
            evaluated_at_utc=datetime.fromisoformat(_f14_native_time_v1(instant)[1]))

    def bind_session(self, session):
        _f14_ingress_require_v1(type(session) is RetailPrivateSessionBindingV1, 'F14_INGRESS_SESSION')
        with self._lock:
            prior = self._sessions.get(session.source_snapshot_ref)
            if prior is not None:
                _f14_ingress_require_v1(prior is session, 'F14_INGRESS_SESSION_CONFLICT')
                self._validate_session_v1(session, time.time_ns())
                return
            key = tuple(session.scope[name] for name in _F14_SCOPE_FIELDS)
            previous = self._generations.get(key)
            _f14_ingress_require_v1(previous is None or session.revocation_epoch > previous,
                'F14_INGRESS_REVOKED')
            # Validate first; publish the new projection only after all predicates.
            now = time.time_ns()
            _f14_ingress_require_v1(_native_utc_nanoseconds(session.valid_from_utc.isoformat()) <= now
                < _native_utc_nanoseconds(session.valid_until_utc.isoformat()), 'F14_INGRESS_SOURCE_EXPIRED')
            validate_pit_source_rights_admission_v1(session.source_receipt, session.rights_receipt,
                admission_id=session.source_snapshot_ref,
                profile_id=Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT,
                account_scope=session.scope['ledger_account_ref'],
                internal_use_class=session.rights_receipt.internal_use_class,
                permitted_retention_class=session.rights_receipt.permitted_retention_class,
                evaluated_at_utc=datetime.fromisoformat(_f14_native_time_v1(_f14_wall_text_v1(now))[1]))
            self._sessions[session.source_snapshot_ref] = session
            self._generations[key] = session.revocation_epoch

    def issue_grant(self, grant):
        _f14_ingress_require_v1(type(grant) is RetailPrivateRuntimeGrantV1, 'F14_INGRESS_GRANT')
        with self._lock:
            now = time.time_ns()
            self._validate_session_v1(grant.session_binding, now)
            _f14_ingress_require_v1(grant.process_epoch_id == self.process_epoch_id
                and grant.monotonic_clock_id == self.monotonic_clock_id, 'F14_INGRESS_CLOCK_DOMAIN')
            _f14_ingress_require_v1(_native_utc_nanoseconds(grant.issued_at_utc.isoformat()) <= now
                < _native_utc_nanoseconds(grant.expires_at_utc.isoformat()), 'F14_INGRESS_GRANT_EXPIRED')
            _f14_ingress_require_v1(time.monotonic_ns() < grant.deadline_monotonic_ns,
                'F14_INGRESS_DEADLINE')
            old = self._grants.get(grant.grant_id)
            _f14_ingress_require_v1(old is None or old is grant, 'F14_INGRESS_GRANT_CONFLICT')
            if old is None:
                self._grants[grant.grant_id] = grant
                self._remaining[grant.grant_id] = grant.transport_attempts_remaining

    def _validate_grant_v1(self, grant, operation=None):
        _f14_ingress_require_v1(type(grant) is RetailPrivateRuntimeGrantV1
            and self._grants.get(grant.grant_id) is grant, 'F14_INGRESS_GRANT')
        now = time.time_ns()
        self._validate_session_v1(grant.session_binding, now)
        _f14_ingress_require_v1(_native_utc_nanoseconds(grant.issued_at_utc.isoformat()) <= now
            < _native_utc_nanoseconds(grant.expires_at_utc.isoformat()), 'F14_INGRESS_GRANT_EXPIRED')
        _f14_ingress_require_v1(grant.process_epoch_id == self.process_epoch_id
            and grant.monotonic_clock_id == self.monotonic_clock_id, 'F14_INGRESS_CLOCK_DOMAIN')
        _f14_ingress_require_v1(time.monotonic_ns() < grant.deadline_monotonic_ns, 'F14_INGRESS_DEADLINE')
        if operation is not None:
            _f14_ingress_require_v1(type(operation) is str
                and operation in grant.session_binding.permitted_route_ops, 'F14_INGRESS_ROUTE')

    @contextmanager
    def fenced(self, grant, operation=None):
        with self._lock:
            self._validate_grant_v1(grant, operation)
            try:
                yield grant.session_binding
            finally:
                self._validate_grant_v1(grant, operation)

    def revoke(self, session_binding, revocation_epoch):
        _f14_counter_v1(revocation_epoch)
        with self._lock:
            _f14_ingress_require_v1(type(session_binding) is RetailPrivateSessionBindingV1
                and self._sessions.get(session_binding.source_snapshot_ref) is session_binding,
                'F14_INGRESS_SESSION')
            key = tuple(session_binding.scope[name] for name in _F14_SCOPE_FIELDS)
            _f14_ingress_require_v1(revocation_epoch > self._generations[key], 'F14_INGRESS_REVOKED')
            self._generations[key] = revocation_epoch

    def _charge_v1(self, grant, operation):
        with self.fenced(grant, operation):
            count = self._remaining[grant.grant_id]
            _f14_ingress_require_v1(count > 0, 'F14_INGRESS_ATTEMPT_BUDGET')
            self._remaining[grant.grant_id] = count - 1

    def _observe_v1(self, grant):
        with self._lock:
            before = time.monotonic_ns()
            wall = time.time_ns()
            after = time.monotonic_ns()
            _f14_counter_v1(before)
            _f14_counter_v1(after)
            _f14_ingress_require_v1(before <= after and (self._last_clock is None
                or self._last_clock <= before), 'F14_INGRESS_TIME_ORDER')
            self._last_clock = after
            self._validate_grant_v1(grant)
            return _f14_freeze_v1(dict(observed_at=_f14_wall_text_v1(wall), monotonic_ns=after,
                process_epoch_id=grant.process_epoch_id, monotonic_clock_id=grant.monotonic_clock_id,
                wall_clock_source_id=grant.wall_clock_source_id,
                clock_quality_receipt_ref=grant.clock_quality_receipt_ref,
                wall_clock_uncertainty_ns=grant.wall_clock_uncertainty_ns))

    def bind_clock_facts(self, *, grant_id, request_ref, item_key, facts_by_role):
        with self._lock:
            grant = self._grants.get(grant_id)
            self._validate_grant_v1(grant)
            _f14_validate_v1(_F14_ID, request_ref)
            _f14_ingress_require_v1(item_key is None or type(item_key) in (str, int), 'F14_INGRESS_ITEM')
            if type(item_key) is int:
                _f14_counter_v1(item_key)
            elif type(item_key) is str:
                _f14_validate_v1(_F14_ID, item_key)
            _f14_ingress_require_v1(type(facts_by_role) is dict
                and set(facts_by_role) <= {'publication', 'revision', 'finality'}, 'F14_INGRESS_CLOCK_FACT')
            facts = {}
            for role, fact in facts_by_role.items():
                _f14_ingress_require_v1(type(fact) is dict
                    and set(fact) == {'timestamp', 'source_record_ref', 'source_binding_ref'},
                    'F14_INGRESS_CLOCK_FACT')
                _native_utc_nanoseconds(fact['timestamp'])
                session = grant.session_binding
                _f14_ingress_require_v1(fact['source_record_ref'] == session.source_receipt.receipt_id
                    and fact['source_binding_ref'] == session.scope['source_binding_ref'],
                    'F14_INGRESS_CLOCK_FACT_SOURCE')
                facts[role] = dict(fact)
            key = (grant_id, request_ref, type(item_key), item_key)
            frozen = _f14_freeze_v1(facts)
            _f14_ingress_require_v1(key not in self._clock_facts or self._clock_facts[key] == frozen,
                'F14_INGRESS_CLOCK_FACT_CONFLICT')
            self._clock_facts[key] = frozen

    def register_observed_capture(self, observed, *, receiver, request, attempt_id):
        from ..private_state_receipts.receipt import ObservedPrivateCaptureV1
        with self.fenced(request.grant, request.operation):
            _f14_ingress_require_v1(type(observed) is ObservedPrivateCaptureV1
                and self._receivers.get(id(receiver)) is receiver
                and receiver.source_registry is self and receiver._active_request is request
                and receiver._attempt_id == attempt_id
                and observed.session_binding is request.grant.session_binding
                and observed.operation == request.operation and observed.consumer == request.consumer
                and observed.requirements == request.requirements,
                'F14_INGRESS_CAPTURE_ASSOCIATION')
            _f14_ingress_require_v1(id(observed) not in self._captures
                and all(value[4] != attempt_id for value in self._captures.values()),
                'F14_INGRESS_CAPTURE_DUPLICATE')
            self._captures[id(observed)] = (observed, receiver, request, False, attempt_id)

    def _consume_capture_v1(self, observed, receiver, request):
        with self.fenced(request.grant, request.operation):
            entry = self._captures.get(id(observed))
            _f14_ingress_require_v1(entry is not None and entry[0] is observed and entry[1] is receiver
                and entry[2] is request and entry[3] is False, 'F14_INGRESS_CAPTURE_ASSOCIATION')
            self._captures[id(observed)] = (*entry[:3], True, entry[4])
            return entry[4]

    def _source_witness_v1(self, grant):
        self._validate_grant_v1(grant)
        session = grant.session_binding
        return dict(record_id=session.scope['source_binding_ref'], scope=dict(session.scope),
            source_snapshot_ref=session.source_snapshot_ref, revocation_epoch=session.revocation_epoch,
            valid_from=session.valid_from_utc.isoformat(), valid_until=session.valid_until_utc.isoformat(),
            rights_receipt_ref=session.rights_receipt.receipt_id,
            currentization_receipt_ref=session.source_receipt.receipt_id)
