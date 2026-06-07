"""Stable PR164 identifier helpers."""

from __future__ import annotations

from typing import Iterable


def plain_ref(prefix: str, index: int, *, width: int = 6) -> str:
    return f"PR164_{prefix}::{index:0{width}d}"


def candidate_index(candidate_packet_id: str) -> int:
    return int(str(candidate_packet_id).split("::")[-1])


def stable_join(parts: Iterable[object]) -> str:
    return "::".join(str(part).strip().replace(" ", "_") for part in parts if str(part).strip())
