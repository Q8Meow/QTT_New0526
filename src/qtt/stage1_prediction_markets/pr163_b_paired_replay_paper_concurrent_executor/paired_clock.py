"""Paired replay/paper clock construction."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .authority_policy import no_authority_fields, plain_ref


BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def iso_at(seconds: int) -> str:
    return (BASE_TIME + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def build_clock(index: int, candidate_packet_id: str, settlement_available: bool) -> dict[str, Any]:
    decision_second = index
    return {
        "clock_ref": plain_ref("CLOCK", index),
        "candidate_packet_id": candidate_packet_id,
        "replay_observation_time": iso_at(decision_second),
        "paper_synthetic_time": iso_at(decision_second),
        "source_as_of_time": iso_at(max(decision_second - 120, 0)),
        "feature_as_of_time": iso_at(max(decision_second - 30, 0)),
        "event_lifecycle_time": iso_at(decision_second),
        "capture_time": iso_at(decision_second + 1),
        "settlement_time_if_available": iso_at(decision_second + 86400) if settlement_available else "",
        "timezone_policy": "UTC_FIXED_SYNTHETIC_AND_REPLAY_FIXTURE_TIMES",
        "monotonic_sequence_policy": "CANDIDATE_PACKET_SEQUENCE_SECONDS",
        "alignment_status": "ALIGNED_WITH_SYNTHETIC_FIXTURE",
        "no_live_time_dependency": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
