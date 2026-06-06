"""Paired alignment receipts."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_alignment(index: int, replay_trace: dict[str, Any], paper_trace: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "alignment_ref": plain_ref("ALIGNMENT", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "replay_trace_ref": replay_trace["replay_trace_ref"],
        "paper_trace_ref": paper_trace["paper_trace_ref"],
        "clock_ref": ctx["clock"]["clock_ref"],
        "input_lock_ref": ctx["input_lock"]["input_lock_ref"],
        "leakage_guard_ref": ctx["leakage_guard"]["leakage_guard_ref"],
        "replay_available": True,
        "paper_available": True,
        "paired_available": True,
        "alignment_status": "ALIGNED_WITH_SYNTHETIC_FIXTURE",
        "exact_alignment_reason": "Shared candidate, QKU, fixture clock, and PR162R-B/PR163 refs are locked for paired non-live execution.",
        "no_result_promotion": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
