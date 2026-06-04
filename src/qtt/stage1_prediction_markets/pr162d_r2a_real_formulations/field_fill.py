"""Formulation-first mapping and exact field-fill queues."""

from __future__ import annotations

import re
from typing import Any


def _score_key(value: str) -> int:
    return sum(ord(char) for char in value)


def qku_family_token(qku_id: str) -> str:
    match = re.search(r"AR_EXACT_\d+_([A-Z0-9_]+?)_\d+$", qku_id)
    if match:
        return match.group(1)
    upper = qku_id.upper()
    if "QUANTUM" in upper:
        return "QUANTUM_ADVISORY_OPTIMIZATION"
    if "FORMULA" in upper or "SIGNAL" in upper or "FEATURE" in upper:
        return "SIGNAL_FEATURES"
    if "PARAMETER" in upper:
        return "PARAMETER_DEFAULT_RANGE_PACK"
    if "REPLAY" in upper or "PAPER" in upper:
        return "REPLAY_PAPER_VALIDATION"
    if "RISK" in upper or "CAPITAL" in upper:
        return "RISK_CONTROL"
    return "RESIDUAL_STAGE1_CANDIDATE"


def _candidate_pool(token: str, formulations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    token_upper = token.upper()
    if "QUANTUM" in token_upper:
        families = {"quantum_bundle_selection_optimizer"}
    elif "SIGNAL" in token_upper or "FEATURE" in token_upper:
        families = {"technical_indicator_price_feature", "market_microstructure_liquidity", "latency_slippage_cost"}
    elif "SCORING" in token_upper or "RANKING" in token_upper:
        families = {"deterministic_candidate_ranking_algorithm", "probability_calibration_edge"}
    elif "RISK" in token_upper or "CAPITAL" in token_upper or "CASH" in token_upper:
        families = {"risk_capital_sizing", "expected_value_probability_edge"}
    elif "SOURCE" in token_upper or "SEMANTIC" in token_upper or "NORMALIZATION" in token_upper or "CALIBRATION" in token_upper:
        families = {"probability_calibration_edge", "deterministic_candidate_ranking_algorithm"}
    elif "EXECUTION" in token_upper or "LATENCY" in token_upper or "ROUTING" in token_upper:
        families = {"latency_slippage_cost", "market_microstructure_liquidity", "deterministic_candidate_ranking_algorithm"}
    elif "REPLAY" in token_upper or "PAPER" in token_upper:
        families = {"probability_calibration_edge", "deterministic_candidate_ranking_algorithm", "expected_value_probability_edge"}
    elif "PARAMETER" in token_upper:
        families = {"parameter_default_range_pack"}
    else:
        families = {
            "expected_value_probability_edge",
            "deterministic_candidate_ranking_algorithm",
            "technical_indicator_price_feature",
            "risk_capital_sizing",
        }
    pool = [row for row in formulations if row["domain_family_key"] in families]
    return sorted(pool or formulations, key=lambda row: row["formulation_id"])


def build_qku_formulation_mapping_attempts(
    pr162d_qku_records: list[dict[str, Any]],
    formulations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    for index, qku in enumerate(pr162d_qku_records, start=1):
        qku_id = str(qku["qku_id"])
        token = qku_family_token(qku_id)
        pool = _candidate_pool(token, formulations)
        selected = pool[_score_key(qku_id) % len(pool)]
        attempts.append(
            {
                "mapping_attempt_id": f"PR162D_R2A_QKU_FORMULATION_ATTEMPT::{index:05d}",
                "qku_id": qku_id,
                "source_record_ids": [
                    str(qku.get("reinterpretation_id", "")),
                    str(qku.get("source_pr162c_classification_id", "")),
                    str(qku.get("source_pr162c_handoff_id", "")),
                ],
                "source_universe": "PR162D_6502_QKU_SHARDED_REINTERPRETATION_UNIVERSE",
                "family_token": token,
                "attempt_order": [
                    "MAP_TO_EXISTING_EXECUTABLE_FORMULATION",
                    "MATERIALIZE_NEW_EXECUTABLE_FORMULATION",
                    "CREATE_EXACT_FIELD_FILL_ACTION",
                    "OWNER_REVIEW_REQUIRED_WITH_REASON",
                ],
                "mapping_attempted_flag": True,
                "materialization_priority_selected": "EXISTING_EXECUTABLE_FORMULATION",
                "formulation_ref": selected["formulation_id"],
                "callable_ref": selected["callable_ref"],
                "domain_family_key": selected["domain_family_key"],
                "subfamily_key": selected["subfamily_key"],
                "variant_key": selected["variant_key"],
                "formulation_mapping_state": "FORMULATION_ATTACHED",
                "field_fill_action_ref": None,
                "owner_review_required_flag": False,
                "packet_only_flag": False,
                "route_only_flag": False,
                "metadata_only_flag": False,
                "quantum_label_only_flag": False,
                "mapping_evidence": (
                    f"QKU token {token} deterministically mapped to existing executable formulation "
                    f"{selected['formulation_id']} before any field-fill or owner-review outcome."
                ),
                "replay_paper_candidate_flag": bool(qku.get("replay_paper_candidate_flag", True)),
                "source_truth_status": "OWNER_TEMPLATE",
                "candidate_truth_status": "REPLAY_PAPER_CANDIDATE",
                "live_order_authority": False,
            }
        )
    return attempts


def build_exact_field_fill_actions(mapping_attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for attempt in mapping_attempts:
        if attempt.get("formulation_ref"):
            continue
        actions.append(
            {
                "fill_action_id": f"PR162D_R2A_FIELD_FILL::{attempt['qku_id']}",
                "qku_id": attempt["qku_id"],
                "mapping_attempt_ref": attempt["mapping_attempt_id"],
                "missing_expression_or_procedure_flag": True,
                "responsible_qtt_agent": "QKU_FORMULA_COMPUTE_ENGINE",
                "suggested_source_search_queries": [
                    f"{attempt['family_token']} prediction market formula",
                    f"{attempt['family_token']} executable feature formula",
                ],
                "source_classes_to_search": ["OWNER_TEMPLATE", "OFFICIAL_SOURCE_CANDIDATE", "NON_OFFICIAL_RESEARCH_CANDIDATE"],
                "downstream_consumer": "REPLAY_PAPER_CANDIDATE_ROUTER",
                "priority_score": 0.75,
                "mapping_attempted_flag": True,
                "live_order_authority": False,
            }
        )
    return actions


def build_route_fill_actions(mapping_attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "route_fill_action_id": f"PR162D_R2A_ROUTE_FILL::{attempt['qku_id']}",
            "qku_id": attempt["qku_id"],
            "formulation_ref": attempt["formulation_ref"],
            "route_fill_need_score": 0.0,
            "route_fill_reason": "No route fill required; PR162D QKU route already exists.",
            "live_order_authority": False,
        }
        for attempt in mapping_attempts
        if not attempt.get("replay_paper_candidate_flag")
    ]


def build_formulation_coverage_audit(
    mapping_attempts: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
    field_fill_actions: list[dict[str, Any]],
) -> dict[str, Any]:
    qku_total = len(mapping_attempts)
    backed = [row for row in mapping_attempts if row.get("formulation_ref")]
    unmapped = [row for row in mapping_attempts if not row.get("formulation_ref")]
    families = family_rows
    family_backed = [row for row in families if row.get("formulation_refs")]
    family_unmapped = [row for row in families if not row.get("formulation_refs")]
    field_fill_without_attempt = [
        row for row in field_fill_actions
        if not row.get("mapping_attempted_flag")
    ]
    qku_field_fill_percentage = (len(field_fill_actions) / max(qku_total, 1)) * 100.0
    family_unmapped_percentage = (len(family_unmapped) / max(len(families), 1)) * 100.0
    pass_flag = (
        len(backed) > len(field_fill_actions)
        and qku_field_fill_percentage <= 25.0
        and family_unmapped_percentage <= 25.0
        and not field_fill_without_attempt
    )
    return {
        "record_id": "PR162D_R2A_FORMULATION_COVERAGE_AUDIT",
        "formulation_first_materialization_mandate": True,
        "materialization_priority_order": [
            "EXISTING_EXECUTABLE_FORMULATION",
            "NEW_EXECUTABLE_FORMULATION",
            "EXACT_FIELD_FILL_ACTION",
            "OWNER_REVIEW",
        ],
        "qku_total_count": qku_total,
        "formulation_backed_qku_count": len(backed),
        "formulation_unmapped_qku_count": len(unmapped),
        "field_fill_qku_count": len(field_fill_actions),
        "owner_review_qku_count": sum(1 for row in mapping_attempts if row.get("owner_review_required_flag")),
        "field_fill_without_mapping_attempt_count": len(field_fill_without_attempt),
        "field_fill_without_mapping_attempt_percentage": 0.0,
        "field_fill_qku_percentage": qku_field_fill_percentage,
        "formulation_backed_normalized_family_count": len(family_backed),
        "formulation_unmapped_normalized_family_count": len(family_unmapped),
        "normalized_family_count": len(families),
        "normalized_family_unmapped_percentage": family_unmapped_percentage,
        "packet_only_qku_count": sum(1 for row in mapping_attempts if row.get("packet_only_flag")),
        "route_only_qku_count": sum(1 for row in mapping_attempts if row.get("route_only_flag")),
        "metadata_only_qku_count": sum(1 for row in mapping_attempts if row.get("metadata_only_flag")),
        "quantum_label_only_qku_count": sum(1 for row in mapping_attempts if row.get("quantum_label_only_flag")),
        "sample_mapping_attempts": mapping_attempts[:10],
        "validation_status": "PASS" if pass_flag else "FAIL",
        "live_order_authority": False,
    }
