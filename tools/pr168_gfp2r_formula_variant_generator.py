#!/usr/bin/env python3
"""Bounded formula variant generation for PR168-GFP2R."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from tools.pr168_gfp2r_config import route_defaults
from tools.pr168_gfp2r_formula_alias_normalizer import UNITS
from tools.pr168_gfp2r_formula_equivalence_dedupe import apply_equivalence
from tools.pr168_gfp2r_formula_template_bank import formula_templates
from tools.pr168_gfp2r_formula_unit_dimension_validator import validate_variant_units
from tools.pr168_gfp2r_input_discovery import (
    MarketContext,
    context_input_values,
    data1_report_refs,
    data1a_report_refs,
)


SIDES = ("YES", "NO")


def _data_consumer_mapping_for(mapping_rows: list[dict[str, Any]], market_context: MarketContext) -> dict[str, Any]:
    data_consumer_id = f"data_consumer::{market_context.venue}::{market_context.market_id_or_token_id}"
    for row in mapping_rows:
        if row.get("data_consumer_id") == data_consumer_id:
            return row
    raise ValueError(f"missing data-consumer mapping for {data_consumer_id}")


def _variant_id(index: int) -> str:
    return f"gfp2r_formula_variant_{index:05d}"


def _variant_row(
    *,
    index: int,
    market_context: MarketContext,
    side: str,
    template: dict[str, Any],
    mapping_row: dict[str, Any],
    available_inputs: dict[str, Any],
    duplicate_receipt: bool = False,
) -> dict[str, Any]:
    validation = validate_variant_units(template, available_inputs)
    eligible = (
        validation["formula_units_valid_flag"]
        and not validation["missing_formula_inputs"]
        and not duplicate_receipt
        and template.get("compute_kind") != "quantum_candidate_stack_variant"
    )
    mapping_class = "FORMULA_VARIANT_GENERATED_NON_PROOF"
    if duplicate_receipt:
        mapping_class = "FORMULA_VARIANT_DUPLICATE_SUPPRESSED"
    elif not validation["formula_units_valid_flag"]:
        mapping_class = "FORMULA_VARIANT_UNIT_INVALID"
    elif validation["missing_formula_inputs"]:
        mapping_class = "FORMULA_VARIANT_DATA_INSUFFICIENT"
    return {
        "mapping_row_id": mapping_row["mapping_row_id"],
        "formula_variant_id": _variant_id(index),
        "qku_id": mapping_row.get("qku_id"),
        "formula_id": template["parent_formula_id"],
        "parent_formula_id": template["parent_formula_id"],
        "template_id": template["template_id"],
        "candidate_id": market_context.context_id,
        "data_consumer_id": mapping_row["data_consumer_id"],
        "mapping_class": mapping_class,
        "mapping_confidence": "MEDIUM" if eligible else "LOW",
        "mapping_source_refs": [mapping_row["mapping_row_id"], market_context.context_id],
        "join_strategy_used": "BOUNDED_TEMPLATE_INSTANTIATION_FROM_DATA1A_MARKET_CONTEXT",
        "join_key_used": "venue + market_id_or_token_id + side + template_id",
        "DATA1A_unblock_row_refs": mapping_row.get("DATA1A_unblock_row_refs", []),
        "DATA1A_formula_input_coverage_refs": mapping_row.get("DATA1A_formula_input_coverage_refs", []),
        "DATA1A_allowed_data_family_refs": mapping_row.get("DATA1A_allowed_data_family_refs", []),
        "DATA1_snapshot_refs": market_context.data1_snapshot_refs,
        "DATA1_feature_refs": market_context.feature_refs,
        "required_formula_inputs": validation["required_formula_inputs"],
        "available_formula_inputs": validation["available_formula_inputs"],
        "missing_formula_inputs": validation["missing_formula_inputs"],
        "input_alias_normalization_refs": [
            f"{name}->{name}" for name in validation["required_formula_inputs"]
        ],
        "input_unit_normalization_refs": [
            f"{name}:{UNITS.get(name, 'unknown')}" for name in validation["required_formula_inputs"]
        ],
        "input_units": {name: UNITS.get(name, "unknown") for name in validation["required_formula_inputs"]},
        "formula_expression_canonical": template["formula_expression_canonical"],
        "formula_expression_source_ref": "tools/pr168_gfp2r_formula_template_bank.py",
        "formula_units_valid_flag": validation["formula_units_valid_flag"],
        "formula_dimension_validation_state": validation["formula_dimension_validation_state"],
        "formula_equivalence_cluster_id": None,
        "duplicate_suppressed_flag": duplicate_receipt,
        "trial_family_id": f"trial_family::{market_context.venue}::{template['template_id']}",
        "formula_variant_family_id": f"formula_variant_family::{template['template_id']}",
        "parameter_family_id": f"parameter_family::{side.lower()}::base",
        "variant_parameter_values": {
            "venue": market_context.venue,
            "market_id_or_token_id": market_context.market_id_or_token_id,
            "side": side,
            "price_band": available_inputs.get("price_band"),
            "edge_band": available_inputs.get("edge_band"),
            "complexity_score": template.get("complexity_score"),
        },
        "formula_complexity_score": template.get("complexity_score"),
        "historical_full_book_required_flag": False,
        "historical_full_book_available_flag": False,
        "exact_candidate_compute_eligible_flag": False,
        "provisional_compute_eligible_flag": eligible,
        "repair_route": None if eligible else "REPAIR_REQUIRED_MISSING_FORMULA_INPUT_OR_UNIT_VALIDATION",
        "GFP2R_consumption_scope": "PROVISIONAL_DATA_CONSUMER_NON_PROOF" if eligible else "REPAIR_ONLY_NOT_PROOF",
        "RP2_handoff_allowed_flag": eligible,
        "RANK2_handoff_allowed_flag": eligible,
        "venue": market_context.venue,
        "market_id_or_token_id": market_context.market_id_or_token_id,
        "side": side,
        "available_input_values": {
            key: value
            for key, value in available_inputs.items()
            if not isinstance(value, (dict, list))
        },
        "market_context": asdict(market_context),
        **route_defaults(
            "formula",
            data1_refs=data1_report_refs(),
            data1a_refs=data1a_report_refs(),
            formula_refs=[template["parent_formula_id"]],
            formula_variant_refs=[_variant_id(index)],
            upstream_refs=[mapping_row["mapping_row_id"], market_context.context_id],
            computed_from_refs=market_context.snapshot_refs,
        ),
    }


def build_formula_variants(context: dict[str, Any], mapping_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    variants: list[dict[str, Any]] = []
    templates = formula_templates()
    index = 0
    for market_context in context["market_contexts"]:
        mapping_row = _data_consumer_mapping_for(mapping_rows, market_context)
        for side in SIDES:
            values = context_input_values(market_context, side)
            if values["entry_price"] is None:
                continue
            for template in templates:
                index += 1
                variants.append(
                    _variant_row(
                        index=index,
                        market_context=market_context,
                        side=side,
                        template=template,
                        mapping_row=mapping_row,
                        available_inputs=values,
                    )
                )
            duplicate_template = templates[0]
            index += 1
            variants.append(
                _variant_row(
                    index=index,
                    market_context=market_context,
                    side=side,
                    template=duplicate_template,
                    mapping_row=mapping_row,
                    available_inputs=values,
                    duplicate_receipt=True,
                )
            )
            invalid_template = {
                **templates[0],
                "template_id": "unit_invalid_entry_price_plus_resolution_timestamp_receipt",
                "parent_formula_id": "PR168_GFP2R_FORMULA_UNIT_INVALID_RECEIPT",
                "formula_expression_canonical": "entry_price + resolution_timestamp",
                "required_formula_inputs": ["entry_price", "resolution_timestamp"],
                "force_unit_invalid_flag": True,
            }
            index += 1
            variants.append(
                _variant_row(
                    index=index,
                    market_context=market_context,
                    side=side,
                    template=invalid_template,
                    mapping_row=mapping_row,
                    available_inputs=values,
                )
            )
    return apply_equivalence(variants)
