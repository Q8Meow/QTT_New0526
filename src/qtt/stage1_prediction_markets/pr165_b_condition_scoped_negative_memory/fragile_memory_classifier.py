"""Fragile condition-scoped memory helpers."""

from __future__ import annotations

from .negative_memory_status_vocab import FRAGILE_CLASSIFICATIONS


def is_fragile_memory(classification: str) -> bool:
    return classification in FRAGILE_CLASSIFICATIONS
