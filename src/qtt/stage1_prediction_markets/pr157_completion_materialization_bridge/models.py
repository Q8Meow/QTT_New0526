"""Lightweight PR157 build models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BuildArtifacts:
    pr154_registry: dict[str, Any]
    pr154_report: dict[str, Any]
    atomicrows_registry: dict[str, Any]
    atomicrows_report: dict[str, Any]
    owner_request_packet: dict[str, Any]
    atomicrows_shards: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class ValidationResult:
    failures: tuple[str, ...]
    receipts: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.failures
