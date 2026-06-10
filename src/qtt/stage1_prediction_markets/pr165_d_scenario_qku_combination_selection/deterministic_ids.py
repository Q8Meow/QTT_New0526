"""Deterministic identifiers for PR165-D records."""

from __future__ import annotations

import hashlib


def ordinal_ref(prefix: str, index: int, width: int = 6) -> str:
    return f"{prefix}::{index:0{width}d}"


def stable_token(*parts: object, length: int = 12) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length].upper()


def stable_ref(prefix: str, *parts: object) -> str:
    return f"{prefix}::{stable_token(*parts)}"
