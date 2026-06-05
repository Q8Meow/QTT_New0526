"""Map source candidates and normalization receipts to materialized bindings."""

from __future__ import annotations

from typing import Any


def build_source_candidate_to_binding_rows(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for binding in dataset_bindings:
        rows.append(
            {
                "source_candidate_to_binding_id": f"PR162R_B_SOURCE_TO_BINDING::{len(rows) + 1:04d}",
                "source_candidate_refs": list(binding.get("source_candidate_refs", [])),
                "normalization_receipt_refs": list(binding.get("normalization_receipt_refs", [])),
                "binding_ref": binding["binding_id"],
                "binding_family": binding["binding_family"],
                "venue_scope": binding["venue_scope"],
                "candidate_truth_status": binding["candidate_truth_status"],
                "promotion_requires_later_source_acceptance": True,
                "no_source_acceptance": True,
                "no_connector_binding": True,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_online_dataset_source_scout_rows(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    seen: set[tuple[str, str]] = set()
    for binding in dataset_bindings:
        key = (binding["binding_family"], binding["venue_scope"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "online_dataset_source_scout_id": f"PR162R_B_ONLINE_DATASET_SCOUT::{len(rows) + 1:04d}",
                "binding_family": binding["binding_family"],
                "venue_scope": binding["venue_scope"],
                "source_scout_query": _query(binding["binding_family"], binding["venue_scope"]),
                "source_classes_to_scout": [
                    "OFFICIAL_SOURCE_CANDIDATE",
                    "NON_OFFICIAL_WEB_CANDIDATE",
                    "RESEARCH_SOURCE_CANDIDATE",
                    "PUBLIC_DATASET_CANDIDATE",
                ],
                "candidate_truth_status_only": True,
                "runtime_retrieval_allowed": False,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def _query(family: str, venue: str) -> str:
    return f"{venue} {family} historical dataset data dictionary replay paper candidate source"
