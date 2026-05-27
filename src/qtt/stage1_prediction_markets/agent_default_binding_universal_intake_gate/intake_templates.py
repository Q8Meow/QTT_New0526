"""Universal classical, quantum, and hybrid intake template catalog."""

from __future__ import annotations

from typing import Any

from . import constants as c
from .classical_quantum_applicability import (
    applicability_for_template,
    owner_priority_state_for_template,
)
from .future_routing import (
    optimizer_hint_for_template,
    replay_paper_hint_for_template,
    scoring_readiness_for_template,
)
from .population_router import authority_boundary


def _population_lane(template_type: str) -> str:
    if template_type == c.CLASSICAL_OPTIMIZER_METHOD_TEMPLATE:
        return c.FUTURE_CLASSICAL_ALGORITHM_TEMPLATE_LANE
    if template_type in {
        c.CLASSICAL_TRADING_FORMULA_TEMPLATE,
        c.CLASSICAL_RISK_FORMULA_TEMPLATE,
        c.CLASSICAL_CAPITAL_ALLOCATION_FORMULA_TEMPLATE,
        c.CLASSICAL_EXECUTION_LATENCY_FORMULA_TEMPLATE,
    }:
        return (
            c.FUTURE_RISK_CAPITAL_EXECUTION_TEMPLATE_LANE
            if template_type
            in {
                c.CLASSICAL_RISK_FORMULA_TEMPLATE,
                c.CLASSICAL_CAPITAL_ALLOCATION_FORMULA_TEMPLATE,
                c.CLASSICAL_EXECUTION_LATENCY_FORMULA_TEMPLATE,
            }
            else c.FUTURE_CLASSICAL_FORMULA_TEMPLATE_LANE
        )
    if template_type in {
        c.CLASSICAL_STATISTICAL_EDGE_TEMPLATE,
        c.CLASSICAL_MARKET_MICROSTRUCTURE_ALPHA_TEMPLATE,
    }:
        return c.FUTURE_EDGE_ALPHA_TEMPLATE_LANE
    if template_type == c.QUANTUM_INSPIRED_OPTIMIZER_TEMPLATE:
        return c.FUTURE_QUANTUM_INSPIRED_OPTIMIZER_TEMPLATE_LANE
    if template_type == c.HYBRID_CLASSICAL_QUANTUM_ALGORITHM_TEMPLATE:
        return c.FUTURE_HYBRID_CLASSICAL_QUANTUM_TEMPLATE_LANE
    if template_type == c.UNKNOWN_RESEARCH_CANDIDATE_BLOCKED_TEMPLATE:
        return c.BLOCKED_AMBIGUOUS_INPUT_LANE
    return c.FUTURE_TRUE_QUANTUM_OPTIMIZER_TEMPLATE_LANE


def _binding_state(template_type: str) -> str:
    if template_type == c.UNKNOWN_RESEARCH_CANDIDATE_BLOCKED_TEMPLATE:
        return c.BINDING_BLOCKED_AMBIGUOUS
    return c.BINDING_PENDING_SOURCE_EVIDENCE


def _block_codes(template_type: str) -> list[str]:
    if template_type == c.UNKNOWN_RESEARCH_CANDIDATE_BLOCKED_TEMPLATE:
        return [c.PR156_REQUIRED_INPUT_AMBIGUOUS]
    return [
        c.PR156_TEMPLATE_ONLY_NO_CANDIDATE,
        c.PR156_SOURCE_EVIDENCE_REQUIRED_FOR_FUTURE_CANDIDATE,
    ]


def build_universal_intake_templates() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for template_type in c.UNIVERSAL_INTAKE_TEMPLATE_TYPE_VALUES:
        records.append(
            {
                "pr156_record_id": f"PR156__FUTURE_INTAKE_TEMPLATE__{template_type}",
                "record_kind": c.FUTURE_INTAKE_TEMPLATE_RECORD,
                "source_population": c.SOURCE_POPULATION_FUTURE_TEMPLATE_CATALOG,
                "source_record_ref": template_type,
                "source_record_type": c.SOURCE_RECORD_TYPE_TEMPLATE,
                "source_artifact_path": None,
                "source_authority_class": c.AUTHORITY_CLASS,
                "population_lane": _population_lane(template_type),
                "agent_binding_state": _binding_state(template_type),
                "bound_agent_ids": [],
                "bound_agent_roles": [],
                "bound_consumer_classes": [],
                "binding_basis_artifacts": [],
                "binding_basis_reason": c.TEMPLATE_ONLY_BINDING_REASON,
                "binding_block_codes": _block_codes(template_type),
                "template_type": template_type,
                "candidate_instance_state": c.TEMPLATE_ONLY_NO_CANDIDATE_INSTANCE,
                "candidate_origin": c.SOURCE_POPULATION_FUTURE_TEMPLATE_CATALOG,
                "candidate_origin_authority_class": c.AUTHORITY_CLASS,
                "candidate_research_intake_state": (
                    c.SOURCE_EVIDENCE_TEMPLATE_ONLY_NOT_ACCEPTED
                ),
                "applicability_class": applicability_for_template(template_type),
                "owner_strategy_priority_state": owner_priority_state_for_template(
                    template_type
                ),
                "atomicrows_ingestion_state": (
                    c.ATOMICROWS_FUTURE_CANDIDATE_MAPPING_REQUIRED
                ),
                "scoring_ranking_readiness_state": scoring_readiness_for_template(
                    template_type
                ),
                "optimizer_routing_hint": optimizer_hint_for_template(template_type),
                "replay_paper_routing_hint": replay_paper_hint_for_template(
                    template_type
                ),
                "market_scope": "PREDICTION_MARKETS_GENERAL",
                "platform_scope": "PREDICTION_MARKETS_GENERAL",
                "route_triage_domain": "PR136_ROUTE_TRIAGE_RECEIPT",
                "launch_readiness_domain": c.NO_EXACT_PR136_RECORD_MAPPING,
                "section_crosswalk_refs": [],
                "market_specific_index_refs": [],
                "command_action_matrix_refs": [],
                "atomicrows_reconciliation_refs": [],
                "atomicrows_semantic_contract_refs": [],
                "pr155_registry_ref": None,
                "pr154_completion_ref": None,
                "blocked_completion_path_ref_or_inline": None,
                "future_completion_pr_hint": c.FUTURE_RESEARCH_INTAKE_PR_HINT,
                "future_scoring_ranking_pr_hint": c.FUTURE_SCORING_RANKING_PR_HINT,
                "future_optimizer_pr_hint": c.FUTURE_OPTIMIZER_PR_HINT,
                "future_replay_paper_pr_hint": c.FUTURE_REPLAY_PAPER_PR_HINT,
                **dict(c.NON_AUTHORITY_BOUNDARY),
                "non_authority_boundary": dict(c.NON_AUTHORITY_BOUNDARY),
                "created_by_pr": c.PR_ID,
                "authority_boundary": authority_boundary(),
            }
        )
    return sorted(records, key=lambda record: record["pr156_record_id"])
