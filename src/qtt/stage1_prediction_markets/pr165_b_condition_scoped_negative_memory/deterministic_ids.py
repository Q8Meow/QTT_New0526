"""Deterministic PR165-B identifiers without hash/checksum authority."""

from __future__ import annotations

import re


_NON_ID = re.compile(r"[^A-Za-z0-9]+")


def numeric_suffix(value: object) -> int:
    text = str(value)
    matches = re.findall(r"\d+", text)
    if not matches:
        return 0
    return int(matches[-1])


def ordinal_ref(prefix: str, index: int) -> str:
    return f"{prefix}::{index:06d}"


def stable_token(value: object, *, max_len: int = 96) -> str:
    text = _NON_ID.sub("_", str(value).upper()).strip("_")
    return (text or "VALUE")[:max_len]


def candidate_version(candidate_packet_id: str) -> str:
    return f"{candidate_packet_id}::VERSION::PR165_B_MEMORY"
