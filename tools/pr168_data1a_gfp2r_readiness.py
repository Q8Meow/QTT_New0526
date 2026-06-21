#!/usr/bin/env python3
"""GFP2R allowed data-family contract and readiness decision."""

from __future__ import annotations

from typing import Any

from tools.pr168_data1a_config import generated_ref, report_path, route_defaults


ALLOWED_DATA_FAMILIES = [
    "current_book",
    "forward_l2_after_capture_start",
    "historical_trade",
    "candlestick_history",
    "price_history",
    "market_lifecycle",
    "resolution_inputs",
    "tick_size_min_order_size_when_present",
]

REPAIR_ONLY_DATA_FAMILIES = [
    "historical_full_book",
    "source_evidence_acceptance",
    "formula_input_binding",
    "explicit_fee_model_when_missing",
    "ForecastEx_IBKR_authenticated_market_data",
]

FORBIDDEN_ASSUMPTIONS = [
    "historical_full_book_exists",
    "current_book_is_historical_full_book",
    "historical_trades_are_full_book",
    "candles_or_price_history_are_full_book",
    "forward_l2_covers_time_before_capture_start",
    "candidate_data_proves_REAL_POSITIVE_or_REAL_NEGATIVE",
]


def build_gfp2r_readiness(
    quality_summary: dict[str, Any],
    quality_rows: list[dict[str, Any]],
    qku_summary: dict[str, Any],
    formula_summary: dict[str, Any],
    historical_summary: dict[str, Any],
    created_at_utc: str,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    selected_rows = [
        row
        for row in quality_rows
        if row["data_sufficiency_tier"]
        in {"DATA_SUFFICIENCY_TIER_A_REPLAY_READY_CANDIDATE", "DATA_SUFFICIENCY_TIER_B_FORMULA_COMPUTE_READY_CANDIDATE"}
    ]
    medium_or_better_bridge = (
        qku_summary.get("qku_unblock_confidence_high_count", 0)
        + qku_summary.get("qku_unblock_confidence_medium_count", 0)
    ) > 0
    go_flag = bool(selected_rows and medium_or_better_bridge and not historical_summary["GFP2R_historical_full_book_assumption_allowed_flag"])
    go_state = (
        "READY_FOR_GFP2R_WITH_PUBLIC_CANDIDATE_DATA_ONLY"
        if go_flag
        else "PARTIAL_READY_REQUIRES_FORMULA_INPUT_REPAIR"
    )
    contract = {
        "contract_id": "pr168_data1a_gfp2r_allowed_data_family_contract",
        "allowed_data_families": ALLOWED_DATA_FAMILIES,
        "repair_only_data_families": REPAIR_ONLY_DATA_FAMILIES,
        "forbidden_assumptions": FORBIDDEN_ASSUMPTIONS,
        "confidence_tier_map": {
            "exact_qku_formula_rows": "exact formula-proof candidate only after GFP2R binds market/input refs",
            "medium_confidence_rows": "mapping repair queue, not exact proof input",
            "low_confidence_rows": "planning only",
        },
        "gfp2r_allowed_data_family_count": len(ALLOWED_DATA_FAMILIES),
        "gfp2r_forbidden_assumption_count": len(FORBIDDEN_ASSUMPTIONS),
        **route_defaults("formula", data1_refs=[generated_ref(report_path("PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse"))]),
    }
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(selected_rows, start=1):
        rows.append(
            {
                "gfp2r_readiness_row_id": f"gfp2r_readiness_{index:05d}",
                "market_or_token_ref": row["market_or_token_ref"],
                "venue": row["venue"],
                "data_sufficiency_tier": row["data_sufficiency_tier"],
                "allowed_data_families": ALLOWED_DATA_FAMILIES,
                "repair_only_data_families": REPAIR_ONLY_DATA_FAMILIES,
                "forbidden_assumptions": FORBIDDEN_ASSUMPTIONS,
                "candidate_only_computation_allowed_flag": True,
                "historical_full_book_assumption_allowed_flag": False,
                "real_positive_negative_allowed_flag": False,
                "source_evidence_required_before_REAL_POSITIVE_NEGATIVE_flag": True,
                "minimum_required_GFP2R_input_repairs": [
                    "bind DATA1 market/token refs to QKU/formula variables",
                    "preserve historical-full-book false flag",
                    "attach source-evidence acceptance gate before any real label",
                ],
                "created_at_utc": created_at_utc,
                **route_defaults("formula", data1_refs=[generated_ref(report_path("PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse"))]),
            }
        )
    decision = {
        "GFP2R_go_flag": go_flag,
        "GFP2R_go_state": go_state,
        "allowed_data_families": ALLOWED_DATA_FAMILIES,
        "repair_only_data_families": REPAIR_ONLY_DATA_FAMILIES,
        "forbidden_assumptions": FORBIDDEN_ASSUMPTIONS,
        "candidate_only_computation_allowed_flag": go_flag,
        "real_positive_negative_allowed_flag": False,
        "historical_full_book_assumption_allowed_flag": False,
        "current_book_allowed_flag": True,
        "forward_l2_allowed_flag": True,
        "historical_trade_allowed_flag": True,
        "historical_candle_allowed_flag": True,
        "price_history_allowed_flag": True,
        "source_evidence_required_before_REAL_POSITIVE_NEGATIVE_flag": True,
        "minimum_required_GFP2R_input_repairs": [
            "formula_input_binding",
            "source_evidence_acceptance_before_real_labels",
            "fee_cost_resolution_latency_completion_for_execution_adjusted_outputs",
        ],
        "first_GFP2R_batch_refs": [row["gfp2r_readiness_row_id"] for row in rows],
        "first_RP2_batch_refs": [generated_ref(report_path("PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch"))],
        "first_RANK2_batch_refs": [generated_ref(report_path("PR168_DATA1_PR168_RANK2_FirstEvidenceRankingBatch"))],
        "operator_actions_before_GFP2R": ["RUN_GFP2R_CANDIDATE_COMPUTE", "SOURCE_EVIDENCE_REVIEW"],
        "gfp2r_allowed_data_family_count": len(ALLOWED_DATA_FAMILIES),
        "gfp2r_forbidden_assumption_count": len(FORBIDDEN_ASSUMPTIONS),
        "formula_input_coverage_rate": formula_summary["formula_input_coverage_rate"],
        **route_defaults("formula", data1_refs=[generated_ref(report_path("PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse"))]),
    }
    return contract, decision, rows
