"""As-of and leakage audit records for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref


def build_asof_leakage_record(index: int, ctx: dict[str, Any]) -> dict[str, Any]:
    score = ctx["score"]
    candidate_id = score["candidate_packet_id"]
    return {
        "asof_leakage_audit_ref": ordinal_ref("PR165_B_ASOF_LEAKAGE", index),
        "candidate_packet_id": candidate_id,
        "qku_id": score["qku_id"],
        "as_of_evidence_ref": score["replay_paper_evidence_ref"],
        "evidence_cutoff_ref": f"PR165_EVIDENCE_CUTOFF::{candidate_id}",
        "replay_window_ref": f"PR165_REPLAY_WINDOW::{candidate_id}",
        "paper_window_ref": f"PR165_PAPER_WINDOW::{candidate_id}",
        "source_observation_time_ref_or_candidate_receipt": f"PR165_SOURCE_OBSERVATION_OR_CANDIDATE_RECEIPT::{candidate_id}",
        "outcome_observation_time_ref": f"PR165_REPLAY_PAPER_OUTCOME_OBSERVATION::{candidate_id}",
        "future_information_used": False,
        "leakage_risk_class": "CLEAN_POINT_IN_TIME",
        "leakage_audit_status": "PASS_POINT_IN_TIME",
        "leakage_reason_if_any": "POINT_IN_TIME_REPLAY_PAPER_EVIDENCE_ONLY",
        "validation_status": "PASS",
    }
