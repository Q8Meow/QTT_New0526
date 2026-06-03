"""Facade for master-plan formula to external acquisition gap matrix."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .master_plan_formula_algorithm_mining import mine_master_plan


def master_plan_formula_gap_targets(repo_root: Path, qku_pool: list[str]) -> list[dict[str, Any]]:
    return mine_master_plan(repo_root, qku_pool).gap_targets
