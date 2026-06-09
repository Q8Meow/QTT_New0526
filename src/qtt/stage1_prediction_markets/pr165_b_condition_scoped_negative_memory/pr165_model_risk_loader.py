"""Loader for PR165 model-risk, provenance, data-quality, and repair confidence rows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_discovery import load_report_records


def load_pr165_model_risk(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_ModelRiskPenaltyRegistry.report.json")


def load_pr165_provenance_quality(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_ProvenanceQualityScoreRegistry.report.json")


def load_pr165_data_quality(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_DataQualityScoreRegistry.report.json")


def load_pr165_repair_confidence(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_RepairConfidenceScoreRegistry.report.json")
