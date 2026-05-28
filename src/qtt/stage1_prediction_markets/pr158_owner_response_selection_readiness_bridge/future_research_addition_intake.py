"""Future research/addition compatibility artifact."""

from __future__ import annotations

from typing import Any

from . import constants as c

ADDITION_CLASSES = (
    "NEW_OWNER_FOUND_PARAMETER",
    "NEW_RESEARCH_AGENT_PARAMETER",
    "NEW_RESEARCH_AGENT_ALGORITHM",
    "NEW_FORMULA_FAMILY",
    "NEW_STATISTICAL_EDGE",
    "NEW_MICROSTRUCTURE_ALPHA",
    "NEW_RISK_CONTROL_RULE",
    "NEW_CAPITAL_ALLOCATION_RULE",
    "NEW_EXECUTION_RULE",
    "NEW_LATENCY_GUARD",
    "NEW_ERROR_GUARD",
    "NEW_QUANTUM_INSPIRED_CANDIDATE",
    "NEW_TRUE_QUANTUM_CANDIDATE",
    "NEW_HYBRID_CLASSICAL_QUANTUM_CANDIDATE",
    "NEW_EXTERNAL_SOURCE_REQUIRED_FACT",
)


def build() -> dict[str, Any]:
    records = []
    for addition_class in ADDITION_CLASSES:
        external = addition_class == "NEW_EXTERNAL_SOURCE_REQUIRED_FACT"
        owner_policy = addition_class.startswith("NEW_OWNER") or any(
            token in addition_class for token in ("RISK", "CAPITAL", "EXECUTION", "LATENCY", "ERROR")
        )
        records.append(
            {
                "addition_class": addition_class,
                "required_owner_or_research_input": (
                    "official source evidence packet"
                    if external
                    else "owner or research candidate packet with AtomicRows classification fields"
                ),
                "source_evidence_required_flag": external,
                "atomicrows_classification_required_flag": True,
                "semantic_row_contract_required_flag": True,
                "owner_editability_required_flag": owner_policy,
                "agent_responsibility_required_flag": True,
                "scoring_feature_role_required_flag": True,
                "trade_context_applicability_required_flag": True,
                "replay_paper_required_before_live_flag": True,
                "owner_review_required_before_live_flag": True,
                "no_direct_live_authority_flag": True,
                "future_route": (
                    c.FutureRoute.PR159_PUBLIC_SOURCE_RETRY.value
                    if external
                    else c.FutureRoute.PR161_ATOMICROWS_COMPLETION.value
                ),
                "future_research_addition_status": (
                    c.FutureResearchAdditionStatus.FUTURE_RESEARCH_ADDITION_REQUIRES_SOURCE_EVIDENCE.value
                    if external
                    else c.FutureResearchAdditionStatus.FUTURE_RESEARCH_ADDITION_REQUIRES_ATOMICROWS_CLASSIFICATION.value
                ),
            }
        )
    return {
        "report_type": "PR158_FUTURE_RESEARCH_ADDITION_INTAKE_COMPATIBILITY",
        "record_count": len(records),
        "records": records,
        "no_runtime_live_order_profit_authority_created": True,
    }

