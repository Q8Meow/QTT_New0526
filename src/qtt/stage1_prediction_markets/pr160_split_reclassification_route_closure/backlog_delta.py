"""Post-PR160 backlog delta construction."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build(decisions: list[Mapping[str, Any]]) -> dict[str, Any]:
    route_counts: dict[str, int] = {}
    for item in decisions:
        route = str(item["final_route_class"])
        route_counts[route] = route_counts.get(route, 0) + 1
    source_count = route_counts.get(
        c.ReclassificationFinalRouteClass.OFFICIAL_SOURCE_REQUIRED_ROUTE_PR159R.value,
        0,
    )
    return {
        "pre_PR160_split_reclassification_count": c.EXPECTED_SPLIT_RECLASSIFICATION_RECORDS,
        "post_PR160_generic_split_reclassification_count": 0,
        "count_added_to_PR159R_source_queue": source_count,
        "count_added_to_PR161_materialization_route": source_count
        + route_counts.get(
            c.ReclassificationFinalRouteClass.ATOMICROWS_SOURCE_VALUE_MATERIALIZATION_ROUTE_PR161.value,
            0,
        ),
        "count_added_to_PR163_agent_binding_route": route_counts.get(
            c.ReclassificationFinalRouteClass.EXACT_AGENT_BINDING_ROUTE_PR163.value,
            0,
        ),
        "count_added_to_owner_policy_review": route_counts.get(
            c.ReclassificationFinalRouteClass.OWNER_INTERNAL_POLICY_ROUTE.value,
            0,
        ),
        "count_added_to_private_doc_attestation": route_counts.get(
            c.ReclassificationFinalRouteClass.PRIVATE_DOC_ATTESTATION_ROUTE.value,
            0,
        ),
        "count_added_to_connector_runtime_future": route_counts.get(
            c.ReclassificationFinalRouteClass.CONNECTOR_SEMANTIC_FUTURE_ROUTE.value,
            0,
        )
        + route_counts.get(c.ReclassificationFinalRouteClass.RUNTIME_RECEIPT_FUTURE_ROUTE.value, 0),
        "count_added_to_formula_derived_route": route_counts.get(
            c.ReclassificationFinalRouteClass.FORMULA_ONLY_DERIVED_ROUTE.value,
            0,
        )
        + route_counts.get(
            c.ReclassificationFinalRouteClass.GENERATED_DERIVATIVE_FROM_ACCEPTED_INPUTS_ROUTE.value,
            0,
        ),
        "count_added_to_quantum_metadata_route": route_counts.get(
            c.ReclassificationFinalRouteClass.QUANTUM_CLASSICAL_METADATA_ONLY_ROUTE.value,
            0,
        ),
        "count_requiring_owner_classification_decision": route_counts.get(
            c.ReclassificationFinalRouteClass.OWNER_CLASSIFICATION_DECISION_REQUIRED_WITH_CHOICES.value,
            0,
        ),
        "total_remaining_PR154_unresolved_after_PR160": 0,
        "total_remaining_AtomicRows_unresolved_after_PR160_if_derivable": "unchanged_by_PR160_route_closure_only",
        "route_counts": dict(sorted(route_counts.items())),
        "notes_on_overlap_and_non_double_counting": "PR159R and PR161 counts intentionally overlap for source-backed materialization flow; PR160 does not change the 342 PR154 or 4183 AtomicRows universes.",
    }
