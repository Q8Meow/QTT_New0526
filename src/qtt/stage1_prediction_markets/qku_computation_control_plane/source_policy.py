"""Exact source-state metadata, currentization overlays, and fail-closed policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
import json
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .errors import ReasonCode, SourcePolicyError


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
    stability_class: str
    ttl_days_or_none: int | None
    currentness_state: str
    rights_state: str
    recheck_trigger: str
    currentness_evidence_ref: str
    codex_research_required: bool

    def __post_init__(self) -> None:
        for field_name in (
            "source_id",
            "source_name",
            "source_class",
            "authority_class",
            "source_locator",
            "publication_or_version",
            "stability_class",
            "currentness_state",
            "rights_state",
            "recheck_trigger",
            "currentness_evidence_ref",
        ):
            _st12h_source_text(getattr(self, field_name), field_name=field_name)
        if type(self.observed_at) is not date:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "observed_at must be an exact date",
            )
        if self.stability_class not in {"STABLE_VERSION", "MUTABLE_RECHECK"}:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "stability_class must select one exact currentness policy",
            )
        if self.stability_class == "STABLE_VERSION":
            if self.ttl_days_or_none is not None:
                raise SourcePolicyError(
                    ReasonCode.SOURCE_CONFLICT,
                    "stable-version sources must not claim a mutable TTL",
                )
        elif type(self.ttl_days_or_none) is not int or self.ttl_days_or_none < 0:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "mutable sources require an exact nonnegative TTL",
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
        observed_at=date(2026, 8, 17),
        stability_class=(
            "MUTABLE_RECHECK"
            if source_id in {
                "ST12H-V8-SRC::04",
                "ST12H-V8-SRC::05",
                "ST12H-V8-SRC::06",
                "ST12H-V8-SRC::09",
            }
            else "STABLE_VERSION"
        ),
        ttl_days_or_none=(
            0
            if source_id in {
                "ST12H-V8-SRC::04",
                "ST12H-V8-SRC::05",
                "ST12H-V8-SRC::06",
                "ST12H-V8-SRC::09",
            }
            else None
        ),
        currentness_state=currentness_state,
        rights_state=rights_state,
        recheck_trigger=recheck_trigger,
        currentness_evidence_ref=f"ST12H-SOURCE-EVIDENCE::{source_id}",
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


def _st12h_symbolic_branch_ref(repo_root: Path) -> str:
    git_entry = repo_root / ".git"
    git_directory = git_entry
    if git_entry.is_file():
        declaration = git_entry.read_text(encoding="utf-8").strip()
        if not declaration.startswith("gitdir: "):
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "selected worktree has no canonical Git directory declaration",
            )
        git_directory = (repo_root / declaration.removeprefix("gitdir: ")).resolve()
    head = (git_directory / "HEAD").read_text(encoding="utf-8").strip()
    if not head.startswith("ref: refs/heads/"):
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_STALE,
            "mutable source recheck requires a symbolic branch context",
        )
    return head.removeprefix("ref: refs/heads/")


def _st12h_mutable_source_recheck(
    binding: ST12HSourceBindingV1,
) -> tuple[str, ...]:
    repo_root = _st12h_repository_root()
    if not (repo_root / ".git").exists():
        raise SourcePolicyError(
            ReasonCode.SOURCE_EPOCH_MISSING,
            "mutable repository source requires the selected Git worktree",
        )
    if binding.source_id == "ST12H-V8-SRC::04":
        branch = _st12h_symbolic_branch_ref(repo_root)
        package_guard = repo_root / ".codex_inputs/h80/p/guard/YOLO_FULL_ACCESS_SAFETY_GUARD.txt"
        active_registry = (
            repo_root
            / ".codex_inputs/h80/p/current_main/h_repository_mutation_allowlist.jsonl"
        )
        protected_registry = (
            repo_root
            / ".codex_inputs/h80/p/current_main/"
            "h_repository_read_only_predecessor_registry.jsonl"
        )
        try:
            active_rows = tuple(
                json.loads(line)
                for line in active_registry.read_text(encoding="utf-8").splitlines()
            )
            protected_rows = tuple(
                json.loads(line)
                for line in protected_registry.read_text(encoding="utf-8").splitlines()
            )
        except (OSError, ValueError, TypeError) as exc:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "post-ST12-G currentization registries are unavailable",
            ) from exc
        if (
            branch
            != "agent/st12h-validation-currentization-operations-publication"
            or not package_guard.is_file()
            or len(active_rows) != 25
            or len(protected_rows) != 66
            or any(row.get("repository_path") is None for row in active_rows)
            or any(row.get("repository_path") is None for row in protected_rows)
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_STALE,
                "post-ST12-G handoff no longer matches the selected H validation context",
            )
        return (
            "agent/st12h-validation-currentization-operations-publication",
            ".codex_inputs/h80/p/guard/YOLO_FULL_ACCESS_SAFETY_GUARD.txt",
            ".codex_inputs/h80/p/current_main/h_repository_mutation_allowlist.jsonl",
            ".codex_inputs/h80/p/current_main/h_repository_read_only_predecessor_registry.jsonl",
            "ACTIVE_PATH_COUNT=25",
            "PROTECTED_PATH_COUNT=66",
            binding.currentness_evidence_ref,
        )
    if binding.source_id == "ST12H-V8-SRC::05":
        paths = (
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py",
            "tools/run_validation_gates.py",
        )
        try:
            validation_source = (repo_root / paths[0]).read_text(encoding="utf-8")
            runner_source = (repo_root / paths[1]).read_text(encoding="utf-8")
        except OSError as exc:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "current repository owner topology is unreadable",
            ) from exc
        if (
            "ST12H_CONTROL_CASES" not in validation_source
            or "ST12H_EXECUTABLE_CONTROL_ADAPTERS" not in validation_source
            or "_execution_command_with_qku_root_importlib" not in runner_source
            or "build_st12h_validation_commands" not in runner_source
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_STALE,
                "current repository owner topology recheck failed",
            )
        return (*paths, binding.currentness_evidence_ref)
    if binding.source_id == "ST12H-V8-SRC::06":
        workflow_path = repo_root / ".github/workflows/qtt_validation.yml"
        try:
            workflow = workflow_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "current validation workflow is unavailable",
            ) from exc
        if (
            workflow.count("uses: actions/setup-python@v5") != 2
            or workflow.count("python-version: '3.14.6'") != 2
            or workflow.count("python -m pip install pytest==9.1.1") != 1
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_STALE,
                "current validation workflow differs from the final H pin contract",
            )
        return (
            ".github/workflows/qtt_validation.yml",
            binding.currentness_evidence_ref,
        )
    if binding.source_id == "ST12H-V8-SRC::09":
        owners = (
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/errors.py",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py",
        )
        try:
            owner_sources = tuple(
                (repo_root / path).read_text(encoding="utf-8") for path in owners
            )
        except OSError as exc:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "current reason/model/validation owners are unreadable",
            ) from exc
        if (
            "class ReasonCode" not in owner_sources[0]
            or "ST12D_KILL_OR_SUBMIT_DISABLED" not in owner_sources[0]
            or "ST12E_CONTEXT_SCOPE_MISMATCH" not in owner_sources[0]
            or "class NoEffectFlagsV1" not in owner_sources[1]
            or "def validate_st12h_control_case_v1" not in owner_sources[2]
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_STALE,
                "current reason/model/validation owner recheck failed",
            )
        return (*owners, binding.currentness_evidence_ref)
    raise SourcePolicyError(
        ReasonCode.SOURCE_CONFLICT,
        f"mutable source has no exact offline recheck owner: {binding.source_id}",
    )


def validate_st12h_source_binding_v1(
    binding: ST12HSourceBindingV1,
    *,
    evaluated_at: date,
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
    if (
        binding.source_class == "CERTIFIED_HISTORICAL_BASELINE"
        and binding.authority_class != "HISTORICAL_PROVENANCE_ONLY"
    ):
        raise SourcePolicyError(
            ReasonCode.SOURCE_CONFLICT,
            "historical ST12-H provenance cannot become current source truth",
        )
    if binding.stability_class == "MUTABLE_RECHECK":
        evidence_refs = _st12h_mutable_source_recheck(binding)
        valid_until = evaluated_at
        terminal_state = "CURRENT_BY_ACTUAL_OFFLINE_RECHECK"
    else:
        if not binding.publication_or_version or not binding.currentness_evidence_ref:
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "stable source requires an exact version and evidence reference",
            )
        evidence_refs = (
            binding.source_locator,
            binding.publication_or_version,
            binding.currentness_evidence_ref,
        )
        valid_until = None
        terminal_state = "CURRENT_BY_STABLE_VERSION_BASIS"
    return _ST12HSourceCurrentnessReceiptV1(
        source_id=binding.source_id,
        evaluated_at=evaluated_at,
        valid_until=valid_until,
        stability_class=binding.stability_class,
        evidence_refs=evidence_refs,
        terminal_state=terminal_state,
    )


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
    if receipt.terminal_state not in {
        "CURRENT_BY_ACTUAL_OFFLINE_RECHECK",
        "CURRENT_BY_STABLE_VERSION_BASIS",
    }:
        raise SourcePolicyError(
            ReasonCode.SOURCE_CONFLICT,
            "source currentness receipt has an unknown terminal state",
        )
    if receipt.stability_class == "MUTABLE_RECHECK":
        if (
            receipt.terminal_state != "CURRENT_BY_ACTUAL_OFFLINE_RECHECK"
            or receipt.valid_until != receipt.evaluated_at
            or not receipt.evidence_refs
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_EPOCH_STALE,
                "mutable source currentness requires a same-evaluation offline recheck receipt",
            )
    elif receipt.stability_class == "STABLE_VERSION":
        if (
            receipt.terminal_state != "CURRENT_BY_STABLE_VERSION_BASIS"
            or receipt.valid_until is not None
            or not receipt.evidence_refs
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_CONFLICT,
                "stable source currentness requires its exact version-basis receipt",
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
