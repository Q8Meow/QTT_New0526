"""Small value objects for PR138 semantic contract validation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationOutcome:
    ok: bool
    failures: tuple[str, ...]
    receipts: tuple[str, ...]

