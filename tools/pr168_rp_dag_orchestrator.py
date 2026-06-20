#!/usr/bin/env python3
"""Artifact and route DAG rows for PR168-RP."""

from __future__ import annotations

from typing import Any


def dag_edge(edge_id: str, source: str, target: str, consumer: str, route: str) -> dict[str, Any]:
    return {
        "edge_id": edge_id,
        "producer": "PR168_RP_DAG_ORCHESTRATOR",
        "consumer": consumer,
        "upstream_source": source,
        "downstream_route": route,
        "artifact_ref": target,
        "target_artifact": target,
        "owning_agent": "Commander Agent",
        "no_orphan_status": "CONNECTED_TO_DAG_CONSUMER",
    }


def core_dag_edges(report_names: list[str]) -> list[dict[str, Any]]:
    base = [
        ("PR168_GFP_TO_PR168_RP", "PR168-GFP", "PR168-RP", "Replay Paper Recompute Agent", "PR168-RP"),
        ("FORMULA_TO_PRETRADE", "PR168_RP_ComputedPnLEvidence.report.json", "PR168_RP_PreTradeSimulationCandidates.report.json", "Execution Simulation Agent", "PR168_RP_PreTradeDecisionDAG.report.json"),
        ("PRETRADE_TO_RANKING", "PR168_RP_PreTradeSimulationCandidates.report.json", "PR168_RP_OrderPolicyCandidateRanking.report.json", "Ranking Agent", "PR168_RP_OrderPolicyConsumerDAG.report.json"),
        ("NO_TRADE_TO_ELIGIBILITY", "PR168_RP_NoTradeCandidateComparison.report.json", "PR168_RP_PreTradeChampionChallengerEligibility.report.json", "Ranking Agent", "PR168_RP_PreTradeDecisionDAG.report.json"),
        ("NEGATIVE_TO_RECOVERY", "PR168_RP_ComputedNegativeEdgeCandidates.report.json", "PR168_RP_NegativeToPositiveRecoveryAttempts.report.json", "Alpha Recovery Agent", "PR168_RP_AgentDutyDAG.report.json"),
        ("QUANTUM_GAP_TO_QC", "PR168_RP_QuantumCoefficientMapInputGaps.report.json", "PR168_RP_To_PR166_QC_R2_RedoWithComputedEvidence.report.json", "Quantum Repair Agent", "PR168_RP_PRDependencyDAG.report.json"),
        ("LIVE_HANDOFF_TO_FUTURE_GATE", "PR168_RP_LivePreTradeDecisionGateSeed.report.json", "PR168_RP_To_ExecutionRouterLiveGateFutureHandoff.report.json", "Future Execution Router", "PR168_RP_LiveCandidateHandoffDAG.report.json"),
    ]
    rows = [dag_edge(edge_id, source, target, consumer, route) for edge_id, source, target, consumer, route in base]
    for index, report_name in enumerate(sorted(report_names), start=1):
        rows.append(
            dag_edge(
                f"REPORT_CONSUMER::{index:04d}",
                "PR168_RP_BUILD_KERNEL",
                report_name,
                "ReportConsumerCrosswalk",
                "PR168_RP_ArtifactInformationValueDAG.report.json",
            )
        )
    return rows
