"""Build the deterministic PR159 879-record retrieval target queue."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .input_discovery import seed_by_retry_target_id
from .official_source_discovery import candidate_sources_for, official_source_by_ref
from .second_pass_source_evidence import exact_source_ref_for


def _field_priority(field_name: str, fallback_priority: str | None = None) -> str:
    field = field_name.lower()
    if fallback_priority == "P0" or any(
        token in field
        for token in (
            "order",
            "fee",
            "tick",
            "payout",
            "settlement",
            "rate_limit",
            "error",
            "execution_lifecycle",
            "fill_integrity",
        )
    ):
        return c.Day1SourcePriorityTier.P0_LAUNCH_BLOCKING.value
    if fallback_priority == "P1" or any(
        token in field
        for token in (
            "orderbook",
            "market_data",
            "liquidity",
            "volume",
            "open_interest",
            "latency",
            "cashflow",
            "pnl",
            "reconciliation",
        )
    ):
        return c.Day1SourcePriorityTier.P1_TRADING_QUALITY_CRITICAL.value
    if fallback_priority == "P2" or any(token in field for token in ("parameter", "range", "quantum", "optimizer", "scoring")):
        return c.Day1SourcePriorityTier.P2_SCORING_OPTIMIZATION.value
    return c.Day1SourcePriorityTier.P3_RESEARCH_OR_METADATA.value


def _materiality(priority: str) -> str:
    if priority == c.Day1SourcePriorityTier.P0_LAUNCH_BLOCKING.value:
        return c.SourceMaterialityClass.LIVE_TRADING_BLOCKING.value
    if priority == c.Day1SourcePriorityTier.P1_TRADING_QUALITY_CRITICAL.value:
        return c.SourceMaterialityClass.CONNECTOR_BLOCKING.value
    if priority == c.Day1SourcePriorityTier.P2_SCORING_OPTIMIZATION.value:
        return c.SourceMaterialityClass.MEDIUM_RISK.value
    return c.SourceMaterialityClass.LOW_RISK.value


def _revalidation(priority: str) -> str:
    if priority in {
        c.Day1SourcePriorityTier.P0_LAUNCH_BLOCKING.value,
        c.Day1SourcePriorityTier.P1_TRADING_QUALITY_CRITICAL.value,
    }:
        return c.RevalidationClass.LIVE_CRITICAL_P1D.value
    if priority == c.Day1SourcePriorityTier.P2_SCORING_OPTIMIZATION.value:
        return c.RevalidationClass.REVALIDATION_REQUIRED_BEFORE_BINDING.value
    return c.RevalidationClass.LOW_RISK_P7D.value


def _unit_for_field(field_name: str) -> str:
    field = field_name.lower()
    if "rate" in field or "limit" in field:
        return "documented_limit_or_endpoint_policy"
    if "price" in field or "tick" in field:
        return "price_increment_or_fixed_point_dollars"
    if "size" in field or "count" in field:
        return "contract_count_or_minimum_size"
    if "payout" in field or "settlement" in field:
        return "payout_or_settlement_basis"
    if "latency" in field:
        return "latency_component_semantics"
    return "official_source_value_or_semantics"


def _scale_for_field(field_name: str) -> str:
    field = field_name.lower()
    if "rate" in field:
        return "per_endpoint_or_session_time_window"
    if "price" in field or "tick" in field:
        return "venue_market_specific"
    if "size" in field or "count" in field:
        return "per_order_or_per_market"
    return "target_field_specific"


def build_pr154_targets(
    retry_records: list[Mapping[str, Any]],
    seed_records: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    seeds = seed_by_retry_target_id(seed_records)
    targets: list[dict[str, Any]] = []
    for record in retry_records:
        target_id = str(record.get("target_id"))
        seed = seeds.get(target_id, {})
        field_name = str(seed.get("field_name") or target_id.rsplit("_", 1)[-1].lower())
        platform = str(seed.get("platform_scope") or "PREDICTION_MARKETS_GENERAL")
        priority = _field_priority(field_name, str(seed.get("priority_class") or ""))
        sources = candidate_sources_for(platform, field_name)
        exact_source_ref = exact_source_ref_for(platform, field_name)
        if exact_source_ref and exact_source_ref not in {str(source["official_source_ref"]) for source in sources}:
            exact_source = official_source_by_ref()[exact_source_ref]
            sources = [exact_source, *sources]
        targets.append(
            {
                "target_id": target_id,
                "source_population": c.PR159TargetPopulation.PR154_PUBLIC_SOURCE_RETRY_34.value,
                "retry_source_ref": c.PR157_PR154_REGISTRY_PATH.as_posix(),
                "prior_PR153R_ref_or_null": c.PR153R_SEED_MAP_PATH.as_posix(),
                "target_field_id": field_name,
                "requested_value_name": field_name,
                "requested_value_type": str(record.get("owner_value_type") or "EXTERNAL_FACT"),
                "requested_unit_or_basis": _unit_for_field(field_name),
                "requested_scale": _scale_for_field(field_name),
                "platform_scope": platform,
                "market_scope": "PREDICTION_MARKETS_GENERAL",
                "source_field_class": field_name,
                "day1_source_priority_tier": priority,
                "source_materiality_class": _materiality(priority),
                "revalidation_class": _revalidation(priority),
                "downstream_consumer_class": str(record.get("primary_consumer_class") or "CONTROL_PLANE_COMPLETION_CONSUMER"),
                "future_route_if_unresolved": c.FutureRoute.PR161_ATOMICROWS_SOURCE_VALUE_MATERIALIZATION.value,
                "official_source_target_ids": [
                    f"PR159_SOURCE_TARGET__{source['official_source_ref']}__{target_id[-32:]}"
                    for source in sources
                ],
                "discovered_official_source_refs": [source["official_source_ref"] for source in sources],
                "attempted_official_source_queries": [
                    f"{platform} official documentation {field_name.replace('_', ' ')}"
                ],
                "source_evidence_state": c.SourceEvidenceState.RETRIEVAL_TARGET_CREATED.value,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return sorted(targets, key=lambda item: item["target_id"])


def _atomic_priority(record: Mapping[str, Any]) -> str:
    family = str(record.get("family_id") or "")
    if family in {"005_execution_connector_boundary", "010_source_evidence_connector_semantic"}:
        return c.Day1SourcePriorityTier.P0_LAUNCH_BLOCKING.value
    if family == "007_latency_routing":
        return c.Day1SourcePriorityTier.P1_TRADING_QUALITY_CRITICAL.value
    return c.Day1SourcePriorityTier.P2_SCORING_OPTIMIZATION.value


def _atomic_requested_value(source_requirement_class: str) -> tuple[str, str]:
    if source_requirement_class == "PARAMETER_RANGE_SOURCE_REQUIRED":
        return "official_parameter_range_or_constraint", "OFFICIAL_RANGE_OR_CONSTRAINT"
    return "accepted_source_evidence_packet", "SOURCE_EVIDENCE_PACKET_REF"


def _first_fill_plan(record: Mapping[str, Any]) -> Mapping[str, Any]:
    plans = record.get("unresolved_field_fill_plans")
    if isinstance(plans, list) and plans and isinstance(plans[0], Mapping):
        return plans[0]
    return {}


def build_atomicrows_targets(
    source_required_records: list[Mapping[str, Any]],
    overlay_by_row: dict[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for record in source_required_records:
        row_id = str(record.get("row_id_or_row_ref"))
        overlay = overlay_by_row.get(row_id, {})
        source_class = str(record.get("source_requirement_class"))
        requested_name, requested_type = _atomic_requested_value(source_class)
        priority = _atomic_priority(record)
        fill_plan = _first_fill_plan(record)
        family_id = str(record.get("family_id") or "")
        field_id = str(fill_plan.get("missing_field_id") or requested_name)
        targets.append(
            {
                "target_id": f"PR159_ATOMICROWS_SOURCE_TARGET__{row_id}",
                "row_id": row_id,
                "family_id": family_id,
                "parameter_id": str(record.get("parameter_id") or row_id),
                "formula_algorithm_edge_alpha_id_or_null": record.get("formula_algorithm_edge_alpha_id_or_null"),
                "source_population": (
                    c.PR159TargetPopulation.ATOMICROWS_PUBLIC_EXTERNAL_SOURCE_REQUIRED_315.value
                    if source_class == "PUBLIC_EXTERNAL_SOURCE_REQUIRED"
                    else c.PR159TargetPopulation.ATOMICROWS_PARAMETER_RANGE_SOURCE_REQUIRED_530.value
                ),
                "source_requirement_class": source_class,
                "PR158_selection_readiness_ref": c.PR158_SELECTION_OVERLAY_REGISTRY_PATH.as_posix(),
                "PR157_completion_ref": c.PR157_ATOMICROWS_REGISTRY_PATH.as_posix(),
                "target_field_id": f"atomicrows.{family_id}.{field_id}",
                "requested_value_name": requested_name,
                "requested_value_type": requested_type,
                "requested_unit_or_basis": "official_documented_range_limit_policy_or_packet",
                "requested_scale": "row_target_specific",
                "platform_scope": str(overlay.get("platform_scope") or "PREDICTION_MARKETS_GENERAL"),
                "venue_scope": str(overlay.get("venue_scope") or "PREDICTION_MARKETS_GENERAL"),
                "market_scope": str(overlay.get("market_scope") or "PREDICTION_MARKETS_GENERAL"),
                "strategy_scope": str(overlay.get("strategy_scope") or "STATIC_SELECTION_READINESS_METADATA_ONLY"),
                "source_field_class": source_class,
                "day1_source_priority_tier": priority,
                "source_materiality_class": _materiality(priority),
                "revalidation_class": _revalidation(priority),
                "downstream_consumer_class": ",".join(str(item) for item in record.get("consumer_class_ids", [])),
                "future_route_if_unresolved": c.FutureRoute.PR161_ATOMICROWS_SOURCE_VALUE_MATERIALIZATION.value,
                "official_source_target_ids": [f"PR159_ATOMICROWS_SOURCE_TARGET__{row_id}"],
                "discovered_official_source_refs": [],
                "attempted_official_source_queries": [
                    f"official documentation for {family_id} {source_class.lower()}"
                ],
                "source_evidence_state": c.SourceEvidenceState.RETRIEVAL_TARGET_CREATED.value,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return sorted(targets, key=lambda item: item["row_id"])


def build_target_queue(
    retry_records: list[Mapping[str, Any]],
    seed_records: list[Mapping[str, Any]],
    source_required_records: list[Mapping[str, Any]],
    overlay_by_row: dict[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        *build_pr154_targets(retry_records, seed_records),
        *build_atomicrows_targets(source_required_records, overlay_by_row),
    ]
