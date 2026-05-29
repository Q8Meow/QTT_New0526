"""Quantum-forward candidate classification metadata for PR159S."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def _quantum_classes(target: Mapping[str, Any]) -> list[str]:
    state = str(target.get("terminal_completion_state"))
    source_id = str(target.get("assigned_research_source_id") or "")
    if state == c.TerminalCompletionState.COMPLETED_AS_QUANTUM_CANDIDATE.value:
        return [
            c.QuantumApplicabilityClass.QUBO_COMPATIBLE.value,
            c.QuantumApplicabilityClass.ISING_COMPATIBLE.value,
            c.QuantumApplicabilityClass.QAOA_COMPATIBLE.value,
            c.QuantumApplicabilityClass.ANNEALING_COMPATIBLE.value,
        ]
    if state == c.TerminalCompletionState.COMPLETED_AS_HYBRID_CANDIDATE.value:
        return [
            c.QuantumApplicabilityClass.HYBRID_CLASSICAL_QUANTUM.value,
            c.QuantumApplicabilityClass.QUBO_COMPATIBLE.value,
        ]
    if "QUBO" in source_id or state == c.TerminalCompletionState.COMPLETED_AS_FORMULA_CANDIDATE.value:
        return [
            c.QuantumApplicabilityClass.QUANTUM_INSPIRED.value,
            c.QuantumApplicabilityClass.QUBO_COMPATIBLE.value,
        ]
    return [c.QuantumApplicabilityClass.CLASSICAL_ONLY.value]


def build_quantum_candidate_records(classified_targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in classified_targets:
        classes = _quantum_classes(target) if target["replay_paper_candidate_flag"] else [c.QuantumApplicabilityClass.NOT_QUANTUM_RELEVANT.value]
        quantum_relevant = any(
            item
            not in {
                c.QuantumApplicabilityClass.NOT_QUANTUM_RELEVANT.value,
                c.QuantumApplicabilityClass.CLASSICAL_ONLY.value,
            }
            for item in classes
        )
        records.append(
            {
                "quantum_candidate_record_id": f"PR159S_QUANTUM_READINESS__{len(records)+1:04d}",
                "target_id_or_row_id": target["target_id_or_row_id"],
                "terminal_completion_state": target["terminal_completion_state"],
                "quantum_applicability_classes": classes,
                "quantum_relevant_candidate_flag": quantum_relevant,
                "qubo_compatibility_flag": c.QuantumApplicabilityClass.QUBO_COMPATIBLE.value in classes,
                "ising_compatibility_flag": c.QuantumApplicabilityClass.ISING_COMPATIBLE.value in classes,
                "qaoa_compatibility_flag": c.QuantumApplicabilityClass.QAOA_COMPATIBLE.value in classes,
                "vqe_compatibility_flag": c.QuantumApplicabilityClass.VQE_COMPATIBLE.value in classes,
                "annealing_compatibility_flag": c.QuantumApplicabilityClass.ANNEALING_COMPATIBLE.value in classes,
                "quantum_portfolio_optimization_compatibility_flag": (
                    c.QuantumApplicabilityClass.QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE.value in classes
                ),
                "objective_function_candidate": (
                    "maximize candidate edge net of cost and risk penalties" if quantum_relevant else None
                ),
                "constraint_set_candidate": (
                    ["capital_limit", "venue_exposure_limit", "liquidity_depth_limit"]
                    if quantum_relevant
                    else []
                ),
                "binary_encoding_possibility": "binary_selection_or_route_activation" if quantum_relevant else None,
                "continuous_variable_handling_note": (
                    "continuous sizes require discretization or classical postprocessing" if quantum_relevant else None
                ),
                "transaction_cost_handling_note": (
                    "include fees, slippage, and crossing costs in objective penalty" if quantum_relevant else None
                ),
                "latency_feasibility_note": "candidate metadata only; latency must be measured in future paper route",
                "replay_paper_test_plan": "compare quantum or quantum-inspired route against classical baseline after data gates",
                "classical_baseline_comparator": "greedy_or_linear_cost_model_baseline",
                "owner_quantum_priority_field": "OWNER_REVIEW_REQUIRED_BEFORE_ANY_BACKEND_EXECUTION",
                "source_provenance_tag": target["source_provenance_tag"],
                "profit_validation_tag": target["profit_validation_tag"],
                "quantum_backend_execution_performed_in_pr159s": False,
                "quantum_simulator_execution_performed_in_pr159s": False,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records

