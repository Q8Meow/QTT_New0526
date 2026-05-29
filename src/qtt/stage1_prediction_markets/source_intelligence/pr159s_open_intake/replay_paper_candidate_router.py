"""Replay/paper candidate route records for PR159S."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build_replay_paper_candidate_routes(classified_targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in classified_targets:
        if not target["replay_paper_candidate_flag"]:
            continue
        records.append(
            {
                "candidate_id": f"PR159S_REPLAY_PAPER_CANDIDATE__{len(records)+1:04d}",
                "source_id": target["assigned_research_source_id"],
                "target_id_or_row_id": target["target_id_or_row_id"],
                "source_class": target["source_class"],
                "source_quality_tier": target["source_quality_tier"],
                "source_provenance_tag": target["source_provenance_tag"],
                "profit_validation_tag": target["profit_validation_tag"],
                "route_state": c.ReplayPaperRouteState.REPLAY_PAPER_ROUTE_CREATED_NOT_EXECUTED.value,
                "claim_summary": "Candidate routed to replay and paper testing; source claim is not QTT profit evidence.",
                "algorithm_formula_parameter_extracted": target["field_value"],
                "target_market_type": "prediction_market_binary_or_multi_outcome",
                "platform_applicability": target["platform_scope"],
                "required_market_data": [
                    "historical_orderbook_depth_or_trade_events",
                    "resolved_market_result_labels",
                    "timestamped venue snapshots",
                    "official fee_tick_settlement facts before live use",
                ],
                "expected_signal_output": [
                    "candidate_signal_score",
                    "candidate_size_hint",
                    "candidate_abstain_flag",
                ],
                "risk_controls": [
                    "cost_model_guard",
                    "slippage_guard",
                    "liquidity_depth_guard",
                    "event_resolution_language_guard",
                ],
                "cost_fee_dependency": "official venue fee tick settlement facts required before live promotion",
                "latency_dependency": "paper route must measure route latency before owner promotion review",
                "overfit_leakage_risks": [
                    "resolved_outcome_leakage",
                    "selection_bias_from_source_popularity",
                    "survivorship_bias_from public writeups",
                ],
                "replay_test_requirements": [
                    "deterministic historical replay",
                    "fee_and_slippage_cost_model",
                    "walk_forward_split_if_parameterized",
                ],
                "paper_test_requirements": [
                    "nonlive paper mode",
                    "dual_result_review",
                    "owner_review_required_before_live",
                ],
                "pass_fail_metrics": [
                    "net_expected_value_after_costs",
                    "drawdown_limit",
                    "fill_rate_under_latency_model",
                    "calibration_error_if_probability_signal",
                ],
                "owner_review_required_before_live": True,
                "official_venue_facts_still_required_before_live": True,
                "replay_execution_performed_in_pr159s": False,
                "paper_execution_performed_in_pr159s": False,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records

