"""Quantum agent route builder."""

from __future__ import annotations

from typing import Any


def quantum_agent_route_records(problem_models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for model in problem_models:
        records.append(
            {
                "quantum_route_id": model["problem_model_id"].replace("PROBLEM", "ROUTE"),
                "problem_model_ref": model["problem_model_id"],
                "qku_refs": model["qku_refs"],
                "agent_path_refs": [
                    "QUANTUM_ADVISORY_AGENT",
                    "QUANTUM_EXECUTION_HARNESS",
                    "QUANTUM_CLASSICAL_HYBRID_COMPARATOR",
                    "REPLAY_PAPER_CANDIDATE_ROUTER",
                    "RISK_MANAGER_CANDIDATE_REVIEW",
                    "CAPITAL_SIZING_CANDIDATE_REVIEW",
                    "PARAMETER_STACK_AGENT",
                ],
                "route_status": "AGENT_ROUTED_QUANTUM_CANDIDATE",
                "direct_live_order_submission_flag": False,
                "live_pretrade_remote_dependency_flag": False,
                "live_order_authority": False,
            }
        )
    return records
