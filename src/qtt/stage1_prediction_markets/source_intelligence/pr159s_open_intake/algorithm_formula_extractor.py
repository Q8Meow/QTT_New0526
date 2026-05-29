"""Algorithm, formula, parameter, and heuristic candidate projections."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


_ALGORITHM_FORMULA_STATES = {
    c.TerminalCompletionState.COMPLETED_AS_ALGORITHM_CANDIDATE.value,
    c.TerminalCompletionState.COMPLETED_AS_FORMULA_CANDIDATE.value,
    c.TerminalCompletionState.COMPLETED_AS_PARAMETER_CANDIDATE.value,
    c.TerminalCompletionState.COMPLETED_AS_EDGE_HYPOTHESIS_CANDIDATE.value,
    c.TerminalCompletionState.COMPLETED_AS_MICROSTRUCTURE_CANDIDATE.value,
    c.TerminalCompletionState.COMPLETED_AS_QUANTUM_CANDIDATE.value,
    c.TerminalCompletionState.COMPLETED_AS_CLASSICAL_CANDIDATE.value,
    c.TerminalCompletionState.COMPLETED_AS_HYBRID_CANDIDATE.value,
    c.TerminalCompletionState.COMPLETED_AS_REPLAY_PAPER_TEST_CANDIDATE.value,
}


def build_algorithm_formula_candidate_records(classified_targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in classified_targets:
        if target["terminal_completion_state"] not in _ALGORITHM_FORMULA_STATES:
            continue
        records.append(
            {
                "candidate_id": f"PR159S_ALGO_FORMULA_CANDIDATE__{len(records)+1:04d}",
                "target_id_or_row_id": target["target_id_or_row_id"],
                "candidate_terminal_state": target["terminal_completion_state"],
                "source_id": target["assigned_research_source_id"],
                "source_class": target["source_class"],
                "source_quality_tier": target["source_quality_tier"],
                "source_provenance_tag": target["source_provenance_tag"],
                "profit_validation_tag": target["profit_validation_tag"],
                "claim_summary": "Candidate accepted for replay/paper design only; PR159S does not prove profitability.",
                "algorithm_or_formula_or_parameter": target["field_value"],
                "input_features": [
                    "orderbook_depth",
                    "bid_ask_spread",
                    "venue_price_gap",
                    "latency_window",
                    "fee_and_slippage_model",
                ],
                "output_signals": [
                    "candidate_edge_score",
                    "risk_adjusted_size_hint",
                    "route_viability_flag",
                ],
                "market_context": target["market_scope"],
                "prediction_market_applicability": True,
                "latency_sensitivity": "requires_replay_measured_latency_model_before_live",
                "data_requirements": [
                    "historical_orderbook_or_trade_events",
                    "resolved_market_outcomes",
                    "venue_fee_tick_settlement_facts_before_live",
                ],
                "risk_assumptions": [
                    "no_profit_claim_from_source",
                    "source_claim_requires_independent_qtt_replay_and_paper",
                ],
                "transaction_cost_assumptions": [
                    "cost_model_required_before_candidate_ranking",
                    "official_fee_tick_settlement_docs_required_before_live",
                ],
                "limitations": target["promotion_limitations"],
                "classical_baseline_comparator": "deterministic_rules_plus_cost_model_baseline",
                "quantum_or_quantum_inspired_applicability": "classified_in_PR159S_QuantumCandidateReadinessDelta",
            }
        )
    return records

