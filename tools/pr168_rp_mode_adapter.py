#!/usr/bin/env python3
"""Mode adapter constants for PR168-RP."""

from __future__ import annotations


MODES = ("REPLAY", "PAPER", "SHADOW_CANDIDATE", "LIVE_CANDIDATE")


def mode_authority(mode: str) -> dict[str, object]:
    normalized = str(mode).upper()
    if normalized not in MODES:
        raise ValueError(f"unknown pretrade mode: {mode}")
    return {
        "mode": normalized,
        "live_authority": False,
        "order_authority": False,
        "execution_router_required_future_gate": normalized == "LIVE_CANDIDATE",
        "connector_semantic_binding_state": "NOT_BOUND_CANDIDATE_ONLY",
    }
