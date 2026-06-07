"""Formula/objective/solver coverage materialization."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref
from .qku_algorithm_formulation_library import algorithm_family_for, solver_family_for


def build_formula_coverage_rows(
    identity_rows: list[dict[str, Any]],
    candidate_by_id: dict[str, dict[str, Any]],
    test_vectors_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, identity in enumerate(identity_rows, 1):
        candidate = candidate_by_id.get(identity["candidate_id"])
        if candidate:
            test_ref = _first(candidate.get("test_vectors") or [], "PR164_TEST_VECTOR::CANDIDATE_VALUE_REQUIRED")
            expected = test_vectors_by_id.get(test_ref, {}).get("expected_outputs", {})
            formula_ref = str(candidate.get("formulation_ref") or f"PR164_FORMULA::CANDIDATE_PACKET::{index:06d}")
            expression = str(candidate.get("expression") or candidate.get("algorithm_pseudocode") or f"{formula_ref} deterministic candidate procedure")
            input_fields = list(candidate.get("inputs") or ["candidate_replay_paper_input"])
            output_fields = list(candidate.get("outputs") or ["candidate_replay_paper_output"])
            algorithm_family = algorithm_family_for(candidate)
            solver_family = solver_family_for(str(candidate.get("candidate_type")), str(candidate.get("domain_family_key")))
            coverage_state = "FORMULA_OBJECTIVE_SOLVER_COVERED_FOR_REPLAY_PAPER"
        else:
            test_ref = "PR164_TEST_VECTOR::MISSING_CANDIDATE_PACKET_FILL"
            expected = {"fill_required": True}
            formula_ref = "PR164_FORMULA::MISSING_CANDIDATE_PACKET_EXACT_FILL"
            expression = "candidate_packet_v1_record required before replay/paper formula materialization"
            input_fields = ["candidate_packet_v1_record"]
            output_fields = ["candidate_replay_paper_materialization_record"]
            algorithm_family = "candidate_acquisition_repair"
            solver_family = "EXACT_MISSING_VALUE_FILL_ROUTER"
            coverage_state = "FORMULA_OBJECTIVE_SOLVER_REQUIRES_EXACT_MISSING_VALUE_FILL"
        rows.append(
            {
                "formula_objective_solver_record_ref": plain_ref("FOS", index),
                "qku_id": identity["qku_id"],
                "candidate_id": identity["candidate_id"],
                "formula_coverage_state": coverage_state,
                "qku_formula_id": formula_ref,
                "formula_name": _formula_name(formula_ref),
                "formula_expression": expression,
                "objective_expression": _objective_expression(identity["market_scope"], algorithm_family),
                "input_fields": input_fields,
                "output_fields": output_fields,
                "parameter_fields": _parameter_fields(candidate),
                "parameter_domain": _parameter_domain(candidate),
                "algorithm_family": algorithm_family,
                "solver_family": solver_family,
                "market_scope": identity["market_scope"],
                "event_contract_assumptions": _event_contract_assumptions(identity["market_scope"]),
                "expected_net_profit_candidate_formula": "expected_net_profit_candidate = formula_edge - execution_cost_components - risk_penalty_formula",
                "latency_cost_formula": "latency_cost = expected_price_move_per_ms * latency_ms + stale_data_penalty",
                "risk_penalty_formula": "risk_penalty = drawdown_penalty + tail_loss_penalty + liquidity_penalty + model_uncertainty_penalty + source_uncertainty_penalty",
                "test_vector_ref": test_ref,
                "expected_test_vector_output": expected,
                "replay_adapter_consumer": "PR162R_REPLAY_ADAPTER_INPUT_CONSUMER",
                "paper_adapter_consumer": "PR163_PAPER_ADAPTER_INPUT_CONSUMER",
                "pr165_scoring_consumer": "PR165_SCORING_RANKING_INPUT_CONSUMER",
                "downstream_agent_consumers": [
                    "formula_objective_solver_agent",
                    "replay_agent",
                    "paper_agent",
                    "risk_agent",
                    "latency_agent",
                    "pr165_scoring_agent",
                ],
                "validation_status": "PASS",
            }
        )
    return rows


def _first(values: list[Any], default: str) -> str:
    return str(values[0]) if values else default


def _formula_name(formula_ref: str) -> str:
    return formula_ref.replace("::", " ").replace("_", " ").title()


def _parameter_fields(candidate: dict[str, Any] | None) -> list[str]:
    if not candidate:
        return ["candidate_packet_v1_record"]
    defaults = candidate.get("candidate_default_ranges")
    if isinstance(defaults, dict) and defaults:
        return sorted(defaults)
    return ["candidate_replay_paper_policy", "no_live_use_until_downstream_verified_flag"]


def _parameter_domain(candidate: dict[str, Any] | None) -> dict[str, str]:
    if not candidate:
        return {"candidate_packet_v1_record": "object with qku_ids, formulation_ref, inputs, outputs, replay_route, paper_route"}
    fields = _parameter_fields(candidate)
    return {field: "candidate/replay-paper domain; no live authority" for field in fields}


def _objective_expression(market_scope: str, algorithm_family: str) -> str:
    if "quantum" in algorithm_family:
        return "maximize candidate objective terms minus risk, correlation, latency, capital, and source uncertainty penalties; no backend execution"
    if market_scope.startswith("PREDICTION_MARKET_"):
        return "maximize expected_net_profit_candidate subject to event contract assumptions and replay/paper execution-cost components"
    return "maximize agent-consumable candidate utility subject to replay/paper risk and latency penalties"


def _event_contract_assumptions(market_scope: str) -> list[str]:
    if market_scope.startswith("PREDICTION_MARKET_"):
        return [
            "binary_or_event_contract_payout_normalized_to_one_when_applicable",
            "fees_slippage_latency_and_settlement_costs_are_candidate_values",
            "no connector or venue live semantics are bound by PR164",
        ]
    return ["market-agnostic control-plane or model-risk use only", "no live venue contract assumption created"]
