"""Classical comparator binding packet builder."""

from __future__ import annotations

from typing import Any


def build_classical_comparator_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for binding in dataset_bindings:
        if binding["binding_family"] != "CLASSICAL_COMPARATOR_INPUTS":
            continue
        rows.append(
            {
                **binding,
                "binding_id": f"PR162R_B_CLASSICAL_COMPARATOR_INPUT_BINDING::{len(rows) + 1:04d}",
                "dataset_binding_ref": binding["binding_id"],
                "comparator_binding_status": "CLASSICAL_COMPARATOR_INPUT_BOUND",
                "comparator_fields": [
                    "expected_value",
                    "transaction_cost_estimate",
                    "risk_score",
                    "liquidity_score",
                    "staleness_seconds",
                ],
                "validation_status": "PASS",
            }
        )
    return rows


def classical_binding_lookup(dataset_bindings: list[dict[str, Any]]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for binding in dataset_bindings:
        if binding["binding_family"] != "CLASSICAL_COMPARATOR_INPUTS":
            continue
        for packet_id in binding.get("consumer_candidate_packet_ids", []):
            lookup.setdefault(packet_id, []).append(binding["binding_id"])
    return {key: sorted(value) for key, value in lookup.items()}
