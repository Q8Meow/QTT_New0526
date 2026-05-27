"""Typed containers for PR156 build steps."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class ArtifactDiscoveryResult:
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
class OptionalArtifactSet:
    artifacts: Mapping[str, Mapping[str, Any]]
    consumed_artifacts: tuple[Mapping[str, Any], ...]
    missing_artifacts: tuple[Mapping[str, Any], ...]
    failures: tuple[str, ...]


@dataclass(frozen=True)
class AgentBindingContext:
    consumed_artifact_paths: tuple[str, ...]
    explicit_agent_bindings_by_ref: Mapping[str, tuple[str, ...]]
    explicit_role_bindings_by_ref: Mapping[str, tuple[str, ...]]
    explicit_consumer_class_bindings_by_ref: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class AtomicRowsUniverseState:
    confirmed_count: int | None
    count_state: str
    source_artifact_paths: tuple[str, ...]
    missing_source_state: str | None


@dataclass(frozen=True)
class BuildOutputs:
    registry: Mapping[str, Any]
    report: Mapping[str, Any]
    failures: tuple[str, ...]
