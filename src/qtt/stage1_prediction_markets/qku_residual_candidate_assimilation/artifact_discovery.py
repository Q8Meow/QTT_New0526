"""Deterministic artifact discovery for PR161C inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c


def posix(path: Path) -> str:
    return path.as_posix()


def selected_artifact_paths(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root)
    generated = root / c.GENERATED_DIR
    pr161a_reports = {
        key: posix(path)
        for key, path in sorted(c.PR161A_REPORT_PATHS.items())
        if (root / path).exists()
    }
    pr161b_reports = {
        key: posix(path)
        for key, path in sorted(c.PR161B_REPORT_PATHS.items())
        if (root / path).exists()
    }
    control_plane = {
        key: posix(path)
        for key, path in sorted(c.CONTROL_PLANE_PATHS.items())
        if (root / path).exists()
    }
    pr161a_all = sorted(
        posix(path.relative_to(root))
        for path in generated.glob("PR161A_*.json")
        if path.is_file()
    )
    pr82_pr96 = sorted(
        posix(c.GENERATED_DIR / name)
        for name in c.PR82_PR96_ARTIFACT_NAMES
        if (root / c.GENERATED_DIR / name).exists()
    )
    prior_pr = sorted(
        posix(path.relative_to(root))
        for pattern in ("PR154_*.json", "PR157_*.json", "PR158_*.json", "PR159*.json", "PR160_*.json")
        for path in generated.glob(pattern)
        if path.is_file()
    )
    atomicrows_compatible = sorted(
        posix(path.relative_to(root))
        for pattern in ("PR137R_*.json", "PR138_*.json", "AtomicRows*.json", "AtomicRows*.report.json")
        for path in generated.glob(pattern)
        if path.is_file()
    )
    return {
        "pr161a_reports": pr161a_reports,
        "pr161a_all_reports": pr161a_all,
        "pr161b_reports": pr161b_reports,
        "control_plane_artifacts": control_plane,
        "pr82_pr96_artifacts": pr82_pr96,
        "prior_pr_artifacts": prior_pr,
        "atomicrows_compatible_artifacts": atomicrows_compatible,
        "pr136_crosswalk_requested_exists": (
            root / c.CONTROL_PLANE_PATHS["pr136_section_crosswalk_requested"]
        ).exists(),
        "pr136_crosswalk_fallback_used": (
            not (root / c.CONTROL_PLANE_PATHS["pr136_section_crosswalk_requested"]).exists()
            and (root / c.CONTROL_PLANE_PATHS["pr136_section_crosswalk_fallback"]).exists()
        ),
    }
