"""AtomicRows candidate/readiness mapping for PR159S."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build_atomicrows_candidate_records(classified_targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in classified_targets:
        if not target["atomicrows_linked_flag"]:
            continue
        replay_ready = bool(target["replay_paper_candidate_flag"])
        connector_pending = target["terminal_completion_state"] == c.TerminalCompletionState.COMPLETED_AS_CONNECTOR_FUTURE_ROUTE.value
        records.append(
            {
                "atomicrows_candidate_record_id": f"PR159S_ATOMICROWS_CANDIDATE__{len(records)+1:04d}",
                "target_id_or_row_id": target["target_id_or_row_id"],
                "target_field_id": target["target_field_id"],
                "family_id": target.get("family_id"),
                "parameter_stack_role_taxonomy_mapping": _role_mapping(target),
                "signal_scoring_normalization_risk_execution_capital_latency_error_guard_quantum_roles": _role_vector(target),
                "source_provenance_tag": target["source_provenance_tag"],
                "profit_validation_tag": target["profit_validation_tag"],
                "row_level_aggregate_provenance_tag": target["row_level_aggregate_provenance_tag"],
                "atomicrows_official_source_ready": False,
                "atomicrows_research_candidate_ready": True,
                "atomicrows_replay_paper_candidate_ready": replay_ready,
                "atomicrows_profit_proven_ready": False,
                "atomicrows_non_profitable_retired": False,
                "atomicrows_quantum_candidate_ready": target["terminal_completion_state"]
                in {
                    c.TerminalCompletionState.COMPLETED_AS_QUANTUM_CANDIDATE.value,
                    c.TerminalCompletionState.COMPLETED_AS_HYBRID_CANDIDATE.value,
                },
                "atomicrows_owner_policy_ready": False,
                "atomicrows_connector_fact_pending": connector_pending,
                "atomicrows_live_use_pending": True,
                "final_bundle_created_flag": False,
                "bundle_checksum_hash_authority_created_flag": False,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records


def _role_mapping(target: Mapping[str, Any]) -> str:
    field_id = str(target.get("target_field_id"))
    if "latency" in field_id:
        return "latency_routing_microstructure_candidate"
    if "execution" in field_id:
        return "execution_boundary_parameter_candidate"
    return "source_evidence_connector_fact_route"


def _role_vector(target: Mapping[str, Any]) -> list[str]:
    field_id = str(target.get("target_field_id"))
    roles = ["source_provenance", "live_use_guard"]
    if "latency" in field_id:
        roles.extend(["latency", "microstructure", "error_guard"])
    if "execution" in field_id:
        roles.extend(["execution", "risk", "capital"])
    if target["replay_paper_candidate_flag"]:
        roles.extend(["signal", "scoring", "normalization"])
    if target["terminal_completion_state"] in {
        c.TerminalCompletionState.COMPLETED_AS_QUANTUM_CANDIDATE.value,
        c.TerminalCompletionState.COMPLETED_AS_HYBRID_CANDIDATE.value,
    }:
        roles.append("quantum_advisory")
    return sorted(set(roles))

