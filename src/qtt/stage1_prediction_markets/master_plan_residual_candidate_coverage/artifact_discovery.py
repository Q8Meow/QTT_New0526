"""Deterministic PR161B artifact discovery."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c


def selected_artifact_paths(root: Path | str) -> dict[str, Any]:
    repo_root = Path(root).resolve()
    generated = repo_root / c.GENERATED_DIR
    crosswalk = repo_root / (c.GENERATED_DIR / "PR136MasterPlanSectionCrosswalk.report.json")
    fallback_used = not crosswalk.exists()
    selected_crosswalk = c.CROSSWALK_FALLBACK_PATH if fallback_used else crosswalk.relative_to(repo_root)
    return {
        "mandatory_orchestration_inputs": _presence_map(repo_root, c.MANDATORY_ORCHESTRATION_INPUTS),
        "fallback_crosswalk_path_used": selected_crosswalk.as_posix() if fallback_used else None,
        "selected_crosswalk_path": selected_crosswalk.as_posix(),
        "pr136_orchestration_artifacts": _existing(
            repo_root,
            (
                c.GENERATED_DIR / "PR136RouteTriage.report.json",
                selected_crosswalk,
                c.GENERATED_DIR / "PR136MarketSpecificLaunchReadinessIndex.report.json",
                c.GENERATED_DIR / "PR136CommandActionMatrix.report.json",
            ),
        ),
        "pr154_artifact_map": _glob_map(generated, ("PR154_*.json",)),
        "pr157_pr158_pr159_pr159r_pr159s_pr160_artifact_map": _prefix_map(
            generated,
            c.PR157_PR160_ARTIFACT_PREFIXES,
        ),
        "pr161a_report_map": _glob_map(generated, ("PR161A_*.json",)),
        "pr73_pr75_stack_artifact_map": _name_map(repo_root, c.PR73_PR75_STACK_ARTIFACT_NAMES),
        "pr82_pr86_quantum_scoring_optimizer_artifact_map": _name_map(
            repo_root,
            c.PR82_PR86_QUANTUM_ARTIFACT_NAMES,
        ),
        "pr87_pr96_downstream_artifact_map": _name_map(
            repo_root,
            c.PR87_PR96_DOWNSTREAM_ARTIFACT_NAMES,
        ),
        "pr152_deterministic_audit_status": (
            "PRESENT" if (repo_root / c.PR152_AUDIT_REPORT_PATH).exists() else "MISSING"
        ),
        "source_evidence_packet_path": (
            c.SOURCE_EVIDENCE_PACKET_PATH.as_posix()
            if (repo_root / c.SOURCE_EVIDENCE_PACKET_PATH).exists()
            else None
        ),
    }


def prior_candidate_artifact_paths(root: Path | str) -> list[Path]:
    repo_root = Path(root).resolve()
    selected = selected_artifact_paths(repo_root)
    paths: set[str] = set()
    for key in (
        "pr136_orchestration_artifacts",
        "pr154_artifact_map",
        "pr157_pr158_pr159_pr159r_pr159s_pr160_artifact_map",
        "pr73_pr75_stack_artifact_map",
        "pr82_pr86_quantum_scoring_optimizer_artifact_map",
        "pr87_pr96_downstream_artifact_map",
        "pr161a_report_map",
    ):
        value = selected[key]
        if isinstance(value, dict):
            for item in value.values():
                if isinstance(item, list):
                    paths.update(str(part) for part in item)
                elif item:
                    paths.add(str(item))
        elif isinstance(value, list):
            paths.update(str(item) for item in value)
    return sorted((repo_root / path for path in paths if (repo_root / path).exists()), key=lambda path: path.as_posix())


def _existing(repo_root: Path, paths: tuple[Path, ...]) -> list[str]:
    return [path.as_posix() for path in paths if (repo_root / path).exists()]


def _presence_map(repo_root: Path, paths: tuple[Path, ...]) -> dict[str, bool]:
    return {path.as_posix(): (repo_root / path).exists() for path in paths}


def _glob_map(generated: Path, patterns: tuple[str, ...]) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for pattern in patterns:
        output[pattern] = [
            path.relative_to(generated.parents[2]).as_posix()
            for path in sorted(generated.glob(pattern), key=lambda value: value.as_posix())
        ]
    return output


def _prefix_map(generated: Path, prefixes: tuple[str, ...]) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for prefix in prefixes:
        output[prefix] = [
            path.relative_to(generated.parents[2]).as_posix()
            for path in sorted(generated.glob(f"{prefix}*.json"), key=lambda value: value.as_posix())
        ]
    return output


def _name_map(repo_root: Path, names: tuple[str, ...]) -> dict[str, str | None]:
    output: dict[str, str | None] = {}
    for name in names:
        path = c.GENERATED_DIR / name
        output[name] = path.as_posix() if (repo_root / path).exists() else None
    return output
