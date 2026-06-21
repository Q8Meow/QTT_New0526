#!/usr/bin/env python3
"""Real-market replay readiness handoff helpers for PR168-GFP2."""

from __future__ import annotations

from typing import Any


def replay_recompute_handoff_rows(universe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "canonical_row_key": row["canonical_row_key"],
            "qku_id": row["qku_id"],
            "handoff_route": "PR168-RP2",
            "required_actions": row["gap_reason_codes"],
            "requires_accepted_real_market_data_flag": True,
            "requires_formula_execution_flag": True,
            "real_positive_claim_allowed_flag": False,
            "real_negative_claim_allowed_flag": False,
            "downstream_pr_refs": ["PR168-RP2"],
            "agent_owner": "Replay Paper Recompute Agent",
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        }
        for row in universe_rows
    ]
