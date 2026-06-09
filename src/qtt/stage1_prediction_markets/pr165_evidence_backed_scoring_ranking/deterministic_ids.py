"""Deterministic ID helpers for PR165."""

from __future__ import annotations

import re


_DIGITS_RE = re.compile(r"(\d+)(?!.*\d)")


def numeric_suffix(value: str) -> int:
    match = _DIGITS_RE.search(value or "")
    return int(match.group(1)) if match else 0


def ref(prefix: str, index: int, width: int = 6) -> str:
    return f"{prefix}::{index:0{width}d}"


def candidate_version(candidate_packet_id: str, suffix: str) -> str:
    return f"{candidate_packet_id}::VERSION::{suffix}"
