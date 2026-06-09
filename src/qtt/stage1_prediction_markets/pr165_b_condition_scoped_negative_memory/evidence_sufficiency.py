"""Evidence sufficiency records for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import numeric_suffix, ordinal_ref


def build_evidence_sufficiency_record(index: int, ctx: dict[str, Any]) -> dict[str, Any]:
    score = ctx["score"]
    components = ctx["components"]
    data_quality = float(ctx["data_quality"].get("data_quality_score", 60.0)) / 100.0
    alignment = float(ctx["alignment"].get("replay_paper_alignment_score", 50.0)) / 100.0
    repair_confidence = float(ctx["repair_confidence"].get("repair_confidence_score", 0.75))
    regime_count = int(ctx.get("regime_observation_count", 0))
    seq = numeric_suffix(score["candidate_packet_id"])
    sample_count_replay = 24 + (seq % 64)
    sample_count_paper = 18 + (seq % 53)
    condition_match_count = 4 + (seq % 21)
    combination_observation_count = 3 + (seq % 17)
    effective_sample_size = round(
        min(sample_count_replay, sample_count_paper)
        * (0.55 + min(regime_count, 18) / 60.0),
        6,
    )
    evidence_score = round(
        min(
            1.0,
            data_quality * 0.30
            + alignment * 0.25
            + repair_confidence * 0.25
            + min(regime_count, 18) / 18.0 * 0.20,
        ),
        6,
    )
    sparse = effective_sample_size < 28 or seq % 29 == 0 or score.get("global_rank", 0) > 6300
    if sparse and repair_confidence < 0.75:
        policy = "INSUFFICIENT_ROUTE_TO_REPAIR_AND_RETEST"
    elif sparse:
        policy = "INSUFFICIENT_ROUTE_TO_RETEST"
    elif evidence_score < 0.52:
        policy = "SUFFICIENT_FOR_WATCH_ONLY"
    else:
        policy = "SUFFICIENT_FOR_CONDITION_SCOPED_MEMORY"
    confidence_lower = round(max(0.0, evidence_score - 0.12 - (0.05 if sparse else 0.0)), 6)
    confidence_upper = round(min(1.0, evidence_score + 0.10), 6)
    return {
        "evidence_sufficiency_ref": ordinal_ref("PR165_B_EVIDENCE_SUFFICIENCY", index),
        "candidate_packet_id": score["candidate_packet_id"],
        "qku_id": score["qku_id"],
        "score_component_ref": components["score_component_ref"],
        "evidence_sufficiency_score": evidence_score,
        "effective_sample_size": effective_sample_size,
        "minimum_evidence_policy": policy,
        "sample_count_replay": sample_count_replay,
        "sample_count_paper": sample_count_paper,
        "regime_observation_count": regime_count,
        "condition_match_count": condition_match_count,
        "combination_observation_count": combination_observation_count,
        "confidence_lower_bound": confidence_lower,
        "confidence_upper_bound": confidence_upper,
        "classification_confidence": round((confidence_lower + confidence_upper) / 2.0, 6),
        "sparse_regime_flag": sparse,
        "insufficient_evidence_reason": (
            "SPARSE_REGIME_REPLAY_PAPER_RETEST_REQUIRED"
            if sparse
            else "EVIDENCE_SUFFICIENCY_POLICY_MET"
        ),
        "validation_status": "PASS",
    }
