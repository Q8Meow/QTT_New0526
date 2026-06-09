"""Positive condition-scoped memory helpers."""

from __future__ import annotations

from .negative_memory_status_vocab import POSITIVE_CLASSIFICATIONS


def is_positive_memory(classification: str) -> bool:
    return classification in POSITIVE_CLASSIFICATIONS
