"""Future paper result packet validator."""

from __future__ import annotations

from typing import Any

from .replay_result_packet_validator import _validate_packet


def validate_paper_packet(packet: dict[str, Any], known_qku_ids: set[str]) -> list[str]:
    return _validate_packet(packet, known_qku_ids, "PAPER")
