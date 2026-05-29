"""PR161C assimilation queue construction for PR161B residuals."""

from __future__ import annotations

from typing import Any

from . import constants as c


def build_assimilation_queue(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for candidate in candidates:
        if not candidate.get("pr161c_assimilation_required_flag"):
            continue
        queue_id = str(candidate.get("pr161c_assimilation_queue_id_if_needed") or f"PR161C_QUEUE__{candidate['residual_candidate_id']}")
        output.append(
            {
                "assimilation_queue_id": queue_id,
                "residual_candidate_id": candidate["residual_candidate_id"],
                "proposed_atomicrows_row_id_or_new_row_family_candidate": _first_or_new(candidate.get("covered_by_atomicrows_row_ids"), candidate),
                "proposed_pr154_target_id_or_new_target_candidate": _first_or_new(candidate.get("covered_by_pr154_target_ids"), candidate),
                "proposed_field_path": _field_path(candidate),
                "candidate_type": candidate["candidate_type"],
                "candidate_family": candidate["candidate_family"],
                "recommended_fill_lane": candidate["recommended_fill_lane"],
                "source_candidates": [candidate["extraction_source_path"]],
                "value_candidate_if_available": candidate.get("default_value_if_available"),
                "range_candidate_if_available": _range(candidate),
                "unit_candidate_if_available": candidate.get("unit_if_available"),
                "scale_candidate_if_available": candidate.get("scale_if_available"),
                "formula_candidate_if_available": candidate.get("formula_expression_if_available"),
                "quantum_profile_candidate_if_available": candidate.get("optimizer_family_if_available"),
                "classical_baseline_required_flag": True,
                "hybrid_arbitration_required_flag": True,
                "replay_paper_route_required_flag": bool(candidate.get("replay_paper_candidate_flag")),
                "downstream_agent_roles": candidate.get("downstream_agent_roles", []),
                "downstream_pr_targets": candidate.get("downstream_pr_targets", []),
                "owner_review_future_promotion_flag": True,
                "live_use_allowed_flag": False,
                "no_profit_evidence_created_flag": True,
                "no_runtime_authority_created_flag": True,
            }
        )
    return output


def build_quantum_assimilation_queue(quantum_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for record in quantum_records:
        if not record.get("pr161c_quantum_assimilation_required_flag"):
            continue
        output.append(
            {
                "pr161c_quantum_queue_id": record["pr161c_quantum_assimilation_queue_id_if_needed"],
                "quantum_residual_id": record["quantum_residual_id"],
                "quantum_candidate_family": record["quantum_candidate_family"],
                "quantum_optimizer_family": record["quantum_optimizer_family"],
                "proposed_pr161a_profile_extension": record["quantum_profile_type"],
                "proposed_atomicrows_row_id_or_new_row_candidate": _first_or_new(record.get("atomicrows_row_ids"), record),
                "proposed_pr154_target_id_or_new_target_candidate": _first_or_new(record.get("pr154_target_ids"), record),
                "proposed_formula_template": record["formula_template_type"],
                "proposed_default_range": record.get("default_range_if_available") or record.get("parameter_range_if_available"),
                "proposed_classical_baseline": "CLASSICAL_GREEDY_LINEAR_BASELINE_CANDIDATE",
                "proposed_hybrid_arbitration_rule": "CLASSICAL_BASELINE_VS_QUANTUM_CHALLENGER_COMPARE_THEN_SELECT",
                "proposed_replay_paper_descriptor": f"PR161B_QUANTUM_REPLAY_DESCRIPTOR__{record['quantum_residual_id']}",
                "proposed_downstream_pr_route": record.get("downstream_pr87_pr92_route", []),
                "proposed_qtt_agent_consumers": record.get("downstream_qtt_agent_roles", []),
                "recommended_fill_lane": record["recommended_fill_lane"],
                "online_research_needed_flag": record["recommended_fill_lane"] == c.AssimilationFillLane.FILL_REQUIRES_PR161C_ONLINE_RESEARCH.value,
                "official_source_needed_for_promotion_flag": True,
                "replay_paper_required_flag": True,
                "owner_live_promotion_review_required_flag": True,
                "quantum_backend_execution_allowed_flag": False,
                "optimizer_execution_allowed_flag": False,
                "profit_evidence_created_flag": False,
            }
        )
    return output


def _first_or_new(values: Any, candidate: dict[str, Any]) -> str:
    if isinstance(values, list) and values:
        return str(values[0])
    return f"NEW_ROW_FAMILY_CANDIDATE__{candidate.get('normalized_candidate_name', candidate.get('quantum_residual_id'))}"


def _range(candidate: dict[str, Any]) -> str | None:
    lower = candidate.get("lower_bound_if_available")
    upper = candidate.get("upper_bound_if_available")
    if lower is None and upper is None:
        return None
    return f"{lower or ''}..{upper or ''}"


def _field_path(candidate: dict[str, Any]) -> str:
    family = str(candidate.get("candidate_family", "candidate")).lower()
    name = str(candidate.get("normalized_candidate_name", "residual"))
    return f"pr161b_residual.{family}.{name}"
