"""Deterministic candidate-name normalization."""

from __future__ import annotations

import re


def normalize_candidate_name(value: str) -> str:
    lowered = value.lower()
    lowered = lowered.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    normalized = re.sub(r"_+", "_", normalized)
    return normalized[:160] or "unnamed_candidate"


def compact_text(value: str, *, limit: int = 360) -> str:
    text = " ".join(value.strip().split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."
