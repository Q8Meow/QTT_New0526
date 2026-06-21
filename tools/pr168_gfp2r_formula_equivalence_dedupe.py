#!/usr/bin/env python3
"""Formula equivalence clustering and duplicate suppression."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from tools.pr168_gfp2r_config import route_defaults
from tools.pr168_gfp2r_input_discovery import data1_report_refs, data1a_report_refs


def dedupe_fingerprint(variant: dict[str, Any]) -> str:
    payload = {
        "template_id": variant.get("template_id"),
        "canonical": variant.get("formula_expression_canonical"),
        "venue": variant.get("venue"),
        "market": variant.get("market_id_or_token_id"),
        "side": variant.get("side"),
        "parameters": variant.get("variant_parameter_values", {}),
        "inputs": sorted(variant.get("available_formula_inputs", [])),
        "unit_state": variant.get("formula_dimension_validation_state"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def apply_equivalence(variants: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seen: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    for index, variant in enumerate(variants, start=1):
        fingerprint = dedupe_fingerprint(variant)
        variant["dedupe_fingerprint"] = fingerprint
        cluster = f"formula_equivalence_cluster_{fingerprint[:8]}"
        variant["formula_equivalence_cluster_id"] = cluster
        duplicate_of = seen.get(fingerprint)
        variant["duplicate_suppressed_flag"] = duplicate_of is not None
        if duplicate_of is not None:
            variant["mapping_class"] = "FORMULA_VARIANT_DUPLICATE_SUPPRESSED"
            variant["repair_route"] = f"duplicate_of:{duplicate_of}"
            variant["provisional_compute_eligible_flag"] = False
        else:
            seen[fingerprint] = str(variant.get("formula_variant_id"))
        rows.append(
            {
                "formula_equivalence_row_id": f"formula_equivalence_{index:05d}",
                "formula_variant_id": variant.get("formula_variant_id"),
                "formula_equivalence_cluster_id": cluster,
                "dedupe_fingerprint": fingerprint,
                "duplicate_suppressed_flag": variant["duplicate_suppressed_flag"],
                "duplicate_of_formula_variant_id": duplicate_of,
                "deduplication_decision": "SUPPRESS_DUPLICATE"
                if duplicate_of is not None
                else "KEEP_CANONICAL_VARIANT",
                **route_defaults(
                    "formula",
                    data1_refs=data1_report_refs(),
                    data1a_refs=data1a_report_refs(),
                    formula_refs=[str(variant.get("formula_id"))],
                    formula_variant_refs=[str(variant.get("formula_variant_id"))],
                    upstream_refs=[str(variant.get("formula_variant_id"))],
                ),
            }
        )
    return variants, rows
