"""PR161D scoring, ranking, bundle, scenario, and queue loader."""

from __future__ import annotations

from pathlib import Path

from . import constants as c
from .artifact_discovery import load_records, load_report


def load_pr161d_report(repo_root: Path, name: str) -> dict:
    return load_report(repo_root, c.PR161D_REPORT_PATHS[name])


def load_pr161d_records(repo_root: Path, name: str) -> list[dict]:
    return load_records(repo_root, c.PR161D_REPORT_PATHS[name])


def load_required_pr161d_record_sets(repo_root: Path) -> dict[str, list[dict]]:
    names = (
        "quality_score",
        "category_ranking",
        "result_backed_slots",
        "scenario_outcome_matrix",
        "order_condition_scenario",
        "future_profitability_pattern",
        "combination_candidate",
        "replay_paper_scenario_inputs",
        "quantum_priority_queue",
        "classical_baseline_queue",
        "hybrid_arbitration_queue",
        "agent_task_queue",
        "owner_review_queue",
    )
    return {name: load_pr161d_records(repo_root, name) for name in names}
