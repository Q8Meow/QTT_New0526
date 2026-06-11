"""Deterministic identifier helpers for PR166-S."""

from __future__ import annotations

import hashlib


def stable_ref(prefix: str, *parts: object, width: int = 12) -> str:
    payload = "||".join(str(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:width].upper()
    return f"{prefix}::{digest}"


def ordinal_ref(prefix: str, index: int, *, width: int = 6) -> str:
    return f"{prefix}::{index:0{width}d}"
