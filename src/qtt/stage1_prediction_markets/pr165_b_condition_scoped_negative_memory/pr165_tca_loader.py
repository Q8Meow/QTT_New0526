"""Loader for PR165 TCA and microstructure score rows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_discovery import load_report_records


def load_pr165_tca(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_TCAAdjustedScoreRegistry.report.json")


def load_pr165_implementation_shortfall(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_ImplementationShortfallScoreRegistry.report.json")


def load_pr165_liquidity(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_LiquidityFillProbabilityScoreRegistry.report.json")


def load_pr165_maker_taker(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_MakerTakerRouteScoreRegistry.report.json")


def load_pr165_adverse_selection(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR165_AdverseSelectionPenaltyRegistry.report.json")
