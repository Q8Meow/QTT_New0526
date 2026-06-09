"""Similarity match policy rows for PR165-B."""

from __future__ import annotations

from typing import Any

from .condition_scope_vocab import SIMILARITY_DISTANCE_METRIC
from .deterministic_ids import ordinal_ref


def build_similarity_match_policy_record(index: int, ctx: dict[str, Any], condition_id: str, combination_id: str, classification: dict[str, Any]) -> dict[str, Any]:
    positive = classification["memory_classification"].startswith("POSITIVE")
    return {
        "similarity_match_policy_ref": ordinal_ref("PR165_B_SIMILARITY_POLICY", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": condition_id,
        "combination_fingerprint_id": combination_id,
        "exact_condition_match_required": not positive,
        "similarity_match_allowed": True,
        "similarity_distance_metric": SIMILARITY_DISTANCE_METRIC,
        "similarity_threshold": 0.0 if not positive else 0.18,
        "similarity_features_used": [
            "venue",
            "spread_bucket",
            "liquidity_bucket",
            "latency_bucket",
            "model_risk_tier",
            "source_provenance_tier",
            "quantum_formulation_class",
            "formula_family",
        ],
        "similarity_action_downgrade": "WATCH_ONLY_UNTIL_MORE_EVIDENCE" if positive else "DEMOTE_WITHIN_MATCHING_CONDITION",
        "nearest_neighbor_memory_confidence_cap": 0.55 if positive else 0.48,
        "validation_status": "PASS",
    }
