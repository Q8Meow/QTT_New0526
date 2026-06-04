from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library import (
    deterministic_candidate_ranking,
    greedy_market_bundle_selection,
    parameter_stack_selector,
    replay_paper_eligibility_router,
)


def test_mandatory_algorithm_callables_execute():
    ranking = deterministic_candidate_ranking(
        {
            "candidates": [
                {"candidate_id": "A", "final_score": 0.5, "latency_class": "B", "risk_class": "M"},
                {"candidate_id": "B", "final_score": 0.8, "latency_class": "A", "risk_class": "L"},
            ]
        }
    )
    assert ranking["ranked_candidate_ids"] == ["B", "A"]
    bundle = greedy_market_bundle_selection(
        {
            "budget": 50,
            "max_exposure": 50,
            "candidates": [
                {"candidate_id": "A", "expected_net_value": 6, "capital_required": 20, "risk_exposure": 20},
                {"candidate_id": "B", "expected_net_value": 7, "capital_required": 40, "risk_exposure": 40},
            ],
        }
    )
    assert bundle["selected_candidate_ids"] == ["A"]
    route = replay_paper_eligibility_router(
        {"formulation_record": {"validator_materiality_status": "FORMULATION_FULLY_MATERIALIZED"}, "route_record": {"route_id": "R"}}
    )
    assert route["route_state"] == "REPLAY_PAPER_ROUTE_READY"
    stack = parameter_stack_selector(
        {"stacks": [{"stack_id": "S1", "compatible_flag": True, "compatibility_score": 0.8, "replay_value_score": 0.4, "risk_score": 0.1}]}
    )
    assert stack["selected_stack_candidate"] == "S1"
