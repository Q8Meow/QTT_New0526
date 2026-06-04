"""Computability class classifier."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type


def classify_computability(record: dict[str, Any]) -> dict[str, Any]:
    cid = candidate_id(record)
    ctype = candidate_type(record)
    family = " ".join(
        str(record.get(key) or "")
        for key in ("algorithm_family", "formula_category", "formula_family", "parameter_family", "quantum_family")
    ).lower()
    computability = "PARTIALLY_COMPUTABLE"
    if record.get("metadata_only_flag") or record.get("quantum_metadata_only_flag"):
        computability = "METADATA_ONLY_NOT_READY"
    elif ctype == "PARAMETER":
        computability = "PARAMETER_ONLY"
    elif ctype == "DATASET":
        computability = "FEATURE_ONLY"
    elif ctype == "QUANTUM":
        computability = "QUANTUM_FORMULATION_BACKED"
    elif ctype == "ALGORITHM" and any(
        token in family for token in ("optimizer", "solver", "qubo", "ising", "bqm", "qaoa", "quantum")
    ):
        computability = "SOLVER_BACKED"
    elif _has_full_compute_contract(record):
        computability = "FULLY_COMPUTABLE"
    elif record.get("mathematical_objective") or record.get("objective"):
        computability = "OBJECTIVE_BACKED"
    elif record.get("constraint_definitions"):
        computability = "CONSTRAINT_BACKED"
    return {
        "computability_classification_id": f"PR162R_A_COMP::{cid}",
        "candidate_id": cid,
        "candidate_type": ctype,
        "computability_class": computability,
        "source_locator": record.get("source_locator"),
        "qku_refs": record.get("qku_refs") or [],
        "agent_refs": record.get("agent_refs") or record.get("agent_route_refs") or [],
        "replay_paper_route_refs": record.get("replay_paper_route_refs") or [],
        "live_order_authority": False,
    }


def _has_full_compute_contract(record: dict[str, Any]) -> bool:
    return bool(
        (record.get("expression") or record.get("deterministic_steps"))
        and record.get("input_fields")
        and record.get("output_fields")
        and record.get("units")
        and record.get("test_vector")
        and record.get("source_locator")
        and record.get("qku_refs")
        and (record.get("agent_refs") or record.get("agent_route_refs"))
        and record.get("replay_paper_route_refs")
    )
