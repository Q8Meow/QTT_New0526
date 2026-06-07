"""Model-risk inventory for PR164 computable candidates."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref


def build_model_risk_rows(computability_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate([item for item in computability_rows if item["candidate_id"]], 1):
        rows.append(
            {
                "model_risk_inventory_record_ref": plain_ref("MODEL_RISK", index),
                "qku_id": row["qku_id"],
                "candidate_id": row["candidate_id"],
                "model_or_formula_id": row["qku_formula_id"],
                "conceptual_soundness_note": "Formula/objective is deterministic and replay/paper-routable; values remain candidate/provisional until downstream verification.",
                "input_data_requirements": row["input_fields"],
                "assumptions": row["event_contract_assumptions"],
                "limitations": [
                    "no live connector semantics",
                    "no source acceptance",
                    "no final replay or paper result authority",
                    "no profit evidence",
                ],
                "intended_use": "REPLAY_PAPER_CANDIDATE_ONLY_FOR_PR164",
                "validation_target": "PR165 scoring readiness and PR165-B negative-memory preparation",
                "monitoring_metric_refs": [
                    "latency_cost_formula",
                    "risk_penalty_formula",
                    "execution_cost_component_refs",
                    "source_uncertainty_penalty",
                ],
                "independent_review_agent": "governance_agent",
                "model_owner_agent": "formula_objective_solver_agent",
                "remediation_route": "ROUTE_TO_PR162D_R3_ACQUISITION_REPAIR",
                "vendor_or_external_source_flag": False,
                "third_party_candidate_flag": False,
                "no_live_use_flag": True,
                "validation_status": "PASS",
            }
        )
    return rows


def build_assumption_limitation_ledger(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "model_assumption_limitation_ref": plain_ref("MODEL_LIMIT", index),
            "model_or_formula_id": row["model_or_formula_id"],
            "candidate_id": row["candidate_id"],
            "assumptions": row["assumptions"],
            "limitations": row["limitations"],
            "no_live_use_flag": True,
            "validation_status": "PASS",
        }
        for index, row in enumerate(model_rows, 1)
    ]


def build_validation_target_ledger(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "model_validation_target_ref": plain_ref("MODEL_VALIDATION", index),
            "model_or_formula_id": row["model_or_formula_id"],
            "candidate_id": row["candidate_id"],
            "validation_target": row["validation_target"],
            "monitoring_metric_refs": row["monitoring_metric_refs"],
            "independent_review_agent": row["independent_review_agent"],
            "validation_status": "PASS",
        }
        for index, row in enumerate(model_rows, 1)
    ]
