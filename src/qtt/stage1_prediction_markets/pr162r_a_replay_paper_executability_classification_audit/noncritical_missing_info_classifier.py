"""Non-critical missing information classifier."""

from __future__ import annotations

from typing import Any

from .candidate_loader import agent_refs, candidate_type, source_tier


def noncritical_tags(record: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    ctype = candidate_type(record)
    tier = source_tier(record)
    confidence = str(record.get("confidence_class") or "")
    family = " ".join(
        str(record.get(key) or "")
        for key in ("formula_category", "formula_family", "algorithm_family", "parameter_family", "quantum_family")
    ).lower()
    if not (tier.startswith("TIER_1") or tier.startswith("TIER_2")):
        tags.append("NON_OFFICIAL_SOURCE")
    if "PROVISIONAL" in confidence or tier.startswith("TIER_3") or tier.startswith("TIER_4"):
        tags.append("PROVISIONAL_SOURCE")
    if ctype == "PARAMETER" or "parameter" in family or record.get("parameter_ranges"):
        tags.append("PARAMETER_CALIBRATION_NEEDED")
    if ctype == "QUANTUM" or any(token in family for token in ("qubo", "ising", "bqm", "cqm", "qaoa", "vqe", "annealing", "quantum")):
        if record.get("strongest_classical_comparator_mapping"):
            tags.append("QUANTUM_COMPARATOR_READY")
        tags.append("QUANTUM_BACKEND_OPTIONAL")
    if any(token in family for token in ("risk", "kelly", "var", "cvar", "drawdown")):
        tags.append("RISK_REVIEW_NEEDED")
    if any(token in family for token in ("portfolio", "variance", "sharpe", "capital", "weight")):
        tags.append("CAPITAL_SIZING_REVIEW_NEEDED")
    if "OWNER_REVIEW_OPTIONAL" in agent_refs(record):
        tags.append("OWNER_REVIEW_OPTIONAL")
    if record.get("formula_equivalence_family_id"):
        tags.append("FORMULA_DEDUPE_REVIEW_NEEDED")
    return sorted(set(tags))


def noncritical_records(records: list[dict[str, Any]], classification_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        cid = str(record["candidate_id"])
        tags = [
            tag
            for tag in classification_by_id[cid]["secondary_tags"]
            if tag
            not in {
                "MICRO_MATERIALIZED_IN_PR162R_A",
                "TARGETED_CRITICAL_GAP_FOR_PR162D_R2",
                "ENHANCEMENT_ONLY_GAP",
            }
        ]
        if tags:
            rows.append(
                {
                    "candidate_id": cid,
                    "noncritical_missing_info_tags": tags,
                    "does_not_block_replay_paper_flag": True,
                    "live_order_authority": False,
                }
            )
    return rows
