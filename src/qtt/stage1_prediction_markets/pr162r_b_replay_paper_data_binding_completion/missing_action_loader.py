"""Load PR162R missing actions and upstream row universes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .json_io import read_json, records_from_payload


def load_report_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    return records_from_payload(read_json(repo_root / "docs/master_plan/generated" / filename))


def load_missing_actions(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR162R_MissingDataBindingActionQueue.report.json")


def load_candidate_packets(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR162D_R2A_CandidatePacketV1Registry.report.json")


def load_replay_packets(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR162R_ReplayAdapterInputPacketRegistry.report.json")


def load_paper_packets(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR162R_PaperAdapterInputPacketRegistry.report.json")


def load_quantum_plan(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR162R_QuantumBatchPrecomputeRoutingPlan.report.json")


def load_qku_computability(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(repo_root, "PR162R_QKUComputabilityClassificationMatrix.report.json")


def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows if row.get(key)}
