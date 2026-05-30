"""Small PR161C data containers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BuildArtifacts:
    payloads: dict[str, Any]
    summary: dict[str, Any]


@dataclass(frozen=True)
class ValidationResult:
    failures: tuple[str, ...] = ()
    receipts: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.failures
