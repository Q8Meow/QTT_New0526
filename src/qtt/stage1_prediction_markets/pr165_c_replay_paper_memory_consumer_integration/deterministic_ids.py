"""Deterministic identifiers for PR165-C rows."""

from __future__ import annotations

import re


def ordinal_ref(prefix: str, index: int, width: int = 6) -> str:
    return f"{prefix}::{index:0{width}d}"


def candidate_slug(candidate_packet_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", candidate_packet_id).strip("_")
    return slug.upper()


def candidate_ref(prefix: str, candidate_packet_id: str) -> str:
    return f"{prefix}::{candidate_slug(candidate_packet_id)}"
