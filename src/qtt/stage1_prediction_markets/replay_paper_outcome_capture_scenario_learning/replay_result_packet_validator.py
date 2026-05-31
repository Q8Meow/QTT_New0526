"""Future replay result packet validator."""

from __future__ import annotations

from typing import Any

from . import constants as c


def validate_replay_packet(packet: dict[str, Any], known_qku_ids: set[str]) -> list[str]:
    return _validate_packet(packet, known_qku_ids, "REPLAY")


def _validate_packet(packet: dict[str, Any], known_qku_ids: set[str], mode: str) -> list[str]:
    failures: list[str] = []
    for field in c.RESULT_PACKET_REQUIRED_FIELDS:
        if field not in packet:
            failures.append(f"missing field {field}")
    if packet.get("result_mode") != mode:
        failures.append(f"result_mode must be {mode}")
    qku_ids = packet.get("qku_ids")
    if not isinstance(qku_ids, list) or not all(str(qku) in known_qku_ids for qku in qku_ids):
        failures.append("qku_ids must map to PR161C primary QKUs")
    for field in c.RESULT_NUMERIC_FIELDS:
        value = packet.get(field)
        if value is not None and not isinstance(value, (int, float)):
            failures.append(f"{field} must be numeric or null")
    if packet.get("future_live_gate_required_flag") is not True:
        failures.append("future live gate must remain required")
    if packet.get("no_live_authority_created_flag") is not True:
        failures.append("packet must not create live authority")
    return failures
