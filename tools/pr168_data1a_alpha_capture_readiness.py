#!/usr/bin/env python3
"""Alpha-capture input readiness, without profit proof."""

from __future__ import annotations

from typing import Any

from tools.pr168_data1a_config import generated_ref, report_path, route_defaults


METRICS = [
    "execution_adjusted_edge_input_readiness",
    "fill_adjusted_expected_pnl_input_readiness",
    "net_expected_pnl_candidate_input_readiness",
    "lower_confidence_bound_edge_input_readiness",
    "TCA_decomposition_input_readiness",
    "capacity_crowding_input_readiness",
    "overfit_fdr_penalty_input_readiness",
    "portfolio_marginal_utility_input_readiness",
    "scenario_ladder_input_readiness",
    "no_trade_comparison_margin_input_readiness",
    "probability_calibration_input_readiness",
    "regime_conditioned_memory_input_readiness",
]


def _state(score_ready: bool, score_partial: bool) -> str:
    if score_ready:
        return "READY"
    if score_partial:
        return "PARTIAL"
    return "MISSING"


def build_alpha_capture_readiness(
    quality_rows: list[dict[str, Any]],
    qku_rows: list[dict[str, Any]],
    created_at_utc: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    for index, quality in enumerate(quality_rows, start=1):
        has_depth = bool(quality["depth_coverage_flag"])
        has_spread = bool(quality["spread_coverage_flag"])
        has_history = bool(quality["trade_coverage_flag"] or quality["price_history_coverage_flag"])
        metric_states = {
            "execution_adjusted_edge_input_readiness": _state(has_spread and has_depth, has_depth),
            "fill_adjusted_expected_pnl_input_readiness": _state(has_depth, False),
            "net_expected_pnl_candidate_input_readiness": _state(False, has_spread or has_history),
            "lower_confidence_bound_edge_input_readiness": _state(False, has_history),
            "TCA_decomposition_input_readiness": _state(False, has_spread and has_depth),
            "capacity_crowding_input_readiness": _state(has_depth, False),
            "overfit_fdr_penalty_input_readiness": _state(False, has_history),
            "portfolio_marginal_utility_input_readiness": _state(False, True),
            "scenario_ladder_input_readiness": _state(False, has_history),
            "no_trade_comparison_margin_input_readiness": _state(False, has_spread or has_depth),
            "probability_calibration_input_readiness": _state(False, has_history),
            "regime_conditioned_memory_input_readiness": _state(False, has_history and has_spread),
        }
        state_scores = {"READY": 1.0, "PARTIAL": 0.5, "MISSING": 0.0, "NOT_APPLICABLE_WITH_REASON": 0.0}
        score = round(
            0.16 * state_scores[metric_states["execution_adjusted_edge_input_readiness"]]
            + 0.14 * state_scores[metric_states["TCA_decomposition_input_readiness"]]
            + 0.12 * state_scores[metric_states["fill_adjusted_expected_pnl_input_readiness"]]
            + 0.10 * state_scores["PARTIAL"]
            + 0.10 * state_scores[metric_states["capacity_crowding_input_readiness"]]
            + 0.10 * state_scores[metric_states["probability_calibration_input_readiness"]]
            + 0.08 * state_scores[metric_states["overfit_fdr_penalty_input_readiness"]]
            + 0.08 * state_scores[metric_states["portfolio_marginal_utility_input_readiness"]]
            + 0.06 * state_scores[metric_states["scenario_ladder_input_readiness"]]
            + 0.06 * state_scores[metric_states["no_trade_comparison_margin_input_readiness"]],
            6,
        )
        rows.append(
            {
                "alpha_capture_row_id": f"alpha_capture_{index:05d}",
                "candidate_stack_id_if_available": None,
                "qku_id_if_available": qku_rows[index - 1]["qku_id"] if index - 1 < len(qku_rows) else None,
                "formula_id_if_available": qku_rows[index - 1]["formula_id_if_available"] if index - 1 < len(qku_rows) else None,
                "algorithm_id_if_available": None,
                "market_or_token_ref": quality["market_or_token_ref"],
                "DATA1_feature_refs": quality["feature_names"],
                "metric_readiness_states": metric_states,
                "metric_readiness_state": "READY" if all(value == "READY" for value in metric_states.values()) else "PARTIAL",
                "metric_missing_inputs": [
                    metric for metric, state in metric_states.items() if state != "READY"
                ],
                "metric_bias_risk_reason": "DATA1 lacks accepted predicted probability, explicit fee, historical full-book, trial-family, and portfolio context inputs.",
                "repair_route": "PR168-GFP2R_FORMULA_BINDING_THEN_PR168-RP2_REPLAY",
                "expected_downstream_unblock_count": 3,
                "alpha_capture_readiness_score_non_proof": score,
                "created_at_utc": created_at_utc,
                **route_defaults("risk", data1_refs=[generated_ref(report_path("PR168_DATA1_NormalizedMarketDataFeatureRegistry"))]),
            }
        )
    summary = {
        "alpha_capture_readiness_ready_count": sum(1 for row in rows if row["metric_readiness_state"] == "READY"),
        "alpha_capture_readiness_partial_count": sum(1 for row in rows if row["metric_readiness_state"] == "PARTIAL"),
        "alpha_capture_readiness_missing_count": sum(1 for row in rows if row["metric_readiness_state"] == "MISSING"),
        "alpha_capture_readiness_score_median_non_proof": sorted([row["alpha_capture_readiness_score_non_proof"] for row in rows] or [0])[len(rows) // 2 if rows else 0],
        "profit_evidence_created_flag": False,
        **route_defaults("risk", data1_refs=[generated_ref(report_path("PR168_DATA1_NormalizedMarketDataFeatureRegistry"))]),
    }
    return summary, rows
