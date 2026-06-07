"""Stable ID helpers for PR163-C."""

from __future__ import annotations

import re


def plain_ref(prefix: str, index: int, width: int = 6) -> str:
    return f"{prefix}::{index:0{width}d}"


def stable_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper()
    return slug or "UNSPECIFIED"
