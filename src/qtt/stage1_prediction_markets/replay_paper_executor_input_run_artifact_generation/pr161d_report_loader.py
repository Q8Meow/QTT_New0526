"""PR161D replay/paper preparation loader for PR161F."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .artifact_loaders import load_records, load_report


def load_pr161d_reports(repo_root: Path) -> dict[str, Any]:
    return {
        "final_summary": load_report(repo_root, c.PR161D_REPORT_PATHS["final_summary"]),
        "quality_score": load_records(repo_root, c.PR161D_REPORT_PATHS["quality_score"]),
        "result_backed_slots": load_records(repo_root, c.PR161D_REPORT_PATHS["result_backed_slots"]),
        "scenario_outcome_matrix": load_records(repo_root, c.PR161D_REPORT_PATHS["scenario_outcome_matrix"]),
        "future_profitability_pattern": load_records(repo_root, c.PR161D_REPORT_PATHS["future_profitability_pattern"]),
        "combination_candidate": load_records(repo_root, c.PR161D_REPORT_PATHS["combination_candidate"]),
        "replay_paper_priority_queue": load_records(repo_root, c.PR161D_REPORT_PATHS["replay_paper_priority_queue"]),
        "replay_paper_scenario_inputs": load_records(repo_root, c.PR161D_REPORT_PATHS["replay_paper_scenario_inputs"]),
        "quantum_priority_queue": load_records(repo_root, c.PR161D_REPORT_PATHS["quantum_priority_queue"]),
        "classical_baseline_queue": load_records(repo_root, c.PR161D_REPORT_PATHS["classical_baseline_queue"]),
        "hybrid_arbitration_queue": load_records(repo_root, c.PR161D_REPORT_PATHS["hybrid_arbitration_queue"]),
        "agent_task_queue": load_records(repo_root, c.PR161D_REPORT_PATHS["agent_task_queue"]),
        "owner_review_queue": load_records(repo_root, c.PR161D_REPORT_PATHS["owner_review_queue"]),
    }

