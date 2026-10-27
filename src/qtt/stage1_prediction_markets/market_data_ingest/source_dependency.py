from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
    NoEffectFlagsV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PITDataContractErrorV1,
    PITDepthClassV2,
    PITEventKindV2,
    PITReasonCodeV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    Stage1VenueProfileIdV1,
)


def project_accepted_public_field_bindings_v1(*, source_binding, acceptance_results: tuple,
                                            originals: tuple, review_facts):
    from ..qku_computation_control_plane.errors import ContractValidationError, ReasonCode

    try:
        return _project_accepted_public_field_bindings_v1(source_binding=source_binding,
            acceptance_results=acceptance_results, originals=originals, review_facts=review_facts)
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "accepted public source projection is malformed") from error


def _project_accepted_public_field_bindings_v1(*, source_binding, acceptance_results, originals, review_facts):
    """Check accepted upstream facts and original bytes, without granting use.

    A reviewed claim binds the complete acceptance bundle's canonical digest.
    The original source text remains separate from the structured extraction;
    constructing either a source binding or an acceptance result is insufficient.
    """
    import hashlib
    from dataclasses import fields
    from src.qtt.source_evidence.acceptance import validator as accepted
    from ..qku_computation_control_plane.context import _native_require, _native_utc_nanoseconds, _public_scalar_tree_v1
    from ..qku_computation_control_plane.receipts import SourceUseReviewFactsV1
    from ..qku_computation_control_plane.serialization import _native_strict_json
    from ..qku_computation_control_plane.source_policy import PublicDataSourceBindingV1

    _native_require(type(source_binding) is PublicDataSourceBindingV1 and type(review_facts) is SourceUseReviewFactsV1,
                    "accepted public field projection requires exact source/review inputs")
    source_binding.__post_init__()
    review_facts.__post_init__()
    _native_require(type(acceptance_results) is tuple and 0 < len(acceptance_results) <= 4096
        and type(originals) is tuple and len(originals) == len(acceptance_results), "accepted source/original vector missing")
    original_by_id = {}
    for row in originals:
        _native_require(type(row) is tuple and len(row) == 3 and type(row[0]) is str
            and type(row[1]) is type(row[2]) is bytes and 0 < len(row[1]) <= 1048576 and 0 < len(row[2]) <= 1048576
            and row[0] not in original_by_id, "invalid accepted source original bytes")
        original_by_id[row[0]] = row[1:]
    _native_require(sum(len(raw)+len(canonical) for raw,canonical in original_by_id.values()) <= 16777216,
                    "accepted source originals exceed containment")
    projected, snapshots, claims, packet_ids = [], [], [], set()
    external = True
    for result in acceptance_results:
        _native_require(type(result) is accepted.ExecuteAcceptanceResult and result.reject_receipt is None,
                        "source projection requires an accepted upstream result")
        raw_bundle = accepted.canonical_json_bytes({item.name:getattr(result,item.name) for item in fields(result)})
        _native_require(len(raw_bundle) <= 65536, "accepted source bundle exceeds containment")
        bundle = _native_strict_json(raw_bundle, max_bytes=65536)
        packet, ledger, decision = (bundle[name] for name in ("accepted_packet","accepted_ledger_record","decision_receipt"))
        _native_require(all(type(row) is dict for row in (packet,ledger,decision))
            and not accepted.validate_accepted_packet(packet) and not accepted.validate_ledger_record(ledger)
            and not accepted.validate_decision_receipt(decision) and decision["decision"] == "ACCEPTED",
            "upstream source acceptance validation failed")
        packet_id = packet["accepted_source_evidence_packet_id"]
        _native_require(packet_id in original_by_id and packet_id not in packet_ids, "accepted original reference mismatch")
        packet_ids.add(packet_id)
        for name in ("accepted_source_evidence_packet_id", "candidate_source_evidence_packet_id", "acceptance_decision_packet_id",
                     "target_field_path"):
            _native_require(packet[name] == ledger[name] == decision[name], "accepted packet/ledger/decision association differs")
        _native_require(ledger["accepted_ledger_record_id"] == decision["accepted_ledger_record_id"]
            and ledger["acceptance_decision_receipt_ref"] == decision["acceptance_decision_packet_id"],
            "accepted ledger decision differs")
        for name in ("retrieval_manifest_id", "source_target_id", "retrieval_target_id", "venue_id", "platform_scope",
                     "applicability_scope", "canonical_text_digest_sha256", "source_digest_sha256", "source_locator",
                     "source_locator_type", "source_locator_status", "source_authority_class", "accepted_at_utc", "accepted_by_tool"):
            _native_require(packet[name] == ledger[name], "accepted source provenance differs: " + name)
        _native_require(packet["production_external_fact_authority"] is ledger["production_external_fact_authority"]
            is decision["production_external_fact_authority"] and type(packet["production_external_fact_authority"]) is bool,
            "accepted source fact classification differs")
        external = external and packet["production_external_fact_authority"] is True and packet["source_authority_class"] in accepted.OFFICIAL_SOURCE_CLASSES
        conflict, revalidation = bundle["conflict_report"], bundle["revalidation_status"]
        _native_require(type(conflict) is type(revalidation) is dict
            and decision["conflict_report_ref"] == packet["conflict_check_id"] == conflict["conflict_check_id"]
            and decision["revalidation_status_ref"] == packet["revalidation_trigger_id"] == revalidation["revalidation_trigger_id"],
            "accepted source conflict/revalidation association differs")
        for row in (conflict,revalidation):
            _native_require(row["candidate_source_evidence_packet_id"] == packet["candidate_source_evidence_packet_id"]
                and row["target_field_path"] == packet["target_field_path"] and row["runtime_live_use_allowed_flag"] is False
                and row["connector_semantic_binding_allowed_flag"] is False, "accepted source review scope differs")
        _native_require(conflict["acceptance_blocked_by_conflict"] is False and conflict["owner_or_risk_review_required"] is False
            and conflict["conflict_state"] == packet["conflict_state"] == ledger["conflict_state"]
            and conflict["conflict_state"] in accepted.VALID_CONFLICT_STATES
            and conflict["conflict_resolution_state"] == packet["conflict_resolution_state"] == ledger["conflict_resolution_state"]
            and conflict["conflict_resolution_state"] in accepted.VALID_CONFLICT_RESOLUTION_STATES
            and revalidation["acceptance_blocked_by_staleness"] is False
            and revalidation["revalidation_state"] == ledger["revalidation_state"]
            and revalidation["revalidation_state"] in accepted.FRESH_REVALIDATION_STATES
            and revalidation["revalidation_due_condition"] == packet["revalidation_due_condition"]
            and revalidation["revalidation_due_condition"] in accepted.FRESH_REVALIDATION_DUE_CONDITIONS,
            "accepted source conflict or revalidation is not current")
        external = external and revalidation["revalidation_state"] != "TEST_FIXTURE_CURRENT"
        raw, canonical = original_by_id[packet_id]
        raw_digest, canonical_digest = hashlib.sha256(raw).hexdigest(), hashlib.sha256(canonical).hexdigest()
        _native_require(raw_digest == packet["raw_capture_digest_sha256"]
            and canonical_digest == packet["canonical_text_digest_sha256"] == ledger["canonicalized_content_digest"],
            "accepted original bytes differ from provenance")
        locator = packet["exact_quote_or_machine_field_locator"]
        _native_require(type(locator) is dict and packet["quote_span_locator_or_machine_field_locator"] == ledger["accepted_value_locator"]
            and packet["quote_span_locator_or_machine_field_locator"] in {"QUOTE_SPAN_LOCATOR","MACHINE_FIELD_LOCATOR"}
            and locator.get("quote_span_locator") == ledger["quote_span_locator"]
            and locator.get("machine_field_locator") == ledger["machine_field_locator"]
            and type(locator.get("quote_span_locator" if ledger["accepted_value_locator"] == "QUOTE_SPAN_LOCATOR" else "machine_field_locator")) is dict,
            "accepted exact value locator differs")
        known = max(_native_utc_nanoseconds(packet[name]) for name in ("source_retrieved_at_utc","accepted_at_utc"))
        _native_require(known <= source_binding.known_at_ns
            and _native_utc_nanoseconds(review_facts.factual_checked_at_utc.isoformat()) <= source_binding.known_at_ns
            and source_binding.expires_at_ns <= _native_utc_nanoseconds(review_facts.source_expires_at_utc.isoformat())
            and source_binding.review_scope_ref == review_facts.document_ref, "accepted field knowledge/review interval differs")
        value = packet["extracted_fact_payload"]
        expected_keys = {"schema_version","profile_id","legal_product_ref","source_contract_version",
                         "allowed_operation_ids","permitted_consumer_ids","field_bindings"}
        _native_require(type(value) is dict and expected_keys <= set(value) <= expected_keys | {
            "venue_semantics", "fee_rules", "account_applicability", "contract_terms"}
            and packet["extracted_fact_type"] == ledger["accepted_value_type"] == "OBJECT"
            and packet["accepted_value_label"] == ledger["accepted_value_label"]
            and value["schema_version"] == "PUBLIC_ACCEPTED_FIELD_BINDINGS_V1"
            and value["profile_id"] == source_binding.profile_id.value
            and value["legal_product_ref"] == source_binding.legal_product_ref
            and value["source_contract_version"] in source_binding.source_contract_versions
            and packet["source_target_id"] in source_binding.source_ids
            and set(value["allowed_operation_ids"]) == set(source_binding.allowed_operation_ids)
            and set(value["permitted_consumer_ids"]) == set(source_binding.permitted_consumer_ids),
            "accepted public field fact scope differs")
        scope = packet["applicability_scope"]
        venue = {Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: "KALSHI",
                 Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: "POLYMARKET",
                 Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: "GEMINI"}[source_binding.profile_id]
        _native_require(type(scope) is dict and scope.get("venue_id") == packet["venue_id"]
            and scope.get("platform_scope") == packet["platform_scope"]
            and packet["venue_id"] in {venue, "PREDICTION_MARKETS_GENERAL"}
            and packet["platform_scope"] in {venue, "PREDICTION_MARKETS_GENERAL"}
            and scope.get("wildcard_scope_allowed") is False and scope.get("cross_venue_scope_allowed") is False
            and packet["target_field_path"] in scope.get("target_field_paths", ()), "accepted field applicability is not exact")
        rows = value["field_bindings"]
        _native_require(type(rows) is list and 0 < len(rows) <= 4096, "accepted material field vector absent")
        for row in rows:
            _native_require(type(row) is list and len(row) == 5 and all(type(item) is str for item in row),
                            "accepted material field vector invalid")
            name, wire, unit, pointer, transform = row
            projected.append((name,wire,unit,packet_id,pointer,transform))
        if "venue_semantics" in value:
            from ..qku_computation_control_plane.source_policy import _validate_public_semantic_facts_v1

            _validate_public_semantic_facts_v1(profile_id=source_binding.profile_id,
                facts=value["venue_semantics"], field_bindings=tuple(projected), original_ref=packet_id)
        if "fee_rules" in value:
            from ..qku_computation_control_plane.source_policy import _project_public_fee_rule_facts_v1

            _project_public_fee_rule_facts_v1(source_binding=source_binding,
                facts=value["fee_rules"], field_bindings=tuple(projected), original_ref=packet_id)
        if "account_applicability" in value:
            from ..qku_computation_control_plane.source_policy import _project_public_account_applicability_facts_v1

            _project_public_account_applicability_facts_v1(source_binding=source_binding,
                facts=value["account_applicability"], field_bindings=tuple(projected), original_ref=packet_id)
        if "contract_terms" in value:
            from .binding import _validate_public_contract_terms_v1

            _validate_public_contract_terms_v1(facts=value["contract_terms"],field_bindings=tuple(projected),original_ref=packet_id)
        claim = "PUBLIC_ACCEPTED_SOURCE_V1::" + packet_id + "::" + hashlib.sha256(raw_bundle).hexdigest()
        _native_require(claim in review_facts.reviewed_claims, "accepted source bundle lacks its exact authenticated-review claim")
        claims.append(claim)
        snapshots.append(_public_scalar_tree_v1(bundle))
    _native_require(packet_ids == set(source_binding.original_evidence_refs) == set(original_by_id)
        and len(projected) == len(source_binding.field_bindings) and set(projected) == set(source_binding.field_bindings),
        "accepted material fields do not exactly cover the selected source binding")
    return (source_binding, tuple(claims), tuple(snapshots), originals, external)


DEPENDENCY_STATE_BY_EVENT_KIND = {
    "MARKET_CATALOG_INPUT_METADATA_ENVELOPE": "ACCEPTED_SOURCE_GATED",
    "MARKET_STATUS_INPUT_METADATA_ENVELOPE": "CONNECTOR_SEMANTIC_GATED",
    "PRICE_QUOTE_INPUT_METADATA_ENVELOPE": "SOURCE_REQUIRED",
    "TRADE_PRINT_INPUT_METADATA_ENVELOPE": "CONNECTOR_SEMANTIC_REQUIRED",
    "ORDERBOOK_INPUT_METADATA_ENVELOPE_FOR_PR115_ONLY": "SOURCE_REQUIRED",
    "ORDERBOOK_DELTA_INPUT_METADATA_ENVELOPE_FOR_PR115_ONLY": (
        "CONNECTOR_SEMANTIC_REQUIRED"
    ),
    "SETTLEMENT_STATUS_INPUT_METADATA_ENVELOPE": "ACCEPTED_SOURCE_GATED",
    "VENUE_HEALTH_INPUT_METADATA_ENVELOPE": "CONNECTOR_SEMANTIC_GATED",
}

INPUT_CLASS_BY_STATE = {
    "ACCEPTED_SOURCE_GATED": "ACCEPTED_SOURCE_GATED_MARKET_DATA_INPUT_METADATA",
    "CONNECTOR_SEMANTIC_GATED": (
        "CONNECTOR_SEMANTIC_REQUIRED_MARKET_DATA_INPUT_PLACEHOLDER"
    ),
    "SOURCE_REQUIRED": "SOURCE_REQUIRED_MARKET_DATA_INPUT_PLACEHOLDER",
    "CONNECTOR_SEMANTIC_REQUIRED": (
        "CONNECTOR_SEMANTIC_REQUIRED_MARKET_DATA_INPUT_PLACEHOLDER"
    ),
    "BLOCKED_SCOPE_MISMATCH": "SOURCE_REQUIRED_MARKET_DATA_INPUT_PLACEHOLDER",
}


def dependency_state_for(event_kind_class: str) -> str:
    return DEPENDENCY_STATE_BY_EVENT_KIND[event_kind_class]


def adapter_input_class_for(dependency_state: str) -> str:
    return INPUT_CLASS_BY_STATE[dependency_state]


def dependency_id(scope_value: str, event_kind_class: str) -> str:
    return f"PR132_{scope_value}_{event_kind_class}_SOURCE_DEPENDENCY_V1"


def _accepted_source_ref(scope_value: str, state: str) -> str | None:
    if state in {"ACCEPTED_SOURCE_GATED", "CONNECTOR_SEMANTIC_GATED"}:
        return f"PR106_ACCEPTED_SOURCE_PACKET_REF_METADATA_ONLY_{scope_value}"
    return None


def _connector_semantic_ref(scope_value: str, state: str) -> str | None:
    if state == "CONNECTOR_SEMANTIC_GATED":
        return f"PR124_CONNECTOR_SEMANTIC_BINDING_REF_METADATA_ONLY_{scope_value}"
    return None


def build_source_dependencies() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for scope_ref in policy.stage1_scope_refs():
        event_kinds = (
            policy.ALLOWED_CANONICAL_EVENT_KIND_CLASSES
            if scope_ref.scope_kind == "venue"
            else ("VENUE_HEALTH_INPUT_METADATA_ENVELOPE",)
        )
        for event_kind in event_kinds:
            state = dependency_state_for(event_kind)
            scope_value = scope_ref.value
            records.append(
                {
                    **policy.common_record_fields("MARKET_DATA_SOURCE_DEPENDENCY"),
                    **policy.scope_field(scope_ref),
                    "dependency_id": dependency_id(scope_value, event_kind),
                    "target_field_class": event_kind,
                    "dependency_state": state,
                    "accepted_source_packet_ref": _accepted_source_ref(
                        scope_value,
                        state,
                    ),
                    "connector_semantic_binding_ref": _connector_semantic_ref(
                        scope_value,
                        state,
                    ),
                    "revalidation_state_ref": (
                        f"PR125_REVALIDATION_STATE_REF_METADATA_ONLY_{scope_value}"
                    ),
                    "live_use_allowed": False,
                }
            )
    return records


def build_no_live_network_attestations(
    scanned_artifact_refs: list[str],
) -> list[dict[str, object]]:
    return [
        {
            **policy.common_record_fields("MARKET_DATA_NO_LIVE_NETWORK_ATTESTATION"),
            "attestation_id": "PR132_MARKET_DATA_NO_LIVE_NETWORK_ATTESTATION_V1",
            "scanned_artifact_refs": scanned_artifact_refs,
            "rest_client_import_count": 0,
            "websocket_client_import_count": 0,
            "socket_import_count": 0,
            "network_io_count": 0,
            "venue_api_call_count": 0,
            "live_market_data_fetch_count": 0,
            "environment_credential_read_count": 0,
            "credential_provider_call_count": 0,
            "production_connector_client_count": 0,
            "private_state_fetch_count": 0,
            "orderbook_snapshot_created_count": 0,
            "runtime_resolver_snapshot_created_count": 0,
            "historical_dataset_digest_created_count": 0,
            "feature_vector_created_count": 0,
            "trading_signal_created_count": 0,
            "quantum_feature_computation_created_count": 0,
            "quantum_optimizer_input_created_count": 0,
            "quantum_trading_signal_created_count": 0,
            "quantum_backend_simulator_optimizer_execution_count": 0,
            "quantum_advantage_claim_created_count": 0,
            "order_authority_count": 0,
            "order_execution_count": 0,
            "logs_contain_live_market_payload": False,
            "reports_contain_live_market_payload": False,
            "fixtures_contain_live_market_payload": False,
        }
    ]


def build_rejection_receipts() -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    for index, reason in enumerate(policy.REJECTION_REASON_CODES, start=1):
        receipts.append(
            {
                **policy.common_record_fields("VENUE_MARKET_DATA_ADAPTER_REJECTION"),
                "rejection_id": f"PR132_MARKET_DATA_ADAPTER_REJECTION_{index:02d}_V1",
                "rejected_action_or_payload_class": reason.replace("BLOCKED_", ""),
                "rejected_reason_code": reason,
                "rejected_artifact_ref": f"PR132_BLOCKED_FIXTURE_{index:02d}",
                "raw_live_payload_stored": False,
                "live_fetch_performed": False,
                "source_fact_accepted": False,
                "connector_semantic_binding_created": False,
                "official_semantics_fabricated": False,
                "validator_fail_closed": True,
            }
        )
    return receipts


def dependency_lookup(
    dependencies: list[Mapping[str, object]],
) -> dict[tuple[str, str], Mapping[str, object]]:
    return {
        (
            str(record.get("venue_id") or record.get("scope_id")),
            str(record["target_field_class"]),
        ): record
        for record in dependencies
    }


@dataclass(frozen=True, slots=True)
class PITSourceDependencyV2:
    dependency_id: str
    profile_id: Stage1VenueProfileIdV1
    event_kind: PITEventKindV2
    access_class: policy.PITAccessClassV1
    host: str
    path_or_channel: str
    read_action: policy.PITReadActionV1
    wire_dialect: str
    depth_class: PITDepthClassV2
    sequence_model: str
    recovery_model: str
    rights_receipt_required: bool
    source_currentization_receipt_required: bool
    credential_alias_required: bool
    no_private_state: bool
    no_write: bool
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1 or self.profile_id not in (
            policy.PIT_SELECTED_SCOPE_V2.selected_profile_ids
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "source dependency profile is outside selected scope",
            )
        if type(self.event_kind) is not PITEventKindV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "event_kind must be exact PITEventKindV2",
            )
        if type(self.access_class) is not policy.PITAccessClassV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "access_class must be exact PITAccessClassV1",
            )
        if type(self.read_action) is not policy.PITReadActionV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "read_action must be exact PITReadActionV1",
            )
        if type(self.depth_class) is not PITDepthClassV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TOP_LEVEL_DEPTH_ONLY,
                "depth_class must be exact PITDepthClassV2",
            )
        for name in (
            "dependency_id",
            "host",
            "path_or_channel",
            "wire_dialect",
            "sequence_model",
            "recovery_model",
        ):
            value = getattr(self, name)
            if type(value) is not str or not value or value != value.strip():
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be canonical nonempty text",
                )
        for name in (
            "rights_receipt_required",
            "source_currentization_receipt_required",
            "credential_alias_required",
            "no_private_state",
            "no_write",
        ):
            if type(getattr(self, name)) is not bool:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact boolean",
                )
        if (
            not self.rights_receipt_required
            or not self.source_currentization_receipt_required
            or not self.no_private_state
            or not self.no_write
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "PIT source dependency requires source/rights and zero write authority",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "PIT source dependency must carry exact NO_EFFECTS_V1",
            )


def _pit_dependency_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


_PIT_DEPENDENCY_EVENT_KINDS = MappingProxyType({
    Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: (
        PITEventKindV2.CATALOG,
        PITEventKindV2.LIFECYCLE,
        PITEventKindV2.BOOK_SNAPSHOT,
        PITEventKindV2.BOOK_DELTA,
        PITEventKindV2.BBO,
        PITEventKindV2.TRADE,
        PITEventKindV2.SETTLEMENT,
        PITEventKindV2.SOURCE_STATUS,
    ),
    Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: (
        PITEventKindV2.CATALOG,
        PITEventKindV2.LIFECYCLE,
        PITEventKindV2.BOOK_REPLACEMENT,
        PITEventKindV2.BBO,
        PITEventKindV2.TRADE,
        PITEventKindV2.SETTLEMENT,
        PITEventKindV2.HEARTBEAT,
        PITEventKindV2.SOURCE_STATUS,
    ),
    Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: (
        PITEventKindV2.CATALOG,
        PITEventKindV2.LIFECYCLE,
        PITEventKindV2.BOOK_SNAPSHOT,
        PITEventKindV2.BOOK_DELTA,
        PITEventKindV2.TRADE,
        PITEventKindV2.SETTLEMENT,
        PITEventKindV2.HEARTBEAT,
        PITEventKindV2.SOURCE_STATUS,
    ),
})


def _pit_dependency_surface(
    profile_id: Stage1VenueProfileIdV1,
    event_kind: PITEventKindV2,
) -> tuple[policy.PITAccessClassV1, str, policy.PITReadActionV1]:
    protocol = policy._pit_profile_protocol_policy_v2(profile_id)
    if profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT and event_kind is PITEventKindV2.LIFECYCLE:
        return (policy.PITAccessClassV1.PUBLIC_UNAUTHENTICATED_READ,
                "prediction_markets.contractStatus", policy.PITReadActionV1.WEBSOCKET_SUBSCRIBE)
    if profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT:
        authenticated = (
            policy.PITAccessClassV1.AUTHENTICATED_PUBLIC_MARKET_DATA_READ
        )
        public = policy.PITAccessClassV1.PUBLIC_UNAUTHENTICATED_READ
        if event_kind is PITEventKindV2.BOOK_SNAPSHOT:
            return (
                authenticated,
                "orderbook_delta",
                policy.PITReadActionV1.WEBSOCKET_RECOVERY,
            )
        if event_kind is PITEventKindV2.TRADE:
            return public, "/historical/trades", policy.PITReadActionV1.GET
        if event_kind is PITEventKindV2.SOURCE_STATUS:
            return (
                authenticated,
                "/portfolio/account_limits",
                policy.PITReadActionV1.GET,
            )
        if event_kind is PITEventKindV2.HEARTBEAT:
            return (
                authenticated,
                "server_ping",
                policy.PITReadActionV1.WEBSOCKET_PONG,
            )
        if event_kind is PITEventKindV2.BOOK_DELTA:
            return (
                authenticated,
                "orderbook_delta",
                policy.PITReadActionV1.WEBSOCKET_SUBSCRIBE,
            )
        if event_kind is PITEventKindV2.LIFECYCLE:
            return (
                authenticated,
                "market_lifecycle_v2",
                policy.PITReadActionV1.WEBSOCKET_SUBSCRIBE,
            )
        return public, "/markets", policy.PITReadActionV1.GET
    websocket_kinds = {
        PITEventKindV2.BOOK_SNAPSHOT,
        PITEventKindV2.BOOK_DELTA,
        PITEventKindV2.BOOK_REPLACEMENT,
        PITEventKindV2.BBO,
        PITEventKindV2.TRADE,
        PITEventKindV2.HEARTBEAT,
        PITEventKindV2.SOURCE_STATUS,
    }
    if event_kind in websocket_kinds:
        access = (
            policy.PITAccessClassV1.PUBLIC_UNAUTHENTICATED_READ
            if profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT
            else policy.PITAccessClassV1.AUTHENTICATED_PUBLIC_MARKET_DATA_READ
        )
        if profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT:
            channel_by_kind = {
                PITEventKindV2.BOOK_SNAPSHOT: "prediction_markets.depth",
                PITEventKindV2.BOOK_DELTA: "prediction_markets.depth",
                PITEventKindV2.BBO: "prediction_markets.bookTicker",
                PITEventKindV2.TRADE: "prediction_markets.trades",
                PITEventKindV2.SOURCE_STATUS: "prediction_markets.depth",
            }
            channel = channel_by_kind[event_kind]
        else:
            channel = "markets"
        return access, channel, policy.PITReadActionV1.WEBSOCKET_SUBSCRIBE
    return (
        policy.PITAccessClassV1.PUBLIC_UNAUTHENTICATED_READ,
        _pit_dependency_text(protocol["allowed_paths"][0], "allowed path"),
        policy.PITReadActionV1.GET,
    )


def _build_pit_source_dependencies_v2() -> tuple[PITSourceDependencyV2, ...]:
    rows: list[PITSourceDependencyV2] = []

    def append_row(
        *,
        profile_id: Stage1VenueProfileIdV1,
        event_kind: PITEventKindV2,
        access_class: policy.PITAccessClassV1,
        path_or_channel: str,
        read_action: policy.PITReadActionV1,
    ) -> None:
        protocol = policy._pit_profile_protocol_policy_v2(profile_id)
        host = (
            _pit_dependency_text(
                protocol["production_rest_base"], "production_rest_base"
            )
            if read_action is policy.PITReadActionV1.GET
            else _pit_dependency_text(protocol["websocket_url"], "websocket_url")
        )
        if event_kind is PITEventKindV2.BOOK_SNAPSHOT:
            depth_class = PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT
        elif event_kind is PITEventKindV2.BOOK_REPLACEMENT:
            depth_class = (
                PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT
                if read_action is policy.PITReadActionV1.GET
                else PITDepthClassV2.PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME
            )
        elif event_kind is PITEventKindV2.BBO:
            depth_class = PITDepthClassV2.BBO_ONLY
        else:
            depth_class = protocol["depth_class"]
        rows.append(
            PITSourceDependencyV2(
                dependency_id=(
                    f"S1-PIT-DEPENDENCY::{profile_id.value}::"
                    f"{event_kind.value}::{access_class.value}"
                ),
                profile_id=profile_id,
                event_kind=event_kind,
                access_class=access_class,
                host=host,
                path_or_channel=path_or_channel,
                read_action=read_action,
                wire_dialect=_pit_dependency_text(
                    protocol["wire_dialect_policy"], "wire_dialect_policy"
                ),
                depth_class=depth_class,
                sequence_model=_pit_dependency_text(
                    protocol["sequence_model"], "sequence_model"
                ),
                recovery_model=_pit_dependency_text(
                    protocol["recovery_model"], "recovery_model"
                ),
                rights_receipt_required=True,
                source_currentization_receipt_required=True,
                credential_alias_required=(
                    access_class
                    is policy.PITAccessClassV1.AUTHENTICATED_PUBLIC_MARKET_DATA_READ
                ),
                no_private_state=True,
                no_write=True,
            )
        )

    for profile_id in policy.PIT_SELECTED_SCOPE_V2.serialization:
        for event_kind in _PIT_DEPENDENCY_EVENT_KINDS[profile_id]:
            access_class, path_or_channel, read_action = _pit_dependency_surface(
                profile_id, event_kind
            )
            append_row(
                profile_id=profile_id,
                event_kind=event_kind,
                access_class=access_class,
                path_or_channel=path_or_channel,
                read_action=read_action,
            )
        if profile_id is Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT:
            append_row(
                profile_id=profile_id,
                event_kind=PITEventKindV2.BOOK_REPLACEMENT,
                access_class=policy.PITAccessClassV1.PUBLIC_UNAUTHENTICATED_READ,
                path_or_channel="/v1/markets/{slug}/book",
                read_action=policy.PITReadActionV1.GET,
            )
        if profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT:
            append_row(
                profile_id=profile_id,
                event_kind=PITEventKindV2.TRADE,
                access_class=(
                    policy.PITAccessClassV1.AUTHENTICATED_PUBLIC_MARKET_DATA_READ
                ),
                path_or_channel="trade",
                read_action=policy.PITReadActionV1.WEBSOCKET_SUBSCRIBE,
            )
    return tuple(rows)


PIT_SOURCE_DEPENDENCIES_V2 = _build_pit_source_dependencies_v2()
_PIT_SOURCE_DEPENDENCY_BY_KEY_V2 = MappingProxyType({
    (row.profile_id, row.event_kind, row.access_class): row
    for row in PIT_SOURCE_DEPENDENCIES_V2
})
if len(_PIT_SOURCE_DEPENDENCY_BY_KEY_V2) != len(PIT_SOURCE_DEPENDENCIES_V2):
    raise RuntimeError("PIT source-dependency keys must be unique")


def _resolve_pit_source_dependency_v2(
    profile_id: Stage1VenueProfileIdV1,
    event_kind: PITEventKindV2,
    access_class: policy.PITAccessClassV1,
) -> PITSourceDependencyV2:
    if (
        type(profile_id) is not Stage1VenueProfileIdV1
        or type(event_kind) is not PITEventKindV2
        or type(access_class) is not policy.PITAccessClassV1
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "source dependency resolution requires exact typed keys",
        )
    try:
        return _PIT_SOURCE_DEPENDENCY_BY_KEY_V2[
            (profile_id, event_kind, access_class)
        ]
    except KeyError as exc:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
            "no selected source dependency matches the exact key",
        ) from exc
