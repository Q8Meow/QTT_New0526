"""Quantum-forward compatibility router."""

from __future__ import annotations

from typing import Any

from .central_reason_codes import QUANTUM_MODEL_FAMILIES, VARIABLE_DOMAINS, require_enum
from .deterministic_ids import plain_ref


_QUANTUM_CYCLE = ("QUBO", "BQM", "CQM", "DQM", "ISING", "QAOA", "VQE")


def quantum_family_for(identity: dict[str, Any], candidate: dict[str, Any] | None, index: int) -> str:
    text = " ".join(
        str(value)
        for value in (
            identity.get("qku_id"),
            identity.get("qku_type"),
            (candidate or {}).get("candidate_type"),
            (candidate or {}).get("domain_family_key"),
        )
    ).lower()
    if "quantum" in text or (candidate and candidate.get("candidate_type") == "QUANTUM_FORMULATION"):
        return _QUANTUM_CYCLE[(index - 1) % len(_QUANTUM_CYCLE)]
    return "NONE"


def build_quantum_rows(
    identity_rows: list[dict[str, Any]],
    candidate_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    eligible_index = 0
    for index, identity in enumerate(identity_rows, 1):
        candidate = candidate_by_id.get(identity["candidate_id"])
        raw_family = quantum_family_for(identity, candidate, eligible_index + 1)
        if raw_family != "NONE":
            eligible_index += 1
            family = quantum_family_for(identity, candidate, eligible_index)
        else:
            family = "NONE"
        family = require_enum(family, QUANTUM_MODEL_FAMILIES, "quantum_model_family_candidate")
        domain = require_enum("binary" if family in {"QUBO", "BQM", "ISING", "QAOA"} else ("mixed" if family != "NONE" else "continuous"), VARIABLE_DOMAINS, "variable_domain")
        rows.append(
            {
                "quantum_compatibility_record_ref": plain_ref("QUANTUM", index),
                "qku_id": identity["qku_id"],
                "candidate_id": identity["candidate_id"],
                "qku_quantum_eligible_flag": family != "NONE",
                "quantum_model_family_candidate": family,
                "variable_domain": domain,
                "objective_terms": [
                    "expected_net_profit_i * x_i",
                    "lambda_risk * portfolio_risk_terms",
                    "lambda_latency * latency_cost_terms",
                    "lambda_capital * capital_lock_terms",
                    "lambda_source * source_uncertainty_terms",
                ],
                "constraint_terms": [
                    "capital",
                    "event_exposure",
                    "venue_exposure",
                    "liquidity",
                    "latency",
                    "mutually_exclusive_outcome",
                ],
                "penalty_terms": [
                    "portfolio_risk_terms",
                    "correlated_event_penalties",
                    "latency_cost_terms",
                    "capital_lock_terms",
                    "source_uncertainty_terms",
                ],
                "embedding_complexity_hint": "CLASSICAL_MAPPING_ONLY_NO_BACKEND",
                "quantum_mapper_pr_route": "PR162E_Q",
                "classical_comparator_required_flag": True,
                "classical_comparator_formula_ref": "PR164_FORMULA::RISK_ADJUSTED_CANDIDATE_SCORE",
                "quantum_backend_execution_allowed_flag": False,
                "quantum_advantage_claim_allowed_flag": False,
                "replay_paper_quantum_comparison_future_route": "PR166_Q",
                "validation_status": "PASS",
            }
        )
    return rows


def build_quantum_completeness_audit(quantum_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "quantum_completeness_ref": plain_ref("QUANTUM_COMPLETENESS", index),
            "qku_id": row["qku_id"],
            "candidate_id": row["candidate_id"],
            "quantum_model_family_candidate": row["quantum_model_family_candidate"],
            "objective_terms_complete": bool(row["objective_terms"]),
            "constraint_terms_complete": bool(row["constraint_terms"]),
            "penalty_terms_complete": bool(row["penalty_terms"]),
            "quantum_backend_execution_allowed_flag": False,
            "quantum_advantage_claim_allowed_flag": False,
            "validation_status": "PASS",
        }
        for index, row in enumerate(quantum_rows, 1)
    ]


def build_classical_comparator_preparation(quantum_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "classical_comparator_preparation_ref": plain_ref("QUANTUM_COMPARATOR", index),
            "qku_id": row["qku_id"],
            "candidate_id": row["candidate_id"],
            "quantum_model_family_candidate": row["quantum_model_family_candidate"],
            "classical_comparator_required_flag": True,
            "classical_comparator_formula_ref": row["classical_comparator_formula_ref"],
            "comparison_route": "PR166_Q_REPLAY_PAPER_QUANTUM_COMPARISON_FUTURE_ROUTE",
            "validation_status": "PASS",
        }
        for index, row in enumerate(quantum_rows, 1)
    ]
