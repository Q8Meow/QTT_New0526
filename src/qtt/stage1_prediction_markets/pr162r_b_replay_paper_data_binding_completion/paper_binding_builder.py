"""Paper binding spine builders."""

from __future__ import annotations

from typing import Any


PAPER_SPINE_FAMILIES = (
    "PAPER_MARKET_STATE_BINDING",
    "PAPER_SYNTHETIC_FILL_MODEL",
    "PAPER_PORTFOLIO_STATE",
    "PAPER_EXECUTION_COST_MODEL",
)


def build_paper_specific_bindings(dataset_bindings: list[dict[str, Any]], family: str, prefix: str) -> list[dict[str, Any]]:
    rows = []
    for binding in dataset_bindings:
        if binding["binding_family"] != family:
            continue
        rows.append(
            {
                **binding,
                "binding_id": f"{prefix}::{len(rows) + 1:04d}",
                "dataset_binding_ref": binding["binding_id"],
                "paper_binding_status": "PAPER_SYNTHETIC_FIXTURE_BOUND",
                "maker_taker_simulation_fields": ["maker_fee_per_share", "taker_fee_per_share"],
                "partial_fill_fields": ["filled_size", "missed_size", "partial_fill"],
                "stale_quote_rejection_fields": ["stale_quote_rejected", "staleness_seconds"],
                "paper_execution_receipt_schema_boundary_only": True,
                "paper_result_packet_created": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_paper_market_state_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_paper_specific_bindings(
        dataset_bindings,
        "PAPER_MARKET_STATE_BINDING",
        "PR162R_B_PAPER_MARKET_STATE_BINDING",
    )


def build_paper_synthetic_fill_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_paper_specific_bindings(
        dataset_bindings,
        "PAPER_SYNTHETIC_FILL_MODEL",
        "PR162R_B_PAPER_SYNTHETIC_FILL_BINDING",
    )


def build_paper_portfolio_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_paper_specific_bindings(
        dataset_bindings,
        "PAPER_PORTFOLIO_STATE",
        "PR162R_B_PAPER_PORTFOLIO_BINDING",
    )


def build_paper_execution_cost_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_paper_specific_bindings(
        dataset_bindings,
        "PAPER_EXECUTION_COST_MODEL",
        "PR162R_B_PAPER_EXECUTION_COST_BINDING",
    )


def paper_binding_lookup(dataset_bindings: list[dict[str, Any]]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for binding in dataset_bindings:
        if binding["binding_family"] not in PAPER_SPINE_FAMILIES:
            continue
        for packet_id in binding.get("consumer_candidate_packet_ids", []):
            lookup.setdefault(packet_id, []).append(binding["binding_id"])
    return {key: sorted(value) for key, value in lookup.items()}
