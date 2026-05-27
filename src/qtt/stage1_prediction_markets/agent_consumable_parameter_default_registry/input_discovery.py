"""Deterministic PR154 input discovery for PR155."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .io import read_json_object
from .models import InputDiscoveryResult


def _is_pr154_materialization_payload(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get("report_id") == c.PR154_INPUT_REPORT_ID
        and payload.get("semantic_pr_label") == "PR154"
        and isinstance(payload.get("per_target_materialization_records"), list)
    )


def _narrow_metadata_candidates(root: Path) -> tuple[Path, ...]:
    generated = root / "docs" / "master_plan" / "generated"
    if not generated.exists():
        return ()
    candidates: list[Path] = []
    for path in sorted(generated.glob("PR154*MaterializationGate.report.json")):
        if not path.is_file():
            continue
        try:
            payload = read_json_object(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if _is_pr154_materialization_payload(payload):
            candidates.append(path.relative_to(root))
    return tuple(candidates)


def _read_candidate(root: Path, rel_path: Path) -> tuple[dict[str, Any], tuple[str, ...]]:
    path = root / rel_path
    if not path.exists():
        return {}, (c.PR155_PR154_INPUT_MISSING,)
    try:
        payload = read_json_object(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}, (c.PR155_PR154_INPUT_INVALID,)
    if not _is_pr154_materialization_payload(payload):
        return {}, (c.PR155_PR154_INPUT_INVALID,)
    return payload, ()


def discover_pr154_input(repo_root: Path | str) -> InputDiscoveryResult:
    root = Path(repo_root).resolve()
    primary = c.PR154_INPUT_REPORT_PATH
    candidates: tuple[Path, ...] = ()
    if (root / primary).exists():
        metadata_candidates = _narrow_metadata_candidates(root)
        candidates = tuple(sorted(set((primary, *metadata_candidates)), key=lambda p: p.as_posix()))
        if len(candidates) > 1:
            return InputDiscoveryResult(
                input_path=None,
                payload={},
                candidate_paths=candidates,
                failures=(c.PR155_PR154_INPUT_AMBIGUOUS,),
            )
        payload, failures = _read_candidate(root, primary)
        return InputDiscoveryResult(
            input_path=primary if not failures else None,
            payload=payload,
            candidate_paths=(primary,),
            failures=failures,
        )

    candidates = _narrow_metadata_candidates(root)
    if len(candidates) > 1:
        return InputDiscoveryResult(
            input_path=None,
            payload={},
            candidate_paths=candidates,
            failures=(c.PR155_PR154_INPUT_AMBIGUOUS,),
        )
    if not candidates:
        return InputDiscoveryResult(
            input_path=None,
            payload={},
            candidate_paths=(),
            failures=(c.PR155_PR154_INPUT_MISSING,),
        )
    payload, failures = _read_candidate(root, candidates[0])
    return InputDiscoveryResult(
        input_path=candidates[0] if not failures else None,
        payload=payload,
        candidate_paths=candidates,
        failures=failures,
    )
