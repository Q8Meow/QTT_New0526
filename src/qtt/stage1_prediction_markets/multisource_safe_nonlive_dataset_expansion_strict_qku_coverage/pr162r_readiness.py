"""PR162C PR162R readiness bridge."""

from __future__ import annotations

from typing import Any

from . import constants as c


def pr162r_readiness_records(proofs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "readiness_id": f"PR162C-PR162R-READINESS-{proof['qku_id']}",
            "qku_id": proof["qku_id"],
            "data_requirement_id": proof["data_requirement_id"],
            "pr162r_ready_flag": proof["pr162r_ready_flag"],
            "replay_lane_eligible_flag": proof["replay_lane_eligible_flag"],
            "paper_lane_eligible_flag": proof["paper_lane_eligible_flag"],
            "strict_coverage_status": proof["strict_coverage_status"],
            "blocker_code": proof["blocker_code"],
            "next_action": proof["next_action"],
            "created_by_pr": c.PR_ID,
        }
        for proof in proofs
    ]
