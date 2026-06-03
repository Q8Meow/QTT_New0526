"""Deterministic IDs and source locator integrity digests."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def deterministic_digest(value: Any, *, size: int = 16) -> str:
    digest = hashlib.blake2b(canonical_text(value).encode("utf-8"), digest_size=size)
    return f"digest-v1:{digest.hexdigest()}"


def deterministic_id(prefix: str, *parts: Any, size: int = 10) -> str:
    digest = hashlib.blake2b(canonical_text(parts).encode("utf-8"), digest_size=size)
    return f"{prefix}-{digest.hexdigest().upper()}"
