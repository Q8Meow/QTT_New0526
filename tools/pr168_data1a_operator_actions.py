#!/usr/bin/env python3
"""Operator action matrix for PR168-DATA1A."""

from __future__ import annotations

from typing import Any

from tools.pr168_data1a_config import generated_ref, report_path, route_defaults


def build_operator_actions(
    quality_rows: list[dict[str, Any]],
    recovery_rows: list[dict[str, Any]],
    quantum_summary: dict[str, Any],
    created_at_utc: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for quality in quality_rows:
        action_type = "RUN_RP2" if quality["RP2_replay_paper_ready_flag"] else "RUN_GFP2R"
        next_pr = "PR168-RP2" if action_type == "RUN_RP2" else "PR168-GFP2R"
        rows.append(
            {
                "action_id": f"operator_action_{len(rows) + 1:05d}",
                "action_type": action_type,
                "priority_score_non_proof": quality["data_quality_score_non_proof"],
                "priority_reason": quality["sufficiency_reason_codes"],
                "venue": quality["venue"],
                "artifact_ref": generated_ref(report_path("PR168_DATA1A_DataQualityCoverageAudit")),
                "market_or_token_ref": quality["market_or_token_ref"],
                "qku_or_formula_ref_if_available": None,
                "candidate_stack_id_if_available": None,
                "next_command_or_next_pr": next_pr,
                "missing_input_or_gap_code": "FORMULA_INPUT_BINDING_OR_SOURCE_ACCEPTANCE",
                "expected_downstream_unblock_count": 3,
                "data_quality_score_non_proof": quality["data_quality_score_non_proof"],
                "alpha_capture_readiness_score_non_proof": None,
                "historical_full_book_gap_flag": True,
                "recovery_route_state_if_applicable": None,
                "quantum_usability_state_if_applicable": None,
                "no_live_authority_flag": True,
                "created_at_utc": created_at_utc,
                **route_defaults("governance", data1_refs=[generated_ref(report_path("PR168_DATA1A_DataQualityCoverageAudit"))]),
            }
        )
    rows.append(
        {
            "action_id": f"operator_action_{len(rows) + 1:05d}",
            "action_type": "SOURCE_EVIDENCE_REVIEW",
            "priority_score_non_proof": 1.0,
            "priority_reason": "required before REAL_POSITIVE/REAL_NEGATIVE labels in downstream PRs",
            "venue": "multi_venue",
            "artifact_ref": generated_ref(report_path("PR168_DATA1A_EndpointAssumptionDriftAudit")),
            "market_or_token_ref": "all_DATA1_candidate_rows",
            "qku_or_formula_ref_if_available": None,
            "candidate_stack_id_if_available": None,
            "next_command_or_next_pr": "SOURCE_EVIDENCE_REVIEW",
            "missing_input_or_gap_code": "SOURCE_EVIDENCE_ACCEPTANCE_REQUIRED",
            "expected_downstream_unblock_count": 3,
            "data_quality_score_non_proof": None,
            "alpha_capture_readiness_score_non_proof": None,
            "historical_full_book_gap_flag": True,
            "recovery_route_state_if_applicable": None,
            "quantum_usability_state_if_applicable": None,
            "no_live_authority_flag": True,
            "created_at_utc": created_at_utc,
            **route_defaults("source_evidence", data1_refs=[generated_ref(report_path("PR168_DATA1A_EndpointAssumptionDriftAudit"))]),
        }
    )
    rows.append(
        {
            "action_id": f"operator_action_{len(rows) + 1:05d}",
            "action_type": "HISTORICAL_L2_ACQUISITION_REVIEW",
            "priority_score_non_proof": 1.0,
            "priority_reason": "historical full-book verified public rows remain zero",
            "venue": "multi_venue",
            "artifact_ref": generated_ref(report_path("PR168_DATA1A_HistoricalFullBookTruthLedger")),
            "market_or_token_ref": "all_DATA1_markets",
            "qku_or_formula_ref_if_available": None,
            "candidate_stack_id_if_available": None,
            "next_command_or_next_pr": "DATA1B",
            "missing_input_or_gap_code": "HISTORICAL_FULL_BOOK_PUBLIC_UNAVAILABLE",
            "expected_downstream_unblock_count": 3,
            "data_quality_score_non_proof": None,
            "alpha_capture_readiness_score_non_proof": None,
            "historical_full_book_gap_flag": True,
            "recovery_route_state_if_applicable": None,
            "quantum_usability_state_if_applicable": None,
            "no_live_authority_flag": True,
            "created_at_utc": created_at_utc,
            **route_defaults("market_data", data1_refs=[generated_ref(report_path("PR168_DATA1A_HistoricalFullBookTruthLedger"))]),
        }
    )
    if quantum_summary.get("penalty_scaling_gap_count") or quantum_summary.get("interpret_back_gap_count"):
        rows.append(
            {
                "action_id": f"operator_action_{len(rows) + 1:05d}",
                "action_type": "QUANTUM_MAPPING_REVIEW",
                "priority_score_non_proof": 0.75,
                "priority_reason": "penalty scaling or interpret-back gaps remain",
                "venue": "multi_venue",
                "artifact_ref": generated_ref(report_path("PR168_DATA1A_QuantumForwardUsabilityAudit")),
                "market_or_token_ref": "quantum_feature_surface",
                "qku_or_formula_ref_if_available": None,
                "candidate_stack_id_if_available": None,
                "next_command_or_next_pr": "PR162E-Q",
                "missing_input_or_gap_code": "QUANTUM_MAPPING_REPAIR_REQUIRED",
                "expected_downstream_unblock_count": 1,
                "data_quality_score_non_proof": None,
                "alpha_capture_readiness_score_non_proof": None,
                "historical_full_book_gap_flag": True,
                "recovery_route_state_if_applicable": None,
                "quantum_usability_state_if_applicable": "QUANTUM_FORWARD_PARTIAL_MISSING_COEFFICIENTS",
                "no_live_authority_flag": True,
                "created_at_utc": created_at_utc,
                **route_defaults("quantum", data1_refs=[generated_ref(report_path("PR168_DATA1A_QuantumForwardUsabilityAudit"))]),
            }
        )
    for recovery in recovery_rows[:3]:
        rows.append(
            {
                "action_id": f"operator_action_{len(rows) + 1:05d}",
                "action_type": "RECOVERY_RETEST_PREP",
                "priority_score_non_proof": recovery["priority_score_non_proof"],
                "priority_reason": recovery["priority_reason"],
                "venue": "multi_venue",
                "artifact_ref": generated_ref(report_path("PR168_DATA1A_NegativeToPositiveRecoveryReadinessQueue")),
                "market_or_token_ref": ",".join(recovery.get("DATA1_snapshot_refs") or []),
                "qku_or_formula_ref_if_available": recovery.get("qku_id_if_available") or recovery.get("formula_id_if_available"),
                "candidate_stack_id_if_available": recovery.get("candidate_stack_id_if_available"),
                "next_command_or_next_pr": recovery["next_pr"],
                "missing_input_or_gap_code": "RECOVERY_REPAIR_ROUTE",
                "expected_downstream_unblock_count": recovery["expected_downstream_unblock_count"],
                "data_quality_score_non_proof": None,
                "alpha_capture_readiness_score_non_proof": None,
                "historical_full_book_gap_flag": True,
                "recovery_route_state_if_applicable": recovery["recovery_route_state"],
                "quantum_usability_state_if_applicable": None,
                "no_live_authority_flag": True,
                "created_at_utc": created_at_utc,
                **route_defaults("governance", data1_refs=[generated_ref(report_path("PR168_DATA1A_NegativeToPositiveRecoveryReadinessQueue"))]),
            }
        )
    return rows
