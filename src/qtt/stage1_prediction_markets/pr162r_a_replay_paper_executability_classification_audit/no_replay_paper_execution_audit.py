"""Replay/paper execution prohibition audit."""

from __future__ import annotations

from typing import Any


def no_replay_paper_execution_records() -> list[dict[str, Any]]:
    return [
        {
            "audit_id": "PR162R_A_NO_REPLAY_PAPER_EXECUTION",
            "replay_execution_count": 0,
            "paper_execution_count": 0,
            "adapter_invocation_count": 0,
            "result_packet_created_count": 0,
            "validation_status": "PASS",
            "live_order_authority": False,
        }
    ]
