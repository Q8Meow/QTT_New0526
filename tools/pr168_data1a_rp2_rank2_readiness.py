#!/usr/bin/env python3
"""RP2/RANK2 batch readiness audit."""

from __future__ import annotations

from typing import Any

from tools.pr168_data1a_config import generated_ref, report_path, route_defaults


INSTITUTIONAL_FIELDS = [
    "execution_adjusted_ranking_input_availability",
    "TCA_decomposition_input_availability",
    "fill_slippage_depth_input_availability",
    "latency_staleness_input_availability",
    "capacity_crowding_input_availability",
    "calibration_sample_input_availability",
    "overfit_FDR_trial_family_input_availability",
    "portfolio_marginal_utility_input_availability",
    "regime_memory_input_availability",
    "scenario_ladder_input_availability",
    "no_trade_comparator_input_availability",
    "quantum_coefficient_feature_input_availability",
]


def build_rp2_rank2_readiness(context: dict[str, Any], quality_rows: list[dict[str, Any]], created_at_utc: str) -> dict[str, Any]:
    rp2_rows = context["reports"].get("PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch", {}).get("records", [])
    rank2_rows = context["reports"].get("PR168_DATA1_PR168_RANK2_FirstEvidenceRankingBatch", {}).get("records", [])
    rp2_count = len(rp2_rows) if isinstance(rp2_rows, list) else 0
    rank2_count = len(rank2_rows) if isinstance(rank2_rows, list) else 0
    field_state = {
        field: "PARTIAL_READY_WITH_DATA1_CANDIDATE_INPUTS" for field in INSTITUTIONAL_FIELDS
    }
    if any(row.get("data_sufficiency_tier") == "DATA_SUFFICIENCY_TIER_A_REPLAY_READY_CANDIDATE" for row in quality_rows):
        field_state["fill_slippage_depth_input_availability"] = "READY"
        field_state["capacity_crowding_input_availability"] = "READY"
    return {
        "rp2_rank2_batch_readiness_id": "pr168_data1a_rp2_rank2_batch_readiness",
        "RP2_first_batch_ready_count": rp2_count,
        "RANK2_first_batch_ready_count": rank2_count,
        "institutional_pretrade_field_states": field_state,
        "execution_adjusted_ranking_input_availability": field_state["execution_adjusted_ranking_input_availability"],
        "TCA_decomposition_input_availability": field_state["TCA_decomposition_input_availability"],
        "fill_slippage_depth_input_availability": field_state["fill_slippage_depth_input_availability"],
        "latency_staleness_input_availability": field_state["latency_staleness_input_availability"],
        "capacity_crowding_input_availability": field_state["capacity_crowding_input_availability"],
        "calibration_sample_input_availability": field_state["calibration_sample_input_availability"],
        "overfit_FDR_trial_family_input_availability": field_state["overfit_FDR_trial_family_input_availability"],
        "portfolio_marginal_utility_input_availability": field_state["portfolio_marginal_utility_input_availability"],
        "regime_memory_input_availability": field_state["regime_memory_input_availability"],
        "scenario_ladder_input_availability": field_state["scenario_ladder_input_availability"],
        "no_trade_comparator_input_availability": field_state["no_trade_comparator_input_availability"],
        "quantum_coefficient_feature_input_availability": field_state["quantum_coefficient_feature_input_availability"],
        "champion_authority_created_flag": False,
        "no_trade_dominance_claim_created_flag": False,
        "rp2_batch_refs": [generated_ref(report_path("PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch"))],
        "rank2_batch_refs": [generated_ref(report_path("PR168_DATA1_PR168_RANK2_FirstEvidenceRankingBatch"))],
        "created_at_utc": created_at_utc,
        **route_defaults("replay", data1_refs=[generated_ref(report_path("PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch"))]),
    }
