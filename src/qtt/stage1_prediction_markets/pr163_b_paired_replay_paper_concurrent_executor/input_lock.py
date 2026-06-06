"""Replay/paper input lock receipts."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_input_lock(index: int, row: dict[str, Any], clock: dict[str, Any]) -> dict[str, Any]:
    replay_refs = list(row.get("replay_binding_refs") or [])
    paper_refs = list(row.get("paper_binding_refs") or [])
    status = "LOCKED" if replay_refs and paper_refs else "PARTIAL_LOCK_WITH_EXACT_REASON"
    return {
        "input_lock_ref": plain_ref("INPUT_LOCK", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": row["candidate_packet_id"],
        "qku_ids": list(row.get("qku_ids") or []),
        "replay_input_refs": replay_refs,
        "paper_input_refs": paper_refs,
        "shared_input_identity_fields": ["candidate_packet_id", "qku_ids", "formulation_ref", "callable_ref"],
        "shared_market_scope": "BINARY_EVENT_MARKET_SYNTHETIC_REPRESENTATIVE",
        "shared_event_scope": "PR162R_B_BOUND_EVENT_SCOPE_CANDIDATE",
        "shared_time_scope": {
            "source_as_of_time": clock["source_as_of_time"],
            "feature_as_of_time": clock["feature_as_of_time"],
            "decision_time": clock["paper_synthetic_time"],
        },
        "input_lock_status": status,
        "exact_lock_reason": "" if status == "LOCKED" else "Replay or paper binding ref absent; row remains exactly represented.",
        "no_sha_or_checksum_authority": True,
        "no_live_authority": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
