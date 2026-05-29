"""Quantum agent-consumption bridge construction."""

from __future__ import annotations

from . import constants as c


def build_quantum_agent_bridge(profiles: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "bridge_record_id": f"PR161A_QUANTUM_AGENT_BRIDGE__{profile['quantum_candidate_id']}",
            "quantum_candidate_id": profile["quantum_candidate_id"],
            "downstream_agent_roles": list(c.DOWNSTREAM_AGENT_ROLES),
            "agent_consumable_state": [
                "AGENT_CONSUMABLE_QUANTUM_ADVISORY_NOW",
                "AGENT_CONSUMABLE_OPTIMIZER_PREP_NOW",
                "AGENT_CONSUMABLE_REPLAY_PAPER_NOW",
                "AGENT_CONSUMABLE_OWNER_REVIEW_QUEUE",
            ],
            "approved_consumption_lanes": [
                "research",
                "scoring_metadata",
                "optimizer_candidate_preparation",
                "quantum_advisory",
                "replay_paper_test_preparation",
                "owner_review",
            ],
            "live_use_allowed_flag": False,
            "promotion_limitations": c.NON_LIVE_PROMOTION_LIMITATION,
        }
        for profile in profiles
    ]

