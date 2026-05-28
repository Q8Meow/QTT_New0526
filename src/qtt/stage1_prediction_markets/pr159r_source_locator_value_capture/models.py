"""Lightweight models for PR159R artifact generation and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BuildArtifacts:
    payloads: dict[str, dict[str, Any]]
    markdown_payloads: dict[str, str]


@dataclass(frozen=True)
class ValidationResult:
    failures: tuple[str, ...]
    receipts: tuple[str, ...] = ()

