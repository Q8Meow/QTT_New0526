from __future__ import annotations

from typing import Any, Mapping


FIXTURE_AUTHORITY_CLASS = "TEST_FIXTURE_NOT_EXTERNAL_FACT"

INFO_ONLY = "INFO_ONLY"
LOW_RISK = "LOW_RISK"
MEDIUM_RISK = "MEDIUM_RISK"
HIGH_RISK = "HIGH_RISK"
CONNECTOR_BLOCKING = "CONNECTOR_BLOCKING"
LIVE_TRADING_BLOCKING = "LIVE_TRADING_BLOCKING"

MATERIALITY_CLASSES = (
    INFO_ONLY,
    LOW_RISK,
    MEDIUM_RISK,
    HIGH_RISK,
    CONNECTOR_BLOCKING,
    LIVE_TRADING_BLOCKING,
)

RECORD_AND_KEEP_BINDING_IF_TARGET_FIELD_UNCHANGED = (
    "RECORD_AND_KEEP_BINDING_IF_TARGET_FIELD_UNCHANGED"
)
RECORD_REVALIDATION_AND_KEEP_BINDING_IF_VALIDATOR_CONFIRMS_NO_TARGET_FIELD_DELTA = (
    "RECORD_REVALIDATION_AND_KEEP_BINDING_IF_VALIDATOR_CONFIRMS_NO_TARGET_FIELD_DELTA"
)
REQUIRE_REVALIDATION_FOR_AFFECTED_TARGET_FIELD = (
    "REQUIRE_REVALIDATION_FOR_AFFECTED_TARGET_FIELD"
)
REQUIRE_OWNER_OR_RISK_REVIEW_IF_USED_BY_STRATEGY_OR_COST_MODEL = (
    "REQUIRE_OWNER_OR_RISK_REVIEW_IF_USED_BY_STRATEGY_OR_COST_MODEL"
)
DOWNGRADE_AFFECTED_CONNECTOR_BINDING_TO_REVALIDATION_REQUIRED = (
    "DOWNGRADE_AFFECTED_CONNECTOR_BINDING_TO_REVALIDATION_REQUIRED"
)
MARK_AFFECTED_SCOPE_NO_NEW_OR_INCREASED_EXPOSURE = (
    "MARK_AFFECTED_SCOPE_NO_NEW_OR_INCREASED_EXPOSURE"
)

SOURCE_CHANGE_ROUTES = (
    RECORD_AND_KEEP_BINDING_IF_TARGET_FIELD_UNCHANGED,
    RECORD_REVALIDATION_AND_KEEP_BINDING_IF_VALIDATOR_CONFIRMS_NO_TARGET_FIELD_DELTA,
    REQUIRE_REVALIDATION_FOR_AFFECTED_TARGET_FIELD,
    REQUIRE_OWNER_OR_RISK_REVIEW_IF_USED_BY_STRATEGY_OR_COST_MODEL,
    DOWNGRADE_AFFECTED_CONNECTOR_BINDING_TO_REVALIDATION_REQUIRED,
    MARK_AFFECTED_SCOPE_NO_NEW_OR_INCREASED_EXPOSURE,
)

_ROUTE_BY_CLASS = {
    INFO_ONLY: RECORD_AND_KEEP_BINDING_IF_TARGET_FIELD_UNCHANGED,
    LOW_RISK: RECORD_REVALIDATION_AND_KEEP_BINDING_IF_VALIDATOR_CONFIRMS_NO_TARGET_FIELD_DELTA,
    MEDIUM_RISK: REQUIRE_REVALIDATION_FOR_AFFECTED_TARGET_FIELD,
    HIGH_RISK: REQUIRE_OWNER_OR_RISK_REVIEW_IF_USED_BY_STRATEGY_OR_COST_MODEL,
    CONNECTOR_BLOCKING: DOWNGRADE_AFFECTED_CONNECTOR_BINDING_TO_REVALIDATION_REQUIRED,
    LIVE_TRADING_BLOCKING: MARK_AFFECTED_SCOPE_NO_NEW_OR_INCREASED_EXPOSURE,
}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def classify_materiality_event(event: Mapping[str, Any]) -> dict[str, Any]:
    declared = str(event.get("declared_materiality_class", "UNKNOWN"))
    materiality_class = declared if declared in MATERIALITY_CLASSES else CONNECTOR_BLOCKING
    defaulted = materiality_class != declared
    route = _ROUTE_BY_CLASS[materiality_class]
    target_delta = event.get("target_field_delta_detected") is True
    validator_confirms_no_delta = (
        event.get("validator_confirms_no_target_field_delta") is True and not target_delta
    )
    affected_bindings = _string_list(event.get("affected_connector_binding_ids"))
    affected_paths = _string_list(event.get("affected_target_field_paths"))
    affected_scopes = _string_list(event.get("affected_scope_ids"))

    connector_binding_revalidation_required = (
        materiality_class == CONNECTOR_BLOCKING
        or defaulted
        or materiality_class == MEDIUM_RISK
        or (materiality_class == LOW_RISK and not validator_confirms_no_delta)
    )
    no_new_binding_required = materiality_class in {
        MEDIUM_RISK,
        CONNECTOR_BLOCKING,
        LIVE_TRADING_BLOCKING,
    } or defaulted
    owner_or_risk_review_required = (
        materiality_class == HIGH_RISK
        and event.get("used_by_strategy_or_cost_model") is True
    )
    no_new_or_increased_exposure_required = materiality_class == LIVE_TRADING_BLOCKING

    if materiality_class == INFO_ONLY:
        revalidation_state = (
            "REVALIDATED_NO_TARGET_FIELD_DELTA"
            if not target_delta
            else "REVALIDATED_TARGET_FIELD_DELTA_DETECTED"
        )
    elif materiality_class == LOW_RISK:
        revalidation_state = (
            "REVALIDATED_NO_TARGET_FIELD_DELTA"
            if validator_confirms_no_delta
            else "REVALIDATED_TARGET_FIELD_DELTA_DETECTED"
        )
    elif owner_or_risk_review_required:
        revalidation_state = "OWNER_OR_RISK_REVIEW_REQUIRED"
    else:
        revalidation_state = "DUE_EVENT_TRIGGERED"

    return {
        "source_change_materiality_event_id": f"PR125_MATERIALITY_{event['source_change_event_id']}",
        "source_change_event_id": event["source_change_event_id"],
        "accepted_source_evidence_packet_id": event["accepted_source_evidence_packet_id"],
        "venue_id": event["venue_id"],
        "target_field_path": event["target_field_path"],
        "declared_materiality_class": declared,
        "materiality_class": materiality_class,
        "unknown_materiality_defaulted_to_connector_blocking": defaulted,
        "source_change_route": route,
        "source_change_summary": event.get("source_change_summary", ""),
        "target_field_delta_detected": target_delta,
        "validator_confirms_no_target_field_delta": validator_confirms_no_delta,
        "used_by_strategy_or_cost_model": event.get("used_by_strategy_or_cost_model") is True,
        "affected_target_field_paths": affected_paths,
        "affected_connector_binding_ids": affected_bindings,
        "affected_scope_ids": affected_scopes,
        "revalidation_state": revalidation_state,
        "connector_binding_revalidation_state": (
            "SOURCE_REVALIDATION_REQUIRED"
            if connector_binding_revalidation_required
            else "KEEP_BINDING_IF_TARGET_FIELD_UNCHANGED"
        ),
        "connector_binding_revalidation_required": connector_binding_revalidation_required,
        "no_new_binding_required": no_new_binding_required,
        "owner_or_risk_review_required": owner_or_risk_review_required,
        "no_new_or_increased_exposure_required": no_new_or_increased_exposure_required,
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_source_change_authority": False,
        "production_revalidation_authority": False,
        "live_pretrade_use_allowed_flag": False,
        "network_io_allowed_flag": False,
        "source_retrieval_allowed_flag": False,
        "source_acceptance_allowed_flag": False,
        "connector_binding_mutation_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "live_reachability_allowed_flag": False,
    }
