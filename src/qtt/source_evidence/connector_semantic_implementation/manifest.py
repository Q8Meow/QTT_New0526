from __future__ import annotations

from typing import Any, Mapping


def build_pr126_fixture_scope_manifest_record(
    *,
    decision: Mapping[str, Any],
    binding: Mapping[str, Any],
    accepted_source_evidence: Mapping[str, Any],
    source_change_snapshot: Mapping[str, Any],
    deterministic_fixture_time: str,
    fixture_authority_class: str,
) -> dict[str, Any]:
    binding_id = str(decision["source_connector_binding_ledger_record_id"])
    return {
        "connector_semantic_pr126_fixture_scope_manifest_id": (
            f"PR126_FIXTURE_SCOPE_IMPLEMENTATION_MANIFEST_{binding_id}"
        ),
        "fixture_authority_class": fixture_authority_class,
        "production_connector_semantic_implementation_authority": False,
        "future_production_launch_path_preserved": True,
        "source_connector_binding_ledger_record_id": binding_id,
        "accepted_source_evidence_packet_id": str(
            decision["accepted_source_evidence_packet_id"]
        ),
        "source_change_snapshot_id": str(source_change_snapshot["source_change_snapshot_id"]),
        "venue_id": str(binding["venue_id"]),
        "target_field_path": str(binding["target_field_path"]),
        "semantic_surface_id": str(binding["semantic_surface_id"]),
        "canonical_connector_namespace": str(binding["canonical_connector_namespace"]),
        "bound_value_canonical": binding["bound_value_canonical"],
        "bound_value_type": str(binding["bound_value_type"]),
        "bound_value_unit_or_scale": str(binding["bound_value_unit_or_scale"]),
        "bound_value_scope": str(binding["bound_value_scope"]),
        "implementation_gate_state": str(decision["implementation_gate_state"]),
        "implementation_decision_receipt_id": str(
            decision["implementation_decision_receipt_id"]
        ),
        "implementation_manifest_state": "PR126_FIXTURE_SCOPE_MANIFEST_READY",
        "connector_binding_revalidation_state": str(
            binding["connector_binding_revalidation_state"]
        ),
        "source_change_snapshot_state": str(
            source_change_snapshot["source_change_snapshot_state"]
        ),
        "deterministic_fixture_time": deterministic_fixture_time,
        "production_connector_use_allowed_flag": False,
        "network_io_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "production_reachability_allowed_flag": False,
        "runtime_resolver_snapshot_creation_allowed_flag": False,
        "replay_paper_execution_allowed_flag": False,
        "runtime_cash_receipt_created": False,
        "quantum_backend_execution_allowed_flag": False,
        "quantum_simulator_execution_allowed_flag": False,
        "optimizer_execution_allowed_flag": False,
        "production_values_filled_by_later_official_source_prs": True,
        "accepted_source_fixture_authority_class": str(
            accepted_source_evidence["fixture_authority_class"]
        ),
    }
