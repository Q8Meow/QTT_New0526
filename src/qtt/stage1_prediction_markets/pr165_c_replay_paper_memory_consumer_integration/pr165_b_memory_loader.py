"""PR165-B memory input loader for PR165-C."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_discovery import index_by, load_report_records

PR165_B_REPORTS = (
    "PR165_B_CandidateVersionMemoryRegistry.report.json",
    "PR165_B_ConditionFingerprintRegistry.report.json",
    "PR165_B_CombinationFingerprintRegistry.report.json",
    "PR165_B_ScenarioOutcomeMatrix.report.json",
    "PR165_B_CombinationOutcomeMemoryLedger.report.json",
    "PR165_B_NegativeCombinationAvoidanceRegistry.report.json",
    "PR165_B_PositiveConditionScopedPreferenceRegistry.report.json",
    "PR165_B_FragileCombinationWatchlist.report.json",
    "PR165_B_OutcomeAttributionLedger.report.json",
    "PR165_B_CounterfactualAttributionLedger.report.json",
    "PR165_B_CooldownPolicyRegistry.report.json",
    "PR165_B_RetestEligibilityRegistry.report.json",
    "PR165_B_ReplayPaperRetestQueue.report.json",
    "PR165_B_RepairRouteHandoffRegistry.report.json",
    "PR165_B_AgentMemoryRouter.report.json",
    "PR165_B_LineageGraph.report.json",
    "PR165_B_DashboardMemoryHandoff.report.json",
    "PR165_B_GovernanceMemoryHandoff.report.json",
)


def load_pr165_b_memory(repo_root: Path) -> dict[str, Any]:
    loaded = {name: load_report_records(repo_root, name) for name in PR165_B_REPORTS}
    indexed = {name: index_by(rows, "candidate_packet_id") for name, rows in loaded.items()}
    indexed["_memory_rows"] = loaded["PR165_B_CandidateVersionMemoryRegistry.report.json"]
    indexed["_raw_counts"] = {name: len(rows) for name, rows in loaded.items()}
    return indexed
