#!/usr/bin/env python3
"""Negative-to-positive recovery readiness routing without positive claims."""

from __future__ import annotations

import json
from typing import Any

from tools.pr168_data1a_config import generated_ref, report_path, route_defaults


def _prior_recovery_rows() -> list[dict[str, Any]]:
    path = report_path("PR162E_PostRepairRetestQueue")
    if not path.exists():
        return []
    try:
        records = json.loads(path.read_text(encoding="utf-8")).get("records", [])
    except json.JSONDecodeError:
        return []
    return records if isinstance(records, list) else []


def build_recovery_readiness(
    quality_rows: list[dict[str, Any]],
    qku_rows: list[dict[str, Any]],
    created_at_utc: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    prior_rows = _prior_recovery_rows()[:5]
    for index, quality in enumerate(quality_rows, start=1):
        diagnosis = [
            "missing_historical_full_book_but_substitute_possible",
            "source_acceptance_pending",
            "formula_input_binding_missing",
        ]
        if not quality["spread_coverage_flag"]:
            diagnosis.append("spread_regime_too_wide")
        if not quality["fee_coverage_flag"]:
            diagnosis.append("missing_fee_tick_min_size")
        if quality["depth_coverage_flag"]:
            route = "RECOVERY_READY_FOR_RP2_REPLAY_PAPER_WITH_DATA1_SUBSTITUTES"
            target = "TCA"
        else:
            route = "RECOVERY_REQUIRES_FEE_RESOLUTION_LATENCY_REPAIR"
            target = "fill"
        rows.append(
            {
                "recovery_row_id": f"recovery_{index:05d}",
                "qku_id_if_available": qku_rows[index - 1]["qku_id"] if index - 1 < len(qku_rows) else None,
                "formula_id_if_available": qku_rows[index - 1]["formula_id_if_available"] if index - 1 < len(qku_rows) else None,
                "candidate_id_if_available": None,
                "candidate_stack_id_if_available": None,
                "previous_negative_or_weak_ref_if_available": None,
                "DATA1_snapshot_refs": quality["snapshot_refs"],
                "DATA1_feature_refs": quality["feature_names"],
                "diagnosis_dimensions": diagnosis,
                "recovery_route_state": route,
                "priority_score_non_proof": round(quality["data_quality_score_non_proof"] + 1.0, 6),
                "priority_reason": "DATA1 supplies current/forward market-data substitutes that can repair weak replay inputs without proving positivity.",
                "expected_downstream_unblock_count": 3,
                "expected_metric_improvement_target": target,
                "next_pr": "PR168-RP2" if route.endswith("SUBSTITUTES") else "PR168-GFP2R",
                "real_positive_claim_allowed_flag": False,
                "created_at_utc": created_at_utc,
                **route_defaults("risk", data1_refs=[generated_ref(report_path("PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch"))]),
            }
        )
    for offset, prior in enumerate(prior_rows, start=len(rows) + 1):
        rows.append(
            {
                "recovery_row_id": f"recovery_{offset:05d}",
                "qku_id_if_available": None,
                "formula_id_if_available": None,
                "candidate_id_if_available": prior.get("original_negative_ref"),
                "candidate_stack_id_if_available": prior.get("plugin_id"),
                "previous_negative_or_weak_ref_if_available": prior.get("row_id"),
                "DATA1_snapshot_refs": ["docs/master_plan/generated/PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse.report.json"],
                "DATA1_feature_refs": ["DATA1_FEATURE_FAMILY_ROUTE_ONLY"],
                "diagnosis_dimensions": [
                    "QKU_formula_mapping_inferred_only",
                    "formula_input_binding_missing",
                    "source_acceptance_pending",
                    "quantum_coefficients_missing",
                    "classical_comparator_missing",
                ],
                "recovery_route_state": "RECOVERY_REQUIRES_FORMULA_INPUT_BINDING_REPAIR",
                "priority_score_non_proof": float(prior.get("repair_roi_score") or 0.0),
                "priority_reason": "Prior negative repair candidate can consume DATA1A market-data routes after GFP2R mapping repair.",
                "expected_downstream_unblock_count": 1,
                "expected_metric_improvement_target": "formula_binding",
                "next_pr": "PR168-GFP2R",
                "real_positive_claim_allowed_flag": False,
                "created_at_utc": created_at_utc,
                **route_defaults("formula", data1_refs=[generated_ref(report_path("PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse"))]),
            }
        )
    summary = {
        "negative_to_positive_recovery_ready_count": sum(
            1 for row in rows if row["recovery_route_state"] in {
                "RECOVERY_READY_FOR_GFP2R_CANDIDATE_COMPUTE",
                "RECOVERY_READY_FOR_RP2_REPLAY_PAPER_WITH_DATA1_SUBSTITUTES",
            }
        ),
        "negative_to_positive_recovery_repair_required_count": sum(
            1 for row in rows if "REQUIRES" in row["recovery_route_state"]
        ),
        "real_positive_claim_allowed_flag": False,
        "profit_evidence_created_flag": False,
        **route_defaults("risk", data1_refs=[generated_ref(report_path("PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch"))]),
    }
    return summary, rows
