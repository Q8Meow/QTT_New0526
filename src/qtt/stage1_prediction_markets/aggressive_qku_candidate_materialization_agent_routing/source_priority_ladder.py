"""Source priority ladder used as priority, not an acquisition gate."""

from __future__ import annotations


def source_priority_records() -> list[dict[str, object]]:
    return [
        {
            "source_tier": "TIER_0",
            "priority_rank": 0,
            "description": "Existing repo-local and owner-provided QTT artifacts.",
            "acquisition_gate_flag": False,
        },
        {
            "source_tier": "TIER_1",
            "priority_rank": 1,
            "description": "Official venue, provider, API, public CSV, and quantum provider docs.",
            "acquisition_gate_flag": False,
        },
        {
            "source_tier": "TIER_2",
            "priority_rank": 2,
            "description": "Reputable technical docs, libraries, textbooks, and institutional references.",
            "acquisition_gate_flag": False,
        },
        {
            "source_tier": "TIER_3",
            "priority_rank": 3,
            "description": "Public prediction-market research, datasets, and GitHub references.",
            "acquisition_gate_flag": False,
        },
        {
            "source_tier": "TIER_4",
            "priority_rank": 4,
            "description": "Social, web, forum, news, and strategy signals.",
            "acquisition_gate_flag": False,
        },
        {
            "source_tier": "TIER_5",
            "priority_rank": 5,
            "description": "Weak or noisy mappable sources routed only as low-confidence candidates.",
            "acquisition_gate_flag": False,
        },
    ]
