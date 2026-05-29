"""Deterministic artifact discovery for PR161A."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c


def _status(root: Path, rel_path: Path) -> dict[str, Any]:
    path = root / rel_path
    return {
        "artifact_path": rel_path.as_posix(),
        "exists": path.exists(),
        "read_mode": "READ_ONLY",
    }


def selected_artifact_paths(root: Path) -> dict[str, list[str] | str | None]:
    mandatory = []
    fallback_used: str | None = None
    for rel_path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if rel_path.name == "PR136MasterPlanSectionCrosswalk.report.json" and not (
            root / rel_path
        ).exists():
            fallback_used = c.CROSSWALK_FALLBACK_PATH.as_posix()
            mandatory.append(c.CROSSWALK_FALLBACK_PATH.as_posix())
        else:
            mandatory.append(rel_path.as_posix())
    return {
        "mandatory_orchestration_inputs": mandatory,
        "fallback_crosswalk_path_used": fallback_used,
        "pr154_artifact_map": [p.as_posix() for p in _glob(root, "PR154*")],
        "pr157_pr160_artifact_map": [
            p.as_posix()
            for prefix in ("PR157", "PR158", "PR159", "PR159R", "PR159S", "PR160")
            for p in _glob(root, f"{prefix}*")
        ],
        "pr159s_report_map": [p.as_posix() for p in c.PR159S_REPORT_PATHS if (root / p).exists()],
        "pr73_pr75_stack_artifact_map": [
            p.as_posix() for p in c.PR73_PR75_STACK_ARTIFACT_PATHS if (root / p).exists()
        ],
        "pr82_pr86_quantum_scoring_optimizer_artifact_map": [
            p.as_posix() for p in c.UPSTREAM_QUANTUM_ARTIFACT_PATHS if (root / p).exists()
        ],
    }


def input_consumption_receipts(root: Path) -> list[dict[str, Any]]:
    paths = [
        *c.MANDATORY_ORCHESTRATION_INPUTS,
        c.CROSSWALK_FALLBACK_PATH,
        c.MASTER_PLAN_PATH,
        c.SOURCE_EVIDENCE_PACKET_PATH,
        c.PR157_ATOMICROWS_REGISTRY_PATH,
        c.PR157_PR154_REGISTRY_PATH,
        c.PR154_REPORT_PATH,
        c.PR152_AUDIT_REPORT_PATH,
        c.BRANCH_CONTEXT_POLICY_PATH,
        c.RUN_VALIDATION_GATES_PATH,
        *c.PR159S_REPORT_PATHS,
        *c.PR73_PR75_STACK_ARTIFACT_PATHS,
        *c.UPSTREAM_QUANTUM_ARTIFACT_PATHS,
    ]
    seen: set[str] = set()
    receipts: list[dict[str, Any]] = []
    for rel_path in paths:
        key = rel_path.as_posix()
        if key in seen:
            continue
        seen.add(key)
        receipts.append(_status(root, rel_path))
    return receipts


def _glob(root: Path, pattern: str) -> list[Path]:
    return sorted(
        p.relative_to(root)
        for p in (root / c.GENERATED_DIR).glob(pattern)
        if p.is_file()
    )

