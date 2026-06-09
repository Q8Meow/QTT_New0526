"""Loader for PR165 quantum formulation and priority rows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_discovery import load_report_records


def load_pr165_quantum_formulations(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_QuantumFormulationMaterializationRegistry.report.json")


def load_pr165_quantum_priority(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_QuantumPriorityScoreRegistry.report.json")
