"""Input discovery for PR156 required and optional artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping

from . import constants as c
from .io import read_json_object
from .models import ArtifactDiscoveryResult, OptionalArtifactSet


PayloadPredicate = Callable[[Mapping[str, Any]], bool]


def _is_pr155_registry_payload(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get("registry_type") == c.PR155_REGISTRY_TYPE
        and payload.get("pr_id") == "PR155"
        and isinstance(payload.get("records"), list)
    )


def _is_pr155_report_payload(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get("report_type") == c.PR155_REPORT_TYPE
        and payload.get("pr_id") == "PR155"
        and payload.get("semantic_task_id")
        == "PR155_AGENT_CONSUMABLE_PARAMETER_DEFAULT_REGISTRY"
    )


def _is_pr154_materialization_payload(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get("report_id") == c.PR154_REPORT_ID
        and payload.get("semantic_pr_label") == "PR154"
        and isinstance(payload.get("per_target_materialization_records"), list)
    )


def _narrow_metadata_candidates(
    root: Path,
    glob_pattern: str,
    predicate: PayloadPredicate,
) -> tuple[Path, ...]:
    generated = root / "docs" / "master_plan" / "generated"
    if not generated.exists():
        return ()
    candidates: list[Path] = []
    for path in sorted(generated.glob(glob_pattern)):
        if not path.is_file():
            continue
        try:
            payload = read_json_object(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if predicate(payload):
            candidates.append(path.relative_to(root))
    return tuple(candidates)


def _read_candidate(
    root: Path,
    rel_path: Path,
    predicate: PayloadPredicate,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    path = root / rel_path
    if not path.exists():
        return {}, (c.PR156_REQUIRED_INPUT_MISSING,)
    try:
        payload = read_json_object(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}, (c.PR156_REQUIRED_INPUT_INVALID,)
    if not predicate(payload):
        return {}, (c.PR156_REQUIRED_INPUT_INVALID,)
    return payload, ()


def _discover_required_artifact(
    repo_root: Path | str,
    *,
    primary: Path,
    glob_pattern: str,
    predicate: PayloadPredicate,
) -> ArtifactDiscoveryResult:
    root = Path(repo_root).resolve()
    if (root / primary).exists():
        metadata_candidates = _narrow_metadata_candidates(root, glob_pattern, predicate)
        candidates = tuple(sorted(set((primary, *metadata_candidates)), key=lambda p: p.as_posix()))
        if len(candidates) > 1:
            return ArtifactDiscoveryResult(
                input_path=None,
                payload={},
                candidate_paths=candidates,
                failures=(c.PR156_REQUIRED_INPUT_AMBIGUOUS,),
            )
        payload, failures = _read_candidate(root, primary, predicate)
        return ArtifactDiscoveryResult(
            input_path=primary if not failures else None,
            payload=payload,
            candidate_paths=(primary,),
            failures=failures,
        )

    candidates = _narrow_metadata_candidates(root, glob_pattern, predicate)
    if len(candidates) > 1:
        return ArtifactDiscoveryResult(
            input_path=None,
            payload={},
            candidate_paths=candidates,
            failures=(c.PR156_REQUIRED_INPUT_AMBIGUOUS,),
        )
    if not candidates:
        return ArtifactDiscoveryResult(
            input_path=None,
            payload={},
            candidate_paths=(),
            failures=(c.PR156_REQUIRED_INPUT_MISSING,),
        )
    payload, failures = _read_candidate(root, candidates[0], predicate)
    return ArtifactDiscoveryResult(
        input_path=candidates[0] if not failures else None,
        payload=payload,
        candidate_paths=candidates,
        failures=failures,
    )


def discover_pr155_registry(repo_root: Path | str) -> ArtifactDiscoveryResult:
    return _discover_required_artifact(
        repo_root,
        primary=c.PR155_REGISTRY_PATH,
        glob_pattern="PR155*AgentConsumableParameterDefaultRegistry*.registry.json",
        predicate=_is_pr155_registry_payload,
    )


def discover_pr155_report(repo_root: Path | str) -> ArtifactDiscoveryResult:
    return _discover_required_artifact(
        repo_root,
        primary=c.PR155_REPORT_PATH,
        glob_pattern="PR155*AgentConsumableParameterDefaultRegistry*.report.json",
        predicate=_is_pr155_report_payload,
    )


def discover_pr154_report(repo_root: Path | str) -> ArtifactDiscoveryResult:
    return _discover_required_artifact(
        repo_root,
        primary=c.PR154_REPORT_PATH,
        glob_pattern="PR154*MaterializationGate.report.json",
        predicate=_is_pr154_materialization_payload,
    )


def artifact_summary(
    *,
    key: str,
    rel_path: Path,
    payload: Mapping[str, Any] | None,
    required: bool,
    consumed: bool,
) -> dict[str, Any]:
    payload = payload or {}
    return {
        "artifact_key": key,
        "artifact_path": rel_path.as_posix(),
        "required": required,
        "present": consumed,
        "consumed": consumed,
        "registry_type": payload.get("registry_type"),
        "report_type": payload.get("report_type"),
        "report_id": payload.get("report_id"),
        "receipt_type": payload.get("receipt_type"),
        "semantic_task_id": payload.get("semantic_task_id"),
        "pr_id": payload.get("pr_id"),
    }


def load_optional_artifacts(repo_root: Path | str) -> OptionalArtifactSet:
    root = Path(repo_root).resolve()
    artifacts: dict[str, Mapping[str, Any]] = {}
    consumed: list[Mapping[str, Any]] = []
    missing: list[Mapping[str, Any]] = []
    failures: list[str] = []

    for key, rel_path in sorted(
        c.OPTIONAL_INPUT_ARTIFACT_PATHS.items(),
        key=lambda item: item[0],
    ):
        path = root / rel_path
        if not path.exists():
            missing.append(
                artifact_summary(
                    key=key,
                    rel_path=rel_path,
                    payload=None,
                    required=False,
                    consumed=False,
                )
            )
            continue
        try:
            payload = read_json_object(path)
        except (OSError, ValueError, json.JSONDecodeError):
            failures.append(f"{c.PR156_OPTIONAL_INPUT_INVALID}: {rel_path.as_posix()}")
            missing.append(
                artifact_summary(
                    key=key,
                    rel_path=rel_path,
                    payload=None,
                    required=False,
                    consumed=False,
                )
            )
            continue
        artifacts[key] = payload
        consumed.append(
            artifact_summary(
                key=key,
                rel_path=rel_path,
                payload=payload,
                required=False,
                consumed=True,
            )
        )

    return OptionalArtifactSet(
        artifacts=artifacts,
        consumed_artifacts=tuple(sorted(consumed, key=lambda item: str(item["artifact_path"]))),
        missing_artifacts=tuple(sorted(missing, key=lambda item: str(item["artifact_path"]))),
        failures=tuple(sorted(set(failures))),
    )
