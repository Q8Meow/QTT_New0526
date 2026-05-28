"""AtomicRows 845 source-required completion records."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build_atomicrows_completion_records(
    atomic_targets: list[Mapping[str, Any]],
    overlay_by_row: dict[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in atomic_targets:
        row_id = str(target["row_id"])
        overlay = overlay_by_row.get(row_id, {})
        records.append(
            {
                "row_id": row_id,
                "family_id": target["family_id"],
                "parameter_id": target["parameter_id"],
                "formula_algorithm_edge_alpha_id_or_null": target["formula_algorithm_edge_alpha_id_or_null"],
                "source_requirement_class": target["source_requirement_class"],
                "PR158_selection_readiness_ref": target["PR158_selection_readiness_ref"],
                "PR157_completion_ref": target["PR157_completion_ref"],
                "target_field_id": target["target_field_id"],
                "requested_value_name": target["requested_value_name"],
                "requested_value_type": target["requested_value_type"],
                "requested_unit_or_basis": target["requested_unit_or_basis"],
                "requested_scale": target["requested_scale"],
                "platform_scope": target["platform_scope"],
                "venue_scope": target["venue_scope"],
                "market_scope": target["market_scope"],
                "strategy_scope": target["strategy_scope"],
                "source_field_class": target["source_field_class"],
                "day1_source_priority_tier": target["day1_source_priority_tier"],
                "official_source_target_ids": target["official_source_target_ids"],
                "discovered_official_source_refs": target["discovered_official_source_refs"],
                "candidate_packet_refs": [],
                "accepted_source_packet_ref_or_null": None,
                "acceptance_decision": c.SourceAcceptanceDecision.DEFERRED_FUTURE_SOURCE_RETRY.value,
                "accepted_value_or_null": None,
                "canonical_value_or_null": None,
                "canonical_unit_or_basis_or_null": None,
                "canonical_scale_or_null": None,
                "quote_span_or_machine_field_locator_or_null": None,
                "conflict_clearance_status": c.ConflictStatus.NO_CONFLICT.value,
                "freshness_state": c.FreshnessState.EVENT_REVALIDATION_REQUIRED.value,
                "revalidation_class": target["revalidation_class"],
                "materiality_class": target["source_materiality_class"],
                "completion_status": c.SourceTargetState.UNRESOLVED_WITH_FILL_PATH.value,
                "blocker_class": c.SourceEvidenceState.BLOCKED_AMBIGUOUS.value,
                "exact_next_action_if_unresolved": (
                    "Capture official documented range, limit, schedule, threshold, policy, API constraint, "
                    "venue constraint, provider constraint, or rulebook specification for this exact row target."
                ),
                "future_route": c.FutureRoute.PR161_ATOMICROWS_SOURCE_VALUE_MATERIALIZATION.value,
                "scoring_readiness_update": "SOURCE_NOT_READY_METADATA_ONLY",
                "trade_context_readiness_update": "SOURCE_NOT_READY_METADATA_ONLY",
                "low_latency_snapshot_update": "SOURCE_NOT_READY_METADATA_ONLY",
                "quantum_classical_compatibility": overlay.get("quantum_classical_compatibility") or [],
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return sorted(records, key=lambda item: item["row_id"])

