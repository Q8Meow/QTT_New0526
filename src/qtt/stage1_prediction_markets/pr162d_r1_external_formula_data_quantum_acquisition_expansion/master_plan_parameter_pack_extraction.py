"""Facade for master-plan parameter-pack extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .master_plan_formula_algorithm_mining import mine_master_plan


def extract_master_plan_parameter_packs(repo_root: Path, qku_pool: list[str]) -> list[dict[str, Any]]:
    return mine_master_plan(repo_root, qku_pool).parameter_pack_candidates
