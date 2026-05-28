"""Deterministic PR160 route arbitration."""

from __future__ import annotations

from typing import Any, Mapping


ARBITRATION_POLICY_STEPS = (
    "existing_pr159_accepted_packet_exact_match",
    "existing_pr159_unresolved_official_source_fill_path",
    "official_online_doc_classification_only_if_used",
    "owner_internal_policy_or_route_metadata",
    "private_doc_attestation_required",
    "exact_agent_binding_required",
    "generated_derivative_from_accepted_inputs",
    "formula_only_no_external_fact",
    "quantum_classical_metadata_only",
    "connector_semantic_or_runtime_receipt_future",
    "owner_choice_if_multiple_routes_remain",
    "invalid_or_unsupported_fail_closed",
)


def selected_route(candidate_matrix_record: Mapping[str, Any]) -> Mapping[str, Any]:
    routes = candidate_matrix_record.get("candidate_routes")
    if isinstance(routes, list) and routes:
        first = routes[0]
        if isinstance(first, Mapping):
            return first
    return {}


def build_arbitration_audit(
    candidate_matrix: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in candidate_matrix:
        selected = selected_route(item)
        output.append(
            {
                "PR154_target_id": item.get("PR154_target_id"),
                "arbitration_policy_steps_applied": list(ARBITRATION_POLICY_STEPS),
                "candidate_route_count": item.get("candidate_route_count"),
                "selected_final_route_class": selected.get("candidate_route_class"),
                "selected_basis_class": selected.get("basis_class"),
                "selected_authority_class": selected.get("authority_class"),
                "deterministic_arbitration_flag": True,
                "owner_choice_required_flag": False,
                "source_acceptance_executed_flag": False,
                "runtime_or_live_execution_flag": False,
                "arbitration_notes": "Single deterministic route selected from prior artifacts; no PR160 value materialization.",
            }
        )
    return output
