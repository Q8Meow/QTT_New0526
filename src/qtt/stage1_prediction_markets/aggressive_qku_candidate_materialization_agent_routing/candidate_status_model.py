"""Candidate progress and route status helpers."""

from __future__ import annotations

from . import constants as c


def progress_status_for_index(index: int) -> str:
    statuses = c.CANDIDATE_PROGRESS_STATUSES
    return statuses[index % len(statuses)]


def route_status_for_progress(progress_status: str) -> str:
    if "QUANTUM" in progress_status:
        return "AGENT_ROUTED_QUANTUM_CANDIDATE"
    if "NEEDS_NORMALIZATION" in progress_status:
        return "AGENT_ROUTED_NEEDS_NORMALIZATION"
    if "OPEN" in progress_status:
        return "AGENT_ROUTED_NEEDS_FIELD_FILL"
    if "REPLAY_PAPER" in progress_status:
        return "AGENT_ROUTED_REPLAY_PAPER_CANDIDATE"
    if "PARTIAL" in progress_status:
        return "AGENT_ROUTED_PARTIAL"
    return "AGENT_ROUTED_CANDIDATE"


def is_disallowed_route_status(status: str) -> bool:
    return status in c.DISALLOWED_ROUTE_STATUSES
