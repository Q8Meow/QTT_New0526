"""Load PR162A upstream report inputs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.nonlive_replay_paper_data_adapter_quantum_forward_bridge.loaders import (
    load_pr161f_records as _load_pr161f_records,
)

from . import constants as c
from .paths import normalize_repo_relative_ref, resolve_repo_relative


def current_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def ensure_required_inputs(repo_root: Path) -> list[str]:
    missing = [
        ref
        for ref in c.REQUIRED_INPUT_REPORTS
        if not resolve_repo_relative(repo_root, ref).exists()
    ]
    if not any(resolve_repo_relative(repo_root, ref).exists() for ref in c.PR136_SECTION_CROSSWALK_ALIASES):
        missing.append("PR136MasterPlanSectionCrosswalk.report.json or PR136MasterPlanCoverageToReadinessDomainMap.report.json")
    if missing:
        raise FileNotFoundError("missing PR162A required inputs: " + ", ".join(missing))
    existing_inputs = list(c.REQUIRED_INPUT_REPORTS)
    existing_inputs.extend(
        ref for ref in c.PR136_SECTION_CROSSWALK_ALIASES if resolve_repo_relative(repo_root, ref).exists()
    )
    return [normalize_repo_relative_ref(repo_root, ref) for ref in existing_inputs]


def load_pr161f_records(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    return _load_pr161f_records(repo_root)


def index_by_qku(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["qku_id"]: record for record in records if isinstance(record.get("qku_id"), str)}
