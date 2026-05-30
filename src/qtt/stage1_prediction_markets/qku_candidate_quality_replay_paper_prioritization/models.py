"""Small typed containers used by PR161D builders and validators."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BuildArtifacts:
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...] = ()
