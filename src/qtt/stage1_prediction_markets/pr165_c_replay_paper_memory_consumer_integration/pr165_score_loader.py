"""PR165 scoring/ranking input loader for PR165-C."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_discovery import group_by, index_by, load_report_records

PR165_REPORTS = (
    "PR165_CandidateScoreComponentRegistry.report.json",
    "PR165_GlobalCandidateRanking.report.json",
    "PR165_RegimeSlicedRanking.report.json",
    "PR165_ExpectedValueScoreRegistry.report.json",
    "PR165_TCAAdjustedScoreRegistry.report.json",
    "PR165_LatencyLaneAssignmentRegistry.report.json",
    "PR165_LiquidityFillProbabilityScoreRegistry.report.json",
    "PR165_AdverseSelectionPenaltyRegistry.report.json",
    "PR165_ModelRiskPenaltyRegistry.report.json",
    "PR165_RepairConfidenceScoreRegistry.report.json",
    "PR165_ProvenanceQualityScoreRegistry.report.json",
    "PR165_QuantumPriorityScoreRegistry.report.json",
    "PR165_QuantumFormulationMaterializationRegistry.report.json",
    "PR165_LineageGraph.report.json",
    "PR165_AgentScoringOrchestrationRouter.report.json",
    "PR165_QKUAgentConsumerCoverageMatrix.report.json",
    "PR165_DashboardScoreHandoff.report.json",
)


def load_pr165_scores(repo_root: Path) -> dict[str, Any]:
    loaded = {name: load_report_records(repo_root, name) for name in PR165_REPORTS}
    indexed = {name: index_by(rows, "candidate_packet_id") for name, rows in loaded.items() if name != "PR165_RegimeSlicedRanking.report.json"}
    regime_rows = loaded["PR165_RegimeSlicedRanking.report.json"]
    regimes_by_candidate = group_by(regime_rows, "candidate_packet_id")
    min_regime_rank: dict[str, int] = {}
    for candidate_id, rows in regimes_by_candidate.items():
        ranks = [int(row.get("regime_rank") or 0) for row in rows if row.get("regime_rank")]
        min_regime_rank[candidate_id] = min(ranks) if ranks else 0
    indexed["PR165_RegimeSlicedRanking.report.json"] = {
        candidate_id: {"min_regime_rank": min_regime_rank.get(candidate_id, 0), "regime_rank_rows": rows[:5]}
        for candidate_id, rows in regimes_by_candidate.items()
    }
    indexed["_raw_counts"] = {name: len(rows) for name, rows in loaded.items()}
    return indexed
