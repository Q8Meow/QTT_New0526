"""Typed data containers for PR155 build steps."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class InputDiscoveryResult:
    input_path: Path | None
    payload: Mapping[str, Any]
    candidate_paths: tuple[Path, ...]
    failures: tuple[str, ...]


@dataclass(frozen=True)
class OrchestrationPreflightResult:
    preflight: Mapping[str, Any]
    payloads: Mapping[str, Mapping[str, Any]]
    failures: tuple[str, ...]


@dataclass(frozen=True)
class BuildOutputs:
    registry: Mapping[str, Any]
    report: Mapping[str, Any]
    input_pr154_artifact: str | None
    failures: tuple[str, ...]
