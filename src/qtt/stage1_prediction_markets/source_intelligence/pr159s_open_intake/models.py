"""Lightweight models for PR159S artifact generation and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BuildArtifacts:
    payloads: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class ValidationResult:
    failures: tuple[str, ...]
    receipts: tuple[str, ...] = ()

