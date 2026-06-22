#!/usr/bin/env python3
"""QKU/formula/data-consumer mapping repair rows for PR168-GFP2R."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2r_config import route_defaults
from tools.pr168_gfp2r_input_discovery import MarketContext, data1_report_refs, data1a_report_refs


def _qku_rows(context: dict[str, Any]) -> list[dict[str, Any]]:
    report = context["data1a_reports"].get("PR168_DATA1A_QKUComputabilityRouteLedger", {})
    rows = report.get("rows", []) if isinstance(report, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def build_qku_formula_mapping_rows(context: dict[str, Any]) -> list[dict[str, Any]]:
    data1_refs = data1_report_refs()
    data1a_refs = data1a_report_refs()
    rows: list[dict[str, Any]] = []
    for index, qku_row in enumerate(_qku_rows(context), start=1):
        exact_pair = qku_row.get("match_state") == "EXACT_QKU_FORMULA_MATCH"
        confidence = "MEDIUM" if exact_pair else "LOW"
        mapping_class = (
            "PROVISIONAL_TO_EXACT_REPAIR_CANDIDATE"
            if exact_pair
            else "DATA_CONSUMER_REQUIREMENT_MATCH_ONLY"
        )
        if qku_row.get("historical_full_book_required_flag") and not qku_row.get("historical_full_book_available_flag"):
            repair_route = "REPAIR_REQUIRED_HISTORICAL_FULL_BOOK_OR_DATA1A_SUBSTITUTE_LIMITED_ROUTE"
        else:
            repair_route = "REPAIR_REQUIRED_FORMULA_INPUT_BINDING"
        rows.append(
            {
                "mapping_row_id": f"mapping_repair_{index:05d}",
                "formula_variant_id": None,
                "qku_id": qku_row.get("qku_id"),
                "formula_id": qku_row.get("formula_id_if_available"),
                "parent_formula_id": qku_row.get("formula_id_if_available"),
                "template_id": None,
                "candidate_id": qku_row.get("candidate_id_if_available"),
                "data_consumer_id": qku_row.get("qku_unblock_row_id"),
                "mapping_class": mapping_class,
                "mapping_confidence": confidence,
                "mapping_source_refs": [qku_row.get("qku_unblock_row_id")],
                "join_strategy_used": "DATA1A_QKU_COMPUTABILITY_ROW_CONSUMPTION",
                "join_key_used": "qku_id + formula_id_if_available + data_family_requirement",
                "DATA1A_unblock_row_refs": [qku_row.get("qku_unblock_row_id")],
                "DATA1A_formula_input_coverage_refs": [
                    "docs/master_plan/generated/PR168_DATA1A_FormulaInputCoverageMatrix.report.json"
                ],
                "DATA1A_allowed_data_family_refs": [
                    "docs/master_plan/generated/PR168_DATA1A_GFP2RAllowedDataFamilyContract.report.json"
                ],
                "DATA1_snapshot_refs": qku_row.get("DATA1_snapshot_refs", []),
                "DATA1_feature_refs": qku_row.get("DATA1_feature_refs", []),
                "required_formula_inputs": qku_row.get("remaining_missing_components", []),
                "available_formula_inputs": qku_row.get("DATA1_feature_refs", []),
                "missing_formula_inputs": qku_row.get("remaining_missing_components", []),
                "input_alias_normalization_refs": [],
                "input_unit_normalization_refs": [],
                "formula_expression_canonical": None,
                "formula_expression_source_ref": qku_row.get("previous_block_report_ref"),
                "formula_units_valid_flag": False,
                "formula_dimension_validation_state": "REPAIR_REQUIRED_BEFORE_FORMULA_DIMENSION_PROOF",
                "formula_equivalence_cluster_id": None,
                "duplicate_suppressed_flag": False,
                "trial_family_id": f"trial_family_qku_repair_{index:05d}",
                "parameter_family_id": "parameter_family_mapping_repair",
                "variant_parameter_values": {},
                "historical_full_book_required_flag": bool(qku_row.get("historical_full_book_required_flag")),
                "historical_full_book_available_flag": False,
                "exact_candidate_compute_eligible_flag": False,
                "provisional_compute_eligible_flag": False,
                "repair_route": repair_route,
                "GFP2R_consumption_scope": "REPAIR_ROUTE_ONLY_NOT_EXACT_PROOF",
                "RP2_handoff_allowed_flag": False,
                "RANK2_handoff_allowed_flag": False,
                **route_defaults(
                    "formula",
                    data1_refs=data1_refs,
                    data1a_refs=data1a_refs,
                    upstream_refs=[qku_row.get("qku_unblock_row_id")],
                    computed_from_refs=[qku_row.get("qku_unblock_row_id")],
                ),
            }
        )
    offset = len(rows)
    for context_index, market_context in enumerate(context["market_contexts"], start=1):
        rows.append(build_data_consumer_mapping_row(market_context, offset + context_index))
    return rows


def build_data_consumer_mapping_row(market_context: MarketContext, index: int) -> dict[str, Any]:
    data1_refs = data1_report_refs()
    data1a_refs = data1a_report_refs()
    return {
        "mapping_row_id": f"mapping_repair_{index:05d}",
        "formula_variant_id": None,
        "qku_id": None,
        "formula_id": "PR168_GFP2R_DATA_CONSUMER_FORMULA_SET",
        "parent_formula_id": "PR168_GFP2R_DATA_CONSUMER_FORMULA_SET",
        "template_id": "DATA1A_MARKET_CONTEXT_FORMULA_SET",
        "candidate_id": market_context.context_id,
        "data_consumer_id": f"data_consumer::{market_context.venue}::{market_context.market_id_or_token_id}",
        "mapping_class": "PROVISIONAL_DATA_CONSUMER_FORMULA_COMPUTE_READY",
        "mapping_confidence": "MEDIUM",
        "mapping_source_refs": [market_context.context_id],
        "join_strategy_used": "DATA1A_DATA_QUALITY_MARKET_CONTEXT_JOIN",
        "join_key_used": "venue + market_id_or_token_id + snapshot_refs + data_quality_ref",
        "DATA1A_unblock_row_refs": [],
        "DATA1A_formula_input_coverage_refs": [
            "docs/master_plan/generated/PR168_DATA1A_FormulaInputCoverageMatrix.report.json"
        ],
        "DATA1A_allowed_data_family_refs": [
            "docs/master_plan/generated/PR168_DATA1A_GFP2RAllowedDataFamilyContract.report.json"
        ],
        "DATA1_snapshot_refs": market_context.data1_snapshot_refs,
        "DATA1_feature_refs": market_context.feature_refs,
        "required_formula_inputs": ["current_orderbook_snapshot", "price_history", "market_lifecycle"],
        "available_formula_inputs": market_context.feature_refs,
        "missing_formula_inputs": [],
        "input_alias_normalization_refs": [],
        "input_unit_normalization_refs": [],
        "formula_expression_canonical": "DATA1A market context can feed bounded non-proof formula templates",
        "formula_expression_source_ref": "tools/pr168_gfp2r_formula_template_bank.py",
        "formula_units_valid_flag": True,
        "formula_dimension_validation_state": "DATA_CONSUMER_CONTEXT_VALID_FOR_PROVISIONAL_COMPUTE",
        "formula_equivalence_cluster_id": None,
        "duplicate_suppressed_flag": False,
        "trial_family_id": f"trial_family_data_consumer_{index:05d}",
        "parameter_family_id": "parameter_family_data_consumer_context",
        "variant_parameter_values": {
            "venue": market_context.venue,
            "market_id_or_token_id": market_context.market_id_or_token_id,
        },
        "historical_full_book_required_flag": False,
        "historical_full_book_available_flag": False,
        "exact_candidate_compute_eligible_flag": False,
        "provisional_compute_eligible_flag": True,
        "repair_route": "PROVISIONAL_COMPUTE_THEN_ROUTE_TO_QKU_FORMULA_BINDING_REPAIR",
        "GFP2R_consumption_scope": "PROVISIONAL_DATA_CONSUMER_NON_PROOF",
        "RP2_handoff_allowed_flag": True,
        "RANK2_handoff_allowed_flag": True,
        **route_defaults(
            "formula",
            data1_refs=data1_refs,
            data1a_refs=data1a_refs,
            upstream_refs=[market_context.context_id],
            computed_from_refs=market_context.snapshot_refs,
        ),
    }
