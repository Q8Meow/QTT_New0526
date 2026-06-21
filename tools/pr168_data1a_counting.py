#!/usr/bin/env python3
"""Count-lineage helpers for PR168-DATA1A."""

from __future__ import annotations

from typing import Any


def count_state_counts(count_rows: list[dict[str, Any]]) -> dict[str, int]:
    states: dict[str, int] = {}
    for row in count_rows:
        state = str(row.get("count_authority_state"))
        states[state] = states.get(state, 0) + 1
    return dict(sorted(states.items()))


def count_confidence_counts(count_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in count_rows:
        confidence = str(row.get("confidence_level"))
        counts[confidence] = counts.get(confidence, 0) + 1
    return dict(sorted(counts.items()))
