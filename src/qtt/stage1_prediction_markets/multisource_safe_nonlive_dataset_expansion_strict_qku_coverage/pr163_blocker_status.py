"""PR162C PR163 blocker status."""

from __future__ import annotations

from typing import Any

from . import constants as c


def pr163_blocker_records(strict_ready_count: int) -> list[dict[str, Any]]:
    return [
        {
            "blocker_status_id": "PR162C-PR163-BLOCKER-STATUS-001",
            "strict_pr162r_ready_qku_count": strict_ready_count,
            "pr163_ready_flag": False,
            "pr163_readiness_state": "BLOCKED_UNTIL_PR162R_VALIDATED_REAL_NONLIVE_REPLAY_PAPER_ARTIFACTS_EXIST",
            "blocker_codes": [
                "PR163_BLOCKED_NO_VALIDATED_REAL_NONLIVE_REPLAY_ARTIFACTS",
                "PR163_BLOCKED_NO_VALIDATED_REAL_NONLIVE_PAPER_ARTIFACTS",
            ],
            "created_by_pr": c.PR_ID,
        }
    ]
